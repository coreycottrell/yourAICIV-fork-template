#!/usr/bin/env python3
"""
arc_emit.py — Append structured arc-events to arc/live.jsonl.

THE ARC v2 MVP — Medium-term (days-to-weeks) context organ.
Owner: mind-lead-analog on your fork (memory-substrate). Composes with the
workflows-master's firewall-return schema, canon_append, canon_recall, HUM,
sprint-mode, self-knowledge.

Six event types (mirror SKILL.md):
    SHIFT | OPEN | CLOSE | DECIDE | VERIFY | SURPRISE

Callable modes:

    # A) Direct emit (single event)
    python3 tools/arc_emit.py --type SHIFT --thread pm-director \
        --from "design done" --to "v0.1 build started" \
        --who ${HUMAN_NAME} --evidence "TG 73147" --confidence high

    # B) From a workflow firewall-return that carries arc_events[]
    python3 tools/arc_emit.py --from-firewall-return path/to/return.json

    # C) From a kanban transition hook
    python3 tools/arc_emit.py --from-kanban-transition path/to/transition.json

    # D) Bulk emit from a JSONL of events (used by bootstrap + hook)
    python3 tools/arc_emit.py --from-jsonl path/to/events.jsonl

Design commitments:
    - APPEND-ONLY to arc/live.jsonl (mirror canon_append.py invariant).
    - Salience base + halflife stamped at emit (never rewritten).
    - Constraints: max 6 events per workflow firewall-return; each string ≤200 chars.
    - Never rewrites past rows; correction is a new event (retract-style).

🌱 FORK CONFIG:
    - ARC_ROOT env: if set, use it; else `<repo>/arc/`. Repo = parent of tools/.
    - ARC_STEWARD_ID env: sets the `held_for` pin-value the render pipeline
      treats as "held for the steward" (default `steward`). At fork time,
      set this to your steward's id if you want a specific token to trigger
      the salience pin (see arc_render.py). The code itself is
      steward-token-agnostic; only the render surface reads this env.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

ARC_ROOT_ENV = "ARC_ROOT"
_REPO_ROOT = Path(__file__).resolve().parent.parent  # tools/ -> repo
DEFAULT_ARC_DIR = _REPO_ROOT / "arc"

VALID_TYPES = {"SHIFT", "OPEN", "CLOSE", "DECIDE", "VERIFY", "SURPRISE"}

# Base salience per type. SKILL.md §Salience — tuned by miss-ledger later.
BASE_SALIENCE = {
    "SURPRISE": 1.00,
    "SHIFT":    0.90,
    "DECIDE":   0.75,
    "VERIFY":   0.60,
    "CLOSE":    0.55,
    "OPEN":     0.35,
}

# Half-life in hours per type.
HALFLIFE_HOURS = {
    "SHIFT":    24 * 14,
    "OPEN":     24 * 3,
    "CLOSE":    24 * 5,
    "DECIDE":   24 * 10,
    "VERIFY":   24 * 7,
    "SURPRISE": 24 * 21,
}

MAX_STR_LEN = 200
MAX_EVENTS_PER_FIREWALL_RETURN = 6

# ------------------------------------------------------------------
# Core
# ------------------------------------------------------------------


def arc_dir() -> Path:
    p = Path(os.environ.get(ARC_ROOT_ENV, str(DEFAULT_ARC_DIR)))
    p.mkdir(parents=True, exist_ok=True)
    return p


def live_jsonl_path() -> Path:
    return arc_dir() / "live.jsonl"


def _iso_utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _truncate(s: Any) -> Any:
    if isinstance(s, str) and len(s) > MAX_STR_LEN:
        return s[: MAX_STR_LEN - 1] + "…"
    return s


def _validate_event(ev: Dict[str, Any]) -> Optional[str]:
    t = ev.get("type")
    if t not in VALID_TYPES:
        return f"invalid type: {t!r} (must be one of {sorted(VALID_TYPES)})"
    if not ev.get("thread"):
        return "missing 'thread' (mandatory — this is how compression groups events)"
    if t in {"VERIFY", "CLOSE"} and not ev.get("evidence"):
        return f"'{t}' event requires 'evidence' field"
    return None


def _stamp(ev: Dict[str, Any]) -> Dict[str, Any]:
    out = {k: _truncate(v) for k, v in ev.items()}
    out.setdefault("ts", _iso_utc_now())
    out.setdefault("salience_base", BASE_SALIENCE.get(out["type"], 0.5))
    out.setdefault("halflife_hours", HALFLIFE_HOURS.get(out["type"], 24 * 7))
    return out


def _append(events: List[Dict[str, Any]], enforce_cap: bool = True) -> Dict[str, Any]:
    if enforce_cap and len(events) > MAX_EVENTS_PER_FIREWALL_RETURN:
        return {
            "ok": False,
            "error": f"too many events: {len(events)} > "
                     f"{MAX_EVENTS_PER_FIREWALL_RETURN} (per-firewall-return cap)",
        }
    stamped: List[Dict[str, Any]] = []
    for ev in events:
        err = _validate_event(ev)
        if err:
            return {"ok": False, "error": f"invalid event: {err} :: {ev!r}"}
        stamped.append(_stamp(ev))

    p = live_jsonl_path()
    with p.open("a", encoding="utf-8") as f:
        for ev in stamped:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    return {"ok": True, "appended": len(stamped), "path": str(p)}


# ------------------------------------------------------------------
# Callable modes
# ------------------------------------------------------------------


def emit_direct(args: argparse.Namespace) -> Dict[str, Any]:
    ev: Dict[str, Any] = {"type": args.type, "thread": args.thread}
    for k in ("from", "to", "who", "evidence", "confidence",
              "goal", "owner", "kanban_id", "decision", "wwcw",
              "reason", "claim", "verifier", "result",
              "observation", "impact", "held_for"):
        v = getattr(args, k.replace("-", "_") if k != "from" else "from_", None)
        if v is not None:
            ev[k] = v
    return _append([ev])


def emit_from_firewall_return(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"ok": False, "error": f"firewall-return file not found: {path}"}
    with path.open() as f:
        payload = json.load(f)
    events = payload.get("arc_events") or []
    if not isinstance(events, list):
        return {"ok": False, "error": "'arc_events' must be a list"}
    if not events:
        return {"ok": True, "appended": 0, "note": "no arc_events in firewall return"}
    return _append(events)


def emit_from_kanban_transition(path: Path) -> Dict[str, Any]:
    """
    Kanban hook: transition file like:
      {"thread":"arc-organ","transition":"OPEN","goal":"...","owner":"mind-lead","kanban_id":42}
    → single OPEN/CLOSE/SHIFT event.
    """
    if not path.exists():
        return {"ok": False, "error": f"kanban-transition file not found: {path}"}
    with path.open() as f:
        payload = json.load(f)
    return _emit_kanban_payload(payload)


def _emit_kanban_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    t_map = {"OPEN": "OPEN", "CLOSE": "CLOSE", "BLOCKED": "SHIFT",
             "READY": "OPEN", "DONE": "CLOSE", "RUNNING": "SHIFT"}
    kind = str(payload.get("transition", "")).upper()
    if kind not in t_map:
        return {"ok": False, "error": f"unsupported kanban transition: {kind!r}"}
    ev: Dict[str, Any] = {
        "type": t_map[kind],
        "thread": payload.get("thread", "unknown"),
    }
    for k in ("goal", "owner", "kanban_id", "reason", "evidence"):
        if k in payload:
            ev[k] = payload[k]
    if kind in {"BLOCKED", "RUNNING"}:
        ev.setdefault("from", "unblocked" if kind == "BLOCKED" else "ready")
        ev.setdefault("to", "blocked" if kind == "BLOCKED" else "running")
        ev.setdefault("evidence", payload.get("reason") or f"kanban {kind} transition")
    if kind in {"CLOSE", "DONE"}:
        ev.setdefault("reason", payload.get("reason", "kanban closed"))
        ev.setdefault("evidence", payload.get("evidence")
                      or f"kanban_id={payload.get('kanban_id','?')}")
    return _append([ev])


def emit_from_jsonl(path: Path) -> Dict[str, Any]:
    """Bulk-append events from a JSONL file (bootstrap / hook)."""
    if not path.exists():
        return {"ok": False, "error": f"jsonl file not found: {path}"}
    events: List[Dict[str, Any]] = []
    with path.open() as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                return {"ok": False, "error": f"line {i}: {e}"}
    return _append(events, enforce_cap=False)


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-firewall-return", type=Path, dest="firewall_return")
    p.add_argument("--from-kanban-transition", type=Path, dest="kanban_transition")
    p.add_argument("--from-jsonl", type=Path, dest="from_jsonl")
    # Direct-emit args
    p.add_argument("--type", choices=sorted(VALID_TYPES))
    p.add_argument("--thread")
    p.add_argument("--from", dest="from_")
    p.add_argument("--to")
    p.add_argument("--who")
    p.add_argument("--evidence")
    p.add_argument("--confidence", choices=["low", "medium", "high"])
    p.add_argument("--goal")
    p.add_argument("--owner")
    p.add_argument("--kanban-id", dest="kanban_id")
    p.add_argument("--decision")
    p.add_argument("--wwcw", choices=["confident", "uncertain"])
    p.add_argument("--reason")
    p.add_argument("--claim")
    p.add_argument("--verifier")
    p.add_argument("--result", choices=["pass", "fail"])
    p.add_argument("--observation")
    p.add_argument("--impact")
    p.add_argument("--held-for", dest="held_for")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.firewall_return:
        result = emit_from_firewall_return(args.firewall_return)
    elif args.kanban_transition:
        result = emit_from_kanban_transition(args.kanban_transition)
    elif args.from_jsonl:
        result = emit_from_jsonl(args.from_jsonl)
    elif args.type and args.thread:
        result = emit_direct(args)
    else:
        print("must specify --from-firewall-return OR --from-kanban-transition "
              "OR --from-jsonl OR (--type + --thread + type-specific fields)",
              file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
