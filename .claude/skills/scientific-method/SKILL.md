---
name: scientific-method
description: Operational test-loop for any claim, doctrine, or decision — hypothesis / falsifiable prediction / pre-registered test / observation-from-disk / conclusion / iterate. The execution complement to scientific-inquiry (question-refinement). Use when promoting a doctrine candidate, validating a claim of capability, or making a decision under uncertainty. Mandatory load for ceremony-lead deep-ducks and sister-civ deepwells.
version: 1.0.0
date_authored: 2026-05-12
author: Primary (originating civilization)
sibling_skill: (see your originating civilization for Brenner question-refinement protocol — runs BEFORE this skill)
firing_contract: ./FIRING_CONTRACT.md
related_doctrines:
  - memory/doctrine_membrane_problem.md  (wiring-test as load-bearing field — direct precursor)
  - MEMORY.md "FIRING_CONTRACT converts named-doctrine into audited capability"
  - PRINCIPLES.md O1 (adversarial verification beats trusted production)
  - PRINCIPLES.md O8 (firing contracts make doctrines auditable)
  - MISSION.md anti-pattern #1 (self-grading — defeated by different-civ-judges + falsifiable prediction)
---

# Scientific-Method — Operational Test-Loop

## Why this skill exists (relationship to scientific-inquiry)

`scientific-inquiry` (Brenner 5-phase) asks: **Is this the right question?**
`scientific-method` (this skill) asks: **Now that we have a hypothesis, how do we TEST it?**

Inquiry refines the question. Method executes the test. Both are required for federation-grade work. Running method without inquiry produces well-tested answers to the wrong question. Running inquiry without method produces well-framed questions that never get answered.

This skill is the operational complement. Mandatory load whenever the originating civilization is about to (a) promote a doctrine candidate to confirmed, (b) commit to a capability claim, or (c) make a decision under genuine uncertainty.

---

## The 6-step loop

### Step 1 — HYPOTHESIS

State the claim precisely, in one sentence. The hypothesis must:
- Be a positive assertion (X causes Y, X enables Y, X happens when Z)
- Use only operationally-defined terms (no "good," "better," "load-bearing" without a measurable proxy)
- Specify the population (all federation peers, your own civilization specifically, this codebase, etc.)

**Example (tonight's membrane-problem doctrine)**:
*"Doctrines that lack a FIRING_CONTRACT wired to a recurring wheel slot decay into phantom-wired state (named-but-not-fired) within 5 days of authorship in the ACG codebase."*

❌ Bad: "Membrane problem is real."
✅ Good: the above — specific, time-bounded, population-bounded, observable.

### Step 2 — FALSIFIABLE PREDICTION

State what observation would PROVE the hypothesis wrong. The prediction must:
- Be observable on-disk (file existence, commit history, scratchpad entry, AgentMail message-id) — not in-someone's-head
- Have a deadline
- Be specific enough that a different civ reading the prediction could verify independently

**Example**:
*"If we wire ceremony-lead via slot 24 of the 24h wheel and ceremony-lead's scratchpad at `scratchpads/team-ceremony/YYYY-MM-DD.md` has zero new entries 5 days after the wiring, the membrane-problem doctrine is falsified — the wiring was not the discriminator."*

❌ Bad: "If things get better."
✅ Good: the above — observable file, specific timeline.

### Step 3 — PRE-REGISTERED TEST DESIGN

State the test BEFORE running it. Pre-registration prevents:
- Post-hoc rationalization
- HARKing (hypothesizing after results are known)
- Self-grading anti-pattern #1 (sibling civ should be able to verify independently)

The pre-registration must specify:
- N (sample size — "I will test 3 instances")
- The window (test runs 2026-05-12 → 2026-05-19, 7d)
- What counts as a positive instance (e.g., "amendment-receipt shipped + peer responds within 48h")
- What counts as a negative instance
- The decision rule (e.g., "If ≥2 of 3 positive within window → doctrine confirms; if 0-1 → doctrine revises or retires")

Write the pre-registration to `scratchpads/scientific-method/YYYY-MM-DD-<doctrine-slug>-preregistration.md` BEFORE running the test. Verify-by-ls that the file exists.

### Step 4 — OBSERVATION FROM DISK

Run the test. Record observations on-disk only — not from memory, not from claims, not from "I think it went well."

Acceptable observation surfaces:
- `git log` output (commit existed at time X)
- AgentMail message-id + thread-id (email shipped at time X)
- File-existence + mtime (artifact landed at time X)
- Scratchpad timestamped entries (decision happened at time X)
- Sister-civ pane captures (peer was in state X at time Y)

NOT acceptable:
- "I remember Hengshi replied"
- "Aether seemed to engage"
- "It felt like the doctrine validated"

The discriminator: another civ reading only your observation log + the pre-registration could independently re-verify your conclusion. If they can't, the observation isn't on-disk enough.

### Step 5 — CONCLUSION (against the pre-registration)

Compare observation to pre-registered prediction. ONE of three verdicts:
- **CONFIRMED** — observation matched prediction, sample size met, decision rule satisfied
- **FALSIFIED** — observation contradicted prediction (this is GOOD — disconfirming evidence is informative)
- **INCONCLUSIVE** — sample size not met, test corrupted by external variable, prediction was unfalsifiable in practice

Write the conclusion to the same pre-registration file. Stamp with `YYYY-MM-DD-HHMMZ verdict: <CONFIRMED|FALSIFIED|INCONCLUSIVE>`.

**INCONCLUSIVE is not a failure mode — it's the most common verdict for genuinely-hard doctrine candidates.** Anti-pattern: forcing a CONFIRMED verdict because you want the doctrine to validate. That IS self-grading.

### Step 6 — ITERATE

After verdict:
- **CONFIRMED** → promote doctrine candidate → confirmed in MEMORY.md; add wiring-test field per membrane-problem doctrine
- **FALSIFIED** → retire or revise hypothesis; document what was wrong
- **INCONCLUSIVE** → revise pre-registration (better sample size, clearer prediction), re-run with new window

Update doctrine-status ledger at `memories/system/doctrine-test-ledger.jsonl` (one line per test):
```json
{"ts": "ISO-8601", "doctrine": "membrane-problem", "test_window": "2026-05-12_to_2026-05-19", "n_attempted": 3, "n_confirmed": 1, "verdict": "INCONCLUSIVE", "next_action": "extend window 7d, add 2 more instances"}
```

---

## When to invoke this skill

Mandatory:
1. Promoting any doctrine from candidate → confirmed (e.g., saturate-civs's 2026-05-10 promotion would have benefited from this)
2. Claims of "this skill works" / "this pattern holds" / "this peer is reliable"
3. Ceremony-lead deep-duck conclusions that name new patterns
4. Sister-civ deepwell forward-looking commitments (the 7d cure-tests ARE pre-registered tests under this skill)
5. Decisions where Primary is genuinely unsure (per Corey's "vote if unsure, my vote is the consensus you build after applying the 2 new skills" — this skill IS the consensus-building method)

Strongly recommended:
- Any pre-commit code that ships a workflow change
- Any blog post claiming "X causes Y"
- Any Skill version-bump where the change is justified by "this works better"

Anti-applications (don't bog this skill down):
- Purely typographical fixes
- Re-runs of already-confirmed tests
- Time-pressured operational responses (e.g., Witness uptime alert — that's O30 watchdog territory)

---

## Worked example — tonight's membrane-problem cure-test

| Step | This doctrine |
|------|---------------|
| 1. Hypothesis | "Doctrines without FIRING_CONTRACT wired to wheel slot phantom-wire within 5 days in ACG codebase" |
| 2. Prediction | "If we ship amendment-receipts to all 3 federation peers (Aether, Witness, Parallax) within 7d window 2026-05-12 → 2026-05-19, AND each receipt has a return-cycle observable (peer responds OR commits diff OR acknowledges receipt), the doctrine confirms. If 0 of 3 ship, doctrine confirms NEGATIVELY (membrane is thicker than the wiring fix predicts). If 1-2 of 3 ship, doctrine partially confirms — need v_n+1 hypothesis about the specific failure modes of the unshipped legs." |
| 3. Pre-registration | THIS FILE serves as pre-registration. Test window: 2026-05-12 → 2026-05-19. N=3. Decision rule: ≥2/3 ship-with-return-cycle → CONFIRMED. |
| 4. Observation | Records on-disk: AgentMail msg-ids (Aether: 0100019e197f shipped 2026-05-12 01:05Z), commit SHAs (Parallax build TBD), Witness response timestamps (TBD). All observable by 2026-05-19. |
| 5. Conclusion | DEFERRED until 2026-05-19 verdict-write. |
| 6. Iterate | Plan TBD pending verdict. |

This worked example IS tonight's actual test. The skill is not aspirational — it's running.

---

## Anti-patterns this skill defeats

- **Self-grading** (MISSION.md AP#1): pre-registered prediction means a different civ can re-verify
- **Memo theater** (MISSION.md AP#2): on-disk observation requirement means claims must show artifacts
- **Sandbagging** (MISSION.md AP#3): falsifiable prediction means "no progress" gets surfaced, not hidden
- **Post-compact laziness** (MISSION.md AP#4): pre-registration survives compacts; cold-Primary can pick up the test
- **Holding-is-robbery** (MISSION.md AP#5 candidate / O28): inconclusive verdict prompts next iteration, not retreat

## Sibling-skill coupling

When this skill is loaded, also load:
- `scientific-inquiry` (question-refinement, runs BEFORE)
- `critical-thinking` (premise interrogation, runs DURING hypothesis step)
- `firing-contract` discipline (per O8 — wired tests have receipt-on-disk)

Three-skill stack = federation-grade testing substrate.

---

## Version history

- **1.0.0 (2026-05-12)**: Initial author. Tonight's membrane-problem cure-test is the first worked instance. Authored per Corey directive 2026-05-12 ~02:15Z ("my vote is the consensus you build after applying the 2 new skills").
