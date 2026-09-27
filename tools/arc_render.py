#!/usr/bin/env python3
"""
arc_render.py — Render arc/ARC-NOW.md + arc.diff(since=...).

THE ARC v2 MVP. Reads arc/live.jsonl + arc/recent.md + arc/epoch.md.
Owner: mind-lead-analog on your fork.

Two callable modes:

    # A) Full render (ARC-NOW.md, ~4KB) — the one wake read
    python3 tools/arc_render.py --render-now [--write arc/ARC-NOW.md]

    # B) Delta render (since a prior read timestamp, ~1KB) — the fork-return read
    python3 tools/arc_render.py --diff-since 2026-07-02T14:00:00Z

Design commitments:
    - Read-only over arc/live.jsonl. Never mutates events.
    - Salience = base × exponential decay (MVP v2.0).
      v2.1 amplifiers (refcount, verified?, held-for-steward pin) noted inline.
    - Diff-read is a first-class primitive: filters live.jsonl by ts > since.
    - Budget clamp: soft warn if render exceeds --budget-kb.

Salience formula (v2.0 MVP — SKILL.md §Salience):
    salience(event, t) = base(type) × exp(-ln2 · Δh / halflife(type))

🌱 FORK CONFIG:
    - ARC_ROOT env: where `arc/` lives (default `<repo>/arc/`).
    - ARC_STEWARD_ID env: the token that marks an event as "held for the
      steward" — matched against `held_for` field. Default `steward`. Set
      to your steward's id (e.g. `alice`) at fork time so the HELD-FOR
      block on ARC-NOW.md carries YOUR steward's asks, not the origin's.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------

ARC_ROOT_ENV = "ARC_ROOT"
_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ARC_DIR = _REPO_ROOT / "arc"


def arc_dir() -> Path:
    p = Path(os.environ.get(ARC_ROOT_ENV, str(DEFAULT_ARC_DIR)))
    p.mkdir(parents=True, exist_ok=True)
    return p


def live_jsonl_path() -> Path:
    return arc_dir() / "live.jsonl"


def recent_md_path() -> Path:
    return arc_dir() / "recent.md"


def epoch_md_path() -> Path:
    return arc_dir() / "epoch.md"


def arc_now_path() -> Path:
    return arc_dir() / "ARC-NOW.md"


# ------------------------------------------------------------------
# Loaders
# ------------------------------------------------------------------


def _parse_ts(ts: str) -> datetime:
    ts = ts.rstrip("Z")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"unparseable ts: {ts!r}")


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
                continue  # graceful degradation
    return out


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------------------
# Salience (MVP v2.0: base × decay)
# ------------------------------------------------------------------


def _salience_now(ev: Dict[str, Any], now: datetime) -> float:
    base = float(ev.get("salience_base", 0.5))
    hl_h = float(ev.get("halflife_hours", 24 * 7))
    try:
        t_emit = _parse_ts(ev["ts"])
    except (KeyError, ValueError):
        return base
    dt_h = max(0.0, (now - t_emit).total_seconds() / 3600.0)
    decay = math.exp(-math.log(2) * dt_h / hl_h)
    # v2.1 amplifiers:
    #   × (1 + 0.15 · refcount_since)
    #   × (1 + 0.3 · verified?)
    #   × held_for_STEWARD ? max(0.6, curr) : curr   (STEWARD = env ARC_STEWARD_ID)
    return base * decay


# ------------------------------------------------------------------
# Grouping + formatting
# ------------------------------------------------------------------


def _group_by_thread(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ev in events:
        out[ev.get("thread", "unknown")].append(ev)
    return out


def _thread_salience(evs: List[Dict[str, Any]], now: datetime) -> float:
    """Thread salience = max event salience (headline dominates)."""
    return max((_salience_now(ev, now) for ev in evs), default=0.0)


def _fmt_ev_oneline(ev: Dict[str, Any]) -> str:
    t = ev.get("type", "?")
    ts = ev.get("ts", "?")[:10]
    who = ev.get("who", "")
    who_tag = f" [{who}]" if who else ""
    if t == "SHIFT":
        return f"- {ts} SHIFT: {ev.get('from', '?')} → {ev.get('to', '?')}{who_tag}"
    if t == "OPEN":
        return f"- {ts} OPEN: {ev.get('goal', ev.get('thread', '?'))}{who_tag}"
    if t == "CLOSE":
        return f"- {ts} CLOSE: {ev.get('reason', '?')} ({ev.get('evidence', '')})"
    if t == "DECIDE":
        return f"- {ts} DECIDE: {ev.get('decision', '?')} (wwcw={ev.get('wwcw', '?')})"
    if t == "VERIFY":
        return f"- {ts} VERIFY: {ev.get('claim', '?')} → {ev.get('result', '?')}"
    if t == "SURPRISE":
        return f"- {ts} SURPRISE: {ev.get('observation', '?')} " \
               f"(impact: {ev.get('impact', '')})"
    return f"- {ts} {t}: {json.dumps(ev, ensure_ascii=False)}"


# ------------------------------------------------------------------
# Renderers
# ------------------------------------------------------------------


def render_now(intent: Optional[str] = None, budget_kb: float = 4.0) -> str:
    """MVP render — salience-only, no intent embedding yet."""
    events = _load_live()
    now = _now_utc()
    grouped = _group_by_thread(events)

    ranked: List[Tuple[str, float, List[Dict[str, Any]]]] = sorted(
        ((thr, _thread_salience(evs, now), evs) for thr, evs in grouped.items()),
        key=lambda x: x[1],
        reverse=True,
    )

    lines: List[str] = []
    lines.append("# ARC-NOW")
    lines.append(
        f"Generated: {now.strftime('%Y-%m-%dT%H:%M:%SZ')} • "
        f"MVP v2.0 (base × decay, no amplifiers) • "
        f"{len(events)} live events across {len(grouped)} threads"
    )
    if intent:
        lines.append(f"Intent: {intent}")
    lines.append("")

    lines.append("## THE STORY (30-day epoch, 2 lines)")
    ep = epoch_md_path()
    if ep.exists() and ep.stat().st_size > 0:
        # Look for the `## The Story` section; take the first non-heading
        # line under it. Fallback: first non-heading, non-metadata line.
        text_lines = ep.read_text().splitlines()
        found = False
        i = 0
        while i < len(text_lines):
            if text_lines[i].strip().lower().startswith("## the story"):
                # take next non-empty, non-heading lines (up to 2)
                j = i + 1
                taken = 0
                while j < len(text_lines) and taken < 2:
                    s = text_lines[j].strip()
                    if s and not s.startswith("#"):
                        lines.append(s)
                        taken += 1
                    j += 1
                found = taken > 0
                break
            i += 1
        if not found:
            for line in text_lines:
                s = line.strip()
                if (s and not s.startswith("#")
                        and not s.lower().startswith("generated:")):
                    lines.append(s)
                    break
    else:
        lines.append("_(epoch.md not yet generated — run tools/arc_compress_epoch.py; "
                     "graceful-degrade: LIVE tier still queryable)_")
    lines.append("")

    lines.append("## LIVE NOW (top 5 threads by salience)")
    if not ranked:
        lines.append("_(no events yet — arc bootstrapping)_")
    for thr, sal, evs in ranked[:5]:
        newest = sorted(evs, key=lambda e: e.get("ts", ""), reverse=True)[0]
        lines.append(
            f"- **{thr}** (salience {sal:.2f}, {len(evs)} event{'s' if len(evs)>1 else ''}) "
            f"— last: {_fmt_ev_oneline(newest).lstrip('- ')}"
        )
    lines.append("")

    shifts = [ev for ev in events if ev.get("type") == "SHIFT"]
    shifts_sorted = sorted(shifts, key=lambda e: _salience_now(e, now), reverse=True)[:3]
    lines.append("## SHIFTS (top 3 by salience — what CHANGED, buried in turn-transcripts)")
    for ev in shifts_sorted:
        lines.append(_fmt_ev_oneline(ev))
    if not shifts_sorted:
        lines.append("_(none)_")
    lines.append("")

    surprises = [ev for ev in events if ev.get("type") == "SURPRISE"]
    lines.append("## SURPRISES / RISKS (the things we didn't expect — persist longest)")
    for ev in sorted(surprises, key=lambda e: _salience_now(e, now), reverse=True)[:3]:
        lines.append(_fmt_ev_oneline(ev))
    if not surprises:
        lines.append("_(none)_")
    lines.append("")

    steward_id = os.environ.get("ARC_STEWARD_ID", "steward")
    held = [ev for ev in events
            if ev.get("held_for") == steward_id
            or f"held_for_{steward_id}" in str(ev.get("wwcw", ""))]
    lines.append(f"## HELD FOR {steward_id.upper()} (blocked on your steward)")
    for ev in held[:5]:
        lines.append(_fmt_ev_oneline(ev))
    if not held:
        lines.append("_(none)_")
    lines.append("")

    lines.append("## READ NEXT (if you need more)")
    lines.append("- arc/recent.md (7d, salience-ordered) — full thread list w/ event trails")
    lines.append("- arc/epoch.md (30d) — full arc summary + closed threads")
    lines.append("- arc/live.jsonl (24h raw) — event stream")
    lines.append("- WORKBOARD.md — kanban-derived open goals (system of record for GOALS)")
    lines.append("")
    lines.append("## HOW TO USE")
    lines.append("- Cold pickup: read this file (~4KB, 5th cold-pickup read).")
    lines.append("- Fork return: `arc.diff --diff-since <last_arc_read_ts>` (~1KB).")
    lines.append("- Do NOT hand-edit; compressors are the only writers.")

    out = "\n".join(lines) + "\n"

    budget_bytes = int(budget_kb * 1024)
    n_bytes = len(out.encode("utf-8"))
    if n_bytes > budget_bytes:
        out += (
            f"\n<!-- render exceeded budget {budget_kb}KB ({n_bytes} bytes) — "
            f"v2.1 tightens salience threshold -->\n"
        )
    return out


def render_diff(since_ts: str, budget_kb: float = 1.0) -> str:
    """Only what changed since `since_ts`."""
    since = _parse_ts(since_ts)
    events = _load_live()
    new_events: List[Dict[str, Any]] = []
    for ev in events:
        try:
            if _parse_ts(ev.get("ts", "1970-01-01T00:00Z")) > since:
                new_events.append(ev)
        except ValueError:
            continue

    now = _now_utc()
    lines: List[str] = []
    lines.append(f"# ARC / DELTA since {since.strftime('%Y-%m-%dT%H:%M:%SZ')}")
    elapsed_h = (now - since).total_seconds() / 3600.0
    counts = defaultdict(int)
    for e in new_events:
        counts[e.get("type", "?")] += 1
    lines.append(
        f"{elapsed_h:.1f}h elapsed • {len(new_events)} events • "
        + " • ".join(f"{v} {k.lower()}" for k, v in counts.items())
    )
    lines.append("")

    for label, tp in [("NEW SHIFTS", "SHIFT"), ("SURPRISES", "SURPRISE"),
                      ("CLOSED", "CLOSE"), ("DECIDED", "DECIDE"),
                      ("VERIFIED", "VERIFY"), ("NEW OPEN", "OPEN")]:
        subset = [e for e in new_events if e.get("type") == tp]
        if not subset:
            continue
        lines.append(f"## {label}")
        for ev in subset:
            lines.append(_fmt_ev_oneline(ev))
        lines.append("")

    if not new_events:
        lines.append("_(no changes since your last read)_")

    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--render-now", action="store_true",
                   help="Render ARC-NOW.md-style one-read surface (~4KB)")
    p.add_argument("--diff-since",
                   help="RFC3339 ts; render only events after this (~1KB)")
    p.add_argument("--intent",
                   help="Intent string (v2.3 shapes retrieval; MVP ignores)")
    p.add_argument("--budget-kb", type=float, default=None,
                   help="Soft budget (default 4 for --render-now, 1 for --diff-since)")
    p.add_argument("--write", type=Path,
                   help="Write to path instead of stdout "
                        "(use `arc/ARC-NOW.md` for canonical render)")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.render_now:
        budget = args.budget_kb if args.budget_kb is not None else 4.0
        out = render_now(intent=args.intent, budget_kb=budget)
    elif args.diff_since:
        budget = args.budget_kb if args.budget_kb is not None else 1.0
        out = render_diff(args.diff_since, budget_kb=budget)
    else:
        print("must specify --render-now OR --diff-since <ts>", file=sys.stderr)
        return 2

    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(out)
        print(json.dumps({
            "ok": True,
            "path": str(args.write),
            "bytes": len(out.encode("utf-8")),
        }))
    else:
        sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
