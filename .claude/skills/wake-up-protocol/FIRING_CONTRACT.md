---
name: wake-up-protocol
description: THE official session wake-up protocol. 8 steps + Flight Tests, lean, work-focused. Load context, get
version: 2.3.0
---

# wake-up-protocol Firing Contract

## WHEN

```bash
python3 skills/wake-up-protocol/[script].py [--args]
```

## WHAT

1. **Input**: description from frontmatter
2. **Process**: standard skill execution flow
3. **Output**: skill-specific output

## PRE

| Prerequisite | Verification |
|---|---|
| Skill directory exists | `skills/wake-up-protocol/` present |
| Entry script present | `[script].py` exists |

## POST

| Condition | Output |
|-----------|--------|
| Success | Skill execution completes |
| Failure | Error message returned |

## FAILURE

| Failure | Detection | Recovery |
|---------|-----------|----------|
| Missing entry | FileNotFoundError | Check skill installation |
| Runtime error | Exception raised | Log and report |

## OBSERVABILITY

```
Skill: wake-up-protocol
Version: 2.3.0
Status: ACTIVE
```

