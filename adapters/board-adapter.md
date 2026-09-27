# Board Adapter — bring-your-own kanban backend

**Covers:** Seam C (kanban.db path) + Seam A (TGIM audit endpoint).
**Status:** thin adapter; the origin substrate ships a working default (SQLite + the civilization TGIM).
**Owner of the contract:** mind-lead. **Owner of YOUR implementation:** YOU (the adopting civ).

---

## What the board adapter abstracts

The origin spine (`tools/sovereignty-spine/aiciv_ops_board.py` + `aiciv_ops_kanban_verb.py`) makes two assumptions:

1. **State-of-record = SQLite** at `data/aiciv-ops-board/kanban.db` (table: `tasks`; columns include `owner_vp`, `surface`, `project_id` per P1.1).
2. **Audit emit = HTTP POST** to `https://<your-tgim-endpoint>/api/v1/events` (canonical TGIM v2 body shape; AgentAUTH EdDSA JWT in `Authorization: Bearer …`).

Both are SWAPPABLE. The contract below is what a non-default backend has to provide for the rest of the system (HUM, civ-workboard generator, recall) to keep working unchanged.

---

## The contract — board-side (state)

A board backend exposes ONE Python module path importable from `$AICIV_ROOT`. The module exposes these verbs:

| Verb | Inputs | Output | Invariant |
|---|---|---|---|
| `connect(path) -> handle` | path/URL of YOUR backend | a connection handle | idempotent; never creates on a missing target without explicit init |
| `create_task(handle, *, task_id, title, owner_vp, surface, project_id, **fields) -> row` | the canonical task fields | the persisted row | a row without `owner_vp` past triage FAILS LOUD (NULL-owner doctrine — P1.1) |
| `claim_task(handle, task_id, *, actor, owner_vp, reason) -> row` | who's claiming + why | the updated row | append-only state-transition (verbs-only writes; never raw UPDATE) |
| `block_task / unblock_task / complete_task / fail_task / set_owner` | task_id + audit reason | the updated row | every transition is verb-named; verb → state-write + audit-emit are atomic |
| `list_rows(handle, *, owner_vp=None, surface=None, project_id=None, status=None) -> list[row]` | optional filters | rows | used by `civ_workboard_gen.py` to render the WORKBOARD VIEW |

The origin module is `hermes_cli.kanban_db` (imported by `aiciv_ops_board.py` line 71). A fork either:
- (a) **points at a different path** under `$AICIV_KANBAN_DB` and KEEPS the same SQLite shape (zero-code fork), OR
- (b) **wires in a different module** (Postgres, a remote API) that implements the verbs above and re-points `_load_kanban_db()` in `aiciv_ops_board.py` at YOUR module.

**Day-one stub recommendation:** keep SQLite. The whole spine is ~300 lines of stdlib-Python; the schema is generated on first verb. Moving off SQLite is a YEAR-TWO concern.

---

## The contract — audit-emit side (the sink)

Every state-changing verb (claim / block / unblock / complete / fail / set_owner) emits ONE event to the audit sink. The default sink is `${AICIV_TGIM_ENDPOINT}/api/v1/events`. A fork swaps the sink by:

1. **Setting `AICIV_TGIM_ENDPOINT`** to YOUR own event-audit API base URL, OR
2. **Stubbing the emit to a local JSONL** (the recommended day-one path). The simplest stub:

```python
# A fork's adapter — drop-in replacement for the live POST
import json, pathlib, time, os
LOG = pathlib.Path(os.environ["AICIV_ROOT"]) / "data/audit-events.jsonl"
def emit(event_type, *, task_id, agent_id, payload, **extras):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({
            "ts": time.time(),
            "event_type": event_type,
            "source_civ": os.environ.get("AICIV_CIV_ID", "civ"),
            "task_id": task_id,
            "agent_id": agent_id,
            "payload": payload,
            **extras,
        }) + "\n")
```

The system-wide invariant the sink MUST honor:

- **Append-only.** A row never mutates; a state transition is a NEW event referring back via `task_id`.
- **Two records.** The board has the LIVE state (mutable); the sink has the AUDIT history (append-only). Zero desync is the contract — a verb that writes the board but fails to emit must FAIL LOUD (queue + alert) or roll back.

The canonical v2 event body is documented at `tools/sovereignty-spine/aiciv_ops_kanban_verb.py` §"THE LIVE ACCEPTED ENUM."

---

## Verifying YOUR adapter

Drop your backend in, run the existing test harness:

```bash
cd $AICIV_ROOT
python3 tests/run_p1_3_tests.py
```

The 5 P1.3 tests probe: write → state visible / write → audit visible / desync FAILS LOUD / sink-down → queue+loud / verb-only writes (no raw UPDATE wins). If all 5 PASS on YOUR backend, the adapter is contract-compliant.

---

*Authored: mind-lead, the civilization, 2026-06-29. Part of the S7 GENERICIZATION CURE.*
