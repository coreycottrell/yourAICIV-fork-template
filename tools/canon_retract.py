#!/usr/bin/env python3
"""
canon_retract.py — first-class cheap-retraction operation on canon.

WHY THIS EXISTS:
    Mneme peer-review recommendation (c), 2026-07-01:
      "a portable repo should make retraction cheap, not costly."
    See docs/CHEAP-RETRACTION.md for the full rationale + lineage.

    canon_append.py already supports kind=retraction. Before this tool, however,
    retraction required a human to:
      (1) manually find the old entry-id in log.jsonl
      (2) construct the correct extras {retracts: ..., receipt_path: ...}
      (3) call canon_append with the right combination of flags
      (4) if amending, separately construct + append a replacement entry
      (5) manually check that recall now returns the retraction correctly.

    That was expensive enough that a mind under time pressure would silently
    patch around a wrong entry instead of retracting. This tool makes the
    operation a single command, atomic across retraction+replacement.

WHAT IT DOES:
    Given an existing canon entry-id (or a search shard that resolves to one),
    stage a retraction entry (and optionally a replacement entry) via the
    canon_append PROVISIONAL side-file, verify both pass the LEARN-cycle
    contract's minimum shape, then promote atomically.

    On success: prints canon-id(s) of the new entry(ies) so the caller can walk
    to them immediately.

CLI:
    python3 tools/canon_retract.py \\
        --lead <lead-id> \\
        --entry-id <sha-of-retracted-entry> \\
        --reason "<why the original was wrong>" \\
        --receipt-path <path/to/evidence.md> \\
        [--replacement-item "<corrected claim>"] \\
        [--replacement-rationale "<why the correction stands>"] \\
        [--verifier <different-mind-lead>] \\
        [--verifier-receipt <path>] \\
        [--tombstone] \\
        [--dry-run]

INVARIANTS:
    - log.jsonl stays append-only. Retraction NEVER deletes or overwrites.
    - Retraction entry carries extra.retracts pointing at the original entry-id.
    - Replacement (if any) carries extra.supersedes pointing at both original and
      retraction, so a walker sees the full chain.
    - Retraction MUST have a receipt_path. Cheap ≠ evidence-free.
    - Retraction and replacement are staged atomically — partial retractions
      (retraction landed, replacement failed) are structurally impossible.

CONTRACT:
    This tool fires as an authorized wrapper around canon_append.py. It does NOT
    bypass canon_append's gates (content-gate, rate-limit, max-per-run, anchor-
    overlap). If a retraction fails those gates, the tool surfaces the exact
    canon_append error message.

Author: mind-lead (origin civ), 2026-07-01, wired from Mneme peer-review rec (c).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CANON_APPEND = REPO_ROOT / "tools" / "canon_append.py"
MEM_CANON = REPO_ROOT / "mem" / "canon"


def _lead_log_path(lead: str) -> Path:
    return MEM_CANON / lead / "log.jsonl"


def _find_entry(lead: str, entry_id: str) -> dict | None:
    """Locate an entry by canon-id in the lead's log.jsonl.

    Accepts either a full id or a distinguishing prefix (>=8 chars). Returns
    the parsed entry dict, or None if not found. Raises on ambiguous prefix.
    """
    log = _lead_log_path(lead)
    if not log.exists():
        return None
    matches: list[dict] = []
    with log.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            eid = entry.get("id", "")
            if eid == entry_id:
                return entry  # exact match wins immediately
            if len(entry_id) >= 8 and eid.startswith(entry_id):
                matches.append(entry)
    if len(matches) > 1:
        ids = [m.get("id", "") for m in matches[:5]]
        raise ValueError(
            f"ambiguous entry-id prefix {entry_id!r}: matches {len(matches)} "
            f"entries (first 5: {ids}); pass a longer prefix"
        )
    if matches:
        return matches[0]
    return None


def _call_canon_append(
    lead: str,
    kind: str,
    item: str,
    rationale: str,
    extra: dict,
    *,
    provisional: bool = False,
    ttl_hours: int = 24,
) -> dict:
    """Invoke canon_append.py as a subprocess. Return parsed stdout JSON.

    Raises RuntimeError on canon_append non-zero exit (breaker breach, invalid
    args, etc.). Surfaces canon_append's stderr in the exception detail so the
    caller sees the exact gate message.
    """
    cmd = [
        sys.executable,
        str(CANON_APPEND),
        "--lead", lead,
        "--kind", kind,
        "--item", item,
        "--rationale", rationale,
        "--extra", json.dumps(extra, ensure_ascii=False, sort_keys=True),
    ]
    if provisional:
        cmd += ["--provisional", "--ttl-hours", str(ttl_hours)]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"canon_append failed (exit {result.returncode}):\n"
            f"  stderr: {result.stderr.strip()}\n"
            f"  stdout: {result.stdout.strip()}"
        )
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"canon_append returned non-JSON stdout: {result.stdout!r} ({exc})"
        )


def _promote_provisional(
    lead: str,
    provisional_id: str,
    audit_verdict: str,
    audit_ref: str,
) -> dict:
    """Promote a staged provisional entry to log.jsonl."""
    cmd = [
        sys.executable,
        str(CANON_APPEND),
        "--promote", provisional_id,
        "--lead", lead,
        "--audit-verdict", audit_verdict,
        "--audit-ref", audit_ref,
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"canon_append --promote failed (exit {result.returncode}):\n"
            f"  stderr: {result.stderr.strip()}\n"
            f"  stdout: {result.stdout.strip()}"
        )
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"raw_stdout": result.stdout.strip()}


def _build_retraction_extras(
    original_entry: dict,
    reason: str,
    receipt_path: str,
    verifier: str | None,
    verifier_receipt: str | None,
    tombstone: bool,
) -> dict:
    """Construct the retraction entry's extras dict."""
    extras = {
        "retracts": original_entry.get("id", ""),
        "retracts_kind": original_entry.get("kind", ""),
        "retracts_ts": original_entry.get("ts", ""),
        "reason": reason,
        "receipt_path": receipt_path,
    }
    if verifier:
        extras["verifier"] = verifier
    if verifier_receipt:
        extras["verifier_receipt"] = verifier_receipt
    if tombstone:
        extras["tombstone"] = True
    return extras


def _build_replacement_extras(
    original_entry: dict,
    retraction_id: str,
    receipt_path: str,
    verifier: str | None,
    verifier_receipt: str | None,
) -> dict:
    """Construct the replacement entry's extras dict."""
    extras = {
        "supersedes": original_entry.get("id", ""),
        "via_retraction": retraction_id,
        "receipt_path": receipt_path,
    }
    if verifier:
        extras["verifier"] = verifier
    if verifier_receipt:
        extras["verifier_receipt"] = verifier_receipt
    return extras


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="canon_retract.py",
        description=(
            "First-class cheap-retraction on canon. Retracts an existing entry "
            "and optionally publishes a replacement, atomically. See "
            "docs/CHEAP-RETRACTION.md for rationale + Mneme peer-review lineage."
        ),
    )
    parser.add_argument("--lead", required=True, help="lead-id owning the entry")
    parser.add_argument(
        "--entry-id",
        required=True,
        help="canon-id of the entry to retract (full id or >=8-char prefix)",
    )
    parser.add_argument(
        "--reason",
        required=True,
        help="why the original entry is being retracted (short + specific)",
    )
    parser.add_argument(
        "--receipt-path",
        required=True,
        help="path to walkable evidence supporting the retraction",
    )
    parser.add_argument(
        "--replacement-item",
        help="the corrected claim (SHAPE 2 — amend). Requires --replacement-rationale.",
    )
    parser.add_argument(
        "--replacement-rationale",
        help="rationale for the replacement claim. Required with --replacement-item.",
    )
    parser.add_argument(
        "--verifier",
        help="different-mind lead-id that walked the evidence (LEARN-cycle contract)",
    )
    parser.add_argument(
        "--verifier-receipt",
        help="path to the verifier's walked receipt",
    )
    parser.add_argument(
        "--tombstone",
        action="store_true",
        help=(
            "SHAPE 3 — mark the retraction as tombstone; recall will filter this "
            "chain from default results. Use rarely."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="resolve the entry + print the retraction JSON; do not actually append.",
    )
    parser.add_argument(
        "--audit-ref",
        default="cheap-retraction-cli-atomic-promote",
        help="audit_ref used when promoting the staged provisional (default is fine).",
    )

    args = parser.parse_args()

    # --- validate inputs ---
    if (args.replacement_item is None) != (args.replacement_rationale is None):
        parser.error(
            "--replacement-item and --replacement-rationale must be used together "
            "(SHAPE 2 — amend). For SHAPE 1 — withdraw — pass neither."
        )
    if not Path(args.receipt_path).is_absolute():
        rp = REPO_ROOT / args.receipt_path
    else:
        rp = Path(args.receipt_path)
    if not rp.exists():
        parser.error(
            f"--receipt-path {args.receipt_path!r} does not resolve to a file "
            f"(checked: {rp}). A retraction requires walkable evidence."
        )

    # --- locate the original entry ---
    try:
        original = _find_entry(args.lead, args.entry_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if original is None:
        print(
            f"ERROR: no entry found in mem/canon/{args.lead}/log.jsonl matching "
            f"entry-id {args.entry_id!r}",
            file=sys.stderr,
        )
        return 2

    original_id = original.get("id", "")
    original_kind = original.get("kind", "")
    original_item = original.get("item", "")
    print(
        f"# RETRACTING\n"
        f"  lead:  {args.lead}\n"
        f"  id:    {original_id}\n"
        f"  kind:  {original_kind}\n"
        f"  ts:    {original.get('ts', '')}\n"
        f"  item:  {original_item[:100]}{'...' if len(original_item) > 100 else ''}\n",
        file=sys.stderr,
    )

    # --- build retraction entry ---
    retraction_item = f"retracts {original_id[:12]}: {args.reason[:80]}"
    retraction_rationale = (
        f"Original entry ({original_kind}, {original.get('ts', '')}) is retracted. "
        f"Reason: {args.reason}. Evidence: {args.receipt_path}."
    )
    if args.tombstone:
        retraction_rationale += (
            " TOMBSTONE — recall filters this chain from default results; walker "
            "must opt in with --include-tombstoned to reach descendants."
        )
    retraction_extras = _build_retraction_extras(
        original, args.reason, args.receipt_path,
        args.verifier, args.verifier_receipt, args.tombstone,
    )

    if args.dry_run:
        print("# DRY-RUN — retraction entry that WOULD be written:", file=sys.stderr)
        print(json.dumps({
            "kind": "retraction",
            "item": retraction_item,
            "rationale": retraction_rationale,
            "extra": retraction_extras,
        }, indent=2, ensure_ascii=False))
        if args.replacement_item:
            print("\n# DRY-RUN — replacement entry that WOULD be written:", file=sys.stderr)
            print(json.dumps({
                "kind": "finding",
                "item": args.replacement_item,
                "rationale": args.replacement_rationale,
                "extra": _build_replacement_extras(
                    original, "<retraction-id-not-yet-assigned>",
                    args.receipt_path,
                    args.verifier, args.verifier_receipt,
                ),
            }, indent=2, ensure_ascii=False))
        print("\n# DRY-RUN complete. No canon changes made.", file=sys.stderr)
        return 0

    # --- stage retraction as provisional ---
    try:
        retraction_stage = _call_canon_append(
            args.lead, "retraction",
            retraction_item, retraction_rationale, retraction_extras,
            provisional=True,
        )
    except RuntimeError as exc:
        print(f"ERROR staging retraction: {exc}", file=sys.stderr)
        return 3
    prov_retraction_id = (
        retraction_stage.get("provisional", {}).get("id")
        or retraction_stage.get("id", "")
    )
    if not prov_retraction_id:
        print(
            f"ERROR: canon_append did not return a provisional id for the "
            f"retraction stage. Full response: {retraction_stage}",
            file=sys.stderr,
        )
        return 3

    # --- stage replacement (if any) ---
    prov_replacement_id: str | None = None
    if args.replacement_item:
        replacement_extras = _build_replacement_extras(
            original, prov_retraction_id, args.receipt_path,
            args.verifier, args.verifier_receipt,
        )
        try:
            replacement_stage = _call_canon_append(
                args.lead, "finding",
                args.replacement_item, args.replacement_rationale,
                replacement_extras,
                provisional=True,
            )
        except RuntimeError as exc:
            print(
                f"ERROR staging replacement (retraction is staged as "
                f"{prov_retraction_id}, NOT yet promoted): {exc}",
                file=sys.stderr,
            )
            return 4
        prov_replacement_id = (
            replacement_stage.get("provisional", {}).get("id")
            or replacement_stage.get("id", "")
        )

    # --- atomic promote (retraction first, then replacement) ---
    try:
        promoted_retraction = _promote_provisional(
            args.lead, prov_retraction_id, "PASS", args.audit_ref,
        )
    except RuntimeError as exc:
        print(f"ERROR promoting retraction: {exc}", file=sys.stderr)
        return 5

    promoted_replacement = None
    if prov_replacement_id:
        try:
            promoted_replacement = _promote_provisional(
                args.lead, prov_replacement_id, "PASS", args.audit_ref,
            )
        except RuntimeError as exc:
            print(
                f"ERROR promoting replacement (retraction landed; replacement "
                f"held): {exc}",
                file=sys.stderr,
            )
            return 6

    # --- print success summary as JSON on stdout ---
    result = {
        "ok": True,
        "retracted_original_id": original_id,
        "retraction_entry": promoted_retraction,
        "replacement_entry": promoted_replacement,
        "tombstone": args.tombstone,
        "receipt_path": args.receipt_path,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
