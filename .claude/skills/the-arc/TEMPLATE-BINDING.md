# Template binding note (aiciv-fork-template, 2026-07-09)

## STATUS: REFERENCE-ONLY / NOT-WIRED (ACG Auditor-B, 2026-07-09)

THE ARC ships in this template as **REFERENCE-ONLY**. The tool (`arc_*.py`) and
skill (`.claude/skills/the-arc/`) are PRESENT on disk, but the ARC is **NOT
wired into any live path** — the grounding wake-read insertion was REVERTED.

Why reference-only, not wired: the origin civ's 7-day wake-blank soak (due
2026-07-09) FAILED the read-bar, and the ARC's render leg is scheduled nowhere.
A wired-but-frozen read (an `arc_render` call in grounding that no trigger keeps
fresh) is WORSE than reference-only: it burns a wake-step reading a stale organ
and dresses a gap as a feature. So we ship the code, unwired.

**A fork MUST ship all THREE of these before wiring the ARC read into grounding
(or any wake floor):**

1. **Automated `arc_render` trigger** — the ARC-NOW.md render must be driven by
   an automated trigger (hook / cron / BOOP step), NOT rendered inline as a
   grounding side-effect.
2. **Render-staleness canary** — a check that ARC-NOW.md is fresh (like the
   PROJECT-BOARD AGE canary), so a frozen render is caught, not silently read.
3. **`arc_events[]` in the firewall-return schemas** — `coo.js` and
   `research.js` must carry an `arc_events[]` field so the ARC is fed
   structurally from workflow returns, not only via manual `arc_emit.py` calls.

Until all three exist, keep the ARC REFERENCE-ONLY. Do not add an `arc_render`
read to grounding Step 2.5 or any other wake step.

---

Prior stamp (retained for lineage): shipped **PROVISIONAL / tested-partial** —
the origin civ's own 7-day wake-blank soak test had NOT reported by integration
time (due 2026-07-09). Do not treat ARC-NOW.md as a proven organ until your
fork walks the wake-blank test in the SKILL.

What ships here: `.claude/skills/the-arc/SKILL.md` (doctrine), tools
`arc_emit.py` / `arc_render.py` / `arc_compress_recent.py` /
`arc_compress_epoch.py` / `arc_backfill_from_session.py` (+
`tools/ARC-BACKFILL-ADAPTER-NOTE.md`), and the `arc/` seed dir.
Emit+render round-trip was walk-tested on the integration branch.

Known gaps vs origin:
- `tools/arc_kanban_hook.py` (kanban-transition feed) is referenced by the
  SKILL but was NOT shipped upstream by origin — a fork with a kanban builds
  it against arc_emit.py's `--from-kanban-transition` mode.
- The `arc_events[]` firewall-return schema field is NOT yet added to this
  template's workflows (coo.js / research.js carry `whats_next` only). Feed
  the ARC via direct `arc_emit.py` calls or the backfill tool until your fork
  wires `arc_events[]` into its workflow returns.
- Wake-read wiring: grounding SKILL Step 2.5 (added 2026-07-09) renders +
  reads ARC-NOW.md, clearly marked PROVISIONAL.
- ARC_STEWARD_ID env: set to your human's id so held-for-steward pinning works.
