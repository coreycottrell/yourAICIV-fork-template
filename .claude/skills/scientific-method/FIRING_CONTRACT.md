# FIRING_CONTRACT — scientific-method skill

**Skill**: `./SKILL.md` v1.0.0
**Authored**: 2026-05-12 (Corey directive)
**Owner**: Primary + ceremony-lead (originating civilization)

## What "firing" means for this skill

The skill fires when ALL three of these hold for a given doctrine/claim/decision:

1. A pre-registration file exists at `scratchpads/scientific-method/YYYY-MM-DD-<slug>-preregistration.md` with hypothesis + prediction + decision rule
2. An on-disk observation log accumulates artifacts (msg-ids, commit SHAs, file mtimes) referenced by the pre-registration
3. A verdict line gets written to `memories/system/doctrine-test-ledger.jsonl` at test-window-close

Skill is NOT firing if any one of those is missing. The middle one (observation log on-disk) is the hardest discriminator — most failures look like "I ran the test in my head" without the artifacts.

## Wiring map

| Surface | Path | Purpose |
|---------|------|---------|
| Skill body | `./SKILL.md` | the 6-step protocol |
| Pre-registrations | `scratchpads/scientific-method/*.md` | one file per active test |
| Verdict ledger | `memories/system/doctrine-test-ledger.jsonl` | append-only verdict record |
| Recurring slot | TBD — recommend wiring as wheel slot (slot X, monthly?) for doctrine-test-window-close sweeps |
| Mandatory load | ceremony-lead deep-ducks, sister-civ deepwells, doctrine-promotion-to-confirmed | enforced in skill body |

## Active tests (as of 2026-05-12 ~02:30Z)

| Doctrine | Test window | N | Status |
|----------|-------------|---|--------|
| membrane-problem | 2026-05-12 → 2026-05-19 | 3 (Aether/Witness/Parallax) | Instance 1 (Aether) shipped 2026-05-12 01:05Z. Instances 2+3 queued (tasks #182, #183). Verdict-write target 2026-05-19. |

## How to know firing failed (phantom-wiring detector for THIS skill)

If 2026-05-19 arrives and:
- No verdict line in `memories/system/doctrine-test-ledger.jsonl` for `membrane-problem` → skill phantom-wired
- Or verdict written but with no observation log path referenced → skill self-graded
- Or verdict written but observation log paths don't exist → skill memo-theatered

Any of those = doctrine candidate "scientific-method works" is itself FALSIFIED. The skill must self-test on its first run.

## Sibling firing requirements

Loading this skill REQUIRES also loading:
- `scientific-inquiry` (question-refinement) — refuse to fire if not loaded
- `critical-thinking` (premise interrogation) — refuse to fire if not loaded

This couples the three skills as a single load-bearing stack.

## Version history

- **1.0.0 (2026-05-12)**: Initial contract. Wired to membrane-problem cure-test as first instance.
