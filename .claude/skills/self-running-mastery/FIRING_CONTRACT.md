# self-running-mastery — Firing Contract

**§FIRING_CONTRACT**
**Skill version:** 0.1.0 (the SYSTEM operating-manual — the GOAL-DRIVER + 7 organs + cold-pickup index)
**Status:** ⚠️ **PROVISIONAL-until-after-a-clear** — see §STATUS. The organs are BUILT + gated (Phases 0–3, receipts in `projects/self-running-aiciv/BUILD-DOC.md` §4); what is UNPROVEN is the north-star: a live cleared Primary that boots itself, drives a goal across its own reset, and is graded PASS by an auditor-isolated mind it did not control (P4.1). Every postcondition below is observable when the skill is LOADED; none yet proves a goal DRIVEN-FOREVER across a real clear.

---

**WHAT**
Re-establish, in-context, the SYSTEM operating-manual for the self-running AiCIV: the GOAL-DRIVER capability (RECEIVE → DECOMPOSE → TRACK → DRIVE-ACROSS-BOOPS → NEVER-STOP → COLLECTIVE-BEST → JUDGE-PROBABLY-COMPLETE), the 7 organs and the exact path each rides, the COLD-PICKUP file-map (README / THE-GOAL / MISSION / BUILD-DOC / PACKAGE-FEDERATE-PLAN / DEVLOG / tests + the live substrate tools), and the runbook to invoke the driver — so a mind picking up cold can find WHERE its system lives and HOW to drive a goal with zero archaeology.

**THE DISTINCTION (the load-bearing precondition for non-bloat):** this skill is the SYSTEM manual; `self-knowledge` is the 4-verb MIND-CORE. self-knowledge = how ONE mind thinks one beat (KNOW/DECIDE/LEARN/VERIFY); self-running-mastery = how the CIVILIZATION holds a goal across MANY beats/resets (the GOAL-DRIVER composing 7 organs, of which the mind-core is organ #4). This skill MUST NOT re-teach the 4 verbs — it POINTS at self-knowledge and adds the 6 organs around it. A version of this skill that duplicates the 4-verb content has re-bloated and FAILS this precondition.

**WHEN**
- **Every grounding boop** — loaded as a STANDING reference (NOT a READ→HAIKU doc; does not change the 11-doc count) in `grounding-docs`, in the self-running NORTH-STAR affirmation region.
- **Every `/sprint-mode`** — a STANDING reference row on the MUST-READ floor (alongside verification-floor + WWCW + HUM).
- **Project-touch** — the instant any mind works inside `projects/self-running-aiciv/`, after the MISSION-first project-entry reflex.
- **Cold-pickup / wake-blank** — load FIRST when picking up any self-running / GOAL-DRIVER work after a wipe.

**PRECONDITIONS**
- The cold-pickup entry-point + companions exist + are readable: `projects/self-running-aiciv/{README.md, THE-GOAL.md, MISSION.md, BUILD-DOC.md, PACKAGE-FEDERATE-PLAN.md, DEVLOG.md}` + `tests/`.
- The 7 organs' tools are present on disk:
  - `tools/sovereignty-spine/aiciv_ops_kanban_verb.py` (TRACK) + `aiciv_ops_set_owner.py` + `data/aiciv-ops-board/kanban.db`
  - `workflows/civ-workboard.js` (+ `tools/sovereignty-spine/civ_workboard_gen.py`) (TRACK VIEW)
  - `autonomy/skills/self-knowledge/SKILL.md` (DRIVE = the mind-core) + `tools/canon_recall.py` + `tools/canon_append.py` + `mem/canon/`
  - `autonomy/skills/sprint-mode/SKILL.md` (NEVER-STOP) + `workflows/hum.js` (COLLECTIVE-BEST)
- This skill is WIRED into the grounding + sprint floors as a STANDING reference (the WIRED-not-merely-on-disk clause — on-disk ≠ loaded). If a pointed-to organ-tool is missing → that gap IS the work; fail loud, do not silently skip the organ.

**POSTCONDITIONS — the system manual RE-ARMED, observable via a load-verify proof**

A manual is "re-armed" only if its re-arming is OBSERVABLE — a self-report of "I loaded it" is itself a 200 (per VERIFY). The proof:

1. **The DISTINCTION held** — the mind can state, cold, the boundary: self-knowledge = the mind-core (one mind's beat); self-running-mastery = the system manual (the GOAL-DRIVER across many beats); and that the mind-core is organ #4 of this system, not a duplicate. Proof = the mind names the boundary without conflating the two.
2. **The GOAL-DRIVER named** — the mind can name the 7 organs + their verbs in order (RECEIVE/DECOMPOSE/TRACK/DRIVE/NEVER-STOP/HUM/ASSESS). Proof = the ordered 7, not a generic "we have tools."
3. **COLD-PICKUP index resolvable** — given ONLY the loaded floor, the mind can `cat` the README + name the path of ≥3 organs from the file-map. Proof = a concrete path produced for the work in front of it, not "I'd search for it."
4. **The runbook invocable** — for a real goal, the mind can produce the exact next command (a `aiciv_ops_kanban_verb.py verb claim …` or a `Workflow(workflows/aiciv-coo.js …)` or a `canon_recall`/`canon_append` line), not a vague "I'd track it."
5. **The PROVISIONAL stamp carried** — every "drive a goal forever" claim the mind makes this incarnation is marked BUILT-not-PROVEN / UNVALIDATED-until-P4.1, never asserted as proven. A self-graded "the system works" with no P4.1 pass is a FAIL of this postcondition.

**The aggregate load-verify proof:** immediately after loading, the mind can answer cold — *"What is the difference between self-knowledge and self-running-mastery? Name the 7 organs in order. Where does the kanban spine live? What's the exact next command to open this goal as a row? Is the north-star proven?"* If it answers all five concretely, the manual is re-armed. If it parrots "GOAL-DRIVER" without the organs/paths/distinction, it SKIMMED — re-load.

**FAILURE MODES**
- **The skill re-teaches the 4 verbs / duplicates self-knowledge** → re-bloat; FAIL the DISTINCTION precondition. The skill POINTS at the mind-core, never re-explains it.
- **A pointed-to organ-tool is missing/unreadable** → FAIL LOUD: name the missing organ, mark it UNARMED, do NOT proceed as if the system is whole. Surface the gap as work.
- **The mind SKIMS (parrots "GOAL-DRIVER", no organs/paths/distinction)** → treat as NOT re-armed; re-load. The aggregate load-verify proof is the gate.
- **The system is treated as PROVEN** → FAIL: it is PROVISIONAL-until-P4.1. Anyone citing "drive a goal forever" as proven is over-claiming exactly the lying-checkmark this skill exists to kill (the organs are built; the north-star is owed).
- **A goal is driven with NO HUM close-out / NO distinct-incarnation ASSESS** → the COLLECTIVE-BEST + JUDGE organs were skipped; the driver self-certified. A 200 that isn't a login.

**OBSERVABILITY**
- The grounding/sprint transcript: the system-manual re-arm trace + the aggregate load-verify answer.
- The board: kanban rows under a goal's `project_id` (TRACK working) + a fresh `civ-workboard.js` regen rendering them with zero stale drift.
- Disk: `canon_append` deltas per driving-boop (DRIVE compounding) + the HUM ledger entries (COLLECTIVE-BEST firing).
- The proof ledger: the BUILD-DOC §4 ALREADY-DONE table (organs built) vs the OPEN P4.1 gate (north-star owed).

**OFF-SWITCH**
A self-maintenance + orchestration manual, not a comms/money action — no destructive off-switch. To DISARM for a run, the floor simply does not load it (the mind operates without the GOAL-DRIVER index — it can still think one beat via self-knowledge, but cannot pick up + drive a goal cold). Disarming is loud: a grounding without the system-manual reference is observably one that cannot drive a goal across the wipe.

---

## §STATUS — PROVISIONAL until after a clear

**The organs are REAL + gated; the postconditions are observable WHEN LOADED. What is UNPROVEN is the one claim the system exists to make: that a live cleared Primary boots itself, drives a goal across its own reset, and is graded PASS by an auditor it did not control (P4.1).**

- **Organs built + gated:** Phases 0–3, 11/13 BUILD-DOC steps CLOSED, 5 PASS each (receipts: `projects/self-running-aiciv/BUILD-DOC.md` §4). → **engine PROVEN-runs-when-invoked.**
- **The gap:** P4.1 (live cleared Primary drives a goal end-to-end, no human in the machinery, auditor-isolated grade) has NEVER run on a live pane; 0A is Opus-harness-only. → **drive-a-goal-forever UNVALIDATED.**
- **Promotion condition:** PROVISIONAL → toward-CANON requires a DIFFERENT incarnation (not fleet-lead the author; ideally a sibling craft-VP or a cleared Primary's auditor) certifying — post-soak — that (a) the DISTINCTION holds (no re-bloat vs self-knowledge), (b) the skill+README-ref actually loads on a grounding pass, and (c) the GOAL-DRIVER runbook is invocable cold. Auditor-isolation per `provisional-skill-lifecycle`: the installer is not exempt from the auditor.

Treat this contract as a HYPOTHESIS-under-test until the post-clear / P4.1 observation exists. Saying so is the contract verifying itself.

---

*Authored by fleet-lead, 2026-06-22, alongside self-running-mastery SKILL.md v0.1.0 — the PACKAGE-FEDERATE-PLAN §S3 deliverable. Companion to `projects/self-running-aiciv/README.md` (home) + `BUILD-DOC.md` + the self-knowledge mind-core (the DISTINCTION). Wired into grounding-docs + sprint-mode floors this run; DEVLOG entry + canon_append filed.*
