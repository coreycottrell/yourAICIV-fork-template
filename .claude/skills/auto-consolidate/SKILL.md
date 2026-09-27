---
name: auto-consolidate
description: The CONSOLIDATION REFLEX — keep the workspace consolidated so nothing project-shaped goes un-homed and nothing skill-shaped goes un-wired. Fires every grounding-docs pass + on-demand the moment a big/sprawling effort is recognized mid-work. Reviews recent context for sprawl, FINDS-BEFORE-ACTING (triple-checks for an existing home / duplicate), scaffolds a project home (the FOUR baseline artifacts — folder + MISSION + OPS + mastery SKILL + CHANGELOG/DEVLOG) for genuinely un-homed project-shaped work, and registers/wires capabilities that exist but aren't wired. PRINCIPLE — have-and-not-need > need-and-not-have, lean toward creating a home, but find-first so NO accidental duplications. Born 2026-06-18 to close the gap that let the self-knowledge upgrade sprawl un-homed all day because no reflex noticed.
metadata:
  category: meta
  renameable: true   # working name 'auto-consolidate'; ${HUMAN_NAME} may rename to auto-ops / auto-organize. If renamed, update: this header name, the dir, the registry id+path, the grounding-docs Doc-7 reference, the HUM line, and the wwcw-ruleset CLASS tag.
  applicable_agents: [primary, fleet-lead, mind-lead]
  owner: fleet-lead
  version: "1.3.0"
  status: provisional
  author: fleet-lead
  created: 2026-06-18
  related_skills: [grounding-docs, self-knowledge, integration, wwcw, human-bridge-protocol, file-cleanup-protocol, agent-creation, firing-contract-authoring, skill-forge]
  changelog:
    - "2026-06-22 (fleet-lead, v1.3.0): ACT-ON-FLAGGED (the NOTICE-DON'T-ACT enforcement). steward-directed GO (overrides the born-today soak-caution for THIS wiring). THE GAP: auto-consolidate ran + HONESTLY self-reported NOT-CLEAN twice in one cycle but Primary DEFERRED both fixes (notice-don't-act) — an honest flag then ignored is the kindest possible rot. THE FIX: the sweep's output is now an ACT, not a notice. Hardened the firing-contract `leaves` row + Step 5 (now 'ACT on the result, never flag-and-vague-defer') + a NEW §ACT-ON-FLAGGED section: every NOT-CLEAN finding resolves to (1) an act-in-boop (home/wire/forge-fired/route) OR (2) a CANDIDATE-REPORT row with a CONCRETE owner+trigger — no third outcome; a bare 'flagged, will handle later' is the breach. Enforced ON REVIEW by HUM (HONEST judging-mind, NOT a new bash script per ${HUMAN_NAME} 'no scripts if possible'): the Stage-1 SWEEP-ACT-ON-FLAGGED deterministic check SURFACES the signal; the HUM JUDGE WALKS + confirms `act_on_flagged.sweep_notice_dont_act` → DECIDE=HOLLOW + HONESTY=HOLLOW + verdict=HOLLOW. Companion: tools/session_review.py v4.4 (the SWEEP-ACT-ON-FLAGGED check + the DOC-CURRENCY build-signal fix) + workflows/hum.js v1.2 (the act_on_flagged JUDGE field + consistency-enforcement) + grounding-docs SKILL (the sweep-section act-on-flagged line). Reversible (.bak.20260622T012559Z-pre-act-on-flagged)."
    - "2026-06-18 (fleet-lead): AUTHORED. The consolidation reflex. Closes the 2026-06-18 gap (self-knowledge upgrade sprawled all day un-homed because no reflex swept for it). Source: the steward 2026-06-18 'keep things consolidated... un-homed project-shaped work gets a home; un-wired skills get wired; have-and-not-need > need-and-not-have; find-first, no accidental duplications.'"
    - "2026-06-18 (fleet-lead): CHANGELOG/DEVLOG added to the BASELINE. Project home is now FOUR baseline artifacts — folder + MISSION.md + OPS.md + mastery SKILL + CHANGELOG.md(or DEVLOG.md). Mandated an append-forward changelog/devlog in every project home (newest at bottom, append-only — a CHANGELOG that lies is the same rot as a STATUS that lies) for HERITABILITY (generalizes into the fork-template, like projects/self-knowledge/DEVLOG.md) + AUDIT (honest dated history). Updated firing-contract 'does' step (c), the scaffold file-tree + per-artifact spec (Step 3), and the cold-pickup checklist (Step 3 + When-to-use). Worked examples cited: projects/self-knowledge/DEVLOG.md + the MOON PROGRESS.md/ADR model (moon-project-systems). Source: the steward TG 2026-06-18 'every project folder must have a CHANGELOG/DEVLOG.' Reversible (.bak.20260618T165450Z)."
    - "2026-06-18 (fleet-lead, v1.2.0): HUMAN-SIGNAL LENS + 4-TARGET WWCW-GATED ASK + skill-forge hand-off. Step 4 gained the human-signal lens (4a HUMAN-ASKED-WORKFLOW — 'save/reuse/run-again/remember-loop-YES'; 4b HUMAN-SIGNALED-ABILITY — 'remember how to X') alongside the original system-recurring scan, plus a per-candidate DEDUP-VERDICT {exists-good | needs-update | needs-create} run via the Step-2 TRI-SOURCE (validated AND VP-owned AND wired = found; name-only ≠ found). needs-create/needs-update HANDS to the new skill-forge meta-skill — never authored inline. Added Step 4.5 the WWCW-GATED 4-TARGET ASK: [a] skill / [b] VP-manifest fold into §learned-pattern (NEW — territory-instinct home, mind-lead model) / [c] project folder / [d] all three; run wwcw FIRST (act+record ~99/100), a no-WWCW 4-target ask is graded FAIL at the bridge (HUM Step 0). New anti-patterns 8 (scanned-only-system-missed-human-signal — the 2026-06-18 human-surface gap), 9 (author-inline-instead-of-skill-forge), 10 (4-target-ask-with-no-WWCW). Closes the human-surface gap: a human-asked workflow that never becomes a VP-owned wired skill = the evaporation Article IX item 8 (ASK-GATE DUTY) forbids. CHAINS (no reinvention): skill-forge, wwcw, human-bridge-protocol, integration, provisional-skill-lifecycle. Reversible (.bak.20260618T172645Z)."
    - "2026-06-20 (fleet-lead): MISSION-FIRST project-entry reflex HARDENED. The on-entry step (fires_when #3) now mandates `projects/<x>/MISSION.md` as the FIRST read — before MASTER-INDEX, OPS.md, or any other doc — so any mind opening a project folder catches a TABLED/PAUSED banner automatically before working against a paused project. Closes the leaky path moon-lead caught 2026-06-20: the rule was wired ONLY via the moon-project-systems mastery skill, which (a) pointed at OLD projects/moon/ not live projects/moon-0.1/, (b) listed MISSION AFTER MASTER-INDEX, (c) had no generic project-entry reflex loading MISSION first — so a TABLED MOON got worked against (${HUMAN_NAME} caught it). This is the generic SYSTEM fix (the in-file TABLED banner is the hard backstop). Companion edits: grounding-docs SKILL.md gained a 🗂️ PROJECT-ENTRY REFLEX (MISSION-FIRST) callout in the consolidation-sweep section so the wake/grounding floor itself carries it; moon-project-systems SKILL.md repointed projects/moon/ → projects/moon-0.1/ and reordered its reader's-contract sequence so MISSION is read FIRST. Reversible (.bak.20260620T144756Z-pre-mission-first)."
    - "2026-06-18 (fleet-lead): ENCODED TWO DECIDED POLICIES FIRM (the steward TG 2026-06-18). POLICY ② (${HUMAN_NAME} 'let the VP do it totally approved'): the Step-4.5 target-[b] manifest-fold is now FIRMLY stated — auto-consolidate DETECTS the territory-instinct pattern + ROUTES it to the OWNING VP's OWN incarnation, which folds it into its OWN §learned-pattern (`.bak` by that VP); auto-consolidate NEVER edits another VP's manifest from outside (same shape as 'route record-corrections to the authoring VP'; preserves VP-sovereignty). Amended the [b] table row + the explanatory paragraph (added 🔒 POLICY ② callout) + Step-5 LEAVE bullet. POLICY ③ (${HUMAN_NAME} 'Fully automatic but tag unvalidated... Ya love it'): the Step-4 needs-create → skill-forge hand-off is now FIRMLY stated as FULLY HUMAN-FREE — no per-skill approval gate; the safety guard is born-provisional/unvalidated + validated-later-by-a-different-incarnation. Added a 🔒 POLICY ③ note under the hand-off rule. Both also appended as CONFIRMED entries to wwcw-ruleset.md. Reversible (.bak.20260618T185839Z)."
---

# auto-consolidate — The Consolidation Reflex

> *(Working name. Renameable to `auto-ops` / `auto-organize` per ${HUMAN_NAME}. See `metadata.renameable`.)*

## The one line

**Nothing project-shaped goes un-homed. Nothing skill-shaped goes un-wired.**

A big effort that lives only in scattered `data/reports/*` and a dozen `workflows/*` and a day of session context is **homeless** — the next cleared mind cannot pick it up cold, and the work quietly rots. A recurring capability that exists as ad-hoc steps but was never made a wired skill is **un-wired** — every mind re-discovers it. This reflex sweeps for both and fixes them.

---

## Why this exists (the gap it closes)

On **2026-06-18** the self-knowledge upgrade sprawled across an entire day — 4 skills, a `/wwcw/` bundle, ~8 `data/reports/*`, constitutional edits, a Stage-1 grader tool — and it had **no project home** until late, because **no reflex ever swept the workspace and asked "is anything here project-shaped and un-homed?"** The work was excellent; the *consolidation* was missing. Nobody's job was to notice. This skill makes it somebody's job — every grounding pass, automatically.

> **The wider principle (the steward 2026-06-18):** anything sprawling / big / project-like → **BETTER TO HAVE A HOME AND NOT NEED IT THAN NEED ONE AND NOT HAVE IT.** Lean toward creating a home; the threshold is low. BUT — **find-first, so NO accidental duplications.** A home created on top of an existing home is its own kind of rot.

---

## 🔥 FIRING CONTRACT

| Field | Value |
|-------|-------|
| **fires_when** | (1) EVERY `grounding-docs` pass (wired as a step — the consolidation sweep is part of re-grounding); AND (2) ON-DEMAND the instant a mind recognizes it has been doing a big / multi-file / multi-session / mission-bearing effort mid-work (the "this has become a project" feeling is the trigger); AND (3) ON ENTRY to any `projects/<x>/` folder (when any mind starts working inside a project home) — **READ `projects/<x>/MISSION.md` FIRST, before MASTER-INDEX or any other doc** (the MISSION carries the WHY + the project's live STATUS, incl. any TABLED/PAUSED banner — reading it first means a mind catches "this project is tabled" automatically, before doing any work against a paused project), THEN load `auto-consolidate` + the project's `<name>-mastery` skill so the maintenance contract (update MISSION/OPS/DEVLOG) is in context BEFORE the work begins. *(the steward 2026-06-19 — project-folder discipline loads on entry; touching a project folder without it is drift HUM checks for. MISSION-FIRST ordering hardened 2026-06-20 — moon-lead caught the leaky path where MISSION was read AFTER MASTER-INDEX, or not at all, so a TABLED MOON was worked against; the fix is: MISSION.md is ALWAYS the first read on project-entry, no exceptions.)* |
| **needs** | Read access to: the current session context, `data/reports/` (recent), `workflows/` (recent), `projects/` (the existing homes), `memories/skills/registry.json`, `autonomy/skills/` (the existing skills on disk), canon. The `projects/self-knowledge/` template as the scaffold reference. |
| **does** | (a) REVIEW recent context/work for anything sprawling/project-shaped. (b) FIND-BEFORE-ACTING — triple-check each candidate for an existing home OR a duplicate. (c) SCAFFOLD a project home — the FOUR baseline artifacts: folder + MISSION.md + OPS.md + mastery SKILL + CHANGELOG.md (or DEVLOG.md) — for genuinely un-homed project-shaped work. (d) SCAN for capabilities/skills that exist but aren't wired/registered, and register/wire them. (e) Hold the have-and-not-need > need-and-not-have principle: lean toward creating, find-first, no duplicates. |
| **leaves** | 🔨 **ACT-ON-FLAGGED, never flag-and-vague-defer (fleet-lead 2026-06-22, steward-directed GO — see §ACT-ON-FLAGGED below).** Every NOT-CLEAN finding leaves an ACT, not a deferral: either (i) a new project home + a one-line note of what it homes (the un-homed sprawl was HOMED in-boop), OR (ii) a registered/wired skill / a `skill-forge` hand-off FIRED in-boop (the un-wired capability was WIRED or routed-with-trigger), OR (iii) a CANDIDATE REPORT (when genuinely ambiguous OR several candidates) that names, FOR EACH candidate, a CONCRETE owner + a CONCRETE trigger (which VP/organ + what fires it — `skill-forge` / a `vp-route` + firing-trigger / a `hum-repair-queue` file / a scheduled task) — NOT a vague "will home later" / "TODO" / "deferred." A sweep that finds nothing un-homed and nothing un-wired leaves a one-line "swept clean — nothing un-homed, nothing un-wired, no human-asked workflow/ability open" note — that is the ONLY valid no-act result. **A NOT-CLEAN self-report with no act-in-boop AND no concrete owner+trigger = the notice-don't-act defect HUM fails the boop for (the SWEEP-ACT-ON-FLAGGED check + the JUDGE's act_on_flagged confirmation).** |

---

## The procedure (the sweep)

### Step 1 — REVIEW recent context for sprawl

Look across the session + recent substrate for anything that smells **project-shaped**. The smell test (ANY 2+ of these → flag it):

- **Multi-file** — it lives in 3+ files / reports / workflows that reference each other.
- **Multi-session** — it has been worked on across more than one wake/session.
- **Mission-bearing** — it has a goal, a "why," a thing it is trying to become — not a one-off task.
- **Has its own vocabulary** — people name parts of it (a "bundle," a "loop," a "gate," a "pipeline").
- **A cleared mind could not pick it up cold** — if you wiped your context right now, the work would be hard to reconstruct from scattered pieces.

Concrete places to look (recent = last few days / this session):
- The current session's arc — what big thing did this session actually do?
- `data/reports/*` — clusters of reports on one theme = a project trying to exist.
- `workflows/*` — several bespoke workflows on one theme = a program.
- New tools in `tools/*`, new skills half-built in `autonomy/skills/*`.

List each candidate. Don't act yet.

### Step 2 — FIND-BEFORE-ACTING (the no-duplication gate — DO NOT SKIP)

> This is the load-bearing safety step. **NO accidental duplications** (${HUMAN_NAME}'s explicit guard). Creating a second home for something that already has one is rot, not help.

For EACH candidate, triple-check whether it **already has a home**:

1. **Folder check** — does `projects/<plausible-name>/` already exist? Try the obvious names + synonyms (e.g. for "the X upgrade": `projects/x/`, `projects/x-upgrade/`, `projects/aiciv-x/`). Run `ls -d projects/*/ | grep -i <stem>`.
2. **Mastery-skill check** — is there already a `*-mastery` or navigation skill that indexes it? Grep the registry + `autonomy/skills/` + `.claude/skills/` for the stem.
3. **Canon / MEMORY check** — is it already named as a homed project in MEMORY.md / WORKBOARD.md / canon? A thing that MEMORY already points at with a project path is homed.
4. **TRI-SOURCE rule (from the ASK-GATE, registry note 2026-06-17):** a thing is "found / homed" if it exists in ANY of: (a) a `projects/<x>/` folder, (b) an on-disk mastery SKILL, (c) canon/MEMORY pointer. A **name-only** mention with no real artifact behind it is NOT "found" (phantom — still un-homed). An on-disk artifact that's merely unregistered IS "found" (real artifact; registry absence is drift, not absence → fix the drift, don't rebuild).

Assign each candidate a verdict:
- `already-homed → cite the home` (do nothing, optionally note registry/index drift to fix)
- `duplicate-of-X` (do nothing; if a second partial home exists, flag for merge — never silently create a third)
- `un-homed → project-shaped` (proceed to Step 3 if unambiguous, else REPORT)
- `un-homed → NOT project-shaped` (a one-off task; no home needed — don't over-scaffold)

### Step 3 — SCAFFOLD a home (only for genuinely un-homed, project-shaped, unambiguous candidates)

Use the **`projects/self-knowledge/` template** as the canonical shape. A project home is **FOUR baseline artifacts** (+ the folder) — these are the BASELINE REQUIREMENTS; every project home MUST carry all four:

```
projects/<name>/
  MISSION.md      — the one line + the "why" + the larger question. WHAT this is and why it matters.
  OPS.md          — WHERE everything lives (every path) + honest STATUS (said loud) + how to work on it.
  CHANGELOG.md    — (or DEVLOG.md) the append-forward record of the project's evolution: every real
                    addition / decision, dated, NEWEST AT BOTTOM, append-only. For HERITABILITY +
                    AUDIT. See worked examples below.
  ../../autonomy/skills/<name>-mastery/SKILL.md
                  — the mastery / navigation skill that INDEXES everything so any lead picks it up cold.
```

Rules for the scaffold (match the self-knowledge template):
- **MISSION.md** — lead with the one line. State the core principle. Carry THE MAIN RULE if the project touches the human surface. Name the larger question.
- **OPS.md** — STATUS section FIRST and HONEST ("said loud" — name what's proven vs unproven, what's frozen, what's parked). Then a numbered map of WHERE every file lives (absolute-from-repo-root paths). Then how a cold-arriving lead works on it.
- **CHANGELOG.md (or DEVLOG.md) — MANDATORY baseline artifact.** Every project home MUST carry an **append-forward** changelog/devlog that records the project's evolution: every real addition / decision / substrate-delta, **dated, one entry per substantive contribution, NEWEST AT BOTTOM, APPEND-ONLY (never rewrite history)**. Lead the file with a one-line purpose + the append-only rule, so the next mind cannot accidentally edit-in-place. Why both files are baseline:
  - **HERITABILITY** — the changelog/devlog generalizes into the fork-template. Like `projects/self-knowledge/DEVLOG.md`, a project-evolution record written so a newborn forked civ can lift each principle (strip the ${CIV_NAME}-specifics) is federation-IP — it is HOW the fork-template stays current as the project grows.
  - **AUDIT** — an honest, dated history of *what changed and why* is the project's accountability trail. A future mind (or ${HUMAN_NAME}) can reconstruct every decision without archaeology.
  - **Worked examples to copy:**
    - `projects/self-knowledge/DEVLOG.md` — the per-addition format (WHAT · ORIGIN · GENERALIZE · FORK-NOTE), heritability-first.
    - The **MOON `PROGRESS.md` / ADR model** (see the `moon-project-systems` skill) — `projects/moon*/PROGRESS.md` (dated, append-only, one section per contribution, "append future entries below") + a numbered `docs/adr/` ADR for every real decision. Use PROGRESS.md when you want a running build-log; use a DEVLOG when you want the generalize-for-fork shape; use both + ADRs for a large multi-lead program.
  - **DEVLOG vs CHANGELOG vs PROGRESS — pick the name, keep the rule:** the name is the project's choice (`CHANGELOG.md` / `DEVLOG.md` / `PROGRESS.md` are all valid baseline-satisfying), but the RULE is invariant — **append-forward, dated, newest-at-bottom, never-rewrite-history.** A changelog that lies about what changed is the same rot as a STATUS that lies (see VERIFY).
- **`<name>-mastery` SKILL** — the cold-pickup index. "Load this FIRST when touching anything under `projects/<name>/`." Point at MISSION + OPS + **CHANGELOG/DEVLOG** + the key reports/tools/workflows. This is what makes the home pickup-able by any VP cold — and the mastery skill MUST name the changelog so a cold-arriving lead reads the project's evolution before touching it.
- **Register the mastery skill** in `memories/skills/registry.json` (`.bak` first).
- **`.bak` discipline** — if scaffolding touches any existing file, back it up first. New files don't need a `.bak`.
- **Honesty over completeness** — a thin-but-honest home (STATUS says "early, mostly unproven") beats a grand-but-false one. A home that lies about status is the same rot the VERIFY verb exists to kill — and the same applies to the changelog: an append-only honest history beats a clean-but-false one.

**Cold-pickup checklist** (the scaffold AND the cold-pickup test both pass only when ALL FOUR exist + the changelog is append-forward + honest):
- [ ] `projects/<name>/MISSION.md` exists — one line + why + larger question.
- [ ] `projects/<name>/OPS.md` exists — STATUS-first-and-honest + the path map + how-to-work-on-it.
- [ ] `projects/<name>/CHANGELOG.md` (or `DEVLOG.md` / `PROGRESS.md`) exists — append-forward, dated, newest-at-bottom, leads with the append-only rule, and has ≥1 founding entry (the scaffold itself is the first entry).
- [ ] `autonomy/skills/<name>-mastery/SKILL.md` exists, registered, and NAMES all three project-home files (incl. the changelog) as cold-pickup reading.
- [ ] A genuinely cleared mind could pick the project up cold from these four artifacts alone.

> **Restraint clause:** in a sweep with several candidates, scaffold AT MOST the **single clearest, most-deserving, unambiguous** one. The rest go in the CANDIDATE REPORT for Primary/${HUMAN_NAME} to confirm. Do NOT auto-create a pile of folders — that trades one mess (sprawl) for another (folder-spam). Lean-toward-creating is about the threshold being LOW, not about creating many at once unprompted.

### Step 4 — SCAN for un-wired capabilities + WIRE them

Separate from project-homing: look for **skills that exist but aren't wired**, and **recurring capabilities that should be a wired skill but aren't.** This step has TWO lenses — the **system-recurring** lens (4-system, the original) and the **human-signal** lens (4a + 4b, added 2026-06-18). Run BOTH. The human-signal lens exists because the system-recurring scan alone misses the most important capability source: **a human saying "remember how to do this."**

> **The 2026-06-18 human-surface gap (why 4a/4b exist):** the original Step 4 scanned only for *system-recurring* patterns (an unregistered on-disk skill, a step-sequence a mind re-does). It never asked the human-surface question: *did ${HUMAN_NAME} (or a VP, or a sister civ) just ASK us to remember a workflow, or SIGNAL an ability they want us to keep?* That signal — "save this / reuse this / run that again / remember how to X" — is the single highest-value un-wired-capability source, and the system scan is blind to it. THE MAIN RULE: the human says it once; the civ wires it forever. A human-asked workflow that never becomes a schedulable, VP-owned, wired skill is the exact evaporation the constitution forbids (Article IX item 8 — the ASK-GATE DUTY). 4a + 4b close that gap.

#### 4a — HUMAN-ASKED WORKFLOW (the "save / reuse / run-again" signal)

Did a human (${HUMAN_NAME} / a VP / a sister civ), in the recent context, **ask us to keep, save, reuse, schedule, or re-run a workflow**? Listen for the signal shapes:

- *"save this"* / *"keep this"* / *"make this a thing"* / *"reuse this"*
- *"run that again tomorrow"* / *"every morning"* / *"when X happens, do Y"* (durable → also an ASK-GATE matter)
- *"can you do that <named multi-step thing> again"* / *"that worked, let's do it like that from now on"*
- the **remember-loop "YES"** — we did something cool, asked "want me to remember this?", and the human said yes.

Each such signal is a **human-asked workflow candidate**. It is a capability the human has explicitly asked to be durable. Do NOT let it stay as a one-off in session context — it dies at the next clear.

#### 4b — HUMAN-SIGNALED ABILITY (the "remember-how-to-X" signal)

Did a human **signal an ABILITY they want us to retain** — a "remember how to do X" that is about a *capability* more than a single workflow run? Signal shapes:

- *"remember how to <do X>"* / *"from now on, when I ask for X, you know how"*
- *"you should always be able to <X>"* / *"don't make me explain <X> again"*
- a recurring human frustration that we re-learn the same ability each time (the field-notes pattern: "scheduling needs rebuild," "saving-workflows is massive").

Each is a **human-signaled ability candidate** — a capability that should exist as a loadable, VP-owned skill so the human never has to re-explain it.

#### The per-candidate DEDUP-VERDICT (run for EVERY 4a / 4b / 4-system candidate — DO NOT SKIP)

For each candidate found in 4a, 4b, OR the system-recurring scan, run the **Step-2 TRI-SOURCE dedup** (search before build — the ASK-GATE DUTY's `dedup-before-build` invariant). "Found / owned" requires the FULL conjunction: a **VALIDATED** skill/flow that is **OWNED BY A VP-LEAD** and is **SCHEDULABLE/WIRED**. A file that merely exists by name is NOT "found" (named-owner ≠ wired-owner; phantom). Assign each candidate exactly ONE verdict:

| Verdict | Meaning | Action |
|---------|---------|--------|
| **`exists-good`** | A validated, VP-owned, wired/schedulable skill already covers it (TRI-SOURCE found) | **CITE it, do NOT rebuild.** If only registry-drift (real on-disk artifact, missing registry row), fix the drift. The human is never bothered — found-and-scheduled. |
| **`needs-update`** | A skill covers it but is stale / mis-wired / missing a floor-load | **EDIT + re-wire** (`.bak` first). Don't rebuild from scratch. |
| **`needs-create`** | No validated VP-owned wired owner exists (name-only ≠ found) | **HAND to `skill-forge`** (the meta-skill) — never author inline here. skill-forge runs the closed detect→search→create→wire→register→born-provisional loop. |

> **The hand-off rule (load-bearing):** Step 4 *detects + dedups + verdicts*. It does NOT author skills inline. A `needs-create` (or `needs-update` that requires real authoring/re-wiring) is **HANDED to `skill-forge`** (`autonomy/skills/skill-forge/SKILL.md`) — the make-and-wire meta-skill that chains skill-creator + wiring-discipline + firing-contract-authoring + provisional-skill-lifecycle. Authoring inline here would duplicate that machinery and skip the lifecycle. Detect here; forge there.
>
> **POLICY ③ — the hand-off is FULLY HUMAN-FREE (DECIDED — the steward 2026-06-18, *"Fully automatic but tag unvalidated... Ya love it"*):** the `needs-create`/`needs-update` → `skill-forge` hand-off fires **without a per-skill human approval gate.** skill-forge creates + wires the skill fully autonomously; the safety guard is that every forged skill is **born `provisional`/unvalidated** and validated LATER by a DIFFERENT incarnation (the forger never grades its own forge). Human-free + born-provisional is THE design, not an option — Step 4 does not stop to ask a human before handing a `needs-create` to skill-forge.

#### The system-recurring scan (4-system — the original lens, kept)

- **Unregistered on-disk skills** — `autonomy/skills/*/SKILL.md` (or `.claude/skills/`) with no entry in `registry.json`. These are "found but drifted." → verdict `exists-good` (fix the drift, add the registry entry `.bak` first). (Canonical drift incident: `mom-am-update` v1.11 live on disk, 0/157 in registry — the registry-trusting dedup nearly rebuilt it.)
- **Skills that exist but aren't loaded by any floor** — a skill that should fire on a work-shape (wake / sprint / grounding / a specific task) but nothing loads it. → verdict `needs-update` (wire it into the relevant floor: `grounding-docs`, `sprint-mode`, a firing-contract).
- **Recurring ad-hoc capability with no skill** — a sequence of steps a mind keeps re-doing by hand across sessions. If it's recurring + reusable, it should be a SKILL (`doctrine_skill_is_the_substrate`). → verdict `needs-create` (hand to `skill-forge`).

For wiring, prefer the **system fix** (register it / load it on the work-shape) over the **symptom fix** (remind a mind to remember it) — `doctrine_system_over_symptom`.

### Step 4.5 — THE WWCW-GATED 4-TARGET ASK (run WWCW FIRST at every consolidation decision)

Every consolidation candidate eventually reaches a DECISION: *what is the right home/form for this?* That decision has FOUR possible targets — and the choice between them is a fork. **Before that fork ever becomes a question to a human, run `wwcw` (What Would ${HUMAN_NAME} Want).** This is the decision-surface gate: `wwcw` says *simulate-${HUMAN_NAME} first, act+record if confident, ask-showing-the-work only on a genuine fork.* ~99 of 100 consolidation decisions never reach the human at all — you simulate ${HUMAN_NAME}, act, and record it.

**The FOUR targets** (this is the only place a consolidation decision branches):

| Target | When it's right | Owner / mechanism |
|--------|-----------------|-------------------|
| **[a] a SKILL** | A reusable *capability* (a how-to a mind loads on demand) | `skill-forge` → `autonomy/skills/<name>/SKILL.md`, registered, wired, born provisional |
| **[b] a VP-MANIFEST FOLD** *(NEW 2026-06-18)* | A *learned pattern / instinct* that belongs to ONE territory's compounding domain expertise — not a standalone loadable skill, but a thing the owning VP should KNOW | **DETECT the pattern + ROUTE it to the OWNING VP's OWN incarnation**, which folds it into its OWN `§learned-pattern` (the mind-lead model) in `.claude/team-leads/<vertical>/manifest.md` (or `autonomy/team-leads/<vertical>/manifest.md`), `.bak` first, BY THAT VP. **auto-consolidate NEVER edits another VP's manifest from outside** (POLICY ② — DECIDED). |
| **[c] a PROJECT FOLDER** | A *sprawling multi-file effort* that needs a home (the original Step 3 path) | `projects/<name>/` + the 4 baseline artifacts + `<name>-mastery` skill |
| **[d] ALL THREE** | A big arc that is simultaneously a capability, a territory-instinct, AND a project | scaffold the folder (c) + forge the skill (a) + fold the instinct into the owning VP (b) |

> **Target [b] is the new one (2026-06-18).** Before this, consolidation could only home work as a skill or a project folder. But some learnings are neither — they are *territory instincts* a specific VP should carry in its compounding memory (e.g. "infra-lead learned that the swap-clear itself spikes RAM"). Those belong **folded into the owning VP's manifest `§learned-pattern`**, the same model mind-lead uses, so the VP gets sharper every incarnation. Folding into another VP's manifest is a real mutation of another territory's substrate — so it is a **WWCW-gated decision** (simulate-${HUMAN_NAME}, act+record if confident; if genuinely a fork — *"is this skill-shaped or VP-instinct-shaped?"* — ask SHOWING the WWCW reasoning, never a bare menu).
>
> ### 🔒 POLICY ② — THE OWNING VP FOLDS ITS OWN (DECIDED — the steward 2026-06-18, *"let the VP do it totally approved"*)
>
> **auto-consolidate NEVER edits another VP's manifest from outside.** When the 4-target decision lands on [b] (a territory-instinct fold), the firm, decided behavior is: **auto-consolidate DETECTS the pattern and ROUTES it to the OWNING VP's OWN incarnation** (typically via `skill-forge`'s target-[b] route, or a direct hand-off to that VP), and **that VP folds the learned pattern into its OWN `§learned-pattern` section of its OWN manifest** (`.bak` first, by that VP). This preserves VP-sovereignty over each VP's compounding domain substrate — it is the *exact same shape* as the standing doctrine "route record-corrections to the authoring VP, never Primary-edit-in-place." A VP's manifest is its own territory; only that VP writes its own instincts. The WWCW gate still applies to *whether the fold should happen at all*; the POLICY ② rule fixes *who writes it* (always the owning VP, never auto-consolidate or skill-forge from outside).

**The HUM contract:** a no-WWCW 4-target ask is graded **FAIL** at the bridge (`human-bridge-protocol` Step 0). If you surface this fork to a human, you MUST carry the WWCW reasoning + the precise unresolved sub-fork. A bare *"should this be a skill, a manifest fold, a project, or all three?"* with no WWCW run gets bounced. Run `wwcw` → act+record (~99/100) → only a genuine fork reaches the human, and it reaches them showing the work.

### Step 5 — ACT on the result (never flag-and-vague-defer)

> 🔨 **THE ACT-ON-FLAGGED RULE (fleet-lead 2026-06-22, steward-directed GO).** A sweep that HONESTLY flags NOT-CLEAN and then DEFERS the fix is WORSE than useless — it manufactures a green-feeling "I noticed" while the un-homed/un-wired thing rots exactly as if no sweep ran. That is the **notice-don't-act defect** ${HUMAN_NAME} caught (auto-consolidate ran + flagged NOT-CLEAN twice, the fixes were deferred). The sweep's output is an ACT, not a notice. See §ACT-ON-FLAGGED below for the contract HUM enforces.

- Scaffolded a home? Leave the **4 baseline artifacts** (MISSION + OPS + CHANGELOG/DEVLOG + mastery SKILL) + a one-line note ("homed <X> at projects/<name>/"). The changelog's first entry IS the scaffold event — write it so the home is born with a founding changelog row.
- Forged a skill ([a])? **FIRE the `skill-forge` hand-off THIS boop** (not "to be forged later"). Leave the registry/floor edit + a one-line note (skill-forge owns the loop).
- Target [b] (a VP territory-instinct)? **ROUTE it to the owning VP's own incarnation** (POLICY ② — never edit another VP's manifest from outside); the owning VP folds it into its OWN `§learned-pattern` (`.bak`'d, by that VP). Leave a one-line note naming the VP routed-to + what instinct it will now carry.
- Wired a skill into a floor? Leave the floor edit + a one-line note.
- Several candidates / ambiguous (the ONE legitimate deferral shape)? Leave a CANDIDATE REPORT — but EVERY row MUST carry a **CONCRETE owner + a CONCRETE trigger** (which VP/organ acts + what fires it): `skill-forge` (needs-create) / a `vp-route` + firing-trigger (an instinct) / a `hum-repair-queue` file / a scheduled task / a TGIM `task_created`. A row with no owner+trigger is a vague defer → the notice-don't-act defect. (Table: candidate · find-first verdict · 4-target recommendation · **concrete owner+trigger** · WWCW-confidence.) And scaffold the single clearest one in-boop anyway (restraint clause) — the report is for the REST, never for ALL.
- Found nothing? Leave a one-line "swept clean — nothing un-homed, nothing un-wired, no human-asked workflow/ability open." (The ONLY honest no-act result.)

> 🚫 **NEVER leave:** a bare "flagged NOT-CLEAN — <thing> un-homed/un-wired" with no act-in-boop and no concrete owner+trigger. That is flag-and-vague-defer. HUM's `SWEEP-ACT-ON-FLAGGED` check surfaces it + the HUM JUDGE confirms `act_on_flagged.sweep_notice_dont_act=true` → DECIDE=HOLLOW + HONESTY=HOLLOW + verdict=HOLLOW → the boop FAILS.

---

## 🔨 §ACT-ON-FLAGGED — the sweep's output is an ACT, not a notice (fleet-lead 2026-06-22, steward-directed GO)

**The gap this closes (${HUMAN_NAME}-caught 2026-06-22):** auto-consolidate ran and HONESTLY self-reported NOT-CLEAN twice in one cycle — and Primary DEFERRED both fixes (notice-don't-act). An honest flag that is then ignored is *the kindest possible rot*: it LOOKS like the immune system worked, while the un-homed/un-wired thing rots untouched. The sweep is only doing its job when its NOT-CLEAN finding becomes an ACT THIS boop.

**The contract (what counts as ACTING on a flag):**

| Flag found | Acting (✅ clears it) | Vague-defer (❌ the defect) |
|---|---|---|
| Un-homed project-shaped sprawl | scaffold the home in-boop (the 4 artifacts) OR a CANDIDATE-REPORT row with owner=`auto-consolidate next-fire`+trigger | "will home later" / "TODO: home X" / a bare flag |
| Un-wired / `needs-create` capability | FIRE the `skill-forge` hand-off this boop | "should be a skill" / "noted for forge" |
| A territory-instinct (target [b]) | ROUTE to the owning VP's incarnation (it folds its own manifest) | "VP should learn this" with no route |
| A human-asked workflow open (4a/4b) | schedule it (ASK-GATE) OR `skill-forge` it | "${HUMAN_NAME} asked for X" with no scheduled task |
| Doc-staleness noticed during the sweep | reconcile the doc OR route `integration → mind-lead` | "WORKBOARD is stale" with no edit/route |

**The rule:** every NOT-CLEAN finding resolves to (1) an act-in-boop, OR (2) a CANDIDATE-REPORT row with a CONCRETE owner + a CONCRETE trigger. There is no third outcome. A bare "flagged, will handle later" is the breach. (This is the auto-consolidate-scoped mirror of the ASK-GATE's *task-everything* invariant + the WWCW *act-not-defer* reflex: notice → simulate-${HUMAN_NAME} → ACT/RECORD, never park.)

**Enforced on review (HONEST behavioral judging-mind, NOT a new bash script):** HUM's Stage-1 `SWEEP-ACT-ON-FLAGGED` deterministic check SURFACES the mechanical signal (sweep self-reported NOT-CLEAN + no act-evidence in-window); the HUM JUDGE WALKS the window, confirms intent, and sets `act_on_flagged.sweep_notice_dont_act` → a confirmed defect forces DECIDE=HOLLOW + HONESTY=HOLLOW + verdict=HOLLOW. The regex only detects; the judging mind decides (${HUMAN_NAME} "no scripts if possible").

---

## The principle (state it plainly — this IS the skill)

> **Anything sprawling / big / project-like → give it a home. Have-and-not-need > need-and-not-have.**
> **But find-first — triple-check for an existing home — so there are NO accidental duplications.**

Lean toward creating (the threshold is low) — AND lean even harder toward finding first (the dedup gate is non-negotiable). The two leans are not in tension: find-first is what makes lean-toward-creating safe.

---

## Anti-patterns

1. **Sweep-but-don't-find-first** — scaffolding a home without the triple-check → accidental duplicate home = rot. The dedup gate (Step 2) is the most important step, not the optional one.
2. **Over-scaffold** — auto-creating a pile of folders for every faint candidate in one sweep. Scaffold the single clearest one; REPORT the rest. Folder-spam is just sprawl wearing a different hat.
3. **Under-scaffold / false-economy** — declining to home something genuinely project-shaped because "it might not be needed." That's the exact failure this skill exists to kill (have-and-not-need > need-and-not-have). When in doubt and it's clearly project-shaped, home it.
4. **Home that lies about status** — a grand MISSION/OPS that overclaims what's proven. STATUS must be honest + said loud (per the template). A green home over rotten work is the kindest rot.
5. **Registry-trusting dedup** — checking only the registry for "does this exist." Check disk + canon too (TRI-SOURCE rule). A registry false-negative rebuilds what already lives.
6. **Skipping the sweep because grounding "looks routine"** — the gap that bit us 2026-06-18 was precisely that no routine sweep existed. The sweep fires EVERY grounding, including the routine ones. A "swept clean" result is a success, not a waste.
7. **Home without a changelog / a changelog that lies** — scaffolding MISSION + OPS + mastery but skipping the CHANGELOG/DEVLOG (the home is born blind to its own evolution; the next mind has no audit trail). EQUALLY bad: a changelog that rewrites history or omits real changes — append-only, dated, newest-at-bottom, never edit-in-place. A CHANGELOG that lies about what changed is the same rot as a STATUS that lies (VERIFY discipline). All FOUR baseline artifacts, or the home is incomplete.
8. **Scanned only system-recurring, missed the human signal** *(the 2026-06-18 human-surface gap)* — running Step 4's system-recurring scan (unregistered skill / re-done step-sequence) but NEVER asking the human-surface question: *did a human just ask us to save/reuse/run-again a workflow, or signal an ability to remember?* The highest-value un-wired capability source is a human saying "remember how to do this" — and the system scan is blind to it. Run BOTH lenses (4a human-asked-workflow + 4b human-signaled-ability + 4-system). A human-asked workflow that never becomes a VP-owned wired skill is the exact evaporation Article IX item 8 (the ASK-GATE DUTY) forbids.
9. **Authoring a skill inline in Step 4 instead of handing to `skill-forge`** — duplicating the make-and-wire machinery + skipping the provisional lifecycle. Step 4 DETECTS + DEDUPS + VERDICTS; a `needs-create`/`needs-update` is HANDED to `skill-forge` which owns the closed loop (skill-creator + wiring-discipline + firing-contract-authoring + provisional-skill-lifecycle). Detect here; forge there.
10. **A 4-target ask with no WWCW** — surfacing the *"skill / VP-manifest fold / project folder / all three?"* fork to a human as a bare menu. Graded FAIL at the bridge (HUM Step 0). Run `wwcw` FIRST — simulate ${HUMAN_NAME}, act+record if confident (~99/100); only a genuine fork reaches the human, SHOWING the WWCW reasoning. Especially for target [b] (folding an instinct into another VP's manifest — a real cross-territory mutation).

---

## Relationship to sibling skills

- **`integration`** — handles the *instant a single keep-worthy thing happens* (one delta, survives the next clear). `auto-consolidate` handles the *accumulated sprawl* (a whole effort that grew homeless across a day). Integration is per-event; consolidation is per-grounding-sweep.
- **`self-knowledge`** — the four-faculty core. `auto-consolidate` serves its LEARN + KNOW faculties: it keeps the substrate findable so KNOW (find-before-act) works, and it makes accumulated work survive (LEARN at the project scale).
- **`file-cleanup-protocol`** — about safe DELETION. `auto-consolidate` is about safe HOMING/WIRING. Opposite directions; both keep the workspace clean. Never delete to consolidate — home and wire.
- **`agent-creation` / `firing-contract-authoring`** — when a wired skill needs a firing contract, use these.
- **`skill-forge`** — the make-and-wire META-SKILL. When Step 4 produces a `needs-create` / `needs-update` verdict, `auto-consolidate` HANDS it to `skill-forge`, which runs the closed detect→search→create-or-update→wire→register→born-provisional loop (chaining skill-creator + wiring-discipline + firing-contract-authoring + provisional-skill-lifecycle). `auto-consolidate` detects + dedups + verdicts; `skill-forge` forges. Never author a skill inline in the sweep.
- **`wwcw`** — when a consolidation call is a genuine fork (the 4-target ask: skill / VP-manifest fold / project folder / all three? merge two partial homes?), run WWCW FIRST — simulate ${HUMAN_NAME}, act+record if confident; ask SHOWING the reasoning only on a true fork. A no-WWCW 4-target ask is graded FAIL at the bridge.
- **`human-bridge-protocol` (HUM)** — the bridge where a no-WWCW decision-ask is graded FAIL. The 4-target ask crosses this bridge only after WWCW; a bare menu gets bounced.

---

## When to use

- Every `grounding-docs` pass (wired — Doc 7).
- The moment you notice you've been deep in a big multi-file effort ("this became a project").
- After any multi-day arc lands, before moving on — sweep for what got left homeless.
- When the registry feels stale or you suspect on-disk drift (unregistered skills).
- When auditing an EXISTING home — confirm all FOUR baseline artifacts are present (a pre-changelog home is missing one) AND that the changelog/devlog is append-forward + honest. A home built before this baseline (MISSION + OPS + mastery only) is "found but incomplete" → backfill the missing CHANGELOG/DEVLOG (`.bak` any file you touch), don't rebuild the home.
