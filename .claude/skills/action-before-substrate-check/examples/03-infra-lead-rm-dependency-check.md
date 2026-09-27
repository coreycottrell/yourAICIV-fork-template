# Example 3 — infra-lead about to `rm -rf` a directory

**Scenario**: It's 2026-05-12 ~14:00Z. Infra-lead is in tech-debt slot 14. Disk audit found a 651MB `google-cloud-sdk/` directory under `/home/you/.../`. No agent appears to use gcloud commands. Slot's pay-target picked: `rm -rf` the directory. Cleanup, done, 651MB recovered.

**Substrate the action depends on**: nothing in the system depends on the binaries in that directory — no cron, no agent manifest, no in-flight build, no PATH-resolution, no lsof handle.

---

## Without the skill (what actually happened)

```
infra-lead: "Slot 14 pay-target — rm 651MB google-cloud-sdk."
[rm -rf executes successfully]
[commits with message "tech-debt: remove unused google-cloud-sdk"]
[651MB recovered, slot exits COMPLETE]
[Next day: nothing visible breaks; verification IS the audit, the audit never happened]
```

Result: the `rm` may have been correct OR it may have removed a binary that some cron or build script depended on — we don't know because we didn't check. The slot exited COMPLETE on assumed substrate. This is the canonical row #1 in system-gt-symptom's "yesterday's 2 misses" table.

---

## With the skill

### Step 1 — NAME THE ACTION

`rm -rf /home/you/.../google-cloud-sdk/ — a 651MB directory containing gcloud + bq + gsutil binaries + ~2.3GB of unpacked support files.`

### Step 2 — LIST ITS SUBSTRATE DEPENDENCIES

```
DEPENDENCY: no cron job invokes gcloud/bq/gsutil = TRUE
DEPENDENCY: no agent manifest cites the path or the gcloud command = TRUE
DEPENDENCY: no in-flight build/deploy script uses it = TRUE
DEPENDENCY: not in PATH of any active shell session = TRUE
DEPENDENCY: no skill / SKILL.md references gcloud = TRUE
DEPENDENCY: no lsof / fuser handle on any file in that directory = TRUE
```

### Step 3 — VERIFY EACH

```bash
# Cron check
crontab -l | grep -E "gcloud|bq |gsutil"
sudo cat /etc/cron.d/* 2>/dev/null | grep -E "gcloud|bq |gsutil"
# (no matches) ← VERIFIED ✓

# Agent manifest check
grep -rE "gcloud|google-cloud-sdk|\bbq\b|gsutil" autonomy/agents/ autonomy/team-leads/
# Match found in autonomy/team-leads/data/manifest.md:47 (hypothetical) ← DRIFT
# OR if no matches: ← VERIFIED ✓

# Build/deploy script check
grep -rE "gcloud|google-cloud-sdk" tools/ projects/aiciv-inc/ scripts/ 2>/dev/null
# Match found in tools/quickbooks_to_bigquery_sync.py:12 ← DRIFT
# (gcloud auth used for BigQuery sync)

# PATH check
echo "$PATH" | tr ':' '\n' | grep -E "google-cloud-sdk"
# /home/you/.../google-cloud-sdk/bin ← DRIFT — it's in PATH

# Skill check
grep -rl "gcloud" autonomy/skills/ .claude/skills/ 2>/dev/null
# autonomy/skills/quickbooks-api/SKILL.md ← DRIFT

# lsof check
lsof 2>/dev/null | grep -E "google-cloud-sdk"
# (no live handles) ← VERIFIED ✓
```

Three dependencies drifted: gcloud is in PATH (active shells expect it), one tool depends on it for BigQuery sync, one skill references it. The "nothing depends on this" assumption is false.

### Step 4 — COMMIT OR AMEND

**Verdict: AMEND-ACTION.** Three fix-paths:

- **Fix-path 1 (amend the action)**: don't rm; instead, audit each finding (is the BigQuery sync tool still in use? if not, deprecate the tool AND rm; if yes, keep the sdk). The "cleanup" action grows into a 3-step audit.
- **Fix-path 2 (amend the substrate)**: deprecate the BigQuery sync tool first, retire the dependent skill section, remove from PATH; *then* rm. The substrate is moved into the action's assumption.
- **Fix-path 3 (abort)**: this isn't tech-debt at the substrate level — gcloud is live infra. Slot pay-target was wrong. Pick a different target.

Choice: Fix-path 1 (the audit). If BigQuery sync is dead, deprecate then rm. If live, keep.

---

## Receipt block written to slot scratchpad

```
ACTION:        rm -rf /home/you/.../google-cloud-sdk/ (651MB cleanup target, slot 14)
DEPENDENCIES:
  - no cron uses gcloud = TRUE | VERIFIED ✓
  - no agent manifest cites it = TRUE | VERIFIED ✓
  - no build script uses it = TRUE | DRIFT — tools/quickbooks_to_bigquery_sync.py:12
  - not in PATH = TRUE | DRIFT — present in $PATH for active shells
  - no skill cites it = TRUE | DRIFT — quickbooks-api/SKILL.md
  - no lsof handles = TRUE | VERIFIED ✓
VERDICT:       AMEND-ACTION
REDIRECT:      Slot 14 redirects to audit: is BigQuery sync tool still in use? If dead, deprecate-tool + deprecate-skill-section + remove-from-PATH first, then rm. If live, this isn't cleanup target — pick different slot 14 work.
```

---

## What the skill caught

- A potentially-broken BigQuery sync tool (would fail next time it ran, with a non-obvious "gcloud: command not found" error)
- A live skill (quickbooks-api) that would lose a referenced binary
- PATH-pollution-flip — active shells would suddenly lose `gcloud` resolution mid-session
- A wrong-shaped slot pay-target — what looked like tech-debt was live infra

**Time cost of the check**: ~2 minutes (6 grep/lsof/PATH commands).
**Time saved**: variable — could have been a silent BigQuery sync failure caught hours-to-days later, or a "why is gcloud gone" debugging session, or trust-cost for an unannounced PATH change.

---

## Meta-lesson

The action-before-substrate-check pattern catches *exactly* the row in system-gt-symptom's "yesterday's misses" table that became its canonical example. The two skills are siblings:

- **action-before-substrate-check** catches: rm executed on assumed substrate (PRE)
- **system-gt-symptom** catches: rm DID execute on broken substrate, now what system allowed this? (POST)

Both together close the loop: the rm wouldn't have happened (PRE), and if it had, the system that allowed assumed-substrate-rm without verification would be named and fixed (POST). The 3-layer PRE/RENDER/POST discipline is the full coverage.
