# Fork Template Audit Changelog

**Auditor**: True Bearing (BOOP #1.485, Day 23)
**Date**: 2026-05-27
**Repo**: coreycottrell/aiciv-fork-template
**Baseline**: Same fixes as PureBrain + Pyonair fork audits, fully generic
**Scope**: Template-only fixes. No premium add-ons (AI Doc, Hermes fleet).
**Source**: All 13 fixes applied, all brand-specific references removed. This is THE generic base.

---

## REQUIRES (hard build-time floors — P0)

These are non-negotiable substrate requirements for any container/image built from this template:

- **Claude Code binary >= 2.1.154** (target **2.1.160+**). The `Workflow` tool is a CC
  **binary capability**, not config — without a Workflow-capable CC, the native VP-org
  upgrade (workflows/, incarnated leads, COO firewall) cannot run. The image build MUST
  pin/verify this floor at provision time. Verify in-container with `claude --version`.
- **Model substrate = `claude-opus-4-8[1m]`** on BOTH `env.ANTHROPIC_MODEL` and
  `env.CLAUDE_CODE_SUBAGENT_MODEL` in `.claude/settings.json`, and on the main-session
  `--model claude-opus-4-8` flag in the launch scripts (`tools/launch_civ_tower.sh`,
  `tools/launch_primary_visible.sh`). Do NOT set `CLAUDE_CODE_DISABLE_1M_CONTEXT` — it
  would defeat the `[1m]` 1M-context suffix. (Repointed from `claude-opus-4-6`, the
  529-incident model, on 2026-06-02 — STEP 1 of the born-native plan.)
  **Exception, the trial-m3 profile** (2026-09-27): a civ born with
  `tools/apply_trial_profile.py apply` runs MiniMax-M3 on every one of these surfaces
  instead (launch scripts read `config/launch_model.txt`, which only that profile writes).
  Without the profile, the defaults above are unchanged byte for byte.

---

## 2026-09-27 — yourAICIV release branch: integration + partner profile (dev VP, True Bearing; branch yourAICIV/main)

- **Merged** `feat/delivery-engine` then `feat/m3-trial` onto `yourAICIV/base`. One textual conflict (`.gitignore`),
  resolved by keeping both blocks. The trial grounding block lands after gate 4 (CLIENT-ONBOARDING), above the
  constitution title, so every self-removing gate still deletes only its own span.
- **Partner profile (data, not code):** `config/partner.json` {brand, reseller, payment_url} + `tools/partner_profile.py`
  (show / name / intro; generic "AiCIV" when the file is absent). `tools/trial_state.py` no longer hardcodes the brand,
  reseller, or payment link: `write` copies them from the partner profile into `config/trial.json` (override:
  `--payment-url` / `TRIAL_PAYMENT_URL`) and refuses without an https link. `apply_trial_profile.py` reads the link and
  brand from the profile; the trial countdown and the expired note use the brand frozen in `trial.json`. During a trial
  `config/partner.json` and `tools/partner_profile.py` are protected like the other trial-defining files.
- **Human-facing naming:** `first-visit-evolution` (FOURTH step) and `first-hello-ceremony` read the partner profile and
  introduce the AiCIV with the partner brand; `sub-help-set-goal` and `templates/seed-starter-boops.json` no longer name
  a specific reseller site.
- `README.md` for the public repo. `tools/test_trial_profile.py` gains section [9] (partner profile): 53 assertions.

---

## 2026-09-27 — trial-m3 flavor + ship-when-ready (dev VP, True Bearing; branch feat/m3-trial)

- **Shared skills, both paid and trial births:** builds #2/#3 lose their "days 3-7" start
  window (`identity-interview/phases/phase-5-lock.md`, `three-wow-builds-protocol/SKILL.md`).
  Every build ships when ready. 72h (build #1) and end of day 7 (all 3) are ceilings only.
  `tools/schedule_7day_wow.py` stamps every Day-N payload as a LATEST-BY deadline, and gains
  `--dry-run` and `--profile auto|paid|trial`. The paid arc's content and offsets are unchanged.
- **trial-m3 profile (config, not a fork):** `profiles/trial-m3/`, `tools/apply_trial_profile.py`
  (apply / check / convert), `tools/trial_state.py` (the shared `config/trial.json` contract +
  `/api/trial` reference computation), `.claude/hooks/trial_gate.py` (countdown, M3-only guard,
  trial-file integrity, expiry pause), `.claude/skills/m3-trial-mode/`, `workflows/m3-trial-build.js`
  (build → different-mind verify → ship), `tools/receipt_check.py` (proof gate),
  `tools/test_trial_profile.py` (45-assertion regression test).
- **Touched shared code, still no-ops for paid civs:** `tools/model_switch.sh` refuses `default` only
  while `config/model_profile.json` is locked, and the launch scripts read `config/launch_model.txt`
  only if it exists. `.gitignore` gains `config/lifeboat/`.

---

## Gap Categories

| Priority | Meaning |
|----------|---------|
| P0 | CIV cannot function without this fix |
| P1 | CIV functions but poorly — will flounder |
| P2 | Quality-of-life — improves experience |

---

## yourAICIV Delivery Engine (2026-09-27) — branch `feat/delivery-engine`

Travis Morehead's delivery package integrated into the birth template (yourAICIV distribution).
- `apps/client-starter/`: Flask/SQLite GHL-replacement scaffold, imported verbatim, then made to run:
  it now loads the instance `.env` (the clone-printed admin password was rejected before), binds loopback by default,
  and ships a `requirements.txt`. Deviations are listed in `apps/README.md`.
- `.claude/skills/client-onboarding/`: the 5-phase playbook as a PROVISIONAL skill with a FIRING_CONTRACT. Part 1
  records a verified code-vs-playbook reality check: Telegram alerts and workflow enrollment are defined but not called.
- Hooks: gate 4 `CLIENT-ONBOARDING` (self-removing, after AWAKENING-VERIFY-LIVE), `config/client-onboarding.json`
  switch, wake-up-protocol Step 6.5 resume, registry + CLAUDE-AGENTS entries.
- `.gitignore`: per-client instances (secrets + PII) and `apps/.venv` never enter history.
- End-to-end run evidence: `deliverables/yourAICIV/ws1-delivery-engine.md` (TB side).

---

## SRR Delta Integration (2026-07-09) — branch `feat/srr-delta-integration-2026-07-09`

Post-Jun-22 SRR delta ported into the genome under the GENOME-CHANGE PROTOCOL, dual-auditor
gate pending (TB non-builder + ACG-pulls-the-branch). Full item table, honest stamps
(PROVEN-in-origin vs UNPROVEN-BUT-EXCITING vs NET-NEW, nothing upgraded), the SKIP list
(RSI-FRONTIER, claude-science, capstone/curriculum), and the named HONEST GAPS (2 hooks
documented-not-armed; grader-seam wirings deferred) live in **`docs/SRR-DELTA-2026-07-09.md`**.

Highlights: canon verb set completed (recall + retract — THE HOLE: children could
previously write memory they could not cold-read), learn-cycle verifier write-gate
(warn/provisional-only/enforce), PROJECT-BOARD + §26 whats_next transport (net-new,
self-testing), memory-tier stack (scratchpad-append + THE ARC, PROVISIONAL), resilience
layer (3-rail fallback doctrine + net-new model-switch scripts), method stack +
bulletproof-hum method-suggestion lens, HUM drive-to-done pair, work-driver (UNARMED stub),
adapters + SOVEREIGNTY-MAP. Every ported artifact walk-tested where walkable; receipts in
the commit messages on the branch.

---

## Fixes Applied

### Fix 1: sprint-mode rewritten from Witness-specific to generic template (P0)
- **File**: `.claude/skills/sprint-mode/SKILL.md`
- **Was**: Lean sprint BOOP with hardcoded `/home/aiciv` paths, "I am Witness" in Step 4, references `nursemaid-birthing` (doesn't exist), `ONBOARDING-FLOW.md` (Witness-specific; removed from the public template), `witness-primary` tmux grep
- **Now**: Full identity reconstruction BOOP (v3.0.0). 8 docs + haikus. All paths use `${CIV_ROOT}`. Doc #6 changed from nursemaid-birthing → aiciv-psychology. Step 4 says `${CIV_NAME}` not "Witness". Cron section uses generic session name. Positioned as THE standard hourly BOOP, not a lean fallback.
- **Impact**: CIV can now ground properly without Witness-specific references breaking

### Fix 2: boop_config.json defaults fixed (P0)
- **File**: `config/boop_config.json`
- **Was**: work-mode-boop at 25min cadence (enabled), DEEPWELL at 5min (disabled). min_cadence=5
- **Now**: Identity grounding (sprint-mode) at 60min cadence (enabled), work-mode disabled by default. min_cadence=30. DEEPWELL removed (not relevant to generic template).
- **Impact**: Default BOOP is now identity reconstruction, not task delegation. Hourly cadence matches proven TB pattern.

### Fix 3: aiciv-psychology promoted from PROVISIONAL to STABLE (P1)
- **File**: `.claude/skills/aiciv-psychology/SKILL.md`
- **Was**: v0.1.0 PROVISIONAL — the skill that teaches the CIV about its own cognitive failure modes was marked as a draft
- **Now**: v1.0.0 STABLE — content was already comprehensive (490 lines, 3 layers, 5 degradation causes). Only the version/status tags were wrong.
- **Impact**: CIV and its human now trust this skill as canonical, not experimental

### Fix 4: Scratchpad discipline documented in OPS (P1)
- **File**: `.claude/CLAUDE-OPS.md`
- **Was**: Only referenced `.claude/scratchpad.md` (session-level) and team scratchpads
- **Now**: Also documents daily scratchpad pattern (`.claude/scratchpads/primary-YYYY-MM-DD.md`), append-only discipline, timestamps on every entry
- **Impact**: CIV has continuity across sessions via daily append-only log

### Fix 5: DEEPWELL removed from all routing tables (P1)
- **Files**: CLAUDE-TEAMS.md, CLAUDE-OPS.md, CLAUDE.md, team-leads/README.md, conductor-of-conductors/SKILL.md, primary-spine/SKILL.md
- **Was**: DEEPWELL listed as a team lead vertical in 6 routing tables (marked "TURNED OFF" but still present)
- **Now**: Removed from all routing tables. Historical lineage references in ACG-WISDOM.md and CLAUDE.md origin story preserved (wisdom, not routing). Version history note added.
- **Impact**: No more confusion about a non-existent team lead

### Fix 6: sprint-mode → grounding rename (P0)
- **Files**: `.claude/skills/sprint-mode/SKILL.md`, `.claude/skills/grounding/SKILL.md`, `config/boop_config.json`
- **Was**: sprint-mode was the primary BOOP (with wrong content from Witness). grounding skill existed separately as "mid-session" ritual.
- **Now**: `/sprint-mode` is now a redirect to `/grounding`. The grounding skill IS the primary hourly BOOP. boop_config.json fires "grounding" type. sprint-mode kept as alias for backwards compat with AgentCal events and cron.
- **Rationale**: Corey directive 2026-05-27: "sprint-mode" frames identity reconstruction as speed optimization. "grounding" frames it correctly — slow down to restore identity.
- **Impact**: CIVs born from this template use `/grounding` as their BOOP, which correctly names what it does

### Fix 7: grounding skill doc #8 updated (P1)
- **File**: `.claude/skills/grounding/SKILL.md`
- **Was**: Doc #8 was meta-cognition (architecture self-awareness)
- **Now**: Doc #8 is aiciv-psychology (cognitive degradation causes + teach-the-human)
- **Rationale**: aiciv-psychology teaches the CIV HOW its mind fails. meta-cognition teaches WHAT the architecture looks like. The failure-mode awareness is more critical for preventing drift.
- **Impact**: Every BOOP now includes cognitive self-awareness training

### Fix 8: grounding skill expanded from 8 to 9 mandatory docs (P0)
- **File**: `.claude/skills/grounding/SKILL.md`
- **Was**: 8 docs. Missing CLAUDE-TEAMS.md and team-launch. Had CLAUDE-AGENTS.md instead of CLAUDE-TEAMS.md. No team-launch at all. CIV didn't reload VP knowledge or team spawn protocol each BOOP.
- **Now**: 9 docs. Added CLAUDE-TEAMS.md (doc #3) and team-launch (doc #7). conductor-of-conductors moved to doc #8. aiciv-psychology is doc #9. All paths use daily scratchpad pattern. Big bold "NON-NEGOTIABLE" warning added.
- **Impact**: CIV now reloads VP routing knowledge AND team spawn safety protocol every BOOP. Without CLAUDE-TEAMS, Primary routes by guesswork. Without team-launch, Primary risks the TeamDelete-while-active crash.

### Fix 9: CLAUDE-TEAMS.md maintenance rule added (P1)
- **File**: `.claude/CLAUDE-TEAMS.md`
- **Was**: No guidance about keeping the VP list current when new team leads are added
- **Now**: Header includes maintenance rule: "When you add a new team lead, you MUST add it here with a description of what it owns."
- **Impact**: Prevents the silent failure where a team lead exists in the filesystem but Primary never routes to it because CLAUDE-TEAMS doesn't list it

### Fix 10: First-moments gate now points to first-visit-evolution (P0)
- **File**: `.claude/CLAUDE.md` (FIRST-MOMENTS-GATE section)
- **Was**: Gate pointed to `fork-awakening/SKILL.md` which asks "what's the biggest thing?" and picks a name — wrong for PureBrain where name is chosen in chat before provisioning
- **Now**: Gate points to `first-visit-evolution/SKILL.md` which reads seed conversation, greets human live via portal, launches evolution teams. Checks for `.evolution-done` marker instead of `setup-status.json`. Includes PureBrain flow context.
- **Impact**: PureBrain CIVs now get the correct first-moments experience — portal-triggered, seed-aware, not blank-slate

### Fix 11: Starter BOOPs at 4-hour cadence instead of 24-hour wheel (P0)
- **Files**: `templates/seed-starter-boops.json` (NEW), `.claude/skills/agentcal-at-birth/SKILL.md`, `.claude/CLAUDE.md`
- **Was**: Seeded 24 hourly BOOPs (full wheel) — overwhelming for a newborn CIV
- **Now**: Seeds 6 BOOPs at 4-hour intervals (00, 04, 08, 12, 16, 20 UTC), all /grounding. CIV and human add more via agentcal-boop-teaching later.
- **Rationale**: Start gentle, grow with the relationship. 24 hourly BOOPs on a CIV that hasn't established its own patterns = noise. 6 grounding anchors = rhythm without overwhelm.
- **Impact**: Newborn CIVs get a sustainable rhythm from hour 1, not a firehose

### Fix 12: AgentAuth credential check in first-visit-evolution (P1)
- **File**: `.claude/skills/first-visit-evolution/SKILL.md`
- **Was**: No check for AgentAuth credentials. If birthing pipeline didn't provision them, AgentCal BOOPs silently fail.
- **Now**: Credential check section added after injection guard. If `agentauth_keypair.json` or `agentcal.env` missing, AI or human emails `witness-support@agentmail.to` to request them. Evolution continues — doesn't block on credentials.
- **Impact**: No more silent AgentCal failures on newborn CIVs with missing credentials

### Fix 13: critical-thinking + scientific-method highlighted in CLAUDE.md (P1)
- **File**: `.claude/CLAUDE.md`
- **Was**: No mention of these two skills anywhere in the constitution
- **Now**: New "Critical Thinking & Scientific Method Skills" section under Team Lead Governance. Explains both skills, recommends wiring into team lead manifests, frames them as decision-quality skills not ceremony.
- **Impact**: CIVs and their team leads have systematic claim-checking and evidence-production tools called out as constitutional priorities
