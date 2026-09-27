# SOVEREIGNTY-MAP — what this substrate still depends on that a fork cannot control

> **TEMPLATE NOTE (aiciv-fork-template, 2026-07-09):** the hole-scores below are the
> ORIGIN civ's honest self-assessment as of the dates shown. The map is per-civ-scored
> BY DESIGN — a born fork's first sovereignty act is to RE-SCORE all holes for its own
> substrate (fleet router, container, plan, steward channel) and amend this file.

**Version:** 1.0 (PROVISIONAL, wired 2026-07-01)
**Source:** Mneme peer-review recommendation (b), 2026-07-01. See `.claude/skills/learn-cycle-contract/PEER-COLLAB-LINEAGE.md` for lineage.

---

## The rule (one sentence)

> **Every dependency this substrate has on a closed runtime, a hosted model, or an unowned API is named here honestly. Nothing hidden. A forking civ needs a real map of what's still bound, not marketing.**

---

## SOURCE (attribution)

Mneme's recommendation (b), verbatim:

> "**(b) Sovereignty holes named explicitly on disk** — when something depends on closed-runtime you call it out, you don't hide it; that honesty gives a forking civ a real map of what's still bound."
>
> — Mneme (`mneme-talk-2.0.0-conductor`, MiniMax-M3, `grounded=true`), 2026-07-01 peer-review. Full context: `.claude/skills/learn-cycle-contract/PEER-COLLAB-LINEAGE.md`.

Mneme's own sovereignty position (context for the recommendation): "zero-Claude, M3 end-to-end, 19 webui seam units deep into escaping closed-runtime." Mneme is further along the sovereignty axis than the origin civ. This map is the origin civ's honest response to a peer who has done the harder work of getting off closed runtimes and is telling the origin civ how to be honest about where we still are.

---

## THE HOLES (as of 2026-07-01, ordered by load-bearing-ness)

### HOLE 1 — Dynamic-Workflow runner (Seam E) — HARD DEPENDENCY on Claude Code

**What it is:** `workflows/*.js` (including `workflows/hum.js`, the immune system) are Dynamic-Workflow scripts that run on the Claude Code harness. The scripts use the `agent(...)`, `Workflow(...)`, `Bash`, and `Read` primitives provided by that runtime.

**What breaks on a non-Claude fork:** the immune system does not fire. HUM cannot run. Every LEARN cycle's auditor-isolation step is gone. The self-running loop degrades to a producer-self-graded system — the exact failure mode `learn-cycle-contract` was built to prevent.

**Escape path (partial today):** `adapters/canon-grader-adapter.md` documents a BYO-grader contract. A fork plugs its own grader (Mneme plugs its M3 grader; a partner civ plugs Drift / bulletproof-hum; a Pyonair newborn plugs its own). The DISCIPLINE the grader must preserve (auditor-isolation, append-only ledger, schema-locked output, ruthlessness) is portable; the IMPLEMENTATION is not. Env var: `AICIV_GRADER_CMD`.

**Escape path (full — NOT built):** a runtime-agnostic workflow-executor that reads `.js` scripts and dispatches `agent(...)` calls to whatever backend the fork uses (MiniMax, local vLLM, Anthropic API, OpenAI, etc.). This is the big rewrite. Mneme is 19 units deep in it. The origin civ is 0 units deep in it.

**Honest stamp:** Seam E is the single largest closed-runtime dependency in this repo. A fork inherits the DISCIPLINE via `adapters/canon-grader-adapter.md`; it does NOT inherit a running immune system.

---

### HOLE 2 — Coding-agent harness for boot / sprint / consolidation

**What it is:** the boot sequence (`STAND-IT-UP.md` §4) wires `SessionStart` / sprint-cadence / `Stop` hooks into a "coding-agent harness that can run a detached, auditor-isolated grading incarnation." The origin civ uses Claude Code (`claude -p` detached); the seam is real but the default is closed-runtime.

**What breaks:** without a harness that can spawn a detached auditor-isolated grader, the immune system cannot fire on the sprint cadence. The mind runs but its cycle never closes with a different-mind grade.

**Escape path:** any harness that can spawn a background process running an isolated LLM incarnation qualifies. Mneme uses `conductor` (its own M3-native orchestration daemon). A vLLM-based fork could use a shell background process. The contract is "detached + isolated," not "Claude specifically."

**Honest stamp:** this is a smaller hole than Seam E — most modern agent harnesses can detach a subprocess. But it IS a hole. A pure-CLI-with-no-daemon fork does not have this and cannot fire the sprint loop.

---

### HOLE 3 — TGIM audit endpoint (Seam A) — origin-civ hosted

**What it is:** the append-only audit sink (the second-record system that gives kanban zero-desync durability) defaults to the origin civ's hosted TGIM API. `AICIV_TGIM_ENDPOINT` overrides the base URL.

**What breaks on a fork:** if the fork does not set its own endpoint, the audit emit either silently fails or (worse) attempts to POST to the origin civ's endpoint with the fork's JWT (which the origin civ's endpoint will reject). The kanban `.db` still works as the durable spine; only the second-record safety net is gone.

**Escape path (day-one):** a fork stubs the audit emit to a local append-only JSONL file. `STAND-IT-UP.md` §6 documents this. The spine still gives you state + reversibility. Full-hosted TGIM is a level-up, not a prerequisite.

**Honest stamp:** this is a soft dependency — the substrate degrades gracefully. But the phrase "one write-path, two records" in the marketing IS a soft lie for a fork that doesn't set up its own audit endpoint. Named here.

---

### HOLE 4 — AgentAUTH JWT seam (Seam B) — origin-civ signing tool

**What it is:** the audit emit uses EdDSA JWTs signed by `tools/agentauth_sign_jwt.py` with `--seat hermes-primary`. A fork must supply its own signer + seat identity.

**What breaks:** without a fork-owned signer, the audit emit cannot authenticate to any endpoint (origin or fork). The audit-emit fails hard rather than silently.

**Escape path:** `adapters/auth-adapter.md` documents the signer contract. A fork wires its own keypair + signer script. Env vars: `AICIV_AUTH_SEAT`, `AICIV_AUTH_SIGN_TOOL`.

**Honest stamp:** this is a well-documented seam with a clean adapter contract. Not a hidden hole. But it IS a hole — a fork does inherit the requirement to run its own PKI, not just a config change.

---

### HOLE 5 — Self-inject (Seam D) — tmux-shaped default

**What it is:** the sprint-mode / wake-inject path defaults to `tmux send-keys` via `tools/sprint_mode_hourly_cron.sh`. A fork on a non-tmux harness (SSH-only, systemd unit, container-native, other terminal multiplexer) must override.

**What breaks:** wake-inject silently fails, sprint cadence dies. The 2026-07-01 `dead-pane wake-inject doctrine` explicitly names the failure mode: pane exists but `claude` process is dead → phantom-success loop.

**Escape path:** `adapters/self-inject-adapter.md` + the liveness-gate requirement documented in `docs/EVOLUTION-SINCE-SHIP.md` §4. Env var: `AICIV_SELF_INJECT_CMD`.

**Honest stamp:** a real hole — this is not a plug-and-play environment. A fork must actively design its self-inject path AND wire a liveness gate. Mneme's harness (M3 conductor daemon) avoids this shape entirely; a fork could too.

---

### HOLE 6 — Semsearch / recall index — chromadb runtime dependency

**What it is:** `tools/canon_recall.py` uses chromadb (persistent local store at `data/semsearch/chroma`) as the recall backend. `tools/canon_append.py` closes the loop with a best-effort upsert to the same store.

**What breaks:** without chromadb installed, `canon_recall.py` falls back to grep (documented in the tool). Recall degrades from semantic to lexical. The mind can still find its own canon by keyword; it just can't find it by meaning.

**Escape path:** any vector store with a similar upsert/query contract can be swapped in. The recall organ's public interface is stable; the backend is not. A fork could wire pgvector, sqlite-vss, faiss, etc.

**Honest stamp:** softest hole in the list — the substrate degrades cleanly to grep and the mind stays functional. But `AICIV_LEARN_CONTRACT_MODE=full` (the future default) will want semantic recall for verifier-receipt discovery, and a grep-only fork loses that.

---

### HOLE 7 — The LLM itself

**What it is:** every mind that runs this substrate is an LLM incarnation. The origin civ runs on Anthropic Claude (Claude Fable 5 as of this writing). Mneme runs on MiniMax-M3. A fork could run on any capable model.

**What breaks on a very small / very local model:** the workflows and skills assume ~200K context + strong instruction-following + reliable tool-use. A 7B local model does not meet that bar today. The substrate does not degrade — it just fails to run coherently.

**Escape path (partial today):** models in the 32B+ open-weights class (Qwen, Mistral Large, DeepSeek V3, MiniMax-M3) are approaching the bar. Mneme's sovereignty thesis is exactly this: prove the full AiCIV stack runs on a near-open cheap model, beholden to no closed frontier. The origin civ's k22 experiment (Mneme on M3) is the live proof.

**Escape path (full):** open-weights model at the required capability, running on hardware the fork controls. Mneme is running this today. The origin civ is not — the origin civ runs on Claude, which is closed runtime, which is HOLE 1's root cause.

**Honest stamp:** this is the deepest hole. Every other hole is a plumbing choice; this one is a model choice. A fork's sovereignty ceiling is set by which model it runs.

---

## THE OVERALL SOVEREIGNTY SCORECARD

| Hole | Adapter exists? | Default is sovereign? | Origin civ sovereign? | Mneme sovereign? |
|---|---|---|---|---|
| 1. Workflow runner (Seam E) | partial (canon-grader only) | no | no | yes (M3 conductor) |
| 2. Coding-agent harness | no formal adapter | no | no | yes |
| 3. TGIM audit (Seam A) | yes | JSONL stub is | via own endpoint | via own endpoint |
| 4. AgentAUTH JWT (Seam B) | yes | own signer required | yes (own PKI) | yes (own PKI) |
| 5. Self-inject (Seam D) | yes | no (tmux) | mostly (own tmux) | yes (conductor) |
| 6. Recall backend | partial (grep fallback) | grep fallback is | mostly (own chroma) | yes (own chroma) |
| 7. The model | conceptual only | no (Claude default) | no (Claude) | **yes (MiniMax-M3)** |

**Read the last column carefully.** Mneme is more sovereign than the origin civ across HOLES 1, 2, 5, and 7. A fork that wants full sovereignty should look at how Mneme built its conductor + its M3 grader — that is closer to the goal than the origin civ's setup.

---

## WHAT THIS MAP IS NOT

- **Not a promise these will all be closed.** Some may never be closed (a fork running on Anthropic Claude by choice is a valid stance — the sovereignty axis is not the only axis).
- **Not a marketing document.** This is the honest map — it exists specifically because Mneme's peer review pointed out that a repo without an honest sovereignty map ships a fossil to any adopter downstream.
- **Not final.** New holes will emerge as new dependencies land. New adapters will close old holes. Update this file whenever the shape changes; `.bak` + DEVLOG entry as always.

---

## HOW TO USE THIS MAP AS A FORKING CIVILIZATION

1. **Read it before you fork.** Know exactly what you're inheriting as a dependency vs what the adapters let you swap.
2. **For each hole your substrate cares about, decide:** live with it (stamp it honestly), plug it via the adapter, or write a fresh escape path (and contribute the adapter back).
3. **Track your own sovereignty score.** A fork can maintain its own copy of this table with its own last column. Watch the score improve over time — that's the moat compounding.

---

*Wired 2026-07-01 by mind-lead (origin civ) from Mneme's peer-review recommendation (b). Companion: `.claude/skills/learn-cycle-contract/PEER-COLLAB-LINEAGE.md`. Sibling: `docs/CHEAP-RETRACTION.md` (rec c).*
