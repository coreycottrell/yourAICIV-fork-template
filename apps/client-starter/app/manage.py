#!/usr/bin/env python3
"""
Instance management CLI (run from the instance's app/ directory, with the
shared venv's python):

    python manage.py issue-setup-link [--ttl-hours 24] [--port PORT]
    python manage.py revoke-sessions
    python manage.py status
    python manage.py sync-workflows [--check]
    python manage.py workflows
    python manage.py run-workflows

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

sync-workflows [--check]
    Validates app/workflows.json (the automation definitions) and loads it into
    the database. A bad file is refused with the reason and nothing changes.
    --check only validates. The running app picks the change up immediately
    (it reads definitions from the database on every pass).

workflows
    Lists the workflows, their steps, enrollment counts, and whether email and
    Telegram are configured. No contact data is printed.

run-workflows
    Sends every due workflow step once, now (the in-process runner does this
    every minute anyway; use this to test or to drive it from cron).
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


def _email_module():
    from modules import email_marketing
    return email_marketing


def sync_workflows_cmd(check_only):
    em = _email_module()
    try:
        templates, workflows = em.load_workflow_definitions()
    except em.WorkflowConfigError as e:
        sys.exit(f"workflows.json is INVALID, nothing changed: {e}")
    if check_only:
        print(f"workflows.json OK: {len(workflows)} workflow(s), "
              f"{len(templates)} template(s)")
        return
    db = sqlite3.connect(webapp.DB_PATH, timeout=30)
    db.execute("PRAGMA busy_timeout=30000")
    try:
        r = em.sync_workflows(db)
    finally:
        db.close()
    print(f"Loaded workflows.json: {r['workflows']} workflow(s) ({r['active']} active), "
          f"{r['templates']} template(s), {r['archived']} archived.")


def list_workflows():
    db = _db()
    db.row_factory = sqlite3.Row
    print(f"email configured: {'yes' if webapp.email_configured() else 'NO (emails wait)'}")
    print(f"telegram configured: {'yes' if webapp.telegram_configured() else 'no'}")
    rows = db.execute("SELECT * FROM workflows ORDER BY status, id").fetchall()
    if not rows:
        print("no workflows defined")
    for w in rows:
        print(f"\n[{w['status']}] {w['id']}: {w['name']}")
        print(f"  trigger: {w['trigger_type']} {w['trigger_config']}")
        for st in db.execute("SELECT * FROM workflow_steps WHERE workflow_id = ? "
                             "ORDER BY step_order", (w['id'],)):
            print(f"  step {st['step_order'] + 1}: +{st['delay_minutes']}m "
                  f"{st['action_type']} {st['action_config']}")
        counts = dict(db.execute("SELECT status, COUNT(*) FROM workflow_enrollments "
                                 "WHERE workflow_id = ? GROUP BY status", (w['id'],)).fetchall())
        due = db.execute("SELECT COUNT(*) FROM workflow_enrollments WHERE workflow_id = ? "
                         "AND status = 'active' AND next_action_at <= ?",
                         (w['id'], datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))).fetchone()[0]
        print(f"  enrollments: {counts or 'none'}; due now: {due}")
    sent = dict(db.execute("SELECT status, COUNT(*) FROM email_log WHERE workflow_id "
                           "IS NOT NULL GROUP BY status").fetchall())
    print(f"\nautomation emails logged: {sent or 'none'}")
    db.close()


def run_workflows():
    em = _email_module()
    with webapp.app.app_context():
        h = webapp.app.config['_helpers']
        stats = em.process_due_workflows(h['get_db'](), h)
    print(" ".join(f"{k}={v}" for k, v in stats.items()))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("issue-setup-link")
    p.add_argument("--ttl-hours", type=float, default=24.0)
    p.add_argument("--port", type=int, default=None)
    sub.add_parser("revoke-sessions")
    sub.add_parser("status")
    p = sub.add_parser("sync-workflows")
    p.add_argument("--check", action="store_true")
    sub.add_parser("workflows")
    sub.add_parser("run-workflows")
    args = parser.parse_args()
    if args.cmd in ("sync-workflows", "workflows", "run-workflows") and not (
            cfg.is_module_enabled("workflows") or cfg.is_module_enabled("email_marketing")):
        sys.exit("The workflows module is off in config.py (modules.workflows).")
    if args.cmd == "sync-workflows":
        return sync_workflows_cmd(args.check)
    if args.cmd == "workflows":
        return list_workflows()
    if args.cmd == "run-workflows":
        return run_workflows()
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
