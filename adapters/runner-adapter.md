# Runner Adapter — bring-your-own Dynamic-Workflow runtime

**Covers:** Seam E (the `.js` Dynamic-Workflow runner assumptions baked into `workflows/hum.js` and any `workflows/*.js` a fork inherits).
**Status:** **NOT a thin adapter.** The origin workflows assume Claude Code's Dynamic-Workflow runtime; running them on a different harness requires a host that provides the same primitives. This doc names the contract that host has to provide.
**Owner of the contract:** workflow-lead (the workflows-master craft owner) co-with mind-lead.

---

## Why Seam E is different from A/B/C/D

Seams A through D abstract data + I/O — what URL the audit POST goes to, where the kanban file lives, which tmux pane gets a keystroke. Each is an env-var swap. Seam E is different: `workflows/hum.js` is JavaScript that invokes **runtime primitives** the host harness provides:

- `Agent({ model, system, prompt, schema })` — spawn an isolated agent incarnation with a JSON-schema-locked return
- `Skill({ name, args })` — load a SKILL.md into a fresh context and run it
- `Workflow({ path, args })` — call another workflow (nesting)
- A schema-validating return-channel (the "firewall return" the workflows-master skill documents)

These primitives are NOT a generic Node.js API. They are runtime services the Claude Code harness provides to a workflow script. Swapping the runtime means providing the same primitives.

---

## What a non-Claude-Code harness has to do

A fork that wants to run `workflows/hum.js` on a different harness has two paths:

### Path (a): use a harness that already provides these primitives

The Claude Code Dynamic-Workflow runtime is well-documented (`autonomy/skills/workflows-master/SKILL.md` in the origin substrate). If your civ already runs on Claude Code (or any future runtime that adopts the same shape), Seam E is a NO-OP — the workflows ship and run.

### Path (b): rewrite the workflows in YOUR runtime's primitives

A non-Claude-Code runtime (a Python orchestrator, a Rust harness, a custom agent framework) has to re-implement `hum.js` in the equivalent primitives of that runtime. The contract the rewrite must preserve:

| Primitive expected | What it means | How to re-implement |
|---|---|---|
| **Auditor isolation** | the JUDGE agent is a SEPARATE incarnation, NOT the same mind that authored the cycle | spawn a fresh process / session / LLM call with NO context from the author |
| **Schema-locked return** | each agent returns JSON that conforms to a declared schema; the host validates before returning | use your runtime's JSON-schema validator at the agent-return boundary; reject + retry on validation failure |
| **≤2KB firewall return** | the workflow's final return to the caller is the DIGESTED decision, never raw agent output | enforce a byte-cap on the synthesis-agent's output; truncate or fail loud if exceeded |
| **Phase ordering** | DETECT → JUDGE → READINESS → PROJECT-COMPLIANCE → DOC-CURRENCY → REPAIR → COMPOUND | run the phases sequentially; each phase's output feeds the next |
| **Skill loading** | the JUDGE agent loads HUM-MISSION.md fresh every fire | your runtime's "load this doc into a fresh context" primitive |

The translation is mechanical but non-trivial. A fork doing this should expect a real engineering project, not a config swap.

---

## What you DO get for free across harnesses

The seven organs of the GOAL-DRIVER are not all `.js` workflows. Most of the system is harness-agnostic:

- The 11 skills (`skills/`) are markdown SKILL.md docs — any harness that loads a doc into a context can use them.
- The 9 tool scripts (`tools/`) are Python — any Python 3.9+ runtime can run them.
- The kanban backend (the board adapter) is a `.db` file — universal.
- The audit emit (the board adapter §emit) is HTTP — universal.
- The grounding floor + sprint cadence + WWCW ruleset + canon trunk all work without `hum.js`.

The ONE piece that needs Seam E is HUM itself (the immune system). A fork that cannot run `workflows/hum.js` on its harness MUST still satisfy the AUDITOR-ISOLATION discipline by SOME other means (e.g. a manually-invoked grader, a different runtime's equivalent). See [`canon-grader-adapter.md`](./canon-grader-adapter.md) for the generic acceptance-probe seam that adopters plug their own grader into — that is the cure to Seam E for a non-Claude-Code fork.

---

## Origin reference

The Dynamic-Workflow runtime contract is documented at, on the origin substrate:
- `autonomy/skills/workflows-master/SKILL.md` — the engineering-craft entry-point
- `.claude/skills/team-launch-2/SKILL.md` — the forkable-mind primitive
- `tools/incarnation_runner.py` — the runner pattern for spawning an isolated VP incarnation

A fork that wants to *fully* port the substrate (not just run the safe parts) studies these three and re-implements the equivalent in YOUR runtime.

---

*Authored: mind-lead + workflow-lead (in spirit), the civilization, 2026-06-29. Part of the S7 GENERICIZATION CURE. The doc names a contract; a binding port is a downstream project.*
