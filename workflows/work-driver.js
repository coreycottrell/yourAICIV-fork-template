// workflows/work-driver.js
//
// WORK-DRIVER — the drive-not-report boop. GENERIC STUB.
//
// UNPROVEN-BUT-EXCITING. Born in origin-civ 2026-07-02 as a 792-line workflow
// with civ-specific manifest paths. This stub carries the SHAPE + doctrine +
// return contract. Wire the placeholders (MANIFESTS + STEWARD_ID) to your own
// civ's substrate before firing.
//
// TEMPLATE STATE (aiciv-fork-template, 2026-07-09): UNARMED by default — no
// cron/AgentCal event fires this. Board/feed/audit paths are wired to this
// template's real Wave-1 organs (PROJECT-BOARD.md + data/reports +
// data/audits/workflow_returns + arc/). MANIFESTS seeds the one runnable
// example lead; a born civ fills it from its composition.yaml roster and sets
// STEWARD_ID to its human's lowercase name, THEN arms a schedule consciously.
// K=0 everywhere (origin had not fired it for real at teach time). Honest.
//
// The problem: grounding surfaces "here are 5 needed actions" then hands them
// back to Primary, who often lists them and moves on. The board fills with
// "board says X but reality is Y" rows. Doctrine ("get it moving; no
// reviewed-looks-fine exit") is not enforceable through a skill alone —
// there has to be an organ that PICKS a stalled project and MAKES A MOVE.
//
// This workflow IS that organ. Five phases, ~4 minutes end-to-end:
//   SCAN   ~40s   read PROJECT-BOARD §0 rows verbatim + arc/ARC-NOW 24h
//   PICK   ~15s   score every row = staleness(cap 168h) + board-lag * 0.5
//   ABSORB ~60s   read the picked project's MISSION + OPS + DEVLOG tail-40
//   DRIVE  ~90s   incarnate the OWNING VP through the manifest and MAKE ONE
//                 CONCRETE MOVE. ZERO-LAUNCH = firewall FAIL.
//   RECORD ~30s   append DEVLOG + whats_next verbatim + arc events
//
// Owner in origin civ: fleet-lead (skill + scheduler + workflow substrate).
// Sibling doctrines: .claude/skills/work-driver/SKILL.md
//                    docs/whats-next-contract.md (the §26 return shape)
//
// STUB DELTA vs origin-civ: MANIFESTS points at PLACEHOLDER paths; the origin
// civ's real file is 792 lines with a fall-to-frontier fallback + full JS ISO
// parser. This stub keeps the shape lean so a fork can read the flow, then
// wire the paths + extend the fallback per their own frontier organ.

export const meta = {
  name: 'work-driver',
  description:
    'Scan the PROJECT-BOARD, pick the most stalled project (score = staleness + board-lag x0.5), absorb its MISSION/OPS/DEVLOG + arc thread, then incarnate the owning VP and MAKE ONE CONCRETE MOVE. Zero-launch DRIVE phase = firewall FAIL. Records the move + whats_next verbatim.',
  phases: [
    { title: 'Scan' },
    { title: 'Pick' },
    { title: 'Absorb' },
    { title: 'Drive' },
    { title: 'Record' },
  ],
}

// ---------------------------------------------------------------------------
// §20-style defensive args parse (workflows-master pattern from origin civ)
// ---------------------------------------------------------------------------
if (typeof args === 'string') { try { args = JSON.parse(args) } catch (_) {} }
const isDryRun = !!(args && args.dry_run === true)
const biasVertical = (args && typeof args.bias_vertical === 'string')
  ? args.bias_vertical.toLowerCase().replace(/[^a-z0-9_\-]/g, '').slice(0, 40)
  : ''

// ---------------------------------------------------------------------------
// FORK-WIRING SEAM — replace these paths with your civ's actual VP manifests.
// The origin civ's roster has 17 VPs. Yours will differ. The KEY is a stable
// short name that shows up in the board's `owner` column (e.g. "mind-lead" ->
// "mind"). The VALUE is the manifest path your forkable-mind primitive loads.
// ---------------------------------------------------------------------------
const MANIFESTS = {
  // Seeded with this template's ONE runnable example (same seam as coo.js).
  // A born civ REPLACES/EXTENDS this from its composition.yaml roster:
  'example': 'team-leads/example-lead/manifest.md',
  // 'research':       '.claude/team-leads/research/manifest.md',
  // 'infrastructure': '.claude/team-leads/infrastructure/manifest.md',
  // ... etc
}

// FORK-WIRING SEAM — replace with your civ's PROJECT-BOARD path + audit dir.
const PROJECT_BOARD_PATH = 'PROJECT-BOARD.md'                           // §0 sentinels live here
const WHATS_NEXT_FEED = 'data/reports/whats-next-feed.jsonl'            // transport ledger
const AUDIT_SHARD_DIR = 'data/audits/workflow_returns'                  // firewall-return archive
const ARC_LIVE_JSONL = 'arc/live.jsonl'                                 // medium-term memory feed

// ---------------------------------------------------------------------------
// PHASE 1 — SCAN
// ---------------------------------------------------------------------------
phase('Scan')

const scanResult = await agent(
  [
    'You are the WORK-DRIVER SCAN agent. Read TWO artifacts and return their',
    'structured content. Use Bash + Read only.',
    '',
    `STEP 1 — Extract PROJECT-BOARD §0 rows from ${PROJECT_BOARD_PATH}.`,
    '  awk to grab lines between the sentinels:',
    '    <!-- PROJECT-BOARD:GENERATED §0 — ... — BEGIN -->',
    '    <!-- PROJECT-BOARD:GENERATED §0 — END -->',
    '  Then find every markdown table row starting with `| **` (project rows).',
    '  For each row parse the 7 columns: Project | Phase | % | Next Move | Blocked | Owner | Last Fire',
    '',
    'STEP 2 — Read arc/ARC-NOW.md. Return the RECENT WINDOW section (last 24h) VERBATIM (up to 3KB).',
    '  Also extract the LAST-GENERATED timestamp from the PROJECT-BOARD §0 header.',
    '',
    `STEP 3 — Also stat ${WHATS_NEXT_FEED} (mtime as ISO).`,
    '',
    'Return ONLY a tight JSON matching the schema. NO prose.',
    'If a field is missing/unreadable, report it as an empty string but continue.',
    'Do NOT invent projects. Only parse what is actually in §0.',
  ].join('\n'),
  {
    label: 'scan',
    phase: 'Scan',
    schema: {
      type: 'object',
      additionalProperties: false,
      properties: {
        board_last_generated: { type: 'string', maxLength: 60 },
        board_rows: {
          type: 'array',
          maxItems: 40,
          items: {
            type: 'object',
            additionalProperties: false,
            properties: {
              project:    { type: 'string', maxLength: 80 },
              phase:      { type: 'string', maxLength: 400 },
              pct:        { type: 'integer' },
              next_move:  { type: 'string', maxLength: 500 },
              blocked_on: { type: 'string', maxLength: 100 },
              owner:      { type: 'string', maxLength: 60 },
              last_fire:  { type: 'string', maxLength: 60 },
            },
            required: ['project'],
          },
        },
        arc_recent_window: { type: 'string', maxLength: 3500 },
        scan_notes:        { type: 'string', maxLength: 400 },
      },
      required: ['board_rows'],
    },
  }
)

const boardRows = (scanResult && Array.isArray(scanResult.board_rows)) ? scanResult.board_rows : []
log(`SCAN: ${boardRows.length} board rows`)

if (boardRows.length === 0) {
  return {
    headline: '[WORK-DRIVER] SCAN produced ZERO board rows — cannot PICK; check PROJECT-BOARD §0 sentinels',
    phase: 'Scan',
    action_taken: 'ABORTED — no rows to pick from',
    zero_launch_fail: true,
    exceptions: ['scan returned empty board_rows array; nothing to drive'],
  }
}

// ---------------------------------------------------------------------------
// PHASE 2 — PICK
// ---------------------------------------------------------------------------
phase('Pick')

// Ask a Bash agent for now-UTC (workflow sandboxes usually have no Date).
const nowAgent = await agent(
  'Return current UTC time as { now_iso, now_epoch }. Use: date -u +%Y-%m-%dT%H:%M:%SZ and date -u +%s',
  {
    label: 'now-utc',
    phase: 'Pick',
    schema: {
      type: 'object',
      additionalProperties: false,
      properties: {
        now_iso:   { type: 'string', maxLength: 32 },
        now_epoch: { type: 'integer' },
      },
      required: ['now_iso', 'now_epoch'],
    },
  }
)
const nowEpoch = (nowAgent && nowAgent.now_epoch) ? nowAgent.now_epoch : 0

// Loose ISO parser (workflow sandbox has no Date). Returns 0 on failure so
// unknown last_fire biases toward maximally-stale.
function parseIsoToEpoch(s) {
  if (!s || typeof s !== 'string') return 0
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?/)
  if (!m) return 0
  const y = parseInt(m[1], 10), mo = parseInt(m[2], 10), d = parseInt(m[3], 10)
  const h = parseInt(m[4], 10), mi = parseInt(m[5], 10), se = parseInt(m[6] || '0', 10)
  const daysBeforeMonth = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
  const yearsSince1970 = y - 1970
  let leapDays = 0
  for (let yr = 1970; yr < y; yr++) {
    if ((yr % 4 === 0 && yr % 100 !== 0) || yr % 400 === 0) leapDays++
  }
  const isLeapCurrent = ((y % 4 === 0 && y % 100 !== 0) || y % 400 === 0) && mo > 2
  const dayOfYear = daysBeforeMonth[mo - 1] + (d - 1) + (isLeapCurrent ? 1 : 0)
  const totalDays = yearsSince1970 * 365 + leapDays + dayOfYear
  return totalDays * 86400 + h * 3600 + mi * 60 + se
}

const boardLastGenEpoch = parseIsoToEpoch(scanResult?.board_last_generated || '')
const boardLagHrs = boardLastGenEpoch > 0 && nowEpoch > 0
  ? Math.max(0, Math.min(168, (nowEpoch - boardLastGenEpoch) / 3600))
  : 24

// FORK-WIRING SEAM — set your civ's steward-id (the human-blocked bucket).
// Rows blocked on this ID get score * 0.3 (Primary can't drive human-blocked).
// NOTE: .js files are NOT swept by tools/template_substitute.sh — a born civ
// edits this line by hand to its human's lowercase name (e.g. 'corey').
const STEWARD_ID = 'steward'

function scoreRow(row) {
  const lastFireEpoch = parseIsoToEpoch(row.last_fire || '')
  const stalenessHrs = lastFireEpoch > 0 && nowEpoch > 0
    ? Math.max(0, Math.min(168, (nowEpoch - lastFireEpoch) / 3600))
    : 72
  let score = stalenessHrs + boardLagHrs * 0.5
  const blocked = (row.blocked_on || '').toLowerCase().trim()
  if (blocked === STEWARD_ID.toLowerCase()) score *= 0.3
  else if (blocked && blocked !== 'none') score *= 0.7
  if (biasVertical) {
    const owner = (row.owner || '').toLowerCase()
    if (owner.includes(biasVertical)) score *= 1.3
  }
  if ((row.project || '').startsWith('grounding/')) score *= 1.1
  return {
    project: row.project,
    owner: row.owner || '',
    blocked_on: row.blocked_on || 'none',
    score: Math.round(score * 100) / 100,
    staleness_hrs: Math.round(stalenessHrs * 10) / 10,
    board_lag_hrs: Math.round(boardLagHrs * 10) / 10,
  }
}

const scored = boardRows.map(scoreRow).sort((a, b) => b.score - a.score)
const picked = scored[0]
const pickedRow = boardRows.find(r => r.project === picked.project) || {}
log(`PICK: ${picked.project} (score=${picked.score}, staleness=${picked.staleness_hrs}h, board-lag=${picked.board_lag_hrs}h)`)

// ---------------------------------------------------------------------------
// PHASE 3 — ABSORB (skipped for brevity in the stub — see origin-civ workflow
// for the full agent prompt. It reads MISSION.md / OPS.md / DEVLOG.md tail-40 /
// grep arc/live.jsonl for events on the picked-project's thread.)
// ---------------------------------------------------------------------------
phase('Absorb')

const absorbResult = await agent(
  [
    `You are the WORK-DRIVER ABSORB agent for project "${picked.project}".`,
    '',
    'STEP 1 — Find the project directory. Try:',
    `  find projects/ -maxdepth 4 -type d -iname "${picked.project}" 2>/dev/null`,
    '  If none found, report project_dir="" honestly.',
    '',
    'STEP 2 — Read MISSION.md (full, up to 6KB) if it exists.',
    'STEP 3 — Read OPS.md (full, up to 4KB) if it exists.',
    'STEP 4 — Read DEVLOG.md tail-40 lines if it exists.',
    `STEP 5 — Grep ${ARC_LIVE_JSONL} for events on this thread: grep -F '"thread": "${picked.project}"' ${ARC_LIVE_JSONL} 2>/dev/null | tail -8`,
    '',
    'HONESTY over completeness: if a file does not exist, report empty string; do NOT invent.',
  ].join('\n'),
  {
    label: 'absorb',
    phase: 'Absorb',
    schema: {
      type: 'object',
      additionalProperties: false,
      properties: {
        project_dir:       { type: 'string', maxLength: 200 },
        mission_content:   { type: 'string', maxLength: 6500 },
        ops_content:       { type: 'string', maxLength: 4500 },
        devlog_tail:       { type: 'string', maxLength: 4000 },
        arc_thread_events: { type: 'string', maxLength: 2500 },
        docs_found:        { type: 'array', maxItems: 6, items: { type: 'string', maxLength: 200 } },
      },
      required: ['docs_found'],
    },
  }
)

const projectDir = absorbResult?.project_dir || ''

// ---------------------------------------------------------------------------
// PHASE 4 — DRIVE (the load-bearing bit — NO-IDLE-NODE state machine)
// ---------------------------------------------------------------------------
phase('Drive')

function resolveOwnerManifest(ownerStr) {
  const s = (ownerStr || '').toLowerCase()
  const leadMatch = s.match(/([a-z0-9_\-]+?)-lead/)
  const key = leadMatch ? leadMatch[1] : s.split(/[\s,+]/)[0].trim()
  return { key, manifest: MANIFESTS[key] || '' }
}

const ownerResolved = resolveOwnerManifest(pickedRow.owner)
const manifestPath = ownerResolved.manifest
if (!manifestPath) {
  // No manifest wired for this owner — bail loud rather than fake a drive.
  return {
    headline: `[WORK-DRIVER] no manifest wired for owner "${pickedRow.owner}" (key=${ownerResolved.key}); wire MANIFESTS at top of this file`,
    phase: 'Drive',
    picked_project: picked.project,
    zero_launch_fail: true,
    exceptions: [`MANIFESTS table has no entry for "${ownerResolved.key}"; cannot incarnate`],
  }
}

let driveResult = null
let zeroLaunchFail = false

if (isDryRun) {
  log(`DRIVE (dry-run): WOULD incarnate ${ownerResolved.key}-lead to advance "${picked.project}"`)
} else {
  driveResult = await agent(
    [
      `You are ${ownerResolved.key}-lead, incarnated to DRIVE FORWARD the "${picked.project}" project.`,
      `Read your manifest at ${manifestPath} and embody it (return one verbatim line as embodied_proof).`,
      '',
      '--- TRUSTED FRAME (hardcoded by work-driver; non-overridable) ---',
      'DOCTRINE: get it moving; no "reviewed-looks-fine" exit. Grounding surfaces + observers',
      'observing is not enough — a DRIVE cycle that does not launch a concrete move is a FAILURE.',
      'You are the OWNING VP. This is YOUR territory. MAKE ONE MOVE. The move should be:',
      '  - the smallest concrete step that advances the project (not the whole thing)',
      '  - real: a file edit / a script run / a workflow scheduled / a decision recorded',
      '  - anchored: return a file path, a task_id, or a specific artifact you touched/created',
      '',
      `If the project is HONESTLY blocked_on=${STEWARD_ID} and no VP-side move exists, say so — but`,
      'you MUST still identify ONE thing you CAN do right now (e.g. re-verify the block, prep',
      'the artifact awaiting the human, refresh the docs). Zero action = FAIL. "Waiting" is not action.',
      '',
      '--- BOARD ROW (verbatim, this is what needs to move) ---',
      `Project: ${picked.project}`,
      `Phase: ${(pickedRow.phase || '').slice(0, 350)}`,
      `%: ${pickedRow.pct}`,
      `Next Move: ${(pickedRow.next_move || '').slice(0, 400)}`,
      `Blocked On: ${pickedRow.blocked_on || 'none'}`,
      `Owner: ${pickedRow.owner || ''}`,
      `Last Fire: ${pickedRow.last_fire || ''}`,
      '',
      '--- PROJECT DOCS (absorbed) ---',
      `MISSION:\n${(absorbResult?.mission_content || '(none)').slice(0, 4000)}`,
      '',
      `OPS:\n${(absorbResult?.ops_content || '(none)').slice(0, 2500)}`,
      '',
      `DEVLOG tail-40:\n${(absorbResult?.devlog_tail || '(none)').slice(0, 2500)}`,
      '',
      `ARC THREAD (recent):\n${(absorbResult?.arc_thread_events || '(no events on thread yet)').slice(0, 1800)}`,
      '',
      '--- YOUR TASK ---',
      'Make ONE concrete move to advance this project. Return:',
      '  action_taken       — verbatim description of what you DID (past tense)',
      '  action_kind        — file_edit | file_write | script_run | workflow_scheduled | decision_recorded | doc_refreshed | verify_block | other',
      '  receipt            — real anchor (file path / task_id / URL). If you edited a file, its path. NEVER a speculative receipt.',
      '  followup_next_move — the SINGLE next concrete step after this one (feeds board §26 whats_next)',
      '  followup_pct       — new % after your move (integer 0-100)',
      '  followup_phase     — updated phase heading (or unchanged verbatim)',
      `  followup_blocked_on — "none" | "${STEWARD_ID}" | "<other-project>"`,
      '  embodied_proof     — one verbatim line from your manifest proving real read',
    ].join('\n'),
    {
      label: `drive-${ownerResolved.key}`,
      phase: 'Drive',
      schema: {
        type: 'object',
        additionalProperties: false,
        properties: {
          embodied_proof: { type: 'string', maxLength: 300 },
          action_taken:   { type: 'string', maxLength: 500 },
          action_kind:    {
            type: 'string',
            enum: ['file_edit', 'file_write', 'script_run', 'workflow_scheduled',
                   'decision_recorded', 'doc_refreshed', 'verify_block', 'other'],
          },
          receipt:              { type: 'string', maxLength: 300 },
          followup_next_move:   { type: 'string', maxLength: 400 },
          followup_pct:         { type: 'integer' },
          followup_phase:       { type: 'string', maxLength: 250 },
          followup_blocked_on:  { type: 'string', maxLength: 60 },
        },
        required: ['action_taken', 'receipt', 'followup_next_move'],
      },
    }
  )

  const actionTaken = (driveResult?.action_taken || '').trim()
  const receipt = (driveResult?.receipt || '').trim()
  if (!actionTaken || !receipt || actionTaken.length < 10) {
    zeroLaunchFail = true
    log('DRIVE: ZERO-LAUNCH FAIL — VP returned empty/dodging action_taken or receipt')
  }
}

// ---------------------------------------------------------------------------
// PHASE 5 — RECORD — append the followup to whats-next-feed + DEVLOG + arc.
// (Trimmed for stub brevity; see origin-civ workflow for the full agent block.)
// ---------------------------------------------------------------------------
phase('Record')

const recordFollowup = {
  project: picked.project,
  phase: (driveResult?.followup_phase || pickedRow.phase || '').slice(0, 350),
  pct: (driveResult && typeof driveResult.followup_pct === 'number')
    ? Math.max(0, Math.min(100, driveResult.followup_pct))
    : (pickedRow.pct || 0),
  next_move: (driveResult?.followup_next_move || pickedRow.next_move || '').slice(0, 400),
  blocked_on: (driveResult?.followup_blocked_on || pickedRow.blocked_on || 'none').slice(0, 60),
}

// ---------------------------------------------------------------------------
// FIREWALL RETURN — small, digested, ≤2KB. Carries whats_next verbatim so the
// board updates on the next --regen.
// ---------------------------------------------------------------------------
const headline = isDryRun
  ? `[WORK-DRIVER dry-fire] picked ${picked.project} (score ${picked.score}); WOULD launch ${ownerResolved.key}-lead to advance`
  : zeroLaunchFail
    ? `[WORK-DRIVER FAIL] picked ${picked.project} but VP returned empty action — ZERO-LAUNCH firewall FAIL`
    : `[WORK-DRIVER] ${ownerResolved.key}-lead drove ${picked.project}: ${(driveResult?.action_taken || '').slice(0, 200)}`

return {
  headline,
  phase: isDryRun ? 'Drive (dry-run)' : (zeroLaunchFail ? 'Drive (zero-launch fail)' : 'Record'),
  picked_project: picked.project,
  picked_owner: pickedRow.owner || '',
  picked_score: picked.score,
  action_kind: driveResult?.action_kind || (isDryRun ? 'dry-run' : ''),
  action_taken: (driveResult?.action_taken || '').slice(0, 400),
  receipt: (driveResult?.receipt || '').slice(0, 250),
  zero_launch_fail: zeroLaunchFail,
  whats_next: recordFollowup,
  scored_top3: scored.slice(0, 3).map(s => ({ project: s.project, score: s.score, staleness_hrs: s.staleness_hrs })),
  exceptions: zeroLaunchFail
    ? ['DRIVE phase produced no concrete action + receipt; doctrine violation']
    : [],
}
