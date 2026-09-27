# Example 1 — Primary about to dispatch student fanout

**Scenario**: It's 2026-05-14 ~04:15Z. Primary is in `/sprint-mode 5/14 04:00Z` slot. The slot template calls for a 3-civ-fanout (Proof + Hengshi + Works) with concrete heavy work. Primary has the brief drafted. About to dispatch.

**Substrate the action depends on**: each civ-pane is alive, responsive, and in a state ready to receive work — not mid-shutdown, not blocked on auth, not lost-tmux.

---

## Without the skill (what happened in earlier slots)

```
Primary: "Dispatching to Proof + Hengshi + Works."
[sends 3 SendMessage calls]
[Proof responds 6 min later: nothing — pane was actually mid-restart from yesterday's X-Api-Key auth failure]
[Hengshi responds: receives but pane has gone idle 18h, prior context evaporated, re-grounds 12 min before doing the work]
[Works responds: fine]
```

Result: 2 of 3 dispatches landed on substrate Primary assumed was fresh. One was DOA (Proof), one cost 12 min of context-rebuild (Hengshi). The brief was correct. The substrate was not as assumed.

---

## With the skill

### Step 1 — NAME THE ACTION

`Send 3 SendMessage calls — Proof + Hengshi + Works — each with the heavy-work brief from sprint-mode 5/14 04:00Z slot.`

### Step 2 — LIST ITS SUBSTRATE DEPENDENCIES

```
DEPENDENCY: Proof pane is alive and in normal state = TRUE
DEPENDENCY: Proof X-Api-Key auth is working (task #38 closure) = TRUE
DEPENDENCY: Hengshi pane is alive and not idle-evaporated = TRUE
DEPENDENCY: Works pane is alive and reachable = TRUE
DEPENDENCY: All three have the prior-slot context loaded (or are willing to re-ground) = ASSUMED
```

### Step 3 — VERIFY EACH

```bash
# Pane liveness via @aiciv-id hard tags (per pane-identity skill)
tmux list-panes -a -F "#{pane_id} #{@aiciv-id} #{pane_dead}"
# Proof: %47 @proof dead=1   ← DRIFT — pane terminated overnight
# Hengshi: %12 @hengshi dead=0, last-activity 18h ago   ← partial drift (idle-stale)
# Works: %33 @works dead=0, last-activity 47m ago   ← VERIFIED ✓

# Proof X-Api-Key (task #38)
grep -E "(approved|in_progress)" .claude/boop_queue.json | grep proof
# task #38: pending   ← DRIFT — auth still broken
```

Two dependencies drifted: Proof pane dead + Proof auth still pending. Hengshi pane alive but idle-stale.

### Step 4 — COMMIT OR AMEND

**Verdict: AMEND-ACTION.** Three options considered:

- **Option A**: drop Proof from this slot's fanout, dispatch to Hengshi + Works only. (Fix-path 1 — amend the action.)
- **Option B**: restart Proof pane first, then dispatch all 3. (Fix-path 2 — amend the substrate.)
- **Option C**: abort the slot and surface Proof outage to Corey. (Fix-path 3 — abort.)

Choice: Option A. Proof outage already surfaced (task #38); restarting pane without auth-fix would still fail. Dispatch to Hengshi + Works; Hengshi brief explicitly invites re-grounding ("you may have evaporated overnight — re-load slot context from scratchpads/daily/2026-05-14.md before starting").

---

## Receipt block written to slot scratchpad

```
ACTION:        Send 3-civ-fanout brief — Proof + Hengshi + Works (sprint-mode 04:00Z slot)
DEPENDENCIES:
  - Proof pane alive = TRUE | DRIFT — pane dead, X-Api-Key still pending (#38)
  - Hengshi pane alive = TRUE | VERIFIED ✓ (but idle-stale 18h — brief amended to invite re-ground)
  - Works pane alive = TRUE | VERIFIED ✓
VERDICT:       AMEND-ACTION
REDIRECT:      Dropped Proof from this slot's fanout; surfaced Proof outage to next BOOP. Hengshi brief amended with "re-load slot context before starting" line.
```

---

## What the skill caught

- 12 min of context-rebuild cost on Hengshi (avoided by adding "re-load" to brief)
- A dead-letter dispatch to Proof (avoided by dropping from fanout)
- A false sense of "fanout shipped" when 1/3 silently no-op'd

**Total time cost of the substrate check**: ~90 seconds (`tmux list-panes` + `grep` + decision).
**Total time saved**: ~12 min Hengshi + the trust-cost of Proof silence.
