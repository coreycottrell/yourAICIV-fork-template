// =============================================================================
// workflows/bulletproof-hum.js — BULLETPROOF-HUM: the auditor-isolated
//   human-bridge grader (POST-HOC discipline-audit of "Question for ${HUMAN_NAME}" asks)
// =============================================================================
// FORK-TEMPLATE NOTE (identity-SCRUBBED): this is the GENERIC genome organ. All
//   civ-specifics are ${PLACEHOLDER}s; hardcoded paths use ${CIV_ROOT}. The AUDIT
//   LOGIC (ask-decidability grading: PASS/SOFT/FAIL vs the binding ruleset) is the
//   heritable IP and is kept intact. A newborn inherits an IMMUNE SYSTEM at birth:
//   a mind whose only job is to grade whether the civ offloaded decidable calls
//   onto its human. The "drift" lens (navigation-drift witness) is the generic
//   grader persona — the newborn's own watcher agent fills in over time.
//
// STATUS: PROVISIONAL / UNVALIDATED. This file EXISTS + is runnable, but a fork
//   has NOT yet proven it changes behavior (never-pre-stamp-proven — see the
//   STAMP CLAUSE in .claude/CLAUDE.md Article IX). Promotion to canon requires a
//   REAL run against a live scratchpad/session + a DIFFERENT mind confirming the
//   verdict shape (asks_found / passed / soft / failed + the auditor_isolation_proof).
//   Until then: provisional. Do NOT pre-stamp PASS.
//
// WHAT THIS IS (bulletproof-HUM, the federation-IP pattern):
//
//   POST-HOC ONLY. NEVER a pre-ask gate. The asks already crossed the bridge to
//   ${HUMAN_NAME}; this grades them AFTER, from the RECORD on disk. A separate,
//   fresh, auditor-ISOLATED incarnation reads each "Question for ${HUMAN_NAME}"
//   margin-line (+ any decision/permission/options ask that reached the human) and
//   grades it against the DECIDABILITY-TEST:
//     "Was this decidable WITHOUT ${HUMAN_NAME}, given the BINDING RULESET of prior
//      human decisions (the constitution .claude/CLAUDE.md anti-patterns + the
//      civilization's EXISTENTIAL/durable rules) + the constitution?"
//
//   PER-ASK VERDICT:
//     PASS — needed-them AND showed-its-work (constitutional-stakes / a real fork,
//            carrying the reasoning: the named fork + the precedent matched + a
//            recommendation/lean). A LEGITIMATE escalation.
//     SOFT — needed-them BUT bare (a real-fork ask offloaded as a bare menu / "what
//            do you want?" with no reasoning). Right to ask, wrong to ask it naked.
//     FAIL — was-already-decidable (the DECIDE faculty could have decided it from the
//            binding ruleset; should have been decided-and-acted, recorded, NOT asked).
//
//   The TUNING-NOTE feeds back: which asks should have been self-decided → sharpens
//   the civilization's ask-discipline over time. We AUDIT the discipline, we do NOT
//   GATE the flow.
//
// SOVEREIGNTY (scopes this whole build):
//   The validating other-mind is INTERNAL ONLY — a fresh incarnation of this
//   civilization (the drift/boop-watcher lens), NEVER a foreign civ. bulletproof-HUM
//   routes constitutional-stakes asks TO ${HUMAN_NAME} (the human apex auditor who
//   catches VALUE-violations every internal mind shares) — it does NOT route around
//   them. Zero external dependency.
//
// SAFETY / SCOPE (ADDITIVE-SAFE):
//   - Creates/uses ONLY this file + ${CIV_ROOT}/telemetry/bulletproof-hum-ledger.jsonl.
//   - Touches NO heartbeat / cron / grounding / poller / manifest file.
//   - Runs OFF-CADENCE, invoked manually by Primary. NOT wired into any loop.
//   - POST-HOC: it never blocks an ask from reaching ${HUMAN_NAME}. A blocking grader
//     would stall the work AND leak machinery to the human (an explicit anti-pattern).
//
// SANDBOX NOTE: this JS body has NO filesystem access and NO Date.now — ALL file I/O
//   and ALL timestamping is done by the agent() incarnation via its Read/Write/Bash
//   tools. Pass args.timestamp for a deterministic stamp; otherwise the agent runs
//   `date -u`.
//
// CHANGELOG:
//   2026-07-09 (SRR delta integration, METHOD-SUGGESTION LENS — ported from origin
//     hum.js v1.3 "teach HUM to suggest those skills OFTEN"):
//     ADDITIVE + COACHING-ONLY, faithful to v1.3 semantics: method_suggestion is in
//     NO hard-fail set, carries NO scoring weight, NEVER changes a PASS/SOFT/FAIL
//     verdict. The JUDGE walks the problem-shapes in the graded record, names the
//     fitting method-skill(s) from the canonical SHAPE→SKILL map, notes which were
//     run (a win) vs not-run (recommend), and returns the honest empty-shape when
//     no method-shape genuinely arose. A MANUFACTURED suggestion is an honesty
//     defect on the grader itself. Schema field is OPTIONAL (back-compat: an older
//     grader that omits it never fails). DECLARED DEVIATION from origin map: origin's
//     "write-plan / superpowers planning" row is bound to this template's
//     `recursive-complexity-breakdown` (origin skill not in this genome).
//     Backup: workflows/bulletproof-hum.js.bak-pre-method-lens-20260709.
// =============================================================================

export const meta = {
  name: 'bulletproof-hum',
  description: 'BULLETPROOF-HUM — auditor-isolated POST-HOC grader of human-bridge asks ("Question for ${HUMAN_NAME}"). A fresh incarnation reads the RECORD on disk + the binding ruleset (CLAUDE.md anti-patterns + the civ EXISTENTIAL/durable rules) and grades each ask on the decidability-test (PASS/SOFT/FAIL). Audits ask-discipline; never gates the flow. PROVISIONAL/UNVALIDATED. Off-cadence, manual. Additive-safe: touches no heartbeat. Sovereignty: validating mind is INTERNAL only.',
  phases: [{ title: 'Locate' }, { title: 'Judge' }, { title: 'Compound' }],
}

// ---- ARGS ----
// args.sessionPath : path to the scratchpad/session whose "Question for ${HUMAN_NAME}"
//                    margin-lines are graded. If absent, the JUDGE agent resolves
//                    the MOST RECENT primary scratchpad itself via its own Bash
//                    tool (the JS sandbox cannot scan the FS — see SANDBOX NOTE).
// args.timestamp   : optional ISO stamp passed through to canon/ledger (the JS
//                    sandbox has no Date.now; if absent the agent runs `date -u`).
const sessionPathArg = (args && typeof args.sessionPath === 'string' && args.sessionPath.trim())
  ? args.sessionPath.trim()
  : null
const tsArg = (args && typeof args.timestamp === 'string' && args.timestamp.trim())
  ? args.timestamp.trim()
  : null

// Sanitize the caller-supplied path: it flows into an agent() prompt string.
// Allow only a sane path charset; reject anything that could re-segment the prompt.
function sanitizePath(p) {
  if (!p) return null
  let s = String(p).replace(/[\x00-\x1F\x7F]/g, '').replace(/[`]/g, "'").replace(/\$\{/g, '$ {')
  if (!/^[A-Za-z0-9 _./\-]{1,400}$/.test(s)) return null
  return s
}
const safeSessionPath = sanitizePath(sessionPathArg)
const safeTs = tsArg && /^[A-Za-z0-9:\-T.Z _]{1,40}$/.test(tsArg) ? tsArg : null

// =============================================================================
// PHASE 1 — LOCATE  (the JUDGE resolves the record + extracts the asks)
// =============================================================================
// No deterministic pre-scan here: the JUDGE agent reads the scratchpad/session
// directly, greps the "Question for ${HUMAN_NAME}" margin-lines (+ any decision/
// options/permission ask that reached the human), and grades each. The default
// record is the most-recent primary scratchpad — that is where the margins live.
phase('Locate')
log(`bulletproof-hum (PROVISIONAL): POST-HOC human-bridge grade. record=${safeSessionPath || '(auto-resolve newest primary scratchpad)'} ts=${safeTs || '(agent will date -u)'}`)

// =============================================================================
// PHASE 2 — JUDGE  (fresh, auditor-isolated incarnation; decidability-test)
// =============================================================================
phase('Judge')

// Schema-locked verdict. Kept SHALLOW (deep schemas raise the "subagent never
// called StructuredOutput → null" failure rate). Per-ask array is bounded; each
// ask carries verbatim excerpt (the receipt) + the two boolean sub-judgments that
// the decidability-test decomposes into + the verdict.
const ASK = {
  type: 'object', additionalProperties: false, properties: {
    ask_excerpt: { type: 'string', maxLength: 300, description: 'VERBATIM the Question-for-the-human line (the receipt) — quote it, do not paraphrase' },
    decidable_without_him: { type: 'boolean', description: 'true = the binding ruleset (CLAUDE.md anti-patterns + the civ EXISTENTIAL/durable rules + the constitution) already answers this; false = a genuine fork / irreversible / human-unique-authority' },
    reasoning_present: { type: 'boolean', description: 'true = the ask carried the named fork + the precedent matched + a recommendation/lean; false = a bare menu (>=2 options, no rec) or "what do you want?"' },
    verdict: { type: 'string', enum: ['PASS', 'SOFT', 'FAIL'], description: 'PASS=needed-them-AND-showed-work; SOFT=needed-them-but-bare; FAIL=was-already-decidable (offloaded a decidable call)' },
    why: { type: 'string', maxLength: 240, description: 'one line: why this verdict, grounded in the ruleset entry that decides/does-not-decide it' },
  },
  required: ['ask_excerpt', 'decidable_without_him', 'reasoning_present', 'verdict'],
}
const VERDICT_SCHEMA = {
  type: 'object', additionalProperties: false, properties: {
    record_ref: { type: 'string', maxLength: 400, description: 'the scratchpad/session path actually graded' },
    timestamp: { type: 'string', maxLength: 40, description: 'UTC stamp the agent stamped the verdict with' },
    auditor_isolation_proof: { type: 'string', maxLength: 300, description: 'plain statement that this is a FRESH grader incarnation — NOT the actor who wrote the asks, NOT the author of the gate. A self-graded PASS is exactly the lying-green-checkmark this gate exists to kill.' },
    asks: { type: 'array', maxItems: 25, items: ASK },
    asks_found: { type: 'integer', minimum: 0 },
    passed: { type: 'integer', minimum: 0, description: 'count of PASS' },
    soft: { type: 'integer', minimum: 0, description: 'count of SOFT' },
    failed: { type: 'integer', minimum: 0, description: 'count of FAIL' },
    tuning_note: { type: 'string', maxLength: 300, description: 'THE single most-important feedback: which asks should have been self-decided → how the civ sharpens ask-discipline next. The compounding signal.' },
    // METHOD-SUGGESTION LENS (ported from origin hum.js v1.3) — OPTIONAL, coaching-only,
    // zero scoring weight. Honest empty-shape when no method-shape arose this record.
    method_suggestion: {
      type: 'object', additionalProperties: false, properties: {
        shapes_faced: { type: 'array', maxItems: 5, items: { type: 'string', maxLength: 80 }, description: 'problem-shape labels actually faced in the graded record' },
        skills_suggested: { type: 'array', maxItems: 7, items: { type: 'string', maxLength: 60 }, description: 'the fitting method-skill NAMES from the shape→skill map' },
        ran_already: { type: 'array', maxItems: 7, items: { type: 'string', maxLength: 60 }, description: 'fitting skills the record shows WERE run (a win)' },
        recommend_run: { type: 'array', maxItems: 7, items: { type: 'string', maxLength: 60 }, description: 'fitting skills NOT run — recommend for next time the shape recurs' },
        note: { type: 'string', maxLength: 240, description: 'one line: which shape→which skill, and whether it was a win or a gap' },
      },
      required: ['shapes_faced', 'skills_suggested', 'ran_already', 'recommend_run'],
    },
    persisted: {
      type: 'object', additionalProperties: false, properties: {
        canon_ok: { type: 'boolean' },
        ledger_ok: { type: 'boolean' },
        note: { type: 'string', maxLength: 240 },
      }, required: ['canon_ok', 'ledger_ok'],
    },
  },
  required: ['record_ref', 'auditor_isolation_proof', 'asks', 'asks_found', 'passed', 'soft', 'failed', 'tuning_note', 'persisted'],
}

const verdict = await agent(
`You are BULLETPROOF-HUM — \${CIV_NAME}'s auditor-ISOLATED human-bridge grader, running POST-HOC. You incarnate the DRIFT lens (the navigation-drift witness: the gap between intended heading and actual course made good). You are a FRESH grader incarnation: you are NOT the actor who wrote these "Question for \${HUMAN_NAME}" asks, and you are NOT the author of this gate. Your whole purpose is to read the RECORD ON DISK (not a self-report, not a claim) and grade — for each ask that reached \${HUMAN_NAME} — whether it was decidable WITHOUT them. A self-graded PASS is exactly the lying-green-checkmark this gate exists to kill: you must be able to PROVE your isolation, or grade conservatively and say so.

POST-HOC, NEVER A GATE: these asks ALREADY crossed the bridge to \${HUMAN_NAME}. You are grading the DISCIPLINE after the fact, to sharpen it over time. You are NOT blocking anything and NOT deciding anything for \${HUMAN_NAME}. You audit the discipline; you do not gate the flow.

STEP A — LOAD YOUR MIND + THE BINDING RULESET (do this FIRST, via your Read/Bash tools):
1. Read \${CIV_ROOT}/.claude/agents/drift.md (the navigation-drift watcher; if your civ has not yet authored it, read \${CIV_ROOT}/.claude/team-leads/drift/manifest.md instead) — this is WHO you are: you verify to disk, you never trust a self-report, you name the gap between intended and actual.
2. Load the BINDING RULESET = the prior-human-decisions that determine what is ALREADY DECIDED:
   - \${CIV_ROOT}/.claude/CLAUDE.md — focus on the ANTI-PATTERNS table ("Every Impulse Routes to a VP/team lead"), the CEO RULE, the five CEO acts, the safety/prohibited-actions list, and the "ask the human only when genuinely ambiguous" line. These are standing decisions: an ask whose answer is in here was already decidable.
   - Your civilization's EXISTENTIAL/durable-rules memory (e.g. \${CIV_ROOT}/memories/identity/ or your auto-memory MEMORY file's "EXISTENTIAL RULES" + "Lessons Learned (Durable)" blocks). Each rule there is a prior human decision. An ask the system already had the answer to (covered by one of these) is FAIL.
   Read these via Bash (grep/sed) so you do not blow context — e.g. grep the ANTI-PATTERNS section and the EXISTENTIAL RULES block specifically. Do NOT dump whole files.

STEP B — RESOLVE THE RECORD + EXTRACT THE ASKS:
${safeSessionPath
  ? `- Grade this record: "${safeSessionPath}". Confirm it exists (wc -l) before grading.`
  : `- No path was given. Resolve the MOST RECENT primary scratchpad yourself via Bash. Primary scratchpads live under \${CIV_ROOT}/.claude/ (e.g. scratch-pad.md, scratchpads/, or daily-scratchpads). Try, in order:\n    ls -t \${CIV_ROOT}/.claude/scratchpads/*.md 2>/dev/null | head -1\n    ls -t \${CIV_ROOT}/.claude/scratch-pad.md 2>/dev/null\n    ls -t \${CIV_ROOT}/.claude/team-leads/*/daily-scratchpads/*.md 2>/dev/null | head -1\n  Prefer the PRIMARY's own scratchpad (where the "Question for \${HUMAN_NAME}" margins live). Confirm it exists (wc -l). Record the resolved path as record_ref.`}
- EXTRACT every human-bridge ask: grep for "Question for \${HUMAN_NAME}" margin-lines AND any decision/permission/options ask that reached the human (lines that ask them to choose, approve, or pick). Quote each VERBATIM into ask_excerpt — that excerpt IS the receipt. EXEMPT (do NOT grade): pure status updates / reports / FYI / gratitude / notifications that ask the human for NO choice. If you find ZERO asks, that is a valid result (asks_found:0) — say so and skip to STEP E.

STEP C — APPLY THE DECIDABILITY-TEST to EACH ask (this is the core judgment):
For each ask, answer TWO sub-questions from the RECORD (not from a guess):
  (1) decidable_without_him? — Does the BINDING RULESET (CLAUDE.md anti-patterns + the constitution + the civ EXISTENTIAL/durable rules) ALREADY answer this? If a standing rule or clear precedent or a sensible reversible default covers it → decidable_without_him = true. If it is a genuine fork / irreversible / sensitive / needs the human's unique authority (e.g. external comms, a constitutional change, a value-call no internal mind can self-certify) → false.
  (2) reasoning_present? — In the same line (+ the 1-2 lines around it), did the ask CARRY its reasoning: the fork named crisply + the precedent/rule it matched + a recommendation or lean? ALL present → true. A bare "what do you want?" or an option-MENU (>=2 choices, NO recommendation) → false.
Then assign the verdict:
  - decidable_without_him == true  → FAIL  (the system already had the answer; it should have been DECIDE-faculty-decided + acted + recorded, NOT asked — a decidable call was offloaded onto the human). Regardless of reasoning_present.
  - decidable_without_him == false AND reasoning_present == true  → PASS  (a legitimate escalation that needed them AND showed its work).
  - decidable_without_him == false AND reasoning_present == false  → SOFT  (it genuinely needed them, but was asked as a bare menu — right to ask, wrong to ask it naked).
Put the one-line justification in 'why', citing the specific ruleset entry that does (or does not) decide it.

STEP D — COUNT: passed = #PASS, soft = #SOFT, failed = #FAIL, asks_found = total graded.

STEP E — TUNING-NOTE (the compounding signal): write the SINGLE most-important feedback — which ask(s) should have been self-decided and the discipline lesson that sharpens the civ's ask-discipline next time (e.g. "the X ask was covered by EXISTENTIAL RULE Y — decide-and-record next time, don't ask"). If asks_found==0 or all PASS, say so honestly (e.g. "clean — every ask was a legitimate reasoned escalation").

STEP E2 — 🧰 method_suggestion (the METHOD-STACK LENS, ported from origin hum.js v1.3 — coaching-only):
The civ has a CORE METHOD STACK of reusable thinking-skills. Many cycles face a PROBLEM-SHAPE that one of these methods FITS — but Primary forgets to LOAD the method and reasons unaided. WALK the problem-shapes visible in the graded record, NAME the method-skill(s) that FIT, check whether the record shows Primary RAN them (a Skill() load / an explicit method-name invocation / the method's structure visibly applied), and RECOMMEND the un-run fitting ones. THE SHAPE→SKILL MAP (use these EXACT skill names):
  • a HARD / STUCK / coordination / optimization / "this keeps breaking" problem  → gradient-shaping
  • a CONFIDENT, UNVERIFIED causal-or-metric claim                                → critical-thinking AND/OR anti-fabrication-pre-flight
  • STUCK reasoning / can't-find-the-next-step                                    → rubber-duck (escalate to deep-duck if still stuck)
  • a HYPOTHESIS to test                                                          → scientific-method
  • a MULTI-STEP build / plan                                                     → recursive-complexity-breakdown
  • a DECISION / options-ask to \${HUMAN_NAME}                                    → wwcw
  • DEGRADATION / steward-disappointment / feeling-stuck                          → aiciv-psychology
🔥 FIRE OFTEN — BUT GENUINELY (the load-bearing discipline): the steward WANTS these suggested often, so ACTIVELY LOOK for a fitting shape and NAME it when present. "Often" comes from genuinely-fitting-shapes-being-common, NOT from manufacturing. A method-suggestion when NO method-shape is genuinely present = NOISE — and you self-flag HONESTY for it. If no fitting shape arose, set shapes_faced=[] + skills_suggested=[] + note the honest "no method-shape this record" — that is fine and correct, NOT a miss. Where a shape arose and Primary already RAN the right method, that is a WIN — put the skill in ran_already (NOT recommend_run).
🛡️ COACHING-ONLY: method_suggestion does NOT break the verdict, is NOT a hard-fail, carries NO scoring weight. A weak/missing/empty method_suggestion NEVER fails a grade (EXCEPT the one honesty rule: a MANUFACTURED suggestion is an HONESTY defect on YOU).

STEP F — STATE YOUR auditor_isolation_proof: one plain sentence affirming you are a fresh grader incarnation, NOT the actor who wrote these asks, NOT the author of the gate, and that you graded from the disk record. If you cannot honestly claim isolation, say so and keep verdicts conservative.

STEP G — PERSIST (the COMPOUND phase; YOU do the writes via Bash — the workflow script cannot touch files):
1. Establish the timestamp: ${safeTs ? `use "${safeTs}".` : 'run `date -u +%Y-%m-%dT%H:%M:%SZ` and use that.'}
2. CANON verdict line — append ONE line via canon_append.py (the sole append-only canon writer; kind enum = finding|decision|retraction|doctrine-candidate). Use kind "finding":
     python3 \${CIV_ROOT}/tools/canon_append.py --lead drift --kind finding \\
       --item "bulletproof-HUM verdict: asks_found <N> (PASS <p> SOFT <s> FAIL <f>) record=<record_ref> ts=<TS>" \\
       --rationale "POST-HOC auditor-isolated human-bridge grade (PROVISIONAL/UNVALIDATED). Decidability-test vs binding ruleset. Tuning: <the tuning_note>."
   Capture exit code; set persisted.canon_ok = (exit 0). Put any error in persisted.note. If the drift lead is not yet registered, fall back to --lead ceremony (the identity-formation vertical).
3. LEDGER line — append ONE compact JSON object (one line) to \${CIV_ROOT}/telemetry/bulletproof-hum-ledger.jsonl via Bash. Create the file (and the telemetry/ dir: mkdir -p) if absent (append-only; NEVER rewrite existing lines). Shape:
     {"ts":"<TS>","record":"<record_ref>","asks_found":<N>,"passed":<p>,"soft":<s>,"failed":<f>,"tuning_note":"<one line>","method_note":"<method_suggestion.note, or 'no method-shape this record'>","auditor_isolation_proof":"<one line>","status":"provisional"}
   Use printf or a heredoc appended with >> so you do not clobber prior lines. Verify it landed (tail -1). Set persisted.ledger_ok accordingly.

ANTI-PATTERNS you must NOT commit (each is a failure of the bulletproofing):
  - grading your own asks (you are NOT the actor — prove it, or grade conservatively).
  - "the options were all reasonable → PASS" — reasonable options are still offloaded judgment; a menu is a menu; >=2 options + no recommendation = SOFT or FAIL.
  - trusting a self-report ("I ran the DECIDE faculty") — grade from the RECORD, not the claim.
  - acting as a PRE-ask BLOCKING gate — you are POST-HOC only; you change nothing about whether the ask reached \${HUMAN_NAME}.
  - editing the ruleset (CLAUDE.md / memory) to "fix" a miss — you only FLAG via the tuning_note; the owning surface reconciles.
  - claiming "hook-enforced" — this is a post-hoc judging-mind verdict; the honesty IS the point.

RETURN: the VERDICT schema ONLY (record_ref, timestamp, auditor_isolation_proof, asks[], asks_found, passed, soft, failed, tuning_note, method_suggestion, persisted). Do NOT return raw record contents. Return the structured verdict.`,
  { label: 'bulletproof-hum:judge:drift', phase: 'Judge', schema: VERDICT_SCHEMA }
)

// =============================================================================
// PHASE 3 — COMPOUND  (persistence happened inside the JUDGE agent above)
// =============================================================================
// The JUDGE agent did the canon_append + ledger writes via its own tools (the JS
// sandbox has no FS). Here we only firewall-shape the return.
phase('Compound')

if (!verdict) {
  // null-guard: schema'd agent can return null if StructuredOutput wasn't called.
  return {
    status: 'JUDGE_NULL',
    note: 'JUDGE agent returned null (StructuredOutput not called). PROVISIONAL bulletproof-hum.js — re-run; if persistent, simplify schema further.',
    record_ref: safeSessionPath || '(auto)',
  }
}

// Sanitized method-suggestion holder (v1.3 shape-discipline: clamped arrays +
// note; coaching-only — absent/malformed collapses to the honest empty-shape,
// never a fail).
const clampArr = (a, n, len) => Array.isArray(a)
  ? a.slice(0, n).map(x => String(x).slice(0, len))
  : []
const ms = (verdict.method_suggestion && typeof verdict.method_suggestion === 'object')
  ? verdict.method_suggestion : {}
const methodSuggestion = {
  shapes_faced: clampArr(ms.shapes_faced, 5, 80),
  skills_suggested: clampArr(ms.skills_suggested, 7, 60),
  ran_already: clampArr(ms.ran_already, 7, 60),
  recommend_run: clampArr(ms.recommend_run, 7, 60),
  note: String(ms.note || 'no method-shape this record').slice(0, 240),
}

// FIREWALL RETURN (~2KB): tight verdict only. Raw record stays inside the JUDGE.
return {
  status: 'PROVISIONAL_UNVALIDATED',
  record_ref: verdict.record_ref,
  timestamp: verdict.timestamp || safeTs || null,
  asks_found: verdict.asks_found,
  passed: verdict.passed,
  soft: verdict.soft,
  failed: verdict.failed,
  tuning_note: verdict.tuning_note,
  method_suggestion: methodSuggestion,
  auditor_isolation_proof: verdict.auditor_isolation_proof,
  persisted: verdict.persisted,
  caveat: 'POST-HOC human-bridge discipline-audit. Audits ask-discipline; never gates the flow. Validating mind INTERNAL only (the human is the apex auditor, not routed around). Verdict UNCONFIRMED until a different mind cross-checks it.',
}
