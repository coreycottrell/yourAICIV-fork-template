#!/usr/bin/env python3
"""
ensure_daily_scratchpad.py — Structural cure for journal-death (Hum-witness 2026-06-01/02).

CONTRACT:
  Idempotent. Cheap. Safe. Designed to be called at every wake/resume/compact
  via the SessionStart hook + every sprint-mode preamble + every haiku-archive
  fire. Same trigger surface as the haiku-append substrate that empirically
  proves it fires reliably.

  - If `.claude/scratchpad-daily/YYYY-MM-DD.md` (UTC) exists → no-op (exit 0).
  - If missing → create from a minimal seed pointing at yesterday's handoff +
    the prior day's scratchpad. The seed is intentionally LIGHT so a real wake
    pass can append richly without fighting a heavy template.

  Background: N=6+1 journal-death pattern. Cure was named in MEMORY as a
  forward-pointer ("→ fleet-lead AM") on 2026-06-01; on 2026-06-02 the same
  thing happened again because a name is not a wire. This script is the wire.

EXIT:
  0 on success (either no-op OR successful create). Never raises to the hook.

USAGE:
  python3 tools/ensure_daily_scratchpad.py            # default: civ repo root
  python3 tools/ensure_daily_scratchpad.py --quiet    # silent unless error
  python3 tools/ensure_daily_scratchpad.py --date YYYY-MM-DD  # explicit (testing)
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def repo_root() -> Path:
    """Locate the civ repo root robustly (env-var > script-anchor > cwd)."""
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    if env and Path(env).is_dir():
        return Path(env)
    # tools/ensure_daily_scratchpad.py → parent.parent
    here = Path(__file__).resolve().parent.parent
    if (here / ".claude").is_dir():
        return here
    return Path.cwd()


def find_prior_scratchpad(daily_dir: Path, today_str: str) -> Path | None:
    """Return the most-recent scratchpad-daily file STRICTLY before today, if any."""
    if not daily_dir.is_dir():
        return None
    candidates = sorted(
        (p for p in daily_dir.glob("*.md") if p.stem < today_str),
        reverse=True,
    )
    return candidates[0] if candidates else None


def find_latest_handoff(root: Path) -> Path | None:
    """Return the most-recent handoff-YYYY-MM-DD.md from memories/sessions, if any."""
    sessions = root / "memories" / "sessions"
    if not sessions.is_dir():
        return None
    handoffs = sorted(sessions.glob("handoff-*.md"), reverse=True)
    return handoffs[0] if handoffs else None


def render_seed(today_str: str, prior_scratchpad: Path | None, handoff: Path | None, root: Path) -> str:
    """Render a minimal seed pointing at carry-forward context. Light by design."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        f"# Scratchpad — {today_str}",
        "",
        f"*Seeded {now_iso} by `tools/ensure_daily_scratchpad.py` (structural cure for journal-death, "
        "wired to the SessionStart hook — same trigger surface as the haiku archive). "
        "This file exists-by-default; the wake pass appends richly.*",
        "",
        "## Carry-forward",
    ]
    if handoff is not None:
        rel = handoff.relative_to(root) if handoff.is_relative_to(root) else handoff
        lines.append(f"- Latest handoff: `{rel}`")
    else:
        lines.append("- (no handoff found in `memories/sessions/`)")
    if prior_scratchpad is not None:
        rel = prior_scratchpad.relative_to(root) if prior_scratchpad.is_relative_to(root) else prior_scratchpad
        lines.append(f"- Prior scratchpad: `{rel}`")
    else:
        lines.append("- (no prior scratchpad found in `.claude/scratchpad-daily/`)")
    lines += [
        "",
        "## Live log",
        "",
        "*(Append here as the day unfolds — haiku archive fires the same trigger that seeded this file, "
        "so if THIS section stays empty while haikus accumulate, the cure regressed → tell fleet-lead.)*",
        "",
    ]
    return "\n".join(lines)


def ensure(today_str: str | None = None, quiet: bool = False) -> int:
    root = repo_root()
    daily_dir = root / ".claude" / "scratchpad-daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    if today_str is None:
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    target = daily_dir / f"{today_str}.md"
    if target.exists():
        if not quiet:
            print(f"[ensure_daily_scratchpad] no-op: {target.name} exists")
        return 0

    prior = find_prior_scratchpad(daily_dir, today_str)
    handoff = find_latest_handoff(root)
    seed = render_seed(today_str, prior, handoff, root)
    target.write_text(seed, encoding="utf-8")
    if not quiet:
        print(f"[ensure_daily_scratchpad] CREATED {target}")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--date", help="YYYY-MM-DD (default: today UTC)")
    ap.add_argument("--quiet", action="store_true", help="silent unless error")
    args = ap.parse_args(argv)
    try:
        return ensure(today_str=args.date, quiet=args.quiet)
    except Exception as e:
        # Never raise to the hook — log to stderr + return 0 so SessionStart
        # never blocks a real wake on a scratchpad-ensure hiccup.
        sys.stderr.write(f"[ensure_daily_scratchpad] WARN: {e}\n")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
