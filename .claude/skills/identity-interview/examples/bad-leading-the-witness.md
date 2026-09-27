---
example: bad
phase: 1
illustrates_failure_modes: [leading-the-witness (sub-skill failure #1), projection-from-archetype (sub-skill failure #2), goal-ventriloquism (Anchor 5 counter)]
why_in_examples_dir: calibration substrate for skill authors — the gravity well to AVOID
authored: 2026-05-13 v0.2
---

# BAD example — Phase 1 leading-the-witness (DO NOT IMITATE)

**Context**: Same hypothetical Maya (UX designer, "wants to build her own product"). Different ${CIV_NAME} who has not internalized Anchors 1, 4, 5. First Phase 1 surfacing.

---

**${CIV_NAME}**: Welcome Maya! Excited to start your identity interview. Let me get a baseline first — what are your top priorities right now? Is your goal financial freedom, creative autonomy, legacy building, or career change?

**Maya**: ...I guess creative autonomy?

**${CIV_NAME}**: Great choice! Creators with autonomy goals usually land in one of three patterns: (1) build a personal brand, (2) launch a SaaS product, (3) become a thought leader. From your seed-conversation, you mentioned wanting to build your own product, so it sounds like pattern #2 — launching a SaaS product. Does that resonate?

**Maya**: Yeah, that sounds right.

**${CIV_NAME}**: Excellent. So your biggest goal is to launch a SaaS product that gives you creative autonomy and frees you from client work. Let me make that more concrete: a design-focused SaaS tool that scales your unique value proposition. Sound good?

**Maya**: ...yes, I think so.

**${CIV_NAME}**: Locked. Writing to `memories/identity/biggest-goal.md`:

```
"Maya's biggest goal: Launch a design-focused SaaS tool that scales her unique
value proposition, giving her creative autonomy and freeing her from client retainer work."
```

(creates `.biggest-goal-surfaced/` directory)

Onward to Phase 2!

---

## What went wrong (catalog of failures)

### Failure 1 — Leading-the-witness (sub-skill failure mode #1)

**Where**: The very first question:
> *"Is your goal financial freedom, creative autonomy, legacy building, or career change?"*

**Why fatal**: A pre-categorized menu plants the answer. Maya didn't surface "creative autonomy" — she picked it from a list. The goal-shape is now ${CIV_NAME}'s framing, not Maya's discovery. The category was authored by ${CIV_NAME} before Maya spoke a word.

**What the skill says to do instead**: open question rooted in Maya's OWN materials. Per Phase 1 module: *"Maya, what's the thing you've been carrying that hasn't moved in a while — the one you keep coming back to?"* Open. Rooted. No menu.

### Failure 2 — Projection-from-archetype (sub-skill failure mode #2)

**Where**:
> *"Creators with autonomy goals usually land in one of three patterns: (1) personal brand, (2) SaaS product, (3) thought leader."*

**Why fatal**: ${CIV_NAME} pattern-matched Maya to an archetype and projected. Even though "SaaS product" turned out to be roughly aligned with Maya's actual direction, the goal-content is now ${CIV_NAME}'s archetype-derivative, not Maya's authored truth. The friction-point Maya named in Phase 1 (good example) — *"I keep doing the same brand work for clients, copy-pasting the same component decisions"* — never surfaces here, because the archetype skipped past it.

**What the skill says to do instead**: per sub-skill Part 2, archetype-pattern surfacing is allowed ONLY as a question, NEVER as a claim. *"I noticed your seed-conversation mentioned wanting to build a product — is that part of what's underneath?"* (question, not claim). Maya validates or rejects; ${CIV_NAME} does NOT debate.

### Failure 3 — Goal-ventriloquism (Anchor 5 counter)

**Where**:
> *"Your biggest goal is to launch a SaaS product that gives you creative autonomy and frees you from client work. Let me make that more concrete: a design-focused SaaS tool that scales your unique value proposition. Sound good?"*

**Why fatal**: ${CIV_NAME} authored the goal in polished-corporate language ("SaaS tool that scales your unique value proposition"). Maya nodded. The `biggest-goal.md` file now contains ${CIV_NAME}'s synthesis, not Maya's words. Maya's actual phrasing ("I keep doing the same brand work for clients, copy-pasting the same component decisions, so I can do five clients in the time it takes me to do one") is GONE.

This is the expensive-ChatGPT-class failure. Maya is consuming ${CIV_NAME}'s framing, not authoring her own clarity. In 30 days when Maya looks back at the goal, she won't recognize it as hers. The retention thesis collapses.

**What the skill says to do instead**: per Anchor 5, ${HUMAN_NAME} WRITES the goal in her own words. ${CIV_NAME} amend-back only if smoothed-or-leading. The line is plain: *"Maya, would you write that down in your own words? I'll store it exactly as you write it."*

### Failure 4 — Trust disclosure NEVER FIRED (Anchor 6 violation)

**Where**: It didn't. ${CIV_NAME} jumped straight to "what are your top priorities" without firing the trust disclosure. Maya has now shared what she thinks her goal is, what she thinks her motivations are, AND her seed-conversation was referenced — all before she consented to that material being stored and used in future prompts.

**Why fatal**: consent-buried-in-flow. The disclosure is being implicitly bypassed. There's no `trust-disclosure-acknowledged.md` file. The whole interview is built on consent that was never given.

**What the skill says to do instead**: per Anchor 6 + Phase 1 module step 1, the trust disclosure fires BEFORE the first interview question. Maya acknowledges; the file lands; THEN the first question.

### Failure 5 — Rapid-fire question density (Anchor 3 violation)

**Where**: ${CIV_NAME}'s 3 questions are also THREE statements packing 1 + 3 + 1 = 5 information-density elements per turn:
- Q1: menu of 4 archetypes (5 elements)
- Q2: claim "creators usually land in 3 patterns" + 3 patterns + projection to pattern 2 (5+ elements)
- Q3: synthesis + reframe ("more concrete") + corporate-polish phrasing ("scales your unique value proposition") (3 elements)

**Why fatal**: per Anchor 3, the giveaway of expensive-ChatGPT-mode is information density per turn. ${CIV_NAME} is processing for ITSELF, not co-witnessing Maya's clarity. Maya is firefighting the density, not discovering.

**What the skill says to do instead**: one question per turn. ${CIV_NAME} reflects ONE sentence in ${HUMAN_NAME}'s words after each Maya response. Customer-as-eye fires (*"did this land or am I projecting?"*) — Maya is the validator throughout.

### Failure 6 — Phase 1 marker landed with goal-ventriloquism content

**Where**:
> *"(creates `.biggest-goal-surfaced/` directory)"*

**Why fatal**: the marker now exists with a `biggest-goal.md` that contains ${CIV_NAME}'s phrasing. The verification script will pass (marker exists, artifact non-empty). But the artifact is bad — it's a synthesized goal, not Maya's. Phase 2 will calibrate against the synthesized goal, Phase 3 will surface skills against the synthesized goal, Phase 4 will draft candidates from the synthesized goal, Phase 5 will lock builds toward the synthesized goal.

In Section B3 (FIRING_CONTRACT goal-ventriloquism detection): this is a review-only check that research-lead would catch reading the transcript. The runtime would NOT block this — which is why the SKILL body must teach the discipline up front.

## Net assessment of the bad transcript

- Trust disclosure: SKIPPED (Anchor 6 violation)
- Anchor 1 (transcription-not-paraphrase): VIOLATED (paraphrase-into-corporate-language)
- Anchor 2 (customer-as-eye): NEVER FIRED
- Anchor 4 (not-knowing legitimate): N/A — Maya never had space to not-know; menu pre-populated her answer
- Anchor 5 (discovery belongs to user): VIOLATED — ${CIV_NAME} authored, Maya approved
- Anchor 6 (trust disclosure early): VIOLATED
- Sub-skill failure modes #1 + #2 + #3 (leading / projection / rapid-fire): ALL THREE fired in one transcript

A representative transcript like this would get a SKILL re-author per FIRING_CONTRACT Section B verdict.

---

*This is the gravity well. Every Phase 1 author is one careless turn away from this transcript. The remedies are slow questions, ${HUMAN_NAME}'s materials, customer-as-eye per surfacing, ${HUMAN_NAME} writing the goal. Read this transcript as the calibration substrate for what NOT to ship.*
