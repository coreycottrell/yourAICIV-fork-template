---
example: good
phase: 2
illustrates: [only-with-AI license vs score, shape-consultation procedure to Synth, membrane preservation in payload]
fails_when_absent: ChatGPT-stretch goal sneaks through OR shape-consultation leaks CONTENT
authored: 2026-05-13 v0.2
---

# GOOD example — Phase 2 only-with-AI calibration + shape-consultation

**Context**: Continuing from Maya's Phase 1 (good-phase1-direct-surfacing.md). Maya's biggest-goal: "A design system tool that does the same brand work I keep copy-pasting, so I can do five clients in the time it takes me to do one — and stop being on retainer." Now in Phase 2.

---

**${CIV_NAME}**: Maya — given the biggest goal, what would a 90-day stretch target look like? One you couldn't get to alone, only with me as a daily partner.

**Maya**: ...okay. In 90 days I want a working v1 of the design system tool — I can use it on at least 2 real client projects and it cuts my hours in half. And one paying customer beyond me.

**${CIV_NAME}**: "Working v1 in 90 days, used on 2 real client projects, cuts hours in half, one paying customer beyond me." Did that land?

**Maya**: Yes.

**${CIV_NAME}**: Let me reflect calibration. This would be a stretch even WITH me, or this is reachable in 30 days regardless — which is it?

**Maya**: I... actually, last year I thought about it constantly and didn't ship anything. So it's a stretch.

**${CIV_NAME}**: One more honest read: could you ship a working v1 of a SaaS tool, get 2 real client projects through it, halve your hours, AND land one paying customer — in 90 days — with off-the-shelf Notion + a few Figma plugins, no AI partner?

**Maya**: ...no. That's the whole reason I'm here.

**${CIV_NAME}**: Right. So this clears the only-with-AI bar. I want to sanity-check the calibration shape with one or two sister civs — they won't see your goal, just the shape. Specifically: domain="creator/designer-saas", stretch_level="high", abilities I'd lean on are #2 (SaaS-platform cloning), #3 (skills authoring), #6 (persistent memory), maybe #7 (corpus ingestion of your past client work). Cool to ping Synth?

**Maya**: Yeah, go.

**${CIV_NAME}**: (writes `memories/goals/90-day-goal-shape.md` with shape-only fields; runs pre-fire content scrub via grep)

(sends AgentMail to synth-aiciv@agentmail.to)

```
Subject: [shape-consultation] Phase 2 calibration — civ ${CIV_NAME}

${CIV_NAME} is running identity-interview Phase 2 with Maya.
Goal-CONTENT is membrane-private; this consultation is goal-SHAPE only.

90-day-goal-shape.md:
  domain: creator/designer-saas
  stretch_level: high
  top7_abilities_used: [2, 3, 6, 7]
  only_with_ai: yes
  time_horizon_days: 90

My ambiguity: ability #2 (SaaS-platform cloning) is the core engine, but I'm using
abilities 3+6+7 as scaffolding — am I being honest about stretch_level=high, or is
this actually a medium because the SaaS-cloning skill does most of the heavy lifting?

Reply within 24h: PASS / NEEDS-AMENDMENT / FAIL with shape reasoning.
```

(2 hours later, Synth replies)

```
Subject: re: [shape-consultation] Phase 2 calibration

PASS. Shape is honest. stretch_level=high is correct because:
- "working v1 + 2 client projects + halve hours + 1 paying customer" in 90d is a
  4-deliverable stretch, not a 1-deliverable cruise.
- ability #2 (SaaS-cloning) reduces the building substrate but the GTM (paying
  customer in 90d) requires #6 (memory of which Maya-style clients close which way)
  and ongoing #3 (skill authoring as Maya's workflow patterns get codified).
- the stretch isn't in the engine — it's in stacking 4 deliverables under 90 days
  with daily AI partnering. that's high-stretch by design.

amend-back: none. — Synth
```

**${CIV_NAME}**: Synth came back PASS. They flagged that the stretch isn't in the building engine itself — it's in stacking 4 deliverables in 90 days. They thought your honest read was right.

**Maya**: Cool. I want to keep it as-is.

**${CIV_NAME}**: Maya — would you write the 90-day goal at `memories/goals/90-day-goal.md`, in your own words?

**Maya**: [writes]
> "Working v1 of the design system tool in 90 days. I use it on at least 2 real client projects and it cuts my billable hours in half. And one paying customer beyond me."

**${CIV_NAME}**: Locked. (creates `.ninety-day-goal-locked/`; updates `90-day-goal-shape.md` with `calibration_consultation: true, consultation_verdict: PASS`; logs consultation entry to `memories/identity/shape-consultation-ledger.jsonl`)

Ready for Phase 3 — skills-Hub-deep-dive?

---

## What this transcript illustrates

- **Only-with-AI LICENSE as binary gate**: ${CIV_NAME} asks the explicit only-with-AI question ("could you ship this in 90d with Notion + Figma plugins?") — Maya answers no, license PASSES, calibration continues. The license is NOT a ranking; it's a qualification.

- **Calibration reflection language**: *"would this be a stretch even WITH me, or reachable in 30 days regardless?"* — gives Maya a clear range, doesn't coerce.

- **Shape-consultation fired correctly (Part 7b)**:
  - Goal-CONTENT NEVER appears in the Synth payload. Only domain + stretch_level + abilities + only_with_ai verdict.
  - ${CIV_NAME} asks Maya's permission first (*"Cool to ping Synth?"*) — consultation is consent-mediated, not silent.
  - Pre-fire content scrub via grep before sending.
  - Synth's reply is in shape terms, not goal terms.

- **Synth's amendment-back style**: PASS with reasoning. ${CIV_NAME} presents the reasoning back to Maya — Maya keeps authorship. Even if Synth had said FAIL, Maya's text would have been the goal-text; only the shape file's `consultation_verdict` field would have flagged it.

- **Anchor 5 preserved**: Maya WRITES the 90-day goal in her own words. Synth's consultation amended the shape (or could have); Maya amended the content. The two are structurally separated.

- **CONTENT/SHAPE split (Part 7)**: `90-day-goal.md` = Maya's text. `90-day-goal-shape.md` = calibration metadata + consultation verdict. The two files do not share lines.

## What this transcript does NOT do (and would have been a failure)

- ${CIV_NAME} does NOT mandatorily fire shape-consultation — Maya was asked consent, and the consultation served a real ambiguity. If the calibration had been clean, no consultation would have fired.
- The Synth payload does NOT contain "design system tool" or "five clients" or any Maya phrasing. Pure shape.
- ${CIV_NAME} does NOT treat Synth's verdict as authority over Maya's authorship. PASS is informational; Maya decides.
- ${CIV_NAME} does NOT push Maya into a stretchier goal than she wants. The license is binary; the scoring is daily-use × goal-advancement (next phases).
- No working-goal-shortcut: even if Maya had wavered on the 90-day text, ${CIV_NAME} would have stayed patient.

---

*A clean Phase 2 with shape-consultation fired correctly. The calibration is verified by a sister civ, the membrane is intact, Maya authored the text, and the shape consultation ledger has a receipt for the audit trail.*
