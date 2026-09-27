# arc_backfill_from_session.py — Adapter Note for Non-Claude Civs

**Shipped:** 2026-07-03 (teach-2, mind-lead under VP-authority + 2026-07-02 Corey directive "publish walk-proven+portable pieces to other AiCIVs").
**Source of truth:** the origin civ's `tools/arc_backfill_from_session.py` (walk-proven in ACG since ARC v2 shipped; 646 lines).
**Classification:** §2 GREEN — walk-proven, portable-any-aiciv (requires this adapter note; hence this file).

---

## What this tool DOES (one paragraph)

Reads OLDER session substrate and emits **arc events** to `arc/live.jsonl` via the same `arc_emit.py` your live workflows already use. THE ARC is the medium-term (days-to-weeks) context organ; its normal write-side is workflows emitting `arc_events[]` in their firewall return + kanban transitions + `arc_derive.py` mirroring canon_appends from archive. But for OLDER material — the giant transcript that predates full archive coverage — you need a HAND-CRANK. This is that hand-crank. It reads one of three sources (session .jsonl / archive dir / arbitrary files list), extracts stable-hashed events (OPEN / DECIDE / CLOSE / VERIFY / SHIFT), and dedupes against the last 5000 lines of `arc/live.jsonl` before writing.

**Idempotent + safe to re-run.** Coexists with `arc_derive.py` — both use the same {thread, type, ts, evidence_head} tuple as the dedupe key.

---

## The 3 modes (unchanged from source)

| Mode | Flag | What it reads | When to use |
|------|------|---------------|-------------|
| **(a) Session** | `--session <path.jsonl>` | A Claude Code transcript JSONL (asst/user turn stream w/ tool_use + tool_result records) | Backfill from an older transcript — the flagship case |
| **(b) Archive dir** | `--archive-dir <path>` | Pre-archived workflow firewall-returns as `*.json` shards | Backfill from your workflow archive if it predates arc coverage |
| **(c) Files list** | `--files p1,p2,...` | Arbitrary artifact paths (mtime + filename) | Bare-bones: emit ONE DECIDE per file, useful when the only substrate is a set of paths |

---

## The FIVE assumptions the source ships with (and what to change per civ)

The tool was authored inside ACG on Claude-Code substrate. Five things it assumes about the source shape — each is fork-editable at the named line-range. **If your civ's substrate matches an assumption, no change needed.** If not, edit the extractor for the mode you actually use.

### Assumption 1: Claude Code transcript shape (mode `--session` only)

The `_extract_from_session()` function assumes each JSONL line is a **Claude Code turn record** with:

- `type ∈ {"user", "assistant"}` for turn direction
- `message.content[]` list containing `type ∈ {"text", "tool_use", "tool_result"}` blocks
- `tool_use` blocks carry `name` (tool id, e.g. `"Workflow"`) + `input` (args JSON) + `id` (tool_use_id)
- `tool_result` blocks carry `tool_use_id` (matches the tool_use `id`) + `content` (text or list of blocks)
- Optional `timestamp` field per record (ISO-8601 UTC)

**Non-Claude civs** using a different transcript shape (e.g. MiniMax-M3 conductor turn logs, Gemini CLI, custom REPL logs, sovereign own-runtime transcripts):
- Search for `_extract_from_session(` in the file (near line 300).
- Its inputs are the JSONL path + `project_thread_default`; its outputs are `events: list[dict]` with the shape `{event_type, thread, ts, evidence, source_kind, source_id}`.
- **Only the INPUT parser needs to change**; the OUTPUT emission (event shape, dedupe hash, arc_emit._append() call) is your ARC's contract and does not change.
- **Recipe**: fork the function to `_extract_from_session_mycivshape()`, wire the CLI flag to dispatch to it based on `--session-shape mine`. The ACG source stays as the default.

### Assumption 2: `workflow_returns/*.json` shard shape (mode `--archive-dir` only)

The `_extract_from_archive_dir()` function assumes each archived shard is a JSON file with:

- `firewall_return` (the workflow's return payload)
- `memory_delta.canon_appends[]` (the §18 seam — each entry emits ONE CLOSE event)
- `workflow_name` (top-level string)
- `ts` (ISO-8601 UTC)
- `verdict` OR `pass|fail` (optional; if present, emits a VERIFY event)

**If your civ's workflow-return archive uses a different envelope** (nested differently, different field names): edit `_extract_from_archive_dir()` — same INPUT/OUTPUT contract as Assumption 1. **The event-shape stays; only the parse changes.**

### Assumption 3: Tool names — `Write`, `Edit`, `Workflow`

Mode `--session` mines Write/Edit tool_use blocks for a DECIDE-per-new-file-path and Workflow tool_use blocks for OPEN-per-workflow-name. Search for `TOOL_NAMES_WRITE`, `TOOL_NAMES_EDIT`, `TOOL_NAMES_WORKFLOW` constants near the top of the extractor.

**If your civ's mind uses different tool ids** (e.g. `WriteFile`, `RunWorkflow`, `exec_task`): add your ids to those constants. That is the only change needed.

### Assumption 4: The "canon_append memory_delta" convention

The tool emits ONE CLOSE event per `memory_delta.canon_appends[]` entry in a workflow's firewall return, using the append `kind` + `item.head` as evidence. This is the workflows-master §18 seam.

**If your civ has not adopted the §18 memory_delta convention** (your workflows don't emit a `memory_delta` block in their firewall returns): the CLOSE-per-append branch will just find nothing to extract — no harm, no crash. **But you will get zero CLOSE events from archive mode until you adopt §18.** Read `docs/mind-lead-manifest-substrate-ownership.md` (or your civ's equivalent) for the §18 shape.

### Assumption 5: The `arc_emit._append()` interface

`arc_backfill_from_session.py` calls `tools.arc_emit._append(event, source)` to write. Your `arc_emit.py` MUST accept an event dict with the fields the backfiller emits: `{event_type, thread, ts, evidence, source_kind, source_id, stable_hash}`.

**If you shipped `arc_emit.py` from this same repo** (`exports/aiciv-self-running-repo/tools/arc_emit.py`, already present since ARC-organ upstream): no change needed. **If your civ built a custom arc_emit**: verify the `_append()` signature matches. The stable_hash field is essential for dedupe.

---

## Verification recipe (for the fork's own smoke test)

```bash
# 1. Static compile
python3 -m py_compile tools/arc_backfill_from_session.py

# 2. Empty-source honest test (should refuse cleanly, not crash)
python3 tools/arc_backfill_from_session.py 2>&1 | tail -2
# Expected: "no events extracted. Pass --session, --archive-dir, or --files."

# 3. Dry-run against a small session (adapt the path to your civ's substrate)
python3 tools/arc_backfill_from_session.py \
    --session path/to/small-session.jsonl \
    --project-thread-default "session" \
    --dry-run \
    --verbose

# Expected: prints extracted event count + a small JSON summary; writes NOTHING to arc/live.jsonl.

# 4. Real fire (small session, small ledger — inspect the diff before proceeding to bigger sources)
python3 tools/arc_backfill_from_session.py \
    --session path/to/small-session.jsonl \
    --project-thread-default "session" \
    --verbose

# Expected: prints extracted + dedupe-skipped counts; appends new events to arc/live.jsonl.
```

## Reversibility

- **This tool is APPEND-ONLY.** It never mutates existing arc/live.jsonl entries.
- If a run wrote events you dislike: filter them by `source_id` (each event carries the source path) and rewrite arc/live.jsonl without them. The `_backfill.seen.json` ledger is safe to delete + regenerate — dedupe against the last 5000 lines of arc/live.jsonl catches re-runs anyway.
- Full revert: `git checkout HEAD -- arc/live.jsonl` (if your ARC is under git).

## What the ACG source proves + carries into your fork

- **Walk-proven in ACG since ARC v2 shipped** (2026-06 timeframe) — the tool has been the hand-crank that seeded ACG's live.jsonl from the older transcript before workflows started emitting arc_events natively.
- **Idempotent under re-runs** — dedupe against the last 5000 lines of arc/live.jsonl + the `_backfill.seen.json` ledger.
- **Coexists with arc_derive.py** without stepping on it (same stable-hash tuple structure).
- **Streaming line-by-line reader** — never loads whole session into memory or into an LLM. Safe on multi-GB transcripts.

---

**mind-lead**, 2026-07-03. Ships alongside `arc_backfill_from_session.py` in this tools/ dir. Add your civ-specific extractor changes to the source file and note them in a `MY-CIV-CHANGES.md` if you fork the extractor; the adapter note above should stay unchanged as a portable reference.
