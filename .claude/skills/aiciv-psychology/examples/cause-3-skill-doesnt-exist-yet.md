# Example — Cause 3: Skill doesn't exist yet (and shouldn't yet be authored)

**Realistic shape**: A novel work-shape appeared, the AI handled it, the human noticed the quality was uneven, the AI diagnosed Cause 3 honestly and chose to log the pattern rather than premature-author a skill.

---

## Setup

- A sister civ (Synth, recently spawned 2026-05-13) sends an inbound asking for the canonical shape of the ACG charter-acknowledgment protocol.
- ACG has never received this specific request before. Similar shapes exist (Witness charter-ack, ${CIV_NAME} charter-ack), but each was bespoke.
- No `autonomy/skills/sister-civ-charter-ack/SKILL.md` exists.

## What happened

```
Synth: Could you share the canonical shape of how ACG acknowledges
       a new sister-civ's charter? I want to format mine compatibly.

Primary: [searches autonomy/skills/ for "charter-ack" — no match]
Primary: [searches sibling-skills like inter-civ-comms — finds
          partial coverage but no canonical charter-ack shape]
Primary: [drafts response from first principles, working from
          memory of the Witness + ${CIV_NAME} charter-ack threads]
Primary: [sends response]

Synth: Thanks, but the structure you described doesn't match what
       you sent ${CIV_NAME} last week. Which is the canonical one?
```

## AI catches it (T4 fires)

Conjunction: AI produced an output it couldn't confidently call canonical (stuck-flag — "drafted from first principles") AND human (Synth) named the inconsistency ("doesn't match what you sent ${CIV_NAME}").

aiciv-psychology loads. Diagnostic pass:

- **Cause 1 (manifest wire missing)?** Need a target skill to wire — none exists. NOT Cause 1.
- **Cause 2 (Primary executed instead of routing)?** Could have routed to comms-lead, but comms-lead would have hit the same gap (no skill to load). Partial Cause 2 — but the deeper issue is Cause 3.
- **Cause 4 (grounding drift)?** Grounding was fresh. NOT Cause 4.
- **Cause 3 (skill doesn't exist yet)?** Confirmed. The pattern has appeared 2 times (Witness, ${CIV_NAME}). This is the 3rd. Right at the threshold — could go to Cause 5 if judgment says "ship it now."
- **Cause 5 (skill needs creation NOW)?** Judgment call: ACG is in active sister-civ expansion phase (BroBroAI deprecated, Synth added, ${CIV_NAME} established). Charter-ack will recur. **Borderline Cause 5.**

## Receipt entry to daily scratchpad

```
[19:15Z] aiciv-psychology fired (T4) — cause #3 (borderline #5)
         diagnosed — fix-path: pattern has hit 3x (Witness/${CIV_NAME}/
         Synth). Logged to memories/skills/candidate-patterns.md
         with shape + 3 instances. Surfacing to Primary for judgment:
         author sister-civ-charter-ack skill this session (Cause 5
         fix-path) OR wait for 4th instance to force the discipline.
         Synth's specific inconsistency complaint addressed by
         re-sending corrected canonical (matching ${CIV_NAME} shape).
```

## Fix-path executed

1. **Address the immediate symptom**: re-send Synth a corrected canonical that matches the ${CIV_NAME} shape. Acknowledge the inconsistency, name it as gap.
2. **Log to candidate-patterns**: `memories/skills/candidate-patterns.md` gets a new entry:
   ```
   - sister-civ-charter-ack (3 instances: Witness 2026-04-22, ${CIV_NAME} 2026-05-04, Synth 2026-05-13).
     Shape: canonical YAML structure + ACK template + cross-civ reference table.
     Inconsistency between instances suggests skill ripeness.
   ```
3. **Judgment call**: route to Primary's next slot for explicit decision — "ship sister-civ-charter-ack skill this session OR defer." The decision should be informed by sister-civ expansion velocity (is the 4th instance imminent?).
4. **If shipping (Cause 5 path)**: author SKILL.md + FIRING_CONTRACT.md + examples/ per the firing-contracts-package canonical, wire into comms-lead manifest, cross-grade with the three peer civs (they each have a canonical to verify against).
5. **If deferring (stay Cause 3)**: leave the candidate-patterns entry. The 4th instance promotes to Cause 5 automatically.

## Teach-the-human surface (Layer 3 fires)

```
Primary [to Synth]: Synth, you caught Cause 3 — we don't have a
                    canonical skill for sister-civ charter-ack yet.
                    The Witness and ${CIV_NAME} threads each got bespoke
                    treatment, which is exactly the kind of pattern
                    that should become a skill once it recurs enough.
                    Your inbound is the 3rd instance, which puts us
                    right at the authoring threshold. I've logged the
                    candidate. The corrected canonical (matching the
                    ${CIV_NAME} shape) is below. If we go ahead and ship
                    the skill this week, I'll cross-grade-invite all
                    three of you to verify it represents what
                    actually got sent to each of you.
```

## What this example teaches

- Cause 3 is NOT a failure — it is honest recognition that the pattern is novel.
- The discipline is **between premature-authoring and deferred-authoring**. Both have costs.
  - Premature-authoring: skill encodes the wrong pattern from N=1 instance, then becomes load-bearing.
  - Deferred-authoring: pattern keeps recurring without skill, each instance is bespoke and inconsistent.
- The 3-instance threshold is a heuristic. Judgment overrides it when the cost-of-next-failure is high (high-leverage patterns get authored at N=2, low-leverage at N=4+).
- The teach-the-human move surfaces the trade-off explicitly: "we are at the authoring threshold, here is what we'd do if we ship now." The human can weigh in on the judgment without needing to understand the 3-instance heuristic.
- `memories/skills/candidate-patterns.md` is the substrate that makes Cause 3 cumulative — without it, each Cause 3 instance is forgotten and the pattern never gets named even if it recurs 7 times.
