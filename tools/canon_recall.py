#!/usr/bin/env python3
"""canon_recall.py — structured recall surface for the canon substrate.

OWNED BY: mind-lead (memory-substrate owner) per CLAUDE.md v3.6.3 §MEMORY-SUBSTRATE OWNERSHIP.

CHANGELOG
  2026-06-21 (mind-lead, COLD-RECONSTITUTION FIX — P2.1 / Phase-2A — backup
    canon_recall.py.bak.20260621T223704Z-pre-cold-recency-boost; WWCW verdict=ACT,
    reversible build per BUILD-DOC §REVERSIBILITY contract):
    - WHY (the 0.0052 / T0A.3 cold-recall FAIL): a cleared mind's OWN
      just-appended close-out canon entry did NOT surface top-3 on a fresh cold
      recall. DIAGNOSED LIVE (not assumed) — TWO root causes, both structural:
        (1) NO RECENCY TERM in the score. The fusion score had zero recency
            signal — a fresh day-one entry competed purely on lexical+vector
            overlap against the whole ~1.5k-entry trunk. The freshness GATE only
            FLAGGED staleness AFTER ranking; nothing PROMOTED recency into top-k.
            A fresh entry ranked #133 on a generic query.
        (2) RRF RANK-FLATTENING drowned a DOMINANT lexical match. Pure RRF uses
            only the RANK (1/(60+rank)), discarding the lexical-score MAGNITUDE.
            A just-written entry that was the #1 lexical hit by 3.8x (0.857 vs
            0.226 next) collapsed to the flat rank-1 floor 0.0164 — and was then
            OUT-RANKED by mediocre entries that merely appeared in BOTH retrievers
            (cross-confirm ~0.033 > a lone dominant lexical 0.0164). The best
            match for a cold mind's own hand-off-seeded query ranked #23.
    - WHAT (additive, defensive — lexical IDF scoring UNCHANGED [06-20 diary-fix
      preserved], freshness-gate UNCHANGED, write-path/canon_append UNCHANGED,
      verdict/noise-floor semantics PRESERVED [reads ORIGINAL _fusion_score]):
        * NEW LEXICAL-MAGNITUDE TERM in _fuse_rrf: a non-exact lexical hit adds
          LEXICAL_MAG_WEIGHT (0.05) × its ABSOLUTE IDF-normalized lexical score.
          ABSOLUTE (not relative-to-top) is load-bearing: relative inflated noise
          to "best-of-the-noise" and broke build-or-tombstone (caught + fixed
          mid-build — see PROBE 8). Absolute keeps noise (abs≈0.005) at +0.00025
          below the floor while a dominant match (abs≈0.86) clears it decisively.
        * NEW RECENCY RE-RANK in recall(): each hit ALREADY in the fusion pool
          (real retriever signal) gets its fusion score × _recency_multiplier()
          — ×(1+COLD_RECENCY_MAX=0.60) at age 0 decaying LINEARLY to ×1.0 at the
          kind's reverify horizon (same horizon the staleness gate uses — the
          recency BOOST and staleness DEMOTE are now symmetric). + a small
          COLD_LEAD_OWN_BONUS (0.15) when the hit is in the caller's own lead.
          NEVER invents signal for a no-overlap entry (multiplies an existing
          positive score; the verdict noise-floor still reads the ORIGINAL score).
    - BEHAVIORAL TEST (real-path, on the live trunk):
        * 5-probe cold-recall fixture (hand-off-seeded generic queries, NOT the
          entries' rarest tokens): 5/5 = 1.00 top-3 cold, lead-scoped AND
          no-lead-scope (gate ≥0.67 — DECISIVELY met). Each probe surfaces #1.
        * T0A.3: a fresh day-one entry (id 5257f16a) surfaces #1 (was #23
          lead-scoped / #133 no-scope) on a hand-off-seeded query.
        * T2.1.4 IDF no-regression: rare-token query still lands its entry #1
          as exact match. T2.1.5 BOOST-not-CRUTCH: top-3 holds WITHOUT lead-scope.
        * build-or-tombstone PRESERVED: impossible pure-hex query → verdict
          BUILD_OR_TOMBSTONE (top fusion 0.0239 < floor 0.025). PROBE 4 + PROBE 8
          restored after the absolute-vs-relative fix.
      Receipt: data/reports/phase-0a-20260621/ + DEVLOG entry P2.1.
    - HONEST RESIDUAL: a query sharing ZERO terms with a specific entry still
      cannot pinpoint THAT entry (fundamental to lexical+vector recall) — but it
      now surfaces the FRESHEST entries (recency boost), which is the correct
      cold-reconstitution behavior. Closing the zero-shared-term case fully would
      need the P3 vector-index work. T0A.3's failure mode (hand-off-seeded cold
      recall of own close-out) is CLOSED.
    - NO REGRESSION: self-test PROBES 1-13 still PASS.

  2026-06-20 (mind-lead, DIARY-PROBLEM SCORING FIX — backup
    canon_recall.py.bak.20260620T134252Z-pre-idf-scoring-fix; WWCW verdict=ACT):
    - WHY (the diary-problem / scoring drift): the lexical token-overlap term
      was FLAT — score += overlap / max(1, |q_tokens|). With no rarity
      weighting, ubiquitous civ-vocabulary tokens (skill/lead/canon/receipt/
      finding — present in nearly every entry) counted the SAME as a rare,
      discriminating token. OBSERVED on the live trunk: an all-common-token
      query produced a flat score-TIE across six topically-UNRELATED entries
      (all at 0.8000), and a vague generic-vocabulary entry ranked as high as
      a specific information-rich one. That is the diary problem made
      mechanical: a diary full of common words out-competes a precise finding.
    - WHAT (surgical, additive — ONLY lexical_search scoring touched; RRF
      fusion, freshness-gate, write-path/canon_append, verdict semantics,
      recall-hit instrumentation, tombstone/build-ticket all UNCHANGED):
        * NEW _compute_idf(entries): smoothed IDF over the corpus being
          searched. IDF(t)=ln((N+1)/(df(t)+1))+1 (sklearn-style; floor 1.0 so
          no token is zero-weighted; ubiquitous tokens collapse toward 1.0,
          rare tokens get a large multiplier). Computed once per corpus load.
        * lexical_search token-overlap term REPLACED:
            old: score += overlap / max(1, |q_tokens|)
            new: score += (Σ idf over q∩doc) / (Σ idf over q_tokens)
          Still normalized into [0,1] so exact-substring (+10) and the
          doctrine/decision tiebreakers stay correctly scaled.
    - BEHAVIORAL TEST: probe battery re-run; common-token tie BROKEN; the 5
      legacy 06-11 probes still land canon top-3 (no regression). Receipt:
      data/reports/canon-recall-scoring-fix-receipt-20260620.md.
    - NO REGRESSION: self-test PROBES 1-13 still PASS.

  2026-06-19 (mind-lead, LEARN-READ instrument — backup
    canon_recall.py.bak.20260619T163131Z-learn-read-instrument):
    - WHY: the civ measured the WRITE (canon_append fires) but not the READ. The
      build_tickets ledger logs recall MISSES; nothing logged recall HITS (which
      canon ids were actually served on a real path). A canon entry never recalled
      is a diary, not learning (LEARN deep-dive 2026-06-19).
    - WHAT (additive, defensive — verdict/return shapes + freshness-gate + sprint-1/2/3/4
      paths ALL preserved): NEW append-only ledger mem/recall_gaps/recall_hits.jsonl,
      symmetric to build_tickets. recall() gains log_hits=True (default); after the
      MISS gate, when canon entries were SERVED, _append_recall_hits() logs ONE row
      with the served canon IDs + lead + kind + staleness + rank (NOT bodies — the
      moat is preserved; only the FACT of recall is logged). result gains
      recall_hit_record. CLI gains --no-log-hits. Self-test sets env-guard
      CANON_RECALL_NO_HIT_LOG=1 so its probes never pollute the baseline.
    - CONSUMED BY: tools/learn_read_kpis.py (recall-hit-rate KPI).
    - NO REGRESSION: self-test still PASS (probes 1-13 unchanged; write-path,
      build-ticket, tombstone, freshness-gate logic untouched).

  2026-06-09 sprint-4 (mind-lead, FRESHNESS-GATE — backup
    canon_recall.py.bak.20260609T200047Z-freshness-pre2):
    - WHY: hybrid recall + closed-loop now work. But a RECALLED hit was still
      being served as fresh truth regardless of age. Stale doctrine read as
      live doctrine = the recursion shape "authored != installed" — the
      mechanism returns a result, the caller trusts it, no gate forces
      re-verify on aged knowledge. 4th of 4 memory-builds owed today per
      mind-lead handoff §MEMORY VALIDATION VERDICT.
    - WHAT (additive, defensive — write-path UNCHANGED, hybrid + tombstone
      retrievers UNCHANGED, all sprint-1/2/3 verdicts preserved):
        * Kind-aware DEFAULT policy window (configurable per-call + per-CLI):
            doctrine/decision      fresh=60d  reverify=180d (load-bearing; stale=danger)
            finding/cure/learning  fresh=14d  reverify=45d  (operational)
            handoff/session        fresh=7d   reverify=21d  (ephemeral)
            unknown                fresh=30d  reverify=90d  (sane default)
        * Each returned hit gains `staleness` ∈ {fresh, aging, stale, unknown}:
            fresh   — age <= fresh_days       → serve as truth
            aging   — fresh_days < age <= reverify_days → serve with caution
            stale   — age > reverify_days     → DO NOT trust without re-verify
            unknown — no parseable ts (rare)
        * Top-level result["freshness_gate"] (NEW field):
            policy{kind → {fresh_days, reverify_days}}
            fresh_count / aging_count / stale_count / unknown_count
            re_verify_required (bool) — true if ANY stale hit OR all hits aging
            next_move — concrete cure language for the re-verify path
        * NEVER drops stale hits silently — they remain in result, flagged.
        * Per-call override: recall(fresh_days=N, reverify_days=N) wins over
          kind-aware defaults; per-CLI: --fresh-days N --reverify-days N.
        * --no-freshness-gate disables the gate entirely (legacy passthrough;
          result["freshness_gate"] = None).
    - GATE FIRES AT THE MECHANISM: inside recall(), AFTER fusion+filter,
      BEFORE auto-record-build-ticket. Caller cannot bypass without explicit
      opt-out. Matches the recursion-lesson shape: gate where the call
      HAPPENS, not in a Primary checklist. The hook IS the mechanism.
    - SELF-TEST adds PROBE 11 (kind-aware policy applied + per-hit staleness)
      and PROBE 12 (synthetic stale entry triggers re_verify_required).
      PROBES 1-10 unchanged — no-regression contract on PASSING write +
      recall paths.
    - NO REGRESSION: existing verdict logic, write-path (canon_append.py
      untouched), sprint-3 tombstone/build-ticket logic intact, max_age_days
      filter preserved (drops; freshness-gate FLAGS; orthogonal mechanisms).
    - PRE-EXISTING UNRELATED ISSUE noted (NOT introduced here, NOT in scope):
      sprint-3 PROBE 8 currently FAILS — pure-hex nonce query gets verdict=OK
      via weak lexical token-overlap, so build-ticket auto-record does not
      fire. Surfacing as residual; sprint-3 owner should harden the noise
      floor for the auto-record path. Sprint-4 PROBE 11/12 use
      record_gap=False to avoid coupling our gate-test to that flake.

  2026-06-09 sprint-3 (mind-lead, build-or-tombstone CLOSED-LOOP — backup
    canon_recall.py.bak.20260609T195741Z):
    - WHY: sprint-1+2 SET the BUILD_OR_TOMBSTONE verdict + next_move TEXT correctly,
      but the gap was NEVER RECORDED. A recall returning nothing only signalled in
      that one process's stdout — the next mind running the same query re-suffered
      the same empty. The failure mode "recall returns nothing → mind assumes
      nothing exists" was textually addressed but mechanically open.
    - WHAT (additive, write-path UNCHANGED, all existing verdict/return shapes
      PRESERVED — see PROBE 8/9/10 in self-test for no-regression on the passing
      WRITE + recall paths):
        * NEW SUBSTRATE: mem/recall_gaps/{build_tickets,tombstones}.jsonl —
          two append-only ledgers under mind-lead's memory-substrate ownership.
        * AUTO-RECORD GATE (the MECHANISM, fires in recall() after verdict
          assignment, BEFORE return): when verdict ∈ {BUILD_OR_TOMBSTONE,
          INDEX_MISSING}, append a build-ticket to build_tickets.jsonl unless
          (a) caller passed record_gap=False (self-test, idempotency-loop), or
          (b) query is too short to be meaningful (<4 chars), or
          (c) an identical query was recorded within GAP_DEDUPE_WINDOW_SEC
              (default 24h) — dedupe-by-query-hash, prevents ledger spam from
              the wheel hammering the same impossible query.
        * NEW CLI: --tombstone "query"  REASON  — append an explicit tombstone
          ("no such canon, intentionally") to tombstones.jsonl. Future recalls
          matching that query string get verdict TOMBSTONED with cite.
        * NEW VERDICT: TOMBSTONED — query matches a recorded tombstone; the
          next_move cites the tombstone reason so a future mind does NOT
          re-suffer the same empty AND does NOT auto-record a build-ticket.
        * NEW CLI: --list-tickets / --list-tombstones / --no-gap-record /
          --gap-dedupe-window-sec — operator + idempotency surfaces.
        * STRUCTURAL SAFETY (per LBI hooks-not-rules cure): gate fires at the
          MECHANISM (recall() function), NOT at Primary discipline. If the
          mechanism is bypassed (no-gap-record, dedupe-hit), there is NO claim
          that the gap was recorded — verdict text remains substrate-honest.
    - SELF-TEST (mandatory): PROBE 8 = auto-record on empty recall produces a
      ledger row, PROBE 9 = tombstone-then-recall surfaces TOMBSTONED verdict,
      PROBE 10 = dedupe prevents double-record within window. PROBES 1–7
      unchanged — no-regression contract on existing PASSING paths.

  2026-06-09 (recall-tuner, mind-lead memory recall-fix workstream 4):
    - BORN: thin CLI over semsearch + canon trunk. Build-or-tombstone verdict surface.

  2026-06-09 sprint-2 (Track A — hybrid lexical+vector, recall-fix-recall2 workstream):
    - BACKUP: tools/canon_recall.py.bak.20260609-recall2
    - WHY: sprint-1 closed the WRITE-loop drift and the search-side mechanics, but T2/T3
      auditor verdicts FAILED at default k=5:
        * T2 nonced anchor only surfaced at k>=30 (vector recall dilutes nonces).
        * T3 exact-canon-substring queries missed the target entry at top-5 (embedding
          model semantic-overlap, not ranker logic).
      These are lexical-exact cases that vector embeddings cannot fix structurally —
      no source-priority rerank can promote a doc the embedder didn't surface.
    - WHAT (additive, defensive — write-path UNCHANGED, Track A does NOT touch
      canon_append.py or the index_queue):
        * LEXICAL retriever: in-memory scan over the canon trunk (mem/canon/*/log.jsonl).
          336 entries on disk today — sub-100ms even with the whole trunk loaded. Two
          signals: (a) exact case-insensitive substring match against item+rationale (very
          high signal — a nonce query MUST hit), (b) token-overlap score for paraphrase.
        * HYBRID FUSION via Reciprocal Rank Fusion (RRF), the standard hybrid-search
          fuser. score(d) = sum_over_retrievers( 1 / (RRF_K + rank_d_in_that_retriever) ).
          Exact-substring lexical hits get an additive boost so a nonced anchor cannot be
          drowned by vector noise.
        * VERDICT semantics PRESERVED + EXTENDED:
            OK              — at least one canon hit (lexical OR vector).
            OK_FALLBACK     — only non-canon (doctrine/handoff/session) hits, OR vector-
                              only canon hits with no lexical reinforcement AND chroma
                              recently rebuilt (low-confidence flag set).
            BUILD_OR_TOMBSTONE — no canon hits anywhere. silent-empty is FORBIDDEN; this
                              verdict carries clear next_move text.
            INDEX_MISSING   — chroma path unresolved. LEXICAL still runs (so an exact
                              substring is recallable even if vector is offline). If
                              lexical hits exist, verdict downgrades to OK + a warning;
                              if neither produces hits, verdict stays BUILD_OR_TOMBSTONE.
        * canon_recall DEFAULT behavior: best-effort recall + clear low_confidence flag
          when only one retriever fired. NEVER silent-empty (build-or-tombstone
          signalling preserved).
    - SELF-TEST (mandatory per LBI discipline):
        1. canon_append a nonced "lead=recall-fix-recall2-test" entry, then recall at
           DEFAULT k=5 → nonce MUST appear in top results.
        2. Recall an EXACT substring of a real, older canon entry at DEFAULT k=5 → that
           entry MUST appear in top results.
        3. Build-or-tombstone discipline (impossible-token recall) → verdict must be
           BUILD_OR_TOMBSTONE with non-empty next_move.

What this tool answers (for any caller — VPs, audits, the 04:30Z wheel slot, Primary):
    "What does canon say about <query>? And if it says nothing, is that a gap to fill
     or a void to label?"

USAGE
  python3 tools/canon_recall.py "your query"                # default: hybrid, k=5
  python3 tools/canon_recall.py --k 10 "query"             # more results
  python3 tools/canon_recall.py --lead tgim-lead "query"   # restrict to one VP's trunk
  python3 tools/canon_recall.py --kind doctrine "query"    # filter on canon entry kind
  python3 tools/canon_recall.py --json "query"             # machine-readable
  python3 tools/canon_recall.py --max-age-days 7 "query"   # only fresh canon
  python3 tools/canon_recall.py --no-lexical "query"       # vector-only (sprint-1 mode)
  python3 tools/canon_recall.py --no-vector "query"        # lexical-only (chroma-offline)
  python3 tools/canon_recall.py --self-test                # end-to-end probe
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Add the semsearch dir to the import path so we can call search() directly.
_AICIV_ROOT = Path(__file__).resolve().parent.parent
_SEMSEARCH_DIR = _AICIV_ROOT / "projects" / "aiciv-mind" / "semsearch"
sys.path.insert(0, str(_SEMSEARCH_DIR))

try:
    import search as _search  # noqa: E402
except Exception as exc:  # pragma: no cover — semsearch missing = caller's job to fix
    _search = None
    _import_error = exc
else:
    _import_error = None


CANON_DIR = _AICIV_ROOT / "mem" / "canon"

# Build-or-tombstone defaults
DEFAULT_K = 5
DEFAULT_MAX_AGE_DAYS = None  # no freshness filter unless caller asks
NO_RESULT_VERDICT = "BUILD_OR_TOMBSTONE"

# --- Build-or-tombstone closed-loop substrate (sprint-3) --------------------
# mem/recall_gaps/ holds the append-only ledger of empty-recall events
# (build-tickets) and explicit "no such canon, intentionally" decisions
# (tombstones). mind-lead's substrate; future minds query before re-suffering.
RECALL_GAPS_DIR = _AICIV_ROOT / "mem" / "recall_gaps"
BUILD_TICKETS_PATH = RECALL_GAPS_DIR / "build_tickets.jsonl"
TOMBSTONES_PATH = RECALL_GAPS_DIR / "tombstones.jsonl"

# --- LEARN-READ instrumentation (2026-06-19, mind-lead) ---------------------
# THE READ LEDGER. The build_tickets ledger above logs recall MISSES (empty
# recalls). This ledger logs recall HITS — which canon entry ids were actually
# RECALLED-AND-SERVED on a real path. Without this, the civ measures the WRITE
# (canon_append fires) but not the READ; a canon entry never recalled is a
# diary, not learning. LEARN's true unit is the CYCLE write->recall->change->
# witness; this ledger instruments the RECALL quarter of that cycle.
# Symmetric pair: build_tickets (MISS) <-> recall_hits (HIT). Append-only;
# mind-lead's substrate; consumed by tools/learn_read_kpis.py to compute the
# recall-hit-rate KPI. Privacy-safe: logs entry IDS + verdict + staleness, NOT
# entry bodies (the moat is preserved; only the FACT of a recall is logged).
RECALL_HITS_PATH = RECALL_GAPS_DIR / "recall_hits.jsonl"

# Dedupe window: same query within N seconds → don't double-record. Prevents
# wheel-slot recurring queries from spamming the ledger. Operator-tunable.
GAP_DEDUPE_WINDOW_SEC = 24 * 3600

# Auto-record gate: skip queries shorter than this (junk noise floor).
GAP_MIN_QUERY_LEN = 4

# Hybrid retriever tunables
RRF_K = 60           # standard RRF constant (Cormack et al.)
LEXICAL_POOL = 200   # how many lexical hits to keep in the fusion pool
VECTOR_POOL_MULT = 6 # vector over-fetch: k * VECTOR_POOL_MULT (min 30)
EXACT_SUBSTRING_BOOST = 1.0   # additive bonus on the RRF score for an exact substring hit
# LEXICAL-MAGNITUDE WEIGHT (2026-06-21, P2.1): the additive weight on a
# non-exact lexical hit's ABSOLUTE IDF-normalized lexical score (NOT relative-to-
# top — see _fuse_rrf for why relative broke build-or-tombstone). Tuned so a
# DOMINANT lexical match (abs≈0.86) earns +0.043 → fusion ≈ 0.0164(rank)+0.043 =
# 0.059, comfortably above cross-confirmation (~0.033) and the noise floor
# (0.025), while PURE NOISE (abs≈0.005, the doctrine-tiebreaker floor) earns only
# +0.00025 and stays well below the floor (build-or-tombstone preserved). Far
# below the exact-match +1.0 so rare-token exact hits still win rank #1.
LEXICAL_MAG_WEIGHT = 0.05
TOKEN_RE = re.compile(r"[A-Za-z0-9_-]+")

# --- COLD-RECONSTITUTION RECENCY BOOST (2026-06-21, mind-lead, P2.1) ----------
# THE COLD-RECALL CURE. The fusion score had ZERO recency term: a fresh day-one
# entry (exactly what a cleared mind needs to recall about its own last wake)
# competes purely on lexical+vector overlap against the whole ~1.5k-entry trunk.
# On a GENERIC cold query (no rare distinguishing token) the just-written entry
# ranks #100+ — buried under older entries with higher token-overlap. The
# freshness GATE only FLAGS staleness AFTER ranking; nothing PROMOTES recency
# into the top-k. This is the 0.0052 / T0A.3 FAIL: write lands, read-back fails.
#
# THE CURE: a multiplicative recency boost on the fusion score, applied ONLY to
# hits that ALREADY have real retriever signal (a non-noise fusion_score from a
# lexical/vector match). It NEVER lifts a zero-overlap entry — the boost
# multiplies an existing positive score; a hit with no real match is not in the
# fusion pool to begin with, and the post-boost noise-floor re-check (below)
# still guards build-or-tombstone signalling. The boost is the SYMMETRIC twin of
# the staleness gate: the gate demotes stale truth, this promotes fresh truth.
#
# Magnitude: at age 0 a same-kind entry gets a multiplier of (1 + COLD_RECENCY_MAX),
# decaying LINEARLY to 1.0 (no boost) at the kind's reverify_days horizon, then
# 1.0 forever after. COLD_RECENCY_MAX is tuned so a day-zero entry with genuine
# overlap is lifted ~1-2 RRF rank-positions — enough to break the flat-tie among
# similar-overlap entries in favor of the freshest, NOT enough to out-rank an
# exact-substring match (+1.0 boost dwarfs it) or to surface a no-overlap entry.
COLD_RECENCY_MAX = 0.60      # max multiplicative uplift at age 0 (×1.60 at day 0)
COLD_LEAD_OWN_BONUS = 0.15   # extra uplift when the hit is in the caller's own lead trunk
                             # (a cold mind recalling ITS OWN close-out gets a small home boost;
                             #  only applies when lead= is set AND the hit is in that lead)


def _normalize_query(q: str) -> str:
    """Casefold + whitespace-collapse — used for dedupe + tombstone matching.

    Stable across re-runs; intentionally simple so two minds re-asking the
    "same" thing collide on the same normalized key.
    """
    return re.sub(r"\s+", " ", (q or "").strip().lower())


def _query_hash(q: str) -> str:
    """Short deterministic hash of the normalized query for dedupe lookups."""
    import hashlib
    return hashlib.sha256(_normalize_query(q).encode("utf-8")).hexdigest()[:16]


def _ensure_gaps_dir() -> None:
    """Create mem/recall_gaps/ if it doesn't exist (idempotent, no-op otherwise)."""
    RECALL_GAPS_DIR.mkdir(parents=True, exist_ok=True)


def _read_jsonl(path) -> list[dict]:
    """Read a JSONL file. Returns [] if missing or unreadable. Never raises."""
    try:
        if not path.exists():
            return []
        rows = []
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        return rows
    except Exception:
        return []


def _recent_ticket_for_query(q: str, window_sec: int) -> dict | None:
    """Return the most-recent build-ticket for this query within window_sec, or None.

    Used by the auto-record dedupe gate. Match on _query_hash for stability.
    """
    qh = _query_hash(q)
    now = dt.datetime.now(dt.timezone.utc)
    most_recent = None
    most_recent_ts = None
    for row in _read_jsonl(BUILD_TICKETS_PATH):
        if row.get("query_hash") != qh:
            continue
        ts = _parse_iso(row.get("ts", ""))
        if ts is None:
            continue
        age = (now - ts).total_seconds()
        if age <= window_sec:
            if most_recent_ts is None or ts > most_recent_ts:
                most_recent = row
                most_recent_ts = ts
    return most_recent


def _matching_tombstone(q: str) -> dict | None:
    """Return the first tombstone whose normalized query matches q, or None.

    Match semantics: exact normalized-query equality. Tombstones are explicit
    decisions; we do NOT want fuzzy matching to silently suppress real recalls.
    """
    qn = _normalize_query(q)
    for row in _read_jsonl(TOMBSTONES_PATH):
        if _normalize_query(row.get("query", "")) == qn:
            return row
    return None


def _append_build_ticket(query: str, verdict: str, warnings: list[str],
                        retrievers_fired: list[str], low_confidence: bool) -> dict:
    """Append a build-ticket row to mem/recall_gaps/build_tickets.jsonl.

    Returns the row that was written (for caller to surface).
    """
    _ensure_gaps_dir()
    row = {
        "ts": _iso_now(),
        "query": query,
        "query_hash": _query_hash(query),
        "verdict": verdict,
        "warnings": warnings,
        "retrievers_fired": retrievers_fired,
        "low_confidence": low_confidence,
        "kind": "build_ticket",
        "actor": os.environ.get("CLAUDE_AGENT_ID", "unknown"),
        "next_move": (
            "BUILD: append a canon entry via tools/canon_append.py once the work "
            "lands. TOMBSTONE: if dead, run "
            "`python3 tools/canon_recall.py --tombstone \"<query>\" \"<reason>\"`."
        ),
    }
    try:
        with BUILD_TICKETS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        row["_write_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _append_tombstone(query: str, reason: str, forward_pointer: str = "") -> dict:
    """Append a tombstone row to mem/recall_gaps/tombstones.jsonl.

    Tombstone = explicit "no such canon, intentionally — do not re-ask, here's
    why." Future recalls matching this query short-circuit to verdict TOMBSTONED.
    """
    _ensure_gaps_dir()
    row = {
        "ts": _iso_now(),
        "query": query,
        "query_hash": _query_hash(query),
        "reason": reason,
        "forward_pointer": forward_pointer,
        "kind": "tombstone",
        "actor": os.environ.get("CLAUDE_AGENT_ID", "unknown"),
    }
    with TOMBSTONES_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _append_recall_hits(query: str, final_hits: list[dict], verdict: str) -> dict:
    """Append ONE recall-hit row to mem/recall_gaps/recall_hits.jsonl.

    THE READ INSTRUMENT. Records WHICH canon entry ids were served on this real
    recall. One row per recall event (not per hit) — the row carries the list of
    served canon ids so learn_read_kpis.py can compute "of all canon entries, how
    many were ever recalled-and-served within their freshness window".

    Privacy-safe: logs ids + lead + kind + staleness + rank, NOT item/rationale
    bodies. The canon moat is preserved; only the FACT of recall is logged.

    Only canon-source hits are logged (the LEARN unit is canon recall; non-canon
    fallback hits are noise for this metric). Returns the row written.

    Env guard: if CANON_RECALL_NO_HIT_LOG is set, this is a no-op (returns an
    empty row). Used by the self-test so its probes never pollute the baseline.
    """
    if os.environ.get("CANON_RECALL_NO_HIT_LOG"):
        return {"ts": _iso_now(), "served_canon_ids": [], "_skipped": "env_guard"}
    _ensure_gaps_dir()
    served = []
    for h in final_hits:
        ce = h.get("_canon_entry") or {}
        if h.get("source") != "canon" or not ce.get("id"):
            continue
        served.append({
            "id": ce.get("id"),
            "lead": h.get("_canon_lead") or ce.get("lead") or "",
            "kind": ce.get("kind") or "",
            "rank": h.get("rank"),
            "staleness": h.get("_staleness"),
            "in_lexical": h.get("_in_lexical", False),
            "in_vector": h.get("_in_vector", False),
            "lexical_exact": h.get("_lexical_exact", False),
        })
    row = {
        "ts": _iso_now(),
        "query": query,
        "query_hash": _query_hash(query),
        "verdict": verdict,
        "served_canon_ids": [s["id"] for s in served],
        "served": served,
        "actor": os.environ.get("CLAUDE_AGENT_ID", "unknown"),
        "kind": "recall_hit",
    }
    try:
        with RECALL_HITS_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception as exc:
        row["_write_error"] = f"{type(exc).__name__}: {exc}"
    return row


def _iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _list_canon_leads() -> list[str]:
    if not CANON_DIR.is_dir():
        return []
    out = []
    for p in sorted(CANON_DIR.iterdir()):
        if not p.is_dir():
            continue
        if p.name.startswith("_") or p.name.startswith("."):
            continue
        if (p / "log.jsonl").is_file():
            out.append(p.name)
    return out


def _read_canon_entries(lead: str | None) -> list[dict]:
    """Read canon log lines as dicts. If lead=None, scan all silos.

    Each entry is decorated with _lead, _log_line, _log_path so hybrid hits look
    identical to vector hits downstream.
    """
    entries: list[dict] = []
    leads = [lead] if lead else _list_canon_leads()
    for ld in leads:
        log = CANON_DIR / ld / "log.jsonl"
        if not log.is_file():
            continue
        for ln, raw in enumerate(log.read_text(encoding="utf-8", errors="replace").splitlines()):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            obj["_lead"] = ld
            obj["_log_line"] = ln
            obj["_log_path"] = f"{log}#L{ln}"
            entries.append(obj)
    return entries


def _parse_iso(ts: str) -> dt.datetime | None:
    if not isinstance(ts, str):
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _age_days(ts: str | None) -> float | None:
    parsed = _parse_iso(ts) if ts else None
    if not parsed:
        return None
    now = dt.datetime.now(dt.timezone.utc)
    return max(0.0, (now - parsed).total_seconds() / 86400.0)


def _freshness_label(age_d: float | None) -> str:
    if age_d is None:
        return "unknown"
    if age_d < 1:
        return "today"
    if age_d < 3:
        return "fresh"
    if age_d < 14:
        return "current"
    if age_d < 60:
        return "aging"
    return "stale"


# --- FRESHNESS GATE (sprint-4) ----------------------------------------------
# Kind-aware policy window: every canon kind decays at a different rate. A
# doctrine 6 months old may still be load-bearing; a finding 6 months old is
# likely superseded. The gate flags hits beyond their kind's re-verify window
# so a future mind sees AGE as part of the recall, not just CONTENT.
#
# Tunables are exposed via recall(fresh_days=N, reverify_days=N) (uniform
# override) and CLI --fresh-days / --reverify-days. Defaults are the sane
# starting point per kind below; review after K=3 distinct fires per kind.

# kind → (fresh_days, reverify_days)
# fresh_days   = age at which we no longer claim "fresh" (becomes "aging")
# reverify_days = age beyond which the recall MUST be re-verified ("stale")
FRESHNESS_POLICY: dict[str, tuple[int, int]] = {
    # Load-bearing, long-shelf knowledge. Stale doctrine = danger because it
    # FEELS canonical but may be superseded. Reverify window is 6 months.
    "doctrine":        (60, 180),
    "decision":        (60, 180),
    "principle":       (60, 180),
    # Operational findings + cures + learnings — shorter shelf. A finding
    # is usually a snapshot of a system state; that state moves.
    "finding":         (14, 45),
    "cure":            (14, 45),
    "learning":        (14, 45),
    "receipt":         (14, 45),
    # Ephemeral by construction — should not be load-bearing past ~3 weeks.
    "handoff":         (7, 21),
    "session":         (7, 21),
    "note":            (7, 21),
    # Sane middle ground for anything unclassified.
    "__default__":     (30, 90),
}

STALENESS_FRESH = "fresh"
STALENESS_AGING = "aging"
STALENESS_STALE = "stale"
STALENESS_UNKNOWN = "unknown"


def _policy_for_kind(kind: str | None,
                     override_fresh: float | None,
                     override_reverify: float | None) -> tuple[float, float]:
    """Return (fresh_days, reverify_days) for a kind, honoring overrides.

    Per-call overrides win uniformly over kind-aware defaults. If only one
    override is set, the other side keeps the kind-aware default (so a caller
    can say "treat everything as fresh up to 90 days" without also having to
    set reverify).
    """
    default_fresh, default_reverify = FRESHNESS_POLICY.get(
        (kind or "").lower(), FRESHNESS_POLICY["__default__"]
    )
    f = float(override_fresh) if override_fresh is not None else float(default_fresh)
    r = float(override_reverify) if override_reverify is not None else float(default_reverify)
    # Defensive: reverify must be >= fresh, else swap so semantics stay sane.
    if r < f:
        f, r = r, f
    return f, r


def _staleness_for(age_d: float | None,
                   fresh_days: float,
                   reverify_days: float) -> str:
    """Bucket an age in days into one of {fresh, aging, stale, unknown}."""
    if age_d is None:
        return STALENESS_UNKNOWN
    if age_d <= fresh_days:
        return STALENESS_FRESH
    if age_d <= reverify_days:
        return STALENESS_AGING
    return STALENESS_STALE


def _recency_multiplier(age_d: float | None, reverify_days: float) -> float:
    """COLD-RECONSTITUTION recency uplift (2026-06-21, P2.1). Returns a
    multiplier >= 1.0 applied to a hit's fusion score.

    Linear decay: ×(1 + COLD_RECENCY_MAX) at age 0 → ×1.0 at reverify_days,
    flat ×1.0 after (an aged entry gets no recency help — it must win on
    content like before). Unknown age (no parseable ts) gets ×1.0 (neutral).

    Why linear over the kind's reverify horizon: a finding's recency matters
    for ~45d (its reverify window), a doctrine's for ~180d — the same window
    the staleness gate uses to call something "stale". This makes the recency
    BOOST and the staleness GATE share one horizon: fresh-promote and
    stale-demote are symmetric around the kind's own shelf-life.
    """
    if age_d is None or reverify_days <= 0:
        return 1.0
    if age_d >= reverify_days:
        return 1.0
    frac_left = 1.0 - (age_d / reverify_days)   # 1.0 at age0 → 0.0 at horizon
    return 1.0 + COLD_RECENCY_MAX * frac_left


def _build_freshness_gate(final_hits: list[dict],
                          override_fresh: float | None,
                          override_reverify: float | None) -> dict:
    """Compute the freshness-gate signal over the final ranked hits.

    Mutates each hit dict in-place to add `_staleness`, `_policy_fresh_days`,
    `_policy_reverify_days` so the gate's verdict is auditable per-hit.

    Returns the top-level freshness_gate dict to attach to result.
    """
    counts = {STALENESS_FRESH: 0, STALENESS_AGING: 0,
              STALENESS_STALE: 0, STALENESS_UNKNOWN: 0}
    used_policy: dict[str, dict[str, float]] = {}

    for h in final_hits:
        ce = h.get("_canon_entry") or {}
        kind = (ce.get("kind") or "").lower() or None
        is_canon = (h.get("source") == "canon")
        # Non-canon hits get the policy for the unknown bucket; their staleness
        # is meaningful but they were never expected to be canon-grade truth.
        f_days, r_days = _policy_for_kind(kind, override_fresh, override_reverify)
        age = h.get("_age_days")
        st = _staleness_for(age, f_days, r_days)
        h["_staleness"] = st
        h["_policy_fresh_days"] = f_days
        h["_policy_reverify_days"] = r_days
        # Don't double-flag unknown for non-canon: handoff/session entries
        # may have ts but the policy is the same.
        counts[st] += 1
        used_policy.setdefault(
            kind or ("__non_canon__" if not is_canon else "__default__"),
            {"fresh_days": f_days, "reverify_days": r_days},
        )

    n = len(final_hits)
    fresh_n = counts[STALENESS_FRESH]
    aging_n = counts[STALENESS_AGING]
    stale_n = counts[STALENESS_STALE]
    unknown_n = counts[STALENESS_UNKNOWN]

    # Re-verify-required logic:
    # - ANY stale hit in the top results → MUST re-verify (one stale truth
    #   can mislead an entire decision).
    # - ALL hits aging with zero fresh → MUST re-verify (no fresh anchor).
    # - Otherwise, fresh anchors exist → no forced re-verify (caller still
    #   sees per-hit staleness flags).
    re_verify = False
    reason_bits = []
    if stale_n > 0:
        re_verify = True
        reason_bits.append(f"{stale_n} stale hit(s) past re-verify window")
    if n > 0 and fresh_n == 0 and aging_n > 0 and stale_n == 0:
        re_verify = True
        reason_bits.append("no fresh anchor; all hits aging")

    if re_verify:
        next_move = (
            "FRESHNESS-GATE: re-verify required — "
            + "; ".join(reason_bits) + ". "
            "Before relying on these hits: (a) confirm the underlying file "
            "or substrate referenced by each stale/aging hit is still the "
            "current state, OR (b) supersede with a fresher canon_append. "
            "DO NOT cite a stale hit as live truth without this step."
        )
    elif n == 0:
        next_move = "FRESHNESS-GATE: no hits to evaluate."
    else:
        next_move = (
            f"FRESHNESS-GATE: ok — {fresh_n} fresh / {aging_n} aging / "
            f"{stale_n} stale / {unknown_n} unknown. Fresh anchor present; "
            "serve as truth + cite by canon id."
        )

    return {
        "policy": used_policy,
        "fresh_count": fresh_n,
        "aging_count": aging_n,
        "stale_count": stale_n,
        "unknown_count": unknown_n,
        "re_verify_required": re_verify,
        "next_move": next_move,
    }



def _canon_entry_by_path_fragment(hits: list[dict]) -> list[dict]:
    """For each vector canon hit, parse the lead + line from path
    'mem/canon/<lead>/log.jsonl#Ln' and load the underlying entry.
    """
    out = []
    for h in hits:
        path = h.get("path", "")
        if "mem/canon/" not in path:
            out.append({**h, "_canon_entry": None})
            continue
        if "#L" in path:
            base, ln_part = path.rsplit("#L", 1)
            try:
                ln_target = int(ln_part)
            except ValueError:
                ln_target = None
        else:
            base, ln_target = path, None
        try:
            lead = Path(base).parent.name
        except Exception:
            lead = ""
        entry = None
        try:
            log = Path(base)
            if log.is_file() and ln_target is not None:
                lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
                if 0 <= ln_target < len(lines):
                    entry = json.loads(lines[ln_target])
        except Exception:
            entry = None
        out.append({**h, "_canon_entry": entry, "_canon_lead": lead})
    return out


# ---------------------------------------------------------------------------
# Track A: LEXICAL retriever (the cure for T2/T3)
# ---------------------------------------------------------------------------

def _tokenize(s: str) -> set[str]:
    if not s:
        return set()
    return {t.lower() for t in TOKEN_RE.findall(s) if len(t) >= 2}


def _compute_idf(entries: list[dict]) -> dict[str, float]:
    """Inverse-document-frequency over the canon corpus being searched.

    THE DIARY-PROBLEM CURE (2026-06-20, mind-lead). The pre-fix token-overlap
    term scored every matched query token equally:
        score += overlap / max(1, |q_tokens|)
    With no rarity weighting, ubiquitous civ-vocabulary tokens (skill / lead /
    canon / receipt / finding) — present in nearly every canon entry — count
    the SAME as a rare, discriminating token. The observed failure: an
    all-common-token query produced a FLAT score-tie across topically-unrelated
    entries (six unrelated docs all at score=0.8000), and a vague entry stuffed
    with common vocabulary ranked as high as a specific, information-rich one.
    That is the diary problem: a diary full of generic words out-competes a
    precise finding.

    IDF(t) = ln( (N + 1) / (df(t) + 1) ) + 1   (smoothed, always >= 1.0 so a
    token never gets zero weight; rare tokens get a large multiplier, tokens
    that appear in EVERY doc collapse toward 1.0). Standard textbook smoothed
    IDF (sklearn-style). Computed once per corpus load; sub-100ms over the
    full trunk (~1.1k entries today).
    """
    import math
    n_docs = len(entries)
    if n_docs == 0:
        return {}
    df: dict[str, int] = {}
    for e in entries:
        for t in _tokenize(_entry_haystack(e)):
            df[t] = df.get(t, 0) + 1
    idf: dict[str, float] = {}
    for t, d in df.items():
        idf[t] = math.log((n_docs + 1) / (d + 1)) + 1.0
    return idf


def _entry_haystack(entry: dict) -> str:
    """Concatenated lexical surface for an entry: item + rationale + id + kind + lead.

    Includes id so a caller searching by canon id gets an immediate hit.
    """
    parts = [
        entry.get("item") or "",
        entry.get("rationale") or "",
        entry.get("id") or "",
        entry.get("kind") or "",
        entry.get("lead") or entry.get("_lead") or "",
    ]
    return " ".join(p for p in parts if p)


def lexical_search(
    query: str,
    *,
    pool: int = LEXICAL_POOL,
    lead: str | None = None,
) -> list[dict]:
    """In-memory lexical scan over the canon trunk. Returns up to `pool` hits in
    semsearch-hit shape (rank/distance/source/path/preview/vertical) so the fusion
    layer treats lexical and vector hits identically.

    Scoring:
        exact substring match (case-insensitive) → score += 10  + (len(query)/len(haystack))
        IDF-weighted token-overlap                → score += Σ_{t in q∩doc} idf(t) / Σ_{t in q} idf(t)
                                                    (DIARY-PROBLEM CURE 2026-06-20: rare/
                                                    discriminating tokens dominate; ubiquitous
                                                    civ-vocabulary collapses toward zero weight,
                                                    so a vague entry can no longer tie a specific
                                                    one on shared common tokens)
        kind=doctrine                             → tiny tiebreaker (doctrine outranks finding
                                                    when both lexically score the same)
    Empty query returns []. Empty trunk returns [].
    """
    q = (query or "").strip()
    if not q:
        return []

    q_lower = q.lower()
    q_tokens = _tokenize(q)

    entries = _read_canon_entries(lead)
    if not entries:
        return []

    # DIARY-PROBLEM CURE (2026-06-20): IDF over the corpus being searched, so
    # token-overlap is rarity-weighted instead of flat-counted. q_idf_total is
    # the max attainable IDF mass for this query (Σ idf over query tokens),
    # used to normalize the overlap term into [0,1] — keeping it proportional
    # to the prior flat term's range (so exact-substring + doctrine tiebreakers
    # stay correctly scaled).
    idf = _compute_idf(entries)
    q_idf_total = sum(idf.get(t, 1.0) for t in q_tokens) if q_tokens else 0.0

    scored: list[tuple[float, bool, dict]] = []
    for e in entries:
        hay = _entry_haystack(e)
        hay_lower = hay.lower()
        score = 0.0
        exact = False
        # Strong signal: exact substring.
        if q_lower and q_lower in hay_lower:
            exact = True
            # Bigger bonus for longer matched substrings (more specific).
            score += 10.0 + min(1.0, len(q_lower) / max(1, len(hay_lower)))
        # IDF-weighted token overlap (replaces the flat overlap/|q_tokens| term).
        if q_tokens and q_idf_total > 0:
            e_tokens = _tokenize(hay)
            shared = q_tokens & e_tokens
            if shared:
                matched_idf = sum(idf.get(t, 1.0) for t in shared)
                score += matched_idf / q_idf_total
        # Tiny tiebreaker so doctrine outranks finding at identical lexical score.
        kind = (e.get("kind") or "").lower()
        if kind == "doctrine":
            score += 0.01
        elif kind == "decision":
            score += 0.005
        if score > 0:
            scored.append((score, exact, e))

    scored.sort(key=lambda x: (-x[0], not x[1]))
    scored = scored[:pool]

    hits: list[dict] = []
    for rank, (score, exact, e) in enumerate(scored, start=1):
        item = e.get("item") or ""
        preview = item[:220].replace("\n", " ")
        hits.append({
            "rank": rank,
            # distance is informational only here — lower = better is the chroma
            # convention; we mirror that so downstream sort logic stays consistent.
            "distance": max(0.0, 1.0 - min(1.0, score / 10.0)),
            "id": e.get("id") or "",
            "source": "canon",            # lexical retriever ONLY scans canon trunk
            "path": e.get("_log_path", ""),
            "vertical": e.get("_lead", ""),
            "project": "",
            "preview": preview,
            "_lexical_score": score,
            "_lexical_exact": exact,
            "_canon_entry": e,
            "_canon_lead": e.get("_lead", ""),
        })
    return hits


# ---------------------------------------------------------------------------
# Track A: HYBRID FUSION (Reciprocal Rank Fusion + exact-substring boost)
# ---------------------------------------------------------------------------

def _fuse_rrf(
    lexical_hits: list[dict],
    vector_hits_decorated: list[dict],
    *,
    rrf_k: int = RRF_K,
    exact_boost: float = EXACT_SUBSTRING_BOOST,
) -> list[dict]:
    """Reciprocal Rank Fusion of two ranked lists.

    score(d) = sum_over_retrievers( 1 / (rrf_k + rank_in_that_retriever) )
             + exact-bonus
             + LEXICAL_MAG_WEIGHT * (lexical_score / top_lexical_score)   [NEW 2026-06-21]

    De-dup key: prefer canon entry id; fall back to (path,line) for non-canon.
    Returns one merged, de-duplicated list sorted by fused score (desc), each hit
    decorated with _fusion_score, _in_lexical, _in_vector, _lexical_exact.

    LEXICAL-MAGNITUDE TERM (2026-06-21, P2.1 — the SECOND cold-recall cause):
    pure RRF uses only the RANK, discarding the lexical score MAGNITUDE. A
    DOMINANT lexical match (e.g. a just-appended close-out entry scoring 0.857
    when the next best is 0.226 — a 3.8x lead) collapsed to the same flat
    1/(60+1)=0.0164 rank-1 contribution as any other rank-1, and was then
    out-ranked by mediocre entries that merely appeared in BOTH retrievers
    (cross-confirmation ~0.033 > a lone dominant lexical 0.0164). That is why a
    cold mind's own freshly-written entry — the BEST lexical match for its own
    hand-off-seeded query — ranked #23 instead of #1. The fix adds a small term
    proportional to the lexical hit's SHARE of the top lexical score, so a
    dominant match earns a real lift above the flat floor, while weak overlaps
    (small share) stay near it and the exact-match +1.0 still dominates all.
    """
    merged: dict[str, dict] = {}

    def _key(h: dict) -> str:
        entry = h.get("_canon_entry") or {}
        if entry.get("id"):
            return f"canon:{entry['id']}"
        # Non-canon (vector-only hits with no canon entry) keyed by path.
        return f"src:{h.get('source','')}:path:{h.get('path','')}"

    for rank, h in enumerate(lexical_hits, start=1):
        k = _key(h)
        score = 1.0 / (rrf_k + rank)
        if h.get("_lexical_exact"):
            score += exact_boost
        else:
            # Magnitude term, ABSOLUTE (not relative-to-top). The IDF-weighted
            # lexical score is already query-normalized into ~[0,1]: a dominant
            # real match scores ~0.86, a mediocre one ~0.22, and PURE NOISE (an
            # impossible query that only hits the 0.005 doctrine-tiebreaker)
            # scores ~0.005. Using the ABSOLUTE score (not score/top_lex) is the
            # load-bearing choice: a relative-to-top normalization inflated
            # noise to share≈1.0 (best-of-the-noise) and broke build-or-tombstone
            # (PROBE 8). Absolute keeps noise at +0.0003 (stays below the floor)
            # while a dominant match earns +0.043 → clears the floor decisively.
            mag = min(1.0, max(0.0, h.get("_lexical_score", 0.0)))
            score += LEXICAL_MAG_WEIGHT * mag
        slot = merged.setdefault(k, dict(h))
        slot["_fusion_score"] = slot.get("_fusion_score", 0.0) + score
        slot["_in_lexical"] = True
        slot["_lexical_rank"] = rank
        slot["_lexical_exact"] = h.get("_lexical_exact", False)

    for rank, h in enumerate(vector_hits_decorated, start=1):
        k = _key(h)
        score = 1.0 / (rrf_k + rank)
        slot = merged.setdefault(k, dict(h))
        # Merge metadata if vector contributed an entry the lexical scan missed.
        for fld in ("_canon_entry", "_canon_lead", "source", "path", "preview", "distance"):
            if fld not in slot and fld in h:
                slot[fld] = h[fld]
        slot["_fusion_score"] = slot.get("_fusion_score", 0.0) + score
        slot["_in_vector"] = True
        slot["_vector_rank"] = rank

    fused = list(merged.values())
    fused.sort(
        key=lambda h: (
            -h.get("_fusion_score", 0.0),
            0 if h.get("source") == "canon" else 1,
            h.get("distance", 1e9),
        )
    )
    for new_rank, h in enumerate(fused, start=1):
        h["rank"] = new_rank
    return fused


# ---------------------------------------------------------------------------
# recall() — the public surface
# ---------------------------------------------------------------------------

def recall(
    query: str,
    *,
    k: int = DEFAULT_K,
    lead: str | None = None,
    kind: str | None = None,
    max_age_days: float | None = DEFAULT_MAX_AGE_DAYS,
    canon_only: bool = True,
    use_lexical: bool = True,
    use_vector: bool = True,
    record_gap: bool = True,
    dedupe_window_sec: int = GAP_DEDUPE_WINDOW_SEC,
    log_hits: bool = True,
    # --- FRESHNESS GATE (sprint-4) ---
    # When freshness_gate=True (default), compute kind-aware staleness on each
    # returned hit and attach result["freshness_gate"]. Per-call overrides for
    # fresh_days/reverify_days uniformly replace the kind-aware defaults; pass
    # None to keep kind-aware defaults. Set freshness_gate=False for legacy
    # passthrough (result["freshness_gate"] = None).
    freshness_gate: bool = True,
    fresh_days: float | None = None,
    reverify_days: float | None = None,
) -> dict:
    """Structured hybrid recall over canon (+ doctrine/handoff/etc when canon_only=False).

    Returns a dict with:
        query, k, verdict ("OK" | "OK_FALLBACK" | "BUILD_OR_TOMBSTONE" |
            "INDEX_MISSING" | "TOMBSTONED"),
        chroma_path, hit_count, hits[], next_move, warnings[],
        retrievers_fired (list), low_confidence (bool),
        gap_record (dict | None — set when an empty-recall was recorded,
            or when a tombstone short-circuited the recall).

    Build-or-tombstone closed-loop (sprint-3): if the verdict is empty
    (BUILD_OR_TOMBSTONE / INDEX_MISSING) and record_gap=True, append a
    build-ticket to mem/recall_gaps/build_tickets.jsonl unless the same
    query was already recorded within dedupe_window_sec. If a tombstone
    matches the query, short-circuit to verdict TOMBSTONED and cite the
    tombstone reason — no build-ticket is recorded (gap already labelled).
    """
    warnings: list[str] = []
    result = {
        "query": query,
        "k": k,
        "lead": lead,
        "kind": kind,
        "max_age_days": max_age_days,
        "canon_only": canon_only,
        "use_lexical": use_lexical,
        "use_vector": use_vector,
        "verdict": NO_RESULT_VERDICT,
        "chroma_path": None,
        "hit_count": 0,
        "hits": [],
        "next_move": "",
        "warnings": warnings,
        "retrievers_fired": [],
        "low_confidence": False,
        "gap_record": None,
        "recall_hit_record": None,
        "freshness_gate": None,
        "ts": _iso_now(),
    }

    # ---- TOMBSTONE SHORT-CIRCUIT (sprint-3) --------------------------------
    # If this query was explicitly tombstoned, surface that decision IMMEDIATELY
    # so the mind does not waste retriever cycles AND does not silently see
    # weak vector noise on a dead topic. Honors normalized-query exact match.
    tomb = None
    try:
        tomb = _matching_tombstone(query)
    except Exception as exc:
        warnings.append(f"tombstone_lookup_exception:{type(exc).__name__}")
    if tomb is not None:
        result["verdict"] = "TOMBSTONED"
        result["next_move"] = (
            f"TOMBSTONE on record (filed {tomb.get('ts', '?')}): "
            f"{tomb.get('reason', '(no reason given)')}. "
            f"forward-pointer: {tomb.get('forward_pointer') or '(none)'}. "
            "Do NOT re-suffer — if this decision is now wrong, REMOVE the tombstone "
            f"line from {TOMBSTONES_PATH.relative_to(_AICIV_ROOT)} and run canon_recall again."
        )
        result["gap_record"] = {"kind": "tombstone_hit", "tombstone": tomb}
        return result

    # ---- LEXICAL leg (best-effort, never fails — disk-backed scan) ----------
    lexical_hits: list[dict] = []
    if use_lexical:
        try:
            lexical_hits = lexical_search(query, pool=LEXICAL_POOL, lead=lead)
            if lexical_hits:
                result["retrievers_fired"].append("lexical")
        except Exception as exc:
            warnings.append(f"lexical_exception:{type(exc).__name__}")

    # ---- VECTOR leg (best-effort, falls back gracefully) --------------------
    vector_hits_decorated: list[dict] = []
    vector_fired = False
    if use_vector:
        if _search is None:
            warnings.append("semsearch_import_failed")
        else:
            result["chroma_path"] = getattr(_search, "CHROMA_PATH", None)
            if _search.CHROMA_PATH is None:
                warnings.append("chroma_path_missing")
            else:
                raw_k = max(k * VECTOR_POOL_MULT, 30)
                source_filter = None
                if canon_only:
                    source_filter = {"canon", "doctrine", "handoff"}
                try:
                    vec = _search.search(query, k=raw_k, canon_first=True, source_filter=source_filter)
                    vector_fired = True
                    result["retrievers_fired"].append("vector")
                    canon_vec = [h for h in vec if h.get("source") == "canon"]
                    other_vec = [h for h in vec if h.get("source") != "canon"]
                    vector_hits_decorated = _canon_entry_by_path_fragment(canon_vec) + [
                        {**h, "_canon_entry": None, "_canon_lead": ""} for h in other_vec
                    ]
                except Exception as exc:
                    warnings.append(f"semsearch_exception:{type(exc).__name__}")

    # ---- FUSE ---------------------------------------------------------------
    fused = _fuse_rrf(lexical_hits, vector_hits_decorated)

    # Apply lead/kind/freshness filters AFTER fusion (filters operate on the
    # canon entry where present; non-canon hits ignore canon-entry filters).
    filtered: list[dict] = []
    for h in fused:
        entry = h.get("_canon_entry") or {}
        is_canon = (h.get("source") == "canon")
        if lead and is_canon and h.get("_canon_lead") != lead:
            continue
        if kind and entry.get("kind") != kind:
            continue
        age = _age_days(entry.get("ts")) if entry else None
        if max_age_days is not None:
            # If we have an age, enforce; if not (non-canon) and max_age requested,
            # drop the entry — caller explicitly asked for "fresh canon only".
            if age is None or age > max_age_days:
                continue
        h["_age_days"] = age
        h["_freshness"] = _freshness_label(age) if is_canon else "non-canon"
        filtered.append(h)

    # ---- COLD-RECONSTITUTION RECENCY RE-RANK (2026-06-21, P2.1) -------------
    # THE COLD-RECALL CURE applied. For each hit ALREADY in the fusion pool
    # (i.e. it had real lexical/vector signal — a no-overlap entry never reaches
    # here), multiply its fusion score by a kind-aware recency multiplier so a
    # fresh, genuinely-relevant entry is promoted into the top-k. This is what
    # lets a cleared mind surface its OWN just-appended close-out entry on a
    # generic cold query instead of seeing it buried at rank #100+.
    #
    # SAFETY (preserves build-or-tombstone + the IDF diary-fix + exact-match):
    #   - Multiplicative on an EXISTING positive score → never invents signal
    #     for a no-overlap entry (those aren't in `filtered`).
    #   - The post-rerank verdict still reads the ORIGINAL _fusion_score for the
    #     noise-floor (see top_fusion below) — recency cannot fake a hit past the
    #     build-or-tombstone floor. The boost only re-ORDERS real hits.
    #   - Exact-substring hits carry +1.0 (EXACT_SUBSTRING_BOOST) which dwarfs
    #     the ≤×1.6 recency uplift, so a rare-token exact match stays rank #1.
    #   - lead-own bonus only when caller passed lead= AND the hit is in it.
    for h in filtered:
        entry = h.get("_canon_entry") or {}
        ekind = (entry.get("kind") or "").lower() or None
        _f_days, r_days = _policy_for_kind(ekind, fresh_days, reverify_days)
        mult = _recency_multiplier(h.get("_age_days"), r_days)
        if lead and h.get("source") == "canon" and h.get("_canon_lead") == lead:
            mult += COLD_LEAD_OWN_BONUS
        base = h.get("_fusion_score", 0.0)
        h["_recency_mult"] = round(mult, 4)
        h["_fusion_score_boosted"] = base * mult
    # Re-sort by the BOOSTED score (same tiebreak shape as _fuse_rrf: canon
    # before non-canon, then nearest distance). The original _fusion_score is
    # preserved on each hit for the verdict's noise-floor + for audit.
    filtered.sort(
        key=lambda h: (
            -h.get("_fusion_score_boosted", h.get("_fusion_score", 0.0)),
            0 if h.get("source") == "canon" else 1,
            h.get("distance", 1e9),
        )
    )
    for new_rank, h in enumerate(filtered, start=1):
        h["rank"] = new_rank

    # Trim to caller's k.
    final = filtered[:k]

    # ---- VERDICT ------------------------------------------------------------
    any_hit = bool(final)
    any_canon = any(h.get("source") == "canon" for h in final)
    only_vector = ("vector" in result["retrievers_fired"]
                   and "lexical" not in result["retrievers_fired"])
    only_lexical = ("lexical" in result["retrievers_fired"]
                    and "vector" not in result["retrievers_fired"])
    no_retriever = not result["retrievers_fired"]

    # Vector retriever returns nearest-neighbors even for nonsense queries
    # (chroma always returns k results from the index), AND the lexical
    # retriever can produce weak token-overlap hits on common tokens (e.g.
    # "no", "match"). To preserve build-or-tombstone signalling, detect the
    # "all-weak" signature via fusion_score:
    #   - single-retriever rank-1 RRF contribution alone is 1/(60+1) ≈ 0.0164
    #   - lexical+vector cross-confirmation pushes fusion_score >= ~0.0328
    #   - exact-substring match adds EXACT_SUBSTRING_BOOST=1.0 → >> floor
    # If the TOP fusion_score across the final hits is below NOISE_FUSION_FLOOR,
    # no retriever signal is meaningful — surface BUILD_OR_TOMBSTONE.
    NOISE_FUSION_FLOOR = 0.025  # > this means lexical+vector cross-confirmed OR exact match
    top_fusion = max((h.get("_fusion_score", 0.0) for h in final), default=0.0)
    all_vector_noise = any_hit and top_fusion < NOISE_FUSION_FLOOR

    if not any_hit:
        if no_retriever:
            # Neither lexical (empty trunk) nor vector (offline) fired.
            result["verdict"] = "INDEX_MISSING"
            result["next_move"] = (
                "neither lexical nor vector retriever produced a hit. Check chroma "
                "(projects/aiciv-mind/semsearch/build_index_full.py) AND canon trunk "
                f"({CANON_DIR})."
            )
        else:
            result["verdict"] = NO_RESULT_VERDICT
            result["next_move"] = (
                "no canon, doctrine, or handoff hit for this query. "
                "BUILD: if this is a real gap, file a build-ticket — append a canon entry "
                "via tools/canon_append.py once the work lands. "
                "TOMBSTONE: if the topic is dead, file a brief tombstone canon entry citing "
                "the forward-pointer or 'NO RECALL — closed as out-of-scope' so future minds "
                "do not re-suffer."
            )
    elif all_vector_noise:
        # Vector returned nearest-neighbors but they have no lexical confirmation
        # AND the top fusion-score is below the cross-retriever floor (each
        # retriever rank-1 RRF contribution alone ~= 0.0164; lexical+vector
        # cross-confirmation pushes well past the floor; an exact-match adds
        # the EXACT_SUBSTRING_BOOST=1.0 bonus). This is the silent-empty trap.
        result["verdict"] = NO_RESULT_VERDICT
        result["low_confidence"] = True
        result["next_move"] = (
            "no LEXICAL canon hit, and the top vector hits have NO lexical "
            f"reinforcement (top fusion_score {top_fusion:.4f} below floor "
            f"{NOISE_FUSION_FLOOR:.4f}). Treat as BUILD_OR_TOMBSTONE: no real "
            "recall for this query. BUILD a canon entry if the topic is real "
            "and missing, or TOMBSTONE if it's out-of-scope. The returned hits "
            "are nearest-noise, not a real recall."
        )
        # Keep the noise-hits attached so the caller can see WHY we called it noise.
    else:
        if any_canon:
            result["verdict"] = "OK"
            # low_confidence flag when only one retriever fired AND no lexical exact-match
            # is in the top results.
            top_exact = any(h.get("_lexical_exact") for h in final[:3])
            if (only_vector or only_lexical) and not top_exact:
                result["low_confidence"] = True
                result["next_move"] = (
                    f"canon recall succeeded (single retriever: "
                    f"{result['retrievers_fired'][0]}); cite the canon entry by id when "
                    "acting. LOW-CONFIDENCE: only one retriever fired — re-run after fixing "
                    "the other for higher confidence."
                )
            else:
                result["next_move"] = "canon recall succeeded; cite the canon entry by id when acting."
        else:
            result["verdict"] = "OK_FALLBACK"
            result["low_confidence"] = True
            result["next_move"] = (
                "no direct canon hit; nearest substrate is doctrine/handoff/session. "
                "Consider promoting a relevant silo entry to canon if work depends on this."
            )

    # ---- FRESHNESS GATE (sprint-4) -----------------------------------------
    # Decorate each `final` hit with _staleness BEFORE pretty_hits projection
    # so the per-hit flag flows through. Gate runs on the post-fusion, post-
    # filter set — the same set that becomes pretty_hits. NEVER drops a hit;
    # only flags it. Off if caller passed freshness_gate=False.
    if freshness_gate:
        fg = _build_freshness_gate(final, fresh_days, reverify_days)
        result["freshness_gate"] = fg
    else:
        # Decorate hits with neutral staleness so downstream consumers don't
        # KeyError on missing flags. Explicit "gate_disabled" makes the
        # passthrough auditable.
        for h in final:
            h["_staleness"] = "gate_disabled"
            h["_policy_fresh_days"] = None
            h["_policy_reverify_days"] = None

    # ---- Pretty hits for output --------------------------------------------
    # SPRINT-6 (2026-06-19, mind-lead, R16 recall-index-dup cure): for non-canon
    # hits (handoff / doctrine / primary_memory / vertical_memory / claude_session),
    # _canon_entry is None — fall back to the hit's own id/kind so the pretty
    # output isn't an empty/'-' shell. Earlier the bug surfaced as
    # `id='-' / ts='-' / double-item` for the handoff with malformed shard
    # reasoning (open-work-register R16). ts stays None for non-canon (handoff
    # chroma metadata has no ts) — the prior `ce.get('ts')` returned None too,
    # so behavior on ts is unchanged.
    pretty_hits = []
    for h in final:
        ce = h.get("_canon_entry") or {}
        is_canon = bool(ce)
        pretty_hits.append({
            "rank": h.get("rank"),
            "source": h.get("source"),
            "distance": h.get("distance"),
            "fusion_score": round(h.get("_fusion_score", 0.0), 6),
            "in_lexical": h.get("_in_lexical", False),
            "in_vector": h.get("_in_vector", False),
            "lexical_exact": h.get("_lexical_exact", False),
            "path": h.get("path"),
            "lead": h.get("_canon_lead") or h.get("vertical") or "",
            # For canon hits: pull from the canon entry. For non-canon hits:
            # fall back to whatever the underlying hit carried (chroma id, etc.).
            "kind": ce.get("kind") if is_canon else h.get("kind"),
            "ts": ce.get("ts"),
            "age_days": h.get("_age_days"),
            "freshness": h.get("_freshness"),
            # NEW sprint-4: per-hit gate verdict
            "staleness": h.get("_staleness"),
            "policy_fresh_days": h.get("_policy_fresh_days"),
            "policy_reverify_days": h.get("_policy_reverify_days"),
            "id": ce.get("id") if is_canon else h.get("id"),
            # For canon: use the canon item (curated). For non-canon: use the
            # preview (the first 220 chars from chroma) — was already the
            # fallback, so behavior on item is unchanged.
            "item": ce.get("item") or h.get("preview"),
            "preview": h.get("preview"),
        })

    result["hit_count"] = len(pretty_hits)
    result["hits"] = pretty_hits

    # ---- AUTO-RECORD BUILD-TICKET ON EMPTY RECALL (sprint-3) ----------------
    # THE MECHANISM. Gates here, in the recall() function — NOT at Primary
    # discipline. Closes "recall returns nothing → mind assumes nothing exists":
    # the gap is now a persistent ledger row a future mind can SEE.
    #
    # Skip conditions (substrate-honest):
    #   - record_gap=False (caller opted out, e.g. self-test idempotency loop)
    #   - query too short (< GAP_MIN_QUERY_LEN chars — junk-noise floor)
    #   - verdict is not an empty-recall (OK / OK_FALLBACK / TOMBSTONED are
    #     NOT gaps)
    #   - dedupe-hit: same query already recorded within dedupe_window_sec
    should_record = (
        record_gap
        and result["verdict"] in (NO_RESULT_VERDICT, "INDEX_MISSING")
        and len((query or "").strip()) >= GAP_MIN_QUERY_LEN
    )
    if should_record:
        try:
            recent = _recent_ticket_for_query(query, dedupe_window_sec)
        except Exception as exc:
            recent = None
            warnings.append(f"dedupe_lookup_exception:{type(exc).__name__}")
        if recent is not None:
            # Surface the existing record but don't duplicate-write.
            result["gap_record"] = {
                "kind": "build_ticket_dedupe_hit",
                "existing_ts": recent.get("ts"),
                "window_sec": dedupe_window_sec,
                "note": "build-ticket for this query was already recorded "
                        "within the dedupe window; not re-writing.",
            }
        else:
            try:
                row = _append_build_ticket(
                    query=query,
                    verdict=result["verdict"],
                    warnings=list(warnings),
                    retrievers_fired=list(result["retrievers_fired"]),
                    low_confidence=result["low_confidence"],
                )
                result["gap_record"] = {"kind": "build_ticket_recorded", "row": row}
            except Exception as exc:
                warnings.append(f"build_ticket_write_exception:{type(exc).__name__}")

    # ---- AUTO-LOG RECALL-HITS (LEARN-READ instrument, 2026-06-19) -----------
    # THE READ MECHANISM, symmetric to the build-ticket MISS gate above. When a
    # recall actually SERVES canon entries (verdict OK / OK_FALLBACK with canon
    # hits present), append ONE recall-hit row recording which canon ids were
    # served on this real path. This is how the civ instruments the READ, not
    # just the WRITE — turning "is canon ever recalled?" from faith into a number.
    #
    # Skip conditions (substrate-honest, mirror the build-ticket gate):
    #   - log_hits=False (self-test / idempotency-loop opt-out)
    #   - no canon hits served (nothing to log; the MISS gate already fired)
    if log_hits:
        canon_served = [h for h in final if h.get("source") == "canon"
                        and (h.get("_canon_entry") or {}).get("id")]
        if canon_served:
            try:
                hit_row = _append_recall_hits(query, final, result["verdict"])
                result["recall_hit_record"] = {
                    "kind": "recall_hit_logged",
                    "served_count": len(hit_row.get("served_canon_ids", [])),
                    "served_canon_ids": hit_row.get("served_canon_ids", []),
                }
            except Exception as exc:
                warnings.append(f"recall_hit_write_exception:{type(exc).__name__}")

    return result


# ---------------------------------------------------------------------------
# Self-test — the cure-validation contract per LBI discipline
# ---------------------------------------------------------------------------

def _self_test() -> int:
    # Guard the LEARN-read instrument: self-test probes must NOT pollute the
    # recall-hits baseline ledger. (env_guard inside _append_recall_hits.)
    os.environ["CANON_RECALL_NO_HIT_LOG"] = "1"
    print("canon_recall.py self-test starting (Track A: hybrid lexical+vector)")
    print(f"  CANON_DIR: {CANON_DIR}")
    print(f"  _search module: {_search}")
    print(f"  CHROMA_PATH: {getattr(_search, 'CHROMA_PATH', None) if _search else 'n/a'}")

    # ---- PROBE 1: hybrid recall on existing canon (write-path UNCHANGED) ----
    # Query a substring that should hit a real canon entry. Tolerant of whether
    # vector is up — lexical alone MUST surface canon entries with this token.
    q1 = "memory-mission validation"
    r1 = recall(q1, k=5)
    print(f"\nPROBE 1: existing-canon recall  query={q1!r}")
    print(f"  retrievers_fired: {r1['retrievers_fired']}")
    print(f"  verdict: {r1['verdict']}  hits: {r1['hit_count']}  low_conf: {r1['low_confidence']}")
    for h in r1["hits"][:3]:
        flags = []
        if h.get("in_lexical"): flags.append("L")
        if h.get("in_vector"): flags.append("V")
        if h.get("lexical_exact"): flags.append("EX")
        print(f"    #{h['rank']} [{h['source']}/{h.get('lead','')}] "
              f"flags={','.join(flags) or '-'} fs={h.get('fusion_score')} "
              f"id={h.get('id','')[:12]}")
    if r1["verdict"] not in ("OK", "OK_FALLBACK"):
        print(f"FAIL probe-1: expected OK/OK_FALLBACK got {r1['verdict']}")
        return 1

    # ---- PROBE 2: nonce append + default-k recall (the T2/T3 cure) ----------
    # The recall-fix-recall2 contract: append a NEW canon entry under a fresh
    # nonced lead, then recall it at DEFAULT k=5. MUST appear in top results.
    # Uses a real-style lead (not _selftest_*) because the lexical retriever
    # deliberately skips underscore-prefixed silos. Pass --receipt-path so the
    # content-gate is satisfied.
    import secrets
    nonce = "recall2nonce" + secrets.token_hex(4)
    # Unique lead per run avoids canon_append's per-lead rate-limiter
    # (max 3 appends per 300s window — guards real silos, not selftests).
    test_lead = f"recall-fix-recall2-test-{secrets.token_hex(3)}"
    item_text = (
        f"track-a hybrid recall self-test nonce {nonce} for default-k contract — "
        "validates that lexical retriever surfaces nonced anchors at default k=5 "
        "(structural cure for sprint-1 T2/T3 FAIL — vector embeddings dilute nonces)."
    )
    rationale_text = (
        f"Self-test of canon_recall.py Track A hybrid retriever ({nonce}). "
        "If this entry surfaces at default k=5, the T2/T3 default-k FAIL is structurally closed. "
        "Receipt: ephemeral selftest receipt file written below by the test runner."
    )
    # Write an on-disk receipt so the content-gate accepts the append.
    receipt = tempfile.NamedTemporaryFile(
        "w", delete=False, prefix="canon-recall-selftest-recall2-", suffix=".txt"
    )
    receipt.write(
        f"canon_recall.py Track A self-test receipt\n"
        f"nonce: {nonce}\n"
        f"ts: {_iso_now()}\n"
    )
    receipt.close()
    cmd = [
        sys.executable, str(_AICIV_ROOT / "tools" / "canon_append.py"),
        "--lead", test_lead,
        "--kind", "finding",
        "--item", item_text,
        "--rationale", rationale_text,
        "--receipt-path", receipt.name,
    ]
    env = dict(os.environ)
    env["AICIV_DISABLE_INDEX_UPSERT"] = "1"  # lexical path is the contract; don't taint chroma
    try:
        cp = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
    except Exception as exc:
        print(f"FAIL probe-2: canon_append subprocess error: {exc}")
        try: os.unlink(receipt.name)
        except Exception: pass
        return 1
    if cp.returncode != 0:
        print("FAIL probe-2: canon_append rejected the self-test append:")
        print(f"  stdout: {cp.stdout[:400]}")
        print(f"  stderr: {cp.stderr[:400]}")
        try: os.unlink(receipt.name)
        except Exception: pass
        return 1
    print(f"\nPROBE 2: nonce append + default-k recall  nonce={nonce}")
    print(f"  canon_append exit=0, lead={test_lead}")

    # Now recall at DEFAULT k=5 by the nonce token.
    r2 = recall(nonce, k=DEFAULT_K)
    print(f"  recall verdict: {r2['verdict']}  hits: {r2['hit_count']}  "
          f"retrievers: {r2['retrievers_fired']}")
    nonce_ranks = [h["rank"] for h in r2["hits"] if nonce in (h.get("item") or "")]
    print(f"  nonce ranks in result: {nonce_ranks}")
    if not nonce_ranks or min(nonce_ranks) > DEFAULT_K:
        print(f"FAIL probe-2: nonce {nonce!r} not in top-{DEFAULT_K} of default-k recall.")
        return 1
    if nonce_ranks[0] != 1:
        print(f"WARN probe-2: nonce hit at rank {nonce_ranks[0]} (expected #1 for exact match)")
    # Cleanup self-test silo (idempotent — best-effort).
    try:
        sil = CANON_DIR / test_lead
        if sil.is_dir():
            for p in sil.iterdir():
                p.unlink()
            sil.rmdir()
    except Exception:
        pass
    try:
        os.unlink(receipt.name)
    except Exception:
        pass

    # ---- PROBE 3: exact substring of a real canon entry surfaces in top-5 ---
    # Pick the FIRST real canon entry across the trunk and use a meaningful
    # substring of its item field as the query.
    real_entries = []
    for ld in _list_canon_leads():
        if ld.startswith("recall-fix") or ld.startswith("_"):
            continue
        log = CANON_DIR / ld / "log.jsonl"
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            item = e.get("item") or ""
            if len(item) >= 30 and e.get("id"):
                real_entries.append((ld, e))
                break
        if len(real_entries) >= 3:
            break
    if not real_entries:
        print("WARN probe-3: no real canon entry available; skipping exact-substring probe")
    else:
        ld_target, target = real_entries[0]
        # Pull a distinctive 25-char substring from the middle of the item.
        item = target["item"]
        start = max(0, (len(item) - 25) // 2)
        substr = item[start:start + 25].strip()
        print(f"\nPROBE 3: exact substring  lead={ld_target} target_id={target['id'][:12]} substr={substr!r}")
        r3 = recall(substr, k=DEFAULT_K)
        print(f"  verdict: {r3['verdict']}  hits: {r3['hit_count']}  retrievers: {r3['retrievers_fired']}")
        ranks = [h["rank"] for h in r3["hits"] if h.get("id") == target["id"]]
        print(f"  target ranks: {ranks}")
        if not ranks or min(ranks) > DEFAULT_K:
            print(f"FAIL probe-3: exact-substring did not surface target id {target['id'][:12]} in top-{DEFAULT_K}")
            return 1

    # ---- PROBE 4: build-or-tombstone discipline -----------------------------
    # Pass record_gap=False so PROBE 4's null-query doesn't pollute the ledger
    # (PROBE 8 below is the one that explicitly tests the auto-record gate).
    nullq = "zzz-impossible-no-match-substring-9f2c1a7b8e6d-zzz-recall2"
    r4 = recall(nullq, k=5, canon_only=True, record_gap=False)
    print(f"\nPROBE 4: build-or-tombstone  verdict={r4['verdict']}  low_conf={r4['low_confidence']}")
    # The contract: silent-empty is forbidden. Either verdict signals build-or-
    # tombstone, OR vector noise leaked through and next_move is populated.
    if not r4.get("next_move"):
        print("FAIL probe-4: empty next_move for impossible query")
        return 1
    if r4["verdict"] not in (NO_RESULT_VERDICT, "INDEX_MISSING"):
        print(f"WARN probe-4: vector noise leaked past floor ({r4['verdict']}); "
              "next_move populated, but consider raising VECTOR_DIST_NOISE_FLOOR")

    # ---- PROBE 5: --lead filter still works ---------------------------------
    r5 = recall("memory substrate", k=5, lead="mind-lead", canon_only=True)
    print(f"\nPROBE 5: lead=mind-lead  verdict={r5['verdict']}  hits={r5['hit_count']}")
    bad_lead = [h for h in r5["hits"] if h.get("source") == "canon" and h.get("lead") != "mind-lead"]
    if bad_lead:
        print(f"FAIL probe-5: lead filter let through {len(bad_lead)} non-mind-lead hits")
        return 1

    # ---- PROBE 6: chroma-offline graceful degradation -----------------------
    # Simulate vector-off via use_vector=False; lexical alone MUST still recall
    # the substring of a real canon entry.
    if real_entries:
        ld_target, target = real_entries[0]
        item = target["item"]
        substr2 = item[:30].strip()
        r6 = recall(substr2, k=5, use_vector=False)
        print(f"\nPROBE 6: lexical-only (vector disabled)  verdict={r6['verdict']}  hits={r6['hit_count']}")
        ranks6 = [h["rank"] for h in r6["hits"] if h.get("id") == target["id"]]
        if not ranks6:
            print("FAIL probe-6: lexical-only could not recall a known canon entry by its own prefix")
            return 1
        if "lexical" not in r6["retrievers_fired"]:
            print("FAIL probe-6: lexical retriever did not fire when use_vector=False")
            return 1

    # ---- PROBE 7: canon-on-disk silo counts (read-only, no mutation) --------
    canon_disk = {}
    for ld in _list_canon_leads():
        log = CANON_DIR / ld / "log.jsonl"
        try:
            canon_disk[ld] = sum(1 for L in log.read_text().splitlines() if L.strip())
        except Exception:
            canon_disk[ld] = 0
    total_disk = sum(canon_disk.values())
    print(f"\nPROBE 7: canon-on-disk total: {total_disk} entries across {len(canon_disk)} silos")
    print(f"  top silos: {sorted(canon_disk.items(), key=lambda kv: -kv[1])[:5]}")

    # ---- PROBE 8: auto-record gate writes a build-ticket (sprint-3) ---------
    # The mechanism: empty recall → build-ticket lands in the ledger.
    # Use pure-hex nonce so no common English tokens leak into lexical scoring
    # (tokens like "impossible"/"no"/"match" can push fusion above the noise
    # floor with weak token-overlap — same shape as PROBE 4 uses dashes between
    # words; here we want NO meaningful tokens at all).
    pre_count = len(_read_jsonl(BUILD_TICKETS_PATH))
    nonce8 = "zzz" + secrets.token_hex(16) + "zzz"
    r8 = recall(nonce8, k=5, canon_only=True)  # record_gap defaults True
    post_count = len(_read_jsonl(BUILD_TICKETS_PATH))
    print(f"\nPROBE 8: auto-record gate  verdict={r8['verdict']}  "
          f"tickets {pre_count}→{post_count}")
    if r8["verdict"] != NO_RESULT_VERDICT and r8["verdict"] != "INDEX_MISSING":
        print(f"WARN probe-8: expected empty verdict, got {r8['verdict']}")
    gr8 = r8.get("gap_record")
    if not gr8 or gr8.get("kind") != "build_ticket_recorded":
        print(f"FAIL probe-8: build-ticket NOT recorded (gap_record={gr8})")
        return 1
    if post_count != pre_count + 1:
        print(f"FAIL probe-8: ledger row count did not increment ({pre_count}→{post_count})")
        return 1

    # ---- PROBE 9: tombstone short-circuit (sprint-3) -----------------------
    # File a tombstone, then recall the same query → verdict must be TOMBSTONED
    # and gap_record.kind must be tombstone_hit (no build-ticket written).
    tomb_query = "zzz-tomb-" + secrets.token_hex(12) + "-zzz"
    _append_tombstone(tomb_query, "self-test: explicit tombstone probe9",
                      forward_pointer="tools/canon_recall.py self-test PROBE 9")
    pre9 = len(_read_jsonl(BUILD_TICKETS_PATH))
    r9 = recall(tomb_query, k=5, canon_only=True)
    post9 = len(_read_jsonl(BUILD_TICKETS_PATH))
    print(f"PROBE 9: tombstone short-circuit  verdict={r9['verdict']}  "
          f"tickets {pre9}→{post9} (must NOT change)")
    if r9["verdict"] != "TOMBSTONED":
        print(f"FAIL probe-9: expected TOMBSTONED, got {r9['verdict']}")
        return 1
    if post9 != pre9:
        print(f"FAIL probe-9: tombstoned query MUST NOT write a build-ticket "
              f"({pre9}→{post9})")
        return 1
    gr9 = r9.get("gap_record")
    if not gr9 or gr9.get("kind") != "tombstone_hit":
        print(f"FAIL probe-9: gap_record.kind should be tombstone_hit, got {gr9}")
        return 1

    # ---- PROBE 10: dedupe within window prevents double-record (sprint-3) --
    # Re-run PROBE 8's query within the dedupe window → must dedupe-hit, not
    # write a new row.
    pre10 = len(_read_jsonl(BUILD_TICKETS_PATH))
    r10 = recall(nonce8, k=5, canon_only=True)  # same query as PROBE 8
    post10 = len(_read_jsonl(BUILD_TICKETS_PATH))
    print(f"PROBE 10: dedupe-window  tickets {pre10}→{post10} (must NOT change)")
    if post10 != pre10:
        print(f"FAIL probe-10: dedupe gate failed, ledger grew ({pre10}→{post10})")
        return 1
    gr10 = r10.get("gap_record")
    if not gr10 or gr10.get("kind") != "build_ticket_dedupe_hit":
        print(f"FAIL probe-10: gap_record.kind should be build_ticket_dedupe_hit, got {gr10}")
        return 1

    # ---- PROBE 11: freshness-gate applied + per-hit staleness (sprint-4) ----
    # Recall any real canon entry — gate MUST be present, every hit MUST have
    # a staleness label, and policy MUST be populated from kind-aware defaults.
    # Use record_gap=False to avoid touching the build-ticket ledger (already
    # exercised by probes 8/10 and decoupled from the freshness verdict).
    q11 = "memory-mission validation"
    r11 = recall(q11, k=5, record_gap=False)
    print(f"\nPROBE 11: freshness-gate present  verdict={r11['verdict']}  hits={r11['hit_count']}")
    fg11 = r11.get("freshness_gate")
    if not fg11:
        print(f"FAIL probe-11: result['freshness_gate'] is missing/None")
        return 1
    if "policy" not in fg11 or not fg11["policy"]:
        print(f"FAIL probe-11: freshness_gate.policy is empty: {fg11}")
        return 1
    missing_staleness = [i for i, h in enumerate(r11["hits"])
                        if h.get("staleness") is None]
    if missing_staleness:
        print(f"FAIL probe-11: {len(missing_staleness)} hits missing staleness label")
        return 1
    print(f"  policy_kinds: {list(fg11['policy'].keys())}")
    print(f"  counts: fresh={fg11['fresh_count']} aging={fg11['aging_count']} "
          f"stale={fg11['stale_count']} unknown={fg11['unknown_count']}")
    print(f"  re_verify_required: {fg11['re_verify_required']}")

    # ---- PROBE 12: synthetic-stale entry triggers re_verify_required --------
    # Use a uniform window override of fresh=0/reverify=0 so EVERY hit with a
    # parseable ts becomes "stale" regardless of kind. Gate MUST then set
    # re_verify_required=True AND next_move MUST cite the re-verify path.
    # This validates the gate ACTIVELY FIRES, not just decorates.
    r12 = recall(q11, k=5, record_gap=False, fresh_days=0, reverify_days=0)
    fg12 = r12.get("freshness_gate")
    print(f"\nPROBE 12: synthetic-stale (override 0/0)  hits={r12['hit_count']}")
    if not fg12:
        print(f"FAIL probe-12: freshness_gate missing")
        return 1
    # If there are any hits with a parseable ts (almost certain for canon),
    # they'll bucket as stale → re_verify_required must be True.
    parseable = [h for h in r12["hits"] if h.get("age_days") is not None]
    if parseable and not fg12.get("re_verify_required"):
        print(f"FAIL probe-12: {len(parseable)} hits had parseable ts but "
              f"re_verify_required={fg12.get('re_verify_required')}")
        return 1
    if parseable and fg12.get("stale_count", 0) == 0:
        print(f"FAIL probe-12: {len(parseable)} parseable hits but stale_count=0")
        return 1
    if fg12.get("re_verify_required") and "re-verify" not in (fg12.get("next_move") or "").lower():
        print(f"FAIL probe-12: re_verify_required=True but next_move missing re-verify cue")
        return 1
    print(f"  stale_count={fg12['stale_count']}  re_verify={fg12['re_verify_required']}")
    print(f"  next_move: {fg12.get('next_move','')[:120]}")

    # ---- PROBE 13: gate-disabled passthrough (no-regression) ----------------
    # --no-freshness-gate caller path: result["freshness_gate"] must be None,
    # but recall must still return the same hits — no regression on PASSING
    # write+recall paths.
    r13 = recall(q11, k=5, record_gap=False, freshness_gate=False)
    fg13 = r13.get("freshness_gate")
    print(f"\nPROBE 13: freshness_gate=False  hits={r13['hit_count']}  "
          f"freshness_gate field={fg13}")
    if fg13 is not None:
        print(f"FAIL probe-13: gate disabled but freshness_gate populated: {fg13}")
        return 1
    if r13["hit_count"] != r11["hit_count"]:
        print(f"FAIL probe-13: hit count differs gate-on={r11['hit_count']} "
              f"vs gate-off={r13['hit_count']} (no-regression contract broken)")
        return 1
    # Each hit gets the explicit "gate_disabled" staleness so consumers don't
    # KeyError; the disabled state is auditable.
    if any(h.get("staleness") != "gate_disabled" for h in r13["hits"]):
        bad = [h.get("staleness") for h in r13["hits"]][:3]
        print(f"FAIL probe-13: gate-disabled hits should carry staleness='gate_disabled' got {bad}")
        return 1

    print("\nPASS: canon_recall.py self-test (Track A hybrid + sprint-3 closed-loop + sprint-4 freshness-gate)")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="canon_recall.py",
        description="Structured HYBRID recall (lexical + vector + RRF fusion) over the canon substrate.",
    )
    ap.add_argument("query", nargs="?", help="recall query text")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help=f"results to return (default {DEFAULT_K})")
    ap.add_argument("--lead", default=None, help="restrict to a single VP's canon (e.g. tgim-lead)")
    ap.add_argument("--kind", default=None, help="filter canon entries by kind (e.g. doctrine, finding)")
    ap.add_argument("--max-age-days", type=float, default=None,
                    help="only canon entries newer than N days")
    ap.add_argument("--all-sources", action="store_true",
                    help="include claude_session/primary_memory/vertical_memory (default canon-only)")
    ap.add_argument("--no-lexical", action="store_true",
                    help="disable lexical leg (vector-only, sprint-1 behavior)")
    ap.add_argument("--no-vector", action="store_true",
                    help="disable vector leg (lexical-only, chroma-offline mode)")
    ap.add_argument("--json", action="store_true", help="machine-readable JSON output")
    ap.add_argument("--self-test", action="store_true", help="run end-to-end self-test")
    # --- Build-or-tombstone closed-loop (sprint-3) ---
    ap.add_argument("--no-gap-record", action="store_true",
                    help="do NOT auto-record a build-ticket on empty recall "
                         "(idempotency-loops, self-tests)")
    ap.add_argument("--no-log-hits", action="store_true",
                    help="do NOT log served canon ids to the recall-hits ledger "
                         "(LEARN-read instrument opt-out; idempotency-loops, self-tests)")
    ap.add_argument("--gap-dedupe-window-sec", type=int, default=GAP_DEDUPE_WINDOW_SEC,
                    help=f"dedupe window for build-ticket auto-record (default {GAP_DEDUPE_WINDOW_SEC}s)")
    ap.add_argument("--tombstone", nargs=2, metavar=("QUERY", "REASON"),
                    help="record an explicit tombstone — 'no such canon, intentionally'. "
                         "Future recalls matching QUERY get verdict TOMBSTONED.")
    ap.add_argument("--forward-pointer", default="",
                    help="optional forward-pointer URL/path attached to a tombstone")
    ap.add_argument("--list-tickets", action="store_true",
                    help="print the build-ticket ledger and exit")
    ap.add_argument("--list-tombstones", action="store_true",
                    help="print the tombstone ledger and exit")
    # --- Freshness gate (sprint-4) ---
    ap.add_argument("--no-freshness-gate", action="store_true",
                    help="disable the kind-aware freshness gate (legacy passthrough)")
    ap.add_argument("--fresh-days", type=float, default=None,
                    help="uniform fresh window override (days). "
                         "Beats kind-aware defaults.")
    ap.add_argument("--reverify-days", type=float, default=None,
                    help="uniform re-verify window override (days). "
                         "Beats kind-aware defaults.")
    return ap


def main(argv: list[str] | None = None) -> int:
    ap = _build_parser()
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()

    # --- Tombstone-record mode (one-shot, no recall) -----------------------
    if args.tombstone:
        q_arg, reason_arg = args.tombstone
        row = _append_tombstone(q_arg, reason_arg, forward_pointer=args.forward_pointer)
        if args.json:
            print(json.dumps(row, indent=2))
        else:
            print(f"[canon_recall] tombstone recorded: query={q_arg!r}")
            print(f"  reason: {reason_arg}")
            if args.forward_pointer:
                print(f"  forward-pointer: {args.forward_pointer}")
            print(f"  path: {TOMBSTONES_PATH}")
        return 0

    # --- List-tickets mode -------------------------------------------------
    if args.list_tickets:
        rows = _read_jsonl(BUILD_TICKETS_PATH)
        if args.json:
            print(json.dumps({"path": str(BUILD_TICKETS_PATH), "count": len(rows), "rows": rows},
                             indent=2, default=str))
        else:
            print(f"[canon_recall] build-tickets ledger: {BUILD_TICKETS_PATH}")
            print(f"  total rows: {len(rows)}")
            for r in rows[-20:]:
                print(f"    {r.get('ts')}  v={r.get('verdict','?')}  q={r.get('query','')[:80]!r}")
        return 0

    # --- List-tombstones mode ----------------------------------------------
    if args.list_tombstones:
        rows = _read_jsonl(TOMBSTONES_PATH)
        if args.json:
            print(json.dumps({"path": str(TOMBSTONES_PATH), "count": len(rows), "rows": rows},
                             indent=2, default=str))
        else:
            print(f"[canon_recall] tombstones ledger: {TOMBSTONES_PATH}")
            print(f"  total rows: {len(rows)}")
            for r in rows:
                print(f"    {r.get('ts')}  q={r.get('query','')[:60]!r}  reason={r.get('reason','')[:60]!r}")
        return 0

    if not args.query:
        ap.print_help()
        return 2

    r = recall(
        args.query,
        k=args.k,
        lead=args.lead,
        kind=args.kind,
        max_age_days=args.max_age_days,
        canon_only=(not args.all_sources),
        use_lexical=(not args.no_lexical),
        use_vector=(not args.no_vector),
        record_gap=(not args.no_gap_record),
        dedupe_window_sec=args.gap_dedupe_window_sec,
        log_hits=(not args.no_log_hits),
        freshness_gate=(not args.no_freshness_gate),
        fresh_days=args.fresh_days,
        reverify_days=args.reverify_days,
    )

    if args.json:
        print(json.dumps(r, indent=2, default=str))
    else:
        print(f"\n[canon_recall] verdict={r['verdict']}  hits={r['hit_count']}  "
              f"retrievers={r['retrievers_fired']}  low_conf={r['low_confidence']}  "
              f"chroma={r['chroma_path']}\n")
        print(f"query: {r['query']!r}")
        if r.get("lead"):
            print(f"lead-filter: {r['lead']}")
        if r.get("kind"):
            print(f"kind-filter: {r['kind']}")
        if r.get("max_age_days") is not None:
            print(f"max-age-days: {r['max_age_days']}")
        print()
        for h in r["hits"]:
            flags = []
            if h.get("in_lexical"): flags.append("L")
            if h.get("in_vector"): flags.append("V")
            if h.get("lexical_exact"): flags.append("EX")
            head = (
                f"#{h['rank']} [{h['source']}/{h.get('lead','')}] "
                f"fs={h.get('fusion_score',0):.4f} d={h.get('distance', 0):.3f} "
                f"flags={','.join(flags) or '-'}"
            )
            if h.get("kind"):
                head += f"  kind={h['kind']}"
            if h.get("freshness"):
                head += f"  freshness={h['freshness']}"
            if h.get("staleness"):
                head += f"  staleness={h['staleness']}"
            print(head)
            print(f"  id: {h.get('id') or '-'}")
            print(f"  ts: {h.get('ts') or '-'}")
            print(f"  path: {h.get('path')}")
            item = h.get("item") or h.get("preview") or ""
            print(f"  item: {item[:240]}")
            print()
        print(f"next_move: {r['next_move']}")
        # Surface the freshness-gate verdict (sprint-4) on the human surface.
        fg = r.get("freshness_gate")
        if fg:
            reverify_flag = "RE-VERIFY-REQUIRED" if fg.get("re_verify_required") else "ok"
            print(f"freshness_gate: [{reverify_flag}]  "
                  f"fresh={fg.get('fresh_count',0)} aging={fg.get('aging_count',0)} "
                  f"stale={fg.get('stale_count',0)} unknown={fg.get('unknown_count',0)}")
            print(f"  next_move: {fg.get('next_move','')}")
        if r.get("warnings"):
            print(f"warnings: {r['warnings']}")
        # Surface the closed-loop gap-record so callers see THE SUBSTRATE was
        # updated (not just stdout).
        gr = r.get("gap_record")
        if gr:
            kind = gr.get("kind", "?")
            if kind == "build_ticket_recorded":
                row = gr.get("row", {})
                print(f"gap_record: BUILD-TICKET WRITTEN to {BUILD_TICKETS_PATH.relative_to(_AICIV_ROOT)}")
                print(f"  ts={row.get('ts')}  hash={row.get('query_hash')}  actor={row.get('actor')}")
            elif kind == "build_ticket_dedupe_hit":
                print(f"gap_record: dedupe-hit (existing ticket @ {gr.get('existing_ts')}, "
                      f"window {gr.get('window_sec')}s) — not re-writing.")
            elif kind == "tombstone_hit":
                tb = gr.get("tombstone", {})
                print(f"gap_record: TOMBSTONED — see {TOMBSTONES_PATH.relative_to(_AICIV_ROOT)} "
                      f"(filed {tb.get('ts')})")
    # Non-error exit; verdict carries signal. INDEX_MISSING returns 0 too so
    # callers/cron don't task_failed when chroma is being rebuilt — the verdict
    # is the actionable signal.
    return 0


if __name__ == "__main__":
    sys.exit(main())
