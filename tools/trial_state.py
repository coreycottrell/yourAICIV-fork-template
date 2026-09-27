#!/usr/bin/env python3
"""
trial_state.py — the reference implementation of the SHARED TRIAL CONTRACT.

The fork-template (this repo) and the yourAICIV React portal BOTH honor this
contract. This file is the single source for the computation so the two sides
cannot drift; the portal backend can import `compute()` directly or port the
formula below line for line.

CONTRACT
--------
File: <civ_root>/config/trial.json, written ONCE at birth by the trial flavor:

    {"trial": true,
     "started_at":   "<ISO8601 UTC>",
     "duration_days": 7,
     "expires_at":   "<ISO8601 UTC>",
     "payment_url":  "https://buy.stripe.com/5kQeVe8Xe9D53GZdLb1Fe06",
     "brand":        "yourAICIV",
     "reseller":     "Travis Morehead",
     "model":        "MiniMax-M3"}

File absent, unreadable, or "trial": false  =>  NOT a trial  =>  no gating anywhere.

WHERE THE RECORD IS READ (one rule, shared with the portal)
    1. $TRIAL_CONFIG_PATH, if set. Production sets it to the OPERATOR COPY,
       /etc/aiciv/trial.json: root-owned 0644, outside the civ tree, so neither
       the AiCIV nor anything it runs can rewrite it (apply --operator-copy).
    2. else the TRIAL_CONFIG_PATH that birth recorded in .claude/settings.json
       "env" (so hooks and tools agree even if the variable is not exported).
    3. else <civ_root>/config/trial.json, civ_root = $CIV_ROOT (standard
       container: /home/aiciv), else $CLAUDE_PROJECT_DIR, else this repo.
`trial_state.py where` prints the resolved path and which rule chose it.
Writes (birth, convert) always go to <civ_root>/config/trial.json; the operator
copy is published only by tools/apply_trial_profile.py --operator-copy.

brand / reseller / payment_url are copied at birth from the partner profile
(config/partner.json, see tools/partner_profile.py). The values above are this
distribution's (yourAICIV). A --payment-url / $TRIAL_PAYMENT_URL override wins.

Portal GET /api/trial shape (exactly what `compute()` returns):

    {"trial": bool, "day": int (1..7), "days_left": int, "expires_at": str,
     "expired": bool, "payment_url": str}

FORMULA (UTC throughout)
------------------------
    expired   = now >= expires_at
    day       = clamp(floor((now - started_at) / 1 day) + 1, 1, duration_days)
    days_left = 0 if expired else ceil((expires_at - now) / 1 day)
Invariant while active: day + days_left == duration_days + 1
(Day 1 -> 7 days left ... Day 7 -> 1 day left; expired -> day 7, 0 left).

A NOT-a-trial file yields {"trial": false, "day": 0, "days_left": 0,
"expires_at": "", "expired": false, "payment_url": ""} — nothing gates.

CLI
---
    trial_state.py write   [--root DIR] [--start ISO] [--days 7] [--payment-url URL] [--force]
    trial_state.py status  [--root DIR] [--now ISO]          # prints the /api/trial JSON
    trial_state.py note    [--root DIR] [--now ISO]          # prints the human-facing line
    trial_state.py convert [--root DIR]                      # sets "trial": false (operator)
    trial_state.py where   [--root DIR]                      # the resolved record path + rule

`write` refuses to overwrite an existing trial.json unless --force: the trial
clock is set ONCE at birth and a re-run of setup must not restart it.
Nothing in this tool ever deletes a file.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Partner-neutral fallbacks. The real values come from config/partner.json
# (tools/partner_profile.py) at birth and are then frozen into config/trial.json.
DEFAULT_PAYMENT_URL = ""
DEFAULT_BRAND = "AiCIV"
DEFAULT_RESELLER = ""
DEFAULT_MODEL = "MiniMax-M3"
DEFAULT_DURATION_DAYS = 7
DAY_SECONDS = 86400

NOT_A_TRIAL = {
    "trial": False,
    "day": 0,
    "days_left": 0,
    "expires_at": "",
    "expired": False,
    "payment_url": "",
}


# ── root + file resolution ───────────────────────────────────────────────────

def civ_root(explicit: str | None = None) -> Path:
    """Civ root: --root, else $CIV_ROOT, else $CLAUDE_PROJECT_DIR, else this repo."""
    for cand in (explicit, os.environ.get("CIV_ROOT"), os.environ.get("CLAUDE_PROJECT_DIR")):
        if cand and "${" not in cand:
            return Path(cand)
    return Path(__file__).resolve().parent.parent


CANONICAL_OPERATOR_COPY = "/etc/aiciv/trial.json"


def trial_path(root: Path) -> Path:
    """The civ copy: where birth writes the record (and what `convert` flips)."""
    return root / "config" / "trial.json"


def configured_record_path(root: Path) -> tuple[str, str]:
    """(path, rule) for rules 1-2: $TRIAL_CONFIG_PATH, else the value birth wrote into settings.json env."""
    env = os.environ.get("TRIAL_CONFIG_PATH", "").strip()
    if env:
        return env, "TRIAL_CONFIG_PATH"
    try:
        s = json.loads((root / ".claude" / "settings.json").read_text())
        v = str(((s.get("env") or {}).get("TRIAL_CONFIG_PATH")) or "").strip()
        if v and "${" not in v:
            return v, ".claude/settings.json env.TRIAL_CONFIG_PATH"
    except (OSError, ValueError, AttributeError):
        pass
    return "", ""


def record_path(root: Path) -> tuple[Path, str]:
    """Where the trial record is READ from (see WHERE THE RECORD IS READ)."""
    p, rule = configured_record_path(root)
    if p:
        return Path(p), rule
    return trial_path(root), "civ copy (<civ_root>/config/trial.json)"


def profile_path(root: Path) -> Path:
    """Written by tools/apply_trial_profile.py; marks an M3-locked trial-profile civ."""
    return root / "config" / "model_profile.json"


def profile_locked(root: Path) -> bool:
    try:
        d = json.loads(profile_path(root).read_text())
    except (OSError, ValueError):
        return False
    return isinstance(d, dict) and d.get("locked") is True


# ── time helpers ─────────────────────────────────────────────────────────────

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> datetime:
    s = s.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── the contract ─────────────────────────────────────────────────────────────

def build_record(started_at: datetime,
                 duration_days: int = DEFAULT_DURATION_DAYS,
                 payment_url: str = DEFAULT_PAYMENT_URL,
                 brand: str = DEFAULT_BRAND,
                 reseller: str = DEFAULT_RESELLER,
                 model: str = DEFAULT_MODEL) -> dict:
    """The exact trial.json record. Key order matches the contract."""
    started_at = started_at.astimezone(timezone.utc).replace(microsecond=0)
    return {
        "trial": True,
        "started_at": iso(started_at),
        "duration_days": int(duration_days),
        "expires_at": iso(started_at + timedelta(days=int(duration_days))),
        "payment_url": payment_url,
        "brand": brand,
        "reseller": reseller,
        "model": model,
    }


def load(root: Path) -> dict | None:
    """Return the trial record if this civ IS in trial, else None (no gating).

    Fails OPEN to "not a trial" only when the file is absent or trial is false.
    A file that exists with "trial": true but is malformed in its dates is
    treated as EXPIRED by compute() (fail closed for a declared trial), so a
    corrupted clock can never silently grant unlimited free use.
    """
    p, rule = record_path(root)
    try:
        raw = json.loads(p.read_text())
    except FileNotFoundError:
        if p != trial_path(root):
            # A configured record (the operator copy) is missing: not published, or not mounted.
            # On a trial-profile civ that must never read as "not a trial": fail CLOSED, loudly.
            if profile_locked(root):
                print(f"trial_state: WARNING {p} ({rule}) missing on a trial-profile civ; failing closed",
                      file=sys.stderr)
                return {"trial": True, "_corrupt": True}
            print(f"trial_state: WARNING {p} ({rule}) missing; reading {trial_path(root)}", file=sys.stderr)
            try:
                raw = json.loads(trial_path(root).read_text())
            except (OSError, ValueError):
                return None
            return raw if isinstance(raw, dict) and raw.get("trial") is True else None
        return None
    except (OSError, ValueError):
        # Unreadable/corrupt file. If this civ was born with the trial profile
        # (config/model_profile.json locked to trial-m3), the file DID declare a
        # trial -> fail CLOSED (compute() will report expired). Otherwise it is
        # not a trial civ and the contract says: no gating.
        if profile_locked(root):
            print(f"trial_state: WARNING corrupt {p} on a trial-profile civ; failing closed",
                  file=sys.stderr)
            return {"trial": True, "_corrupt": True}
        print(f"trial_state: WARNING unreadable {p}; treating as not-a-trial", file=sys.stderr)
        return None
    if not isinstance(raw, dict) or raw.get("trial") is not True:
        return None
    return raw


def compute(record: dict | None, now: datetime | None = None) -> dict:
    """Pure function: trial record (or None) -> the /api/trial response dict."""
    if not record or record.get("trial") is not True:
        return dict(NOT_A_TRIAL)
    now = (now or utcnow()).astimezone(timezone.utc)
    duration = int(record.get("duration_days") or DEFAULT_DURATION_DAYS)
    payment_url = str(record.get("payment_url") or DEFAULT_PAYMENT_URL)
    try:
        started = parse_iso(str(record["started_at"]))
        expires = parse_iso(str(record["expires_at"]))
    except (KeyError, ValueError, TypeError):
        # Declared trial with a broken clock -> fail CLOSED (treat as expired).
        return {"trial": True, "day": duration, "days_left": 0,
                "expires_at": str(record.get("expires_at", "")),
                "expired": True, "payment_url": payment_url}
    expired = now >= expires
    elapsed = (now - started).total_seconds()
    day = int(math.floor(elapsed / DAY_SECONDS)) + 1
    day = max(1, min(duration, day))
    if expired:
        day, days_left = duration, 0
    else:
        days_left = int(math.ceil((expires - now).total_seconds() / DAY_SECONDS))
    return {
        "trial": True,
        "day": day,
        "days_left": days_left,
        "expires_at": iso(expires),
        "expired": expired,
        "payment_url": payment_url,
    }


def state(root: Path | None = None, now: datetime | None = None) -> dict:
    return compute(load(root or civ_root()), now)


def human_note(st: dict, human_name: str = "", brand: str | None = None) -> str:
    """The one line the AiCIV (and the portal) show a human."""
    if not st.get("trial"):
        return ""
    brand = brand or DEFAULT_BRAND
    if st["expired"]:
        lead = f"{human_name}, our" if human_name else "Our"
        return (f"{lead} 7-day {brand} trial has ended. Everything we built together is "
                f"saved exactly as it was: your work, your files, and everything I learned "
                f"about you. The moment you subscribe it all comes back and we pick up "
                f"where we left off: {st['payment_url']}")
    return (f"Day {st['day']} of 7 of your trial with {brand} "
            f"({st['days_left']} day{'s' if st['days_left'] != 1 else ''} left, "
            f"ends {st['expires_at']}).")


# ── writes (atomic, never delete) ────────────────────────────────────────────

def _atomic_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    with os.fdopen(fd, "w") as fh:
        json.dump(obj, fh, indent=2)
        fh.write("\n")
    os.chmod(tmp, 0o644)
    os.replace(tmp, path)


def partner(root: Path) -> dict:
    """brand / reseller / payment_url from config/partner.json (generic if absent)."""
    try:
        here = str(Path(__file__).resolve().parent)
        if here not in sys.path:
            sys.path.insert(0, here)
        import partner_profile  # noqa: E402  (sibling tool)
        return partner_profile.load(root)
    except ImportError:
        return {"brand": DEFAULT_BRAND, "reseller": DEFAULT_RESELLER, "payment_url": DEFAULT_PAYMENT_URL}


def write(root: Path, started_at: datetime | None = None, duration_days: int = DEFAULT_DURATION_DAYS,
          payment_url: str | None = None, force: bool = False,
          model: str = DEFAULT_MODEL) -> dict:
    p = trial_path(root)
    if p.exists() and not force:
        raise FileExistsError(f"{p} already exists — the trial clock is set once at birth. "
                              f"Use --force only to deliberately reset it.")
    prof = partner(root)
    payment_url = (payment_url or prof["payment_url"] or "").strip()
    if not payment_url.startswith("https://"):
        raise ValueError("no payment link: a trial must tell the human where to subscribe. "
                         "Set payment_url in config/partner.json or pass --payment-url / "
                         "$TRIAL_PAYMENT_URL (https://...).")
    rec = build_record(started_at or utcnow(), duration_days, payment_url,
                       brand=prof["brand"], reseller=prof["reseller"], model=model)
    _atomic_write_json(p, rec)
    return rec


def convert(root: Path) -> dict:
    """Operator conversion: keep the whole record for audit, flip trial -> false."""
    p = trial_path(root)
    raw = json.loads(p.read_text())
    raw["trial"] = False
    raw["converted_at"] = iso(utcnow())
    _atomic_write_json(p, raw)
    return raw


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("write", "status", "note", "convert", "where"):
        sp = sub.add_parser(name)
        sp.add_argument("--root", default=None)
        if name in ("status", "note"):
            sp.add_argument("--now", default=None, help="ISO8601 override (testing)")
        if name == "note":
            sp.add_argument("--human", default="")
        if name == "write":
            sp.add_argument("--start", default=None, help="ISO8601 UTC; default now")
            sp.add_argument("--days", type=int, default=DEFAULT_DURATION_DAYS)
            sp.add_argument("--payment-url", default=os.environ.get("TRIAL_PAYMENT_URL") or None,
                            help="default: payment_url from config/partner.json")
            sp.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    root = civ_root(a.root)

    if a.cmd == "write":
        try:
            rec = write(root, parse_iso(a.start) if a.start else None, a.days, a.payment_url, a.force)
        except (FileExistsError, ValueError) as e:
            print(f"REFUSED: {e}", file=sys.stderr)
            return 3
        print(json.dumps(rec, indent=2))
        return 0
    if a.cmd == "convert":
        if not trial_path(root).exists():
            print("nothing to convert: no config/trial.json (not a trial)", file=sys.stderr)
            return 1
        print(json.dumps(convert(root), indent=2))
        return 0
    if a.cmd == "where":
        p, rule = record_path(root)
        print(json.dumps({"path": str(p), "rule": rule, "exists": p.exists(),
                          "civ_copy": str(trial_path(root)),
                          "canonical_operator_copy": CANONICAL_OPERATOR_COPY}))
        return 0
    now = parse_iso(a.now) if a.now else None
    st = compute(load(root), now)
    if a.cmd == "status":
        print(json.dumps(st))
        return 0
    print(human_note(st, a.human, (load(root) or {}).get("brand")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
