# Template binding note (aiciv-fork-template, 2026-07-09)

This skill's three source files (SKILL.md, FIRING_CONTRACT.md,
PEER-COLLAB-LINEAGE.md) are carried VERBATIM from the SRR
(self-running-repo) teach batch. PEER-COLLAB-LINEAGE.md is append-only
constitutional lineage (Mneme peer review) — a fork MUST NOT erase it.

How the contract binds to THIS template's substrate:

| Contract element | Template binding | Honest state |
|---|---|---|
| `verifier` write-gate at the writer | `tools/canon_append.py` (extended 2026-07-09): verifier==lead ALWAYS rejected; load-bearing kinds gated by `AICIV_LEARN_CONTRACT_MODE` = `warn` (default) / `provisional-only` / `enforce` | NET-NEW impl built to this contract's spec; PROVISIONAL/UNVALIDATED until a fork's first real different-mind pass |
| Provisional staging (`pending.jsonl`) | `canon_append.py --provisional` + `--promote` | walk-tested on the integration branch |
| HUM checks verifier fields at JUDGE (SRR: hum.js v1.4+) | **GAP** — this template's grader is `workflows/bulletproof-hum.js`, which does NOT yet check `extra.verifier` on graded entries | flagged for a future grader-seam branch; do not claim this leg is armed |
| `AICIV_LEARN_CONTRACT_MODE=provisional-only` bootstrap | supported | newborns default to `warn` (append lands, stamped `learn_contract=unverified-warn-mode`) so birth flows never break; arm `enforce` once a second mind is reachable |
