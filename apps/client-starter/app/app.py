"""
Client-Starter Scaffold -- Core Application
============================================
A config-driven Flask admin shell with CRM, dashboard, and modular
Blueprint registration. Everything per-client lives in config.py.

Modules (email_marketing, ecommerce, blog, affiliates, appointments,
shipping) register themselves as Blueprints based on config toggles.
Each module provides: get_schema(), get_nav_items(), get_metrics(db).
"""

import os
import sys
import json
import html
import sqlite3
import uuid
import hashlib
import secrets
import hmac as _hmac
from datetime import datetime, timedelta
from functools import wraps
import time as _time

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, g, jsonify, abort, session)
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import check_password_hash, generate_password_hash
import nh3

import config as cfg

# ── App Factory ──────────────────────────────────────────────────────────

app = Flask(__name__)


# ── Reverse-proxy headers: trusted ONLY from the proxy itself ───────────
# The instance binds 127.0.0.1 and is published through a local reverse
# proxy / tunnel. X-Forwarded-* is honoured only when the TCP peer is in
# CLIENT_TRUSTED_PROXIES; from anyone else those headers are stripped, so a
# client cannot choose its own remote_addr (rate-limit bypass) or scheme.
_TRUSTED_PROXIES = {
    p.strip() for p in os.environ.get(
        "CLIENT_TRUSTED_PROXIES", "127.0.0.1,::1").split(",") if p.strip()}
_PROXY_HOPS = max(1, int(os.environ.get("CLIENT_PROXY_HOPS", "1")))
_FORWARDED_HEADERS = (
    "HTTP_FORWARDED", "HTTP_X_FORWARDED_FOR", "HTTP_X_FORWARDED_PROTO",
    "HTTP_X_FORWARDED_HOST", "HTTP_X_FORWARDED_PORT", "HTTP_X_FORWARDED_PREFIX",
)


class TrustedProxyFix:
    def __init__(self, wsgi_app):
        self.raw = wsgi_app
        self.fixed = ProxyFix(wsgi_app, x_for=_PROXY_HOPS, x_proto=_PROXY_HOPS,
                              x_host=_PROXY_HOPS, x_prefix=_PROXY_HOPS)

    def __call__(self, environ, start_response):
        if environ.get("REMOTE_ADDR") in _TRUSTED_PROXIES:
            return self.fixed(environ, start_response)
        for header in _FORWARDED_HEADERS:
            environ.pop(header, None)
        return self.raw(environ, start_response)


app.wsgi_app = TrustedProxyFix(app.wsgi_app)


# ── Path-prefix hosting (e.g. https://<portal>/site/<slug>/) ────────────
# The AiCIV's portal publishes this instance under /site/<slug>/ and sends
# X-Forwarded-Prefix, which ProxyFix turns into SCRIPT_NAME, so url_for()
# and redirects already carry the prefix. The session cookie must follow the
# same prefix: several client sites can share one host, and a cookie on "/"
# would be sent to (and overwritten by) every one of them. On the client's
# own domain the prefix is empty and the cookie path is "/" as before.
from flask.sessions import SecureCookieSessionInterface  # noqa: E402


class PrefixAwareSessionInterface(SecureCookieSessionInterface):
    def get_cookie_path(self, app):
        return (request.script_root or "") + "/"


app.session_interface = PrefixAwareSessionInterface()

app.secret_key = cfg.CLIENT_CONFIG["secret_key"]
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024   # 16 MB upload limit

# ── CSRF Protection (C2) ───────────────────────────────────────────────
csrf = CSRFProtect(app)

# ── Session security ───────────────────────────────────────────────────
# Secure cookies by default: every instance is served over HTTPS through
# its proxy. CLIENT_INSECURE_COOKIES=1 exists ONLY for plain-http testing on
# loopback; never set it on a public instance.
_INSECURE_COOKIES = os.environ.get("CLIENT_INSECURE_COOKIES", "0") == "1"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = not _INSECURE_COOKIES
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=8)
if _INSECURE_COOKIES:
    sys.stderr.write("[SECURITY] WARNING: CLIENT_INSECURE_COOKIES=1 -- session "
                     "cookies are not Secure. Loopback testing only.\n")

# ── Security headers ──────────────────────────────────────────────────
# CSP: no inline scripts or inline event handlers anywhere in the templates
# (behaviour lives in static/js/app.js). Inline style attributes are still
# allowed. Override per client with CLIENT_CONFIG["content_security_policy"].
_DEFAULT_CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; font-src 'self' data: https:; "
    "connect-src 'self'; object-src 'none'; base-uri 'self'; "
    "frame-ancestors 'self'; form-action 'self' https://checkout.stripe.com"
)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    # setdefault: a route may set a stricter policy (the order page sends
    # no-referrer because its entry URL carries an access token).
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers["Content-Security-Policy"] = cfg.CLIENT_CONFIG.get(
        "content_security_policy") or _DEFAULT_CSP
    if request.is_secure:
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains")
    return response


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "client.db")


# ── Rate limiting (SQLite-backed: shared by all workers, survives restarts)
# Fixed-window counters in the instance DB. Keys are namespaced by endpoint
# (or an explicit scope) so one form's traffic never eats another's budget.
# Rows expire and are pruned on every call, so the table stays bounded.
_RATE_LIMIT_WINDOW = 60       # seconds
_RATE_LIMIT_MAX_ATTEMPTS = 10  # max requests per window


def _limiter_db():
    db = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    db.execute("PRAGMA busy_timeout=30000")
    return db


def _rate_limited(ip, window=_RATE_LIMIT_WINDOW,
                  max_attempts=_RATE_LIMIT_MAX_ATTEMPTS, scope=None):
    """Return True if this caller has exceeded the limit for this scope."""
    if scope is None:
        try:
            scope = request.endpoint or "global"
        except RuntimeError:
            scope = "global"
    key = f"{scope}|{ip or 'unknown'}|{window}"
    now = _time.time()
    db = _limiter_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        db.execute("DELETE FROM rate_limits WHERE reset_at < ?", (now,))
        row = db.execute(
            "SELECT count FROM rate_limits WHERE key = ?", (key,)).fetchone()
        if row is None:
            db.execute(
                "INSERT INTO rate_limits (key, count, reset_at) VALUES (?, 1, ?)",
                (key, now + window))
            limited = False
        elif row[0] >= max_attempts:
            limited = True
        else:
            db.execute(
                "UPDATE rate_limits SET count = count + 1 WHERE key = ?", (key,))
            limited = False
        db.execute("COMMIT")
        return limited
    except sqlite3.Error as e:
        sys.stderr.write(f"[RATE-LIMIT] store error, failing closed: {e}\n")
        try:
            db.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        return True
    finally:
        db.close()


# ── Per-account login backoff (not only per IP) ─────────────────────────
_LOGIN_FREE_FAILURES = 5
_LOGIN_MAX_LOCK_SECONDS = 15 * 60


def _account_locked_for(account):
    """Seconds the account is still locked (0 = not locked)."""
    db = _limiter_db()
    try:
        row = db.execute(
            "SELECT locked_until FROM login_failures WHERE account = ?",
            (account,)).fetchone()
    finally:
        db.close()
    if not row or not row[0]:
        return 0
    return max(0, int(row[0] - _time.time()))


def _record_login_failure(account):
    now = _time.time()
    db = _limiter_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute(
            "SELECT failures FROM login_failures WHERE account = ?",
            (account,)).fetchone()
        failures = (row[0] if row else 0) + 1
        locked_until = None
        if failures > _LOGIN_FREE_FAILURES:
            lock = min(2 ** (failures - _LOGIN_FREE_FAILURES) * 15,
                       _LOGIN_MAX_LOCK_SECONDS)
            locked_until = now + lock
        db.execute(
            "INSERT INTO login_failures (account, failures, locked_until, updated_at) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(account) DO UPDATE SET "
            "failures = excluded.failures, locked_until = excluded.locked_until, "
            "updated_at = excluded.updated_at",
            (account, failures, locked_until, now))
        db.execute("COMMIT")
    finally:
        db.close()


def _clear_login_failures(account):
    db = _limiter_db()
    try:
        db.execute("DELETE FROM login_failures WHERE account = ?", (account,))
    finally:
        db.close()

# Store registered modules for nav/metrics
_registered_modules = []


# ── Helpers ──────────────────────────────────────────────────────────────

def now_iso():
    """Current time as ISO-8601 string (no timezone)."""
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ── Database ─────────────────────────────────────────────────────────────

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH, timeout=30)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA busy_timeout=30000")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    """Create core tables from schema.sql, then let modules extend."""
    db = sqlite3.connect(DB_PATH, timeout=30)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=30000")

    # Core schema
    schema_path = os.path.join(BASE_DIR, "db", "schema.sql")
    with open(schema_path) as f:
        db.executescript(f.read())

    # Module schemas (+ optional in-place migrations for existing DBs)
    for mod_info in _registered_modules:
        get_schema = mod_info.get('get_schema')
        if get_schema:
            try:
                db.executescript(get_schema())
            except Exception as e:
                sys.stderr.write(
                    f"[DB] Schema error for module {mod_info['name']}: {e}\n")
        migrate = mod_info.get('migrate')
        if migrate:
            try:
                migrate(db)
            except Exception as e:
                sys.stderr.write(
                    f"[DB] Migration error for module {mod_info['name']}: {e}\n")

    db.commit()
    db.close()
    sys.stderr.write(f"[DB] Initialized at {DB_PATH}\n")


# ── Settings (key-value store in the instance DB) ───────────────────────

def get_setting(key, default=None):
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value, commit=True):
    db = get_db()
    if value is None:
        db.execute("DELETE FROM settings WHERE key = ?", (key,))
    else:
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)))
    if commit:
        db.commit()


# ── Auth ─────────────────────────────────────────────────────────────────
# The admin session is a signed cookie carrying {"admin": True, "sv": N}.
# N must equal settings.session_version; bumping it (logout, password change,
# `manage.py revoke-sessions`) invalidates every outstanding admin cookie.

MIN_ADMIN_PASSWORD_LENGTH = 12


def _session_version():
    try:
        return int(get_setting("session_version", "1"))
    except (TypeError, ValueError):
        return 1


def bump_session_version():
    set_setting("session_version", _session_version() + 1)


def is_admin():
    return bool(session.get("admin")) and session.get("sv") == _session_version()


def start_admin_session():
    session.clear()                      # no fixation, no leftover state
    session["admin"] = True
    session["sv"] = _session_version()
    session.permanent = True


def admin_required(f):
    """Require a current (non-revoked) admin session for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not is_admin():
            session.pop("admin", None)
            session.pop("sv", None)
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def cron_key_required(f):
    """Require the X-Cron-Key header (never a query param: URLs get logged)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        cron_key = cfg.CLIENT_CONFIG["cron_key"]
        key = request.headers.get("X-Cron-Key", "")
        if not cron_key or not _hmac.compare_digest(key, cron_key):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


def _validate_new_password(pw, confirm):
    if len(pw) < MIN_ADMIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_ADMIN_PASSWORD_LENGTH} characters."
    if pw != confirm:
        return "Passwords do not match."
    return None


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if _rate_limited(request.remote_addr, window=300, max_attempts=10):
            flash("Too many login attempts. Try again later.", "error")
            return render_template("admin/login.html"), 429
        username = request.form.get("username", "")
        password_input = request.form.get("password", "")
        account = "admin:" + cfg.CLIENT_CONFIG["admin_user"]
        locked = _account_locked_for(account)
        if locked:
            flash(f"Too many failed attempts. Try again in {locked // 60 + 1} min.",
                  "error")
            return render_template("admin/login.html"), 429
        admin_pass_hash = get_setting("admin_pass_hash", "")
        if not admin_pass_hash:
            flash("No admin password has been set yet. Use the one-time setup "
                  "link from your AiCIV.", "error")
            return render_template("admin/login.html")
        user_ok = _hmac.compare_digest(username.encode(),
                                       cfg.CLIENT_CONFIG["admin_user"].encode())
        pass_ok = check_password_hash(admin_pass_hash, password_input)
        if user_ok and pass_ok:
            _clear_login_failures(account)
            start_admin_session()
            return redirect(url_for("admin_dashboard"))
        _record_login_failure(account)
        flash("Invalid credentials.", "error")
    return render_template("admin/login.html")


@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    if is_admin():
        bump_session_version()           # revokes this and every other admin cookie
    session.clear()
    return redirect(url_for("index"))


def _setup_token_valid(token):
    stored = get_setting("admin_setup_token_hash", "")
    expires = get_setting("admin_setup_token_expires", "0")
    if not stored or not token:
        return False
    digest = hashlib.sha256(token.encode()).hexdigest()
    try:
        not_expired = _time.time() < float(expires)
    except (TypeError, ValueError):
        not_expired = False
    return _hmac.compare_digest(digest, stored) and not_expired


@app.route("/admin/setup/<token>", methods=["GET", "POST"])
def admin_setup(token):
    """Single-use set-password link (issued by `manage.py issue-setup-link`)."""
    if _rate_limited(request.remote_addr, window=300, max_attempts=20):
        abort(429)
    if not _setup_token_valid(token):
        return render_template("admin/setup_password.html", valid=False), 410
    if request.method == "POST":
        pw = request.form.get("password", "")
        err = _validate_new_password(pw, request.form.get("confirm", ""))
        if err:
            flash(err, "error")
            return render_template("admin/setup_password.html", valid=True)
        set_setting("admin_pass_hash", generate_password_hash(pw), commit=False)
        set_setting("admin_setup_token_hash", None, commit=False)
        set_setting("admin_setup_token_expires", None, commit=False)
        set_setting("session_version", _session_version() + 1)
        _clear_login_failures("admin:" + cfg.CLIENT_CONFIG["admin_user"])
        start_admin_session()
        flash("Password set. You are logged in.", "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/setup_password.html", valid=True)


@app.route("/admin/password", methods=["GET", "POST"])
@admin_required
def admin_change_password():
    if request.method == "POST":
        current = request.form.get("current_password", "")
        pw = request.form.get("password", "")
        if not check_password_hash(get_setting("admin_pass_hash", ""), current):
            flash("Current password is incorrect.", "error")
            return render_template("admin/change_password.html")
        err = _validate_new_password(pw, request.form.get("confirm", ""))
        if err:
            flash(err, "error")
            return render_template("admin/change_password.html")
        set_setting("admin_pass_hash", generate_password_hash(pw), commit=False)
        set_setting("session_version", _session_version() + 1)
        start_admin_session()            # keep THIS browser, drop all others
        flash("Password changed. All other admin sessions were signed out.",
              "success")
        return redirect(url_for("admin_dashboard"))
    return render_template("admin/change_password.html")


# ── CRM: sync_to_crm ────────────────────────────────────────────────────

def sync_to_crm(form_data, form_type, trusted=False):
    """Create-or-match a contact by email, log activity, and auto-tag.

    Public forms (trusted=False, the default) may CREATE a contact but never
    overwrite an existing contact's identity fields: anyone can type anyone's
    email into a form, and those fields are merged into emails sent from the
    client's own domain. Submitted values that differ are recorded in the
    activity log for a human to apply. Only admin-side code passes trusted=True.
    """
    try:
        email = (form_data.get("email") or "").strip().lower()
        if not email:
            return

        db = get_db()
        now = now_iso()

        row = db.execute(
            "SELECT id FROM contacts WHERE LOWER(email) = ?", (email,)
        ).fetchone()

        unapplied = {}
        if row:
            contact_id = row["id"]
            updates = {}
            for form_key in ("first_name", "last_name", "phone", "address",
                             "city", "state", "postal_code", "date_of_birth"):
                val = (form_data.get(form_key) or "").strip()
                if val:
                    updates[form_key] = val
            if not trusted:
                unapplied, updates = updates, {}
            updates["updated_at"] = now
            # Column names come from the fixed whitelist above, never input.
            set_clause = ", ".join(f"{k} = ?" for k in updates)
            db.execute(
                f"UPDATE contacts SET {set_clause} WHERE id = ?",
                list(updates.values()) + [contact_id]
            )
        else:
            contact_id = str(uuid.uuid4())
            db.execute(
                """INSERT INTO contacts
                   (id, first_name, last_name, email, phone, address, city,
                    state, postal_code, date_of_birth, source, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (contact_id,
                 (form_data.get("first_name") or "").strip(),
                 (form_data.get("last_name") or "").strip(),
                 email,
                 (form_data.get("phone") or "").strip(),
                 (form_data.get("address") or "").strip(),
                 (form_data.get("city") or "").strip(),
                 (form_data.get("state") or "").strip(),
                 (form_data.get("postal_code") or "").strip(),
                 (form_data.get("date_of_birth") or "").strip(),
                 form_type, now, now)
            )

        details = dict(form_data)
        if unapplied:
            details["_unapplied_identity_fields"] = unapplied
        details_json = json.dumps(details, ensure_ascii=False, default=str)
        db.execute(
            "INSERT INTO activity_log (contact_id, type, details, created_at) "
            "VALUES (?, ?, ?, ?)",
            (contact_id, form_type, details_json, now)
        )

        tag_map = cfg.CLIENT_CONFIG.get("tag_map", {})
        tag_name, tag_color = tag_map.get(form_type, (form_type, "#6b7280"))
        tag_row = db.execute(
            "SELECT id FROM tags WHERE name = ?", (tag_name,)
        ).fetchone()

        if tag_row:
            tag_id = tag_row["id"]
        else:
            tag_id = str(uuid.uuid4())
            db.execute(
                "INSERT INTO tags (id, name, color, created_at) VALUES (?, ?, ?, ?)",
                (tag_id, tag_name, tag_color, now)
            )

        db.execute(
            "INSERT OR IGNORE INTO contact_tags "
            "(contact_id, tag_id, added_at) VALUES (?, ?, ?)",
            (contact_id, tag_id, now)
        )

        db.commit()
        app.logger.info(f"CRM sync OK: contact {contact_id} -> {form_type}")

    except Exception as e:
        app.logger.error(f"CRM sync failed for {form_type}: {e}")


def _save_form_submission(contact_email, form_type, form_data_dict,
                          source_url=None):
    """Archive a form submission to form_submissions table."""
    try:
        db = get_db()
        email = (contact_email or "").strip().lower()

        contact_id = None
        if email:
            row = db.execute(
                "SELECT id FROM contacts WHERE LOWER(email) = ?", (email,)
            ).fetchone()
            if row:
                contact_id = row["id"]

        clean_data = {k: v for k, v in form_data_dict.items() if v}
        form_data_json = json.dumps(clean_data, ensure_ascii=False, default=str)

        db.execute(
            """INSERT INTO form_submissions
               (contact_id, contact_email, form_type, form_data,
                submission_date, source_url)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (contact_id, contact_email, form_type, form_data_json,
             datetime.now().isoformat(), source_url or "")
        )
        db.commit()
    except Exception as e:
        app.logger.error(f"Failed to save form_submission ({form_type}): {e}")


# ── Notifications ────────────────────────────────────────────────────────

def tg_escape(value):
    """Escape a value for a Telegram parse_mode="HTML" message."""
    return html.escape(str(value if value is not None else ""), quote=True)


def send_telegram(message, parse_mode=None):
    """Send a Telegram notification. No-op if not configured.

    Default is PLAIN TEXT (no parse_mode): alerts carry text typed by
    anonymous visitors, and with HTML parsing a visitor could plant links in
    the operator's own alert. If you pass parse_mode="HTML", every
    interpolated value MUST go through tg_escape().
    """
    import urllib.request
    bot_token = cfg.CLIENT_CONFIG.get("telegram_bot_token", "")
    chat_id = cfg.CLIENT_CONFIG.get("telegram_chat_id", "")
    if not bot_token or not chat_id:
        return
    try:
        body = {"chat_id": chat_id, "text": message,
                "disable_web_page_preview": True}
        if parse_mode:
            body["parse_mode"] = parse_mode
        payload = json.dumps(body).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        app.logger.error(f"Telegram notification failed: {e}")


# ── Email ────────────────────────────────────────────────────────────────

def _send_email(to_addr, subject, html_body, tags=None, headers=None):
    """Send an HTML email via Resend API. No-op if not configured."""
    import urllib.request
    import urllib.error
    api_key = cfg.CLIENT_CONFIG.get("resend_api_key", "")
    from_addr = cfg.CLIENT_CONFIG.get("email_from", "")
    if not api_key or not from_addr:
        sys.stderr.write(
            f"[EMAIL SKIP] No Resend key/from -- skipping {to_addr}\n")
        return None

    try:
        payload = {
            "from": from_addr,
            "to": [to_addr],
            "subject": subject,
            "html": html_body,
        }
        if tags:
            payload["tags"] = tags
        if headers:
            payload["headers"] = headers

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST"
        )
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        return result.get("id", True)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise ValueError("rate_limited")
        return None
    except Exception:
        return None


# ── Admin Nav Builder ────────────────────────────────────────────────────

def _build_admin_nav():
    """Build admin sidebar nav items from enabled modules."""
    nav = []

    # Always present
    nav.append({
        "label": "Dashboard",
        "endpoint": "admin_dashboard",
        "match": "admin_dashboard"
    })

    # CRM section (always on -- core)
    if cfg.is_module_enabled("crm"):
        nav.append({"divider": True})
        nav.append({
            "label": "Contacts",
            "endpoint": "admin_contacts",
            "match": "admin_contact"
        })

    # Module nav items (from registered modules)
    for mod_info in _registered_modules:
        get_nav = mod_info.get('get_nav_items')
        if get_nav:
            try:
                items = get_nav()
                nav.extend(items)
            except Exception:
                pass

    # Extra custom items from config
    for item in cfg.CLIENT_CONFIG.get("admin_nav_extra", []):
        nav.append(item)

    # Footer links
    nav.append({"divider": True})
    nav.append({
        "label": "View Site",
        "endpoint": "index",
        "target": "_blank",
        "match": "__never__"
    })
    nav.append({
        "label": "Change Password",
        "endpoint": "admin_change_password",
        "match": "admin_change_password"
    })
    nav.append({
        "label": "Logout",
        "endpoint": "admin_logout",
        "match": "__never__",
        "post": True,                      # rendered as a CSRF-protected form
    })

    return nav


# ── HTML Sanitization (nh3; bleach is deprecated upstream) ─────────────
# No `id` (DOM clobbering) and no `style` (UI redress); nh3 adds
# rel="noopener noreferrer" to every link itself, so `rel` is not allowed in.

SAFE_TAGS = {
    'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'div', 'em', 'h1',
    'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol', 'p',
    'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead',
    'tr', 'u', 'ul', 'figure', 'figcaption', 'details', 'summary',
}
SAFE_ATTRS = {
    '*': {'class'},
    'a': {'href', 'title', 'target'},
    'img': {'src', 'alt', 'title', 'width', 'height'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
}
SAFE_URL_SCHEMES = {'http', 'https', 'mailto'}


@app.template_global('site_path')
def site_path(url):
    """Config-driven link ("/contact", "https://...", "#faq") -> href.
    Root-relative paths get the hosting prefix (request.script_root), so
    links written for the client's own domain also work under /site/<slug>/."""
    url = (url or "").strip()
    if url.startswith("/") and not url.startswith("//"):
        return (request.script_root or "") + url
    return url


@app.template_filter('sanitize')
def sanitize_html(value):
    """Sanitize HTML: allow safe tags, strip everything else."""
    if not value:
        return ''
    from markupsafe import Markup
    return Markup(nh3.clean(
        value, tags=SAFE_TAGS, attributes=SAFE_ATTRS,
        url_schemes=SAFE_URL_SCHEMES))


# ── Template Context Injection ───────────────────────────────────────────

@app.context_processor
def inject_config():
    """Expose ONLY the whitelisted public config (never API keys, bot
    token, cron key or secret key) plus the admin nav to templates."""
    return dict(
        cfg=cfg.public_config(),
        admin_nav=_build_admin_nav(),
    )


# ── Dashboard Metrics ───────────────────────────────────────────────────

def _dashboard_metrics():
    """Gather KPI metrics from enabled modules."""
    db = get_db()
    metrics = []

    # CRM is always on
    total_contacts = db.execute(
        "SELECT COUNT(*) as c FROM contacts"
    ).fetchone()["c"]
    metrics.append({"label": "Contacts", "value": total_contacts})

    unread_messages = db.execute(
        "SELECT COUNT(*) as c FROM contact_messages WHERE read = 0"
    ).fetchone()["c"]
    metrics.append({"label": "Unread Messages", "value": unread_messages})

    # Module-specific metrics
    for mod_info in _registered_modules:
        get_metrics_fn = mod_info.get('get_metrics')
        if get_metrics_fn:
            try:
                mod_metrics = get_metrics_fn(db)
                metrics.extend(mod_metrics)
            except Exception as e:
                sys.stderr.write(
                    f"[METRICS] Error from module {mod_info['name']}: {e}\n")

    return metrics


# ── Routes: Dashboard ───────────────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    metrics = _dashboard_metrics()
    recent_messages = db.execute(
        "SELECT * FROM contact_messages ORDER BY submitted_at DESC LIMIT 5"
    ).fetchall()
    return render_template("admin/dashboard.html",
                           metrics=metrics,
                           recent_messages=recent_messages)


# ── Routes: CRM Contacts ────────────────────────────────────────────────

@app.route("/admin/contacts")
@admin_required
def admin_contacts():
    db = get_db()
    search = request.args.get("q", "").strip()
    if search:
        like = f"%{search}%"
        contacts = db.execute(
            """SELECT * FROM contacts
               WHERE first_name LIKE ? OR last_name LIKE ?
               OR email LIKE ? OR phone LIKE ?
               ORDER BY updated_at DESC LIMIT 100""",
            (like, like, like, like)
        ).fetchall()
    else:
        contacts = db.execute(
            "SELECT * FROM contacts ORDER BY updated_at DESC LIMIT 100"
        ).fetchall()

    contact_tags = {}
    for c in contacts:
        tags = db.execute(
            """SELECT t.name, t.color FROM tags t
               JOIN contact_tags ct ON ct.tag_id = t.id
               WHERE ct.contact_id = ?""",
            (c["id"],)
        ).fetchall()
        contact_tags[c["id"]] = tags

    return render_template("admin/contacts.html",
                           contacts=contacts,
                           contact_tags=contact_tags,
                           search=search)


@app.route("/admin/contacts/<contact_id>")
@admin_required
def admin_contact_detail(contact_id):
    db = get_db()
    contact = db.execute(
        "SELECT * FROM contacts WHERE id = ?", (contact_id,)
    ).fetchone()
    if not contact:
        abort(404)

    tags = db.execute(
        """SELECT t.* FROM tags t
           JOIN contact_tags ct ON ct.tag_id = t.id
           WHERE ct.contact_id = ?""",
        (contact_id,)
    ).fetchall()

    activity = db.execute(
        "SELECT * FROM activity_log WHERE contact_id = ? "
        "ORDER BY created_at DESC LIMIT 50",
        (contact_id,)
    ).fetchall()

    submissions = db.execute(
        "SELECT * FROM form_submissions WHERE contact_id = ? "
        "ORDER BY submission_date DESC",
        (contact_id,)
    ).fetchall()

    return render_template("admin/contact_detail.html",
                           contact=contact, tags=tags,
                           activity=activity, submissions=submissions,
                           json=json)


@app.route("/admin/contacts/<contact_id>/note", methods=["POST"])
@admin_required
def admin_contact_add_note(contact_id):
    db = get_db()
    note = request.form.get("note", "").strip()
    if note:
        db.execute(
            "INSERT INTO activity_log (contact_id, type, details, created_at) "
            "VALUES (?, 'note', ?, ?)",
            (contact_id, note, now_iso())
        )
        db.commit()
        flash("Note added.", "success")
    return redirect(url_for("admin_contact_detail", contact_id=contact_id))


# ── Routes: Messages ────────────────────────────────────────────────────

@app.route("/admin/messages")
@admin_required
def admin_messages():
    db = get_db()
    messages = db.execute(
        "SELECT * FROM contact_messages ORDER BY submitted_at DESC"
    ).fetchall()
    return render_template("admin/messages.html", messages=messages)


@app.route("/admin/messages/<int:msg_id>/read", methods=["POST"])
@admin_required
def admin_message_read(msg_id):
    db = get_db()
    db.execute(
        "UPDATE contact_messages SET read = 1 WHERE id = ?", (msg_id,))
    db.commit()
    return redirect(url_for("admin_messages"))


# ── Routes: Public ──────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("public/home.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        if _rate_limited(request.remote_addr):
            flash("Too many submissions. Please wait a moment.", "error")
            return render_template("public/contact.html"), 429
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if name and email and message:
            db = get_db()
            db.execute(
                "INSERT INTO contact_messages "
                "(name, email, message, submitted_at) VALUES (?, ?, ?, ?)",
                (name, email, message, now_iso())
            )
            db.commit()

            sync_to_crm({"first_name": name, "email": email}, "contact")
            _save_form_submission(
                email, "contact",
                {"name": name, "email": email, "message": message},
                source_url=request.url)

            flash("Message sent! We will be in touch.", "success")
            return redirect(url_for("contact"))
        flash("Please fill in all fields.", "error")
    return render_template("public/contact.html")


# ── Module Registration System ──────────────────────────────────────────

def register_module(module_name, module):
    """Register a module's Blueprint, schema, nav, and metrics."""
    mod_info = {
        'name': module_name,
        'get_schema': getattr(module, 'get_schema', None),
        'get_nav_items': getattr(module, 'get_nav_items', None),
        'get_metrics': getattr(module, 'get_metrics', None),
        'migrate': getattr(module, 'migrate', None),
    }
    _registered_modules.append(mod_info)

    # Register Blueprint
    bp = getattr(module, f'{module_name}_bp', None)
    if bp is None:
        # Try common naming conventions
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            from flask import Blueprint as BP
            if isinstance(attr, BP):
                bp = attr
                break
    if bp:
        app.register_blueprint(bp)
        sys.stderr.write(f"[MODULE] Registered: {module_name}\n")


# ── Expose helpers to modules ───────────────────────────────────────────

app.config['_helpers'] = {
    'get_db': get_db,
    'send_email': _send_email,
    'send_telegram': send_telegram,
    'tg_escape': tg_escape,
    'sync_to_crm': sync_to_crm,
    'config': cfg.CLIENT_CONFIG,
    'base_url': cfg.base_url,
    'now_iso': now_iso,
    'is_admin': is_admin,
    'admin_required': admin_required,
    'get_setting': get_setting,
    'set_setting': set_setting,
}
app.config['_rate_limited'] = _rate_limited


# ── Auto-register enabled modules ──────────────────────────────────────

if cfg.is_module_enabled("email_marketing") or cfg.is_module_enabled("workflows"):
    from modules import email_marketing
    register_module("email_marketing", email_marketing)

if cfg.is_module_enabled("ecommerce"):
    from modules import ecommerce
    register_module("ecommerce", ecommerce)

if cfg.is_module_enabled("blog"):
    from modules import blog
    register_module("blog", blog)

if cfg.is_module_enabled("affiliates"):
    from modules import affiliates
    register_module("affiliates", affiliates)

if cfg.is_module_enabled("appointments"):
    from modules import appointments
    register_module("appointments", appointments)

if cfg.is_module_enabled("shipping"):
    from modules import shipping
    register_module("shipping", shipping)

# Payments is always registered when ecommerce is on (provides provider
# framework for checkout). Can also be registered standalone for the
# admin payments info page.
if cfg.is_module_enabled("ecommerce") or cfg.CLIENT_CONFIG.get("payment", {}).get("active_provider", "manual") != "manual":
    from modules import payments
    register_module("payments", payments)


# ── CSRF Exemptions for webhooks/APIs ──────────────────────────────────
# These endpoints receive external callbacks and cannot include CSRF tokens.

if cfg.is_module_enabled("email_marketing") or cfg.is_module_enabled("workflows"):
    csrf.exempt(email_marketing.resend_webhook)
    csrf.exempt(email_marketing.api_process_workflows)
    csrf.exempt(email_marketing.unsubscribe)     # RFC 8058 one-click POST

if cfg.is_module_enabled("ecommerce") or \
        cfg.CLIENT_CONFIG.get("payment", {}).get("active_provider", "manual") != "manual":
    csrf.exempt(payments.payment_webhook)


# ── Startup ──────────────────────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    # DEVELOPMENT ONLY. Production runs under gunicorn on 127.0.0.1 via
    # ../run.sh or the systemd unit in ../deploy/ (see clone_client.sh output).
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5099
    host = os.environ.get("CLIENT_BIND_HOST", "127.0.0.1")
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    if debug and host not in ("127.0.0.1", "::1", "localhost"):
        sys.exit("[SECURITY] FATAL: FLASK_DEBUG=1 exposes the interactive "
                 "debugger (remote code execution). Refusing debug on a "
                 f"non-loopback host ({host}).")
    sys.stderr.write("[DEV] Werkzeug development server -- not for production. "
                     "Use ../run.sh (gunicorn) instead.\n")
    app.run(host=host, port=port, debug=debug)
