#!/usr/bin/env python3
"""
needed_actions_to_board.py — Primary-authored needed-actions feeder for the
PROJECT-BOARD staleness organs (see PROJECT-BOARD-TEMPLATE.md § Staleness organs).

Post-grounding, Primary judges the forward frontier of a project and records
that judgment in EXACTLY the same shape as a workflow firewall return's
`whats_next` (docs/whats-next-contract.md §26.1). The shard lands in
data/audits/workflow_returns/YYYY-MM/ so the existing
`whats_next_to_board.py --sweep --regen` picks it up VERBATIM — no second
transport path, no second format.

This is the STRUCTURAL-freshness leg: every grounding cycle can refresh
frontier state even when individual workflows silently omit.

CLI:
    python3 tools/needed_actions_to_board.py \\
        --project my-project --phase "Phase 2 — wire the transport" --pct 40 \\
        --next-move "Run tools/whats_next_to_board.py --sweep --regen" \\
        --blocked-on none [--owner primary]
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys
import uuid
from pathlib import Path


def _root() -> Path:
    env = os.environ.get("CIV_ROOT") or os.environ.get("AICIV_ROOT")
    return Path(env).resolve() if env else Path(__file__).resolve().parent.parent


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--project", required=True, help="stable project id (upsert key)")
    ap.add_argument("--phase", required=True, help="current phase heading, verbatim")
    ap.add_argument("--pct", required=True, type=int, help="honest completion estimate 0-100")
    ap.add_argument("--next-move", required=True, help="the SINGLE next concrete step (≤400 chars)")
    ap.add_argument("--blocked-on", required=True,
                    help="'none' | '<steward-id>' | '<other-project-id>'")
    ap.add_argument("--owner", default="primary")
    args = ap.parse_args()

    if not (0 <= args.pct <= 100):
        print("pct must be 0-100", file=sys.stderr)
        return 1
    if len(args.next_move) > 400:
        print("next_move exceeds 400 chars (§26.1) — tighten it", file=sys.stderr)
        return 1

    now = _dt.datetime.now(_dt.timezone.utc)
    root = _root()
    shard_dir = root / "data" / "audits" / "workflow_returns" / now.strftime("%Y-%m")
    shard_dir.mkdir(parents=True, exist_ok=True)
    shard = shard_dir / f"needed-actions-{uuid.uuid4()}.json"
    shard.write_text(json.dumps({
        "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "needed-actions",
        "owner": args.owner,
        "whats_next": {
            "project": args.project,
            "phase": args.phase,
            "pct": args.pct,
            "next_move": args.next_move,
            "blocked_on": args.blocked_on,
        },
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {shard.relative_to(root)} — next sweep/regen will board it verbatim")
    return 0


if __name__ == "__main__":
    sys.exit(main())
