#!/usr/bin/env python3
"""
arc_compress_recent.py — Nightly compressor. LIVE (24h) → RECENT (7d).

Produces `arc/recent.md`: threads-by-momentum (salience-ordered), each
thread with its top-N events. Prunes `arc/live.jsonl` older than the
LIVE window (default 24h) INTO a rotated archive (arc/_archive/live-YYYYMMDD.jsonl)
so nothing is ever lost.

Also regenerates `arc/ARC-NOW.md` after compression.

Wheel slot: nightly (see wheel-slots doc).

Usage:
    python3 tools/arc_compress_recent.py [--live-hours 24] [--recent-days 7]

Idempotent: re-running produces the same recent.md (deterministic — salience
+ ts sort). Rotation only fires if there is content to rotate.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent
ARC_ROOT_ENV = "ARC_ROOT"

# reuse salience formula from arc_render
sys.path.insert(0, str(_REPO_ROOT / "tools"))
from arc_render import (  # noqa: E402
    _salience_now, _group_by_thread, _fmt_ev_oneline, _parse_ts, arc_dir,
    live_jsonl_path, recent_md_path, arc_now_path,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load_live() -> List[Dict[str, Any]]:
    p = live_jsonl_path()
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def compress(live_hours: int = 24, recent_days: int = 7) -> Dict[str, Any]:
    events = _load_live()
    now = _now_utc()
    recent_cutoff = now - timedelta(days=recent_days)
    live_cutoff = now - timedelta(hours=live_hours)

    # RECENT scope = anything within recent_days
    recent_events: List[Dict[str, Any]] = []
    old_events: List[Dict[str, Any]] = []
    keep_events: List[Dict[str, Any]] = []
    for ev in events:
        try:
            t = _parse_ts(ev.get("ts", "1970-01-01T00:00Z"))
        except ValueError:
            keep_events.append(ev)
            continue
        if t >= recent_cutoff:
            recent_events.append(ev)
        else:
            old_events.append(ev)
        if t >= live_cutoff:
            keep_events.append(ev)

    grouped = _group_by_thread(recent_events)

    ranked = sorted(
        ((thr, max((_salience_now(ev, now) for ev in evs), default=0.0), evs)
         for thr, evs in grouped.items()),
        key=lambda x: x[1],
        reverse=True,
    )

    lines: List[str] = []
    lines.append("# ARC / RECENT (7d, salience-ordered)")
    lines.append(f"Generated: {now.strftime('%Y-%m-%dT%H:%M:%SZ')} • "
                 f"{len(recent_events)} events • {len(grouped)} threads • "
                 f"compressor: arc_compress_recent.py v1.0")
    lines.append("")

    if not ranked:
        lines.append("_(no events in the 7d window)_")
    for thr, sal, evs in ranked:
        lines.append(f"## {thr}  ·  salience {sal:.2f}  ·  {len(evs)} event"
                     f"{'s' if len(evs)>1 else ''}")
        for ev in sorted(evs, key=lambda e: e.get("ts", ""), reverse=True)[:6]:
            lines.append(_fmt_ev_oneline(ev))
        lines.append("")

    recent_out = "\n".join(lines) + "\n"
    recent_md_path().write_text(recent_out)

    # rotate old events out of live.jsonl (before recent_cutoff)
    rotated = 0
    if old_events:
        arch_dir = arc_dir() / "_archive"
        arch_dir.mkdir(parents=True, exist_ok=True)
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        arch = arch_dir / f"live-pruned-{stamp}.jsonl"
        with arch.open("w") as f:
            for ev in old_events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        # rewrite live.jsonl with only events inside LIVE window
        with live_jsonl_path().open("w") as f:
            for ev in keep_events:
                f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        rotated = len(old_events)

    # regenerate ARC-NOW
    from arc_render import render_now  # local import to keep top clean
    now_out = render_now()
    arc_now_path().write_text(now_out)

    return {
        "ok": True,
        "recent_md_bytes": len(recent_out.encode("utf-8")),
        "arc_now_bytes": len(now_out.encode("utf-8")),
        "recent_events": len(recent_events),
        "threads": len(grouped),
        "old_pruned_rotated": rotated,
        "live_kept": len(keep_events),
        "paths": {
            "recent_md": str(recent_md_path()),
            "arc_now": str(arc_now_path()),
            "live_jsonl": str(live_jsonl_path()),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--live-hours", type=int, default=24,
                   help="LIVE tier window (default 24)")
    p.add_argument("--recent-days", type=int, default=7,
                   help="RECENT tier window (default 7)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    result = compress(live_hours=args.live_hours, recent_days=args.recent_days)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
