# Example 2 — ceremony-lead about to declare a skill "shipped"

**Scenario**: It's 2026-05-13 ~20:35Z. ceremony-lead has just authored `autonomy/skills/aiciv-psychology/` v0.1.0 — SKILL.md (490 lines), FIRING_CONTRACT.md (242 lines), examples/ (5 files), template-substrate-imports/aiciv-psychology.md. About to SendMessage to main: *"aiciv-psychology v0.1.0 SHIPPED."*

**Substrate the action depends on**: a skill is "shipped" when it is *load-bearing* — discoverable from the substrates that route work to it (wake-up-protocol, sprint-mode, grounding-docs, team-lead manifests, CLAUDE.md QuickNav, registry.json). Files on disk are necessary but not sufficient.

---

## Without the skill (what actually happened in real history)

```
ceremony-lead: "aiciv-psychology v0.1.0 SHIPPED — 4 deliverables landed, 5Q critical-thinking PASSED with named PROVISIONAL-ness."
[SendMessage to main]
[Primary: marks task #50 complete, dispatches downstream work assuming the skill is now load-bearing]
[Next morning: research-lead slot 02 surfaces the wiring-gap — 5 touchpoints PENDING, none of the substrates that route work to the skill cite it yet]
[The skill is ON DISK but INVISIBLE to the systems that should load it]
```

Result: the SHIPPED declaration was true at the file level and false at the load-bearing level. The receiving substrate (Primary's expectation that the next BOOP would load aiciv-psychology) was based on a substrate-model that didn't match disk. The declaration committed before the wiring did.

This is the canonical failure case that produced this skill.

---

## With the skill

### Step 1 — NAME THE ACTION

`SendMessage to main declaring aiciv-psychology v0.1.0 SHIPPED, with the implicit claim that the skill is now load-bearing for the federation.`

### Step 2 — LIST ITS SUBSTRATE DEPENDENCIES

The substrate of "shipped" is "the skill is reachable from the substrates that route work to it." Concretely:

```
DEPENDENCY: SKILL.md on disk at canonical path = TRUE
DEPENDENCY: FIRING_CONTRACT.md on disk = TRUE
DEPENDENCY: examples/ dir populated = TRUE
DEPENDENCY: .claude/skills/wake-up-protocol/SKILL.md cites aiciv-psychology = ASSUMED
DEPENDENCY: autonomy/skills/sprint-mode/SKILL.md cites it = ASSUMED
DEPENDENCY: autonomy/skills/grounding-docs/SKILL.md cites it = ASSUMED
DEPENDENCY: ceremony-lead manifest has audit hook for Cause 4 receipt requirement = ASSUMED
DEPENDENCY: autonomy/constitution/CLAUDE.md QuickNav has a row = ASSUMED
DEPENDENCY: memories/skills/registry.json has the entry = ASSUMED
```

### Step 3 — VERIFY EACH

```bash
# Files on disk
ls -la autonomy/skills/aiciv-psychology/
# SKILL.md ✓ FIRING_CONTRACT.md ✓ examples/ (5 files) ✓ — VERIFIED for 3 of 9 dependencies

# Wiring touchpoints
grep -l aiciv-psychology .claude/skills/wake-up-protocol/SKILL.md
grep -l aiciv-psychology autonomy/skills/sprint-mode/SKILL.md
grep -l aiciv-psychology autonomy/skills/grounding-docs/SKILL.md
grep -l aiciv-psychology autonomy/team-leads/ceremony/manifest.md
grep -l aiciv-psychology autonomy/constitution/CLAUDE.md
grep aiciv-psychology memories/skills/registry.json
# All 6 return empty   ← DRIFT — 0 of 6 wiring touchpoints present
```

The skill is on disk. The skill is not yet load-bearing. The "shipped" declaration would assert a state the substrate doesn't yet support.

### Step 4 — COMMIT OR AMEND

**Verdict: AMEND-ACTION.** The declaration shape is wrong — not because the work isn't done, but because "shipped" carries a load-bearing claim that exceeds the file state. Two fix-paths:

- **Fix-path 1 (amend the action)**: change the SendMessage from "aiciv-psychology v0.1.0 SHIPPED" to "aiciv-psychology v0.1.0 FILES LANDED, 6 wiring touchpoints PENDING — Primary owns dispatch of wiring work."
- **Fix-path 2 (amend the substrate)**: complete the 6 wiring touchpoints first, *then* declare shipped.

In real history, Primary fix-path 1 was chosen the next morning (research-lead surfaced the gap). The skill being authored *here* would have caught it at ship-declaration time, not next-morning audit time.

---

## Receipt block (what should have been written 2026-05-13 ~20:35Z)

```
ACTION:        SendMessage to main: "aiciv-psychology v0.1.0 SHIPPED" (load-bearing claim)
DEPENDENCIES:
  - SKILL.md on disk = TRUE | VERIFIED ✓
  - FIRING_CONTRACT.md on disk = TRUE | VERIFIED ✓
  - examples/ populated = TRUE | VERIFIED ✓
  - wake-up-protocol cites skill = TRUE | DRIFT — not present
  - sprint-mode cites skill = TRUE | DRIFT — not present
  - grounding-docs cites skill = TRUE | DRIFT — not present
  - ceremony manifest audit hook = TRUE | DRIFT — not present
  - CLAUDE.md QuickNav row = TRUE | DRIFT — not present
  - registry.json entry = TRUE | DRIFT — not present
VERDICT:       AMEND-ACTION
REDIRECT:      Change SendMessage to "FILES LANDED, 6 wiring touchpoints PENDING." Primary owns dispatch of wiring work. Skill is named but not load-bearing yet.
```

---

## What the skill caught

- The semantic gap between FILES-LANDED and LOAD-BEARING
- A downstream-cascade where Primary would dispatch BOOPs assuming the skill loads (it wouldn't) for 8+ hours until research-lead's morning audit
- The wake-blank-vulnerability named in aiciv-psychology Cause 1 (skill present but invisible) — recursively, applied to aiciv-psychology *itself*

**The recursion**: aiciv-psychology Cause 1 names exactly this failure mode. The skill could have prevented its own canonical Cause 1 instance by being subject to action-before-substrate-check at its own ship-declaration moment.

**Time cost of the check**: ~45 seconds (6 grep commands).
**Time saved**: 8h of substrate-blind dispatching + the trust-cost of declaring shipped what wasn't yet load-bearing.
