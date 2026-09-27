#!/usr/bin/env python3
"""
Instance management CLI (run from the instance's app/ directory, with the
shared venv's python):

    python manage.py issue-setup-link [--ttl-hours 24] [--port PORT]
    python manage.py revoke-sessions
    python manage.py status

issue-setup-link
    Creates a SINGLE-USE set-password link (256-bit token, default 24h expiry)
    and writes it to <instance>/.setup-link (mode 0600). It never prints the
    link or any password to stdout, so nothing lands in an agent transcript
    or a log. Read the file and send the link to the client privately; it is
    dead once used or expired. Re-run it for a lost password: using the new
    link sets a new password and signs out every existing admin session.
    Only the SHA-256 of the token is stored in the database.

revoke-sessions
    Signs out every admin session immediately (bumps settings.session_version).

status
    Shows whether an admin password is set and whether a setup link is pending.
"""

import argparse
import hashlib
import os
import secrets
import sqlite3
import sys
import time
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import config as cfg          # noqa: E402  (loads .env, fails closed on a bad key)
import app as webapp          # noqa: E402  (creates/migrates the DB schema)


def _db():
    db = sqlite3.connect(webapp.DB_PATH, timeout=30)
    db.execute("PRAGMA busy_timeout=30000")
    return db


def _get(db, key, default=None):
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row[0] if row else default


def _set(db, key, value):
    db.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
               "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
               (key, str(value)))


def issue_setup_link(ttl_hours, port):
    token = secrets.token_urlsafe(32)
    expires = time.time() + ttl_hours * 3600
    db = _db()
    with db:
        _set(db, "admin_setup_token_hash", hashlib.sha256(token.encode()).hexdigest())
        _set(db, "admin_setup_token_expires", f"{expires:.0f}")
    db.close()

    path = os.path.join(os.path.dirname(HERE), ".setup-link")
    expires_iso = datetime.fromtimestamp(expires, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# One-time admin set-password link. Send it to the client privately.",
        "# It works ONCE and expires at " + expires_iso + ".",
        "# Delete this file after sending it.",
        "public: " + cfg.base_url() + "/admin/setup/" + token,
    ]
    if port:
        lines.append(f"local:  http://127.0.0.1:{port}/admin/setup/{token}")
    old_umask = os.umask(0o077)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        os.chmod(path, 0o600)
    finally:
        os.umask(old_umask)
    print(f"Setup link written to {path} (mode 0600), valid until {expires_iso}.")
    print("Send it to the client privately, then delete the file.")


def revoke_sessions():
    db = _db()
    with db:
        current = int(_get(db, "session_version", "1") or 1)
        _set(db, "session_version", current + 1)
    db.close()
    print("All admin sessions revoked.")


def status():
    db = _db()
    has_pw = bool(_get(db, "admin_pass_hash"))
    exp = _get(db, "admin_setup_token_expires")
    db.close()
    print(f"admin password set: {'yes' if has_pw else 'no'}")
    if exp and float(exp) > time.time():
        print("setup link pending until " + datetime.fromtimestamp(
            float(exp), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        print("setup link pending: no")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("issue-setup-link")
    p.add_argument("--ttl-hours", type=float, default=24.0)
    p.add_argument("--port", type=int, default=None)
    sub.add_parser("revoke-sessions")
    sub.add_parser("status")
    args = parser.parse_args()
    if args.cmd == "issue-setup-link":
        if not 0 < args.ttl_hours <= 72:
            sys.exit("--ttl-hours must be between 0 and 72")
        issue_setup_link(args.ttl_hours, args.port)
    elif args.cmd == "revoke-sessions":
        revoke_sessions()
    else:
        status()


if __name__ == "__main__":
    main()
