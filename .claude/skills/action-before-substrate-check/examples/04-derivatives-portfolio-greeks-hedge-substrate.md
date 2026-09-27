# Example 4 — trading-strategist about to compute portfolio Greeks and propose a hedge

**Scenario**: It's 2026-05-16 ~14:20Z. trading-strategist has a queued task from Primary: "Compute net Greeks for SOL treasury and propose a delta-hedge ratio for today's rebalancing." The strategist loads `black-scholes-pricer` and `sol-options-pricing-engine`, fetches the position ledger, and is about to price the open covered-call leg and compute the hedge.

**Substrate the action depends on**: the market data used to price the open leg is fresh (not stale from an API failure hours ago), the position ledger reflects the actual current exposure (not a pre-weekend state before a spot move), and the hedge instrument (SOL perp or spot) is still available and liquid.

---

## Without the skill (what could happen)

```
trading-strategist: "Computing net Greeks for SOL treasury."
[fetches position ledger from memories/agents/trading-strategist/positions.json]
[ledger shows 1,000 SOL + 10 short 30-DTE ATM calls from 2026-05-13]
[prices the calls using BSM with sigma = 0.78, S = $142.30]
[computes net delta = 1,000 - (10 × 100 × 0.52) = 480 delta-long]
[proposes hedge: short 480 SOL-perp to bring delta to neutral]
[sends hedge proposal to Primary]
```

Result: the computation committed on assumed substrate. The position ledger was from 2026-05-13; a new covered-call leg was opened on 2026-05-14 but the ledger wasn't updated. The spot price was from a Jupiter API response cached at 06:00Z; the actual spot at 14:20Z is $148.50 after a rally. The sigma was from a pre-rally vol regime. The hedge proposal is sized for a 480-long delta that is actually closer to 200-long if repriced with current spot — the strategist is about to over-hedge by ~140%.

---

## With the skill

### Step 1 — NAME THE ACTION

`Price the open covered-call leg using current spot and vol, compute net delta from position ledger, propose a SOL-perp hedge ratio that brings treasury delta to target (default 0.10 long).`

### Step 2 — LIST ITS SUBSTRATE DEPENDENCIES

```
DEPENDENCY: position ledger reflects all open legs as of this computation = TRUE
DEPENDENCY: spot price is fresh (<15 min old, from live API, not cached/stale) = TRUE
DEPENDENCY: implied-vol proxy is current-regime-appropriate (not from pre-race stale calc) = TRUE
DEPENDENCY: SOL perpetual futures market is liquid (bid-ask spread <0.5%) = TRUE
DEPENDENCY: hedge instrument (SOL perp) is reachable from the civ's trading interface = TRUE
```

### Step 3 — VERIFY EACH

```bash
# (a) Filesystem state — position ledger freshness
cat memories/agents/trading-strategist/positions.json | jq '.last_updated'
# 2026-05-13T18:00:00Z   ← DRIFT — 20 hours stale, missing 2026-05-14 new leg

grep -E "2026-05-14|covered_call|protective_put" memories/agents/trading-strategist/pricing-log.jsonl | tail -5
# 2026-05-14T05:00:00Z SOL-30DTE-148.50-C covered_call qty=5   ← DRIFT — 5 new calls
#   opened since last ledger update

# (b) External-system state — spot price freshness
curl -s "https://api.jup.ag/price/v2?ids=So11111111111111111111111111111111111111112" | jq '.data[].price'
# 148.50
# Check API response timestamp vs current time
# Response-Date header: 2026-05-16T14:19:32Z   ← VERIFIED ✓ (fresh, <2 min)

# (c) External-system state — vol regime
python3 -c "import json; print(json.load(open('memories/agents/trading-strategist/vol-regime.json'))['current_regime'])"
# "HIGH"   ← VERIFIED ✓ (regime updated 14:00Z from Pyth)
# sigma proxy should use HIGH-regime heuristic (realized×1.5, not ×1.2)

# (d) External-system state — SOL perp liquidity
curl -s "https://api.binance.com/api/v3/ticker/bookTicker?symbol=SOLUSDT" | jq '{bid: .bidPrice, ask: .askPrice}'
# bid: 148.48, ask: 148.52
# spread = 0.04 / 148.50 = 0.027%   ← VERIFIED ✓ (<0.5%)

# (e) Doctrine-state — hedge instrument availability
grep -l "SOL.perp\|SOLUSDT\|perpetual" .claude/skills/solana-token-operations/SKILL.md
# Match found   ← VERIFIED ✓ (skill knows how to route to perp)
```

Two dependencies drifted: position ledger is stale (missing 5 new calls from 2026-05-14), and vol regime is HIGH (requires ×1.5 proxy, not the default ×1.2). Spot and perp liquidity verified.

### Step 4 — COMMIT OR AMEND

**Verdict: AMEND-ACTION.** Fix-path 1 (amend the action) and fix-path 2 (amend the substrate):

- **Amend the substrate first**: update position ledger to include 2026-05-14 leg (5 calls, strike $148.50, opened at 05:00Z). Source of truth is `pricing-log.jsonl` entries since last ledger update.
- **Amend the action**: recompute with updated ledger + HIGH-regime sigma (realized-vol 65% × 1.5 = 0.975). New net delta = 1,000 - (15 × 100 × 0.48) = 280 delta-long. Hedge proposal: short 180 SOL-perp (not 480).
- **Abort avoided**: the action is correct-shape once substrate is updated. No need to abort; the drift is data-staleness, not model-failure.

---

## Receipt block written to slot scratchpad

```
ACTION:        Compute net Greeks + propose SOL-perp hedge for treasury rebalancing
DEPENDENCIES:
  - position ledger current = TRUE | DRIFT — stale 20h, missing 5 calls from 2026-05-14
  - spot price fresh = TRUE | VERIFIED ✓ (Jupiter, <2 min)
  - vol regime current = TRUE | DRIFT — ledger assumed MEDIUM, actual HIGH (×1.5 not ×1.2)
  - SOL perp liquid = TRUE | VERIFIED ✓ (spread 0.027%)
  - hedge instrument reachable = TRUE | VERIFIED ✓ (solana-token-operations skill cites perp)
VERDICT:       AMEND-ACTION
REDIRECT:      Updated position ledger from pricing-log.jsonl (5 new calls added). Recomputed
               with HIGH-regime sigma=0.975. Net delta revised from 480-long to 280-long.
               Hedge proposal amended: short 180 SOL-perp (not 480).
```

---

## What the skill caught

- **An over-hedge of ~140%** (480 vs 180 SOL-perp) caused by a stale position ledger missing 5 new covered calls opened the previous day
- **Wrong vol regime** (MEDIUM ×1.2 vs HIGH ×1.5) that would have understated gamma risk and overstated delta stability
- **Silent data-staleness** — the position ledger had no automatic freshness check; the strategist assumed it was current because it was the most-recent file
- **Cross-skill dependency gap** — `sol-options-pricing-engine` auto-logs to `pricing-log.jsonl` but nothing auto-reconciles pricing-log into the position ledger. The substrate (ledger) drifted from its source of truth (pricing-log) without anyone noticing.

**Total time cost of the substrate check**: ~2 minutes (ledger timestamp check + pricing-log grep + API freshness verify + regime file read + perp spread check).
**Total time saved**: ~30-60 minutes of debugging a hedge that was inexplicably losing money as SOL rallied (the over-hedge would have shorted 300 more SOL than needed, turning a delta-neutral position into a delta-short that loses on rallies).

---

## Meta-lesson

This example is the **cross-skill data-staleness** shape: Skill A (`sol-options-pricing-engine`) produces data. Skill B (`trading-strategist`) consumes data. The handoff substrate (position ledger) is not automatically kept in sync with the producer's output stream (pricing-log). The action assumes the handoff substrate is current; it is not.

**The substrate-type at play**: primarily **(b) External-system state** (spot, perp liquidity) and **(a) Filesystem state** (ledger file timestamp, pricing-log as source-of-truth), plus an implicit **(d) Doctrine-state** gap (no skill auto-reconciles pricing-log → ledger; the civ doesn't have a `position-ledger-sync` skill yet).

**The fix-path**: amend the substrate by adding reconciliation logic, or amend the action by making the strategist always grep pricing-log as source-of-truth rather than trusting the ledger file.
