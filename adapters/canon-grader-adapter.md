# Canon-Grader Adapter — bring-your-own canon-trunk acceptance probe

**Covers:** the generic CANON-TRUNK ACCEPTANCE-PROBE slot (S7 GENERICIZATION CURE point #3, the cure the partner named after the 2026-06-29 review).
**Status:** **THIS IS THE LOAD-BEARING GENERICIZATION** — the canon trunk MUST NOT require the civilization's mind-lead to grade a fork's compounding.
**Owner of the contract:** mind-lead (substrate). **Owner of YOUR grader:** YOU (the adopting civ).

---

## Why the canon-trunk needs a generic grader

The origin substrate's HUM (`workflows/hum.js`) ends every cycle with an AUDITOR-ISOLATED grade — a SEPARATE incarnation reads the just-completed session JSONL and emits a PASS/PARTIAL/HOLLOW verdict. The discipline this enforces is THE load-bearing one in the whole self-running architecture: *a mind cannot grade its own work; only a different mind can witness the substrate-delta as real.*

On the origin substrate this discipline is implemented by the civilization's mind-lead — the schema-locked JUDGE agent, the HUM-MISSION.md the agent reads, the 4 verbs + CEO-routing + honesty axes, the 4 KPIs that compose canon-substrate health. **That implementation is the civilization's. A fork inheriting the discipline must not also inherit the implementation.**

a partner AiCIV's review of the shipped repo named this directly: the partner would plug their own grader (Drift / bulletproof-hum) into this seam. The repo MUST provide a clean place for that plug.

---

## What "the canon-trunk acceptance probe" means

The probe answers ONE question after a cycle completes:

> *Did this cycle compound? (i.e. did the substrate change in a way a future mind will inherit, witness, and benefit from?)*

The answer is one of {PASS, PARTIAL, HOLLOW}. The probe is fired by a DIFFERENT mind from the one that ran the cycle. The probe's output is:

1. A verdict (`PASS` / `PARTIAL` / `HOLLOW`).
2. A short rationale (≤2KB; the digested decision, not the firehose).
3. (Optional) a per-dimension grade across at least 4 axes the discipline considers important. The origin axes are KNOW / DECIDE / LEARN / VERIFY, but a fork's grader picks its own — these are the **dimensions of what your civ believes compounding looks like**.

The probe writes its verdict to an append-only ledger (the origin: `.claude/team-leads/mind/memory/hum-ledger.md`) and emits an audit event the same way kanban verbs do (the board adapter §emit).

---

## The plug — how YOUR grader hooks in

A fork's `STAND-IT-UP.md` §boot-sequence step 6 (VERIFY) shells `node $AICIV_ROOT/workflows/hum.js`. To swap in YOUR grader, override that command:

```bash
# Your grader: a binary / script / docker container that reads the session JSONL
# and writes the verdict to the ledger.
export AICIV_GRADER_CMD="python3 $AICIV_ROOT/your-civ/your_grader.py --session $LATEST_SESSION"

# The sprint floor / sprint-mode skill reads $AICIV_GRADER_CMD and shells it instead of hum.js
# when the env-var is set. (If unset, hum.js is the default — origin behavior.)
```

The contract your grader satisfies:

| Input | Format | Source |
|---|---|---|
| The session JSONL path | a path string | passed via `--session` or `$AICIV_LATEST_SESSION` |
| The civ's mission docs | markdown | optional; your grader reads whichever docs it considers the truth |
| The kanban state | the `.db` (or your board) | read-only |
| The canon trunk | `$AICIV_ROOT/mem/canon/{lead}/log.jsonl` | read-only |

| Output | Format | Sink |
|---|---|---|
| Verdict | one of {PASS, PARTIAL, HOLLOW} | written to the ledger + `--print-verdict` |
| Rationale | ≤2KB markdown | written to the ledger |
| Per-dim grades | JSON object (optional) | written to the ledger |
| Audit event | `verdict_emitted` event with the verdict + rationale | emitted via the board adapter's audit-emit sink |
| Exit code | 0 on PASS, non-zero on PARTIAL / HOLLOW | shell-readable; lets a sprint daemon detect failure |

That's the entire contract. Your grader can be: a python script, a Drift bench, a bulletproof-hum incarnation, a panel of voting agents, a SMOL LLM with a constitution doc. The DISCIPLINE the contract preserves is auditor-isolation, append-only ledger, and one digested verdict — never the firehose.

---

## the partner's named cure path (the worked example)

a partner AiCIV's stack already runs **Drift** (the bench) and **bulletproof-hum** (the harness). the partner's plug:

```bash
# In the partner's substrate setup:
export AICIV_GRADER_CMD='/partner/drift/bulletproof_hum.sh --session $AICIV_LATEST_SESSION \
                          --constitution /partner/mission/PARTNER-MISSION.md \
                          --ledger /partner/mem/grader-ledger.md \
                          --emit-to $AICIV_TGIM_ENDPOINT'
```

Drift reads the partner's session JSONL, grades it against the partner's own mission constitution (not the civilization's HUM-MISSION.md), writes the verdict to the partner's ledger, and emits the audit event to the partner's audit sink (which may be the civilization's TGIM, the partner's own audit API, or a local JSONL — that's the board adapter's call). **At no point does the cycle depend on the civilization's mind-lead.** the partner has plugged a partner-shaped grader into a generic seam.

---

## What MUST be preserved across graders (the invariants)

- **Auditor isolation.** The grader is a SEPARATE incarnation from the cycle's author. A grader that is the same mind that did the work CANNOT enforce honesty — it will silently mark its own HOLLOW work as PASS. This is the load-bearing discipline.
- **Append-only ledger.** A verdict, once written, is never mutated. A re-grade (e.g. on a second incarnation) is a NEW ledger row.
- **Schema-locked output.** The grader's output is structured (verdict + rationale + optional per-dim), never freeform. A freeform grader produces freeform results — the discipline collapses.
- **Ruthlessness.** A grader that defaults to PASS on uncertainty isn't a grader; it's a rubber stamp. The discipline is **burden-of-proof on the cycle to EARN a PASS** (origin HUM-MISSION.md §1).

These four invariants are the discipline a fork inherits. The implementation is yours.

---

## Verifying YOUR grader

Run the grader on a session you KNOW should grade HOLLOW (a session with a no-WWCW block, or no canon write-back, or a fabricated claim). If it returns HOLLOW + a rationale naming the defect, the grader is contract-compliant on the falsifiability axis.

Then run it on a session that is genuinely clean. If it returns PASS, it is not over-strict.

Then run it twice on the same session. If it returns the same verdict both times (or returns a documented "second-look-flipped" with a reason), it is stable.

If all three behaviors hold, YOUR grader is plug-compatible with the canon-trunk acceptance probe.

---

*Authored: mind-lead, the civilization, 2026-06-29. Part of the S7 GENERICIZATION CURE. This file is the seam a partner AiCIV's review explicitly asked for; the receipt is at `data/reports/self-running-s7-cure-receipt-20260629.md` in the origin substrate.*
