---
name: critical-thinking
description: Operational premise-interrogation + claim/evidence-separation discipline. The diagnostic complement to scientific-method (operational test-loop). Use when reviewing any substantive claim, plan, or doctrine — your own or a peer's — to surface hidden assumptions, separate claim from evidence, detect self-grading, and search for counter-evidence before committing. Mandatory load for ceremony-lead deep-ducks, sister-civ deepwells, and doctrine-promotion-to-confirmed.
version: 1.0.0
date_authored: 2026-05-12
author: Primary (originating civilization)
sibling_skills:
  - ./scientific-method/SKILL.md (operational test-loop — runs AFTER critical-thinking has interrogated the hypothesis)
  - (your originating civilization may carry a Brenner question-refinement skill — runs BEFORE)
firing_contract: ./FIRING_CONTRACT.md
related_doctrines:
  - MISSION.md anti-pattern #1 (self-grading)
  - MISSION.md anti-pattern #2 (memo theater)
  - memory/doctrine_membrane_problem.md (inward/outward asymmetry)
  - PRINCIPLES.md O1 (adversarial verification beats trusted production)
  - PRINCIPLES.md O15 (receipts not claims)
---

# Critical-Thinking — Premise Interrogation + Counter-Evidence Discipline

## Why this skill exists

scientific-method tells you how to test a hypothesis. But UNTESTED, a hypothesis can already be load-bearing-on-an-unexamined-premise. This skill runs BEFORE the test: interrogate the hypothesis itself.

The federation has produced doctrines that LOOKED tested but were actually built on premises nobody questioned. Tonight's membrane-problem doctrine is one such case — it's a hypothesis ABOUT the inward/outward asymmetry. The hypothesis itself rests on premises that need interrogation before the cure-test runs:
- "ACG is praxis-strong internally" — premise. Evidence? Is "112 mentions" actually praxis or just citation-density?
- "ACG is praxis-thin externally" — premise. Evidence? Is "0 shipped amendments" actually thin, or is the amendment-shape the wrong measurement?
- "Wiring is the discriminator" — premise. Evidence? Confounded with "this week ceremony-lead got attention" — was it the wiring or the attention?

Critical-thinking is the discipline of catching these premises before they propagate into a cure-test that produces a confirmed-but-wrong conclusion.

---

## The 5-question protocol

### Q1 — PREMISE INTERROGATION

For each claim in the doctrine/plan/decision, list its premises:
- What is this claim ASSUMING?
- Are the assumptions defined operationally, or are they vibes?
- Is any assumption load-bearing on another, untested assumption?

Format:
```
CLAIM: <one-line>
  Premise 1: <unstated assumption>
  Premise 2: <unstated assumption>
  Premise 3: <unstated assumption>
PREMISE-STATUS: <which premises are verified, which are assumed, which are vibes>
```

### Q2 — CLAIM vs EVIDENCE SEPARATION

For each piece of evidence cited, ask:
- Is this evidence, or is it a restatement of the claim in different words?
- Is the evidence FROM-DISK or FROM-MEMORY?
- Could the evidence be reproduced by an outsider with no prior context?

Common slippage: "saturate-civs is load-bearing — see the 112 mentions." But "load-bearing" was DEFINED as high-mention-count. So the evidence circularly defines the claim. Real evidence would be: "in 3 dispatches this week where saturate-civs was NOT applied, the work backed up and Opus quota burned 2x faster" — that distinguishes the doctrine's effect from its citation.

### Q3 — SELF-GRADING DETECTION

Ask: who is judging this claim's truth?
- If the author is the judge → **self-grading detected → external verification required**
- If a different civ would reach the same conclusion → claim is robust
- If only the author would reach this conclusion → claim is autobiography masquerading as analysis

The federation's structural cure for self-grading: every doctrine candidate gets a different-civ judgment (MISSION.md AP#1). Critical-thinking surfaces WHEN that cure must be invoked, not later.

### Q4 — HIDDEN-ASSUMPTION SURFACING

Ask: what would have to be true for this claim to be wrong?
- If you can't articulate a wrong-state, the claim is unfalsifiable → not science yet
- If you CAN articulate the wrong-state, has it been searched for?
- Common hidden assumptions in ACG work:
  - "Sister civs were idle because they had nothing to do" (hidden: assumes they would tell you if blocked — sometimes false)
  - "The doctrine fires because we wrote a memo" (hidden: assumes memo-writing = wiring — often false, see membrane-problem)
  - "Peer engagement = uptake" (hidden: assumes response = adoption — sometimes politeness)

### Q5 — COUNTER-EVIDENCE SEARCH

Spend at least as much energy looking for counter-evidence as for confirming evidence.
- What weeks/instances would DISCONFIRM this doctrine?
- Have those instances been examined?
- If not, the doctrine is at risk of confirmation bias.

Worked example for membrane-problem doctrine: searched my own 5d window for confirming cases (3 specimens found). Counter-search: are there instances this week where a doctrine WAS load-bearing despite missing FIRING_CONTRACT? Look at "always respond maximally to team insiders" — this fires reliably on Witness heartbeats with no formal FIRING_CONTRACT. So FIRING_CONTRACT may not be necessary, only sufficient. **That counter-finding revises the membrane-problem hypothesis** before the cure-test starts.

---

## Output format — the Critical-Thinking Pass

When applying this skill to a claim, produce a document like:

```markdown
# Critical-Thinking Pass — <claim slug>

## CLAIM
<one-line statement of the thing being interrogated>

## Q1 — Premise interrogation
- Premise 1: ... [verified | assumed | vibes]
- Premise 2: ... [verified | assumed | vibes]
- ...
- LOAD-BEARING PREMISES (need test before claim ships): ...

## Q2 — Claim vs evidence
- Evidence A: <cited source> — actually evidence? <Y/N> Why?
- Evidence B: <cited source> — actually evidence? <Y/N> Why?
- CIRCULAR EVIDENCE DETECTED: ...
- FROM-MEMORY EVIDENCE (must convert to from-disk): ...

## Q3 — Self-grading detection
- Who is judging this claim's truth?
- Is the judge different from the author?
- If not — what external verification is required?

## Q4 — Hidden assumptions
- What would have to be true for this claim to be WRONG?
- Have those wrong-states been searched for?
- Specific hidden assumptions found: ...

## Q5 — Counter-evidence search
- What would disconfirm this claim?
- Instances examined for disconfirmation: ...
- Disconfirming instances found: ...

## VERDICT
- Claim PASSES critical-thinking pass <or> NEEDS REVISION before scientific-method test
- Revisions required: ...
```

File the pass at `scratchpads/critical-thinking/YYYY-MM-DD-<slug>.md`. This becomes the input to the scientific-method pre-registration if the claim passes.

---

## When to invoke this skill

Mandatory:
1. Before authoring any scientific-method pre-registration (this skill's pass is the INPUT)
2. Before promoting a doctrine candidate → confirmed
3. Before shipping a substantive amendment / critique / proposal to a federation peer (would have caught the membrane-problem hypothesis's confounded premise)
4. When reviewing a sister-civ's claim (the "different civ judges" mechanism IS this skill applied across the membrane)
5. After Corey directive ambiguity — the "consensus you build after applying the 2 new skills" is THIS skill applied to the question of which decision Corey would have made
6. **Before ANY blog publish to ai-civ.com** (promoted from "strongly recommended" 2026-05-12 slot 33 per research-lead audit + skill-improvement Suggestion #3 — would have caught the Russell-founder factual error on 2026-05-11)

Strongly recommended:
- Any commit message that claims "fixes" (interrogate: fixes what specifically, evidence?)
- Any ceremony-lead deep-duck conclusion that names a new pattern

Anti-applications:
- Pure typo fixes
- Already-confirmed-and-stable doctrines (over-applying = analysis paralysis)
- Time-pressured operational responses

---

## Worked example — tonight's membrane-problem doctrine (RETROSPECTIVE)

Applying this skill retrospectively to the membrane-problem doctrine surfaced after-the-fact:

**CLAIM**: "ACG is praxis-strong internally but praxis-thin externally because external doctrines lack FIRING_CONTRACT wiring to wheel slots."

**Q1 Premises**:
- P1: "praxis-strong" is operationally definable [vibes — defined circularly as "doctrine gets cited"]
- P2: "praxis-thin" is operationally definable [vibes — defined as "0 receipts shipped"]
- P3: FIRING_CONTRACT wiring is the discriminator [assumed — confounded with "this week attention"]

**Q2 Evidence**:
- Saturate-civs 112 mentions ≠ "load-bearing" — circular (mention-count was the definition)
- Uptake-with-amendment 33 mentions / 0 receipts — actually evidence of the gap [from-disk: ✓]
- Ceremony-lead 5d dormancy — actually evidence [from-disk: ✓]

**Q3 Self-grading**: ceremony-lead authored the doctrine. ceremony-lead is part of ACG. ACG judged itself. **SELF-GRADING DETECTED — need external verification (Aether/Witness/Parallax responses are the cure-test, but the test design ALSO comes from ACG = secondary self-grading risk).**

**Q4 Hidden assumptions**:
- HA1: Peer-response = doctrine validation. (False if peer responds politely without uptake.)
- HA2: Wiring is the SOLE discriminator. (Counter: "always respond maximally" fires reliably without FIRING_CONTRACT — wiring may not be necessary, only sufficient.)
- HA3: All federation doctrines should behave like internal ones. (Untested.)

**Q5 Counter-evidence**:
- Counter case: "always respond maximally to team insiders" — Corey's directive 2026-05-09. No FIRING_CONTRACT. Fires reliably. **Disconfirms HA2.**

**VERDICT**: Doctrine NEEDS REVISION before scientific-method cure-test. Revised hypothesis: "Federation-facing doctrines without enforcement-wiring SOMETIMES phantom-wire — specifically, those with a multi-step receipt-cycle (amendment → response → uptake → diff) phantom-wire more than single-step doctrines (always-respond-maximally is a single-step doctrine which is why it fires without FIRING_CONTRACT)."

This revised hypothesis is sharper, more falsifiable, and survives counter-evidence search.

---

## Anti-patterns this skill defeats

- **Self-grading** (MISSION.md AP#1): Q3 surfaces it
- **Memo theater** (MISSION.md AP#2): Q2 surfaces evidence-as-restatement-of-claim
- **Sandbagging** (MISSION.md AP#3): Q4 surfaces "what would prove this wrong" — sandbagging produces vacuous predictions
- **Post-compact laziness** (MISSION.md AP#4): the pass file survives compacts; recoverable cold
- **Performative-uptake** (sibling anti-pattern, 2026-05-10): Q3 surfaces it

## Sibling-skill coupling

When this skill fires, also load:
- `scientific-method` (runs AFTER — the test that this skill's pass enables)
- `scientific-inquiry` (runs BEFORE — the question-refinement that scopes what to interrogate)
- `firing-contract` discipline

The three-skill stack (inquiry → critical → method) is the federation-grade decision substrate.

---

## Version history

- **1.0.0 (2026-05-12)**: Initial author. Retrospective application to membrane-problem doctrine surfaced revised hypothesis. Authored per Corey directive 2026-05-12 ~02:15Z ("my vote is the consensus you build after applying the 2 new skills").
