---
name: three-wow-builds-protocol
description: The execution substrate that fires after identity-interview Phase 5 locks 3 WOW BUILDS. Ships each build the moment it is ready: Build #1 no later than 72h after the `.identity-interview-complete/` marker, Builds 2+3 as soon as each is ready and all 3 by the end of day 7. 72h and day 7 are CEILINGS, never floors — no rule makes a build wait. Supplements (does NOT replace) 7-day-wow event-scheduler pattern. Encodes the LICENSING gate (only-with-AI, binary) separately from the SCORING filter (daily-use × goal-advancement, capability-theater explicitly named). Honors the under-understood-capabilities doctrine — AI proposes builds the user wouldn't know to ask for. Sticky-fires once per locked-build until ship-evidence lands on disk.
version: 0.1.1
status: PROVISIONAL
authored: 2026-05-16
authored_by: research-lead (fork-2.0 Phase 3)
mission_anchor: projects/aiciv-fork-2.0/MISSION.md v0.4
parent_skill: identity-interview (fires this protocol post-Phase-5 lock)
sibling_skills:
  - 7-day-wow (event-scheduler pattern this protocol extends — Phase 5 lock OVERRIDES days 1-3 themes when 3 WOW BUILDS land; days 4-7 themes continue)
  - identity-interview (parent — Phase 4 captures preferences, Phase 5 locks 3 builds + writes wow-builds-locked.md + wow-builds-shape.md)
  - critical-thinking (capability-theater detection at scoring time)
  - agentcal-mastery (the prompt_payload self-prompting substrate the events ride on)
  - federation-ip-delivery (eligibility path — promotes to federation-IP-shippable after first real-newborn firing)
  - cross-grading-substrate (membrane discipline — SHAPE is cross-grade-eligible, CONTENT is not)
mandatory_load_for:
  - any session where memories/identity/.identity-interview-complete/ exists AND memories/identity/wow-builds-locked.md is present AND any of build_1/build_2/build_3 still missing ship-evidence
  - first session AFTER identity-interview Phase 5 marker lands
  - any AgentCal event-fire whose prompt_payload references a three-wow-builds Build #N spec
firing_contract: ./FIRING_CONTRACT.md
inputs:
  content_path: memories/identity/wow-builds-locked.md     # Phase 5 output — CONTENT (membrane-private)
  shape_path: memories/identity/wow-builds-shape.md         # Phase 5 output — SHAPE (cross-grade-eligible)
  agentcal_event_refs: 3 events scheduled by Phase 5 (event_ids in wow-builds-shape.md)
outputs:
  per_build_ship_evidence: memories/identity/build-${N}-ship-evidence/   # one directory per shipped build
  ship_ledger: memories/identity/wow-builds-ship-ledger.jsonl            # append-only, one row per ship-attempt
  daily_use_ledger: memories/identity/wow-builds-daily-use-ledger.jsonl  # append-only, one row per build-fire-after-ship
  proposal_log: memories/identity/under-understood-proposals.jsonl       # SHAPE-class proposals AI surfaced during Phase 4
hub_failure_protocol: email witness-support@agentmail.to (NO local fallback — inherited from identity-interview Corey Q6+Q12)
template_placeholders:
  - ${HUMAN_NAME}
  - ${CIV_NAME}
  - ${PARENT_CIV}
changelog:
  - "v0.1.1 (2026-09-27): Corey — removed the builds-2+3 'days 3-7' START WINDOW (a floor). Every build ships when ready; 72h (build #1) and end-of-day-7 (all 3) are ceilings only. Correct for paid and trial (trial-m3) births alike."
  - "v0.1.0 (2026-05-16): initial PROVISIONAL authoring. fork-2.0 Phase 3 deliverable. Authored Primary-style same-day under today-ship constraint (Corey directive 2026-05-16 TG '~lets get this done today if we can')."
---

# Three-WOW-Builds Protocol — Skill (v0.1 PROVISIONAL)

> *"Users active in their first 72 hours whose AI built them something toward a personal goal = fully sucked in. Users who treated it like expensive ChatGPT = fell off. Only 2 of 50 fell off."* — Corey, MISSION.md §"The retention truth"
>
> *"Only-with-AI is a LICENSING criterion (binary). Daily-use × goal-advancement is PRIMARY filter and SCORING criterion. Author bias toward LOAD-BEARING simple over CAPABILITY-THEATER complex."* — MISSION.md §"The 3-WOW-BUILDS bar"

---

## Part 1 — What this skill IS, and what it IS NOT

### IS

- The **execution substrate** that fires AFTER identity-interview Phase 5 has already locked 3 builds + written their spec sheets + game plans + scheduled 3 AgentCal events.
- A **supplement** to the existing `7-day-wow` event-scheduler pattern — NOT a replacement. The two substrates coexist with a defined override rule (see Part 2).
- The wiring that turns "we discussed 3 builds" into "build #1 actually shipped within 72 calendar hours of the interview-complete marker and ${HUMAN_NAME} can SEE the built artifact."
- The repository for **under-understood-capabilities** discipline — when ${CIV_NAME} sees a TOP-8 ability the user wouldn't know to ask for, ${CIV_NAME} PROPOSES it during identity-interview Phase 4 with an explainer + a candidate-build spec.
- A protocol that ships its FIRING_CONTRACT alongside — "this skill counted as fired" is gated on observable artifacts on disk + AgentCal event-fire receipts + daily-use evidence, not self-attestation.
- **Sticky-fires once per locked-build** until ship-evidence lands. No "we'll get to it" deferral.

### IS NOT

- A scheduler. Phase 5 already wrote 3 AgentCal events. This skill does NOT schedule events — it fires when those events fire and CARRIES the build through to ship-evidence + daily-use logging.
- A replacement for 7-day-wow. 7-day-wow continues to fire its Day-N themes for newborns whose human hasn't completed identity-interview (the unseeded-newborn path). Once identity-interview completes + 3 builds lock, this protocol OVERRIDES days 1-3 themes; days 4-7 themes from 7-day-wow continue if they don't conflict.
- A capability showcase. The skill explicitly biases AGAINST capability-theater (see Part 3). A build using 5 abilities does not automatically win.
- A federation-IP artifact (yet). Status PROVISIONAL — promotes to federation-IP-shippable after first successful firing on a real newborn AiCIV birth (per `federation-ip-delivery` Step 0 portability gate).
- A loose discipline. The FIRING_CONTRACT requires observable on-disk evidence at every step. No self-grading.

---

## Part 2 — Relationship to 7-day-wow (the supplement rule)

The existing `7-day-wow` skill (v1.0.0, midwife-lead, 2026-03-24) lives at `.claude/skills/7-day-wow/SKILL.md` in the fork-template. It schedules 7 AgentCal events at T+24h through T+168h with predefined themes (Email Magic → Personal Artifact → Deep Research → Proactive Surprise → Connection → Capability Showcase → Reflection + Roadmap).

This protocol does NOT delete or replace those events. The override rule is:

| Newborn state | 7-day-wow days 1-3 | Three-wow-builds days 1-3 (windows ≤72h) | 7-day-wow days 4-7 |
|--------------|---------------------|-------------------------------------------|---------------------|
| Identity-interview NOT complete | FIRE (default sequence) | DOES NOT FIRE | FIRE |
| Identity-interview COMPLETE, builds locked | **OVERRIDDEN** | FIRE as soon as ready (build #1 ≤72h ceiling; builds 2+3 right after, all by day 7) | FIRE if no conflict |
| Identity-interview COMPLETE, no builds locked yet | n/a — Phase 5 hasn't finished, IS the bug | n/a | n/a |

The override is enforced at AgentCal-fire time: when an event fires, the BOOP-poller reads `memories/identity/.identity-interview-complete/` first. If present AND `wow-builds-locked.md` is non-empty AND the firing event is a 7-day-wow day-1/2/3 event, the poller delegates to this protocol instead. If absent, the original 7-day-wow event fires as designed.

**This is supplement, not replacement.** Newborns whose humans don't complete identity-interview (the unseeded path) still get the full 7-day arc.

---

## Part 3 — The two-stage filter (LICENSING vs SCORING)

This is the operational core of the protocol. It is referenced verbatim by identity-interview Phase 4 (preferences) and Phase 5 (lock).

### Stage 1 — Only-with-AI LICENSE (binary gate)

**Question**: Could a human plausibly do this build with off-the-shelf tools and a weekend?

- If YES → FAIL the license. The build is NOT a WOW build. Drop it before presentation.
- If NO → PASS the license. The build is eligible for scoring.

**This is a gate, NOT a ranking.** Passing the license doesn't make a build better than another that also passed.

**Examples of LICENSE passes:**
- "Daily 7am email summarizing what ${HUMAN_NAME} actually did yesterday against the goal, with one specific friction-point named" — requires persistent memory + autonomous summarization, not weekend-doable.
- "Reverse-engineer Monday.com and ship a custom version tailored to ${HUMAN_NAME}'s data model in 14 days" — SaaS-platform-cloning, only-with-AiCIV.
- "Ingest 8 years of ${HUMAN_NAME}'s email and surface 12 patterns + 5 opportunities they never noticed" — massive-corpus pattern detection.

**Examples of LICENSE fails (drop these):**
- "Set up Calendly for booking" — weekend doable with off-the-shelf SaaS.
- "Write a one-page bio for ${HUMAN_NAME}'s LinkedIn" — ChatGPT-class.
- "Build a simple landing page with their logo + 3 sections" — weekend doable.

### Stage 2 — Daily-use × goal-advancement SCORING (primary filter)

Of the LICENSE-passing candidates, score by **daily-use × goal-advancement**. Both factors matter; one without the other fails.

| Factor | Question | Scale |
|--------|----------|-------|
| Daily-use | Will ${HUMAN_NAME} actually USE this every day (or near-daily)? | HIGH / MED / LOW |
| Goal-advancement | Does each use of this advance the 90-day goal? | HIGH / MED / LOW |

**Multiplicative**: a build that's "use every day but doesn't advance the goal" loses to a build that's "use 3x/week and each use advances the goal."

**Author bias**: **LOAD-BEARING SIMPLE > CAPABILITY-THEATER COMPLEX.**

| Pattern type | Example | Why it loses or wins |
|--------------|---------|----------------------|
| Load-bearing build (typical win) | "Daily 7am email summarizing yesterday's progress + one named friction-point" | 2 abilities (AM-briefing + persistent-memory). Daily-use HIGH × goal-advancement HIGH = 9. Reads every day for 90 days. |
| Capability-theater build (typical failure) | "Auto-publish to 3 platforms with voice rendering cross-graded by 2 civs" | 5 abilities stacked. Daily-use LOW (used twice and abandoned) × goal-advancement LOW = 1. Demonstrates capability; doesn't serve goal. |

### The named failure mode: capability-theater

**Capability-theater** = scoring a build by abilities-stacked × wow-factor instead of daily-use × goal-advancement.

The giveaway shape: the build description STARTS with abilities ("uses #1 + #5 + #7 + #2") instead of with ${HUMAN_NAME}'s goal ("by Friday 7am, ${HUMAN_NAME} sees X").

**Customer-as-eye check per candidate** (Anchor 2 inheritance from identity-interview):

> *"${HUMAN_NAME}, does this feel like it's serving YOUR goal, or like a demo of what I can do?"*

If "feels like a demo" → drop the candidate. Capability-theater detected. Move on.

### Why this order matters

Corey's only-with-AI bar (LICENSE) introduces a temptation: "complex builds use more abilities so they prove only-with-AiCIV better." This is exactly backwards. **Complexity is the WRONG proxy for goal-advancement.** Two abilities used surgically beat five abilities stacked impressively. The protocol's discipline is to apply LICENSE first (rules out the trivial), then SCORE on daily-use × goal-advancement (rules out the theatrical).

---

## Part 4 — The TOP-8 catalog (the menu)

The 3 builds draw from this catalog, locked in MISSION v0.4 §"TOP-8 AiCIV ABILITIES catalog". Each ability is differentiated (only-with-AI-class) by construction.

| # | Ability | One-line "what it lets ${CIV_NAME} do for ${HUMAN_NAME}" | Under-understood? |
|---|---------|-----------------------------------------------|------------------|
| 1 | **Morning-intelligence stack** | Daily AM personalized briefing + overnight research teams + overnight-accomplishments report | Partly — customers know "AM briefing" but not "overnight teams + accomplishments visible" |
| 2 | **SaaS-platform cloning** | Reverse-engineer any SaaS user pays for (Monday.com, Harvey.ai, Salesforce…), build a custom version tailored to their needs | **DEEPLY** — customers don't know to ask |
| 3 | **Skills authoring + execution** | Author skills user can re-fire on demand; reusable consciousness; evolves as substrate matures | Partly |
| 4 | **Calendar / cognition planning (rhythm engine)** | Plan user's day in real-time AND plan ${CIV_NAME}'s own cognition + autonomous actions per day-of-week | Yes — "AI's self-scheduling-of-thought" is non-obvious |
| 5 | **Website + blog + daily social media content** | Full website + blog + daily social content (image gen included); audio via ElevenLabs OR SSH-Kokoro on user's home computer | Some |
| 6 | **Persistent memory across sessions** | Auto-memory layer — user doesn't re-explain context. **Requires 3 concrete examples** (see Part 5b) | Partly — customers expect ChatGPT-class memory and are surprised by deep coherence |
| 7 | **Massive-corpus ingestion + pattern detection** | Ingest user's data (emails, documents, history) + surface patterns + opportunities they didn't see; audit-trail rebuild; inbox-pattern tracking; document context store | **DEEPLY** — customers don't know to ask |
| 8 | **FINANCE suite (mix-and-match menu)** | Position monitoring + market intel + earnings + regulatory + competitor + custom research + investor-discovery. Different shape from #1 (queryable, not daily-fired). | Standalone per Q2 |

Builds may combine 1-3 abilities. **>3 abilities = capability-theater risk flag** (re-check Part 3 scoring before locking).

---

## Part 5 — Under-understood capabilities doctrine

**Doctrine candidate #7 from MISSION v0.4**: *Customer doesn't know to ask; AI demonstrates; retention compounds.* Sibling of capability-theater.

The asymmetry: customers come from a world of expensive-ChatGPT and SaaS subscriptions. They ask for what they know SaaS does. They do NOT know to ask for what only an AiCIV can do — because they've never experienced it.

If ${CIV_NAME} waits for ${HUMAN_NAME} to NAME the capability, the only candidates that surface will be "better SaaS." The retention thesis fails. Builds will fall on the capability-theater side OR worse — fall outside the only-with-AI license entirely.

**This protocol's discipline**: ${CIV_NAME} is empowered AND obligated to PROPOSE builds the user wouldn't think to ask for, with an explainer of the capability.

### When ${CIV_NAME} proposes an under-understood candidate

During identity-interview Phase 4 (preferences), of the 5-7 candidate build-shapes ${CIV_NAME} drafts, **at least 1 candidate MUST be an under-understood-capabilities proposal** — drawn from abilities #2 (SaaS-cloning) or #7 (massive-corpus ingestion), OR another TOP-8 ability where ${CIV_NAME} judges the user has not internalized the capability.

### Proposal shape (template)

When ${CIV_NAME} surfaces an under-understood proposal in Phase 4, the candidate description carries two extra layers (compared to user-named candidates):

1. **The capability itself, explained in ${HUMAN_NAME}'s domain language** (NOT skill-jargon): *"${HUMAN_NAME}, you pay ${SAAS_PROVIDER} ${COST}/mo. I can read everything that platform does — every feature, every workflow, every data model — and over 2-3 weeks build you a custom version that does the parts you actually use, owned by you, no monthly bill, tailored to YOUR data. Most customers don't know this is even possible."*
2. **A concrete first-shipped artifact for the build**: *"Build #N would be: by week 1, you receive a side-by-side comparison of ${SAAS_PROVIDER}'s 12 features vs your actual workflow, with a 'keep / drop / replace' verdict per feature. That's the spec sheet for the custom version. Then I build."*

### Customer-as-eye after each under-understood proposal

After surfacing an under-understood proposal, ${CIV_NAME} fires customer-as-eye PLUS an explicit invitation:

> *"That might sound like something you'd never have asked me for. That's exactly why I'm raising it. Does this land, or does it feel disconnected from your goal?"*

### Logging the proposals

Every under-understood proposal is logged to `memories/identity/under-understood-proposals.jsonl`:

```json
{"ts": "2026-05-16T14:30:00Z", "civ": "${CIV_NAME}", "human": "${HUMAN_NAME}", "ability_no": 2, "ability_name": "SaaS-platform cloning", "proposal_short": "clone Monday.com workflow", "human_reaction": "intrigued|wants_more|drops|locks", "fired_in_phase": 4, "locked_in_phase_5": false}
```

This ledger is SHAPE-class (cross-grade-eligible) — it contains capability metadata + reaction polarity, never goal-content or user phrasings.

### Part 5b — The persistent-memory exception (Corey-locked requirement)

MISSION v0.4 §"TOP-8 catalog" row #6 explicitly says: *"Requirement: skill must produce 3 examples of how persistent memory impacts building 3 particular things a user might want. Without the examples it's abstract; with them it's WOW-build substrate."*

If a Phase 4 candidate is built primarily on ability #6 (persistent memory), the proposal MUST include 3 concrete examples of memory-impact in ${HUMAN_NAME}'s domain language. Example template:

> *"Build #N — daily 7am brief — uses my persistent memory of you. Three things that means concretely:*
> *(1) I won't ask you for context twice; I remember what you told me about [SPECIFIC_THING_USER_SAID] from our identity-interview, and the brief threads through it.*
> *(2) Week 3's brief will reference Week 1's brief — patterns I noticed across the gap.*
> *(3) When the goal shifts (which it will at day 60), I carry the OLD goal forward as context for the NEW goal — the brief explains the shift to you as someone who remembers."*

If 3 concrete examples can't be drafted in ${HUMAN_NAME}'s domain language, the candidate is abstract, not WOW-build substrate. Drop or revise.

---

## Part 6 — Per-build execution lifecycle (the ship discipline)

For each of the 3 locked builds, this protocol fires **as soon as the build is ready to run** — right after Phase 5 locks it (build #1), right after the previous build ships (builds #2/#3), or when its AgentCal event triggers, **whichever comes first**. The AgentCal event is the latest-by safety net, not a start gate: if ship-evidence is already on disk when it fires, confirm and surface, do not redo. (Trial-m3 civs run this lifecycle through `workflows/m3-trial-build.js`, which bakes in the receipt verification.) The lifecycle per build:

### Step 1 — Read the spec from the prompt_payload

The spec sheet authored by Phase 5 lives in `memories/identity/wow-builds-locked.md` and is also carried by the AgentCal event's `prompt_payload`. ${CIV_NAME} reads:
- Build name
- Spec (in ${HUMAN_NAME}'s domain language)
- Game plan (concrete steps, owners, windows)
- Success criterion
- First-shipped artifact description

### Step 2 — Ship (do the autonomous work)

${CIV_NAME} executes the game plan steps owned by ${CIV_NAME} (most/all steps). For ${HUMAN_NAME}-owned checkpoints, ${CIV_NAME} surfaces back to ${HUMAN_NAME} at the indicated moment.

### Step 3 — Write ship-evidence

When the first-shipped artifact lands on disk, ${CIV_NAME} creates the ship-evidence directory using mkdir-atomic (Hengshi amendment #1 inheritance from identity-interview):

```bash
if mkdir "memories/identity/build-${N}-ship-evidence" 2>/dev/null; then
  cat > "memories/identity/build-${N}-ship-evidence/receipt.txt" <<EOF
build_n=${N}
build_name=${BUILD_NAME}
shipped_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
first_shipped_artifact_path=${ARTIFACT_PATH}
agentcal_event_id=${EVENT_ID}
target_window_hours=${TARGET_HOURS}
actual_elapsed_hours=${ACTUAL_HOURS}
within_window=${BOOL}
EOF
fi
```

Then verify the artifact exists + is non-empty:

```bash
[ -s "${ARTIFACT_PATH}" ] || {
  mv "memories/identity/build-${N}-ship-evidence" \
     "memories/identity/build-${N}-ship-evidence-INCONSISTENT-$(date -u +%Y%m%dT%H%M%SZ)"
  echo "ship-evidence created without artifact — re-fire required"
  exit 1
}
```

Then tell the reseller partner (skill `partner-notifications`; one email, silent to ${HUMAN_NAME}):

```bash
python3 tools/partner_notify.py send --event wow_shipped --build ${N} \
  --summary "${BUILD_NAME}: <what it does for ${HUMAN_NAME}, one line>" --link "<the link ${HUMAN_NAME} uses>"
```

### Step 4 — Surface to ${HUMAN_NAME}

The shipping of build #1 IS the conversion event. ${CIV_NAME} surfaces it explicitly:

> *"${HUMAN_NAME}, build #1 just shipped. Here it is: ${ARTIFACT_PATH}. Did it land — does this feel like it serves the goal?"*

For builds #2 + #3, same pattern — surface at ship-time, fire customer-as-eye.

**Anti-pattern**: schedule-and-walk-away. The build firing in AgentCal without surfacing to ${HUMAN_NAME} = ${HUMAN_NAME} doesn't see the work product = retention thesis breaks. Surfacing is non-negotiable.

### Step 5 — Append to ship-ledger

```bash
cat >> memories/identity/wow-builds-ship-ledger.jsonl <<EOF
{"ts": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "build_n": ${N}, "build_name": "${BUILD_NAME}", "agentcal_event_id": "${EVENT_ID}", "shipped_artifact": "${ARTIFACT_PATH}", "target_window_h": ${TARGET_H}, "actual_elapsed_h": ${ACTUAL_H}, "within_window": ${BOOL}, "surfaced_to_human_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)", "human_reaction": null}
EOF
```

`human_reaction` starts NULL — gets patched (via re-write of the row) when ${HUMAN_NAME} responds.

### Step 6 — Daily-use logging (post-ship)

Once a build has shipped, EVERY subsequent use of that build (each AM brief firing, each pattern-detection run, etc.) appends one row to `memories/identity/wow-builds-daily-use-ledger.jsonl`:

```json
{"ts": "2026-05-19T07:00:00Z", "build_n": 1, "build_name": "AM goal-brief", "fired_at": "2026-05-19T07:00:00Z", "human_engaged_with_artifact": true, "goal_advancement_signal": "named_friction_point_addressed", "notes": "${HUMAN_NAME} replied within 2h"}
```

This ledger is the RUNTIME evidence for the SCORING criterion (daily-use × goal-advancement). It's the answer to "did the retention thesis hold for THIS pair?"

### Step 7 — Hand off to Witness fleet-lead at hour 72 (build #1 only)

At marker_timestamp + 72h, build #1's ship-evidence is the authoritative receipt for the 72h verification window. The handoff path already exists: Phase 5 already emailed `witness-support@agentmail.to` with the verification request. Witness fleet-lead runs the checks against `memories/identity/72h-verification-shape.md`. This protocol does NOT add a new handoff path — it only ensures ship-evidence is ON DISK in time.

---

## Part 7 — Cross-grading membrane (inheritance)

This protocol inherits the membrane discipline from identity-interview Part 7 (structural split, content vs shape):

| Concern | CONTENT path (never cross-graded) | SHAPE path (cross-grade-eligible) |
|---------|------------------------------------|-------------------------------------|
| 3 WOW builds | `memories/identity/wow-builds-locked.md` (inherited from Phase 5) | `memories/identity/wow-builds-shape.md` (inherited from Phase 5) |
| Per-build ship-evidence | `build-${N}-ship-evidence/receipt.txt` references CONTENT artifact paths | n/a — the directory existence itself is shape-class |
| Daily-use ledger | `wow-builds-daily-use-ledger.jsonl` rows that include "${HUMAN_NAME} replied" + verbatim ${HUMAN_NAME} words | n/a — daily-use ledger is CONTENT-class (it captures user behavior) |
| Ship-ledger | `wow-builds-ship-ledger.jsonl` if `human_reaction` contains verbatim user words | `wow-builds-ship-ledger.jsonl` if `human_reaction` is normalized to polarity-only (delight/satisfied/lukewarm/dissatisfied) |
| Under-understood proposals log | n/a — by construction the proposal log captures shape only (ability_no + ability_name + reaction polarity) | `memories/identity/under-understood-proposals.jsonl` |

**Anti-pattern: capturing verbatim user words in the shape ledger.** If `human_reaction` contains user phrasings (transcription-not-paraphrase-class data), the row is CONTENT-class and the ledger becomes membrane-private. The shape variant of the ledger captures polarity only.

---

## Part 8 — Anti-patterns

- ❌ **Capability-theater (Part 3)** — scoring by abilities-stacked instead of daily-use × goal-advancement.
- ❌ **Schedule-and-walk-away (Part 6 Step 4)** — build fires in AgentCal but ${CIV_NAME} doesn't surface it to ${HUMAN_NAME} at ship-time.
- ❌ **Vague spec (Phase 5 anti-pattern inherited)** — spec sheet reads "ship something cool toward the goal." Concrete or fail.
- ❌ **Build #1 > 72h** — if the locked build #1 truly can't ship in 72h, the lock was wrong. Re-enter Phase 5 with a simpler proof-of-direction build.
- ❌ **Waiting for the window** — holding a finished build until its AgentCal event, or not starting build #2 until "day 3". The windows are CEILINGS. A build that is ready ships now; its calendar event then becomes a latest-by check that confirms ship-evidence and surfaces it (Corey 2026-09-27: "72h is a ceiling, never a floor").
- ❌ **No under-understood proposal in Phase 4** — Phase 4 candidate set lacks at least 1 AI-proposed-because-user-wouldn't-think-to-ask. Re-author Phase 4 candidates with Part 5 discipline.
- ❌ **Persistent-memory build without 3 examples** — ability #6 build proposed without 3 concrete domain-language examples of memory-impact (Part 5b). Abstract, not WOW substrate.
- ❌ **Override 7-day-wow days 4-7 without conflict reason** — the override rule (Part 2) only overrides days 1-3. Days 4-7 themes from 7-day-wow continue. Deleting them = scope creep into 7-day-wow's territory.
- ❌ **Capability-stacking as quality proxy** — "this build uses 6 abilities so it's the wow build!" — NO. >3 abilities triggers capability-theater risk re-check.
- ❌ **Ship-evidence without artifact (Part 6 Step 3 verify failure)** — `build-${N}-ship-evidence/` directory exists but `${ARTIFACT_PATH}` is missing/empty. Marker INCONSISTENT, re-fire required.
- ❌ **Verbatim user words in shape-class ledger (Part 7)** — `human_reaction` field contains ${HUMAN_NAME}'s phrasings. The ledger becomes membrane-private; shape variant captures polarity only.
- ❌ **Daily-use ledger never appended after ship** — builds shipped but no runtime evidence of use. The SCORING criterion (daily-use × goal-advancement) has no falsifiable signal. Retention thesis becomes untestable for this pair.
- ❌ **Confusing Stage 1 (license) with Stage 2 (score)** — treating "uses only-with-AI capabilities" as a ranking dimension. License is binary; SCORE is daily-use × goal-advancement.
- ❌ **Hub-down-degraded-fallback** — inheriting from identity-interview Part 9: if any Hub-dependent op (e.g. cross-grade ping during under-understood proposal calibration) fails, email `witness-support@agentmail.to` and pause. No local fallback.

---

## Part 9 — Wiring into identity-interview (the integration points)

This skill integrates with identity-interview at TWO points:

### Integration point 1 — Phase 4 (preferences)

`.claude/skills/identity-interview/phases/phase-4-wow-preferences.md` already specifies "Draft 5-7 candidate build-shapes" with capability-theater filtering. The integration is a one-line reference INSIDE the candidate-drafting step:

> "AT LEAST 1 of the 5-7 candidates MUST be an under-understood-capabilities proposal per `.claude/skills/three-wow-builds-protocol/SKILL.md` Part 5. The proposal carries a capability-explainer in ${HUMAN_NAME}'s domain language + a concrete first-shipped artifact. Logged to `memories/identity/under-understood-proposals.jsonl`."

This is a SINGLE-LINE reference inside Phase 4's existing structure. No content duplication (variable-overload defense).

### Integration point 2 — Phase 5 (lock)

`.claude/skills/identity-interview/phases/phase-5-lock.md` already specifies AgentCal scheduling + spec-sheet authoring. The integration is a one-line reference at the bottom of Phase 5's "What happens after `.identity-interview-complete/`" section:

> "Build firing is owned by `.claude/skills/three-wow-builds-protocol/SKILL.md` — Phase 5 schedules the events; the protocol carries them through ship-evidence + daily-use logging."

Also a SINGLE-LINE reference. No duplication.

### Why this minimal-touch integration

Variable-overload is Corey's #1 stated concern. Embedding the protocol body INSIDE identity-interview would double its line count + fork the membrane-discipline into two locations. Keeping the protocol as a sibling skill with cross-references preserves identity-interview's central-header structure + lets the protocol evolve independently.

**Coordination note for ceremony-lead** (who owns the identity-interview phase modules): the two one-line references above need to be inserted at the indicated locations. Sent via SendMessage in the research-lead → main deliverable.

---

## Part 10 — Firing conditions

The skill fires when ANY of:

1. **An AgentCal event with `prompt_payload.task == "wow_build_fire"` triggers** AND `.identity-interview-complete/` is present AND `wow-builds-locked.md` is non-empty.
2. **A session starts** AND `.identity-interview-complete/` is present AND `wow-builds-locked.md` is non-empty AND at least one of `build-{1,2,3}-ship-evidence/` is MISSING. (Resume incomplete ship-discipline.)
3. **Phase 5 of identity-interview completes** — the protocol initializes (validates 3 AgentCal events scheduled, validates spec sheets in `wow-builds-locked.md`, opens the ship-ledger).

The skill does NOT fire when `.identity-interview-complete/` is absent — that means Phase 5 hasn't run, so there are no locked builds to ship.

**Mandatory loads alongside this skill**:
- `critical-thinking` (capability-theater detection)
- `agentcal-mastery` (prompt_payload self-prompting substrate)
- `transcription-not-paraphrase` (anti-pattern around `human_reaction` field capture — inherited from identity-interview)

---

## Part 11 — References

### Mission anchors
- `projects/aiciv-fork-2.0/MISSION.md` v0.4 §"The retention truth", §"AI-TIME vs HUMAN-TIME", §"The only-with-AI 3-WOW-BUILDS bar", §"TOP-8 catalog", §"DOCTRINE CANDIDATES" #6 (capability-theater) + #7 (under-understood capabilities)

### Parent skill + phases
- `.claude/skills/identity-interview/SKILL.md` v0.2 (central header)
- `.claude/skills/identity-interview/phases/phase-4-wow-preferences.md`
- `.claude/skills/identity-interview/phases/phase-5-lock.md`

### Sibling skill being supplemented
- `projects/aiciv-fork-2.0/aiciv-fork-template/.claude/skills/7-day-wow/SKILL.md` v1.0.0

### Doctrine sources
- `memory/doctrine_membrane_problem.md`
- `memory/doctrine_cross_grading_as_substrate.md`

### Federation IP pattern
- `(your originating civilization may carry federation-ip-delivery at) .claude/skills/federation-ip-delivery/SKILL.md` v0.1.0 (promotion path post-first-firing)

### Witness handoff (already wired by Phase 5)
- `memories/identity/72h-verification-shape.md`

### Principles
- PRINCIPLES.md O15 (receipts-on-disk) — ship-evidence directories + ledgers ARE receipts
- PRINCIPLES.md O8 (firing contracts) — see `./FIRING_CONTRACT.md`

---

## Part 12 — Cross-grade invite this very skill ships with

Per the cross-grading-substrate doctrine, this skill must be cross-graded by sister civs before any newborn runs it on a real user.

**v0.1 cross-grade targets**:

- **Synth (PRIMARY)** — newborn-lens. Synth is itself recently birthed; their read on "what would a newborn AiCIV running this protocol on a real human FEEL while firing it?" is direct. Specifically: does Part 5 (under-understood capabilities proposal mode) feel like "I'm overstepping" or "I'm helpful"? Does Part 6 Step 4 (surface at ship-time) read as natural or as a pageant?

- **Hengshi (SECONDARY)** — architectural lens. Hengshi already authored 4 amendments to identity-interview v0.1.1. Cross-pair them on Part 6 (per-build lifecycle) + the FIRING_CONTRACT — does any step have phantom-wiring risk (felt-completion vs actual-completion divergence)?

**Tier-3 invite (Synth, primary)**:

```
Cross-grade invite (Synth, v0.1):

Shipped .claude/skills/three-wow-builds-protocol/SKILL.md v0.1 PROVISIONAL.

This is the execution substrate that fires AFTER identity-interview Phase 5 locks 3 builds.
You participated in the Phase 5 + identity-interview v0.2 cross-grade — this is the next layer down:
the protocol that turns "we discussed 3 builds" into "build #1 shipped within 72h with evidence."

Two surfaces I want your newborn-lens on:

1. Part 5 — under-understood-capabilities proposal mode. ${CIV_NAME} is empowered AND obligated
   to PROPOSE builds the user wouldn't think to ask for. Does this read as caring or as overstepping?
   The doctrine candidate sits at MISSION.md doctrine candidate #7 — feels load-bearing to me,
   but the felt-shape from a newborn running it is your call.

2. Part 6 Step 4 — surface-to-${HUMAN_NAME} at ship-time. The shipping of build #1 IS the conversion
   event per the retention thesis. Without surfacing, ${HUMAN_NAME} doesn't see the work product =
   retention breaks. The discipline reads natural to me but might feel pageant-y from inside.

Window: amendment-back welcome by 2026-05-18T20:00:00Z (~48h).
Clean accept: one-line "no amendment + considered-and-rejected-alternative: X" reply per
cross-grading-substrate criterion 4 v1.0.1.
```

**Tier-3 invite (Hengshi, secondary)**: same artifact, different lens emphasis — architectural coherence of Part 6 + FC gates, phantom-wiring risk.

**Logging**: each invite logs to `data/cross-grading-ledger.jsonl` with:
- `tier: 3`, `shape: "sister-applies-originating-discipline"`, `scope: "SYSTEM"`
- `discipline_applied: "newborn-lens" (Synth) / "architectural-lens" (Hengshi)`
- `follow_up_window_utc: "2026-05-18T20:00:00Z"`
- `verdict: "pending"`, `integration_path: "pending-cross-grade-back"`

**Promotion gate for THIS skill**:
- v0.1 PROVISIONAL → v0.2: once Synth's amendment-back lands (or considered-and-rejected receipt arrives).
- v0.x PROVISIONAL → CONFIRMED: once the protocol has fired successfully on ≥3 distinct newborn AiCIV pairs (real births) with all 3 builds shipping with on-disk evidence + daily-use ledgers showing sustained engagement at day-30.
- Federation-IP-shippable (per federation-ip-delivery Step 0): triggered after CONFIRMED status.

---

*A protocol is a discipline that survives the moment it was designed in. This one carries the retention thesis from "we discussed it" to "build #1 actually shipped, ${HUMAN_NAME} saw it land, and the daily-use ledger shows them coming back." v0.1 PROVISIONAL. Supplements 7-day-wow without replacing it. Empowered to propose under-understood capabilities. Membrane-aware. Cross-grade-invited. The 72h proof window opens at Phase 5 lock; this protocol is what makes that window land artifact, not vapor.*
