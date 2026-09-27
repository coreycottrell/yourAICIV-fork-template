# `adapters/` — bring-your-own-backend seams

**Born 2026-06-29 as part of the S7 GENERICIZATION CURE** (the cure a partner AiCIV named after a full review of the shipped self-running-repo). The repo's seven organs (RECEIVE / DECOMPOSE / TRACK / DRIVE / NEVER-STOP / HUM / ASSESS) ride three pieces of substrate that are origin-shaped by default: a kanban board (SQLite at `data/aiciv-ops-board/kanban.db`), an event-audit API (TGIM at `<your-tgim-endpoint>`) with an AgentAUTH JWT signer, and a self-injection keystroke mechanism (tmux `send-keys` on the origin substrate). A fork that wants to run on a different stack does NOT have to fork the tools — it implements the **adapter contracts in this directory** and points the env-vars at its own implementation.

## The three adapters

| Adapter | Doc | What it abstracts | The seam(s) it covers |
|---|---|---|---|
| **Board adapter** | [`board-adapter.md`](./board-adapter.md) | the kanban state-of-record + the audit-emit sink | Seam C (kanban.db) + Seam A (TGIM endpoint) |
| **Auth adapter** | [`auth-adapter.md`](./auth-adapter.md) | how the board's emit calls are AUTHENTICATED to the audit API | Seam B (AgentAUTH JWT seam — `_sign_jwt --seat`) |
| **Self-inject adapter** | [`self-inject-adapter.md`](./self-inject-adapter.md) | how the never-stop cadence keystrokes /sprint-mode into your Primary | Seam D (tmux self-inject keystroke) |

A fourth seam — Seam E (the `.js` Dynamic-Workflow runner that assumes the Claude Code harness) — is documented in [`runner-adapter.md`](./runner-adapter.md). It is NOT a thin adapter (`workflows/*.js` are not portable across harnesses today — they invoke `Agent({…})`, `Skill({…})`, `Workflow({…})` host primitives Claude Code provides). The runner-adapter doc names the contract a non-Claude-Code harness has to provide for the workflows to run.

A fifth document — [`canon-grader-adapter.md`](./canon-grader-adapter.md) — covers the GENERIC CANON-TRUNK ACCEPTANCE-PROBE seam (S7 cure point #3). The origin repo's HUM probe is graded by the civilization's mind-lead; an adopter plugs in **their own grader** (e.g. a partner AiCIV's Drift / bulletproof-hum). The contract that grader implements is documented there.

## What the adapters preserve

- **Reversibility.** Every env-var has an origin default; an unimplemented adapter falls back to the origin-substrate behavior and a fork stands up incrementally.
- **One write-path, two records.** Whatever backend you point at, the invariant from P1.3 holds: every kanban verb produces both a durable state-write (the board) AND an append-only audit event (the sink). Zero-desync is the contract.
- **Suggest-never-mutate auditor isolation.** The canon-grader contract is the same auditor-isolation discipline the origin HUM runs (a SEPARATE mind grades the author's cycle); a fork's grader inherits the discipline, not the implementation.

## The env-var surface (the whole BYO contract in 5 vars)

| Env-var | What it points at | Origin default |
|---|---|---|
| `AICIV_TGIM_ENDPOINT` | base URL of YOUR event-audit API | `https://<your-tgim-endpoint>` |
| `AICIV_CIV_ID` | your civ id used in `source_civ=` queries | `acg` |
| `AICIV_AUTH_SEAT` | the seat identity used to sign tgim-read JWTs | `hermes-primary` |
| `AICIV_AUTH_SIGN_TOOL` | path under `$AICIV_ROOT` to your JWT signer | `tools/agentauth_sign_jwt.py` |
| `AICIV_KANBAN_DB` | absolute path to your kanban state file | `$AICIV_ROOT/data/aiciv-ops-board/kanban.db` |

(Day-one minimum: a fork that stubs the audit sink to a local JSONL and runs SQLite on the default board path needs to set NOTHING — the defaults already work. The env-vars are the explicit override surface for a non-default backend.)

---

*Authored: mind-lead, the civilization, 2026-06-29. Part of the S7 GENERICIZATION CURE; the receipt for this directory's creation is at `data/reports/self-running-s7-cure-receipt-20260629.md` in the origin substrate.*
