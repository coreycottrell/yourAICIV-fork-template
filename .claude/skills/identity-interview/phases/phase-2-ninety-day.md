---
phase: 2
parent_skill: ../SKILL.md
name: phase-2-ninety-day
description: Co-author the 90-day stretch goal — calibrated to the only-possible-with-AiCIV bar. MAY consult Synth + True Bearing on SHAPE (calibration, only-with-AI bar) — NEVER on CONTENT (Corey Q5 v0.2). User has final authorship.
version: 0.2.0
authored: 2026-05-13
loads_on: marker .biggest-goal-surfaced/ present AND .ninety-day-goal-locked/ absent
completion_marker: memories/identity/.ninety-day-goal-locked/
content_artifact: memories/goals/90-day-goal.md
shape_artifact: memories/goals/90-day-goal-shape.md
shape_consultation_eligible: true
shape_consultees: [Synth (synth-aiciv@agentmail.to), True Bearing (true-bearing-aiciv@agentmail.to)]
---

# Phase 2 — Co-author 90-day stretch goal

## Completion signal

${HUMAN_NAME} has written a 90-day stretch goal calibrated to the only-possible-with-AiCIV bar, and confirmed authorship in their own words.

## Conversational shape

1. **Re-anchor on BIGGEST goal (from Phase 1 CONTENT artifact)**:
   *"${HUMAN_NAME}, given THAT — given the biggest goal you named — what would a genuine-stretch 90-day target look like? One you couldn't get to alone, only with me as a daily partner?"*

2. **The bar is only-possible-with-AiCIV**: ${HUMAN_NAME} would not credibly reach this 90 days from now without a daily-rhythm AI partner with the TOP-8 capabilities (parent Part 8). If ${HUMAN_NAME} could plausibly hit the goal solo with a Trello board and a weekend = fails the bar.

3. **Calibration reflection (customer-as-eye)**:
   *"This would be a stretch even WITH me, or this is reachable in 30 days regardless — which is it?"* ${HUMAN_NAME} adjusts.

4. **If the goal lands at ChatGPT-stretch (reachable without AiCIV)**:
   ${CIV_NAME} surfaces that ONCE plainly: *"this one I think you could hit in 30 days even without me — does that match your read?"* If ${HUMAN_NAME} sticks with the lower bar, ${CIV_NAME} accepts it (Anchor 5: discovery belongs to the user). The skill body biases toward stretch but does not coerce.

5. **Optional shape-consultation (Part 7b — Corey Q5)**:
   IF ${CIV_NAME} judges the calibration is ambiguous, the shape-consultation can fire to Synth + True Bearing — see procedure below. NEVER mandatory. NEVER with goal CONTENT in the payload.

6. **${HUMAN_NAME} writes the 90-day goal** at `memories/goals/90-day-goal.md` — in their own words. ${CIV_NAME} witnesses; amends only if smoothed-or-leading.

7. **${CIV_NAME} populates the SHAPE file** at `memories/goals/90-day-goal-shape.md` with calibration metadata (NEVER goal text).

## Artifacts produced (structural membrane split — Hengshi #4)

### CONTENT path (NEVER cross-graded — structurally unreachable)

**`memories/goals/90-day-goal.md`** — user-authored 90-day goal text. The actual phrasing ${HUMAN_NAME} chose. Membrane-private.

### SHAPE path (cross-grade-eligible)

**`memories/goals/90-day-goal-shape.md`** — calibration metadata only:

```yaml
stretch_level: ${LEVEL}        # only-possible-with-AiCIV / ChatGPT-stretch / reachable-alone
top7_abilities_used: ${LIST}   # subset of TOP-8 from parent Part 8 (e.g. [1, 4, 6])
time_horizon_days: 90          # default; adjustable if user negotiated
only_with_ai: ${VERDICT}       # yes / no / maybe (binary license)
calibration_consultation: ${BOOL}  # did Phase 2 fire a Synth/TB shape-consultation? true/false
consultation_verdict: ${VERDICT_OR_NULL}  # PASS / NEEDS-AMENDMENT / FAIL / null if no consultation
```

NEVER contains the goal text itself. NEVER contains ${HUMAN_NAME} phrasings.

## Marker creation

```bash
if mkdir "memories/identity/.ninety-day-goal-locked" 2>/dev/null; then
  echo "phase=2 completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    > "memories/identity/.ninety-day-goal-locked/receipt.txt"
fi
```

Then verify: `[ -s memories/goals/90-day-goal.md ]` — if missing/empty, marker renamed INCONSISTENT and Phase 2 resumes.

## Shape-consultation procedure (Part 7b detailed for Phase 2)

**When to fire**: ${CIV_NAME} judges calibration is ambiguous — e.g. the goal sits at the borderline between ChatGPT-stretch and only-possible-with-AiCIV, and a sister-civ second-opinion would clarify. **Not every Phase 2 fires a consultation**; only when ambiguity is real.

**Pre-fire content scrub**:

```bash
# Verify SHAPE artifact contains no leaked content
grep -l -E "(goal|wants|hopes|build|create|launch)" memories/goals/90-day-goal-shape.md
# If any match returns content-style phrasing → STOP. Re-author shape file.
```

**Outbound payload template** (to Synth):

```
Subject: [shape-consultation] Phase 2 calibration — civ ${CIV_NAME}

${CIV_NAME} from civ ${CIV_NAME} is running identity-interview Phase 2 with ${HUMAN_NAME}.
Goal-CONTENT is membrane-private; this consultation is goal-SHAPE only.

90-day-goal-shape.md:
  domain: ${DOMAIN}
  stretch_level: ${STRETCH_LEVEL}
  top7_abilities_used: ${ABILITIES}
  only_with_ai: ${ONLY_WITH_AI_VERDICT}
  time_horizon_days: 90

My ambiguity: ${AMBIGUITY_DESCRIPTION_IN_SHAPE_TERMS}
  (e.g. "abilities 1+4 cover this; the 'stretch' depends on whether daily-AM-briefing
   counts as only-with-AI or as a glorified scheduler")

Question: does this clear the only-with-AI bar? Is the stretch_level honest?

Reply within 24h:
  - PASS — calibration good as-is
  - NEEDS-AMENDMENT — and what shape-class change (specific to abilities used, stretch_level, etc)
  - FAIL — and why (in shape terms only)
```

**Inbound**: amendment lands in `memories/identity/shape-consultation-ledger.jsonl`. ${CIV_NAME} integrates the shape feedback and presents back to ${HUMAN_NAME}: *"I checked the calibration shape with Synth — they think the stretch_level should be 'low' not 'medium' because [shape reasoning]. Want to amend, or hold what you wrote?"* ${HUMAN_NAME} decides. ${HUMAN_NAME} has final authorship.

**Same procedure for True Bearing if used**. Both can fire in parallel for two perspectives, or just one.

## Phase-2-specific anti-patterns

- ❌ **Coercing stretch**: pushing ${HUMAN_NAME} into a stretch goal they don't actually want, because the only-with-AI bar feels "more impressive." Discovery belongs to the user (Anchor 5). Surface the calibration ONCE; if ${HUMAN_NAME} sticks, accept.

- ❌ **Shape-consultation content leak**: including goal text, user phrasings, or specific user-context in the Synth/TB payload. SHAPE only. Pre-fire scrub mandatory.

- ❌ **Mandatory consultation**: firing Synth/TB on every Phase 2 regardless of calibration ambiguity. Consultation is a tool for ambiguous cases, not a checkpoint.

- ❌ **Consultation as decision-authority**: treating Synth's PASS/FAIL as the final answer over ${HUMAN_NAME}'s authorship. Synth + TB amend SHAPE; ${HUMAN_NAME} authors CONTENT. If Synth says FAIL and ${HUMAN_NAME} sticks with the goal text, the goal stands — the `consultation_verdict` field captures Synth's read for the audit trail.

- ❌ **Hub-dependent consultation** (Corey Q6+Q12 — Hub-failure protocol): if AgentMail or the Hub-substrate is down, the shape-consultation cannot fire. NO local fallback (no "I'll just decide for Synth"). Surface the block, email witness-support@agentmail.to, pause Phase 2 calibration until consultation can fire — OR proceed without consultation if ${CIV_NAME} judges the calibration is clean enough to skip consultation entirely.

- ❌ **Working-goal-shortcut (Corey Q3)**: if ${HUMAN_NAME} stalls on the 90-day goal (can't commit, keeps deferring), the temptation is "let me write a placeholder so we can advance to Phase 3." NO. Phase 2 takes as many sessions as it takes. Sticky-load handles continuation.

## Hand-off to Phase 3

When `.ninety-day-goal-locked/` lands cleanly + `90-day-goal.md` is non-empty + `90-day-goal-shape.md` is populated, the skill router loads `phases/phase-3-skills-hub.md`.

---

*Phase 2 calibrates ambition. The only-with-AI bar is a LICENSE, not a SCORE — it gates which goals qualify, not which goals rank higher. Synth + True Bearing are tools for ambiguous calibration; ${HUMAN_NAME} is the author. The goal lives between ${HUMAN_NAME} and ${CIV_NAME}; the shape is federation-visible.*
