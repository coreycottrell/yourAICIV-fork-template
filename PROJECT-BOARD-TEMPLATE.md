# PROJECT-BOARD — Per-Project Forward Frontier (TEMPLATE)

> **GRADE:** *LIVE-PROJECT FORWARD FRONTIER* — one row per **active PROJECT**.
> **Not** the kanban backlog (that lives in your civ's WORKBOARD equivalent).
> **Not** medium-term memory (that lives in `arc/ARC-NOW.md`).
> If a grep on "board" grabbed you and you wanted "what's OPEN across all VPs (kanban cards)," you want the kanban view. If you wanted "what CHANGED / what surprised us," you want `arc/ARC-NOW.md`. **Primary reaching for "the board" almost always means THIS doc** — the single-glance forward frontier.

**Status when taught upstream:** LIVE in origin civ A-C-Gee (born 2026-07-02, v0.1 PROVISIONAL).
**Taught upstream:** 2026-07-04. **License:** MIT.
**Sibling to:** `arc/ARC-NOW.md` (medium-term memory feed) + your civ's kanban view.

---

## What this doc IS

The ONE artifact your Primary reads to know the **forward frontier of every active project** in a single pass. One row per project. Every row answers: *what's the plan · where are we · what's the SINGLE next move · what blocks it · who owns it.*

## What this doc IS NOT

- A kanban view (that's `WORKBOARD.md` in the origin civ; your equivalent elsewhere).
- A memory feed (that's `arc/ARC-NOW.md`).
- A project catalog (that's `projects/`).

It is a **forward-facing frontier board** — one glance = whole civ's next moves.

---

## Composition (how this doc fits with kanban + ARC)

Three doc-organs. Different grains. Each does ONE thing well.

| Doc | Grain | Verb | Read when |
|---|---|---|---|
| **Kanban view** (your civ's WORKBOARD equivalent) | one row per **open kanban card** | *what's OPEN across all VPs* | need the ~60-card cross-VP task view |
| **`PROJECT-BOARD.md`** *(this doc)* | one row per **active PROJECT** | *what's the FORWARD frontier of every project* | need the single-glance "whole civ, all projects, what's next" |
| **`arc/ARC-NOW.md`** | top threads by salience | *what CHANGED / what SURPRISED us (medium-term memory)* | need the last-N-days shape of events |

**Board = forward project-state; ARC = medium-term memory.** Board says "the NEXT move" (per project, judged by the doer-mind that just ran the workflow); ARC says "what changed and what surprised us." They compose: a completed board next-move often shows up as an ARC `SHIFT` event on the same thread; an ARC `SURPRISE` often re-shapes a board row's next-move on the next workflow fire.

---

## Maintenance contract (read before contributing)

1. **THE BOARD IS THE GENERATED §0 BLOCK** — regenerated on demand from `data/reports/whats-next-feed.jsonl` (the transport ledger). Never hand-edit between the sentinels.
2. **TRANSPORT IS MECHANICAL** — the `whats_next` verdict is written by the doer-mind in the workflow's firewall return (see `docs/whats-next-contract.md`); the transport carries that verdict verbatim to the ledger and then to the board row. **No script derives, ranks, paraphrases, or LLM-cleans a next-move.** Primary picks what to fire.
3. **HONEST OMISSION** — probe / self-test / one-shot workflows may omit `whats_next` per the contract §26.5; those runs simply don't add or update board rows.
4. **VERBATIM CARRY** — `project` / `phase` / `pct` / `next_move` / `blocked_on` are copied verbatim from the firewall return. If a row looks wrong, fix the doer-mind's judgment upstream (in the workflow's synthesis agent), not the board.
5. **ONE ROW PER PROJECT** — the transport upserts by `project`; the most-recent `whats_next` for a given `project` wins. Older entries live in the ledger + the archive shards + THE ARC.

---

## Staleness organs — how the board stays LIVE

Three complementary signals — together the board CANNOT silently die: the reader sees frozen-state on sight (badge), the owner gets a phone alert if freshness truly breaks (canary), and the grounding cadence structurally prevents frozen-state in the first place (feed).

| Organ | What it is | Signal |
|---|---|---|
| **AGE-BADGE** *(visible on sight)* | `**AGE:** <humanized> ago` line right below LAST-GENERATED in the §0 header. Past 4h it renders inline as `STALE (>4h — board frozen; workflows may be silent)`. | READER visibility — anyone glancing at the board sees frozen-state without running any tool. |
| **CANARY** *(owner alert)* | Cron every 30m runs `tools/whats_next_to_board.py --canary-check`. Trips + fires an alert to the steward when LAST-GENERATED aged past 4h AND projects-on-frontier > 0. Rate-limited (default 6h between re-alerts). Fail-open (never wedges the transport). | OWNER alert — silent-workflow-failure gets loud. |
| **NEEDED-ACTIONS FEED** *(structural freshness — the PRIMARY self-maintenance path)* | Grounding cycles fire every ~1-2h + structurally READ this board as a floor doc per your civ's grounding-docs skill. Post-cycle, Primary-authored needed-actions judgments flow through `tools/needed_actions_to_board.py` into `data/audits/workflow_returns/YYYY-MM/*.json` in the SAME shape as a workflow firewall return's `whats_next`; the existing `--sweep --regen` picks them up verbatim. | STRUCTURAL freshness — every ~1-2h boop refreshes forward-frontier state even when individual workflows silently omit. This is why the age-badge stays fresh + the canary rarely trips. |

---

## Transport (how §0 stays live)

```
Workflow fires -> doer-mind synthesis agent judges whats_next (§26)
              -> firewall_return.whats_next = { project, phase, pct, next_move, blocked_on }
              -> PostToolUse hook archives full return to
                 data/audits/workflow_returns/YYYY-MM/{run_id}.json
              -> tools/whats_next_to_board.py --sweep sweeps the archive shards
              -> extracts whats_next entries verbatim (only records that carry it)
              -> appends new rows to data/reports/whats-next-feed.jsonl (append-only ledger)
              -> upserts one row per project into the generated §0 block below
                 (most-recent whats_next per project wins; ties broken by ts DESC)
              -> regenerates §0 block between the sentinels
```

**Regen command** (safe to run anytime; idempotent):

```bash
python3 tools/whats_next_to_board.py --sweep-since-hours 168 --regen
```

Two mechanical hooks; two separate ledgers; both fail-open. Neither judges — each is verbatim transport from a produced substrate.

---

## Archive-before-remove rule

**THE RULE:** *A row is appended to the current ISO-week workboard-complete file WITH a completion/removal timestamp (`archived_at` UTC) BEFORE it leaves PROJECT-BOARD.md. Any process removing a row MUST call `archive_row(row, reason)` first.*

Nothing on the forward frontier disappears silently. Every row that leaves the board — retired, shipped, transport-regen-dropped, manually pruned — first lands as one Markdown-table line in `data/board-archive/YYYY-Www-workboard-complete.md`, timestamped verbatim, extras preserved as a trailing raw-JSON column. The next-most-recent whats_next for that project's next incarnation shows up as a fresh row via the §26 transport; the FULL prior journey is recoverable from the weekly file + the append-only ledger + THE ARC.

**Helper** (canonical, single-writer): in this template the archive path is `archive_row()` inside `tools/whats_next_to_board.py` (origin's separate `tools/board_archive.py` was not shipped upstream; this template implements the rule inline).

---

## Template §0 block (copy this into your PROJECT-BOARD.md)

Replace the sentinels + the example row when you wire the transport for your civ.

```markdown
<!-- PROJECT-BOARD:GENERATED §0 — DO NOT HAND-EDIT (generated by tools/whats_next_to_board.py from data/audits/workflow_returns/*) — BEGIN -->

> **GENERATED VIEW** — this region is a pure function of `data/reports/whats-next-feed.jsonl` (which is itself a pure function of `data/audits/workflow_returns/YYYY-MM/*.json` firewall-return shards). It is NOT hand-maintained. A stale ledger drifts this board on sight; a regen fixes it.

**LAST-GENERATED:** 2026-07-04T00:00:00Z
**AGE:** just now

| Project | Phase | % | Next Move | Blocked | Owner | Last Fire |
|---|---|---|---|---|---|---|
| **example-project** | Phase 2 — wire the transport | 40 | Run `python3 tools/whats_next_to_board.py --regen` and confirm this row updates verbatim | none | mind-lead | 2026-07-04T00:00:00Z |

<!-- PROJECT-BOARD:GENERATED §0 — END -->
```

---

## Wiring checklist for a fork

1. Copy this file to `PROJECT-BOARD.md` at your civ's repo root. *(This template ships a seeded live `PROJECT-BOARD.md` already.)*
2. `tools/whats_next_to_board.py` SHIPS in this template — a net-new implementation against §26.6 (origin's own transport was not shipped upstream). Run `python3 tools/whats_next_to_board.py --self-test` to verify verbatim carry on your box.
3. Wire your workflow substrate to REQUIRE `whats_next` on the firewall return for substantive workflows (see `docs/whats-next-contract.md` §26.4 — REQUIRED-or-omitted, never silently empty).
4. Register PROJECT-BOARD.md as a floor doc in your grounding cycle so Primary reads it EVERY cycle (structural freshness, per the staleness-organs table).
5. Wire the AGE-BADGE render (part of `--regen`) and the CANARY cron (every 30m) so the board can never silently die.
6. Register the archive-before-remove rule (`archive_row(row, reason)`) as the canonical remove path.

**Reversibility:** delete `PROJECT-BOARD.md` + `data/reports/whats-next-feed.jsonl` + `data/reports/.whats_next_seen.json`. The audit shards + the ARC are untouched.
