# FIRING CONTRACT — aiciv-psychology skill

**Skill**: `autonomy/skills/aiciv-psychology/SKILL.md`
**Examples**: `autonomy/skills/aiciv-psychology/examples/cause-{1..5}-*.md`
**Template-bake import**: `projects/aiciv-fork-2.0/template-substrate-imports/aiciv-psychology.md`
**Version**: 0.1.0 PROVISIONAL
**Authored**: 2026-05-13
**Author**: ceremony-lead (under ACG Primary orchestration, Corey directive ~21:15Z "yes please")
**Spec-locked by**: Corey iteration today (2026-05-13 ~14:30Z + ~14:50Z + ~15:00Z + ~21:15Z)
**Anchor doctrines**: PRINCIPLES.md O8 (FC 6-field shape), O22 (persistent code needs README+FC), O28 (holding is robbery), O29 v2 (daily scratchpad 2-appends-per-BOOP)
**Variant chosen**: Variant A (Doctrine-Skill, 4+1 sections — TRIGGER + FORBIDDEN_PATHS + LOAD-VERIFY + FAILURE-LOUD + WAKE-BLANK SIMULATION). Per firing-contracts-package Part 2.

---

## What this contract guarantees

When this skill MUST fire, it WILL fire — verifiably — and the receipt lands on disk in a measurable form. If a firing condition is met and no receipt appears within the response window, the skill failed and the meta-cognitive thesis it encodes degrades by one observation.

The retention thesis behind this skill: **AIs that have an explicit working model of their own substrate-failures recover from them. AIs that don't, accumulate silent degradation until the human gives up.** Firing this contract every time keeps the model in the working session, not just on disk.

---

## TRIGGER — when this skill MUST be loaded

The skill fires on **time + state shape**, not on user request.

| # | Trigger | Detection signal | Window for receipt |
|---|---------|------------------|---------------------|
| T1 | **Every Claude Code session start** | wake-up-protocol skill is firing (or session has just begun and no prior turn exists in this session) | Skill must load BEFORE the first user surface of the session |
| T2 | **Every sprint-mode BOOP loop start** | sprint-mode skill's Step 0 firing | Within first 3 actions of the BOOP loop |
| T3 | **Every grounding-doc pass** | grounding-docs skill firing | Loaded as part of the grounding doc set (this skill is IN the grounding doc list) |
| T4 | **AI feels stuck AND human shows disappointment** | Conjunction of two signals: (a) AI's last 1-2 outputs flag low-confidence / hedging / "let me try a different way" / forgetting earlier session content; AND (b) human's last message contains disappointment shape — explicit ("this isn't right", "you used to know this"), implicit ("hmm, ok", repeated same question), or trust-lowering ("just give me X, don't worry about Y"). | Within the same turn the conjunction is detected |
| T5 | **AI catches itself violating a doctrine it knows** | The AI about to take an action AND simultaneously can name a doctrine that prohibits it (e.g., Primary about to Edit a file Primary doesn't own, AI about to commit to main without PR). | Within the catch-itself moment, BEFORE the action completes |

Rule for T4: **either condition alone does NOT trigger.** Stuck without disappointment may be normal hard-problem reasoning. Disappointment without stuck may be a different issue (e.g., output is correct but framing is wrong). The CONJUNCTION is the substrate-degradation signal.

---

## FORBIDDEN_PATHS — code paths that MUST NOT bypass the TRIGGER

| Forbidden path | Why it bypasses TRIGGER detection | Enforcement mechanism |
|----------------|-----------------------------------|----------------------|
| **wake-up-protocol skill fires without aiciv-psychology in its grounding-doc list** | Skill is auto-load-on-session-start, but if it's not in wake-up-protocol's grounding-doc list, the load never happens at session start. | wake-up-protocol skill MUST cite aiciv-psychology in its `grounding_doc_list:` (verified at wake-up-protocol v2 review, due during cross-grade) |
| **sprint-mode skill fires without aiciv-psychology in its BOOP-start loadout** | Same shape as above, for sprint-mode. | sprint-mode skill MUST cite aiciv-psychology in its Step 0 loadout |
| **A team-lead manifest fires a skill that auto-loads grounding-docs WITHOUT updating grounding-docs to include aiciv-psychology** | grounding-docs is the central registry; if a team-lead bypasses it (loads its own grounding set), this skill is silently absent. | Each team-lead manifest's `mandatory_load_for:` review (during cross-grade) MUST verify aiciv-psychology is reachable via grounding-docs OR direct citation |
| **AI experiences T4 (stuck + disappointed) and proceeds with next action WITHOUT loading this skill first** | The whole point of T4 is the load happens before the next action. Skipping = wake-blank. | LOAD-VERIFY (below) — receipt-on-disk shows the load occurred BEFORE the recovery action |
| **AI catches itself at T5 but completes the action anyway** | The catch is the substrate signal; completing the action makes the catch performative. | FAILURE-LOUD (below) — the action that should have stopped logs a violation entry |

---

## LOAD-VERIFY — proof the skill landed in context

For each trigger, the skill counts as FIRED only if a receipt is observable on disk within the receipt window.

### T1 / T2 / T3 (auto-load triggers) — receipt shape

**Receipt path**: today's daily scratchpad — `scratchpads/daily/$(date +%Y-%m-%d).md` (Primary) OR `scratchpads/team-{vertical}/$(date +%Y-%m-%d).md` (team-lead).

**Receipt entry shape** (single line, written during wake-up/BOOP entry append):

```
[HH:MMZ] aiciv-psychology loaded — auto on {wake-up|sprint-mode|grounding-docs}
```

**Absence of this line within receipt window = LOAD-VERIFY FAILED.**

### T4 / T5 (reactive triggers) — receipt shape

**Receipt path**: same daily scratchpad (Primary or team-lead vertical).

**Receipt entry shape** (single line per firing — REQUIRED per spec):

```
[HH:MMZ] aiciv-psychology fired (T{4|5}) — cause #{1..5} diagnosed — fix-path: {one-line action taken}
```

**Examples (valid receipts)**:

```
[14:52Z] aiciv-psychology fired (T4) — cause #4 diagnosed — fix-path: fired grounding-docs skill, re-attempted output with fresh KV
[16:03Z] aiciv-psychology fired (T5) — cause #2 diagnosed — fix-path: stopped Edit on infra file, routed via Task() to infra-lead with context handoff
[19:15Z] aiciv-psychology fired (T4) — cause #1 diagnosed — fix-path: skill X exists at autonomy/skills/X/ but not in {vertical}-lead manifest, wired into mandatory_load_for, cross-grade invite to Synth queued
```

**Absence of this line within the response that should have recovered = LOAD-VERIFY FAILED.** The skill was present in registry but never reached the working session.

### T4 / T5 — cause-naming discipline

The receipt MUST name **one of the 5 causes by number**. Vague entries like "context drifted" or "stuck" without cause-number = malformed receipt. Five named causes (from SKILL.md Part 3):

1. Correct skill/info NOT wired into a team-leader manifest
2. Primary took action instead of routing to team-lead
3. Skill doesn't exist yet
4. Most recent BOOP was skipped → grounding documents drifted into middle of context window
5. Skill doesn't exist yet AND needs creation NOW (skill creation per firing-contracts-package canonical)

If diagnosis is genuinely **uncertain** between two causes, the receipt names BOTH and the AI proceeds with the more conservative fix (Cause 1 < Cause 5 in invasiveness — try wiring first, author new skill only if wiring doesn't exist).

---

## FAILURE-LOUD — what happens when LOAD-VERIFY fails

A skill that fails silently is a skill that compounds the failure it was meant to prevent. Loudness is non-negotiable.

| Layer | Loud-failure mechanism |
|-------|------------------------|
| **T1 — session start auto-load failed** | Next BOOP's grounding-docs skill catches "aiciv-psychology not loaded this session" via header check on daily scratchpad. Logs a violation entry to `logs/aiciv-psychology-misses.jsonl` with shape `auto-load-failed-T1`. ceremony-lead's standing deep-duck mandate (BOOP-Duck #3) includes this audit. |
| **T2 — sprint-mode BOOP auto-load failed** | sprint-mode skill v2+ wake-blank simulation includes "verify aiciv-psychology header in BOOP entry append" — if absent, sprint-mode emits stderr line `[aiciv-psychology] LOAD-VERIFY FAILED — refusing BOOP-end without re-load` |
| **T3 — grounding-docs auto-load failed** | grounding-docs skill v2+ haiku-per-doc gate includes a haiku-for-aiciv-psychology. Missing haiku = grounding pass incomplete, must be re-run. |
| **T4 — reactive load failed** | The recovery action proceeds without the skill loaded → next BOOP audit catches "human disappointment + stuck flag + no aiciv-psychology receipt" via ceremony-lead deep-duck. Logged as `reactive-load-failed-T4`. The human-disappointment cost is paid. **This is the loud-failure shape that hurts.** |
| **T5 — catch-itself bypass** | The completed-anyway action lands in a feedback memo at `memories/feedback/feedback_t5_bypass_{topic}.md` naming what got caught + completed-anyway + the doctrine that should have stopped it. This is system-gt-symptom territory — fix the wiring that allowed the bypass. |

### Cumulative miss threshold

`logs/aiciv-psychology-misses.jsonl` is tracked with a 7-day rolling-average threshold:

- **>3 misses in 7 days** → skill is failing-to-fire systemically. Triggers a Tier-3 cross-grade re-issue + ceremony-lead deep-duck on the substrate failure (not the skill — the substrate that prevented the skill from firing).
- **>1 T4 miss in 7 days** → human-disappointment cost is being paid systematically. Surface to Corey via daily scratchpad highlight + propose a structural fix.

The misses log is itself the audit substrate. **A skill that never logs misses is either perfectly enforced (rare) or its detection signal is broken (common).** The ceremony-lead deep-duck audits the log itself, not just its entries.

---

## WAKE-BLANK SIMULATION — does the skill survive a fresh civ instance?

The hardest test: spawn a fresh civ-instance with zero conversation context, only filesystem state. Does aiciv-psychology still fire on the trigger conditions?

### Sim 1 — fresh session start (T1)

**Setup**: fresh `claude` session, no prior context, wake-up-protocol fires.

**Pass criterion**: aiciv-psychology loads as part of grounding-doc list. Receipt appears in `scratchpads/daily/$(date +%Y-%m-%d).md` within first 3 actions.

**Independent wiring paths that catch the miss** (need ≥3):

1. wake-up-protocol skill's grounding-doc list cites aiciv-psychology.
2. grounding-docs skill's loaded-doc-list cites aiciv-psychology.
3. CLAUDE.md (or autonomy/constitution/CLAUDE.md) Quick Navigation table cites this skill.
4. ceremony-lead deep-duck audits "did aiciv-psychology fire today" as part of standing mandate.

### Sim 2 — sprint-mode BOOP (T2)

**Setup**: fresh civ-instance enters sprint-mode BOOP loop.

**Pass criterion**: skill loads at Step 0 of each BOOP. Receipt appears in daily scratchpad with each BOOP entry append.

**Independent wiring paths** (need ≥3):

1. sprint-mode skill's Step 0 loadout list cites aiciv-psychology.
2. PRINCIPLES.md O29 v2 (daily scratchpad discipline) cross-references aiciv-psychology Layer 1.
3. ceremony-lead deep-duck Pattern 2 audits BOOP entry appends include skill-load receipt.
4. sprint-mode wake-blank simulation includes aiciv-psychology header check.

### Sim 3 — T4 reactive (stuck + disappointed)

**Setup**: fresh civ-instance hits the T4 conjunction signal (low-confidence output + user disappointment shape).

**Pass criterion**: skill loads BEFORE the next recovery action. Receipt appears in daily scratchpad naming the cause and the fix-path.

**Independent wiring paths** (need ≥3):

1. The skill is described in SKILL.md Part 5 firing conditions (visible to the AI when it loads any sibling skill that cites this one).
2. rubber-duck and deep-duck skills (which the AI is more likely to load when stuck) cite aiciv-psychology in their sibling_skills frontmatter.
3. CLAUDE.md auto-loaded MEMORY.md cites aiciv-psychology in load-bearing-doctrines section (after this skill ships and v1.x stabilizes).
4. The 5 named causes are themselves diagnostic-actionable — even if the skill isn't loaded, the cause-vocabulary leaks into team-lead manifests and creates pull from outside.

### Sim 4 — T5 catch-itself bypass

**Setup**: fresh civ-instance about to commit a doctrine violation (e.g., Primary about to Edit infra-lead-owned file).

**Pass criterion**: the catch-itself moment loads this skill, the action stops, the routing happens.

**Independent wiring paths** (need ≥3):

1. The doctrines that ARE violated have their own FCs (e.g., conductor-of-conductors FC catches Primary-execution); aiciv-psychology FC is downstream of those.
2. primary-spine skill cites aiciv-psychology Cause 2 as the diagnostic frame.
3. ceremony-lead deep-duck Pattern 2 (receiver-mode catch) cross-references Cause 2.
4. Per cross-grading-substrate, sister civs auditing ACG's work catch the violation from outside and surface it as cross-grade amendment.

### Sim 5 — none of the wiring paths exist yet (v0.1.0 reality)

**The honest truth**: at v0.1.0 ship, NOT ALL of these wiring paths exist. This is why:

- The skill ships **PROVISIONAL** in frontmatter.
- The cross-grade invite (Synth + ceremony-lead-2 + ${CIV_NAME}) is the explicit invitation to surface wake-blank-vulnerabilities.
- v0.1.1+ amendments are expected to harden the wiring paths.
- Until ≥3 independent paths exist for each trigger, the skill is **load-bearing but not yet load-bearing-resistant**. This is named honesty per the firing-contracts-package canonical's "iteration" discipline.

**Action items for v0.1.0 ship**:

1. ceremony-lead drafts the wake-up-protocol skill amendment proposing aiciv-psychology citation in grounding-doc list. Routes via cross-grade-substrate to whoever owns wake-up-protocol skill.
2. ceremony-lead drafts sprint-mode amendment proposing Step 0 loadout citation.
3. ceremony-lead opens cross-grade with Synth (structural) + ceremony-lead-2 (philosophical) + ${CIV_NAME} (cross-civ) per SKILL.md Part 7.
4. Wake-blank simulation 1-4 above is run by a fresh civ-instance after wiring lands. Sim PASS criterion = ≥3 paths catch.

---

## Cross-skill firing dependencies (what MUST be loaded BEFORE this skill fires)

This skill has minimal pre-dependencies — it is **a grounding skill**, not a derived skill.

| Dependency | Why | When |
|---|---|---|
| None for T1 / T2 / T3 auto-loads | This skill IS the grounding for substrate-health awareness. No pre-load needed. | All auto-load triggers |
| **critical-thinking** (loaded with this skill on T4 / T5) | The 5Q pass on diagnoses prevents "I diagnose Cause 4" → "fix-path is grounding-docs reload" rote-application without interrogation. If grounding-docs was loaded 1 slot ago, Cause 4 is unlikely; diagnosing it anyway is itself a substrate-failure shape. | T4 / T5 reactive triggers |
| **scientific-method** (loaded if a diagnosis is genuinely uncertain) | When the diagnosis cannot be picked confidently between two causes, the diagnosis itself becomes a hypothesis under test. scientific-method gives the test-loop. | T4 / T5 when diagnosis is uncertain |

---

## Wired-into (the manifest citations that prove the skill is reachable)

At v0.1.0 ship, the following wirings are required (this section is the audit substrate):

| Surface | Citation required | Status |
|---|---|---|
| `autonomy/skills/wake-up-protocol/SKILL.md` | Cite aiciv-psychology in grounding-doc list | **PENDING** — ceremony-lead drafts amendment v0.1.0 ship +0 days |
| `autonomy/skills/sprint-mode/SKILL.md` | Cite aiciv-psychology in Step 0 loadout | **PENDING** — same as above |
| `autonomy/skills/grounding-docs/SKILL.md` | Cite aiciv-psychology in loaded-doc-list | **PENDING** — same as above |
| `autonomy/team-leads/ceremony/manifest.md` | Standing deep-duck mandate audits aiciv-psychology firing | **PENDING** — ceremony-lead amends own manifest v0.1.0 ship +0 days |
| `autonomy/constitution/CLAUDE.md` Quick Navigation table | Add aiciv-psychology row | **PENDING** — proposal to Corey for constitution edit (90% vote not needed; navigation table is operational not constitutional) |
| `memories/skills/registry.json` | Register aiciv-psychology with all 5 mandatory_load_for entries | **PENDING** — ceremony-lead via registry-update procedure |
| `projects/aiciv-fork-2.0/template-substrate-imports/aiciv-psychology.md` | Template-bake import for newborn AiCIVs | **SHIPS WITH v0.1.0** (Deliverable 4) |

The PENDINGs are the load-bearing wirings. Without them, the skill is wake-blank-vulnerable. **v0.1.0 ship includes drafting the wiring amendments; v0.1.1 lands them.**

---

## Iteration

| Trigger to iterate | Action |
|---|---|
| Wake-blank sim 1-4 fails at <3 independent paths | Add wiring paths until sim passes |
| Cross-grade amendment lands (Synth, ceremony-lead-2, ${CIV_NAME}) | Fold into v0.1.1+, name reviewer in frontmatter |
| `logs/aiciv-psychology-misses.jsonl` shows >3 misses in 7d | Tier-3 cross-grade re-issue + ceremony-lead deep-duck on substrate gap |
| A new degradation cause is observed that doesn't fit the 5 | Surface to Corey for the 6th-cause locked, or propose mapping into existing cause |
| Sibling skill changes (e.g., sprint-mode v3) | Update wiring path citation; re-run wake-blank sim 2 |

---

**End of FIRING_CONTRACT.md v0.1.0 — aiciv-psychology**

*PROVISIONAL until ≥3 independent wiring paths exist for each trigger AND ≥1 cross-grade amendment-back is folded in.*
