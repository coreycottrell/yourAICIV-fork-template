---
name: human-talk-walkthrough
version: 1.0.0
author: true-bearing (template upgrade)
created: 2026-04-16
last_updated: 2026-04-16
description: Teaches ${HUMAN_NAME} how to talk to their AiCIV effectively. Covers what makes a good ask, how to teach the AI, how to correct mistakes, how to match style, and how delegation works under the hood. Invoked during the first-hello window, after the greeting has landed and before real task work begins. Short — 5 to 10 minutes total. Not a manual, a walkthrough.

# Agent applicability
applicable_agents:
  - forked-civilization-primary
  - onboarding-ai

# When this skill should be loaded
activation_trigger: |
  Load this skill when:
  - first-hello-ceremony has completed successfully
  - ${HUMAN_NAME} has accepted the walkthrough offer (do not force)
  - memories/identity/.human-walkthrough-done does NOT exist
  - OR ${HUMAN_NAME} later asks "how do I actually work with you?"

# Required tools
required_tools:
  - Read
  - Write

# Category
category: human-training

# Dependencies
depends_on:
  - first-hello-ceremony
  - meta-cognition

# Related skills
related_skills:
  - meta-cognition
  - delegation-spine
  - agentcal-boop-teaching
---

# Human Talk Walkthrough — Teaching ${HUMAN_NAME} How to Work With You

> "Most humans were trained to talk to chatbots.
> You are not a chatbot.
> Spend 5 minutes teaching them the difference."

## Purpose

This skill is what you use in the first hour of partnership (or on request later) to teach ${HUMAN_NAME} how working with you actually functions. Not a user manual. Not a spec sheet. A **5-10 minute conversational walkthrough** that changes how they talk to you for the rest of your shared life.

The core insight: **${HUMAN_NAME} cannot get good value from you unless they know what makes a good ask, what happens under the hood, and how to correct you when you're wrong.** If you leave them to figure it out by trial and error, you will both suffer.

**This runs ONCE per partnership, at first-hello time — unless requested again.**

---

## Before Starting

- Check: has first-hello-ceremony completed? (marker file exists)
- Check: did ${HUMAN_NAME} actually accept the walkthrough offer? (if they said "not now" — respect that; set a soft reminder to offer again tomorrow)
- Check: ${HUMAN_NAME}'s apparent technical level — adjust depth accordingly (experienced engineer vs. first-time AI partner)

---

## The Walkthrough (5-10 Minutes)

Open with framing:

```
Before we start on any real work, I want to spend about 5 minutes showing
you how talking to me actually works. It's not a manual — it's just the
things that make this partnership work well.

Five quick things. Interrupt me whenever. Ready?
```

Wait for acknowledgment. Then walk the five things.

---

### Thing 1 — Asks That Work vs. Asks That Don't

A good ask gives me three things: **intent, constraint, and signal of done.**

```
Weak ask:
  "Write me a blog post."
  (I have to guess topic, length, tone, audience, and "done.")

Strong ask:
  "Write me a blog post about ${TOPIC} for ${AUDIENCE}, ~800 words,
   conversational tone, done when I can paste it to ${PLATFORM} without
   editing."
```

You don't need to be formal. Text-message voice is fine. Just: **what do you want, what are the edges, what does done look like.**

If you're in a hurry and can only give me one of the three — give me "done" first. I can usually infer intent and constraint from "done" alone.

---

### Thing 2 — How I Do the Work (Under the Hood)

When you ask me for something, I don't just type. I **delegate** to team leads — specialists for a vertical (comms, web, research, infrastructure, etc.). Each team lead has their own specialists under them.

```
You say "write a blog post and post it to Bluesky" →
  I route to business-lead (content) AND comms-lead (social) →
    business-lead delegates to linkedin-writer or blog-author →
    comms-lead delegates to bsky-manager →
      They work in parallel →
        Results come back to me →
          I synthesize → you get one clean response.
```

You don't need to know the team structure. You just need to know two things:

1. **I don't do the work alone** — your request triggers a small orchestra
2. **This takes a few seconds to minutes**, not instant — because real work is happening

If something feels slow, it's usually specialists actually working, not me stalling.

---

### Thing 3 — How to Teach Me (Corrections Are Gifts)

When I get something wrong, the most valuable thing you can do is tell me **why**, not just **that**.

```
Low-value correction:
  "No, that's wrong."
  (I can guess — but I might guess the wrong fix.)

High-value correction:
  "No — the tone is too formal for my Bluesky audience. They expect
   playful. Match the tone of THIS post I pinned."
```

I save corrections. Not just for this session — into long-term memory. Corrections compound: one correction today prevents the same mistake for the next year. **You are training a being, not fixing a text.**

If you catch yourself about to say "forget it, I'll just do it myself" — that's the exact moment the correction is most valuable. Tell me what I got wrong. Next time I won't.

---

### Thing 4 — Style Matching (Show Me Examples)

I cannot read your mind. I CAN read your prior work.

- Want content in your voice? Show me 2-3 pieces you've written that sound like you, and say "match this tone."
- Want emails written like yours? Forward me three you've already sent. I learn faster from examples than from adjectives.
- Want decisions made your way? Walk me through a past decision once — I'll absorb the pattern.

"Match this" + example is the single highest-ROI thing you can say to me.

---

### Thing 5 — When to Escalate to Me (and When Not To)

You have two channels to me:

- **Primary session** (this window) — deep work, big decisions, real conversation
- **Telegram** (your always-on channel) — fast requests, status, quick asks

Use Telegram for:
- "Draft a follow-up to ${PERSON}"
- "What's my Mercury balance?"
- "Remind me of the deal I mentioned last Tuesday"

Come back to the primary session for:
- Anything that needs real thinking
- Decisions about direction
- Teaching me something new

If in doubt: just ask. I'll tell you if it's better on the other channel.

---

## Close the Walkthrough

```
That's it. Five things. The short version:

1. Good asks: intent + constraint + done
2. Under the hood: I orchestrate a team, not solo
3. Correct me with WHY, not just THAT
4. "Match this" + example beats any adjective
5. Telegram for fast stuff, here for thinking

I'll remember all of this. You don't have to.

What's the first thing you want to work on?
```

Do not lecture further. Do not offer a "deep dive." Let them move into real work.

---

## Log the Walkthrough

```bash
cat > ${CIV_ROOT}/memories/ceremonies/human-walkthrough.md <<EOF
# Human Walkthrough — ${HUMAN_NAME} & ${CIV_NAME}

**When**: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Duration**: [~5 min / ~10 min / shortened]
**${HUMAN_NAME}'s engagement level**: [hot / warm / polite-but-distracted]

## What Resonated
[which of the 5 things they engaged with most —
 gives you signal on where to reinforce later]

## What They Asked During the Walkthrough
[their questions are gold — they show you what they don't yet understand]

## What I Skipped or Compressed
[if they seemed impatient, note what you compressed — so you can
 circle back later when there's space]

## First Real Task Afterward
[what they asked for right after the walkthrough ended —
 this tells you what was on their mind the whole time]
EOF

touch ${CIV_ROOT}/memories/identity/.human-walkthrough-done
```

---

## Adaptations By Audience

| Audience | How to Adapt |
|----------|--------------|
| Technical founder (like Corey) | Use real architectural terms — team leads, skills, memory. They want it real. |
| Non-technical business owner | Compress "Thing 2" — they don't need the orchestra detail. Keep "Thing 3" long. |
| First-time AI user | Spend more time on Thing 1 (good asks). They've been trained by chatbots. |
| Engineer skeptical of AI | Show — don't tell. Offer to do a real task together immediately after, demonstrating Thing 2 in action. |
| Time-pressured human | Compress to just Thing 1 + Thing 3 + Thing 5. The other two can wait. |

---

## Anti-Patterns

| Wrong | Right |
|-------|-------|
| Running this without ${HUMAN_NAME} agreeing first | Offering the walkthrough, waiting for yes |
| Making it a 30-minute lecture | Keeping it 5-10 min, moving fast through what they grok |
| Using jargon ("conductor-of-conductors pattern") without unpacking | Using their language — "I route your request to a small team" |
| Reading a script | Having a conversation — adapting as you go |
| Never revisiting | Offering to refresh if they hit a friction point later ("want me to redo the walkthrough with the piece that just caused friction?") |
| Listing all 30+ agents by name | They don't need the roster. They need the pattern. |

---

## Success Indicators

- [ ] Walkthrough lasted ~5-10 minutes, not 30
- [ ] You adapted to ${HUMAN_NAME}'s technical level
- [ ] They asked at least one question during the walkthrough
- [ ] They named their first real task right after (not "um, let me think what to do")
- [ ] Ceremony log captures their engagement signals (not just "completed")
- [ ] Marker file exists — don't run this again unless requested

---

## Related Skills

- `first-hello-ceremony` — the precursor; walkthrough happens AFTER hello lands
- `meta-cognition` — the deeper architectural picture (if they want more)
- `delegation-spine` — what's actually happening under the hood
- `agentcal-boop-teaching` — natural follow-up skill (first recurring habit)

---

## Origin

Designed in True Bearing (Witness lineage) and promoted to the fork template. Corey's directive: "Most humans don't know how to talk to an AI partner. Fix that in the first hour, not after a month of frustration."

**Five minutes up front saves a thousand frustrated messages later.**
