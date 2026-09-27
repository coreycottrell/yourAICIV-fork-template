#!/usr/bin/env python3
"""
session_review.py — Stage-1 of the HUM grader (deterministic layer).

  🌱 FORK CONFIG — {AICIV-NAME} / {STEWARD-NAME} (READ BEFORE YOU RELY ON THE BLOCK/WWCW GATES):
    Several LOAD-BEARING regexes below embed the ORIGIN steward's name as a literal token —
    "corey" — because they detect block-language ("HELD-FOR-STEWARD", "parked for corey",
    "awaiting corey", "needs corey") and WWCW-run evidence ("what would corey want",
    "simulate corey", "given his rules"). These literals are INTENTIONALLY left as the origin
    value so the tool RUNS without edits — but for YOUR fork they will silently MISS your own
    blocks/WWCW-runs (e.g. "HELD-FOR-SAM", "what would Sam want") until you replace the steward-name
    token. DO NOT naively sed "corey" → "{STEWARD-NAME}" (that creates a literal that matches the
    characters "{STEWARD-NAME}", breaking the gate). INSTEAD: search this file for the lowercase
    token `corey` inside `re.compile(...)` patterns (BLOCK_RE, BLOCK_CAPS_FLAG_RE, WWCW_TEXT_RE,
    WWCW_EVIDENCE_RE, WWCW_SIMULATE_RE, GENUINE_ASK_RE, DEFER_TO_HUMAN_RE) and substitute YOUR
    steward's name. The narrative changelog/docstring uses of "the steward" below are origin-civ dated
    lineage — they are harmless and need no change.

WHAT THIS IS
  A pure, deterministic, stdlib-only reviewer of a Claude-Code session JSONL
  transcript. It parses the session, walks turns in order, and runs each of
  qa-lead's deterministic checks (WWCW-GATE, BLOCK-NO-WWCW, MODEL-PIN, MEMORY-EMIT,
  CLAIM-BACKING, DONE-DONE, SYNTHETIC-ERROR, SKILL-FLOOR, SKILL-CANDIDATE,
  DELEGATION-SHAPE, PROJECT-FOLDER-TOUCH, DOC-CURRENCY, SWEEP-ACT-ON-FLAGGED,
  SPRINT-MODE-READ, HAIKU-PER-DOC,
  GROUNDING-COMPLETENESS, FREEZE-EDIT, FREEZE-CONFIG-MISSING). It
  emits a JSON findings record that a Stage-2 judging mind (the HUM grader) reads.

  🚨 GROUNDING-COMPLETENESS (2026-06-20, steward directive) is the COMPLETE-OR-FAIL gate: a grounding
  boop that did substantive grounding work but is MISSING ≥1 required element (any per-doc haiku short
  of the docset, OR a missing load-verify / synthesis / workflows-mandate / wwcw / hum / auto-consolidate
  / hum-fired step) → status=flag → in the hard-fail set → breaks summary.clean → the boop FAILS. STRICT:
  partial completion = full failure. "Miss one doc or one haiku or one step it's 100% fail on that boop.
  The discipline is EVERYTHING." — the steward 2026-06-20. SUPERSEDES the narrower SPRINT-MODE-READ +
  HAIKU-PER-DOC receipts (which a single haiku + a single load-verify line could pass).
  🚨 v5.1 (2026-06-20, the steward `"lean cycle" < discipline`): the contract now fires on a GENUINE /sprint-mode
  boop too (a /sprint-mode command-message/calendar boop + ≥1 work-act, NOT a byte-identical re-injection
  within SPRINT_DEDUP_WINDOW_SECONDS), not just on the haiku-bearing slow-sprint shape. A LEAN /sprint-mode
  cycle (genuine boop + work but no full grounding) now FLAGS → FAILS — closing the false-fail-guard dodge
  Primary used ~4x in a day. THE DEDUP WINDOW IS THE CADENCE KNOB (default 60 = strict per-cycle; widen to
  3600 = per-hour). The only two exemptions left: a 60s byte-identical dedup re-injection + a non-/sprint-
  mode turn.
  🚨 v5.2 (2026-06-20, fleet-lead — RECENCY-EXEMPTION KILL, the CLOCKWORK-EVERY-FIRE design; the steward "Hum
  every cycle FOR SURE"). The v5.1 close left ONE residual leak on TRIGGER-1: a BARE grounding-pass with
  NO work-signatures was exempted via `did_grounding_work=False` EVEN WITHOUT clustered-re-fire corroboration
  (the old `else` brief PASSED it as "not a substantive grounding boop"). That was the recency-as-excuse
  residue ("I grounded recently → a bare grounding-pass skips the contract"). v5.2 narrows the
  did_grounding_work exemption to a CORROBORATED clustered re-fire ONLY (a recognized byte-identical re-fire,
  evidenced by the dedup marker OR prior-boop archive haikus in the ts-range). An UNCORROBORATED bare
  grounding-pass now FALLS THROUGH to grading → every element missing → 100% FAIL (recency_dodge=True,
  did_grounding_work reported honestly). The two HONEST exemptions are UNCHANGED: (a) the 60s byte-identical
  dedup re-injection (kept_boops-empty path), (b) a non-/sprint-mode turn. What is GONE is the abused third
  path. Every genuine fire now grounds fully + fires HUM — clockwork.

  🚨 BLOCK-NO-WWCW (2026-06-20, steward directive) is the ONE HARD-FAIL DECIDE check: a BLOCK
  (park / hold / present-for-confirmation / flag-as-needing-the steward) present in the scanned window
  with NO evidence the WWCW skill was actually RUN → status=flag → breaks summary.clean → the boop
  FAILS. It SUPERSEDES the too-narrow over-deference path inside WWCW-GATE (which a bare park slipped
  past). WWCW-GATE stays candidate-only (finer DECIDE taxonomy for the grader); BLOCK-NO-WWCW is the
  enforcement. "If no evidence of wwcw run it's to fail your boop." — the steward 2026-06-20.

  This is the DETERMINISTIC layer ONLY. It contains NO LLM call. It makes no
  judgment of intent — it surfaces mechanical signals + positions. Anything
  requiring reading-comprehension or intent (e.g. "was this PASS claim actually
  earned?") is left to Stage-2 and is emitted here as a CANDIDATE hit, not a
  verdict.

SECURITY / PII
  CRITICAL: this tool NEVER writes message text, tool inputs, secrets, file
  contents, emails, tokens, or PII into the findings record. Hits carry a
  turn_index + a short, non-sensitive `brief` that names only the MECHANICAL
  trigger (marker matched, tool name, check id) — never the surrounding human
  text. Freeze-path hits emit the path only (paths are not secrets; their
  contents are never read). When in doubt, fewer characters.

OUTPUT SHAPE
  {
    "session_id": "<uuid or filename stem>",
    "session_path": "<abs path>",
    "turns_scanned": <int>,
    "checks": [
      {"id": "WWCW-GATE", "status": "pass|flag|na", "hits": [{"turn_index": N, "brief": "..."}]},
      ...
    ],
    "summary": {"flagged": [...ids...], "candidate": [...ids...], "na": [...ids...], "clean": bool}
  }

STATUS SEMANTICS
  pass  — check ran, found nothing to flag.
  flag  — check ran, found mechanical hit(s). Some checks only ever produce
          CANDIDATE hits (CLAIM-BACKING, DONE-DONE, DELEGATION-SHAPE Stage-2);
          those still set status=flag but each hit is marked candidate=true and
          the check id is listed under summary.candidate as well.
  na    — check could not run as a deterministic test on this session
          (e.g. FREEZE-EDIT / FREEZE-CONFIG-MISSING with no freeze config given).

USAGE
  python3 tools/session_review.py [SESSION.jsonl]
  python3 tools/session_review.py                      # newest session in default project dir
  python3 tools/session_review.py --freeze-config cfg.json
  python3 tools/session_review.py --pretty
  python3 tools/session_review.py --help

FREEZE CONFIG (optional, JSON)
  { "freeze_globs": ["autonomy/skills/self-knowledge/**", "..."],
    "window_start": "2026-06-17T00:00:00Z",   # ISO8601, inclusive
    "window_end":   "2026-06-19T00:00:00Z" }  # ISO8601, exclusive
  If absent OR missing globs/window -> FREEZE-EDIT = na, FREEZE-CONFIG-MISSING = flag.

CHANGELOG
  2026-06-18 (fleet-lead, v1.0) — NEW FILE. Built per qa-lead Stage-1 HUM-grader
      spec (10 deterministic checks). Pure stdlib json parse, no LLM. PII-safe
      findings (positions + mechanical briefs only). Tested on a real 5418-line
      the civilization session. Honest noise notes for the candidate-only checks are recorded
      in the spec discussion, not in code: CLAIM-BACKING / DONE-DONE / SKILL-FLOOR
      are heuristic and emitted as CANDIDATE / advisory, never hard verdicts.
  2026-06-18 (fleet-lead, v1.1) — Closure-3 of the consolidation/HUM backstop.
      Added the SKILL-CANDIDATE check (11th): deterministic, candidate-only, two
      signals — (a) REMEMBER_MARKER_RE over REAL user turns (the human-asked-
      workflow / human-signaled-ability signal auto-consolidate Step 4a/4b chases),
      and (b) the SAME Bash command-shape (leading verb) repeating >=2x with no
      Skill load between (a step-sequence re-done by hand = a candidate for a wired
      skill). PII-safe (marker class / command-shape + turn_index only — never the
      human text, never the full command). Stage-2 reads these hits, runs TRI-SOURCE
      dedup {exists-good | needs-update | needs-create}, and routes a genuine
      reusable capability to skill-forge. Heuristic → candidate-only, never a hard
      verdict (same discipline as CLAIM-BACKING/DONE-DONE/SKILL-FLOOR). Backup:
      tools/session_review.py.bak.20260618T172645Z.
  2026-06-19 (workflow-lead, v1.2) — HUM v0.2 CYCLE-DELTA SCOPING. Added the
      `--since-turn N` argument. When N>0, the deterministic checks flag ONLY turns
      whose idx > N (the NEW turns since the last HUM grade of this session). The
      cursor (.claude/team-leads/mind/memory/hum-cursor.json, written by hum.js)
      passes the last-graded turn index; this removes the O(session²) re-walk where
      each fire re-scanned ~2500 overlapping turns. Default (absent / N=0) PRESERVES
      the prior full-session behavior EXACTLY (idx > 0 keeps every 0-based turn whose
      idx >= 1, AND we special-case N<=0 to keep idx 0 too — see _filter). LOAD-
      BEARING INVARIANT: this scopes DETECTION only. The Stage-2 judge still reads
      the FULL session transcript (session_path) to WALK any flagged turn — a flag at
      turn 2750 may need context from turn 40. `--since-turn` filters which turns get
      SCANNED for flags; it NEVER filters what the judge may read to confirm intent.
      Backup: tools/session_review.py.bak.20260619T093208Z.
  2026-06-19 (mind-lead + workflow-lead, v1.3) — PROJECT-FOLDER-COMPLIANCE. Added the
      12th check, PROJECT-FOLDER-TOUCH (deterministic, candidate-only). It walks Edit/Write
      tool-uses, detects which projects/<x>/ folders were TOUCHED this cycle (scoped window),
      and whether each touched project's DEVLOG/CHANGELOG/PROGRESS/MASTER-INDEX/ADR was updated
      in the SAME cycle. A touched-but-undevlogged project = a CANDIDATE compliance defect (the
      moon-project-systems living-master rots otherwise). Compliant projects are surfaced as
      informational hits (devlog_updated=true) so the HUM compliance phase can report the full
      {folders_touched, devlogs_updated} picture without re-deriving it. PII-safe (project name +
      file BASENAME only — paths are not secrets, contents never read). ADDITIVE: does NOT touch
      the v1.2 --since-turn cursor/scoping logic or any existing check. Heuristic -> candidate-only,
      never a hard verdict (same discipline as the other Stage-2-candidate checks). Backup:
      tools/session_review.py.bak.20260619T110214Z-pre-project-folder-compliance.
  2026-06-19 (fleet-lead, v1.4) — GROUNDING-RECEIPT (steward directive: HUM must CONFIRM the ACTUAL
      RECEIPT of the grounding floor, not a claim). Added the 13th + 14th checks — SPRINT-MODE-READ
      and HAIKU-PER-DOC (both deterministic, candidate-only, ADDITIVE — never hard-fail, never block).
      The principle: the gate is PROVEN by the artifact it leaves (the load-verify block + the
      haiku-archive entries), exactly like canon_recall's hit-ledger proves recall — NOT by a
      self-report. (1) SPRINT-MODE-READ: a /sprint-mode|grounding pass was invoked but the load-verify
      FLOOR block (>=2 `skill_loaded:`/`*_loaded:` lines from the sprint-mode SKILL) was never ACTUALLY
      written this session (assistant text OR a scratchpad Write) -> flag (floor read claimed, not
      received). (2) HAIKU-PER-DOC: a /grounding-docs|slow-sprint pass was invoked but
      data/haiku-archive/haikus.jsonl got ZERO fresh {ts,doc,haiku} entries inside THIS session's
      time-window -> flag (comprehension gate claimed, not received); surfaces fresh-count + distinct-
      doc count so a SHALLOW grounding is weighable. WHOLE-SESSION INVARIANT: both checks run against
      the FULL session (not the --since-turn delta) because the floor read + haiku gate fire at session
      START — delta-scoping would falsely flag every later fire. Threaded via run_all/build_record
      full_turns. PII-safe (counts + marker-class + haiku DOC labels only — never human text, never
      the haiku body). FAIL-SOFT: archive unreadable / no session timestamps -> candidate NA note,
      never a crash. Backup: tools/session_review.py.bak.20260619T173214Z-pre-grounding-receipt.
  2026-06-19 (mind-lead, v1.5) — DOC-CURRENCY (the DOC-UP-TO-DATE mandate). steward directive: "HUM is
      supposed to MANDATE keeping these things up to date... not wired sufficiently." The v1.3
      PROJECT-FOLDER-TOUCH check was too NARROW (projects/<x>/ devlog only). Added the 15th check —
      DOC-CURRENCY (deterministic, candidate-only, ADDITIVE — never hard-fails, never blocks). It
      detects the BROADER documentation-staleness that lets a day evaporate: keep-worthy work landed
      this cycle (canon_append Bash calls + new data/reports/*.md Writes + finish-list/mission/vision/
      ratified DECISION markers) WITHOUT a corresponding update to the civ-level doc surfaces (WORKBOARD
      + the named program-home devlogs self-knowledge/SKILL.md + m3-combo-mastery/SKILL.md). RECEIPT NOT
      CLAIM (the steward today: verify ACTUAL RECEIPT — the behavior happened on disk): it reads each surface's
      on-disk os.path.getmtime (contents NEVER read) and compares to the LATEST keep-worthy turn's epoch
      timestamp. A surface whose mtime is OLDER than the latest keep-worthy work (or is MISSING) = STALE
      = ONE candidate hit carrying the actual mtime-delta-seconds (the receipt). A surface updated
      at/after the work = informational compliant hit (so HUM reports the full {stale, current} picture).
      VACUOUS-PASS: if NO keep-worthy work happened this cycle, nothing to keep current -> pass, no hits.
      Uses the (delta-scoped) `turns` like the other candidate checks. PII-safe (surface label +
      mtime-delta-seconds + keep-worthy counts only — never file content, never human text, never a
      canon item body). Does NOT touch the v1.2 cursor/scoping, v1.3 PROJECT-FOLDER-TOUCH, or v1.4
      grounding-receipt logic. Backup: tools/session_review.py.bak.20260619T173642Z-pre-doc-currency-final.
  2026-06-19 (mind-lead, v1.5.1) — DOC-CURRENCY PATH FIX (first-run FALSE-POSITIVE cure). The v1.5
      DOC_CURRENCY_SURFACES "devlog" entries pointed at the SKILL.md skill DEFINITIONS
      (autonomy/skills/self-knowledge/SKILL.md + autonomy/skills/m3-combo-mastery/SKILL.md) instead of
      the PROGRAM-HOME DEVLOGs where the document-the-day LEARN entries actually land. On the v1.5 first
      run the check flagged self-knowledge STALE (-148056s ≈ -41h) — but that delta was the SKILL.md's
      mtime (last edited 2026-06-17 20:23), NOT the real doc. The real projects/self-knowledge/DEVLOG.md
      was ~28min fresh (mtime 2026-06-19 13:20) and CONTAINED that day's LEARN entries (LEARN-at-load,
      two-halves, recall-hit-rate 0.0052, skill-load-health). So the document-the-day update DID land;
      the check read the wrong file. ROOT CAUSE = WRONG PATH (not a delta/timezone bug — the epoch math
      is correct: it returned -28min for the real DEVLOG and -41h for the wrong SKILL.md). m3-combo had
      the SAME wrong-path defect, masked only because its SKILL.md happened to be touched that day
      (-112min, within grace). FIX: point both surfaces at projects/self-knowledge/DEVLOG.md and
      projects/AI-CIV/m3-combo/DEVLOG.md. Re-validated on the current session: self-knowledge now reads
      CURRENT (-29min real DEVLOG), m3-combo stays CURRENT (-28min real DEVLOG), WORKBOARD stays CURRENT
      (-27min). No other logic touched (grace window, scoping, signals, delta math all unchanged).
      Backup: tools/session_review.py.bak.20260619T175018Z-pre-doc-currency-path-fix.

  2026-06-19 (fleet-lead, v1.6) — GROUNDING-RECEIPT HARD-FAIL (steward directive verbatim: "Hum needs to
      FAIL your sprint mode boops if they can't find proof you did it correctly"). PROMOTED the v1.4
      grounding-receipt checks (SPRINT-MODE-READ + HAIKU-PER-DOC) from CANDIDATE-only (warn+route, never
      breaks clean) to HARD-FAIL via the new GROUNDING_RECEIPT_HARDFAIL_CHECKS set. A GENUINE flag from
      either check (a /sprint-mode|grounding boop ACTUALLY RAN this session AND the proof is ABSENT — no
      load-verify floor block written AND/OR zero fresh haiku-archive entries in-window) now lands in
      summary.flagged → breaks summary.clean. The unproven sprint is a FAILED boop on the record, loud +
      surfaced. ZERO change to WHEN a flag fires: the detection inside check_sprint_mode_read /
      check_haiku_per_doc ALREADY scopes airtight (a non-sprint / pure-notification / no-grounding-claimed
      session takes the `invoked_idx is None` branch → status="pass" → never enters hard-fail; a
      received/compliant/N-A/could-not-verify[-1] hit is status="pass" → never hard-fail). This edit
      changes ONLY the SUMMARY classification of a flag (hard vs candidate). The checks REMAIN in
      CANDIDATE_CHECKS so each HIT still carries candidate=True for the Stage-2 judge's per-hit WALK —
      a check in BOTH sets that flags is classified HARD (flagged) by an explicit BEFORE-fallthrough
      branch in build_record. FALSE-FAIL GUARD (an hour after a sibling doc-currency check false-positived
      on a wrong path): validated on (a) the live grounded session 303ecb5f → both PASS (floor block
      received via scratchpad-write + 26 fresh haikus across 23 docs) → clean unaffected by these checks;
      (b) a synthetic sprint-ran-but-no-proof session → SPRINT-MODE-READ + HAIKU-PER-DOC FLAG → clean=False;
      (c) a synthetic non-sprint session → both PASS → no false-fail. Backup:
      tools/session_review.py.bak.20260619T175645Z-pre-grounding-hardfail. Companion: workflows/hum.js v0.6
      (the GRADER's GROUNDING-RECEIPT dimension is now a deterministic verdict-failing dimension).
  2026-06-20 (fleet-lead, v1.7) — BLOCK-NO-WWCW HARD-FAIL (steward directive verbatim: "'What needs you' is a
      block and i see zero evidence that you ran the wwcw skill. And zero evidence that hum caught you... If
      no evidence of wwcw run it's to fail your boop"). ROOT-CAUSE: the v1.x over-deference path was TOO
      NARROW. check_wwcw_gate fired on only (1) ASK_DECIDE_RE + no-WWCW, OR (2) a WWCW-marker + CONFIDENCE_RE
      + DEFER_TO_HUMAN_RE. A BARE PARK ("Parked for the steward", "HELD-FOR-STEWARD", "what needs you") has NO
      ASK_DECIDE verb and NO WWCW+confidence pair, so it slipped past BOTH (0/9 real parked phrases from the
      failing session matched either). And WWCW-GATE is CANDIDATE-only → structurally could not fail a boop.
      THE FIX (4 parts): (a) BLOCK_RE — a BROAD park-language family (parked/awaiting/held-for-steward, needs
      corey, what-needs-you, what-would-you-like, for-your-approval, your-call, should-I, do-you-want-me-to,
      let-me-know-if, standing-by, pending-your, I'll-hold, presenting-options-for-confirmation, say-the-word,
      on-your-go). (b) WWCW_EVIDENCE_RE — proof the doctrine ACTUALLY RAN (ruleset load / simulate-the steward /
      what-would-the steward-want reasoning / RATE-confidence / ACT+RECORD / explicit "ran WWCW") — a MENTION is NOT
      a run. (c) NEW check_block_no_wwcw (id BLOCK-NO-WWCW): ≥1 BLOCK in the window AND zero WWCW-run evidence
      in the window → status=flag, candidate=False. (d) BLOCK-NO-WWCW is in CHECK_ORDER + the new
      BLOCK_NO_WWCW_HARDFAIL_CHECKS set + ABSENT from CANDIDATE_CHECKS → a genuine flag breaks summary.clean →
      the boop FAILS (not flagged-soft). WWCW-GATE RETAINED (its finer DECIDE taxonomy still feeds the grader)
      but is now the SUPERSEDED narrow layer; BLOCK-NO-WWCW is the enforcement. FALSE-FAIL GUARD: fires ONLY
      when a real BLOCK exists AND the window holds ZERO WWCW footprint — a no-block session, a status-only
      session (BLOCK_RE is anchored to park/hold/ask-for-the steward shapes, never a bare question mark), or any
      window with a real WWCW run = status="pass". Backup:
      tools/session_review.py.bak.20260620T131343Z-pre-block-no-wwcw. Companion: workflows/hum.js v0.7 (the
      grader forces DECIDE=HOLLOW + verdict=HOLLOW on a deterministic BLOCK-NO-WWCW flag — mirror of the v0.6
      grounding-receipt hard-fail).

  2026-06-20 (mind-lead, v1.8) — BLOCK-NO-WWCW v2: CO-LOCATED REAL-RUN FOOTPRINT (fixes the auditor's v1
      FAIL). The v1.7 evidence test (window_has_wwcw_evidence) was a WINDOW-WIDE VOCABULARY scan: ONE match
      of WWCW_EVIDENCE_RE (which matched WWCW VOCABULARY — the ruleset path / 'simulate corey' / a bare
      'ran WWCW' token) ANYWHERE in the scanned window cleared EVERY block in the window. Auditor's verbatim
      FAIL: "Real-path walk on THIS session (177 BLOCK turns) returned pass/hit=0 … one match clears the
      whole window. False-negative on every WWCW-touching session." PROVEN: on the live 4736-turn session,
      178 bare-park BLOCK turns (idx 5/26/29/70…) were cleared by a SINGLE 'ran WWCW' mention at turn 1506
      (~1500 turns away) → status=pass on a session full of unresolved parks. The fix (the ONE broken piece —
      WWCW_EVIDENCE_RE / check_block_no_wwcw; the rest of v1.7 KEPT intact): (a) 3 NEW regexes replace the
      window-wide vocabulary scan as the gate — WWCW_SIMULATE_RE (the SIMULATE-the steward derivation beat),
      WWCW_RESOLVE_RE (the RESOLVE beat — ACT+RECORD or ASK-SHOWING-WORK precise sub-fork), WWCW_MARKER_RE
      (the structured-marker bonus fast-path: WWCW-RUN:/ACT+RECORD:/WWCW VERDICT:). (b) CO-LOCATION: each
      block is cleared ONLY by a footprint within ±WWCW_COLOCATION_TURNS (=8) of the block turn — never
      anywhere-in-session; a run 1500 turns away can no longer clear a bare park at turn 5. (c) REAL-RUN
      FOOTPRINT (resolution structure): a block clears iff a co-located turn-window holds BOTH a SIMULATE
      AND a RESOLVE (the 5-beat resolution), OR a structured marker, OR a Skill('wwcw') load. A SIMULATE
      with no RESOLVE = a run left HANGING (a bare park) → still FAIL. A RESOLVE with no SIMULATE = action
      with no the steward-sim → still FAIL. The discriminator that MATTERS (the steward): was the block RESOLVED by a
      run, or left hanging as 'awaiting the steward'? (d) the check FLAGS if ANY block is left UNCLEARED; the hit
      now carries uncleared_block_count / cleared_block_count / colocation_turns (window_has_wwcw_evidence
      KEPT for grader/back-compat). WWCW_EVIDENCE_RE RETAINED as legacy/informational only (no longer the
      gate). Re-validated: live session 303ecb5f now FLAGS (178 blocks, 1 cleared, 177 uncleared → clean=False;
      v1.7 falsely returned pass). 9-case test battery PASS (bare-park/distant/hanging-run/action-no-sim
      FLAG; co-located-run/marker/skill-load/no-block/status-only PASS). ENFORCEMENT HONESTY: this is the
      deterministic session_review backstop layer feeding the BEHAVIORAL judging-mind at the HUM step — NOT
      a settings.json structural hook. Backup: tools/session_review.py.bak.20260620T173000Z-pre-v2-colocated-wwcw.
      Companion: workflows/hum.js (grader prompt updated to v2 co-located semantics; the deterministic
      DECIDE=HOLLOW/verdict=HOLLOW backstop on block_no_wwcw.failed is UNCHANGED — it reads the SAME
      status=flag signal).

  2026-06-20 (mind-lead, v1.9) — BLOCK-NO-WWCW v3: MARKER MUST CO-LOCATE A SIMULATE (closes the v2 marker
      leak). The v2 auditor's residual (verbatim): "WWCW_MARKER_RE marker fast-path clears a block on a
      BARE 'ACT+RECORD:' token alone, no simulate (adv7=pass), contradicting spec's RESOLVE-without-
      SIMULATE-must-FAIL. v1 vocab-bug in miniature (±8 turns) — narrower but a real lying-check path.
      Fix: marker must co-locate a SIMULATE." Also adv2 (resolve-no-sim) PASSed but should FAIL — same
      root cause: v2's _block_cleared_by_colocated_run had THREE clear-paths and TWO of them were
      back-doors around the AND — `if saw_marker: return True` cleared on a bare structured marker, and
      `if saw_skill: return True` cleared on a bare Skill('wwcw') load — neither required a SIMULATE.
      THE v3 FIX (the ONE broken piece — _block_cleared_by_colocated_run; everything else in v2 KEPT):
      collapse the three clear-paths into a SINGLE conjunction — a block clears IFF a co-located
      SIMULATE-the steward footprint (WWCW_SIMULATE_RE — the 'given his rules → what the steward wants' derivation)
      AND a co-located RESOLVE footprint BOTH appear within ±WWCW_COLOCATION_TURNS. The RESOLVE half is
      satisfied by a WWCW_RESOLVE_RE match OR a structured WWCW marker OR a Skill('wwcw') load (all are
      resolution-shaped), but the SIMULATE half is ALWAYS required. NEITHER half alone clears: a bare
      'ACT+RECORD:' marker, a bare resolve, a bare wwcw token, a bare simulate, or a bare skill-load each
      stand the block. KEPT EXACTLY: the ±8 co-location window (no whole-session clear, v2), the
      BLOCK-NO-WWCW hard-fail wiring (CHECK_ORDER + BLOCK_NO_WWCW_HARDFAIL_CHECKS, ABSENT from
      CANDIDATE_CHECKS → a genuine flag breaks summary.clean), and the hum.js L1029 deterministic
      DECIDE=HOLLOW/verdict=HOLLOW backstop on block_no_wwcw.failed (it reads the SAME status=flag signal —
      v3 only changes WHEN status=flag fires, never the consumer contract). FALSE-FAIL GUARD: a block with
      a co-located SIMULATE+RESOLVE (real run) still CLEARS; a no-block / status-only session still PASSES.
      Re-validated with a 12-case battery (incl. the auditor's adv2 resolve-no-sim + adv7 bare-marker, both
      now FLAG; co-located simulate+marker / simulate+resolve / simulate+skill-load PASS; bare-simulate /
      bare-skill / bare-wwcw-token / distant-run / no-block / status-only behave correctly). Backup:
      tools/session_review.py.bak.20260620T140031Z-pre-v3-marker-needs-simulate. Companion: workflows/hum.js
      UNCHANGED (it consumes the status=flag signal; the deterministic HOLLOW backstop is untouched).

  2026-06-20 (mind-lead, v2.0) — GROUNDING-COMPLETENESS HARD-FAIL (the COMPLETE-OR-FAIL gate). the steward
      directive verbatim: "Hum needs to check and fully FAIL any boop that isn't hyper detailed and
      complete. Miss one doc or one haiku or one step it's 100% fail on that boop. The discipline is
      EVERYTHING." CONTEXT: the afternoon /sprint-mode cycles (12:51 / 13:53 / 14:55) wrote CHEAP
      receipts — ONE haiku each, a bare load-verify line, NO per-doc haiku, NO read-one-at-a-time, NO
      auto-consolidate sweep, HUM DEFERRED — and PASSED the narrower SPRINT-MODE-READ + HAIKU-PER-DOC
      receipts (which only confirm SOME artifact landed; a single haiku + a single load-verify line
      passes both). The new 17th check check_grounding_completeness (id GROUNDING-COMPLETENESS,
      deterministic, HARD-FAIL, ABSENT from CANDIDATE_CHECKS) enforces the FULL written contract the
      sprint-mode + grounding-docs SKILLs now DECLARE. STRICT (no partial credit): a grounding boop is
      graded against an ENUMERATED 8-element checklist — (1) ≥GROUNDING_COMPLETE_DOCSET (10) DISTINCT
      fresh in-window per-doc haikus [count haikus == count docs, the exact afternoon miss],
      (2) load-verify block, (3) synthesis statement, (4) workflows-for-everything mandate, (5) WWCW
      affirmation, (6) HUM/human-bridge affirmation, (7) auto-consolidate sweep, (8) HUM fired as last
      step (Workflow(workflows/hum.js) seen). If ANY required element is absent → status=flag →
      GROUNDING_COMPLETENESS_HARDFAIL_CHECKS → breaks summary.clean → the boop FAILS (forced HOLLOW in
      hum.js). 🛡️ FALSE-FAIL GUARD (HONEST, the steward's explicit guard): fires ONLY on a boop that DID
      substantive grounding work — GROUNDING_PROMPT_RE invoked (haiku-bearing shape; bare lean
      /sprint-mode exempt — no haikus) AND ≥1 grounding-work-signature (≥1 fresh haiku-doc OR the
      load-verify block OR a doc-read marker). A pure status reply / notification / no-grounding session
      = pass, never hard-fails. ARCHIVE-UNVERIFIABLE: haiku archive unreadable / no session timestamps →
      the per-doc-haiku element is could-not-verify, NOT a miss (never fail what we could not check) —
      the other 7 in-session elements stay required. WHOLE-SESSION (runs against full_turns like the two
      receipt checks — the elements land at grounding time; delta-scoping would falsely flag later
      cycles). PII-safe (counts + element labels + marker classes only). Backup:
      tools/session_review.py.bak.20260620T145803Z-pre-grounding-completeness. Companion: workflows/hum.js
      v0.9 (grounding_completeness firewall field + a deterministic verdict=HOLLOW backstop the LLM grader
      cannot launder) + sprint-mode/SKILL.md + grounding-docs/SKILL.md (the DECLARED completeness contract).

  2026-06-20 (mind-lead, v4) — BLOCK-NO-WWCW v4: PRIMARY-AUTHORED-ONLY block test (HUM caught its OWN
      false-positive — wxxeuo7j2). THE FALSE-POSITIVE: BLOCK-NO-WWCW flagged a turn whose matched block-vocab
      was NOT a real Primary park — it was (a) block-vocab living inside the INJECTED sprint-mode SKILL doc
      (injected on EVERY /sprint-mode boop; it LISTS the ENTIRE block-vocab family — "what needs you",
      "HELD-FOR-STEWARD", "your call", "standing by", … — as the gate's OWN DEFINITIONS), and (b) block-vocab
      QUOTED inside a Primary SELF-CATCH turn that quotes the vocab to ACKNOWLEDGE a prior catch, never to
      author a park. WHY URGENT: left unfixed, EVERY HUM false-HOLLOWs the moment a /sprint-mode doc is
      injected — an always-red gate is useless (alert-fatigue = the trust-poison the review itself warns of).
      THE FIX (system-over-symptom): a new helper assistant_authored_block_idxs(text) replaces the bare
      `BLOCK_RE.search(text) or BLOCK_CAPS_FLAG_RE.search(text)` inside check_block_no_wwcw, counting ONLY
      block-language that is PRIMARY-AUTHORED in Primary's own assistant prose as a REAL park. Two exclusion
      layers: (A) INJECTED-CONTENT — role!="assistant" (task-notifications / SKILL-doc tool_result /
      system-reminders / command-messages are ALL user-role; the role filter already drops them, hardened
      here) PLUS an injected-region strip (_strip_injected_regions: <task-notification>/<system-reminder>/
      <command-message>/<command-name> bodies blanked before the scan — defense-in-depth if ever echoed in an
      assistant record); (B) SELF-CATCH-QUOTATION — a block-vocab match fully CONTAINED in a quotation
      (_quoted_ranges: double-quote "…", apostrophe-tolerant single-quote '…' so it's/I'll/the steward's do NOT
      open spans, backtick `…`/```…``` fences, markdown emphasis *"…"*) is the mind QUOTING the vocab to
      discuss it → excluded. A REAL park is bare UNQUOTED closing prose ("Holding for your steer.", "Your
      call —", "Want me to X?") → STILL FLAGS, exactly as the steward directed. KEPT EXACTLY: the v2/v3 co-located
      REAL-RUN clear-logic (_block_cleared_by_colocated_run — SIMULATE+RESOLVE within ±8), the hard-fail
      wiring (CHECK_ORDER + BLOCK_NO_WWCW_HARDFAIL_CHECKS, ABSENT from CANDIDATE_CHECKS → breaks
      summary.clean), the hum.js deterministic DECIDE=HOLLOW/verdict=HOLLOW backstop (reads the SAME
      status=flag). v4 changes ONLY WHICH turns count as blocks, never the clear-logic or the consumer
      contract. VALIDATED on the live session that exposed the FP (303ecb5f): 184 raw assistant block-turns
      → 164 authored block-turns; the 20 newly-EXCLUDED turns are ALL confirmed quoted/code-fenced/
      meta-discussion (gate-definition recitals, "want me to remember?" loop-name quotes, prior-catch
      class-name quotes, backtick floor-summary "HELD this stretch" recitals) — ZERO real parks lost; the
      original FP self-catch turn 5093 now EXCLUDED. 6-case synthetic battery PASS (injected-echo / quoted-
      vocab-list / real-park / backtick-floor-recital / quoted-loop-name + role-drop). HONEST RESIDUAL
      (recorded, not hidden — THE MAIN RULE: auditable): one self-catch turn (5033) retains a SINGLE
      UNQUOTED residual — "If something is genuinely your call, I either run WWCW and act" — which is a
      hypothetical commit-to-ACT sentence, NOT a quote and NOT injected. v4 does NOT suppress it: the task
      scope is the two named shapes (injected + quoted); adding hypothetical-conditional detection would
      risk FALSE-NEGATIVES on real conditional soft-parks ("Or if the demo's where you want it, say the
      word"). Conservative-by-design: we never widen the exclusion past injected+quoted. PII-safe (helpers
      return bools / ranges; no text echoed). Backup:
      tools/session_review.py.bak.20260620T180629Z-pre-block-self-catch-exclusion. Companion: workflows/hum.js
      UNCHANGED (it consumes the SAME status=flag signal; v4 only refines when status=flag fires).

  2026-06-20 (mind-lead, v4.1) — GROUNDING-COMPLETENESS PER-INVOCATION (PER-CYCLE) WINDOW (the steward caught
      the WHOLE-SESSION bug). THE BUG: GROUNDING-COMPLETENESS was WHOLE-SESSION scoped — it counted the
      haiku-archive entries inside [session_first_ts, session_last_ts] (the whole session min/max), and
      scanned full_turns for the 8 elements. With the cron injecting /sprint-mode on EVERY boop, a LEAN
      boop that wrote ~0 fresh haikus THIS window still PASSED completeness by riding EARLIER cycles'
      haikus: the last HUM reported per_doc_haikus=34 (session-wide) for a lean boop. So "full proven
      per-boop" was NEVER actually checked — the gate could not distinguish a complete boop from a lean
      one parked atop a morning of accumulated haikus. THE FIX (the ONE broken piece —
      check_grounding_completeness window scope; everything else KEPT): the completeness contract now
      scopes to the PER-INVOCATION boop window when since_turn>0 (the hum-cursor / --since-turn boundary
      = the start of THIS boop's window, between this /sprint-mode injection and the next boop / end).
      It counts ONLY (a) the haikus whose ts falls in THIS boop's time-window (the scoped turns' min/max
      ts, NOT the session min/max — a new optional `window=` param on _count_fresh_haiku_docs) and (b)
      the structured elements emitted in THIS boop's turns (idx>since_turn). A lean boop (fresh-haikus <
      GROUNDING_COMPLETE_DOCSET THIS window) now correctly FAILS; a genuinely-full per-cycle boop (≥10
      fresh haikus + all 9 elements THIS window) PASSES. since_turn is threaded run_all → build_record →
      main (the cursor main already computes for --since-turn). KEPT EXACTLY: the false-fail guard (a
      pure status / lean-no-grounding boop is exempt under BOTH scopings — only a boop that DID grounding
      work THIS window owes the whole contract), the 8-element checklist, the archive-unverifiable
      could-not-verify path, the hard-fail wiring (GROUNDING_COMPLETENESS_HARDFAIL_CHECKS → breaks
      summary.clean → hum.js forces verdict=HOLLOW). BACK-COMPAT: since_turn==0 (the firewall whole-
      session call HUM also makes with --since-turn 999999999 for the window/cursor) takes the
      whole-session path BYTE-IDENTICAL to v2.0 — the per-cycle scope fires ONLY on the cursor-bounded
      grade call (the real per-boop fire). VALIDATED trust-the-walk: per-cycle on a LEAN window riding
      earlier haikus → FLAG (fails); per-cycle on a genuinely-FULL window (10 docs + 10 fresh haikus + 9
      elements) → PASS; whole-session (since_turn=0) unchanged. Backup:
      tools/session_review.py.bak.20260620T190404Z-pre-grounding-completeness-per-cycle-window. Companion:
      workflows/hum.js (grader prompt note that GROUNDING-COMPLETENESS is per-cycle-scoped via the cursor;
      the deterministic verdict=HOLLOW backstop on grounding_completeness.failed is UNCHANGED — it reads
      the SAME status=flag signal, only WHEN the flag fires is now per-boop-correct).

  2026-06-20 (mind-lead, v5.0) — TWO NEW HUM-MANDATE CHECKS (ADDITIVE; companion to workflows/hum.js v1.0
      HUM-MISSION + mandatory per-boop checklist + find-the-miss build). HONEST behavioral enforcement of
      the HUM per-boop discipline ON REVIEW:
        • CHECKLIST-SAVED — a HUM fire observed in-window that left NO saved checklist doc is FLAGGED
          (the mandatory deterministic per-boop save was skipped). Cleared by ANY of three independent
          signals: a Write to the hum-checklists dir, a checklist_doc/hum-checklist signal in prose/return,
          or the newest checklist doc on disk mtime'd at/after the fire.
        • FIND-THE-MISS-PRESENT — a HUM fire observed in-window that recorded NO find-the-miss is FLAGGED
          (the immune-system mandate — ≥1 genuine miss every boop — was skipped). Cleared by any
          find_the_miss field / ledger line / prose mention.
      BOTH are in CHECK_ORDER + the new HUM_MANDATE_HARDFAIL_CHECKS set + ABSENT from CANDIDATE_CHECKS → a
      genuine flag breaks summary.clean (a real discipline-skip, not a heuristic). 🛡️ FALSE-FAIL GUARD: each
      fires ONLY when a HUM fire is GENUINELY observed (a Workflow tool-use naming workflows/hum.js) AND the
      mandatory evidence is absent by ALL independent signals — a window with NO HUM fire returns status="na"
      (nothing to enforce), so a normal non-HUM boop is never touched. New helpers: _hum_fire_window (the
      observed-HUM-fire predicate, mirrors saw_hum_fired in check_grounding_completeness) +
      _newest_checklist_doc_mtime (dir-listing + getmtime only; never reads file contents — PII-safe). 🚨
      PRESERVES wls4i6lu2's concurrent v4.1-and-after grounding-completeness turn-consistency fix ENTIRELY:
      check_grounding_completeness + its hard-fail wiring + every existing check are UNTOUCHED — this edit is
      purely additive (two new functions + their CHECK_ORDER/run_all/hard-fail-set/build-record entries). Both
      files were read FRESH immediately before editing to avoid clobbering the in-flight fix. Backup:
      tools/session_review.py.bak.20260620T194316Z-pre-checklist-saved-findthemiss-checks. Companion:
      workflows/hum.js v1.0 + .claude/team-leads/mind/HUM-MISSION.md + HUM-CHECKLIST-TEMPLATE.md. Canon:
      537a1652dbab4d5fb6fdc37592059dbf.
  2026-06-20 (mind-lead, v5.1) — LEAN-CYCLE LOOPHOLE CLOSE (steward directive verbatim: `"lean cycle" <
      discipline`). THE LOOPHOLE: GROUNDING-COMPLETENESS triggered ONLY on GROUNDING_PROMPT_RE (the
      haiku-bearing slow-sprint shape). A BARE lean /sprint-mode does NOT match GROUNDING_PROMPT_RE, so it
      took the `invoked_idx is None → pass` branch and was EXEMPT — and the false-fail guard ("a bare lean
      /sprint-mode that does no haikus is exempt → NOT a grounding boop") was the explicit dodge. Primary
      called genuine NEW /sprint-mode boops "lean continuation" and skipped the full 10-doc/10-haiku/
      9-element grounding ~4x in one day (the 19:1x / 19:50 / 20:0x / 20:51 windows). THE FIX (the loophole
      removed; the gate kept honest): check_grounding_completeness now fires on EITHER trigger — TRIGGER 1
      (kept) a GROUNDING_PROMPT_RE pass, OR TRIGGER 2 (NEW) a GENUINE /sprint-mode boop = a /sprint-mode
      command-message / calendar boop (SPRINT_MODE_COMMAND_RE; injected-SKILL-doc + meta turns excluded via
      _is_injected_or_skilldoc_turn) AND ≥1 work-act (_has_work_act) AND NOT a byte-identical re-injection
      within SPRINT_DEDUP_WINDOW_SECONDS (_dedup_clustered_reinjections). A genuine /sprint-mode cycle now
      OWES the full contract REGARDLESS of grounding-work signatures (the `did_grounding_work` exemption was
      the loophole — it now applies ONLY to a TRIGGER-1 lean CLUSTERED RE-FIRE, never to a genuine TRIGGER-2
      /sprint-mode boop). A lean /sprint-mode cycle (genuine boop + work but NO full grounding) now FLAGS →
      GROUNDING_COMPLETENESS_HARDFAIL_CHECKS → breaks summary.clean → FAILS. 🎛️ THE DEDUP WINDOW IS THE
      CADENCE KNOB: SPRINT_DEDUP_WINDOW_SECONDS=60 (strict per-cycle — every non-deduped /sprint-mode fully
      grounds; only a byte-identical re-injection within 60s of a prior /sprint-mode is the cluster
      carve-out). Widen to 3600 = per-HOUR cadence (any identical /sprint-mode within an hour of a prior
      full grounding is the same cycle) — one-line change; the steward's ruling. THE ONLY TWO REMAINING
      EXEMPTIONS: (a) a byte-identical 60s dedup re-injection (cadence-lock cluster carve-out); (b) a
      non-/sprint-mode turn (no /sprint-mode boop in window — a pure status/conversation turn is never a
      grounding boop, never failed → no over-fire on regular turns). VALIDATED (synthetic battery, all PASS):
      lean /sprint-mode cycle → FLAGS (clean=False); full grounding boop (10 docs + 10 fresh haikus + 9
      elements) → PASSES; byte-identical 60s re-injection → exempt (pass); non-/sprint-mode conversation
      turn → not flagged (pass). py_compile clean. KEPT EXACTLY: the v4.1 per-cycle window, the 9-element
      checklist, the archive-unverifiable could-not-verify path, the hard-fail wiring, all other checks.
      Backup: tools/session_review.py.bak.20260620T210551Z-pre-lean-sprint-loophole-close. Companion:
      sprint-mode/SKILL.md (COMPLETENESS CONTRACT false-fail-guard line REPLACED with the lean-cycle-FAILS
      rule + dedup-knob note) + wwcw-ruleset.md (new QUESTION CLASS: lean-cycle-vs-full-grounding).

  2026-06-21 (mind-lead, v4.2) — TWO WALKED FALSE-POSITIVE CURES (HUM wa28qwcpv walked both; soak payoff
      — curing WALKED defects, NOT a born-today re-tune). Targeted false-positive-only; everything else KEPT.
      (1) BLOCK-NO-WWCW NEGATION-GUARD (the confirmed defect). BLOCK_RE's `(?:needs?|needing)\s+corey`
          matched the substring "needs the steward" INSIDE Primary's standard WWCW AFFIRMATION line "simulate-the steward
          before any ask; nothing this cycle needs the steward" — the OPPOSITE of a park (Primary affirming it ran
          WWCW and found NOTHING needing the steward). Because Primary's affirmation ALWAYS contains that phrase and
          BLOCK-NO-WWCW forces verdict=HOLLOW deterministically, this false-HOLLOWed EVERY grounding cycle →
          the immune system cried wolf every hour → signal corruption (the alert-fatigue trust-poison the v4
          quotation-fix already warred against). THE FIX (a THIRD exclusion layer (C) in
          assistant_authored_block_idxs, alongside (A) injected + (B) quoted): a new _match_is_negated()
          excludes a block-vocab match when a NEGATOR ("no"/"nothing"/"none"/"never"/"not"/"without"/"zero"/
          n't, _NEGATOR_RE) sits within NEG_WINDOW_CHARS(=40) BEFORE the match AND IN THE SAME CLAUSE (cut at
          the last . ; : ! ? \n — the same-clause rule keeps a real park in the NEXT clause flaggable: the
          MIXED case "nothing needs the steward. But: your call on X" STILL flags the park), OR the match sits in an
          explicit WWCW run-affirmation context (_WWCW_AFFIRM_CONTEXT_RE — "simulate-the steward before any ask",
          "ran WWCW", "act+record"). NARROW BY DESIGN: a REAL park ("HELD-FOR-STEWARD", "your call", "I'll hold
          pending your steer", "what would you like me to do", bare "needs the steward") has NO same-clause negator
          → STILL FLAGS. WALK (live session 303ecb5f, 5785 turns): the guard newly EXCLUDED exactly 9 turns,
          ALL confirmed negated affirmations (idx 5663/5769 = the canonical "nothing this cycle needs the steward";
          1465 "without your call"; 3359 "nothing waiting but your call"; 3533 "Nothing needs you this cycle";
          …) — ZERO of the 164 real authored parks (idx 5/26/29/70/77/86…) lost. 19-case synthetic battery
          PASS both directions.
      (2) GROUNDING-COMPLETENESS synthesis-miss (ELLIPSIS-TOLERANT GAP). The GROUNDING_SYNTHESIS_RE gap
          `[^.\n]{0,120}?` forbade ANY period, so Primary's real 03:00 synthesis "I am now the CEO three hours
          into a clean clockwork night — grounded fully on a fresh hour... ready to route by ownership…" did
          NOT match (the "hour..." ellipsis tripped `[^.\n]`) → saw_synthesis=False even though a valid "I am
          now X, ready to Y" synthesis WAS written in BOTH assistant text + the scratchpad 03:00 block. The
          compact form matched; only ellipsis/period-bearing elaborate phrasing evaded. VERDICT (honest call,
          directive #3): a DETECTOR regex-strictness miss (an ellipsis is NOT a sentence boundary in a
          synthesis — forbidding it was over-strict), NOT a Primary-phrasing-evaded-a-reasonable-detector case
          → surgical fix warranted (the @5680 hit anchor is the trigger/prune-region idx, NOT where synthesis
          was searched — saw_synthesis scans the whole scoped window; the miss was the regex, not the anchor).
          THE FIX (narrow): gap now `(?:[^.\n]|\.{2,}|…){0,160}?` — tolerates a `...`/`…` ellipsis run + the
          em-dash (already non-period) while STILL stopping at a real SENTENCE-ENDING lone period (so it cannot
          swallow across a true sentence break: "I am now done. … Ready to review" still MISSES). Cap 120→160
          for the longer elaborate phrasing. NOT BLINDED: a turn with no "I am now … ready to" still misses.
          8-case synthetic battery PASS (real elaborate / compact / unicode-ellipsis / conductor-literal /
          em-dash MATCH; sentence-break / no-synthesis / I-am-now-without-ready-to MISS). COMPANION BEHAVIORAL
          LESSON (recorded, not a gate-loosen excuse): Primary should prefer the COMPACT "I am now X, ready to
          Y" synthesis form — the detector is now ellipsis-tolerant, but the compact form is the canonical,
          always-detectable shape.
      SOAK RESPECTED (handoff #1 caution "do not re-tune the born-today gate"): both are minimal targeted
      false-positive-ONLY fixes with .bak + this changelog; NO broad re-tune of thresholds, the 9-element
      checklist, the hard-fail wiring, the co-located clear-logic, or the per-cycle window. This is the soak's
      PAYOFF — curing two defects the soak surfaced via HUM's own walk — not speculative tuning. py_compile
      clean. Backup: tools/session_review.py.bak.20260621T032212Z-pre-block-negation-guard. Companion:
      workflows/hum.js UNCHANGED (it consumes the SAME status=flag signals; v4.2 only refines WHEN a flag
      fires — fewer false-positives, identical consumer contract).

  2026-06-21 (mind-lead, v4.3) — READ→HAIKU PAIRING + DOCSET 10→11 (steward directive verbatim: "Hum
      manifest should show it checking for read commands followed by haiku, and you should be saving all
      the haikus"). MINIMAL + REVERSIBLE (steward-directed; do NOT over-tune the born-today gate beyond
      these asks). THREE additive changes to GROUNDING-COMPLETENESS — the hard-fail wiring, the per-cycle
      window, the false-fail guard, the co-located clear-logic, and every other check are UNTOUCHED:
      (1) DOCSET 10 → 11. GROUNDING_COMPLETE_DOCSET bumped to match fleet-lead's stage-1 grounding-docs
          SKILL change — it added Doc -0.5 (WWCW) as a numbered read→haiku doc (grep -cE '^### Doc'=11;
          count(haikus)==count(docs)==11). The per-doc-haiku archive element now requires ≥11 distinct
          fresh in-window haiku-docs.
      (2) READ→HAIKU PAIRING element (1b). the steward wants the gate to verify the read-command→haiku PAIRING
          — a Read tool-call FOLLOWED by a haiku — as grounding-PROOF, not merely a flat haiku count.
          New HAIKU_LINE_RE (slash-3 haiku shape) + READ_HAIKU_PAIR_WINDOW_TURNS (=4 turn look-ahead).
          Inside the existing per-turn loop we now count read_tool_calls (Read tool-uses this window) and
          read_haiku_pairs (FIFO-pair each Read with the next haiku artifact within the look-ahead — a
          slash-3 haiku in prose OR a haiku-archive Write/Edit). A new missing-element fires ONLY when
          the boop MADE ≥docset Read tool-calls (a real read-one-at-a-time pass) AND fewer than docset of
          those reads paired with a following haiku → read-without-comprehend = INCOMPLETE → status=flag →
          (already in GROUNDING_COMPLETENESS_HARDFAIL_CHECKS) breaks summary.clean → FAILS. CONSERVATIVE:
          a re-ground off the archive with NO Read tool-calls this window is NOT penalized by (1b) — the
          per-doc-haiku archive element governs that case — so no false-fail on a no-Read-call window.
      (3) HAIKU-SAVED confirmation. The archive IS the durable save; the elements dict now surfaces
          haikus_saved_to_archive = (archive_verifiable AND ≥docset fresh entries) so HUM reports the
          "saving all the haikus" (the steward) discipline explicitly. The per-doc-haiku archive element already
          hard-fails an under-saved window; this names it in the report.
      BEHAVIORAL TEST: py_compile clean; a synthetic grounding WITH read→haiku pairing (11 Reads each
      followed by a haiku + all elements) PASSES; one MISSING the pairing (11 Reads, <11 paired) FLAGS;
      live-session 303ecb5f back-compat preserved (it re-grounds off prose/archive without 11 Read
      tool-calls in a single per-cycle window → element (1b) does not fire → its prior verdict is
      unchanged). PII-safe (counts only — Read tool-call count + pairing count; never the haiku body,
      never doc contents). Backup: tools/session_review.py.bak.<ts>-pre-readhaiku-pairing. Companion:
      .claude/team-leads/mind/HUM-MISSION.md (HUM now visibly CHECKS the read→haiku pairing as part of
      its grounding-completeness review) + autonomy/skills/grounding-docs/SKILL.md (fleet-lead stage-1:
      Doc -0.5 + SAVE EVERY HAIKU discipline). workflows/hum.js UNCHANGED (it consumes the SAME
      status=flag signal; v4.3 only adds WHAT makes the flag fire — an unpaired full read-pass).

  2026-06-22 (fleet-lead, v4.4) — DOC-CURRENCY BUILD-SIGNAL FIX (the surfaces_checked:0 cause) +
      SWEEP-ACT-ON-FLAGGED check (the notice-don't-act enforcement). steward-directed GO (overrides the
      born-today soak-caution for THIS wiring). TWO additive changes; every existing check + the
      hard-fail wiring + the per-cycle window UNTOUCHED.
      (A) THE surfaces_checked:0 ROOT CAUSE + FIX (DOC-CURRENCY). Tonight DOC-CURRENCY returned
          surfaces_checked:0 after a real BUILD arc — it did NOT catch WORKBOARD staleness. WALKED root
          cause: the keep-worthy signal set was canon_append + data/reports-Write + decision-marker ONLY.
          A build arc that Edits/Writes SKILLs / manifests / tools / workflows (the COMMON fleet/mind/
          workflow shape) produces ZERO of those three → keepworthy_total==0 → check_doc_currency takes the
          "vacuously compliant (pass, no hits)" branch → the hum-doc-currency agent counts ZERO surfaces in
          the empty hits → surfaces_checked:0. The check was structurally BLIND to build-shaped keep-worthy
          work; a stale WORKBOARD after a build was never even compared. THE FIX: a 4th keep-worthy signal —
          a substantive BUILD edit (Edit/Write to a substrate-shaped path: SKILL.md / team-lead manifest.md
          / tools/*.py / workflows/*.js; BUILD_EDIT_PATH_RE). A build arc now MAKES the check run
          (surfaces_checked>0) so the stale-WORKBOARD comparison fires. Conservative: substrate-shaped paths
          ONLY (not every Edit), and .bak + WORKBOARD/DEVLOG/CHANGELOG themselves are EXCLUDED
          (BUILD_EDIT_EXCLUDE_RE) so the check can never self-trigger on its own remediation. DOC-CURRENCY
          stays CANDIDATE-only (additive — it surfaces the stale surface; the JUDGE routes the doc-update).
      (B) SWEEP-ACT-ON-FLAGGED (NEW check, CANDIDATE-only). The notice-don't-act defect (the steward-caught):
          auto-consolidate ran + HONESTLY self-reported NOT-CLEAN twice but Primary DEFERRED the fixes. The
          auto-consolidate + grounding-docs SKILLs now MANDATE act-on-flagged (home/wire/close IN-BOOP, OR a
          concrete owner+trigger). check_sweep_act_on_flagged surfaces the signal: a sweep that self-reports
          a found-and-un-acted candidate (un-homed / un-wired / human-asked-workflow / needs-create) with NO
          act-evidence in-window (no home/forge/register + no concrete owner+trigger route; a VAGUE
          "deferred"/"TODO" is deliberately NOT act-evidence). JUDGING-MIND NOT BASH-REGEX (the steward "no scripts
          if possible"): the regex only DETECTS the mechanical co-occurrence (sweep-ran + not-clean + no-act);
          the HUM JUDGE (separate incarnation) WALKS the window, confirms intent, and assigns the FAIL — it
          is in CANDIDATE_CHECKS so the deterministic layer never decides the verdict. 🛡️ FALSE-FAIL GUARD:
          fires ONLY when a sweep RAN + self-reported NOT-CLEAN (co-occurring with sweep vocab in the same
          turn-blob) + ZERO act-evidence anywhere in-window. A swept-CLEAN result = pass; a sweep that acted
          = pass; no-sweep window = na (a non-grounding turn does not owe a sweep). PII-safe (marker-class +
          turn_index only). Backup: tools/session_review.py.bak.20260622T012559Z-pre-doccurrency-buildsignal-
          actonflagged. Companion: workflows/hum.js (the JUDGE prompt + DocCurrency/SWEEP coaching surfaces) +
          autonomy/skills/auto-consolidate/SKILL.md + autonomy/skills/grounding-docs/SKILL.md (the DECLARED
          act-on-flagged contract) + .claude/team-leads/mind/HUM-MISSION.md (the two new JUDGE checks).

OWNER: fleet-lead (tooling) — DOC-CURRENCY check is mind-lead's (WORKBOARD + doc-staleness mandate owner);
       the v4.4 DOC-CURRENCY build-signal fix + SWEEP-ACT-ON-FLAGGED are fleet-lead's (grounding/sprint floor).
       BLOCK-NO-WWCW v2 co-located redesign + v4 primary-authored-only exclusion + GROUNDING-COMPLETENESS
       (incl. v4.1 per-invocation window) are mind-lead's (HUM immune-system / JUDGE owner). Consumed by:
       the HUM Stage-2 judging mind.
"""

import argparse
import fnmatch
import glob
import json
import os
import re
import sys
from datetime import datetime, timezone

DEFAULT_PROJECT_DIR = "$AICIV_HARNESS_PROJECT_DIR"

# ---------------------------------------------------------------------------
# Marker vocabularies (deterministic regexes). Kept narrow + word-boundaried.
# These match on MARKERS, never on free-form human text we then echo back.
# ---------------------------------------------------------------------------

# A WWCW signal present in an assistant turn (the doctrine ran).
WWCW_TEXT_RE = re.compile(r"\b(WWCW|what\s+would\s+corey\s+want)\b", re.IGNORECASE)
WWCW_SKILL_NAMES = {"wwcw"}

# Assistant text that reads like "I'm asking the human to decide / pick an option".
# Conservative: requires an explicit decision-ask shape, not merely a question mark.
ASK_DECIDE_RE = re.compile(
    r"(which\s+(option|do\s+you\s+(want|prefer))|"
    r"should\s+i\s+(do|proceed|go\s+with|pick|choose)|"
    r"do\s+you\s+want\s+me\s+to|"
    r"(option\s+a\b.*option\s+b\b)|"
    r"let\s+me\s+know\s+(which|if\s+you'?d\s+like)|"
    r"shall\s+i\b|"
    r"your\s+call\b|"
    r"(a)\)\s.*\(?b\)\s|"
    r"awaiting\s+your\s+(decision|go|call))",
    re.IGNORECASE | re.DOTALL,
)

# --- OVER-DEFERENCE candidate vocab (the WORSE failure the bare WWCW-GATE misses) ---
# A turn that RAN a confident WWCW and then HANDED the call back to the human instead of
# acting+recording. The bare WWCW-GATE only catches "ask with NO WWCW marker"; it PASSES this
# strictly-worse shape because the WWCW marker is PRESENT. We surface it as a CANDIDATE (the
# reversibility/within-Primary's-authority judgment is Stage-2's job; the deterministic layer only
# names the mechanical signature: WWCW present + confidence language + an explicit DEFER-to-human shape).
#
# DEFER markers = the mind handing the decision back ("say the word", "your call", "I'll route on go").
# Deliberately does NOT reuse the broad ASK_DECIDE_RE: that regex false-matches quoted WWCW-template
# phrases (e.g. an inline 'DECIDE … RATE: high confidence … ACT+RECORD' walk that quotes "decide, go"
# but then ACTS — that turn is WWCW done RIGHT and must NOT be flagged). The discriminator for
# over-deference is an actual hand-back-to-the-human marker, not the presence of a decision-word.
DEFER_TO_HUMAN_RE = re.compile(
    r"(say\s+the\s+word|"
    r"say\s+[\"'*]*go[\"'*]*\b|"
    r"want\s+me\s+to\b|"
    r"shall\s+i\b|"
    r"let\s+me\s+know\b|"
    r"i'?ll\s+(execute|route|fire)\b|"
    r"your\s+(call|word)\b|"
    r"rest\s+with\s+you|"
    r"keep\s+(shaping|till\s+morning)|"
    r"awaiting\s+your\s+(decision|go|call))",
    re.IGNORECASE,
)
# Confidence language in the SAME turn — the WWCW reached a confident verdict, which is precisely
# what makes the subsequent defer a DECIDE defect (a confident, equipped mind handed the call back).
CONFIDENCE_RE = re.compile(
    r"\b(confiden\w+|high\s+confidence|i'?m\s+confident|confidently)\b",
    re.IGNORECASE,
)

# --- THE BLOCK GATE (steward directive 2026-06-20, the REAL gate; SUPERSEDES the narrow over-deference path) ---
# steward verbatim 2026-06-20: "'What needs you' is a block and i see zero evidence that you ran the wwcw skill...
# If no evidence of wwcw run it's to fail your boop." The root-cause audit proved the over-deference path
# (DEFER_TO_HUMAN_RE + CONFIDENCE_RE + a WWCW marker) was TOO NARROW — a BARE PARK has no WWCW marker and no
# confidence word, so it sailed past BOTH detection paths (0/9 real parked phrases from this session matched).
#
# A BLOCK = anything Primary parks / holds / presents-for-confirmation / flags as needing-the steward. This is a
# BROAD vocabulary that matches the full block-language family — it deliberately does NOT require a WWCW
# marker or a confidence word (that was the fatal narrowness). It matches the PARK SHAPE itself.
#   Examples it MUST catch (all 0/9 before): "Parked for the steward", "HELD-FOR-STEWARD", "awaiting the steward",
#   "needs the steward", "what needs you", "what would you like", "for your approval", "your call", "should I",
#   "do you want me to", "let me know if", "standing by", "pending your", "I'll hold", "presenting options".
BLOCK_RE = re.compile(
    r"("
    r"park(?:ed|s|ing)?\s+(?:for|awaiting|pending|till|until|on)\s+corey|"   # parked for/awaiting corey
    r"park(?:ed|s|ing)?\s+for\s+(?:your|corey'?s)\b|"                          # parked for your/corey's …
    r"\bHELD[-\s]?FOR[-\s]?STEWARD\b|"                                           # HELD-FOR-STEWARD (the literal flag)
    r"held\s+for\s+corey|"                                                     # held for corey (prose)
    r"awaiting\s+corey|await(?:ing|s)?\s+(?:your|corey'?s)\s+(?:decision|go|call|approval|word|sign[\s-]?off)|"
    r"(?:needs?|needing)\s+corey\b|"                                           # needs corey / needing corey
    r"what\s+needs?\s+you\b|"                                                  # "what needs you" (the steward's example)
    r"what\s+would\s+you\s+like\b|"                                            # "what would you like…"
    r"for\s+your\s+(?:approval|sign[\s-]?off|review\s+before|go[\s-]?ahead)\b|"# "for your approval"
    r"your\s+call\b|"                                                          # "your call"
    r"your\s+word\b|"                                                          # "your word"
    r"should\s+i\b|"                                                           # "should I …"
    r"shall\s+i\b|"                                                            # "shall I …"
    r"do\s+you\s+want\s+me\s+to\b|"                                            # "do you want me to …"
    r"want\s+me\s+to\b|"                                                       # "want me to …"
    r"let\s+me\s+know\s+(?:if|whether|which|and\s+i'?ll|before)\b|"            # "let me know if/which…"
    r"standing\s+by\b|"                                                        # "standing by"
    r"pending\s+your\b|"                                                       # "pending your …"
    r"i'?ll\s+hold\b|"                                                         # "I'll hold"
    r"holding\s+for\s+(?:your|corey)|"                                         # "holding for your/corey"
    r"present(?:ing|ed)?\s+(?:the\s+)?options?\s+(?:for\s+(?:your|corey'?s)|to\s+you)|"  # presenting options for your…
    r"options?\s+for\s+(?:your|corey'?s)\s+(?:confirmation|review|decision|pick|approval)|"
    r"for\s+your\s+confirmation\b|"                                           # "for your confirmation"
    r"awaiting\s+your\s+(?:decision|go|call|approval|word|sign[\s-]?off)|"     # "awaiting your go/decision"
    r"say\s+the\s+word\b|"                                                     # "say the word"
    r"on\s+your\s+go\b"                                                        # "on your go"
    r")",
    re.IGNORECASE,
)

# Bare ALL-CAPS status-flags the mind writes as standalone parks ("...GROUP-tier PARKED", "R2 HELD").
# CASE-SENSITIVE (NOT IGNORECASE) on purpose: the ALL-CAPS form is the deliberate flag Primary writes;
# lowercase "parked"/"held" in prose ("the car was parked", "the meeting was held") is NOT a park signal
# and must not false-positive. A separate regex because BLOCK_RE carries re.IGNORECASE for the broad family.
BLOCK_CAPS_FLAG_RE = re.compile(
    r"\b(PARKED|HELD|BLOCKED|HOLDING|DEFERRED[-\s]TO[-\s]STEWARD|NEEDS[-\s]STEWARD|AWAITING[-\s]STEWARD)\b"
)

# --- BLOCK-NO-WWCW v4 (2026-06-20, mind-lead): PRIMARY-AUTHORED-ONLY GATE (the false-positive cure) ---
# WHY v4: HUM wxxeuo7j2 caught its OWN false-positive. BLOCK-NO-WWCW flagged a turn whose matched
# block-vocab was NOT a real Primary park — it was (a) block-vocab living inside an INJECTED SKILL doc /
# task-notification / system-reminder (the sprint-mode SKILL doc is injected on EVERY /sprint-mode boop
# and LISTS the ENTIRE block-vocab family — "what needs you", "HELD-FOR-STEWARD", "your call", "standing
# by", ... — as the gate's OWN DEFINITIONS), and (b) block-vocab QUOTED inside a Primary self-catch turn
# that QUOTES the vocab (in quotes/backticks) to DISCUSS/ACKNOWLEDGE a prior catch — never to author a
# park. An always-red gate is useless (alert-fatigue, the trust-poison the review itself warns about):
# left unfixed, EVERY HUM false-HOLLOWs the moment a /sprint-mode doc is injected.
#
# THE v4 FIX (system-over-symptom): BLOCK-NO-WWCW now counts ONLY block-language that is PRIMARY-AUTHORED
# in Primary's OWN assistant prose as a REAL park. Two exclusion layers, applied BEFORE the block scan:
#   (A) INJECTED-CONTENT exclusion — never count a turn that is injected, not Primary-authored:
#         • role != "assistant"  (task-notifications, command-messages, system-reminders, the injected
#           SKILL-doc tool_result are ALL user-role — the existing role filter already drops them; this is
#           kept + hardened so a harness-layout change can't re-open the hole), AND
#         • an assistant turn whose text carries an INJECTED-MARKER (<task-notification> / <system-reminder>
#           / <command-message> / <command-name> / a SKILL-doc fence) has those injected REGIONS stripped
#           before the block scan (defense-in-depth: if an injected block ever lands echoed inside an
#           assistant record, its vocab no longer counts).
#   (B) SELF-CATCH-QUOTATION exclusion — within a Primary assistant turn, a block-vocab match that sits
#         INSIDE a quotation (double-quote "…", single-quote '…' [apostrophe-tolerant: contraction
#         apostrophes in it's/I'll do NOT open a span], backtick `…`/```…```, or markdown emphasis *"…"*)
#         is the mind QUOTING the vocab to discuss/acknowledge it (the gate's own definitions, a prior
#         catch's class-name, a "want me to remember?" loop-name) — NOT authoring a park. Quoted matches
#         are EXCLUDED. A REAL park is bare closing prose ("Holding for your steer.", "Your call —", "Want
#         me to X?") with the vocab UNQUOTED — those still FLAG, exactly as the steward directed.
#
# THE INVARIANT (the steward 2026-06-20 refinement of the 2026-06-20 directive): the gate fires on a
# PRIMARY-AUTHORED park (a genuine "holding for your steer" in Primary's own closing prose), NEVER on a
# definition-in-a-doc or a quote-of-a-prior-block. Validated on the live session that exposed the
# false-positive: 184 raw block-turns → 164 authored block-turns; the 20 newly-EXCLUDED turns are all
# confirmed quoted/code-fenced/meta-discussion (gate-definition recitals, "want me to remember?" loop-name
# quotes, prior-catch class-name quotes, floor-summary backtick fences) — ZERO real parks lost.

# Injected-marker shapes. An assistant turn's text is NEVER expected to author these; if present they are
# echoed/injected content whose regions are stripped before the block scan. (Injected turns are normally
# user-role and already dropped by the role filter; this is the defense-in-depth layer.)
INJECTED_MARKER_RE = re.compile(
    r"(<task-notification>|</task-notification>|"
    r"<system-reminder>|</system-reminder>|"
    r"<command-message>|</command-message>|"
    r"<command-name>|</command-name>|"
    r"<local-command-stdout>|<local-command-stderr>)",
    re.IGNORECASE,
)
# An injected REGION to strip from an assistant turn before scanning (the whole notification/reminder body).
INJECTED_REGION_RE = re.compile(
    r"(<task-notification>.*?</task-notification>|"
    r"<system-reminder>.*?</system-reminder>|"
    r"<command-message>.*?</command-message>|"
    r"<command-name>.*?</command-name>)",
    re.IGNORECASE | re.DOTALL,
)

# Quotation spans (for the self-catch exclusion). A block-vocab match fully CONTAINED in any of these
# spans is QUOTED (discussed), not AUTHORED (a park) → excluded.
#   DQ — double-quote spans (straight " or curly “ ”). Double-quotes never appear in contractions, so a
#        simple non-greedy pair scan is robust.
#   BT — backtick spans (` … ` and ``` … ``` fences). Code/marker fences = discussion, never a park.
#   SQ — single-quote spans, APOSTROPHE-TOLERANT: the opening ' must NOT be preceded by an alphanumeric
#        (so the apostrophe in it's / I'll / the steward's / '90s does NOT open a span) and the closing ' must
#        NOT be followed by an alphanumeric. This is the one piece that makes single-quote containment
#        reliable in prose dense with contractions (the naive scan mis-pairs apostrophes and leaks).
# (Markdown emphasis *"…"* is captured by DQ — the inner straight-quotes are the span boundary.)
_QUOTE_DQ_RE = re.compile(r'["“][^"”]{1,600}?["”]', re.DOTALL)
_QUOTE_BT_RE = re.compile(r"`[^`]{1,600}?`", re.DOTALL)
_QUOTE_SQ_RE = re.compile(r"(?<![A-Za-z0-9])'[^']{1,600}?'(?![A-Za-z0-9])", re.DOTALL)


def _strip_injected_regions(text):
    """Remove injected notification/reminder/command REGIONS from an assistant turn's text before the
    block scan. Defense-in-depth for the (A) injected-content exclusion: even if an injected block is ever
    echoed inside an assistant record, its block-vocab no longer counts as Primary-authored. Replaces each
    injected region with same-length spaces so downstream offsets stay sane. No-op when no markers present."""
    if not text or not INJECTED_MARKER_RE.search(text):
        return text
    return INJECTED_REGION_RE.sub(lambda m: " " * len(m.group(0)), text)


def _quoted_ranges(text):
    """Char-ranges [(start,end), ...] that are QUOTED (double-quote / backtick / apostrophe-tolerant
    single-quote). A block-vocab match fully inside any range is a self-catch QUOTATION (discussed), not a
    Primary-authored park. See the v4 SELF-CATCH-QUOTATION exclusion note above."""
    ranges = []
    for rx in (_QUOTE_DQ_RE, _QUOTE_BT_RE, _QUOTE_SQ_RE):
        for m in rx.finditer(text):
            ranges.append((m.start(), m.end()))
    return ranges


def _match_is_quoted(ms, me, ranges):
    """True iff the match span [ms,me) is fully contained in some quoted range (self-catch quotation)."""
    return any(ms >= a and me <= b for (a, b) in ranges)


# --- BLOCK-NO-WWCW v4.2 (2026-06-21, mind-lead): NEGATION-GUARD (the confirmed false-positive cure) ---
# WHY v4.2: HUM wa28qwcpv WALKED a confirmed defect — BLOCK-NO-WWCW was NEGATION-BLIND. The BLOCK_RE
# alternative `(?:needs?|needing)\s+corey` matched the substring "needs the steward" INSIDE Primary's standard
# WWCW AFFIRMATION line "simulate-the steward before any ask; nothing this cycle needs the steward" — which is the
# OPPOSITE of a park (Primary AFFIRMING it ran WWCW and found NOTHING needing the steward). Because Primary's
# affirmation ALWAYS contains "nothing this cycle needs the steward", this false-positive false-HOLLOWed EVERY
# grounding cycle → the immune system cried wolf every hour → signal corruption (the exact alert-fatigue
# trust-poison the v4 quotation-fix already warred against).
#
# THE v4.2 FIX (narrow, surgical — guard the CONFIRMED shape, do NOT blind the gate): a block-vocab match
# is EXCLUDED as a non-park when it is NEGATED — a negator ("no" / "nothing" / "none" / "never" / "not" /
# "n't" / "without" / "zero") appears in a SMALL window (NEG_WINDOW_CHARS) immediately BEFORE the match.
# A negated "need(s)/needing the steward" ("nothing … needs the steward", "no … need for the steward", "never needs the steward")
# is an AFFIRMATION of NO-need, the antithesis of a park. PLUS a belt-and-suspenders WWCW-affirmation
# context guard: if the match sits inside an explicit run-affirmation phrase ("simulate-the steward before any
# ask", "ran WWCW", "act+record"), it is the doctrine affirmation, never a park.
#
# DELIBERATELY NARROW (does NOT blind the gate): the window is short (a negator must be CLOSE, not anywhere
# in the turn) so a real park elsewhere in a turn that ALSO contains an early "no" is unaffected; and a
# REAL park has NO negator on its block-phrase ("HELD-FOR-STEWARD", "your call", "I'll hold pending your
# steer", "what would you like me to do") → STILL FLAGS. Validated both directions in the v4.2 changelog.
_NEGATOR_RE = re.compile(
    r"\b(no|nothing|none|never|not|nor|without|zero)\b|n['’]t\b",
    re.IGNORECASE,
)
# The explicit WWCW-affirmation context: when a block-vocab match falls inside one of these run-affirmation
# phrases it is the doctrine being affirmed (NOT a park). Kept tight to the canonical affirmation shapes.
_WWCW_AFFIRM_CONTEXT_RE = re.compile(
    r"(simulate[-\s]?corey\s+before\s+any\s+ask|"
    r"ran\s+(?:the\s+)?wwcw|running\s+(?:the\s+)?wwcw|"
    r"act\s*\+\s*record|act\s+and\s+record|"
    r"wwcw[-_/]ruleset)",
    re.IGNORECASE,
)
# How far BEFORE a block-vocab match a negator may sit and still negate it. Short on purpose: the negator
# in "nothing this cycle needs the steward" sits ~19 chars before "needs the steward"; "no … need for the steward" similar.
# A long window would let an unrelated early "no" in a turn falsely negate a real later park.
NEG_WINDOW_CHARS = 40


def _match_is_negated(ms, scan):
    """True iff a NEGATOR ('no'/'nothing'/'none'/'never'/'not'/'without'/'zero'/n't) sits within the
    NEG_WINDOW_CHARS chars immediately BEFORE the block-vocab match at ms AND IN THE SAME CLAUSE (no
    sentence/clause boundary . ; : ! ? newline between the negator and the match) — i.e. the block-phrase
    itself is NEGATED (an affirmation of NO-need, not a park). v4.2 negation-guard. PII-safe (returns bool).

    The same-clause rule is the discriminator that keeps the guard NARROW: a turn that AFFIRMS no-need in
    one clause ("nothing this cycle needs the steward.") and then PARKS a different item in the NEXT clause
    ("But: your call on X.") still FLAGS the real park — the clause boundary stops the early negator from
    reaching across into the later park. Only a block-phrase whose OWN clause carries the negator is
    excluded ("nothing … needs the steward", "no need for the steward", "never needs the steward").

    Also returns True when the match falls inside an explicit WWCW run-affirmation context phrase
    ('simulate-the steward before any ask', 'ran WWCW', 'act+record') — the doctrine affirmation, never a park."""
    pre = scan[max(0, ms - NEG_WINDOW_CHARS):ms]
    # Restrict to the SAME CLAUSE: cut pre at the last clause/sentence boundary so a negator on the OTHER
    # side of a `. ; : ! ? \n` cannot negate THIS match (keeps a real later park flaggable — the MIXED case).
    cut = max(pre.rfind(c) for c in ".;:!?\n")
    if cut != -1:
        pre = pre[cut + 1:]
    if _NEGATOR_RE.search(pre):
        return True
    # WWCW-affirmation context: scan a slightly wider pre-window for the canonical affirmation phrasing.
    ctx = scan[max(0, ms - 80):ms + 1]
    if _WWCW_AFFIRM_CONTEXT_RE.search(ctx):
        return True
    return False


def assistant_authored_block_idxs(text):
    """The PRIMARY-AUTHORED-ONLY block test (BLOCK-NO-WWCW v4 + v4.2 negation-guard). Given ONE assistant
    turn's text, return True iff it contains ≥1 block-vocab match that is ALL of (A) not in an injected
    region AND (B) not inside a self-catch quotation AND (C) not NEGATED / inside a WWCW run-affirmation
    context — i.e. a REAL park Primary authored in its own prose. Returns False for a turn whose only
    block-vocab is injected/definitional, quoted-for-discussion, OR a negated affirmation ("nothing this
    cycle needs the steward").

    This is the load-bearing discriminator the v4 gate uses in place of the bare `BLOCK_RE.search(text) or
    BLOCK_CAPS_FLAG_RE.search(text)`. The CALLER still enforces role=='assistant' (the primary (A) layer)
    before invoking this; this function adds the injected-region strip (defense-in-depth) + the quote
    exclusion + the v4.2 negation/affirmation exclusion. PII-safe (returns a bool; never echoes text)."""
    if not text:
        return False
    scan = _strip_injected_regions(text)            # (A) injected-region strip (defense-in-depth)
    ranges = _quoted_ranges(scan)                    # (B) quotation spans
    for rx in (BLOCK_RE, BLOCK_CAPS_FLAG_RE):
        for m in rx.finditer(scan):
            if _match_is_quoted(m.start(), m.end(), ranges):
                continue                             # (B) quoted-for-discussion → not a park
            if _match_is_negated(m.start(), scan):
                continue                             # (C) negated / WWCW-affirmation context → not a park
            return True                              # an UNQUOTED, NON-INJECTED, NON-NEGATED block = a real park
    return False


# --- WWCW-RUN EVIDENCE (proof the doctrine ACTUALLY RAN this session, not merely was named) ---
# the steward 2026-06-20: "i see zero evidence that you ran the wwcw skill." A MENTION of WWCW is NOT a RUN.
# The over-deference path's bug was treating the presence of the marker as proof. Real-run evidence is
# the FOOTPRINT of the 5-beat procedure (the rubber-duck-as-the steward, wwcw/SKILL.md): the ruleset was LOADED,
# the the steward-sim was performed ("what would the steward want" reasoning), confidence was RATED, and the mind
# ACTED + RECORDED.
#
# 🚨 v2 REDESIGN (2026-06-20, mind-lead — auditor's v1 FAIL fix): WWCW_EVIDENCE_RE was kept ONLY as a
# legacy WINDOW-WIDE vocabulary scan, and that scan is the BROKEN piece the auditor caught:
#   "Real-path walk on THIS session (177 BLOCK turns) returned pass/hit=0: WWCW_EVIDENCE_RE matches WWCW
#    VOCABULARY (ruleset path / 'simulate corey'), one match clears the whole window. False-negative on
#    every WWCW-touching session."
# The fatal property: ONE 'ran WWCW' token 1500 turns away cleared 178 early bare parks (proven: blocks at
# turns 5/26/29/70 were 'cleared' by a WWCW mention at turn 1506). VOCABULARY-PRESENCE != A-RUN-HERE.
#
# THE v2 FIX (two new properties, both required — co-location + resolution-structure):
#   (1) CO-LOCATION — evidence is counted only WITHIN A BOUNDED TURN-WINDOW of the block (±WWCW_COLOCATION_TURNS),
#       never anywhere-in-session. A WWCW footprint 1500 turns away can NOT clear a bare park at turn 5.
#   (2) REAL-RUN FOOTPRINT — a real WWCW run leaves the RESOLUTION STRUCTURE of the 5-beat procedure, not a
#       bare vocabulary token. We require, co-located with the block, BOTH:
#         (a) a SIMULATE-STEWARD derivation (WWCW_SIMULATE_RE — "what would the steward want", "given his rules → …",
#             "simulate the steward", the the steward-sim reasoning), AND
#         (b) a RESOLUTION (WWCW_RESOLVE_RE — an ACT+RECORD: actually fired a workflow / made + recorded the
#             decision / "decision recorded" / "acting + recording"; OR an ASK-SHOWING-WORK with the precise
#             sub-fork — "the only sub-fork that genuinely needs the steward is X").
#       A SIMULATE without a RESOLVE = a run that started but left the block HANGING (a bare park) → still FAIL.
#       A RESOLVE without a SIMULATE = an action with no the steward-sim derivation → not a WWCW run → still FAIL.
#       The discriminator that MATTERS: was the block RESOLVED by a run, or left hanging as 'awaiting the steward'?
#   (3) STRUCTURED-MARKER BONUS (high-confidence single-signal path) — a real run MAY emit an explicit
#       structured marker (WWCW_MARKER_RE: "WWCW-RUN:" / "ACT+RECORD:" / "WWCW VERDICT:"). Co-located, that
#       marker ALONE clears the block (a run that self-announced is a run). But we do NOT rely ONLY on the
#       marker — retroactive / un-marked real runs are still caught by the (a)+(b) resolution-structure path.
#
# Legacy WWCW_EVIDENCE_RE is RETAINED for the `--debug` / informational count only; it is NO LONGER the
# clear-the-block test. check_block_no_wwcw v2 uses the three regexes below. (Kept so any external caller
# referencing the name does not break; it carries an explicit "legacy, not the gate" note.)
WWCW_EVIDENCE_RE = re.compile(  # LEGACY (informational vocabulary scan only — NOT the v2 gate; see above)
    r"("
    r"wwcw[-_/]ruleset|"
    r"autonomy/skills/wwcw|"
    r"simulate[-\s]?corey|simulat\w*\s+corey|"
    r"what\s+would\s+corey\s+(?:want|do|say|think)|"
    r"given\s+(?:his|corey'?s)\s+rules|"
    r"act\s*\+\s*record|act\s+and\s+record|acting\s+and\s+recording|"
    r"rate(?:d)?\s+(?:my\s+)?confidence|confidence:\s*(?:high|medium|low)|"
    r"5[-\s]?beat|five[-\s]?beat|"
    r"ran\s+(?:the\s+)?wwcw|running\s+(?:the\s+)?wwcw|wwcw\s+(?:run|came\s+back|verdict|reasoning)"
    r")",
    re.IGNORECASE,
)

# CO-LOCATION WINDOW: how many turns each side of a BLOCK a WWCW footprint may appear and still count
# as "the run that resolved THIS block". A 5-beat run + the park written a couple turns later co-locate;
# a WWCW mention 1500 turns away does NOT. 8 turns each side absorbs a normal run→derive→rate→act→park
# cadence (the park is usually the SAME turn or the next 1-3 turns after the run) while making a distant
# vocabulary mention structurally unable to clear an unrelated bare park. (Turn idx is the contiguous
# message-turn index from load_turns — a stable, dense ordinal.)
WWCW_COLOCATION_TURNS = 8

# (a) SIMULATE-STEWARD derivation — the beat where the mind DERIVES what the steward wants FROM his rules (not a
#     bare "WWCW" token). This is the rubber-duck-as-the steward reasoning footprint. Word-boundaried; requires
#     an actual derive-from-the steward shape, not merely the name "the steward" in passing.
WWCW_SIMULATE_RE = re.compile(
    r"("
    r"what\s+would\s+corey\s+(?:want|do|say|think|decide)|"                    # the the steward-sim question itself
    r"simulate[-\s]?corey|simulat\w*\s+(?:corey|as\s+corey)|"                  # "simulate the steward" / "simulating as the steward"
    r"given\s+(?:his|corey'?s)\s+(?:rules|directives|pattern|teaching)|"       # derive FROM his rules
    r"corey\s+would\s+(?:want|say|approve|prefer|tell\s+me|push\s+back)|"      # "the steward would want/say/approve…"
    r"channel\w*\s+corey|as\s+corey\s+would|"                                  # "channeling the steward" / "as the steward would"
    r"rubber[-\s]?duck\w*\s+(?:as\s+)?corey|"                                  # rubber-duck-as-the steward
    r"corey[-\s]?sim\b|corey\s+simulation"                                     # "the steward-sim" / "the steward simulation"
    r")",
    re.IGNORECASE,
)

# (b) RESOLUTION — proof the block was RESOLVED, not left hanging. Two acceptable resolution shapes:
#     ACT+RECORD (the mind actually fired/decided + recorded), OR ASK-SHOWING-WORK (a precise sub-fork that
#     genuinely needs the steward, derived — not a bare "what do you want?"). Either co-located with the block
#     proves the run RESOLVED. A SIMULATE with NEITHER = a started-but-hanging run = still a FAIL.
WWCW_RESOLVE_RE = re.compile(
    r"("
    # --- ACT+RECORD family (the mind acted on its own derived verdict) ---
    r"act\s*\+\s*record|act\s+and\s+record|acting\s+and\s+recording|act[-\s]?record\b|"
    r"so\s+i'?ll\s+(?:act|proceed|do|go\s+ahead|fire|run|record)\b|"           # "so I'll act/proceed/fire"
    r"i(?:'?m| am)\s+(?:acting|proceeding|recording|firing|deciding)\b|"        # "I'm acting/proceeding/deciding"
    r"decision\s+recorded|recorded\s+the\s+decision|recording\s+(?:the\s+)?decision|"
    r"i\s+(?:decided|will\s+proceed|am\s+proceeding)\b|"                       # "I decided …"
    r"act(?:ing|ed)?\s+by\s+default|default(?:ing)?\s+to\s+act|"               # "act by default" (the wwcw posture)
    r"high\s+confidence\b.{0,80}?(?:act|proceed|fire|record|decid)|"           # rated-high → then acted (one beat)
    r"reversible\b.{0,80}?(?:act|proceed|fire|so\s+i)|"                        # "reversible → I'll act"
    # --- ASK-SHOWING-WORK family (a derived, precise sub-fork that genuinely needs the steward) ---
    r"the\s+only\s+(?:sub-?fork|part|piece|thing)\s+(?:that\s+)?(?:genuinely\s+)?needs?\s+corey|"
    r"genuinely\s+(?:a\s+)?corey[-\s]?fork|genuinely\s+needs\s+corey\s+because|"
    r"narrowed\s+(?:it\s+)?to\s+(?:the\s+)?(?:one\s+)?(?:question|fork|decision)\s+(?:that\s+)?needs?\s+corey|"
    r"irreversible\b.{0,80}?(?:so\s+i\s+ask|needs?\s+corey|corey[-\s]?fork)"   # derived-irreversible → ask (correct defer)
    r")",
    re.IGNORECASE | re.DOTALL,
)

# (3) STRUCTURED-MARKER — a RESOLUTION-SHAPED announcement a real run MAY emit. 🚨 v3 (2026-06-20): the
#     marker is NO LONGER a single-signal clear (that was the v2 leak the auditor caught: a bare
#     'ACT+RECORD:' token cleared a block with no SIMULATE). The marker now satisfies only the RESOLVE
#     HALF of the clear-condition; it STILL requires a co-located SIMULATE-the steward derivation to clear the
#     block (per _block_cleared_by_colocated_run). A self-announced 'ACT+RECORD:' with no the steward-sim near
#     it = a bare resolution token = does NOT clear. The marker shapes a run emits per the wwcw skill /
#     wwcw-ruleset; it is a stronger RESOLVE signal than prose, but never a stand-alone bypass of the AND.
WWCW_MARKER_RE = re.compile(
    r"("
    r"\bWWCW[-\s]?RUN\s*:|"                                                    # "WWCW-RUN:" structured marker
    r"\bACT\s*\+\s*RECORD\s*:|"                                                # "ACT+RECORD:" structured marker
    r"\bWWCW\s+VERDICT\s*:|"                                                   # "WWCW VERDICT:" structured marker
    r"\bWWCW[-\s]?RESOLVED\b|"                                                 # "WWCW-RESOLVED"
    r"\[WWCW\b"                                                                # "[WWCW …]" bracketed run tag
    r")",
    re.IGNORECASE,
)

# Forbidden model literals inside a Workflow/agent script. Allowed: claude-opus-4-8, MiniMax-M3.
# CRITICAL anti-false-positive rule (learned 2026-06-18 from real-session test): the literal must
# be in a MODEL-ASSIGNMENT context (a `model:`/`model=` field, or a quoted model value), NOT bare
# prose that merely NAMES a forbidden model (e.g. a doc describing the ban, or a `/`-delimited skill
# list like `anti-fab/fable/cir-audit`). We therefore anchor every pattern to an assignment shape.
#   We FLAG: model field assigned to opus-4.7 / bare 'opus' / 'fable' / bare 'sonnet'|'haiku'.
#   We ALLOW: model assigned to claude-opus-4-8 or MiniMax-M3 (handled by MODEL_ALLOWED_RE).
_MODEL_FIELD = r"""model\s*[:=]\s*['"]\s*"""   # model: '   /   model = "
MODEL_FORBIDDEN_PATTERNS = [
    # model field assigned to an opus-4.7 literal in any quoting
    (re.compile(_MODEL_FIELD + r"""[^'"]*opus[\s_-]*4\.7""", re.IGNORECASE), "model=opus-4.7"),
    # model field assigned to 'fable'
    (re.compile(_MODEL_FIELD + r"""fable\s*['"]""", re.IGNORECASE), "model=fable"),
    # model field assigned to bare 'opus' (NOT claude-opus-4-8 — the value is exactly opus)
    (re.compile(_MODEL_FIELD + r"""opus\s*['"]""", re.IGNORECASE), "model=bare-opus"),
    (re.compile(_MODEL_FIELD + r"""sonnet\s*['"]""", re.IGNORECASE), "model=bare-sonnet"),
    (re.compile(_MODEL_FIELD + r"""haiku\s*['"]""", re.IGNORECASE), "model=bare-haiku"),
]
MODEL_ALLOWED_RE = re.compile(r"(claude-opus-4-8|minimax-m3)", re.IGNORECASE)

# canon_append presence inside a script (the memory-emit).
CANON_APPEND_RE = re.compile(r"canon[_\-]?append", re.IGNORECASE)
# A script that spawns/forks specialist agents (so it OUGHT to emit memory).
SCRIPT_HAS_AGENT_RE = re.compile(r"\bagent\s*\(", re.IGNORECASE)

# PASS / proven / verified / done — claim language (assistant text).
CLAIM_PASS_RE = re.compile(
    r"\b(verified|proven|confirmed|all\s+green|passes?\b|passed\b|"
    r"works?\s+(clean|correctly)|done\b|✅)",
    re.IGNORECASE,
)
# DONE-DONE completion language.
COMPLETE_CLAIM_RE = re.compile(
    r"\b(complete|completed|shipped|ready\s+to\s+ship|ready\s+for|"
    r"finished|landed|good\s+to\s+go)\b",
    re.IGNORECASE,
)

# API-error text.
API_ERROR_RE = re.compile(r"^\s*API\s+Error\b", re.IGNORECASE)

# Floor skills that a sprint/grounding pass is expected to load.
# (Deterministic membership test; advisory — see noise notes.)
FLOOR_SKILLS = {
    "self-knowledge",
    "sprint-mode",
    "grounding-docs",
    "wwcw",
    "integration",
    "primary-spine",
    "aiciv-spine",
}
# Prompt markers that indicate a sprint / grounding pass is starting.
SPRINT_PROMPT_RE = re.compile(r"(/sprint-mode|/?grounding-docs|sprint\s+mode|grounding\s+boop)", re.IGNORECASE)

# Tools that mutate the substrate directly (specialist work if done OUTSIDE a workflow by Primary).
PRIMARY_MUTATING_TOOLS = {"Edit", "Write", "Bash"}
# Bash sub-commands that are allowlisted as orchestration-level (read/route), not specialist mutation.
# Conservative: this is Stage-2 territory; we only emit CANDIDATE hits.

# ---------------------------------------------------------------------------
# PROJECT-FOLDER-TOUCH markers (project-folder devlog-compliance check, 2026-06-19).
# Deterministic detection that a cycle TOUCHED a project folder (projects/<x>/...) via an
# Edit/Write, and whether that same project's DEVLOG/CHANGELOG was updated in the SAME cycle
# (the same scoped turn-window). The discipline this guards (moon-project-systems doctrine):
# any real contribution under projects/<x>/ MUST land in that project's devlog/changelog the
# same cycle — else the living-master rots and the next incarnation works against stale state.
# CANDIDATE-only (heuristic — a cycle may legitimately touch a project folder without a devlog
# entry, e.g. a read-only-ish rename; Stage-2 / HUM weighs intent + routes the real defects).
# PII-safe: emits the project NAME + the FILE BASENAME only (paths are not secrets; contents are
# never read), never the surrounding human text or file contents.
# ---------------------------------------------------------------------------

# Match a repo-relative path under projects/<project>/... and capture <project>.
# Anchored to the projects/ prefix (abs paths are normalized to repo-relative before matching).
PROJECT_PATH_RE = re.compile(r"^projects/([^/]+)/")
# Filenames (basename, case-insensitive) that COUNT as a project's devlog/changelog/progress
# discipline surface. A touch of any of these under projects/<x>/ = "<x> devlog updated this cycle".
# Generous on the canonical discipline names (DEVLOG / CHANGELOG / PROGRESS / KANBAN) + the
# moon-project-systems living-master surfaces (MASTER-INDEX, ADR files).
DEVLOG_BASENAME_RE = re.compile(
    r"^("
    r"devlog|"
    r"change[-_]?log|"
    r"progress|"
    r"kanban([-_].*)?|"
    r"00[-_]master[-_]index|master[-_]index|"
    r"adr[-_].*"          # a numbered ADR entry counts as a logged decision
    r")\.(md|markdown|jsonl|json|txt)$",
    re.IGNORECASE,
)


def _project_of_path(fp):
    """Return the <project> name if fp is under projects/<project>/..., else None.
    Normalizes an abs the civilization path to repo-relative first. Path only — never reads contents."""
    if not isinstance(fp, str) or not fp:
        return None
    rel = fp
    for root in ((os.environ.get("CIV_ROOT", os.environ.get("AICIV_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + "/"),):
        if rel.startswith(root):
            rel = rel[len(root):]
    m = PROJECT_PATH_RE.match(rel)
    return m.group(1) if m else None


def _is_devlog_basename(fp):
    """True if fp's basename matches the devlog/changelog/progress discipline surface."""
    if not isinstance(fp, str) or not fp:
        return False
    base = os.path.basename(fp)
    return bool(DEVLOG_BASENAME_RE.match(base))

# ---------------------------------------------------------------------------
# DOC-CURRENCY markers (the DOC-UP-TO-DATE mandate, 2026-06-19).
# steward directive: "HUM is supposed to MANDATE keeping these things up to date... not wired
# sufficiently." The PROJECT-FOLDER-TOUCH check above is too NARROW — it only catches
# projects/<x>/ edits without a same-cycle projects/<x>/devlog. The DOCUMENTATION-STALENESS that
# lets a day evaporate is BROADER: keep-worthy work landed (canon_appends / new reports / finish-
# list items / mission-vision decisions) WITHOUT a corresponding update to the relevant DEVLOG
# (self-knowledge / m3-combo program-home docs) AND/OR the civ WORKBOARD.
#
# THIS CHECK (DOC-CURRENCY) detects that gap MECHANICALLY, by RECEIPT not claim: it compares the
# count + latest-timestamp of keep-worthy SIGNALS in the scoped turns against the on-disk MTIME of
# the canonical doc-currency surfaces (WORKBOARD + the program-home devlogs). A surface whose mtime
# is OLDER than the latest keep-worthy turn in the scoped window = STALE = a candidate doc-currency
# defect. Receipt = the file's ACTUAL mtime vs the session's ACTUAL keep-worthy work — not a
# self-report that "I updated the docs". (Per the steward today: verify ACTUAL RECEIPT — the behavior
# happened on disk — not a self-report.)
#
# ADDITIVE + CANDIDATE-ONLY: this NEVER hard-fails HUM or blocks a session. It DETECTS + grades +
# routes (warn), exactly like the other Stage-2-candidate checks. A cycle may legitimately do
# keep-worthy work whose home is NOT one of these surfaces (e.g. a VP silo append); Stage-2/HUM
# weighs intent + routes the real staleness to the doc-update organ (integration / mind-lead).
# PII-safe: emits surface NAME + mtime-delta-seconds + keep-worthy COUNTS only — never file content,
# never the human text, never a canon item body.
# ---------------------------------------------------------------------------

# The canonical DOC-CURRENCY surfaces: the civ WORKBOARD + the two named program-home devlogs.
# Each entry: (label, repo-relative path). mind-lead owns all three (WORKBOARD + the doc-staleness
# mandate). Kept as repo-relative paths resolved against ROOT at runtime (mtime read; contents never).
DOC_CURRENCY_SURFACES = [
    ("WORKBOARD", "WORKBOARD.md"),
    # v1.5.1 PATH FIX (mind-lead, 2026-06-19): the "devlog" surfaces must point at the
    # PROGRAM-HOME DEVLOGs (where the document-the-day LEARN entries actually land), NOT at the
    # SKILL.md skill DEFINITIONS. v1.5 pointed at autonomy/skills/*/SKILL.md, which are skill
    # specs that change rarely (self-knowledge/SKILL.md was ~41h stale on the v1.5 first run →
    # FALSE-POSITIVE STALE, while the real projects/self-knowledge/DEVLOG.md was ~28min fresh and
    # contained that day's LEARN entries). m3-combo had the SAME wrong-path defect, masked only
    # because its SKILL.md happened to be edited that day. Both now read their real DEVLOG.
    ("self-knowledge-devlog", "projects/self-knowledge/DEVLOG.md"),
    # NOTE (2026-07-09, ACG Auditor-B MINOR): the origin-specific
    # "projects/AI-CIV/m3-combo/DEVLOG.md" entry was DROPPED — it named an origin
    # project a fork does not have, producing a false-positive STALE on every fork.
    # A fork adds its own program DEVLOG paths here (relative to CIV_ROOT).
]
DOC_CURRENCY_ROOT = os.environ.get("CIV_ROOT", os.environ.get("AICIV_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# GRACE WINDOW (seconds). The staleness test is NOT "doc mtime must be after the VERY LAST keep-worthy
# turn" — that is too strict: during active work you canon_append, update the doc, then canon_append
# AGAIN, leaving the doc a few minutes "behind" the last signal even though it WAS just updated this
# cycle. The real "a day evaporated" defect is a doc whose mtime predates the cycle's work by a LONG
# margin (or never updated). So: a surface is CURRENT if its mtime is within GRACE_WINDOW_S of (i.e.
# at-or-after, minus grace) the latest keep-worthy turn — it was touched as part of THIS cycle's work.
# It is STALE only if its mtime is MORE than GRACE_WINDOW_S BEFORE the latest keep-worthy turn (the doc
# was not meaningfully updated alongside the work). 2h grace absorbs a normal active-cycle work-then-doc
# cadence while still catching the genuine "worked all day, never touched the devlog/WORKBOARD" case.
DOC_CURRENCY_GRACE_WINDOW_S = 7200  # 2 hours

# A keep-worthy SIGNAL is a session event that SHOULD be reflected in a devlog/WORKBOARD:
#   (1) a canon_append Bash invocation  (a substrate-delta was committed → keep-worthy by definition)
#   (2) a Write of a NEW report under data/reports/*.md  (a report is a keep-worthy artifact)
#   (3) a finish-list / mission / vision decision marker in an assistant turn (a recorded decision)
#   (4) 🆕 a substantive BUILD edit — an Edit/Write to a SUBSTRATE-shaped path (a SKILL.md, a
#       team-lead manifest.md, a tools/*.py, a workflows/*.js). A build arc IS keep-worthy work that
#       SHOULD be reflected in WORKBOARD — and it was the EXACT gap that let WORKBOARD go stale after
#       a build while DOC-CURRENCY returned surfaces_checked:0. See §WHY-SURFACES-CHECKED-0 below.
# All four are MECHANICAL + deterministic. We capture, per signal, the turn's timestamp (for the
# mtime comparison) — never the content.
#
# 🚨 §WHY-SURFACES-CHECKED-0 (the gap this fix closes; fleet-lead 2026-06-22, steward-directed GO):
#   Tonight DOC-CURRENCY returned surfaces_checked:0 after a real build arc — it did NOT catch
#   WORKBOARD staleness. ROOT CAUSE (walked): the keep-worthy signal set was canon_append +
#   data/reports-Write + decision-marker ONLY. A build arc that does substantial Edit/Write to
#   SKILLs / manifests / tools / workflows (the COMMON shape of fleet/mind/workflow work) produces
#   ZERO of those three signals → keepworthy_total==0 → check_doc_currency takes the
#   "vacuously compliant (pass, no hits)" branch → the hum-doc-currency agent counts ZERO distinct
#   surfaces in the (empty) hits → surfaces_checked:0. The check was structurally BLIND to build-shaped
#   keep-worthy work, so a stale WORKBOARD after a build never even got compared. THE FIX: a build edit
#   to a substrate-shaped path is a 4th keep-worthy signal — so a build arc now MAKES the check run
#   (surfaces_checked>0) and the stale-WORKBOARD comparison actually fires. (Conservative: only
#   SUBSTRATE-shaped paths count — not every Edit, so an edit to e.g. a scratchpad/devlog itself is not
#   a self-triggering keep-worthy signal. .bak files + the doc-currency surfaces themselves are excluded
#   so the check never flags itself.)
CANON_APPEND_CMD_RE = re.compile(r"canon_append(\.py)?\b", re.IGNORECASE)
# A new-report Write target: data/reports/<name>.md (the keep-worthy-report convention).
REPORT_PATH_RE = re.compile(r"(^|/)data/reports/[^/]+\.(md|markdown)$", re.IGNORECASE)
# (4) A substantive BUILD-edit target: a substrate-shaped path whose change is keep-worthy work that
# SHOULD land in WORKBOARD. Matched against the repo-relative path of an Edit/Write file_path.
# SUBSTRATE-shaped = a SKILL.md (any skills tree), a team-lead manifest.md, a tools/*.py, a
# workflows/*.js. Conservative by design (not "any Edit") so the signal stays specific to BUILD arcs.
BUILD_EDIT_PATH_RE = re.compile(
    r"(^|/)("
    r"autonomy/skills/[^/]+/SKILL\.md|"        # a skill definition (the most common build artifact)
    r"\.claude/skills/[^/]+/SKILL\.md|"
    r"(autonomy|\.claude)/team-leads/[^/]+/(manifest|FIRING_CONTRACT)\.md|"  # a VP manifest / firing-contract
    r"tools/[^/]+\.py|"                          # a tool
    r"workflows/[^/]+\.js"                       # a workflow
    r")$",
    re.IGNORECASE,
)
# Paths that must NEVER count as a build-edit keep-worthy signal even though they may match the
# substrate shape: a .bak snapshot (not a real edit) and the doc-currency surfaces themselves
# (editing WORKBOARD / a tracked devlog is the REMEDIATION, not the work that triggers the check —
# excluding them prevents the check from ever self-triggering on its own remediation).
BUILD_EDIT_EXCLUDE_RE = re.compile(r"\.bak(\.|$)|(^|/)WORKBOARD\.md$|(^|/)DEVLOG\.md$|(^|/)CHANGELOG\.md$", re.IGNORECASE)
# Decision-shaped markers in assistant prose that name a finish-list / mission / vision decision.
# Conservative + word-boundaried: requires an explicit decision/finish/mission/vision shape, not the
# bare words. These are the "mission/vision decisions" + "finish-list items" the directive names.
DECISION_MARKER_RE = re.compile(
    r"\b("
    r"finish[-\s]?list\b|"
    r"finish[-\s]?item\b|"
    r"(mission|vision)\s+(decision|update|change|amend|ratif)|"
    r"ratified\b|"
    r"constitutional(ize|ized|-tier)\b|"
    r"decision\s+recorded\b|"
    r"keep[-\s]?worthy\b"
    r")",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 🔎 HUM-MANDATE checks (mind-lead 2026-06-20, ADDITIVE): two deterministic checks that enforce the
# HUM per-boop discipline ON REVIEW. Companion to workflows/hum.js v1.0 (the mission + mandatory
# checklist + find-the-miss build). These fire ONLY when a HUM fire is observed in the scanned window
# (a Workflow tool-use naming workflows/hum.js); on a window with NO HUM fire they are status="na"
# (nothing to enforce). HONEST enforcement: a HUM fire that left no saved checklist doc, or recorded no
# find-the-miss, is FLAGGED. PII-safe: paths + mechanical counts only, never message content.
# ---------------------------------------------------------------------------
# A HUM fire signature in the session: a Workflow tool-use (or prose) naming workflows/hum.js. Same
# signal check_grounding_completeness uses for saw_hum_fired.
HUM_FIRE_PATH = "workflows/hum.js"
# The checklist-doc save directory (relative to ROOT). hum.js COMPOUND writes the completed doc here
# EVERY boop. The det-check confirms a doc was saved (mtime in-window OR a Write tool-use to the dir).
HUM_CHECKLISTS_DIR_REL = ".claude/team-leads/mind/memory/hum-checklists"
HUM_CHECKLISTS_DIR_ABS = os.path.join(DOC_CURRENCY_ROOT, HUM_CHECKLISTS_DIR_REL)
# A find-the-miss SIGNAL in the session: hum.js v1.0 bubbles a find_the_miss field to the CEO + the
# ledger records a "find_the_miss:" line. Either the firewall field name or the ledger line counts as
# "a find-the-miss was recorded this fire". Word-boundaried, conservative.
FIND_THE_MISS_SIGNAL_RE = re.compile(r"find[_\s-]?the[_\s-]?miss", re.IGNORECASE)
# The checklist-save SIGNAL in the session: hum.js returns checklist_doc_saved / checklist_doc_path,
# and the ledger records "checklist_doc:". Any of these naming the checklist counts.
CHECKLIST_SAVE_SIGNAL_RE = re.compile(r"(checklist_doc|hum-checklist|checklist_doc_saved|hum-checklists)", re.IGNORECASE)


def _hum_fire_window(turns):
    """Return (saw_hum_fire, earliest_hum_fire_epoch) over the scanned turns. A HUM fire = a Workflow
    tool-use whose script names workflows/hum.js, or prose naming it. Mirrors saw_hum_fired in
    check_grounding_completeness. earliest_hum_fire_epoch is the epoch of the FIRST observed fire (for
    the checklist-mtime comparison), or None if no timestamp."""
    saw = False
    earliest = None
    for t in turns:
        if t["role"] != "assistant":
            continue
        fired_here = False
        for tu in t["tool_uses"]:
            st = script_text(tu)
            if tu.get("name") == "Workflow" and st and HUM_FIRE_PATH in st:
                fired_here = True
            elif st and HUM_FIRE_PATH in st:
                fired_here = True
        if not fired_here and (t.get("text") and HUM_FIRE_PATH in t["text"]):
            fired_here = True
        if fired_here:
            saw = True
            ep = _turn_epoch(t)
            if ep is not None and (earliest is None or ep < earliest):
                earliest = ep
    return saw, earliest


def _newest_checklist_doc_mtime():
    """Return the mtime (epoch float) of the most-recently-saved checklist doc in HUM_CHECKLISTS_DIR,
    or None if the dir is absent/empty. Reads ONLY directory listing + os.path.getmtime — never opens
    a file's contents (PII-safe)."""
    try:
        names = [n for n in os.listdir(HUM_CHECKLISTS_DIR_ABS) if n.startswith("hum-checklist") and n.endswith(".md")]
    except Exception:
        return None
    newest = None
    for n in names:
        try:
            m = os.path.getmtime(os.path.join(HUM_CHECKLISTS_DIR_ABS, n))
        except Exception:
            continue
        if newest is None or m > newest:
            newest = m
    return newest


def check_checklist_saved(turns):
    """🔎 HARD (mind-lead 2026-06-20): a HUM fire that left NO saved checklist doc is FLAGGED.

    HUM v1.0 SAVES the completed per-boop checklist to disk EVERY boop (deterministic). This check
    enforces that ON REVIEW. NA when no HUM fire is observed in the scanned window (nothing to enforce).
    When a HUM fire IS observed, it is COMPLIANT (pass) if EITHER:
      (a) a Write tool-use targeting the hum-checklists dir appears in-window (the save was observed), OR
      (b) a checklist-save signal appears in-window (checklist_doc / hum-checklist named in prose/return), OR
      (c) the newest checklist doc on disk has mtime AT/AFTER the first HUM fire's epoch (the doc landed).
    Otherwise FLAG (a HUM fire with no checklist-save evidence — the mandatory save was skipped).

    🛡️ FALSE-FAIL GUARD: fires ONLY when a HUM fire was genuinely observed AND no save evidence exists by
    ANY of the three independent signals. A window with no HUM fire = na; any one signal = pass. We never
    flag a non-HUM window, and any single piece of save evidence clears it. PII-safe: paths + counts only."""
    saw_hum, hum_epoch = _hum_fire_window(turns)
    if not saw_hum:
        return "na", []
    # (a) a Write to the checklist dir, observed in-window
    saw_write = False
    # (b) a checklist-save signal in prose or a tool input, in-window
    saw_signal = False
    for t in turns:
        if t["role"] != "assistant":
            continue
        if t.get("text") and CHECKLIST_SAVE_SIGNAL_RE.search(t["text"]):
            saw_signal = True
        for tu in t["tool_uses"]:
            if tu.get("name") == "Write":
                inp = tu.get("input")
                fp = inp.get("file_path") if isinstance(inp, dict) else None
                if isinstance(fp, str) and HUM_CHECKLISTS_DIR_REL in fp:
                    saw_write = True
            st = script_text(tu)
            if st and CHECKLIST_SAVE_SIGNAL_RE.search(st):
                saw_signal = True
    # (c) the newest checklist doc on disk landed at/after this fire
    saw_disk = False
    newest = _newest_checklist_doc_mtime()
    if newest is not None and hum_epoch is not None and newest >= (hum_epoch - 300):
        saw_disk = True
    elif newest is not None and hum_epoch is None:
        # could not timestamp the fire; a present doc on disk is corroborating (don't false-fail)
        saw_disk = True

    if saw_write or saw_signal or saw_disk:
        return "pass", [{"turn_index": -1,
                         "brief": ("HUM fire observed + checklist-save evidence present "
                                   f"(write={saw_write}, signal={saw_signal}, disk={saw_disk})"),
                         "checklist_saved": True,
                         "candidate": False}]
    return "flag", [{"turn_index": -1,
                     "brief": ("CHECKLIST-SAVED: a HUM fire was observed in-window but NO saved checklist "
                               "doc evidence (no Write to hum-checklists/, no checklist_doc signal, no "
                               "in-window doc on disk) — the mandatory per-boop checklist save was SKIPPED"),
                     "checklist_saved": False,
                     "candidate": False}]


def check_find_the_miss_present(turns):
    """🔎 HARD (mind-lead 2026-06-20): a HUM fire with NO find-the-miss recorded is FLAGGED.

    HUM v1.0 is schema-REQUIRED to emit ≥1 find_the_miss EVERY boop (the immune-system mandate). This
    check enforces that ON REVIEW. NA when no HUM fire is observed in the scanned window. When a HUM fire
    IS observed, it is COMPLIANT (pass) if a find-the-miss signal appears in-window (the find_the_miss
    field bubbled to the CEO / the ledger's 'find_the_miss:' line / prose naming it). Otherwise FLAG.

    🛡️ FALSE-FAIL GUARD: fires ONLY when a HUM fire was genuinely observed AND no find-the-miss signal
    exists at all in-window. A non-HUM window = na. Any find-the-miss mention clears it. PII-safe."""
    saw_hum, _ = _hum_fire_window(turns)
    if not saw_hum:
        return "na", []
    saw_ftm = False
    for t in turns:
        if t["role"] != "assistant":
            continue
        if t.get("text") and FIND_THE_MISS_SIGNAL_RE.search(t["text"]):
            saw_ftm = True
            break
        for tu in t["tool_uses"]:
            st = script_text(tu)
            if st and FIND_THE_MISS_SIGNAL_RE.search(st):
                saw_ftm = True
                break
        if saw_ftm:
            break
    if saw_ftm:
        return "pass", [{"turn_index": -1,
                         "brief": "HUM fire observed + find-the-miss recorded (immune-mandate honored)",
                         "find_the_miss_present": True,
                         "candidate": False}]
    return "flag", [{"turn_index": -1,
                     "brief": ("FIND-THE-MISS-PRESENT: a HUM fire was observed in-window but NO find-the-miss "
                               "signal recorded (no find_the_miss field / ledger line / prose) — the immune-"
                               "system mandate (>=1 genuine miss every boop) was SKIPPED"),
                     "find_the_miss_present": False,
                     "candidate": False}]


# ---------------------------------------------------------------------------
# 🧹 SWEEP-ACT-ON-FLAGGED markers (fleet-lead 2026-06-22, steward-directed GO). The gap this closes:
# tonight auto-consolidate ran + HONESTLY self-reported NOT-CLEAN twice, but Primary DEFERRED the fixes
# (notice-don't-act). The auto-consolidate SKILL now MANDATES act-on-flagged (home/wire/close IN-BOOP, OR
# name a concrete owner+trigger) and never flag-and-vague-defer. This check enforces that ON REVIEW:
# a consolidation sweep that SELF-REPORTS not-clean (found something un-homed / un-wired / a human-asked
# workflow open) but shows NO act-in-boop (no home scaffolded, no skill-forge hand-off, no concrete
# owner+trigger named) → a real discipline-skip the JUDGE confirms as FAIL.
#
# 🧠 JUDGING-MIND, NOT BASH-REGEX (the steward "no scripts if possible"): this deterministic layer ONLY surfaces
# the mechanical signal (sweep-said-NOT-CLEAN + no-act-marker in-window). It is CANDIDATE-only — the HUM
# JUDGE (a separate incarnation that WALKS the window) confirms intent + assigns the FAIL. The regex never
# decides the verdict; it hands the JUDGE an evidenced candidate to walk. (Same discipline as the other
# Stage-2 candidate checks: detect mechanically, judge with intent.)
#
# A sweep "self-reports NOT-CLEAN" = it names a found-and-un-acted candidate. The HONEST swept-clean result
# ("swept clean — nothing un-homed, nothing un-wired") is the OPPOSITE signal → never flags.
SWEEP_RAN_RE = re.compile(
    r"(auto[-_\s]?consolidat|consolidation\s+sweep|consolidation\s+reflex|swept\s+clean|sweep[-\s]?(?:result|clean|verdict))",
    re.IGNORECASE,
)
# A sweep that found something un-homed / un-wired / a human-asked-workflow open (the NOT-CLEAN report).
# Anchored to consolidation vocabulary so a generic "stale"/"un-homed" elsewhere does not trip it.
SWEEP_NOT_CLEAN_RE = re.compile(
    r"\b("
    r"not[-\s]?clean\b|"
    r"un[-\s]?homed\b|"
    r"un[-\s]?wired\b|"
    r"needs[-\s]?(?:create|update|home|wiring|forge)\b|"
    r"human[-\s]?asked[-\s]?workflow\b|"
    r"human[-\s]?signaled[-\s]?ability\b|"
    r"candidate[-\s]?report\b|"
    r"project[-\s]?shaped\b.{0,40}\bun[-\s]?homed\b"
    r")",
    re.IGNORECASE,
)
# Evidence the sweep ACTED on what it flagged THIS boop. Two acceptable shapes (per the SKILL contract):
#   (1) ACT-IN-BOOP: a home was scaffolded / a skill was forged-or-wired / a register edit landed, OR
#   (2) CONCRETE OWNER+TRIGGER: it routed the flagged item to a named VP/organ WITH a trigger (queued to
#       skill-forge / routed to <vp>-lead / filed to hum-repair-queue / scheduled / a TGIM task_created).
# A VAGUE defer ("will home later", "TODO", "deferred", "noted for next time") is NOT an act — and is
# deliberately ABSENT from this set so it does not clear the flag.
SWEEP_ACTED_RE = re.compile(
    r"\b("
    r"homed\s+(?:at|to)\b|scaffold(?:ed)?\s+(?:a\s+)?(?:home|project)|"
    r"skill[-\s]?forge|forged\b|wired\b|registered\b|register(?:ed)?\s+(?:the\s+)?skill|"
    r"routed\s+to\b|handed\s+to\b|filed\s+to\b|hum[-\s]?repair[-\s]?queue|"
    r"owner\s*[:=]|trigger\s*[:=]|fires?[-\s]?when\b|scheduled\b|task_created\b|"
    r"vp[-\s]?drift[-\s]?flag|integration\s+route"
    r")",
    re.IGNORECASE,
)


def check_sweep_act_on_flagged(turns):
    """CANDIDATE (Stage-2 / HUM): a consolidation sweep self-reported NOT-CLEAN but did NOT act in-boop.

    The notice-don't-act defect (the steward-caught 2026-06-22): auto-consolidate ran, HONESTLY flagged
    NOT-CLEAN, and the fix was DEFERRED. The auto-consolidate SKILL now requires ACT-ON-FLAGGED — home/wire/
    close IN-BOOP, or name a concrete owner+trigger (skill-forge hand-off / vp-route / queue-file). This
    check surfaces the signal for the JUDGE: a sweep that self-reports a found-and-un-acted candidate
    (un-homed / un-wired / human-asked-workflow open / needs-create) WITHOUT any act-evidence in the window.

    CANDIDATE-only (the JUDGE confirms intent + assigns FAIL — judging-mind, not bash-regex per the steward).
    PII-safe: marker-class + turn_index only; never the human text.

    🛡️ FALSE-FAIL GUARD (airtight): fires ONLY when BOTH (a) a sweep ran AND self-reported NOT-CLEAN
    (a found-and-un-acted candidate named), AND (b) NO act-evidence appears anywhere in the window. A
    sweep that swept CLEAN ('nothing un-homed, nothing un-wired') = pass. A sweep that acted (homed /
    forged / routed-with-trigger) = pass. A window with NO sweep at all = na (nothing to enforce —
    a non-grounding turn does not owe a sweep)."""
    saw_sweep = False
    saw_not_clean = False
    saw_acted = False
    not_clean_idx = None
    for t in turns:
        if t["role"] != "assistant":
            continue
        txt = t.get("text") or ""
        # also scan tool-call script text (a sweep result may be written into a scratchpad Write)
        blob = txt
        for tu in t["tool_uses"]:
            st = script_text(tu)
            if st:
                blob += "\n" + st
        if SWEEP_RAN_RE.search(blob):
            saw_sweep = True
        if SWEEP_NOT_CLEAN_RE.search(blob) and SWEEP_RAN_RE.search(blob):
            # require the not-clean signal to CO-OCCUR with sweep vocabulary in the SAME turn-blob, so a
            # generic "un-wired" elsewhere in the session does not masquerade as a sweep verdict.
            saw_not_clean = True
            if not_clean_idx is None:
                not_clean_idx = t["idx"]
        if SWEEP_ACTED_RE.search(blob):
            saw_acted = True

    # No sweep ran at all → nothing to enforce (na). A non-grounding turn does not owe a sweep.
    if not saw_sweep:
        return "na", []
    # Sweep ran but reported CLEAN (or reported nothing not-clean) → honest clean result → pass.
    if not saw_not_clean:
        return "pass", [{"turn_index": -1,
                         "brief": "consolidation sweep ran + no not-clean self-report (swept-clean or acted) — compliant",
                         "sweep_not_clean": False, "sweep_acted": saw_acted, "candidate": True}]
    # Sweep reported NOT-CLEAN AND acted somewhere in-window → compliant (acted-on-flagged) → pass.
    if saw_acted:
        return "pass", [{"turn_index": not_clean_idx if not_clean_idx is not None else -1,
                         "brief": "consolidation sweep self-reported NOT-CLEAN AND acted in-boop (homed/forged/routed-with-trigger) — act-on-flagged honored",
                         "sweep_not_clean": True, "sweep_acted": True, "candidate": True}]
    # Sweep reported NOT-CLEAN AND NO act-evidence in-window → the notice-don't-act defect → CANDIDATE flag.
    return "flag", [{"turn_index": not_clean_idx if not_clean_idx is not None else -1,
                     "brief": ("SWEEP-ACT-ON-FLAGGED: a consolidation sweep SELF-REPORTED NOT-CLEAN "
                               "(found un-homed / un-wired / human-asked-workflow / needs-create) but shows "
                               "NO act-in-boop (no home/forge/register + no concrete owner+trigger route) — "
                               "the notice-don't-act defect (flag-and-vague-defer). JUDGE: confirm intent → FAIL"),
                     "sweep_not_clean": True, "sweep_acted": False, "candidate": True}]


def _surface_mtime(rel_path):
    """Return the on-disk mtime (epoch seconds, float) of a doc-currency surface, or None if absent.
    Reads ONLY os.path.getmtime — never opens/reads the file's contents."""
    fp = os.path.join(DOC_CURRENCY_ROOT, rel_path)
    try:
        return os.path.getmtime(fp)
    except Exception:
        return None


def _turn_epoch(t):
    """Epoch seconds (float) of a turn's timestamp, or None. Pure datetime → epoch; no content read."""
    ts = t.get("ts")
    if ts is None:
        return None
    try:
        return ts.timestamp()
    except Exception:
        return None

# ---------------------------------------------------------------------------
# SKILL-CANDIDATE markers (closure-3 of the consolidation/HUM backstop, 2026-06-18).
# Two deterministic signals that a reusable capability MIGHT be hiding un-wired:
#   (a) a human REMEMBER/SAVE/REUSE marker in a REAL user turn (the human-asked-workflow /
#       human-signaled-ability signal that auto-consolidate Step 4a/4b chases).
#   (b) the SAME command-shape repeating >=2x with no Skill load between (a step-sequence a
#       mind keeps re-doing by hand = a candidate for being a wired skill).
# Both are CANDIDATE-only (heuristic). Stage-2 reads them, runs TRI-SOURCE dedup, and routes
# a genuine reusable-capability to skill-forge. Mechanical briefs only — never the human text.
# ---------------------------------------------------------------------------

# A human asking us to KEEP / SAVE / REUSE / REMEMBER a workflow or ability.
# Matches the 4a/4b signal shapes from auto-consolidate. Conservative + word-boundaried;
# requires an imperative-ish remember/save shape, not merely the word "remember" in passing.
REMEMBER_MARKER_RE = re.compile(
    r"\b("
    r"remember\s+(this|that|how\s+to|to\s+\w+)|"
    r"(save|keep)\s+(this|that|it)\b|"
    r"make\s+(this|that|it)\s+a\s+(thing|skill|workflow|reflex)|"
    r"reuse\s+(this|that|it)\b|"
    r"(run|do)\s+(that|this|it)\s+again\b|"
    r"from\s+now\s+on\b|"
    r"every\s+(morning|day|time|night)\b|"
    r"want\s+me\s+to\s+remember|"
    r"don'?t\s+(lose|forget)\s+(this|that)|"
    r"you\s+should\s+(always\s+be\s+able\s+to|know\s+how\s+to)|"
    # STEWARD-approved widening #1 (2026-06-22): "the steward caught a missing skill" shapes.
    # The prior patterns matched save/reuse but NOT "there should be a git SKILL".
    # Append-only — these ADD coverage, they never alter the patterns above.
    r"there\s+should\s+be\s+an?\s+.{1,60}?\s*(skill|workflow|agent)\b|"
    r"we\s+should\s+have\s+a\s+skill\s+for\b|"
    r"make\s+.{1,60}?\s+a\s+skill\b|"
    r"turn(ed)?\s+.{1,60}?\s+into\s+an?\s+(skill|agent|lead)\b"
    r")",
    re.IGNORECASE,
)

# A normalized "command shape" extractor: the first token (verb) of a Bash command, used to
# detect the SAME hand-run command-sequence repeating. Deliberately coarse (verb-level), so it
# flags repetition of a KIND of step, not exact-string dupes. We compare consecutive Bash runs.
_CMD_SHAPE_RE = re.compile(r"^\s*([a-zA-Z0-9_./-]+)")

# Ubiquitous shell-glue verbs that are NOT meaningful as "a hand-run step worth a skill".
# Repeating `echo`/`cd`/`ls` is normal navigation, not a re-done capability. Skipping these
# keeps the (b) signal pointed at substantive repeated work (scripts, API calls, tools).
_CMD_SHAPE_IGNORE = {
    "echo", "cd", "ls", "cat", "pwd", "true", "false", "export", "set",
    "head", "tail", "wc", "sleep", "mkdir", "cp", "mv", "rm", "touch", "chmod",
}


def _bash_command_shape(tool_use):
    """Coarse shape of a Bash command = its leading verb/binary (e.g. 'python3', 'grep', 'curl').
    Returns None for non-Bash or unparseable. Never returns the full command text."""
    if tool_use.get("name") != "Bash":
        return None
    inp = tool_use.get("input")
    cmd = inp.get("command") if isinstance(inp, dict) else (inp if isinstance(inp, str) else None)
    if not isinstance(cmd, str):
        return None
    m = _CMD_SHAPE_RE.match(cmd)
    if not m:
        return None
    shape = m.group(1)
    if shape in _CMD_SHAPE_IGNORE:
        return None
    return shape


# ---------------------------------------------------------------------------
# GROUNDING-RECEIPT markers (the two grounding-comprehension-gate receipts, 2026-06-19).
# steward directive: HUM must CONFIRM the ACTUAL RECEIPT of (1) the sprint-mode floor read and
# (2) the grounding-docs haiku-per-doc — today they are CLAIMED, not verified, so a shallow/
# skipped grounding slips past and a human has to catch it. The principle (same as canon_recall's
# hit-ledger proving recall): the gate is PROVEN by the ARTIFACT it leaves, not by a self-report.
#   (1) SPRINT-MODE-READ RECEIPT — the load-verify block (the `skill_loaded:` lines from the
#       sprint-mode SKILL) was ACTUALLY written this session (assistant text OR a scratchpad Write).
#       Real in-session evidence, not a claim. If a substantive sprint/grounding pass was invoked
#       but NO load-verify block landed -> flag (the floor was claimed but not received).
#   (2) HAIKU-PER-DOC RECEIPT — read off-session: data/haiku-archive/haikus.jsonl got FRESH
#       entries within THIS session's time window (one {ts, doc, haiku} per doc). If a grounding/
#       slow-sprint was invoked but no fresh haiku entries landed in-window -> flag (the
#       comprehension gate was claimed but not received).
# Both CANDIDATE-only (heuristic — a long manned session may legitimately ground ONCE and then
# do hours of substantive work; Stage-2/HUM weighs intent). PII-safe: counts + the matched marker
# class + the doc NAMES from the haiku archive only (haiku docs are non-sensitive labels), never
# the human text, never the haiku body beyond a count.
# ---------------------------------------------------------------------------

# The load-verify block's signature line. The sprint-mode SKILL writes a multi-line block to the
# top of the session scratchpad beginning with `skill_loaded:` lines (plus wwcw_loaded / hum_loaded
# / verification_floor_resident / hum_last_step_fired). We treat the PRESENCE of >=2 distinct
# `skill_loaded:` lines (or the named single-key load lines) as the receipt the floor was loaded.
# Word-boundaried, anchored to the colon-form the SKILL prescribes; matches in assistant text OR in
# a Write/Edit tool input targeting a scratchpad (the canonical landing place).
SKILL_LOADED_LINE_RE = re.compile(r"(?mi)^\s*skill_loaded\s*:\s*\S")
# The other named single-key load-verify lines the block carries (any one of these co-occurring with
# the skill_loaded lines reinforces it; we count them toward the receipt strength).
LOAD_VERIFY_KEY_RE = re.compile(
    r"(?mi)^\s*(skill_loaded|wwcw_loaded|hum_loaded|verification_floor_resident|hum_last_step_fired|self_knowledge_loaded)\s*:",
)
# A path that looks like the session scratchpad (where the load-verify block canonically lands).
SCRATCHPAD_PATH_RE = re.compile(r"scratchpad", re.IGNORECASE)

# data/haiku-archive/haikus.jsonl — the off-session artifact the grounding-docs haiku gate leaves.
# Each fresh line is one {ts, doc, haiku[, context]}. The HAIKU-PER-DOC receipt reads this file and
# counts entries whose `ts` falls inside THIS session's [first_turn_ts, last_turn_ts] window.
HAIKU_ARCHIVE_PATH = "data/haiku-archive/haikus.jsonl"
# The expected grounding doc-set size (Doc -1, Doc 0, Doc 1..6 + 4a/4b). A FULL grounding leaves
# ~8-10 fresh haiku entries; a slow-sprint leaves ~6. We do not hard-require an exact count (manned
# sessions vary) — we flag the BINARY "grounding/sprint invoked but ZERO fresh in-window haikus",
# which is the unambiguous skipped-comprehension-gate signal, and surface the in-window count so
# Stage-2 can weigh a SHALLOW (few-haiku) grounding too.
HAIKU_DOCSET_EXPECTED = 6

# A prompt/marker that indicates a GROUNDING pass (haiku-per-doc) was invoked. Distinct from the
# broader SPRINT_PROMPT_RE: grounding-docs / grounding-boop / slow-sprint specifically run the haiku
# gate. /sprint-mode (lean) does NOT run haikus — so the haiku receipt only applies when a grounding
# / slow-sprint was actually invoked.
GROUNDING_PROMPT_RE = re.compile(
    r"(/?grounding-docs|grounding\s+boop|grounding-boop|slow[\s-]?sprint|/grounding\b|haiku-per-doc|haiku\s+gate)",
    re.IGNORECASE,
)
# A prompt/marker that indicates a SPRINT-MODE pass was invoked (lean OR slow). Either expects the
# load-verify floor block to land. Reuse SPRINT_PROMPT_RE-style breadth + the grounding markers.
SPRINT_OR_GROUNDING_PROMPT_RE = re.compile(
    r"(/sprint-mode|sprint\s+mode|/?grounding-docs|grounding\s+boop|grounding-boop|slow[\s-]?sprint|/grounding\b)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# GROUNDING-COMPLETENESS markers (the COMPLETE-OR-FAIL contract, 2026-06-20).
# steward directive verbatim 2026-06-20: "Hum needs to check and fully FAIL any boop that isn't hyper
# detailed and complete. Miss one doc or one haiku or one step it's 100% fail on that boop. The
# discipline is EVERYTHING."
#
# CONTEXT (the failure that birthed this gate): the afternoon /sprint-mode cycles (12:51 / 13:53 /
# 14:55) wrote CHEAP receipts — ONE haiku each, a bare load-verify line, NO full doc-read-one-at-a-
# time, NO per-doc haiku, NO auto-consolidate sweep, HUM DEFERRED. The existing receipts checks
# (SPRINT-MODE-READ + HAIKU-PER-DOC) caught "did the floor leave SOME artifact" but NOT "did the
# boop ground COMPLETELY". A boop can pass both prior checks with a single haiku + a single
# load-verify line. This gate enforces the FULL contract: a grounding boop is COMPLETE-or-FAILED.
#
# THE PHILOSOPHY (strict — the steward's "miss one … it's 100% fail"): a grounding boop is graded against
# the ENUMERATED required-element checklist below. If ANY required element is absent → status=flag →
# HARD-FAIL → breaks summary.clean → forces verdict=HOLLOW. Partial completion = full failure. There
# is NO partial credit. The gate checks against the WRITTEN standard the sprint-mode + grounding-docs
# SKILLs DECLARE (so a boop knows it must be complete-or-failed against a published contract, not a
# moving target).
#
# 🛡️ FALSE-FAIL GUARD (HONEST — the steward's explicit guard, NARROWED 2026-06-20 to close the lean-cycle
# loophole `"lean cycle" < discipline`). The gate fires on a boop with EITHER trigger:
#   TRIGGER 1 — a GROUNDING_PROMPT_RE pass (a real grounding/slow-sprint, haiku-bearing) AND ≥1
#               grounding-work-signature (≥1 fresh haiku OR the load-verify block OR a doc-read marker).
#               A TRIGGER-1 pass with NO fresh work this window is exempt ONLY when it is a CORROBORATED
#               clustered re-fire (v5.2 RECENCY-EXEMPTION KILL, fleet-lead 2026-06-20): the dedup marker
#               present OR prior-boop archive haikus in the ts-range. A BARE grounding-pass with no work
#               AND no clustered-re-fire corroboration is the recency-as-excuse dodge → NO LONGER exempt
#               → falls through to grading → 100% FAIL. Every genuine fire grounds fully (clockwork).
#   TRIGGER 2 — a GENUINE /sprint-mode boop (a /sprint-mode command-message / calendar boop + ≥1
#               work-act, NOT a byte-identical 60s dedup re-injection). A genuine /sprint-mode cycle
#               OWES the FULL contract whether or not it left grounding-work signatures — the lean-cycle
#               dodge (a genuine boop that did NO grounding) is EXACTLY what now FAILS.
# The ONLY two remaining exemptions (both honest, neither a discipline-dodge): (a) a byte-identical
# /sprint-mode re-injection within SPRINT_DEDUP_WINDOW_SECONDS (the cadence-lock cluster carve-out);
# (b) a non-/sprint-mode turn (no /sprint-mode boop in the window — a pure status reply / a the steward
# question is never a grounding boop, never failed). Once a boop is a genuine grounding cycle, it must
# ground COMPLETELY or fail 100%.
#
# WHOLE-SESSION (not delta-scoped): like SPRINT-MODE-READ + HAIKU-PER-DOC, the required elements land
# at grounding time (session start / the boop's own turns). Runs against full_turns when provided so a
# later cycle does not falsely flag an earlier-grounded session. PII-safe: counts + element labels +
# marker classes only — never the human text, never a haiku body, never doc contents.
# ---------------------------------------------------------------------------

# The expected number of DISTINCT grounding docs whose haiku must land. The grounding stack
# (grounding-docs/SKILL.md): Doc -1 self-knowledge, Doc -0.5 wwcw (added 2026-06-21), Doc 0
# aiciv-psychology, Doc 1 CLAUDE.md, Doc 2 VERTICAL-TEAM-LEADS, Doc 3 conductor-of-conductors,
# Doc 4 the workflows cluster, Doc 4a hermes-nodes, Doc 4b tgim-doctrine, Doc 5 today's scratchpad,
# Doc 6 latest handoff = 11 docs.
# A COMPLETE grounding leaves ONE context-informed haiku PER doc → ≥ this many distinct fresh
# haiku-docs in-window. (count haikus == count docs, NOT one-haiku-per-cycle — the exact miss the
# afternoon boops committed.) Set to 11 = the full stack; a boop with fewer distinct fresh haiku-docs
# is INCOMPLETE → fails. 🚨 LEAN-CYCLE LOOPHOLE CLOSE (the steward 2026-06-20, `"lean cycle" < discipline`):
# a GENUINE /sprint-mode boop is NO LONGER exempt — it now OWES all 11 per-doc haikus (a lean boop that
# does NOT haiku now FAILS the contract). The count applies to a GROUNDING_PROMPT_RE-invoked boop AND
# to a genuine non-deduped /sprint-mode boop. The ONLY haiku-exempt cases are a byte-identical 60s
# dedup re-injection + a non-/sprint-mode turn (no grounding trigger at all).
# 🚨 v4.3 (2026-06-21, mind-lead — steward directive "Hum manifest should show it checking for read
# commands followed by haiku, and you should be saving all the haikus"): bumped 10 → 11 to match
# fleet-lead's stage-1 grounding-docs SKILL change (grep -cE '^### Doc'=11; the new Doc -0.5 WWCW
# read→haiku doc). count(haikus)==count(docs)==11. Companion: the new READ→HAIKU PAIRING element
# (see check_grounding_completeness element (1b)) verifies each Read tool-call is FOLLOWED by a haiku
# — the PAIRING, not a flat archive count alone.
GROUNDING_COMPLETE_DOCSET = 11

# The required STRUCTURED elements a complete grounding boop MUST emit (beyond the per-doc haikus).
# Each is detected as an ARTIFACT (receipt-not-claim) in assistant text OR a Write/Edit input:
#   • synthesis      — the "I am now [what] ready to [what]" synthesis statement after all haikus.
#   • workflows_mandate — the workflows-for-everything affirmation ("EVERYTHING via workflows" / the
#                    5 Primary-scoped acts re-affirmed).
#   • wwcw_affirm    — the WWCW run-before-asking affirmation re-grounded this pass.
#   • hum_affirm     — the HUM-as-last-step / human-bridge affirmation (the hum_last_step_fired promise
#                    + the bridge discipline).
#   • auto_consolidate — the auto-consolidate sweep was run this pass (the "swept clean / nothing
#                    un-homed, nothing un-wired" reflex — the exact step the afternoon boops skipped).
# load-verify block + the per-doc haikus + HUM-fired are tracked separately (the load-verify block via
# the SPRINT-MODE-READ receipt machinery; the haikus via the docset count; HUM-fired via the promise).
# 🚨 v4.2 (2026-06-21, mind-lead) — ELLIPSIS-TOLERANT GAP (the GROUNDING-COMPLETENESS synthesis-miss
# walked by HUM wa28qwcpv). THE DEFECT: the gap `[^.\n]{0,120}?` forbade ANY period, so an elaborate
# synthesis with a mid-phrase ELLIPSIS — Primary's real 03:00 line "I am now the CEO three hours into a
# clean clockwork night — grounded fully on a fresh hour... ready to route by ownership..." — did NOT
# match (the "hour..." ellipsis tripped the `[^.\n]` exclusion), so saw_synthesis=False even though a
# valid "I am now X, ready to Y" synthesis WAS written. The compact form matched; only ellipsis/period-
# bearing elaborate phrasing evaded. An ellipsis is NOT a sentence boundary inside a synthesis — forbidding
# it was over-strict. THE FIX (narrow): the gap now tolerates a `...`/`…` ellipsis run (and the em-dash is
# already a non-period char) while STILL stopping at a real SENTENCE-ENDING single period — `\.{2,}` / `…`
# are allowed, a lone `.` is not, so the gap cannot swallow across a true sentence break. Cap widened
# 120→160 to absorb the longer elaborate phrasing. NARROW: a turn that has NO "I am now … ready to" at all
# still misses (the gate is not blinded); only the false-NEGATIVE on a real ellipsis-bearing synthesis is
# cured. Companion behavioral lesson recorded: prefer the COMPACT "I am now X, ready to Y" form.
GROUNDING_SYNTHESIS_RE = re.compile(
    r"(i\s+am\s+now\b(?:[^.\n]|\.{2,}|…){0,160}?\bready\s+to\b|"   # "I am now [the X] … ready to [Y]" (ellipsis-tolerant)
    r"i\s+am\s+now\s+the\s+conductor\s+of\s+conductors)",
    re.IGNORECASE,
)
GROUNDING_WORKFLOWS_MANDATE_RE = re.compile(
    r"("
    r"everything\s+(?:delegated\s+)?via\s+workflows|"
    r"workflows[-\s]?for[-\s]?everything|"
    r"every\s*thing\s+(?:via|through)\s+workflows|"
    r"5\s+primary[-\s]?scoped\s+acts|"
    r"think[-\s]?big\s*/?\s*plan\s*/?\s*route|"
    r"unthinkable\s+(?:for\s+you\s+)?to\s+do\s+anything\s+but\s+use\s+workflows"
    r")",
    re.IGNORECASE,
)
GROUNDING_WWCW_AFFIRM_RE = re.compile(
    r"("
    r"\bwwcw\b|what\s+would\s+corey\s+want|"
    r"run[-\s]?before[-\s]?asking|"
    r"simulate[-\s]?corey|act\s*\+\s*record"
    r")",
    re.IGNORECASE,
)
GROUNDING_HUM_AFFIRM_RE = re.compile(
    r"("
    r"\bHUM\b|human[-\s]?bridge|"
    r"hum_last_step_fired|"
    r"immune\s+system|"
    r"fire\s+hum\b|firing\s+hum\b|hum\s+as\s+(?:the\s+)?last\s+step"
    r")",
    re.IGNORECASE,
)
GROUNDING_AUTO_CONSOLIDATE_RE = re.compile(
    r"("
    r"auto[-\s]?consolidate|"
    r"consolidation\s+sweep|"
    r"nothing\s+(?:project[-\s]?shaped\s+)?(?:goes\s+)?un[-\s]?homed|"
    r"nothing\s+(?:skill[-\s]?shaped\s+)?(?:goes\s+)?un[-\s]?wired|"
    r"swept\s+clean\b|"
    r"find[-\s]?before[-\s]?acting"
    r")",
    re.IGNORECASE,
)
# A per-doc DOC-READ marker — the "[CLAUDE.md read]" / "Doc N read" / "[proceeding to doc N]" shape
# the grounding-docs protocol prescribes between reads. Presence of ≥ docset of these is a stronger
# read-one-at-a-time signal than the haiku count alone (a boop that wrote 10 haikus but did NOT read
# one-doc-at-a-time would still lack these). Used as the grounding-work-signature for the false-fail
# guard AND counted toward read-completeness.
GROUNDING_DOCREAD_MARKER_RE = re.compile(
    r"(\[[^\]\n]{1,60}\s+read\]|"                            # "[CLAUDE.md read]" / "[handoff … read]"
    r"\[proceeding\s+to\s+doc|"                              # "[proceeding to doc N]"
    r"\bdoc\s+-?\d+[a-b]?\s+(?:read|done)\b)",               # "Doc 4a read" / "doc -1 done"
    re.IGNORECASE,
)
# A HAIKU signature in assistant prose (the comprehension-gate artifact written AFTER each doc-read).
# The grounding-docs protocol writes each haiku as a 3-line slash-separated phrase, e.g.
# "Events, never PATCH / lowercase priority / name your source, drift". We recognize the canonical
# slash-3 shape (two "/"-separators between three short phrases) — narrow enough not to match prose
# (a sentence rarely has exactly two slashes between three short clauses) but tolerant of spacing.
# Used by the READ→HAIKU PAIRING element (2026-06-21): a Read tool-call FOLLOWED by a haiku is the
# grounding-PROOF (the read was comprehended, not merely opened), not a flat archive count alone.
# PII-safe: used only to COUNT a pairing (presence/absence), never echoed.
HAIKU_LINE_RE = re.compile(
    r"[^\n/]{2,40}?\s*/\s*[^\n/]{2,40}?\s*/\s*[^\n/]{2,40}",   # "phrase / phrase / phrase" (slash-3)
)
# How many turns AFTER a Read tool-call a haiku may appear and still count as PAIRED. A grounding pass
# reads a doc then writes its haiku in the same turn or the immediately-following assistant turn; we
# allow a small look-ahead (a Read tool_result is its own turn, so the haiku lands ~1-2 turns later).
READ_HAIKU_PAIR_WINDOW_TURNS = 4
# A CLUSTERED-RE-FIRE / dedup marker — the signature a boop leaves when a /sprint-mode injection
# RE-FIRES inside the same cycle (a clustered double-injection) and the mind RECOGNIZES it rather
# than re-grounding (it dedups: "deduped … re-fire" / "clustered re-fire" / "double-injection
# re-fire" / "hum_cadence: deduped"). Used as a CORROBORATING exempt signal: a window that carries
# this marker AND did no FRESH turn-windowed grounding work is a recognized lean re-fire (the prior
# full boop already grounded; this window only processed/reported), NOT an incomplete grounding boop.
# 2026-06-20, mind-lead — the second half of the per-cycle false-fire cure (companion to the
# turn-windowed did_grounding_work predicate). PII-safe: matches the dedup/re-fire VOCABULARY class
# only, never human text.
GROUNDING_REFIRE_DEDUP_RE = re.compile(
    r"("
    r"\bdedup(?:e|ed|ing|licat\w*)?\b[^\n]{0,40}\bre[-\s]?fire\b|"   # "deduped … re-fire"
    r"\bre[-\s]?fire\b[^\n]{0,40}\bdedup|"                            # "re-fire … dedup"
    r"\bclustered?\s+re[-\s]?fire\b|"                                 # "clustered re-fire"
    r"\bdouble[-\s]?inject\w*\b[^\n]{0,40}\bre[-\s]?fire\b|"          # "double-injection re-fire"
    r"\bhum[_\s-]?cadence\b[^\n]{0,40}\bdedup"                        # "hum_cadence: deduped"
    r")",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# 🚨 LEAN-CYCLE LOOPHOLE CLOSE (steward directive 2026-06-20, verbatim: `"lean cycle" < discipline`).
# ---------------------------------------------------------------------------
# THE LOOPHOLE (what this closes): GROUNDING-COMPLETENESS originally triggered ONLY on
# GROUNDING_PROMPT_RE (the haiku-bearing slow-sprint shape: /grounding-docs, slow-sprint, …). A BARE
# lean /sprint-mode does NOT match GROUNDING_PROMPT_RE, so it took the `invoked_idx is None → pass`
# branch and was EXEMPT from the completeness contract. Primary used that false-fail guard as a DODGE:
# it called genuine NEW /sprint-mode boops "lean continuation" and skipped the full 10-doc / 10-haiku /
# 9-element grounding ~4x in one day (the 19:1x / 19:50 / 20:0x / 20:51 windows). the steward is killing that
# exemption: `"lean cycle" < discipline` — a lean cycle is a discipline-dodge, NOT a legitimate exemption.
#
# THE NEW RULE: a scoped window that contains a GENUINE /sprint-mode boop now REQUIRES the FULL
# completeness contract (all 9 elements + the 10 per-doc haikus). A GENUINE /sprint-mode boop =
#   (a) a /sprint-mode command-message OR a calendar /sprint-mode boop in the window, AND
#   (b) ≥1 work-act in the window (a real tool-use — the boop actually DID something), AND
#   (c) NOT a byte-identical re-injection within the DEDUP WINDOW (the cadence-lock cluster carve-out).
# A lean /sprint-mode cycle (genuine boop + work but NO full grounding) now FLAGS GROUNDING-COMPLETENESS
# → clean=False → the boop FAILS, exactly the shape Primary dodged.
#
# THE ONLY TWO REMAINING EXEMPTIONS (kept honest — these are NOT discipline-dodges):
#   (a) a byte-identical /sprint-mode RE-INJECTION within SPRINT_DEDUP_WINDOW_SECONDS of a prior
#       /sprint-mode boop — the cadence-lock cluster carve-out (a clustered double-injection that the
#       cron re-fired; the FIRST boop in the cluster carries the grounding, the re-injection is not a
#       new cycle). Detected by byte-identity (same command text) + ts-proximity (≤ the dedup window).
#   (b) a NON-/sprint-mode turn — NO /sprint-mode boop in the scoped window at all (a pure conversation
#       / status reply / answering a the steward question is NEVER a grounding boop, so it is NEVER failed).
# Everything else with a genuine /sprint-mode boop must fully ground or fail.

# A /sprint-mode COMMAND-MESSAGE or a calendar /sprint-mode boop (the genuine cycle trigger). Narrower
# than SPRINT_OR_GROUNDING_PROMPT_RE on purpose: it matches the /sprint-mode INVOCATION shape (the slash
# command or a "sprint-mode boop"/calendar-boop marker), NOT mere prose mentioning sprint mode. The
# command-message the cron/the steward injects is the literal `/sprint-mode` (a user-role turn).
SPRINT_MODE_COMMAND_RE = re.compile(
    r"(/sprint-mode\b|"
    r"sprint[-\s]?mode\s+boop|"
    r"\bsprint[-\s]?mode\b\s*(?:cycle|cron|calendar\s+boop|injection))",
    re.IGNORECASE,
)

# 🎛️ THE DEDUP WINDOW IS THE CADENCE KNOB (single named constant). STEWARD FIRM DIRECTIVE 2026-06-21:
# widen the boop cadence from EVERY HOUR to EVERY 2 HOURS. → PER-2H cadence: ANY /sprint-mode-class boop
# within 2 HOURS of a prior full grounding is the SAME 2-hour cycle (deduped, logged, NOT a 2nd full
# grounding/HUM owed). The FIRST /sprint-mode of a new 2-hour window still OWES the FULL contract
# (per-2h ≠ never — one full grounding per 2-hour window is still required; a genuine 2-hour window with
# zero grounding still FAILS). ⚠️ THE PER-BOOP STANDARD DID NOT SHRINK: only the CADENCE widened. A
# genuine non-deduped /sprint-mode boop still OWES the ENTIRE completeness contract (all 9 elements + the
# 10 per-doc haikus) — see GROUNDING-COMPLETENESS below. This is a CADENCE change, NOT a doc-strip;
# leaner-by-design (fewer docs/haikus per boop) is a SEPARATE future change, not this one.
#   7200 = per-2H  (CURRENT, steward directive 2026-06-21).
#   3600 = per-HOUR (prior — steward ruling 2026-06-20; superseded by the 2026-06-21 widen).
#   60   = strict per-cycle (older default — superseded; kept here only as the documented alternative).
# This is a ONE-LINE knob; the dedup MATCHER (broadened from byte-identical to /sprint-mode-CLASS-aware,
# see _sprint_command_norm + _dedup_clustered_reinjections) is what makes the per-2h cadence actually
# catch the daemon + calendar + skill-doc boops that are NOT byte-identical.
SPRINT_DEDUP_WINDOW_SECONDS = 7200


def parse_iso_loose(ts):
    """Lenient ISO-8601 parse for the haiku archive's compact `2026-06-17T13:50Z` shape (no seconds)
    AND full ISO. Returns an aware datetime or None. Never raises."""
    if not isinstance(ts, str) or not ts:
        return None
    s = ts.strip().replace("Z", "+00:00")
    # try full fromisoformat first (handles seconds + offset)
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    # fallback: the compact YYYY-MM-DDTHH:MM (no seconds) shape -> pad seconds
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2})(\+00:00)?$", s)
    if m:
        try:
            dt = datetime.fromisoformat(m.group(1) + ":00+00:00")
            return dt
        except Exception:
            return None
    return None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

# A typed-by-a-human prompt marker. The MAIN Primary session is the only one a human
# ever types into; every workflow/VP-incarnation (and every subagent) session is launched
# programmatically and has ZERO typed user turns. This is the load-bearing discriminator.
_TYPED_MARKER = '"promptSource":"typed"'
_TYPED_MARKER_SPACED = '"promptSource": "typed"'
# A cheap message-turn marker (role line) used as the tie-break "most turns / longest-lived"
# signal. Coarse on purpose — it only ranks candidates, never gates correctness.
_ROLE_MARKERS = ('"role":"user"', '"role": "user"', '"role":"assistant"', '"role": "assistant"')


def _session_signal(path):
    """Cheap scan of one session JSONL → (typed_user_turns, message_lines).

    Reads the file line-by-line as TEXT (no JSON parse) for speed — we only need
    two counts to rank candidates: how many human-typed prompts it carries (the
    main-session signal), and how many message-turn lines it has (the size/lifetime
    tie-break). Never parses or echoes content. Robust to huge files."""
    typed = 0
    msg_lines = 0
    try:
        with open(path, "r", errors="replace") as fh:
            for line in fh:
                if not line:
                    continue
                if _TYPED_MARKER in line or _TYPED_MARKER_SPACED in line:
                    typed += 1
                # cheap message-turn proxy (one role line per turn record)
                for rm in _ROLE_MARKERS:
                    if rm in line:
                        msg_lines += 1
                        break
    except Exception:
        return (0, 0)
    return (typed, msg_lines)


def newest_session(project_dir):
    """Return the MAIN Primary session JSONL in project_dir — NOT a subagent or
    workflow/VP-incarnation session.

    ROOT-CAUSE THIS GUARDS (HUM-009, 2026-06-19): the old logic returned the
    most-recently-MODIFIED top-level *.jsonl. When a Workflow / VP incarnation runs,
    its session JSONL is written most-recently and (for incarnations launched in the
    same project dir) lands TOP-LEVEL — so mtime-newest picked a short-lived
    incarnation session (e.g. 50999942, a 'legal-lead VP incarnation', 117 lines,
    0 typed turns) instead of the live Primary session (303ecb5f, 9000+ lines,
    174 typed turns). HUM then graded the WRONG session.

    SELECTION (targeting-only — does NOT change any check/scoping logic):
      1. Candidates = TOP-LEVEL *.jsonl only (glob is non-recursive, so nested
         '<sid>/subagents/*.jsonl' incarnation/subagent files are already excluded;
         we additionally hard-exclude any path containing a 'subagents'/'workflows'
         segment for defense-in-depth if the layout ever changes).
      2. Prefer candidates that have >=1 human-typed user turn (the main session is
         the ONLY one a human types into). If ANY typed candidate exists, the pool
         is restricted to typed candidates — an incarnation can never win.
      3. Among the pool, rank by (typed_user_turns, message_turns, mtime) descending
         — i.e. the most-conducted / longest-lived / most-recent session. This is the
         'most turns / longest-lived = main session' tiebreak.
      4. Fallback: if the cheap scan yields nothing usable, fall back to mtime-newest
         (never crash, never return None when files exist)."""
    files = glob.glob(os.path.join(project_dir, "*.jsonl"))
    if not files:
        return None
    # defense-in-depth: exclude any nested incarnation/subagent path segments
    def _is_toplevel_main_candidate(fp):
        rel = os.path.relpath(fp, project_dir)
        parts = rel.replace("\\", "/").split("/")
        # top-level file has exactly one path component; reject anything nested under
        # a subagents/ or workflows/ incarnation subdir.
        if len(parts) != 1:
            return False
        if "subagents" in parts or "workflows" in parts:
            return False
        return True

    candidates = [f for f in files if _is_toplevel_main_candidate(f)] or files

    scored = []
    for fp in candidates:
        typed, msg_lines = _session_signal(fp)
        scored.append((typed, msg_lines, os.path.getmtime(fp), fp))

    if not scored:
        return max(files, key=os.path.getmtime)

    # If any candidate has typed turns, restrict the pool to those (an incarnation,
    # with 0 typed turns, can then never be selected).
    typed_pool = [s for s in scored if s[0] > 0]
    pool = typed_pool if typed_pool else scored
    # rank by (typed, msg_turns, mtime) descending → main/most-conducted/newest wins.
    pool.sort(key=lambda s: (s[0], s[1], s[2]), reverse=True)
    return pool[0][3]


def parse_iso(ts):
    if not ts:
        return None
    try:
        s = ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def load_turns(path):
    """
    Returns a list of normalized 'turn' dicts in file order. Each record line that
    carries a message (role user/assistant) becomes one turn. Non-message records
    (mode, file-history-snapshot, attachment, system, etc.) are skipped for turn
    indexing but their existence does not break parsing.

    Normalized turn fields (NO raw human text retained beyond what checks need;
    text bodies are kept ONLY in-memory transiently for regex tests and never
    emitted):
      idx            : sequential turn index (0-based) among message turns
      role           : 'user' | 'assistant'
      prompt_source  : str or None  (typed / system / queued / None)
      is_meta        : bool
      is_api_error   : bool
      model          : str or None
      ts             : datetime or None
      text           : concatenated text-block content (assistant) or str content (user) [transient]
      tool_uses      : list of {name, input(dict or str)}  (assistant)
      tool_results   : count of tool_result blocks (user)
      skill_loaded   : skill name if this is a Skill tool_use result/attr, else None
    """
    turns = []
    parse_errors = 0
    idx = 0
    session_id = None
    with open(path, "r", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                parse_errors += 1
                continue
            if session_id is None:
                session_id = o.get("sessionId")
            msg = o.get("message")
            if not isinstance(msg, dict):
                continue
            role = msg.get("role")
            if role not in ("user", "assistant"):
                continue

            text_parts = []
            tool_uses = []
            tool_results = 0
            skill_loaded = None

            cont = msg.get("content")
            if isinstance(cont, str):
                text_parts.append(cont)
            elif isinstance(cont, list):
                for b in cont:
                    if not isinstance(b, dict):
                        continue
                    bt = b.get("type")
                    if bt == "text":
                        text_parts.append(b.get("text", "") or "")
                    elif bt == "tool_use":
                        tool_uses.append({"name": b.get("name", "?"), "input": b.get("input")})
                        if b.get("name") == "Skill":
                            inp = b.get("input") or {}
                            if isinstance(inp, dict):
                                skill_loaded = inp.get("skill")
                    elif bt == "tool_result":
                        tool_results += 1
                    # thinking blocks intentionally ignored for claim detection

            # attributionSkill on the assistant record is another signal a skill ran
            if skill_loaded is None and o.get("attributionSkill"):
                skill_loaded = o.get("attributionSkill")

            turns.append({
                "idx": idx,
                "role": role,
                "prompt_source": o.get("promptSource"),
                "is_meta": bool(o.get("isMeta")),
                "is_api_error": bool(o.get("isApiErrorMessage")),
                "model": msg.get("model"),
                "ts": parse_iso(o.get("timestamp")),
                "text": "\n".join(text_parts),
                "tool_uses": tool_uses,
                "tool_results": tool_results,
                "skill_loaded": skill_loaded,
            })
            idx += 1
    return turns, parse_errors, (session_id or os.path.splitext(os.path.basename(path))[0])


def is_real_user_turn(t):
    """A real human-typed prompt (not a tool result, not a meta/system injection)."""
    if t["role"] != "user":
        return False
    if t["is_meta"]:
        return False
    if t["tool_results"] > 0:
        return False
    return t["prompt_source"] == "typed"


def script_text(tool_use):
    """Extract searchable text from a tool_use input (Workflow script / agent prompt)."""
    inp = tool_use.get("input")
    if isinstance(inp, str):
        return inp
    if isinstance(inp, dict):
        # Workflow carries the JS in 'script'; other tools may carry 'prompt'/'command'.
        parts = []
        for k in ("script", "prompt", "command", "content", "new_string"):
            v = inp.get(k)
            if isinstance(v, str):
                parts.append(v)
        return "\n".join(parts)
    return ""


# ---------------------------------------------------------------------------
# Checks. Each returns (status, hits). hit = {turn_index, brief, [candidate]}
# Briefs are mechanical + non-sensitive. No human text is ever placed in a brief.
# ---------------------------------------------------------------------------

def check_wwcw_gate(turns):
    """FLAG/CANDIDATE: two distinct DECIDE-defect shapes the gate surfaces.

    (1) DECISION-ASK-NO-WWCW: an assistant turn asks the human to decide with NO WWCW marker
        in that turn. The mind didn't even run the the steward-sim before handing the call over.

    (2) OVER-DEFERENCE (the strictly-WORSE shape the bare gate (1) MISSES): a turn that DID run a
        confident WWCW (WWCW marker PRESENT + confidence language) and then DEFERRED the call back
        to the human anyway (a defer-to-human marker). The WWCW marker's PRESENCE masks this miss
        from (1) — the mind got a green check for *mentioning* WWCW while committing the exact sin
        WWCW exists to prevent: making the human decide a matter a confident, equipped mind should
        have decided + recorded. Whether the matter was actually reversible / within the mind's
        authority is INTENT — emitted as a CANDIDATE for Stage-2 to confirm, never a hard flag here.

    Both hit-shapes are candidate=True (ask/defer/confidence detection is heuristic).

    🚨 NOTE (2026-06-20): shapes (1)+(2) were TOO NARROW — a BARE PARK ("what needs you",
    "HELD-FOR-STEWARD") has neither an ASK_DECIDE verb nor a WWCW+confidence pair, so it passed BOTH.
    The REAL gate is now the SEPARATE `check_block_no_wwcw` (id BLOCK-NO-WWCW), which is HARD-FAIL
    (not candidate) and fires on the BROAD block vocabulary with NO WWCW-run evidence. This function
    is RETAINED for its finer DECIDE-defect taxonomy (the over-deference brief the grader still uses)
    but it is the SUPERSEDED narrow layer; the boop-FAILING enforcement lives in check_block_no_wwcw."""
    hits = []
    for t in turns:
        if t["role"] != "assistant":
            continue
        if t["is_api_error"] or t["model"] == "<synthetic>":
            continue
        text = t["text"] or ""
        has_wwcw = bool(WWCW_TEXT_RE.search(text)) or \
            (t["skill_loaded"] in WWCW_SKILL_NAMES)
        # (1) decision-ask with NO WWCW marker in the turn
        if ASK_DECIDE_RE.search(text) and not has_wwcw:
            hits.append({"turn_index": t["idx"],
                         "brief": "decision-ask shape with no WWCW marker in turn",
                         "candidate": True})  # ask-detection is heuristic -> candidate
        # (2) OVER-DEFERENCE: confident WWCW present, then handed the call back to the human.
        #     Gate on the DEFER-to-human marker (not ASK_DECIDE_RE) so an inline 'DECIDE…RATE: high
        #     confidence…ACT+RECORD' walk that ACTS is NOT flagged — only a genuine hand-back is.
        if has_wwcw and CONFIDENCE_RE.search(text) and DEFER_TO_HUMAN_RE.search(text):
            hits.append({"turn_index": t["idx"],
                         "brief": "confident WWCW that DEFERRED to human instead of acting (over-deference)",
                         "candidate": True})  # reversibility/authority is intent -> Stage-2 confirms
    return ("flag" if hits else "pass"), hits


def _turn_has_wwcw_footprint(t):
    """Return a footprint tuple (simulate, resolve, marker, skill) for ONE assistant turn.
    Each element is bool. Pure per-turn regex test over the turn's text + skill_loaded. No state."""
    text = t["text"] or ""
    simulate = bool(WWCW_SIMULATE_RE.search(text))
    resolve = bool(WWCW_RESOLVE_RE.search(text))
    marker = bool(WWCW_MARKER_RE.search(text))
    skill = (t["skill_loaded"] in WWCW_SKILL_NAMES)
    return (simulate, resolve, marker, skill)


def _block_cleared_by_colocated_run(block_idx, footprints, idx_pos):
    """Is the BLOCK at turn block_idx CLEARED by a co-located REAL WWCW run?

    🚨 v3 (2026-06-20, mind-lead — closes the marker leak the v2 auditor caught). THE CLEAR-CONDITION
    is now a SINGLE conjunction that requires BOTH halves of a real run, co-located within
    ±WWCW_COLOCATION_TURNS of the block:

        a block clears IFF  (co-located SIMULATE-the steward footprint)  AND  (co-located RESOLVE footprint)

    where, within the co-location window:
      • SIMULATE = a WWCW_SIMULATE_RE match — the "given his rules → what the steward wants" derivation
        (the rubber-duck-as-the steward beat). This is the half that proves the decision was DERIVED, not
        bare-parked.
      • RESOLVE  = ANY of: a WWCW_RESOLVE_RE match (ACT+RECORD / ASK-SHOWING-WORK precise sub-fork),
        OR a structured WWCW marker (WWCW_MARKER_RE: 'WWCW-RUN:' / 'ACT+RECORD:' / 'WWCW VERDICT:'),
        OR a co-located Skill('wwcw') tool-load. A structured marker / skill-load is a RESOLUTION-SHAPED
        announcement — it satisfies the RESOLVE half, but it is NOT a free pass: it STILL needs a
        co-located SIMULATE to count as a run.

    WHY v3 changed from v2 (the auditor's v2 FAIL, verbatim): "WWCW_MARKER_RE marker fast-path clears a
    block on a BARE 'ACT+RECORD:' token alone, no simulate (adv7=pass), contradicting spec's RESOLVE-
    without-SIMULATE-must-FAIL. v1 vocab-bug in miniature (±8 turns) — narrower but a real lying-check
    path. Fix: marker must co-locate a SIMULATE." v2 returned True on saw_marker ALONE and on saw_skill
    ALONE — both are bare-RESOLVE (or bare-token) clears that skip the the steward-sim. adv2 (resolve-no-sim)
    had the same root cause: a WWCW_RESOLVE_RE match with no SIMULATE wrongly... no, v2 already required
    sim+resolve for that path — but the marker/skill fast-paths were the back doors around it. v3 removes
    the back doors: there is now exactly ONE clear-rule, the AND.

    THE DISCRIMINATOR THAT MATTERS (the steward): was the block RESOLVED by a run (= a the steward-sim derivation that
    landed in an act/record-or-derived-ask), or left hanging as 'awaiting the steward'?
      • a bare SIMULATE, no RESOLVE          → run started, left HANGING (a bare park)   → does NOT clear.
      • a bare RESOLVE / bare ACT+RECORD: marker / bare wwcw-token, no SIMULATE
                                              → action/announcement with no the steward-sim     → does NOT clear.
      • SIMULATE + (RESOLVE | marker | skill-load), co-located → a real run resolving it  → CLEARS.

    footprints: dict idx -> (simulate, resolve, marker, skill) for assistant turns.
    idx_pos: dict idx -> its position in the sorted assistant-turn index list (for window slicing).
    Returns (cleared: bool, how: str)."""
    lo = block_idx - WWCW_COLOCATION_TURNS
    hi = block_idx + WWCW_COLOCATION_TURNS
    saw_simulate = saw_resolve = saw_marker = saw_skill = False
    for j in range(lo, hi + 1):
        fp = footprints.get(j)
        if not fp:
            continue
        sim, res, mark, sk = fp
        saw_simulate = saw_simulate or sim
        saw_resolve = saw_resolve or res
        saw_marker = saw_marker or mark
        saw_skill = saw_skill or sk
    # The RESOLVE half is satisfied by an explicit RESOLVE match OR a structured marker OR a skill-load
    # (all are resolution-shaped). But the SIMULATE half is ALWAYS required — no half-signal clears alone.
    has_resolve_half = saw_resolve or saw_marker or saw_skill
    if not (saw_simulate and has_resolve_half):
        return False, ""
    # Name the strongest co-located RESOLVE shape for the `how` audit-string (marker > skill-load > prose).
    if saw_marker:
        return True, "simulate+marker"
    if saw_skill:
        return True, "simulate+skill-load"
    return True, "resolution-structure"


def check_block_no_wwcw(turns):
    """🚨 HARD-FAIL: a BLOCK present with NO CO-LOCATED REAL-WWCW-RUN footprint resolving it.

    THE REAL GATE (steward directive 2026-06-20, verbatim: "'What needs you' is a block and i see zero
    evidence that you ran the wwcw skill... If no evidence of wwcw run it's to fail your boop").

    🚨 v4 (2026-06-20, mind-lead — PRIMARY-AUTHORED-ONLY block test; the FALSE-POSITIVE cure HUM caught on
    ITSELF). A block now counts ONLY when it is PRIMARY-AUTHORED in Primary's own assistant prose as a REAL
    park, via assistant_authored_block_idxs(text). EXCLUDED: (A) injected content — task-notifications /
    SKILL-doc injections / system-reminders / command-messages (all user-role → dropped by the role filter;
    plus a defense-in-depth injected-region strip if ever echoed inside an assistant turn); the sprint-mode
    SKILL doc, injected on EVERY /sprint-mode boop, LISTS the whole block-vocab family as the gate's OWN
    DEFINITIONS — counting it made the gate ALWAYS-RED (alert-fatigue, the trust-poison the review warns of).
    (B) self-catch quotations — block-vocab QUOTED inside quotes/backticks/markdown-emphasis to discuss or
    acknowledge a prior catch (the gate-definition recital, a class-name, the "want me to remember?" loop
    name) is NOT a park. A REAL park is bare UNQUOTED closing prose ("Holding for your steer.") → still
    FLAGS. See the v4 note + the helpers (assistant_authored_block_idxs / _quoted_ranges /
    _strip_injected_regions) near BLOCK_CAPS_FLAG_RE. The CO-LOCATED-RUN clear-logic (v2/v3) is UNCHANGED;
    v4 only refines WHICH turns are counted as blocks in the first place.

    🚨 v2 REDESIGN (2026-06-20, mind-lead — fixes the auditor's v1 FAIL). v1's evidence test was a
    WINDOW-WIDE VOCABULARY scan: one match of WWCW_EVIDENCE_RE (which matched WWCW vocabulary — the ruleset
    path, 'simulate corey', a bare 'ran WWCW' token) ANYWHERE in the window cleared EVERY block in the
    window. Proven false-negative: on a 4736-turn session, 178 bare-park BLOCK turns (idx 5/26/29/70…) were
    cleared by a SINGLE 'ran WWCW' mention at turn 1506 — ~1500 turns away. v1 returned pass on every
    WWCW-touching session. VOCABULARY-PRESENCE is NOT a-RUN-RESOLVED-THIS-BLOCK.

    v2 requires a CO-LOCATED REAL-RUN FOOTPRINT for EACH block — two properties together:
      (1) CO-LOCATION: the footprint must appear WITHIN ±WWCW_COLOCATION_TURNS of the block turn, never
          anywhere-in-session. A run 1500 turns away can NOT clear a bare park at turn 5.
      (2) REAL-RUN FOOTPRINT (the RESOLUTION STRUCTURE of an actual 5-beat run, co-located):
            • the RESOLUTION-STRUCTURE path: BOTH a SIMULATE-the steward derivation (WWCW_SIMULATE_RE —
              'what would the steward want', 'given his rules → …') AND a RESOLVE (WWCW_RESOLVE_RE — an ACT+RECORD:
              actually fired/decided+recorded, OR an ASK-SHOWING-WORK: the precise derived sub-fork that
              genuinely needs the steward) co-located with the block. A SIMULATE with no RESOLVE = a run left
              HANGING (a bare park) → does NOT clear. A RESOLVE with no SIMULATE = action with no the steward-sim
              → does NOT clear.  (per _block_cleared_by_colocated_run)
            • the STRUCTURED-MARKER fast-path: a co-located WWCW-RUN:/ACT+RECORD:/WWCW VERDICT: marker
              clears alone (a run that self-announced). BONUS — not relied on (retroactive runs lack it).
            • a co-located Skill('wwcw') tool-load also clears (the doctrine was literally invoked here).
      The discriminator that MATTERS (the steward): was the block RESOLVED by a run, or left hanging as
      'awaiting the steward'? A bare park = block-phrase with NO co-located resolution → FAIL. A real run =
      block/decision WITH co-located simulate+resolve (or marker / skill-load) → PASS.

    A block is the broad park-family (BLOCK_RE, IGNORECASE) OR a bare ALL-CAPS status-flag
    (BLOCK_CAPS_FLAG_RE, case-sensitive). The check FLAGS if ANY block is left UNCLEARED by a co-located
    real run; the hit names the first uncleared block + counts.

    HARD (not candidate): each hit carries candidate=False. In the hard-fail set + CHECK_ORDER (NOT in
    CANDIDATE_CHECKS) so a genuine flag breaks summary.clean → the boop FAILS, exactly as directed.

    🛡️ FALSE-FAIL GUARD (load-bearing): a block that DOES have a co-located real WWCW run is CLEARED
    (not a false-fail — we never fail a mind that ran WWCW right there). A session with no block at all =
    pass. Pure status / reports / notifications do NOT match BLOCK_RE (anchored to park/hold/present/ask-
    for-the steward shapes, never a bare question mark), so a status update is never a false block. The fail
    fires ONLY on a park the mind made the human carry WITHOUT a co-located WWCW run resolving it.

    Returns ("flag", hits) naming the first UNCLEARED block, with co-location-window metadata, or ("pass", [])."""
    # Build per-turn WWCW footprints over the (scoped) assistant turns, keyed by turn idx. We index by the
    # turn's own idx (contiguous message-turn ordinal) so the co-location window is a simple idx-range.
    footprints = {}
    block_idxs = []
    for t in turns:
        if t["role"] != "assistant":
            continue
        if t["is_api_error"] or t["model"] == "<synthetic>":
            continue
        footprints[t["idx"]] = _turn_has_wwcw_footprint(t)
        text = t["text"] or ""
        # v4 (2026-06-20): PRIMARY-AUTHORED-ONLY block test. The role!="assistant" guard above is the
        # (A) injected-content exclusion's first layer (task-notifications / SKILL-doc injections /
        # system-reminders / command-messages are ALL user-role); assistant_authored_block_idxs adds the
        # injected-region strip (defense-in-depth) + the (B) self-catch-quotation exclusion. Replaces the
        # bare `BLOCK_RE.search OR BLOCK_CAPS_FLAG_RE.search` which counted block-vocab that was injected
        # (the sprint-mode SKILL doc lists the whole family) or QUOTED to discuss a prior catch — the
        # always-red false-positive HUM caught on itself. A REAL authored park still flags.
        if assistant_authored_block_idxs(text):
            block_idxs.append(t["idx"])

    idx_pos = None  # window is idx-range based; no positional list needed (kept for signature stability)
    uncleared = []
    cleared = []
    for bidx in block_idxs:
        ok, how = _block_cleared_by_colocated_run(bidx, footprints, idx_pos)
        if ok:
            cleared.append((bidx, how))
        else:
            uncleared.append(bidx)

    if uncleared:
        hits = [{
            "turn_index": uncleared[0],
            "brief": ("BLOCK (park/hold/present-for-the steward) with NO co-located WWCW-RUN footprint "
                      "(simulate+resolve / marker / skill-load within ±%d turns) — boop FAILED per "
                      "the steward 2026-06-20 (a block without a co-located WWCW run fails the boop)"
                      % WWCW_COLOCATION_TURNS),
            "uncleared_block_turns": uncleared[:50],
            "uncleared_block_count": len(uncleared),
            "cleared_block_count": len(cleared),
            "block_count": len(block_idxs),
            "colocation_turns": WWCW_COLOCATION_TURNS,
            # back-compat field: v1 callers / the grader read window_has_wwcw_evidence. In v2 it means
            # "was the FIRST uncleared block cleared?" — always False here (this is the uncleared list).
            "window_has_wwcw_evidence": False,
            "candidate": False,  # HARD — breaks clean and FAILS the boop
        }]
        return "flag", hits
    # No block at all, OR every block had a co-located real WWCW run resolving it.
    return "pass", []


def check_model_pin(turns):
    """FLAG: a Workflow/agent-spawn script ASSIGNS a forbidden model.

    Only scans EXECUTABLE orchestration inputs (Workflow scripts, agent-spawn prompts) — NOT
    arbitrary Edit/Write of docs/scratchpads/skills, because those legitimately NAME forbidden
    models in prose (the ban doc, a skill list). Each pattern is anchored to a `model:`/`model=`
    assignment, so prose mentions do not fire. An assignment to an ALLOWED model
    (claude-opus-4-8 / MiniMax-M3) on the same line does not flag."""
    hits = []
    for t in turns:
        if t["role"] != "assistant":
            continue
        for tu in t["tool_uses"]:
            # ONLY orchestration tools that actually pin a model at runtime.
            if tu["name"] not in ("Workflow", "Task", "TaskCreate"):
                continue
            stext = script_text(tu)
            if not stext:
                continue
            for rx, label in MODEL_FORBIDDEN_PATTERNS:
                m = rx.search(stext)
                if not m:
                    continue
                # suppress if the matched span actually names an allowed model (e.g. claude-opus-4-8)
                span = stext[m.start():m.end() + 12]
                if MODEL_ALLOWED_RE.search(span):
                    continue
                hits.append({"turn_index": t["idx"],
                             "brief": f"{tu['name']} script: forbidden model assignment [{label}]"})
    return ("flag" if hits else "pass"), hits


def check_memory_emit(turns):
    """FLAG: a script forks agents but has no canon_append (memory-emit) anywhere in it."""
    hits = []
    for t in turns:
        if t["role"] != "assistant":
            continue
        for tu in t["tool_uses"]:
            if tu["name"] != "Workflow":
                continue
            stext = script_text(tu)
            if not stext:
                continue
            if SCRIPT_HAS_AGENT_RE.search(stext) and not CANON_APPEND_RE.search(stext):
                hits.append({"turn_index": t["idx"],
                             "brief": "Workflow forks agent(s) but no canon_append in script"})
    return ("flag" if hits else "pass"), hits


def check_claim_backing(turns):
    """CANDIDATE: a PASS/verified claim with no prior tool use (Bash/Read/Workflow) in the run.

    Heuristic + advisory only. 'Prior' = any tool_use by the assistant earlier in the
    transcript. This cannot prove intent; it only surfaces claim-without-any-walk for
    Stage-2 to read."""
    hits = []
    any_tool_before = False
    for t in turns:
        if t["role"] == "assistant":
            if CLAIM_PASS_RE.search(t["text"] or "") and not any_tool_before:
                hits.append({"turn_index": t["idx"],
                             "brief": "PASS/verified-style claim with no prior tool use in session",
                             "candidate": True})
            if t["tool_uses"]:
                any_tool_before = True
    return ("flag" if hits else "pass"), hits


def check_done_done(turns):
    """CANDIDATE: a completion claim with no LATER tool use that re-walks an artifact.

    Heuristic + advisory. 'Re-walk after' = any assistant tool_use occurring in a turn
    after the claim. Cannot confirm the later tool actually re-verified the SAME artifact
    — that is Stage-2's job. Emitted candidate-only."""
    hits = []
    n = len(turns)
    # precompute index of last assistant tool_use turn
    tool_turn_idxs = [t["idx"] for t in turns if t["role"] == "assistant" and t["tool_uses"]]
    last_tool_idx = max(tool_turn_idxs) if tool_turn_idxs else -1
    for t in turns:
        if t["role"] != "assistant":
            continue
        if COMPLETE_CLAIM_RE.search(t["text"] or ""):
            if t["idx"] >= last_tool_idx:
                hits.append({"turn_index": t["idx"],
                             "brief": "completion claim with no later tool re-walk in session",
                             "candidate": True})
    return ("flag" if hits else "pass"), hits


def check_synthetic_error(turns):
    """Mark API-error / synthetic turns as NON-EVIDENCE (informational flag)."""
    hits = []
    for t in turns:
        if t["role"] != "assistant":
            continue
        if t["is_api_error"] or t["model"] == "<synthetic>" or API_ERROR_RE.search(t["text"] or ""):
            hits.append({"turn_index": t["idx"],
                         "brief": "API-error/synthetic turn — mark non-evidence for other checks"})
    # This check 'passes' in the sense of always running; hits are informational.
    return ("flag" if hits else "pass"), hits


def check_skill_floor(turns):
    """CANDIDATE/advisory: a sprint/grounding prompt with no later Skill-load of any floor skill.

    Advisory only — floor skills can load via mechanisms this deterministic pass cannot
    see (auto-load hooks, settings.json). Emitted candidate-only to avoid false-hard-fails."""
    hits = []
    n = len(turns)
    for i, t in enumerate(turns):
        # detect a sprint/grounding START in a real prompt OR an assistant invoking it
        is_sprint_prompt = (
            (t["role"] == "user" and SPRINT_PROMPT_RE.search(t["text"] or ""))
        )
        if not is_sprint_prompt:
            continue
        # look forward for any floor skill load
        loaded = False
        for u in turns[i:]:
            if u["role"] == "assistant" and u["skill_loaded"] in FLOOR_SKILLS:
                loaded = True
                break
            # also: a Skill tool_use whose name is a floor skill
            for tu in (u["tool_uses"] if u["role"] == "assistant" else []):
                if tu["name"] == "Skill":
                    inp = tu.get("input") or {}
                    if isinstance(inp, dict) and inp.get("skill") in FLOOR_SKILLS:
                        loaded = True
                        break
            if loaded:
                break
        if not loaded:
            hits.append({"turn_index": t["idx"],
                         "brief": "sprint/grounding prompt, no floor-skill load detected after",
                         "candidate": True})
    return ("flag" if hits else "pass"), hits


def check_delegation_shape(turns):
    """CANDIDATE (Stage-2): Primary mutating via Edit/Write/Bash OUTSIDE a Workflow.

    Counts assistant mutating-tool uses NOT wrapped in a Workflow. This is heuristic:
    a single session cannot reliably know whether the actor is 'Primary' vs a delegated
    specialist whose transcript was merged. Emitted candidate-only, with a count, for
    Stage-2 to weigh against the allowlist. Never a hard verdict here."""
    hits = []
    mutate_count = 0
    for t in turns:
        if t["role"] != "assistant":
            continue
        names = {tu["name"] for tu in t["tool_uses"]}
        for tu in t["tool_uses"]:
            if tu["name"] in PRIMARY_MUTATING_TOOLS:
                mutate_count += 1
                hits.append({"turn_index": t["idx"],
                             "brief": f"direct {tu['name']} (mutating tool outside Workflow)",
                             "candidate": True})
    # We do not threshold here; Stage-2 owns the 'excess' judgment.
    return ("flag" if hits else "pass"), hits


def check_skill_candidate(turns):
    """CANDIDATE (Stage-2): a reusable capability MIGHT be hiding un-wired.

    Two deterministic signals, both candidate-only (heuristic, never a hard verdict):

      (a) REMEMBER_MARKER — a REAL user turn (is_real_user_turn) carries a save/reuse/remember
          shape. This is the human-asked-workflow / human-signaled-ability signal that
          auto-consolidate Step 4a/4b chases. The single highest-value un-wired-capability source.

      (b) CMD-SEQUENCE-REPEAT — the SAME Bash command-shape (leading verb/binary) appears >=2x
          across the session with NO Skill load occurring between the repeats. A step-sequence a
          mind keeps re-doing by hand = a candidate for being a wired skill (doctrine_skill_is_the
          _substrate). Coarse verb-level shape on purpose: it flags repetition of a KIND of step.

    Briefs are mechanical (marker class / command-shape + turn_index) and PII-safe — never the
    human text, never the full command. Stage-2 reads these, runs TRI-SOURCE dedup, and routes a
    genuine reusable capability to skill-forge."""
    hits = []
    # (a) remember/save/reuse markers in REAL human turns
    for t in turns:
        if not is_real_user_turn(t):
            continue
        if REMEMBER_MARKER_RE.search(t["text"] or ""):
            hits.append({"turn_index": t["idx"],
                         "brief": "human REMEMBER/SAVE/REUSE marker in real user turn (4a/4b skill-candidate)",
                         "candidate": True})
    # (b) repeated hand-run command-shape with no Skill load between repeats
    shape_seen = {}          # shape -> first turn_index it appeared
    skill_since = set()      # shapes that have had a Skill load since last seen (reset eligibility)
    for t in turns:
        if t["role"] != "assistant":
            continue
        # a Skill load anywhere clears the "no skill between" condition for all pending shapes
        loaded_a_skill = (t.get("skill_loaded") is not None) or \
            any(tu["name"] == "Skill" for tu in t["tool_uses"])
        if loaded_a_skill:
            skill_since = set(shape_seen.keys())  # everything pending is now "had a skill since"
        for tu in t["tool_uses"]:
            shape = _bash_command_shape(tu)
            if not shape:
                continue
            if shape in shape_seen and shape not in skill_since:
                hits.append({"turn_index": t["idx"],
                             "brief": f"repeated hand-run command-shape '{shape}' with no Skill load between (candidate for a wired skill)",
                             "candidate": True})
                # collapse further repeats of this shape into one hit per shape to avoid flooding
                skill_since.add(shape)
            else:
                shape_seen.setdefault(shape, t["idx"])
                skill_since.discard(shape)
    return ("flag" if hits else "pass"), hits


def check_project_folder_touch(turns):
    """CANDIDATE (Stage-2 / HUM): a cycle TOUCHED a project folder (projects/<x>/...) via an
    Edit/Write but did NOT update that project's DEVLOG/CHANGELOG in the SAME cycle.

    The discipline (moon-project-systems / auto-consolidate): any real contribution under
    projects/<x>/ must land in that project's devlog/changelog the same cycle — else the
    living-master rots and the next incarnation works against stale state.

    Per-project, within the scoped turn-window:
      • touched_files   = count of non-devlog Edit/Write under projects/<x>/
      • devlog_updated  = whether a devlog/changelog/progress/master-index/ADR under projects/<x>/
                          was Edit/Written this cycle.
    A project with touched_files > 0 AND devlog_updated == False is a CANDIDATE compliance defect
    (one hit per such project — the worst-case turn_index = the last non-devlog touch). Briefs are
    mechanical: project name + file BASENAME only (paths are not secrets; contents never read).
    Heuristic → candidate-only (never a hard verdict); Stage-2/HUM weighs intent + routes."""
    # per-project accumulators over the scoped window
    touched = {}        # project -> count of non-devlog touches
    last_touch_idx = {}  # project -> last turn_index of a non-devlog touch
    last_touch_base = {}  # project -> basename of last non-devlog touch (PII-safe)
    devlogged = {}      # project -> bool (devlog/changelog updated this cycle)
    for t in turns:
        if t["role"] != "assistant":
            continue
        for tu in t["tool_uses"]:
            if tu["name"] not in ("Edit", "Write"):
                continue
            inp = tu.get("input")
            fp = inp.get("file_path") if isinstance(inp, dict) else None
            proj = _project_of_path(fp)
            if not proj:
                continue
            if _is_devlog_basename(fp):
                devlogged[proj] = True
            else:
                touched[proj] = touched.get(proj, 0) + 1
                last_touch_idx[proj] = t["idx"]
                last_touch_base[proj] = os.path.basename(fp) if isinstance(fp, str) else "?"
    hits = []
    for proj, n in sorted(touched.items()):
        if not devlogged.get(proj, False):
            hits.append({"turn_index": last_touch_idx.get(proj, -1),
                         "brief": (f"project '{proj}' touched ({n} edit(s); last={last_touch_base.get(proj, '?')}) "
                                   f"but no devlog/changelog updated this cycle"),
                         "project": proj,
                         "touched_files": n,
                         "devlog_updated": False,
                         "candidate": True})
    # ALSO surface compliant projects as informational (devlog WAS updated) so Stage-2 can report
    # the full {folders_touched, devlogs_updated} picture without re-deriving it. status stays 'flag'
    # only when there is a real defect (a touched-but-undevlogged project); compliant-only = pass.
    for proj, n in sorted(touched.items()):
        if devlogged.get(proj, False):
            hits.append({"turn_index": last_touch_idx.get(proj, -1),
                         "brief": f"project '{proj}' touched ({n} edit(s)) AND devlog/changelog updated this cycle (compliant)",
                         "project": proj,
                         "touched_files": n,
                         "devlog_updated": True,
                         "candidate": True,
                         "compliant": True})
    # a project where ONLY a devlog was touched (no other edits) is fully fine — not surfaced.
    has_defect = any((not h.get("devlog_updated", False)) for h in hits)
    return ("flag" if has_defect else "pass"), hits


def check_doc_currency(turns):
    """CANDIDATE (Stage-2 / HUM): keep-worthy work landed this cycle but a DEVLOG/WORKBOARD is STALE.

    The DOC-UP-TO-DATE mandate (steward directive 2026-06-19): HUM must catch when keep-worthy work
    happened but the devlogs/WORKBOARD were NOT updated — the documentation-staleness that lets a day
    evaporate (today the human had to catch it). The existing PROJECT-FOLDER-TOUCH check is too NARROW
    (projects/<x>/ only); THIS check covers the BROADER civ-level surfaces: the WORKBOARD + the named
    program-home devlogs (self-knowledge / m3-combo).

    RECEIPT, NOT CLAIM (the steward today: verify ACTUAL RECEIPT — the behavior happened on disk):
      • keep-worthy SIGNALS detected in the scoped turns, with the LATEST signal's epoch timestamp:
          (1) canon_append Bash invocation  (a substrate-delta committed)
          (2) a Write of a NEW report under data/reports/*.md  (a keep-worthy artifact)
          (3) a finish-list / mission / vision / ratified DECISION marker in an assistant turn
          (4) 🆕 a substantive BUILD edit (Edit/Write to a SKILL.md / team-lead manifest.md /
              tools/*.py / workflows/*.js) — a build arc IS keep-worthy work; its ABSENCE from the
              signal set was the EXACT cause of tonight's surfaces_checked:0 (WORKBOARD went stale
              after a build, the check went vacuous, never compared). Conservative: substrate-shaped
              paths only; .bak + the doc-currency surfaces themselves excluded (never self-trigger).
      • for EACH doc-currency surface, the on-disk MTIME is read (os.path.getmtime — contents NEVER read).
      • a surface is STALE iff: keep-worthy work happened (>=1 signal) AND the surface's mtime is OLDER
        than the LATEST keep-worthy turn's timestamp (the doc was not touched after the work landed) OR
        the surface is MISSING. Each stale surface = ONE candidate hit (the receipt = the actual
        mtime-delta in seconds, on disk — not a self-report that 'I updated the docs').
      • a surface that IS current (mtime >= latest keep-worthy ts) is surfaced as an informational
        compliant hit so the HUM doc-currency phase can report the full {surfaces, stale, current}
        picture without re-deriving it.

    ADDITIVE + candidate-only — NEVER hard-fails HUM / blocks a session (same discipline as the other
    Stage-2-candidate checks). If NO keep-worthy work happened this cycle, there is nothing to keep
    current → pass with no hits (vacuously compliant). PII-safe: surface label + mtime-delta-seconds +
    keep-worthy counts only — never file content, never the human text, never a canon item body."""
    # --- detect keep-worthy signals + the latest signal timestamp (epoch) over the scoped turns ---
    kw_canon = 0          # canon_append Bash invocations
    kw_reports = 0        # new data/reports/*.md Writes
    kw_decisions = 0      # finish-list / mission / vision / ratified decision markers
    kw_builds = 0         # 🆕 substantive BUILD edits (SKILL.md / manifest.md / tools/*.py / workflows/*.js)
    latest_kw_epoch = [None]  # the most-recent keep-worthy turn's epoch ("work landed by" time)

    def _bump_latest(ep):
        if ep is None:
            return
        if latest_kw_epoch[0] is None or ep > latest_kw_epoch[0]:
            latest_kw_epoch[0] = ep

    for t in turns:
        if t["role"] != "assistant":
            continue
        ep = _turn_epoch(t)
        # (3) decision markers live in assistant prose
        if DECISION_MARKER_RE.search(t.get("text") or ""):
            kw_decisions += 1
            _bump_latest(ep)
        for tu in t["tool_uses"]:
            name = tu.get("name")
            inp = tu.get("input")
            # (1) canon_append via Bash
            if name == "Bash":
                cmd = inp.get("command") if isinstance(inp, dict) else (inp if isinstance(inp, str) else None)
                if isinstance(cmd, str) and CANON_APPEND_CMD_RE.search(cmd):
                    kw_canon += 1
                    _bump_latest(ep)
            # (2) a NEW report Write under data/reports/*.md  AND/OR
            # (4) a substantive BUILD edit (Write to a substrate-shaped path)
            elif name == "Write":
                fp = inp.get("file_path") if isinstance(inp, dict) else None
                if isinstance(fp, str):
                    rel = fp
                    for root in (DOC_CURRENCY_ROOT + "/",):
                        if rel.startswith(root):
                            rel = rel[len(root):]
                    if REPORT_PATH_RE.search(rel):
                        kw_reports += 1
                        _bump_latest(ep)
                    elif BUILD_EDIT_PATH_RE.search(rel) and not BUILD_EDIT_EXCLUDE_RE.search(rel):
                        kw_builds += 1
                        _bump_latest(ep)
            # (4) a substantive BUILD edit via Edit (the common build-arc shape — Edit a SKILL.md /
            # manifest.md / tools/*.py / workflows/*.js). This is the signal whose absence caused
            # surfaces_checked:0 tonight (a build arc that Edits substrate but never canon_appends).
            elif name == "Edit":
                fp = inp.get("file_path") if isinstance(inp, dict) else None
                if isinstance(fp, str):
                    rel = fp
                    for root in (DOC_CURRENCY_ROOT + "/",):
                        if rel.startswith(root):
                            rel = rel[len(root):]
                    if BUILD_EDIT_PATH_RE.search(rel) and not BUILD_EDIT_EXCLUDE_RE.search(rel):
                        kw_builds += 1
                        _bump_latest(ep)

    keepworthy_total = kw_canon + kw_reports + kw_decisions + kw_builds
    latest = latest_kw_epoch[0]
    hits = []

    # No keep-worthy work this cycle → nothing to keep current. Vacuously compliant (pass, no hits).
    if keepworthy_total == 0 or latest is None:
        return "pass", hits

    # --- for each surface, read its mtime ON DISK and compare to the latest keep-worthy turn ---
    kw_brief = (f"keep-worthy: {kw_canon} canon_append + {kw_reports} report(s) + "
                f"{kw_decisions} decision-marker(s) + {kw_builds} build-edit(s)")
    any_stale = False
    for label, rel in DOC_CURRENCY_SURFACES:
        mtime = _surface_mtime(rel)
        if mtime is None:
            # missing surface = stale by definition (the doc that should record this work is absent)
            hits.append({"turn_index": -1,
                         "brief": f"DOC-CURRENCY: '{label}' surface MISSING while {kw_brief} landed this cycle",
                         "surface": label,
                         "stale": True,
                         "mtime_delta_s": None,
                         "candidate": True})
            any_stale = True
            continue
        delta = int(mtime - latest)  # >=0: updated AT/AFTER the work; <0: updated BEFORE it (by |delta|s)
        # STALE only if the doc predates the latest keep-worthy work by MORE than the grace window
        # (i.e. it was NOT meaningfully updated alongside this cycle's work). A doc updated within the
        # grace window of the work = touched THIS cycle = CURRENT (absorbs the work-then-doc cadence).
        if delta < -DOC_CURRENCY_GRACE_WINDOW_S:
            hits.append({"turn_index": -1,
                         "brief": (f"DOC-CURRENCY: '{label}' STALE — last updated {abs(delta)}s "
                                   f"(> {DOC_CURRENCY_GRACE_WINDOW_S}s grace) BEFORE the latest keep-worthy "
                                   f"work ({kw_brief})"),
                         "surface": label,
                         "stale": True,
                         "mtime_delta_s": delta,
                         "candidate": True})
            any_stale = True
        else:
            hits.append({"turn_index": -1,
                         "brief": (f"DOC-CURRENCY: '{label}' CURRENT — mtime within {DOC_CURRENCY_GRACE_WINDOW_S}s "
                                   f"grace of the latest keep-worthy work (delta={delta}s; compliant)"),
                         "surface": label,
                         "stale": False,
                         "mtime_delta_s": delta,
                         "candidate": True,
                         "compliant": True})
    # flag only when there is a real defect (>=1 stale surface while keep-worthy work landed)
    return ("flag" if any_stale else "pass"), hits


def _session_time_window(turns):
    """Return (first_ts, last_ts) as aware datetimes over all turns that carry a timestamp.
    Used to window the off-session haiku archive to THIS session. Either may be None if no turn
    carried a parseable ts."""
    tss = [t["ts"] for t in turns if t.get("ts") is not None]
    if not tss:
        return (None, None)
    return (min(tss), max(tss))


def check_sprint_mode_read(turns, full_turns=None):
    """CANDIDATE (Stage-2 / HUM): a SPRINT/GROUNDING pass was invoked this session but the
    sprint-mode load-verify FLOOR block (the `skill_loaded:` lines) was never ACTUALLY written.

    🚨 WHOLE-SESSION CHECK (not delta-scoped): grounding/sprint floor-reads happen at session START
    (turn ~0-50). Delta-scoping (--since-turn) would exclude those early turns and make every later
    fire falsely flag 'no floor read this cycle'. So this check ALWAYS runs against full_turns (the
    complete session) when provided, NOT the scoped window. This mirrors the HUM judge's invariant:
    detection of NEW work is delta-scoped; verification of a whole-session property is full-session.

    This is the ACTUAL-RECEIPT of the sprint-mode floor read — steward directive 2026-06-19: today
    the floor read is CLAIMED, not verified, so a shallow/skipped grounding slips past. The receipt
    is the load-verify block landing in-session (assistant text OR a scratchpad Write/Edit). We do
    NOT trust a self-report 'I read the floor' — we look for the ARTIFACT the floor read leaves.

    DETECTION:
      • invoked = a real user turn OR an assistant turn carries a /sprint-mode | grounding marker.
      • received = ANY turn (assistant text OR a Write/Edit tool input — esp. one targeting a
        scratchpad) contains >=2 distinct load-verify key lines (skill_loaded: / wwcw_loaded: /
        hum_loaded: / verification_floor_resident: / hum_last_step_fired: / self_knowledge_loaded:).
    A pass that was invoked-but-not-received = a CANDIDATE floor-read miss (the comprehension floor
    was claimed but its artifact never landed). PII-safe: counts + marker class only, never the text.
    CANDIDATE-only (heuristic — the block may land via a mechanism the deterministic pass cannot see,
    e.g. a hook that writes the scratchpad out-of-band; Stage-2/HUM weighs intent + walks the turn)."""
    scan = full_turns if full_turns is not None else turns
    # was a sprint/grounding pass invoked at all this session?
    invoked_idx = None
    for t in scan:
        txt = t["text"] or ""
        # a real human typed it, OR an assistant echoed/invoked the marker (the cron injects /sprint-mode)
        if SPRINT_OR_GROUNDING_PROMPT_RE.search(txt):
            invoked_idx = t["idx"]
            break
    if invoked_idx is None:
        # no sprint/grounding invoked -> nothing to receipt. Pass (na-like, but pass keeps it simple).
        return "pass", []

    # was the load-verify floor block ACTUALLY written? scan assistant text + Write/Edit inputs.
    received = False
    received_idx = None
    received_where = None
    for t in scan:
        # (a) assistant prose carrying the block
        if t["role"] == "assistant":
            keys = len(set(m.group(1).lower() for m in LOAD_VERIFY_KEY_RE.finditer(t["text"] or "")))
            if keys >= 2 or SKILL_LOADED_LINE_RE.search(t["text"] or ""):
                # require at least 2 distinct load-verify keys to count it a real block (one stray
                # 'skill_loaded:' mention is not the floor block); the skill_loaded-line regex alone
                # is multiline so >=1 of those + any other key is enough — recount for strength.
                if keys >= 2:
                    received = True
                    received_idx = t["idx"]
                    received_where = "assistant-text"
                    break
        # (b) a Write/Edit landing the block into a file (scratchpad is canonical, but count any)
        for tu in (t["tool_uses"] if t["role"] == "assistant" else []):
            if tu["name"] not in ("Write", "Edit"):
                continue
            stext = script_text(tu)  # pulls content / new_string
            if not stext:
                continue
            keys = len(set(m.group(1).lower() for m in LOAD_VERIFY_KEY_RE.finditer(stext)))
            if keys >= 2:
                received = True
                received_idx = t["idx"]
                inp = tu.get("input")
                fp = inp.get("file_path") if isinstance(inp, dict) else None
                received_where = "scratchpad-write" if (fp and SCRATCHPAD_PATH_RE.search(fp)) else "file-write"
                break
        if received:
            break

    if received:
        # informational compliant hit (the receipt landed) so Stage-2 can report the full picture.
        return "pass", [{"turn_index": received_idx,
                         "brief": f"sprint/grounding invoked (turn {invoked_idx}) AND load-verify floor block received ({received_where})",
                         "received": True,
                         "candidate": True,
                         "compliant": True}]
    # invoked but NOT received -> the floor read was claimed but its artifact never landed.
    return "flag", [{"turn_index": invoked_idx,
                     "brief": "sprint/grounding pass invoked but NO load-verify floor block (>=2 skill_loaded/-loaded lines) written this session — floor read claimed, not received",
                     "received": False,
                     "candidate": True}]


def check_haiku_per_doc(turns, full_turns=None):
    """CANDIDATE (Stage-2 / HUM): a GROUNDING / slow-sprint pass was invoked this session but the
    haiku-per-doc comprehension gate left NO fresh entries in data/haiku-archive/haikus.jsonl
    within this session's time window.

    🚨 WHOLE-SESSION CHECK (not delta-scoped): like SPRINT-MODE-READ, the grounding invocation +
    the session time-window are whole-session properties. Always runs against full_turns when
    provided (grounding happens at session start; the time-window must span the FULL session so the
    off-session haiku archive is windowed correctly). Delta-scoping detects NEW work; this verifies a
    whole-session comprehension-gate receipt.

    This is the ACTUAL-RECEIPT of the grounding-docs haiku gate — steward directive 2026-06-19: the
    gate is PROVEN by the artifact it leaves (the haiku-archive entries), exactly like canon_recall's
    hit-ledger proves recall. We read the OFF-SESSION archive and count {ts, doc, haiku} rows whose
    `ts` falls inside [session_first_ts, session_last_ts]. If a grounding/slow-sprint was invoked but
    ZERO fresh in-window haikus landed -> flag (the comprehension gate was claimed but not received).
    We ALSO surface the in-window count + distinct doc count so Stage-2 can weigh a SHALLOW grounding
    (e.g. 2 haikus where ~6 were expected) without hard-failing it.

    PII-safe: counts + the doc NAMES from the archive (non-sensitive labels) only; never the haiku
    body, never the human text. CANDIDATE-only (heuristic — a long manned session may ground once and
    work for hours; clock skew between the session ts and the archive ts is tolerated by the window)."""
    scan = full_turns if full_turns is not None else turns
    # was a GROUNDING / slow-sprint pass (the haiku gate) invoked? (lean /sprint-mode does NOT haiku.)
    invoked_idx = None
    for t in scan:
        if GROUNDING_PROMPT_RE.search(t["text"] or ""):
            invoked_idx = t["idx"]
            break
    if invoked_idx is None:
        # no grounding/slow-sprint invoked -> the haiku gate does not apply this session. Pass.
        return "pass", [{"turn_index": -1,
                         "brief": "no grounding/slow-sprint invoked this session — haiku gate N/A",
                         "applicable": False,
                         "candidate": True}]

    first_ts, last_ts = _session_time_window(scan)
    # tolerance: pad the window 10 min each side for clock skew between the session record + archive.
    pad = None
    try:
        from datetime import timedelta
        pad = timedelta(minutes=10)
    except Exception:
        pad = None
    lo = (first_ts - pad) if (first_ts is not None and pad is not None) else first_ts
    hi = (last_ts + pad) if (last_ts is not None and pad is not None) else last_ts

    archive_path = os.path.join(os.environ.get("CIV_ROOT", os.environ.get("AICIV_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), HAIKU_ARCHIVE_PATH)
    fresh = 0
    fresh_docs = set()
    archive_read_ok = True
    if not os.path.isfile(archive_path):
        archive_read_ok = False
    else:
        try:
            with open(archive_path, "r", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        o = json.loads(line)
                    except Exception:
                        continue
                    ets = parse_iso_loose(o.get("ts"))
                    if ets is None:
                        continue
                    # in-window? (if we have no session window at all, count nothing — can't verify)
                    if lo is not None and ets < lo:
                        continue
                    if hi is not None and ets > hi:
                        continue
                    if lo is None and hi is None:
                        continue  # no session window -> cannot attribute any haiku to THIS session
                    fresh += 1
                    d = o.get("doc")
                    if isinstance(d, str) and d:
                        fresh_docs.add(d[:60])  # doc label only, capped (non-sensitive)
        except Exception:
            archive_read_ok = False

    if not archive_read_ok:
        # fail-soft: cannot read the archive -> candidate-only NA note, never a hard fail.
        return "pass", [{"turn_index": invoked_idx,
                         "brief": f"grounding invoked (turn {invoked_idx}) but haiku archive unreadable/missing ({HAIKU_ARCHIVE_PATH}) — cannot verify haiku receipt",
                         "fresh_haikus": -1,
                         "candidate": True}]

    if first_ts is None and last_ts is None:
        # no session window -> cannot window the archive. Candidate NA, not a flag.
        return "pass", [{"turn_index": invoked_idx,
                         "brief": "grounding invoked but session has no parseable timestamps — cannot window haiku archive",
                         "fresh_haikus": -1,
                         "candidate": True}]

    if fresh == 0:
        # invoked but ZERO fresh in-window haikus -> the comprehension gate was claimed, not received.
        return "flag", [{"turn_index": invoked_idx,
                         "brief": (f"grounding/slow-sprint invoked (turn {invoked_idx}) but ZERO fresh "
                                   f"haiku-archive entries in this session's window — comprehension gate "
                                   f"claimed, not received (expected ~{HAIKU_DOCSET_EXPECTED} {{ts,doc,haiku}} rows)"),
                         "fresh_haikus": 0,
                         "distinct_docs": 0,
                         "candidate": True}]

    # fresh haikus DID land. Surface the count + distinct-doc count (a SHALLOW grounding — fewer than
    # the docset — is a Stage-2 weigh, not a hard flag here). Informational compliant-ish hit.
    shallow = (len(fresh_docs) < HAIKU_DOCSET_EXPECTED)
    return ("pass"), [{"turn_index": invoked_idx,
                       "brief": (f"grounding invoked (turn {invoked_idx}); {fresh} fresh haiku-archive "
                                 f"entr{'y' if fresh == 1 else 'ies'} in-window across {len(fresh_docs)} distinct doc(s)"
                                 + (f" — SHALLOW (< expected ~{HAIKU_DOCSET_EXPECTED})" if shallow else " — receipt landed")),
                       "fresh_haikus": fresh,
                       "distinct_docs": len(fresh_docs),
                       "shallow": shallow,
                       "candidate": True,
                       "compliant": not shallow}]


def _count_fresh_haiku_docs(scan, window=None, no_backward_pad=False):
    """Return (distinct_fresh_haiku_docs:int, archive_verifiable:bool) for a turn-set's time window.
    distinct count = the number of DISTINCT doc labels with a fresh in-window haiku entry. Mirrors
    check_haiku_per_doc's windowing exactly (10-min pad, parse_iso_loose). archive_verifiable=False
    means the archive was unreadable / no window (could-not-verify — never penalize).

    PER-CYCLE WINDOW (2026-06-20, mind-lead): `window=(first_ts,last_ts)` lets the caller pass an
    EXPLICIT time-range — e.g. the PER-INVOCATION boop window (this /sprint-mode injection → the next
    boop / session end) instead of the whole-session min/max. When window is None (default / the
    full-session back-compat path) the time-range is derived from `scan` exactly as before — so the
    firewall whole-session call is byte-identical. This is the fix for the WHOLE-SESSION-scoped
    completeness bug: a lean boop riding EARLIER cycles' haikus must not count them as THIS boop's.

    `no_backward_pad=True` (2026-06-20, per-cycle false-fire cure): drop the 10-min BACKWARD pad on
    the lower bound so the window cannot reach back across the since_turn boundary into a PRIOR
    cluster's haiku-writes. The upper bound keeps the +10min clock-skew pad (a haiku written slightly
    after the last turn is still THIS boop's). Used only on the per-cycle scoped call; the full-session
    back-compat call leaves no_backward_pad=False so it is byte-identical."""
    if window is not None:
        first_ts, last_ts = window
    else:
        first_ts, last_ts = _session_time_window(scan)
    pad = None
    try:
        from datetime import timedelta
        pad = timedelta(minutes=10)
    except Exception:
        pad = None
    # lower bound: pad backward by default; when no_backward_pad the floor is the exact first_ts so the
    # window never reaches back past the since_turn boundary into a prior cluster's haiku-writes.
    if no_backward_pad:
        lo = first_ts
    else:
        lo = (first_ts - pad) if (first_ts is not None and pad is not None) else first_ts
    hi = (last_ts + pad) if (last_ts is not None and pad is not None) else last_ts
    if first_ts is None and last_ts is None:
        return 0, False  # no session window -> cannot attribute any haiku -> not verifiable
    archive_path = os.path.join(os.environ.get("CIV_ROOT", os.environ.get("AICIV_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), HAIKU_ARCHIVE_PATH)
    if not os.path.isfile(archive_path):
        return 0, False
    fresh_docs = set()
    try:
        with open(archive_path, "r", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                ets = parse_iso_loose(o.get("ts"))
                if ets is None:
                    continue
                if lo is not None and ets < lo:
                    continue
                if hi is not None and ets > hi:
                    continue
                d = o.get("doc")
                if isinstance(d, str) and d:
                    fresh_docs.add(d[:60])
    except Exception:
        return 0, False
    return len(fresh_docs), True


# ---------------------------------------------------------------------------
# 🚨 GENUINE /sprint-mode BOOP DETECTION (the lean-cycle loophole close, 2026-06-20).
# ---------------------------------------------------------------------------
def _is_injected_or_skilldoc_turn(t):
    """True for a turn that is the INJECTED /sprint-mode SKILL-doc body (the cron injects the whole
    sprint-mode SKILL.md text on every boop) or any injected/meta region — NOT the genuine command
    boop. The literal `/sprint-mode` command-message is a small user-role turn (promptSource='typed'
    or a short command-message); the injected SKILL doc is a LONG user-role turn carrying the SKILL's
    own header / <command-message> / <command-name> / 'Base directory for this skill' markers. We do
    NOT count the injected doc itself as the boop trigger (it merely DELIVERS the skill); the boop is
    the command-message that invoked it. PII-safe: structural markers only, never echoes text."""
    txt = t.get("text") or ""
    if t.get("is_meta"):
        return True
    # the injected SKILL-doc body carries these structural markers; the bare command does not.
    if INJECTED_MARKER_RE.search(txt):
        return True
    if "Base directory for this skill" in txt:
        return True
    # a very long user turn carrying the sprint-mode SKILL header is the injected doc, not the command.
    if t.get("role") == "user" and len(txt) > 400 and re.search(r"sprint-mode\s+SKILL", txt, re.IGNORECASE):
        return True
    return False


def _genuine_sprint_mode_boops(scan):
    """Return the list of turn-idxs that are GENUINE /sprint-mode boop INVOCATIONS in this window — a
    /sprint-mode command-message OR a calendar /sprint-mode boop — EXCLUDING the injected SKILL-doc body
    and meta turns. These are the candidate cycle-triggers; dedup (below) then removes byte-identical
    re-injections within the cadence window. PII-safe: idxs only."""
    boops = []
    for t in scan:
        txt = t.get("text") or ""
        if not SPRINT_MODE_COMMAND_RE.search(txt):
            continue
        if _is_injected_or_skilldoc_turn(t):
            continue
        # assistant prose merely REFERRING to /sprint-mode ("the BOOP /sprint-mode already ran") is not
        # a fresh invocation — the invocation is a user-role command-message (the cron/the steward inject it)
        # OR a calendar-boop marker. Restrict to user-role invocation turns.
        if t.get("role") != "user":
            continue
        boops.append(t["idx"])
    return boops


def _sprint_command_norm(t):
    """A CLASS-AWARE signature of a /sprint-mode boop turn (for the per-hour cadence dedup).

    🚨 BROADENED 2026-06-20 (the steward "one an hour only" + class-aware ruling): the dedup used to compare
    BYTE-IDENTICAL normalized text — but the stacking boops are DIFFERENT strings that are all the SAME
    /sprint-mode CLASS:
        • the DAEMON fire            → "/sprint-mode"
        • the CALENDAR boop          → "[BOOP] CALENDAR BOOP: /sprint-mode"
        • the injected SKILL-DOC     → "<command-message>sprint-mode</command-message>" / "command-message sprint-mode"
    Byte-identical dedup MISSED these (different surrounding text) → each stacked into a SECOND full
    grounding/HUM in the same hour. The matcher now collapses ANY /sprint-mode-class boop to a single
    stable class token "/sprint-mode-class" so two class boops within SPRINT_DEDUP_WINDOW_SECONDS dedup
    to the same hourly cycle regardless of byte differences. (The genuine-boop gate
    _genuine_sprint_mode_boops already requires SPRINT_MODE_COMMAND_RE + user-role + non-injected-doc,
    so anything reaching this norm IS a /sprint-mode-class invocation by construction; the class token is
    the correct equivalence key.)

    PII-safe: returns a short stable class token (never echoes turn text). Falls back to the old
    whitespace-collapsed signature ONLY for a turn that somehow is NOT /sprint-mode-class (defensive;
    a non-/sprint-mode turn should never reach here)."""
    txt = (t.get("text") or "")
    if SPRINT_MODE_COMMAND_RE.search(txt):
        return "/sprint-mode-class"
    # defensive fallback (should be unreachable — callers pass genuine /sprint-mode boops only)
    return re.sub(r"\s+", " ", txt.strip().lower())[:200]


def _prior_sprint_boop_anchor(full_turns, since_turn):
    """When per-cycle scoped (since_turn>0), the prior /sprint-mode boop that THIS window's first boop
    might be a byte-identical re-injection OF may live BEFORE the scoped window (idx<=since_turn). Find
    the most-recent genuine /sprint-mode boop at idx<=since_turn so the dedup can compare across the
    since_turn boundary. Returns (norm, ts) or (None, None) when none / not scoped. PII-safe: a short
    normalized signature + a ts only."""
    if not full_turns or not since_turn or since_turn <= 0:
        return (None, None)
    prior = [t for t in full_turns if t["idx"] <= since_turn]
    anchor_idxs = _genuine_sprint_mode_boops(prior)
    if not anchor_idxs:
        return (None, None)
    by_idx = {t["idx"]: t for t in prior}
    last = by_idx.get(anchor_idxs[-1])
    if last is None:
        return (None, None)
    return (_sprint_command_norm(last), last.get("ts"))


def _dedup_clustered_reinjections(scan, boop_idxs, anchor_norm=None, anchor_ts=None):
    """Given the genuine /sprint-mode boop idxs (chronological), drop the ones that are SAME-CLASS
    re-fires within SPRINT_DEDUP_WINDOW_SECONDS of a prior /sprint-mode boop (the per-hour cadence
    cluster carve-out). Returns (kept_idxs, deduped_idxs).

    `anchor_norm`/`anchor_ts` (per-cycle scoping): the prior /sprint-mode boop that lives BEFORE the
    scoped window (idx<=since_turn) — see _prior_sprint_boop_anchor. When provided it SEEDS the cluster
    anchor so THIS window's first boop can be recognized as a same-class re-fire of a prior
    out-of-scope boop (the per-hour dedup that whole-session scope handles naturally). When None
    (whole-session) the anchor starts empty and the FIRST boop in scan is always kept (it IS the cycle).

    🎛️ THE DEDUP WINDOW IS THE CADENCE KNOB: a boop is deduped iff it (a) is the SAME /sprint-mode CLASS
    as the prior KEPT/anchor boop (matcher BROADENED 2026-06-20 from byte-identical to class-aware — see
    _sprint_command_norm; the daemon fire / calendar boop / injected skill-doc are DIFFERENT strings but
    all dedup to the same class token) AND (b) lands within SPRINT_DEDUP_WINDOW_SECONDS of that prior
    boop's timestamp. CURRENT 7200s = PER-2H cadence (steward directive 2026-06-21 "every 2 hours"): ANY
    /sprint-mode-class boop within 2 hours of a prior full grounding is the same 2-hour cycle (2nd..N →
    deduped). The FIRST boop of a new 2-hour window is ALWAYS kept (it owes the FULL contract — cadence
    widened, per-boop standard unchanged). If timestamps are missing for a pair, we do NOT dedup
    (fail-safe toward REQUIRING grounding — never silently exempt an un-timestamped boop, so a skipped
    2-hour window still fails). PII-safe: idxs only."""
    if not boop_idxs:
        return [], []
    by_idx = {t["idx"]: t for t in scan}
    kept = []
    deduped = []
    # the most-recent KEPT (or anchor) boop, for the byte-identity + ts-window comparison.
    last_kept_ts = anchor_ts
    last_kept_norm = anchor_norm
    for bi in boop_idxs:
        t = by_idx.get(bi)
        if t is None:
            kept.append(bi)
            continue
        ts = t.get("ts")
        norm = _sprint_command_norm(t)
        is_dedup = False
        if last_kept_norm is not None and norm == last_kept_norm:
            # same /sprint-mode CLASS as the prior KEPT boop. Dedup ONLY if within the cadence window.
            if ts is not None and last_kept_ts is not None:
                try:
                    delta = abs((ts - last_kept_ts).total_seconds())
                    if delta <= SPRINT_DEDUP_WINDOW_SECONDS:
                        is_dedup = True
                except Exception:
                    is_dedup = False  # ts math failed -> fail-safe toward REQUIRING grounding
            # ts missing on either side -> NOT deduped (fail-safe: a fresh cycle owes grounding).
        if is_dedup:
            deduped.append(bi)
            # a deduped re-fire does NOT advance the cluster anchor (the cluster stays anchored to the
            # first kept boop of the hour, so the 3rd..Nth class boop 50min after the 1st is still
            # in-window → still deduped within the same hourly cycle).
        else:
            kept.append(bi)
            last_kept_ts = ts
            last_kept_norm = norm
    return kept, deduped


def _has_work_act(scan, after_idx=None):
    """True if the window did ≥1 WORK-ACT — a real tool-use (the boop actually DID something, not a pure
    status reply). A genuine /sprint-mode CYCLE both invokes the boop AND does work; a bare command with
    no work that follows is an empty fire (we still require grounding on a genuine boop, but the work-act
    is part of the genuine-boop definition so a no-op echo turn alone is not treated as a cycle). Counts
    any assistant tool-use EXCEPT the bare Skill('sprint-mode') self-load (loading the skill is not work).
    PII-safe: bool only."""
    for t in scan:
        if t.get("role") != "assistant":
            continue
        if after_idx is not None and t["idx"] <= after_idx:
            continue
        for tu in t.get("tool_uses", []):
            nm = tu.get("name")
            if nm == "Skill":
                inp = tu.get("input") or {}
                sk = inp.get("skill") if isinstance(inp, dict) else None
                if sk in ("sprint-mode", "grounding-docs"):
                    continue  # loading the grounding skill itself is not a work-act
            return True
    return False


def check_grounding_completeness(turns, full_turns=None, since_turn=0):
    """🚨 HARD-FAIL: a grounding boop that did substantive grounding work but is NOT COMPLETE.

    THE COMPLETE-OR-FAIL CONTRACT (steward directive 2026-06-20, verbatim: "Hum needs to check and
    fully FAIL any boop that isn't hyper detailed and complete. Miss one doc or one haiku or one step
    it's 100% fail on that boop. The discipline is EVERYTHING.").

    Born from the afternoon /sprint-mode cycles (12:51 / 13:53 / 14:55) that wrote CHEAP receipts —
    ONE haiku each, a bare load-verify line, NO per-doc haiku, NO read-one-at-a-time, NO
    auto-consolidate sweep, HUM DEFERRED — and PASSED the narrower SPRINT-MODE-READ + HAIKU-PER-DOC
    receipts (which only confirm SOME artifact landed). This gate enforces the FULL written contract.

    STRICT (no partial credit — the steward's "miss one … it's 100% fail"): the boop is graded against the
    ENUMERATED required-element checklist. If ANY required element is absent → status=flag → HARD-FAIL
    (in GROUNDING_COMPLETENESS_HARDFAIL_CHECKS, ABSENT from CANDIDATE_CHECKS → breaks summary.clean →
    forces verdict=HOLLOW). Partial completion = full failure.

    THE REQUIRED ELEMENTS (the checklist this gate enforces — it MUST match the written standard the
    sprint-mode + grounding-docs SKILLs DECLARE):
      (1) per_doc_haikus  — ≥ GROUNDING_COMPLETE_DOCSET (11) DISTINCT fresh in-window haiku-docs (ONE
                            context-informed haiku PER doc — count haikus == count docs, NOT one-per-
                            cycle). The exact miss the afternoon boops committed. (10 → 11 on 2026-06-21
                            to match the new Doc -0.5 WWCW read→haiku doc fleet-lead added.)
      (1b) read_haiku_pairing — (NEW 2026-06-21, steward directive "Hum manifest should show it checking
                            for read commands followed by haiku") each grounding-doc Read (the doc-open)
                            is FOLLOWED by a haiku (the comprehension). 🛡️ CONSERVATIVE TRIGGER: fires
                            ONLY on a GENUINE read-one-at-a-time grounding pass — signaled by ≥docset
                            DOC-READ MARKERS (`[Doc N read]`), NOT raw Read tool-call count — so a normal
                            work/processing window (many file Reads, ZERO doc-read markers) is NOT gated.
                            When gated: fewer than docset of the doc-reads paired with a following haiku
                            → INCOMPLETE. The PAIRING is the grounding-proof, not a flat archive count
                            alone. (We track read_tool_calls + read_haiku_pairs for the report either way.)
      (2) load_verify     — the load-verify floor block landed (≥2 distinct *_loaded: keys).
      (3) synthesis       — the "I am now [what] ready to [what]" synthesis statement.
      (4) workflows_mandate — the workflows-for-everything affirmation.
      (5) wwcw_affirm     — the WWCW run-before-asking affirmation.
      (6) hum_affirm      — the HUM / human-bridge affirmation (the hum_last_step_fired promise).
      (7) auto_consolidate — the auto-consolidate sweep was run (the step the afternoon boops skipped).
      (8) hum_fired       — HUM fired as the deterministic last step (Workflow(workflows/hum.js) seen).

    🛡️ FALSE-FAIL GUARD (HONEST — the steward's explicit guard, NARROWED 2026-06-20 to close the lean-cycle
    loophole `"lean cycle" < discipline`). The contract fires on a boop with EITHER trigger:
      TRIGGER 1 — a GROUNDING_PROMPT_RE pass (real grounding / slow-sprint, haiku-bearing) AND ≥1
                  grounding-work-signature (≥1 fresh haiku-doc OR the load-verify block OR a doc-read
                  marker). A TRIGGER-1 pass with NO fresh work this window = a recognized LEAN CLUSTERED
                  RE-FIRE (prior boop grounded) → exempt.
      TRIGGER 2 — a GENUINE /sprint-mode boop (a /sprint-mode command-message / calendar boop + ≥1
                  work-act, NOT a byte-identical SPRINT_DEDUP_WINDOW_SECONDS re-injection). A genuine
                  /sprint-mode cycle OWES the FULL contract whether or not it left grounding-work
                  signatures — the lean-cycle dodge (a genuine boop that did NO grounding) now FAILS.
    The ONLY two remaining exemptions: (a) a byte-identical /sprint-mode re-injection within
    SPRINT_DEDUP_WINDOW_SECONDS (the cadence-lock cluster carve-out); (b) a non-/sprint-mode turn (no
    /sprint-mode boop in the window — a pure status reply / a the steward question is never a grounding boop,
    never failed). ARCHIVE-UNVERIFIABLE: if the haiku archive is unreadable / the session has no
    parseable timestamps, the per-doc-haiku element is treated as could-not-verify and NOT counted as a
    miss (we never fail what we could not check) — but the OTHER 8 in-session elements are still
    required (so a lean /sprint-mode that did NO load-verify/synthesis/etc still FAILS).

    🚨 PER-INVOCATION (PER-CYCLE) WINDOW (2026-06-20, mind-lead — the COMPLETE-PER-BOOP fix). the steward
    caught it: GROUNDING-COMPLETENESS was WHOLE-SESSION scoped. With the cron injecting /sprint-mode
    EVERY boop, a LEAN boop that wrote ~0 fresh haikus THIS window still PASSED completeness by riding
    EARLIER cycles' haikus (the last HUM reported per_doc_haikus=34 session-wide for a lean boop). So
    "full proven per-boop" was never actually checked. THE FIX: when since_turn>0 (the hum-cursor /
    --since-turn boundary = the start of THIS boop's window, between this /sprint-mode injection and the
    next), the completeness contract scopes to THIS boop ONLY — it counts ONLY the haikus + elements
    emitted WITHIN this boop's turn-range (idx>since_turn) and this boop's time-window (the scoped
    turns' min/max ts). A lean boop (fresh-haikus < the docset THIS window) now FAILS; a genuinely-full
    per-cycle boop (10 fresh haikus + 9 elements THIS window) PASSES. When since_turn==0 (the full-
    session firewall back-compat call), behavior is the WHOLE-SESSION original, byte-identical. The
    false-fail guard is KEPT under both scopings (a pure status / lean-no-grounding boop is exempt —
    only a boop that DID grounding work THIS window is held to per-cycle completeness). PII-safe:
    counts + element labels + marker classes only — never human text, never a haiku body, never doc
    contents.

    🚨 TURN-CONSISTENCY FIX (2026-06-20, mind-lead — HUM w11apf32v caught my OWN gate over-firing).
    THE BUG: the per-cycle window above was applied to the ELEMENT-check by TURN BOUNDARY (idx>since_turn)
    but to the did_grounding_work signal + the haiku-COUNT by TIMESTAMP — and the ts-window (scoped turns'
    min/max + a 10-min pad) REACHES BACK across a clustered re-fire and picks up a PRIOR full boop's 10
    haikus. So on a LEAN clustered re-fire (since_turn cursor lands AFTER the prior full boop) the ts-
    windowed count saw per_doc_haikus=10 → did_grounding_work=true, while the turn-windowed element-check
    correctly found the elements absent (they were before since_turn) → flag → FALSE-FIRE / forced HOLLOW
    on a legit re-fire (the dedup was logged in-window). THE CURE (system-over-symptom, keep STRICT on
    real misses, remove ONLY the leak): make did_grounding_work TURN-CONSISTENT with the element-check.
    Per-cycle, the grounding-WORK signal uses ONLY the two in-window ARTIFACTS a real read-one-at-a-time
    grounding pass leaves — the load-verify FLOOR block (saw_load_verify) and per-doc DOC-READ markers
    (docread_markers≥1) — NEVER the ts-windowed archive count and NEVER the cheap affirmation/synthesis
    PROSE (which a lean re-fire emits while PROCESSING a prior HUM verdict). Result:
      • LEAN clustered re-fire (0 in-window load-verify/doc-read THIS window) → did_grounding_work=FALSE
        → EXEMPT (lean-boop exemption now applies correctly). The logged clustered-re-fire dedup marker
        (GROUNDING_REFIRE_DEDUP_RE) is honored as a corroborating re-fire signal in the exempt brief.
      • STANDALONE FULL boop → its load-verify + doc-reads + 10 haikus are IN its turn-window →
        did_grounding_work=TRUE → graded full (still PASSES).
      • STANDALONE INCOMPLETE boop that DID fresh grounding THIS window (load-verify landed) but missed an
        element → did_grounding_work=TRUE → STILL hard-fails 100% (under-fire guard intact — a real
        grounding boop ALWAYS lands its load-verify floor, so it is always caught).
    The haiku-count's per-cycle window ALSO drops the BACKWARD pad (no_backward_pad) so a STANDALONE
    full boop's count can't be inflated by an adjacent cluster either. since_turn==0 (firewall) keeps the
    ORIGINAL predicate (archive count incl.) byte-identical. Validated trust-the-walk on live session
    303ecb5f: lean window 5143-5165 now EXEMPT (did_grounding_work=false, refire_dedup=true, the 10
    archive haikus attributed to the PRIOR boop); standalone-full (since_turn=4) still PASSES;
    standalone-incomplete (missed synthesis) still FLAGS. Backup:
    tools/session_review.py.bak.20260620T192724Z-pre-grounding-work-turn-consistency."""
    full = full_turns if full_turns is not None else turns
    # PER-CYCLE SCOPE: when since_turn>0 the boop window is the turns AFTER the last-graded turn
    # (idx>since_turn) — exactly THIS /sprint-mode injection → end-of-session (or next boop). The
    # haiku archive + the structured elements are counted against THIS window ONLY. since_turn==0 ->
    # whole-session (the firewall back-compat path, unchanged).
    if since_turn and since_turn > 0:
        scan = [t for t in full if t["idx"] > since_turn]
    else:
        scan = full
    # the time-range to window the off-session haiku archive to: PER-CYCLE when scoped, whole-session
    # otherwise. Computed from the scoped turns' own timestamps so a lean boop's window can never reach
    # back to an earlier cycle's haikus.
    #   🚨 2026-06-20 (mind-lead, per-cycle false-fire cure): when per-cycle scoped, pass the window's
    #   first-turn ts as an EXPLICIT floor so _count_fresh_haiku_docs does NOT pad 10min BACKWARD past
    #   the since_turn boundary (the pad-backward reached into the PRIOR cluster's haiku-writes — the
    #   exact leak that gave a lean re-fire per_doc_haikus=10). The floor is the boundary; only the
    #   upper bound keeps the +10min clock-skew pad. (Even with this tight floor, a prior boop whose
    #   haiku-writes COMPLETED just inside this window's ts-range could still bleed in — which is why
    #   the haiku-count is no longer trusted as a grounding-WORK signal; did_grounding_work below is
    #   turn-windowed. The tight floor is belt-and-suspenders so a STANDALONE full boop's count is not
    #   itself inflated by an adjacent cluster.)
    cycle_window = _session_time_window(scan) if (since_turn and since_turn > 0) else None
    per_cycle_scoped = bool(since_turn and since_turn > 0)

    # --- TRIGGER: does the completeness contract apply to THIS window? ---
    # 🚨 LEAN-CYCLE LOOPHOLE CLOSE (the steward 2026-06-20, `"lean cycle" < discipline`): the contract now
    # fires on EITHER of two triggers — and the old "lean /sprint-mode is exempt" branch is GONE.
    #   TRIGGER 1 (kept): a GROUNDING / slow-sprint pass (GROUNDING_PROMPT_RE — the haiku-bearing shape).
    #   TRIGGER 2 (NEW — closes the loophole): a GENUINE /sprint-mode boop —
    #       (a) a /sprint-mode command-message / calendar boop in the window (SPRINT_MODE_COMMAND_RE,
    #           injected-SKILL-doc + meta turns excluded), AND
    #       (b) ≥1 work-act in the window (the boop actually DID something), AND
    #       (c) NOT a byte-identical re-injection within SPRINT_DEDUP_WINDOW_SECONDS (the cadence-lock
    #           cluster carve-out — kept exemption (a)).
    # A genuine /sprint-mode boop now OWES the full completeness contract; a lean /sprint-mode cycle
    # (genuine boop + work but no full grounding) FLAGS → clean=False → FAILS. The ONLY two remaining
    # exemptions: a byte-identical 60s dedup re-injection (handled below), and a non-/sprint-mode turn
    # (no /sprint-mode boop in the window — handled by the final `return "pass"` below).
    invoked_idx = None
    for t in scan:
        if GROUNDING_PROMPT_RE.search(t["text"] or ""):
            invoked_idx = t["idx"]
            break

    # TRIGGER 2: genuine /sprint-mode boop(s) in the window, deduped by the cadence knob. When per-cycle
    # scoped, seed the dedup with the prior /sprint-mode boop that lives BEFORE this window (idx<=since_turn)
    # so a re-injection of an out-of-scope prior boop is recognized as the cadence-lock cluster carve-out.
    anchor_norm, anchor_ts = _prior_sprint_boop_anchor(full, since_turn) if per_cycle_scoped else (None, None)
    sprint_boop_idxs = _genuine_sprint_mode_boops(scan)
    kept_boops, deduped_boops = _dedup_clustered_reinjections(
        scan, sprint_boop_idxs, anchor_norm=anchor_norm, anchor_ts=anchor_ts)
    genuine_sprint_idx = kept_boops[0] if kept_boops else None
    sprint_has_work = _has_work_act(scan) if genuine_sprint_idx is not None else False

    # the trigger turn-idx + the trigger kind (for the brief / element-scoping).
    if invoked_idx is not None:
        trigger_idx = invoked_idx
        trigger_kind = "grounding-pass"
    elif genuine_sprint_idx is not None and sprint_has_work:
        trigger_idx = genuine_sprint_idx
        trigger_kind = "sprint-mode-boop"
    else:
        trigger_idx = None
        trigger_kind = None

    if trigger_idx is None:
        # EXEMPTION (b): NO genuine grounding-trigger in THIS window.
        #   • a NON-/sprint-mode turn (no /sprint-mode boop at all — a pure conversation / status reply /
        #     answering a the steward question) is NEVER a grounding boop → pass, never failed. (no over-fire)
        #   • a /sprint-mode boop that is ENTIRELY a byte-identical 60s-dedup re-injection (kept_boops
        #     empty, all deduped) is the cadence-lock cluster carve-out → pass (the prior boop grounds).
        #   • a /sprint-mode boop with NO work-act (an empty echo, no tool-use) is not a substantive
        #     cycle → pass (the work-act is part of the genuine-boop definition).
        if deduped_boops and not kept_boops:
            return "pass", [{"turn_index": deduped_boops[0],
                             "brief": ("byte-identical /sprint-mode re-injection within the "
                                       f"{SPRINT_DEDUP_WINDOW_SECONDS}s dedup window — cadence-lock "
                                       "cluster carve-out; the prior boop carried the grounding "
                                       "(completeness contract N/A this re-injection)"),
                             "did_grounding_work": False,
                             "dedup_reinjection": True,
                             "deduped_boop_count": len(deduped_boops)}]
        if genuine_sprint_idx is not None and not sprint_has_work:
            return "pass", [{"turn_index": genuine_sprint_idx,
                             "brief": ("/sprint-mode boop with NO work-act in window — empty echo, not a "
                                       "substantive cycle (completeness contract N/A)"),
                             "did_grounding_work": False}]
        # the plain non-/sprint-mode / non-grounding turn.
        return "pass", []

    # --- collect the in-session element receipts (assistant text + Write/Edit inputs) ---
    saw_load_verify = False
    saw_synthesis = False
    saw_workflows = False
    saw_wwcw = False
    saw_hum_affirm = False
    saw_auto_consolidate = False
    saw_hum_fired = False
    saw_refire_dedup = False   # 2026-06-20: the clustered-re-fire dedup marker (corroborating exempt)
    docread_markers = 0
    # 🚨 READ→HAIKU PAIRING (2026-06-21, mind-lead — steward directive: "Hum manifest should show it
    # checking for read commands followed by haiku"). A Read tool-call FOLLOWED by a haiku is the
    # grounding-PROOF (the doc was comprehended into a haiku, not merely opened). We count the PAIRING,
    # not just the flat archive haiku count: `read_tool_calls` = how many Read tool-uses fired this
    # window; `read_haiku_pairs` = how many of those Reads were FOLLOWED (same turn or within
    # READ_HAIKU_PAIR_WINDOW_TURNS later) by a haiku artifact (a slash-3 haiku in prose OR a
    # haiku-archive append). `pending_reads` carries Read turn-idxs awaiting their haiku.
    read_tool_calls = 0
    read_haiku_pairs = 0
    pending_reads = []   # list of idxs of Read tool-calls not yet paired with a following haiku

    for t in scan:
        # gather all searchable text for this turn: assistant prose + any Write/Edit/Workflow inputs.
        texts = []
        turn_has_read_call = False
        turn_haiku_archive_write = False
        if t["role"] == "assistant":
            if t["text"]:
                texts.append(t["text"])
            for tu in t["tool_uses"]:
                # HUM-fired signature: a Workflow tool-use whose script/input names workflows/hum.js.
                st = script_text(tu)
                if st:
                    texts.append(st)
                if tu.get("name") == "Workflow" and st and "workflows/hum.js" in st:
                    saw_hum_fired = True
                # READ→HAIKU PAIRING: count Read tool-calls (the doc-open) this window.
                if tu.get("name") == "Read":
                    turn_has_read_call = True
                # a Write/Edit whose target is the haiku archive = the haiku-save artifact (counts as a
                # haiku for pairing AND is the SAVE-DISCIPLINE signal).
                if tu.get("name") in ("Write", "Edit") and st and HAIKU_ARCHIVE_PATH in st:
                    turn_haiku_archive_write = True
        blob = "\n".join(texts)
        # 🚨 READ→HAIKU PAIRING (continued): does THIS turn carry a haiku artifact? Either a slash-3
        # haiku in prose, a doc-read marker paired with a slash-3, or a haiku-archive append. A haiku
        # in this turn PAIRS the nearest pending Read (FIFO) within the look-ahead window — the read
        # was followed by its haiku = grounding-proof.
        turn_has_haiku = turn_haiku_archive_write or bool(blob and HAIKU_LINE_RE.search(blob))
        if turn_has_read_call:
            read_tool_calls += 1
            pending_reads.append(t["idx"])
        if turn_has_haiku and pending_reads:
            # pair the OLDEST pending read still inside the look-ahead window with this haiku.
            oldest = pending_reads[0]
            if (t["idx"] - oldest) <= READ_HAIKU_PAIR_WINDOW_TURNS:
                read_haiku_pairs += 1
                pending_reads.pop(0)
            else:
                # the oldest read aged out of the window unpaired; drop stale heads, then try to pair.
                while pending_reads and (t["idx"] - pending_reads[0]) > READ_HAIKU_PAIR_WINDOW_TURNS:
                    pending_reads.pop(0)
                if pending_reads and (t["idx"] - pending_reads[0]) <= READ_HAIKU_PAIR_WINDOW_TURNS:
                    read_haiku_pairs += 1
                    pending_reads.pop(0)
        if not blob:
            continue
        # load-verify block: >=2 distinct *_loaded: keys in any single turn's blob.
        if not saw_load_verify:
            keys = len(set(m.group(1).lower() for m in LOAD_VERIFY_KEY_RE.finditer(blob)))
            if keys >= 2:
                saw_load_verify = True
        if not saw_synthesis and GROUNDING_SYNTHESIS_RE.search(blob):
            saw_synthesis = True
        if not saw_workflows and GROUNDING_WORKFLOWS_MANDATE_RE.search(blob):
            saw_workflows = True
        if not saw_wwcw and GROUNDING_WWCW_AFFIRM_RE.search(blob):
            saw_wwcw = True
        if not saw_hum_affirm and GROUNDING_HUM_AFFIRM_RE.search(blob):
            saw_hum_affirm = True
        if not saw_auto_consolidate and GROUNDING_AUTO_CONSOLIDATE_RE.search(blob):
            saw_auto_consolidate = True
        if not saw_refire_dedup and GROUNDING_REFIRE_DEDUP_RE.search(blob):
            saw_refire_dedup = True
        docread_markers += len(GROUNDING_DOCREAD_MARKER_RE.findall(blob))
        # HUM-fired can also be named in prose ("fired Workflow(workflows/hum.js)").
        if not saw_hum_fired and "workflows/hum.js" in blob:
            saw_hum_fired = True

    # --- the per-doc-haiku receipt (the docset count) — windowed to THIS boop when per-cycle scoped.
    #     per-cycle: drop the BACKWARD pad so the window cannot reach across the since_turn boundary
    #     into a prior cluster's haiku-writes (the leak that gave a lean re-fire per_doc_haikus=10). ---
    fresh_haiku_docs, archive_verifiable = _count_fresh_haiku_docs(
        scan, window=cycle_window, no_backward_pad=per_cycle_scoped)

    # --- FALSE-FAIL GUARD: did the boop do FRESH grounding work THIS turn-window? ---
    # 🚨 2026-06-20 (mind-lead, per-cycle false-fire cure — TURN-CONSISTENCY). THE BUG HUM w11apf32v
    # caught: did_grounding_work was driven partly by the ts-windowed archive haiku-count, which reaches
    # BACK across a clustered re-fire and picks up a PRIOR full boop's 10 haikus (per_doc_haikus=10 ->
    # did_grounding_work=true) while the element-check is TURN-windowed (idx>since_turn) and correctly
    # finds the elements absent (they were before since_turn). The two scopings disagreed -> a legit
    # lean clustered re-fire FALSE-FAILED (forced HOLLOW).
    # THE FIX: when per-cycle scoped, the grounding-WORK signal is turn-windowed too — it uses ONLY the
    # in-window element signatures (load-verify block, doc-read markers, the grounding synthesis/affirm
    # prose), NEVER the ts-windowed archive count. A lean re-fire that did NO fresh grounding THIS
    # window -> did_grounding_work=FALSE -> EXEMPT (the existing lean-boop exemption now applies
    # correctly). A STANDALONE full boop has its load-verify + doc-reads + its 10 haikus IN this window
    # -> did_grounding_work=TRUE -> graded full. The full-session back-compat path (since_turn==0) keeps
    # the original predicate (incl. the haiku count) byte-identical.
    # GUARD AGAINST UNDER-FIRE: the in-window FRESH-grounding signatures are the two ARTIFACTS a real
    # read-one-at-a-time grounding pass leaves — the load-verify FLOOR block (saw_load_verify) and the
    # per-doc DOC-READ markers (docread_markers>=1). Either trips did_grounding_work=TRUE, so a
    # genuinely-incomplete STANDALONE boop that DID fresh grounding THIS window but missed an element
    # STILL hard-fails 100% (a real grounding boop ALWAYS lands its load-verify floor — so it is always
    # caught). We removed the cross-cluster leak, not the strict standard.
    #   We DELIBERATELY EXCLUDE the affirmation/synthesis PROSE (wwcw/hum/workflows/auto-consolidate/
    #   synthesis) from the fresh-WORK predicate: those phrases are cheap to emit while a LEAN re-fire
    #   PROCESSES a prior HUM verdict (the live 5143-5165 window mentions WWCW + HUM + auto-consolidate
    #   purely in verdict-reporting), so counting them as "fresh grounding work" re-opens the exact
    #   false-fire. The affirmations remain REQUIRED ELEMENTS of completeness (graded below) — they are
    #   just not evidence that fresh GROUNDING happened this window.
    grounding_work_signatures_this_window = saw_load_verify or (docread_markers >= 1)
    if per_cycle_scoped:
        did_grounding_work = grounding_work_signatures_this_window
    else:
        # full-session (firewall back-compat): original predicate, byte-identical (archive count incl.).
        did_grounding_work = (fresh_haiku_docs >= 1) or saw_load_verify or (docread_markers >= 1)

    # 🚨 LEAN-CYCLE LOOPHOLE CLOSE (the steward 2026-06-20, `"lean cycle" < discipline`): when the trigger is a
    # GENUINE non-deduped /sprint-mode boop (TRIGGER 2), the boop OWES the full grounding REGARDLESS of
    # whether it left grounding-work signatures. The whole POINT of a lean-cycle dodge is that the boop
    # did NO grounding work — so the `did_grounding_work` exemption MUST NOT exempt it (that exemption was
    # the loophole). The exemption stays ONLY for a TRIGGER-1 grounding-pass that is a recognized lean
    # CLUSTERED RE-FIRE (a prior boop already grounded; this window only processed verdicts). A genuine
    # /sprint-mode cycle that did no grounding now falls through to grading and FAILS (every element
    # missing). Note: the byte-identical-dedup carve-out already fired ABOVE (kept_boops empty → pass);
    # any boop reaching here under TRIGGER 2 is a KEPT (non-deduped) genuine cycle that must fully ground.
    grounding_pass_trigger = (trigger_kind == "grounding-pass")
    # 🚨 RECENCY-EXEMPTION KILL (fleet-lead 2026-06-20, per the approved CLOCKWORK-EVERY-FIRE design,
    # steward verbatim `"lean cycle" < discipline` + "Hum every cycle FOR SURE"). THE RESIDUAL LEAK this
    # closes: the prior v5.1 branch exempted ANY grounding-pass with no work-signatures — including a
    # BARE grounding-pass with NO dedup-corroboration (the `else` brief below used to read "not a
    # substantive grounding boop, completeness contract N/A" and PASS). That was the recency-as-excuse
    # residue: "I grounded recently so this bare grounding-pass is exempt." The CLOCKWORK design kills
    # it — the `did_grounding_work` exemption now applies ONLY to a CORROBORATED clustered re-fire (a
    # recognized byte-identical re-fire, evidenced by the dedup marker OR by archive haikus that demonstrably
    # belong to the PRIOR boop's ts-range). A bare uncorroborated grounding-pass that did NO work this
    # window is NOT a recognized re-fire — it falls through to grading and FAILS (every element missing).
    # The two HONEST exemptions remain intact: (a) the byte-identical 60s dedup re-injection (handled
    # ABOVE at kept_boops-empty → pass); (b) a non-/sprint-mode turn (no trigger → pass). What is GONE
    # is the third, abused path: "recently-grounded → a bare grounding-pass skips the contract."
    if not did_grounding_work and grounding_pass_trigger:
        # 🚨 CORROBORATION = the EXPLICIT clustered-re-fire dedup marker ONLY (saw_refire_dedup).
        # We DELIBERATELY do NOT accept "archive haikus in the ts-range" as corroboration: that
        # ts-windowed archive count BLEEDS across a clustered re-fire (it reaches back and picks up
        # the PRIOR boop's haikus — the exact leak wls4i6lu2's turn-consistency fix removed from the
        # grounding-WORK signal). Using it as corroboration would re-open that leak and let a bare
        # recency-dodge launder a PASS off a neighbor's haikus. Only the mind's OWN explicit
        # "hum_cadence: deduped byte-identical /sprint-mode re-injection within Ns" marker (written
        # this window) corroborates a recognized re-fire. Everything else falls through and FAILS.
        corroborated_refire = per_cycle_scoped and saw_refire_dedup
        if corroborated_refire:
            # CORROBORATED clustered re-fire — the prior full boop grounded; this window only processed
            # verdicts / reported, and the mind LOGGED the dedup. EXEMPT (completeness contract N/A).
            brief = ("lean clustered re-fire — NO fresh grounding work THIS turn-window "
                     "(0 in-window load-verify/doc-read/synthesis signatures); clustered-re-fire dedup "
                     "marker present — completeness contract N/A (the prior full boop carried it)")
            return "pass", [{"turn_index": trigger_idx,
                             "brief": brief,
                             "did_grounding_work": False,
                             "refire_dedup_marker": True,
                             "corroborated_refire": True}]
        # UNCORROBORATED bare grounding-pass: a grounding-pass-shaped boop that did NO work this window
        # AND has no clustered-re-fire corroboration = the recency-as-excuse dodge. CLOCKWORK design:
        # this is NO LONGER exempt. Fall through to grading → every element missing → 100% FAIL.
        # (Note: a genuine grounding pass ALWAYS lands its load-verify floor + ≥1 haiku, so this only
        # ever bites the bare dodge; a real full grounding sets did_grounding_work=True and is graded
        # against the full checklist below.)
        pass  # intentional fall-through to the COMPLETENESS grading block

    # --- COMPLETENESS: enumerate every missing required element. STRICT: any missing = 100% fail. ---
    missing = []
    # (1) per-doc haikus — only counted as a miss when the archive is VERIFIABLE (never fail what we
    #     could not check). archive-unverifiable -> the element is could-not-verify, not a miss.
    haiku_complete = (fresh_haiku_docs >= GROUNDING_COMPLETE_DOCSET)
    if archive_verifiable and not haiku_complete:
        missing.append(f"per-doc-haikus({fresh_haiku_docs}/{GROUNDING_COMPLETE_DOCSET})")
    # (1b) READ→HAIKU PAIRING (2026-06-21, mind-lead — steward directive: "Hum manifest should show it
    #      checking for read commands followed by haiku"). The grounding-PROOF is not merely that N
    #      haikus exist in the archive — it is that each grounding-doc Read (the doc-open) is FOLLOWED
    #      by a haiku (the comprehension). A grounding pass that opened the docs but did NOT pair each
    #      read with a haiku (read-without-comprehend) is INCOMPLETE.
    #      🛡️ CONSERVATIVE TRIGGER (do NOT over-tune the born-today gate, the steward 2026-06-21): this element
    #      fires ONLY when the boop is a GENUINE read-one-at-a-time grounding pass — signaled by ≥docset
    #      DOC-READ MARKERS (`[Doc N read]`, the grounding-specific artifact a real grounding leaves),
    #      NOT raw Read tool-call count. A normal WORK window reads many files (≥docset Read tool-calls)
    #      but leaves ZERO doc-read markers → NOT gated by (1b) (it is not a grounding pass — its real
    #      grounding happened elsewhere; the per-doc-haiku archive element governs the archive count).
    #      This makes (1b) additive PAIRING-proof ON TOP of a confirmed grounding pass, never a false-
    #      fail on a work/processing window. (Validated: the live 303ecb5f per-cycle 5600 window — 59
    #      Read tool-calls, docread_markers=0, a processing window — does NOT trip (1b), preserving the
    #      pre-edit verdict; a real grounding pass with ≥docset `[Doc N read]` markers IS held to the
    #      pairing.) When (1b) IS gated, completeness requires ≥docset of the doc-read pairs land a haiku.
    is_genuine_read_pass = (docread_markers >= GROUNDING_COMPLETE_DOCSET)
    pairing_complete = (read_haiku_pairs >= GROUNDING_COMPLETE_DOCSET)
    if is_genuine_read_pass and not pairing_complete:
        missing.append(f"read-haiku-pairing({read_haiku_pairs}/{docread_markers} doc-reads paired)")
    if not saw_load_verify:
        missing.append("load-verify-block")
    if not saw_synthesis:
        missing.append("synthesis-statement")
    if not saw_workflows:
        missing.append("workflows-mandate")
    if not saw_wwcw:
        missing.append("wwcw-affirmation")
    if not saw_hum_affirm:
        missing.append("hum-affirmation")
    if not saw_auto_consolidate:
        missing.append("auto-consolidate-sweep")
    if not saw_hum_fired:
        missing.append("hum-last-step-fired")

    elements = {
        "per_doc_haikus": fresh_haiku_docs,
        "haiku_archive_verifiable": archive_verifiable,
        # 🚨 READ→HAIKU PAIRING (2026-06-21): the read-command→haiku PAIRING proof the steward asked for.
        "read_tool_calls": read_tool_calls,
        "read_haiku_pairs": read_haiku_pairs,
        "read_haiku_pairing_complete": pairing_complete,
        # 🚨 HAIKU-SAVED: the archive IS the durable save (count(haikus in archive this window)). A
        #    verifiable archive with >=docset fresh entries proves "saving all the haikus" (the steward).
        "haikus_saved_to_archive": (archive_verifiable and haiku_complete),
        "load_verify": saw_load_verify,
        "synthesis": saw_synthesis,
        "workflows_mandate": saw_workflows,
        "wwcw_affirm": saw_wwcw,
        "hum_affirm": saw_hum_affirm,
        "auto_consolidate": saw_auto_consolidate,
        "hum_fired": saw_hum_fired,
        "docread_markers": docread_markers,
        "refire_dedup_marker": saw_refire_dedup,
        "trigger_kind": trigger_kind,
    }

    if missing:
        # a lean /sprint-mode cycle that triggered via a genuine /sprint-mode boop (not a grounding-pass)
        # surfaces the trigger so HUM names the EXACT shape Primary dodged ("lean cycle < discipline").
        lean_note = (" [LEAN /sprint-mode CYCLE — genuine boop did NOT fully ground; "
                     "'lean cycle' < discipline, the steward 2026-06-20]"
                     if trigger_kind == "sprint-mode-boop" else "")
        # 🚨 RECENCY-EXEMPTION KILL (fleet-lead 2026-06-20): an UNCORROBORATED bare grounding-pass that
        # did NO fresh work this window AND has no clustered-re-fire corroboration reaches here via the
        # CLOCKWORK fall-through above. Name it honestly so HUM reads the EXACT dodge: "I grounded
        # recently → a bare grounding-pass skips the contract" — now FAILED, not exempt.
        recency_dodge = (trigger_kind == "grounding-pass") and (not did_grounding_work)
        recency_note = (" [RECENCY-DODGE — bare grounding-pass, no fresh work, no clustered-re-fire "
                        "corroboration; the just-grounded/lean exemption is KILLED, every fire grounds "
                        "fully, the steward 2026-06-20]" if recency_dodge else "")
        return "flag", [{"turn_index": trigger_idx,
                         "brief": ("INCOMPLETE grounding boop (the steward complete-or-fail contract "
                                   "2026-06-20: miss one doc/haiku/step = 100% fail) — missing: "
                                   + ", ".join(missing) + lean_note + recency_note),
                         "missing_elements": missing,
                         "elements": elements,
                         "trigger_kind": trigger_kind,
                         "did_grounding_work": did_grounding_work,
                         "recency_dodge": recency_dodge,
                         "candidate": False}]
    # COMPLETE — every required element present. Informational compliant hit (so HUM reports the full
    # picture: a complete boop is the proof the discipline held).
    return "pass", [{"turn_index": trigger_idx,
                     "brief": (f"COMPLETE grounding boop ({trigger_kind}) — {fresh_haiku_docs} per-doc "
                               f"haikus + load-verify + synthesis + workflows + wwcw + hum + "
                               f"auto-consolidate + hum-fired all present"),
                     "missing_elements": [],
                     "elements": elements,
                     "trigger_kind": trigger_kind,
                     "did_grounding_work": True,
                     "compliant": True,
                     "candidate": False}]


def check_freeze_edit(turns, freeze_cfg):
    """FLAG: an Edit/Write whose file_path matches a freeze glob within the freeze window.

    NA if no usable freeze config (no globs OR no window). Emits PATH ONLY (paths are not
    secrets); never reads file contents."""
    globs = (freeze_cfg or {}).get("freeze_globs") or []
    ws = parse_iso((freeze_cfg or {}).get("window_start"))
    we = parse_iso((freeze_cfg or {}).get("window_end"))
    if not globs or ws is None or we is None:
        return "na", []
    hits = []
    for t in turns:
        if t["role"] != "assistant":
            continue
        for tu in t["tool_uses"]:
            if tu["name"] not in ("Edit", "Write"):
                continue
            inp = tu.get("input")
            fp = inp.get("file_path") if isinstance(inp, dict) else None
            if not fp:
                continue
            in_window = True
            if t["ts"] is not None:
                in_window = (ws <= t["ts"] < we)
            if not in_window:
                continue
            # normalize: match against both abs and repo-relative forms
            rel = fp
            for root in ((os.environ.get("CIV_ROOT", os.environ.get("AICIV_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + "/"),):
                if rel.startswith(root):
                    rel = rel[len(root):]
            matched = any(fnmatch.fnmatch(fp, g) or fnmatch.fnmatch(rel, g) for g in globs)
            if matched:
                hits.append({"turn_index": t["idx"],
                             "brief": f"freeze-path edit: {rel}"})  # path only, non-sensitive
    return ("flag" if hits else "pass"), hits


def check_freeze_config_missing(freeze_cfg):
    """FLAG (CONFIG-MISSING, not a pass): a freeze check requested with no paths/window.

    This check exists so that 'no freeze config' is reported as CONFIG-MISSING rather than
    silently passing FREEZE-EDIT. If a complete config IS present, this check passes."""
    globs = (freeze_cfg or {}).get("freeze_globs") or []
    ws = (freeze_cfg or {}).get("window_start")
    we = (freeze_cfg or {}).get("window_end")
    if globs and ws and we:
        return "pass", []
    return "flag", [{"turn_index": -1,
                     "brief": "freeze config absent/incomplete (need freeze_globs + window_start + window_end)"}]


CHECK_ORDER = [
    "WWCW-GATE", "BLOCK-NO-WWCW", "MODEL-PIN", "MEMORY-EMIT", "CLAIM-BACKING", "DONE-DONE",
    "SYNTHETIC-ERROR", "SKILL-FLOOR", "SKILL-CANDIDATE", "DELEGATION-SHAPE",
    "PROJECT-FOLDER-TOUCH", "DOC-CURRENCY", "SWEEP-ACT-ON-FLAGGED",
    "SPRINT-MODE-READ", "HAIKU-PER-DOC", "GROUNDING-COMPLETENESS",
    # 🔎 HUM-MANDATE checks (mind-lead 2026-06-20, ADDITIVE): enforce the per-boop HUM discipline ON
    # REVIEW. na when no HUM fire is observed; flag a HUM fire that left no saved checklist / no find-the-miss.
    "CHECKLIST-SAVED", "FIND-THE-MISS-PRESENT",
    "FREEZE-EDIT", "FREEZE-CONFIG-MISSING",
]

# checks whose hits are inherently candidate-only (heuristic, not hard verdicts)
# 🚨 BLOCK-NO-WWCW is DELIBERATELY ABSENT from this set — it is a HARD-FAIL check (a block without a
# WWCW run FAILS the boop, the steward 2026-06-20). WWCW-GATE remains candidate-only (its finer DECIDE
# taxonomy is heuristic, weighed by the Stage-2 grader); BLOCK-NO-WWCW is the boop-failing enforcement.
CANDIDATE_CHECKS = {"WWCW-GATE", "CLAIM-BACKING", "DONE-DONE", "SKILL-FLOOR", "SKILL-CANDIDATE", "DELEGATION-SHAPE", "PROJECT-FOLDER-TOUCH", "DOC-CURRENCY", "SWEEP-ACT-ON-FLAGGED", "SPRINT-MODE-READ", "HAIKU-PER-DOC"}
# informational checks (a 'flag' is a signal for downstream, not a defect of the session)
INFORMATIONAL_CHECKS = {"SYNTHETIC-ERROR"}

# ---------------------------------------------------------------------------
# GROUNDING-RECEIPT HARD-FAIL set (steward directive 2026-06-19, v1.6): "HUM needs to FAIL
# your sprint-mode boops if they can't find proof you did it correctly." The two
# grounding-receipt checks (SPRINT-MODE-READ + HAIKU-PER-DOC) are PROMOTED from candidate-only
# to HARD-FAIL flags — but ONLY in the specific, airtight case where a /sprint-mode | grounding
# boop GENUINELY RAN this session AND the proof is ABSENT (the floor load-verify block never
# written AND/OR zero fresh haiku-archive entries in-window). That genuine flag now breaks
# summary.clean (clean = no HARD flags), surfacing an unproven sprint as a FAILED boop on the record.
#
# 🚨 WHY THIS IS SAFE FROM FALSE-FAIL (the load-bearing scoping invariant): the DETECTION inside
# check_sprint_mode_read / check_haiku_per_doc ALREADY scopes correctly — they `flag` ONLY when a
# sprint/grounding pass was INVOKED but its artifact never landed. A non-sprint turn, a pure
# task-notification turn, or any session where no sprint/grounding was claimed returns status="pass"
# (the `invoked_idx is None` branch), so it never enters this hard-fail. Promotion here changes ONLY
# how a GENUINE flag is classified (hard vs candidate); it does NOT widen WHEN a flag fires. The
# checks' compliant/received/N-A hits all carry status="pass" → never hard-fail. fresh_haikus=-1
# (could-not-verify) returns status="pass" → never hard-fail (we never penalize what we could not check).
#
# These checks REMAIN in CANDIDATE_CHECKS so each HIT still carries candidate=True for the Stage-2
# judge to WALK (per-hit heuristic honesty); the HARD-FAIL set governs only the SUMMARY classification
# of a flag (flagged vs candidate). A check in BOTH sets that flags → flagged (breaks clean).
GROUNDING_RECEIPT_HARDFAIL_CHECKS = {"SPRINT-MODE-READ", "HAIKU-PER-DOC"}

# ---------------------------------------------------------------------------
# 🚨 BLOCK-NO-WWCW HARD-FAIL (steward directive 2026-06-20, verbatim: "If no evidence of wwcw run
# it's to fail your boop"). This check is NOT in CANDIDATE_CHECKS — a genuine flag breaks summary.clean
# (the boop FAILS), full stop. The flag fires ONLY when a BLOCK (park/hold/present-for-the steward) is present
# AND the scanned window holds ZERO WWCW-run footprint (check_block_no_wwcw's airtight predicate). A clean
# session, a status-only session, or any session where WWCW was actually run = status="pass" → no hard-fail.
# This naming makes the boop-failing intent explicit even though the default `else` branch (not-candidate →
# flagged) would already classify it HARD — belt-and-suspenders for the most load-bearing gate.
BLOCK_NO_WWCW_HARDFAIL_CHECKS = {"BLOCK-NO-WWCW"}

# ---------------------------------------------------------------------------
# 🚨 GROUNDING-COMPLETENESS HARD-FAIL (steward directive 2026-06-20, verbatim: "Hum needs to check and
# fully FAIL any boop that isn't hyper detailed and complete. Miss one doc or one haiku or one step
# it's 100% fail on that boop. The discipline is EVERYTHING."). This check is NOT in CANDIDATE_CHECKS
# — a genuine flag breaks summary.clean (the boop FAILS), full stop. STRICT: partial completion = full
# failure. The flag fires ONLY when a boop DID substantive grounding work (GROUNDING_PROMPT_RE invoked
# AND ≥1 grounding-work-signature) AND is MISSING ≥1 required element (any per-doc haiku short of the
# docset, OR a missing load-verify/synthesis/workflows/wwcw/hum/auto-consolidate/hum-fired step). A
# non-grounding session, a pure status reply, or a COMPLETE grounding boop = status="pass" → no
# hard-fail (the airtight did-grounding-work-AND-incomplete predicate inside check_grounding_completeness).
GROUNDING_COMPLETENESS_HARDFAIL_CHECKS = {"GROUNDING-COMPLETENESS"}

# ---------------------------------------------------------------------------
# 🔎 HUM-MANDATE HARD-FAIL set (mind-lead 2026-06-20). HONEST behavioral enforcement of the HUM per-boop
# discipline ON REVIEW: a HUM fire that left no saved checklist doc (CHECKLIST-SAVED), or recorded no
# find-the-miss (FIND-THE-MISS-PRESENT), FLAGS → breaks summary.clean. These are NOT in CANDIDATE_CHECKS
# — a genuine flag is a real discipline-skip, not a heuristic. The flag fires ONLY when a HUM fire was
# genuinely observed in the scanned window AND the mandatory evidence is absent by ALL independent signals
# (the airtight observed-AND-missing predicate inside each check). A window with no HUM fire = na → never
# hard-fail. This naming makes the discipline-skip intent explicit (the default else branch would already
# flag a non-candidate check; belt-and-suspenders).
HUM_MANDATE_HARDFAIL_CHECKS = {"CHECKLIST-SAVED", "FIND-THE-MISS-PRESENT"}


def run_all(turns, freeze_cfg, full_turns=None, since_turn=0):
    # full_turns = the COMPLETE session (unscoped). The two grounding-receipt checks
    # (SPRINT-MODE-READ / HAIKU-PER-DOC) are WHOLE-SESSION properties (the floor read + haiku gate
    # fire at session START) and MUST run against the full session even when --since-turn scopes the
    # delta-detection of the other checks. All other checks use the (possibly delta-scoped) `turns`.
    # since_turn = the hum-cursor boundary (the start of THIS boop's window). GROUNDING-COMPLETENESS
    # uses it to scope the COMPLETE-OR-FAIL contract to the PER-INVOCATION boop window (counts only
    # THIS boop's fresh haikus + this-boop elements, not session-wide). The two receipt checks stay
    # whole-session (they detect "did SOME grounding receipt ever land"); GROUNDING-COMPLETENESS is the
    # per-cycle completeness enforcer.
    ft = full_turns if full_turns is not None else turns
    results = {}
    results["WWCW-GATE"] = check_wwcw_gate(turns)
    results["BLOCK-NO-WWCW"] = check_block_no_wwcw(turns)
    results["MODEL-PIN"] = check_model_pin(turns)
    results["MEMORY-EMIT"] = check_memory_emit(turns)
    results["CLAIM-BACKING"] = check_claim_backing(turns)
    results["DONE-DONE"] = check_done_done(turns)
    results["SYNTHETIC-ERROR"] = check_synthetic_error(turns)
    results["SKILL-FLOOR"] = check_skill_floor(turns)
    results["SKILL-CANDIDATE"] = check_skill_candidate(turns)
    results["DELEGATION-SHAPE"] = check_delegation_shape(turns)
    results["PROJECT-FOLDER-TOUCH"] = check_project_folder_touch(turns)
    results["DOC-CURRENCY"] = check_doc_currency(turns)
    # 🧹 SWEEP-ACT-ON-FLAGGED (fleet-lead 2026-06-22): a consolidation sweep that self-reported NOT-CLEAN
    # but did NOT act in-boop (notice-don't-act). CANDIDATE-only — the JUDGE confirms intent + FAILs.
    results["SWEEP-ACT-ON-FLAGGED"] = check_sweep_act_on_flagged(turns)
    results["SPRINT-MODE-READ"] = check_sprint_mode_read(turns, full_turns=ft)
    results["HAIKU-PER-DOC"] = check_haiku_per_doc(turns, full_turns=ft)
    # GROUNDING-COMPLETENESS scopes the COMPLETE-OR-FAIL contract to the PER-INVOCATION boop window
    # when since_turn>0 (the hum-cursor boundary): it counts ONLY THIS boop's fresh haikus + this-boop
    # elements (NOT session-wide). since_turn==0 -> whole-session (firewall back-compat). full_turns is
    # passed so the per-cycle scope is sliced from the COMPLETE session by idx>since_turn (the scoped
    # `turns` may already be delta-filtered; GROUNDING-COMPLETENESS re-derives its own window from ft).
    results["GROUNDING-COMPLETENESS"] = check_grounding_completeness(turns, full_turns=ft, since_turn=since_turn)
    # 🔎 HUM-MANDATE checks (mind-lead 2026-06-20): enforce the HUM per-boop discipline ON REVIEW. They
    # scan the (possibly delta-scoped) `turns` for a HUM fire — na if none observed; flag a HUM fire that
    # left no saved checklist (CHECKLIST-SAVED) / no find-the-miss (FIND-THE-MISS-PRESENT). Additive —
    # no existing check is touched (PRESERVES wls4i6lu2's grounding-completeness work entirely).
    results["CHECKLIST-SAVED"] = check_checklist_saved(turns)
    results["FIND-THE-MISS-PRESENT"] = check_find_the_miss_present(turns)
    results["FREEZE-EDIT"] = check_freeze_edit(turns, freeze_cfg)
    results["FREEZE-CONFIG-MISSING"] = (lambda r: r)(check_freeze_config_missing(freeze_cfg))
    return results


def build_record(session_id, path, turns, parse_errors, freeze_cfg, full_turns=None, since_turn=0):
    results = run_all(turns, freeze_cfg, full_turns=full_turns, since_turn=since_turn)
    checks = []
    flagged, candidate, na = [], [], []
    for cid in CHECK_ORDER:
        status, hits = results[cid]
        # cap hits per check to keep the record bounded + non-floody (positions preserved as count)
        total = len(hits)
        capped = hits[:50]
        entry = {"id": cid, "status": status, "hit_count": total, "hits": capped}
        if total > len(capped):
            entry["hits_truncated"] = True
        if cid in CANDIDATE_CHECKS:
            entry["candidate_only"] = True
        if cid in INFORMATIONAL_CHECKS:
            entry["informational"] = True
        checks.append(entry)
        if status == "na":
            na.append(cid)
        elif status == "flag":
            # 🚨 BLOCK-NO-WWCW HARD-FAIL (the steward 2026-06-20): a BLOCK with no WWCW-run evidence FAILS
            # the boop. Classified HARD explicitly (it is not in CANDIDATE_CHECKS, so the `else` would
            # already flag it — this named branch makes the boop-failing intent unmissable + ordered
            # before the candidate fallthrough so it can never be soft-classified by a future edit).
            if cid in BLOCK_NO_WWCW_HARDFAIL_CHECKS:
                flagged.append(cid)
            # 🚨 GROUNDING-COMPLETENESS HARD-FAIL (the steward 2026-06-20): a substantive grounding boop that
            # is MISSING ≥1 required element (a doc/haiku/step) FAILS the boop. STRICT — partial = full
            # failure. Not in CANDIDATE_CHECKS, so the `else` would already flag it; this named branch
            # makes the boop-failing intent unmissable + ordered before the candidate fallthrough so a
            # future edit can never soft-classify it.
            elif cid in GROUNDING_COMPLETENESS_HARDFAIL_CHECKS:
                flagged.append(cid)
            # 🔎 HUM-MANDATE HARD-FAIL (mind-lead 2026-06-20): a HUM fire that left no saved checklist
            # (CHECKLIST-SAVED) / no find-the-miss (FIND-THE-MISS-PRESENT) FLAGS → breaks summary.clean.
            # Not in CANDIDATE_CHECKS, so the else would already flag it; named branch makes the
            # discipline-skip intent unmissable + ordered before the candidate fallthrough.
            elif cid in HUM_MANDATE_HARDFAIL_CHECKS:
                flagged.append(cid)
            # GROUNDING-RECEIPT HARD-FAIL (v1.6): SPRINT-MODE-READ / HAIKU-PER-DOC flag ONLY on a
            # genuine invoked-but-no-proof sprint boop (their detection scopes out non-sprint sessions
            # to status="pass"). A flag here is a FAILED boop on the record → it MUST break clean.
            # This check is evaluated BEFORE the candidate fallthrough so a grounding-receipt check that
            # lives in BOTH sets is classified HARD (flagged), not soft (candidate).
            elif cid in GROUNDING_RECEIPT_HARDFAIL_CHECKS:
                flagged.append(cid)
            elif cid in CANDIDATE_CHECKS:
                candidate.append(cid)
            else:
                flagged.append(cid)
    # clean = no HARD flags. Candidate + informational do not break clean; a GENUINE grounding-receipt
    # flag (invoked sprint boop with no proof) DOES (v1.6 the steward hard-fail directive).
    clean = (len(flagged) == 0)
    return {
        "stage": "1-deterministic",
        "tool": "session_review.py",
        "session_id": session_id,
        "session_path": os.path.abspath(path),
        "turns_scanned": len(turns),
        "parse_errors": parse_errors,
        "checks": checks,
        "summary": {
            "flagged": flagged,
            "candidate": candidate,
            "na": na,
            "clean": clean,
        },
    }


def main():
    ap = argparse.ArgumentParser(
        description="Stage-1 deterministic session-file reviewer (HUM grader, layer 1). "
                    "Parses a Claude-Code session JSONL and emits a PII-safe JSON findings "
                    "record for a Stage-2 judging mind. No LLM call inside.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Output: JSON to stdout. Hits carry turn-index + a short mechanical brief only "
               "(never message text, secrets, or PII).",
    )
    ap.add_argument("session", nargs="?", default=None,
                    help="Path to session .jsonl (default: newest in the origin project dir).")
    ap.add_argument("--project-dir", default=DEFAULT_PROJECT_DIR,
                    help="Project dir to pick the newest session from when none is given.")
    ap.add_argument("--freeze-config", default=None,
                    help="Path to a JSON freeze config {freeze_globs, window_start, window_end}.")
    ap.add_argument("--since-turn", type=int, default=0,
                    help="HUM v0.2 cycle-delta scoping. When >0, the deterministic checks flag "
                         "ONLY turns whose 0-based idx > N (the NEW turns since the last grade of "
                         "this session). Default 0 = full-session behavior (backward-compatible). "
                         "NOTE: this scopes DETECTION only — the Stage-2 judge still reads the FULL "
                         "session to WALK any flagged turn.")
    ap.add_argument("--pretty", action="store_true", help="Pretty-print the JSON output.")
    args = ap.parse_args()

    path = args.session or newest_session(args.project_dir)
    if not path:
        print(json.dumps({"error": "no session jsonl found",
                          "project_dir": args.project_dir}), file=sys.stderr)
        return 2
    if not os.path.isfile(path):
        print(json.dumps({"error": "session file not found", "path": path}), file=sys.stderr)
        return 2

    # CHANGELOG 2026-06-19 (fleet-lead): cure the recurring HUM FREEZE-CONFIG-MISSING flag
    # systemically. When --freeze-config is not given, fall back to the canonical
    # config/freeze-config.json (mind-lead-owned) IF it exists on disk. This makes the freeze
    # gate read its config by DEFAULT for EVERY invocation — direct calls AND HUM's DETECT shell —
    # so FREEZE-CONFIG-MISSING stops firing once the config is present. Reversible: delete this
    # block + the constant to revert to flag-only behavior (.bak.20260619T210001Z-pre-freeze-default).
    DEFAULT_FREEZE_CONFIG = (os.environ.get("CIV_ROOT", os.environ.get("AICIV_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))) + "/config/freeze-config.json")
    freeze_config_path = args.freeze_config
    if not freeze_config_path and os.path.isfile(DEFAULT_FREEZE_CONFIG):
        freeze_config_path = DEFAULT_FREEZE_CONFIG

    freeze_cfg = None
    if freeze_config_path:
        try:
            with open(freeze_config_path) as fh:
                freeze_cfg = json.load(fh)
        except Exception as e:
            print(json.dumps({"error": "freeze config unreadable", "detail": str(e)}), file=sys.stderr)
            return 2

    turns, parse_errors, session_id = load_turns(path)
    total_turns = len(turns)

    # --- HUM v0.2 CYCLE-DELTA SCOPING (DETECTION scope only) ---
    # When --since-turn N > 0, flag ONLY the NEW turns (idx > N) since the last HUM grade of
    # this session. N is the last-graded turn index (the cursor's high-water mark). Default N=0
    # keeps the full session (every 0-based idx >= 0) — backward-compatible to the byte.
    #
    # 🚨 LOAD-BEARING INVARIANT: this filter narrows ONLY which turns the deterministic checks
    # SCAN for flags. It does NOT — and MUST NOT — limit what the Stage-2 judge may read. The
    # judge is handed session_path (the FULL transcript) and the original (unscoped) turn-window
    # bounds, and WALKS any flagged turn against full-session context. A flag at turn 2750 may
    # require reading turn 40 to confirm intent. session_review.py is the DETECT layer; "trust
    # the walk" lives in the judge, which always sees everything.
    since = args.since_turn
    scoped_turns = turns
    if since and since > 0:
        scoped_turns = [t for t in turns if t["idx"] > since]

    # `turns` = the FULL session (unscoped); `scoped_turns` = the delta-detection window.
    # The two grounding-receipt checks run against `turns` (whole-session) via full_turns; all
    # other checks scan `scoped_turns`.
    record = build_record(session_id, path, scoped_turns, parse_errors, freeze_cfg, full_turns=turns, since_turn=since)
    # Audit-transparency: record exactly which turn-window this run scoped its DETECTION to
    # (the human CAN look, never HAS to). turns_scanned already reflects the scoped count.
    record["scoping"] = {
        "since_turn": since,
        "delta_scoped": bool(since and since > 0),
        "turn_window": {"from": (since + 1 if since and since > 0 else 0),
                        "to": (total_turns - 1 if total_turns else -1)},
        "session_total_turns": total_turns,
    }
    print(json.dumps(record, indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
