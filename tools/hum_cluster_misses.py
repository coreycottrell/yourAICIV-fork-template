#!/usr/bin/env python3
"""hum_cluster_misses.py — the HUM weakness-mining CLUSTER organ.

WHY THIS EXISTS (mind-lead, 2026-06-25; Self-Harness adoption #2 from mind-lead's own deep review):
  HUM's weakness-mining is ANECDOTAL. Every boop it emits >=1 `find_the_miss` across 9 surfaces
  (over-deference / doc-not-updated / discipline-skip / dropped-balls / un-wired / claim-not-walked /
  shortcut / ...), a per-INSTANCE hunt. There has been NO organ that AGGREGATES those find-the-miss
  rows across boops into a SIGNATURE, orders by SUPPORT, and escalates ONLY a recurring CLUSTER (not
  a one-off) into a real proposal. A one-off miss is noise; a CLUSTER of >=N at the same signature is
  a structural weakness worth a build. This organ is that aggregator.

WHAT IT IS:
  φ = (surface, defect-class, mechanism) — a 3-tuple SIGNATURE per find-the-miss entry.
    - surface       = HUM's own surface tag (the `surface=...` field on each find_the_miss line).
    - defect-class  = the verb-dimension the miss hit (DECIDE / KNOW / VERIFY / LEARN / CEO-ROUTING /
                      HONESTY / GROUNDING-RECEIPT) — taken from the self_evolution_feedback (VERB) label
                      co-located in the same verdict block (the dimension HUM itself named for the miss).
    - mechanism     = a coarse normalized phrase distilled from the find_the_miss prose (e.g.
                      "deferred-reversible-to-human", "stale-workboard", "skipped-grounding-floor").
                      Mechanism is the HOW; it disambiguates two misses on the same surface+class that
                      are actually different failures.

  GROUP by φ. ORDER by support (count). PRINT:
    - clusters with support >= ESCALATE_MIN (default 2)  -> ESCALATION CANDIDATES (recurring weakness
      worth a real proposal).
    - clusters with support 1                            -> ONE-OFFS (recorded, NOT escalated; the
      potemkin guard — a single instance is not a structural weakness).

INVARIANTS:
  - READ-ONLY on the ledger. Writes NOTHING to the ledger. Emits its report to stdout (or a path you
    name with --out, which it CREATES, never the ledger).
  - ADDITIVE. This organ does NOT touch session_review.py or hum.js. It does not re-tune any of the
    4 live HUM hard-fail gates (BLOCK-NO-WWCW / GROUNDING-COMPLETENESS / SPRINT-MODE-READ / HAIKU-PER-DOC).
    It READS the ledger those gates wrote; it is an analysis organ, not a gate.
  - SUGGEST-never-MUTATE (audit-doctrine): an escalation candidate is a SUGGESTION for mind-lead to
    turn into a proposal — this organ never files the proposal itself, never mutates canon.

USAGE:
  python3 tools/hum_cluster_misses.py                 # scan all daily ledgers, human report
  python3 tools/hum_cluster_misses.py --json          # machine-readable
  python3 tools/hum_cluster_misses.py --min 3         # escalate only clusters with support >=3
  python3 tools/hum_cluster_misses.py --days 7        # only the last 7 day-files
  python3 tools/hum_cluster_misses.py --ledger-dir <path>

Owner: mind-lead (HUM + memory-substrate territory, CLAUDE.md v3.6.3).
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

# ---------------------------------------------------------------------------
# Canonical paths (origin-civ layout — repo-root-relative).
# Portability (taught upstream 2026-07-04 from origin civ A-C-Gee):
#   override via env var HUM_LEDGER_DIR or --ledger-dir. The default matches
#   the origin civ's mind-lead memory tree; a fork with a different VP roster
#   just points it wherever its HUM daily ledgers actually live.
# ---------------------------------------------------------------------------
_THIS = os.path.abspath(__file__)
_REPO_ROOT = os.path.dirname(os.path.dirname(_THIS))  # tools/ -> repo root
DEFAULT_LEDGER_DIR = os.environ.get(
    "HUM_LEDGER_DIR",
    os.path.join(_REPO_ROOT, ".claude", "team-leads", "mind", "memory", "hum-ledger-daily"),
)

ESCALATE_MIN_DEFAULT = 2

# A verdict block opens with a timestamped H2:  "## 2026-06-25T14:07:21Z — verdict: LOW"
VERDICT_HDR_RE = re.compile(r"^##\s+(?P<ts>\S+)\s+—\s+verdict:\s+(?P<verdict>\w+)", re.IGNORECASE)
# The find_the_miss line ONLY (anchored on the literal field prefix so a stray "surface="
# inside a trend/repair line can never masquerade as the miss):
#   "- find_the_miss: found=true surface=over-deference walked=true — <prose>"
# The surface token can be MULTI-WORD ("un-wired capability", "dropped balls"); we capture up
# to ` walked=` (or end) then canonicalize to the known 9-surface taxonomy below.
# Surface is one-or-more hyphenated words ("over-deference", "un-wired capability",
# "dropped balls"). We capture greedily up to ` walked=` (the always-present next field)
# so a hyphen inside the surface tag can never be mistaken for the prose em-dash. The prose
# separator is the em-dash "—" specifically (NOT the ASCII hyphen, which lives inside tags).
FIND_MISS_RE = re.compile(
    r"^[-*\s]*find_the_miss:\s*found=(?P<found>\w+)\s+"
    r"surface=(?P<surface>[a-z0-9][a-z0-9 -]*?)\s+walked=(?P<walked>\w+)"
    r"\s*(?:—\s*(?P<prose>.*))?$",
    re.IGNORECASE,
)

# Canonical surface taxonomy (HUM's 9 find-the-miss surfaces, normalized). A raw surface
# token is matched against these; multi-word raw tags ("un-wired capability") collapse to
# the canonical tag ("un-wired"). An unrecognized surface is kept verbatim (lower, hyphenated)
# so a NEW surface is visible, never silently merged.
CANONICAL_SURFACES = [
    "over-deference", "doc-not-updated", "discipline-skip", "dropped-balls",
    "un-wired", "claim-not-walked", "shortcut", "vp-amnesia", "dropped-ball",
]


def canon_surface(raw: str) -> str:
    s = (raw or "").strip().lower()
    s = re.sub(r"\s+", "-", s)  # "dropped balls" -> "dropped-balls"
    for c in CANONICAL_SURFACES:
        if s == c or s.startswith(c + "-"):
            return c
    # "un-wired-capability" -> "un-wired"; "dropped-balls"/"dropped-ball" stay as-is
    if s.startswith("un-wired"):
        return "un-wired"
    if s.startswith("dropped"):
        return "dropped-balls"
    return s
# The self_evolution_feedback verb dimension:  "- self_evolution_feedback (DECIDE): ..."
SELF_EVO_RE = re.compile(r"self_evolution_feedback\s*\((?P<verb>[A-Z][A-Z-]*)\)")
# The dimensions line carries each verb's PASS/PARTIAL/LOW:  "- dimensions: KNOW=PASS · DECIDE=LOW · ..."
DIMENSIONS_RE = re.compile(r"dimensions:\s*(?P<body>.+)$")


# ---------------------------------------------------------------------------
# Mechanism distillation: map the free-text prose of a miss to a coarse, stable
# mechanism phrase. The patterns are ordered; first match wins. This is the HOW
# axis of the signature — it separates two misses on the same surface that are
# actually different failures (e.g. a stale-WORKBOARD doc-miss vs a stale-pointer
# doc-miss). Conservative + transparent: an unmatched prose falls to "unclassified"
# so a new mechanism is visible, never silently merged into a wrong bucket.
# ---------------------------------------------------------------------------
MECHANISM_PATTERNS = [
    # over-deference family
    ("deferred-reversible-to-human",
     r"\b(your call|awaiting (corey|your)|for your (review|approval)|say the word|"
     r"yours to decide|your (nod|steer)|defer|deferr|present(ed|ing)?[- ]for|"
     r"not one i'?ll make|hand[- ]?back)\b"),
    # doc-currency family
    ("stale-workboard",
     r"\bWORKBOARD\b"),
    ("stale-devlog",
     r"\bdevlog\b"),
    ("stale-pointer-or-index",
     r"\b(stale pointer|MEMORY\.md|carry[- ]forward|cite[s]? (the )?missing|stale .*ref)\b"),
    ("doc-not-reconciled-generic",
     r"\b(stale|not (updated|reconciled)|un-?logged|did not reconcile)\b"),
    # discipline-skip family
    ("skipped-grounding-floor",
     r"\b(grounding (floor|contract|boop)|/sprint-mode|load[- ]verify|synthesis|"
     r"re-?ground|haiku)\b"),
    ("lying-checklist-or-receipt",
     r"\b(lying[- ]?check|checklist (saved|absent)|claimed .* but .* absent|cursor stayed)\b"),
    # dropped-balls / verify family
    ("unverified-delivery-or-claim",
     r"\b(verify|delivery|did it land|confirmation rides|drop(ped)?[- ]ball|sacred)\b"),
    # un-wired / capability family
    ("on-disk-not-wired",
     r"\b(un-?wired|on-?disk\s*(!=|≠|not)\s*loaded|no .*-mastery|not wired into|"
     r"survives? a clear|R13)\b"),
    # claim-not-walked
    ("claim-without-walk",
     r"\b(claim[- ]not[- ]walked|no .*walk|asserted without|unverified causal)\b"),
]
MECHANISM_COMPILED = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in MECHANISM_PATTERNS]


def distill_mechanism(prose: str) -> str:
    if not prose:
        return "unclassified"
    for name, rx in MECHANISM_COMPILED:
        if rx.search(prose):
            return name
    return "unclassified"


def parse_ledger_file(path: str):
    """Parse one daily ledger into a list of miss-entry dicts.

    Each entry carries: ts, verdict, surface, walked, defect_class (verb), mechanism,
    prose (trimmed), source_file. The defect_class is resolved from the
    self_evolution_feedback verb of the SAME verdict block (HUM's own naming of which
    verb the miss hit); falls back to the worst-graded dimension on the dimensions line,
    then "unknown".
    """
    entries = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except (OSError, UnicodeDecodeError):
        return entries

    cur_ts = None
    cur_verdict = None
    cur_block = []  # accumulate raw lines of the current verdict block

    def flush(block, ts, verdict):
        if not block:
            return
        # Find the find_the_miss line + the verb dimension within this block.
        miss = None
        verb = None
        worst_dim = None
        for ln in block:
            m = FIND_MISS_RE.match(ln.strip())
            if m and m.group("found").lower() == "true":
                miss = m
            ev = SELF_EVO_RE.search(ln)
            if ev:
                verb = ev.group("verb").upper()
            dm = DIMENSIONS_RE.search(ln)
            if dm and worst_dim is None:
                # pick the worst-graded verb on the dimensions line as a fallback class
                pairs = re.findall(r"([A-Z][A-Z-]*)=(\w+)", dm.group("body"))
                rank = {"LOW": 0, "HOLLOW": 0, "PARTIAL": 1, "PASS": 2}
                bad = [(v, rank.get(g.upper(), 3)) for v, g in pairs]
                bad = [v for v, r in bad if r <= 1]  # LOW/HOLLOW/PARTIAL only
                if bad:
                    worst_dim = bad[0]
        if not miss:
            return
        surface = canon_surface(miss.group("surface"))
        walked = (miss.group("walked") or "").lower() == "true"
        prose = (miss.group("prose") or "").strip()
        defect_class = verb or worst_dim or "UNKNOWN"
        mechanism = distill_mechanism(prose)
        entries.append({
            "ts": ts,
            "verdict": (verdict or "").upper(),
            "surface": surface,
            "walked": walked,
            "defect_class": defect_class,
            "mechanism": mechanism,
            "prose": prose[:240],
            "source_file": os.path.basename(path),
        })

    for ln in lines:
        hdr = VERDICT_HDR_RE.match(ln)
        if hdr:
            flush(cur_block, cur_ts, cur_verdict)
            cur_ts = hdr.group("ts")
            cur_verdict = hdr.group("verdict")
            cur_block = []
            continue
        if cur_ts is not None:
            cur_block.append(ln)
    flush(cur_block, cur_ts, cur_verdict)
    return entries


def collect_entries(ledger_dir: str, days: int | None):
    files = []
    if os.path.isdir(ledger_dir):
        for fn in sorted(os.listdir(ledger_dir)):
            # day-files are YYYY-MM-DD.md; skip the _archive dir + non-day files
            if re.match(r"^\d{4}-\d{2}-\d{2}\.md$", fn):
                files.append(os.path.join(ledger_dir, fn))
    if days is not None and days > 0:
        files = files[-days:]
    all_entries = []
    for path in files:
        all_entries.extend(parse_ledger_file(path))
    return all_entries, [os.path.basename(f) for f in files]


def cluster(entries, escalate_min: int):
    groups = defaultdict(list)
    for e in entries:
        phi = (e["surface"], e["defect_class"], e["mechanism"])
        groups[phi].append(e)
    clusters = []
    for phi, members in groups.items():
        surface, defect_class, mechanism = phi
        days_span = sorted({m["source_file"] for m in members})
        clusters.append({
            "signature": {
                "surface": surface,
                "defect_class": defect_class,
                "mechanism": mechanism,
            },
            "support": len(members),
            "distinct_days": len(days_span),
            "days": days_span,
            "verdicts": sorted({m["verdict"] for m in members}),
            "sample_prose": members[-1]["prose"],
            "escalate": len(members) >= escalate_min,
        })
    # order by support desc, then distinct_days desc, then surface for stability
    clusters.sort(key=lambda c: (-c["support"], -c["distinct_days"], c["signature"]["surface"]))
    return clusters


def render_human(clusters, escalate_min, scanned_files, total_entries):
    out = []
    out.append("=" * 78)
    out.append("HUM WEAKNESS-MINING CLUSTER ORGAN — find-the-miss aggregated by φ")
    out.append("φ = (surface, defect-class, mechanism)   |   escalate when support >= %d" % escalate_min)
    out.append("READ-ONLY on the ledger. SUGGEST-never-MUTATE. Additive to the 4 live HUM gates.")
    out.append("=" * 78)
    out.append("scanned %d day-file(s): %s" % (len(scanned_files), ", ".join(scanned_files)))
    out.append("parsed %d find-the-miss entr(y/ies) into %d distinct signature(s)"
               % (total_entries, len(clusters)))
    out.append("")

    escalations = [c for c in clusters if c["escalate"]]
    oneoffs = [c for c in clusters if not c["escalate"]]

    out.append("█ ESCALATION CANDIDATES (recurring weakness — worth a real proposal) — %d" % len(escalations))
    out.append("-" * 78)
    if not escalations:
        out.append("  (none — no signature recurred at support >= %d)" % escalate_min)
    for i, c in enumerate(escalations, 1):
        sig = c["signature"]
        out.append("  %d. support=%d  across %d day(s) %s  verdicts=%s"
                   % (i, c["support"], c["distinct_days"], c["days"], ",".join(c["verdicts"])))
        out.append("     φ = surface:%s | defect:%s | mechanism:%s"
                   % (sig["surface"], sig["defect_class"], sig["mechanism"]))
        out.append("     e.g. %s" % c["sample_prose"])
        out.append("")

    out.append("░ ONE-OFFS (support 1 — recorded, NOT escalated; a single instance is not a structure) — %d"
               % len(oneoffs))
    out.append("-" * 78)
    for c in oneoffs:
        sig = c["signature"]
        out.append("  - φ = surface:%s | defect:%s | mechanism:%s   (%s)"
                   % (sig["surface"], sig["defect_class"], sig["mechanism"], c["days"][0]))
    out.append("")
    out.append("END — %d escalation candidate(s), %d one-off(s). "
               "Escalations are SUGGESTIONS for mind-lead; this organ files no proposal + mutates no canon."
               % (len(escalations), len(oneoffs)))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="HUM find-the-miss cluster organ (read-only).")
    ap.add_argument("--ledger-dir", default=DEFAULT_LEDGER_DIR,
                    help="dir of daily HUM ledgers (default: mind-lead's hum-ledger-daily/)")
    ap.add_argument("--min", dest="min_support", type=int, default=ESCALATE_MIN_DEFAULT,
                    help="minimum support to ESCALATE a cluster (default 2)")
    ap.add_argument("--days", type=int, default=None,
                    help="only the last N day-files (default: all)")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON output")
    ap.add_argument("--out", default=None,
                    help="write report to this path (NEVER the ledger); default stdout")
    args = ap.parse_args()

    entries, scanned = collect_entries(args.ledger_dir, args.days)
    clusters = cluster(entries, args.min_support)

    if args.json:
        payload = {
            "ledger_dir": args.ledger_dir,
            "scanned_files": scanned,
            "escalate_min": args.min_support,
            "total_entries": len(entries),
            "distinct_signatures": len(clusters),
            "escalation_candidates": [c for c in clusters if c["escalate"]],
            "one_offs": [c for c in clusters if not c["escalate"]],
        }
        text = json.dumps(payload, indent=2)
    else:
        text = render_human(clusters, args.min_support, scanned, len(entries))

    if args.out:
        # The --out path is the report; it is NEVER the ledger. Guard against it.
        if os.path.abspath(args.out).startswith(os.path.abspath(args.ledger_dir)):
            print("REFUSED: --out must not write inside the ledger dir (read-only invariant).",
                  file=sys.stderr)
            return 2
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("wrote report -> %s" % args.out)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
