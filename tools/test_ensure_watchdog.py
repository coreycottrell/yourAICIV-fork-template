#!/usr/bin/env python3
"""
test_ensure_watchdog.py -- the watchdog comes back after a container restart.

A container restart kills tools/watchdog.sh and the entrypoint has no startup hook. The
SessionStart hook (which the fleet's restart/launch path does run) calls
tools/ensure_watchdog.py, which starts the watchdog in a detached tmux session named
"watchdog" when it is not running, and does nothing when it is.

[1] starts when absent (tmux new-session -d -s watchdog 'bash <civ>/tools/watchdog.sh'), logs one line
[2] no-op when present; a tmux server whose argv mentions watchdog.sh is not a watchdog
[3] a stale "watchdog" session without a watchdog -> new window in it, never a second session
[4] never raises and never hangs: missing tmux, hung tmux, failing tmux, bad /proc, bad root
[5] only the civ root acts (test copies / checkouts are a no-op); AICIV_ENSURE_WATCHDOG=0 is off
[6] the SessionStart hook runs it: starts it, stays silent on stdout, exit 0
[7] real tmux (private socket): started for real, then recognized as running (no second copy)
[8] watchdog.sh: a stale pidfile whose PID is now another process does not stop the watchdog
[9] watchdog.sh: a portal restart passes PORTAL_PUBLIC_URL / TRIAL_CONFIG_PATH through
    (process env wins, else ~/.env, else <civ>/.env, TRIAL_CONFIG_PATH else settings.json env)

    python3 tools/test_ensure_watchdog.py        # exit 0 = all pass
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SRC / "tools"))
import ensure_watchdog as ew  # noqa: E402

FAILS: list[str] = []
PASSES = 0


def ok(cond: bool, label: str, detail: str = "") -> None:
    global PASSES
    if cond:
        PASSES += 1
        print(f"  PASS  {label}")
    else:
        FAILS.append(label)
        print(f"  FAIL  {label}" + (f"  [{detail}]" if detail else ""))


def make_civ(tmp: Path) -> Path:
    civ = tmp / "civ"
    (civ / "tools").mkdir(parents=True)
    (civ / ".claude" / "hooks").mkdir(parents=True)
    shutil.copy(SRC / "tools" / "watchdog.sh", civ / "tools" / "watchdog.sh")
    shutil.copy(SRC / "tools" / "ensure_watchdog.py", civ / "tools" / "ensure_watchdog.py")
    shutil.copy(SRC / ".claude" / "hooks" / "session_start.py", civ / ".claude" / "hooks" / "session_start.py")
    return civ


def fake_tmux(tmp: Path, has_session: bool = False, rc: int = 0, hang: bool = False,
              hang_start: bool = False) -> tuple[Path, Path]:
    calls = tmp / "tmux-calls.txt"
    stub = tmp / "bin" / "tmux"
    stub.parent.mkdir(exist_ok=True)
    body = ['#!/usr/bin/env bash', f'printf "%s\\n" "$*" >> "{calls}"']
    if hang:
        body.append("sleep 20")
    if hang_start:   # has-session answers at once; new-session hangs and leaves a child holding stderr
        body.append('[[ "$1" == new-session ]] && { sleep 20 & sleep 20; }')
    body.append(f'[[ "$1" == has-session ]] && exit {0 if has_session else 1}')
    body.append(f"exit {rc}")
    stub.write_text("\n".join(body) + "\n")
    stub.chmod(0o755)
    return stub, calls


def fake_proc(tmp: Path, cmdlines: list[list[str]]) -> Path:
    proc = tmp / "proc"
    proc.mkdir(exist_ok=True)
    for i, argv in enumerate(cmdlines, start=100):
        (proc / str(i)).mkdir()
        (proc / str(i) / "cmdline").write_bytes(b"\0".join(a.encode() for a in argv) + b"\0")
    return proc


def calls_of(calls: Path) -> list[str]:
    return calls.read_text().splitlines() if calls.exists() else []


def with_env(**kv):
    old = {k: os.environ.get(k) for k in kv}
    for k, v in kv.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    return old


def restore(old):
    for k, v in old.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def case(fn):
    tmp = Path(tempfile.mkdtemp(prefix="ensure-wd-"))
    try:
        fn(tmp)
    except Exception as e:  # a test crash is a failure, not a traceback
        ok(False, f"{fn.__name__} crashed", repr(e))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t1_starts_when_absent(tmp):
    print("[1] starts when absent")
    civ = make_civ(tmp)
    tmux, calls = fake_tmux(tmp)
    proc = fake_proc(tmp, [["bash", "-l"], ["python3", "portal_server.py"]])
    old = with_env(AICIV_CIV_ROOT=str(civ), AICIV_ENSURE_WATCHDOG=None)
    try:
        r = ew.ensure(civ, tmux=str(tmux), proc=str(proc))
    finally:
        restore(old)
    c = calls_of(calls)
    ok(r == "started", "returns 'started'", r)
    ok(c == ["has-session -t =watchdog", f"new-session -d -s watchdog bash {civ}/tools/watchdog.sh"],
       "tmux new-session -d -s watchdog 'bash <civ>/tools/watchdog.sh'", repr(c))
    log = (civ / "logs" / "watchdog.log").read_text().splitlines()
    ok(len(log) == 1 and "ensure_watchdog: watchdog was not running" in log[0], "logs exactly one line", repr(log))


def t2_noop_when_present(tmp):
    print("[2] no-op when present")
    civ = make_civ(tmp)
    tmux, calls = fake_tmux(tmp, has_session=True)
    old = with_env(AICIV_CIV_ROOT=str(civ), AICIV_ENSURE_WATCHDOG=None)
    try:
        for argv, label in (
            (["bash", f"{civ}/tools/watchdog.sh"], "bash <civ>/tools/watchdog.sh"),
            (["/bin/bash", "tools/watchdog.sh"], "/bin/bash tools/watchdog.sh (relative)"),
            ([f"{civ}/tools/watchdog.sh"], "watchdog.sh executed directly"),
            (["sh", "-c", f"bash {civ}/tools/watchdog.sh"], "tmux's sh -c wrapper"),
        ):
            p = tmp / f"p{abs(hash(label))}"
            p.mkdir()
            proc = fake_proc(p, [["bash", "-l"], argv])
            r = ew.ensure(civ, tmux=str(tmux), proc=str(proc))
            ok(r == "running", f"running: {label} -> no-op", r)
        ok(calls_of(calls) == [], "tmux never called while it runs", repr(calls_of(calls)))
        ok(not (civ / "logs" / "watchdog.log").exists(), "no-op writes no log line")
        # the tmux server keeps the argv of the client that started it
        tsrv = tmp / "tsrv"
        tsrv.mkdir()
        proc = fake_proc(tsrv, [["tmux", "new-session", "-d", "-s", "watchdog", f"bash {civ}/tools/watchdog.sh"],
                                ["vim", f"{civ}/tools/watchdog.sh"]])
        ok(not ew.watchdog_running(str(proc)), "tmux server / editor argv is not a running watchdog")
    finally:
        restore(old)


def t3_stale_session(tmp):
    print("[3] stale 'watchdog' session, no watchdog process")
    civ = make_civ(tmp)
    tmux, calls = fake_tmux(tmp, has_session=True)
    proc = fake_proc(tmp, [["bash"]])
    old = with_env(AICIV_CIV_ROOT=str(civ), AICIV_ENSURE_WATCHDOG=None)
    try:
        r = ew.ensure(civ, tmux=str(tmux), proc=str(proc))
    finally:
        restore(old)
    c = calls_of(calls)
    ok(r == "started", "returns 'started'", r)
    ok(c[-1:] == [f"new-window -d -t =watchdog: bash {civ}/tools/watchdog.sh"] and
       not any(x.startswith("new-session") for x in c), "new window in the existing session, no second session", repr(c))


def t4_never_raises(tmp):
    print("[4] never raises, never hangs")
    civ = make_civ(tmp)
    proc = fake_proc(tmp, [])
    old = with_env(AICIV_CIV_ROOT=str(civ), AICIV_ENSURE_WATCHDOG=None)
    try:
        r = ew.ensure(civ, tmux=str(tmp / "no-such-tmux"), proc=str(proc))
        ok(r.startswith("error:"), "tmux missing -> 'error: ...' returned, not raised", r)
        bad, _ = fake_tmux(tmp, rc=1)
        r = ew.ensure(civ, tmux=str(bad), proc=str(proc))
        ok(r.startswith("failed"), "tmux fails -> 'failed ...' returned", r)
        hung, _ = fake_tmux(tmp, hang=True)
        t0 = time.time()
        r = ew.ensure(civ, tmux=str(hung), proc=str(proc))
        took = time.time() - t0
        ok(r.startswith("error:") and took < ew.TIMEOUT + 2, f"hung tmux -> times out ({took:.1f}s)", r)
        hung2, _ = fake_tmux(tmp, hang_start=True)
        t0 = time.time()
        r = ew.ensure(civ, tmux=str(hung2), proc=str(proc))
        took = time.time() - t0
        ok(r.startswith("error:") and took < ew.TIMEOUT + 2,
           f"new-session hangs with a child holding stderr -> still bounded ({took:.1f}s)", r)
        r = ew.ensure(civ, tmux=str(bad), proc=str(tmp / "no-proc"))
        ok(isinstance(r, str), "missing /proc -> still returns", r)
        r = ew.ensure(None, tmux=str(bad), proc=str(proc))
        ok(isinstance(r, str), "root=None -> still returns", r)
        lines = (civ / "logs" / "watchdog.log").read_text().splitlines()
        ok(all("ensure_watchdog:" in x for x in lines) and len(lines) >= 3, "each failure logs one line", repr(lines))
    finally:
        restore(old)
    (civ / "logs").chmod(0o500)
    try:
        old = with_env(AICIV_CIV_ROOT=str(civ), AICIV_ENSURE_WATCHDOG=None)
        good, _ = fake_tmux(tmp)
        r = ew.ensure(civ, tmux=str(good), proc=str(proc))
        ok(r == "started", "unwritable log -> still works", r)
    finally:
        restore(old)
        (civ / "logs").chmod(0o700)


def t5_scope(tmp):
    print("[5] only the civ root acts")
    civ = make_civ(tmp)
    tmux, calls = fake_tmux(tmp)
    proc = fake_proc(tmp, [])
    old = with_env(AICIV_CIV_ROOT=str(tmp / "elsewhere"), AICIV_ENSURE_WATCHDOG=None)
    try:
        r = ew.ensure(civ, tmux=str(tmux), proc=str(proc))
        ok(r.startswith("skipped"), "a copy outside the civ root -> skipped", r)
        os.environ.pop("AICIV_CIV_ROOT")
        r = ew.ensure(civ, tmux=str(tmux), proc=str(proc))
        ok(r.startswith("skipped"), "default civ root is /home/aiciv/civ -> temp copy skipped", r)
        os.environ.update(AICIV_CIV_ROOT=str(civ), AICIV_ENSURE_WATCHDOG="0")
        r = ew.ensure(civ, tmux=str(tmux), proc=str(proc))
        ok(r == "disabled", "AICIV_ENSURE_WATCHDOG=0 -> disabled", r)
        os.environ.pop("AICIV_ENSURE_WATCHDOG")
        (civ / "tools" / "watchdog.sh").unlink()
        r = ew.ensure(civ, tmux=str(tmux), proc=str(proc))
        ok(r.startswith("skipped"), "no tools/watchdog.sh -> skipped", r)
    finally:
        restore(old)
    ok(calls_of(calls) == [], "tmux never called", repr(calls_of(calls)))


def run_hook(civ: Path, env: dict) -> subprocess.CompletedProcess:
    e = {k: v for k, v in os.environ.items() if not k.startswith("AICIV_")}
    e.update(env)
    e["CLAUDE_PROJECT_DIR"] = str(civ)
    return subprocess.run([sys.executable, str(civ / ".claude/hooks/session_start.py")], input='{"session_type":"startup"}',
                          capture_output=True, text=True, env=e, timeout=30)


def t6_hook(tmp):
    print("[6] SessionStart hook")
    civ = make_civ(tmp)
    tmux, calls = fake_tmux(tmp)
    proc = fake_proc(tmp, [])
    path = f"{tmux.parent}:{os.environ.get('PATH', '')}"
    r = run_hook(civ, {"PATH": path, "AICIV_PROC_ROOT": str(proc)})
    ok(r.returncode == 0 and calls_of(calls) == [], "not the civ root: hook runs, tmux untouched", r.stderr[-300:])
    r = run_hook(civ, {"PATH": path, "AICIV_CIV_ROOT": str(civ), "AICIV_PROC_ROOT": str(proc)})
    c = calls_of(calls)
    ok(r.returncode == 0, "hook exit 0", r.stderr[-300:])
    ok(f"new-session -d -s watchdog bash {civ}/tools/watchdog.sh" in c, "hook started the watchdog", repr(c))
    ok("watchdog" not in r.stdout.lower(), "nothing about it on stdout")
    ok("[Session Ledger] Initialized" in r.stdout, "rest of the hook still ran")
    broken = tmp / "broken-bin"
    broken.mkdir()
    (broken / "tmux").write_text("#!/usr/bin/env bash\nexit 7\n")
    (broken / "tmux").chmod(0o755)
    r = run_hook(civ, {"PATH": f"{broken}:{os.environ.get('PATH', '')}", "AICIV_CIV_ROOT": str(civ),
                       "AICIV_PROC_ROOT": str(proc)})
    ok(r.returncode == 0 and "[Session Ledger] Initialized" in r.stdout, "failing tmux never breaks session start")


def t7_real_tmux(tmp):
    print("[7] real tmux on a private socket")
    if not shutil.which("tmux"):
        ok(True, "tmux not installed -- skipped")
        return
    civ = make_civ(tmp)
    (civ / "tools" / "watchdog.sh").write_text("#!/usr/bin/env bash\nsleep 60\n")   # stand-in watchdog
    sock = f"ensure-wd-test-{os.getpid()}"
    wrap = tmp / "bin" / "tmux"
    wrap.parent.mkdir()
    wrap.write_text(f'#!/usr/bin/env bash\nexec tmux -L {sock} "$@"\n')
    wrap.chmod(0o755)
    empty = fake_proc(tmp, [])
    old = with_env(AICIV_CIV_ROOT=str(civ), AICIV_ENSURE_WATCHDOG=None)
    try:
        r = ew.ensure(civ, tmux=str(wrap), proc=str(empty))
        ok(r == "started", "started", r)
        has = subprocess.run(["tmux", "-L", sock, "has-session", "-t", "=watchdog"]).returncode == 0
        ok(has, "tmux session 'watchdog' exists")
        mine = None
        for _ in range(30):
            mine = []
            for p in os.listdir("/proc"):
                try:
                    if p.isdigit() and str(civ) in Path(f"/proc/{p}/cmdline").read_bytes().decode(errors="replace"):
                        mine.append(p)
                except OSError:
                    pass
            if mine:
                break
            time.sleep(0.1)
        view = tmp / "view"
        view.mkdir()
        for p in mine or []:
            try:
                data = Path(f"/proc/{p}/cmdline").read_bytes()
            except OSError:
                continue
            (view / p).mkdir()
            (view / p / "cmdline").write_bytes(data)
        r = ew.ensure(civ, tmux=str(wrap), proc=str(view))
        ok(r == "running", "the started process is recognized -> second ensure is a no-op", r)
        n = subprocess.run(["tmux", "-L", sock, "list-sessions"], capture_output=True, text=True).stdout
        ok(n.count("watchdog") == 1, "still exactly one 'watchdog' session", n)
    finally:
        restore(old)
        subprocess.run(["tmux", "-L", sock, "kill-server"], capture_output=True)


def wd_functions(tmp: Path) -> Path:
    """The helper + portal-env + pidfile functions of tools/watchdog.sh, without its main loop."""
    s = (SRC / "tools" / "watchdog.sh").read_text()
    body = s[s.index("# ── Helpers"):s.index("# ── Process Checks")]
    f = tmp / "wd_funcs.sh"
    f.write_text("set -euo pipefail\n" + body)
    return f


def bash(tmp: Path, script: str, env: dict) -> subprocess.CompletedProcess:
    e = {k: v for k, v in os.environ.items() if k not in ("PORTAL_PUBLIC_URL", "TRIAL_CONFIG_PATH")}
    e.update(env)
    return subprocess.run(["bash", "-c", f'source "{wd_functions(tmp)}"\n{script}'], capture_output=True,
                          text=True, env=e, timeout=20)


def t8_stale_pidfile(tmp):
    print("[8] watchdog.sh stale pidfile")
    pidfile = tmp / "wd.pid"
    other = subprocess.Popen(["sleep", "30"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    fake = tmp / "watchdog.sh"
    fake.write_text("#!/usr/bin/env bash\nsleep 30 & wait\n")
    live = subprocess.Popen(["bash", str(fake)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            start_new_session=True)
    try:
        env = {"LOG": str(tmp / "wd.log"), "PIDFILE": str(pidfile)}
        pidfile.write_text(str(other.pid))
        r = bash(tmp, 'LOG=$LOG; PIDFILE=$PIDFILE; check_already_running; echo "ME=$$"', env)
        ok(r.returncode == 0 and "ME=" in r.stdout and "already running" not in r.stdout,
           "PID reused by an unrelated process -> watchdog starts", r.stdout + r.stderr)
        pidfile.write_text(str(live.pid))
        r = bash(tmp, 'LOG=$LOG; PIDFILE=$PIDFILE; check_already_running; echo "ME=$$"', env)
        ok("already running" in r.stdout and "ME=" not in r.stdout, "a live watchdog.sh -> exits (no second copy)",
           r.stdout + r.stderr)
    finally:
        other.kill()
        try:
            os.killpg(live.pid, 9)   # bash and its sleep
        except OSError:
            pass


def t9_portal_env(tmp):
    print("[9] watchdog.sh portal restart keeps PORTAL_PUBLIC_URL / TRIAL_CONFIG_PATH")
    home = tmp / "home"
    civ = tmp / "civ"
    (civ / ".claude").mkdir(parents=True)
    home.mkdir()
    log = tmp / "wd.log"
    show = 'LOG=$LOG; portal_env; echo "URL=${PORTAL_PUBLIC_URL:-}"; echo "TCP=${TRIAL_CONFIG_PATH:-}"; ' \
           'bash -c \'echo "CHILD=$PORTAL_PUBLIC_URL|$TRIAL_CONFIG_PATH"\''
    base = {"HOME": str(home), "CLAUDE_PROJECT_DIR": str(civ), "LOG": str(log)}

    r = bash(tmp, show, base)
    ok(r.returncode == 0 and "URL=\n" in r.stdout and "TCP=\n" in r.stdout,
       "nothing anywhere -> unset, no crash under set -euo pipefail", r.stdout + r.stderr)
    ok("PORTAL_PUBLIC_URL=unset TRIAL_CONFIG_PATH=unset" in log.read_text(), "logs one 'Portal env' line")

    (home / ".env").write_text('FOO=1\nexport PORTAL_PUBLIC_URL="https://keel-travis.ai-civ.com"\n'
                               "TRIAL_CONFIG_PATH='/etc/aiciv/trial.json'\n")
    r = bash(tmp, show, base)
    ok("CHILD=https://keel-travis.ai-civ.com|/etc/aiciv/trial.json" in r.stdout,
       "read from ~/.env (export + quotes) and passed to the child portal", r.stdout + r.stderr)

    r = bash(tmp, show, {**base, "PORTAL_PUBLIC_URL": "https://env.example", "TRIAL_CONFIG_PATH": "/x/t.json"})
    ok("CHILD=https://env.example|/x/t.json" in r.stdout, "process env wins over ~/.env", r.stdout)

    (home / ".env").write_text("OTHER=1\n")
    (civ / ".env").write_text("PORTAL_PUBLIC_URL=https://civ-env.example\n")
    (civ / ".claude" / "settings.json").write_text(json.dumps({"env": {"TRIAL_CONFIG_PATH": "/etc/aiciv/trial.json"}}))
    r = bash(tmp, show, base)
    ok("CHILD=https://civ-env.example|/etc/aiciv/trial.json" in r.stdout,
       "fallbacks: <civ>/.env, then settings.json env for TRIAL_CONFIG_PATH", r.stdout + r.stderr)

    s = (SRC / "tools" / "watchdog.sh").read_text()
    restart = s[s.index("portal_check() {"):s.index("telegram_check() {")]
    ok(restart.index("portal_env") < restart.index('nohup bash "$PORTAL_DIR/start.sh"'),
       "portal_check exports them before 'nohup bash start.sh' (Python portal path)")


def main() -> int:
    for t in (t1_starts_when_absent, t2_noop_when_present, t3_stale_session, t4_never_raises, t5_scope,
              t6_hook, t7_real_tmux, t8_stale_pidfile, t9_portal_env):
        case(t)
    print(f"\n{PASSES} passed, {len(FAILS)} failed")
    for f in FAILS:
        print(f"  - {f}")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
