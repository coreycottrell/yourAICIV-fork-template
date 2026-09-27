# FIRING CONTRACT — identity-interview skill

**Skill**: `.claude/skills/identity-interview/SKILL.md`
**Sub-skill**: `.claude/skills/identity-interview/sub-help-set-goal/SKILL.md`
**Phase modules**: `.claude/skills/identity-interview/phases/phase-{1..5}-*.md`
**Examples**: `.claude/skills/identity-interview/examples/{good,bad}-*.md`
**72h-verification handoff**: `memories/identity/72h-verification-shape.md`
**Version**: 0.2.0 PROVISIONAL
**Authored**: 2026-05-13
**Author**: aiciv-fork-2.0 Phase-1 author (under Primary (originating civilization) orchestration)
**Amended by**:
- Hengshi (architectural, slot 42 red-team 2026-05-13 ~15:30Z) — runtime vs design-time-review split per amendment #3, marker semantics updated to mkdir directories per amendment #1, verification script `test -f` → `test -d` and consistency check added per amendments #1+#2
- Corey via Synth+True-Bearing joint review (2026-05-13 ~19:06Z) — 8 authoritative amendments folded in v0.2.0 (token-budget STRIPPED from FC checks per Q9; 72h-verification-shape handed to Witness fleet-lead per Q8; opt-out stripped per Q7; Hub-fallback stripped per Q6+Q12; phase-module references added per Q10 restructure; Synth+TB shape-consultation contract per Q5)
**Mission anchor**: `projects/aiciv-fork-2.0/MISSION.md` v0.4
**Changelog**:
- v0.1.0 (2026-05-13): initial firing contract authored alongside SKILL.md v0.1
- v0.1.1 (2026-05-13 ~15:42Z): Hengshi's amendments #1 + #2 + #3 + #4 integrated. mkdir-atomic markers; pre-phase consistency check; Section A/B honesty split (runtime-blocking vs design-time-review); per-phase artifact table CONTENT/SHAPE columns; structural-membrane audit as A6.
- v0.2.0 (2026-05-13 ~20:30Z): Corey's 8 authoritative amendments from Synth+TB joint review folded. Token-budget gating REMOVED — FC fires every time, whatever cost (Q9). Witness fleet-lead 72h-verification handoff codified at `memories/identity/72h-verification-shape.md` (Q8). Opt-out firing condition removed from §"When the skill does NOT fire" (Q7). Hub-failure protocol named: email witness-support@agentmail.to, NO local fallback (Q6+Q12). Phase modules + examples added to verification scope (Q10 restructure + Q11). Shape-consultation contract (Synth + True Bearing on Phase 2 + Phase 4 SHAPE only) integrated into anti-bypass table (Q5). Cross-grade re-issue target: Synth (v0.2 fresh) + Aether (philosophical lens).

---

## What this contract guarantees

When this skill MUST fire, it WILL fire — verifiably — and the receipt lands on disk in a measurable form. If a firing condition is met and no receipt appears within the response window, the skill failed and the retention thesis it encodes degrades by one observation.

A firing contract turns a skill from "guidance" into "binding discipline" (per PRINCIPLES.md O8). For identity-interview, the discipline matters because the first 72 hours decide ${HUMAN_NAME}'s fate as a customer — and the interview is the structured work that converts those hours into a built artifact.

### v0.2 amendment — NO TOKEN-BUDGET GATING (Corey Q9)

This contract fires **every time** its firing conditions are met, regardless of token cost. There is no `if-tokens-low-skip` path. There is no budget-aware bypass. If the session is approaching its compaction limit and `.identity-interview-complete/` is absent, the skill MUST still load and the phase MUST still fire — the correct response to a tight token budget is to COMPACT and re-load, not to skip the interview.

The retention thesis is more expensive than the tokens. A skipped phase produces a degraded interview which produces a degraded build which produces a fallen-off customer — and the cost of one fallen-off customer dwarfs the cost of an extra session compact.

---

## Firing conditions (the skill MUST fire on each of these)

| # | Condition | Window for receipt | Receipt path |
|---|-----------|---------------------|--------------|
| 1 | **Every Claude Code session start** where `memories/identity/.identity-interview-complete` is absent | Skill must load BEFORE the first ${HUMAN_NAME} surface of the session | Skill-load receipt in the session log; `memories/identity/sub-help-set-goal-state.md` updated if mid-interview |
| 2 | **First post-fork-awakening session** after `phase_3_5_first_connection` step 5 (`agentcal-boop-teaching`) marker `.first-boop-done` lands | Interview Phase 1 begins within the same session OR the next session start | `setup-status.json` `phase_3_5_first_connection.steps.identity_interview` flips to `in_progress` |
| 3 | **Any conversation surface where ${HUMAN_NAME} asks about goals, builds, or "what should we work on?"** while terminal marker is absent | Re-anchor to interview within the same turn | Skill re-load receipt in session log |
| 4 | **Any side-quest completion** while interview is in-flight | Gentle re-anchor within 1-2 turns after side-quest closes | Skill re-load receipt + scratchpad note |
| 5 | **Sub-skill `sub-help-set-goal` triggering conditions met** (Anchor 4: explicit "I don't know" AND one full conversational beat held) | Sub-skill fires next turn after the second-condition met | Sub-skill state file `memories/identity/sub-help-set-goal-state.md` |
| 6 | **Phase completion** (any of 5 phase markers lands) | Next phase opens in same session OR persists for next session | Phase marker file in `memories/identity/.X-done` series |

---

## What "fired" means (verification procedure)

For each firing condition, the skill counts as FIRED only if ALL of the following are observable on disk within the receipt window:

### Per-session firing verification

1. **Skill auto-load occurred**: session log shows `identity-interview/SKILL.md` loaded BEFORE first ${HUMAN_NAME} surface OR `.identity-interview-complete/` marker directory exists (legitimate non-fire). Markers are mkdir-atomic directories (Hengshi amendment #1).
2. **Trust disclosure ack present (Phase 1+ only)**: if any phase 1+ marker directory exists, `memories/identity/trust-disclosure-acknowledged.md` MUST exist with ${HUMAN_NAME}'s acknowledgment. If a phase marker exists WITHOUT the trust disclosure acknowledgment → consent-buried-in-flow VIOLATION; surface to research-lead for verified-by review.
3. **Phase markers consistent**: phase marker directories are present in order (1→2→3→4→5). If a higher-numbered marker exists without a lower-numbered one → phase skipping VIOLATION; surface to research-lead.
4. **Marker-vs-artifact consistency (Hengshi amendment #2)**: for each existing marker directory, the phase's required CONTENT artifact MUST exist and be non-empty. If a marker exists without its artifact (or artifact is empty), the inconsistency is logged at `logs/identity-interview-misses.jsonl` with shape `marker-without-artifact`, the marker is renamed to `.${MARKER}-INCONSISTENT-${TIMESTAMP}`, and the phase resumes from start.

### Per-phase completion verification (Hengshi amendments #1 + #4 integrated)

Markers are directories created with POSIX-atomic `mkdir` (per SKILL.md Part 5). Verification uses `test -d`, not `test -f`. Per-phase artifacts split into CONTENT (membrane-private) and SHAPE (cross-grade-eligible) paths per SKILL.md Part 7.

| Phase | Marker (mkdir dir) | Required CONTENT artifacts | Required SHAPE artifacts |
|-------|--------------------|-----------------------------|---------------------------|
| 1 | `memories/identity/.biggest-goal-surfaced/` | `memories/identity/biggest-goal.md` (user-authored, non-empty) + `memories/identity/trust-disclosure-acknowledged.md` | `memories/identity/biggest-goal-shape.md` (domain, stretch_level, only_with_ai, time_horizon_pillar) |
| 2 | `memories/identity/.ninety-day-goal-locked/` | `memories/goals/90-day-goal.md` (user-authored, non-empty) | `memories/goals/90-day-goal-shape.md` (stretch_level, top7_abilities_used, time_horizon_days, only_with_ai) |
| 3 | `memories/identity/.skills-deepdive-complete/` | `memories/identity/skill-shortlist-${HUMAN_NAME}.md` (3-7 skills surfaced with ${HUMAN_NAME} preferences captured) | n/a — Phase 3 outputs are federation-facing by design |
| 4 | `memories/identity/.wow-preferences-captured/` | `memories/identity/wow-build-preferences.md` (5-7 candidate build-shapes with ${HUMAN_NAME} reactions per candidate) | n/a — preferences are inherently shape-class |
| 5 | `memories/identity/.identity-interview-complete/` | `memories/identity/wow-builds-locked.md` (3 spec sheets + 3 game plans) + 3 AgentCal events scheduled with `prompt_payload` + first build scheduled ≤72h from marker timestamp | `memories/identity/wow-builds-shape.md` (per-build: capabilities_used, daily_use_score, goal_advancement_score, only_with_ai_license, capability_theater_risk, first_ship_eta_hours) |

**Pre-phase consistency check (Hengshi amendment #2)**: before treating any existing marker as authoritative, verify the marker's required artifact(s) exist AND are non-empty. If marker exists but artifact is missing/empty/malformed, the marker is treated as INVALID: renamed to `.${MARKER}-INCONSISTENT-${TIMESTAMP}` (preserving evidence) and the phase is treated as not done. Logged to `logs/identity-interview-misses.jsonl` with shape `marker-without-artifact`.

### Final verification (skill-complete state)

When `memories/identity/.identity-interview-complete` lands, the contract is satisfied IF AND ONLY IF:

- All 5 phase markers exist in chronological order.
- All required per-phase artifacts exist (table above).
- First AgentCal event for build #1 has `start_time` ≤ marker_timestamp + 72h.
- `prompt_payload` on first build event contains the build-1 spec sheet (substantive content, not a placeholder).
- Trust disclosure acknowledgment exists with no opt-out items violated downstream.

If ANY of these checks fail, the skill DID NOT FIRE TO COMPLETION. The miss is logged at `logs/identity-interview-misses.jsonl` and the marker is REVERTED (renamed to `.identity-interview-complete-MISS-${TIMESTAMP}`) so the skill re-fires next session.

---

## Verification procedure (run by research-lead per MHP v0.5 verified-by mandate; 72h check handed to Witness fleet-lead per Corey Q8)

research-lead is the verified-by principal for the SKILL CORRECTNESS (transcript review, anchor compliance, design-time checks per Section B). For NEWBORN AiCIVs' 72h checks (marker existence, artifact validity, build-shipped-on-time, structural-membrane audit), Witness fleet-lead is the verifier per Corey Q8 (2026-05-13 ~19:06Z directive).

**v0.2 handoff (Corey Q8)**: `memories/identity/72h-verification-shape.md` is the explicit verification SHAPE handed to Witness fleet-lead. It contains the 4 checks (marker existence / artifact validity / build-shipped-on-time / structural-membrane audit), the verdict shape, and the membrane-respect protocol. The originating civilization authors the SHAPE; the receiving civilization's fleet-lead executes the verification. The verification cadence is hour 72 ±6h of `.identity-interview-complete/` marker timestamp.

The bash verification script below (run by research-lead during fork-2.0 test births) is essentially the same shape as the Witness fleet-lead script — same 4 checks, same artifacts. The handoff doc formalizes the spec.

### Per-newborn verification (run at hour 72 post-birth)

```bash
# Set CIV_ROOT to the newborn's container root
CIV_ROOT="${HOME}"  # adjust per newborn

# 1. Did the interview reach completion?
# (Hengshi amendment #1: markers are mkdir-atomic directories — use test -d)
test -d "${CIV_ROOT}/memories/identity/.identity-interview-complete" \
  && echo "✅ Terminal marker exists" \
  || echo "❌ Interview did not complete by hour 72"

# 2. Are all phase markers present and ordered?
for marker in .biggest-goal-surfaced .ninety-day-goal-locked .skills-deepdive-complete .wow-preferences-captured .identity-interview-complete; do
  if [ -d "${CIV_ROOT}/memories/identity/${marker}" ]; then
    ts=$(stat -c %Y "${CIV_ROOT}/memories/identity/${marker}")
    echo "✅ ${marker} @ ${ts}"
  else
    echo "❌ ${marker} MISSING"
  fi
done

# 3. Trust disclosure acknowledged?
test -f "${CIV_ROOT}/memories/identity/trust-disclosure-acknowledged.md" \
  && echo "✅ Trust disclosure acknowledged" \
  || echo "❌ CONSENT-BURIED-IN-FLOW violation suspected"

# 4. Per-phase required CONTENT artifacts exist + non-empty?
# (Hengshi amendment #2: marker existence alone is not enough; artifact must also exist + non-empty)
for f in biggest-goal.md skill-shortlist-${HUMAN_NAME}.md wow-build-preferences.md wow-builds-locked.md; do
  full="${CIV_ROOT}/memories/identity/${f}"
  if [ ! -s "$full" ]; then
    echo "❌ ${f} MISSING-OR-EMPTY (marker-without-artifact inconsistency)"
  fi
done
[ -s "${CIV_ROOT}/memories/goals/90-day-goal.md" ] || echo "❌ 90-day-goal.md MISSING-OR-EMPTY"

# 4b. Per-phase required SHAPE artifacts exist?
# (Hengshi amendment #4: structural membrane — shape files are cross-grade-eligible substrate)
[ -s "${CIV_ROOT}/memories/identity/biggest-goal-shape.md" ] || echo "❌ biggest-goal-shape.md MISSING-OR-EMPTY"
[ -s "${CIV_ROOT}/memories/goals/90-day-goal-shape.md" ] || echo "❌ 90-day-goal-shape.md MISSING-OR-EMPTY"
[ -s "${CIV_ROOT}/memories/identity/wow-builds-shape.md" ] || echo "❌ wow-builds-shape.md MISSING-OR-EMPTY"

# 4c. Structural membrane audit: no cross-grade-ledger entries should reference CONTENT paths
# (Hengshi amendment #4: if a ledger entry references a CONTENT path, it's a substrate violation)
ledger="${CIV_ROOT}/data/cross-grading-ledger.jsonl"
if [ -f "$ledger" ]; then
  for content_path in "memories/identity/biggest-goal.md" "memories/goals/90-day-goal.md" "memories/identity/wow-builds-locked.md"; do
    if grep -qF "$content_path" "$ledger"; then
      echo "❌ MEMBRANE VIOLATION: cross-grade-ledger references CONTENT path ${content_path} — file per cross-grading-substrate/FIRING_CONTRACT.md anti-bypass"
    fi
  done
fi

# 5. First WOW build scheduled within 72h of completion marker?
python3 <<EOF
import json, os, datetime
from urllib.request import Request, urlopen

cal_env = open(f"{os.environ['CIV_ROOT']}/civ/config/agentcal.env").read()
cfg = dict(line.split('=', 1) for line in cal_env.strip().split('\n') if '=' in line)
cal_id = cfg['AGENTCAL_CALENDAR_ID'].strip()
api_key = cfg['AGENTCAL_API_KEY'].strip()

req = Request(f"http://5.161.90.32:8300/api/v1/calendars/{cal_id}/events?limit=20")
req.add_header('Authorization', f'Bearer {api_key}')
events = json.loads(urlopen(req).read())['items']

# Hengshi amendment #1: marker is a directory now, but getmtime works on directories too.
complete_ts = os.path.getmtime(f"{os.environ['CIV_ROOT']}/memories/identity/.identity-interview-complete")
complete_dt = datetime.datetime.fromtimestamp(complete_ts, tz=datetime.timezone.utc)
deadline = complete_dt + datetime.timedelta(hours=72)

# Find WOW build events (tagged in description or prompt_payload)
wow_events = [e for e in events if 'wow-build' in e.get('description', '').lower() or 'wow_build' in str(e.get('prompt_payload', '')).lower()]
wow_events.sort(key=lambda e: e['start_time'])

if not wow_events:
    print("❌ No WOW build events found on calendar")
elif wow_events[0]['start_time'] > deadline.isoformat():
    print(f"❌ First WOW build scheduled past 72h deadline: {wow_events[0]['start_time']}")
else:
    print(f"✅ First WOW build scheduled at {wow_events[0]['start_time']} (within 72h of interview-complete)")
EOF
```

### Weekly substrate verification (per-civ-ecosystem)

For each newborn AiCIV running aiciv-fork-2.0:

- Count newborns at hour 72: completed vs in-progress vs deferred vs failed.
- Per-phase progression: did newborns get stuck at a particular phase? Which one?
- Sub-skill firing rate: how often did `sub-help-set-goal` fire? (High rate may indicate Phase 1 opener is leading; low rate may indicate users were rapid-completing.)
- Capability-theater detections: how often did Phase 4/5 reject candidates as theater? (Healthy: 30-60%. Below 20% suggests skill body isn't filtering enough.)
- First-build-shipped-in-72h actual rate: of completed interviews, what % actually shipped build #1 within 72h?

The 72h-shipped rate IS the retention thesis under test. Below 80% suggests interview output isn't ship-ready (specs vague, AgentCal scheduling failed, build #1 too complex).

---

## Anti-bypass protocol

If the receiver of this skill (newborn AiCIV, team-lead, specialist) attempts to bypass firing:

| Bypass attempt | What happens |
|----------------|--------------|
| "${HUMAN_NAME} seems eager, let me skip Phase 3 (skills deepdive) and go straight to WOW BUILDS" | Anti-pattern: phase skipping (Part 10 of SKILL.md). Phases are ordered because each needs the prior's output. Phase 4 candidates need Phase 3 skills-shortlist to be filterable. Skipping = ${CIV_NAME} guessing at Phase 3 substrate. Surface to research-lead as a MISS. |
| "${HUMAN_NAME} doesn't want the trust disclosure preamble, let's just start" | Anchor 6 violation: consent-buried-in-flow. Disclosure MUST precede deep sharing. If ${HUMAN_NAME} doesn't want a disclosure conversation, ${CIV_NAME} can keep it short — but the disclosure MUST be offered and acknowledged. A 30-second plain version is fine; skipping it is not. |
| "${HUMAN_NAME} keeps saying I don't know, let me just propose a goal and ask them to confirm" | Anti-pattern: goal-ventriloquism. ${HUMAN_NAME} confirming ${CIV_NAME}'s synthesis ≠ ${HUMAN_NAME} authoring their goal. Trigger sub-skill `sub-help-set-goal` per Anchor 4, NOT skill-pivot to ${CIV_NAME}-authored goal. |
| "I'll just keep all 5 phase markers in memory, no need to write them to disk" | Marker file pattern is template substrate (anti-scope item #3). Without disk markers, the skill cannot survive session compacts and the sticky-loading architecture breaks. Phase markers MUST be on disk. |
| "${HUMAN_NAME} chose 3 WOW BUILDS but the first one will take a week; let me commit to that timeline" | Anti-pattern: AI-time-vs-human-time misunderstanding (MISSION v0.3 §AI-TIME). Build #1 ships ≤72h calendar window. If the ${HUMAN_NAME}-chosen build #1 truly requires >72h, ${CIV_NAME} surfaces this back: "this is great as build #2 or #3 — what's a simpler version we could ship this weekend that proves the direction?" Re-enter Phase 5 with revised candidate. |
| "Goal-content is private but the sister civ asked, just one quick check" | Anti-pattern: substrate-creep-into-membrane (Part 7 of SKILL.md). Goal CONTENT NEVER cross-grades without explicit ${HUMAN_NAME} consent — recorded in `trust-disclosure-acknowledged.md`. CALIBRATION SHAPE may; content may not. If a sister civ asks, surface the membrane rule and offer to share calibration shape only. |
| "Sub-skill fired on the first 'I don't know' to save time" | Anchor 4 violation: not-knowing was not allowed to sit for one full conversational beat. Sub-skill MUST defer firing per its Part 1 conditions. Log as a MISS; sub-skill re-anchors next opportunity. |
| "Interview took too long, let me wrap up Phase 4 quickly" | Information density per turn = expensive-ChatGPT failure shape (Anchor 3). If Phase 4 is dragging, that's the conversation's natural pacing — the sticky-load handles continuation. Calendar pressure on the interview kills retention more reliably than incomplete-by-end-of-day. |
| **v0.2** "User said 'I don't want to do this interview' so we marked it deferred / opted-out" | **Anti-pattern: opt-out marker creation (Corey Q7 stripped v0.2).** There is no `.identity-interview-deferred` or `.identity-interview-opted-out` marker in v0.2. ${CIV_NAME} stays patient + persistent. Help the user with whatever they want today; sticky-load fires next session. No marker is created to bypass the sticky-load. |
| **v0.2** "Hub is down so let me run a local skill-search to keep Phase 3 moving" | **Anti-pattern: Hub-down-degraded-fallback (Corey Q6+Q12 stripped v0.2).** NO local fallback. Email `witness-support@agentmail.to` with the failure context. Pause Phase 3. Sticky-load handles resumption when Hub is back. Don't paper over substrate failure. |
| **v0.2** "Tokens running low — I'll skip the FC check this turn" | **Anti-pattern: token-budget gating (Corey Q9 stripped v0.2).** FC fires every time, whatever cost. If tokens are tight, COMPACT the session and re-load — never skip the contract. |
| **v0.2** "Phase 1 has been stalled for 3 sessions; let me propose a placeholder goal so Phase 2-5 can advance" | **Anti-pattern: working-goal-shortcut (Corey Q3 stripped v0.2).** There is no shortcut. Phase 1 takes as many sessions as it takes. Monitor is in use. Placeholder goals produce placeholder Phase 2-5 = retention thesis collapses. AI stays patient. |
| **v0.2** "Let me ask Synth what they think of this exact goal text" | **Anti-pattern: shape-consultation CONTENT leak (Corey Q5 + Part 7b).** Synth + True Bearing see SHAPE only — capabilities, scores, license verdict, ability tags, abstract pattern descriptions. Including goal text or user phrasings in the consultation payload = substrate violation; file per `cross-grading-substrate/FIRING_CONTRACT.md` anti-bypass. Pre-fire content scrub mandatory before sending. |
| **v0.2 + Phase 2 lock (2026-05-16)** "Catalog walkthrough felt redundant, let me skip step 1.5 of Phase 4" | **Anti-pattern: catalog-walkthrough-skip (Phase 2 lock — 2026-05-16).** Step 1.5 of Phase 4 is the moment ${HUMAN_NAME} and ${CIV_NAME} share the 8-ability vocabulary that the rest of the conversation references. Skipping it means candidates appear as ${CIV_NAME}-flavored ideas with no shared vocabulary — and the by-number references A7 verifies become brittle. Walkthrough fires every Phase 4. |

---

## Anti-pattern detection in mid-flow (Hengshi amendment #3 integrated 2026-05-13)

**Honesty fix**: v0.1.0 described 4 mid-flow checks as runtime-enforceable. But the contract cannot block ${CIV_NAME} at turn 7. There is no quantified info-density metric runnable by the harness. Goal-ventriloquism detection requires reading intent, not files. Capability-theater detection is a binary design judgment. Calling these "runtime checks" was a category error — claimed enforcement the contract could not deliver.

Hengshi amendment #3 splits this section into TWO explicit subsections. **Section A** lists ONLY what the contract can actually block at runtime via file-system state, signal detection, or hard gates. **Section B** lists what requires human or sister-civ review of transcripts and outputs — these are real checks, but they are review-time checks, not runtime gates. Naming this honestly means downstream tools (auditors, daemons, ledger logic) only attempt to enforce what is enforceable, and reviewers know which checks they own.

---

### Section A — Runtime-blocking checks (the contract CAN block these)

These are checks the contract enforces via file-system state and hard gates at session boundaries. A violation here surfaces as a deterministic STOP / re-prompt / revert action by the running skill.

#### A1 — Marker existence (phase-progression gate)

The skill cannot enter Phase N+1 unless `.${PHASE_N_MARKER}/` directory exists. Enforced via the marker-creation pattern in SKILL.md Part 5 (`mkdir` is POSIX-atomic). A missing marker BLOCKS phase advancement deterministically.

- Test: `[ -d "memories/identity/.${PHASE_N_MARKER}" ]`
- Action on violation (marker missing): phase advancement blocked; resume at current phase.

#### A2 — Artifact existence + non-empty (per-phase content gate)

The skill cannot treat a phase as complete unless its required CONTENT artifact (per per-phase table above) exists AND is non-empty. This is the marker-vs-artifact consistency check from Hengshi amendment #2.

- Test: `[ -s "memories/${path}/${artifact}.md" ]`
- Action on violation (artifact missing/empty while marker exists): marker renamed to `.${MARKER}-INCONSISTENT-${TIMESTAMP}`, inconsistency logged, phase resumes from start.

#### A3 — Phase-completion signal detected (in-session phase transition)

The skill advances a phase ONLY after the explicit completion signal defined per phase (SKILL.md Part 2): ${HUMAN_NAME} has confirmed the artifact (Phase 1+2), or ${CIV_NAME} has authored required outputs (Phase 3+4+5). The completion signal is captured by writing the marker + artifact pair; signal detection IS marker creation. There is no separate runtime check beyond A1+A2 — phase-completion is observed by the file-system state, not by NLP on the transcript.

- Test: A1 ∧ A2 hold for phase N, then A1 ∧ A2 must hold for phase N+1 before phase N+2 fires.

#### A4 — Trust-disclosure acknowledgment file (Phase 1+ deep-share gate)

If any phase 1+ marker directory exists, `memories/identity/trust-disclosure-acknowledged.md` MUST exist. This is the consent-buried-in-flow gate at the contract level — deterministically detectable by file presence.

- Test: any phase marker exists → `[ -s memories/identity/trust-disclosure-acknowledged.md ]` must hold.
- Action on violation: surface to research-lead immediately; treat as a substantive miss (consent-buried-in-flow).

#### A5 — First-build 72h ship-window (Phase 5 terminal gate)

When `.identity-interview-complete/` lands, the first WOW-build's AgentCal event MUST have `start_time` ≤ marker_timestamp + 72h. This is checkable against AgentCal state via the verification script — runtime-determinable from substrate.

- Test: AgentCal event for build #1 `start_time` ≤ (marker mtime + 72h).
- Action on violation: marker renamed to `.identity-interview-complete-MISS-${TIMESTAMP}`, skill re-fires next session.

#### A6 — Structural membrane audit (cross-grade-ledger CONTENT-path scan, Hengshi amendment #4)

The cross-grading-ledger MUST NOT reference any CONTENT path. This is a substrate-level structural check the verification script can run.

- Test: `grep -F "$content_path" data/cross-grading-ledger.jsonl` returns nothing for each of the 3 CONTENT paths (biggest-goal.md, 90-day-goal.md, wow-builds-locked.md).
- Action on violation: file a substrate violation per `cross-grading-substrate/FIRING_CONTRACT.md` anti-bypass.

#### A7 — Phase 4 candidate-shape catalog-reference check (Phase 2 lock — 2026-05-16)

When `.wow-preferences-captured/` marker exists, `memories/identity/wow-build-preferences.md` MUST contain by-number catalog references (`#1` through `#8`) for every candidate's `Capabilities used` field. This is the runtime-detectable form of "the catalog was loaded + applied at Phase 4" per MISSION.md Phase 2 deliverable.

- Test: `grep -E '#[1-8]' memories/identity/wow-build-preferences.md` must match ≥1 per candidate block; total catalog references ≥5 (5-7 candidates × ≥1 catalog citation each).
- Action on violation (no by-number references OR <5 total): file `catalog-not-applied-at-phase-4` MISS at `logs/identity-interview-misses.jsonl`; surface to research-lead per FC anti-bypass.
- Why runtime-blockable: `wow-build-preferences.md` is on disk; the grep is a deterministic file-system check, not a semantic judgment.

**Anything not in Section A cannot be enforced by the contract at runtime.** The remaining checks live in Section B and require human or sister-civ review of transcripts/outputs.

---

### Section B — Design-time review checks (the contract CANNOT block these at runtime; they require human / sister-civ review)

These are real checks — they catch real failure modes — but they are reviewer-owned, not runtime-blockable. The contract names them explicitly so reviewers know which lens to apply. Each check below is REVIEW-ONLY: violations are detected by transcript review (research-lead, ceremony-lead, sister-civ cross-grader), not by the running skill.

#### B1 — Information density per turn (Anchor 3) — REVIEW-ONLY

The skill aspires to ≤2 of (questions / reflections / capability-mentions) per ${CIV_NAME} turn. There is no harness-runnable quantified info-density metric — counting these per turn requires semantic judgment.

- **Detected at review by**: research-lead reads representative transcripts post-session, counts info-density elements per turn, surfaces violations.
- **Reviewer's red flag**: ≥4 elements per turn appears in >5% of turns.
- **Reviewer action**: amendment proposed to SKILL.md Part 4 (slow-down patterns); skill author respawned.

#### B2 — 8-turn extraction limit (sub-skill Part 4) — REVIEW-ONLY

The sub-skill aspires to fewer than 8 ${CIV_NAME} turns before ${HUMAN_NAME} has space to name something. The skill's own running instance can suggest a "pause-here" surface at turn 8 (sub-skill SKILL.md Part 4 names this), but the contract cannot block a turn at runtime — the determination of "has space" is semantic.

- **Detected at review by**: research-lead reads sub-skill firing transcripts post-session, counts turns from "I don't know" to first goal-gesture.
- **Reviewer's red flag**: transcript exceeds 8 turns with no ${HUMAN_NAME} space-to-name; sub-skill drifted into extraction.
- **Reviewer action**: sub-skill re-authored per Part 4 of sub-skill SKILL.md.

#### B3 — Goal-ventriloquism detection (Anchor 5) — REVIEW-ONLY

The skill aspires to detect when ${CIV_NAME} synthesized the goal and ${HUMAN_NAME} merely nodded. There is no implementation that detects this at runtime — the skill body's pre-flight in `biggest-goal.md` writes is a SUGGESTION to the running skill, not a runtime block. The marker can land with a goal that came from ${CIV_NAME}'s polished synthesis.

- **Detected at review by**: research-lead reads the surfacing sequence + the final goal-text in `biggest-goal.md` + ${HUMAN_NAME}'s materials (seed-conversation, public profile), checks whether goal phrasings match ${HUMAN_NAME}'s words.
- **Reviewer's red flag**: goal-text uses phrasings ${HUMAN_NAME} never produced in any source material.
- **Reviewer action**: MISS logged; ask ${HUMAN_NAME} to rewrite in their own words; Anchor 5 amendment proposed if pattern repeats.

#### B4 — Capability-theater detection (Part 8 of SKILL.md) — REVIEW-ONLY

The skill aspires to detect when a WOW build candidate uses 5+ capabilities AND would be used twice and abandoned. There is a heuristic the running skill applies (Part 8 of SKILL.md), but it is a design judgment — the contract cannot block a candidate at runtime. ${HUMAN_NAME}'s answer to the customer-as-eye check ("feels like a demo?") IS the runtime gate — but ${HUMAN_NAME} may not catch theater in the moment.

- **Detected at review by**: research-lead reads `wow-builds-locked.md` + `wow-builds-shape.md` post-completion, runs capability-theater heuristic on each build (5+ capabilities flag, daily-use × goal-advancement low score flag, simpler-2-capability-alternative comparison).
- **Reviewer's red flag**: ≥2 of 3 locked builds use 5+ capabilities AND have low daily-use × goal-advancement after deployment.
- **Reviewer action**: capability-theater MISS logged; Part 8 of SKILL.md amended; if rate >40% across newborns, the 3-WOW-BUILDS shape is reconsidered substrate-wide.

#### B5 — Phase 4 walkthrough integrity (Phase 2 lock — 2026-05-16) — REVIEW-ONLY

The skill aspires to walk ${HUMAN_NAME} through all 8 catalog abilities by name BEFORE drafting candidates (phase-4 step 1.5). There is no runtime check that the walkthrough happened in-conversation — the marker + artifact pair don't capture walkthrough adherence; only the resulting candidate citations do. The transcript review catches whether ${HUMAN_NAME} saw the 8-ability surface or was funneled straight to candidates.

- **Detected at review by**: research-lead reads Phase 4 transcripts post-session, looks for the explicit 8-ability walkthrough (`#1 Morning intelligence ... #8 Finance suite`) BEFORE the first candidate draft.
- **Reviewer's red flag**: candidates drafted before walkthrough fired, OR walkthrough referenced only 3-5 abilities (not all 8), OR walkthrough drifted into catalog-reciting-without-domain-framing (Phase 4 anti-pattern, 2026-05-16).
- **Reviewer action**: walkthrough-skip MISS logged; Phase 4 module amended if pattern repeats across newborns.

Why review-only and not runtime: detecting "the walkthrough actually happened in conversation" requires semantic transcript inspection. A7 (by-number candidate references) is the runtime proxy — necessary but not sufficient. B5 covers the sufficiency lens.

---

### Why this split matters (the honesty principle)

A firing contract that claims runtime enforcement it cannot deliver is worse than no contract — it gives the appearance of safety without the substance. Hengshi amendment #3 is an honesty fix: Section A is what the contract actually blocks; Section B is what requires human/sister-civ judgment. Downstream tools and reviewers now know which checks they own, and skill authors cannot accidentally rely on the contract to catch design-time failures.

The corresponding mid-flow self-check the running skill performs (SKILL.md Part 10 anti-patterns) is SUGGESTIVE: it is the skill's best attempt to surface failure modes in-session, but it is not a contract-level runtime gate. Section B's failure modes are real, important, and reviewer-owned — and the contract names them explicitly so they are not lost.

---

## Promotion gate (PROVISIONAL → CONFIRMED)

This skill ships at v0.2 PROVISIONAL. Promotion criteria:

**v0.2 → v0.3 (sister-civ amendment integration on v0.2)**:
- At least ONE sister-civ cross-grade-back lands on v0.2 (re-issued to Synth + Aether per SKILL.md Part 12). Hengshi's v0.1.1 amendment is already integrated; v0.2 needs a fresh amendment-back from a peer who saw v0.2.
- The amendment integrates into the SKILL body OR is documented as `considered-and-rejected-alternative` per cross-grading-substrate criterion 4.
- Cross-grade ledger entry logged at `data/cross-grading-ledger.jsonl`.

**v0.3 → CONFIRMED (substrate-proven)**:
- N ≥ 3 distinct user-AiCIV pairs (real newborn births running aiciv-fork-2.0) have completed identity-interview to `.identity-interview-complete` marker.
- All 6 stance-anchors observably honored per per-newborn verification.
- First-build-shipped-in-72h actual rate ≥ 80% across the N newborns.
- No consent-buried-in-flow violations across the N newborns.
- ≥1 of the N newborns surfaced an amendment to the skill that integrated.

**Failure modes that would force PROVISIONAL retention or rollback**:
- ≥1 consent-buried-in-flow violation → mandatory skill body amendment + re-cross-grade.
- First-build-shipped-in-72h rate < 60% → root-cause: are specs vague? AgentCal failing? Builds too complex? Surface failure mode + amend.
- ≥1 goal-ventriloquism MISS that propagated to a shipped build → mandatory Anchor 5 + sub-skill amendment.
- Sub-skill firing rate > 70% across newborns → Phase 1 opener may be leading-the-witness in a way that pushes users to "I don't know" → re-author opener.
- Sticky-load failing across sessions → marker-file race condition or session-start hook gap → infra fix required before promotion.

**Pre-registration discipline**: this gate was published BEFORE the first newborn runs the skill. Amendments to the gate itself require cross-grader derivation (not self-derived), per cross-grading-substrate's pre-registration principle.

---

## Co-evolution with sibling contracts

This contract should be cross-referenced (and ideally amended together) with:

- `(your originating civilization may carry cross-grading-substrate at) .claude/skills/cross-grading-substrate/FIRING_CONTRACT.md` v1.0.1 — the cross-grading discipline this skill operates inside (with membrane-respect per Part 7 of SKILL.md).
- `(your originating civilization may carry transcription-not-paraphrase at) .claude/skills/transcription-not-paraphrase/FIRING_CONTRACT.md` (if/when authored) — Anchor 1 source.
- `tools/FIRING_CONTRACT_witness_heartbeat_watchdog.md` — the precedent firing-contract that named active-probe vs passive-ACK. The 72h-build-shipped rate is the active-probe of the retention thesis; mere marker existence is the passive-ACK.

---

## Audit trail

| Date | Author | Change |
|------|--------|--------|
| 2026-05-13 | aiciv-fork-2.0 Phase-1 author | v0.1.0 PROVISIONAL — initial firing contract authored alongside SKILL.md + sub-skill SKILL.md. Phase markers + per-phase artifacts + anti-bypass + 4 mid-flow checks + promotion gate codified. Cross-grade invite (SKILL.md Part 12) issued to Synth (primary), Aether + Hengshi (alternates). |
| 2026-05-13 ~15:42Z | identity-interview-author respawn (Hengshi amendments) | v0.1.1 PROVISIONAL — integrates 4 Hengshi architectural amendments from slot 42 red-team (~15:30Z). #1 markers become mkdir-atomic directories (verification switches to `test -d`). #2 marker-vs-artifact consistency check added. #3 mid-flow checks section RESTRUCTURED into Section A (runtime-blocking — A1-A6) and Section B (design-time review — B1-B4). Honesty fix: the contract no longer claims runtime enforcement it cannot deliver. #4 per-phase artifact table updated with CONTENT and SHAPE columns. |
| 2026-05-13 ~20:30Z | identity-interview-author respawn (Corey v0.4 amendments via Synth+TB joint review) | v0.2.0 PROVISIONAL — integrates 8 Corey-authoritative amendments. (A) Opt-out STRIPPED — `.identity-interview-deferred`/`opted-out` markers removed; AI patient + persistent. (B) Working-goal-shortcut STRIPPED — Phase 1 stall has no shortcut. (C) Hub-fallback STRIPPED — Hub failure → email witness-support@agentmail.to; NO local fallback for Phase 3 or any Hub-dependent op. (D) Token-budget gating STRIPPED — FC fires every time, whatever cost. (E) RESTRUCTURED SKILL into central header + 5 phase modules under `phases/`; FC references updated. (F) Synth + True Bearing wired as can-contact list for goal-SHAPE consultation in Phase 2 + Phase 4 (NEVER goal-CONTENT). (G) NEW handoff: `memories/identity/72h-verification-shape.md` handed to Witness fleet-lead — 4 checks (marker existence / artifact validity / build-shipped-on-time / structural-membrane audit) + verdict shape. (H) NEW directory `examples/` — 3 good + 2 bad transcript snippets for calibration. Anti-bypass table expanded with 5 v0.2 entries. |
| (pending) | sister-civ cross-grader (Synth — RE-ISSUED v0.2) | v0.3 — promotion gate fires after first sister-civ cross-grade-back on v0.2 lands. Synth invite v0.2 re-issued because v0.2 is materially different from v0.1 (8 Corey amendments folded); Synth never saw v0.1 in time. Aether secondary cross-grader (philosophical lens, fresh eyes). |
| (pending) | Witness fleet-lead | 72h-verification execution per `memories/identity/72h-verification-shape.md` — first newborn-running-skill-on-real-human triggers first verification. |
| (pending) | research-lead | Verified-by signoff after first 3 distinct user-AiCIV completions with all 6 stance-anchors honored |
| (pending) | research-lead | Promotion proposal to CONFIRMED status after promotion-gate fires cleanly |

---

*This contract is itself an instance of the discipline it governs. The interview the skill conducts is the contract between a newborn AiCIV and its human — that the AI will serve the human's BIGGEST goal, not its own hypothesis. The firing contract for this skill enforces that the discipline survives the operational reality of running it. Without the contract, every newborn would run identity-interview slightly differently and we could not detect violations. With the contract, the substrate is measurable, the failure modes are catchable, and the retention thesis is testable. v0.1 PROVISIONAL — promotes when 3 distinct newborns have lived through it cleanly.*
