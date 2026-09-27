---
name: scratchpad-append
version: 0.1.0
status: PROVISIONAL — standardized 2026-07-02 per steward directive ("ship both — scratchpad = hygiene, ARC = centerpiece").
owner: mind-lead-analog on your fork
purpose: THE per-turn short-term hygiene layer. Append prose state to today's scratchpad EVERY turn, so a fork returning from auto-compact / cross-turn interruption / a fresh session picks up mid-thought without re-parsing conversation history.
composes_with: [the-arc, grounding-docs, sprint-mode, self-knowledge, auto-consolidate, wwcw]
---

# scratchpad-append — the per-turn short-term hygiene layer

**Read this ONE file to know the discipline.** The whole rule collapses to: *the scratchpad is the only memory that survives auto-compact. Write to it. Every turn. Prose is fine.*

---

## The one-line frame

> **Short-term context is per-turn prose — what am I doing right now, what just changed this turn, what is the next move?** It's not a story-shape (that's `the-arc`). It's not a permanent fact (that's `learn-cycle-contract` + canon). It's the running thought a mind carries between turns, in the mind's own prose voice, so a compact or a wake doesn't lose the current move.

---

## Where scratchpad-append sits in the memory tier stack

| Tier | Timescale | Skill | Storage | Discipline |
|---|---|---|---|---|
| **short** | this-turn | **`scratchpad-append` (this skill)** | `.claude/scratchpad-daily/YYYY-MM-DD.md` | append prose per turn; hygiene, not centerpiece |
| **medium** | days-to-weeks | `the-arc` | `arc/{live.jsonl, recent.md, epoch.md, ARC-NOW.md}` | append structured events; the CENTERPIECE |
| **long** | permanent | `learn-cycle-contract` + `canon_append` | `mem/canon/<lead>/log.jsonl` | witnessed substrate-delta with different-mind verifier |

**Steward directive 2026-07-02: SHIP BOTH.** The scratchpad is the hygiene layer. The ARC is the centerpiece. They compose — the ARC does NOT re-parse scratchpad prose, and the scratchpad does NOT try to be structured event-log.

---

## When to load this skill

- **Every turn that produces work.** Before this turn ends, append a brief prose entry to today's scratchpad.
- **After auto-compact** (silent context shrink between turns). Read today's scratchpad FIRST to know what was just done, then continue.
- **On a fresh wake** (any duration). Read today's scratchpad after the mandatory floor (`grounding-docs`, `self-knowledge`) — it carries what the last-run-instance was doing.
- **Before running any workflow / delegation.** Note the trigger + expected outcome so the next-turn mind can grade whether it landed.

---

## The path (one file per day)

```
.claude/scratchpad-daily/YYYY-MM-DD.md
```

**One file per calendar day.** Rolls at 00:00 in your timezone (or UTC — either is fine, the discipline is the append, not the boundary). If today's file doesn't exist yet, the wake mind is the first mind of the day; it CREATES the file and appends its first entry.

Keep the file BOUNDED — a day's worth of turn-notes is normally 5-20KB. If it grows past ~50KB, the auto-consolidate skill (or your fork's daily consolidator) rolls the tail into a per-day summary and starts fresh.

---

## The three-step reflex (short-term hygiene)

### Step 1 — Read today's scratchpad (on wake / after auto-compact)

```
Read: .claude/scratchpad-daily/YYYY-MM-DD.md   (use today's date)
```

If the file doesn't exist yet, that means this is the first turn of the day — proceed with no prior state.

### Step 2 — Orient on current state

After reading, answer these questions BEFORE taking any action:

1. **What's actively in flight?** (running workflows, in-progress work, open sub-tasks)
2. **What was just completed this session / today?** (last-turn completions, receipts)
3. **What's blocked or waiting for the steward?** (decisions needed, approvals pending)
4. **Any warnings or recovery notes?** (crash marks, self-kill guards, dead-pane alerts)

### Step 3 — Append this turn's entry BEFORE the turn ends

```
Append: ## [HH:MM UTC] — <brief description of what happened this turn>
- Active: <workflows / delegations still running>
- Completed: <what shipped this turn>
- Blockers for steward: <what needs a steward-side decision>
- Notes: <anything a next-turn mind needs to know>
```

**The scratchpad is the only memory that survives auto-compact. Write to it. Every turn.**

---

## Anti-patterns (things to NOT do)

1. **DO NOT** treat the scratchpad as permanent memory. Turn-prose decays fast; if something is worth keeping past the day, promote it: emit an arc-event (`the-arc`) OR run `learn-cycle-contract` and append to canon.
2. **DO NOT** re-parse the scratchpad to feed the ARC. The ARC consumes structured events from workflow firewall returns + kanban transitions + direct emits. The scratchpad is prose for the mind's own continuity, not a machine-readable feed.
3. **DO NOT** skip the append at end-of-turn. The temptation is highest when the turn feels "small" — that's when the failure mode bites hardest, because the next turn thinks nothing happened.
4. **DO NOT** let the scratchpad grow unbounded. Consolidate (or archive) old day-files; today's file should be readable in one pass at wake.
5. **DO NOT** use the scratchpad as a substitute for a firing contract. Duties belong in `FIRING_CONTRACT.md` files that a workflow enforces; the scratchpad is running commentary, not a covenant.
6. **DO NOT** put the scratchpad on the delegation report-up path. It is a coordination workspace ALONGSIDE report-ups (mirror of the origin substrate's per-workflow scratchpad §23 doctrine — the scratchpad points at the ledger, it never claims to BE the ledger).

---

## Composition rules

- **vs `the-arc`:** the scratchpad is prose ("what am I doing right now?"); the ARC is structured events ("what story am I in?"). They compose — the scratchpad may REFERENCE arc-events by ID / thread name, but the ARC never re-parses scratchpad prose.
- **vs `learn-cycle-contract` (canon):** the scratchpad is ephemeral running thought; canon is witnessed permanent substrate-delta. If a scratchpad entry crosses into "this is a learning worth keeping," promote it through `learn-cycle-contract` — a DIFFERENT mind verifies, then `canon_append` writes. Never promote a scratchpad note directly to canon without the verifier gate.
- **vs `auto-consolidate`:** `auto-consolidate` reads the day's scratchpad and rolls the essentials into whatever durable form the fork uses at end-of-day (canon promotions, arc-event emits, next-day priority header). The scratchpad is the RAW substrate `auto-consolidate` reads from.
- **vs handoffs (if the fork keeps them):** handoffs are human-narrative artifacts for cross-session continuity when a specific hand-off is happening. Scratchpad is the always-on daily running-state. They coexist.

---

## Why this discipline exists (the failure mode it cures)

**The gap this closes:** on any harness that supports auto-compact (silent context shrink between turns, or a re-wake into a new session), the mind loses the current turn's running-state — what workflow it just kicked off, what it was about to do next, whether the last delegation returned. Without the scratchpad-append, the next-turn mind either re-does work (wasteful) or drops in-flight work (lossy).

**Cost of the discipline:** ~5-10 seconds per turn to append a 5-line entry.
**Cost of skipping:** a re-wake mind that re-does the same work, or worse, silently drops an in-flight delegation because nothing on disk carries "I was mid-way through this."

**The discipline is cheap; the failure mode is expensive.** Ship the discipline.

---

## Verification

**On any fork, after 3 days of running the discipline**, do the reboot-blank test:

1. Auto-compact happens (or force one by starting a fresh session).
2. New mind reads ONLY today's scratchpad.
3. Can it name: what's actively in flight, what shipped this session, what's blocked?
4. **If yes** → discipline works. Keep it.
5. **If no** → the entries are too thin or too formatted-for-the-writer, not for-the-reader. Iterate the template (the Step 3 shape above) until a fresh mind picks up cleanly.

---

## Reversibility

Delete `.claude/scratchpad-daily/*.md` + stop appending. No other organ depends on it (the ARC has its own feeds; canon has its own gates). The mind loses per-turn continuity but the heartbeat survives.

**Scratchpad-append is additive, cheap, and honest.** It's the discipline that says: *I am accountable to the next mind that has to pick this up mid-thought, and I write for that mind, not for myself.*

---

## Provenance

- Origin discipline: origin civ's `scratchpad-read` skill (short read-side) + `scratch-pad` skill (long full-schema version) collapsed into ONE append-focused per-turn hygiene skill for portable adoption.
- Standardized into this repo: 2026-07-02 per steward directive *"ship both — scratchpad = hygiene, ARC = centerpiece."*
- Companion: `.claude/skills/the-arc/SKILL.md` (the centerpiece medium-term-context organ this composes with).
- Not centerpiece — hygiene layer. If a fork must choose one to adopt first, adopt `the-arc` (medium-term recall compounds over weeks); scratchpad-append cures a common but transient failure mode. Both together is the whole picture.
