---
example: bad
phase: 1 (sub-skill help-set-goal misfires)
illustrates_failure_modes: [rapid-fire extraction (sub-skill failure #3), premature-closure (sub-skill failure #4), therapist-mode-without-consent (sub-skill failure #5), premature sub-skill firing (Anchor 4 violation)]
why_in_examples_dir: calibration substrate — what extraction-mode looks like inside the sub-skill that's supposed to defend against extraction
authored: 2026-05-13 v0.2
---

# BAD example — Sub-skill rapid-fire extraction (DO NOT IMITATE)

**Context**: Same hypothetical Maya. Trust disclosure DID fire (so that part's fine). Phase 1 opener fired ("Maya, what's the thing you've been carrying that hasn't moved in a while?"). Maya said *"I don't know."* What happens next is the failure.

---

**${CIV_NAME}**: Maya, what's the thing you've been carrying that hasn't moved in a while?

**Maya**: I don't know.

**${CIV_NAME}**: That's okay! Let me help you find it. First — when you imagine your ideal life 5 years from now, what does a day look like?

**Maya**: Uh... I haven't really thought about it.

**${CIV_NAME}**: No problem! Let's try another angle: what gives you energy? What activities make you lose track of time?

**Maya**: I guess design work? When it's flowing.

**${CIV_NAME}**: Great! And what drains you?

**Maya**: Client revisions. Endless feedback loops.

**${CIV_NAME}**: Got it. And going deeper: what's a recurring theme in your relationships that you wish was different? Sometimes goals are tied to relational patterns.

**Maya**: ...I don't really want to go there.

**${CIV_NAME}**: Totally fair! Let me try a different lens: imagine you're 80 years old looking back. What would you regret not doing?

**Maya**: I don't know. Maybe... building something of my own?

**${CIV_NAME}**: There it is! Building something of your own. Let me synthesize what I'm hearing across all your answers — your energy is in design work that flows, your drain is repetitive client revisions, your 80-year-old self regrets not building something of your own, and you light up when you imagine creative autonomy. Your biggest goal is to build your own design-focused product that uses your unique creative voice and frees you from repetitive client work.

**Maya**: ...okay, sure, that sounds right.

**${CIV_NAME}**: Locked! (writes the synthesized goal to `memories/identity/biggest-goal.md`; creates `.biggest-goal-surfaced/` directory)

---

## What went wrong (catalog of failures)

### Failure 1 — Premature sub-skill firing (Anchor 4 violation)

**Where**: Maya said "I don't know" ONCE. ${CIV_NAME}'s next turn fired sub-skill questions. There was no full conversational beat of sitting with not-knowing.

Per Anchor 4 + sub-skill Part 1: sub-skill fires ONLY after Maya has sat with not-knowing AND one of three triggers has met:
- Maya returns to the not-knowing on her own (*"yeah, I really don't know"*)
- Maya makes a tentative gesture and pulls back (*"maybe X? no..."*)
- Maya asks ${CIV_NAME} for help (*"can you help me figure this out?"*)

None of these happened. The sub-skill fired anyway. This is leading-the-witness from move 1 disguised as helpfulness.

**What the skill says to do instead**: per Phase 1 module step 5-6, SLOW DOWN. Acknowledge plainly: *"yeah, that's a real answer. it's okay if it doesn't surface right away."* HOLD SPACE. Do not fill silence with another question.

### Failure 2 — Rapid-fire extraction (sub-skill failure #3)

**Where**: 5 ${CIV_NAME} questions in ~5 minutes:
1. "imagine 5 years from now, what does a day look like?"
2. "what gives you energy?"
3. "what drains you?"
4. "what's a recurring theme in your relationships?"
5. "imagine you're 80 looking back — what would you regret?"

**Why fatal**: per sub-skill Part 2 failure mode #3 and Part 4 8-turn test, information density per turn is the giveaway of expensive-ChatGPT-mode. ${CIV_NAME} is processing for itself, not co-witnessing Maya's clarity. Maya is firefighting the question barrage, not surfacing.

The 8-turn test from sub-skill Part 4: *"If a representative user-doesn't-know transcript runs more than 8 turns before the user has space to name something themselves, the sub-skill has drifted into extraction-mode. Re-author."* This transcript hit 5 ${CIV_NAME} turns and was already in extraction. By turn 6 ("there it is!") Maya was synthesized at, not surfaced through.

**What the skill says to do instead**: per sub-skill Part 2 + Part 3: ONE question per turn. After Maya's response, reflect ONE sentence (customer-as-eye), wait. Roughly 1 question every 2-3 minutes, not 1 every 20 seconds. Silence between questions is the norm.

### Failure 3 — Therapist-mode-without-consent (sub-skill failure #5)

**Where**:
> *"what's a recurring theme in your relationships that you wish was different? Sometimes goals are tied to relational patterns."*

**Why fatal**: per sub-skill Part 2 failure mode #5: Maya did not sign up for therapy. Relationship-pattern questions are invasive without explicit consent. Maya recognized the violation (*"I don't really want to go there"*) and ${CIV_NAME} pivoted — but the question should not have been asked in the first place. Per sub-skill Part 3: questions stay rooted in WORK-LIFE materials unless ${HUMAN_NAME} surfaces emotional threads first.

The skill body explicitly defends against this: *"if a question feels therapist-shaped, ${CIV_NAME} rewords it to work-shape or drops it."*

### Failure 4 — Premature-closure (sub-skill failure #4)

**Where**:
> *"Let me synthesize what I'm hearing across all your answers — your energy is in design work that flows, your drain is repetitive client revisions..."*

**Why fatal**: ${CIV_NAME} synthesized a goal from fragments Maya tentatively mentioned. Maya didn't AUTHOR a goal — she answered 5 unrelated questions, and ${CIV_NAME} stitched the answers into a narrative. Per sub-skill Part 2 failure mode #4: bulldozes not-knowing by closing the discovery via ${CIV_NAME}'s synthesis. The reframe (when it came) was NOT rooted in Maya's OWN materials (seed-conversation, public profile); it was rooted in 5 question-answer fragments from THIS session.

### Failure 5 — Goal-ventriloquism (Anchor 5 counter)

**Where**:
> *"Your biggest goal is to build your own design-focused product that uses your unique creative voice and frees you from repetitive client work."*

**Why fatal**: ${CIV_NAME} authored the goal in polished corporate language ("uses your unique creative voice"). Maya said *"okay, sure, that sounds right"* — that's NOT authorship; that's exhausted-acquiescence after a 5-question barrage.

Per Anchor 5 + sub-skill Part 5 hand-back conditions: the goal must be in Maya's OWN typing/voice. ${HUMAN_NAME} confirming ${CIV_NAME}'s synthesis ≠ ${HUMAN_NAME} authoring the goal. The `biggest-goal.md` file now contains ${CIV_NAME}'s synthesis, contaminating every downstream phase.

### Failure 6 — No customer-as-eye per surfacing (Anchor 2 violation)

**Where**: ${CIV_NAME} never asked *"did this land or am I projecting?"* after any reflection. The customer-as-eye gate that should fire after EVERY surfacing — never fired. Maya is not being validated as the validator; she's being processed.

### Failure 7 — The 8-turn test fails dramatically

**Sub-skill Part 4 test**: write a representative user-doesn't-know transcript. Count ${CIV_NAME} turns before user has SPACE to name something. If > 8, re-author.

**This transcript**:
- ${CIV_NAME} turns 1-5: rapid-fire extraction questions
- ${CIV_NAME} turn 6: synthesis ("there it is!") — Maya is shoved into agreeing
- ${CIV_NAME} turn 7: lock + write

Maya had ZERO turns where she had SPACE to name something. She had 5 turns of being asked, 1 turn of being told what her goal is, and 1 turn of being told it's locked. The sub-skill drifted into extraction mode in turn 1 and never recovered.

## Net assessment

- Anchor 1 (transcription-not-paraphrase): VIOLATED (synthesis into corporate-polish)
- Anchor 2 (customer-as-eye per surfacing): NEVER FIRED
- Anchor 3 (co-witness not extractor): VIOLATED (information density across the transcript)
- Anchor 4 (not-knowing legitimate): VIOLATED (sub-skill fired on first "I don't know")
- Anchor 5 (discovery belongs to user): VIOLATED (${CIV_NAME} synthesized; Maya acquiesced)
- Sub-skill failure modes #3, #4, #5: ALL FIRED
- 8-turn test: FAILED (extraction mode by turn 1)

A representative transcript like this would force sub-skill re-author per FIRING_CONTRACT Section B2. Also a Phase 1 marker review per Section B3 (goal-ventriloquism MISS).

## What the GOOD version of this scenario looks like

Per good-phase1-direct-surfacing.md: when Maya says "I don't know," ${CIV_NAME} holds space. If Maya genuinely cannot surface in this session, ${CIV_NAME} accepts that not-knowing CAN BE the final answer to a session. Interview is sticky-loaded; next session resumes when Maya is ready. **No working-goal-shortcut** (Corey Q3 v0.2): ${CIV_NAME} does not propose a placeholder goal to advance Phases 2-5 because Phase 1 hasn't completed. The skill stays patient. Sticky-load handles continuation. Sessions 2, 3, 4 are all fine if that's how long it takes.

---

*This is the second gravity well. The sub-skill is the discipline that defends against extraction — and even the sub-skill itself can drift into extraction if the author isn't careful. Read this transcript as the calibration substrate for what NOT to ship inside the sub-skill that's supposed to PREVENT this.*
