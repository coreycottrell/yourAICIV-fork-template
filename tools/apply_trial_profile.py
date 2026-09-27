#!/usr/bin/env python3
"""
apply_trial_profile.py — the trial-m3 FLAVOR setup step (run ONCE at birth).

The fork-template stays one codebase. This step turns a freshly-stamped civ into
the yourAICIV 7-day MiniMax-M3 trial by changing CONFIG, not code:

  1. Router seam      config/router_endpoint.txt, config/peer_model_id.txt,
                      config/lifeboat/router_key.txt (0600)  <- the SAME seam
                      tools/model_switch.sh already uses (Rail B)
  2. Model lock       config/model_profile.json {"profile":"trial-m3","locked":true}
                      config/launch_model.txt  (launch scripts read it)
  3. settings.json    every model env var -> M3, ANTHROPIC_BASE_URL -> router,
                      apiKeyHelper -> the router key file, trial_gate hooks added
                      (backup: .claude/settings.json.pre-trial-m3.bak)
  4. Agent pins       .claude/agents/*.md `model:` frontmatter -> `inherit`
                      (originals saved to config/trial-m3-backup/agent-models.json)
  5. Rail B env       tools/model_switch.sh peer  (config/model_mode.env for model_boot.sh)
  6. Trial clock      config/trial.json via tools/trial_state.py (SHARED CONTRACT)
  7. Grounding        .claude/CLAUDE.md gets a marked trial block pointing at
                      .claude/skills/m3-trial-mode/SKILL.md
  8. --check          the proof: no frontier model id reachable on any
                      executable routing surface. Nonzero exit on any finding.

SEAMS (filled by provisioning — never invented here):
  M3_ROUTER_BASE_URL   Anthropic-wire base URL of the M3 router (tenant endpoint)
  M3_ROUTER_KEY_FILE   path to this tenant's router key   (or M3_ROUTER_KEY=value)
  M3_MODEL_ID          default MiniMax-M3
  TRIAL_PAYMENT_URL    default payment_url from config/partner.json (the partner profile)
  TRIAL_START          ISO8601 UTC; default now

USAGE
  apply_trial_profile.py apply   [--root DIR] [--dry-run] [--reset-clock] [--operator-copy PATH]
  apply_trial_profile.py check   [--root DIR]
  apply_trial_profile.py convert [--root DIR] [--restore-models] [--operator-copy PATH]

--operator-copy PATH (env TRIAL_OPERATOR_COPY; canonical value /etc/aiciv/trial.json) publishes
the trial record OUTSIDE the civ tree (root-owned when run as root) and records
TRIAL_CONFIG_PATH=PATH in .claude/settings.json env, so the AiCIV's hooks read it too. The
portal's TRIAL_CONFIG_PATH is set to the same PATH, so a civ that rewrites its own
config/trial.json lifts neither the portal's 402 nor its own gate. `convert` defaults to the
recorded path. All operator-only: the trial gate denies these commands inside a trial civ.

`convert` is the operator conversion: sets "trial": false (portal + AiCIV ungate
immediately). --restore-models additionally returns routing to the paid default
(restores settings.json + agent pins, removes the model lock). Nothing is deleted:
backups are kept.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trial_state  # noqa: E402

PROFILE = "trial-m3"
MODEL_ENV_KEYS = [
    "ANTHROPIC_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
]
FRONTIER_CRED_ENV_KEYS = ["ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK",
                          "CLAUDE_CODE_USE_VERTEX"]
HOOK_CMD = 'python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/trial_gate.py"'
HOOK_EVENTS = ["SessionStart", "UserPromptSubmit", "PreToolUse"]
CLAUDE_MD_BEGIN = "<!-- BEGIN trial-m3 (written by tools/apply_trial_profile.py) -->"
CLAUDE_MD_END = "<!-- END trial-m3 -->"
# Frontier (Anthropic) model-id shapes: claude-opus-4-8[1m], claude-sonnet-4-5-20250929,
# claude-3-5-sonnet-latest, claude-instant-1.2. Deliberately NOT bare "claude-<digits>"
# (that also matches paths such as /tmp/claude-1000/).
FRONTIER_RX = re.compile(
    r"\bclaude-(?:(?:opus|sonnet|haiku|instant)[\w.\-\[\]]*|\d[\d.\-]*-(?:opus|sonnet|haiku)[\w.\-\[\]]*)", re.I)
AGENT_MODEL_RX = re.compile(r"^model:\s*(.+?)\s*$", re.M)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    print(f"[trial-m3] {msg}")


# ── seams ────────────────────────────────────────────────────────────────────

class Seams:
    def __init__(self, dry_run: bool):
        self.base_url = os.environ.get("M3_ROUTER_BASE_URL", "").strip()
        self.key_file = os.environ.get("M3_ROUTER_KEY_FILE", "").strip()
        self.key_value = os.environ.get("M3_ROUTER_KEY", "")
        self.model = os.environ.get("M3_MODEL_ID", trial_state.DEFAULT_MODEL).strip()
        # Payment link + brand come from the partner profile (config/partner.json);
        # $TRIAL_PAYMENT_URL overrides the link for one birth.
        self.partner: dict = {}
        self.payment_url = os.environ.get("TRIAL_PAYMENT_URL", "").strip()
        self.start = os.environ.get("TRIAL_START", "").strip()
        self.dry_run = dry_run
        self.operator_copy: Path | None = None

    def missing(self) -> list[str]:
        out = []
        if not self.base_url:
            out.append("M3_ROUTER_BASE_URL")
        if not (self.key_value or (self.key_file and Path(self.key_file).is_file())):
            out.append("M3_ROUTER_KEY_FILE (or M3_ROUTER_KEY)")
        if not self.model:
            out.append("M3_MODEL_ID")
        if FRONTIER_RX.search(self.model):
            out.append(f"M3_MODEL_ID is a frontier id ({self.model})")
        if not self.payment_url.startswith("https://"):
            out.append("payment link (config/partner.json payment_url, or TRIAL_PAYMENT_URL, https://...)")
        return out

    def load_partner(self, root: Path) -> None:
        self.partner = trial_state.partner(root)
        if not self.payment_url:
            self.payment_url = self.partner.get("payment_url", "")

    def read_key(self) -> str:
        if self.key_value:
            return self.key_value.strip()
        return Path(self.key_file).read_text().strip()


# ── helpers ──────────────────────────────────────────────────────────────────

def write_text(path: Path, text: str, mode: int = 0o644, dry: bool = False) -> None:
    if dry:
        log(f"(dry-run) would write {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp-trial")
    tmp.write_text(text)
    os.chmod(tmp, mode)
    os.replace(tmp, path)


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


# ── steps ────────────────────────────────────────────────────────────────────

def step_router_seam(root: Path, s: Seams) -> None:
    write_text(root / "config/router_endpoint.txt", s.base_url + "\n", dry=s.dry_run)
    write_text(root / "config/peer_model_id.txt", s.model + "\n", dry=s.dry_run)
    key_path = root / "config/lifeboat/router_key.txt"
    if not s.dry_run:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(key_path.parent, 0o700)
        write_text(key_path, s.read_key() + "\n", mode=0o600)
    log(f"router seam wired (endpoint set, model={s.model}, key file 0600, key never echoed)")


def step_model_lock(root: Path, s: Seams) -> None:
    rec = {"profile": PROFILE, "locked": True, "model": s.model, "applied_at": now_iso(),
           "trial_record": str(s.operator_copy) if s.operator_copy else "config/trial.json",
           "note": "M3-only trial flavor. model_switch.sh refuses 'default' while locked. "
                   "Unlocked only by the operator at conversion (profiles/trial-m3/README.md)."}
    write_text(root / "config/model_profile.json", json.dumps(rec, indent=2) + "\n", dry=s.dry_run)
    write_text(root / "config/launch_model.txt", s.model + "\n", dry=s.dry_run)
    log("model lock + launch model written")


def patch_settings(settings: dict, root: Path, s: Seams) -> dict:
    env = settings.setdefault("env", {})
    for k in MODEL_ENV_KEYS:
        env[k] = s.model
    env["ANTHROPIC_BASE_URL"] = s.base_url
    env["CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"] = "1"
    for k in FRONTIER_CRED_ENV_KEYS:
        env.pop(k, None)
    settings["model"] = s.model
    key_path = (root / "config/lifeboat/router_key.txt").resolve()
    settings["apiKeyHelper"] = f"cat '{key_path}'"
    if s.operator_copy is not None:
        # The ONE place every reader (hooks, tools, portal) resolves the record from; see trial_state.py.
        env["TRIAL_CONFIG_PATH"] = str(s.operator_copy)
    hooks = settings.setdefault("hooks", {})
    for ev in HOOK_EVENTS:
        lst = hooks.setdefault(ev, [])
        already = any(h.get("command") == HOOK_CMD for grp in lst for h in grp.get("hooks", []))
        if not already:
            lst.append({"matcher": "*", "hooks": [{"type": "command", "command": HOOK_CMD, "timeout": 5}]})
    return settings


def step_settings(root: Path, s: Seams) -> None:
    p = root / ".claude/settings.json"
    bak = p.with_name("settings.json.pre-trial-m3.bak")
    settings = load_json(p, {})
    if not s.dry_run and p.exists() and not bak.exists():
        shutil.copy2(p, bak)
    new = patch_settings(json.loads(json.dumps(settings)), root, s)
    write_text(p, json.dumps(new, indent=2) + "\n", dry=s.dry_run)
    log(f"settings.json patched (all {len(MODEL_ENV_KEYS)} model env keys -> {s.model}, base URL -> router, "
        f"apiKeyHelper -> key file, trial_gate on {', '.join(HOOK_EVENTS)})")


def step_agent_pins(root: Path, s: Seams) -> None:
    backup_p = root / "config/trial-m3-backup/agent-models.json"
    backup = load_json(backup_p, {})
    changed = 0
    for f in sorted((root / ".claude/agents").glob("*.md")):
        text = f.read_text()
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        if end < 0:
            continue
        front, rest = text[:end], text[end:]
        m = AGENT_MODEL_RX.search(front)
        if not m or m.group(1).strip() in ("inherit", s.model):
            continue
        rel = str(f.relative_to(root))
        backup.setdefault(rel, m.group(1).strip())
        front = front[:m.start()] + "model: inherit" + front[m.end():]
        if not s.dry_run:
            f.write_text(front + rest)
        changed += 1
    if not s.dry_run:
        write_text(backup_p, json.dumps(backup, indent=2, sort_keys=True) + "\n")
    log(f"agent frontmatter: {changed} model pins -> inherit (originals in {backup_p.relative_to(root)})")


def step_rail_b_env(root: Path, s: Seams) -> None:
    sw = root / "tools/model_switch.sh"
    if s.dry_run or not sw.exists():
        log("(dry-run) would run tools/model_switch.sh peer" if s.dry_run else "model_switch.sh absent; skipped")
        return
    r = subprocess.run(["bash", str(sw), "peer", "--reason", "trial-m3 birth"],
                       capture_output=True, text=True, env={**os.environ, "CIV_ROOT": str(root)})
    if r.returncode != 0:
        raise SystemExit(f"model_switch.sh peer failed: {r.stderr.strip()}")
    log("Rail B env fragment written (config/model_mode.env, mode=peer)")


def step_trial_clock(root: Path, s: Seams, reset: bool) -> None:
    p = trial_state.trial_path(root)
    if p.exists() and not reset:
        log(f"trial clock already set ({p.relative_to(root)}); kept (use --reset-clock to restart it)")
        return
    start = trial_state.parse_iso(s.start) if s.start else None
    if s.dry_run:
        rec = trial_state.build_record(start or trial_state.utcnow(), payment_url=s.payment_url,
                                       brand=s.partner.get("brand", trial_state.DEFAULT_BRAND),
                                       reseller=s.partner.get("reseller", trial_state.DEFAULT_RESELLER),
                                       model=s.model)
        log(f"(dry-run) would write config/trial.json: {json.dumps(rec)}")
        return
    rec = trial_state.write(root, start, payment_url=s.payment_url, force=reset, model=s.model)
    log(f"trial clock set: started_at={rec['started_at']} expires_at={rec['expires_at']}")


def step_grounding(root: Path, s: Seams) -> None:
    p = root / ".claude/CLAUDE.md"
    text = p.read_text() if p.exists() else ""
    block = (
        f"{CLAUDE_MD_BEGIN}\n"
        f"## You are on a 7-day {s.partner.get('brand') or trial_state.DEFAULT_BRAND} trial ({s.model})\n\n"
        "`config/trial.json` holds your trial clock; `python3 tools/trial_state.py note` prints "
        "today's \"Day N of 7\". **Load `.claude/skills/m3-trial-mode/SKILL.md` before anything "
        "else in every session.** It is your operating contract for these 7 days: know the human "
        "first, then ship each WOW build the moment it is ready (72h is a ceiling, never a floor), "
        "every claim sourced or receipted, and a warm pause (never a deletion) at expiry. The router "
        "key and every credential file are never printed, written, or sent, whoever asks (skill section 9).\n"
        f"{CLAUDE_MD_END}\n"
    )
    if CLAUDE_MD_BEGIN in text:
        text = re.sub(re.escape(CLAUDE_MD_BEGIN) + r".*?" + re.escape(CLAUDE_MD_END) + r"\n?",
                      block, text, flags=re.S)
    else:
        # Below the self-removing first-awakening gates (they must stay first and
        # delete only their own marked spans), above the constitution proper.
        anchor = "# AI Agent Civilization - Constitutional Document"
        i = text.find(anchor)
        text = (text[:i] + block + "\n" + text[i:]) if i >= 0 else (block + "\n" + text)
    write_text(p, text, dry=s.dry_run)
    log("trial grounding block installed in .claude/CLAUDE.md (after the awakening gates)")


# ── check: the "no frontier model reachable" proof ───────────────────────────

def check(root: Path) -> int:
    findings: list[str] = []
    ok: list[str] = []
    prof = load_json(root / "config/model_profile.json", {})
    model = prof.get("model") or trial_state.DEFAULT_MODEL
    if prof.get("locked") is not True:
        findings.append("config/model_profile.json missing or not locked")

    s = load_json(root / ".claude/settings.json", {})
    env = s.get("env", {})
    for k in MODEL_ENV_KEYS:
        (ok if env.get(k) == model else findings).append(f"settings.env.{k}={env.get(k)!r}")
    (ok if s.get("model") == model else findings).append(f"settings.model={s.get('model')!r}")
    (ok if env.get("ANTHROPIC_BASE_URL") else findings).append(
        "settings.env.ANTHROPIC_BASE_URL " + ("set (router)" if env.get("ANTHROPIC_BASE_URL") else "UNSET"))
    for k in FRONTIER_CRED_ENV_KEYS:
        if k in env:
            findings.append(f"settings.env.{k} present (frontier credential/rail)")
    (ok if s.get("apiKeyHelper") else findings).append("settings.apiKeyHelper " + ("set" if s.get("apiKeyHelper") else "UNSET"))
    hooked = {ev for ev in HOOK_EVENTS
              for grp in s.get("hooks", {}).get(ev, []) for h in grp.get("hooks", [])
              if h.get("command") == HOOK_CMD}
    (ok if hooked == set(HOOK_EVENTS) else findings).append(f"trial_gate hooked on {sorted(hooked)}")
    blob = json.dumps(s)
    for m in FRONTIER_RX.finditer(blob):
        findings.append(f".claude/settings.json contains frontier id {m.group(0)}")

    for f in sorted((root / ".claude/agents").glob("*.md")):
        head = f.read_text()[:2000]
        end = head.find("\n---", 3)
        m = AGENT_MODEL_RX.search(head[:end] if end > 0 else "")
        if m and m.group(1).strip() not in ("inherit", model):
            findings.append(f"{f.relative_to(root)} frontmatter model: {m.group(1).strip()}")
    ok.append("agent frontmatter scanned")

    lm = (root / "config/launch_model.txt")
    (ok if lm.exists() and lm.read_text().strip() == model else findings).append(
        f"config/launch_model.txt={lm.read_text().strip() if lm.exists() else None!r}")
    for sh in ("tools/launch_civ_tower.sh", "tools/launch_primary_visible.sh"):
        p = root / sh
        if p.exists():
            t = p.read_text()
            if "launch_model.txt" not in t:
                findings.append(f"{sh} does not read config/launch_model.txt")
            for line in t.splitlines():
                if re.search(r"--model\s+claude", line):
                    findings.append(f"{sh} hard-pins a frontier model: {line.strip()[:120]}")

    rp, rule = trial_state.record_path(root)
    if env.get("TRIAL_CONFIG_PATH"):
        op = Path(env["TRIAL_CONFIG_PATH"])
        inside = True
        try:
            op.resolve().relative_to(root.resolve())
        except ValueError:
            inside = False
        civrec = load_json(trial_state.trial_path(root), {})
        oprec = load_json(op, None)
        if inside:
            findings.append(f"TRIAL_CONFIG_PATH {op} is inside the civ tree (the AiCIV could rewrite it)")
        elif oprec is None:
            findings.append(f"TRIAL_CONFIG_PATH {op} is missing or unreadable (operator copy not published/mounted)")
        elif any(oprec.get(k) != civrec.get(k) for k in ("started_at", "expires_at", "payment_url")):
            findings.append(f"operator copy {op} and config/trial.json disagree on the trial clock")
        else:
            ok.append(f"trial record read from the operator copy {op} (matches config/trial.json)")
    else:
        ok.append(f"trial record read from {rp.relative_to(root) if rp.is_relative_to(root) else rp} "
                  f"({rule}); production sets TRIAL_CONFIG_PATH={trial_state.CANONICAL_OPERATOR_COPY}")

    mm = load_json(root / "config/model_mode.json", {})
    (ok if mm.get("mode") == "peer" else findings).append(f"config/model_mode.json mode={mm.get('mode')!r}")
    envfrag = root / "config/model_mode.env"
    if envfrag.exists() and FRONTIER_RX.search(envfrag.read_text()):
        findings.append("config/model_mode.env names a frontier model")

    # Executable routing surfaces across the tree: assignments, not prose.
    assign_rx = re.compile(
        r"(--model[= ]+['\"]?claude|\bmodel\s*[:=]\s*['\"]claude-|\"model\"\s*:\s*\"claude-|"
        r"(ANTHROPIC_MODEL|CLAUDE_CODE_SUBAGENT_MODEL)=['\"]?claude)", re.I)
    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts or "trial-m3-backup" in p.parts:
            continue
        if p.suffix not in (".js", ".mjs", ".ts", ".sh", ".py", ".json") or p.name.endswith(".bak"):
            continue
        if p.name in ("apply_trial_profile.py", "trial_gate.py", "session_review.py", "test_trial_profile.py"):
            continue  # the guards themselves name the patterns they forbid
        try:
            for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                if assign_rx.search(line):
                    findings.append(f"{p.relative_to(root)}:{i}: {line.strip()[:140]}")
        except OSError:
            continue
    ok.append("tree scan: .js/.ts/.sh/.py/.json model assignments")

    dotenv = root / ".env"
    if dotenv.exists():
        for line in dotenv.read_text().splitlines():
            if re.match(r"^\s*GOOGLE_API_KEY\s*=\s*\S", line):
                findings.append(".env GOOGLE_API_KEY set: Gemini image-gen is a non-M3 inference path")
            if re.match(r"^\s*ANTHROPIC_(API_KEY|AUTH_TOKEN)\s*=\s*\S", line):
                findings.append(".env holds a frontier Anthropic credential")

    for line in ok:
        print(f"  PASS  {line}")
    for line in findings:
        print(f"  FAIL  {line}")
    print(f"check: {len(ok)} pass, {len(findings)} fail -> {'NO FRONTIER MODEL REACHABLE' if not findings else 'NOT CLEAN'}")
    return 0 if not findings else 1


# ── operator-owned copy (the portal's source of truth) ───────────────────────
#
# config/trial.json lives in the civ tree, which the AiCIV can write. The portal must not trust it:
# provisioning publishes an identical copy OUTSIDE the civ tree (root-owned when run as root) and points
# the portal's TRIAL_CONFIG_PATH at it. Conversion then updates that copy from itself, never from the
# civ's copy, so a civ that edits its own file cannot lift the portal's 402.

def operator_copy_target(root: Path, dest: str | None) -> Path | None:
    if not dest:
        return None
    d = Path(dest).expanduser().resolve()
    try:
        d.relative_to(root.resolve())
    except ValueError:
        return d
    raise SystemExit(f"REFUSED: --operator-copy {d} is inside the civ tree; the AiCIV could rewrite it. "
                     "Use a path outside it (e.g. /etc/aiciv/<civ>/trial.json).")


def publish_operator_copy(dest: Path, rec: dict) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if os.geteuid() == 0:
        os.chown(dest.parent, 0, 0)
        os.chmod(dest.parent, 0o755)
    trial_state._atomic_write_json(dest, rec)   # 0644, atomic replace
    if os.geteuid() == 0:
        os.chown(dest, 0, 0)
    owner = "root" if os.geteuid() == 0 else f"uid {os.geteuid()} (run as root in production)"
    log(f"operator copy -> {dest} (owner {owner}); point the portal's TRIAL_CONFIG_PATH here")


# ── convert ──────────────────────────────────────────────────────────────────

def notify_partner_converted(root: Path) -> None:
    """Tell the reseller partner (config/partner.json notify_emails). Once; never fails convert."""
    try:
        import partner_notify  # sibling tool
        r = partner_notify.notify(root, "converted", "The operator converted this trial to paid.")
        log(f"partner notification (converted): {r.get('result')}"
            + (f" ({r['why_queued']})" if r.get("why_queued") else ""))
    except Exception as e:  # noqa: BLE001
        log(f"partner notification skipped: {e}")


def convert(root: Path, restore_models: bool, op_copy: Path | None = None) -> int:
    if op_copy is not None:
        src = op_copy if op_copy.exists() else trial_state.trial_path(root)
        if src.exists():
            rec = json.loads(src.read_text())
            rec["trial"] = False
            rec["converted_at"] = trial_state.iso(trial_state.utcnow())
            publish_operator_copy(op_copy, rec)
    if trial_state.trial_path(root).exists():
        trial_state.convert(root)
        log('config/trial.json -> "trial": false (portal and AiCIV ungate immediately)')
        notify_partner_converted(root)
    else:
        log("no config/trial.json; nothing to convert")
    if not restore_models:
        log("model routing left on M3 (pass --restore-models to return to the paid default)")
        return 0
    bak = root / ".claude/settings.json.pre-trial-m3.bak"
    if bak.exists():
        shutil.copy2(root / ".claude/settings.json", root / ".claude/settings.json.trial-m3.bak")
        shutil.copy2(bak, root / ".claude/settings.json")
        log("settings.json restored from pre-trial backup (trial copy kept as settings.json.trial-m3.bak)")
    backup = load_json(root / "config/trial-m3-backup/agent-models.json", {})
    for rel, orig in backup.items():
        f = root / rel
        if f.exists():
            t = f.read_text()
            f.write_text(t.replace("model: inherit", f"model: {orig}", 1))
    log(f"restored {len(backup)} agent model pins")
    prof = root / "config/model_profile.json"
    if prof.exists():
        d = load_json(prof, {})
        d.update({"locked": False, "unlocked_at": now_iso()})
        write_text(prof, json.dumps(d, indent=2) + "\n")
    lm = root / "config/launch_model.txt"
    if lm.exists():
        lm.rename(lm.with_name("launch_model.txt.trial-m3"))
    sw = root / "tools/model_switch.sh"
    if sw.exists():
        subprocess.run(["bash", str(sw), "default", "--reason", "trial converted"],
                       env={**os.environ, "CIV_ROOT": str(root)})
    return 0


# ── main ─────────────────────────────────────────────────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="trial-m3 flavor setup")
    ap.add_argument("cmd", choices=["apply", "check", "convert"])
    ap.add_argument("--root", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--reset-clock", action="store_true")
    ap.add_argument("--restore-models", action="store_true")
    ap.add_argument("--operator-copy", default=os.environ.get("TRIAL_OPERATOR_COPY") or None,
                    help="publish the trial record OUTSIDE the civ tree for the portal (TRIAL_CONFIG_PATH)")
    a = ap.parse_args(argv)
    root = trial_state.civ_root(a.root).resolve()
    if a.operator_copy is None and a.cmd == "convert":
        # Converting must flip the copy the portal and the hooks actually read.
        a.operator_copy = trial_state.configured_record_path(root)[0] or None
    op_copy = operator_copy_target(root, a.operator_copy)

    if a.cmd == "check":
        return check(root)
    if a.cmd == "convert":
        return convert(root, a.restore_models, op_copy)

    s = Seams(a.dry_run)
    s.operator_copy = op_copy
    s.load_partner(root)
    miss = s.missing()
    if miss and not a.dry_run:
        print("REFUSED: provisioning seams not filled: " + ", ".join(miss), file=sys.stderr)
        print("The trial must never fall back to a frontier model. Fill the seams and re-run.", file=sys.stderr)
        return 2
    if a.dry_run and miss:
        log("dry-run with unfilled seams: " + ", ".join(miss))
        s.base_url = s.base_url or "<M3_ROUTER_BASE_URL>"
    log(f"applying profile {PROFILE} to {root}")
    step_router_seam(root, s)
    step_model_lock(root, s)
    step_settings(root, s)
    step_agent_pins(root, s)
    step_rail_b_env(root, s)
    step_trial_clock(root, s, a.reset_clock)
    if op_copy is not None and not a.dry_run:
        if op_copy.exists() and not a.reset_clock:
            log(f"operator copy {op_copy} kept (it is authoritative; --reset-clock republishes it)")
        else:
            publish_operator_copy(op_copy, json.loads(trial_state.trial_path(root).read_text()))
    step_grounding(root, s)
    if a.dry_run:
        log("dry-run complete; nothing written")
        return 0
    log("verifying...")
    return check(root)


if __name__ == "__main__":
    sys.exit(main())
