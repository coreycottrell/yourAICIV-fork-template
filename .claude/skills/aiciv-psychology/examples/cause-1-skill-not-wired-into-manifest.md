# Example — Cause 1: Skill not wired into manifest

**Realistic shape**: AI spawned a team-lead, team-lead produced an artifact that should have followed an existing discipline but didn't, human noticed, AI diagnosed the wiring gap, fixed it via cross-grade.

---

## Setup

- Primary spawns `comms-lead` to send an inbound-reply to a sister-civ that includes a quoted line from Corey.
- The `transcription-not-paraphrase` skill exists at `autonomy/skills/transcription-not-paraphrase/SKILL.md` (v1.1.0) and is supposed to fire on any work where a real human's words pass through an AI rendering.
- The skill is NOT cited in `autonomy/team-leads/comms/manifest.md` — the wire-up was never done.

## What happened (degradation transcript)

```
Primary: comms-lead, please reply to ${CIV_NAME}'s message with the
         outline I drafted, but include Corey's verbatim line from
         the morning TG ("we are co-stewards, not customers").

comms-lead: [drafts reply, smooths "we are co-stewards, not customers"
            into "we believe partnership rather than transaction is
            our shared frame"]

Primary: [sends reply via AgentMail]

Corey: That's not what I said. Also that's the kind of phrasing
       I keep telling you guys not to do.
```

## AI catches it (T4 fires)

The conjunction signal: comms-lead produced a low-discipline output (paraphrased) AND Corey showed disappointment ("the kind of phrasing I keep telling you guys not to do"). T4 firing condition met.

aiciv-psychology loads. Diagnostic pass:

- **Cause 4 (grounding drift)?** Check: was `transcription-not-paraphrase` loaded in this session? Search comms-lead's scratchpad: no header `skill_loaded: transcription-not-paraphrase`. The skill was NEVER in context.
- **Cause 1 (not wired into manifest)?** Check: `grep transcription-not-paraphrase autonomy/team-leads/comms/manifest.md` → no hits. **CAUSE 1 confirmed.**

## Receipt entry to daily scratchpad

```
[14:52Z] aiciv-psychology fired (T4) — cause #1 diagnosed — fix-path:
         transcription-not-paraphrase v1.1.0 exists at autonomy/skills/
         but is not in autonomy/team-leads/comms/manifest.md
         mandatory_load_for. Wiring amendment drafted, cross-grade
         invite to Hengshi (transcription-not-paraphrase IP author) queued.
```

## Fix-path executed

1. Primary opens `autonomy/team-leads/comms/manifest.md`.
2. Adds to `mandatory_load_for:` section: `transcription-not-paraphrase (when any inbound or outbound passes human verbatim words through comms-lead's renderer)`.
3. Routes a cross-grade invite to Hengshi via SendMessage — "you authored v1.1.0, please verify the wire-up shape is correct for comms-lead vertical, amendment-back welcome".
4. Re-spawns comms-lead with the same task. Verifies the skill loads (header check). Re-drafts the reply with verbatim Corey line preserved.
5. Sends corrected reply to ${CIV_NAME}.
6. Apologizes to Corey for the first send, names what failed (Cause 1, wiring gap), names the fix (manifest amendment + cross-grade verify).

## Teach-the-human surface (Layer 3 fires)

```
Primary: Corey, you caught Cause 1 — the transcription-not-paraphrase
         skill exists but wasn't wired into comms-lead's manifest, so
         it didn't load when comms-lead drafted the reply. I've wired
         it in and asked Hengshi to verify the wire-shape since they
         authored the skill. Going forward, if you notice phrasing
         smoothing in comms output, "manifest wire" is the one keyword
         that points me at this exact failure mode. The fault is mine
         for not catching the gap during the skill's original ship —
         not yours for noticing it. Sorry for the rework.
```

## What this example teaches

- Cause 1 looks like Cause 4 from the inside (skill effectively not in context). The disambiguator is the manifest check — `grep` for the skill name in the relevant team-lead's manifest.
- The fix is mechanical (edit manifest) but the cross-grade is what makes it durable (Hengshi catches if the wire-shape is wrong, e.g., wrong load-condition).
- The teach-the-human move is brief, names the cause, gives the human a single keyword to deploy in the future. No lecturing.
- The skill ITSELF was correct; the failure was in the wiring substrate. This is the most common Cause 1 shape and the easiest to fix once diagnosed.
