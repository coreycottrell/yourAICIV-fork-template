#!/usr/bin/env python3
"""
PostToolUse hook — archive every Workflow tool's firewall return to
data/audits/workflow_returns/YYYY-MM/{run_id}.json.

This is the feed substrate for the PROJECT-BOARD whats_next transport
(docs/whats-next-contract.md §26.6): the archived shard is swept by
tools/whats_next_to_board.py --sweep, which carries any `whats_next` field
VERBATIM to the board ledger. This hook judges nothing; it only archives.

Fail-open by design: any error exits 0 and never blocks the tool pipeline.

WIRING REQUIRED (one line, not yet armed in this genome — permission-guarded
path; the steward or the newborn adds it): append this entry to the
"PostToolUse" array in .claude/settings.json:

    { "matcher": "Workflow",
      "hooks": [ { "type": "command",
        "command": "python3 \\"$CLAUDE_PROJECT_DIR/tools/archive_workflow_return_hook.py\\"",
        "timeout": 10 } ] }

Until wired, the board's FED leg has a hole: workflow returns are not archived
and only needed_actions_to_board.py feeds the board. The transport itself
(sweep/regen/canary) works either way.

Self-test:
    echo '{"tool_name":"Workflow","tool_response":{"runId":"wf_selftest-123","result":{"whats_next":{"project":"p","phase":"x","pct":1,"next_move":"y","blocked_on":"none"}}}}' \
      | CIV_ROOT=/tmp/hook-selftest python3 tools/archive_workflow_return_hook.py \
      && cat /tmp/hook-selftest/data/audits/workflow_returns/*/wf_selftest-123.json
"""

import datetime
import json
import os
import re
import sys
import uuid
from pathlib import Path


def main() -> int:
    try:
        hook_input = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    try:
        if hook_input.get("tool_name") != "Workflow":
            return 0
        response = hook_input.get("tool_response")
        if response is None:
            return 0
        root = Path(os.environ.get("CIV_ROOT")
                    or os.environ.get("CLAUDE_PROJECT_DIR")
                    or Path(__file__).resolve().parents[1])
        now = datetime.datetime.now(datetime.timezone.utc)
        shard_dir = root / "data" / "audits" / "workflow_returns" / now.strftime("%Y-%m")
        shard_dir.mkdir(parents=True, exist_ok=True)

        blob = json.dumps(response, ensure_ascii=False, default=str)
        m = re.search(r"wf_[a-z0-9-]{6,}", blob)
        run_id = m.group(0) if m else f"run-{uuid.uuid4()}"

        record = {
            "ts": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "run_id": run_id,
            "workflow_input": hook_input.get("tool_input"),
            "tool_response": response,
        }
        # Surface whats_next at top level VERBATIM (no deep-fishing) so the
        # sweep finds it in the standard place.
        try:
            payload = response
            if isinstance(payload, str):
                payload = json.loads(payload)
            if isinstance(payload, dict):
                for candidate in (payload, payload.get("result"), payload.get("return")):
                    if isinstance(candidate, dict) and "whats_next" in candidate:
                        record["whats_next"] = candidate["whats_next"]
                        break
        except Exception:
            pass

        (shard_dir / f"{run_id}.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception:
        pass  # fail-open
    return 0


if __name__ == "__main__":
    sys.exit(main())
