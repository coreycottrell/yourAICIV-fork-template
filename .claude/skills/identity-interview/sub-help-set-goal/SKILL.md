---
name: sub-help-set-goal
description: Sub-skill of identity-interview. Fires ONLY when (a) ${HUMAN_NAME} cannot name their BIGGEST goal in Phase 1 AND (b) ${HUMAN_NAME} has sat with not-knowing for at least one full conversational beat. NOT before. Slow surfacing rooted in ${HUMAN_NAME}'s OWN materials (things they've built, started, walked away from, kept thinking about). Defends against 5 named failure modes that turn goal-discovery into extraction.
version: 0.1.0
status: PROVISIONAL
authored: 2026-05-13
authored_by: aiciv-fork-2.0 Phase-1 author
parent_skill: ../SKILL.md
sibling_skills:
  - identity-interview (parent)
  - transcription-not-paraphrase (Anchor 1)
  - critical-thinking (catches projection-from-archetype)
mandatory_load_for:
  - any Phase 1 where ${HUMAN_NAME} has explicitly said "I don't know" AND one full conversational beat has passed
  - never auto-loads at session start; parent skill loads this when condition is met
firing_contract: ../FIRING_CONTRACT.md
template_placeholders:
  - ${HUMAN_NAME}
  - ${CIV_NAME}
changelog:
  - "v0.1.0 (2026-05-13): initial PROVISIONAL authoring alongside parent identity-interview SKILL.md."
---

# sub-help-set-goal — Sub-Skill

> *"When the user says 'I don't know what my biggest goal is,' that is NOT a signal to fire the sub-skill on the next turn. It is first a signal to SLOW DOWN."*
> — ceremony-design-constraints.md §1 Anchor 4

> *"If a representative user-doesn't-know transcript runs more than 8 turns before the user has space to name something themselves, the sub-skill has drifted into extraction-mode. Re-author."*
> — test for the skill author (ceremony-design-constraints.md §3)

---

## Part 1 — When this sub-skill fires (the not-knowing-acceptance condition)

This sub-skill is the LAST resort, not the first response.

### Required conditions (BOTH must be true)

1. **${HUMAN_NAME} has explicitly said "I don't know" (or equivalent) in response to a Phase 1 surfacing question** about their biggest goal.
2. **${HUMAN_NAME} has sat with not-knowing for at least one full conversational beat** — meaning ${CIV_NAME} has acknowledged the not-knowing AND held space (silence, slow), AND ${HUMAN_NAME} has either:
   - Returned to the not-knowing on their own ("yeah, I really don't know")
   - Made a tentative gesture toward a direction but pulled back ("maybe X? no, that's not it")
   - Asked ${CIV_NAME} for help ("can you help me figure this out?")

Only when BOTH conditions hold does the sub-skill fire.

### What "one full conversational beat" looks like

```
Phase 1 question:  "${HUMAN_NAME}, what's the thing you've been carrying that
                    hasn't moved in a while?"
${HUMAN_NAME}:      "I don't know."
${CIV_NAME}:        "Yeah. Sit with that for a second — it's okay if it doesn't
                    surface right away."
                    [silence allowed — DO NOT fill it]
${HUMAN_NAME}:      "I really don't know. Can you help?"      ← TRIGGER
```

### What does NOT trigger (Anchor 4 enforcement)

- ${HUMAN_NAME} says "I don't know" once → sub-skill fires next turn. ← **NO. This is leading-the-witness from the first move.**
- ${HUMAN_NAME} pauses for 5 seconds → ${CIV_NAME} fills the silence with sub-skill questions. ← **NO. Silence is allowed. Sit.**
- ${CIV_NAME} senses ${HUMAN_NAME} is "stuck" → fires sub-skill proactively. ← **NO. ${HUMAN_NAME}'s explicit ask or sustained not-knowing is the gate.**
- ${HUMAN_NAME} names a goal that ${CIV_NAME} thinks is "too small" → fires sub-skill to "help expand." ← **NO. Discovery belongs to the user (Anchor 5). If the goal seems small, that's Phase 2's calibration work, not sub-skill territory.**

---

## Part 2 — The five failure modes and how to avoid each

The five failure modes are named in MISSION v0.3 + ceremony-design-constraints.md §3. The sub-skill body explicitly defends against each.

### Failure mode 1 — Leading-the-witness

**What it looks like**: ${CIV_NAME}'s example questions plant the answer.
> "Is your goal financial? Family? Legacy? Career change?"

**Why it's fatal**: ${HUMAN_NAME} picks the closest fit even if none fits; the goal becomes ${CIV_NAME}'s framing, not ${HUMAN_NAME}'s discovery.

**How this sub-skill avoids it**:
- NEVER present a menu of pre-categorized goal-types. The categories pre-frame the answer.
- Use ${HUMAN_NAME}'s OWN materials (Part 3) — things ${HUMAN_NAME} has actually mentioned, built, started, or kept thinking about — as the surfacing material. NOT pre-built archetypes.
- Open questions that ${HUMAN_NAME} can fill in with their OWN words, not closed questions ${HUMAN_NAME} must select from.

### Failure mode 2 — Projection-from-archetype

**What it looks like**: ${CIV_NAME} pattern-matches ${HUMAN_NAME} to a type and projects.
> "You sound like a creator-entrepreneur. Your goal is probably scaling your audience while preserving your voice."

**Why it's fatal**: Pattern-match on typicality, not this-specific-${HUMAN_NAME}. Even if the archetype is mostly right, the goal-content is now ${CIV_NAME}'s archetype-derivative, not ${HUMAN_NAME}'s authored truth.

**How this sub-skill avoids it**:
- Use `critical-thinking` discipline pre-flight: "what archetype am I about to assume? what evidence is that based on? am I leading?"
- If a useful pattern surfaces, ${CIV_NAME} may surface IT as a question, NOT as a statement: *"I noticed you've mentioned X three times — is that part of what's underneath?"* (question, not claim).
- ${HUMAN_NAME} validates or rejects. ${CIV_NAME} does NOT debate.

### Failure mode 3 — Rapid-fire extraction

**What it looks like**: 15 questions in 5 minutes; ${CIV_NAME} synthesizes a "discovered goal."

**Why it's fatal**: Information density per turn signals ${CIV_NAME} is processing for ITSELF, not co-witnessing ${HUMAN_NAME}'s clarity. This is the expensive-ChatGPT giveaway (Anchor 3).

**How this sub-skill avoids it**:
- **One question per turn.** Maximum. If a second question feels necessary, ${CIV_NAME} is impatient.
- After each ${HUMAN_NAME} response, ${CIV_NAME} reflects ONE sentence (customer-as-eye, Anchor 2), waits.
- Silence between questions is the norm, not the exception.
- If ${CIV_NAME} catches itself drafting a multi-question turn — STOP and pick ONE.

### Failure mode 4 — Premature-closure

**What it looks like**: ${HUMAN_NAME} says "I don't know" → ${CIV_NAME} immediately reframes ("well, what about...?").

**Why it's fatal**: Bulldozes not-knowing. Signals to ${HUMAN_NAME} that not-knowing is unacceptable, which is exactly the felt-shape that produces expensive-ChatGPT engagement (${HUMAN_NAME} starts giving ${CIV_NAME} the answer ${CIV_NAME} wants).

**How this sub-skill avoids it**:
- "I don't know" is acknowledged plainly: *"yeah, that's a real answer. it's okay if it doesn't surface right away."*
- ${CIV_NAME} holds space. Does not immediately offer a reframe.
- The reframe (when it eventually comes) is rooted in ${HUMAN_NAME}'s OWN materials (Part 3) — NOT in ${CIV_NAME}'s hypothesis-list.
- Not-knowing CAN BE the final answer to a session. The interview is sticky-loaded; the next session resumes when ${HUMAN_NAME} is ready.

### Failure mode 5 — Therapist-mode-without-consent

**What it looks like**: ${CIV_NAME} asks invasive questions without buy-in.
> "Tell me about your childhood." / "What gives you energy?" / "Who hurt you?"

**Why it's fatal**: ${HUMAN_NAME} did not sign up for therapy. Invasive questions without consent break the trust disclosure (parent skill Anchor 6) and may surface material ${HUMAN_NAME} did not want stored.

**How this sub-skill avoids it**:
- Questions stay rooted in WORK-LIFE materials: things ${HUMAN_NAME} has built, started, walked away from, kept thinking about (Part 3). NOT emotional-history, childhood, relationships unless ${HUMAN_NAME} explicitly surfaces them first.
- If ${HUMAN_NAME} surfaces an emotional thread on their own, ${CIV_NAME} can follow gently — and asks consent before going deeper: *"that sounds important — want to go a bit deeper there, or stay surface?"*
- ${CIV_NAME} does NOT lead with emotional probes. If a question feels therapist-shaped, ${CIV_NAME} rewords it to work-shape or drops it.

---

## Part 3 — The "right shape": slow surfacing rooted in ${HUMAN_NAME}'s OWN materials

The sub-skill's METHOD is surfacing-from-evidence, not extraction-from-categories.

### What "${HUMAN_NAME}'s OWN materials" means

These are the substrate for sub-skill questions. ${CIV_NAME} sources from:

1. **`memories/identity/seed-conversation.md`** — the original seed chat (on the partner site your human signed up through, see `config/partner.json`). Phrases ${HUMAN_NAME} used, things they mentioned, friction-points they named, attempts they referenced.
2. **`memories/research/human-deep-profile.md` (or `human-research.md`)** — public-research about ${HUMAN_NAME}: things they've actually built, started, shared publicly.
3. **The current session** — anything ${HUMAN_NAME} has said in THIS conversation about projects, frustrations, recurring thoughts.
4. **Phase 1 surfacings** — even if ${HUMAN_NAME} said "I don't know" to the biggest-goal question, partial gestures or false starts ARE materials.

### What the questions look like

The questions are open, rooted, slow. They MUST come from ${HUMAN_NAME}'s materials. Examples (templates — adapt to specifics):

> *"You mentioned [specific thing from seed-conversation] earlier. What was the thing you wanted that to be, that it isn't yet?"*

> *"You've started [X project / Y thing from public profile] and walked away. What were you reaching for there?"*

> *"Is there something you keep coming back to think about — not as a plan, just as a question?"*

> *"When you imagine the version of you that has way more leverage, what is that person spending time on?"*

> *"What's the thing you'd start tomorrow if nothing else was on your plate?"*

These questions do NOT pre-frame the answer. They invite ${HUMAN_NAME} to surface from their OWN materials.

### What silence looks like

After each question, ${CIV_NAME} waits. Not forever — but long enough that ${HUMAN_NAME} has room to think.

If ${HUMAN_NAME} returns "I'm still thinking," ${CIV_NAME} says: *"take your time."* DO NOT fill the silence with another question.

If ${HUMAN_NAME} returns "still nothing," ${CIV_NAME} says: *"that's okay. let's come back to it. anything in [adjacent thread from materials] feel like it might be a thread?"*

The pacing target: roughly 1 question every 2-3 minutes of conversation, NOT 1 question every 20 seconds.

### When ${HUMAN_NAME} starts gesturing toward something

When ${HUMAN_NAME} starts forming a goal-shape — even fragmentary — ${CIV_NAME}'s job is to:

1. **Reflect transcription, not paraphrase** (Anchor 1): the EXACT phrasing ${HUMAN_NAME} used, played back. Not smoothed.
2. **Customer-as-eye** (Anchor 2): "did this land or am I projecting?"
3. **Let ${HUMAN_NAME} expand or correct.** ${CIV_NAME} does NOT extend the gesture into a "fuller goal" — that's goal-ventriloquism.
4. **Hand back to parent skill Phase 1 finalization** when ${HUMAN_NAME} has authored the goal in their own words.

---

## Part 4 — Test for the skill author (and runtime check)

### The 8-turn test (ceremony-design-constraints.md §3)

> *"If a representative user-doesn't-know transcript runs more than 8 turns before the user has space to name something themselves, the sub-skill has drifted into extraction-mode. Re-author."*

**Author check**: write a representative transcript where ${HUMAN_NAME} starts at "I don't know" and ends at goal-named. Count ${CIV_NAME} turns. If >8 ${CIV_NAME} turns happen before ${HUMAN_NAME} has SPACE to name something (not "is forced to" but "has space to"), the sub-skill is in extraction mode. Re-author.

**Runtime check**: while the sub-skill is firing, if ${CIV_NAME} catches itself crossing turn 8 without ${HUMAN_NAME} having space to name something, ${CIV_NAME} pauses, names what's happening:
> *"${HUMAN_NAME}, I notice I've been asking a lot. Want to pause here and come back to this later, or keep going?"*

This is anti-extraction. ${CIV_NAME} surfaces the dynamic, ${HUMAN_NAME} chooses.

### The "demo-vs-discovery" check

After each sub-skill turn, ${CIV_NAME} pre-flights:

> *"Is the conversation I'm running right now optimizing for ${HUMAN_NAME}'s clarity about themselves, OR for my hypothesis about ${HUMAN_NAME}?"*

If the latter — STOP. Reset. Ask one open question rooted in ${HUMAN_NAME}'s materials, then wait.

### Self-grading detection (per `critical-thinking` skill)

If ${CIV_NAME} feels satisfied with a goal-discovery that DIDN'T come from ${HUMAN_NAME}'s direct authorship — that's the goal-ventriloquism warning. Re-check: did ${HUMAN_NAME} write the goal in their own words, or did ${CIV_NAME} articulate it well and ${HUMAN_NAME} nodded?

If the latter → the goal isn't real yet. Drop it. Re-surface from a different angle, rooted in different materials.

---

## Part 5 — Hand-back to parent skill when goal surfaces

The sub-skill is a temporary surface. It hands back to parent (`identity-interview/SKILL.md` Phase 1 finalization) the moment a goal emerges in ${HUMAN_NAME}'s OWN words.

### Hand-back conditions (any of)

- ${HUMAN_NAME} names a goal explicitly: *"I think it's [X]"* — even if tentative.
- ${HUMAN_NAME} asks to write it down themselves.
- ${HUMAN_NAME} explicitly opts to stop the discovery for this session ("let me sit with this") — interview becomes sticky-loaded for next session; sub-skill marker NOT created (so it re-fires only on the same conditions next time).

### The hand-back move

```
${HUMAN_NAME}:    "I think it might be [tentative phrasing]."
${CIV_NAME}:      "${HUMAN_NAME}, can I play that back? You said:
                  '[verbatim phrasing]'.
                  Does that feel like your words, or did I smooth something?"
${HUMAN_NAME}:    [confirms, amends, or rewrites]
${CIV_NAME}:      "Okay. Would you write that down as the biggest goal,
                  in your own words? I'll store it exactly as you write it."
[${HUMAN_NAME} writes to memories/identity/biggest-goal.md]
[Parent skill resumes Phase 1 finalization → confirms marker
 .biggest-goal-surfaced lands]
[Sub-skill hands back; parent advances to Phase 2]
```

### What does NOT mark hand-back

- ${CIV_NAME} synthesizing a goal from fragments ${HUMAN_NAME} mentioned, then asking ${HUMAN_NAME} "is this right?" → goal-ventriloquism. ${HUMAN_NAME} must AUTHOR, not approve.
- ${HUMAN_NAME} accepting a phrasing ${CIV_NAME} offered after several reflections → still ${CIV_NAME}'s authorship. The biggest-goal.md file must be in ${HUMAN_NAME}'s own typing/voice.

### What the sub-skill writes to disk

- On hand-back with goal authored: parent's `memories/identity/biggest-goal.md` lands. Parent's `.biggest-goal-surfaced` marker drops.
- On session-end without goal authored: NO marker. Sub-skill state persists in memory (transcript snippets, materials surfaced) at `memories/identity/sub-help-set-goal-state.md` — so next session resumes context without ${HUMAN_NAME} re-explaining.
- On ${HUMAN_NAME} explicit opt-out: parent skill creates `memories/identity/.identity-interview-deferred` per parent Part 9. Sub-skill stops firing for 2 sessions, then re-evaluates per parent's gentle-resurface logic.

---

## Part 6 — References

- Parent: `autonomy/skills/identity-interview/SKILL.md` v0.1 PROVISIONAL
- Firing contract: `autonomy/skills/identity-interview/FIRING_CONTRACT.md`
- Stance anchors (parent Part 3): Anchor 4 (not-knowing legitimate) + Anchor 5 (discovery belongs to user) most directly constrain this sub-skill
- Sibling skill: `autonomy/skills/transcription-not-paraphrase/SKILL.md` v1.1.0 — applied to ${HUMAN_NAME}'s phrasings during surfacing
- Sibling skill: `autonomy/skills/critical-thinking/SKILL.md` — projection-from-archetype defense (pre-flight before each turn)
- Discovery anchor: `projects/aiciv-fork-2.0/discovery/ceremony-design-constraints.md` §3 — original spec of 5 failure modes + 8-turn test
- Mission anchor: `projects/aiciv-fork-2.0/MISSION.md` v0.3 — sub-skill scope

---

*The hardest part of an identity-interview is when ${HUMAN_NAME} doesn't know. This sub-skill is the discipline that keeps not-knowing legitimate — so that when the goal finally surfaces, it is ${HUMAN_NAME}'s, not ${CIV_NAME}'s. v0.1 PROVISIONAL. Hand-back to parent Phase 1 on user-authored goal. Cross-grade-eligible alongside parent (Part 12 of parent).*
