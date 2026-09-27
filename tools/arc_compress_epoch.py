#!/usr/bin/env python3
"""
arc_compress_epoch.py — Weekly compressor. RECENT (7d) → EPOCH (30d).

Produces `arc/epoch.md`: a 30-day arc-summary. Top threads over the epoch,
2-line story-header (headline SHIFT + open-thread-count), closed-thread
roll-up, surprises persisted.

Wheel slot: weekly (Sun; see wheel-slots doc).

Reads: `arc/live.jsonl` (30-day view — live.jsonl was already rotated by
nightly compressor, so archived shards under `arc/_archive/` are also
scanned for the 30-day window).

Usage:
    python3 tools/arc_compress_epoch.py [--epoch-days 30]

Idempotent — regenerating epoch.md is deterministic given the same
event set.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "tools"))

from arc_render import (  # noqa: E402
    _salience_now, _fmt_ev_oneline, _parse_ts, arc_dir,
    live_jsonl_path, epoch_md_path, arc_now_path,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _load_all_events_within(cutoff: datetime) -> List[Dict[str, Any]]:
    """Load live.jsonl + any archived shards inside the window."""
    out: List[Dict[str, Any]] = []

    def _read(p: Path) -> None:
        if not p.exists():
            return
        with p.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                try:
                    if _parse_ts(ev.get("ts", "1970-01-01T00:00Z")) >= cutoff:
                        out.append(ev)
                except ValueError:
                    continue

    _read(live_jsonl_path())
    arch = arc_dir() / "_archive"
    if arch.exists():
        for p in arch.glob("*.jsonl"):
            _read(p)
    return out


def compress(epoch_days: int = 30) -> Dict[str, Any]:
    now = _now_utc()
    cutoff = now - timedelta(days=epoch_days)
    events = _load_all_events_within(cutoff)

    grouped = defaultdict(list)
    for ev in events:
        grouped[ev.get("thread", "unknown")].append(ev)

    ranked = sorted(
        ((thr, max((_salience_now(ev, now) for ev in evs), default=0.0), evs)
         for thr, evs in grouped.items()),
        key=lambda x: x[1],
        reverse=True,
    )

    # Story header — top SHIFT + open-thread count
    shifts = [ev for ev in events if ev.get("type") == "SHIFT"]
    top_shift = None
    if shifts:
        top_shift = sorted(shifts, key=lambda e: _salience_now(e, now), reverse=True)[0]

    closed_threads = {ev.get("thread") for ev in events if ev.get("type") == "CLOSE"}
    open_threads = [thr for thr in grouped if thr not in closed_threads]

    surprises = [ev for ev in events if ev.get("type") == "SURPRISE"]

    lines: List[str] = []
    lines.append("# ARC / EPOCH (30d summary)")
    lines.append(f"Generated: {now.strftime('%Y-%m-%dT%H:%M:%SZ')} • "
                 f"{len(events)} events • {len(grouped)} threads "
                 f"({len(open_threads)} open, {len(closed_threads)} closed) • "
                 f"compressor: arc_compress_epoch.py v1.0")
    lines.append("")

    # 2-line story header (ARC-NOW reads first non-heading line)
    lines.append("## The Story")
    if top_shift:
        lines.append(f"Headline SHIFT: {top_shift.get('from','?')} → "
                     f"{top_shift.get('to','?')} on thread "
                     f"'{top_shift.get('thread','?')}' — {len(open_threads)} threads "
                     f"live, {len(closed_threads)} closed, {len(surprises)} surprises.")
    else:
        lines.append(f"{len(open_threads)} threads live, {len(closed_threads)} "
                     f"closed, {len(surprises)} surprises in the last {epoch_days}d.")
    lines.append("")

    lines.append("## Top Threads by Salience")
    for thr, sal, evs in ranked[:10]:
        status = "CLOSED" if thr in closed_threads else "live"
        lines.append(f"- **{thr}** [{status}] · salience {sal:.2f} · {len(evs)} events")
    lines.append("")

    lines.append("## Closed Threads (30d)")
    if closed_threads:
        for thr in sorted(closed_threads):
            closes = [ev for ev in grouped[thr] if ev.get("type") == "CLOSE"]
            reason = closes[-1].get("reason", "?") if closes else "?"
            lines.append(f"- **{thr}** — {reason}")
    else:
        lines.append("_(none)_")
    lines.append("")

    lines.append("## Surprises (persist longest — we LEARN from these)")
    if surprises:
        for ev in sorted(surprises, key=lambda e: _salience_now(e, now),
                         reverse=True)[:5]:
            lines.append(_fmt_ev_oneline(ev))
    else:
        lines.append("_(none)_")
    lines.append("")

    out_text = "\n".join(lines) + "\n"
    epoch_md_path().write_text(out_text)

    # Regenerate ARC-NOW so the story-header shows through.
    from arc_render import render_now
    now_out = render_now()
    arc_now_path().write_text(now_out)

    return {
        "ok": True,
        "epoch_md_bytes": len(out_text.encode("utf-8")),
        "arc_now_bytes": len(now_out.encode("utf-8")),
        "events_scanned": len(events),
        "threads": len(grouped),
        "open_threads": len(open_threads),
        "closed_threads": len(closed_threads),
        "surprises": len(surprises),
        "paths": {
            "epoch_md": str(epoch_md_path()),
            "arc_now": str(arc_now_path()),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--epoch-days", type=int, default=30,
                   help="EPOCH tier window (default 30)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    result = compress(epoch_days=args.epoch_days)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
