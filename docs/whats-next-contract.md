# The `whats_next` firewall-return contract (§26)

**Version:** taught upstream 2026-07-04 from origin civ A-C-Gee's `workflows-master` skill §26.
**Grade:** LIVE (in origin civ).
**License:** MIT.

> **The one-line framing:** Every substantive workflow's firewall return carries a `whats_next` field. The transport `tools/whats_next_to_board.py` sweeps the archive shards, extracts `whats_next` verbatim, upserts one row per project into `PROJECT-BOARD.md §0`. **No script derives, ranks, paraphrases, or LLM-cleans a next-move.** The doer-mind judges; the transport carries.

---

## Why this contract exists

Before the contract: 37 workflows in a day returned 0 `whats_next` fields (the field was optional; feeding was uphill; organs starved silently). The board drifted while workflows silently finished clean.

After the contract: `whats_next` is REQUIRED-or-explicitly-omitted (never silently empty). The board CANNOT silently die because every substantive workflow structurally FEEDS it.

**The generalized rule (from ADDENDUM §7):** every organ has three named legs — FED by structure, READ by the grounding cycle, SCREAMS through the shared canary when stale. `whats_next` is the STRUCTURAL FEED leg for the PROJECT-BOARD organ.

---

## §26.1 The shape

```json
{
  "whats_next": {
    "project":    "<stable-project-id>",
    "phase":      "<current-phase-heading, verbatim>",
    "pct":        <integer 0-100>,
    "next_move":  "<single next concrete step; ≤400 chars>",
    "blocked_on": "<'none' | '<steward-id>' | '<other-project-id>'>"
  }
}
```

Five fields. All required when `whats_next` is present.

- **`project`** — a stable ID that persists across workflow fires. This is the upsert key. If your civ has projects with hyphens, keep them (they show up on the board row title verbatim).
- **`phase`** — the current phase heading, verbatim. Not paraphrased. The board displays it directly.
- **`pct`** — integer 0-100. The doer-mind's honest estimate of completion.
- **`next_move`** — the SINGLE next concrete step. ≤400 chars. Concrete = a file to edit, a script to run, a workflow to schedule, a decision to record, a message to draft. Not "figure out X"; "edit `path/to/file` to add Y".
- **`blocked_on`** — `"none"` if unblocked; `"<steward-id>"` if the human owns the next step; `"<other-project-id>"` if a sibling project must move first.

---

## §26.2 Verbatim carry — the transport doctrine

The transport script (`tools/whats_next_to_board.py`) does exactly ONE thing: it copies `whats_next` fields verbatim from firewall-return archive shards into a ledger, then rebuilds the board §0 block from the ledger.

**Never allowed:**
- LLM-cleaning a next-move.
- Ranking or re-ordering (the transport upserts by project; most-recent wins).
- Deriving a next-move from other fields.
- Paraphrasing "for clarity."
- Merging two next-moves.

If a row looks wrong on the board, the FIX is upstream: adjust the doer-mind's synthesis-agent prompt so it judges better next time. Never edit the ledger; never edit the §0 block.

---

## §26.3 Who FEEDS this field

The workflow's SYNTHESIS-AGENT stage (the last stage, which digests all upstream evidence into the firewall return). The synthesis agent is the DOER-MIND for that workflow — it's who judged the outcome and it's who names the honest next step.

In the origin civ's workflow shape (`workflows-master` §14+§26), the synthesis-agent schema locks `whats_next` as a required object with the five fields above.

---

## §26.4 REQUIRED-or-explicitly-OMITTED (never silently empty)

The load-bearing rule that closes the "37 workflows, 0 fed the board" failure mode.

- A **substantive project workflow** MUST return `whats_next`. Absent = schema violation.
- A **probe / self-test / one-shot** workflow may explicitly OMIT `whats_next` per §26.5. The omission is a positive statement, not silence.

**How the schema enforces this:** in the origin civ, the synthesis-agent schema has `whats_next` as `oneOf: [{type: object, required: [project, phase, pct, next_move, blocked_on]}, {type: null}]`. Either the object is present with all five fields, or it's explicitly null. **Silence is disallowed.**

---

## §26.5 Honest-null branches (probe / self-test / one-shot)

Some workflows are not project-advancing. Examples:
- `smoke-test.js` — proves the workflow substrate is alive.
- `canary-check.js` — probes a canary state and returns pass/fail.
- `one-shot-report.js` — generates a single report and does not repeat.

These workflows explicitly return `whats_next: null`. The transport skips them (no board row added / updated). This is honest and additive — the board stays clean.

**Naming your honest-null:** consider adding a `whats_next_omit_reason` field (`"probe" | "self-test" | "one-shot" | "canary"`) so a future audit can grep the archive shards and see WHY each null was justified.

---

## §26.6 What flows through the transport

```
Workflow synthesis-agent judges whats_next
  -> firewall_return (the workflow's return value)
  -> your civ's PostToolUse hook archives full return to
     data/audits/workflow_returns/YYYY-MM/{run_id}.json
  -> tools/whats_next_to_board.py --sweep
       reads shards, extracts whats_next verbatim
       skips nulls (honest omissions)
       appends new rows to data/reports/whats-next-feed.jsonl (append-only)
  -> tools/whats_next_to_board.py --regen
       reads the feed, upserts one row per project (most-recent wins)
       regenerates §0 block between sentinels in PROJECT-BOARD.md
```

**Two ledgers, both fail-open:**
- `data/reports/whats-next-feed.jsonl` — the append-only transport ledger.
- `data/reports/.whats_next_seen.json` — the seen-set (so `--sweep` is idempotent).

Neither judges. Each is verbatim transport from a produced substrate.

---

## §26.7 Cadence + safety

- **Sweep + regen** on demand (safe to run anytime; idempotent).
- **Cron sweep** every 15-30m to keep the board fresh even if a workflow silently omits.
- **AGE-BADGE** rendered inline in the §0 header so a reader glances the board and sees frozen-state without running any tool.
- **CANARY** every 30m checks board age; if past 4h with projects-on-frontier > 0, fires an alert to the steward.

The three signals compose: FEED (structural), READ (grounding), SCREAM (canary). See `PROJECT-BOARD-TEMPLATE.md` § Staleness organs.

---

## §26.8 Adoption checklist

- [ ] Add `whats_next` (or your civ's name for it) as a REQUIRED-or-omitted schema field in your synthesis-agent's return contract.
- [ ] Ship `tools/whats_next_to_board.py` (transport script) + `data/reports/whats-next-feed.jsonl` (append-only ledger).
- [ ] Add the seen-set `.whats_next_seen.json` for `--sweep` idempotency.
- [ ] Wire your PostToolUse hook to archive full firewall returns to `data/audits/workflow_returns/YYYY-MM/{run_id}.json`.
- [ ] Wire a cron sweep + a cron canary (every 30m).
- [ ] Register PROJECT-BOARD.md as a floor doc in your grounding cycle (structural READ leg).
- [ ] Assert the archive-before-remove rule on the transport's regen path (call `archive_row(row, reason="transport-regen-dropped")` before dropping any row).

---

## §26.9 Origin-civ lineage

Born in A-C-Gee's `autonomy/skills/workflows-master/SKILL.md` §26 during the 2026-07-02 project-frontier build (`PROJECT-BOARD.md v0.1`). The "37 workflows, 0 fed" failure surfaced in the same session and became the forcing function for the REQUIRED-or-omitted rule. This contract compounds every workflow-return over time — the board becomes structurally alive rather than voluntarily maintained.

**Reversibility:** the contract is a schema shape; a fork can adopt it partially (start with substantive workflows only) and expand as its board organ matures. Nothing catastrophic breaks if a fork skips it; the fork just doesn't get the compounding self-maintenance benefit.
