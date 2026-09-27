#!/usr/bin/env python3
"""
receipt_check.py — the deterministic proof gate for M3 trial work.

Rule (m3-trial-mode, Corey 2026-09-27): every factual claim carries a source URL
or an on-disk receipt, and nothing is reported done without evidence.

A build/research run writes a CLAIMS LEDGER next to its artifact:

    <artifact>.claims.json   (a JSON list)   or   *.claims.jsonl (one object per line)
    [{"claim": "Stripe charges 2.9% + 30c for US cards",
      "evidence": "https://stripe.com/pricing",
      "kind": "url"},
     {"claim": "Landing page is live on port 5101",
      "evidence": "deliverables/build-1/curl-5101.txt",
      "kind": "receipt"},
     {"claim": "Build #1 shipped",
      "evidence": "memories/identity/build-1-ship-evidence/receipt.txt",
      "kind": "receipt"}]

This tool checks STRUCTURE, offline (it never fetches a URL; a verifier agent
reads the source when content-support must be confirmed):
  - every entry has a non-empty claim and evidence
  - "url"     evidence is an absolute http(s) URL with a host (no placeholders)
  - "receipt" evidence is a path that exists under the civ root and is non-empty
  - the civ's own completion claims ("done", "shipped", "is live", "deployed", "sent",
    "delivered") MUST use an on-disk receipt, not a URL
  - kind is inferred when omitted (http(s) -> url, else receipt)

Exit 0 = every claim evidenced. Exit 1 = at least one unevidenced claim (listed).
Exit 2 = ledger unreadable. Output is short and meant to be quoted verbatim.

    python3 tools/receipt_check.py deliverables/build-1/report.claims.json [--root DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

# The civ's OWN completion claims ("it's live", "I sent it"). Deliberately narrow: words
# like "published" or "completed" also describe ordinary sourced facts about the world.
DONE_WORDS = re.compile(r"\b(done|shipped|is live|went live|deployed|sent|delivered)\b", re.I)
PLACEHOLDER = re.compile(r"(<[^>]+>|\$\{[^}]+\}|\bexample\.(com|org|net)\b)", re.I)
PLACEHOLDER_WORD = re.compile(r"\b(TODO|TBD|XXX|FIXME)\b")


def load_ledger(p: Path) -> list[dict]:
    text = p.read_text()
    if p.suffix == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("claims", [])
    if not isinstance(data, list):
        raise ValueError("ledger must be a list or {'claims': [...]}")
    return data


def check_entry(e: dict, root: Path) -> str | None:
    if not isinstance(e, dict):
        return "entry is not an object"
    claim = str(e.get("claim", "")).strip()
    ev = str(e.get("evidence", "")).strip()
    if not claim:
        return "empty claim"
    if not ev:
        return "no evidence"
    if PLACEHOLDER.search(ev) or PLACEHOLDER_WORD.search(ev):
        return f"placeholder evidence '{ev[:80]}'"
    kind = e.get("kind") or ("url" if ev.lower().startswith(("http://", "https://")) else "receipt")
    if kind == "url":
        u = urlparse(ev)
        if u.scheme not in ("http", "https") or not u.netloc or "." not in u.netloc:
            return f"malformed url '{ev[:80]}'"
        if DONE_WORDS.search(claim):
            return "completion claim needs an on-disk receipt, not a URL"
        return None
    if kind == "receipt":
        p = Path(ev)
        p = p if p.is_absolute() else root / p
        try:
            p.resolve().relative_to(root.resolve())
        except ValueError:
            return f"receipt outside civ root '{ev[:80]}'"
        if not p.exists():
            return f"receipt missing '{ev[:80]}'"
        if p.is_file() and p.stat().st_size == 0:
            return f"receipt empty '{ev[:80]}'"
        if p.is_dir() and not any(p.iterdir()):
            return f"receipt dir empty '{ev[:80]}'"
        return None
    return f"unknown kind '{kind}'"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ledger")
    ap.add_argument("--root", default=os.environ.get("CIV_ROOT") or str(Path(__file__).resolve().parent.parent))
    a = ap.parse_args(argv)
    root = Path(a.root)
    lp = Path(a.ledger)
    lp = lp if lp.is_absolute() else root / lp
    try:
        entries = load_ledger(lp)
    except (OSError, ValueError) as e:
        print(f"RECEIPT-CHECK ERROR: cannot read ledger {a.ledger}: {e}")
        return 2
    if not entries:
        print(f"RECEIPT-CHECK FAIL: {a.ledger} has 0 claims (an empty ledger proves nothing)")
        return 1
    bad = []
    for i, e in enumerate(entries, 1):
        why = check_entry(e, root)
        if why:
            bad.append(f"  #{i}: {why} :: {str(e.get('claim', ''))[:100] if isinstance(e, dict) else ''}")
    n_url = sum(1 for e in entries if isinstance(e, dict) and str(e.get("evidence", "")).lower().startswith("http"))
    if bad:
        print(f"RECEIPT-CHECK FAIL: {len(bad)}/{len(entries)} claims unevidenced in {a.ledger}")
        print("\n".join(bad))
        return 1
    print(f"RECEIPT-CHECK PASS: {len(entries)}/{len(entries)} claims evidenced "
          f"({n_url} source URLs, {len(entries) - n_url} on-disk receipts) in {a.ledger}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
