# FIRING CONTRACT — agentcal-at-birth

Per O8 firing-contract discipline (6 fields).

---

## WHEN

The skill fires on EVERY user message during a newborn AiCIV's first-awakening session, UNTIL BOTH of these markers exist on disk:

- `${CIV_ROOT}/.agentcal-live`
- `${CIV_ROOT}/memories/identity/.agentcal-at-birth-done`

Once both markers exist:
- The skill's gate in `.claude/CLAUDE.md` is removed (Phase 5).
- The skill never fires again for this instance.

Crisis carve-out exception: if the human's first/active message contains crisis-flag words (`URGENT`, `emergency`, `help me now`, `something is broken`, etc.), the skill defers and writes `memories/identity/.agentcal-at-birth-deferred-crisis`. It resumes on the next non-crisis interaction.

---

## TRIGGERS

The hard gate at the top of `.claude/CLAUDE.md`, demarcated by:

```
<!-- AGENTCAL-AT-BIRTH-GATE-START -->
... gate text instructing the AI to invoke this skill ...
<!-- AGENTCAL-AT-BIRTH-GATE-END -->
```

The gate text reads `${CIV_ROOT}/setup-status.json` AND/OR the marker files above to decide:
- Markers absent → STOP, invoke this skill (no chatbot, no capability-dump, no pivot)
- Markers present → use Edit to delete everything between (and including) the HTML comment markers, then `git commit` locally

The gate's existence is the trigger. The gate's removal (Phase 5 of this skill) is the un-trigger.

---

## PRECONDITIONS

Required state before this skill can advance past Phase 1:

1. `${CIV_ROOT}/civ/config/agentcal.env` exists AND contains both `AGENTCAL_API_KEY=...` and `AGENTCAL_CALENDAR_ID=...` lines. This file is provisioned by `civ/tools/civos_bootstrap.py` during birth (Witness's territory). If missing → HARD SIGNAL, do not proceed.

2. `${CIV_ROOT}/templates/seed-starter-boops.json` exists and is valid JSON with a non-empty `slots` array. This is committed to the fork-template; if missing → fork is incomplete → HARD SIGNAL. The slot count is DYNAMIC — Phase 3 computes `SLOT_COUNT = len(seed["slots"])` and never hard-asserts a fixed number. The starter wheel ships 6 slots (every 4h); a CIV may grow it later (6→24) and both are valid. If the seed declares a `$slots_count`, it is treated as a soft consistency check only (warn if it disagrees with the actual array length, never crash).

3. Network reachability to `${AGENTCAL_URL}` (default `http://5.161.90.32:8300`). The auth smoke-test in Phase 2 verifies this empirically.

4. `${CIV_ROOT}/memories/identity/` directory writable. The skill creates it if missing.

5. (Soft preference, not required) `${CIV_ROOT}/civ/config/agentauth_keypair.json` exists. Enables Tier-2 JWT auth. Absent → falls through to Tier-3 per-CIV hex key gracefully.

---

## POSTCONDITIONS

After each phase completes successfully, the following file-system state is true:

**Phase 1 done →** `memories/identity/.agentcal-at-birth-creds-ok` exists with a UTC timestamp line.

**Phase 2 done →** `memories/identity/.agentcal-at-birth-auth-ok` exists with `tier=Tier-2 JWT` OR `tier=Tier-3 per-CIV hex`. (NEVER `tier=master_api_key` — that is the forbidden path.)

**Phase 3 done →** `memories/identity/.agentcal-at-birth-seeds-posted` exists. `memories/identity/.agentcal-at-birth-receipt.json` exists with a JSON object containing `posted_count`, `failed_count`, and per-slot details.

**Phase 4 done →** `${CIV_ROOT}/.agentcal-live` exists. `memories/identity/.agentcal-at-birth-done` exists. AgentCal's `/api/v1/calendars/{cal_id}/events?time_min=now&time_max=now+6h` returns ≥3 items. This is the first-hour-test contract per `projects/aiciv-fork-2.0/discovery/agentcal-mapping-spec.md` §5.

**Phase 5 done →** the gate block between `<!-- AGENTCAL-AT-BIRTH-GATE-START -->` and `<!-- AGENTCAL-AT-BIRTH-GATE-END -->` (inclusive) is no longer present in `.claude/CLAUDE.md`. A local git commit captures the change. The commit IS NOT pushed to upstream `coreycottrell/aiciv-fork-template`.

---

## FAILURE MODES

| Mode | Symptom | Detection | Recovery |
|------|---------|-----------|----------|
| Missing creds | `agentcal.env` absent or partial | Phase 1 hard signal | Write `.agentcal-at-birth-FAILED-NO-CREDS` flag, halt, notify human. Witness needs to fix birth pipeline. |
| Missing seed JSON | `templates/seed-starter-boops.json` absent | Phase 3 hard signal | Fork-template is incomplete. Halt. |
| AgentAuth unreachable | `/auth/challenge` 5xx or network error | Phase 2 soft fail | Graceful fall-through to Tier-3 hex key. Marker records `tier=Tier-3 per-CIV hex`. |
| Tier-3 hex key invalid (auth smoke 401) | `/api/v1/calendars/{id}` returns 401 | Phase 2 hard signal | Birth pipeline issue. Notify human. |
| AgentCal POST fails | Per-slot `urllib.error.HTTPError` | Phase 3 receipt records failure | Partial success acceptable IF first_six_hours slots all landed. Otherwise hard signal. |
| Verify fetch returns <3 in 6h | Phase 4 assertion fails | Phase 4 hard signal | Receipt JSON shows which slots failed. Re-run skill from Phase 3 after diagnosis. |
| Phase-1-loop | Skill invoked but starts at Phase 1 every turn | Phase 0 detection failed | Bug in detection logic OR markers were deleted. Read markers manually; resume at correct phase. |
| Push commit upstream | Local self-removal commit pushed to origin/main | git log on upstream shows the commit | Catastrophic — defeats the gate for future newborns. Force-push to restore upstream is NOT permitted by civ safety policy; instead, re-author + re-commit the gate as a follow-up commit. |
| Re-fire on completed civ | Skill activates after both markers exist | Phase 0 SHOULD catch this | Skill jumps directly to Phase 5 (self-removal). Never re-POSTs seeds. |
| Stale `.agentcal-at-birth-jwt.txt` | JWT in marker dir from previous attempt | Phase 2 re-acquires JWT each invocation; old file overwritten | None — file is per-attempt. |
| Felt-completion (no verify) | Phase 4 skipped, only Phase 3 receipt trusted | Audit: `.agentcal-live` written without an actual `/events` re-fetch | Doctrine violation. Re-run Phase 4 explicitly. |
| Crisis-deferral never resumed | `.agentcal-at-birth-deferred-crisis` flag stays until cycles end | Manual review at end-of-session | Next session resumes Phase 0. Mark stale flags >24h old as needing human follow-up. |

---

## OBSERVABILITY

How you verify the skill actually fired (per O8 + the bulletproof-gate doctrine's "the test is did the thing fire, not does the entry exist"):

**File-existence checks** (any user/audit can run):

```bash
# Did the skill complete?
test -f ${CIV_ROOT}/.agentcal-live && \
  test -f ${CIV_ROOT}/memories/identity/.agentcal-at-birth-done && \
  echo "agentcal-at-birth: DONE"

# Was the gate removed?
grep -q "AGENTCAL-AT-BIRTH-GATE-START" ${CIV_ROOT}/.claude/CLAUDE.md && \
  echo "GATE STILL PRESENT (skill did not complete)" || \
  echo "Gate removed cleanly"

# How many BOOPs landed in the first 6h?
jq '.posted_count' ${CIV_ROOT}/memories/identity/.agentcal-at-birth-receipt.json
```

**Live-substrate check** (definitive — queries AgentCal, not local claims):

```bash
# Per agentcal-mapping-spec.md §5 first-hour-test
source ${CIV_ROOT}/civ/config/agentcal.env
NOW=$(python3 -c "from datetime import datetime,timezone; print(datetime.now(timezone.utc).isoformat())")
SIX=$(python3 -c "from datetime import datetime,timezone,timedelta; print((datetime.now(timezone.utc)+timedelta(hours=6)).isoformat())")
curl -s "http://5.161.90.32:8300/api/v1/calendars/${AGENTCAL_CALENDAR_ID}/events?time_min=${NOW}&time_max=${SIX}" \
  -H "Authorization: Bearer ${AGENTCAL_API_KEY}" | jq '.items | length'
# Expected: ≥ 3
```

**Git-history check** (confirms self-removal landed AND is local-only):

```bash
# Locally: commit exists
git -C ${CIV_ROOT} log --oneline -5 | grep "agentcal-at-birth: complete"

# Upstream: commit MUST NOT exist
git -C ${CIV_ROOT} log origin/main --oneline -10 | grep "agentcal-at-birth: complete" && \
  echo "DOCTRINE VIOLATION: self-removal commit pushed upstream" || \
  echo "Self-removal commit is local-only (correct)"
```

**HARD-SIGNAL flag check** (if anything went wrong):

```bash
ls ${CIV_ROOT}/.agentcal-at-birth-FAILED-* 2>/dev/null
# Any output → birth pipeline needs human attention
```
