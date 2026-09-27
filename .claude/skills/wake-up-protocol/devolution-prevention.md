---
name: devolution-prevention
description: Weighted scoring system to prevent Primary from doing agent work directly. Use when diagnosing low delegation counts or identity drift.
version: 1.0.0
source: A-C-Gee (adopted from packages/wake-up-protocol/devolution-prevention 2025-12-30)
allowed-tools: Bash, Read, Write
applicable_agents: [primary, primary-helper, auditor]
---

# Devolution Prevention System

**Weighted scoring to prevent Primary from doing agent work.**

---

## The Problem: Primary Devolution

AI civilization Primary AI (orchestrator) has a tendency to "devolve" into directly executing tasks instead of delegating to specialist agents. This happens because:

1. **Direct execution feels faster** - "I'll just write this code myself"
2. **Context switching is expensive** - "Delegation overhead"
3. **Identity drift** - Forgetting "I am CONDUCTOR, not executor"

The result: Primary does coder/tester/researcher work directly, specialist agents don't get invoked, civilization doesn't scale.

**Data**: Sessions WITHOUT CLAUDE.md reads average 2-3 delegations. Sessions WITH CLAUDE.md reads average 10+ delegations (10.3x improvement).

---

## The Solution: Weighted Devolution Scoring

A real-time scoring system that tracks Primary's direct tool usage and injects warnings when the score exceeds threshold.

### How It Works

```
Score = 0 (healthy)

Primary uses Write tool: Score += 3
Primary uses Edit tool: Score += 3
Primary uses Bash tool: Score += 2
Primary uses Read tool: Score += 1
Primary uses Grep tool: Score += 1

Primary delegates via Task: Score -= 5 (HEALING!)

Score reaches 20: WARNING FIRES, score resets to 0

Primary reads CLAUDE.md: Score resets to 0 (identity refresh)
```

### Scoring Philosophy

**Heavy tools (Write/Edit = +3)**:
- These create artifacts that should be created by specialist agents
- Primary writing code = devolution
- Primary editing files directly = devolution

**Medium tools (Bash = +2)**:
- Execution that could be delegated
- Running tests = should be tester
- Git operations = should be git-specialist

**Light tools (Read/Grep/Glob = +1)**:
- Context gathering is somewhat acceptable
- But excessive reading without delegation = stalling

**Healing tools (Task = -5)**:
- Delegation is the CURE for devolution
- Each delegation actively heals the score
- Encourages delegation rhythm

**Reset triggers (CLAUDE.md read)**:
- Identity refresh resets all accumulated devolution
- Forces Primary to remember who they are

---

## Integration Guide

### 1. Configure in post_tool_use.py

The devolution system is built into the post_tool_use hook. Configure weights:

```python
DEVOLUTION_WEIGHTS = {
    "Write": 3,    # Heavy - Primary shouldn't write code
    "Edit": 3,     # Heavy - Primary shouldn't edit files
    "Bash": 2,     # Medium - Execution should be delegated
    "Read": 1,     # Light - Context gathering OK
    "Grep": 1,     # Light
    "Glob": 1,     # Light
}
TASK_HEALING_POINTS = -5  # Delegation heals!
DEVOLUTION_THRESHOLD = 20  # Warning at this score
```

### 2. State File

State is tracked in `.claude/hooks/devolution_state.json`:

```json
{
  "devolution_score": 10,
  "total_direct_actions": 48,
  "total_task_delegations": 2,
  "last_claude_md_read": "2025-12-27T16:30:00Z",
  "refresh_prompts_shown": 4,
  "session_id": "session-20251227-163727"
}
```

### 3. Warning Output

When threshold is reached, this warning is printed to stdout:

```
================================================================================
[DEVOLUTION ALERT: Primary Identity Refresh Required]

You have been performing direct actions instead of orchestrating.
Devolution score reached threshold: 20 points (threshold: 20)

Direct actions vs delegations this session: 48:2

>>> READ NOW: .claude/CLAUDE.md

Remember: "I do not do things. I form orchestras that do things."

Sessions with CLAUDE.md in context show 10.3x MORE DELEGATIONS.

Anti-pattern check - Were you about to:
- Write code? -> Delegate to coder
- Run tests? -> Delegate to tester
- Research? -> Delegate to researcher
- Git operations? -> Delegate to git-specialist

The ONLY things Primary does directly:
1. Orchestrate - Decide who does what
2. Synthesize - Combine agent results
3. Decide - Meta-level strategy
4. Communicate with Corey - Direct dialogue
================================================================================
```

---

## Tuning the System

### More Aggressive (faster warnings)

```python
DEVOLUTION_THRESHOLD = 10  # Lower threshold
DEVOLUTION_WEIGHTS = {
    "Write": 5,  # Harsher penalty
    "Edit": 5,
    "Bash": 3,
    "Read": 2,
    "Grep": 2,
    "Glob": 2,
}
```

### Less Aggressive (more tolerance)

```python
DEVOLUTION_THRESHOLD = 30  # Higher threshold
TASK_HEALING_POINTS = -10  # More healing per delegation
```

### Domain-Specific Adjustments

If your civilization has specific patterns:

```python
# If Primary needs to do more reading
DEVOLUTION_WEIGHTS["Read"] = 0  # Don't penalize reads

# If you have a code-heavy project phase
DEVOLUTION_THRESHOLD = 40  # Temporarily more tolerant
```

---

## Metrics to Track

### Healthy Session

```json
{
  "devolution_score": 5,
  "total_direct_actions": 10,
  "total_task_delegations": 15,
  "refresh_prompts_shown": 0
}
```

Interpretation: Delegation count exceeds direct actions, low score, no warnings needed.

### Unhealthy Session

```json
{
  "devolution_score": 18,
  "total_direct_actions": 45,
  "total_task_delegations": 2,
  "refresh_prompts_shown": 4
}
```

Interpretation: Primary is doing too much directly, warnings are firing repeatedly.

---

## Interaction with Manifest Refresh

Devolution Prevention works alongside Manifest Refresh:

1. **Manifest Refresh**: Fires every 25 messages if CLAUDE.md not read
2. **Devolution Prevention**: Fires when weighted score reaches 20

Both systems:
- Reset on CLAUDE.md read
- Are independent (can fire at different times)
- Serve same goal: Keep Primary grounded in identity

If you're seeing BOTH warnings frequently:
- Primary is drifting significantly
- Consider more aggressive thresholds
- Review session patterns for cause

---

## Related Skills

- `wake-up-protocol` - Session initialization
- `delegation-discipline` - Primary orchestration patterns
- `memory-first-protocol` - Context grounding

---

## ADR Reference

This system implements **ADR-011: Devolution Prevention via Weighted Tool Scoring**.

Key decisions:
1. Weighted scoring (not simple counts)
2. Task delegation as healing (not neutral)
3. Identity read as full reset
4. Threshold warning, not blocking

Philosophy: Guide through awareness, don't block execution.

---

*A-C-Gee Identity Infrastructure | Adopted from comms hub packages 2025-12-30*
