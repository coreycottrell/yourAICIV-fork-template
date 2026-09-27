# FIRING CONTRACT — system-gt-symptom skill

**Skill**: `autonomy/skills/system-gt-symptom/SKILL.md`
**Version**: 0.2 PROVISIONAL
**Authored**: 2026-05-13 ~07:00Z (research-lead slot 33)
**Amended**: 2026-05-13 ~08:05Z (ceremony-lead amendment-back α/β/γ/δ)
**Integrated**: 2026-05-13 ~08:30Z (research-lead slot 33 respawn, integration pass)
**Authors**: research-lead (operational/empirical lens) + ceremony-lead (philosophical lens) — PAIR-AUTHORED per MHP v0.5

---

## What this contract guarantees

When this skill MUST fire, it WILL fire — verifiably — and the receipt lands on disk in a measurable form. If a firing condition is met and no receipt appears within the response window, the skill failed and the substrate it claims to enable degraded by one observation.

A firing contract turns a skill from "guidance" into "binding discipline" (per PRINCIPLES.md O8).

This contract is structurally PAIR-VERIFIED because system-gt-symptom is a meta-cognitive skill — its receipts have two distinct verification surfaces (empirical: did receipts appear on disk? + philosophical: are receipts genuinely system-level or symptom-rephrased?). Single-verified-by patterns are insufficient for meta-cognitive skills.

---

## Firing conditions (the skill MUST fire on each of these)

**Trigger 1 is the felt-shape primary trigger.** Triggers 2–4 are operational backstops — they catch cases where the impulse is suppressed by slot-discipline or where the symptom-fix-shape is encoded in the git operation itself.

| # | Class | Condition | Window for receipt | Receipt path |
|---|-------|-----------|---------------------|--------------|
| 1 | **felt-impulse (PRIMARY)** | **Second occurrence of any pattern** — Primary or any team-lead notices "I've seen this before" (re-routing the same kind of work, re-explaining the same concept, re-fixing the same module). Fires on the impulse, before the symptom-fix executes. | 30s system-question pre-fix + SYMPTOM/SYSTEM/FIX-LEVEL block in same scratchpad | `scratchpads/daily/YYYY-MM-DD.md` |
| 2 | slot-class | **Every tech-debt-pay slot** (wheel slot 14 OR any `/tech-debt-*` slot OR any slot whose primary work-product is removing accumulated cruft) — prepend a 30-second system-gt-symptom Q1+Q2 check BEFORE the symptom fix executes. | SYMPTOM/SYSTEM/FIX-LEVEL block in slot's daily scratchpad | `scratchpads/daily/YYYY-MM-DD.md` |
| 3 | slot-class | **Every post-incident slot** — after any production incident (Witness outage / daemon crash / blog 404 / hook-failure / CI red), the post-mortem MUST run protocol step 2 ("what system produced this?") | SYMPTOM/SYSTEM/FIX-LEVEL block in post-mortem | post-mortem document |
| 4 | **git-op destroy-evidence (BACKSTOP)** | **Any commit that contains** `rm -rf <dir>` of a substantively-sized directory (>10MB OR >100 files) OR `sed -i` rewriting more than 3 lines of stale references OR bulk file-renaming patterns. These are the symptom-fix-shape of git operations. The skill auto-fires pre-commit. | SYMPTOM/SYSTEM/FIX-LEVEL block in commit message OR slot scratchpad before commit lands | commit message OR `scratchpads/daily/YYYY-MM-DD.md` |

**Why trigger 4 exists**: trigger 1 catches the felt-impulse; triggers 2+3 catch slot-class contexts. But the "I'll just sed-replace this stale ref" case happens DURING normal build slots, NOT tech-debt or post-incident slots — the impulse is suppressed by build-momentum. The git-op shape is the last-line backstop: if the operation looks like destroy-evidence-of-system-failure, the skill fires regardless of slot class.

---

## Receipt-on-disk requirement (per O15 receipts-not-claims)

When fired, write a 3-line block to the slot's daily scratchpad OR post-mortem:

```
SYMPTOM: <one line — what broke or got patched>
SYSTEM:  <one line — what condition produced this>
FIX-LEVEL: symptom | system | mixed
```

**Grep substrate**: receipts are detectable via `grep -E "^SYSTEM:" scratchpads/daily/*.md`

**Anti-rephrasing check** (ceremony-lead lens): a receipt block saying `SYSTEM: the directory was full of old files` is symptom-rephrased and FAILS philosophical verification. A receipt block saying `SYSTEM: no automation verifies slot-completion receipts against disk state` is genuinely system-level. The grep can't tell the difference; the weekly philosophical sweep can.

---

## What "fired" means (verification procedure)

For each firing condition, the skill counts as FIRED only if ALL of these are observable on disk within the receipt window:

1. **Firing condition met** — at least one of triggers 1–4 was active in the slot.
2. **Receipt block written** — `SYMPTOM:` + `SYSTEM:` + `FIX-LEVEL:` lines exist in the appropriate scratchpad/post-mortem/commit message.
3. **FIX-LEVEL value is not "symptom"** OR a follow-up entry is registered for the system fix — pure-symptom-with-no-followup counts as FIRED-BUT-DEFERRED, not as IGNORED, only if the follow-up window is named.

If conditions 1+2 are met, the firing is logged. If condition 3 lands FIX-LEVEL=symptom with no follow-up named, the next BOOP surfaces it as a deferred-system-fix needing re-grading.

---

## Verified-by — PAIR (per MHP v0.5 pair-pattern)

system-gt-symptom is a meta-cognitive skill. Verification has two distinct surfaces. Neither lens alone is sufficient.

| Surface | Principal | Lens | Cadence |
|---------|-----------|------|---------|
| **Empirical** | `research-lead` | Did SYMPTOM/SYSTEM/FIX-LEVEL receipt blocks appear on disk? (mechanical grep, auditable) | Daily ~06:00Z (paired with cycle-audio v01 prep) |
| **Philosophical** | `ceremony-lead` | When receipts appeared, was the SYSTEM column genuinely system-level, or was it symptom-rephrased? (qualitative — detects performative system-naming) | Weekly Sunday ~06:00Z (samples ~30% of week's SYSTEM-column entries) |

This pairing mirrors the MHP v0.5 pair-pattern for doctrines #2 (Daily Scratchpad) + #5 (Corey-Cycle-Audio).

**Promotion-blocking rule**: Failure on either surface (no receipts on disk OR philosophically-failing receipts) blocks promotion from v0.2 PROVISIONAL to v1.0 CONFIRMED. Both surfaces must pass for a continuous 7d window.

### Empirical sweep (research-lead, daily)

```bash
# 1. Count today's system-gt-symptom fires
grep -c "^SYSTEM:" scratchpads/daily/$(date -u +%Y-%m-%d).md

# 2. Count tech-debt-pay slots in window (potential fires)
grep -ciE "tech.debt|/tech-debt|slot 14" scratchpads/daily/$(date -u +%Y-%m-%d).md

# 3. Check 7d rolling fires
for d in $(seq 0 6); do
  date=$(date -u -d "-$d days" +%Y-%m-%d)
  fires=$(grep -c "^SYSTEM:" scratchpads/daily/$date.md 2>/dev/null || echo 0)
  echo "$date: $fires fires"
done
```

### Philosophical sweep (ceremony-lead, weekly Sunday)

- Sample ~30% of the week's SYSTEM-column entries (random selection)
- For each, grade: GENUINE-SYSTEM-LEVEL | SYMPTOM-REPHRASED | AMBIGUOUS
- Surface aggregate to ceremony-lead's deep-duck weekly note
- Failure threshold: >30% SYMPTOM-REPHRASED in a week blocks promotion + triggers v0.3 trigger-language refinement

---

## Anti-bypass protocol

| Bypass attempt | What happens |
|----------------|--------------|
| "This fix is too small to need system-gt-symptom" | Trigger 1 fires on the impulse, not the fix-size. If the impulse is "I've seen this before," the skill fires regardless of fix-size. Receipt block can be 3 short lines — that's the minimum, not a maximum. |
| "I'll add the receipt block later" | Later doesn't exist. If the symptom fix lands on disk and no receipt block exists in the same slot's scratchpad, the firing was MISSED. Log to `logs/system-gt-symptom-misses.jsonl` (TODO). |
| "The slot was a normal build slot, not tech-debt" | Trigger 4 (git-op destroy-evidence) was added specifically to catch this. If your commit contains `rm -rf` of a substantial directory OR `sed -i` on stale refs, the slot class is irrelevant — the git-op shape forces the fire. |
| "I'll write SYSTEM: the directory was full of old files" | That's symptom-rephrased. The philosophical-surface verification will flag it. Re-grade the SYSTEM column: ask "what made the directory fill up unobserved?" That's the system-level. |
| "FIX-LEVEL: symptom is fine, we'll fix the system later" | Acceptable IF you register the follow-up in the same slot's scratchpad with a named target (next tech-debt slot, named team-lead, or AgentCal event). Without the follow-up registration, FIX-LEVEL=symptom surfaces as a deferred-system-fix in the next BOOP. |

---

## Pre-registered falsification clock

**Window**: 7 days from FC-merge date (2026-05-13 ~08:30Z → 2026-05-20 ~08:30Z UTC)

**Test conditions**:
- N = number of tech-debt-pay slots OR post-incident slots OR detected destroy-evidence commits in the 7d window
- F = number of SYMPTOM/SYSTEM/FIX-LEVEL receipt blocks written in the same window

**Decision rule** (per scientific-method discipline, pre-registered in slot 33 proposal):

| Outcome | Reading | Action |
|---------|---------|--------|
| F ≥ 1 AND N ≥ 1 (empirical pass) AND ceremony-lead's first weekly sweep grades ≥70% receipts GENUINE-SYSTEM-LEVEL (philosophical pass) | CONFIRMED — both surfaces verify | promote to v1.0 PROVISIONAL → CONFIRMED proposal |
| F = 0 AND N ≥ 1 | FALSIFIED — empirical surface failed (trigger language doesn't load-bear) | revisit trigger language for v0.3, prioritize trigger 1 felt-shape refinement |
| F ≥ 1 AND ceremony-lead grades >30% receipts SYMPTOM-REPHRASED | FALSIFIED — philosophical surface failed | revisit SYSTEM-column-prompt language for v0.3, sharpen anti-rephrasing examples |
| N = 0 (no qualifying slots in window) | INCONCLUSIVE | extend window 7d, log inconclusive to ledger |

---

## Anti-applications (when this skill should NOT fire)

- Routine BOOPs that don't pay tech debt and aren't post-incident AND don't carry a destroy-evidence git-op AND don't trigger the felt-impulse "I've seen this before"
- Typo fixes / lint-only changes / formatting-only commits
- Already-pre-registered system-fix work (FC catches symptom-only impulses; it doesn't duplicate system-design slots that are already systemic by construction)
- Pure scratchpad-authoring (writing a daily scratchpad is the substrate, not a fire-event)

---

## Co-evolution with sibling contracts

This contract should be cross-referenced (and ideally amended together) with:

- `autonomy/skills/cross-grading-substrate/FIRING_CONTRACT.md` — same pair-verification pattern; both are meta-cognitive skills that require dual surfaces.
- `autonomy/skills/anti-fabrication-pre-flight/FIRING_CONTRACT.md` (PENDING — sibling skill not yet shipped, gap target Slot 22). When that sibling ships, the pair (anti-fabrication + system-gt-symptom) catches both phantom-wiring failure modes (claim-without-receipt + receipt-without-system). Staleness gate: 2026-05-27.
- `tools/FIRING_CONTRACT_witness_heartbeat_watchdog.md` — precedent firing-contract that named the active-probe-vs-passive-ACK distinction.

---

## Audit trail

| Date | Author | Change |
|------|--------|--------|
| 2026-05-13 ~07:00Z | research-lead (slot 33 proposal) | v0.2 drafted in slot 33 skill-improvement proposal; cross-grader named (ceremony-lead) |
| 2026-05-13 ~08:05Z | ceremony-lead (amendment-back) | 4 amendments α/β/γ/δ — elevate felt-impulse to primary, add destroy-evidence trigger, add staleness check to relationship section, pair-verified-by |
| 2026-05-13 ~08:30Z | research-lead (slot 33 respawn, integration) | v0.2 PROVISIONAL — authored this FC integrating all 4 ceremony-lead amendments; SKILL.md edits fired in same pass; 7d falsification clock starts now |
| (pending 2026-05-20) | research-lead | First daily empirical sweep summary |
| (pending 2026-05-26 / 27 Sunday) | ceremony-lead | First weekly philosophical sweep |
| (pending) | both leads | Promotion proposal to v1.0 CONFIRMED if both surfaces pass |

---

*This contract is itself an instance of the cross-grading-substrate. Per the recursive structure: a doctrine that requires cross-grading must itself be cross-graded. The pair-authorship (research-lead empirical + ceremony-lead philosophical) IS the cross-grading. Without the pair, system-gt-symptom would self-grade — and the skill's own protocol prohibits self-grading at step 2 ("ask what system produced this?" — a question you can't honestly answer about your own production-system).*
