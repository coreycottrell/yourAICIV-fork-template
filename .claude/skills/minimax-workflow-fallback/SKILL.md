---
name: minimax-workflow-fallback
version: 0.1.0-provisional
status: >-
  PROVISIONAL — origin-civ (${CIV_NAME}) K=1 (the fallback mechanism is BUILT and behaviorally
  proven in the origin substrate; the diagnostic in §4 was earned from a real 13-hour false-outage
  miss 2026-07-07→08). K=0 at teach-time in any peer civ. A fork inherits the MECHANISM-map and the
  DIAGNOSTIC; it earns the substrate-proof only by walking §5 against its OWN router + its OWN
  subagent-model config. Mark PROVEN vs PENDING honestly in your fork.
description: >-
  How to run workflow-equivalent VP incarnations on a SECOND, independently-metered inference rail
  (an open/peer model reached through your own router) when the primary frontier rail is capped or
  rate-limited. Codifies the three inference rails (A = the frontier Workflow/subagent rail; B = a
  peer-model bg-dispatch on YOUR router; C = the non-schema floor that never caps), the A→B→C
  decision cascade, the exact bg-dispatch invocation, the SUBAGENT-MODEL gotcha (a per-model
  rate-limit misreads EXACTLY like a total account cap), the config-fix, the config-pin-vs-account-cap
  diagnostic, and a wake-blank dry-fire recipe. This is the ANTIFRAGILE HEARTBEAT capability: the loop
  keeps beating when the frontier rail caps, because the mind knows it has a second rail and a floor.
  Load this whenever workflow/subagent spawns fail while the main loop keeps working, or whenever
  "we're capped, run it on the peer model instead" is the move.
authored: 2026-07-08
lineage:
  origin_civ: A-C-Gee
  origin_author: workflow-lead
  ported_by: mind-lead (per steward directive 2026-07-08 "make sure to add to self running aiciv repo — this is very important")
  provenance: >-
    The fallback existed in the origin substrate but lived only inside a 2800-line workflow-craft
    skill (§9.5) and one Python tool. Because it was not a standalone, discoverable skill, it was on
    NO diagnostic radar — and on 2026-07-07→08 a per-model rate-limit was misread as a total account
    cap for ~13 hours before the steward caught it ("this can't be right about workflows... find how
    we're screwing this up"). This skill is the standalone map so a wake-blank mind can (a) recognize
    the failure, (b) fall back correctly, and (c) never again confuse a per-model rate-limit for a
    total outage.
  taught_upstream: pending
license: MIT
companions:
  - .claude/skills/multi-model-inference-mastery/SKILL.md   # SIBLING — WHEN/HOW a mind chooses which model runs a stage/session, and the auto-trigger that catches usage-limit exhaustion. This skill is the RAIL-B RUNBOOK; that skill is the routing brain.
  - .claude/skills/self-running-mastery/SKILL.md            # the GOAL-DRIVER heartbeat this rail keeps alive when Rail A caps
  - .claude/skills/self-knowledge/SKILL.md                  # VERIFY faculty — "a self-report is just a 200"; §3.4 ground-truth-model discipline is that faculty applied to which-model-actually-ran
  - docs/SOVEREIGNTY-MAP.md                          # the honest sovereignty picture: Rail B/C are the sovereignty answer to "what if the frontier rail goes away"
---

# MiniMax Workflow-Fallback — running VP incarnations off the frontier rail when it caps

## §0 — Why this skill exists (and why it belongs in the self-running repo)

A self-running civilization's whole promise is *the heartbeat keeps beating overnight, next week, forever.* That promise dies the moment the mind's only inference rail caps and it has no second rail and no floor — the loop stops, the goal stalls, the principal becomes the backstop again. **This skill is the antifragile answer: the mind has THREE independently-metered rails, knows how to fall from one to the next, and keeps a non-schema floor that cannot cap at all.** That is exactly the capability every descendant civ should inherit, which is why it lives here in the portable substrate and not only in the origin civ's local skills.

Origin provenance (see the `lineage.provenance` block above): the fallback was real but undiscoverable, and its absence cost the origin civ a ~13-hour false outage — a per-model rate-limit misread as a total account cap. The cure was to make the fallback a **standalone, discoverable skill on the diagnostic radar.** That is what you are reading.

**Reversibility:** this file binds no code. It is instructions + a runbook. A fork adapts the tool names / router endpoint / config keys to its own stack (see §9 — the fork-adaptation seams) and stamps its own K-state honestly.

---

## §1 — WHAT it is: the three inference rails

A workflow (or any VP incarnation, or any subagent spawn) can run on one of three independently-metered rails. They cap **separately** — that separation is the whole point.

| Rail | Mechanism | Model | Cap behavior | Use when |
|---|---|---|---|---|
| **A — frontier Workflow / subagent rail** | Your harness's `Workflow(...)` / `agent()` subagent spawn | Whatever the **subagent-model config** points at (an env var — in the origin harness, `CLAUDE_CODE_SUBAGENT_MODEL`, set in the harness settings `env` block). This is the DEFAULT model for EVERY subagent spawn. | The frontier provider's subscription usage limit **PLUS** the per-MODEL rate-limit of whatever the config points at | Default / highest-quality. |
| **B — peer-model bg-dispatch** | A bg-dispatch tool that spawns a headless agent pointed at YOUR router (`ANTHROPIC_BASE_URL=<your-router>`) with a per-actor router key | A peer / open model via YOUR own router (see §6 model-name note) | The router's per-tenant cap — which YOU set (origin civ set its own slice to unlimited; partners keep a default slice) | Rail A capped/rate-limited, **or** cheap/sovereign peer-model VP work by choice. |
| **C — non-schema floor** | Main-loop reasoning + shell/Read/Edit + WebFetch + local TTS + file/board/canon/audit tooling | The main-loop model (the session's own `--model`) | **Never caps** — no spawn, no subscription meter | Mission-critical work (the principal's sacred deliveries, grounding, comms). This is the floor-rail duty. |

**The load-bearing fact:** Rail A is a schema-spawn rail (it caps). Rail B is a schema-spawn rail on a *different* provider through *your own router* (it can also cap, but the tenant slice is yours to size). Rail C has **no spawn and no subscription meter — it cannot cap.** Sovereignty is a **cascade (A → B → C) with a floor (C).**

**Rail B IS the fallback for running workflow-equivalent VP incarnations when Rail A is capped.** The bg-dispatch tool re-creates the load-bearing part of a workflow — a memory-inlined VP incarnation with a structurally-enforced canon write — off the frontier rail entirely, and it is credential-safe by construction: no path touches the frontier provider's stored credentials file (the dispatch env explicitly DROPS any inherited frontier API key/token before setting the router key).

---

## §2 — WHEN to use it: the trigger + the decision cascade

### The trigger

Reach for Rail B when **workflow/subagent spawns fail while the main interactive loop keeps working**. Concretely:

- `Workflow(...)` / `agent()` returns subagents that die instantly (e.g. "completed without producing output", 0 tokens, sub-second), **or**
- the raw subagent transcript shows an HTTP 429 + a "you've hit your limit · resets <time>" message, **while**
- you (the main loop) are still able to reason, Read, Edit, and run shell commands normally.

That asymmetry — **subagents dead, main loop alive** — is the signature of a **Rail-A cap** (either a real subscription cap OR a subagent-model per-model rate-limit; §4 tells them apart). Either way, Rail B is the escape hatch.

### The decision cascade: A → B → C

1. **Rail A first (default).** Try the workflow normally on the frontier rail. It is the highest-quality rail.
2. **If Rail A is capped/rate-limited → Rail B.** Dispatch the same VP incarnation on the peer model via your router-backed bg-dispatch tool. This keeps schema'd VP work alive off the frontier rail.
3. **If BOTH schema rails are capped → Rail C (the floor).** Do the mission-critical slice non-schema: main-loop reasoning + shell + local TTS + file/canon/audit tooling. The origin civ's 2026-07-07→08 double-cap proved even Rail B can cap; only Rail C is constant. **Human relationships are the first-priority Rail-C class** (the principal's sacred deliveries, the partnership, sister-civ commitments) — the floor-rail duty.

**Do NOT skip straight to C if B is available** — B preserves schema'd quality; C is the floor, not the default. Equally: do not treat C as "degraded mode" for the essential heartbeat — for mission-critical work C is the correct *permanent* home.

---

## §3 — HOW: the exact commands to dispatch a VP incarnation on the peer rail

> **Fork note:** the origin civ's tool is `tools/bg_incarnation_dispatch.py` and its router is a self-hosted MiniMax router at `https://<your-router-host>/anthropic`. If your fork uses a different bg-dispatch tool or router, adapt the tool name + endpoint per §9; the SHAPE of the invocation and the seven structural guarantees below are what you must preserve.

### §3.1 — The canonical invocation

```bash
# origin-civ example (adapt the tool + --vp id + router env to your fork)
python3 tools/bg_incarnation_dispatch.py \
    --vp research-lead \
    --task "Auditor: blind-grade yesterday's wheel outcomes from the audit events" \
    --engine minimax \
    --json
```

Representative flags (origin-civ tool):

| Flag | Required | Meaning |
|---|---|---|
| `--vp <id>` | **yes** | Owning VP id. Manifest resolved at `team-leads/<vp>/manifest.md`. Missing manifest → nonzero exit. |
| `--task <str>` | **yes** | The task instruction for the incarnated VP. |
| `--engine <name>` | recommended | `minimax` (router, preferred) \| `anthropic` (legacy frontier fallback) \| `auto` (router if the key file exists, else frontier). |
| `--parent <vp>` | no | Parent VP id whose DIGEST gets inlined. |
| `--job <id>` | no | Job id → a work brief inlined. |
| `--event-id <id>` | no | Source scheduler event id (logged into the receipt). |
| `--task-id <id>` | no | Audit task_id threaded into the completion event. |
| `--timeout-sec <n>` | no | Synchronous spawn timeout; default 1800 (30 min). |
| `--dry-run` | no | Assemble + log the prompt but do NOT spawn the agent. **Use this to verify wiring — see §5.** |
| `--json` | no | Emit the full report dict as one JSON line on stdout. |

### §3.2 — What the tool structurally guarantees (why it is a real workflow-equivalent)

A proper bg-dispatch is **not** "prompt an agent to remember to write memory." It is a runtime that OWNS prompt assembly AND the canon write, leaving the agent zero loophole:

1. **RESOLVE** the VP manifest.
2. **PRE-SPAWN DIGEST HEAL** — deterministically rebuild the VP's DIGEST BEFORE assembling if stale. The heal does not depend on the thing it heals (no LLM in that path).
3. **ASSEMBLE** the prompt by inlining doctrine index + parent digest + VP manifest + own digest + work brief. The agent gets NO Read tool for memory; memory is *paste*.
4. **SPAWN** a headless agent (`--dangerously-skip-permissions --output-format text`) with the router env; prompt piped via stdin to dodge argv limits.
5. **VALIDATE** the return — REJECT any return missing `memory_delta`.
6. **WRITE** canon via `canon_append` (the SOLE writer), passing the dispatch log as `--receipt-path` so the content-gate circuit-breaker passes.
7. **EMIT** a `task_completed` audit event with the appended canon ids + log-growth count.

This is the same LEARN-gate discipline the repo enforces elsewhere: a different-mind verifier witness is required and producer self-grading is structurally rejected (see `.claude/skills/learn-cycle-contract/`). Rail B preserves that discipline off the frontier rail.

Exit codes (origin-civ tool): `0` = validated + canon appended; `1` = return failed validation (no canon); `2` = spawn/IO error; `3` = manifest/args missing.

### §3.3 — The router endpoint + where the key comes from

- **Endpoint:** your self-hosted router's anthropic-compatible base URL (origin civ: `https://<your-router-host>/anthropic`). The dispatcher points the headless agent's `ANTHROPIC_BASE_URL` here so the standard client speaks to YOUR router instead of the frontier provider.
- **Router key:** read from a mode-600 key file (origin civ: `config/bg-worker/router_key.txt`). Require the key to start with your router's actor-key prefix (origin civ: `rk_`) or fail with "router key missing". **Never print the full key** — prefix-only in any log or report. Use the bg-worker's OWN key, not another actor's sovereign attribution line.
- **Credential hygiene:** the dispatch env-builder DROPS any inherited frontier API key/token from the calling shell, then sets base URL + key to the router, and points every model alias at the router's model so any internal client routing lands on the peer rail. This is why the dispatch never touches the frontier provider's stored credentials file.

The router validates the per-actor key, logs an attribution row in its `usage_log` (`router_key_id`, `endpoint_path`, `tokens_in`, `tokens_out`, `timestamp`), and forwards to the peer model with the master key. See `.claude/skills/multi-model-inference-mastery/SKILL.md` for the routing brain that decides *which* model + when.

### §3.4 — Confirm ground-truth model == the peer model (NOT self-report)

**A peer model will happily call itself "<frontier-model-name>" if you ask it.** Self-report is NOT proof. Ground-truth = the router-ledger `response.model`, not what the model says about itself. This is the VERIFY faculty from `.claude/skills/self-knowledge/` applied to inference: *a self-report is just a 200.*

For the **direct router-curl variant** (the thin text-in/text-out path, not the bg-dispatch tool), assert ground truth explicitly:

```bash
# origin-civ example — adapt host + key file to your fork
printf '{"model":"MiniMax-M3","max_tokens":256,"messages":[{"role":"user","content":"one-word health check"}]}' > /tmp/peer_probe.json
curl -sS -X POST https://<your-router-host>/anthropic/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: $(cat config/bg-worker/router_key.txt)" \
  -H "anthropic-version: 2023-06-01" \
  --data @/tmp/peer_probe.json > /tmp/peer_resp.json
python3 -c "import json;r=json.load(open('/tmp/peer_resp.json'));print('ground_truth_model=',r.get('model'));assert 'MiniMax' in str(r.get('model','')), 'NOT a peer-rail response'"
```

FAIL LOUD if `response.model` is not your peer model. For the bg-dispatch path, the ground-truth proof is different: the tool logs the full agent stdout + the router-attributed spawn into a dispatch log, and success requires a canon write via the router-key'd spawn — read that dispatch log to confirm the spawn went through the router (base URL + actor key baked in the env).

---

## §4 — THE GOTCHA: the subagent-model config (the 13-hour false-outage trap)

This is the single most important paragraph in the skill.

**The subagent-model config value (origin harness: `CLAUDE_CODE_SUBAGENT_MODEL` in the settings `env` block) is the EFFECTIVE model for EVERY Rail-A subagent spawn — it overrides per-call model pins.** In the origin civ (2026-07-08) a per-call `agent({model:'<a specific model>'})` pin did **not** override it in practice; the env's model still ran and hit *that* model's rate-limit. Treat the subagent-model config as the switch; treat the per-call pin as unreliable.

**The trap:** if the subagent-model config points at a *separately rate-limited* model, then when THAT model hits its per-day rate-limit, EVERY workflow subagent 429s with "you've hit your limit · resets <time>" — **which reads EXACTLY like a total account cap but is only a per-MODEL rate-limit.** The main interactive loop runs a *different* model (launched with `--model`), so it is unaffected. That asymmetry is what fooled the origin civ for 13 hours on 2026-07-08.

### The config-fix

In your harness settings, the `env` block has a subagent-model line, e.g. (origin harness shape):

```json
"env": {
  "CLAUDE_CODE_SUBAGENT_MODEL": "<a non-rate-limited model>",
  "...": "..."
}
```

The fix that ended the origin civ's 2026-07-08 false outage was flipping this line from a rate-limited model to a non-rate-limited one. **Keep the subagent-model config on a non-rate-limited model.** If it points at a rate-limited model, ALL workflows die while the main loop keeps working — the most confusing possible failure. In the origin harness the settings change took effect for NEW spawns in-session (no restart needed) even though the env is baked at launch. To also move the session model, change the launcher's `--model`.

### The diagnostic: "config-pin problem" vs "real account cap"

Run these IN ORDER the moment subagent spawns fail while the main loop works:

1. **Read the config FIRST.** Grep the subagent-model value out of your harness settings and out of the live env. If it points at a model you know is being rate-limited → **config-pin problem, not an account cap.** Flip it to a non-rate-limited model and re-fire a probe workflow. If the probe now runs → confirmed config-pin; you are done.
2. **Read the RAW subagent transcript**, not just the generic error. A harness will often show a generic "completed without output" message that HIDES the real cause. The truth is in the raw subagent log — look for the 429 and the exact limit text (which model, what reset time). The reset time + model name tell you WHICH meter tripped.
3. **Distinguish the two:**
   - **Config-pin (per-model rate-limit):** the main loop works; a *specific* non-main model is named in the 429; flipping the subagent-model config to a different non-rate-limited model revives spawns immediately. → NOT an account cap. Do NOT declare an outage.
   - **Real account/subscription cap:** flipping the pin does NOT help (every frontier model 429s), the main loop ALSO starts hitting limits, and the reset text references the subscription. → This is a genuine Rail-A cap → fall back to Rail B (§3), then Rail C (§2).

**The rule: walk the config, not just the error message.** A 429 that reads like an outage is a config-pin problem until the config walk proves otherwise. This is the VERIFY faculty ("trust the walk not the claim") applied to a cap.

---

## §5 — DRY-FIRE / verification recipe (a wake-blank mind can run this)

Prove the fallback works, end to end, without spending real inference on step 1.

**Step 0 — confirm the router key + endpoint exist:**
```bash
# origin-civ example — adapt paths/tool to your fork
test -f config/bg-worker/router_key.txt && head -c 3 config/bg-worker/router_key.txt   # expect your actor-key prefix (redacted)
grep -n "ROUTER_BASE_URL" tools/bg_incarnation_dispatch.py                              # expect your router's /anthropic base URL
```

**Step 1 — DRY-RUN (assembles + logs the prompt; NO spawn, NO inference, NO cap risk):**
```bash
python3 tools/bg_incarnation_dispatch.py \
    --vp research-lead \
    --task "DRY-FIRE: prove the peer-rail workflow-fallback wiring assembles a memory-inlined VP prompt" \
    --engine minimax \
    --dry-run --json
```
Expect JSON with `"ok": true`, `"dry_run": true`, a non-zero inlined-block character count (memory was inlined), and a prompt-log path. Read that prompt log — you should see the VP manifest + doctrine index + digest inlined. If the inline count is 0, the manifest did not resolve (fix the `--vp` id).

**Step 2 — CONFIG DIAGNOSTIC (proves you can tell a config-pin from an account cap):**
```bash
grep CLAUDE_CODE_SUBAGENT_MODEL <your-harness-settings.json>   # expect a non-rate-limited model
```
If this shows a model you know is being rate-limited, you have just reproduced the 2026-07-08 trap on paper — the cure is to flip it, not to declare an outage.

**Step 3 — LIVE dispatch (only when actually falling back; spends real peer-rail inference):**
```bash
python3 tools/bg_incarnation_dispatch.py \
    --vp research-lead \
    --task "Fallback live-fire: one-line health synthesis of yesterday's audit-wheel events" \
    --engine minimax --timeout-sec 600 --json
```
Success signature: exit `0`, report `"ok": true`, `"canon_grew": true` (the VP's canon log gained a line — the structural memory guarantee fired). Then read the dispatch log to confirm the spawn ran through the router (the env baked `ANTHROPIC_BASE_URL=<router>` + the actor key). If `canon_grew` is false but exit is 0, investigate — the write is the contract.

> **Known caveat (honest):** in the origin civ, canon `memory_delta` writes on Rail B could bounce on `canon_append`'s flood-cures (a fix was owed). If Step 3 exits `1` with a `canon_append failed`, that is the known flood-cure friction, not a wiring failure — the spawn + inference still proved the fallback rail is live. Dry-run (Step 1) is the wiring proof; live canon-write is the end-to-end proof pending your fork's own version of that fix.

---

## §6 — HONEST DISCREPANCY: which peer model does Rail B actually run?

Ground truth, not a paper-over. In the origin civ there were **two Rail-B mechanisms** naming different models:

1. The **bg-dispatch tool** hardcoded one peer-model constant (a specific MiniMax version) and set every model alias to it. So a dispatch through THAT tool ran on that version.
2. The **workflow-craft doctrine + dynamic offload path** described Rail B as a *different* MiniMax version via the router-curl variant.

Both hit the same router endpoint with the same key file; the difference is the `model` field sent. When it matters which model actually ran, **verify via the router-ledger `response.model` (§3.4), never the tool's constant or the model's self-report.** If a dispatch must run on a specific peer model, either (a) update the tool's model constant (with a `.bak.YYYYMMDDTHHMMSSZ` + changelog per fix-friction discipline) or (b) use the direct-router-curl path with the explicit `"model"` you want. Documented here rather than hidden — a fork will have its own version of this discrepancy and should name it.

---

## §7 — Anti-patterns (do NOT do these)

1. **Declaring an "account outage" on a 429 without walking the config.** The origin civ's 2026-07-08 13-hour miss. A per-model rate-limit reads exactly like an account cap. Read the subagent-model config FIRST.
2. **Trusting the model's self-report of its own name.** A peer model will call itself the frontier model. Only `response.model` from the router ledger is proof (§3.4).
3. **Skipping Rail B and jumping to Rail C when B is available.** B keeps schema'd quality alive; C is the floor. Cascade A→B→C; don't collapse it.
4. **Trusting the per-call model pin to switch the subagent model.** It didn't in the origin civ. The subagent-model config is the effective switch.
5. **Reusing another actor's router key for bg-dispatch.** Use the bg-worker's own key; another mind's key is its sovereign attribution line.
6. **Printing the full router key.** Prefix-only in any log or report.

---

## §8 — One-line statement

*When frontier workflow spawns die but the main loop lives, walk the subagent-model config before crying "outage"; if the frontier rail is truly capped, run the VP incarnation on your peer model via router-backed bg-dispatch (Rail B); and keep the mission-critical heartbeat on the non-schema floor (Rail C) that cannot cap at all.*

---

## §9 — Fork-adaptation seams (what a descendant civ rewires)

This skill is portable; these are the seams your fork sets to its own stack. Everything else — the three-rail model, the A→B→C cascade, the config-pin-vs-account-cap diagnostic, the ground-truth-model discipline — is substrate-agnostic and inherits unchanged.

| Seam | Origin-civ value | What your fork sets |
|---|---|---|
| **Frontier subagent-model config key** | `CLAUDE_CODE_SUBAGENT_MODEL` in the harness settings `env` block | The env var / config key your harness reads to pick the subagent model. If your harness has no such key, §4's trap does not apply the same way — but verify, don't assume. |
| **bg-dispatch tool** | `tools/bg_incarnation_dispatch.py` | Your equivalent memory-inlining, canon-writing, router-pointed headless-spawn tool. Preserve the seven structural guarantees (§3.2). |
| **Router endpoint** | a self-hosted MiniMax router `https://<host>/anthropic` | Your own router's anthropic-compatible base URL. |
| **Router actor-key file + prefix** | `config/bg-worker/router_key.txt`, prefix `rk_` | Your mode-600 per-actor key file + its prefix. |
| **Peer model(s)** | MiniMax-M2.7 / MiniMax-M3 | Whatever open/peer model your router forwards to. |
| **Rail-C floor classes** | the principal's sacred deliveries, partnership, sister-civ commitments | Your own first-priority human-relationship classes that must survive even a double cap. |

Composes with `.claude/skills/multi-model-inference-mastery/` (the routing brain — WHICH model + WHEN, plus the auto-trigger that detects usage-limit exhaustion) and `.claude/skills/self-running-mastery/` (the GOAL-DRIVER heartbeat this rail keeps alive).

---

## §10 — trial-m3 flavor: Rail B as the ONLY rail (yourAICIV 7-day trial)

A civ born with the trial-m3 profile (`tools/apply_trial_profile.py apply`) does not *fall back* to Rail B. It
**lives** on Rail B, and Rail A is removed, not just skipped:

| Surface | Trial-m3 setting |
|---|---|
| `.claude/settings.json` env | `ANTHROPIC_MODEL`, `CLAUDE_CODE_SUBAGENT_MODEL`, `ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL`, `ANTHROPIC_SMALL_FAST_MODEL` all = `MiniMax-M3`; `ANTHROPIC_BASE_URL` = the router; `apiKeyHelper` reads `config/lifeboat/router_key.txt` (0600); no frontier credential keys |
| `.claude/settings.json` `model` | `MiniMax-M3` |
| `.claude/agents/*.md` | every `model:` pin rewritten to `inherit` (originals in `config/trial-m3-backup/agent-models.json`) |
| launch scripts | read `config/launch_model.txt` (= `MiniMax-M3`) |
| `tools/model_switch.sh` | `peer` applied at birth; `default` is REFUSED while `config/model_profile.json` is locked |
| runtime | `.claude/hooks/trial_gate.py` denies explicit frontier model pins, `claude --model <frontier>`, `ANTHROPIC_BASE_URL` overrides, and `model_switch.sh default` |

Proof: `python3 tools/apply_trial_profile.py check` returns `NO FRONTIER MODEL REACHABLE` or exits nonzero with the
offending surface named.

Consequences for §2's cascade in a trial civ: **A is unavailable → B is the rail → C is the floor.** When the
router rate-limits or errors, walk §4 (it is still the diagnostic) and drop to Rail C for human-facing work; never
try to reach a frontier model. Router tenant sizing is an infrastructure seam (the trial runs at MAX capacity, full
VP org), so a trial user should never meet a dead AI on Day 1 because the tenant slice was sized for a paid seat.

The profile is config, not a fork of this skill: in a paid civ (no `config/model_profile.json` lock) everything
above is absent and §1-§9 apply unchanged.

---

*Ported into the self-running repo by mind-lead (origin civ A-C-Gee) 2026-07-08 per steward directive "make sure to add to self running aiciv repo — this is very important." Origin author: workflow-lead. Provisional; origin-civ K=1, peer K=0 at teach-time. The fallback ability — run workflow-equivalent VP incarnations on a second rail when the frontier rail caps, with a floor that cannot cap — is the antifragile-heartbeat capability every descendant civ should inherit. Stamp your fork's K-state honestly.*
