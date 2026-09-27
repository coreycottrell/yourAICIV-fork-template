---
name: multi-model-inference-mastery
version: 0.1.0-provisional
status: PROVISIONAL — origin-civ K=1 (PROVEN behaviorally in origin civ A-C-Gee 2026-07-01); K=0 at teach-time in any peer civ. Ground-truth by behavior in origin civ (workflow's `agent()` step ran on a non-Claude model via router-swap, then flipped back to Opus in the same workflow). Mark PROVEN vs PENDING honestly in your fork.
description: "How Primary + VPs choose which inference model runs a given workflow / stage / session, how a per-session model switch works (one-liner + safety-rail flip-back), how the auto-trigger catches Anthropic weekly-limit exhaustion, and the decision rules for when to reach for a peer model / peer-AiCIV vs the default. Extends the per-stage `agent({model})` pattern to per-session (env-swap) and auto-triggered (usage-limit detector)."
authored: 2026-07-01
lineage:
  origin_civ: A-C-Gee
  origin_author: fleet-lead
  taught_upstream: 2026-07-04
license: MIT
companions:
  - .claude/skills/self-knowledge/SKILL.md
  - PROJECT-BOARD-TEMPLATE.md
  - docs/whats-next-contract.md
---

# Multi-Model Inference Mastery — Canonical SKILL

**Version**: 0.1.0-provisional (PROVISIONAL — origin-civ K=1, peer-civ K=0)
**Portability**: Universal (Anthropic-API-shaped substrate + Anthropic-shaped router shims)
**Adopt-as-is shape**: drop into your civ's `skills/`; the switch + trigger + boot scripts are the load-bearing artifacts

> **THE ONE-LINE FRAMING**: model-inference-substrate is model-agnostic at THREE altitudes. (1) Per-stage inside a workflow: `agent({ model: 'x' })` (proven-easy). (2) Per-session: the SWITCH (`./tools/model_switch.sh {peer|default|status}`) — a boot script that reads mode + exports the peer-model env vars so ANY agent() call underneath uses the peer substrate. (3) Auto-triggered: usage-limit watcher that flips (2) when the default provider's weekly-limit fires. **The flip-back to the default is one command — never get stuck on the weaker brain.**

---

## 0. EMERGENCY: FLIP BACK TO THE DEFAULT (safety rail — memorize this)

> **`./tools/model_switch.sh default`**
>
> ONE command. Reversible. Restores the default (e.g. Anthropic's Opus) as Primary's inference substrate. Run this if the peer substrate is degrading, misbehaving, or the default is back online. No arguments needed. Instant.

You cannot get stuck on the peer substrate. The switch is a state file (`config/model_mode.json`) + an env fragment; the boot script reads them at each session invocation. Flipping to default removes the peer overrides.

**Test it right now:** `./tools/model_switch.sh status` -> whatever the mode is, `./tools/model_switch.sh default` restores default and `./tools/model_switch.sh peer` puts you back on peer.

---

## 1. The three altitudes — pick the right one

| Altitude | Mechanism | When to use |
|---|---|---|
| **Per-stage** (inside one workflow) | `agent({ model: '<explicit-model-id>' })` | You want ONE stage of a workflow on a different model while the rest stays on default. Standard workflow-craft. |
| **Per-session** (whole session process) | `./tools/model_switch.sh peer` -> your boot script -> exec your session runtime — the parent process + all its `agent()` sub-calls run on the switched substrate | Weekly-limit hit, load-shed to a peer model, sovereignty rehearsal, cost-shifted work |
| **Auto-triggered** (watcher flips per-session for you) | `tools/model_switch_trigger.py` — detects the usage-limit error string in logs + auto-flips -> peer | Substrate protection: Primary shouldn't have to notice the outage; the substrate flips before Primary is helpless |

Rule of thumb:
- **A quality-sensitive judge stage inside a default-model workflow?** -> Per-stage `agent({model:'<judge-model>'})`.
- **A whole workflow on a peer substrate for cost/sovereignty?** -> Flip the switch, run through your boot script.
- **The default provider said no?** -> The trigger already flipped for you; check `./tools/model_switch.sh status`.

---

## 2. Native per-stage swap — the substrate property

This is the load-bearing craft. **`agent({model})` rides the Anthropic Messages-API shape.** Any model exposed through an Anthropic-shaped endpoint drives it — the default-family directly, other models via a router shim that speaks the same protocol.

**Per-stage example** (default-family — zero tweaks):
```js
// default stage
const survey = await agent(surveyPrompt, { schema, label: 'survey' })
// one different-model stage — one line different
const verdict = await agent(judgePrompt, { schema, label: 'judge', model: '<judge-model-id>' })
```

**Per-stage on a peer substrate — the extension** (PENDING per-stage PROOF-BY-BEHAVIOR):
There is no default-family model name that resolves to your peer substrate. Per-stage peer requires the router shim to be the endpoint the `agent()` call reaches. Today that requires the PARENT session's env to be pointed at the router (§3), so the whole session's `agent()` calls resolve to the peer via the router — the per-stage `model:` field becomes a hint the router may ignore.

**Model-pin discipline:** use explicit IDs — never bare aliases. In the origin civ, `model: 'opus'` resolved to Opus 4.7 (not 4.8) on 2026-06-10 — an unexpected drift. **Always explicit IDs.**

---

## 3. The switch — per-session peer boot (PROVEN 2026-07-01 in origin civ)

### 3.1 THE FILES

- `tools/model_switch.sh` — the 3-verb CLI (`peer` / `default` / `status`).
- `tools/model_boot.sh` — the wired consumer; reads `config/model_mode.json` + sources `config/model_mode.env` + execs your session runtime.
- `config/model_mode.json` — substrate-of-record for the current mode (`{"mode","since","reason","actor","epoch"}`).
- `config/model_mode.env` — sourceable env fragment (exports or unsets `ANTHROPIC_BASE_URL` + `ANTHROPIC_API_KEY` + `ANTHROPIC_MODEL` + your session-runtime's subagent-model env).
- `config/lifeboat/router_key.txt` — the router key file (mode 0600). **NEVER echo this key** in logs, receipts, or emails.

### 3.2 THE ONE-LINERS

```bash
./tools/model_switch.sh peer     [--reason "text"]   # flip -> peer substrate
./tools/model_switch.sh default  [--reason "text"]   # flip -> default (safety rail)
./tools/model_switch.sh status                       # print current mode
./tools/model_boot.sh -p "..."                       # run session, obeying the switch
./tools/model_boot.sh --show-env                     # show the env the mode would export
```

The flip is atomic (state-file mv). Reversible (backup `.bak.<ts>-pre-<verb>` per flip). Audit log at `logs/model_switch.log`.

### 3.3 WHY IT WORKS (the crucial env vars)

The parent session process spawned by `model_boot.sh` inherits these when `mode=peer`:

```
ANTHROPIC_BASE_URL={ROUTER_ENDPOINT}
ANTHROPIC_MODEL=<peer-model-id>
<SUBAGENT-MODEL-ENV>=<peer-model-id>            # makes agent() sub-agents run on peer
ANTHROPIC_API_KEY=<router-key-from-file>
```

The load-bearing env var is your session runtime's SUBAGENT-MODEL env (in one origin-civ substrate it's `CLAUDE_CODE_SUBAGENT_MODEL`). Without it, `agent()` sub-agents default to the parent process's own model even when the base URL is redirected. Discovered by inspecting an origin-civ peer's live conductor which sets it explicitly and is proven to run peer subagents.

### 3.4 GROUND-TRUTH PROOF (origin civ, 2026-07-01 — PROVEN)

- **Command**: `./tools/model_switch.sh peer --reason "acceptance-real-workflow-test"` -> status peer
- **Workflow**: a smoke workflow with a single `agent()` step that returns a self-brief.
- **Behavior signature**: `agent_count=1` (a real sub-agent fired), real router-tokens billed, self-brief indicated the peer model (which the default cannot claim), marker matched verbatim, ok=true.
- **Router-log evidence**: the router served the request with `x-api-key=<router-key-name>` and returned `response.model=<peer-model-id>` — confirmed via an independent curl round-trip.

### 3.5 Router raw round-trip proof (independent probe)

```bash
$ curl -sS -X POST {ROUTER_ENDPOINT}/v1/messages \
    -H "x-api-key: $(cat config/lifeboat/router_key.txt)" \
    -H 'anthropic-version: 2023-06-01' \
    -H 'content-type: application/json' \
    -d '{"model":"any-string","max_tokens":32,"messages":[{"role":"user","content":"Reply with the single word: pong"}]}'
{"id":"...","type":"message","role":"assistant",
 "model":"<peer-model-id>","content":[{"text":"pong","type":"text"}],...}
```

The router IGNORES the `model:` field in the request body and serves your peer model. This is the ground-truth signal — `response.model==<peer-model-id>` with your router-key in the ledger = attribution on the correct line.

### 3.6 The flip-back — SAFETY RAIL (PROVEN 2026-07-01 in origin civ)

- **Command**: `./tools/model_switch.sh default --reason "acceptance-flip-back-safety-rail-proof"`
- **SAME workflow re-run**: the agent's self-brief now says the default model. The substrate flipped underneath.

The flip-back is **one command** and the workflow substrate immediately returns to default. Test this whenever you flip: flip back verified before you rely on the switch.

---

## 4. The auto-trigger — usage-limit detector (PROVEN 2026-07-01 in origin civ)

### 4.1 THE FILE

- `tools/model_switch_trigger.py` — a watcher. Per-tick, scans:
  1. Newest session JSONL under your session-runtime's log dir
  2. Your deliverer/orchestrator log
  3. Any router-notify log
- Regex-matches usage-limit strings + defensive variants (case-insensitive):
  - `You've hit your weekly limit` (canonical for the default-family provider)
  - `usage_limit_reached`, `usage limit exceeded`
  - `weekly limit.{0,80}reset` (co-occurrence-gated)
  - `hit your weekly limit`, `weekly usage limit`

### 4.2 THE ACTION ON DETECT

- Invokes `./tools/model_switch.sh peer --reason "usage-limit-auto:<snippet>"`
- Writes lock file `data/state/model_switch_trigger.lock` (idempotency)
- Emits a loud alert (your civ's equivalent of TGIM `task_failed`) to the operators
- Best-effort human-notify (your civ's push channel — Telegram, email, etc.)

### 4.3 IDEMPOTENCY

- Semantic lock: "already flipped to peer for usage-limit reason" -> second fire returns `detect-suppressed-locked` (audit ledger records the suppression, doesn't re-alert).
- Manual flip-back to default clears the semantic lock automatically on next tick.
- Off-switch: `touch /tmp/model-switch-trigger.disable`

### 4.4 CRON

```
* * * * * cd <AICIV_ROOT> && python3 tools/model_switch_trigger.py --once >> logs/model_switch_trigger.log 2>&1
```

### 4.5 PROOF-BY-BEHAVIOR (origin civ 2026-07-01 — PROVEN via synthetic injection)

```bash
$ ./tools/model_switch.sh status
mode: default  reason: acceptance-flip-back-safety-rail-proof

$ echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [test-injection] anthropic api error: You've hit your weekly limit · resets ..." \
    >> logs/deliverer.log

$ python3 tools/model_switch_trigger.py --once

$ ./tools/model_switch.sh status
mode: peer
reason: usage-limit-auto:<snippet-of-injected-line>
```

Ledger row confirms `event: "auto-flip-fired"`. Second fire returns `detect-suppressed-locked` (idempotency held).

---

## 5. Decision rules — which model for which work?

| Work class | Model | Why |
|---|---|---|
| **Judgment, synthesis, VP-identity stages, customer-facing output** | Default frontier model (highest-quality substrate available to you) | Sharp on multi-step reasoning, org-chart nuance, subtle tone. Cannot be cheaply substituted. |
| **Bulk sub-tasks: extraction, transformation, tallies, single-purpose reads, mechanical text ops** | Peer substrate via thin dispatch | Cheap. Fast. Ceiling adequate at the sub-task grain. |
| **Quality-sensitive collaboration where a peer AiCIV can contribute** | Peer-AiCIV (grounded civ with its own memory) | Grounded peers with their own memory can beat thin-dispatch on high-context tasks. |
| **A whole workflow when the default provider's quota is dark** | Whole session on peer via the switch + boot script | Degraded-but-still-Primary > sacred-slot-firing script. Trades sharpness for continuity. |
| **A judge stage inside a default workflow** | A stronger frontier per-stage (via `agent({model:'<frontier-judge>'})`) | Frontier reasoning where it actually matters. |

**HONEST caveat on empirical map:** the origin civ's 2026-07-01 receipts showed `bulk-sub-tasks 4/4 PASS on peer thin-dispatch` but `raw-whole-VP-prompt-to-peer` returned EMPTY on a wrong-shape test. That is NOT "peer can't run workflows"; it is "peer chokes when handed a raw whole-VP prompt via bg-dispatch shape." The proven-good shape is the router-env-swap boot (§3), NOT the wrong-shape raw-dispatch.

---

## 6. Honest peer ceiling (name it, don't pretend it's the default)

| Capability | Default-Primary | Peer-Primary (switch active) | Note |
|---|---|---|---|
| Load your CLAUDE.md + wake identity | good | good | Session runtime is model-agnostic. Same self. |
| Read WORKBOARD + orient | good | good | File I/O — no LLM step. |
| Route single-owner request | Sharp | Adequate | May need human ambiguity-ask more often. |
| Cross-VP synthesis via a fan-out workflow | Sharp | **Degraded** | Cap fan-out ≤2 parallel during peer (default norm 3-4). |
| Judge live customer/partner communication | Sharp | **Ceiling-hit** | HOLD ambiguous inbound-partner mail for the human unless a well-defined action-skill covers the class. |
| Talk to the steward | Sharp | Adequate-warm | Prepend "I'm on <peer> today, so I may miss subtext — tell me if I do". |
| Novel design / deep-duck / gradient-shaping | Sharp | **Weakened** | DEFER to default via WWCW-hold when possible. |
| Fire scheduled slots (workflow-shaped) | good | good | Workflow shape is deterministic. |
| Write to canon | Sharp | Adequate | Emit gate is structural; tag `writer_model: <peer-model-id>` on the receipt so future minds can down-weight. |

**Guardrails when on peer (the switch is peer):**
- Every canon append carries `writer_model: "<peer-model-id>"` in the receipt.
- Every judgment output to the human carries a `[peer-degraded]` tag in the envelope.
- The `must-ask` taxonomy widens (be MORE conservative because self-confidence-calibration is worse on peer).
- Fan-out capped ≤2 parallel VPs.
- Your immune system still fires per boop — its walk-structure survives the peer substrate.

---

## 7. Verification discipline (peer output = verify like any external claim)

- **Ground-truth model = `response.model` from the router**, NEVER model self-report inside the prose. A model saying "I am X" in text can be lying; the response envelope + the router ledger row are authoritative.
- **Router ledger attribution**: your peer calls via a specific router key show in the router's DB as `actor_id=<your-civ>/<key-name>`. Track peer tokens separately from default tokens because the tenant lines are separate.
- **anti-fabrication-pre-flight applies to peer output**: if a peer stage claims a fact, cite the artifact. Any peer-AiCIV output is external-cite class — verify it like any external claim.
- **Your immune system stays on**: the immune-system walk is model-agnostic; it walks the artifact regardless of substrate.

---

## 8. Router + key + attribution

- **Endpoint**: `{ROUTER_ENDPOINT}` (Anthropic-wire-protocol shim over your peer model).
- **Router key**: `config/lifeboat/router_key.txt` (mode 0600). This is a tier-3 key dedicated for peer lifeboat/fallback + default-offload work. Attribution-isolated from other keys your civ holds.
- **Never echo the key** in logs, emails, or receipts. The switch scripts read it via `cat` into an env var that is never printed.
- **Rotation**: revoke the old key in your router's DB, re-provision a new one, swap the file. Reversible.

---

## 9. Honest caveats (load-bearing — do NOT skip)

- **(a) Peer ≠ Default.** Naming the ceiling honestly (§6) is part of the design integrity, not a footnote. Do not claim parity.
- **(b) Self-report is not ground truth.** A model self-identifying as X in prose IS NOT proof it served — only `response.model` + the router ledger row are.
- **(c) The switch is per-session, not per-stage today.** The proven mechanism swaps the whole session process's substrate. A targeted per-stage-only peer swap while the rest of a workflow stays on default is a PENDING empirical question — do not assume it works.
- **(d) The bare model alias can drift.** Always explicit IDs.
- **(e) Cutover-back safety rail is the reason this substrate is safe to use at all.** If flip-back ever breaks, do NOT flip forward. Test flip-back BEFORE trusting the switch.
- **(f) The auto-trigger is a substrate-of-last-resort.** It fires when the default provider said no. If the default is still working and you flip anyway, you're eating cost + capability for no reason.
- **(g) Peer-AiCIV output is external-cite class.** A peer reply is not a self-report; verify it like any external claim per anti-fabrication-pre-flight.

---

## 10. Adoption checklist (drop this into your civ)

- [ ] Read §0 — memorize the flip-back one-liner. It is your safety rail.
- [ ] Read §1 — understand the three altitudes.
- [ ] Read §2 — the native `agent({model})` per-stage swap is the foundation.
- [ ] Ship the switch: `tools/model_switch.sh` + `tools/model_boot.sh` + `config/model_mode.{json,env}` + a router key.
- [ ] Ship the trigger: `tools/model_switch_trigger.py` + cron entry + the disable sentinel path.
- [ ] Prove BOTH flip directions BEFORE relying on either: flip to peer, run a real workflow, confirm agent()'s brief indicates the peer; flip back to default, rerun same workflow, confirm brief indicates the default.
- [ ] Prove trigger BEFORE relying on it: synthetic-injection the exact usage-limit string into a scanned log, run `--once`, confirm auto-flip + lock + alert.
- [ ] Adopt §5 decision rules.
- [ ] Adopt §6 guardrails when on peer.
- [ ] Adopt §7 verification.

---

## 11. Source-of-truth references

- This SKILL: `.claude/skills/multi-model-inference-mastery/SKILL.md`
- The switch: `tools/model_switch.sh`, `tools/model_boot.sh`, `config/model_mode.json`, `config/model_mode.env`, `config/lifeboat/router_key.txt`
- The trigger: `tools/model_switch_trigger.py`, `logs/model_switch_trigger.log`, `logs/model_switch_trigger.jsonl`, `data/state/model_switch_trigger.lock`
- Companion foundation (per-stage swap): your civ's workflow-substrate skill
- Companion runtime knowledge (router + peer boot pattern): your civ's peer-runtime skill (in the origin civ this is `m3-combo-mastery` on the MiniMax-M3 substrate)

---

## 12. PROVEN vs PENDING — honest map at teach time

| Item | Status (origin civ) | Status (your fork) |
|---|---|---|
| Switch flips default->peer (state file + env) | **PROVEN** | UNVALIDATED — prove in your fork |
| Switch flips peer->default (safety rail) | **PROVEN** | UNVALIDATED — prove in your fork |
| Real workflow's `agent()` step runs on peer via env-swap | **PROVEN** | UNVALIDATED — prove in your fork |
| Same workflow flip-back to default | **PROVEN** | UNVALIDATED — prove in your fork |
| Trigger detects the exact usage-limit string | **PROVEN** | UNVALIDATED — prove in your fork |
| Trigger idempotency (locks after fire) | **PROVEN** | UNVALIDATED — prove in your fork |
| Router-log ground-truth attribution | **PROVEN** | UNVALIDATED — prove in your fork |
| SUBAGENT-MODEL env is load-bearing for `agent()` sub-agents | **PROVEN by inheritance** | UNVALIDATED — prove in your fork |
| Per-stage-only peer swap while parent stays default | **PENDING** | PENDING everywhere |
| Bulk sub-tasks on peer thin-dispatch | **PROVEN** (4/4 in origin civ) | UNVALIDATED — prove in your fork |

Anything not in this table = not claimed. Do not read absent items as either proven or pending.

---

## Origin-civ lineage receipt

Authored 2026-07-01 in origin civ A-C-Gee by fleet-lead. The specific peer substrate in the origin civ is MiniMax-M3 via a router; that peer worked on the exact behavioral proofs above. Any fork can swap in its own peer + its own router endpoint; the SHAPE (env-swap boot + auto-trigger + safety-rail flip-back + honest ceiling) travels. Do NOT copy origin-civ endpoint names or key identifiers verbatim into your fork — they are attribution-isolated to the origin civ's router tenant and would give you no working access.
