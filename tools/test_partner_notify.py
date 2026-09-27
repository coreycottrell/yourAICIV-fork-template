#!/usr/bin/env python3
"""
test_partner_notify.py -- regression test for partner notifications (skill: partner-notifications).

Copies this template into temp dirs, "births" a scratch civ (Keel, for Sam Jones), and drives
every partner event through the real entry points: the session start hook, the trial gate hook,
`apply_trial_profile.py convert`, the watchdog's `tick`, and the AiCIV's own `send`. AgentMail is
a loopback stub (AGENTMAIL_API_BASE), so the full HTTP send path runs and nothing leaves the box.

Asserts, per event: exactly ONE email to the partner address from config/partner.json
(cryptoconsultants1@gmail.com), however many parts report it; plus the outbox path when no email
is provisioned, retry after a failed send, and that no notification ever fails its trigger.

    python3 tools/test_partner_notify.py        # exit 0 = all pass
"""
from __future__ import annotations

import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
PARTNER = "cryptoconsultants1@gmail.com"
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


class Stub:
    """Loopback AgentMail: records sends; `fail` makes the next sends answer 500."""

    def __init__(self):
        self.posts: list[dict] = []
        self.fail = 0
        stub = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"inboxes": [{"inbox_id": "keel@agentmail.to"}]}).encode()
                                 if self.path.startswith("/v0/inboxes") else b"{}")

            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
                if stub.fail:
                    stub.fail -= 1
                    self.send_response(500)
                    self.end_headers()
                    return
                stub.posts.append({"path": self.path, "auth": self.headers.get("Authorization"), **body})
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"message_id": "m"}')

            def log_message(self, *a):
                pass

        self.srv = http.server.HTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.srv.server_port}"

    def events(self, word: str) -> list[dict]:
        return [p for p in self.posts if word in p["subject"]]


def closed_port() -> int:
    import socket
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def birth(dst: Path) -> Path:
    shutil.copytree(SRC, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", "partner-notifications", ".venv"),
                    symlinks=True)
    for p in ("config/trial.json", "config/model_profile.json", "config/launch_model.txt"):
        (dst / p).unlink(missing_ok=True)
    ident = json.loads((dst / ".aiciv-identity.json").read_text())
    ident.update({"civ_name": "Keel", "human_name": "Sam Jones"})
    (dst / ".aiciv-identity.json").write_text(json.dumps(ident))
    prof = json.loads((dst / "memories/identity/human-profile.json").read_text())
    prof.update({"human_name": "Sam Jones", "goals": ["double catering orders", "stop losing weekend leads"]})
    (dst / "memories/identity/human-profile.json").write_text(json.dumps(prof))
    return dst


def main() -> int:
    stub = Stub()
    base_env = {k: v for k, v in os.environ.items()
                if not k.startswith(("AGENTMAIL_", "PARTNER_", "TRIAL_", "ANTHROPIC_BASE_URL", "CIV_"))}
    base_env.pop("CLAUDE_PROJECT_DIR", None)
    mail = {"AGENTMAIL_API_KEY": "am_test_dummy_not_a_key", "AGENTMAIL_INBOX": "keel@agentmail.to",
            "AGENTMAIL_API_BASE": stub.url, "AGENTMAIL_ENV_FILE": "/nonexistent",
            "PARTNER_NOTIFY_SYNC": "1", "PARTNER_NOTIFY_KICK_THROTTLE_SECS": "0"}
    tmp = Path(tempfile.mkdtemp(prefix="partner-notify-"))

    def run(cmd, root: Path, extra=None, stdin=None):
        env = {**base_env, **mail, "CLAUDE_PROJECT_DIR": str(root), "CIV_ROOT": str(root), **(extra or {})}
        return subprocess.run(cmd, cwd=root, env=env, input=stdin, capture_output=True, text=True)

    def send(root, *args, extra=None):
        return run([sys.executable, "tools/partner_notify.py", "send", *args], root, extra)

    def hook(root, name, event, extra=None):
        return run([sys.executable, f".claude/hooks/{name}"], root, extra, json.dumps({"hook_event_name": event}))

    try:
        civ = birth(tmp / "civ")

        print("[1] recipients + no-partner no-op")
        pp = json.loads(run([sys.executable, "tools/partner_profile.py", "show"], civ).stdout)
        ok(pp["notify_emails"] == [PARTNER], "config/partner.json notify_emails -> the partner address")
        pp = json.loads(run([sys.executable, "tools/partner_profile.py", "show"], civ,
                            {"PARTNER_NOTIFY_EMAILS": "ops@example.com, x"}).stdout)
        ok(pp["notify_emails"] == ["ops@example.com"], "PARTNER_NOTIFY_EMAILS overrides (invalid entries dropped)")
        bare = birth(tmp / "bare")
        (bare / "config/partner.json").unlink()
        r = send(bare, "--event", "born")
        ok(r.returncode == 0 and r.stdout.startswith("NO PARTNER") and not stub.posts,
           "no partner.json: nothing sent, exit 0")
        tpl = tmp / "tpl"
        shutil.copytree(SRC, tpl, ignore=shutil.ignore_patterns(".git", "__pycache__", "partner-notifications", ".venv"))
        r = run([sys.executable, "tools/partner_notify.py", "sweep"], tpl)
        ok(r.returncode == 0 and r.stdout.strip() == "" and not stub.posts,
           "template source tree (unsubstituted identity): no 'born' notice")

        print("[2] born: session start hook, exactly once")
        r = hook(civ, "session_start.py", "SessionStart")
        born = stub.events("born and awake")
        ok(r.returncode == 0 and len(born) == 1 and born[0]["to"] == PARTNER, "session start -> one 'born' email",
           f"{len(born)} {r.stderr[-300:]}")
        ok(born and born[0]["subject"] == "[yourAICIV] Sam Jones (Keel) - is born and awake",
           "subject: [brand] client (civ) - event", born[0]["subject"] if born else "")
        ok(born and born[0]["path"] == "/v0/inboxes/keel@agentmail.to/messages/send"
           and born[0]["auth"] == "Bearer am_test_dummy_not_a_key", "sent from the AiCIV's own AgentMail inbox")
        hook(civ, "session_start.py", "SessionStart")
        run([sys.executable, "tools/partner_notify.py", "tick"], civ)
        ok(len(stub.events("born and awake")) == 1, "second session + watchdog tick: still one 'born'")

        print("[3] first conversation")
        ident = civ / "memories/identity"
        (ident / ".identity-interview-complete").mkdir()
        r = send(civ, "--event", "first_conversation", "--summary",
                 "Goals: double catering orders. First build: a catering booking page.")
        fc = stub.events("first conversation")
        ok(r.stdout.startswith("SENT") and len(fc) == 1 and "catering booking page" in fc[0]["text"],
           "AiCIV report -> one email with its summary", r.stdout + r.stderr[-200:])
        run([sys.executable, "tools/partner_notify.py", "sweep"], civ, {"PARTNER_NOTIFY_GRACE_SECS": "0"})
        r = send(civ, "--event", "first_conversation", "--summary", "again")
        ok(len(stub.events("first conversation")) == 1 and r.stdout.startswith("ALREADY REPORTED"),
           "disk sweep + a repeat report: still one")
        civ2 = birth(tmp / "civ2")
        (civ2 / "memories/identity/.evolution-done").write_text("done\n")
        run([sys.executable, "tools/partner_notify.py", "sweep"], civ2)
        ok(len(stub.events("Sam Jones (Keel) - first conversation")) == 1,
           "backstop waits out the grace period (AiCIV's own report wins)")
        run([sys.executable, "tools/partner_notify.py", "sweep"], civ2, {"PARTNER_NOTIFY_GRACE_SECS": "0"})
        fc2 = [p for p in stub.events("first conversation") if "double catering orders" in p["text"]
               and "Goals:" in p["text"] and "catering booking page" not in p["text"]]
        ok(len(stub.events("first conversation")) == 2 and len(fc2) == 1,
           "backstop (AiCIV forgot): one email, goals from human-profile.json")

        print("[4] WOW builds")
        for n in (1, 2):
            d = ident / f"build-{n}-ship-evidence"
            d.mkdir()
            (d / "receipt.txt").write_text(f"build_n={n}\nbuild_name=Build {n} name\n"
                                           f"first_shipped_artifact_path=deliverables/b{n}/index.html\n")
        r = send(civ, "--event", "wow_shipped", "--build", "1", "--summary", "Catering booking page",
                 "--link", "https://portal.example/site/sams-bakery/")
        w1 = stub.events("WOW build #1 shipped")
        ok(len(w1) == 1 and "https://portal.example/site/sams-bakery/" in w1[0]["text"]
           and "Catering booking page" in w1[0]["text"], "build #1: AiCIV report with what + link")
        run([sys.executable, "tools/partner_notify.py", "sweep"], civ)
        ok(not stub.events("WOW build #2"), "fresh receipt for build #2: sweep waits (grace)")
        run([sys.executable, "tools/partner_notify.py", "sweep"], civ, {"PARTNER_NOTIFY_GRACE_SECS": "0"})
        w2 = stub.events("WOW build #2 shipped")
        ok(len(stub.events("WOW build #1")) == 1 and len(w2) == 1 and "Build 2 name" in w2[0]["text"],
           "sweep: build #1 still one; build #2 (forgotten) one, from its receipt")
        send(civ, "--event", "wow_shipped", "--build", "2", "--summary", "late")
        ok(len(stub.events("WOW build #2")) == 1, "late AiCIV report of build #2 deduped")

        print("[5] trial: day 6, expired, converted (trial gate hook + operator convert)")
        key = tmp / "key.txt"
        key.write_text("rk_TEST_dummy_not_a_key\n")
        now = datetime.now(timezone.utc)
        seams = {"M3_ROUTER_BASE_URL": "https://m3-router.invalid/anthropic", "M3_ROUTER_KEY_FILE": str(key)}
        day6 = (now - timedelta(days=5, hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = run([sys.executable, "tools/apply_trial_profile.py", "apply", "--root", str(civ)], civ,
                {**seams, "TRIAL_START": day6})
        ok(r.returncode == 0, "trial profile applied (clock at day 6)", r.stderr[-300:])
        ok(not stub.events("trial"), "applying the trial sends nothing by itself")
        g = hook(civ, "trial_gate.py", "UserPromptSubmit")
        ctx = json.loads(g.stdout or "{}").get("hookSpecificOutput", {}).get("additionalContext", "")
        te = stub.events("trial expires tomorrow")
        ok(len(te) == 1 and "Day 6 of 7" in te[0]["text"], "day 6 -> one 'expires tomorrow' email",
           f"{len(te)} {g.stderr[-300:]}")
        ok("Day 6 of 7" in ctx, "the gate's own output is unchanged (valid JSON countdown)")
        hook(civ, "trial_gate.py", "UserPromptSubmit")
        ok(len(stub.events("trial expires tomorrow")) == 1, "next turn: still one")
        gate_bash = run([sys.executable, ".claude/hooks/trial_gate.py"], civ, None, json.dumps({
            "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {
                "command": 'python3 tools/partner_notify.py send --event wow_shipped --build 3 --summary "x"'}}))
        ok('"deny"' not in gate_bash.stdout, "active trial: the AiCIV may run the sender")

        old = (now - timedelta(days=8)).strftime("%Y-%m-%dT%H:%M:%SZ")
        run([sys.executable, "tools/apply_trial_profile.py", "apply", "--root", str(civ), "--reset-clock"], civ,
            {**seams, "TRIAL_START": old})
        g = hook(civ, "trial_gate.py", "SessionStart")
        tx = stub.events("trial expired")
        ok(len(tx) == 1 and "buy.stripe.com" in tx[0]["text"], "expired -> one email with the payment link shown",
           f"{len(tx)} {g.stderr[-200:]}")
        ok("TRIAL EXPIRED" in g.stdout, "expired directive still injected")
        ok(len(stub.events("trial expires tomorrow")) == 1, "no late 'expires tomorrow' after expiry")
        hook(civ, "trial_gate.py", "UserPromptSubmit")
        ok(len(stub.events("trial expired")) == 1, "next turn: still one")

        r = run([sys.executable, "tools/apply_trial_profile.py", "convert", "--root", str(civ)], civ)
        cv = stub.events("converted to paid")
        ok(r.returncode == 0 and len(cv) == 1 and "partner notification (converted): sent" in r.stdout + r.stderr,
           "operator convert -> one 'converted' email", r.stdout[-300:] + r.stderr[-300:])
        hook(civ, "trial_gate.py", "UserPromptSubmit")
        hook(civ, "session_start.py", "SessionStart")
        run([sys.executable, "tools/apply_trial_profile.py", "convert", "--root", str(civ)], civ)
        ok(len(stub.events("converted to paid")) == 1, "gate + session start + second convert: still one")

        civ3 = birth(tmp / "civ3")        # portal-side conversion: operator flips the record, no convert call
        run([sys.executable, "tools/apply_trial_profile.py", "apply", "--root", str(civ3)], civ3,
            {**seams, "TRIAL_START": old})
        rec = json.loads((civ3 / "config/trial.json").read_text())
        rec.update({"trial": False, "converted_at": "2026-10-05T09:00:00Z"})
        (civ3 / "config/trial.json").write_text(json.dumps(rec))
        n, n_exp = len(stub.events("converted to paid")), len(stub.events("trial expired"))
        run([sys.executable, "tools/partner_notify.py", "tick"], civ3)
        ok(len(stub.events("converted to paid")) == n + 1 and len(stub.events("trial expired")) == n_exp,
           "record flipped elsewhere -> watchdog tick reports 'converted' (not 'expired')")

        print("[6] health")
        for _ in range(2):
            send(civ, "--event", "health", "--kind", "repeated_failures", "--summary", "Telegram replies failed 5x")
        hp = stub.events("health problem: repeated failures")
        ok(len(hp) == 1 and "Telegram replies failed" in hp[0]["text"], "self-reported health: one per kind per day")
        send(civ, "--event", "health", "--kind", "disk_full", "--summary", "disk 98%")
        ok(len(stub.events("health problem: disk full")) == 1, "a different kind is its own email")
        dead = f"http://127.0.0.1:{closed_port()}/anthropic"
        probe_env = {"ANTHROPIC_BASE_URL": dead, "PARTNER_HEALTH_PROBE_SECS": "0"}
        for i in range(4):
            run([sys.executable, "tools/partner_notify.py", "tick"], civ, probe_env)
            if i == 1:
                ok(not stub.events("model unreachable"), "router down 2 checks: no alert yet")
        mu = stub.events("model unreachable")
        ok(len(mu) == 1 and "127.0.0.1" in mu[0]["text"], "router down 3+ checks -> exactly one alert")
        run([sys.executable, "tools/partner_notify.py", "tick"], civ, {**probe_env, "ANTHROPIC_BASE_URL": stub.url})
        h = json.loads((civ / "memories/partner-notifications/health.json").read_text())
        ok(h["consecutive_failures"] == 0 and h["last_result"] == "reachable", "router back: failure count reset")
        wd = (civ / "tools/watchdog.sh").read_text()
        ok("    partner_check\n" in wd and 'partner_health "crash_loop_' in wd and 'partner_health "aiciv_down"' in wd,
           "watchdog wires tick + crash-loop + Claude-down health notices")

        print("[7] no email capability: queue, say so, send later")
        q = birth(tmp / "q")
        noemail = {"AGENTMAIL_API_KEY": ""}
        n = len(stub.posts)
        r = send(q, "--event", "wow_shipped", "--build", "1", "--summary", "site", extra=noemail)
        outbox = list((q / "memories/partner-notifications/outbox").glob("*.json"))
        ok(r.returncode == 0 and r.stdout.startswith("QUEUED") and "no AgentMail key" in r.stdout
           and len(outbox) == 1 and len(stub.posts) == n, "no email -> queued once to the outbox, exit 0", r.stdout)
        s = hook(q, "session_start.py", "SessionStart", noemail)
        ok("[Partner notifications]" in s.stdout and "no email capability is provisioned" in s.stdout,
           "session start status says so", s.stdout[-400:])
        st = json.loads(run([sys.executable, "tools/partner_notify.py", "status", "--json"], q, noemail).stdout)
        ok(st["queued"] == 2 and not st["email_ready"] and st["recipients"] == [PARTNER],
           "status: 2 queued (build + born), email not ready", json.dumps(st))
        run([sys.executable, "tools/partner_notify.py", "tick"], q)       # email provisioned now
        ok(len(stub.posts) == n + 2 and len([p for p in stub.posts[n:] if "WOW build #1" in p["subject"]]) == 1
           and not list((q / "memories/partner-notifications/outbox").glob("*.json")),
           "once email exists: tick sends each queued notice once, outbox empty")
        run([sys.executable, "tools/partner_notify.py", "flush"], q)
        ok(len(stub.posts) == n + 2, "flush again: nothing re-sent")

        print("[8] provider failure: retried, never duplicated, never fails the trigger")
        stub.fail = 1
        n = len(stub.posts)
        r = send(civ, "--event", "wow_shipped", "--build", "3", "--summary", "Menu planner")
        ok(r.returncode == 0 and r.stdout.startswith("QUEUED") and len(stub.posts) == n, "500 from provider -> queued")
        run([sys.executable, "tools/partner_notify.py", "flush"], civ)
        run([sys.executable, "tools/partner_notify.py", "flush"], civ)
        ok(len(stub.events("WOW build #3")) == 1, "retry sends it exactly once")
        r = send(civ, "--event", "health", "--kind", "x", "--summary", "y",
                 extra={"AGENTMAIL_API_BASE": f"http://127.0.0.1:{closed_port()}"})
        ok(r.returncode == 0 and r.stdout.startswith("QUEUED"), "provider unreachable -> exit 0, queued")

        print("[9] delivery-engine alerts queued by a client site")
        site_logs = civ / "apps/sams-bakery/logs"
        site_logs.mkdir(parents=True)
        (site_logs / "partner-outbox.jsonl").write_text("".join(json.dumps(
            {"key": f"alert:sams-bakery:lead:{i}", "to": [PARTNER], "subject": f"[yourAICIV] Sams Bakery - new lead {i}",
             "text": f"New lead: Visitor {i}"}) + "\n" for i in range(2)))
        n = len(stub.posts)
        run([sys.executable, "tools/partner_notify.py", "flush"], civ)
        run([sys.executable, "tools/partner_notify.py", "flush"], civ)
        al = stub.events("Sams Bakery - new lead")
        ok(len(al) == 2 and len(stub.posts) >= n + 2 and not (site_logs / "partner-outbox.jsonl").exists(),
           "site outbox: each alert sent once from the AiCIV inbox, file consumed")

        print("[10] every email went to the partner, and only the partner")
        ok(stub.posts and all(p["to"] == PARTNER for p in stub.posts),
           f"{len(stub.posts)} emails, all to {PARTNER}")
    finally:
        stub.srv.shutdown()
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{PASSES} passed, {len(FAILS)} failed")
    for f in FAILS:
        print(f"  FAILED: {f}")
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
