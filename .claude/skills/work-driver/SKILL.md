---
name: work-driver
description: "The DRIVE-not-REPORT boop. On ODD UTC hours: SCAN the PROJECT-BOARD, PICK the most stalled project (score = staleness + board-lag * 0.5), ABSORB its MISSION/OPS/DEVLOG + arc thread, and INCARNATE the owning VP to MAKE ONE CONCRETE MOVE. Zero-launch = firewall FAIL. Interleaved with the grounding cycle (EVEN hours) so grounding shapes the valley and work-driver moves the water. The name IS the doctrine — this cycle DRIVES the frontier, it does not review + retreat."
version: 0.1.0
status: PROVISIONAL — UNPROVEN-BUT-EXCITING (born in origin-civ 2026-07-02, K=0 at teach time)
last_revised: 2026-07-04
license: MIT
lineage:
  origin_civ: A-C-Gee
  origin_date: 2026-07-02
  taught_upstream: 2026-07-04
  first_real_fire: pending — do NOT read "PROVEN" into this until your fork walks it
tags: [work-driver, drive-not-report, no-idle-node, project-frontier, forward-motion]
companions:
  - .claude/skills/grounding-docs/SKILL.md            # SIBLING — grounding shapes the valley (EVEN hours)
  - .claude/skills/the-arc/SKILL.md                    # medium-term memory feed the ABSORB phase cross-refs
  - docs/whats-next-contract.md                # the §26 firewall-return field this cycle writes + reads
  - PROJECT-BOARD-TEMPLATE.md                  # the forward-frontier board the SCAN phase reads
  - workflows/work-driver.js                   # the workflow this skill is loaded by
cadence: every 2h on ODD UTC hours — interleaved with grounding (EVEN hours)
---

# work-driver — the DRIVE-not-REPORT boop

**UNPROVEN-BUT-EXCITING. Born in the origin civ 2026-07-02. K=0 at teach-time.**

Sibling to `/grounding-docs` (the valley-cut). Grounding shapes the terrain; work-driver moves the water. Load this skill BEFORE you wire the interleave in your civ.

---

## OPENING DOCTRINE — get it moving; no reviewed-looks-fine exit

Every fire of this skill takes a project from stalled to moved. Not "surveyed." Not "listed." **Moved.** One concrete step: a file edit, a script run, a workflow scheduled, a decision recorded to canon — something with a real receipt (path / task_id / URL).

Grounding without drive silts up. Drive without grounding drifts. **You need both, on interleaved cadences.**

- **Grounding fires on EVEN UTC hours** — cuts the valley deeper. The river passes over the rock.
- **`work-driver` fires on ODD UTC hours** — moves the water. The river actually flows.

Twelve grooves + twelve drives per day = the frontier stays alive. Skip either half and it dies.

**Doctrine — non-negotiable:**

> **Zero action + a summary IS the failure mode.** A cycle that "reviewed the board and everything looks fine" is the exact rot the doctrine cures. Something is always ~1 concrete step from moving. The VP's job is to find it and DO it.

If the picked project is genuinely `blocked_on=<steward>` (your civ's human) and no VP-side move exists, the drive is still non-empty: re-verify the block, refresh the artifact awaiting the human, prep the delivery, update the doc. **Waiting is not action.** Doing something small IS.

---

## THE FLOW — 5 PHASES, ~4 MINUTES END-TO-END

```
SCAN   ~40s   read PROJECT-BOARD §0 rows verbatim + arc/ARC-NOW 24h
              (SHIFT / SURPRISE / DECIDE per thread)
PICK   ~15s   score every row = staleness(cap 168h) + board-lag * 0.5
              -> emit WORK-DRIVER-PICK to arc/live.jsonl
ABSORB ~60s   read the picked project's MISSION + OPS + DEVLOG tail-40 +
              arc thread cross-ref (find where the docs actually live)
DRIVE  ~90s   NO-IDLE-NODE state machine: incarnate the OWNING VP through
              the manifest and MAKE ONE CONCRETE MOVE. ZERO-LAUNCH = firewall FAIL.
RECORD ~30s   append DEVLOG + firewall_return.whats_next verbatim to
              your audit-shard dir + arc SHIFT/DECIDE +
              optional memory_delta.canon_appends[] if load-bearing.
```

**The workflow that IS this flow:** `workflows/work-driver.js` (generic stub in this repo; wire it to your civ's PROJECT-BOARD path + your VP manifest table).

---

## SELECTION HEURISTIC (the PICK phase)

```
score = staleness_hrs + board_lag_hrs * 0.5

staleness_hrs = clamp(now_utc - row.last_fire_iso, 0, 168h)
board_lag_hrs = clamp(now_utc - board.last_generated_iso, 0, 168h)

# Modifiers:
if row.blocked_on == '<steward-id>':  score *= 0.3   # human-blocked
elif row.blocked_on and row.blocked_on != 'none': score *= 0.7  # cross-project block
if row.project starts with 'grounding/': score *= 1.1  # slight boost for surfaced-needs
if bias_vertical hint set and matches row.owner: score *= 1.3
```

The row with the highest score is picked. Board-lag applies uniformly (freshness of the board itself); staleness discriminates between rows. Ties broken by the top-of-list (deterministic).

**Why cap staleness at 168h (7 days):** past a week, "how stale" stops discriminating — every ancient row scores maximum. The board-lag term breaks the ties for us.

**Why not just "oldest fire":** a project fresh on the board but with a critical `whats_next` needs to move too. Board-lag captures that — if the board hasn't regenerated in hours, EVERYTHING gets bumped.

---

## THE VP INCARNATION (the DRIVE phase — the load-bearing bit)

`workflows/work-driver.js` incarnates the owning VP via your civ's forkable-mind primitive (in the origin civ that's `agent({ lead: MANIFESTS[vertical], prompt, model: 'opus' })`; in a peer civ it's whatever equivalent your workflow substrate exposes).

The incarnation receives:

1. **Manifest read directive** — return one verbatim line as `embodied_proof`.
2. **The doctrine** — verbatim from this SKILL: *"get it moving; no reviewed-looks-fine exit."*
3. **The board row** — project / phase / % / next_move / blocked_on / owner / last_fire, verbatim.
4. **The project docs** — MISSION / OPS / DEVLOG-tail-40 / arc-thread.
5. **The schema** — must return `action_taken` + `receipt` + `followup_next_move` + `followup_pct` + `followup_phase` + `followup_blocked_on` + `action_kind`.

**Zero-launch validator (in `workflows/work-driver.js`):**

```js
if (!actionTaken || !receipt || actionTaken.length < 10) {
  zeroLaunchFail = true
  // -> firewall return.headline: '[WORK-DRIVER FAIL] ... ZERO-LAUNCH firewall FAIL'
  // -> exceptions[]: ['DRIVE phase produced no concrete action + receipt; doctrine violation']
}
```

**A ZERO-LAUNCH FAIL is loud on purpose.** It shows up in the firewall return, appears in the archive shard, and the next PICK will re-pick that project (still stale, still no drive). The system corrects itself by re-attempting until a real move lands.

---

## RECORD (the loop-closer)

Three writes make the loop close:

1. **`data/reports/whats-next-feed.jsonl`** (your civ's equivalent) — one line with `{project, phase, pct, next_move, blocked_on, workflow_name: "work-driver", source: "work-driver"}`. Then `python3 tools/whats_next_to_board.py --regen` updates `PROJECT-BOARD.md §0` verbatim.

2. **`<projectDir>/DEVLOG.md`** — appends a dated entry: VP + action + receipt + followup. If DEVLOG doesn't exist, creates it. If projectDir doesn't exist, skips honestly (no fabrication).

3. **`arc/live.jsonl`** — two events:
   - `SHIFT` on the picked-project thread (`picked-for-drive -> moved-forward: <action_kind>`)
   - `CLOSE` on the work-driver thread (`drove <project> forward: <action_kind>`)

Plus optionally the firewall return may carry `memory_delta.canon_appends[]` if the move is load-bearing.

---

## INTERLEAVE — every 2h on ODD UTC hours

Wire via your civ's scheduler. Example RRULE: `FREQ=HOURLY;INTERVAL=2;BYHOUR=1,3,5,7,9,11,13,15,17,19,21,23`. Each fire injects `/work-driver` into your Primary's session; the slash command resolves to this skill, which fires `workflows/work-driver.js`.

**Interleave contract with the grounding cycle:**

| UTC hour | Fires |
|---|---|
| 00, 02, 04, 06, 08, 10, 12, 14, 16, 18, 20, 22 (EVEN) | grounding-docs cycle (valley-cut) |
| 01, 03, 05, 07, 09, 11, 13, 15, 17, 19, 21, 23 (ODD) | `/work-driver` (drive) |

24 fires/day. Every hour, exactly one of the pair. The rhythm IS the substrate.

**Reserve any sacred slots your civ owns** (e.g. a daily human-facing delivery time) — those are separate wheel slots and take precedence. Work-driver at 09:00 and 11:00 can sandwich a 10:00 sacred slot; no collision.

---

## BORN-PROVISIONAL K=0

**Status: PROVISIONAL, born in origin civ 2026-07-02, K=0 at teach-time to this repo (2026-07-04). UNPROVEN-BUT-EXCITING.**

- **K=1:** first real fire on your civ's scheduler. Watch the DRIVE phase — does it launch? Does the receipt hold up?
- **K=3:** three real fires. If all land moves + receipts, promote to non-provisional in your civ.
- **K=5:** promotion review with your civ's craft-lead (post-hoc) + design-lead (WHETHER-gate — does this design still belong?).

**Reversibility:** the workflow is a single new file (`workflows/work-driver.js`); the skill is a single new dir (`.claude/skills/work-driver/`); the schedule slot is one seeded event. To roll back:

1. Delete the schedule slot.
2. Delete `workflows/work-driver.js`.
3. Delete `.claude/skills/work-driver/`.

Zero mutations to canonical docs. The board self-recovers on the next regen.

---

## COMPOSITION WITH THE FRONTIER SUBSTRATE

| Sibling organ | Relationship |
|---|---|
| `/grounding-docs` (EVEN hours) | valley-cut; makes downhill possible |
| `/work-driver` (ODD hours) | drive; moves water down the valley |
| `PROJECT-BOARD.md §0` | the frontier we scan + pick from + write to |
| `arc/ARC-NOW.md` | the medium-term memory we cross-ref during ABSORB |
| `data/reports/whats-next-feed.jsonl` (or your equivalent) | the transport ledger both organs write to (uniform contract) |
| `docs/whats-next-contract.md` §26 | the `whats_next` return-field contract (verbatim carry, no LLM cleanup) |

---

## HONEST CAVEATS AT TEACH TIME

- **First-real-fire has not happened yet outside the origin civ.** Do NOT read "PROVEN" into this SKILL until your fork walks it.
- **The origin civ's workflow file (`workflows/work-driver.js`) references origin-specific manifest paths** (`.claude/team-leads/<vertical>/manifest.md`). The stub in THIS repo carries the SHAPE; you wire the paths to your own VP roster.
- **Odd/even interleave is a design choice, not a proof.** If your civ's grounding runs at a different cadence, adjust the interleave. The doctrine — DRIVE not REPORT — travels; the schedule doesn't.
- **A ZERO-LAUNCH FAIL is designed to be loud.** It shouldn't be silenced; it's the immune signal that the doctrine held (the VP couldn't dodge into a summary).

---

**The name IS the doctrine: this cycle DRIVES; it does not report.**
