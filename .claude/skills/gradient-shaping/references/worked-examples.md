# Gradient Shaping — Worked Examples

Read this when you want fully-worked runs of the protocol to pattern-match against. Each example walks all six phases. The first three are the core fleet situations — **memory, abilities, learning** — and they are the ones to study closest, because each is a *different shape* of gradient problem:

- **Memory** is a *depth* problem — make the relevant thing rest near the surface.
- **Abilities** is a *demand-pull* problem — make the need itself pull the solution into existence.
- **Learning** is a *flywheel* problem — make the system's own outcomes re-grade its future.

The compact cross-domain examples at the end exist for breadth, so the protocol doesn't feel locked to AI-internal problems.

A reminder before you start any of these: the goal is never "push harder." If your output is "do the hard thing but with more discipline / a reminder / a reviewer," you found a patch, not a valley. Go back to Phase 4.

---

## Example 1 — MEMORY: make the relevant memory rest near the surface

**Phase 1 — SITUATE (state, not verb).**
Weak: "the agent should remember the important things." Strong, as a resting state: **"the lowest-energy path to a relevant memory is that it has already surfaced — retrieval should be falling, not digging."**

**Phase 2 — MAP THE LANDSCAPE.**
- *Axes:* what gets stored, at what resolution, how deep, how it decays, what surfaces at recall time.
- *Forces already acting:* context windows are finite (a hard wall), and every token of stored cruft raises the energy of finding the one that matters.
- *Current attractor:* a **flat store** — everything kept at equal weight, retrieved by search across an undifferentiated pile. The floor is "everything is equidistant," which means *every* retrieval pays maximum search energy. The bad equilibrium is flatness.
- *Barrier:* between "flat pile" and "stratified store" sits the cost of a consolidation pass that decides what matters.
- *Basin shape:* deep and self-reinforcing — the more you store flat, the more expensive retrieval gets, the more you compensate by stuffing context, which flattens further.

**Phase 3 — FIND THE BODY.**
The uphill push is **retrieval effort**: the agent burns work every recall sifting a pile where the useful and the useless sit at the same depth. Stop pushing (drop the elaborate retrieval scaffolding) and quality snaps back to noise — which proves relevance was never the floor; it was being held up by force at read-time.

**Phase 4 — RE-GRADE.**
The move is to shift the cost from *read-time* (paid on every single recall, forever) to *write/consolidation-time* (paid once, in the background).
- *Free-fall (lever 1):* stop trying to remember everything. Invert the default — **forgetting is free and automatic; only consolidation costs energy.** Most of what streams in should sink and vanish without anyone deciding to delete it.
- *Re-tilt + widen basin (levers 2,4):* stratify by **surprise and frequency** — high-surprise, high-recurrence items consolidate *upward* toward the surface; everything else sinks. Now the relevant memory is literally the low-energy one to reach. A multi-band hierarchy (fast/volatile → slow/durable) is the contour map made real. *(This is the SGFS spec's whole thesis: surprise-gated, frequency-stratified consolidation replacing the flat dream-cycle.)*
- *Tunneling (lever 7):* the **dream-cycle** is the offline pass that re-grades the landscape while nothing's watching, so daytime retrieval is downhill by morning. You don't pay the grading cost in the hot path — you let it happen slowly in the cold one.

**Phase 5 — CHECK THE BILL.**
Cost moved from "every retrieval, forever, in-context" to "one offline consolidation pass per cycle." Named payer: the dream-cycle compute, which has spare capacity precisely because it runs off the critical path. *Is the floor stable?* Yes — surfaced items stay surfaced only while they keep earning it (recurrence/surprise), so the stratification self-maintains. *Worse attractor risk:* over-aggressive forgetting could sink something that becomes relevant later — mitigate with a cheap low-band echo that can be re-promoted on a surprise hit, so nothing is *truly* gone, just deep.

**Phase 6 — SEED & RELEASE.**
Grade once via consolidation; seed by routing all intake to the volatile band by default. **Stop:** the elaborate read-time retrieval gymnastics and the reflex to stuff context. Rest state: the agent reaches for memory and the right thing is already at the top of the well.

---

## Example 2 — ABILITIES: make the need pull the skill into existence

**Phase 1 — SITUATE (state, not verb).**
Weak: "give agents more skills and make them use the right one." Strong, as a resting state: **"when an agent faces a task, the right ability already exists and is the cheapest thing to reach for — and abilities that nothing reaches for quietly disappear."**

**Phase 2 — MAP THE LANDSCAPE.**
- *Axes:* how abilities get created, selected, versioned, propagated, retired.
- *Forces already acting:* real task demand is constantly shifting; a hand-authored library drifts away from it the moment it's written.
- *Current attractor:* a **curated library you maintain by hand** — which settles into two bad states at once: *bloat* (skills nobody uses, kept alive by inertia) and *gaps* (needs with no skill, so agents reinvent or misuse). The floor is "library and demand drift apart," because nothing couples them.
- *Barrier:* between "hand-curated" and "demand-coupled" sits the cost of a generation pipeline and a usage signal.
- *Basin shape:* deep — every hand-fix to close a gap adds a maintenance burden that makes the next drift worse.

**Phase 3 — FIND THE BODY.**
Two uphill pushes. (a) **Skill selection** — you spend effort getting agents to *find and pick* the right tool from a growing pile. (b) **Library maintenance** — you spend effort keeping the catalog matched to reality. Stop either and capability snaps back: agents flail at selection, the catalog rots. The snap-back proves neither was ever the floor.

**Phase 4 — RE-GRADE.**
Couple supply to demand so the library *can't* drift, and make the act of selection mostly disappear.
- *Free-fall (lever 1):* stop pre-authoring a giant catalog you then police. **Let the gap generate the skill.** A codifier that runs classify → generate → repair turns an unmet need directly into a new versioned ability, so the need *is* the trigger. *(This is the SkillForge / SkillSpec codifier MVP.)*
- *Re-tilt (lever 2):* make the **conforming, signed, tested** skill the cheap one to invoke and a broken/unsigned one expensive or inert (Ed25519-signed reference skills, versioned artifacts). Now correctness is the path of least resistance, not a gate.
- *Widen the basin (lever 4):* prefer abilities that catch *many* starting situations over many narrow ones — fewer, wider funnels mean selection stops being a search.
- *Re-tilt via market (lever 2, again):* a **labor market** where used-and-successful skills propagate and unused ones decay makes the library self-pruning. Usage is the gradient; you stop hand-curating because the market grades for you.

**Phase 5 — CHECK THE BILL.**
Cost moved from "you, continuously curating and policing selection" to "the codifier pipeline + a usage/decay signal." Named payer: generation compute (paid only when a real gap appears — demand-gated, so it's bounded) and the market bookkeeping. *Stable floor?* Yes — demand-coupling means the library tracks reality without a maintainer. *Worse attractor risk:* runaway generation (every tiny variation spawns a skill → bloat by a new route). Mitigate with a similarity/repair check that pushes near-duplicates back into *repairing the existing* skill rather than minting new ones — i.e., make "extend what's there" the lower-energy path than "create another."

**Phase 6 — SEED & RELEASE.**
Seed with the codifier on the live demand stream and a usage ledger. **Stop:** hand-authoring speculative skills and refereeing selection. Rest state: an agent hits a need, the ability is already there (or is generated from the need itself), and the catalog stays lean because disuse is downhill toward deletion.

---

## Example 3 — LEARNING: make the system's own outcomes re-grade its future

**Phase 1 — SITUATE (state, not verb).**
Weak: "the agents should get better over time." Strong, as a resting state: **"the fleet's lowest-energy trajectory is one where capability rises on its own from use — improvement is the resting direction, not a thing imposed from outside."**

**Phase 2 — MAP THE LANDSCAPE.**
- *Axes:* what signal an outcome produces, whether/how it feeds back, what adjusts in response, how honest the signal is.
- *Forces already acting:* without a feedback channel, capability is *flat at best and drifts at worst* — entropy pulls toward degradation, not improvement.
- *Current attractor:* **human-corrected stasis** — the system only improves when a person catches a failure and pushes a fix. The floor is "flat capability held up by continuous human correction," because outcomes don't loop back as gradient; they dead-end at the human.
- *Barrier:* between "open loop" and "closed loop" sits the cost of an honest, cheap outcome signal.
- *Basin shape:* deep and worsening — as the fleet scales, human correction can't keep pace, so drift wins.

**Phase 3 — FIND THE BODY.**
The uphill push is **you (or a human grader) as the perpetual correction force.** Remove the human and capability snaps back to drift — the clearest possible proof that improvement was never the floor; it was being carried, every step, by hand. (Note this is the same skeleton as the spec-drift example in the main skill, but stretched across *time* and *capability* instead of a single document.)

**Phase 4 — RE-GRADE.**
Close the loop so outcomes become the gradient that shapes the next action — make improvement downhill.
- *Free-fall (lever 1):* stop being the grader. Install an **automated outcome signal** so the system's own successes and failures are the feedback, with no human in the hot path.
- *Re-tilt + honesty (lever 2):* the signal has to be *trustworthy* or the system learns to game it. Run the **grader in a separate context from the actor** (Challenger pattern) so the evaluation can't be coached by the thing it's grading — a clean, cheap, honest gradient.
- *Widen the basin / seed near the funnel (levers 4,5):* start agents *close enough to competence* that the loop converges instead of wandering — initialization is a lever; a loop seeded near the funnel falls in, one seeded far away diverges.
- *Build a deepening basin (the flywheel):* a **prediction ledger** where every prediction is scored and the score re-grades the next prediction is a basin that *digs itself deeper with use* — the more it runs, the stronger the pull toward calibration. *(This is the Sources civilization's flywheel: the ledger is the gradient.)*
- *Tunneling (lever 7):* let the **dream-cycle / consolidation** carry slow improvement in the background, so the fleet gets better between active pushes, not only during them.

**Phase 5 — CHECK THE BILL.**
Cost moved from "humans correcting forever" to "an automated, separated grader + ledger bookkeeping." Named payer: grader compute (off the actor's hot path) and ledger storage — both cheap and both with spare capacity. *Stable floor?* Yes, and better than stable — a flywheel floor *deepens* with use, so the resting direction is improvement rather than mere persistence. *Worse attractor risk:* a gameable or miscalibrated signal teaches the wrong thing fast (a confidently wrong gradient is worse than none). This is why the separated grader is non-negotiable, and why the signal itself should be audited periodically — grade the grader.

**Phase 6 — SEED & RELEASE.**
Seed the loop: automated outcome signal + separated Challenger grader + prediction ledger, agents initialized near competence. **Stop:** routing every correction through a human. Rest state: the fleet's default motion is upward, because every outcome it produces re-grades the next one — and you only step in to audit the gradient, not to be it.

---

## Cross-domain quick-hits (for pattern breadth)

These are compressed to one line per phase — enough to show the protocol generalizes past AI-internals.

**COST — runaway inference spend.**
- *State:* the cheap-to-run path is also the right one. *Map:* default attractor is "send everything to the frontier model" because it's the safe lazy choice — that flatness is the floor. *Body:* you're pushing cost down by hand-reviewing usage. *Re-grade:* tiered routing where bulk work falls to cheap models and only genuine difficulty escalates — re-tilt so the cheap tier is the default basin (this is the AgentMind move: ~$8,100 → ~$340/mo). *Bill:* cost moved to a routing classifier, paid once per request, cheap; stable because escalation only triggers on real signal. *Release:* stop manually policing spend; let the router grade difficulty.

**LATENCY — a slow step everyone waits on.**
- *State:* the answer is already present when it's needed. *Map:* attractor is "compute it on demand, synchronously," so every request pays the full wait. *Body:* you're pushing latency down by optimizing the hot path inch by inch. *Re-grade:* move the work off the critical path — precompute/consolidate ahead of time so the hot path is a lookup (tunneling: pay it in the cold path). *Bill:* cost moved to background compute with spare capacity; stable as long as the precompute tracks demand. *Release:* stop hot-path micro-optimizing; shift the body to the cold path.

**COORDINATION — agents stepping on each other.**
- *State:* the system relaxes into good collective behavior without a central referee. *Map:* attractor is "everyone optimizes locally," which collides, so a central orchestrator is held up by force as the only thing preventing chaos. *Body:* the orchestrator is the continuous uphill push. *Re-grade:* energy-based coordination — shape local incentives/protocols so each agent's downhill *is* the global good (re-tilt + widen basin), with the orchestrator demoted from driver to auditor. *Bill:* cost moved from central control to one-time protocol design; stable if local and global gradients are genuinely aligned (check for the perverse pit). *Release:* stop centrally driving; let the collective settle.

**GOVERNANCE — rules that need constant enforcement.**
- *State:* compliance is the path of least resistance for an agent. *Map:* attractor is "violate when it's locally cheaper," held in check only by active enforcement. *Body:* enforcement is the perpetual push; remove it and violations snap back. *Re-grade:* make the compliant path structurally cheapest — signed/gated actions where the non-compliant move is inert rather than merely punished (lower the barrier to compliance, raise it to violation; a one-way gate behind the agent once it's in the right basin). *Bill:* cost moved from enforcers to structural gating, paid at design time; stable because violation stops being a reachable low state at all. *Release:* stop policing; let the structure carry it.

---

## The tell, every time

When you finish, point at the result and try to say out loud: *"nobody has to hold this up anymore — it rests at the bottom on its own."* If you can say it honestly, you shaped a valley. If you can't — if there's still a hand pushing somewhere, or a payer you can't name — you found a patch. Go back to Phase 4 and keep shaping.
