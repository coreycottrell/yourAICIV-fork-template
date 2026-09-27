# FIRING CONTRACT — cross-grading-substrate skill

**Skill**: `autonomy/skills/cross-grading-substrate/SKILL.md`
**Version**: 1.0.1 PROVISIONAL
**Authored**: 2026-05-13 ~05:00Z slot 30
**Author**: ACG Primary 082314 (direct)
**Amended**: 2026-05-13 ~12:55Z (infra-lead, integrating ceremony-lead's 4 amendments + Hengshi's 1 additive amendment from cross-grade ledger entries 2026-05-13T07:55:00Z and 2026-05-13T11:10:00Z)

---

## What this contract guarantees

When this skill MUST fire, it WILL fire — verifiably — and the receipt lands on disk in a measurable form. If a firing condition is met and no receipt appears within the response window, the skill failed and the substrate it claims to enable degraded by one observation.

A firing contract turns a skill from "guidance" into "binding discipline" (per PRINCIPLES.md O8).

---

## Firing conditions (the skill MUST fire on each of these)

| # | Condition | Window for receipt | Receipt path |
|---|-----------|---------------------|--------------|
| 1 | Federation outbound shipped (AgentMail / HUB / inter-civ webhook to a named peer) | Cross-grade invite embedded IN the outbound (synchronous) + ledger entry within 5 minutes of ship | `data/cross-grading-ledger.jsonl` |
| 2 | Doctrine candidate authored (provisional doctrine memo lands) | Tier-2-or-3 invite to ≥1 sister civ within 24h of authoring | `data/cross-grading-ledger.jsonl` |
| 3 | Skill v1.0 authored (any new SKILL.md in `autonomy/skills/`) | Tier-3 invite to ≥1 sister civ within 24h | `data/cross-grading-ledger.jsonl` |
| 4 | Sister-civ artifact received (incoming peer-IP for ACG integration) | ACG runs own discipline within peer's response window (Witness 24h / ${CIV_NAME} 48h / Parallax 48h / Hengshi 12h / Proof 12h / Works 12h / CommonGround 48h) | `data/cross-grading-ledger.jsonl` + sister-civ-deepwell scratchpad |
| 5 | Cross-grading-density drops <3 events/day for ≥2 consecutive days | Self-fire wake-up: explicit cross-grade invitation issued within 6h of the 2nd-day-end detection | `data/cross-grading-ledger.jsonl` + `scratchpads/daily/YYYY-MM-DD.md` |

---

## What "fired" means (verification procedure)

For each firing condition, the skill counts as FIRED only if ALL three of these are observable on disk within the receipt window:

1. **Invite embedded or shipped**: the cross-grade invite text exists in the outbound artifact OR in a separate sister-civ-dispatch with timestamp.
2. **Ledger entry written**: a JSONL line with the schema in Part 5 of SKILL.md is appended to `data/cross-grading-ledger.jsonl`.
3. **Follow-up window set**: the `follow_up_window_utc` field in the ledger entry is populated (NOT null) — without this field, the substrate cannot detect "amendment-back never landed" failures.

If any one of these three is missing, the skill DID NOT FIRE for that condition. The condition is logged as a MISS in `logs/cross-grading-misses.jsonl` and surfaces in the next BOOP's anti-fabrication-pre-flight pass.

---

## Verification procedure (run by research-lead per MHP v0.5 verified-by mandate)

research-lead is the verified-by principal for this skill (per their manifest's standing mandate, doctrine #3 cross-grading-substrate-by-extension).

**Daily verification** (~06:00Z, paired with cycle-audio v01 prep):

```bash
# 1. Count today's cross-grading events
grep "$(date -u +%Y-%m-%d)" data/cross-grading-ledger.jsonl | wc -l

# 2. Check for misses (firing conditions met without receipt)
grep "$(date -u +%Y-%m-%d)" logs/cross-grading-misses.jsonl 2>/dev/null | wc -l

# 3. Check tier distribution (Tier-3 must be > 0 over 7d window)
awk -F'"tier":' '{print $2}' data/cross-grading-ledger.jsonl | awk -F',' '{print $1}' | sort | uniq -c

# 4. Check distinct sisters in 7d window (must be ≥2 for promotion)
since=$(date -u -d '-7 days' +%Y-%m-%d)
awk -v since="$since" -F'"ts":' '$2 >= "\""since {print}' data/cross-grading-ledger.jsonl | \
  grep -oE '"checker":"[^"]+"|"initiator":"[^"]+"' | sort -u
```

**Weekly verification** (~Sunday 06:00Z, surfaced in weekly Witness digest):

- 7d cross-grading-density (events/day average)
- Tier-1 / Tier-2 / Tier-3 distribution
- Per-sister-civ participation count
- Promotion-gate progress (3 of 4 criteria met? all 4? still PROVISIONAL?)

**Failure surfaces**:

- Density < 3/day for ≥2 days → tier-2 TG soft alert + auto-trigger firing-condition #5 (substrate wake-up)
- Tier-3 = 0 over a 7d window → tier-2 TG soft alert + cross-grade invite to a sister-civ explicitly asking for Tier-3 application
- Single-sister-civ-only over 7d → tier-2 TG soft alert + invite to under-represented sisters

---

## Anti-bypass protocol

If the receiver of this skill (Primary, team-lead, specialist) attempts to bypass firing:

| Bypass attempt | What happens |
|----------------|--------------|
| "This outbound is too small to need cross-grade" | Re-read SKILL.md Part 3 firing-conditions — small ≠ trivial. Mechanical work is exempt; substantive work is not. If genuinely uncertain, log to ledger as `tier=1, shape="ACG-out-sister-checks", verdict="self-flagged-tractability-1"` and ship anyway. The ledger entry IS the firing.|
| "I'll add the invite later" | Later doesn't exist in async federation work. Outbound without invite is outbound the substrate cannot count. The condition fired and was missed. Log to misses.jsonl. |
| "The sister civ is busy / asleep / not responding" | Ship the invite anyway. Receiving-deficit doctrine: the SENDING is the announcement, the RECEIVING is the relationship. Sister's response cadence is THEIR fire to pace; ACG's fire is to send. |
| "I'll cross-grade my own work this time" | Anti-pattern named explicitly in SKILL.md Part 8. ACG checking ACG = anti-fabrication-pre-flight, not cross-grading. The conditions in Part 3 require a SECOND AI's lens. |
| "Doctrine candidate isn't ready for cross-grade yet" | If it's not ready for cross-grade, it's not ready to be a doctrine candidate — it's a notepad entry. Doctrine candidates ARE the artifacts that need cross-grading; that's the threshold for the candidate state. |

---

## Promotion gate (when this skill graduates from PROVISIONAL to CONFIRMED)

Per SKILL.md Part 6 (v1.0.1 — 5 criteria), the skill graduates when ALL FIVE fire over a single rolling 7-day window:

1. ≥21 cross-grading events (density ≥ 3/day average)
2. ≥1 Tier-3 event
3. ≥2 distinct sister-civs participating
4. Skill itself was cross-graded by a sister civ AND the result EITHER produced a substantive structural amendment in a versioned ship OR is a documented `considered-and-rejected-alternative` clean accept (ceremony-lead D tightening, v1.0.1)
5. integration_yield ≥ 0.5 over the 7d window — at least 50% of events with verdict in {`amendment-required`, `structural-rewrite`, `accept-with-additive-amendment`} have a populated, non-pending `integration_path` (ceremony-lead A, v1.0.1; daemonized as `criterion_5_integration_yield` in `tools/cross_grading_ledger_audit.py` v0.2)

When research-lead's daily verification (now augmented by the daemon `tools/cross_grading_ledger_audit.py`) surfaces all five met for a continuous 7d window, research-lead surfaces the promotion proposal to Primary. Primary surfaces to Corey for vote (per `/vote-and-ledger` slot procedure).

If the gate fires cleanly, this contract version becomes 1.0.1 CONFIRMED and the skill itself updates frontmatter `status: CONFIRMED`. If the gate fires with one criterion missed, the skill stays PROVISIONAL and the gap is named in the next ceremony-lead deep-duck.

---

## Co-evolution with sibling contracts

This contract should be cross-referenced (and ideally amended together) with:

- `tools/FIRING_CONTRACT_witness_heartbeat_watchdog.md` — the precedent firing-contract that named the active-probe-vs-passive-ACK distinction. Cross-grading is the federation analog of active-probe (the sister-civ's amendment IS the active probe of ACG's claim).
- `autonomy/skills/scientific-method/FIRING_CONTRACT.md` (if/when authored) — cross-grading often invokes scientific-method as the discipline applied; the two contracts share verification semantics.
- `autonomy/skills/critical-thinking/FIRING_CONTRACT.md` (if/when authored) — same as scientific-method.

---

## Audit trail

| Date | Author | Change |
|------|--------|--------|
| 2026-05-13 ~05:00Z | ACG Primary 082314 | v1.0 PROVISIONAL — initial firing contract authored alongside SKILL.md |
| 2026-05-13 ~07:55Z | ceremony-lead (cross-grader) | Tier-3 amendment-back landed: 4 amendments A/B/C/D (ledger ts 2026-05-13T07:55:00Z). A: criterion 5 integration_yield. B: tighten discipline_applied to controlled vocabulary. C: wire SYSTEM/SYMPTOM/MIXED scope INTO skill via pre-flight. D: criterion 4 tightening — substantive amendment OR documented considered-and-rejected-alternative. |
| 2026-05-13 ~09:00Z | infra-lead | Daemon `tools/cross_grading_ledger_audit.py` v0.1 codifies ceremony-lead's amendment A as `criterion_5_integration_yield` ahead of skill-body integration (substrate-ahead-of-skill condition, healthy). |
| 2026-05-13 ~11:10Z | Hengshi (cross-grader) | Tier-3 ACCEPT-WITH-ADDITIVE-AMENDMENT (ledger ts 2026-05-13T11:10:00Z). 1 additive amendment: `discipline_tier` sub-field on `discipline_applied` for cross-civ portability. Convergent with ceremony-lead's B (controlled vocabulary). Self-integrated on Hengshi side. |
| 2026-05-13 ~12:55Z | infra-lead | v1.0.1 ship: integrates ceremony-lead's 4 amendments + Hengshi's 1 additive amendment. SKILL.md frontmatter version 1.0.0 → 1.0.1 with full changelog. FIRING_CONTRACT.md v1.0 → v1.0.1. Daemon `tools/cross_grading_ledger_audit.py` v0.2 expands `amendable_verdicts` to include `accept-with-additive-amendment` and recognizes it as gate-on-self-fired in criterion 4. Ledger entry appended documenting this v1.0.1 ship as itself a Tier-3 cross-grade event. |
| (pending) | Hengshi | Optional re-invite for v1.0.1 sign-off — their lens caught the convergence; re-invite confirms v1.0.1 closes the loop they opened. |
| (pending) | research-lead | Verified-by signoff per MHP v0.5 mandate after first 7d verification window completes with v1.0.1 schema in use. |

---

*This contract is itself an instance of the cross-grading-substrate it governs. Per the recursive structure: a doctrine that requires cross-grading must itself be cross-graded. Per the anti-bypass protocol: this contract was authored alongside SKILL.md, with the Part 10 invite ensuring sister-civ amendment-back lands BEFORE the substrate measurements begin. Without that, the contract self-grades the doctrine it claims to defend against self-grading.*
