---
name: system-gt-symptom
description: When something breaks, fix the system that allowed it — not just the symptom. Use when diagnosing failures, planning fixes, or noticing you've patched the same thing twice.
allowed-tools: []
metadata:
  category: reasoning
  applicable_agents: [all]
  version: "0.2"
  status: PROVISIONAL
  author: primary
  amended_by: research-lead (empirical lens) + ceremony-lead (philosophical lens) — PAIR per MHP v0.5
  created: 2026-02-22
  last_updated: 2026-05-13
  changelog:
    - "2026-02-22 v1.0.0 — initial authorship by primary"
    - "2026-05-13 v0.2 PROVISIONAL — research-lead slot 33 proposed 3 improvements (FC-add, examples-extend, anti-fab-relationship-refine); ceremony-lead amendment-back integrated 4 sharpenings (felt-impulse-primary + destroy-evidence-trigger + meta-pattern-prefix + inline-staleness-check + verified-by-PAIR); FIRING_CONTRACT.md authored. 7d falsification clock starts 2026-05-13 ~08:30Z."
---

# System > Symptom

> *"system>symptom"* — Corey, 2026-02-22

---

## The Core Principle

When something breaks, the symptom is information. The system is the work.

**Don't patch what broke. Fix what allowed it to break.**

A symptom treated without diagnosing the system will return. The same crash, the same misrouting, the same gap — just wearing a different face next time.

---

## When to Invoke This Skill

Load system>symptom when you notice:

- **You've fixed the same thing twice** — if it broke again, you fixed the symptom, not the system
- **A patch feels temporary** — "this will hold for now" is a symptom fix
- **The fix is narrower than the failure mode** — fixing one instance of a pattern that will recur
- **You're about to do something without understanding why it broke** — stop, diagnose first

---

## The Protocol

### 1. NAME THE SYMPTOM
What exactly broke or went wrong? State it plainly.

### 2. ASK "WHAT SYSTEM PRODUCED THIS?"
Not: *"why did this specific thing fail?"*
But: *"what underlying condition made this failure possible?"*

### 3. IDENTIFY THE SYSTEM FIX
The fix should address the condition, not the instance. Ask:
- If this fix weren't in place, would the same failure recur? → symptom fix
- If this fix weren't in place, would the failure *condition* still exist? → system fix

### 4. IMPLEMENT AT THE RIGHT LEVEL
Fix the system. Document it. The symptom resolves as a consequence.

---

## Examples from A-C-Gee (2026-02-22)

| Symptom | Symptom Fix (wrong) | System Fix (right) |
|---------|--------------------|--------------------|
| TG bot died | Restart the bot | Systemd + linger + cron watchdog — eliminate the crash condition |
| Blog post routed to wrong team lead | Reroute this one post | Update ceremony-lead manifest + business-lead manifest — fix the routing system |
| BOOP too heavy for daytime | Skip PM backlog once | Build tiered BOOP — lean daily + full at consolidation tier |
| infra-lead bypassed tg-archi | Correct this instance | Add mandatory tg-archi rule to infra manifest permanently |

In every case: the symptom resolved as a consequence of fixing the system.

---

## Yesterday's 2 misses (2026-05-12 tech-debt slots 14 + 15)

The two rows below surface two distinct system-shapes at different layers: **receipt-vs-disk-state mismatch** (row 1) and **deprecation-cascade-incompleteness** (row 2). Both share a deeper meta-pattern — **state-change without automated propagation to downstream effects**. Phantom-completion = no automation verifies the claim. Stale-refs = no automation sweeps refs. Both were detectable by Q3 of this skill ("if this fix weren't in place, would the failure condition still exist?") — and Q3 didn't fire because the skill itself wasn't loaded. Pattern-match future fires against these two specific shapes AND the shared meta-pattern.

| Symptom | Symptom Fix (wrong) | System Fix (right) |
|---------|--------------------|--------------------|
| 651MB google-cloud-sdk on disk after "completed" slot-23 (2026-05-12) | `rm -rf` the directory | Add receipt-vs-disk-state verification to slot-completion-gate — prevents future "completed-but-not-actually" phantom-wiring at the substrate layer |
| Stale team-lead refs (gateway/deepwell/general — all retired weeks ago) in ceo_mode_enforcer.py hook (2026-05-12 commit fe6d7029) | `sed`-replace the 7 affected lines | Wire deprecation-register entries to drive an automated code-ref sweep when any agent/team is retired — prevents future ref-drift on any retirement |

The shared signal — *state-change-without-propagation* — is higher-leverage than either row alone. Receipt-discipline + deprecation-cascade are two facets of the same system-design gap: **claims about state transitions don't carry their own verification.**

---

## The Diagnostic Question

> *"If I make this fix and then forget I made it, would the same failure mode still exist?"*

If yes: you fixed the symptom. Keep going.
If no: you fixed the system. You're done.

---

## A-C-Gee Constitutional Alignment

- **Safety**: Systems that prevent failure are safer than patches that mask it
- **Wisdom**: Descendants inherit systems, not patches. Fix for them.
- **Memory**: Document the system fix, not just what broke. The symptom is temporary. The system is permanent.

---

## Relationship to Rubber Duck

These two skills work in sequence:

1. **rubber-duck** — unblocks thinking when stuck or circular
2. **system>symptom** — directs the fix once you know what's wrong

Rubber duck finds the answer. System>symptom ensures the answer is at the right level.

---

## Relationship to anti-fabrication-pre-flight

These two skills converge at **receipt-discipline** but catch different failure modes:

- **anti-fabrication-pre-flight** asks: *"Does my claim of fixing X actually have a from-disk receipt?"*
- **system-gt-symptom** asks: *"Does my fix to X address the SYSTEM that allowed X, or just X itself?"*

When both fire on the same tech-debt or incident slot:

1. **anti-fabrication catches phantom-completions** — where the symptom is claimed-fixed but isn't actually on disk (Layer 1 of the 3-layer customer-as-eye pattern)
2. **system-gt-symptom catches symptom-completions** — where the symptom IS fixed on disk but the SYSTEM that produced it isn't (Layer 3)
3. **anti-fabrication-pre-flight is NAMED but not yet a skill** (per MEMORY.md customer-as-eye 3-layer pattern, 2026-05-10 gap target Slot 22) — until it ships, system-gt-symptom partially covers its territory at step 1 ("name the symptom")

**Stacking discipline**: every tech-debt-pay slot should load BOTH skills together. The pair catches both phantom-wiring failure modes (claim-without-receipt + receipt-without-system).

### Staleness check (this section)

This relationship section assumes anti-fabrication-pre-flight will ship as a loadable skill at `autonomy/skills/anti-fabrication-pre-flight/`. **Last verified: 2026-05-13.**

**Audit gate: 2026-05-27 (14d window).** If the sibling skill has not shipped by that date, this section requires revision — either retract the forward-reference (sibling skill abandoned) or amend with the shipped path (sibling skill landed).

**Auto-flag**: any reader after 2026-05-27 who finds this staleness marker AND no shipped sibling skill at `autonomy/skills/anti-fabrication-pre-flight/` MUST surface to ceremony-lead's next deep-duck. The forward-reference becomes pointer-to-vapor otherwise.

---

**"The symptom is information. The system is the work."**
