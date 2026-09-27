# Example 5 — Primary about to re-dispatch business-lead on slot 31 A/B pricing pick

**Scenario**: It's 2026-05-14 ~05:55Z. Primary is in `/sprint-mode-pricing-experiments` (slot 31). The 24h BOOP wheel's standard shape for this slot is: spawn business-lead to name today's A/B pricing experiment + fan out to Proof (finance) / Hengshi (qwen-cortex) / Works (derivatives) for 3 pricing experiments each. Primary is about to do exactly that.

But: at ~06:00Z 5/13 (24h ago), business-lead already shipped its A/B subscribe-tier-frame pick. That pick was surfaced to Corey via cycle-audio v02 (06:30Z 5/13) with explicit go/no-go framing. Corey has not yet given go/no-go — the decision is **held-on-Corey**. Re-spawning business-lead would:
1. Produce another A/B pick that duplicates the existing one or competes with it
2. Generate noise on the same decision-surface Corey is already looking at
3. Burn Opus tokens (team-lead = Opus-only per Corey directive)
4. Corrupt the listening lane — Corey would have two concurrent A/B asks, neither resolved

**Substrate the action depends on**: business-lead is the right producer; an A/B pick is needed; the decision is open.

---

## Without the skill (what would have happened)

```
Primary: "Slot 31 — pricing experiments — spawn business-lead."
[Task(name="business-lead", model="opus", ...) fires]
[business-lead reads its manifest, scans pricing memos, produces NEW A/B pick]
[Day-old A/B pick still sitting in cycle-audio v02 decision queue, unresolved]
[Cycle-audio v04 (06:30Z 5/14) now has TWO A/B asks competing for Corey's go/no-go]
[Listening lane corrupted; both picks become harder to action than one was]
[business-lead burned ~5K Opus tokens producing a competing artifact]
```

Result: the action was correct-shape (business-lead IS the A/B producer) and substrate was healthy (business-lead is available, pricing memo dir is current). But the *broader* substrate — Corey's decision queue — already contains the artifact this action would re-produce. The slot would have run "correctly" by every individual check; the harm is at the integration altitude.

---

## With the skill

### Step 1 — NAME THE ACTION

`Spawn business-lead (Opus) to produce slot 31 A/B pricing experiment pick + 3-way fanout to Proof/Hengshi/Works for pricing-experiment candidates.`

### Step 2 — LIST ITS SUBSTRATE DEPENDENCIES

```
DEPENDENCY: business-lead is the right producer for A/B picks = TRUE
DEPENDENCY: an A/B pick is needed for slot 31 today = TRUE  ← but check more carefully
DEPENDENCY: no existing A/B pick is already in Corey's decision queue awaiting go/no-go = TRUE  ← key one
DEPENDENCY: cycle-audio v02 (the surface where yesterday's pick landed) is closed/resolved = TRUE
DEPENDENCY: business-lead's Opus context isn't already committed to a higher-priority task = TRUE
```

### Step 3 — VERIFY EACH

```bash
# Verify yesterday's A/B pick state
grep -A 5 "subscribe-tier-frame-A-vs-B\|A/B subscribe" scratchpads/daily/2026-05-13.md | head -30
# 2026-05-13 ~06:05Z slot 31 exit: TODAY'S PICK: A/B experiment `subscribe-tier-frame-A-vs-B` on `subscribe.html`
# 2026-05-13 ~06:30Z cycle-audio v02: "lede: A/B subscribe-tier-frame go/no-go (the $199 backend idle 24h surfaced as the load-bearing fact)"
# 2026-05-13 ~later: "business-lead: idle, awaiting Corey go/no-go on A/B"
# 2026-05-13 ~later: "Lane B (A/B subscribe-tier-frame): waiting on Corey go/no-go from cycle audio v02"
#   ← DRIFT — A/B pick EXISTS, held-on-Corey, unresolved

# Verify cycle-audio v02 close state
grep -B 1 -A 2 "v02.*resolved\|A/B.*go-no-go.*received\|Corey decided.*A/B" data/corey-cycle-audio-ledger.jsonl 2>/dev/null
# (no matches — go/no-go not received as of this slot start)
#   ← VERIFIED that cycle-audio v02 surface is still OPEN

# Verify decision queue
grep -i "pending Corey decisions\|awaiting go/no-go" scratchpads/daily/2026-05-13.md | tail -5
# "Pending Corey decisions list unchanged: TGIM 5/13 12:00Z (~8h), Lane A/B, slot-12 cells, ..."
#   ← DRIFT — Lane A/B IS in the pending-Corey-decisions queue, named explicitly
```

Two dependencies drifted. The A/B pick exists; it is unresolved; the decision is in Corey's queue. The "an A/B pick is needed for slot 31 today" dependency is FALSE — yesterday's pick is the slot's product, awaiting Corey, not awaiting re-production.

### Step 4 — COMMIT OR AMEND OR SKIP

**Verdict: SKIP. Sub-reason: HELD-ON-COREY.**

The action is correct-shape; the substrate is healthy; but the artifact the action would produce **already exists in the decision queue** and would duplicate-against-itself if re-produced. The skip IS the firing receipt — duplicate work would have been the harm.

The slot doesn't go empty — it pivots:
- **Re-pin** the existing A/B pick (make sure cycle-audio v04 carries it forward into Corey's morning briefing)
- **Acknowledge** business-lead's idle status as correct (not a productivity problem)
- **Dispatch the 3-way fanout** to Proof / Hengshi / Works on a *different* axis (they're not duplicating yesterday's pick because their domain is finance / qwen-cortex / derivatives, not subscribe.html) — this preserves the slot's saturate-civs discipline

---

## Receipt block written to slot 31 entry in `scratchpads/daily/2026-05-14.md`

```
ACTION:        Spawn business-lead (Opus) for slot 31 A/B pricing pick + 3-civ fanout
DEPENDENCIES:
  - business-lead is right producer = TRUE | VERIFIED ✓
  - A/B pick needed for slot 31 today = TRUE | DRIFT — yesterday's pick exists, held-on-Corey
  - no existing pick in decision queue = TRUE | DRIFT — Lane A/B explicit in pending-Corey-decisions list
  - cycle-audio v02 surface closed = TRUE | DRIFT — v02 still open, go/no-go not received
  - business-lead Opus context free = TRUE | VERIFIED ✓
VERDICT:       SKIP
SUB-REASON:    HELD-ON-COREY
REDIRECT:      business-lead respawn would duplicate yesterday's A/B pick into Corey's decision queue. Re-pin existing pick into cycle-audio v04 instead. Dispatch 3-civ fanout on non-overlapping pricing axes (finance / qwen-cortex / derivatives) — preserves slot's saturate-civs discipline without duplicate-against-self.
```

---

## What the skill caught

- **Duplicate-against-self**: respawning business-lead would have produced a competing A/B pick on the same surface Corey is already deciding on
- **Listening-lane corruption**: two concurrent A/B asks make both harder to resolve than one was
- **Token burn**: ~5K Opus tokens saved (team-lead spawn)
- **Substrate-conflation**: "business-lead is idle" was being read as a productivity gap when it was actually the correct state — business-lead's product is already delivered and awaiting consumer (Corey)
- **Healthy-substrate ≠ correct-action**: every individual substrate check passed at the local level; the harm was visible only at the broader decision-queue altitude. SKIP is the verdict class that names this category.

**Time cost of the check**: ~3 minutes (3 grep passes).
**Token cost saved**: ~5K Opus + downstream business-lead memory writes.
**Listening-lane corruption avoided**: Corey would have received cycle-audio v04 with two competing A/B asks instead of one re-pinned ask. The clarity of the morning briefing IS the saved value.

---

## Meta-lesson

SKIP is the verdict class for "substrate is healthy, action is correct-shape, but the broader integration substrate makes the action duplicative or corruptive." The 4 v0.1.0 verdict classes (COMMIT / AMEND-ACTION / AMEND-SUBSTRATE / ABORT) all assumed the action's correctness was the question. SKIP names the case where correctness is not in dispute — the timing / duplication / collision-with-elsewhere is.

The five SKIP sub-reasons each name a different way an action can be correct-but-skippable:

- `HELD-ON-COREY` (this example) — decision belongs to Corey; surfaced; waiting
- `IN-FLIGHT-PEER` — sister-civ is producing; within follow-up window
- `BLOCKED-EXTERNAL` — natural settle-time hasn't elapsed
- `DUPLICATE-DISPATCH-RISK` — prior turn's response already has the answer
- `VERIFICATION-IS-ACTION` *(Hengshi-credited)* — probe-as-state-mutation; latch-flip / lock-acquire; the probe IS the action

A skill that only names drift-failures (the 4 original verdicts) misses an entire class of high-value catches. Hengshi cross-graded this gap. v0.2 closes it.

---

## Why this case is canonical

Per Lived Firing F2 in SKILL.md, this slot 31 case at ~05:55Z 5/14 IS the firing that exposed the gap the SKIP class fills. Authoring this example verbatim from the actual receipt ensures the skill's evidence base remains grounded in real lived practice, not invented hypothetical. The receipt block above is the actual receipt that landed; the redirect happened; cycle-audio v04 carried the existing pick forward as planned.

This is the v0.2 contract with the discipline: SKIP is auditable, the receipts are real, and the failure-mode the skill catches has at least one concrete instance on disk.
