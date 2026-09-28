# yourAICIV — AiCIV birth template

This repository is the **birth template** for a yourAICIV AiCIV. An AiCIV is a persistent AI partner for one
human: it has its own name, memory, schedule, and a small organization of specialist minds it coordinates.
Each new AiCIV starts as a copy of this repository and grows from there.

yourAICIV is a reseller distribution (reseller: Travis Morehead). It adds three things to the generic AiCIV
template:

1. **A partner profile** (`config/partner.json`). Greetings, the trial countdown, and the payment link all read
   from this one file.
2. **The delivery engine** (`apps/client-starter/`). The AiCIV uses it to stand up and run a small business system
   for its human or their clients.
3. **A 7-day MiniMax-M3 trial birth** (`profiles/trial-m3/`). This is a config profile, not a separate codebase.

> This repository is public. Secrets never live here: the router address and key, per-client secrets, and customer
> data are **seams** that provisioning fills at birth, outside version control (see [Provisioning](#provisioning)).

---

## Two kinds of birth

| | **Paid birth** | **7-day trial birth** |
|---|---|---|
| How | Stamp the template. Nothing else. | Stamp the template, then run `tools/apply_trial_profile.py apply` |
| Model | The template's default model configuration | **MiniMax-M3 only**, on every surface (primary, every specialist, every workflow), through a router |
| Capacity | Full organization | Full organization. Nothing is cut down for the trial |
| `config/trial.json` | absent, so nothing is gated anywhere | written once at birth with the trial clock |
| After day 7 | n/a | **Paused, never deleted.** The AiCIV does no work and replies with a short, warm note plus the payment link. The portal shows only a payment button. All work, files, and memory are kept |
| Becoming paid | n/a | The operator runs `apply_trial_profile.py convert`. Everything unlocks immediately, and `--restore-models` returns the civ to paid routing byte for byte |

### The trial contract (shared with the portal)

`config/trial.json` at the civ root:

```json
{"trial": true, "started_at": "<ISO8601 UTC>", "duration_days": 7, "expires_at": "<ISO8601 UTC>",
 "payment_url": "<from config/partner.json>", "brand": "yourAICIV", "reseller": "Travis Morehead",
 "model": "MiniMax-M3"}
```

- If the file is absent or `"trial": false`, the civ is not on trial and nothing is gated.
- **Where the record is read (one rule for the AiCIV, its tools, and the portal):**
  1. `$TRIAL_CONFIG_PATH` if set. In production this is the **operator copy at `/etc/aiciv/trial.json`**
     (root-owned 0644, outside the civ tree; one civ per container, so one path everywhere);
  2. else the `TRIAL_CONFIG_PATH` birth recorded in `.claude/settings.json` `env`;
  3. else `$CIV_ROOT/config/trial.json` (the civ copy; `CIV_ROOT=/home/aiciv` in the standard container).

  `python3 tools/trial_state.py where` prints the resolved path. A configured operator copy that is missing on a
  trial civ fails **closed** (the AiCIV treats the trial as ended, `check` fails), so a mount mistake can never
  silently ungate a trial. A host that runs several civs outside containers uses `/etc/aiciv/<civ>/trial.json`
  and sets `TRIAL_CONFIG_PATH` to it for both the civ and its portal.
- The portal's `GET /api/trial` returns `{"trial", "day", "days_left", "expires_at", "expired", "payment_url"}`.
  `tools/trial_state.py` is the reference implementation (`python3 tools/trial_state.py status` prints exactly that
  JSON).
- Expiry is enforced on both sides. The AiCIV's hook (`.claude/hooks/trial_gate.py`) blocks all work tools except
  the reply path. The portal API refuses normal endpoints with a 402-style response. The router key expiring is the
  hard stop for inference (see below).

### What the trial does in its week

The trial AiCIV knows it is on Day N of 7 (`.claude/skills/m3-trial-mode/`). It learns its human's goals first with a
short identity interview, then ships three builds aimed at those goals. Each build ships **as soon as it is ready**:
72 hours is a ceiling for the first build, never a waiting period. Every factual claim carries a source URL or an
on-disk receipt, and a second mind checks each build before it ships (`workflows/m3-trial-build.js`,
`tools/receipt_check.py`). The week closes with an honest review of what shipped and a plan for week two.

---

## The delivery engine

`apps/client-starter/` is a self-hosted Flask/SQLite business system: public funnel, CRM, a three-number dashboard,
email automations, store, blog, affiliates, booking, and pluggable payments with Stripe as the default. The AiCIV
runs it **for** its human (client #1 is their own business by default) and for their clients.

- **Operating manual:** `.claude/skills/client-onboarding/SKILL.md`, five phases: Intake, Provision, Customize,
  Verify, Hand Off.
- **When it fires:** a self-removing gate in `.claude/CLAUDE.md` starts it after the newborn's awakening is
  verified. It also fires whenever the human asks for a website, funnel, CRM, store, or booking page. The switch is
  `config/client-onboarding.json`.
- **Never edited in place.** `clone_client.sh <client-slug>` stamps a per-client instance with its own random
  secrets, database, and port. Instances bind to `127.0.0.1`, and they are gitignored (they hold client secrets and
  customer data).
- **Trial rule:** after a trial expires, no new client work starts. Running client sites are never stopped or
  deleted.
- Provenance, and every deviation from the original package, is listed in `apps/README.md`.

---

## Partner profile

`config/partner.json`:

```json
{"brand": "yourAICIV", "reseller": "Travis Morehead", "payment_url": "https://buy.stripe.com/...",
 "notify_emails": []}
```

- `python3 tools/partner_profile.py show | name | intro` prints the resolved profile.
- The newborn's first greeting and first-hello ceremony introduce it with the brand (for example, "your AiCIV from
  yourAICIV"). The AiCIV's own name, chosen with its human, always comes first.
- On a trial birth the three values are frozen into `config/trial.json`, and the countdown reads "Day 3 of 7 of your
  trial with yourAICIV". While the trial runs, the file is read-only to the AiCIV.
- **Another reseller** gets their own distribution by replacing this one file. Delete it for a plain, unbranded
  AiCIV. A trial birth refuses to start without an `https://` payment link, from this file or `TRIAL_PAYMENT_URL`.

### Partner notifications: off by default

**Reseller notifications come from True Bearing, not from the AiCIV** (Corey 2026-09-27). Not every AiCIV has an
email inbox, and True Bearing already emails the reseller about billing and trial events from its own side. So
`notify_emails` ships empty, and with it empty:

- the AiCIV sends nothing, queues nothing (`memories/partner-notifications/` is never created), and shows no
  "email not provisioned / queued" status to its human or operator;
- the watchdog skips its partner checks, and `apply_trial_profile.py convert` says nothing about the partner;
- client-site business alerts (lead, order, booking, affiliate application) go to the client owner only.

The code path is kept, dormant: `tools/partner_notify.py` (`send | sweep | flush | tick | status | enabled`) and
skill `.claude/skills/partner-notifications/SKILL.md`. An operator can switch it on for one civ by putting addresses
in `notify_emails` or setting `PARTNER_NOTIFY_EMAILS`; it then needs an AgentMail inbox on that civ (see the skill).

---

## Provisioning

### Paid birth

Stamp the template into the new civ's home and fill the usual template variables (`variables.template.json`).
No trial step runs, so no trial file exists.

### Trial birth: filling the router seams

The trial reaches MiniMax-M3 through an Anthropic-wire-compatible router. The template never contains the router
address or key. Provisioning supplies them as environment variables for one command:

```bash
export M3_ROUTER_BASE_URL="<router base URL for this tenant>"      # required, never committed
export M3_ROUTER_KEY_FILE="<path to this tenant's router key>"     # required (or M3_ROUTER_KEY)
# optional:
#   M3_MODEL_ID        default MiniMax-M3
#   TRIAL_PAYMENT_URL  default payment_url from config/partner.json
#   TRIAL_START        default now (UTC)
export TRIAL_OPERATOR_COPY="/etc/aiciv/trial.json"   # canonical; outside the civ tree
sudo -E python3 tools/apply_trial_profile.py apply --root "$CIV_ROOT"   # as root, so that copy is root-owned
# then start the portal with TRIAL_CONFIG_PATH=/etc/aiciv/trial.json in its environment
```

The portal must read the **operator copy**, not the civ's `config/trial.json`, because the AiCIV can write its own
tree (see `profiles/trial-m3/README.md`). `apply` also records `TRIAL_CONFIG_PATH` in `.claude/settings.json`, so the
AiCIV's own hook reads the same copy. `apply` refuses (exit 2) if any seam is empty, so a trial can never quietly fall back to another model. It then:

- copies the key to `config/lifeboat/router_key.txt` (mode 0600, gitignored) and records the endpoint;
- points every model setting at M3, sets the router as the base URL with a key helper, and removes other model
  credentials;
- sets every specialist's model to `inherit`, and locks the model profile so it cannot be switched back from inside;
- writes `config/trial.json` and the trial block in `.claude/CLAUDE.md`, and installs the trial hook.

It finishes by running `check`, which must end with `NO FRONTIER MODEL REACHABLE`. Re-running it is safe, and the
trial clock is kept.

**Required on the router side (outside this repository).** Anyone with shell access can edit files inside a
container, so the router is the real boundary for a trial:

1. one key per trial civ, sized for the full organization;
2. the key only forwards MiniMax model ids;
3. the key expires (or throttles to a trickle) at `expires_at`, and is rotated on conversion;
4. no other model credentials are provisioned into a trial container;
5. web search and fetch work through the router, or research is marked "unverified" rather than guessed.

Full detail is in `profiles/trial-m3/README.md`.

### Conversion

```bash
sudo -E python3 tools/apply_trial_profile.py convert --root "$CIV_ROOT"                    # ungate now
sudo -E python3 tools/apply_trial_profile.py convert --root "$CIV_ROOT" --restore-models   # and return to paid routing
```

`convert` flips the operator copy recorded at birth (or `--operator-copy PATH`) and the civ copy.

Conversion is a manual operator step for now. The planned follow-up is a Stripe `checkout.session.completed`
webhook on the payment link that calls `convert` for the matching civ.

---

## Watchdog after a container restart

Birth starts `tools/watchdog.sh` in a detached tmux session named `watchdog`. A container restart kills it, and
nothing in the container brings it back. The AiCIV's own session start does: the SessionStart hook runs
`tools/ensure_watchdog.py`, which starts the watchdog the same way when it is not running and does nothing when
it is. It never starts a second copy, never blocks the session, and logs one line to `logs/watchdog.log` when it
acts. It only acts in the civ root (`/home/aiciv/civ`); `AICIV_ENSURE_WATCHDOG=0` turns it off. No fleet
startup hook is needed.

When the watchdog restarts the portal (`start.sh`), it passes `PORTAL_PUBLIC_URL` and `TRIAL_CONFIG_PATH`
through. A value missing from its own environment is read from `~/.env`, then `<civ>/.env`, and
`TRIAL_CONFIG_PATH` finally from `.claude/settings.json` `env`.

---

## Checks

```bash
python3 tools/test_trial_profile.py                 # trial + partner regression suite (scratch births, no network)
python3 tools/test_partner_notify.py                # partner notifications: off by default = silent; switched on = every event once (stub)
apps/.venv/bin/python tools/test_delivery_engine.py # delivery engine (owner-only alerts by default; partner copy when switched on)
python3 tools/test_ensure_watchdog.py               # watchdog self-heal after a container restart + portal env passthrough
python3 tools/apply_trial_profile.py check          # on a trial civ: no frontier model reachable
python3 tools/trial_state.py status                 # the /api/trial JSON (not a trial -> "trial": false)
```

Delivery-engine checks: `apps/client-starter/preflight.sh` (pinned dependencies, audit, compile), then the
V1-V19 verification list in `.claude/skills/client-onboarding/SKILL.md`, Phase 4.

## Layout

| Path | What |
|---|---|
| `.claude/CLAUDE.md` | the newborn's constitution, with its self-removing birth gates at the top |
| `.claude/skills/` | skills the AiCIV loads (client-onboarding, m3-trial-mode, identity-interview, and more) |
| `apps/client-starter/` | the delivery engine scaffold |
| `profiles/trial-m3/` | the trial profile |
| `config/partner.json` | reseller brand, reseller name, payment link, partner notification addresses (empty = off, the default) |
| `tools/` | provisioning and state tools (`apply_trial_profile.py`, `trial_state.py`, `partner_profile.py`, ...) |
| `workflows/` | multi-mind workflows, including the trial's build, verify, and ship loop |
