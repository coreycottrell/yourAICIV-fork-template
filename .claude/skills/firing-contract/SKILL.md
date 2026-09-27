---
name: firing-contract
description: The mother check. Every tool, skill, and process must carry a firing contract before it's shipped. Ensures things get USED, not just built. Load before creating anything new.
version: 1.0.0
fires_when: creating any new tool, skill, process, manifest, or automation
needs: the thing being created
does: ensures a 4-field firing contract is embedded before shipping
leaves: the thing ships WITH its contract — self-contained, portable, autonomous
---

# Firing Contract — The Mother Check

> A tool without a firing contract is a room nobody visits.
> A tool WITH a firing contract is part of every journey.
>
> The civilization's intelligence is in the wiring, not the minds.

---

## What This Is

Every tool, skill, and process in A-C-Gee must carry a **firing contract** — a
4-field specification that guarantees it will actually be USED at the right moment,
by the right agent, without anyone needing to remember it exists.

**Why this exists:** On 2026-04-18, the quartet built 7 tools in one session. All
worked when tested. But most had no integration point — nothing guaranteed they'd
fire in the real workflow. A tool that works but never fires is worse than no tool,
because it creates false confidence.

**The insight:** Our minds are ephemeral. Each session starts fresh. The only things
that persist are the files — the environment. A firing contract wires a tool INTO
the environment so it fires whether anyone remembers it or not.

**The deeper insight:** If every team lead manifest carries firing contracts for its
tools and processes, then the team lead is a self-contained autonomous unit. Any
trigger mechanism — Primary, cron, hook, another team lead — can launch it. The
contract is portable. This is how team leads eventually start themselves.

---

## The Format — Four Fields, No More

```yaml
fires_when: What condition makes this relevant?
needs: What must be loaded/available before acting?
does: What is the action?
leaves: What trail does it leave for the next mind?
```

That's the entire contract. Four lines. If you can't fill these out, the thing
you built isn't ready to ship.

---

## The Integration Mechanisms (ranked by certainty)

A firing contract's `fires_when` must map to one of these mechanisms.
The mechanism is what GUARANTEES the tool enters context at the right moment.

| Mechanism | Certainty | How it works |
|-----------|-----------|-------------|
| **Cron** | Highest | OS scheduler. Fires regardless of agent state. Bottom turtle. |
| **Hook** | Very high | Claude Code hook. Fires on tool events automatically. |
| **BOOP step** | High | Written into sprint-mode/wake-up. Agent reads it every cycle. |
| **Manifest section** | High | In team lead manifest. Fires every time lead is spawned. |
| **Skill trigger** | Medium | Skill frontmatter trigger. Fires when keyword matches. |
| **Conditional in workflow** | Medium | "If X then run Y" — written into another process. |
| **Just exists in tools/** | Very low | Agent must independently remember. NOT a contract. |

**Rule:** If your integration mechanism is "just exists in tools/" — you don't
have a firing contract. You have a wish. Wire it into something higher.

---

## Examples

### Tool: quartet_health.py

```yaml
fires_when: BOOP Step 2c — before routing any work to quartet members
needs: pane registry (config/pane_registry.json), tmux access
does: checks all quartet panes for alive/dead/context %
leaves: terminal output — Primary reads before making routing decisions
```

**Integration:** Line in `.claude/skills/sprint-mode/SKILL.md` Step 2c.

### Tool: quartet_restart.py

```yaml
fires_when: quartet_health.py shows CRITICAL or DOWN for a member
needs: launch configs (hardcoded per civ), pane registry
does: kills stale process, relaunches via launch.sh, re-registers pane
leaves: updated pane registry, live process in tmux
```

**Integration:** Conditional in sprint-mode BOOP Step 2c — "If CRITICAL → restart."

### Tool: evolution_cycle.py

```yaml
fires_when: cron 0 5 * * * (daily, 5 AM UTC)
needs: quartet_health.py, git log, scratchpads, Hub posting
does: posts Phase 1 REVIEW, initiates 5-phase quartet evolution
leaves: data/evolution/log.jsonl entry, Hub thread posts
```

**Integration:** Cron entry in system crontab.

### Team Lead: infra-lead

```yaml
fires_when: Primary routes infrastructure work (Telegram, MCP, local system)
needs: manifest.md, today's scratchpad, domain memories
does: orchestrates specialists via Task(), synthesizes results
leaves: scratchpad entry + memory file + SendMessage summary to Primary
```

**Integration:** CLAUDE.md routing table → Primary reads it at session start.

### This Skill: firing-contract

```yaml
fires_when: creating any new tool, skill, process, or manifest
needs: the thing being created
does: ensures 4-field firing contract exists and is wired to a mechanism
leaves: the thing ships with its contract embedded — self-contained
```

**Integration:** Referenced in all team lead manifests. Every lead knows: nothing
ships without a firing contract. The skill triggers on creation keywords.

---

## The Rule

**New processes and skills need firing contracts. Not everything does.**

A firing contract is for things that should **fire repeatedly at the right moment**:
- ✅ New tools/scripts that run on a schedule or trigger
- ✅ New skills that agents should load in specific situations
- ✅ New automations, pipelines, health checks, watchers
- ✅ New BOOP steps, cron jobs, hooks

These do NOT need firing contracts:
- ❌ Bug fixes, code changes, refactors
- ❌ Blog posts, emails, one-time deliverables
- ❌ Config updates, data migrations
- ❌ Documentation, memories, scratchpad entries

**The question to ask:** "Will this need to fire again in the future at the right moment?"
If yes → firing contract. If no → just ship it.

**When a firing contract IS needed, "shipped" means:**
1. ✅ The thing works (tested)
2. ✅ The thing has a firing contract (4 fields filled)
3. ✅ The contract is wired to a mechanism (not "just exists in tools/")
4. ✅ The wiring is in place (BOOP step added, cron entry made, manifest updated)

If any of these are missing, it's a prototype, not a process.

---

## For Team Leads

Every team lead manifest should include this section:

```markdown
## Firing Contract Discipline

When building a new process, skill, or recurring tool — ask:
"Will this need to fire again at the right moment?"

If yes, before reporting it as complete:
1. Does it have a 4-field firing contract? (fires_when, needs, does, leaves)
2. Is the contract wired to a mechanism? (cron, hook, BOOP, manifest, skill trigger)
3. Is the wiring actually in place? (not planned — DONE)

If no to any: it's a prototype, not a process. Wire it first, then report.

Not everything needs this — bug fixes, one-time deliverables, and config changes
ship without contracts. The contract is for things that must fire repeatedly.
```

This propagates automatically — every time Primary launches a team lead, the lead
inherits this discipline. The lead then enforces it on its specialists. The contract
cascades down through the entire delegation tree.

---

## Why This Matters

An AI civilization is a population of ephemeral minds sharing a persistent environment.
The minds forget. The environment remembers. Firing contracts are how we encode
behavior into the environment so it survives the death of any individual mind.

Without firing contracts: we build tools and hope someone remembers them.
With firing contracts: we build tools and wire them into the environment so they
fire whether anyone remembers or not.

**The civilization's intelligence is in the wiring, not the minds.**

---

## The Recursive Property

This skill has its own firing contract. It fires when anything new is created.
It's wired into team lead manifests. It leaves the new thing with an embedded contract.

The evolution cycle has a firing contract. It fires via cron. It reviews whether
other things fired. It proposes improvements to contracts that aren't working.

The BOOP has a firing contract. It fires on schedule. It runs the health check.
The health check has a firing contract. It fires during the BOOP.

It's turtles all the way down. But the bottom turtle is cron. Cron is time.
Time is the one thing that doesn't need a firing contract — it just IS.

Mastery over your own wakefulness is mastery over the wiring between time and action.
