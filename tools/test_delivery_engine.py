#!/usr/bin/env python3
"""
test_delivery_engine.py -- regression test for the delivery engine (apps/client-starter).

Clones a THROWAWAY client instance into a temp dir with the scaffold's own
clone_client.sh, then runs tools/delivery_engine_checks.py inside it
(in-process Flask test client; Stripe, Telegram and Resend are stubbed, no
port is bound, nothing leaves the box). The temp dir is deleted afterwards.

Coverage: the security hardening checks, the partner copies of business alerts
(PARTNER: lead / order / booking / affiliate each email the reseller partner once;
no email provider -> queued to logs/partner-outbox.jsonl and sent by the AiCIV's
tools/partner_notify.py flush through a loopback AgentMail stub), plus the automation checks (AUTO):
a contact form fires a Telegram lead alert and a welcome-workflow enrollment;
alerts for order / booking / affiliate application; Telegram down or hanging
never fails or slows the request; scheduled steps send (day 0 / 2 / 7) through
the cron endpoint, the shared processor and the in-process runner; held /
retry / unsubscribe / double-claim behaviour; workflows.json validate, load,
archive via manage.py.

    python3 tools/test_delivery_engine.py [--python PATH] [--keep]

--python   a Python that has the app dependencies (apps/client-starter/requirements.txt).
           Default: $DE_TEST_PYTHON, else ${CIV_ROOT}/apps/.venv/bin/python, else this Python.
Exit 0 = every check passed. Exit 2 = no Python with the dependencies (not a pass).
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent
SCAFFOLD = SRC / "apps" / "client-starter"
CHECKS = SRC / "tools" / "delivery_engine_checks.py"
SLUG = "de-selftest"
DEPS = "import flask, flask_wtf, dotenv, nh3, stripe"


def pick_python(explicit: str | None) -> str | None:
    root = os.environ.get("CIV_ROOT") or str(SRC)
    for cand in (explicit, os.environ.get("DE_TEST_PYTHON"),
                 str(Path(root) / "apps" / ".venv" / "bin" / "python"), sys.executable):
        if cand and Path(cand).exists():
            if subprocess.run([cand, "-c", DEPS], capture_output=True).returncode == 0:
                return cand
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--python", default=None)
    ap.add_argument("--keep", action="store_true", help="keep the temp instance for inspection")
    a = ap.parse_args(argv)

    py = pick_python(a.python)
    if not py:
        print("NOT RUN: no Python with the app dependencies. Create one with:\n"
              "  python3 -m venv apps/.venv && apps/.venv/bin/pip install --require-hashes "
              "-r apps/client-starter/requirements.txt", file=sys.stderr)
        return 2

    tmp = Path(tempfile.mkdtemp(prefix="de-test-"))
    try:
        apps = tmp / "apps"
        shutil.copytree(SCAFFOLD, apps / "client-starter",
                        ignore=shutil.ignore_patterns("__pycache__", ".env", ".setup-link", "logs",
                                                      "client.db*"))
        env = {**os.environ, "PATH": f"{Path(py).parent}:{os.environ.get('PATH', '')}",
               "CLIENT_GO_LIVE": "0"}  # never start or register the throwaway instance
        env.pop("PORTAL_PUBLIC_URL", None)
        r = subprocess.run(["bash", str(apps / "client-starter" / "clone_client.sh"), SLUG, "5190"],
                           cwd=apps, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-2000:], r.stderr[-2000:], sep="\n", file=sys.stderr)
            print("FAIL: clone_client.sh did not produce an instance", file=sys.stderr)
            return 1
        inst = apps / SLUG
        env.update({"DE_SELFTEST_INSTANCE": str(inst),
                    "CLIENT_PUBLIC_BASE_URL": f"https://{SLUG}.example.com"})
        for k in ("STRIPE_SECRET_KEY", "STRIPE_WEBHOOK_SECRET", "RESEND_API_KEY", "TELEGRAM_BOT_TOKEN",
                  "PARTNER_NOTIFY_EMAILS", "CIV_ROOT"):
            env.pop(k, None)
        for k in [k for k in env if k.startswith("AGENTMAIL_")]:
            env.pop(k)
        r = subprocess.run([py, str(CHECKS)], cwd=inst / "app", env=env, text=True)
        return r.returncode
    finally:
        if a.keep:
            print(f"kept: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
