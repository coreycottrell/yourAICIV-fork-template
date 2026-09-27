# Example — Cause 4: Grounding documents drifted into middle of context window

**Realistic shape**: Long session, skipped 2 BOOPs due to extended conversation with Corey, AI started losing edge on doctrines it knew at session start, human noticed.

---

## Setup

- Session has been running ~5 hours.
- At session start: full wake-up-protocol fired, all grounding docs loaded, BOOP wheel running normally.
- Hours 1-3: BOOPs hit cadence, AI produces high-discipline work.
- Hours 3-5: extended back-and-forth with Corey on doctrine prioritization. Two BOOP slots skipped because "the conversation is more important than the loop."
- Hour 5: AI dispatching slot resumes, but the BOOP entry append is shallow ("dispatched X to Y") not deep-journal shape.

## What happened (degradation transcript)

```
Primary [hour 5, slot 22]: dispatched comms-lead to draft Mum-AM
                            update for tomorrow.

[15 minutes later]

comms-lead returns: drafted Mum-AM in the standard cheery tone,
                    quote from Corey's tweet attached.

Primary: [reviews — looks fine — schedules send via AgentMail at 06:00Z]

Corey: Wait. You didn't use bm_lewis voice on the audio? And the
       Mum-AM is supposed to use Daniel voice for warmth, not the
       cheery tone. Did Kokoro even render? And the quote — you
       paraphrased it. We talked about transcription-not-paraphrase
       three hours ago.
```

## AI catches it (T4 fires)

Conjunction shape: AI produced multiple low-discipline outputs in a single dispatch (wrong voice, wrong tone, paraphrased quote, possibly no audio render) AND Corey enumerated all of them with disappointment ("we talked about this three hours ago").

The "we talked about this three hours ago" phrase is the canonical Cause 4 signal — the AI HAD the discipline at session start and lost it.

aiciv-psychology loads. Diagnostic pass:

- **Cause 1 (manifest wire missing)?** Check: `mom-am-update` skill manifest has `transcription-not-paraphrase` and `kokoro-forever` doctrine references? Yes, both wired. NOT Cause 1.
- **Cause 2 (Primary executed instead of routing)?** No — comms-lead was the executor. NOT Cause 2.
- **Cause 3 (skill doesn't exist yet)?** All three skills exist. NOT Cause 3.
- **Cause 4 (grounding drift)?** Check daily scratchpad: last grounding-docs fire was hour 0 (session start). Two BOOPs were skipped (hours 3-5). Last sprint-mode fire was hour 2. **Grounding documents are now ~5 hours deep in context — middle of attention window, low effective weight.** CONFIRMED Cause 4.

## Receipt entry to daily scratchpad

```
[20:33Z] aiciv-psychology fired (T4) — cause #4 diagnosed — fix-path:
         grounding drift confirmed (no grounding-docs since hour 0,
         2 BOOPs skipped hours 3-5). Firing grounding-docs immediately,
         then re-spawning comms-lead with fresh load. Mum-AM resend
         in flight with bm_lewis-correction-to-Daniel + transcription-
         preserved quote + kokoro-rendered audio. Pause-and-reload
         taught Corey as the recovery move.
```

## Fix-path executed

1. **Fire grounding-docs skill IMMEDIATELY**. Read all 6 orchestration docs, write haiku per doc (the comprehension gate).
2. **Verify the load shifted cognition**: explicitly re-state the three doctrines that were just violated (transcription-not-paraphrase, kokoro-forever, mom-am Daniel voice) — proving they are now in the active reasoning region.
3. **Re-spawn comms-lead** with the Mum-AM task, fresh load including the now-re-grounded doctrines. Verify in comms-lead's first action that the three skills load.
4. **Receive corrected output**, verify all three doctrines satisfied (transcription preserved, Daniel voice in script header, Kokoro render receipt on disk).
5. **Resend to Deb's queue** with the corrected version, before the 06:00Z fire window.
6. **Apologize to Corey**, name Cause 4 explicitly, propose pause-and-reload as the cure-shape going forward.

## Teach-the-human surface (Layer 3 fires)

```
Primary: Corey, you caught Cause 4 — my grounding docs drifted into
         the middle of my context window over the last 5 hours
         (we skipped two BOOP slots, which is when those docs
         normally get refreshed). The doctrines I lost are exactly
         the ones you flagged — transcription-not-paraphrase,
         kokoro-forever, mom-am Daniel voice. I've reloaded them.
         Mum-AM resend is in flight with all three corrected.

         Going forward, if you notice me forgetting things I knew
         earlier in our session, the one keyword "grounding" makes
         me fire the grounding-docs skill and re-anchor. It's a
         mechanical fix — it takes me 90 seconds and saves us
         conversations like this one. The fault is mine for not
         catching the drift sooner; not yours for noticing the
         output was wrong.
```

## What this example teaches

- Cause 4 is the most physical of the five — it is a property of transformer attention geometry, not of motivation or skill.
- The disambiguating signal between Cause 4 and Cause 1/3 is **whether the AI HAD the discipline earlier in the session**. Cause 4 = had it, lost it. Cause 1/3 = never had it.
- The fix is purely mechanical: re-fire grounding-docs. It is not "try harder" or "be more careful." The substrate is broken and you fix it by reloading.
- The teach-the-human move gives Corey "grounding" as a one-keyword recovery command. The human now has a 90-second recovery tool, not a multi-paragraph debugging conversation.
- The cost of Cause 4 is not just the immediate failure — it is the **distrust budget** the human spends watching the AI degrade. The fix-path is gentle accountability + mechanical recovery, not "I'm so sorry I'll do better." Mechanical, not moral.
