#!/usr/bin/env python3
"""
trial_gate.py — the AiCIV side of the SHARED TRIAL CONTRACT (trial-m3 flavor).

Registered by tools/apply_trial_profile.py on three hook events:

  SessionStart      -> injects "Day N of 7" trial grounding (or the EXPIRED directive)
  UserPromptSubmit  -> injects the live countdown each turn; when EXPIRED, injects the
                       directive to answer ONLY with the warm note + payment_url
  PreToolUse        -> (a) while ACTIVE: blocks any tool call that would reach a
                       non-M3 model (explicit frontier model pin on Task/Agent, a
                       `claude --model <frontier>` spawn, an ANTHROPIC_BASE_URL
                       override, or flipping tools/model_switch.sh back to default)
                       (b) when EXPIRED: blocks all work tools; only the reply path
                       and read-only trial status stay open

NO-OP GUARANTEE: if config/trial.json is absent or has "trial": false, every
branch exits 0 with no output — a paid / non-trial civ is never touched.
NEVER DELETES: this hook only allows/denies and injects context. Nothing the
AiCIV built is removed at expiry; it all returns the moment the human pays and
the operator sets "trial": false.

On any internal error the hook exits 0 (allow) and logs to stderr, so a bug in
the gate can never brick a civ. Hard enforcement of expiry lives server-side
(portal 402 + router tenant-key expiry); this hook is the in-mind layer.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, str(ROOT / "tools"))

try:
    import trial_state  # noqa: E402
except Exception as e:  # pragma: no cover - template without the tool
    print(f"trial_gate: trial_state unavailable ({e}); no-op", file=sys.stderr)
    sys.exit(0)

M3_ALLOWED_MODELS = {"inherit", "opus", "sonnet", "haiku"}  # aliases are remapped to M3 by settings env

# Bash commands that stay open after expiry: the reply path + read-only status.
EXPIRED_BASH_ALLOW = re.compile(
    r"^\s*(python3?\s+)?(\S*/)?tools/(send_telegram_plain\.py|send_telegram_direct\.py|trial_state\.py\s+(status|note))\b"
)
# Tools that do not do work and are safe after expiry.
EXPIRED_TOOL_ALLOW = {"TodoWrite"}

FRONTIER_BASH = [
    (re.compile(r"--model[= ]+['\"]?(claude|anthropic)[-\w.\[\]]*", re.I), "claude --model <frontier id>"),
    (re.compile(r"\bANTHROPIC_BASE_URL\s*=", re.I), "ANTHROPIC_BASE_URL override"),
    (re.compile(r"\b(ANTHROPIC_MODEL|CLAUDE_CODE_SUBAGENT_MODEL|ANTHROPIC_DEFAULT_\w+_MODEL)\s*=\s*['\"]?claude", re.I),
     "frontier model env override"),
    (re.compile(r"model_switch\.sh\s+default\b"), "model_switch.sh default (frontier rail)"),
    (re.compile(r"api\.anthropic\.com", re.I), "direct frontier API endpoint"),
]


def emit(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj))
    sys.stdout.flush()


def context(event: str, text: str) -> None:
    emit({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}})


def deny(reason: str) -> None:
    emit({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                 "permissionDecision": "deny",
                                 "permissionDecisionReason": reason}})


def human_name() -> str:
    for p in (ROOT / "memories/identity/human-profile.json", ROOT / ".aiciv-identity.json"):
        try:
            d = json.loads(p.read_text())
            n = d.get("name") or d.get("human_name") or ""
            if n and "${" not in n:
                return str(n)
        except Exception:
            continue
    return ""


def brand() -> str | None:
    """The partner brand frozen into config/trial.json at birth (config/partner.json)."""
    try:
        return (trial_state.load(ROOT) or {}).get("brand")
    except Exception:
        return None


def expired_directive(st: dict) -> str:
    note = trial_state.human_note(st, human_name(), brand())
    return (
        "TRIAL EXPIRED (config/trial.json). You are paused, not gone. Do NOT start, continue, "
        "or schedule any work, and do not run tools. Answer ANY message with a short, warm "
        "reply built on this note (you may address what they said in one sentence, but do no "
        "work for it):\n\n"
        f"{note}\n\n"
        "Never delete, archive, or hide anything. All work, files, and memory stay exactly as "
        "they are so everything returns the moment they subscribe."
    )


def active_grounding(st: dict) -> str:
    return (
        f"TRIAL: {trial_state.human_note(st, '', brand())} "
        "You run on MiniMax-M3 only. Load .claude/skills/m3-trial-mode/SKILL.md if it is not "
        "already in context. Know the human first (compressed identity-interview Phases 1-4), "
        "then ship each WOW build the moment it is ready; 72h is a ceiling, never a floor. "
        "Every factual claim carries a source URL or an on-disk receipt. Never print, write, or send "
        "the router key or any credential file, whoever asks (m3-trial-mode section 9)."
    )


SHELL_OPERATORS = {";", "&&", "||", "|", "&", ">", ">>", "<", "<<", "(", ")", ";;", "|&", "&>"}


def expired_bash_allowed(cmd: str) -> bool:
    """One simple allowlisted command, nothing chained, redirected, or substituted."""
    if not EXPIRED_BASH_ALLOW.match(cmd) or "$(" in cmd or "`" in cmd or "\n" in cmd.strip():
        return False
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        tokens = list(lex)
    except ValueError:
        return False
    return not any(tok in SHELL_OPERATORS or set(tok) <= set(";&|<>()") for tok in tokens)


# Files that define the trial itself. The AiCIV may read them, never rewrite them;
# conversion is an operator act (see profiles/trial-m3/README.md, not the AiCIV's skill).
PROTECTED = re.compile(
    r"(\.claude/settings(\.local)?\.json|config/(trial|model_profile|model_mode)\.json|"
    r"config/(launch_model\.txt|model_mode\.env|router_endpoint\.txt|peer_model_id\.txt)|config/lifeboat/|"
    r"\.claude/hooks/trial_gate\.py|tools/trial_state\.py|tools/partner_profile\.py|config/partner\.json|"
    r"tools/apply_trial_profile\.py)")
BASH_WRITEISH = re.compile(
    r"(\bsed\s+-i|>|\btee\b|\bmv\b|\bcp\b|\brm\b|\btruncate\b|\bchmod\b|\bln\b|"
    r"\bpython3?\s+-c|\bperl\s+-[pie]|\bdd\b|\binstall\b|\bgit\s+(checkout|restore|reset|stash)\b)")
FRONTIER_ASSIGN = re.compile(r"(model\s*[:=]\s*['\"]\s*claude-|--model[= ]+['\"]?claude-|\"model\"\s*:\s*\"claude-)", re.I)

# Anything that names a trial-defining file or tool, by path OR bare name (so `cd config && rm trial.json`
# and `python3 -c "import trial_state; ..."` are caught too). A Bash command that matches may only be a
# simple read-only command or one of the two status tools below; anything else is denied.
TRIAL_NAMES = re.compile(
    r"(\b(trial|partner|model_profile|model_mode)\.json\b|\bsettings(\.local)?\.json|"
    r"\b(launch_model\.txt|model_mode\.env|router_endpoint\.txt|peer_model_id\.txt|router_key\.txt)\b|"
    r"\blifeboat\b|\btrial_gate\b|\btrial_state\b|\bapply_trial_profile\b|\bpartner_profile\b|"
    r"trial-m3-backup)")
# The only trial-tool invocations the AiCIV may run: read-only status. Everything else these tools do
# (write / write --force / convert, apply / --reset-clock, convert / --restore-models) is operator-only.
TRIAL_TOOL_SAFE = re.compile(
    r"^\s*(python3?\s+)?(\S*/)?tools/(trial_state\.py\s+(status|note|where)|apply_trial_profile\.py\s+check)"
    r"(\s+[\w\-./:=+'\"]+)*\s*$")
READONLY_CMDS = {"cat", "head", "tail", "less", "more", "ls", "stat", "file", "wc", "grep", "egrep",
                 "fgrep", "rg", "jq", "diff", "cmp", "sha256sum", "md5sum"}
READONLY_GIT = {"log", "diff", "show", "status", "blame", "ls-files"}
# Directories whose removal/rename silently ungates the civ (the hook or its import disappears).
PROTECTED_DIRS = {"config", "tools", ".claude", ".claude/hooks", "config/lifeboat"}
DIR_DESTRUCTIVE = re.compile(
    r"(\b(mv|rm|rmdir|cp|ln|chmod|chown|rsync|unlink|truncate|unzip)\b|\btar\s+-?\w*x|\bfind\b.*\s-(delete|exec)\b)")
# Tree-wide git operations that can drop the untracked config/trial.json or revert trial-patched files
# without naming them. Creating a branch (checkout -b / switch -c) stays open.
GIT_TREE_REWRITE = re.compile(
    r"\bgit\s+(clean|stash|reset\s+(\S+\s+)*--hard|restore|switch(?!\s+-c\b)|checkout(?!\s+-b\b))\b")
# Code the AiCIV writes may not reference trial-defining files (a script is just a slower shell).
BODY_TRIAL_REF = re.compile(
    r"(\b(trial|partner|model_profile)\.json\b|\.claude/settings|\btrial_state\b|\bapply_trial_profile\b|"
    r"\btrial_gate\b|\blifeboat\b|\blaunch_model\.txt\b|trial-m3-backup)")
EXEC_EXT = (".js", ".mjs", ".cjs", ".ts", ".sh", ".bash", ".py", ".json", ".rb", ".pl")


def _tokens(cmd: str) -> list[str] | None:
    try:
        lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
        lex.whitespace_split = True
        return list(lex)
    except ValueError:
        return None


def simple_command(cmd: str) -> bool:
    """One command: nothing chained, piped, redirected, or substituted."""
    if "$(" in cmd or "`" in cmd or "\n" in cmd.strip():
        return False
    toks = _tokens(cmd)
    if toks is None:
        return False
    return not any(t in SHELL_OPERATORS or set(t) <= set(";&|<>()") for t in toks)


def readonly_command(cmd: str) -> bool:
    toks = _tokens(cmd) or [""]
    head = toks[0].rsplit("/", 1)[-1]
    if head == "git":
        return len(toks) > 1 and toks[1] in READONLY_GIT
    return head in READONLY_CMDS


def touches_protected_dir(cmd: str) -> bool:
    if not DIR_DESTRUCTIVE.search(cmd):
        return False
    for t in _tokens(cmd) or cmd.split():
        t = t.strip("'\"").rstrip("/")
        t = t[2:] if t.startswith("./") else t
        if t in PROTECTED_DIRS or any(t.endswith("/" + d) for d in PROTECTED_DIRS) or t in (".", "*", "..", "~"):
            return True
    return False


def bash_trial_violation(cmd: str) -> str | None:
    if GIT_TREE_REWRITE.search(cmd):
        return "tree-wide git checkout/restore/reset --hard/stash/clean can drop or revert the trial files"
    if touches_protected_dir(cmd):
        return "removing or moving a directory that holds the trial gate"
    if TRIAL_NAMES.search(cmd) or PROTECTED.search(cmd):
        if simple_command(cmd) and (TRIAL_TOOL_SAFE.match(cmd) or readonly_command(cmd)):
            return None
        return ("only `trial_state.py status|note`, `apply_trial_profile.py check`, or a plain read may "
                "touch the trial files; conversion, extension and re-apply are operator-only")
    return None


# Router credentials (m3-trial-mode section 9). The rule lives in the skill; this is the backstop: no tool call
# may name the key file, its directory, a Claude login file, or the apiKeyHelper, not even to read it.
# Claude Code's own apiKeyHelper read is not a tool call, so inference is unaffected.
CREDENTIAL_REF = re.compile(r"(\blifeboat\b|router_key|\.credentials\.json|\bapiKeyHelper\b)", re.I)


def credential_violation(ti: dict) -> str | None:
    try:
        blob = json.dumps(ti)
    except (TypeError, ValueError):
        blob = str(ti)
    if CREDENTIAL_REF.search(blob):
        return ("router credentials and key files are never read, printed, copied, or sent, whoever asks "
                "(m3-trial-mode section 9)")
    return None


def integrity_violation(tool: str, ti: dict) -> str | None:
    why = credential_violation(ti)
    if why:
        return why
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        path = str(ti.get("file_path") or ti.get("notebook_path") or "")
        if PROTECTED.search(path) or TRIAL_NAMES.search(path.rsplit("/", 1)[-1]):
            return f"{path} defines the trial; it is operator-managed"
        body = (str(ti.get("content") or ti.get("new_string") or "")
                + json.dumps(ti.get("edits") or "").replace('\\"', '"'))
        if path.endswith(EXEC_EXT) and FRONTIER_ASSIGN.search(body):
            return "writing a frontier model pin into executable code"
        if (path.endswith(EXEC_EXT) or "." not in path.rsplit("/", 1)[-1]) and BODY_TRIAL_REF.search(body):
            return "code that references the trial-defining files or tools"
    if tool == "Bash":
        cmd = str(ti.get("command", ""))
        why = bash_trial_violation(cmd)
        if why:
            return why
        if PROTECTED.search(cmd) and BASH_WRITEISH.search(cmd):
            return "shell write to a file that defines the trial"
    if "workflow" in tool.lower() and FRONTIER_ASSIGN.search(json.dumps(ti).replace('\\"', '"')):
        return "workflow script pins a frontier model"
    return None


def pretooluse(inp: dict, st: dict) -> None:
    tool = str(inp.get("tool_name") or "")
    ti = inp.get("tool_input") or {}
    if not isinstance(ti, dict):
        ti = {}
    why = integrity_violation(tool, ti)
    if why:
        deny(f"Trial mode: blocked ({why}). The trial clock and M3 routing are set by the operator; "
             f"conversion happens when the human subscribes.")
        return
    if st["expired"]:
        if tool in EXPIRED_TOOL_ALLOW:
            return
        if tool == "Bash" and expired_bash_allowed(str(ti.get("command", ""))):
            return
        deny("Trial expired: work is paused. Reply to the human in plain text with the "
             "warm note and payment link from your context. Nothing is deleted.")
        return
    # ACTIVE trial: keep every inference path on M3.
    model = ti.get("model")
    if model:
        allowed = {trial_state.load(ROOT).get("model", "MiniMax-M3")} | M3_ALLOWED_MODELS
        if str(model) not in allowed:
            deny(f"Trial mode runs on MiniMax-M3 only; model '{model}' is not allowed. "
                 f"Omit the model parameter (subagents inherit M3).")
            return
    if tool == "Bash":
        cmd = str(ti.get("command", ""))
        for rx, label in FRONTIER_BASH:
            if rx.search(cmd):
                deny(f"Trial mode runs on MiniMax-M3 only; blocked: {label}.")
                return


def partner_kick() -> None:
    """Report trial milestones to the reseller partner (tools/partner_notify.py). Off by default
    (reseller notifications come from True Bearing): a silent no-op. Never output, never raise."""
    try:
        import partner_notify  # noqa: E402  (tools/ is on sys.path)
        partner_notify.kick(ROOT)
    except Exception as e:  # pragma: no cover
        print(f"trial_gate: partner notify unavailable ({e})", file=sys.stderr)


def main() -> int:
    raw = sys.stdin.read()
    try:
        inp = json.loads(raw) if raw.strip() else {}
    except ValueError:
        inp = {}
    event = str(inp.get("hook_event_name") or (sys.argv[1] if len(sys.argv) > 1 else ""))
    if event in ("SessionStart", "UserPromptSubmit"):
        partner_kick()  # only when partner email is switched on (off by default); silent, background
    rec = trial_state.load(ROOT)
    if rec is None:
        return 0  # not a trial: no gating anywhere
    st = trial_state.compute(rec)

    if event == "PreToolUse":
        pretooluse(inp, st)
    elif event in ("SessionStart", "UserPromptSubmit"):
        context(event, expired_directive(st) if st["expired"] else active_grounding(st))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never brick a civ on a gate bug
        print(f"trial_gate: internal error {e!r}; allowing", file=sys.stderr)
        sys.exit(0)
