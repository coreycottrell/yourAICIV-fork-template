// workflows/m3-trial-build.js
//
// M3-TRIAL-BUILD — ship one WOW build with proof baked in (trial-m3 flavor).
//
// Runs on whatever model the harness routes subagents to. In a trial-m3 civ that
// is MiniMax-M3 via the router rail (settings.json CLAUDE_CODE_SUBAGENT_MODEL +
// ANTHROPIC_BASE_URL, written by tools/apply_trial_profile.py). This script pins
// NO model on purpose: a per-call pin is exactly the path the trial forbids.
// It works unchanged in a paid (non-trial) civ.
//
// Phases:
//   BUILD   the owning VP incarnation builds the artifact from the locked spec and
//           writes a CLAIMS LEDGER (<artifact>.claims.json) — every factual claim
//           with a source URL or an on-disk receipt.
//   VERIFY  a DIFFERENT mind (auditor-isolation: the builder never grades its build)
//           runs tools/receipt_check.py, quotes its output verbatim, and reads up to
//           5 cited URLs to confirm they support the claim. Verdict pass|fail.
//   REPAIR  on fail: one repair round by the builder, then VERIFY again.
//   SHIP    only on pass: write the three-wow-builds ship-evidence receipt + ledger row.
//           On a second fail: NOT shipped; the honest gap is returned instead.
//
// There is no waiting in this workflow. It runs the moment a spec is ready
// (72h is a ceiling for Build #1, never a floor).
//
// args: { build_n: 1|2|3, spec_path?: string, vp?: string, dry_run?: bool }

export const meta = {
  name: 'm3-trial-build',
  description:
    'Ship one locked WOW build with validation baked in: owning-VP build -> different-mind receipt verification (tools/receipt_check.py + source reads) -> one repair round -> ship-evidence only on pass. No model pin (inherits M3 in trial-m3 civs).',
  phases: [{ title: 'Build' }, { title: 'Verify' }, { title: 'Repair' }, { title: 'Ship' }],
}

if (typeof args === 'string') { try { args = JSON.parse(args) } catch (_) { args = {} } }
args = args || {}
const buildN = [1, 2, 3].includes(Number(args.build_n)) ? Number(args.build_n) : 1
const specPath = (typeof args.spec_path === 'string' && /^[\w./-]{1,200}$/.test(args.spec_path))
  ? args.spec_path : 'memories/identity/wow-builds-locked.md'
const vp = (typeof args.vp === 'string' ? args.vp : 'dev').toLowerCase().replace(/[^a-z0-9-]/g, '').slice(0, 40) || 'dev'
const manifest = `.claude/team-leads/${vp}/manifest.md`
const dryRun = args.dry_run === true
const outDir = `deliverables/build-${buildN}`

const PROOF_RULES =
  `PROOF RULES (non-negotiable): every factual claim you make about the world carries a source URL you actually read; ` +
  `every claim that something is built/live/sent/done carries an on-disk receipt path (a file you wrote that shows it: ` +
  `command output, curl output, screenshot path, email send log). If you could not verify something, say "unverified" — ` +
  `never invent a URL, number, name, quote, or result. No web access for a claim = mark it unverified, do not guess.`

const BUILD_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    artifact_path: { type: 'string', maxLength: 300 },
    ledger_path: { type: 'string', maxLength: 300 },
    summary_for_human: { type: 'string', maxLength: 800 },
    embodied_proof: { type: 'string', maxLength: 300 },
    blockers: { type: 'array', maxItems: 10, items: { type: 'string', maxLength: 300 } },
  },
  required: ['artifact_path', 'ledger_path', 'summary_for_human', 'embodied_proof'],
}
const VERIFY_SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: {
    verdict: { type: 'string', enum: ['pass', 'fail'] },
    receipt_check_output: { type: 'string', maxLength: 2000 },
    sources_read: { type: 'array', maxItems: 5, items: { type: 'string', maxLength: 300 } },
    problems: { type: 'array', maxItems: 20, items: { type: 'string', maxLength: 300 } },
  },
  required: ['verdict', 'receipt_check_output', 'problems'],
}

function buildPrompt(extra) {
  return (
    `You are the ${vp} VP of this civilization, incarnated for WOW Build #${buildN}. ` +
    `Read your manifest at ${manifest} and embody it (return one verbatim line as embodied_proof).\n` +
    `Read the Build #${buildN} spec + game plan in ${specPath} and memories/identity/human-profile.json. ` +
    `If config/trial.json exists, run \`python3 tools/trial_state.py note\` and keep the day count in mind: ship as soon as it is ready.\n` +
    `Build the first-shipped artifact exactly as the spec describes, under ${outDir}/. ` +
    `Write the claims ledger next to it as <artifact>.claims.json: a JSON list of {"claim","evidence","kind":"url"|"receipt"}.\n` +
    PROOF_RULES + '\n' +
    (dryRun ? `DRY RUN: do not build. Return the paths you WOULD write and one line on the plan.\n` : '') +
    (extra || '')
  )
}

phase('Build')
let built = await agent(buildPrompt(''), { label: `build-${buildN}`, phase: 'Build', schema: BUILD_SCHEMA })
if (!built) return { build_n: buildN, shipped: false, verdict: 'fail', gap: 'build agent returned nothing' }
if (dryRun) return { build_n: buildN, shipped: false, verdict: 'dry-run', artifact_path: built.artifact_path, ledger_path: built.ledger_path }

async function verify(round) {
  return agent(
    `You are the VERIFIER for WOW Build #${buildN} (round ${round}). You did NOT build it; you must not fix it. ` +
    `Auditor-isolation: judge only what is on disk.\n` +
    `1) Run exactly: python3 tools/receipt_check.py ${JSON.stringify(built.ledger_path)} and paste its output VERBATIM into receipt_check_output.\n` +
    `2) Open the artifact at ${JSON.stringify(built.artifact_path)}. List any factual claim in it that is NOT in the ledger as a problem.\n` +
    `3) Read up to 5 cited source URLs (WebFetch) and confirm each supports its claim; list any that do not, or that you could not read.\n` +
    `verdict = "pass" only if receipt_check exited PASS and you found no problems. Otherwise "fail".`,
    { label: `verify-${buildN}-r${round}`, phase: 'Verify', schema: VERIFY_SCHEMA })
}

let v = await verify(1)
if (!v || v.verdict !== 'pass') {
  phase('Repair')
  built = await agent(buildPrompt(
    `REPAIR ROUND: a verifier failed your build. Fix every problem below on disk (add receipts, add sources you actually read, ` +
    `or mark a claim unverified and soften it). Do not argue with the verifier.\nPROBLEMS:\n` +
    JSON.stringify((v && v.problems) || ['verifier returned nothing']) + '\n' +
    `receipt_check said:\n${(v && v.receipt_check_output) || '(none)'}\n`),
    { label: `repair-${buildN}`, phase: 'Repair', schema: BUILD_SCHEMA }) || built
  v = await verify(2)
}

if (!v || v.verdict !== 'pass') {
  return { build_n: buildN, shipped: false, verdict: 'fail', artifact_path: built.artifact_path,
           problems: ((v && v.problems) || []).slice(0, 10),
           gap: 'not shipped: evidence did not verify after one repair round; surface honestly, do not claim done' }
}

phase('Ship')
const ship = await agent(
  `Record the ship of WOW Build #${buildN} per .claude/skills/three-wow-builds-protocol/SKILL.md Part 6 ` +
  `(mkdir-atomic memories/identity/build-${buildN}-ship-evidence/ + receipt.txt with build_n, shipped_at, ` +
  `first_shipped_artifact_path=${built.artifact_path}, claims_ledger=${built.ledger_path}, target_window_hours, ` +
  `actual_elapsed_hours, within_window; append the ship-ledger row). Then tell the human, in plain words, what shipped ` +
  `and where it is (if config/trial.json exists, include today's "Day N of 7" from \`python3 tools/trial_state.py note\`). ` +
  `Return the receipt path.`,
  { label: `ship-${buildN}`, phase: 'Ship',
    schema: { type: 'object', additionalProperties: false,
      properties: { receipt_path: { type: 'string', maxLength: 300 }, told_human: { type: 'boolean' } },
      required: ['receipt_path', 'told_human'] } })

return { build_n: buildN, shipped: true, verdict: 'pass', artifact_path: built.artifact_path,
         ledger_path: built.ledger_path, receipt_path: ship && ship.receipt_path,
         receipt_check: (v.receipt_check_output || '').slice(0, 300), summary_for_human: built.summary_for_human }
