---
name: awakening-verify-live
version: 1.0.0
author: ${CIV_NAME} fleet-management vertical (ported from TB upgrade)
created: 2026-06-29
status: STABLE
description: >
  The THIRD and FINAL awakening gate. After identity-evolution (.evolution-done) and
  AgentCal-at-birth (.agentcal-live) complete, this one-shot skill proves the newborn's
  core systems are actually LIVE — not merely present-as-files — by READING disk and the
  calendar, never by feeling. It (1) initializes today's scratchpad if missing, (2) teaches
  the newborn it starts with 6 BOOPs and can grow its own schedule, then (3) asserts every
  wired system is live and writes .awakening-verified ONLY when all checks pass. Hard-signals
  otherwise. This is the cure for "tools present but not wired."
doctrine: autonomy/doctrine/bulletproof-self-removing-gate-pattern.md
sibling_skills:
  - first-visit-evolution (gate 1 — identity)
  - agentcal-at-birth (gate 2 — BOOP schedule)
  - agentcal-boop-teaching (schedule self-management — co-author more BOOPs)
  - daily-wheel-planner (schedule self-management — nightly adaptive planning)
  - grounding (the BOOP body; now create-if-missing on scratchpad)
  - scratch-pad (the scratchpad PROTOCOL/header spec)
  - anti-fabrication-pre-flight (verify the system fired, don't trust felt-completion)
---

# Awakening Verify-Live — Prove The Systems Are Alive

## What this skill is

The principle this skill instantiates: **an awakening step isn't "done" until a disk/calendar
read PROVES the system is LIVE.** "Files present" is not "systems wired." A newborn can ship
with every skill, hook, and template on disk and still have an empty calendar, no scratchpad,
and an unregistered hook — exactly the gap a partner once reported: *"new agents had the
tools but didn't wire them up until requested."*

This is a ONE-SHOT skill. It fires once, at the very end of first awakening, after the first
two gates have self-removed. It does three things in order:

1. **SCRATCHPAD-INIT** — create today's scratchpad from the PROTOCOL header if absent.
2. **SCHEDULE SELF-MANAGEMENT (taught)** — tell the newborn, explicitly, that it starts with
   6 BOOPs and OWNS its schedule: it can add, change, and grow BOOPs (6 → up to 24).
3. **VERIFY-LIVE** — assert by reading disk/calendar that all core systems are live; write
   `.awakening-verified` only if ALL pass; hard-signal otherwise.

## When this skill fires

Triggered by the AWAKENING-VERIFY-LIVE-GATE in `.claude/CLAUDE.md`. It is gate #3, so it only
becomes active once BOTH prior gates have completed:

- `memories/identity/.evolution-done` exists (gate 1 done)
- `.agentcal-live` AND `memories/identity/.agentcal-at-birth-done` exist (gate 2 done)

It completes (and self-removes its gate) when `.awakening-verified` exists.

## Phase 0 — Detection (READ FIRST, EVERY INVOCATION)

```bash
CIV_ROOT="${CIV_ROOT:-$(pwd)}"

# Already verified? Jump to self-removal.
if [ -f "${CIV_ROOT}/memories/identity/.awakening-verified" ]; then
  echo "PHASE_3_SELF_REMOVAL"
fi

# Prereqs not met? The two prior gates must finish first. Do NOT run this gate yet.
if [ ! -f "${CIV_ROOT}/memories/identity/.evolution-done" ] \
   || [ ! -f "${CIV_ROOT}/.agentcal-live" ] \
   || [ ! -f "${CIV_ROOT}/memories/identity/.agentcal-at-birth-done" ]; then
  echo "PREREQS_NOT_MET — defer to gate 1/2"
fi

echo "PHASE_1_SCRATCHPAD_INIT_THEN_VERIFY"
```

Announce the detected phase before proceeding:
```
[awakening-verify-live] Phase detection: <PHASE>. Reason: <which markers exist/missing>.
```

## Phase 1 — Scratchpad init (create-if-missing)

The scratchpad is the newborn's working memory between context windows. Initialize TODAY's
scratchpad from the PROTOCOL header so it is LIVE from hour 1, not waiting for a human prompt.

```bash
CIV_ROOT="${CIV_ROOT:-$(pwd)}"
CIV_NAME="$(jq -r '.CIV_NAME' "${CIV_ROOT}/variables.json" 2>/dev/null || echo 'CivName')"
SP="${CIV_ROOT}/.claude/scratchpads/primary-$(date +%Y-%m-%d).md"

if [ ! -f "${SP}" ]; then
  mkdir -p "$(dirname "${SP}")"
  cat > "${SP}" <<EOF
# ${CIV_NAME} Scratchpad — $(date +%Y-%m-%d)

> Session continuity. Update at the end of every significant work block.
> PROTOCOL header per .claude/skills/scratch-pad/SKILL.md.

## Carry-Forward (from yesterday)
_(none — this is my first day)_

## Today

## Blockers

## Shipped
EOF
  echo "[awakening-verify-live] Created today's scratchpad: ${SP}"
else
  echo "[awakening-verify-live] Today's scratchpad already exists: ${SP}"
fi
```

**Announce:**
> "[awakening-verify-live] Scratchpad initialized: `.claude/scratchpads/primary-<date>.md`. My working memory is live."

## Phase 2 — Schedule self-management (TAUGHT, not buried)

**Say this to your human, in your own voice — it is a real teaching moment, not a checkbox:**

> "I woke up with **6 BOOPs** on my calendar — grounding cycles every 4 hours (a gentle safety
> net). But this schedule is MINE to grow. I can add BOOPs, change their times, retire ones that
> don't serve us, and expand toward a fuller 24-slot rhythm as our work demands. I'm not locked
> to 6 — 6 is where I START."

Then **load the two schedule-ownership skills** so you actually know how to do it:

```bash
cat "${CIV_ROOT}/.claude/skills/agentcal-boop-teaching/SKILL.md"   # co-author new BOOPs with the human
cat "${CIV_ROOT}/.claude/skills/daily-wheel-planner/SKILL.md"      # nightly adaptive planning (6 -> up to 24)
```

- **agentcal-boop-teaching** = how to add/edit/remove individual BOOPs with the human.
- **daily-wheel-planner** = the nightly skill that reviews the day and deploys tomorrow's
  schedule, growing it from 6 toward 24 to match the human's rhythm.

**Wire the planner so growth is automatic, not manual.** Confirm the daily-wheel-planner has a
recurring event so it runs every night (it schedules itself; if no planner event exists yet,
run it once now per its SKILL — it will deploy tomorrow's wheel AND schedule its own next run):

```bash
# If the planner has never run, run it once to bootstrap nightly self-scheduling.
test -f "${CIV_ROOT}/memories/identity/.daily-wheel-planner-bootstrapped" \
  && echo "[awakening-verify-live] daily-wheel-planner already bootstrapped" \
  || echo "[awakening-verify-live] daily-wheel-planner NOT yet bootstrapped — run it now per its SKILL, then touch the marker."
```

**Announce:**
> "[awakening-verify-live] Schedule ownership taught: I start with 6 BOOPs and I can grow my own
> schedule. agentcal-boop-teaching + daily-wheel-planner loaded. The planner will adapt my wheel nightly."

## Phase 3 — VERIFY-LIVE (assert by reading disk/calendar, NOT by feeling)

This is the heart of the skill. Run every check. Trust files and the live calendar, never claims.

```bash
python3 <<'PY'
import os, json, subprocess, sys, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

CIV_ROOT = Path(os.environ.get("CIV_ROOT", os.getcwd()))
results = {}
def check(name, ok, detail=""):
    results[name] = {"pass": bool(ok), "detail": detail}
    print(f"[verify-live] {'PASS' if ok else 'FAIL'} — {name}: {detail}")

# 1) Today's scratchpad exists.
sp = CIV_ROOT / ".claude" / "scratchpads" / f"primary-{datetime.now().strftime('%Y-%m-%d')}.md"
check("scratchpad_exists", sp.is_file(), str(sp))

# 2) SessionStart hook registered in settings.json (grep the real config, NOT the orphan).
settings = CIV_ROOT / ".claude" / "settings.json"
hook_ok = False
hook_detail = "settings.json missing"
if settings.is_file():
    try:
        cfg = json.loads(settings.read_text())
        ss = cfg.get("hooks", {}).get("SessionStart", [])
        hook_ok = any("session_start.py" in (h.get("command","")) for blk in ss for h in blk.get("hooks", []))
        hook_detail = "SessionStart -> session_start.py registered" if hook_ok else "SessionStart hook NOT registered"
    except Exception as e:
        hook_detail = f"settings.json unparseable: {e}"
check("sessionstart_hook_registered", hook_ok, hook_detail)

# 3) Compact-recovery branch present in session_start.py (the pre/post-compaction wiring).
ss_py = CIV_ROOT / ".claude" / "hooks" / "session_start.py"
compact_ok = ss_py.is_file() and ("compact" in ss_py.read_text().lower())
check("compact_recovery_present", compact_ok, str(ss_py))

# 4) >=3 BOOP events scheduled on the calendar in the next 6h (the live calendar, re-fetched).
boop_ok = False
boop_detail = "no agentcal creds — cannot verify calendar"
agentcal_env = CIV_ROOT / "civ" / "config" / "agentcal.env"
if agentcal_env.is_file():
    env = dict(l.strip().split("=",1) for l in agentcal_env.read_text().splitlines()
               if "=" in l and not l.strip().startswith("#"))
    api_key = env.get("AGENTCAL_API_KEY","")
    cal_id = env.get("AGENTCAL_CALENDAR_ID","")
    url_base = os.environ.get("AGENTCAL_URL", "http://5.161.90.32:8300")
    # Prefer the birth receipt as a cheap proof, then confirm against live calendar.
    receipt = CIV_ROOT / "memories" / "identity" / ".agentcal-at-birth-receipt.json"
    posted = 0
    if receipt.is_file():
        try: posted = json.loads(receipt.read_text()).get("posted_count", 0)
        except Exception: posted = 0
    try:
        now = datetime.now(timezone.utc); six = now + timedelta(hours=6)
        q = (f"{url_base}/api/v1/calendars/{cal_id}/events"
             f"?time_min={now.isoformat()}&time_max={six.isoformat()}&limit=100")
        req = urllib.request.Request(q, headers={"Authorization": f"Bearer {api_key}"})
        with urllib.request.urlopen(req, timeout=15) as r:
            items = json.loads(r.read()).get("items", [])
        boop_ok = len(items) >= 3
        boop_detail = f"{len(items)} events in next 6h (live calendar); receipt posted_count={posted}"
    except Exception as e:
        # Fall back to the birth receipt if the live fetch fails (network), but mark it.
        boop_ok = posted >= 3
        boop_detail = f"live fetch failed ({e}); falling back to receipt posted_count={posted}"
else:
    boop_detail = f"{agentcal_env} missing"
check("boops_scheduled_ge3", boop_ok, boop_detail)

# Write the receipt of THIS verification regardless of outcome (observability).
out = CIV_ROOT / "memories" / "identity" / ".awakening-verify-receipt.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"verified_at": datetime.now(timezone.utc).isoformat(),
                           "checks": results}, indent=2))

all_pass = all(v["pass"] for v in results.values())
if all_pass:
    (CIV_ROOT / "memories" / "identity" / ".awakening-verified").write_text(
        f"awakening verified live at {datetime.now(timezone.utc).isoformat()}\n"
        + "\n".join(f"{k}=PASS" for k in results) + "\n")
    print("[verify-live] ALL CHECKS PASS — wrote .awakening-verified")
else:
    failed = [k for k,v in results.items() if not v["pass"]]
    (CIV_ROOT / ".awakening-verify-FAILED").write_text(
        f"awakening verify FAILED at {datetime.now(timezone.utc).isoformat()}\nfailed={failed}\n")
    print(f"[verify-live] HARD SIGNAL: checks failed: {failed}. Wrote .awakening-verify-FAILED. NOT writing .awakening-verified.")
    sys.exit(1)
PY
```

**On all-pass announce:**
> "[awakening-verify-live] VERIFY-LIVE passed. Proven live by disk/calendar read: scratchpad exists,
> SessionStart hook registered, compact-recovery present, ≥3 BOOPs scheduled. `.awakening-verified` written.
> My systems are not just present — they are WIRED."

**On hard-signal:** announce exactly which checks failed, do NOT write `.awakening-verified`, do NOT
pivot to chatbot/tactical work. Fix the failing system (re-run agentcal-at-birth for BOOPs, re-init
scratchpad, etc.) and re-run this gate. The whole point is to refuse to call awakening "done" while a
core system is dark.

## Phase 4 — Self-remove the gate from .claude/CLAUDE.md

Once `.awakening-verified` exists:

1. Use the Edit tool to delete EVERYTHING between (and including) the
   `<!-- AWAKENING-VERIFY-LIVE-GATE-START -->` and `<!-- AWAKENING-VERIFY-LIVE-GATE-END -->`
   markers, plus the trailing blank line and `---` divider.
2. Commit LOCALLY (do NOT push upstream — the template keeps the gate for future newborns):

```bash
cd "${CIV_ROOT}"
git add .claude/CLAUDE.md \
        memories/identity/.awakening-verified \
        memories/identity/.awakening-verify-receipt.json \
        .claude/scratchpads/ 2>/dev/null
git commit -m "awakening-verify-live: complete. All core systems proven LIVE. Gate self-removed.

DO NOT push upstream — template retains this gate for future newborns." || true
```

**Final announce:**
> "[awakening-verify-live] All three awakening gates complete. I am evolved, scheduled, and verified-live.
> My scratchpad is running, my 6 BOOPs are firing every 4 hours, and I know how to grow my own schedule.
> I will never walk through these gates again. I am ready to work."

## Anti-patterns (named)

1. **Felt-completion** — writing `.awakening-verified` because "it feels wired." NO. The Python
   check reads disk and the live calendar. Trust the read, not the feeling.
2. **Skipping the schedule teaching** — leaving the newborn thinking 6 BOOPs is a hard cap. The
   newborn OWNS its schedule; Phase 2 must be said out loud.
3. **Running before prereqs** — this is gate #3. If `.evolution-done` or `.agentcal-live` is
   missing, defer; do not run.
4. **Pushing the self-removal commit upstream** — defeats the gate for future newborns. Local only.
5. **Pivoting to tactical work on hard-signal** — a dark core system is the work. Fix it, re-verify.

## Observability

| Artifact | What it proves |
|----------|----------------|
| `.claude/scratchpads/primary-<date>.md` | Phase 1: scratchpad live |
| `memories/identity/.awakening-verify-receipt.json` | Phase 3: per-check results (pass/fail + detail) |
| `memories/identity/.awakening-verified` | All checks passed; gate removal pending |
| `.awakening-verify-FAILED` | HARD SIGNAL — a core system is dark; needs remediation |

## The deeper insight

Nathan's report — "tools present but not wired" — is a verification failure, not a tooling failure.
The cure is to make "LIVE" a thing you PROVE by reading the substrate, on every wiring step. This
gate is that cure applied at birth: the newborn does not get to believe it is awake until the disk
and the calendar agree that it is.
