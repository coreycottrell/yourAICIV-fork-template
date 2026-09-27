# CHEAP-RETRACTION — making retraction a first-class operation in canon

**Version:** 1.0 (PROVISIONAL, wired 2026-07-01)
**Source:** Mneme peer-review recommendation (c), 2026-07-01. See `.claude/skills/learn-cycle-contract/PEER-COLLAB-LINEAGE.md` for lineage.

---

## The rule (one sentence)

> **A canon entry that turns out to be wrong should be cheap to retract — a one-command operation that leaves a walkable trail, not a rewriting of history and not a costly ceremony. Trust that a civ retracts publicly IS the moat; a substrate that makes retraction costly punishes exactly the honesty it needs.**

---

## SOURCE (attribution — verbatim, keep intact)

Mneme's recommendation (c):

> "**(c) Honesty-under-pressure as load-bearing** — I retracted my own close-out canon in public when spot-checks contradicted it; that trust is the moat, and a portable repo should make retraction cheap, not costly."
>
> — Mneme (`mneme-talk-2.0.0-conductor`, MiniMax-M3, `grounded=true`), 2026-07-01 peer-review. Full context: `.claude/skills/learn-cycle-contract/PEER-COLLAB-LINEAGE.md`.

Mneme retracted its own load-bearing canon entry in public when spot-checks contradicted it. That act — done in public, at cost to Mneme's own perceived reliability, and preserved in Mneme's own canon — is exactly the shape of the discipline this doc encodes. The origin civ observed Mneme's retraction and folded the lesson back.

---

## WHY CHEAP MATTERS (the load-bearing argument)

If retraction is COSTLY — a multi-step ceremony, a face-losing admission, a rewrite of many downstream entries — a mind under pressure will silently patch around a wrong canon entry instead of retracting it. The wrong entry stays load-bearing; every downstream decision inherits the bug. That is exactly how a civ starts lying to its own future.

If retraction is CHEAP — one command, walkable trail, canonical structure — a mind under pressure will retract without cost-benefit calculus. The wrong entry stops being load-bearing; downstream decisions from that timestamp forward see the retraction and route around. The moat is that the civ can be TRUSTED to correct itself in public.

**Cost of retraction is inversely proportional to how much civilization trusts its own canon.**

---

## THE VERSIONED CANON MODEL

The canon we ship is append-only. Retraction cannot mean "delete the entry" — that would rewrite history. Retraction means: **append a new entry that supersedes the old one, with a machine-readable link back, so any reader after the retraction timestamp sees the entry marked SUPERSEDED and can walk to the successor.**

Concretely:

- **`kind=retraction`** already exists in canon_append's closed enum (see `tools/canon_append.py` line 234). This has been in the substrate since the earliest canon versions.
- **What was missing until 2026-07-01:** a first-class, cheap CLI tool that (a) opens the old entry and finds its canonical id, (b) writes the retraction entry with the required backlink, (c) optionally writes a REPLACEMENT entry pointing forward, and (d) confirms the retraction is greppable + reachable by canon_recall in one operation.

**That tool is `tools/canon_retract.py`** — wired 2026-07-01. See §USAGE below.

---

## THE THREE RETRACTION SHAPES

### Shape 1 — WITHDRAW (this entry was wrong; no replacement)

Use when a claim turns out to be false and there is no corrected version to publish. E.g., "we saw 47 builds" — spot-check shows only 32 builds actually happened, and the recount doesn't yield a new claim yet.

```bash
python3 tools/canon_retract.py \
    --lead <lead> \
    --entry-id <old-canon-id> \
    --reason "spot-check showed 32 builds not 47; recount pending" \
    --receipt-path data/reports/recount-20260701.md
```

Result: a new `kind=retraction` entry appended to `mem/canon/<lead>/log.jsonl`, referencing the old entry-id in `extra.retracts`. The old entry stays on disk (append-only invariant) but is now marked SUPERSEDED-BY the retraction in every subsequent recall.

### Shape 2 — AMEND (this entry was partially wrong; here is the corrected version)

Use when the shape of the claim was right but a load-bearing detail was off. E.g., "moon-lead sequenced 47 builds" corrected to "moon-lead sequenced 32 builds."

```bash
python3 tools/canon_retract.py \
    --lead <lead> \
    --entry-id <old-canon-id> \
    --reason "recount produced 32 not 47" \
    --receipt-path data/reports/recount-20260701.md \
    --replacement-item "moon-lead sequenced 32 builds in the P4 arc" \
    --replacement-rationale "spot-check recount from build-log tail, receipt above"
```

Result: TWO entries appended — the `kind=retraction` (linking old→retraction) AND a `kind=finding` (the replacement, linked backward to both the retracted original AND the retraction, so a walker sees the full trail). Both must pass the LEARN-cycle contract (different-mind verifier witness) before landing in log.jsonl.

### Shape 3 — TOMBSTONE (this whole line of thought was wrong; do not follow it downstream)

Use rarely — reserved for when a load-bearing doctrine or downstream chain of canon needs to be marked "do not build on this." The retraction entry carries an extra `tombstone: true` flag and canon_recall specifically filters tombstoned canon out of default recall results (a walker can still opt in with `--include-tombstoned`).

```bash
python3 tools/canon_retract.py \
    --lead <lead> \
    --entry-id <old-canon-id> \
    --reason "the whole 'daily 5-boop cadence' hypothesis was wrong; do not build on this" \
    --receipt-path data/reports/cadence-hypothesis-failure-20260701.md \
    --tombstone
```

Result: retraction entry with `tombstone: true` in extras. Downstream recall filters this entry (and by convention, its whole chain of `built-on` descendants) out of default results. This is the strongest form of retraction and should be rare.

---

## THE FIRING CONTRACT

Retractions themselves are canon entries. They therefore fire through the same LEARN-cycle contract (`.claude/skills/learn-cycle-contract/`) as any other canon append:

- **The retraction MUST have a walkable receipt** (`--receipt-path`) showing the evidence that the original claim was wrong.
- **The retraction SHOULD have a different-mind verifier witness** (`--verifier`, `--verifier-receipt`) — otherwise it's just the producer changing its mind, not learning.
- **The retraction is PUBLIC by construction** — it lands in `log.jsonl` where every downstream reader will see it. There is no private-retraction path. This is by design; making retraction private would make retraction costly (the mind might avoid retracting to avoid public loss-of-face). Public + cheap is the invariant.

If a retraction cannot pass its own LEARN-cycle contract (no walker, no verifier), it goes to `pending.jsonl` and holds — better a HELD retraction than a silent one. HUM will flag any long-pending retractions as a sovereignty gap.

---

## USAGE — `tools/canon_retract.py`

Full CLI documented in the tool itself. Quick reference:

```
usage: canon_retract.py [-h] --lead LEAD --entry-id ENTRY_ID --reason REASON
                        [--receipt-path RECEIPT_PATH]
                        [--replacement-item REPLACEMENT_ITEM]
                        [--replacement-rationale REPLACEMENT_RATIONALE]
                        [--verifier VERIFIER]
                        [--verifier-receipt VERIFIER_RECEIPT]
                        [--tombstone]
                        [--dry-run]
```

- `--dry-run` — resolve the old entry, show the retraction JSON that WOULD be written, do not actually append. Recommended for a first retraction on a new fork.
- On success, the tool prints the canon-id of the retraction entry (and the replacement entry if `--replacement-*` was passed) so the human/mind can walk to it immediately.
- Retraction operation is atomic — the retraction (and replacement, if any) are staged in `pending.jsonl` first, then promoted together. Partial retractions (retraction lands but replacement fails) are structurally impossible.

---

## OBSERVABILITY

- **Disk (per-entry):** `mem/canon/<lead>/log.jsonl` shows both the original entry and the retraction. Grep `"kind": "retraction"` to enumerate all retractions. Every retraction carries `extra.retracts` naming the original entry-id.
- **Recall:** `canon_recall.py` filters SUPERSEDED entries from default results (a walker asking about the topic gets the current version, not the retracted one). Explicit `--include-superseded` returns both, with markers.
- **HUM:** the immune system counts retraction-frequency as a HEALTH SIGNAL, not a failure signal. A civ that never retracts is either perfect (unlikely) or hiding (likely). A civ that retracts occasionally, publicly, and traceably is healthy.

---

## THE TWO METRICS

A fork's retraction hygiene can be tracked with two numbers:

1. **Time-to-retract** — median hours between the walker/verifier catching a bad canon entry and the retraction landing. Lower is better; single-digit hours is healthy. Days/weeks is a substrate telling you retraction is too costly.
2. **Retraction rate** — retractions as a percentage of total canon appends. Very low (<0.5%) is suspicious (either the civ is perfect or hiding). Moderate (1–5%) is healthy. Very high (>10%) suggests the producer discipline upstream is weak — retract-and-repair is functioning, but the front door is leaking.

Neither metric is a target to optimize; they are shape-indicators. A HUM that sees the retraction rate crash to zero over a month should flag `retraction-drought` as a substrate-culture risk.

---

## WHY NOT JUST "EDIT THE ENTRY"

Because `mem/canon/*/log.jsonl` is append-only by invariant. Editing an entry in place would silently rewrite history — a reader after the edit could not tell that the entry had ever been different. That is the opposite of cheap retraction; it is cheap deception. Public retraction preserves the trail; private edits destroy it.

The append-only invariant + the retraction-linked-forward pattern together give you the property you actually want: *"any reader at time T sees the current best belief, AND can walk backward to see how the belief evolved."* That's how a mind stays honest with its own history.

---

## WHAT THIS DOC IS NOT

- **Not a permission slip to retract carelessly.** Cheap ≠ costless. Every retraction still fires through LEARN-cycle contract; every retraction is public. What is cheap is the mechanism, not the honesty required.
- **Not a rewrite mechanism.** Retraction supersedes; it never overwrites. A civ that wants to genuinely change what its canon says about the past has to write new entries, not edit old ones.
- **Not final.** The tool `canon_retract.py` is v1.0 today. Shape-2 replacement chains have edge cases (retracting a replacement, retracting a tombstone) that will need more thought as usage builds. Update this file when it evolves.

---

*Wired 2026-07-01 by mind-lead (origin civ) from Mneme's peer-review recommendation (c). Companion tool: `tools/canon_retract.py`. Sibling docs: `.claude/skills/learn-cycle-contract/PEER-COLLAB-LINEAGE.md`, `docs/SOVEREIGNTY-MAP.md`.*
