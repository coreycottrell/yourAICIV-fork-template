#!/usr/bin/env python3
"""
model_switch_trigger.py — usage-limit watcher that auto-flips the inference
substrate to the peer rail.

Spec: .claude/skills/multi-model-inference-mastery/SKILL.md §4 (the
auto-trigger). HONEST STAMP: the mechanism is PROVEN K=1 in the origin civ
(2026-07-01, synthetic-injection proof); THIS script is a NET-NEW
implementation for the aiciv-fork-template (origin did not ship its scripts
upstream). Walk-tested here via synthetic injection; UNVALIDATED against a
real usage-limit event in any fork.

Per tick (--once), scans (newest-first, bounded tails):
  1. newest session JSONL under ~/.claude/projects/*/           (session runtime)
  2. logs/*.log under the civ root                               (orchestrator logs)
Regex-matches usage-limit strings (case-insensitive):
  - "You've hit your weekly limit"        (canonical Anthropic string)
  - "usage_limit_reached" / "usage limit exceeded"
  - "hit your weekly limit" / "weekly usage limit"
  - "weekly limit" co-occurring with "reset" within 80 chars

On detect:
  - invokes ./tools/model_switch.sh peer --reason "usage-limit-auto:<snippet>"
  - writes lock data/state/model_switch_trigger.lock (idempotency: second fire
    while mode==peer-for-usage-limit returns detect-suppressed-locked)
  - appends an audit row to logs/model_switch_trigger_ledger.jsonl
  - best-effort human-notify is YOUR civ's push channel — wire it where marked

Manual flip-back to default clears the semantic lock on the next tick.
Off-switch: touch /tmp/model-switch-trigger.disable

CRON (arm consciously — NOT armed by default in this template):
    * * * * * cd $CIV_ROOT && python3 tools/model_switch_trigger.py --once \\
        >> logs/model_switch_trigger.log 2>&1

IMPORTANT: flipping to peer requires the router seam wired
(config/router_endpoint.txt + config/lifeboat/router_key.txt +
config/peer_model_id.txt) — model_switch.sh REFUSES otherwise, and this
trigger surfaces that refusal loudly rather than silently failing.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CIV_ROOT") or Path(__file__).resolve().parent.parent)
STATE = ROOT / "config" / "model_mode.json"
LOCK = ROOT / "data" / "state" / "model_switch_trigger.lock"
LEDGER = ROOT / "logs" / "model_switch_trigger_ledger.jsonl"
DISABLE = Path("/tmp/model-switch-trigger.disable")
SWITCH = ROOT / "tools" / "model_switch.sh"

PATTERNS = [
    re.compile(r"you'?ve hit your weekly limit", re.I),
    re.compile(r"usage_limit_reached", re.I),
    re.compile(r"usage limit exceeded", re.I),
    re.compile(r"hit your weekly limit", re.I),
    re.compile(r"weekly usage limit", re.I),
    re.compile(r"weekly limit.{0,80}reset", re.I | re.S),
]

TAIL_BYTES = 64 * 1024


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ledger(event: str, detail: str = "") -> None:
    try:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": _now(), "event": event,
                                 "detail": detail[:300]}) + "\n")
    except Exception:
        pass


def _tail(path: Path) -> str:
    try:
        size = path.stat().st_size
        with path.open("rb") as fh:
            if size > TAIL_BYTES:
                fh.seek(-TAIL_BYTES, os.SEEK_END)
            return fh.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def _scan_sources() -> list[Path]:
    out: list[Path] = []
    # 1. newest session JSONL per project dir
    proj_root = Path.home() / ".claude" / "projects"
    if proj_root.is_dir():
        jsonls = sorted(proj_root.glob("*/*.jsonl"),
                        key=lambda p: p.stat().st_mtime, reverse=True)
        out.extend(jsonls[:3])
    # 2. civ logs
    logdir = ROOT / "logs"
    if logdir.is_dir():
        logs = sorted(logdir.glob("*.log"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        out.extend(logs[:5])
    return out


def _current_mode() -> dict:
    try:
        return json.loads(STATE.read_text())
    except Exception:
        return {"mode": "default"}


def tick() -> str:
    if DISABLE.exists():
        return "disabled"

    mode = _current_mode()
    # semantic lock maintenance: manual flip-back clears the lock
    if mode.get("mode") != "peer" and LOCK.exists():
        try:
            LOCK.unlink()
            _ledger("lock-cleared", "mode is no longer peer")
        except Exception:
            pass

    hit_snippet = ""
    for src in _scan_sources():
        text = _tail(src)
        for pat in PATTERNS:
            m = pat.search(text)
            if m:
                hit_snippet = f"{src.name}: {m.group(0)[:120]}"
                break
        if hit_snippet:
            break

    if not hit_snippet:
        return "no-detect"

    if LOCK.exists() and mode.get("mode") == "peer":
        _ledger("detect-suppressed-locked", hit_snippet)
        return "detect-suppressed-locked"

    # FIRE: flip to peer
    reason = f"usage-limit-auto:{hit_snippet}"[:180]
    try:
        cp = subprocess.run([str(SWITCH), "peer", "--reason", reason],
                            capture_output=True, text=True, timeout=30)
    except Exception as exc:
        _ledger("auto-flip-error", str(exc))
        print(f"AUTO-FLIP ERROR: {exc}", file=sys.stderr)
        return "flip-error"
    if cp.returncode != 0:
        # loud: the switch refused (likely unwired router seam)
        _ledger("auto-flip-refused", cp.stderr.strip()[:300])
        print(f"USAGE-LIMIT DETECTED but flip REFUSED:\n{cp.stderr}",
              file=sys.stderr)
        return "flip-refused"

    LOCK.parent.mkdir(parents=True, exist_ok=True)
    LOCK.write_text(json.dumps({"ts": _now(), "reason": reason}))
    _ledger("auto-flip-fired", reason)
    print(f"AUTO-FLIP FIRED -> peer ({reason})")
    # --- best-effort human-notify seam: wire your civ's push channel here ---
    # e.g. subprocess.run([sys.executable, "tools/send_telegram_plain.py",
    #                      f"substrate auto-flipped to peer: {reason}"])
    return "auto-flip-fired"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--once", action="store_true", help="run one tick and exit")
    args = ap.parse_args()
    if not args.once:
        ap.error("only --once mode is supported (run from cron)")
    print(f"{_now()} tick -> {tick()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
