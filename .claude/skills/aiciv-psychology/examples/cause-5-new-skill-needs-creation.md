# Example — Cause 5: Skill doesn't exist yet AND needs creation NOW

**Realistic shape**: A novel work-shape with high cost-of-failure appeared, AI judged "this needs a skill before the 3-instance threshold, ship it now," authored SKILL + FC + examples + wired the manifest, cross-graded.

---

## Setup

- Corey introduces a new substrate: 4× daily Kokoro-rendered audio cycle-update to Corey via Telegram (the "corey-cycle-audio" pattern).
- This is instance #1. Pattern is novel.
- BUT: Corey has explicitly said this is a recurring substrate — 00:30/06:30/12:30/18:30 UTC, 6h cadence.
- Cost of next failure (skipped or malformed cadence) = Corey loses the feedback loop he just designed.

## What happened

```
Corey: Render and ship the cycle-update audio at 12:30Z today.
       This is a 4-per-day thing now — 6h cadence, peer-CEO
       content in my voice, Kokoro bm_lewis, 9-10 min,
       Telegram delivery.

Primary [thinks]: This is instance #1. By the 3-instance heuristic
                  I should defer the skill. BUT — Corey has named
                  this as a 4-per-day cadence, which means 28
                  instances in 7 days. The cost of one missed
                  cadence is the substrate itself failing in week 1.
                  This is Cause 5, not Cause 3.

Primary: [renders + sends instance #1 at 12:30Z — symptom addressed]
Primary: [opens aiciv-psychology — fires Cause 5 path]
```

## AI catches the moment (T5 fires — self-aware substrate creation)

This is the rarer Cause 5 firing — the AI catches itself BEFORE the failure, recognizes that an absent skill will cause failure within the week, and decides to ship the skill now. T5 (catch-itself) fires, not T4 (stuck + disappointed).

aiciv-psychology loads. Diagnostic pass:

- **Cause 3 (defer authoring)?** Heuristic says yes (instance #1). Judgment says no (28 instances coming in 7 days).
- **Cause 5 (author NOW)?** Confirmed. Override the heuristic, ship the skill.

## Receipt entry to daily scratchpad

```
[12:35Z] aiciv-psychology fired (T5) — cause #5 diagnosed — fix-path:
         corey-cycle-audio is instance #1 but cadence-locked to 4/day
         x 7d = 28 instances. Cost of misses is substrate-failure
         within week 1. Cause 5 override of N=3 heuristic. Authoring
         SKILL.md + FIRING_CONTRACT.md + examples now, wiring into
         comms-lead manifest + Primary's wake-up-protocol grounding
         list, cross-grade invite to Hengshi (Kokoro IP) + comms-lead
         self-review queued. Per firing-contracts-package canonical
         + PRINCIPLES O8/O22.
```

## Fix-path executed (the full skill-creation discipline)

### 1. Author `autonomy/skills/corey-cycle-audio/SKILL.md`

Per firing-contracts-package canonical, with proper frontmatter:

```yaml
---
name: corey-cycle-audio
description: Render and ship a 9-10 min Kokoro bm_lewis audio cycle-
             update to Corey via Telegram, 4x daily on a 6h cadence
             (00:30/06:30/12:30/18:30 UTC). Peer-CEO content
             authoring stays Primary-direct.
version: 0.1.0
status: PROVISIONAL
authored: 2026-05-07
mandatory_load_for:
  - any Primary BOOP within ±15min of 00:30/06:30/12:30/18:30 UTC
sibling_skills:
  - kokoro-forever (doctrine)
  - transcription-not-paraphrase (doctrine for any Corey quote)
  - telegram (delivery substrate)
firing_contract: ./FIRING_CONTRACT.md
---
```

### 2. Author `autonomy/skills/corey-cycle-audio/FIRING_CONTRACT.md`

Variant B (Operational-Skill, 8 sections per firing-contracts-package Part 2):

- **WHEN this MUST fire**: cron-like — at 00:30/06:30/12:30/18:30 UTC ±15min, fires if Primary BOOP active.
- **Pre-flight checklist**: Kokoro venv reachable, bm_lewis voice present, Telegram bot tokens loaded, ≥7 min script content drafted.
- **Post-action verification**: ledger entry at `data/corey-cycle-audio-ledger.jsonl` showing send-receipt + Telegram message_id.
- **Escalation conditions**: missed cadence (no ledger entry within 30min of window) → ceremony-lead deep-duck audit.
- **Validation receipts**: 7-day rolling 28-entry expectation.
- **Cross-skill firing dependencies**: kokoro-forever doctrine must be in context, transcription-not-paraphrase if quoting Corey.
- **Wired-into**: comms-lead manifest mandatory_load_for, Primary wake-up-protocol cadence-skills list.
- **Iteration**: 7-day audit by ceremony-lead, conversational-first rule added if user feedback indicates report-shape > peer-CEO-shape.

### 3. Author `autonomy/skills/corey-cycle-audio/examples/`

- `examples/good-12-30-instance.md` — instance #1 (today) transcript with what went well.
- `examples/bad-paraphrase-corey-quote.md` — hypothetical failure mode (paraphrasing Corey's words instead of verbatim).

### 4. Wire into manifests

- `autonomy/team-leads/comms/manifest.md` `mandatory_load_for:` gets `corey-cycle-audio (within ±15min of cadence windows)`.
- `autonomy/skills/wake-up-protocol/SKILL.md` cadence-skill list gets `corey-cycle-audio`.

### 5. Template-bake (if relevant)

- This is ACG-specific (Corey-specific) — NOT a newborn-AiCIV inheritance candidate. Do NOT add to `template-substrate-imports/`. Document why in changelog.

### 6. Cross-grade invite

- Hengshi (Kokoro IP author): "verify Kokoro pipeline wire-shape in FC pre-flight is correct."
- comms-lead self-review next session: "verify FC fires at expected cadence."

### 7. Wake-blank simulation

- Spawn fresh civ-instance at 18:25Z, give it Corey directive "cycle-update soon," verify it loads corey-cycle-audio skill + fires render+send by 18:45Z.

## Teach-the-human surface (Layer 3 fires)

```
Primary: Corey, the cycle-update for 12:30Z is sent (Telegram
         message_id 4221, ledger entry logged). I also authored
         the corey-cycle-audio skill this session — SKILL + FC +
         examples + comms-lead manifest wire + cross-grade invite
         to Hengshi for the Kokoro pipeline verification. This is
         a Cause 5 call: the 4-per-day cadence means 28 instances
         in 7 days, and the cost of any miss is the substrate
         itself failing. Authoring the skill at instance #1 instead
         of waiting for N=3 is the judgment override per the
         firing-contracts canonical (PRINCIPLES O8). If you see
         the pattern not fire at any window, the one keyword
         "cycle-update?" surfaces the gap immediately. Let me
         know if the v0.1.0 shape needs amendment — Hengshi's
         cross-grade will catch the Kokoro side; your eyes on
         the content-shape would catch what they can't.
```

## What this example teaches

- Cause 5 is the **judgment-override of the 3-instance heuristic**. Not all skills should wait for N=3.
- The discipline is: when the cost-of-future-misses is high AND the cadence is named, ship the skill at N=1.
- The firing-contracts-package canonical (Part 2, two variants) is the source of truth for what FC shape to author. Doctrine-skill (Variant A) for skills that protect output classes; Operational-skill (Variant B) for skills that govern recurring actions. corey-cycle-audio is Variant B.
- PRINCIPLES O8 (6-field FC shape) + O22 (persistent code needs README+FC) are non-negotiable for Cause 5 authoring.
- The cross-grade invite is the wake-blank-resistance step — the skill is **PROVISIONAL until ≥1 cross-grade amendment-back lands** even if the FC fires correctly.
- The teach-the-human move names the judgment override explicitly (Corey can verify the call was correct) and gives Corey "cycle-update?" as a one-keyword catch-pattern.
- The template-bake decision is made consciously — not every Cause 5 skill is newborn-AiCIV-relevant. This one is Corey-specific, so no template-bake. The aiciv-psychology skill ITSELF is template-bake-relevant (every newborn AiCIV needs it) — see Deliverable 4 (`projects/aiciv-fork-2.0/template-substrate-imports/aiciv-psychology.md`).
