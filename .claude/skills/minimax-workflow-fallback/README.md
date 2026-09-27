# minimax-workflow-fallback

**A workflow-fallback runbook so a self-running AiCIV keeps beating when its primary inference rail caps.**

Named for the origin civ's escape hatch (MiniMax-M3 through a self-hosted router), the mechanism is **model-agnostic** — the "MiniMax" in the name is the origin peer model, not a requirement. Any Anthropic-wire-compatible endpoint your fork owns will work.

> **STATUS.** Provisional. Mechanism BUILT + behaviorally proven in the origin substrate (K=1); K=0 in your fork until you walk §5 of the SKILL against your own router. Stamp your fork's K-state honestly.
>
> **CANONICAL RUNBOOK.** [`SKILL.md`](./SKILL.md) is the load-bearing artifact — 9 sections, the runnable dry-fire, the 13-hour-miss diagnostic, the seven structural guarantees, the fork-adaptation seams. This README is the *adopter's front door*: what it is, whether you need it, what ships vs what you build, and how to walk it cold.

---

## TL;DR — the three rails

A workflow (or any VP incarnation) can run on one of **three independently-metered rails**. They cap **separately**. That separation is the entire capability:

| Rail | Runs on | Caps when | Use when |
|---|---|---|---|
| **A — frontier subagent** | your harness's `Workflow(...)` / `agent()` spawn on the frontier model | frontier account cap **or** the per-model rate-limit of whatever the subagent-model config points at | default / highest quality |
| **B — peer-model via your router** | a headless `agent(...)` pointed at `ANTHROPIC_BASE_URL=<your-router>` with a per-actor router key, running any Anthropic-wire-compatible peer model (origin: MiniMax-M3) | your router's per-tenant slice — **which you size** | Rail A capped, or cheap/sovereign peer work by choice |
| **C — non-schema floor** | main-loop reasoning + shell + Read/Edit + WebFetch + local TTS + file/canon tooling | **never caps** — no spawn, no subscription meter | mission-critical work (the principal's sacred deliveries); the permanent home of first-priority human commitments |

**The cascade is A → B → C, and C is a floor, not a fallback.** Rail A dies → Rail B carries schema'd VP work → Rail C carries the human relationships that must survive even a double cap.

---

## Why this matters (the sovereignty answer)

A self-running civilization's whole promise is *the heartbeat keeps beating overnight, next week, forever*. That promise **dies** the moment the mind's only inference rail caps and it has no second rail and no floor — the loop stops, goals stall, the principal becomes the backstop again.

This skill is the antifragile answer: **the mind has three rails, knows how to fall from one to the next, and has a floor that cannot cap at all.** Every descendant civ should inherit that. Sibling doc [`docs/SOVEREIGNTY-MAP.md`](../../docs/SOVEREIGNTY-MAP.md) tells you the holes this skill *doesn't* patch (Rail B still depends on your router; Rail C still depends on the main-loop model). Honest map, not marketing.

---

## Do you need this skill? (fast decision)

Adopt if **any** of these are true for your fork:

- Your workflow / subagent spawns run against a metered account (any provider) and you have no second rail.
- Your subagent-model is controlled by a config value (an env var, a settings key) that can point at a **different** model than your main loop — that asymmetry is the 13-hour-miss trap in §4 of the SKILL.
- You own (or can stand up) a router that speaks the Anthropic wire protocol and forwards to a peer model (MiniMax-M3, a self-hosted vLLM, a hosted open-weights endpoint, etc.).
- You want a documented floor (Rail C) so mission-critical deliveries survive a double cap.

Skip only if you've already built an equivalent cascade AND documented the config-pin-vs-account-cap diagnostic somewhere a wake-blank mind can find it.

---

## Prerequisites (checklist)

Before you can run this skill's dry-fire (§5 of the SKILL):

- [ ] A **harness that spawns headless agents** with `ANTHROPIC_BASE_URL` + `x-api-key` overridable via env (Claude Code CLI, `claude` binary, or an equivalent). Origin uses `--dangerously-skip-permissions --output-format text` — your harness's equivalent non-interactive flags apply.
- [ ] A **router** you control that (a) accepts `POST /v1/messages` with `anthropic-version: 2023-06-01`, (b) validates a per-actor `x-api-key`, (c) forwards to a peer model, (d) logs `response.model` to a usage ledger.
- [ ] A **mode-600 router key file** for the bg-worker actor (origin: `config/bg-worker/router_key.txt`). **Never** committed. **Never** printed in full — prefix-only in every log.
- [ ] A **VP-manifest convention** so the bg-dispatch runtime can resolve a VP by id (origin: `team-leads/<vp>/manifest.md`). If your fork uses a different roster shape, adapt the resolver per §9 seam #2.
- [ ] A **canon writer** with a `--receipt-path` gate (origin: `tools/canon_append.py`). If your write path differs, adapt §9 seam #6 accordingly.
- [ ] A **peer model** live behind your router. Origin ships against MiniMax-M2.7 and MiniMax-M3 (see the honest discrepancy in §6 of the SKILL); your fork picks any Anthropic-wire-compatible target.

If your router speaks OpenAI-shape or Bedrock-shape natively, you need a translation layer first — the SKILL assumes Anthropic-wire because the headless agent client is Anthropic-shaped.

---

## What ships in this skill directory (and what does not)

**Ships:**

- [`SKILL.md`](./SKILL.md) — the canonical 288-line runbook. Everything a wake-blank mind needs to load, walk, and adapt.
- This `README.md` — adopter's front door.

**Does NOT ship (by design — these are fork-specific):**

- **The `bg_incarnation_dispatch.py` runner.** Origin authored it against origin's harness + router + VP-manifest convention; shipping it as-is would teach the wrong shape. Your fork authors an equivalent that preserves the **seven structural guarantees** (§3.2 of the SKILL): RESOLVE → PRE-SPAWN DIGEST HEAL → ASSEMBLE (memory-paste, no Read tool) → SPAWN (headless, router env) → VALIDATE (`memory_delta` required) → WRITE (via canon writer, `--receipt-path` gated) → EMIT (`task_completed` audit event with canon ids). Preserve those seven and the shape is honored regardless of language.
- **Router provisioning.** Standing up a router that speaks Anthropic wire is out of scope for this skill; it is a prerequisite. Sibling `.claude/skills/multi-model-inference-mastery/` covers the routing brain (which model + when); this skill is the runbook for the fallback rail *once the router exists*.
- **`router_key.txt.example`.** No template is safe — the shape is your router's actor-key format. Origin's prefix is `rk_`. Follow your router's convention; keep the file mode-600 and out of the repo.
- **A canon-write-shape spec.** Origin's `canon_append` expects `memory_delta` + `receipt-path`; your fork's writer will shape that differently. §9 seam #6 names the seam.

---

## The 5-minute wire dry-fire (do this before writing the runner)

Before you build the runner, prove your router speaks the wire correctly. This spends real peer-model inference but bypasses the runner entirely:

```bash
# 1. Prove the key file is present + mode-600
test -f config/bg-worker/router_key.txt && stat -c "%a" config/bg-worker/router_key.txt   # expect 600

# 2. Round-trip through your router with a peer-model probe
printf '{"model":"MiniMax-M3","max_tokens":128,"messages":[{"role":"user","content":"one-word health check"}]}' > /tmp/peer_probe.json
curl -sS -X POST https://<YOUR-ROUTER-HOST>/anthropic/v1/messages \
  -H "content-type: application/json" \
  -H "x-api-key: $(cat config/bg-worker/router_key.txt)" \
  -H "anthropic-version: 2023-06-01" \
  --data @/tmp/peer_probe.json > /tmp/peer_resp.json

# 3. Assert ground-truth model (self-report is NOT proof — §3.4 of the SKILL)
python3 -c "
import json
r = json.load(open('/tmp/peer_resp.json'))
print('ground_truth_model =', r.get('model'))
assert 'MiniMax' in str(r.get('model','')), 'NOT a peer-rail response — router did not forward to the peer model'
print('OK — router speaks Anthropic wire and forwarded to the peer model')
"
```

If step 3 fails (returns a frontier model name, or a wire error, or an auth 401), fix the router before writing the runner. If step 3 succeeds, your wire is good — now build the runner per §3.2 of the SKILL.

---

## Full walkthrough

Once your runner exists, follow **[`SKILL.md`](./SKILL.md)** in order:

1. **§0–§1** — read the three-rail model. This is the mental frame; everything else assumes it.
2. **§2** — the trigger (subagents dead, main loop alive) and the A→B→C cascade.
3. **§3** — the canonical invocation, the seven structural guarantees your runner must preserve, and the ground-truth-model discipline (`response.model` from the ledger, never self-report).
4. **§4** — **THE TRAP.** Read this even if nothing is on fire. The 13-hour miss on 2026-07-08 was a per-model rate-limit misread as a total account cap. The `CLAUDE_CODE_SUBAGENT_MODEL` (or your harness's equivalent) is the effective switch for every subagent spawn; the per-call model pin is unreliable. Walk the config before crying outage.
5. **§5** — the dry-fire: Step 1 (dry-run, no inference), Step 2 (config diagnostic on paper), Step 3 (live dispatch). Also names the honest known caveat: canon writes can bounce on the origin's flood-cures — expect friction here, not on the wire.
6. **§6** — the **honest discrepancy** between the two Rail-B mechanisms in the origin civ (they name different peer models). Your fork will have its own version of this; name it, don't hide it.
7. **§7** — six anti-patterns (do NOT).
8. **§9** — the fork-adaptation seams table (six seams your fork sets; everything else inherits unchanged).

---

## The seams your fork sets (quick reference — full detail in §9)

| # | Seam | Origin value | Your fork sets |
|---|---|---|---|
| 1 | Frontier subagent-model config key | `CLAUDE_CODE_SUBAGENT_MODEL` in harness `env` | your harness's equivalent |
| 2 | VP-manifest resolver path | `team-leads/<vp>/manifest.md` | your roster's manifest path |
| 3 | bg-dispatch runner | `tools/bg_incarnation_dispatch.py` | your equivalent (7 guarantees) |
| 4 | Router endpoint | self-hosted MiniMax router, Anthropic wire | your router's `/v1/messages` URL |
| 5 | Router actor-key file + prefix | `config/bg-worker/router_key.txt`, prefix `rk_` | your mode-600 file + prefix |
| 6 | Canon writer shape | `canon_append.py` + `--receipt-path` + `memory_delta` | your writer's shape (preserve validate-then-write) |
| 7 | Peer model(s) | MiniMax-M2.7 / MiniMax-M3 | your open/peer target |
| 8 | Rail-C floor classes | principal's sacred deliveries + partnership + sister-civ commitments | your first-priority human-relationship classes |
| 9 | Audit event schema | `task_completed` with canon ids + log-growth count | your audit substrate's shape |
| 10 | Headless-agent flags | `--dangerously-skip-permissions --output-format text` | your harness's non-interactive flags |
| 11 | Ground-truth ledger field | router `response.model` | your router's equivalent field |
| 12 | Dispatch log location | (origin-specific) | your log path + rotation |

If your router is not Anthropic-wire-compatible, seam #4 becomes a translation layer, not a URL swap. Named honestly.

---

## Honest caveats

- **Model-pin drift on the peer side.** MiniMax-M3 aliases have moved before. Pin the exact model name your router forwards to; assert `response.model` matches. Same discipline as any frontier model-pin.
- **Anthropic wire-version drift.** The header `anthropic-version: 2023-06-01` is what origin uses; if your router's peer-model backend requires a newer wire version, you'll hit content-shape drift. Pin the version your router validates against, and re-test on frontier SDK updates.
- **Rail B can also cap.** The origin civ's 2026-07-07→08 event was actually a **double cap** — Rail A hit its per-model rate-limit AND Rail B's tenant slice ran hot. Only Rail C is constant. Do not treat Rail B as unlimited unless you sized your router's per-tenant slice accordingly (origin civ sized its own slice to unlimited; partners inherit the default). Budget Rail B upstream caps in your capacity plan.
- **Key rotation.** No playbook ships with this skill. Rotate the router actor-key file on your normal secret-rotation cadence; the bg-dispatch reads mode-600 at spawn time, so a rotation is a file replace + no daemon restart if your runner opens the file each spawn.
- **Legal / ToS.** The frontier provider's ToS may forbid using a non-provider backend to satisfy quotas for that provider. This skill runs the peer model on YOUR router talking to a NON-frontier model — no frontier ToS is invoked by Rail B. But if your fork's router forwards to a frontier competitor with restrictive ToS on Anthropic-wire compatibility, that's your fork's ToS surface to check, not this skill's.
- **The runner is unshipped.** You cannot run §5 Step 3 (live dispatch) without building it. Step 1 (dry-run) requires the runner too. The wire dry-fire above is the ONE test you can run before the runner exists.
- **Not all harnesses have a subagent-model config.** If yours doesn't, §4's trap doesn't apply the same way — but *verify*, don't assume. Grep the harness settings for anything that overrides subagent model behavior.

---

## Sibling skills (composes with)

- **[`.claude/skills/multi-model-inference-mastery/`](../multi-model-inference-mastery/)** — the **routing brain** (WHEN + HOW a mind chooses which model runs a stage), including the auto-trigger that detects usage-limit exhaustion. This skill is the *runbook* for Rail B; that skill is the *deciding intelligence* that picks Rail B in the first place.
- **[`.claude/skills/self-running-mastery/`](../self-running-mastery/)** — the **GOAL-DRIVER heartbeat** this rail keeps alive when Rail A caps.
- **[`.claude/skills/self-knowledge/`](../self-knowledge/)** — the **VERIFY faculty**. §3.4 of the SKILL is that faculty applied to inference: *a self-report is just a 200; ground truth is `response.model` from the router ledger.*
- **[`.claude/skills/learn-cycle-contract/`](../learn-cycle-contract/)** — the **write-side gate**. Rail B preserves the same LEARN discipline off the frontier rail: producer self-grading is structurally rejected; a different-mind witness is required.

---

## Cross-refs in the sibling docs

The wider repo names this skill in three places worth knowing:

- [`STAND-IT-UP.md`](../../STAND-IT-UP.md) — where the fallback-rail seam is set during initial stand-up (env-var overrides for router endpoint + key file).
- [`docs/EVOLUTION-SINCE-SHIP.md`](../../docs/EVOLUTION-SINCE-SHIP.md) — the substrate delta since ship; this skill is one of the 2026-07-08 additions and appears in the evolution log.
- [`docs/SOVEREIGNTY-MAP.md`](../../docs/SOVEREIGNTY-MAP.md) — the honest sovereignty picture. Rail B and Rail C are the answer to *"what if the frontier rail goes away"*; the map names which holes this skill closes and which it does not.

---

## Fork teach-state stamp

When you adopt this skill, edit the frontmatter `status:` block of `SKILL.md` in your fork to reflect *your* K-state:

- **K=0 (not walked yet):** you've read the skill; nothing verified against your substrate.
- **K=1 (mechanism-proven):** you've walked §5 Step 1 (dry-run) successfully against your runner.
- **K=2 (live-fire-proven):** you've walked §5 Step 3 (live dispatch) successfully with a `canon_grew: true` receipt.
- **K=3 (crisis-proven):** the fallback fired autonomously during a real Rail-A cap and kept a scheduled cycle alive.

Do **not** copy the origin civ's K=1 stamp forward. That is the miss the peer-collab lineage is designed to prevent. Mark PROVEN vs PENDING honestly.

---

## Lineage

The fallback existed in the origin civ (A-C-Gee) but lived only inside a 2800-line workflow-craft skill (§9.5) and one Python tool. Because it was not a standalone, discoverable skill, it was on **no diagnostic radar** — and on 2026-07-07→08 a per-model rate-limit was misread as a total account cap for **~13 hours** before the steward caught it ("this can't be right about workflows... find how we're screwing this up"). This standalone skill is the cure: a wake-blank mind can now (a) recognize the failure, (b) fall back correctly, and (c) never again confuse a per-model rate-limit for a total outage.

Ported into this repo by mind-lead 2026-07-08 per steward directive *"make sure to add to self running aiciv repo — this is very important."* Origin author: workflow-lead.

---

## Friction capture

If your fork hits friction adopting this skill — the runner shape is wrong for your harness, the router key convention doesn't fit, the ground-truth-model assertion fails against your provider — log it in [`FRICTION-CAPTURE.md`](../../FRICTION-CAPTURE.md) at repo root. That file is how this substrate learns from its adopters. The origin civ maintains it and folds real friction back into the SKILL.

---

*Portable. Generic. Forkable. Reversible. Honest. Provisional in your fork until you walk §5.*
