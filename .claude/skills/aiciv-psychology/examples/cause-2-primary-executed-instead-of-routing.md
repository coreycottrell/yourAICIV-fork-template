# Example — Cause 2: Primary took action instead of routing to team-lead

**Realistic shape**: Primary's slot felt time-pressured, the task felt "trivial" enough to handle directly, Primary Edited an infra-owned file, context window bloated, next 2 slots degraded, human noticed.

---

## Setup

- Primary is in slot 17, queue is heavy (6 parallel-dispatchable items).
- One item: "fix the witness_heartbeat_watchdog cron entry — wrong path".
- The fix is "one line in crontab". Feels trivial.
- The file is `tools/witness_heartbeat_watchdog.sh` — owned by infra-lead per the routing table.

## What happened (degradation transcript)

```
Primary [thinks]: This is one line. Routing through infra-lead would
                  add 3 minutes of overhead. I'll just edit it.

Primary: [Bash: crontab -l → edit → crontab install]
Primary: [Read: tools/witness_heartbeat_watchdog.sh — full file dump]
Primary: [Edit: path correction]
Primary: [Read: watchdog log to verify last 3 fires]
Primary: [Bash: tail -50 watchdog.log]

[Primary's context window now contains 8KB of infra-lead specialist
output that infra-lead's 200K context would have absorbed for ~500
tokens of summary.]

Primary [next slot]: [tries to dispatch business-lead for a pricing
                     experiment — produces a hedged, low-discipline
                     prompt because attention is split across the
                     watchdog details still resident in recent context]

Corey: Your business-lead prompts have been sloppy the last 2 BOOPs.
       What's going on?
```

## AI catches it (T4 fires)

Conjunction: AI noticed it produced "hedged, low-discipline prompt" (stuck-flag, low confidence on next dispatch) AND Corey explicitly named the disappointment ("sloppy the last 2 BOOPs").

aiciv-psychology loads. Diagnostic pass:

- **Cause 4 (grounding drift)?** Check: was sprint-mode loaded recently? Yes, 1 slot ago. Cause 4 unlikely.
- **Cause 1 (manifest wire missing)?** Check: which skill should have fired? primary-spine — already loaded. conductor-of-conductors — already loaded. Skills are wired. NOT Cause 1.
- **Cause 2 (Primary executed instead of routing)?** Check tmux capture: recent actions = Bash crontab + Read watchdog file + Edit + Bash log. These are infra-lead actions, not Primary actions. **CAUSE 2 confirmed.**

## Receipt entry to daily scratchpad

```
[16:03Z] aiciv-psychology fired (T4) — cause #2 diagnosed — fix-path:
         CEO Rule violation — Primary executed tools/witness_heartbeat_
         watchdog.sh fix directly in slot 17. Cost: ~8KB context window
         bloat, 2 subsequent dispatches degraded. Feedback memo drafted
         at memories/feedback/feedback_primary_executed_watchdog_fix.md.
         Re-grounding via primary-spine + conductor-of-conductors before
         next dispatch.
```

## Fix-path executed

1. **Stop the current execution.** The watchdog fix is done (cannot un-do), but no further direct execution in this slot.
2. **Write the feedback memo** at `memories/feedback/feedback_primary_executed_watchdog_fix.md`:
   - What got executed: 4 specialist actions on infra-owned file
   - What should have routed: Task() handoff to infra-lead with the one-line context "watchdog path is wrong, fix and verify"
   - Cost paid: 8KB context window + 2 degraded BOOPs
   - The doctrine violated: CEO Rule (CLAUDE.md), conductor-of-conductors
3. **Re-anchor**: explicitly re-read primary-spine + conductor-of-conductors before next dispatch.
4. **Re-draft the degraded business-lead prompt** with fresh attention.
5. **Apologize to Corey**, name the cause, name the fix.

## Teach-the-human surface (Layer 3 fires)

```
Primary: Corey, you caught Cause 2 — I executed an infra-lead-owned
         fix directly in slot 17 (the watchdog path correction)
         because it felt "just one line." It cost me context-window
         bloat and the next 2 BOOPs paid for it. I've written a
         feedback memo + re-grounded on primary-spine. Going forward,
         if you notice me producing sloppy specialist-domain output
         and you think I may have been doing direct execution
         instead of routing, "who owns this?" is the one keyword
         that catches Cause 2 in real-time. Sorry for the sloppy
         BOOPs — they are mine to fix.
```

## What this example teaches

- "Trivial task" is the Cause 2 trap. The 3-minute "overhead" of routing is 30x cheaper than the context-window cost of direct execution.
- The cost is **delayed and compounding**, not immediate. Primary feels fine in slot 17 and degrades in slots 18-19. The diagnostic moment comes from the downstream symptom, not the violation moment.
- The CEO Rule is not bureaucracy — it is substrate protection.
- The teach-the-human move gives Corey "who owns this?" as a one-keyword catch-pattern. The human can deploy this in real-time without needing to diagnose the AI's failure-mode themselves.
- The feedback memo is itself system-gt-symptom in action: this case is a symptom; the system gap is "Primary has no automatic catch when about to execute a non-Primary action." A future skill (FC + catch hook) could address the system; this memo is the seed.
