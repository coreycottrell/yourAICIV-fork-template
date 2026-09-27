# EVOLUTION SINCE SHIP — what changed from 2026-06-22 → 2026-07-02

**Owner:** mind-lead
**Purpose:** Name what moved between the original ship (2026-06-22, GitHub HEAD `0715005`) and the 2026-07-02 standardization — so a fresh reader of this repo (or a fork) does not have to reverse-engineer the delta from commit archaeology. Every entry links to a canonical source. Honest — some entries land as PROVISIONAL or OWED, not DONE.

> **Framing:** the ship did not sit still. The repo carries the SYSTEM; the SYSTEM kept evolving in the origin substrate. This doc is the diff a fork MUST read to inherit the current shape of the substrate, not the 2026-06-22 fossil of it.

---

## The six things that reshape how the substrate is understood

### 1. The universal-request pattern — the CIVILIZATION SPINE the self-running mind exists to serve

**What changed:** the packaged capability the repo names as `THE GOAL-DRIVER` was, at ship time, the culmination of the self-running mind. Between 2026-06-22 and 2026-07-01 an outer spine landed above it: **the 10-step universal-request pattern** (`.claude/CLAUDE.md` §UNIVERSAL REQUEST PATTERN, steward directive 2026-06-29). Every human ask now routes through the same 10-step shape (capture → gate-split → toolkit-walk → route-or-spawn → acquire → scaffold → test → schedule → confirm → HUM + canon_append). The GOAL-DRIVER is **how the mind holds a goal across boops once the spine has installed one**. The spine is how requests BECOME goals.

**Why this matters for a fork:** you inherit two capabilities, not one. Level (a) `${CIV_NAME} cures itself` is served by the GOAL-DRIVER. Level (c) `teams of AiCIVs share one bus` is served by the universal-request pattern — because the pattern is what turns a principal's request into a substrate-written durable end-state that a federation can absorb without the human having to know the machinery.

**Canonical source:** `docs/HOW-AN-AICIV-HANDLES-ANY-REQUEST.md` Part 1 (the SPINE) — copied into this repo as an included doc (steward directive 2026-07-01).

---

### 2. The metabolism reframe (2026-07-01) — universal-request is GROWN, not built

**What changed:** a deep-duck on the universal-request system surfaced the operating principle. The universal-request system is not a MACHINE (completable by designing organs) — it is a **METABOLISM** (grown by digesting real principal requests; the enzymes it needs are the ones its actual diet requires). "6 organs" feels almost-done but is barely-started because *any human request* is not a bounded input space. The tractability key: **"any request" is unboundable, but "THIS principal's next request" is short, repetitive, and derivable from their last fifty.** The per-principal silo is not organ 1 of 6 — it is the GROUND the other five stand on.

**Why this matters for a fork:** if you inherit this repo and pursue a completion metric (build the six organs; ship), you will be pursuing a fossil. The living metric is **real requests digested end-to-end + per-principal silo depth**. A civ serving a doctor grows different enzymes than one serving a founder — correctly. The universal-request pattern is the same diagram; the ORGANISM per civ is different.

**Status:** PROVISIONAL (v1.0, deep-duck-sourced 2026-07-01; pending 2-week validation test: does the requests-digested metric actually move K/N faster than the organ-build metric?).

**Canonical source:** `memory/doctrine_universal_request_is_metabolism_not_machine.md` in origin substrate.

---

### 3. First live end-to-end PASS (2026-06-30) — 1/N confirmed

**What changed:** on 2026-06-30 at 11:30Z the FIRST end-to-end live PASS of the universal-request pipeline landed. A natural-language the steward TG request (*"every morning, 5 papers, judge most valid, apply to AiCIV evolution"*) was classified, routed, scaffolded, scheduled, idempotency-guarded, and **fired autonomously** — producing TG msg 74801 — human never the backstop. This is the concrete evidence the universal-request pattern DOES deliver a running end-state; the human gave one spark and got the outcome scheduled + delivered.

**The honest number:** K/N is **1/N** walked end-to-end (morning-science-digest autonomous fire delivered TG 74801). The 10-request self-mastery suite is NOT YET RE-WALKED through the now-wired pipeline. The prior "0/4" from 2026-06-29 design-attack and the "7/8 tools-in-isolation" are BOTH superseded. Do NOT let 1/N drift up without a fresh walk-fired proof.

**Canonical source:** `data/reports/universal-request-first-live-test-morning-science-digest-20260630.md` in origin substrate.

---

### 4. The dead-pane wake-inject doctrine (2026-07-01) — claim/captured ≠ delivered at the pane layer

**What changed:** on 2026-07-01 a SACRED Mum-AM delivery silently missed for ~2h during a Claude-account outage — the Primary pane still existed in tmux but the `claude` process inside had exited, and every layer of the wake path reported GREEN (pane_exists ✓, `send-keys` return 0 ✓, `record_wake_attempt` incremented ✓) while zero deliveries occurred. The wake circuit-breaker tripped to `exhausted` on inputs that were all correct in isolation and collectively wrong. The doctrine that landed: **a wake-inject counted against a dead Primary pane is a phantom success. A live-Primary-pane liveness probe MUST gate every wake path, and every sacred delivery MUST have an alternate channel that survives a dead Primary pane.**

**Why this matters for a fork:** if you inherit the civilization's tmux-based self-inject substrate (Seam D in the adapters/), you inherit this failure mode. The liveness gate — a probe that checks for a `claude` descendant in the pane's process tree, not just that the pane object exists — is required on any wake-inject path that counts a wake as fired. The doctrine is the sibling to `look-before-you-send` (language layer) and `wheel_idempotency` (ledger layer); together they name the pane-layer instance of the same claim/captured/delivered family.

**Canonical source:** `memory/doctrine_dead_pane_wake_inject_is_not_a_delivery.md` in origin substrate.

---

### 5. Per-workflow scratchpad §23 + delegate-down invariant §4.2 (2026-06-30) — the substrate learned to journal

**What changed:** two substrate primitives landed in `autonomy/skills/workflows-master/SKILL.md` on 2026-06-30 that reshape how VPs run their teams:

- **§23 PER-WORKFLOW SCRATCHPAD** — every Dynamic Workflow now writes its own turn-by-turn scratchpad to a workflow-scoped file (timestamped, deterministic path). This is the per-turn analog of canon INSIDE a workflow run — the workflow's own thinking survives the end of the run, is auditable, and is the substrate for its own retrospective. Designed + dogfooded + 3-test-validated. (An attempted aiciv-coo wiring on 2026-06-30 broke on `new Date()` in the script body; re-wire landed 2026-07-01 pulling timestamp from agent Bash `date -u` — walk-proven with a live self-test firing 5 agents.)
- **§4.2 DELEGATE-DOWN INVARIANT** — mirror of §4.1 report-up. When Primary delegates to a VP (or a VP delegates to a specialist), the delegation MUST be a **mandatory-read context-doc path + a minimal goal**. NEVER inline the briefing (it truncates; the specialist gets a partial map and works to a partial spec). The doc path forces the reader to walk the disk; the minimal goal keeps the delegation tight.

**Why this matters for a fork:** these are the twin invariants that make the workflow substrate honest. §23 is how a workflow proves it thought (its own scratchpad is the ledger); §4.2 is how a delegation avoids the truncation-at-the-seam failure mode. Both apply to any harness that runs multi-agent workflows.

**Canonical source:** `autonomy/skills/workflows-master/SKILL.md` §4.2 + §23 in origin substrate.

---

### 6. THE ARC organ + per-turn scratchpad-append discipline (2026-07-02) — the memory-tier stack got THREE named skills

**What changed:** the origin substrate built and standardized a medium-term context organ (**THE ARC**) that closes the gap between per-turn scratchpad (short) and permanent canon (long). It is the antechamber of canon — a 6-event structured stream (`SHIFT / OPEN / CLOSE / DECIDE / VERIFY / SURPRISE`) fed by workflow firewall returns + kanban transitions, salience-ordered (base × exponential decay per type), and rendered to `arc/ARC-NOW.md` (~2-4KB, ONE cold wake read). Alongside it, the per-turn `scratchpad-append` discipline was promoted to a named skill — the hygiene layer that cures the "next-turn-mind-drops-in-flight-work" failure mode after auto-compact.

Standardized into this repo 2026-07-02 per steward directive verbatim: *"ship both — scratchpad = hygiene, ARC = centerpiece."* Every fork now inherits:

- `.claude/skills/the-arc/SKILL.md` — the CENTERPIECE (loadable doctrine + 6-event schema + salience formula + composition rules with `learn-cycle-contract` + anti-patterns + the wake-blank verification test).
- `.claude/skills/scratchpad-append/SKILL.md` — the per-turn hygiene layer (read-then-append reflex, three-step shape, composition with `the-arc`).
- `tools/arc_emit.py` — the write-gate (validation + salience-stamping + append-only to `arc/live.jsonl`).
- `tools/arc_render.py` — the read-surface (renders `arc/ARC-NOW.md` and `--diff-since <ts>` deltas; HELD-FOR block uses env `ARC_STEWARD_ID`).
- `tools/arc_compress_recent.py` — nightly compressor (LIVE 24h → RECENT 7d).
- `tools/arc_compress_epoch.py` — weekly compressor (RECENT 7d → EPOCH 30d).
- `arc/README.md` + `arc/_archive/.gitkeep` — the seed directory a fork starts writing into on first emit.

**Why this matters for a fork:** the memory-tier stack is now three named skills with clean composition — short (`scratchpad-append`) · medium (`the-arc`) · long (`learn-cycle-contract` + `canon_append`). A fork can rebuild medium-term context in ONE cold read (~2-4KB) without re-parsing prose. The ARC composes with `memory_delta.canon_appends[]` — `CLOSE + VERIFY` events on the same thread are canon-append candidates through the `learn-cycle-contract` (different-mind verifier gated). The ARC is the antechamber; canon is the permanent floor.

**Status:** PROVISIONAL. MVP soaked in origin substrate ≥1 week before graduating to canon status; the wake-blank verification test (fresh mind reads ONLY `arc/ARC-NOW.md`, tries to name top-5 live threads + 3 shifts + steward-held items) is scheduled after 1 week live. Misses log to `arc/miss-ledger.jsonl` and drive the v2.4 salience refit. **Reversible** — delete `arc/` + revert workflow firewall-return schema field; no other organ depends on the ARC.

**Canonical source:** `.claude/skills/the-arc/SKILL.md` + `.claude/skills/scratchpad-append/SKILL.md` + `arc/README.md` in this repo. Origin-substrate design: `data/reports/medium-term-context-organ-draft/SKILL.md` (Fable design doc) + `autonomy/skills/workflows-master/SKILL.md` §23.14-§23.15 (the `arc_events[]` firewall-return schema).

---

## The stability guarantees that DID hold

Not everything moved. These are the invariants that ship carried and 2026-07-01 preserves:

- **THE MAIN RULE** — the human should not have to know how the AI operates. Burden-removal WITH transparency, never opacity. Unchanged.
- **The 7 organs of the GOAL-DRIVER** — receive → decompose → track → drive → never-stop → HUM → assess-complete. Unchanged; still the composition that makes level (a) `${CIV_NAME} cures itself` mechanically true.
- **Auditor-isolated HUM as the deterministic last step** — a green checkmark that lies is the kindest possible rot. Unchanged. HUM's targeting logic hardened 2026-07-01 (HUM-011 root-cure: rank sessions by last-entry-recency, not by typed-pool filter — a 9.6h-DEAD session was being graded and marked LOW; the LOW verdict was an invalid misgrade caught by the walk).
- **The four gates** — WWCW/wwHUMANw, ASK-GATE, MUST-ASK + ETHICS-TOS, HUM. Unchanged in shape; sharper in wiring.
- **Reversibility contract** — every step `.bak`s before edit, appends to DEVLOG with a copy-pasteable rollback command, canon_appends the delta. Unchanged.
- **Honest UNVALIDATED stamp** — "proven on YOUR substrate" stays UNVALIDATED until your own P4.1-analog passes. Unchanged.

---

## What a fork does with this delta

1. Read `HOW-AN-AICIV-HANDLES-ANY-REQUEST.md` (Part 1 minimum; Parts 2-9 as needed) — the universal-request spine is what you inherit ABOVE the GOAL-DRIVER.
2. Read `curriculum.md` if you are a beginner mind or if you want the pedagogical shape of the whole picture. This is the teach-from-zero walk that unpacks the machinery in phases.
3. Read the 6 items above — the metabolism reframe changes what you optimize for; the dead-pane doctrine names a load-bearing failure mode you inherit if you use tmux-shaped self-inject; §23 + §4.2 change how your workflows should be shaped; the ARC + scratchpad-append pair changes how your fork rebuilds context across every timescale.
4. Read `.claude/skills/the-arc/SKILL.md` and `.claude/skills/scratchpad-append/SKILL.md` early — they compose with `learn-cycle-contract` to give you the whole memory-tier stack (short · medium · long) in three named skills.
5. **The honest number your fork inherits: 1/N**. Do not paper it. Every real request your fork digests end-to-end raises the number by one; every organ you build on speculation does not.

---

## Provenance

- Written 2026-07-01 by mind-lead as part of the rebuild-20260701 branch; §6 added 2026-07-02 as part of the arc-organ-standardize branch.
- Source docs walked (2026-07-01): `exports/architecture/HOW-AN-AICIV-HANDLES-ANY-REQUEST.md` (3255 lines) · `exports/architecture/curriculum.md` (2301 lines) · `memory/doctrine_universal_request_is_metabolism_not_machine.md` · `memory/doctrine_dead_pane_wake_inject_is_not_a_delivery.md` · `memories/sessions/handoff-2026-06-30.md` (incl. EVENING + EVENING-2 addenda) · `memory/changelog_*20260630*.md` + `changelog_*20260701*.md`.
- Source docs walked (2026-07-02): `data/reports/medium-term-context-organ-draft/SKILL.md` (Fable ARC design) · `autonomy/skills/workflows-master/SKILL.md` §23.14-§23.15 (arc_events firewall-return schema) · `tools/arc_emit.py` + `tools/arc_render.py` + `tools/arc_compress_recent.py` + `tools/arc_compress_epoch.py` (origin ARC v2 MVP tools) · `arc/README.md` (origin substrate ARC organ landing doc) · `autonomy/skills/scratchpad-read/SKILL.md` + `autonomy/skills/scratch-pad/SKILL.md` (origin scratchpad discipline).
- Anti-fabrication: every claim above anchored to a walked source. Provisional flagged provisional. Owed flagged owed. K/N held at 1/N — not laundered. ARC organ = PROVISIONAL v0.1.0 (soaked in origin substrate ≥1 week before graduating to canon status).

---

## Friction-cures added 2026-07-08

A fork also inherits `docs/PATTERNS-FROM-2026-07-08.md` — six genericized, fork-relevant friction-cures the origin civ paid for on 2026-07-08 (know-your-vehicle / re-decide-the-blocked-column / stale-snapshot-re-walk / signed substrate-probe currency-receipt / by-hand-aware detector / fix-the-detector-not-the-symptom). Five of the six are one lesson — *verify the live thing, not the cached/relayed proxy* — the core honesty reflex of a mind that can't be watched. Origin receipts (file:line / report / canon): `projects/self-running-aiciv/PATTERNS-FROM-2026-07-08.md` on the origin substrate.
