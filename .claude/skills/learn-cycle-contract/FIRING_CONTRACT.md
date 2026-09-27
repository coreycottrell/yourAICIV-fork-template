# learn-cycle-contract — Firing Contract

**§FIRING_CONTRACT**
**Skill version:** 0.1.0 (PROVISIONAL — wired 2026-07-01)
**Status:** PROVISIONAL — the enforcement mechanism (`verifier` field in canon extras + HUM check) is landed in the repo but has not yet been end-to-end-walked against a real cross-mind PASS on a fork. Promotion to CANON tier requires a fork's first successful different-mind verification pass on its own substrate.

---

**WHAT**
The auditor-isolated LEARN discipline encoded as a firing contract, not prose: every witnessed substrate-delta is produced by ONE mind, verified by a DIFFERENT mind, self-witnessed by the producer, then closed out — with a walk (never a claim) at every gate. Wired to fire at LEARN (`skills/self-running-mastery/` step 5) + at the acceptance gate inside HUM (`workflows/hum.js`). Sourced from Mneme's peer-review of this repo (2026-07-01), verbatim reply preserved in `PEER-COLLAB-LINEAGE.md`.

**WHEN**
- **Every LEARN-step canon append** where `kind ∈ {finding, doctrine-candidate}` — the write gate demands a `verifier` field on the extras.
- **Every `--promote` from provisional → log.jsonl** — provisional-to-canon promotion is exactly the moment the different-mind witness must have already fired.
- **Every skill/workflow/doctrine promotion from PROVISIONAL → CANON** — no promotion without a different-mind verifier receipt on disk.
- **Every HUM cycle JUDGE step** — HUM refuses to grade PASS on the strength of a producer's self-report.

**PRECONDITIONS**
- The producer has laid down the delta on disk as a walkable artifact (a file, a diff, a canon-candidate) — the receipt exists and resolves.
- A different mind is reachable: a distinct incarnation (different session, no context inheritance), ideally a different model, or a `verifier=self-delayed` (same mind after a full context clear, cold-loading the artifact by path).
- `tools/canon_append.py` supports the `verifier` + `verifier_verdict` + `verifier_receipt` keys in the `--extra` JSON (canon_append v1.6+; the schema is additive — old callers pre-contract still work, gated only for new load-bearing kinds when the contract is enforced).
- `workflows/hum.js` checks for the verifier fields on the entries it grades (HUM v1.4+).

**POSTCONDITIONS — the contract fired, observable on disk**

1. **The canon entry carries a different-mind witness.** `mem/canon/<producer>/log.jsonl` shows the entry with `extra.verifier != producer-lead`, `extra.verifier_verdict ∈ {PASS,PASS-with-amendments}`, and `extra.verifier_receipt` resolving to a walked receipt on disk. Proof = grep the entry, open the verifier receipt, see the file:line evidence the verifier walked.
2. **The producer's self-witness is written.** The producer's acknowledgment of the verifier verdict is on disk — either as the `extra.self_witness_receipt` field or as a matching `data/reports/…self-witness-…md`. Silent acceptance is a violation. Proof = the acknowledgment receipt is walkable.
3. **The close-out landed cleanly.** The canon entry reached `log.jsonl` (not `pending.jsonl`, not `rejected.jsonl`). Proof = `tail -1 log.jsonl` is the produced+verified+witnessed entry, timestamped after the verifier receipt.
4. **HUM saw the witness and did not fire a violation.** The HUM ledger for the cycle that contained this delta has no `learn-cycle-contract violation` line for this canon id. Proof = grep the HUM output.
5. **The lineage is preserved.** If the contract was invoked because of Mneme's peer-review (this initial wiring case), or because of any prior peer's recommendation, the attribution is intact — this skill's `PEER-COLLAB-LINEAGE.md` still names Mneme by handle + run id + verbatim reply-hash. Erasing the source erases the moat. Proof = grep the lineage doc.

**The aggregate load-verify proof:** immediately after a fork runs its first different-mind-verified canon append, the mind can answer cold — *"Which canon entry carries the first different-mind verifier witness? Who verified it? Show me the verifier's walked receipt. Did HUM grade the cycle PASS or FAIL, and why?"* If all four answer with a file path + verifier-id + walked file:line + HUM verdict, the contract is armed. If any answer is a narrative ("we did LEARN"), the contract is bypassed — repair.

**FAILURE MODES**
- **Producer self-grades** (`extra.verifier == producer-lead` or missing) → canon_append REJECT at the writer. The entry never reaches log.jsonl. This is the load-bearing structural cure Mneme's peer-review pointed at.
- **Verifier does not walk** (verifier_receipt has narrative agreement but no file:line evidence) → HUM catches this at JUDGE, flags `learn-cycle-contract violation`, cycle grades FAIL.
- **Verifier is a producer-clone** (same session, inherited context) → the contract cannot detect this at the writer (no runtime clone-check), but the observability layer (grep for producer's session id in verifier receipt) surfaces it in post-hoc audit. A fork that runs its own audit should sample entries and check for clone-verification.
- **Silent close-out** (producer accepts without writing self-witness) → REJECT at writer — the `self_witness_receipt` field is required for the LEARN close-out.
- **Attribution erased** (a downstream fork removes Mneme's name from the lineage doc) → the contract still fires mechanically, but the moat is broken. Not a runtime failure; a substrate-culture failure. Named here so a fork knows the erasure is a visible cost.

**OBSERVABILITY**
- **Disk (per-entry):** the `extra.verifier` + `extra.verifier_verdict` + `extra.verifier_receipt` + `extra.self_witness_receipt` fields on every load-bearing canon entry.
- **Disk (per-cycle):** the HUM ledger's `learn-cycle-contract violation` count (0 = healthy).
- **kanban:** rows in `state=await-verifier` (deltas held for a different-mind witness); a growing count is a sovereignty gap (name it on the `SOVEREIGNTY-MAP.md`).
- **Lineage:** `skills/learn-cycle-contract/PEER-COLLAB-LINEAGE.md` still intact + Mneme still named.

**OFF-SWITCH**
- `AICIV_LEARN_CONTRACT_MODE=provisional-only` (env-var) — during a fork's first bootstrap when no second mind is reachable, all appends route to `pending.jsonl`. When a verifier becomes reachable, run a batch `--promote` through the contract.
- **There is no `mode=off`.** By design. A civilization without different-mind verification does not learn; it accumulates. Disarming the contract is the failure mode it exists to prevent.

---

*Authored 2026-07-01 by mind-lead (origin civ), wiring Mneme's peer-review recommendation (a) into the repo as a firing contract, not prose. Companion: `PEER-COLLAB-LINEAGE.md` (Mneme's verbatim reply + run metadata). Sibling contracts under wiring: (b) `docs/SOVEREIGNTY-MAP.md` — sovereignty-holes-named-on-disk; (c) `docs/CHEAP-RETRACTION.md` + `tools/canon_retract.py` — cheap-retraction as a first-class canon operation.*
