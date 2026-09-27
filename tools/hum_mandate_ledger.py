#!/usr/bin/env python3
"""
HUM Mandate Ledger — the DRIVE-TO-DONE bookkeeping engine for workflows/hum.js REPAIR phase.

Corey 2026-06-27 (verbatim): "when hum sees a problem they should be cleared to fix it or
mandate and confirm that you have an infra lead fix it." THE FAILURE it cures: a defect HUM
flags is re-flagged forever (the GROUNDING-COMPLETENESS anchor false-positive was vp-drift-flagged
to fleet-lead 4x in one day WITHOUT a fix landing — it took a Corey directive to actually fix it).
An immune system that only FLAGS (and re-flags forever) is a smoke detector with no sprinklers.

This tool is the deterministic substrate that lets HUM DRIVE each confirmed defect to DONE via two
sanctioned paths on a CONFIRMED problem:
  (A) CLEARED-TO-FIX     — a safe, reversible, born-provisional organ HUM is authorized to repair
                           DIRECTLY this run (default: wwcw-ruleset-append). HUM fires it; it self-
                           RESOLVES on a later fire when the defect no longer appears.
  (B) MANDATE-AND-CONFIRM — HUM mandates the OWNING VP fix it, RECORDS the mandate here, RE-CHECKS
                           that exact defect each subsequent fire, and ESCALATES LOUD if still-open.

THE KEY RULE (enforced deterministically here — NOT trusted to a judging mind):
  A defect HUM has flagged >= 2 times WITHOUT a fix MUST become a mandate-and-confirm (with a
  re-check), NEVER a 3rd identical bare flag.

WHY A TOOL (system-over-symptom): the COUNT + the >=2 threshold + the cross-fire re-check are PURE
deterministic bookkeeping — exactly the kind of work that must NOT be an LLM's job (an LLM cannot be
trusted to count flag-history across fires). This is the same discipline that put GROUNDING-
COMPLETENESS *detection* in tools/session_review.py while the *judging* stays in the HUM mind.
hum.js shells this tool; the judging stays in the mind, the counting stays in the tool.

DEFECT IDENTITY — the load-bearing insight: a defect is identified by a STABLE defect_key =
organ + '::' + normalize(target), where normalize() strips the per-cycle noise (timestamps, dates,
session/cycle ids, turn-indices, (N/M) fraction counts, long hex ids, bare numbers) so the SAME
defect produces the SAME key fire after fire even as the cycle-id changes. Without a stable key,
"have I seen this before?" is unanswerable and the re-flag-forever bug is structural.

I/O CONTRACT (called by workflows/hum.js REPAIR phase):
  python3 tools/hum_mandate_ledger.py --routes-json <path> [--session <id>] [--fire-ts <iso8601>] \
      [--ledger <path>] [--cleared-organs wwcw-ruleset-append,...] --json
    --routes-json : path to a JSON file = [{organ,target,why,live}, ...]  (this fire's CONFIRMED defects)
    --session     : the graded session id (audit only)
    --fire-ts     : the UTC timestamp of this fire (optional; defaults to now-UTC computed here)
    --ledger      : ledger path (default .claude/team-leads/mind/memory/hum-mandate-ledger.json)
    --cleared-organs : comma-list of organs HUM may fix directly (default: wwcw-ruleset-append)
  Reads + UPDATES + WRITES the ledger (atomic), prints a disposition JSON to stdout. The disposition
  tells hum.js which routes are cleared-to-fix vs bare-flag vs mandate, which open entries RESOLVED
  this fire (the fix landed / defect did not recur), and which are STILL-OPEN-AFTER-MANDATE (escalate).

  --selftest : run a synthetic battery proving the >=2 rule + re-check-resolve + still-open escalation,
               then exit non-zero on any failure (behavioral proof, per the BUILD-VERIFICATION LESSON
               in workflows/hum.js — node --check / py_compile are necessary but NOT sufficient).

OWNER: mind-lead (HUM's owner in the origin civ). Companion to tools/session_review.py.
Reviewed POST-HOC by workflow-lead (HOW-WELL) + qa-lead (WHETHER).

PORTABILITY (taught upstream from origin civ A-C-Gee, 2026-07-04):
  Ledger path defaults to origin-civ layout. In your fork, override via env var
  HUM_MANDATE_LEDGER, or pass --ledger, or just create the parent dir yourself.
  The tool is otherwise substrate-agnostic — pure deterministic bookkeeping on JSON.
"""

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone

# Default ledger path (origin-civ layout). Override via HUM_MANDATE_LEDGER env or --ledger.
DEFAULT_LEDGER = os.environ.get(
    "HUM_MANDATE_LEDGER",
    ".claude/team-leads/mind/memory/hum-mandate-ledger.json",
)
DEFAULT_CLEARED = ["wwcw-ruleset-append"]
LEDGER_VERSION = 1

# THE KEY RULE threshold: prior flag_count >= MANDATE_AT (encounters before this one) => this
# encounter MUST be a mandate, never a 3rd identical bare flag. 2 prior bare flags => the 3rd
# encounter mandates.
MANDATE_AT = 2

# Bound the per-entry history ring so the ledger cannot grow unbounded.
HISTORY_MAX = 12

# ---------------------------------------------------------------------------
# DEFECT KEY — the stable cross-fire fingerprint. Strips per-cycle noise so the SAME defect maps
# to the SAME key fire after fire (the precondition for counting repeats at all).
# ---------------------------------------------------------------------------
_TS_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}t?\d{0,2}:?\d{0,2}:?\d{0,2}z?\b", re.I)  # iso-ish ts/date
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_CYCLE_RE = re.compile(r"\b(?:cycle|session|sid|boop|fire|run)\s*[:#=]?\s*[0-9a-f._-]{4,}\b", re.I)
_TURN_RE = re.compile(r"\bturns?\s*[:#=]?\s*\d+\b", re.I)
_FRAC_RE = re.compile(r"\(\s*\d+\s*/\s*\d+\s*\)")  # (1/10) per-doc-haikus(1/10)
_HEXID_RE = re.compile(r"\b[0-9a-f]{6,}\b", re.I)  # long hex ids (session/cursor ids)
_NUM_RE = re.compile(r"\b\d+\b")
_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def defect_key(organ, target):
    """organ + '::' + normalized-target. Deterministic + stable across cycles."""
    organ = (organ or "?").strip().lower()
    t = (target or "").lower()
    t = _TS_RE.sub(" ", t)
    t = _DATE_RE.sub(" ", t)
    t = _CYCLE_RE.sub(" ", t)
    t = _TURN_RE.sub(" ", t)
    t = _FRAC_RE.sub(" ", t)
    t = _HEXID_RE.sub(" ", t)
    t = _NUM_RE.sub(" ", t)
    t = _NONWORD_RE.sub(" ", t).strip()
    t = " ".join(t.split())[:120]  # bounded prefix so tail noise doesn't fork the key
    return "{}::{}".format(organ, t)


# ---------------------------------------------------------------------------
# OWNING VP — who must fix a mandated defect. Parsed from the target's leading "vp-id:" if present
# (the route convention, e.g. "fleet-lead: grounding INCOMPLETE ..."), else mapped by organ.
# ---------------------------------------------------------------------------
_VP_RE = re.compile(r"^\s*([a-z][a-z0-9-]*-(?:lead|infra)|hermes-infra)\s*:", re.I)
_ORGAN_DEFAULT_VP = {
    "vp-drift-flag": "owning-vp",
    "auto-consolidate": "mind-lead",
    "skill-forge": "fleet-lead",
    "integration": "mind-lead",
    "canon_append": "mind-lead",
    "wwcw-ruleset-append": "hum-self",
}


def owning_vp(organ, target):
    m = _VP_RE.match(target or "")
    if m:
        return m.group(1).lower()
    return _ORGAN_DEFAULT_VP.get((organ or "").lower(), "owning-vp")


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_ledger(path):
    if not os.path.exists(path):
        return {"version": LEDGER_VERSION, "entries": []}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
            return {"version": LEDGER_VERSION, "entries": []}
        return data
    except (ValueError, OSError):
        # Corrupt/unreadable ledger MUST NOT crash HUM — fail-soft to empty (the re-check simply
        # finds no prior state this fire; the next fire rebuilds). FAIL-LOUD is reported in stdout.
        return {"version": LEDGER_VERSION, "entries": [], "_load_error": True}


def write_ledger(path, data):
    """Atomic write (tmp + os.replace) so a crash mid-write cannot corrupt the count substrate."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", prefix=".hum-mandate-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def _index(entries):
    return {e.get("defect_key"): e for e in entries if isinstance(e, dict) and e.get("defect_key")}


def process(routes, ledger, cleared_organs, fire_ts, session):
    """
    The deterministic state machine. Returns (updated_ledger, disposition).

    disposition = {
      cleared_to_fix: [route-with-key...],   # HUM fixes DIRECTLY this run (path A)
      bare_flags:     [route-with-key...],    # 1st/2nd encounter — file a flag (existing behavior)
      mandates:       [mandate...],           # >=2 prior OR already-mandated — MANDATE-AND-CONFIRM (path B)
      resolved:       [{defect_key, organ, owner, flag_count, was_status}...],  # absent this fire => fix landed
      still_open_after_mandate: [{defect_key, owner, flag_count, escalation_level, mandated_at}...],
      open_total, ledger_version, session, fire_ts, load_error
    }
    """
    cleared_set = set(o.strip().lower() for o in cleared_organs if o.strip())
    entries = ledger.get("entries", [])
    by_key = _index(entries)

    # PRE-FIRE status snapshot (timestamp-INDEPENDENT escalation — do NOT gate escalation on a
    # ts comparison: two fires inside the same wall-clock second would collide and suppress the
    # escalation, exactly the fragility the hourly-boop cadence usually hides). An entry whose
    # status was ALREADY "MANDATED" BEFORE this fire's processing, and is STILL seen this fire, is
    # still-open-after-mandate => escalate, no matter how close the fires are in time.
    pre_status = {k: (e.get("status") if isinstance(e, dict) else None) for k, e in by_key.items()}

    cleared_to_fix = []
    bare_flags = []
    mandates = []
    seen_keys = set()

    for r in routes:
        if not isinstance(r, dict):
            continue
        organ = str(r.get("organ", "?")).lower()
        target = str(r.get("target", "") or "")
        why = str(r.get("why", "") or "")
        key = defect_key(organ, target)
        seen_keys.add(key)
        ent = by_key.get(key)
        prior_count = int(ent.get("flag_count", 0)) if ent else 0
        prior_status = ent.get("status") if ent else None

        rk = {"organ": organ, "target": target[:200], "why": why[:240], "defect_key": key,
              "live": bool(r.get("live", False))}

        if organ in cleared_set:
            # PATH A — CLEARED-TO-FIX. HUM repairs directly this run; tracked so recurrence is visible.
            disp = "cleared-to-fix"
            new_status = "OPEN"  # active; re-check RESOLVES it on a later fire when it stops appearing
        else:
            owner = owning_vp(organ, target)
            rk["owning_vp"] = owner
            # THE KEY RULE: already mandated and still here, OR prior_count >= 2 => MANDATE-AND-CONFIRM.
            if prior_status == "MANDATED" or prior_count >= MANDATE_AT:
                disp = "mandate"
                new_status = "MANDATED"
            else:
                disp = "bare-flag"
                new_status = "OPEN"

        ent = _upsert(by_key, entries, key, organ, target, why, fire_ts, session, disp, new_status,
                      prior_count, prior_status)

        if disp == "cleared-to-fix":
            cleared_to_fix.append(rk)
        elif disp == "bare-flag":
            bare_flags.append(rk)
        else:  # mandate
            rk["flag_count"] = ent["flag_count"]
            rk["escalation_level"] = ent["escalation_level"]
            rk["mandated_at"] = ent["mandated_at"]
            rk["newly_mandated"] = (prior_status != "MANDATED")
            mandates.append(rk)

    # RE-CHECK every existing OPEN/MANDATED entry against THIS fire's seen_keys.
    resolved = []
    still_open_after_mandate = []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        key = ent.get("defect_key")
        status = ent.get("status")
        if status not in ("OPEN", "MANDATED"):
            continue
        if key in seen_keys:
            # Still present. If it was MANDATED BEFORE this fire (pre_status snapshot) and is STILL
            # here => still-open-after-mandate => escalate LOUD. Timestamp-INDEPENDENT (the pre-fire
            # snapshot, not a ts compare — robust to same-second fires).
            if pre_status.get(key) == "MANDATED":
                ent["escalation_level"] = int(ent.get("escalation_level", 0)) + 1
                ent["last_seen"] = fire_ts
                _push_history(ent, fire_ts, "escalate(still-open-after-mandate)")
                still_open_after_mandate.append({
                    "defect_key": key,
                    "organ": ent.get("organ"),
                    "owning_vp": ent.get("owning_vp"),
                    "target": (ent.get("target") or "")[:160],
                    "flag_count": int(ent.get("flag_count", 0)),
                    "escalation_level": int(ent.get("escalation_level", 0)),
                    "mandated_at": ent.get("mandated_at"),
                })
        else:
            # Absent this fire => the fix landed (or the defect did not recur). DRIVE-TO-DONE: close it.
            ent["status"] = "RESOLVED"
            ent["resolved_at"] = fire_ts
            ent["resolution"] = "absent-this-fire (fix landed or defect did not recur)"
            _push_history(ent, fire_ts, "resolve(absent)")
            resolved.append({
                "defect_key": key,
                "organ": ent.get("organ"),
                "owning_vp": ent.get("owning_vp"),
                "flag_count": int(ent.get("flag_count", 0)),
                "was_status": status,
            })

    open_total = sum(1 for e in entries if isinstance(e, dict) and e.get("status") in ("OPEN", "MANDATED"))
    ledger["entries"] = entries
    ledger["version"] = LEDGER_VERSION
    ledger["last_fire_ts"] = fire_ts

    disposition = {
        "cleared_to_fix": cleared_to_fix,
        "bare_flags": bare_flags,
        "mandates": mandates,
        "resolved": resolved,
        "still_open_after_mandate": still_open_after_mandate,
        "open_total": open_total,
        "ledger_version": LEDGER_VERSION,
        "session": session,
        "fire_ts": fire_ts,
        "load_error": bool(ledger.get("_load_error")),
    }
    return ledger, disposition


def _upsert(by_key, entries, key, organ, target, why, fire_ts, session, disp, new_status,
            prior_count, prior_status):
    ent = by_key.get(key)
    if ent is None:
        ent = {
            "defect_key": key,
            "organ": organ,
            "owning_vp": owning_vp(organ, target),
            "target": target[:240],
            "first_seen": fire_ts,
            "flag_count": 0,
            "status": new_status,
            "mandated_at": None,
            "resolved_at": None,
            "escalation_level": 0,
            "history": [],
        }
        entries.append(ent)
        by_key[key] = ent

    # A RESOLVED entry that re-appears is REOPENED (history preserved). Its prior flag_count is
    # monotonic, so a defect that recurs after a "fix" escalates fast (its prior_count >= MANDATE_AT
    # immediately re-mandates) — recurrence-after-fix is a louder signal, not a softer one.
    ent["organ"] = organ
    ent["target"] = target[:240]
    ent["last_seen"] = fire_ts
    ent["last_why"] = why[:240]
    ent["last_disposition"] = disp
    if disp != "cleared-to-fix":
        ent["owning_vp"] = owning_vp(organ, target)

    if disp == "bare-flag" or disp == "cleared-to-fix":
        # Count each non-mandate encounter (this is what the >=2 rule reads next fire).
        ent["flag_count"] = int(ent.get("flag_count", 0)) + 1
        ent["status"] = new_status
        _push_history(ent, fire_ts, disp)
    else:  # mandate
        ent["status"] = "MANDATED"
        if not ent.get("mandated_at"):
            ent["mandated_at"] = fire_ts
        # On the encounter that FIRST mandates, count it too (so flag_count reflects total encounters).
        if prior_status != "MANDATED":
            ent["flag_count"] = int(ent.get("flag_count", 0)) + 1
        _push_history(ent, fire_ts, "mandate")
    return ent


def _push_history(ent, fire_ts, disp):
    h = ent.get("history")
    if not isinstance(h, list):
        h = []
    h.append({"ts": fire_ts, "disposition": disp})
    ent["history"] = h[-HISTORY_MAX:]


# ---------------------------------------------------------------------------
# SELFTEST — behavioral proof of the three load-bearing behaviors (per the BUILD-VERIFICATION
# LESSON in workflows/hum.js: parse-clean is necessary but NOT sufficient; only a completing
# behavioral run proves the contract).
# ---------------------------------------------------------------------------
def selftest():
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    # Use an in-memory ledger across simulated fires.
    led = {"version": LEDGER_VERSION, "entries": []}
    drift = {"organ": "vp-drift-flag",
             "target": "fleet-lead: grounding INCOMPLETE — per-doc-haikus(1/10) not present cycle aaa111",
             "why": "false-positive anchor", "live": True}

    # Fire 1: first bare flag.
    led, d1 = process([dict(drift)], led, DEFAULT_CLEARED, "2026-06-27T00:00:00Z", "s1")
    check(len(d1["bare_flags"]) == 1 and len(d1["mandates"]) == 0, "fire1 should be a bare flag")

    # Fire 2: same defect, different cycle-id => SAME key => 2nd bare flag (still bare).
    drift2 = dict(drift); drift2["target"] = drift2["target"].replace("aaa111", "bbb222")
    led, d2 = process([drift2], led, DEFAULT_CLEARED, "2026-06-27T01:00:00Z", "s2")
    check(len(d2["bare_flags"]) == 1 and len(d2["mandates"]) == 0, "fire2 should be a 2nd bare flag (same key)")

    # Fire 3: THE KEY RULE — 3rd encounter (prior_count==2) MUST become a mandate, NEVER a 3rd bare flag.
    drift3 = dict(drift); drift3["target"] = drift3["target"].replace("aaa111", "ccc333")
    led, d3 = process([drift3], led, DEFAULT_CLEARED, "2026-06-27T02:00:00Z", "s3")
    check(len(d3["bare_flags"]) == 0 and len(d3["mandates"]) == 1, "fire3 MUST mandate (>=2 prior), not bare-flag")
    check(d3["mandates"][0]["owning_vp"] == "fleet-lead", "fire3 mandate must route to fleet-lead")
    check(d3["mandates"][0]["newly_mandated"] is True, "fire3 mandate is newly_mandated")

    # Fire 4: defect STILL present after mandate => escalate LOUD (still_open_after_mandate).
    drift4 = dict(drift); drift4["target"] = drift4["target"].replace("aaa111", "ddd444")
    led, d4 = process([drift4], led, DEFAULT_CLEARED, "2026-06-27T03:00:00Z", "s4")
    check(len(d4["still_open_after_mandate"]) == 1, "fire4 still-present-after-mandate MUST escalate")
    check(d4["still_open_after_mandate"][0]["escalation_level"] == 1, "fire4 escalation_level should be 1")
    check(len(d4["mandates"]) == 1, "fire4 should re-affirm the mandate")

    # Fire 5: defect ABSENT => RESOLVED (the fix landed). DRIVE-TO-DONE closes the loop.
    led, d5 = process([], led, DEFAULT_CLEARED, "2026-06-27T04:00:00Z", "s5")
    check(len(d5["resolved"]) == 1, "fire5 absent defect MUST resolve")
    check(d5["resolved"][0]["was_status"] == "MANDATED", "fire5 resolved entry was MANDATED")
    check(d5["open_total"] == 0, "fire5 open_total should be 0 after resolve")

    # Cleared-to-fix lane: wwcw-ruleset-append is HUM's direct-fix organ, never a mandate.
    led2 = {"version": LEDGER_VERSION, "entries": []}
    wroute = {"organ": "wwcw-ruleset-append", "target": "missing rule X", "why": "decide gap", "live": True}
    for i in range(4):
        led2, dc = process([dict(wroute)], led2, DEFAULT_CLEARED, "2026-06-27T0%d:00:00Z" % i, "c%d" % i)
        check(len(dc["mandates"]) == 0, "cleared-to-fix must NEVER mandate (fire %d)" % i)
        check(len(dc["cleared_to_fix"]) == 1, "cleared-to-fix route must be in cleared lane (fire %d)" % i)

    # Distinct defects keep distinct keys (no false merge).
    led3 = {"version": LEDGER_VERSION, "entries": []}
    a = {"organ": "vp-drift-flag", "target": "infra-lead: swap not cleared", "why": "x", "live": True}
    b = {"organ": "vp-drift-flag", "target": "fleet-lead: hook missing", "why": "y", "live": True}
    led3, dd = process([a, b], led3, DEFAULT_CLEARED, "2026-06-27T05:00:00Z", "d1")
    check(len(dd["bare_flags"]) == 2, "two distinct defects => two distinct bare flags")
    check(len({e["defect_key"] for e in led3["entries"]}) == 2, "two distinct keys persisted")

    # SAME-SECOND escalation robustness (regression guard): escalation must NOT depend on a ts
    # comparison — two fires inside the same wall-clock second must still escalate a still-open mandate.
    # (Realistic targets: a space-separated 8-hex session-id per cycle, which normalize to ONE key.)
    SAMETS = "2026-06-27T06:00:00Z"
    sids = ["303ecb5f", "71a2616e", "9f3c0d12", "a1b2c3d4"]
    led4 = {"version": LEDGER_VERSION, "entries": []}
    dz = None
    for j, sid in enumerate(sids):  # 4 fires, SAME ts: fire3 mandates, fire4 must escalate
        tgt = "infra-lead: swap not cleared cycle " + sid
        led4, dz = process([{"organ": "vp-drift-flag", "target": tgt, "why": "x", "live": True}],
                           led4, DEFAULT_CLEARED, SAMETS, sid)
    check(len({e["defect_key"] for e in led4["entries"]}) == 1, "same-second: 4 cycles => ONE stable key")
    check(len(dz["still_open_after_mandate"]) == 1,
          "same-second fire MUST still escalate a still-open mandate (ts-independent)")

    if fails:
        print("SELFTEST FAILED:")
        for f in fails:
            print("  - " + f)
        return 1
    print("SELFTEST PASSED: KEY-RULE(>=2->mandate) + re-check-resolve + still-open-escalation + "
          "cleared-lane + distinct-keys all proven.")
    return 0


def main():
    ap = argparse.ArgumentParser(description="HUM mandate-ledger drive-to-done bookkeeping engine.")
    ap.add_argument("--routes-json", help="path to JSON file = [{organ,target,why,live},...]")
    ap.add_argument("--session", default="", help="graded session id (audit only)")
    ap.add_argument("--fire-ts", default="", help="UTC ts of this fire (default: now-UTC)")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help="ledger path")
    ap.add_argument("--cleared-organs", default=",".join(DEFAULT_CLEARED),
                    help="comma-list of organs HUM may fix directly (path A)")
    ap.add_argument("--json", action="store_true", help="print disposition JSON to stdout")
    ap.add_argument("--selftest", action="store_true", help="run behavioral battery + exit")
    args = ap.parse_args()

    if args.selftest:
        sys.exit(selftest())

    fire_ts = args.fire_ts.strip() or _now_iso()
    cleared = [s for s in (args.cleared_organs or "").split(",") if s.strip()]

    routes = []
    if args.routes_json:
        try:
            with open(args.routes_json, "r", encoding="utf-8") as fh:
                routes = json.load(fh)
            if not isinstance(routes, list):
                routes = []
        except (ValueError, OSError) as e:
            # FAIL-SOFT but FAIL-LOUD: no routes parsed => re-check still runs (resolve absent entries).
            print(json.dumps({"error": "routes-json unreadable: %s" % e, "cleared_to_fix": [],
                              "bare_flags": [], "mandates": [], "resolved": [],
                              "still_open_after_mandate": [], "open_total": 0}))
            sys.exit(0)

    ledger = load_ledger(args.ledger)
    ledger, disposition = process(routes, ledger, cleared, fire_ts, args.session)
    write_ledger(args.ledger, ledger)
    disposition["ledger_path"] = args.ledger
    disposition["ledger_written"] = True
    print(json.dumps(disposition, ensure_ascii=False))


if __name__ == "__main__":
    main()
