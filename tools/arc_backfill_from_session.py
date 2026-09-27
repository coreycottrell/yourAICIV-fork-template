#!/usr/bin/env python3
"""
arc_backfill_from_session.py — REUSABLE manual ARC backfill from a source.

THE ARC v2 — write-side hand-crank.
Owner: mind-lead (ARC owner). Composes with: arc_emit.py, canon_append.py.

Purpose (why this exists):
    THE ARC is the medium-term (days-to-weeks) context organ. Its write-side
    is normally fed by (a) workflows emitting arc_events[] in their firewall
    return, (b) kanban transitions, (c) arc_derive.py mirroring canon_appends
    from archived firewall-returns. But for OLDER sessions — the giant JSONL
    transcript that predates full archive coverage — we need a HAND-CRANK
    that reads what was actually said + done in-transcript, and emits arc
    events for the big shifts / decisions / closes / verifies / surprises.

    This tool is that hand-crank. It reads ONE OF:

        (a) --session <path/to/*.jsonl>              (Claude Code transcript)
        (b) --archive-dir <path/to/workflow_returns> (already-archived returns)
        (c) --files <path1,path2,...>                (arbitrary artifact files)

    and emits stable-hashed, deduped arc events to arc/live.jsonl via
    tools.arc_emit._append(). Safe to re-run + safe to coexist with the
    archive-derived write-side (arc_derive.py) — dedupe is by content hash,
    not source id, so cross-source overlap is naturally suppressed.

Extraction strategy per source
------------------------------

Session .jsonl (mode a):
    EFFICIENTLY (line-by-line, streaming — never read every line into an LLM):
      1. Every Workflow tool_use (asst→Workflow tool_use)   → OPEN  (thread=workflow name)
      2. Every task-notification with a parseable <result>   → DECIDE (headline of return)
         · If the return carries memory_delta.canon_appends[] → one CLOSE per canon_append
           (thread = lead of the append, evidence = canon kind + item head)
         · If the return has explicit `verdict` / `pass|fail` → VERIFY
      3. Every Write / Edit tool_use on a NEW file path      → DECIDE (thread=file dir)
      4. Every explicit user "shift" turn (rare)              → SHIFT (thread=inferred)

    We map each surface to (event_type, thread, ts, evidence) and hash it
    (stable_hash = sha1(source_kind|thread|type|round(ts,minute)|evidence_head)).

Archive dir (mode b):
    Read each *.json shard, use its `firewall_return` + `memory_delta` +
    `workflow_name` + `ts`. Same mapping to arc events. Same stable hash.
    (Effectively a lite arc_derive with the same dedupe surface.)

Files list (mode c):
    For each file in --files, emit a single DECIDE (thread = file dir, ts =
    file mtime, evidence = "wrote path {path}"). Bare-bones — useful when
    the only substrate you have is a set of artifact paths.

Dedupe / append-safety
----------------------
    - Hash ledger at:  arc/_backfill.seen.json  (stable_hash → {ts, source})
    - Re-runs of this tool on the SAME session skip already-hashed events.
    - Coexistence with arc_derive.py's `_derive.seen.json`: arc_derive uses
      its own ledger + writes canon-id-anchored events; our stable hash
      naturally deduplicates a same-content event that arc_derive already
      wrote (because arc_derive's events use the same {thread, type, ts,
      evidence_head} tuple structure our hash keys on). We check against
      the LAST 5000 lines of arc/live.jsonl (streaming, bounded) BEFORE
      writing, so a same-shape event already present is skipped.

Usage
-----
    # Session backfill (this tool's flagship case):
    python3 tools/arc_backfill_from_session.py \
        --session ~/.claude/projects/.../<uuid>.jsonl \
        --project-thread-default "session"

    # Archive-dir backfill:
    python3 tools/arc_backfill_from_session.py \
        --archive-dir data/audits/workflow_returns/2026-07

    # Files backfill:
    python3 tools/arc_backfill_from_session.py \
        --files data/reports/foo.md,data/reports/bar.md

    # Dry run (extract but don't write):
    python3 tools/arc_backfill_from_session.py --session <path> --dry-run

Constraints
-----------
    - APPEND-ONLY (mirrors arc_emit + canon_append invariants).
    - Never rewrites past rows.
    - Stable hash means re-runs are safe (idempotent within source + across
      sources with same event content).
    - LLM is never used to extract — pure line-by-line stream + regex/JSON.

Author: mind-lead (Primary walk 2026-07-02).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Reuse arc_emit's write path + salience/halflife stamping.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
import arc_emit  # noqa: E402  (canonical writer)

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

_REPO_ROOT = _HERE.parent  # tools/ -> repo
DEFAULT_ARC_DIR = _REPO_ROOT / "arc"
LEDGER_NAME = "_backfill.seen.json"
DEDUPE_TAIL_LINES = 5000  # bound the live.jsonl tail we check against


# ------------------------------------------------------------------
# Ledger + dedupe
# ------------------------------------------------------------------


def _arc_dir() -> Path:
    p = Path(os.environ.get(arc_emit.ARC_ROOT_ENV, str(DEFAULT_ARC_DIR)))
    p.mkdir(parents=True, exist_ok=True)
    return p


def _ledger_path() -> Path:
    return _arc_dir() / LEDGER_NAME


def _load_ledger() -> Dict[str, Any]:
    p = _ledger_path()
    if not p.exists():
        return {}
    try:
        with p.open() as f:
            return json.load(f)
    except Exception:
        return {}


def _save_ledger(ledger: Dict[str, Any]) -> None:
    p = _ledger_path()
    tmp = p.with_suffix(p.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
    tmp.replace(p)


def _stable_hash(source_kind: str, ev: Dict[str, Any]) -> str:
    """Stable per-event hash — safe across re-runs + coexistence with arc_derive."""
    thread = str(ev.get("thread", ""))
    typ = str(ev.get("type", ""))
    ts = str(ev.get("ts", ""))
    # Round to minute to tolerate ~seconds drift from any upstream reformat.
    ts_min = ts[:16] if len(ts) >= 16 else ts
    evidence = str(ev.get("evidence") or ev.get("reason") or ev.get("decision") or "")[:120]
    key = f"{source_kind}|{thread}|{typ}|{ts_min}|{evidence}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def _live_tail_hashes() -> set:
    """Bounded tail-hash of arc/live.jsonl for cross-source dedupe."""
    p = _arc_dir() / "live.jsonl"
    if not p.exists():
        return set()
    tail: List[str] = []
    try:
        with p.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            # read last ~2MB
            back = min(size, 2 * 1024 * 1024)
            f.seek(size - back)
            data = f.read().decode("utf-8", errors="ignore")
            tail = data.splitlines()[-DEDUPE_TAIL_LINES:]
    except Exception:
        return set()
    out = set()
    for line in tail:
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        out.add(_stable_hash("live_tail", ev))
    return out


# ------------------------------------------------------------------
# Session .jsonl extraction (mode a)
# ------------------------------------------------------------------


def _thread_from_wf_name(name: Optional[str], default: str) -> str:
    if not name:
        return default
    # Compact — arc thread labels are short project tags.
    return f"wf:{name}"[:100]


def _headline(payload: Dict[str, Any]) -> str:
    for k in ("headline", "summary", "headline_or_summary", "title", "verdict"):
        v = payload.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()[:180]
    # Fallback: first str-valued key
    for k, v in payload.items():
        if isinstance(v, str) and len(v) > 20:
            return v.strip()[:180]
    return "workflow completed"


def _extract_from_session(path: Path, project_thread_default: str,
                          verbose: bool = False) -> List[Tuple[Dict[str, Any], str]]:
    """
    Stream the .jsonl once, extract arc events + source-kind tag.
    Returns [(event, source_kind), ...] — writer handles hash/dedupe.
    """
    events: List[Tuple[Dict[str, Any], str]] = []
    if not path.exists():
        print(f"[error] session file not found: {path}", file=sys.stderr)
        return events

    # First pass: index Workflow tool_use → {tool_use_id: (ts, name, desc)}
    wf_launches: Dict[str, Dict[str, Any]] = {}
    # Also index Write/Edit tool_use for DECIDE
    write_events: List[Dict[str, Any]] = []
    # And index task-notification completions
    completions: List[Dict[str, Any]] = []

    _NAME_RE = re.compile(r"name:\s*'([^']+)'")
    _DESC_RE = re.compile(r"description:\s*'([^']+)'")
    _RESULT_RE = re.compile(r"<result>(.*?)</result>", re.DOTALL)
    _SUMMARY_RE = re.compile(r"<summary>(.*?)</summary>", re.DOTALL)
    _TASK_ID_RE = re.compile(r"<task-id>([^<]+)</task-id>")
    _TOOL_USE_ID_RE = re.compile(r"<tool-use-id>([^<]+)</tool-use-id>")
    _WF_NAME_RE = re.compile(r'Dynamic workflow "([^"]{4,180})')

    with path.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except Exception:
                continue
            t = j.get("type")
            ts = j.get("timestamp") or ""
            msg = j.get("message", {}) if isinstance(j.get("message"), dict) else {}

            if t == "assistant":
                content = msg.get("content", [])
                if not isinstance(content, list):
                    continue
                for c in content:
                    if not isinstance(c, dict):
                        continue
                    tu = c.get("type")
                    if tu == "tool_use":
                        name = c.get("name")
                        inp = c.get("input", {}) if isinstance(c.get("input"), dict) else {}
                        if name == "Workflow":
                            script = inp.get("script", "") or ""
                            nm = _NAME_RE.search(script)
                            ds = _DESC_RE.search(script[:4000])
                            wf_launches[c.get("id", "")] = {
                                "ts": ts,
                                "name": nm.group(1) if nm else None,
                                "desc": (ds.group(1) if ds else None),
                            }
                        elif name in ("Write", "Edit"):
                            path_arg = inp.get("file_path") or inp.get("path") or ""
                            if path_arg:
                                write_events.append({
                                    "ts": ts,
                                    "path": str(path_arg),
                                    "tool": name,
                                })

            elif t == "user":
                content = msg.get("content", "")
                if isinstance(content, str) and "<task-notification>" in content:
                    m_res = _RESULT_RE.search(content)
                    m_sum = _SUMMARY_RE.search(content)
                    m_tid = _TASK_ID_RE.search(content)
                    m_tuid = _TOOL_USE_ID_RE.search(content)
                    result_payload: Any = None
                    if m_res:
                        try:
                            result_payload = json.loads(m_res.group(1))
                        except Exception:
                            result_payload = None
                    sum_txt = (m_sum.group(1) if m_sum else "").strip()
                    completions.append({
                        "ts": ts,
                        "task_id": m_tid.group(1) if m_tid else None,
                        "tool_use_id": m_tuid.group(1) if m_tuid else None,
                        "summary_head": sum_txt[:400],
                        "result": result_payload,
                    })

    if verbose:
        print(f"[extract] wf_launches={len(wf_launches)} "
              f"completions={len(completions)} "
              f"write_events={len(write_events)}", file=sys.stderr)

    # --- Map to arc events ---

    # (1) Every Workflow launch → OPEN
    for _, info in wf_launches.items():
        wf_name = info.get("name")
        desc = info.get("desc") or ""
        thread = _thread_from_wf_name(wf_name, project_thread_default)
        ev = {
            "type": "OPEN",
            "thread": thread,
            "ts": info["ts"],
            "goal": (desc or wf_name or "workflow launched")[:180],
            "owner": "primary",
        }
        events.append((ev, "session_wf_launch"))

    # (2) Every completion → DECIDE (headline) + optional CLOSE per canon_append
    for comp in completions:
        # Prefer the launch's meta.name (linked via tool_use_id) — it's short + stable.
        launch = wf_launches.get(comp.get("tool_use_id") or "", {})
        wf_name = launch.get("name")
        thread = _thread_from_wf_name(wf_name, project_thread_default)
        result = comp.get("result") if isinstance(comp.get("result"), dict) else {}
        headline = _headline(result) if result else (comp.get("summary_head", "")[:180]
                                                    or "workflow completed")
        # If we couldn't link (no launch meta.name) and got no wf_name,
        # fall back to first 80 chars of headline for thread-flavor.
        if thread == _thread_from_wf_name(None, project_thread_default) and headline:
            thread = f"wf:{headline[:60]}"
        ev = {
            "type": "DECIDE",
            "thread": thread,
            "ts": comp["ts"],
            "decision": headline,
            "evidence": f"task_id={comp.get('task_id') or 'n/a'}",
        }
        events.append((ev, "session_wf_completion"))

        # canon_appends[] → CLOSE per append
        mem_delta = result.get("memory_delta") if isinstance(result, dict) else None
        canon_items_for_overview: List[str] = []  # v2.1 overview-grab dedup basis
        if isinstance(mem_delta, dict):
            appends = mem_delta.get("canon_appends", []) or []
            if isinstance(appends, list):
                for a in appends[:6]:  # cap 6 (matches workflows-master §18 cap)
                    if not isinstance(a, dict):
                        continue
                    kind = str(a.get("kind", "note"))
                    item = str(a.get("item", ""))[:120]
                    lead = str(a.get("lead", "")) or "unknown-lead"
                    canon_items_for_overview.append(item)
                    close_ev = {
                        "type": "CLOSE",
                        "thread": f"lead:{lead}"[:100],
                        "ts": comp["ts"],
                        "reason": f"canon_append kind={kind}: {item}"[:180],
                        "evidence": f"workflow={comp.get('wf_name','?')} task_id={comp.get('task_id','?')}",
                    }
                    events.append((close_ev, "session_canon_append"))

        # v2.1 OVERVIEW-GRAB (Corey 2026-07-02): if the firewall-return's
        # top-level headline carries info that DIFFERS from every canon_append
        # item, emit a separate DECIDE event tagged overview=True. Uses the
        # same token-Jaccard dedup as arc_emit.emit_overview_if_novel (kept
        # inline here because arc_backfill uses arc_emit._append directly and
        # we want the source-kind stamped for the seen-ledger).
        try:
            # Lazy import to avoid circular init in edge callers.
            from tools.arc_emit import _headline_captured_by_appends  # type: ignore
        except Exception:
            _headline_captured_by_appends = None  # graceful degrade
        if (headline
                and _headline_captured_by_appends is not None
                and not _headline_captured_by_appends(headline, canon_items_for_overview)):
            overview_ev = {
                "type": "DECIDE",
                "thread": thread,
                "ts": comp["ts"],
                "decision": headline,
                "overview": True,   # v2.1 marker: human-facing gist
                "evidence": f"task_id={comp.get('task_id') or 'n/a'} "
                            f"overview_grab (differs from {len(canon_items_for_overview)} "
                            f"canon_append{'s' if len(canon_items_for_overview)!=1 else ''})",
            }
            events.append((overview_ev, "session_overview_grab"))

        # explicit verdict → VERIFY
        for verdict_key in ("verdict", "result", "pass_fail", "verify"):
            v = result.get(verdict_key) if isinstance(result, dict) else None
            if isinstance(v, str) and v.lower() in ("pass", "fail", "partial", "true", "false"):
                events.append(({
                    "type": "VERIFY",
                    "thread": thread,
                    "ts": comp["ts"],
                    "claim": headline,
                    "verifier": "workflow_return",
                    "result": "pass" if v.lower() in ("pass", "true") else "fail",
                    "evidence": f"task_id={comp.get('task_id') or 'n/a'}",
                }, "session_wf_verify"))
                break

    # (3) Every Write to a NEW-ish artifact → DECIDE (thread = file dir)
    seen_paths = set()
    for w in write_events:
        p = w["path"]
        if p in seen_paths:
            continue
        seen_paths.add(p)
        # Skip noisy paths — .claude scratchpad thrash, tmp
        if "/.claude/scratchpad" in p or p.startswith("/tmp/"):
            continue
        parent = str(Path(p).parent)
        # Thread = the LAST 2 path segments after ACG/ (project-flavored)
        segs = [s for s in parent.split(os.sep) if s]
        if "ACG" in segs:
            idx = segs.index("ACG")
            tail = segs[idx + 1: idx + 4]
        else:
            tail = segs[-2:]
        thread = "file:" + "/".join(tail)[:80] if tail else "file:root"
        ev = {
            "type": "DECIDE",
            "thread": thread,
            "ts": w["ts"],
            "decision": f"{w['tool']} {Path(p).name}",
            "evidence": p[:180],
        }
        events.append((ev, "session_write"))

    return events


# ------------------------------------------------------------------
# Archive-dir extraction (mode b) — lite arc_derive
# ------------------------------------------------------------------


def _extract_from_archive_dir(dir_path: Path) -> List[Tuple[Dict[str, Any], str]]:
    events: List[Tuple[Dict[str, Any], str]] = []
    if not dir_path.exists() or not dir_path.is_dir():
        print(f"[error] archive dir not found: {dir_path}", file=sys.stderr)
        return events
    for shard in sorted(dir_path.glob("*.json")):
        try:
            with shard.open() as f:
                doc = json.load(f)
        except Exception as e:
            print(f"[warn] skip {shard.name}: {e}", file=sys.stderr)
            continue
        ts = doc.get("ts") or ""
        # Normalize ISO to Z form if possible
        if ts and "+" in ts:
            ts = ts.split("+")[0] + "Z"
        wf_name = doc.get("workflow_name") or "inline"
        thread = _thread_from_wf_name(wf_name, "archive")
        fr = doc.get("firewall_return") or {}
        headline = _headline(fr) if isinstance(fr, dict) else "archived return"
        events.append(({
            "type": "DECIDE",
            "thread": thread,
            "ts": ts,
            "decision": headline,
            "evidence": f"archive={shard.name}",
        }, "archive_shard"))
        mem_delta = fr.get("memory_delta") if isinstance(fr, dict) else None
        if isinstance(mem_delta, dict):
            for a in (mem_delta.get("canon_appends") or [])[:6]:
                if not isinstance(a, dict):
                    continue
                events.append(({
                    "type": "CLOSE",
                    "thread": f"lead:{a.get('lead','unknown-lead')}"[:100],
                    "ts": ts,
                    "reason": f"canon_append kind={a.get('kind','note')}: {a.get('item','')[:120]}"[:180],
                    "evidence": f"archive={shard.name}",
                }, "archive_canon_append"))
    return events


# ------------------------------------------------------------------
# Files list extraction (mode c)
# ------------------------------------------------------------------


def _extract_from_files(paths: List[Path]) -> List[Tuple[Dict[str, Any], str]]:
    events: List[Tuple[Dict[str, Any], str]] = []
    for p in paths:
        if not p.exists():
            print(f"[warn] file not found, skipping: {p}", file=sys.stderr)
            continue
        try:
            mtime = time.gmtime(p.stat().st_mtime)
            ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", mtime)
        except Exception:
            ts = arc_emit._iso_utc_now()
        parent = str(p.parent)
        segs = [s for s in parent.split(os.sep) if s]
        thread = "file:" + "/".join(segs[-2:]) if segs else "file:root"
        events.append(({
            "type": "DECIDE",
            "thread": thread[:100],
            "ts": ts,
            "decision": f"wrote {p.name}",
            "evidence": str(p)[:180],
        }, "files"))
    return events


# ------------------------------------------------------------------
# Write path (calls arc_emit._append after dedupe)
# ------------------------------------------------------------------


def _write_deduped(events: List[Tuple[Dict[str, Any], str]],
                   dry_run: bool = False,
                   verbose: bool = False) -> Dict[str, Any]:
    ledger = _load_ledger()
    live_tail = _live_tail_hashes()
    to_write: List[Dict[str, Any]] = []
    skipped_ledger = 0
    skipped_live = 0

    for ev, source_kind in events:
        h = _stable_hash(source_kind, ev)
        # Cross-source coexistence: same event content already in live tail?
        h_generic = _stable_hash("live_tail", ev)
        if h in ledger:
            skipped_ledger += 1
            continue
        if h_generic in live_tail:
            skipped_live += 1
            ledger[h] = {"skipped": "already_in_live_tail",
                         "ts": ev.get("ts")}
            continue
        to_write.append(ev)
        ledger[h] = {"source": source_kind, "ts": ev.get("ts"),
                     "wrote_at": arc_emit._iso_utc_now()}

    if verbose:
        print(f"[dedupe] to_write={len(to_write)} "
              f"skipped_ledger={skipped_ledger} "
              f"skipped_live={skipped_live}", file=sys.stderr)

    if dry_run:
        return {
            "ok": True,
            "dry_run": True,
            "would_write": len(to_write),
            "skipped_ledger": skipped_ledger,
            "skipped_live": skipped_live,
            "sample": to_write[:5],
        }

    if not to_write:
        return {
            "ok": True,
            "appended": 0,
            "skipped_ledger": skipped_ledger,
            "skipped_live": skipped_live,
            "note": "nothing new to write",
        }

    # Chunk in batches of 500 to keep arc_emit._append happy (its cap
    # applies to firewall-return context only; we pass enforce_cap=False).
    result = arc_emit._append(to_write, enforce_cap=False)
    if not result.get("ok"):
        return result

    _save_ledger(ledger)
    result["skipped_ledger"] = skipped_ledger
    result["skipped_live"] = skipped_live
    return result


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--session", type=Path,
                   help="Path to a Claude Code session .jsonl transcript")
    p.add_argument("--archive-dir", type=Path,
                   help="Path to a workflow_returns/YYYY-MM directory")
    p.add_argument("--files", type=str,
                   help="Comma-separated list of file paths")
    p.add_argument("--project-thread-default", type=str, default="session",
                   help="Fallback thread label when workflow name is unknown")
    p.add_argument("--dry-run", action="store_true",
                   help="Extract + report but don't write to arc/live.jsonl")
    p.add_argument("--verbose", "-v", action="store_true")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    events: List[Tuple[Dict[str, Any], str]] = []
    sources: List[str] = []

    if args.session:
        ev = _extract_from_session(args.session, args.project_thread_default, verbose=args.verbose)
        events.extend(ev)
        sources.append(f"session={args.session.name} extracted={len(ev)}")

    if args.archive_dir:
        ev = _extract_from_archive_dir(args.archive_dir)
        events.extend(ev)
        sources.append(f"archive_dir={args.archive_dir.name} extracted={len(ev)}")

    if args.files:
        paths = [Path(p.strip()) for p in args.files.split(",") if p.strip()]
        ev = _extract_from_files(paths)
        events.extend(ev)
        sources.append(f"files={len(paths)} extracted={len(ev)}")

    if not events:
        print("[error] no events extracted. Pass --session, --archive-dir, or --files.",
              file=sys.stderr)
        return 2

    result = _write_deduped(events, dry_run=args.dry_run, verbose=args.verbose)
    result["sources"] = sources
    result["extracted_total"] = len(events)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
