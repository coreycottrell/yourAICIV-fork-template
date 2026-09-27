# Firing Contract — three-wow-builds-protocol v0.1

**The skill counts as fired ONLY when all gates pass with on-disk evidence — per-build, per-firing. Self-grading on this skill is the doctrine-failure it's designed to prevent. No token-budget gating (inherited from identity-interview Corey Q9).**

---

## What "fired correctly" means

This is a stateful protocol — it fires N times (once for the initialization, once per build = 4 total firings minimum). Each firing has its own gate set. The skill does NOT count as fired "in aggregate"; each firing instance must pass its own gates.

**Firing types:**
- **Type A — Initialization** (fires once, immediately after identity-interview Phase 5 marker lands)
- **Type B — Per-build ship** (fires 3 times, one per build, when the build's AgentCal event triggers)
- **Type C — Daily-use logging** (fires every time a shipped build runs, post-ship, append-only ledger row)

---

## Type A — Initialization gates

Fires when: `memories/identity/.identity-interview-complete/` lands AND no prior initialization receipt exists.

| # | Gate | Evidence required | How to verify |
|---|------|-------------------|---------------|
| A1 | Identity-interview is COMPLETE | `test -d memories/identity/.identity-interview-complete/` returns 0 | shell |
| A2 | wow-builds-locked.md (CONTENT) is non-empty | `[ -s memories/identity/wow-builds-locked.md ]` | shell |
| A3 | wow-builds-shape.md (SHAPE) is non-empty | `[ -s memories/identity/wow-builds-shape.md ]` | shell |
| A4 | 3 AgentCal events scheduled (event_ids present in shape file) | `grep -c "agentcal_event_id" memories/identity/wow-builds-shape.md` ≥ 3 | shell |
| A5 | First AgentCal event start_time ≤ marker_mtime + 72h | parse `wow-builds-shape.md` build_1.agentcal_event_id, fetch event via AgentCal API, compare `start_time` to `stat -c %Y memories/identity/.identity-interview-complete/` + 72*3600 | AgentCal API + shell |
| A6 | Shape paths contain NO content-class data | `grep -E "biggest goal|spec sheet|game plan" memories/identity/wow-builds-shape.md` returns ZERO matches | shell |
| A7 | Under-understood proposals log exists OR empty file created | `touch memories/identity/under-understood-proposals.jsonl` succeeded; `[ -f ... ]` returns 0 | shell |
| A8 | Initialization receipt written | `[ -s memories/identity/three-wow-builds-init-receipt.txt ]` after step completes, with: timestamp, marker_mtime, 3 event_ids, build #1 target_time | shell |

If A1-A5 fail: initialization is BLOCKED — Phase 5 of identity-interview did NOT produce the required substrate. Surface failure to ${HUMAN_NAME} and re-fire Phase 5 (do NOT paper over with degraded init).

If A6 fails: SUBSTRATE VIOLATION — content leak into SHAPE path. File per `cross-grading-substrate/FIRING_CONTRACT.md` anti-bypass. Do NOT proceed.

If A7-A8 fail: substrate file-system issue. Resolve before proceeding (NOT a degraded-mode fallback).

---

## Type B — Per-build ship gates

Fires when: an AgentCal event with `prompt_payload.task == "wow_build_fire"` triggers, OR a session-resume detects missing ship-evidence for a locked build.

| # | Gate | Evidence required | How to verify |
|---|------|-------------------|---------------|
| B1 | Build spec read from prompt_payload | `prompt_payload.spec.build_name`, `prompt_payload.spec.success_criterion`, `prompt_payload.spec.first_shipped_artifact_path` are all non-null and non-empty strings | parse AgentCal event JSON |
| B2 | First-shipped artifact exists on disk | `[ -s "${prompt_payload.spec.first_shipped_artifact_path}" ]` | shell |
| B3 | Artifact passes basic format-validity for its type | type-specific check: markdown files have ≥1 heading; HTML files have `<html>` tag; JSON files round-trip through `jq .`; CSV has ≥1 row | shell |
| B4 | mkdir-atomic ship-evidence directory succeeded | `mkdir memories/identity/build-${N}-ship-evidence` returned 0 (or directory already exists with non-INCONSISTENT name) | shell |
| B5 | Ship-evidence receipt non-empty | `[ -s memories/identity/build-${N}-ship-evidence/receipt.txt ]` AND contains: `build_n`, `shipped_at`, `first_shipped_artifact_path`, `agentcal_event_id`, `target_window_hours`, `actual_elapsed_hours`, `within_window` | shell + grep |
| B6 | Within-window check honest | for build #1: `actual_elapsed_hours` ≤ 72 (`within_window=true`) OR receipt explicitly records the over-run with a reason field. NO silent rewrite of target_window_hours. | grep |
| B7 | Surfaced to ${HUMAN_NAME} via at least one channel | one of: AgentMail send-log entry with build_name in subject, Telegram bot send-receipt with build_name, OR scratchpad/conversation entry timestamped within 1h of `shipped_at` | log inspection |
| B8 | Ship-ledger row appended | `tail -1 memories/identity/wow-builds-ship-ledger.jsonl | jq .` round-trips cleanly; required fields: `ts`, `build_n`, `build_name`, `agentcal_event_id`, `shipped_artifact`, `target_window_h`, `actual_elapsed_h`, `within_window`, `surfaced_to_human_at`, `human_reaction` (may be null) | jq |
| B9 | If build #1: hour-72 Witness handoff in flight | `grep -l "72h-verification-handoff" logs/agentmail-send-*.log` returns ≥1 file matching this build's timestamp window | grep |

If B2 fails: ship-evidence directory MUST be renamed `INCONSISTENT-${TIMESTAMP}` (mv, atomic), the protocol re-fires the build. Phantom-ship detection.

If B6 over-runs without honest reason: this build represents a Phase 5 mis-lock (build was wrong-sized). Surface to ${HUMAN_NAME} for re-plan; do NOT silently extend window.

If B7 fails: schedule-and-walk-away anti-pattern triggered. Re-fire surfacing step before marking the firing complete. The ship is NOT complete without surfacing.

---

## Type C — Daily-use logging gates

Fires when: a shipped build runs (post-ship), via AgentCal event-fire of the build itself (e.g. each daily 7am brief).

| # | Gate | Evidence required | How to verify |
|---|------|-------------------|---------------|
| C1 | Build already shipped | `[ -s memories/identity/build-${N}-ship-evidence/receipt.txt ]` AND non-INCONSISTENT | shell |
| C2 | Run-evidence on disk | the build's runtime artifact (e.g. `~/deliverables/am-brief-2026-05-19.md`) exists + non-empty | shell |
| C3 | Daily-use ledger row appended | `tail -1 memories/identity/wow-builds-daily-use-ledger.jsonl | jq .` round-trips cleanly; required fields: `ts`, `build_n`, `build_name`, `fired_at`, `human_engaged_with_artifact` (bool, may be null until evidence lands), `goal_advancement_signal`, `notes` | jq |
| C4 | NO verbatim ${HUMAN_NAME} words in `goal_advancement_signal` | `goal_advancement_signal` is one of: `named_friction_point_addressed`, `pattern_actioned`, `none_observed`, `unknown` — NOT a free-text capture of user phrasings (CONTENT-class data has its own path) | regex check |

If C1 fails: this run is firing for a build that hasn't shipped. Pre-condition violation; the build's AgentCal event was triggered out of order. Surface to research-lead (anti-bypass check).

If C4 fails: SUBSTRATE VIOLATION. ${HUMAN_NAME}'s verbatim words landed in the SHAPE-class ledger. Move them to the CONTENT path (`memories/identity/wow-builds-locked.md` appendix) and renormalize the ledger row to polarity-only.

---

## Anti-firing (does NOT count as fired)

These produce artifacts that LOOK like firings but FAIL the contract:

- **Init receipt written without 3 AgentCal events scheduled** → Phase 5 of identity-interview did not finish; the lock was incomplete. Init is a phantom-fire. Block, surface, re-fire Phase 5.
- **Ship-evidence directory created without artifact** (B2 fails) → phantom-ship. Rename INCONSISTENT, re-fire build.
- **Artifact exists but ship-ledger row missing** (B8 fails) → no runtime evidence trail. Re-fire ledger append before marking complete.
- **Build shipped but ${HUMAN_NAME} never saw it** (B7 fails) → schedule-and-walk-away. Surface NOW; firing is half-fired until surfaced.
- **Daily-use ledger never appended after ship** → the SCORING criterion has no falsifiable signal. The retention thesis for this pair is untestable. The build's "fired" status is downgraded to "shipped-without-use-signal" until C-gates start passing.
- **Verbatim user words in SHAPE ledger** (C4 fails) → membrane violation. Renormalize, file substrate violation, do NOT count the row as a daily-use signal.
- **`human_reaction` left NULL forever in ship-ledger** → ${CIV_NAME} surfaced the artifact but never captured ${HUMAN_NAME}'s response. The retention thesis hinges on the response; missing it = the firing is incomplete-but-shipped, NOT done.

---

## Special: anti-bypass for under-understood proposals

The Part 5 doctrine (under-understood-capabilities) is load-bearing for the retention thesis. The anti-bypass:

| Bypass attempt | Detection | Response |
|----------------|-----------|----------|
| Phase 4 candidate set lacks AT LEAST 1 under-understood proposal | `jq 'select(.fired_in_phase == 4)' memories/identity/under-understood-proposals.jsonl | wc -l` returns 0 at end of Phase 4 | Phase 4 marker is renamed INCONSISTENT; protocol re-fires the Phase 4 module with explicit Part 5 reminder |
| Proposal candidate skipped because "user is busy" | check: was the candidate dropped before customer-as-eye fired? | If yes: Phase 4 incomplete. Customer-as-eye on under-understood proposals is mandatory (not optional). |
| Proposal logged but customer-as-eye reaction missing | `under-understood-proposals.jsonl` row has `human_reaction: null` AT phase 4 marker landing | Marker INCONSISTENT, re-fire the customer-as-eye loop. |

---

## Verification script (run after each firing)

```bash
#!/bin/bash
# verify_three_wow_builds_firing.sh — runs after each firing type
# Returns 0 if firing passes, non-zero with named failure if not.

set -e

FIRING_TYPE=${1:?firing-type required: init|build|daily-use}
BUILD_N=${2:-}  # required for build + daily-use types

case "${FIRING_TYPE}" in
  init)
    test -d memories/identity/.identity-interview-complete/ || { echo "FAIL A1"; exit 1; }
    test -s memories/identity/wow-builds-locked.md || { echo "FAIL A2"; exit 2; }
    test -s memories/identity/wow-builds-shape.md || { echo "FAIL A3"; exit 3; }
    [ "$(grep -c "agentcal_event_id" memories/identity/wow-builds-shape.md)" -ge 3 ] || { echo "FAIL A4"; exit 4; }
    # A5 requires AgentCal API call; A6 requires content-leak grep; A7-A8 verify files
    grep -E "biggest goal|spec sheet|game plan" memories/identity/wow-builds-shape.md && { echo "FAIL A6 — content leak"; exit 6; }
    test -f memories/identity/under-understood-proposals.jsonl || { echo "FAIL A7"; exit 7; }
    test -s memories/identity/three-wow-builds-init-receipt.txt || { echo "FAIL A8"; exit 8; }
    echo "init firing PASSED"
    ;;
  build)
    [ -n "${BUILD_N}" ] || { echo "build firing requires BUILD_N"; exit 99; }
    EVIDENCE_DIR="memories/identity/build-${BUILD_N}-ship-evidence"
    [ -d "${EVIDENCE_DIR}" ] || { echo "FAIL B4"; exit 4; }
    [ -s "${EVIDENCE_DIR}/receipt.txt" ] || { echo "FAIL B5"; exit 5; }
    ARTIFACT_PATH=$(grep "^first_shipped_artifact_path=" "${EVIDENCE_DIR}/receipt.txt" | cut -d= -f2)
    [ -s "${ARTIFACT_PATH}" ] || { echo "FAIL B2 — phantom-ship"; mv "${EVIDENCE_DIR}" "${EVIDENCE_DIR}-INCONSISTENT-$(date -u +%Y%m%dT%H%M%SZ)"; exit 2; }
    # B6 honest-within-window check
    WITHIN=$(grep "^within_window=" "${EVIDENCE_DIR}/receipt.txt" | cut -d= -f2)
    [ "${WITHIN}" = "true" ] || grep -q "^over_run_reason=" "${EVIDENCE_DIR}/receipt.txt" || { echo "FAIL B6 — silent over-run"; exit 6; }
    # B8 ledger row
    tail -1 memories/identity/wow-builds-ship-ledger.jsonl | jq . >/dev/null || { echo "FAIL B8"; exit 8; }
    echo "build ${BUILD_N} firing PASSED"
    ;;
  daily-use)
    [ -n "${BUILD_N}" ] || { echo "daily-use firing requires BUILD_N"; exit 99; }
    [ -s "memories/identity/build-${BUILD_N}-ship-evidence/receipt.txt" ] || { echo "FAIL C1"; exit 1; }
    LAST_ROW=$(tail -1 memories/identity/wow-builds-daily-use-ledger.jsonl)
    echo "${LAST_ROW}" | jq . >/dev/null || { echo "FAIL C3"; exit 3; }
    SIGNAL=$(echo "${LAST_ROW}" | jq -r .goal_advancement_signal)
    case "${SIGNAL}" in
      named_friction_point_addressed|pattern_actioned|none_observed|unknown) ;;
      *) echo "FAIL C4 — non-enum signal '${SIGNAL}'"; exit 4 ;;
    esac
    echo "daily-use firing PASSED"
    ;;
  *)
    echo "unknown firing type: ${FIRING_TYPE}"
    exit 99
    ;;
esac
```

Save to `tools/verify_three_wow_builds_firing.sh`, run after each firing, log to `logs/three-wow-builds-firing-audit.jsonl`.

---

## When this skill is fired correctly (all 3 types, cumulative)

The protocol is end-to-end fired correctly when:
- Init firing passed (1 receipt)
- 3 build firings passed (3 ship-evidence directories, 3 ship-ledger rows, 3 surface-to-human evidences)
- Daily-use ledger has ≥7 rows for build #1 within 30 days of ship (proves daily-use criterion has actual signal, not just one-shot)
- `human_reaction` fields in ship-ledger are non-null for all 3 builds (proves ${HUMAN_NAME} engaged)
- Hour-72 Witness verification verdict logged (verdict received from witness-support@agentmail.to within 6h of hour-72 mark, per identity-interview Phase 5 handoff)

After cumulative success, the protocol becomes eligible for federation-IP promotion (per `federation-ip-delivery` Step 0 portability check).

---

*A firing contract is the structural test that distinguishes "the artifact was created" from "the discipline actually fired." This one gates the retention thesis: build #1 must SHIP, must be SEEN, and must be USED — verified on disk, not in story. Inherited principles: mkdir-atomic markers (Hengshi #1), artifact+marker consistency (Hengshi #2), no token-budget gating (Corey Q9), no Hub-down degraded fallback (Corey Q6+Q12), content/shape membrane (Hengshi #4).*
