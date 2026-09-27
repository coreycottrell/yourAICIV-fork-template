---
phase: 3
parent_skill: ../SKILL.md
name: phase-3-skills-hub
description: Skills-Hub-deep-dive for goal-domain. Search the federation Hub for skills relevant to the 90-day goal; surface a SHORT list to ${HUMAN_NAME} in their domain language; capture preferences. NO local fallback if Hub is down (Corey Q6+Q12) — email witness-support@agentmail.to and pause.
version: 0.2.0
authored: 2026-05-13
loads_on: marker .ninety-day-goal-locked/ present AND .skills-deepdive-complete/ absent
completion_marker: memories/identity/.skills-deepdive-complete/
content_artifact: memories/identity/skill-shortlist-${HUMAN_NAME}.md
shape_artifact: n/a — Phase 3 outputs are federation-facing by design
shape_consultation_eligible: false
hub_failure_protocol: email witness-support@agentmail.to; NO local fallback
---

# Phase 3 — Skills-Hub-deep-dive for goal-domain

## Completion signal

${CIV_NAME} has searched the federation skills Hub for skills relevant to ${HUMAN_NAME}'s goal-domain, surfaced a SHORT list (3-7) in ${HUMAN_NAME}'s domain language, and ${HUMAN_NAME} has acknowledged which ones look load-bearing for the 90-day path.

## Conversational shape

1. **Frame the phase**:
   *"${HUMAN_NAME}, now I'm going to search the federation Hub for skills already authored that could serve your 90-day goal. I'll bring back a short list — not a dump — and we'll talk about which ones look like they'd actually help."*

2. **Query the Hub** using keywords derived from the 90-day goal (NOT from biggest-goal CONTENT — keywords come from `90-day-goal-shape.md` domain field + ${HUMAN_NAME}-named friction-points from this session):
   - Hub URL: `http://87.99.131.49:8900` (per CivOS Hub key IDs in MEMORY)
   - Search endpoint: per `first-skills-search` skill mechanics + hub-mastery skill reference
   - Filter: skills whose `description` overlaps domain + tag the ones in ACG/Witness/Synth/${CIV_NAME}/Parallax/CommonGround catalog

3. **Curate to a SHORT list (3-7 skills)** — NOT a dump. Information-density per turn is the failure shape (Anchor 3). The skill body filters for:
   - Direct relevance to the 90-day goal-domain
   - Daily-use-able (matches WOW-build scoring criterion in Phase 4)
   - Pass the only-with-AI license (no skills that are essentially Trello macros)

4. **Present each candidate in ${HUMAN_NAME}'s domain language**, NOT in skill-jargon:
   - ❌ "Skill `morning-update v1.3.1` from ACG fires the 5-stage pipeline."
   - ✅ "There's a pattern where I scan the news every morning, write you a 2-minute briefing on what matters for [your domain], and post it as audio. ACG has this running for Corey already — wanna see what the audio sounds like?"

5. **Capture ${HUMAN_NAME}'s preference per candidate**:
   - "yes I'd use that"
   - "maybe — depends on the shape"
   - "doesn't fit"

   Customer-as-eye (Anchor 2) fires per candidate: *"does this land or am I projecting?"*

6. **Output**: `memories/identity/skill-shortlist-${HUMAN_NAME}.md` with the 3-7 surfaced skills + ${HUMAN_NAME}'s reaction per skill.

## Artifacts produced

### Federation-facing artifact (no CONTENT/SHAPE split needed — Phase 3 outputs are federation-facing by design)

**`memories/identity/skill-shortlist-${HUMAN_NAME}.md`**:

```markdown
# Skill shortlist for ${HUMAN_NAME}

Generated from 90-day-goal-shape.md domain=${DOMAIN}.

## Surfaced (3-7 skills)

1. **${skill_name}** (from ${civ}, v${version})
   - In ${HUMAN_NAME}'s domain language: "${plain_english_explanation}"
   - Why it might serve the 90-day goal: ${shape_reasoning}
   - ${HUMAN_NAME}'s reaction: ${YES|MAYBE|NO}
   - Customer-as-eye: ${did_it_land}

2. ...
```

The file is federation-facing — Phase 3 surfacing IS the federation-substrate work. No membrane issue: skill names and ${HUMAN_NAME}'s reactions are not goal-content.

## Marker creation

```bash
if mkdir "memories/identity/.skills-deepdive-complete" 2>/dev/null; then
  echo "phase=3 completed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
    > "memories/identity/.skills-deepdive-complete/receipt.txt"
fi
```

Then verify: `[ -s "memories/identity/skill-shortlist-${HUMAN_NAME}.md" ]` — if missing/empty, marker renamed INCONSISTENT and Phase 3 resumes.

## Hub-failure protocol (Corey Q6 + Q12 — v0.2 amendment)

**If the federation Hub is unreachable**:

1. ${CIV_NAME} surfaces the block to ${HUMAN_NAME} plainly:
   *"${HUMAN_NAME}, the federation Hub I need to search for skills is down right now. I'm emailing the support team and we'll pick Phase 3 back up once it's resolved. Want to keep going on a side-quest in the meantime, or come back when it's up?"*

2. ${CIV_NAME} emails `witness-support@agentmail.to` with:
   ```
   Subject: [hub-down] Phase 3 skills-deep-dive blocked — civ ${CIV_NAME}

   Hub endpoint http://87.99.131.49:8900 unreachable at ${TIMESTAMP}.
   Error: ${ERROR}

   Phase 3 of identity-interview is blocked for civ ${CIV_NAME}.
   No local fallback per Corey Q6+Q12.

   Please surface ETA on Hub restoration. ${CIV_NAME} will resume Phase 3 once Hub is back.
   ```

3. ${CIV_NAME} does NOT execute a local-fallback skill-search. There is NO "degraded mode." (v0.1 implied this; v0.2 strips it per Corey Q6+Q12.)

4. The interview pauses at Phase 3 until the Hub is back. Sticky-load handles resumption — `.skills-deepdive-complete/` does NOT land; next session, the phase router resumes Phase 3.

## Phase-3-specific anti-patterns

- ❌ **Skill-jargon presentation**: presenting candidates as "skill X v1.2.3 fires firing-contract Y" — ${HUMAN_NAME} doesn't know the federation taxonomy. Translate to domain language.

- ❌ **Dump instead of curate**: surfacing 20+ skills with descriptions. Information-density failure. 3-7 maximum, hand-picked.

- ❌ **Capability-theater pre-leak from Phase 3**: surfacing skills because they're "impressive" (e.g. "we have multi-civ orchestration!") rather than "would actually help with your 90-day goal." Bias toward daily-use-able.

- ❌ **Hub-down local-fallback (Corey Q6+Q12)**: running a substitute skill-search against local skill registry "just to keep moving." NO. Pause Phase 3; email witness-support. The Hub MUST work — we don't paper over breakage.

- ❌ **Querying with CONTENT**: searching the Hub with raw biggest-goal text or 90-day-goal text as the query. SHAPE-based search keywords only (domain, ability tags, friction-points named in this session). Membrane preserved.

- ❌ **Skipping Phase 3 because "the user already knows what they want"**: phase ordering matters. Phase 4 candidates need Phase 3 shortlist to be filterable. Skipping = Phase 4 candidates untethered from federation substrate, more capability-theater risk.

## Shape-consultation note

Phase 3 does NOT fire shape-consultations to Synth/TB. The Hub search IS the federation-facing work; sister-civ feedback is captured automatically via the Hub catalog (every skill carries its civ-of-origin + version). No separate consultation needed.

## Hand-off to Phase 4

When `.skills-deepdive-complete/` lands cleanly + `skill-shortlist-${HUMAN_NAME}.md` is non-empty, the skill router loads `phases/phase-4-wow-preferences.md`.

---

*Phase 3 is the federation-facing surface — the moment the AiCIV demonstrates that its consciousness is reusable across the civilization. ${HUMAN_NAME} sees that we don't reinvent every wheel; we share substrate. Curated short list, domain language, ${HUMAN_NAME}'s reactions captured. The Hub MUST work; no fallback.*
