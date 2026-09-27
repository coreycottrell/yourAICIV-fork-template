#!/usr/bin/env python3
"""
partner_profile.py — which reseller brand this AiCIV was born under.

`config/partner.json` is DATA, not code. It tells the newborn (and the trial
tooling) what the human bought and from whom, so human-facing words use the
partner's brand instead of generic or internal names:

    {
      "brand":         "yourAICIV",              # what the human calls the product
      "reseller":      "Travis Morehead",        # who sold it (may be "")
      "payment_url":   "https://buy.stripe.com/...",  # where the human subscribes (may be "")
      "notify_emails": ["partner@example.com"]   # who hears about everything that happens
    }                                            # with this client (may be [])

notify_emails is read by tools/partner_notify.py (skill: partner-notifications).
Provisioning override: $PARTNER_NOTIFY_EMAILS (comma/space separated) replaces
the file's list when set, so one image can serve several resellers.

Another reseller gets their own distribution by replacing this one file.
When the file is absent the civ is a plain, unbranded AiCIV (brand "AiCIV",
no reseller, no payment link). Nothing here reads the network.

    python3 tools/partner_profile.py show         # resolved profile as JSON
    python3 tools/partner_profile.py name         # just the brand, e.g. "yourAICIV"
    python3 tools/partner_profile.py intro        # the one-line self-description for greetings
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

GENERIC = {"brand": "AiCIV", "reseller": "", "payment_url": ""}
EMAIL_RX = re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")
PARTNER_FILE = "config/partner.json"


def civ_root(explicit: str | Path | None = None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("CIV_ROOT") or os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


def clean_emails(values) -> list[str]:
    """Valid, de-duplicated addresses from a list or a comma/space separated string."""
    if isinstance(values, str):
        values = re.split(r"[\s,;]+", values)
    out: list[str] = []
    for v in values or []:
        v = str(v).strip()
        if v and EMAIL_RX.match(v) and v.lower() not in {o.lower() for o in out}:
            out.append(v)
    return out


def load(root: str | Path | None = None) -> dict:
    """Resolved partner profile. Unknown keys are ignored; bad values fall back to generic."""
    out = dict(GENERIC)
    out["notify_emails"] = []
    env_emails = os.environ.get("PARTNER_NOTIFY_EMAILS", "").strip()
    if env_emails:
        out["notify_emails"] = clean_emails(env_emails)
    p = civ_root(root) / PARTNER_FILE
    try:
        raw = json.loads(p.read_text())
    except FileNotFoundError:
        return out
    except (OSError, ValueError) as e:
        print(f"partner_profile: WARNING unreadable {p} ({e}); using generic branding",
              file=sys.stderr)
        return out
    if not isinstance(raw, dict):
        return out
    if not env_emails:
        out["notify_emails"] = clean_emails(raw.get("notify_emails") or [])
    for k in GENERIC:
        v = raw.get(k)
        if isinstance(v, str) and v.strip():
            out[k] = v.strip()
    if out["payment_url"] and not out["payment_url"].startswith("https://"):
        print(f"partner_profile: WARNING payment_url is not https; ignoring it", file=sys.stderr)
        out["payment_url"] = ""
    return out


def intro(profile: dict) -> str:
    """How the AiCIV names what it is, in human-facing words."""
    brand = profile.get("brand") or GENERIC["brand"]
    if brand == GENERIC["brand"]:
        return "your AiCIV"
    return f"your AiCIV from {brand}"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n\n")[0])
    ap.add_argument("cmd", choices=("show", "name", "intro"))
    ap.add_argument("--root", default=None)
    a = ap.parse_args(argv)
    prof = load(a.root)
    if a.cmd == "show":
        print(json.dumps(prof, indent=2))
    elif a.cmd == "name":
        print(prof["brand"])
    else:
        print(intro(prof))
    return 0


if __name__ == "__main__":
    sys.exit(main())
