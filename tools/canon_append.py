#!/usr/bin/env python3
"""
canon_append.py — SOLE append-only writer to mem/canon/<lead>/log.jsonl.

========================================================================
REDUCED-PORT DISCLOSURE (2026-07-09, read this first — honesty, not FUD)
========================================================================
This file is a ~721-line REDUCED reimplementation of SRR's writer. It is
NOT the full SRR canon_append. The upstream SRR writer (@67dcc96, ~2034
lines) ships several protective cures that this port SILENTLY DROPPED. A
fork MUST NOT assume these cures are present just because the file is
named canon_append.py. NOT ported here:
  - phantom-receipt anchor-guard  (SRR verifies a claimed receipt path
    actually exists / is anchored before trusting a verifier witness)
  - FLOOD-CURE circuit-breakers    (SRR rate/volume breakers that trip when
    an incarnation floods canon with low-value appends)
  - chroma / vector-index write path (this port is lexical-rail only)
  - rejection-ledger               (SRR logs rejected appends to an audit
    ledger; this port just returns non-zero)
Net effect: **phantom-receipt protection and flood protection are NOT
present in this port.** What IS net-new here is the learn-cycle write-gate
(different-mind verifier check + warn/provisional-only/enforce modes) —
that gate is genuinely new code, but it is a NARROW slice of SRR's writer,
not the full writer. If you need the dropped cures, port them from
SRR @67dcc96; do not assume this file already has them.
========================================================================

Part of the AiCIV-Native Org Phase-1 foundation (SPEC §5: WRITE step of the
memory pipe). Agents NEVER write directly; the incarnation_runner calls this.

Closed enum for `kind`:
    finding | decision | retraction | doctrine-candidate

Behavior:
  - Append EXACTLY ONE JSON line per invocation.
  - On append, if log grew +50 lines since the last DIGEST rebuild, write a
    MECHANICAL placeholder DIGEST.md = last-200-lines of the log (one line per
    canon entry, rendered as compact markdown bullets).
    Phase 2 replaces this placeholder with the agentic librarian (Option B).

CLI:
    python3 tools/canon_append.py --lead <id> --kind <enum> \\
        --item "<short claim>" --rationale "<why it matters>" \\
        [--extra '<json>'] [--provisional [--ttl-hours N]]
    python3 tools/canon_append.py --promote <provisional-id> --lead <id> \\
        --audit-verdict PASS --audit-ref <ref>

Self-test:
    python3 tools/canon_append.py --self-test
    # Appends to mem/canon/_selftest/log.jsonl and verifies the line landed,
    # then exercises the learn-cycle gate + provisional/promote round-trip.

LEARN-CYCLE WRITE-GATE (added 2026-07-09, SRR delta integration — see
.claude/skills/learn-cycle-contract/SKILL.md + FIRING_CONTRACT.md):
    Load-bearing kinds (finding, doctrine-candidate) SHOULD carry a
    different-mind witness in extras: {"verifier": "<lead != producer>",
    "verifier_verdict": "PASS", "verifier_receipt": "<path>"}.

    - extra.verifier == --lead is ALWAYS rejected (an explicit self-grade is
      the contract's named failure mode — worse than no claim).
    - Mode env AICIV_LEARN_CONTRACT_MODE (alias CIV_LEARN_CONTRACT_MODE):
        warn (DEFAULT)     — unverified load-bearing appends land, stamped
                             extra.learn_contract="unverified-warn-mode",
                             warning on stderr. Newborn-safe.
        provisional-only   — unverified load-bearing appends are staged to
                             pending.jsonl instead of log.jsonl (promote later
                             with a verifier witness).
        enforce            — unverified load-bearing direct appends REJECT
                             (exit 2). Arm this once a second mind is reachable.
    HONEST STAMP (corrected 2026-07-09 per ACG Auditor-B): the learn-cycle
    write-gate is a NET-NEW learn-cycle GATE built onto a REDUCED PORT of the
    SRR writer — it is NOT "SRR ships no writer impl". SRR @67dcc96 DOES ship a
    fuller (~2034-line) writer; this file is a ~721-line reduced reimpl that
    dropped SRR's phantom-receipt anchor-guard, flood-cure circuit-breakers,
    chroma vector path, and rejection-ledger (see REDUCED-PORT DISCLOSURE at
    top of file). So the accurate stamp is: "REDUCED PORT + net-new learn-cycle
    gate (NOT the full SRR writer)". The gate itself is PROVISIONAL /
    UNVALIDATED until a fork's first real different-mind verification pass.
    Backup of the pre-gate organ: tools/canon_append.py.bak-pre-learn-gate-20260709.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys
import uuid
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Resolve repo root from this file's location (tools/ is a child of repo root).
REPO_ROOT = Path(__file__).resolve().parent.parent
MEM_CANON = REPO_ROOT / "mem" / "canon"

ALLOWED_KINDS = frozenset({
    "finding",
    "decision",
    "retraction",
    "doctrine-candidate",
})

# Digest-rebuild trigger: per SPEC §5 ("at +50 lines runtime rebuilds DIGEST.md").
# This is a placeholder threshold per OQ-4; revisit with production data.
DIGEST_TRIGGER_DELTA = 50

# Mechanical placeholder digest target length (Phase 1).
# SPEC §5: DIGEST.md ≤200 lines.
DIGEST_TAIL_LINES = 200

# Restrict lead ids to a safe charset so we cannot path-traverse out of mem/canon.
# Also covers the reserved _selftest lead (leading underscore allowed).
LEAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$")

DIGEST_MARKER_PREFIX = "<!-- canon_append.py digest@"  # used to read back ledger_lines


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso_utc() -> str:
    """RFC-3339 UTC timestamp, second resolution + 'Z' suffix."""
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_lead(lead: str) -> str:
    if not LEAD_ID_PATTERN.match(lead):
        raise ValueError(
            f"invalid --lead {lead!r}: must match {LEAD_ID_PATTERN.pattern}"
        )
    return lead


def _validate_kind(kind: str) -> str:
    if kind not in ALLOWED_KINDS:
        raise ValueError(
            f"invalid --kind {kind!r}: allowed = {sorted(ALLOWED_KINDS)}"
        )
    return kind


def _lead_dir(lead: str) -> Path:
    d = MEM_CANON / lead
    d.mkdir(parents=True, exist_ok=True)
    return d


def _log_path(lead: str) -> Path:
    return _lead_dir(lead) / "log.jsonl"


def _digest_path(lead: str) -> Path:
    return _lead_dir(lead) / "DIGEST.md"


def _pending_path(lead: str) -> Path:
    return _lead_dir(lead) / "pending.jsonl"


# ---------------------------------------------------------------------------
# LEARN-cycle write-gate (learn-cycle-contract; PROVISIONAL — see module doc)
# ---------------------------------------------------------------------------

# Kinds that carry load-bearing claims and therefore want a different-mind
# witness (FIRING_CONTRACT: "every LEARN-step canon append where
# kind ∈ {finding, doctrine-candidate}").
LOAD_BEARING_KINDS = frozenset({"finding", "doctrine-candidate"})

VALID_CONTRACT_MODES = ("warn", "provisional-only", "enforce")


def _learn_contract_mode() -> str:
    mode = (os.environ.get("AICIV_LEARN_CONTRACT_MODE")
            or os.environ.get("CIV_LEARN_CONTRACT_MODE")
            or "warn").strip().lower()
    return mode if mode in VALID_CONTRACT_MODES else "warn"


def _check_learn_gate(lead: str, kind: str, extra: dict | None) -> str:
    """Apply the learn-cycle write-gate to a DIRECT (non-provisional) append.

    Returns one of: "ok" (append normally), "warn" (append + stamp unverified),
    "stage" (route to pending.jsonl). Raises ValueError on the always-rejected
    self-grade shape (extra.verifier == lead).
    """
    ext = extra or {}
    verifier = ext.get("verifier")
    if verifier is not None and str(verifier).strip() == lead:
        raise ValueError(
            f"learn-cycle-contract REJECT: extra.verifier == --lead ({lead!r}) "
            f"is a self-graded entry — the contract's named failure mode. "
            f"The verifier MUST be a different mind."
        )
    if kind not in LOAD_BEARING_KINDS:
        return "ok"
    if verifier and str(verifier).strip():
        return "ok"  # different-mind witness present
    mode = _learn_contract_mode()
    if mode == "enforce":
        raise ValueError(
            f"learn-cycle-contract REJECT (mode=enforce): kind={kind!r} is "
            f"load-bearing and carries no extra.verifier (different-mind "
            f"witness). Stage it with --provisional and promote after "
            f"verification, or supply --extra '{{\"verifier\": ...}}'."
        )
    if mode == "provisional-only":
        return "stage"
    return "warn"


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    with path.open("rb") as fh:
        for _ in fh:
            n += 1
    return n


def _read_digest_ledger_lines(digest: Path) -> int:
    """Parse the marker we embed in DIGEST.md so we know when last rebuild was."""
    if not digest.exists():
        return 0
    try:
        with digest.open("r", encoding="utf-8") as fh:
            for line in fh:
                if line.startswith(DIGEST_MARKER_PREFIX):
                    # marker shape: <!-- canon_append.py digest@<lines> at <ts> -->
                    try:
                        chunk = line.split("digest@", 1)[1]
                        n_str = chunk.split(" ", 1)[0]
                        return int(n_str)
                    except (IndexError, ValueError):
                        return 0
    except OSError:
        return 0
    return 0


def _maybe_rebuild_digest(lead: str) -> bool:
    """Rebuild MECHANICAL placeholder digest if log grew +DIGEST_TRIGGER_DELTA lines.

    Returns True if a rebuild occurred. Phase 2 swaps this for the agentic
    librarian; the trigger condition stays the same.
    """
    log = _log_path(lead)
    digest = _digest_path(lead)
    current = _count_lines(log)
    previous = _read_digest_ledger_lines(digest)

    # Trigger on first-ever digest too (previous==0 and current>=DIGEST_TRIGGER_DELTA),
    # or any growth beyond the threshold since last rebuild.
    if (current - previous) < DIGEST_TRIGGER_DELTA:
        return False

    # MECHANICAL placeholder: last-DIGEST_TAIL_LINES of the log, one bullet each.
    tail: list[str] = []
    with log.open("r", encoding="utf-8") as fh:
        lines = fh.readlines()
    for raw in lines[-DIGEST_TAIL_LINES:]:
        raw = raw.strip()
        if not raw:
            continue
        try:
            obj = json.loads(raw)
            ts = obj.get("ts", "?")
            kind = obj.get("kind", "?")
            item = obj.get("item", "")
            tail.append(f"- `{ts}` **{kind}** — {item}")
        except json.JSONDecodeError:
            tail.append(f"- (unparsable) {raw[:200]}")

    marker = f"{DIGEST_MARKER_PREFIX}{current} at {_now_iso_utc()} -->"
    body = "\n".join([
        f"# mem/canon/{lead}/DIGEST.md",
        "",
        marker,
        "",
        f"**Mode**: MECHANICAL placeholder (last-{DIGEST_TAIL_LINES} canon lines).",
        "**Replaced by**: Phase-2 agentic librarian (`workflows/digest-librarian.js`).",
        f"**Ledger lines at rebuild**: {current}",
        "",
        "## Recent canon",
        "",
        *tail,
        "",
    ])
    digest.write_text(body, encoding="utf-8")
    return True


def append_canon(
    lead: str,
    kind: str,
    item: str,
    rationale: str,
    *,
    writer: str = "canon_append.py",
    extra: dict | None = None,
) -> dict:
    """Append exactly one JSON line to mem/canon/<lead>/log.jsonl and return it.

    Raises ValueError on invalid lead/kind/empty fields.
    """
    lead = _validate_lead(lead)
    kind = _validate_kind(kind)
    if not item or not item.strip():
        raise ValueError("--item must be a non-empty string")
    if not rationale or not rationale.strip():
        raise ValueError("--rationale must be a non-empty string")

    # LEARN-cycle write-gate (raises on self-grade; may warn-stamp or reroute)
    gate = _check_learn_gate(lead, kind, extra)

    entry = {
        "ts": _now_iso_utc(),
        "id": uuid.uuid4().hex,
        "lead": lead,
        "kind": kind,
        "item": item.strip(),
        "rationale": rationale.strip(),
        "writer": writer,
    }
    if extra:
        # Don't let extras shadow load-bearing fields.
        for k, v in extra.items():
            if k not in entry:
                entry[k] = v

    if gate == "warn":
        entry["learn_contract"] = "unverified-warn-mode"
        print(
            f"WARN learn-cycle-contract: load-bearing kind={kind!r} appended "
            f"WITHOUT a different-mind verifier (mode=warn). Add extra.verifier "
            f"or arm AICIV_LEARN_CONTRACT_MODE=enforce once a second mind is "
            f"reachable.",
            file=sys.stderr,
        )
    elif gate == "stage":
        # provisional-only mode: reroute to pending.jsonl, never log.jsonl
        return stage_provisional_entry(entry)

    line = json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n"
    log = _log_path(lead)
    # Atomic-enough append: open in "a", write once. Single-writer discipline
    # (only this script writes to mem/canon/<lead>/log.jsonl) is the contract;
    # POSIX append is atomic for write() <= PIPE_BUF for single small lines.
    with log.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass  # tmpfs etc; the write hit the page cache, good enough

    _maybe_rebuild_digest(lead)
    return entry


# ---------------------------------------------------------------------------
# Provisional staging + promotion (pending.jsonl side-file)
# ---------------------------------------------------------------------------

def stage_provisional_entry(entry: dict, ttl_hours: int = 24) -> dict:
    """Stage a fully-built entry into mem/canon/<lead>/pending.jsonl.

    pending.jsonl is a staging side-file (append-only by convention; promotion
    appends a marker line rather than rewriting). The trunk (log.jsonl) is
    untouched until --promote.
    """
    entry = dict(entry)
    entry["provisional"] = True
    entry["ttl_hours"] = ttl_hours
    pending = _pending_path(entry["lead"])
    with pending.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    return entry


def stage_provisional(
    lead: str,
    kind: str,
    item: str,
    rationale: str,
    *,
    writer: str = "canon_append.py",
    extra: dict | None = None,
    ttl_hours: int = 24,
) -> dict:
    """Build + validate an entry, then stage it provisionally (never log.jsonl).

    The learn-cycle gate's self-grade rejection still applies (a staged
    self-graded entry would just be a delayed lie); the missing-verifier check
    does NOT (staging IS the sanctioned pre-verification parking spot).
    """
    lead = _validate_lead(lead)
    kind = _validate_kind(kind)
    if not item or not item.strip():
        raise ValueError("--item must be a non-empty string")
    if not rationale or not rationale.strip():
        raise ValueError("--rationale must be a non-empty string")
    ext = extra or {}
    verifier = ext.get("verifier")
    if verifier is not None and str(verifier).strip() == lead:
        raise ValueError(
            "learn-cycle-contract REJECT: extra.verifier == --lead is a "
            "self-graded entry, even provisionally."
        )
    entry = {
        "ts": _now_iso_utc(),
        "id": uuid.uuid4().hex,
        "lead": lead,
        "kind": kind,
        "item": item.strip(),
        "rationale": rationale.strip(),
        "writer": writer,
    }
    for k, v in ext.items():
        if k not in entry:
            entry[k] = v
    return stage_provisional_entry(entry, ttl_hours=ttl_hours)


def promote_provisional(
    lead: str,
    provisional_id: str,
    audit_verdict: str,
    audit_ref: str,
) -> dict:
    """Promote a staged entry from pending.jsonl to log.jsonl.

    Appends the promoted entry to the trunk with audit attestation fields,
    then appends a promotion-marker line to pending.jsonl (side-file stays
    append-only; a marker supersedes the staged line).
    """
    lead = _validate_lead(lead)
    pending = _pending_path(lead)
    if not pending.exists():
        raise ValueError(f"no pending.jsonl for lead {lead!r}")
    staged = None
    promoted_ids = set()
    for raw in pending.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        try:
            rec = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if rec.get("promoted_id"):
            promoted_ids.add(rec["promoted_id"])
        elif rec.get("id") == provisional_id or (
                len(provisional_id) >= 8
                and str(rec.get("id", "")).startswith(provisional_id)):
            staged = rec
    if staged is None:
        raise ValueError(
            f"no staged entry matching id {provisional_id!r} in {pending}"
        )
    if staged["id"] in promoted_ids:
        raise ValueError(f"entry {staged['id']} was already promoted")

    trunk_entry = {k: v for k, v in staged.items()
                   if k not in ("provisional", "ttl_hours")}
    trunk_entry["ts"] = _now_iso_utc()
    trunk_entry["audit_verdict"] = audit_verdict
    trunk_entry["audit_ref"] = audit_ref
    trunk_entry["promoted_from"] = "pending.jsonl"

    line = json.dumps(trunk_entry, ensure_ascii=False, sort_keys=True) + "\n"
    log = _log_path(lead)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(line)
        fh.flush()
        try:
            os.fsync(fh.fileno())
        except OSError:
            pass
    with pending.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "promoted_id": staged["id"],
            "ts": _now_iso_utc(),
            "audit_verdict": audit_verdict,
            "audit_ref": audit_ref,
        }, ensure_ascii=False, sort_keys=True) + "\n")
    _maybe_rebuild_digest(lead)
    return trunk_entry


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def run_self_test() -> int:
    """Append to mem/canon/_selftest/log.jsonl and verify the line landed.

    Exit 0 = pass, 1 = fail. Prints a one-line verdict.
    """
    lead = "_selftest"
    log = _log_path(lead)
    pre_count = _count_lines(log)

    marker = f"selftest-{uuid.uuid4().hex[:8]}"
    try:
        entry = append_canon(
            lead=lead,
            kind="finding",
            item=f"canon_append.py self-test {marker}",
            rationale="Phase-1 build gate — proves single append + JSONL parses + line count grew by exactly 1.",
            writer="canon_append.py --self-test",
        )
    except Exception as exc:
        print(f"FAIL self-test: append raised {type(exc).__name__}: {exc}")
        return 1

    post_count = _count_lines(log)
    if post_count != pre_count + 1:
        print(
            f"FAIL self-test: line count went {pre_count} -> {post_count} "
            f"(expected {pre_count + 1})"
        )
        return 1

    # Verify the last line parses and contains our marker
    with log.open("r", encoding="utf-8") as fh:
        last = fh.readlines()[-1].strip()
    try:
        parsed = json.loads(last)
    except json.JSONDecodeError as exc:
        print(f"FAIL self-test: last line is not valid JSON: {exc}")
        return 1

    if marker not in parsed.get("item", ""):
        print(f"FAIL self-test: marker {marker!r} not found in last entry")
        return 1
    if parsed.get("id") != entry["id"]:
        print("FAIL self-test: returned entry id != id on disk")
        return 1
    if parsed.get("kind") not in ALLOWED_KINDS:
        print(f"FAIL self-test: kind {parsed.get('kind')!r} not in closed enum")
        return 1

    # --- learn-cycle gate: self-grade is ALWAYS rejected ---
    try:
        append_canon(
            lead=lead, kind="finding",
            item=f"self-grade probe {marker}",
            rationale="must be rejected: verifier == lead",
            extra={"verifier": lead},
        )
        print("FAIL self-test: self-graded append (verifier==lead) was ACCEPTED")
        return 1
    except ValueError:
        pass

    # --- learn-cycle gate: enforce mode rejects unverified load-bearing kinds ---
    prev_mode = os.environ.get("AICIV_LEARN_CONTRACT_MODE")
    os.environ["AICIV_LEARN_CONTRACT_MODE"] = "enforce"
    try:
        append_canon(
            lead=lead, kind="finding",
            item=f"unverified probe {marker}",
            rationale="must be rejected in enforce mode: no verifier",
        )
        print("FAIL self-test: enforce mode ACCEPTED an unverified finding")
        return 1
    except ValueError:
        pass
    finally:
        if prev_mode is None:
            os.environ.pop("AICIV_LEARN_CONTRACT_MODE", None)
        else:
            os.environ["AICIV_LEARN_CONTRACT_MODE"] = prev_mode

    # --- provisional staging + promotion round-trip ---
    staged = stage_provisional(
        lead=lead, kind="finding",
        item=f"provisional round-trip {marker}",
        rationale="self-test: stage to pending.jsonl then promote to log.jsonl",
    )
    if not _pending_path(lead).exists():
        print("FAIL self-test: stage_provisional wrote no pending.jsonl")
        return 1
    promoted = promote_provisional(lead, staged["id"], "PASS", "self-test")
    with log.open("r", encoding="utf-8") as fh:
        tail = json.loads(fh.readlines()[-1])
    if tail.get("id") != staged["id"] or tail.get("audit_verdict") != "PASS":
        print("FAIL self-test: promoted entry did not land as trunk tail")
        return 1
    try:
        promote_provisional(lead, staged["id"], "PASS", "self-test")
        print("FAIL self-test: double-promotion was ACCEPTED")
        return 1
    except ValueError:
        pass

    print(
        f"PASS self-test: appended id={entry['id']} to {log} "
        f"(lines {pre_count} -> {post_count}); learn-gate self-grade REJECT ok; "
        f"enforce-mode REJECT ok; provisional stage+promote ok "
        f"(promoted id={promoted['id']}); double-promote REJECT ok"
    )
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="canon_append.py",
        description=(
            "Sole append-only writer to mem/canon/<lead>/log.jsonl "
            "(AiCIV-Native Org Phase 1, SPEC §5)."
        ),
    )
    p.add_argument("--lead", help="Lead identity id (e.g. 'web-lead').")
    p.add_argument(
        "--kind",
        choices=sorted(ALLOWED_KINDS),
        help="Closed enum: finding | decision | retraction | doctrine-candidate.",
    )
    p.add_argument("--item", help="Short claim (single-line preferred).")
    p.add_argument("--rationale", help="Why this matters; trace to evidence.")
    p.add_argument(
        "--extra",
        help=(
            "JSON object of extra fields (e.g. verifier/verifier_verdict/"
            "verifier_receipt per learn-cycle-contract; receipt_path; retracts)."
        ),
    )
    p.add_argument(
        "--receipt-path",
        help="Path to walkable evidence for this entry (stored as "
             "extra.receipt_path; SRR-compatible flag).",
    )
    p.add_argument(
        "--provisional",
        action="store_true",
        help="Stage the entry to pending.jsonl instead of log.jsonl.",
    )
    p.add_argument(
        "--ttl-hours",
        type=int,
        default=24,
        help="Advisory TTL for a provisional entry (default 24).",
    )
    p.add_argument(
        "--promote",
        metavar="PROVISIONAL_ID",
        help="Promote a staged pending.jsonl entry to log.jsonl (needs --lead, "
             "--audit-verdict, --audit-ref).",
    )
    p.add_argument("--audit-verdict", help="Verdict recorded on promotion (e.g. PASS).")
    p.add_argument("--audit-ref", help="Audit reference recorded on promotion.")
    p.add_argument(
        "--self-test",
        action="store_true",
        help="Run the self-test against mem/canon/_selftest/ and exit.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    if args.promote:
        missing = [n for n in ("lead", "audit_verdict", "audit_ref")
                   if getattr(args, n) is None]
        if missing:
            parser.error("--promote requires: "
                         + ", ".join(f"--{m.replace('_', '-')}" for m in missing))
        try:
            entry = promote_provisional(
                args.lead, args.promote, args.audit_verdict, args.audit_ref)
        except ValueError as exc:
            print(f"reject: {exc}", file=sys.stderr)
            return 2
        print(json.dumps({"ok": True, "promoted": entry, "id": entry["id"]},
                         ensure_ascii=False))
        return 0

    missing = [
        name
        for name in ("lead", "kind", "item", "rationale")
        if getattr(args, name) is None
    ]
    if missing:
        parser.error(
            "missing required arguments: " + ", ".join(f"--{m}" for m in missing)
        )

    extra = None
    if args.extra:
        try:
            extra = json.loads(args.extra)
        except json.JSONDecodeError as exc:
            parser.error(f"--extra is not valid JSON: {exc}")
        if not isinstance(extra, dict):
            parser.error("--extra must be a JSON object")
    if args.receipt_path:
        extra = dict(extra or {})
        extra.setdefault("receipt_path", args.receipt_path)

    try:
        if args.provisional:
            entry = stage_provisional(
                lead=args.lead, kind=args.kind, item=args.item,
                rationale=args.rationale, extra=extra, ttl_hours=args.ttl_hours,
            )
            print(json.dumps({"ok": True, "provisional": entry,
                              "id": entry["id"]}, ensure_ascii=False))
            return 0
        entry = append_canon(
            lead=args.lead,
            kind=args.kind,
            item=args.item,
            rationale=args.rationale,
            extra=extra,
        )
    except ValueError as exc:
        print(f"reject: {exc}", file=sys.stderr)
        return 2

    landed = "provisional" if entry.get("provisional") else "appended"
    print(json.dumps({"ok": True, landed: entry, "id": entry["id"]},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
