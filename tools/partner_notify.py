#!/usr/bin/env python3
"""
partner_notify.py -- tell the reseller partner what is happening with their client.

The method lives in .claude/skills/partner-notifications/SKILL.md. This file is
the thin sender that skill (and the hooks / watchdog) call.

WHO:   config/partner.json "notify_emails" (tools/partner_profile.py), or
       $PARTNER_NOTIFY_EMAILS. No addresses = nothing is ever sent (plain AiCIV).
HOW:   this AiCIV's own AgentMail inbox (skill: agentmail-mastery). If no email
       capability is provisioned the message waits in the OUTBOX
       (memories/partner-notifications/outbox/) and every status says so; it is
       sent by the next `flush` once email exists. Nothing here ever fails the
       action that triggered it: every command exits 0 unless its arguments are wrong.
ONCE:  every event has a key (born, first_conversation, wow_shipped:<n>, ...).
       A key is claimed atomically before anything is queued, so the AiCIV, the
       hooks and the watchdog can all report the same event and the partner
       still gets exactly one email.

EVENTS
  born                 AiCIV born and awake (auto: first session of a real birth)
  first_conversation   first real conversation with the human done (--summary: goals, one line)
  wow_shipped          a WOW build shipped (--build N --summary what --link URL)
  trial_ending         trial day 6+: expires tomorrow (auto)
  trial_expired        trial ended; payment link shown to the human (auto)
  converted            trial converted to paid (auto + operator convert)
  health               a problem the AiCIV detects about itself (--kind K --summary what);
                       at most one per kind per day
  business_alert       a delivery-engine alert (new lead / order / booking / affiliate
                       application), normally imported from apps/<slug>/logs/partner-outbox.jsonl

CLI
  partner_notify.py send --event E [--summary S] [--link URL] [--build N] [--kind K] [--no-deliver]
  partner_notify.py sweep [--no-deliver]   # report every event visible on disk (idempotent)
  partner_notify.py flush                  # send what waits in the outbox (+ app outboxes)
  partner_notify.py tick                   # sweep + model/router probe + flush (tools/watchdog.sh)
  partner_notify.py status [--json]        # recipients, transport, queued / sent counts

Environment (tests and provisioning):
  PARTNER_NOTIFY_EMAILS   replaces config/partner.json notify_emails
  PARTNER_NOTIFY_DISABLE  "1" = do nothing at all (quiet no-op)
  PARTNER_NOTIFY_SYNC     "1" = hooks run the sweep inline instead of in the background
  AGENTMAIL_API_KEY / AGENTMAIL_INBOX / AGENTMAIL_ENV_FILE / AGENTMAIL_API_BASE
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import partner_profile  # noqa: E402  (sibling tool)

STATE_DIR = "memories/partner-notifications"
EVENTS = ("born", "first_conversation", "wow_shipped", "trial_ending", "trial_expired",
          "converted", "health", "business_alert")
TITLES = {
    "born": "is born and awake",
    "first_conversation": "first conversation done",
    "wow_shipped": "WOW build shipped",
    "trial_ending": "trial expires tomorrow",
    "trial_expired": "trial expired",
    "converted": "converted to paid",
    "health": "health problem",
    "business_alert": "business alert",
}
# A disk marker must be this old before the sweep reports it, so the AiCIV's own
# richer report (sent the moment it writes the marker) always wins the key.
GRACE_SECS = int(os.environ.get("PARTNER_NOTIFY_GRACE_SECS", "600"))
KICK_THROTTLE_SECS = int(os.environ.get("PARTNER_NOTIFY_KICK_THROTTLE_SECS", "30"))
PROBE_EVERY_SECS = int(os.environ.get("PARTNER_HEALTH_PROBE_SECS", "300"))
PROBE_FAILS_BEFORE_ALERT = 3
HTTP_TIMEOUT = 10


# ── basics ───────────────────────────────────────────────────────────────────

def civ_root(explicit: str | Path | None = None) -> Path:
    for cand in (explicit, os.environ.get("CIV_ROOT"), os.environ.get("CLAUDE_PROJECT_DIR")):
        if cand and "${" not in str(cand):
            return Path(cand)
    return HERE.parent


def disabled() -> bool:
    return os.environ.get("PARTNER_NOTIFY_DISABLE", "").strip() in ("1", "true", "yes")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime | None = None) -> str:
    return (dt or utcnow()).astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def state_dir(root: Path) -> Path:
    d = root / STATE_DIR
    for sub in ("keys", "outbox", "sent"):
        (d / sub).mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    return d


def _json(path: Path, default=None):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def _write_json(path: Path, obj) -> None:
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _real(v) -> str:
    v = str(v or "").strip()
    return "" if (not v or "${" in v or v.lower() in ("yourname", "your name", "null", "none")) else v


# ── who is this about ────────────────────────────────────────────────────────

def identity(root: Path) -> dict:
    ident = _json(root / ".aiciv-identity.json", {}) or {}
    prof = _json(root / "memories/identity/human-profile.json", {}) or {}
    civ = _real(os.environ.get("CIV_NAME")) or _real(ident.get("civ_name"))
    human = (_real(prof.get("human_name")) or _real(prof.get("name"))
             or _real(ident.get("human_name")) or _real(os.environ.get("HUMAN_NAME")))
    return {"civ": civ, "human": human, "profile": prof}


def display_name(root: Path) -> str:
    who = identity(root)
    if who["human"] and who["civ"]:
        return f"{who['human']} ({who['civ']})"
    return who["human"] or who["civ"] or socket.gethostname()


def is_real_birth(root: Path) -> bool:
    """A provisioned civ, not the template source tree."""
    return bool(identity(root)["civ"]) or (root / "memories/identity/seed-conversation.md").exists()


# ── transport: this AiCIV's AgentMail inbox ──────────────────────────────────

def _env_file_values(path: Path) -> dict:
    out = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.replace("export ", "").strip()
            out[k] = v.strip().strip("'\"")
    except OSError:
        pass
    return out


def agentmail_config(root: Path) -> tuple[dict | None, str]:
    """({key, inbox, base}, "") or (None, why-not). Never prints the key."""
    vals: dict = {}
    files = [os.environ.get("AGENTMAIL_ENV_FILE", ""), str(root / "civ/config/agentmail.env"),
             str(root / "config/agentmail.env"), str(root / ".env")]
    for f in files:
        if f:
            for k, v in _env_file_values(Path(f)).items():
                vals.setdefault(k, v)
    for k in ("AGENTMAIL_API_KEY", "AGENTMAIL_INBOX", "AGENTMAIL_INBOX_ID", "AGENTMAIL_ADDRESS"):
        if os.environ.get(k, "").strip():
            vals[k] = os.environ[k].strip()
        elif k in os.environ:                  # explicitly set empty = not provisioned
            vals.pop(k, None)
    key = _real(vals.get("AGENTMAIL_API_KEY"))
    if not key:
        return None, "no AgentMail key (AGENTMAIL_API_KEY / civ/config/agentmail.env)"
    base = os.environ.get("AGENTMAIL_API_BASE", "https://api.agentmail.to").rstrip("/")
    inbox = (_real(vals.get("AGENTMAIL_INBOX")) or _real(vals.get("AGENTMAIL_INBOX_ID"))
             or _real(vals.get("AGENTMAIL_ADDRESS")))
    if not inbox:
        for cand in (os.environ.get("CIV_EMAIL"), vals.get("CIV_EMAIL"),
                     (_json(root / ".aiciv-identity.json", {}) or {}).get("email")):
            if _real(cand).endswith("@agentmail.to"):
                inbox = _real(cand)
                break
    if not inbox:
        try:
            req = urllib.request.Request(f"{base}/v0/inboxes", headers={"Authorization": f"Bearer {key}"})
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
                data = json.loads(r.read() or b"{}")
            boxes = data.get("inboxes") or data.get("data") or []
            inbox = str((boxes[0] or {}).get("inbox_id") or (boxes[0] or {}).get("address") or "") if boxes else ""
        except Exception as e:  # noqa: BLE001
            return None, f"AgentMail inbox lookup failed ({type(e).__name__})"
    if not inbox:
        return None, "AgentMail key present but no inbox (set AGENTMAIL_INBOX)"
    return {"key": key, "inbox": inbox, "base": base}, ""


def agentmail_send(conf: dict, to: str, subject: str, text: str) -> str:
    """POST one message from this AiCIV's inbox. Returns the provider message id ("" if none)."""
    body = json.dumps({"to": to, "subject": subject, "text": text}).encode()
    req = urllib.request.Request(
        f"{conf['base']}/v0/inboxes/{conf['inbox']}/messages/send", data=body, method="POST",
        headers={"Authorization": f"Bearer {conf['key']}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as r:
        if r.status >= 300:
            raise RuntimeError(f"HTTP {r.status}")
        try:
            return str(json.loads(r.read() or b"{}").get("message_id") or "")
        except ValueError:
            return ""


# ── compose ──────────────────────────────────────────────────────────────────

def compose(root: Path, event: str, summary: str = "", link: str = "", build: str = "",
            kind: str = "", extra: dict | None = None) -> tuple[str, str]:
    prof = partner_profile.load(root)
    name = display_name(root)
    who = identity(root)
    title = TITLES.get(event, event)
    if event == "wow_shipped" and build:
        title = f"WOW build #{build} shipped"
    if event == "health" and kind:
        title = f"health problem: {kind.replace('_', ' ')}"
    if event == "business_alert" and extra and extra.get("title"):
        title = extra["title"]
    subject = f"[{prof['brand']}] {name} - {title}"
    lines = []
    head = {
        "born": f"{who['civ'] or 'A new AiCIV'} was just born for {who['human'] or 'its human'} and is awake.",
        "first_conversation": "The first real conversation with the human is done; the AiCIV knows their goals.",
        "wow_shipped": f"WOW build{(' #' + build) if build else ''} is shipped and in the human's hands.",
        "trial_ending": "The 7-day trial expires tomorrow.",
        "trial_expired": "The 7-day trial has expired. The human is being shown the payment link; "
                         "nothing they built is deleted.",
        "converted": "The client converted to paid. The trial gate is lifted.",
        "health": "The AiCIV detected a problem with itself.",
        "business_alert": "The client's business site just had activity.",
    }.get(event, "")
    if head:
        lines.append(head)
    if summary:
        lines += ["", summary.strip()]
    if link:
        lines += ["", f"Link: {link}"]
    for k, v in (extra or {}).items():
        if k != "title" and v:
            lines.append(f"{k.replace('_', ' ').capitalize()}: {v}")
    lines += ["", f"AiCIV: {who['civ'] or '-'}", f"Client: {who['human'] or '-'}", f"When: {iso()}", "",
              f"-- automated {prof['brand']} partner notice. One email per event; reply-to is the AiCIV's inbox."]
    return subject[:200], "\n".join(lines)


# ── queue + deliver ──────────────────────────────────────────────────────────

def _safe(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", key)[:120]


def claim(root: Path, key: str) -> bool:
    """Atomically claim an event key. False = already reported (exactly-once)."""
    p = state_dir(root) / "keys" / _safe(key)
    try:
        fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return False
    with os.fdopen(fd, "w") as fh:
        fh.write(iso() + "\n")
    return True


def enqueue(root: Path, key: str, event: str, to: list[str], subject: str, text: str) -> Path:
    d = state_dir(root)
    msg = {"key": key, "event": event, "to": to, "subject": subject, "text": text,
           "created_at": iso(), "attempts": 0, "delivered_to": [], "last_error": ""}
    p = d / "outbox" / f"{int(time.time() * 1000)}-{_safe(key)}.json"
    _write_json(p, msg)
    return p


class _Lock:
    def __init__(self, root: Path, wait: float = 20.0):
        self.path, self.wait, self.fh = state_dir(root) / ".flush.lock", wait, None

    def __enter__(self):
        self.fh = open(self.path, "w")
        end = time.time() + self.wait
        while True:
            try:
                fcntl.flock(self.fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return True
            except BlockingIOError:
                if time.time() >= end:
                    return False
                time.sleep(0.1)

    def __exit__(self, *exc):
        try:
            fcntl.flock(self.fh, fcntl.LOCK_UN)
        finally:
            self.fh.close()


def import_app_outboxes(root: Path) -> int:
    """Pull queued delivery-engine alerts (apps/<slug>/logs/partner-outbox.jsonl) into this outbox."""
    n = 0
    for f in sorted((root / "apps").glob("*/logs/partner-outbox.jsonl")):
        grab = f.with_name(f"partner-outbox.importing-{os.getpid()}.jsonl")
        try:
            f.rename(grab)
        except OSError:
            continue
        for line in grab.read_text().splitlines():
            try:
                m = json.loads(line)
            except ValueError:
                continue
            to = partner_profile.clean_emails(m.get("to") or []) or partner_profile.load(root)["notify_emails"]
            key = str(m.get("key") or f"alert:{f.parent.parent.name}:{m.get('created_at')}:{n}")
            if to and m.get("subject") and claim(root, key):
                enqueue(root, key, "business_alert", to, str(m["subject"]), str(m.get("text", "")))
                n += 1
        grab.unlink()
    return n


def flush(root: Path) -> dict:
    """Send everything waiting. Returns {"sent": n, "queued": n, "transport": ..., "error": ...}."""
    res = {"sent": 0, "queued": 0, "transport": "none", "error": ""}
    if disabled():
        return res
    d = state_dir(root)
    with _Lock(root) as got:
        if not got:
            res["error"] = "another flush is running"
            res["queued"] = len(list((d / "outbox").glob("*.json")))
            return res
        import_app_outboxes(root)
        pending = sorted((d / "outbox").glob("*.json"))
        conf, why = agentmail_config(root) if pending else (None, "")
        if conf:
            res["transport"] = f"agentmail:{conf['inbox']}"
        for p in pending:
            msg = _json(p)
            if not isinstance(msg, dict):
                continue
            if not conf:
                msg["last_error"] = why
                _write_json(p, msg)
                res["queued"] += 1
                continue
            msg["attempts"] = int(msg.get("attempts", 0)) + 1
            for to in msg.get("to", []):
                if to in msg["delivered_to"]:
                    continue
                try:
                    mid = agentmail_send(conf, to, msg["subject"], msg["text"])
                    msg["delivered_to"].append(to)
                    msg.setdefault("message_ids", {})[to] = mid
                except Exception as e:  # noqa: BLE001  (never raise to the caller)
                    code = getattr(e, "code", "")
                    msg["last_error"] = f"{type(e).__name__} {code}".strip()
            if set(msg.get("to", [])) <= set(msg["delivered_to"]):
                msg["sent_at"] = iso()
                _write_json(d / "sent" / p.name, msg)
                p.unlink()
                res["sent"] += 1
            else:
                _write_json(p, msg)
                res["queued"] += 1
        if not conf and why:
            res["error"] = why
    write_status(root, res)
    return res


def write_status(root: Path, last: dict | None = None) -> dict:
    d = state_dir(root)
    queued = len(list((d / "outbox").glob("*.json")))
    why = "" if agentmail_config_offline(root) else "no email capability provisioned (AgentMail)"
    st = {"updated_at": iso(), "recipients": partner_profile.load(root)["notify_emails"],
          "queued": queued, "sent": len(list((d / "sent").glob("*.json"))),
          "email_ready": not why, "why_not": why if queued else "",
          "last_flush": last or {}}
    _write_json(d / "status.json", st)
    return st


def agentmail_config_offline(root: Path) -> bool:
    """Is an AgentMail key provisioned? (no network)"""
    vals = {}
    for f in (os.environ.get("AGENTMAIL_ENV_FILE", ""), str(root / "civ/config/agentmail.env"),
              str(root / "config/agentmail.env"), str(root / ".env")):
        if f:
            vals.update({k: v for k, v in _env_file_values(Path(f)).items() if k not in vals})
    if "AGENTMAIL_API_KEY" in os.environ:
        return bool(_real(os.environ["AGENTMAIL_API_KEY"]))
    return bool(_real(vals.get("AGENTMAIL_API_KEY")))


def status_line(root: Path) -> str:
    """One line for the AiCIV's session status. Empty when there is nothing to say."""
    if disabled():
        return ""
    rcpt = partner_profile.load(root)["notify_emails"]
    if not rcpt:
        return ""
    d = root / STATE_DIR / "outbox"
    queued = len(list(d.glob("*.json"))) if d.exists() else 0
    if not queued:
        return ""
    if not agentmail_config_offline(root):
        return (f"[Partner notifications] {queued} waiting in {STATE_DIR}/outbox: no email capability "
                f"is provisioned yet (AgentMail). They send automatically once it is. "
                f"Partner: {', '.join(rcpt)}")
    return (f"[Partner notifications] {queued} waiting in {STATE_DIR}/outbox (last send failed; "
            f"retried every minute). Check: python3 tools/partner_notify.py status")


def notify(root: Path, event: str, summary: str = "", link: str = "", build: str = "", kind: str = "",
           key: str | None = None, deliver: bool = True, extra: dict | None = None) -> dict:
    """Report one event to the partner. Never raises. Returns {"result": ..., ...}."""
    try:
        if disabled():
            return {"result": "disabled"}
        if event not in EVENTS:
            return {"result": "error", "error": f"unknown event {event!r}; one of {', '.join(EVENTS)}"}
        to = partner_profile.load(root)["notify_emails"]
        if not to:
            return {"result": "no-partner", "detail": "no notify_emails in config/partner.json"}
        if key is None:
            key = {"wow_shipped": f"wow_shipped:{build or 'x'}",
                   "health": f"health:{kind or 'general'}:{utcnow().strftime('%Y-%m-%d')}",
                   "business_alert": f"alert:{iso()}:{os.getpid()}:{time.time_ns()}"}.get(event, event)
        if not claim(root, key):
            return {"result": "duplicate", "key": key}
        subject, text = compose(root, event, summary, link, build, kind, extra)
        p = enqueue(root, key, event, to, subject, text)
        out = {"result": "queued", "key": key, "to": to, "subject": subject, "outbox": str(p)}
        if deliver:
            f = flush(root)
            if f.get("sent") and not p.exists():
                out["result"] = "sent"
            elif f.get("error"):
                out["why_queued"] = f["error"]
        else:
            write_status(root)
        return out
    except Exception as e:  # noqa: BLE001  (a notification must never break its trigger)
        return {"result": "error", "error": f"{type(e).__name__}: {e}"}


# ── what the disk says happened (sweep) ──────────────────────────────────────

def _old_enough(p: Path) -> bool:
    try:
        return time.time() - p.stat().st_mtime >= GRACE_SECS
    except OSError:
        return False


def _receipt(p: Path) -> dict:
    out = {}
    try:
        for line in p.read_text().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def trial_events(root: Path) -> list[tuple]:
    try:
        import trial_state  # sibling tool
    except Exception:  # noqa: BLE001
        return []
    ev = []
    rec_path, _rule = trial_state.record_path(root)
    raw = _json(rec_path) or _json(trial_state.trial_path(root))
    if isinstance(raw, dict) and raw.get("trial") is False and raw.get("converted_at"):
        ev.append(("converted", f"Converted at {raw['converted_at']}.", "", {}))
        return ev
    rec = trial_state.load(root)
    if not rec:
        return ev
    st = trial_state.compute(rec)
    if st["expired"]:
        ev.append(("trial_expired", f"Expired at {st['expires_at']}.", "",
                   {"payment_link_shown": st.get("payment_url", "")}))
    elif st["day"] >= 6:
        ev.append(("trial_ending", f"Day {st['day']} of 7; the trial ends {st['expires_at']} "
                                   f"({st['days_left']} day{'s' if st['days_left'] != 1 else ''} left).", "", {}))
    return ev


def sweep(root: Path, deliver: bool = True) -> list[dict]:
    """Report every event visible on disk. Idempotent: each key is sent once, ever."""
    if disabled() or not partner_profile.load(root)["notify_emails"]:
        return []
    found: list[tuple] = []           # (event, summary, link, extra, build)
    if is_real_birth(root):
        found.append(("born", "", "", {}, ""))
    ident = root / "memories/identity"
    for marker in (ident / ".identity-interview-complete", ident / ".evolution-done"):
        if marker.exists() and _old_enough(marker):
            goals = identity(root)["profile"].get("goals") or []
            summ = ("Goals: " + "; ".join(str(g) for g in goals[:5])) if goals else ""
            found.append(("first_conversation", summ, "", {}, ""))
            break
    for ev_dir in sorted(ident.glob("build-*-ship-evidence")):
        m = re.match(r"build-(\d+)-ship-evidence$", ev_dir.name)
        rc = ev_dir / "receipt.txt"
        if m and rc.exists() and _old_enough(rc):
            r = _receipt(rc)
            what = r.get("build_name") or r.get("title") or r.get("first_shipped_artifact_path", "")
            link = r.get("link") or r.get("url") or r.get("public_url") or ""
            found.append(("wow_shipped", f"What: {what}" if what else "", link, {}, m.group(1)))
    for ev, summ, link, extra in trial_events(root):
        found.append((ev, summ, link, extra, ""))
    out = []
    for ev, summ, link, extra, build in found:
        key = f"wow_shipped:{build}" if ev == "wow_shipped" else ev
        if (state_dir(root) / "keys" / _safe(key)).exists():
            continue
        out.append(notify(root, ev, summ, link, build=build, key=key, deliver=False, extra=extra))
    if deliver and (out or list((state_dir(root) / "outbox").glob("*.json"))):
        flush(root)
    return out


def kick(root: Path) -> None:
    """For hooks: run the sweep without slowing the hook (background, throttled, silent)."""
    try:
        if disabled() or not partner_profile.load(root)["notify_emails"]:
            return
        stamp = state_dir(root) / ".last-kick"
        try:
            if time.time() - stamp.stat().st_mtime < KICK_THROTTLE_SECS:
                return
        except OSError:
            pass
        stamp.touch()
        if os.environ.get("PARTNER_NOTIFY_SYNC", "").strip() == "1":
            sweep(root)
            return
        subprocess.Popen([sys.executable, str(HERE / "partner_notify.py"), "sweep", "--root", str(root)],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
    except Exception:  # noqa: BLE001
        pass


# ── self-health probe (watchdog tick) ────────────────────────────────────────

def model_base_url(root: Path) -> str:
    v = os.environ.get("ANTHROPIC_BASE_URL", "").strip()
    if not v:
        s = _json(root / ".claude/settings.json", {}) or {}
        v = str((s.get("env") or {}).get("ANTHROPIC_BASE_URL") or "").strip()
    return "" if "${" in v else v


def probe_model(root: Path) -> dict | None:
    """Is this AiCIV's model router reachable? Only probed when a router URL is configured.
    Any HTTP answer below 500 = reachable (no key is sent). Alerts after 3 misses in a row."""
    base = model_base_url(root)
    if not base:
        return None
    hp = state_dir(root) / "health.json"
    h = _json(hp, {}) or {}
    if time.time() - float(h.get("last_probe", 0)) < PROBE_EVERY_SECS:
        return None
    ok, detail = True, ""
    try:
        with urllib.request.urlopen(urllib.request.Request(base, method="GET"), timeout=HTTP_TIMEOUT):
            pass
    except urllib.error.HTTPError as e:
        ok, detail = e.code < 500, f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001
        ok, detail = False, type(e).__name__
    h["last_probe"] = time.time()
    h["consecutive_failures"] = 0 if ok else int(h.get("consecutive_failures", 0)) + 1
    h["last_result"] = "reachable" if ok else f"unreachable ({detail})"
    _write_json(hp, h)
    if h["consecutive_failures"] == PROBE_FAILS_BEFORE_ALERT:
        host = re.sub(r"^https?://([^/]+).*$", r"\1", base)
        return notify(root, "health", f"Cannot reach its model router ({host}): {detail}, "
                                      f"{PROBE_FAILS_BEFORE_ALERT} checks in a row. The AiCIV cannot think "
                                      f"until this is fixed.", kind="model_unreachable", deliver=False)
    return None


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("send")
    s.add_argument("--event", required=True, choices=EVENTS)
    s.add_argument("--summary", default="")
    s.add_argument("--link", default="")
    s.add_argument("--build", default="")
    s.add_argument("--kind", default="")
    s.add_argument("--no-deliver", action="store_true")
    for name in ("sweep", "flush", "tick", "status"):
        sp = sub.add_parser(name)
        sp.add_argument("--root", default=None)
        if name == "sweep":
            sp.add_argument("--no-deliver", action="store_true")
        if name == "status":
            sp.add_argument("--json", action="store_true")
    s.add_argument("--root", default=None)
    a = ap.parse_args(argv)
    root = civ_root(a.root)

    if a.cmd == "send":
        r = notify(root, a.event, a.summary, a.link, a.build, a.kind, deliver=not a.no_deliver)
        line = {"sent": "SENT", "queued": "QUEUED", "duplicate": "ALREADY REPORTED",
                "no-partner": "NO PARTNER", "disabled": "DISABLED"}.get(r["result"], "ERROR")
        extra = r.get("why_queued") or r.get("error") or r.get("detail") or ""
        print(f"{line}: {a.event} -> {', '.join(r.get('to', [])) or '-'}" + (f" ({extra})" if extra else ""))
        return 0
    if a.cmd == "sweep":
        for r in sweep(root, deliver=not a.no_deliver):
            print(json.dumps(r))
        return 0
    if a.cmd == "flush":
        print(json.dumps(flush(root)))
        return 0
    if a.cmd == "tick":
        try:
            sweep(root, deliver=False)
            probe_model(root)
            if list((state_dir(root) / "outbox").glob("*.json")) or list((root / "apps").glob("*/logs/partner-outbox.jsonl")):
                flush(root)
        except Exception as e:  # noqa: BLE001
            print(f"partner_notify tick: {type(e).__name__}: {e}", file=sys.stderr)
        return 0
    st = write_status(root)
    if a.json:
        print(json.dumps(st, indent=2))
    else:
        print(f"recipients: {', '.join(st['recipients']) or '(none: nothing is sent)'}")
        print(f"email: {'AgentMail key provisioned' if st['email_ready'] else 'NOT provisioned (queued to outbox)'}")
        print(f"queued: {st['queued']}   sent: {st['sent']}")
        line = status_line(root)
        if line:
            print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
