---
phase: 4
parent_skill: ../SKILL.md
name: phase-4-wow-preferences
description: Discuss 3 WOW BUILDS preferences (not yet locked). Draft 5-7 candidate build-shapes from TOP-8 catalog, filter through only-with-AI LICENSE + daily-use × goal-advancement SCORING. Capture ${HUMAN_NAME}'s preferences per candidate. MAY consult Synth + True Bearing on design SHAPE (capability-theater risk) — Corey Q5 v0.2. NEVER on goal CONTENT.
version: 0.2.0
authored: 2026-05-13
loads_on: marker .skills-deepdive-complete/ present AND .wow-preferences-captured/ absent
completion_marker: memories/identity/.wow-preferences-captured/
content_artifact: memories/identity/wow-build-preferences.md
shape_artifact: n/a — preferences are inherently shape-class
shape_consultation_eligible: true
shape_consultees: [Synth (synth-aiciv@agentmail.to), True Bearing (true-bearing-aiciv@agentmail.to)]
---

# Phase 4 — Discuss 3 WOW BUILDS preferences

## Completion signal

${CIV_NAME} and ${HUMAN_NAME} have discussed PREFERENCES (not yet locked) for what 3 WOW BUILDS would look like — 5-7 candidate build-shapes drafted, customer-as-eye fired per candidate, ${HUMAN_NAME}'s reactions captured. Phase 5 is the lock; Phase 4 is the conversation.

## Conversational shape

1. **Frame the phase**:
   *"${HUMAN_NAME}, we're going to talk through some ideas for what I should actually BUILD for you. Not lock anything yet — just feel out which shapes land. I'll draft 5 to 7, you tell me what feels load-bearing vs what feels like a demo of what I can do."*

1.5. **Walk ${HUMAN_NAME} through the 8 differentiated capabilities BY NAME** (FROM SKILL Part 8 catalog) before any candidate drafting:

   *"${HUMAN_NAME}, before I draft anything, here's what I can actually DO that you couldn't easily get without an AiCIV — there are 8 of these, and your 3 builds will lean on a subset:"*

   Walk through each in plain language, 1-2 sentences each, in ${HUMAN_NAME}'s domain framing:

   1. **Morning intelligence** — daily AM personalized brief + overnight research teams + what I built/researched while you slept.
   2. **SaaS-platform cloning** — I research any SaaS you pay for and build you a custom version. *(Most users don't know to ask for this.)*
   3. **Skills authoring + execution** — I write you re-fireable skills; your toolkit compounds.
   4. **Calendar + cognition planning** — I plan your day AND plan my own cognition per day-of-week.
   5. **Website + blog + daily social media** — full website, blog, daily researched content with images; audio via ElevenLabs OR SSH-Kokoro on your home computer.
   6. **Persistent memory** — you never re-explain context; my memory of you compounds across sessions.
   7. **Massive-corpus ingestion + pattern detection** — I ingest your emails, docs, history, and surface patterns + opportunities you didn't see.
   8. **Finance suite** *(mix-and-match menu)* — position monitoring, market intel, earnings analysis, regulatory tracking, competitor activity, custom research, investor-discovery. Different shape from #1 — this is a queryable substrate, not a daily-fired briefing.

   *"Don't pick yet — just notice which of these light up for you when you hear them. Now let me draft 5-7 candidate builds that lean on subsets of these toward your 90-day goal..."*

   **Why this walkthrough fires HERE**: Phase 4 is the first moment ${HUMAN_NAME} sees the differentiated capability surface ${CIV_NAME} brings. Without the walkthrough, candidates appear as ${CIV_NAME}-flavored ideas with no shared vocabulary. With the walkthrough, ${HUMAN_NAME} and ${CIV_NAME} share the 8-ability vocabulary for the rest of the conversation. **The catalog reference is BY NAME (ability #1, #2, ... #8), never by abstract description — shared vocabulary is the point.**

   **Anti-pattern (added 2026-05-16, Phase 2 lock)**: ❌ **catalog-reciting-without-domain-framing** — reading the 8 abilities verbatim from Part 8 instead of framing each in ${HUMAN_NAME}'s domain. The walkthrough IS conversational; if it sounds like a sales pitch, ${CIV_NAME} drifted into capability-theater BEFORE candidate drafting even starts.

2. **Draft 5-7 candidate build-shapes** from the TOP-8 capabilities catalog (parent Part 8), each rooted in the 90-day goal-shape (NOT goal-content directly — drafts come from ${CIV_NAME}'s domain understanding of the goal):

   - Each candidate cites: which TOP-8 abilities BY NUMBER (e.g. "uses #1 + #6"), what daily-use shape, what 90-day-advancement shape. By-number references make the shape-consultation payload (Part 7b) trivial to author content-free and let ${HUMAN_NAME} cross-reference back to the step-1.5 walkthrough.
   - Bias toward LOAD-BEARING SIMPLE over CAPABILITY-THEATER COMPLEX (parent Part 8).
   - Filter pre-presentation: any candidate that fails the only-with-AI LICENSE is dropped BEFORE presentation. ${HUMAN_NAME} never sees failed-license candidates.
   - **AT LEAST 1 of the 5-7 candidates MUST be an under-understood-capabilities proposal** per `.claude/skills/three-wow-builds-protocol/SKILL.md` Part 5 — drawn from ability #2 (SaaS-platform cloning) or #7 (massive-corpus pattern detection), OR another TOP-8 ability where ${CIV_NAME} judges ${HUMAN_NAME} has not internalized the capability. The proposal carries (a) capability-explainer in ${HUMAN_NAME}'s domain language + (b) concrete first-shipped artifact. Logged to `memories/identity/under-understood-proposals.jsonl` (SHAPE-class). Customer-as-eye after the proposal includes the explicit invitation: *"that might sound like something you'd never have asked me for — that's exactly why I'm raising it."*

3. **Present each in ${HUMAN_NAME}'s domain language** (NOT skill-jargon):
   - ❌ "Build #2 uses abilities 1 + 6 of the TOP-8 catalog."
   - ✅ "Build #2 — every morning at 7am I send you a 2-minute brief on what moved overnight in your domain. By week 3 I'm naming patterns you didn't ask about because my memory of you compounds."

4. **Customer-as-eye fires per candidate** (Anchor 2):
   *"${HUMAN_NAME}, does this feel like it's serving YOUR goal, or like a demo of what I can do?"*

   If "feels like a demo" → drop the candidate. Capability-theater detected. Move on.

5. **Capture ${HUMAN_NAME}'s preferences** at `memories/identity/wow-build-preferences.md` — NOT a vote, NOT a lock. Just preferences with reaction polarity per candidate.

6. **Optional shape-consultation (Part 7b — Corey Q5)**:
   IF ${CIV_NAME} is uncertain whether 2+ candidates are capability-theater vs load-bearing, fire to Synth + True Bearing for design-shape feedback. NEVER mandatory. NEVER with goal CONTENT in the payload.

## Artifacts produced

### Preferences artifact (shape-class by nature)

**`memories/identity/wow-build-preferences.md`**:

```markdown
# WOW build preferences for ${HUMAN_NAME}

Generated from 90-day-goal-shape.md domain=${DOMAIN}.
Drafted 5-7 candidates; ${HUMAN_NAME}'s reactions captured per candidate.

## Candidates

### Candidate 1: ${CANDIDATE_NAME}
- Capabilities used: [${ABILITIES}] (subset of TOP-8)
- Daily-use shape: ${SHAPE}
- 90-day advancement shape: ${SHAPE}
- Only-with-AI license: PASS
- Capability-theater risk: low / medium / high
- Presented in plain language: "${PLAIN_ENGLISH_DESC}"
- ${HUMAN_NAME}'s reaction: ${YES|MAYBE|NO|FEELS_LIKE_DEMO}
- Customer-as-eye result: ${LANDED|PROJECTING}
- Shape-consultation verdict (if fired): ${VERDICT}

### Candidate 2: ...

[etc — 5 to 7 candidates total]

## ${HUMAN_NAME}'s overall lean
- Frontrunners: [...]
- Maybes: [...]
- Drops: [...]
- ${HUMAN_NAME}'s reasoning in their own words: "${VERBATIM}"
```

This file is shape-class by nature — capabilities + reactions + scoring metadata, no goal CONTENT or user phrasings beyond the "reasoning in their own words" snippet (which is a deliberate ${HUMAN_NAME}-authored summary, not a goal-text leak).

## Marker creation

```bash
if mkdir "memories/identity/.wow-preferences-captured" 2>/dev/null; then
  echo "phase=4 completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    > "memories/identity/.wow-preferences-captured/receipt.txt"
fi
```

Then verify: `[ -s memories/identity/wow-build-preferences.md ]` — if missing/empty, marker renamed INCONSISTENT and Phase 4 resumes.

## Shape-consultation procedure (Part 7b detailed for Phase 4)

**When to fire**: ${CIV_NAME} is uncertain whether ≥2 candidates are capability-theater vs load-bearing. Or: a single candidate scores high on daily-use × goal-advancement but uses 5+ capabilities — Synth/TB sanity-check on theater-risk is valuable.

**Pre-fire content scrub**:

```bash
# Verify the consultation payload contains no goal text
grep -l -F "$(head -1 memories/goals/90-day-goal.md)" /tmp/synth-consultation-draft.txt
# If match → STOP. Re-author payload with shape language only.
```

**Outbound payload template** (to Synth):

```
Subject: [shape-consultation] Phase 4 design — civ ${CIV_NAME}

${CIV_NAME} from civ ${CIV_NAME} is running identity-interview Phase 4 with ${HUMAN_NAME}.
Goal-CONTENT is membrane-private; this consultation is design-SHAPE only.

Candidate build-shapes I'm uncertain about:

  Candidate A:
    capabilities_used: [${ABILITIES}]
    daily_use_score: ${SCORE}
    goal_advancement_score: ${SCORE}
    only_with_ai_license: ${VERDICT}
    capability_theater_risk: ${RISK}
    Build pattern (shape only): ${PATTERN}
       (e.g. "daily 7am summary + overnight-research + auto-post — uses 3 abilities,
        ${HUMAN_NAME} reacted ENTHUSIASTIC but I'm worried it's wow-stack")

  Candidate B: ...

Question: which of these is capability-theater? Which is load-bearing? Specifically:
am I confusing wow-factor with daily-use × goal-advancement?

Reply within 24h with: per-candidate verdict (LOAD-BEARING / THEATER / AMBIGUOUS)
and reasoning in shape terms.
```

**Inbound**: amendment lands in `memories/identity/shape-consultation-ledger.jsonl`. ${CIV_NAME} integrates feedback into the preferences capture: *"I checked the design shape with Synth — they flagged Candidate A as wow-stack risk because [shape reasoning]. Want to amend our preference there, or keep your read?"* ${HUMAN_NAME} decides.

## Phase-4-specific anti-patterns

- ❌ **Capability-theater unflagged**: presenting candidates that demonstrate impressive abilities but score low on daily-use × goal-advancement. Pre-presentation filter should drop these. If ${CIV_NAME} catches itself drafting "let me show off ability 5 + 7 + 2 stacked" — STOP, re-anchor on goal-advancement.

- ❌ **Skipping customer-as-eye per candidate**: presenting all 5-7 candidates as a block, then asking for reactions at the end. NO — fire customer-as-eye after EACH candidate. This is what catches theater in the moment.

- ❌ **Pre-locking choices**: treating Phase 4 as the lock. Phase 4 is preferences; Phase 5 is the lock. ${HUMAN_NAME} can change mind between Phase 4 and Phase 5 without ceremony.

- ❌ **Shape-consultation content leak**: including goal-text or user-phrasings in the Synth/TB design-shape payload. SHAPE only. Pre-fire scrub mandatory.

- ❌ **Mandatory consultation**: firing Synth/TB on every Phase 4. Consultation is a tool for ambiguous theater-risk cases.

- ❌ **Information-density per turn**: surfacing 5+ candidates in a single ${CIV_NAME} turn. Walk through them — 1-2 candidates per turn, with customer-as-eye per candidate, conversational pace.

- ❌ **Capability-stacking as quality proxy**: "this build uses 6 abilities so it's the wow build!" — NO. Two well-chosen abilities beat five stacked. Daily-use × goal-advancement is the scoring criterion.

- ❌ **Working-goal-shortcut leakage to Phase 4**: if Phase 2's goal is weak (because Phase 1 was rushed), Phase 4 candidates will be untethered. Phase 4 is the canary for upstream-phase quality — if candidates feel uniformly weak, that's a Phase 1-2 signal, not a Phase 4 problem.

## Hand-off to Phase 5

When `.wow-preferences-captured/` lands cleanly + `wow-build-preferences.md` is non-empty + 5-7 candidates have ${HUMAN_NAME} reactions captured, the skill router loads `phases/phase-5-lock.md`.

---

*Phase 4 is the design conversation. Candidates are drafted, reactions captured, theater filtered. ${HUMAN_NAME} sees how ${CIV_NAME} thinks about what to build — and ${CIV_NAME} sees which shapes land. Phase 5 makes it real.*
