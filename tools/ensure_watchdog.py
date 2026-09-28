#!/usr/bin/env python3
"""ensure_watchdog.py -- bring tools/watchdog.sh back after a container restart.

The fleet starts tools/watchdog.sh at birth in a detached tmux session named
"watchdog". A container restart kills it and the container entrypoint has no
startup hook, so nothing brought it back. What DOES run after a restart is the
AiCIV's Claude session (the fleet's restart/launch path), and with it the
SessionStart hook. That hook calls ensure() here:

  * watchdog.sh already running (any copy)  -> "running", silent
  * not running, no tmux session "watchdog" -> tmux new-session -d -s watchdog
        'CLAUDE_PROJECT_DIR=<civ> HOME=<home> bash <civ>/tools/watchdog.sh'
        -> "started in tmux session 'watchdog'"
  * not running, a stale "watchdog" session -> a new window in that session, same command
        -> "started in a new window of the existing tmux session 'watchdog'"

It never starts a second copy (watchdog.sh also refuses to run twice via its
pidfile), never blocks session start (every subprocess has a short timeout),
never raises, prints nothing to stdout, and logs one line to logs/watchdog.log
when it acts or fails.

It only acts for the civ the watchdog serves. The civ root is the tree this file
lives in (<root>/tools/ensure_watchdog.py), and it must be a LIVE civ's tree: in
the fleet the template is checked out at /home/aiciv, which is also HOME, so the
tree must be $HOME (or the legacy /home/aiciv/civ layout). A copy of the tree
anywhere else (tests, a developer checkout) is a no-op. $AICIV_CIV_ROOT, when
set, overrides all of that: the project dir must then be exactly that root.
AICIV_ENSURE_WATCHDOG=0 switches it off.

The started command carries the root along -- CLAUDE_PROJECT_DIR=<root> and
HOME -- because a tmux server that is already running gives new sessions ITS
environment, not ours, and watchdog.sh reads client_sites, partner_notify, the
portal env and its log from CLAUDE_PROJECT_DIR.

CLI:  python3 tools/ensure_watchdog.py [--root DIR]   (prints the outcome)
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SESSION = "watchdog"
OWN_TREE = Path(__file__).resolve().parent.parent   # the civ tree this file ships in
LEGACY_CIV_ROOT = "/home/aiciv/civ"                  # older layout: civ tree under HOME
SHELLS = {"bash", "sh", "dash"}
TIMEOUT = 2


def _log(root: Path, line: str) -> None:
    try:
        log = root / "logs" / "watchdog.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with open(log, "a") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ensure_watchdog: {line}\n")
    except Exception:
        pass


def watchdog_running(proc: str = "/proc") -> bool:
    """True if a process is executing watchdog.sh (bash watchdog.sh, or watchdog.sh itself).

    Matches on argv, not a substring of the whole command line: a tmux server
    whose argv mentions watchdog.sh (it keeps the argv of the client that
    started it) is not a running watchdog.
    """
    try:
        entries = os.listdir(proc)
    except OSError:
        return False
    me = str(os.getpid())
    for pid in entries:
        if not pid.isdigit() or pid == me:
            continue
        try:
            with open(os.path.join(proc, pid, "cmdline"), "rb") as f:
                argv = [a.decode(errors="replace") for a in f.read().split(b"\0") if a]
        except OSError:
            continue
        if not argv:
            continue
        if os.path.basename(argv[0]) == "watchdog.sh":
            return True
        if os.path.basename(argv[0]) in SHELLS and any(
                os.path.basename(a) == "watchdog.sh" for a in argv[1:]):
            return True
    return False


def _same(a, b) -> bool:
    try:
        return Path(a).resolve() == Path(b).resolve()
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def is_civ_root(root) -> bool:
    """The project dir is the civ this watchdog serves.

    $AICIV_CIV_ROOT set -> root must be exactly that. Otherwise root must be the tree this
    file lives in AND a live civ's tree: $HOME (the fleet: template checked out at
    /home/aiciv = HOME) or the legacy /home/aiciv/civ.
    """
    override = os.environ.get("AICIV_CIV_ROOT")
    if override:
        return _same(root, override)
    if not _same(root, OWN_TREE):
        return False
    home = os.environ.get("HOME") or os.path.expanduser("~")
    return _same(root, home) or _same(root, LEGACY_CIV_ROOT)


def start_command(root: Path) -> str:
    """The shell command tmux runs: watchdog.sh with the root (and HOME) passed along."""
    root = Path(root).resolve()
    home = os.environ.get("HOME") or os.path.expanduser("~")
    return (f"CLAUDE_PROJECT_DIR={shlex.quote(str(root))} HOME={shlex.quote(home)} "
            f"bash {shlex.quote(str(root / 'tools' / 'watchdog.sh'))}")


def ensure(root, tmux: str = "tmux", proc: str | None = None) -> str:
    """Start the watchdog if it is not running. Returns what it did. Never raises."""
    try:
        proc = proc or os.environ.get("AICIV_PROC_ROOT") or "/proc"   # override: tests only
        root = Path(root)
        if os.environ.get("AICIV_ENSURE_WATCHDOG", "1").strip() == "0":
            return "disabled"
        if not is_civ_root(root):
            return "skipped: not the civ root"
        script = root / "tools" / "watchdog.sh"
        if not script.is_file():
            return "skipped: no tools/watchdog.sh"
        if watchdog_running(proc):
            return "running"

        env = dict(os.environ)
        env.pop("TMUX", None)          # called from inside the civ's own tmux pane
        env.pop("TMUX_PANE", None)
        cmd = start_command(root)
        has = subprocess.run([tmux, "has-session", "-t", f"={SESSION}"], env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             timeout=TIMEOUT).returncode == 0
        if has:   # session left behind without a watchdog in it
            argv = [tmux, "new-window", "-d", "-t", f"={SESSION}:", cmd]
            how = "started in a new window of the existing tmux session 'watchdog'"
        else:
            argv = [tmux, "new-session", "-d", "-s", SESSION, cmd]
            how = "started in tmux session 'watchdog'"
        # stderr to a file, not a pipe: a pipe held open by a lingering child would make
        # subprocess wait past the timeout.
        with tempfile.TemporaryFile() as errf:
            r = subprocess.run(argv, env=env, cwd=str(root), stdout=subprocess.DEVNULL,
                               stderr=errf, timeout=TIMEOUT)
            errf.seek(0)
            stderr = errf.read(4096)
        if r.returncode != 0:
            err = stderr.decode(errors="replace").strip().splitlines()
            msg = f"failed to start watchdog ({err[-1] if err else f'exit {r.returncode}'})"
            _log(root, msg)
            return msg
        _log(root, f"watchdog was not running; {how} (CLAUDE_PROJECT_DIR={root.resolve()})")
        return how
    except Exception as e:   # never let this break a session start
        try:
            _log(Path(root), f"error: {e}")
        except Exception:
            pass
        return f"error: {e}"


def main(argv: list[str]) -> int:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or str(Path(__file__).resolve().parent.parent)
    if len(argv) >= 2 and argv[0] == "--root":
        root = argv[1]
    print(ensure(root))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
