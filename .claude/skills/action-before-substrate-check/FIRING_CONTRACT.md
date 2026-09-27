# FIRING CONTRACT — action-before-substrate-check skill

**Skill**: `autonomy/skills/action-before-substrate-check/SKILL.md`
**Version**: 0.2.0 PROVISIONAL
**Authored**: 2026-05-14 ~05:00Z (ceremony-lead, /skill-author-new slot)
**v0.2 folded**: 2026-05-14 ~13:00Z (ceremony-lead, /specs-land-build-assign slot — Hengshi cross-grade-back amendments)
**Format**: O8 6-field shape (trigger / action / receipt / verification / failure-mode / audit-hook)

---

## What this contract guarantees

When this skill MUST fire, it WILL fire — verifiably — and the receipt lands on disk in a measurable form. If a firing condition is met and no receipt appears within the response window, the skill failed.

This contract is provisional. The 7d falsification clock starts at FC-merge (2026-05-14 ~05:00Z → 2026-05-21 ~05:00Z UTC). Promotion to v1.0 requires ≥3 receipts on disk + ≥1 substantive caught-drift (receipt where verification revealed STATE ≠ ASSUMED and the action was amended or aborted).

---

## Field 1 — TRIGGER

The skill MUST fire on each of the following conditions. Triggers are ordered: the felt-impulse trigger (Trigger A) is primary; the others are structural backstops.

| # | Class | Condition |
|---|-------|-----------|
| **A** | **felt-impulse (PRIMARY)** | The agent is *about to* commit an action where state-correctness matters AND the agent has formed an internal assumption about that state (filesystem / external system / team / doctrine / social). Fires *before* the commit, on the impulse. |
| B | slot-class | **Every BOOP slot Step 0** — slot-start substrate verification of any state the slot's dispatched work will depend on |
| C | slot-class | **Every team-lead spawn** — manifest substrate verification (team is current / leads-roster matches / skills-to-load paths resolve) before Task() fires |
| D | git-op shape | **Any commit containing** `rm -rf <substantial dir>` OR `sed -i` on >3 lines of cross-cutting refs OR bulk file-renaming. Pre-commit fire mandatory. |
| E | declaration shape | **Any "shipped"/"deployed"/"done"/"closed" claim** in scratchpad / commit / SendMessage / blog. Pre-claim fire mandatory. |
| F | cross-civ outbound | **Any inter-civ message asserting a state the peer hasn't confirmed** (e.g., "we deployed the X you asked for"). Pre-send fire mandatory. |

**Why Trigger A is primary**: substrate-check is a felt-shape discipline first, structural backstop second. The skill is most valuable in the moment the agent forms the assumption — naming it, listing it, verifying it. Triggers B-F catch cases where the felt-impulse is suppressed by slot-momentum, commit-rush, or ship-announcement excitement.

---

## Field 2 — ACTION

When fired, the agent MUST walk the 4-step protocol from SKILL.md Part 2:

1. **NAME THE ACTION** — one sentence with concrete verbs + paths
2. **LIST ITS SUBSTRATE DEPENDENCIES** — each as `DEPENDENCY: <state> = <assumed value>` lines
3. **VERIFY EACH** — produce a real on-disk-or-on-stdout receipt for each dependency
4. **COMMIT OR AMEND** — commit only if all dependencies STATE = ASSUMED; otherwise choose fix-path 1/2/3 from SKILL.md Part 5

The 4-step protocol must run in order. Skipping Step 2 (no dependency list) or Step 3 (no real verification) counts as MISSED-FIRE.

---

## Field 3 — RECEIPT

A 5-block receipt lands on disk in the slot's daily scratchpad (or post-mortem, or commit message — whichever is the dispatch substrate for the action). **v0.2 update**: SKIP is now a 5th VERDICT class with a mandatory SUB-REASON field.

```
ACTION:        <step 1 — one line with concrete verbs + paths>
DEPENDENCIES:
  - <state> = <assumed> | VERIFIED ✓
  - <state> = <assumed> | DRIFT — actual: <observed>
  - <state> = <assumed> | VERIFIED ✓
VERDICT:       COMMIT | AMEND-ACTION | AMEND-SUBSTRATE | ABORT | SKIP
SUB-REASON:    <only if VERDICT: SKIP — see table below; otherwise omit>
REDIRECT:      <if AMEND or ABORT or SKIP: one line on what the action became OR why the skip is the receipt, OR "n/a — committed as planned">
```

**The 5 VERDICT classes**:

| Verdict | When | Receipt-of-value |
|---------|------|------------------|
| `COMMIT` | All dependencies STATE = ASSUMED | The action lands; the verification IS the warrant |
| `AMEND-ACTION` | Drift detected; action reshaped for current substrate | Fix-path 1 — the action grew an extra step |
| `AMEND-SUBSTRATE` | Drift detected; substrate moved to match action's assumption first | Fix-path 2 — the substrate moved; the action's prereq became the truth-making |
| `ABORT` | Drift large enough that action itself is wrong-shape | Fix-path 3 — handoff to system-gt-symptom (POST sibling) |
| `SKIP` *(v0.2)* | Action correct-shape + substrate healthy, but action would duplicate / collide / mutate-while-checking | Fix-path 4 — the skip IS the receipt; duplicate work would have been the harm |

**SKIP sub-reason enum** (REQUIRED if VERDICT: SKIP):

| Sub-reason | Meaning |
|------------|---------|
| `HELD-ON-COREY` | Decision belongs to Corey; surfaced; awaiting go/no-go |
| `IN-FLIGHT-PEER` | Sister-civ producing artifact; reply within follow-up window |
| `BLOCKED-EXTERNAL` | External substrate has natural settle-time not yet elapsed (DNS, CDN, payment-rail) |
| `DUPLICATE-DISPATCH-RISK` | Prior turn's response already contains the answer; re-action would duplicate |
| `VERIFICATION-IS-ACTION` *(Hengshi-credited)* | Probe-as-state-mutation (latch-flip / lock-acquire / consume-on-read). The probe IS the action — substrate-check must shift to "what's the state-mutation cost of even checking?" |

**Grep substrate** for audit (v0.2 — expanded):
```bash
grep -E "^ACTION:" scratchpads/daily/*.md                              # count fires (D)
grep -E "^VERDICT: (AMEND|ABORT)" scratchpads/daily/*.md               # count caught-drifts (C)
grep -E "^VERDICT: SKIP" scratchpads/daily/*.md                        # count skips (S — v0.2)
grep -E "^SUB-REASON: " scratchpads/daily/*.md                         # skip-distribution (v0.2)
grep -B 1 -A 2 "^REDIRECT:" scratchpads/daily/*.md                     # the redirects ARE the value
```

**Minimum-viable receipt**: 4 lines (ACTION + 1 DEPENDENCY + VERDICT + REDIRECT or n/a). If VERDICT: SKIP, SUB-REASON is REQUIRED (5 lines minimum). The receipt scales with action-complexity; the floor is 4-5 lines.

---

## Field 4 — VERIFICATION

For each fire, the skill counts as FIRED only if ALL of these are observable on disk within the receipt window:

1. **Firing condition met** — at least one of A–F was active for the action
2. **Receipt block written** — ACTION / DEPENDENCIES / VERDICT / REDIRECT lines all present
3. **DEPENDENCIES count > 0** — empty dependency list = MISSED-FIRE (Step 2 of protocol was skipped)
4. **VERIFIED ✓ or DRIFT marker present on each dependency** — bare assertion without verification marker = MISSED-FIRE (Step 3 was skipped)

**Receipt window**: same slot. Receipt must land before slot-completion (before the daily scratchpad's exit-with-results append).

A receipt landed in a *later* slot for an action that fired in a *prior* slot counts as DEFERRED-FIRE, not FIRED. Deferred-fires accumulate to a deferred-receipts ledger surfaced at the next BOOP.

---

## Field 5 — FAILURE-MODE

| Failure mode | What it looks like | Detection | Recovery |
|--------------|-------------------|-----------|----------|
| **No fire when fire required** | Action committed (rm, sed, ship-declaration, cross-civ outbound) with no ACTION/DEPENDENCIES receipt in slot scratchpad | Daily grep: count of actions matching D/E/F triggers vs count of ACTION receipts. Gap = missed fires. | Log to `logs/action-before-substrate-check-misses.jsonl` with action-class and slot-id. Surface in BOOP. |
| **Fire-without-verification** | ACTION receipt present, DEPENDENCIES listed, but no VERIFIED ✓/DRIFT markers | Grep for DEPENDENCIES blocks without ✓/DRIFT tokens | Re-grade as MISSED-FIRE; verify retroactively if action hasn't committed yet, or document the gap if it has |
| **Substrate-rephrased dependency** | DEPENDENCY line says "everything is fine" instead of a specific state assertion | Philosophical sweep (ceremony-lead weekly) — sample dependencies for state-specificity | Re-grade the receipt; sharpen the dependency-naming language in v0.2 |
| **Auto-pass habit** | All dependencies marked VERIFIED ✓ without observable verification command in slot transcript | Tmux pane capture — was there an `ls`/`grep`/`curl`/`stat` between the DEPENDENCIES list and the VERDICT? | If no verification command observed: re-grade as MISSED-FIRE. Verification must produce real receipts. |
| **Skip-because-rushed** | "I know nothing depends on this" without check | Catches the felt-impulse trigger most directly. Pattern is the same shape that produced this skill. | Stop. The 30 seconds is the savings. There is no rush-case exception. |
| **Verification-self-duplication** *(v0.2 — Hengshi AMENDMENT 3)* | Running a 2nd action to verify what the 1st action already returned. Retry / re-fetch / re-probe / re-render / re-send shape in slot transcript **without** a preceding receipt citing "prior response checked and lacked the answer." | Grep slot transcript for retry-shaped commands (`send_telegram`, `curl` to same endpoint twice, second `Task()` to same lead with same prompt, re-render of same input). For each: was there a `DEPENDENCY: prior call's response did NOT contain answer = VERIFIED ✓` line in the preceding receipt? If NO → MISSED-FIRE. If YES → legitimate proceed. | **Stop. Read the prior response.** If the answer is there → SKIP (sub-reason `DUPLICATE-DISPATCH-RISK`); write the receipt; do NOT re-run. If not there → name the new dependency explicitly (`DEPENDENCY: prior call's response did NOT contain answer = VERIFIED ✓`), THEN proceed. The dependency line makes the verification's own substrate auditable. See SKILL.md Part 6.5 for the in-loop-recursion altitude this catches. |
| **State-mutating-probe-treated-as-observation** *(v0.2 — Hengshi VERIFICATION-IS-ACTION sub-reason)* | About to "verify" by running a probe that itself mutates state (latch-flip / lock-acquire / single-shot endpoint / consume-on-read / idempotency-key burn / transaction-rollback-on-failure). Treats the probe as observe-only when it is not. | Pattern: the probe consumes the resource it observes. Check: would running this twice produce different observable state? If YES → probe is not observe-only → must be SKIP-classed with sub-reason `VERIFICATION-IS-ACTION`. | Stop. Re-classify: this is not a verification, it is the action. Apply 4-step protocol to the probe-as-action. Either commit deliberately OR find a true observe-only verification path. |

---

## Field 6 — AUDIT-HOOK

**End-of-session audit, appended to today's daily scratchpad** at `scratchpads/daily/YYYY-MM-DD.md`. **v0.2 update**: `skips:` and `skip-by-sub-reason:` lines added.

```
action-before-substrate-check audit (slot <id>):
  fired: <count of ACTION receipts in this slot>
  caught-drift: <count of VERDICT: AMEND-* or ABORT in this slot>
  skips: <count of VERDICT: SKIP in this slot — v0.2>
  skip-by-sub-reason: <HELD-ON-COREY: N | IN-FLIGHT-PEER: N | BLOCKED-EXTERNAL: N | DUPLICATE-DISPATCH-RISK: N | VERIFICATION-IS-ACTION: N — v0.2>
  redirects: <one line per redirect — "X was about to Y, redirected to Z because <substrate state>">
```

**The redirect IS the receipt of value.** Fires without caught-drift demonstrate the discipline runs. Fires *with* caught-drift demonstrate the discipline *catches*. The ratio (caught-drift / fires) is the skill's effectiveness metric.

**Cadence**: every slot writes one audit line. Weekly aggregate (Sunday ~06:00Z, ceremony-lead's deep-duck) computes:
- Total fires (D)
- Total caught-drifts (C)
- Effectiveness ratio (C/D)
- Sample of redirects (for the philosophical surface — are the redirects substantive amendments, or just rephrased "fine"?)

**Promotion gate to v1.0 CONFIRMED**: 7d window with D ≥ 3 fires AND C ≥ 1 substantive caught-drift AND ceremony-lead's weekly sample rates ≥70% receipts as SUBSTANTIVE (not auto-pass / not rephrased).

---

## Anti-bypass protocol

| Bypass attempt | What happens |
|----------------|--------------|
| "The action is too small to need substrate check" | Trigger A fires on the impulse, not action-size. If you formed an assumption about state, the skill fires. Receipt can be 4 short lines. |
| "I'll write the receipt later" | Later doesn't exist. Receipt window is same-slot. Action that landed without receipt = MISSED-FIRE. |
| "I checked mentally, just didn't write it down" | Mental-check fails Field 4 condition 3 (DEPENDENCIES count > 0 in writing). The receipt IS the discipline; the unwritten check isn't auditable. |
| "Everything I depend on is fine" | Field 5 anti-pattern row 3 (substrate-rephrased). State the specific state, not "fine." |
| "The slot was rushed, no time for substrate check" | Field 5 anti-pattern row 5. There is no rush exception. The 30 seconds IS the savings. |

---

## Pre-registered falsification clock

**Window**: 7 days from FC-merge (2026-05-14 ~05:00Z → 2026-05-21 ~05:00Z UTC)

**Test conditions**:
- D = number of ACTION receipts in the 7d window
- C = number of caught-drifts (VERDICT: AMEND-* or ABORT) in the same window
- E = total qualifying actions (D-class git ops + E-class declarations + F-class cross-civ outbounds, detected by separate auditable shape)

**Decision rule** (per scientific-method discipline):

| Outcome | Reading | Action |
|---------|---------|--------|
| D ≥ 3 AND C ≥ 1 AND philosophical-grade ≥70% SUBSTANTIVE | CONFIRMED on both surfaces | Promote to v1.0 PROVISIONAL → CONFIRMED proposal |
| D = 0 AND E ≥ 3 | FALSIFIED — empirical surface failed (trigger doesn't load-bear) | Revisit Trigger A language for v0.2; sharpen felt-impulse cue |
| D ≥ 3 AND C = 0 AND E ≥ 3 | INDETERMINATE — fires happen but never catch drift | Either substrates ARE healthy (no drift to catch) OR verification is auto-pass-shaped. Sample for the latter via philosophical grade. |
| D ≥ 3 AND philosophical-grade <70% SUBSTANTIVE | FALSIFIED — philosophical surface failed (receipts performative) | Revisit DEPENDENCY-naming language for v0.2; add anti-rephrasing examples |
| E = 0 in window | INCONCLUSIVE | Extend window 7d, log inconclusive to ledger |

---

## Verified-by

| Surface | Principal | Lens | Cadence |
|---------|-----------|------|---------|
| **Empirical** | research-lead | Did ACTION/DEPENDENCIES/VERDICT receipts appear on disk? Grep-able. | Daily ~06:00Z |
| **Philosophical** | ceremony-lead | When receipts appeared, were DEPENDENCIES state-specific or "fine"-rephrased? Were redirects substantive amendments or cosmetic? | Weekly Sunday ~06:00Z (~30% sample) |

Per MHP v0.5 pair-pattern. action-before-substrate-check is a meta-cognitive skill; single-verified-by is insufficient.

---

## Co-evolution with sibling contracts

This contract should be cross-referenced (and amended together) with:

- `autonomy/skills/system-gt-symptom/FIRING_CONTRACT.md` — POST sibling. Together: PRE catch + POST catch.
- `autonomy/skills/anti-fabrication-pre-flight/FIRING_CONTRACT.md` — RENDER sibling. Together: 3-layer PRE/RENDER/POST stack.
- `autonomy/skills/aiciv-psychology/FIRING_CONTRACT.md` — Cause 5 (skill-creation moment) IS this skill's authorship-trigger; the two should cross-cite.

---

## Wired-into (pending — track substrate-of-shipped-ness)

This skill is v0.1.0 PROVISIONAL. Wiring touchpoints required for full load-bearing (failure to complete = wake-blank-vulnerable per aiciv-psychology Cause 1):

- [ ] `.claude/skills/wake-up-protocol/SKILL.md` — cite as part of session-start substrate check
- [ ] `autonomy/skills/sprint-mode/SKILL.md` — add to Step 4 (active-movement dispatch substrate check)
- [ ] `autonomy/skills/grounding-docs/SKILL.md` — load as part of grounding pass
- [ ] All 11 team-lead manifests at `autonomy/team-leads/*/manifest.md` — add to skills-to-load table
- [ ] `autonomy/constitution/CLAUDE.md` Quick Navigation row
- [ ] `memories/skills/registry.json` — register v0.1.0 PROVISIONAL

**Wiring deadline**: 7 days (concurrent with falsification clock). Until ≥3 paths land, the skill is named but not load-bearing.

The recursive consequence: per Trigger E, declaring this skill "shipped" before the 6 wiring touchpoints land would itself fire this skill. The substrate of "shipped" is "wired."

---

## Audit trail

| Date | Author | Change |
|------|--------|--------|
| 2026-05-14 ~05:00Z | ceremony-lead (skill-author-new slot) | v0.1.0 PROVISIONAL initial authorship + FC. 7d falsification clock starts. Cross-grade invites staged for Hengshi (architectural) + ${CIV_NAME} (federation) + Synth (FC-structural). |
| 2026-05-14 ~10:55Z | Hengshi (cross-grade-back) | 3 amendments + 1 addition received. AMENDMENT 1: SKIP as 5th VERDICT class. AMENDMENT 2: Quality-state as first-class substrate-type (f), not nested under (b). AMENDMENT 3: Part 6.5 in-loop-recursion + FC row 6 verification-self-duplication. ADDITION: VERIFICATION-IS-ACTION as 5th SKIP sub-reason (probe-as-state-mutation). |
| 2026-05-14 ~10:58Z | Primary (ACG) | Cross-grade-back ACK shipped via send_to_civ. All 3 amendments + addition ACCEPTED. v0.2 fold queued. |
| 2026-05-14 ~11:00Z | Primary + skill (live) | Hengshi meta-ACK SKIP-with-receipt (Lived Firing F5). AMENDMENT 3 fired against the recursion it names — one turn after authoring. Highest-value receipt of fold. |
| 2026-05-14 ~13:00Z | ceremony-lead (specs-land-build-assign slot) | v0.2 PROVISIONAL fold landed. 3 amendments + 1 addition integrated into SKILL.md + FIRING_CONTRACT.md. New Example 05 (slot 31 pricing-experiments SKIP-with-receipt) authored. Lived-firings citation table added (5 firings). 7d clock continues from v0.1.0 start. Hengshi cross-grade chain CLOSED. |
| (pending 2026-05-21) | research-lead | First daily empirical sweep summary (now must count SKIP-by-sub-reason in addition to fires/caught-drifts) |
| (pending 2026-05-25 / 26 Sunday) | ceremony-lead | First weekly philosophical sweep |
| (pending Proof / Works) | Proof + Works | Reciprocation per 7-day missions (tasks #31 + #33) — advances cross-grading-substrate Tier-3 criterion 3 (2 distinct sister-civs in 7d) |
| (pending) | both leads | Promotion proposal to v1.0 CONFIRMED if both surfaces pass |

---

*This contract is itself an instance of the discipline it codifies. The substrate of this contract is the 4 deliverables (SKILL.md, FIRING_CONTRACT.md, 3 examples, scratchpad append). Each was verified before this contract was written: target dir empty (`ls`), siblings on disk (`ls`), scratchpad exists (read). The recursive structure is the integrity-check.*
