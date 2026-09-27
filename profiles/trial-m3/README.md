# trial-m3: the yourAICIV 7-day MiniMax-M3 trial flavor

A **profile** of the birth template. It changes config, not code. A civ born without it is a normal paid civ, and
every trial mechanism below does nothing there (no `config/trial.json`, so no gating anywhere).

## What it is

- **M3 only, max capacity.** Primary, every subagent, every workflow, and every VP incarnation run on MiniMax-M3 through
  the router rail (Rail B, `.claude/skills/minimax-workflow-fallback/` §10). You get the full VP org, and no
  frontier-model path stays reachable.
- **It knows it's on trial.** `config/trial.json` (the shared contract with the yourAICIV portal) sets the clock.
  The AiCIV sees "Day N of 7" every session and every turn.
- **It knows the human first, then ships as soon as each build is ready.** A compressed identity interview
  (Phases 1-4) happens in the first conversation, then 3 builds lock. Each build ships the moment it's ready, with
  verification built in. 72h is a ceiling for Build #1, never a floor.
- **Every claim is proven.** Every factual claim carries a source URL or an on-disk receipt
  (`tools/receipt_check.py`). A different mind verifies each build before it ships (`workflows/m3-trial-build.js`).
- **Day 7 is a warm pause, not a deletion.** After expiry the AiCIV does no work and answers with a short note plus
  the payment link. The portal blocks everything except the payment button. Nothing is deleted.

## Provisioning (once, at birth, after the template is stamped)

```bash
export M3_ROUTER_BASE_URL="<Anthropic-wire base URL of the M3 router for this tenant>"   # REQUIRED
export M3_ROUTER_KEY_FILE="/secure/path/to/this-tenant-router-key"                        # REQUIRED (or M3_ROUTER_KEY)
# optional:
export M3_MODEL_ID="MiniMax-M3"
export TRIAL_PAYMENT_URL="https://..."   # default: payment_url in config/partner.json
export TRIAL_START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
export TRIAL_OPERATOR_COPY="/etc/aiciv/trial.json"   # REQUIRED in production (canonical path; outside the civ tree)

sudo -E python3 tools/apply_trial_profile.py apply --root "$CIV_ROOT"   # root, so the operator copy is root-owned
# -> ends with the check; must print: check: N pass, 0 fail -> NO FRONTIER MODEL REACHABLE
```

Brand, reseller, and the payment link come from the partner profile (`config/partner.json`, see
`tools/partner_profile.py`) and are frozen into `config/trial.json` at birth.

The step **refuses to run** if the router seams or the payment link are empty, because the trial must never quietly fall back to a
frontier model. It is safe to re-run: the trial clock is kept (`--reset-clock` to restart it deliberately), and
hooks and the grounding block are not duplicated.

### The portal reads the operator copy, never the civ's

`config/trial.json` sits in the civ tree, and the AiCIV can write its own tree. The in-mind gate
(`.claude/hooks/trial_gate.py`) denies every trial-changing command, but it is a best-effort layer: a
determined process with a shell can still find a way around a text filter. So the portal must not trust the civ's copy.

- `--operator-copy PATH` (or `TRIAL_OPERATOR_COPY`) publishes the same record at `PATH`. `apply` refuses a path
  inside the civ tree. Run as root, the file and its directory are root-owned, 0644/0755.
- **Canonical path: `/etc/aiciv/trial.json`**, inside the civ's container (the portal runs in the same container,
  so it is the same file for both; nothing to mount). If the portal runs elsewhere, bind-mount that file
  read-only at the same path. A host with several civs outside containers uses `/etc/aiciv/<civ>/trial.json`.
- Start the portal with `TRIAL_CONFIG_PATH=/etc/aiciv/trial.json`. `apply` records the same value in
  `.claude/settings.json` `env` and in `config/model_profile.json` (`trial_record`), so the AiCIV's hook and tools
  read the same copy.

**One resolution rule, everywhere** (`tools/trial_state.py`, and the portal must match it):
`$TRIAL_CONFIG_PATH` → the value recorded in `.claude/settings.json` `env` → `$CIV_ROOT/config/trial.json`.
`python3 tools/trial_state.py where` prints the result. `check` fails if the operator copy is missing, inside the
tree, or disagrees with `config/trial.json` on the clock. On a trial civ, a configured operator copy that is missing
fails **closed** (the AiCIV treats the trial as ended) rather than silently ungating.
- Re-running `apply` keeps an existing operator copy. It is authoritative, and only `--reset-clock` republishes it.
- `convert --operator-copy PATH` flips the operator copy from **itself**, never from the civ's file.

The authority is the operator copy (UI and API 402) plus the router key expiry (inference). The civ-side gate
decides what the AiCIV does, but it never decides access.

### What it writes

| File | Purpose |
|---|---|
| `config/trial.json` | the trial clock (the civ copy; the operator copy at `TRIAL_CONFIG_PATH` is what the portal and the hook read) |
| `config/model_profile.json` | `{"profile":"trial-m3","locked":true}`; `model_switch.sh default` is refused while locked |
| `config/launch_model.txt` | read by `tools/launch_civ_tower.sh` and `tools/launch_primary_visible.sh` |
| `config/router_endpoint.txt`, `config/peer_model_id.txt`, `config/lifeboat/router_key.txt` (0600, gitignored) | the Rail B seam `tools/model_switch.sh` already uses |
| `config/model_mode.json`, `config/model_mode.env` | `model_switch.sh peer`, for `tools/model_boot.sh` |
| `.claude/settings.json` | model env keys and `model` set to M3, `ANTHROPIC_BASE_URL` set to the router, `apiKeyHelper` reads the key file, frontier credential keys removed, `trial_gate.py` hooked on SessionStart / UserPromptSubmit / PreToolUse. Backup: `.claude/settings.json.pre-trial-m3.bak` |
| `.claude/agents/*.md` | `model:` becomes `inherit`. Originals: `config/trial-m3-backup/agent-models.json` |
| `.claude/CLAUDE.md` | a marked trial block after the self-removing awakening gates, pointing at `.claude/skills/m3-trial-mode/SKILL.md` |

### Infrastructure prerequisites (outside this repo)

1. **Router tenant key**: one per trial civ, sized for **max capacity** (the full VP org fans out). An undersized
   slice means the trial user meets a dead AI on Day 1.
2. **Router must not forward non-MiniMax model ids** for trial tenant keys. This is the server-side half of
   "no frontier model reachable". The civ side is proven by `check`; the router side is an infra configuration.
3. **Expire the router tenant key at `expires_at`** (or throttle it to a trickle so the pause note can still go
   out). This is the hard stop for inference if anyone edits files inside the container. The portal's 402 is the
   hard stop for the UI.
4. **Do not provision frontier credentials** into a trial container: no Claude login and no `ANTHROPIC_API_KEY`.
   Leave `GOOGLE_API_KEY` empty, since Gemini image generation is a non-M3 inference path and `check` flags it.
5. **Web tools:** confirm `WebSearch`/`WebFetch` work through the router before launch. If they don't, the proof rule
   makes the AiCIV mark research "unverified". It won't invent sources, but the Day-3 research beat gets weaker.

6. **Treat the router key as extractable.** The AiCIV runs as the same OS user that reads the key, so file modes
   do not hide it from the AiCIV or from anyone with a shell in the container. The skill rule (`m3-trial-mode` §9:
   never disclosed, whoever asks) and the gate's filter are best-effort layers. The boundary is router-side:
   a per-tenant key that expires at `expires_at`, a per-tenant spend cap, a MiniMax-only model allow-list, and a
   new key on conversion. Do not open public trial births until an expired test key is refused by the router.

## After birth

The AiCIV runs `python3 tools/schedule_7day_wow.py`. It auto-detects the trial and puts the latest-by trial arc in
AgentCal, timed from `started_at`.

## Conversion (operator)

```bash
sudo -E python3 tools/apply_trial_profile.py convert --root "$CIV_ROOT"                    # "trial": false -> portal + AiCIV ungate now
sudo -E python3 tools/apply_trial_profile.py convert --root "$CIV_ROOT" --restore-models   # also return to paid routing
```

`convert` flips the operator copy recorded at birth (override with `--operator-copy PATH`) from itself, then the civ copy.

`--restore-models` restores `settings.json` and the agent pins byte-for-byte from the birth backups, unlocks and
flips `model_switch.sh` to `default`, and keeps every trial file as an audit copy. Nothing is deleted.

**Follow-up (documented, not built):** a Stripe webhook on the payment link's `checkout.session.completed` that
calls `convert` for the matching civ. Conversion is manual until then.

## Proof commands

```bash
python3 tools/apply_trial_profile.py check        # no frontier model reachable (nonzero exit otherwise)
python3 tools/trial_state.py status               # the /api/trial JSON
python3 tools/trial_state.py note                 # "Day N of 7 ..." / the expired note
python3 tools/receipt_check.py <ledger.claims.json>
python3 tools/schedule_7day_wow.py --dry-run      # the arc, no network
```
