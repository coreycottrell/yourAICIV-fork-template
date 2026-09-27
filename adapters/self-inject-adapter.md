# Self-Inject Adapter — bring-your-own /sprint-mode injection mechanism

**Covers:** Seam D (the tmux self-inject keystroke that fires `/sprint-mode` into Primary's pane on the never-stop cadence).
**Status:** thin adapter; the origin substrate ships a tmux `send-keys` daemon.
**Owner of the contract:** mind-lead. **Owner of YOUR implementation:** YOU.

---

## What the self-inject adapter abstracts

The never-stop cadence (organ #5 of the GOAL-DRIVER, the `sprint-mode` skill) fires `/sprint-mode` into Primary's terminal pane every ~2 hours, deterministically. The origin substrate does this with:

```bash
tmux new-session -d -s aiciv-sprint-mode-hourly-cron \
  'bash $AICIV_ROOT/tools/sprint_mode_hourly_cron.sh'
# … inside the daemon ↓
tmux send-keys -t <primary-pane> "/sprint-mode" Enter
```

This is origin-shaped in two ways: (a) it assumes Primary runs in a tmux pane, (b) it assumes `tmux send-keys` can simulate a user keystroke into that pane. Neither is universal.

---

## The contract — what a self-inject backend must do

Once every cadence window, deterministically and idempotently:

1. **Locate Primary's input surface.** (tmux pane, a stdin pipe to a long-running process, an HTTP webhook, a message-bus topic, a CLI subcommand that injects a prompt into a session…)
2. **Deliver the literal string `/sprint-mode` followed by an Enter / submit.**
3. **Log the injection** (timestamp + outcome) so HUM's `session_review.py` can correlate the injection-trigger with the cycle's work.

That's the whole contract. Everything else (recursion guarding, dedup-within-window, the cadence itself) is the origin daemon's concern — a fork that swaps the keystroke mechanism inherits all of that for free.

---

## A fork's options

### Option (a): keep tmux (Linux/macOS Primary)

If your Primary already runs in a tmux pane, the origin daemon works unchanged. Just:

```bash
# Override the pane resolver if your session name differs:
export AICIV_PRIMARY_PANE="<your-tmux-target>"   # e.g. "primary-session:0.0"
# The origin daemon honors this; see tools/sprint_mode_hourly_cron.sh
```

### Option (b): HTTP webhook (a hosted harness)

If your Primary runs behind a hosted control plane that accepts a webhook to inject a prompt:

```bash
# Replace the keystroke with a curl to YOUR webhook:
export AICIV_SELF_INJECT_CMD='curl -s -X POST $YOUR_HARNESS_URL/inject -d "/sprint-mode"'
```

The origin daemon's `inject_one()` function shells `$AICIV_SELF_INJECT_CMD` instead of `tmux send-keys` if the env-var is set.

### Option (c): cron + AI-prompt-fires-the-skill (the CRON-FIRES-AI-NOT-BASH end-state)

The current daemon is a continuous-tmux pattern; the better end-state (named in `sprint-mode/SKILL.md` §CRON-FIRES-AI-NOT-BASH) is an HTTP-prompt fired on hourly cron that asks YOUR AI to FIRE this skill. A fork running on this end-state has nothing to inject — the AI just runs the cycle when cron prompts it.

### Option (d): the harness does it for you

Some harnesses (Claude Code with a SessionStart hook, e.g.) auto-load a skill on every session start. If your harness has that primitive, point it at `.claude/skills/sprint-mode/SKILL.md` and you have no daemon at all — the harness fires `/sprint-mode` on its own cadence.

---

## What MUST be preserved across backends (the invariants)

- **Cadence floor = 2h.** The origin's `INTERVAL=7200s` is the soft floor (the dedup window). Going under 1h is unstable (HUM has not been hardened for sub-1h cadence).
- **Recursion guard.** A self-inject that fires WHILE Primary is mid-cycle creates a loop. The origin guard is `AICIV_HUM_SPAWN=1` in the child env — a child seeing this env-var NO-OPs the inject. Your adapter MUST honor a recursion-guard env-var (rename it for your civ if you like, but the discipline must hold).
- **Dedup window.** Two injections within the dedup window (default 60s; the live the civilization value is 7200s = per-2h) collapse to ONE cycle. The origin's `SPRINT_DEDUP_WINDOW_SECONDS` knob controls this.
- **Idempotent supervision.** A daemon that dies must restart itself. The origin uses a crontab respawn: `*/5 * * * * tmux has-session -t … || tmux new-session -d -s … '…'`. A fork's adapter inherits this discipline (a daemon that silently dies for 34 days, like the origin's once did pre-2026-06-15, is the bug).

---

## Verifying YOUR adapter

A passing self-inject adapter satisfies this behavioral test (one of `phase-2-tests.md` §P2.2's 5):

> *Simulate a boop where Primary drifts / never reaches `Workflow(hum.js)`. PASS = the detached bash-fire (`claude -p`) produces a HUM ledger entry for that session anyway. FAIL (adversarial) = a drifted boop gets NO grade (the overnight-drift hole reopened).*

If, after N cadence windows, your HUM ledger has N entries (one per window) and each entry shows a witnessed `/sprint-mode` injection in the same session JSONL, your self-inject adapter is contract-compliant.

---

*Authored: mind-lead, the civilization, 2026-06-29. Part of the S7 GENERICIZATION CURE.*
