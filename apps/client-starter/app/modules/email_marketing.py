"""
Email Marketing + Workflows Module
===================================
Subscribers, campaigns, send engine, unsubscribe, Resend webhooks,
workflow automation (triggers, steps, enrollment, cron processor).

Toggleable via config: modules.email_marketing and modules.workflows
"""

import os
import sys
import json
import html
import secrets
import hashlib
import hmac as _hmac
import base64
import threading
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, g, jsonify, abort, session, Response)

email_bp = Blueprint('email_marketing', __name__,
                     template_folder='../templates')


def _is_admin():
    """Admin check shared with app.py (honours session revocation)."""
    from flask import current_app
    return current_app.config['_helpers']['is_admin']()

# ── Schema extension ────────────────────────────────────────────────────

EMAIL_SCHEMA = """
CREATE TABLE IF NOT EXISTS email_subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    phone TEXT,
    tags TEXT DEFAULT '[]',
    source TEXT DEFAULT 'manual',
    subscribed INTEGER DEFAULT 1,
    unsubscribe_token TEXT UNIQUE,
    confirm_token_hash TEXT,
    confirm_sent_at TEXT,
    confirmed_at TEXT,
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS email_campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    status TEXT DEFAULT 'draft',
    sent_count INTEGER DEFAULT 0,
    created_at TEXT,
    sent_at TEXT
);

CREATE TABLE IF NOT EXISTS campaign_sends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER REFERENCES email_campaigns(id),
    subscriber_id INTEGER,
    sent_at TEXT,
    status TEXT DEFAULT 'sent',
    resend_email_id TEXT,
    recipient_email TEXT,
    recipient_name TEXT
);

CREATE TABLE IF NOT EXISTS campaign_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER,
    subscriber_email TEXT,
    resend_email_id TEXT,
    event_type TEXT NOT NULL,
    link_url TEXT,
    timestamp TEXT,
    raw_data TEXT DEFAULT '{}'
);

-- Workflow engine tables
CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    trigger_type TEXT NOT NULL,
    trigger_config TEXT DEFAULT '{}',
    status TEXT DEFAULT 'draft',
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS workflow_steps (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    step_order INTEGER DEFAULT 0,
    action_type TEXT NOT NULL,
    action_config TEXT DEFAULT '{}',
    delay_minutes INTEGER DEFAULT 0,
    created_at TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS workflow_enrollments (
    id TEXT PRIMARY KEY,
    workflow_id TEXT NOT NULL,
    contact_id TEXT NOT NULL,
    current_step INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active',
    next_action_at TEXT,
    enrolled_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (workflow_id) REFERENCES workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_email_subs_email ON email_subscribers(email);
CREATE INDEX IF NOT EXISTS idx_campaign_status ON email_campaigns(status);
CREATE INDEX IF NOT EXISTS idx_ce_campaign ON campaign_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ce_type ON campaign_events(event_type);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_wf ON workflow_steps(workflow_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_wf ON workflow_enrollments(workflow_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_contact ON workflow_enrollments(contact_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_next ON workflow_enrollments(next_action_at);
"""


# ── Helpers (attached to app at register time) ──────────────────────────

def _get_app_helpers():
    """Get helpers from the main app (set during register_module)."""
    from flask import current_app
    return current_app.config['_helpers']


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def migrate(db):
    """Add columns introduced by the yourAICIV hardening to existing DBs."""
    cols = {r[1] for r in db.execute("PRAGMA table_info(email_subscribers)")}
    for col in ("confirm_token_hash", "confirm_sent_at", "confirmed_at"):
        if col not in cols:
            db.execute(f"ALTER TABLE email_subscribers ADD COLUMN {col} TEXT")


# ── Per-recipient unsubscribe tokens (HMAC, work for ANY address) ──────
# token = b64url(email) "." b64url(HMAC-SHA256(secret_key, "unsub:" + email)[:16])
# Works for subscribers AND CRM contacts, needs no DB row, cannot be forged
# without the instance secret key.

def _b64e(raw):
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()


def _b64d(text):
    return base64.urlsafe_b64decode(text + '=' * (-len(text) % 4))


def _unsub_mac(email):
    from flask import current_app
    key = current_app.secret_key
    key = key.encode() if isinstance(key, str) else key
    return _hmac.new(key, f'unsub:{email}'.encode(), hashlib.sha256).digest()[:16]


def make_unsub_token(email):
    email = (email or '').strip().lower()
    return f"{_b64e(email.encode())}.{_b64e(_unsub_mac(email))}"


def parse_unsub_token(token):
    """Return the email a valid token belongs to, else None."""
    try:
        enc_email, enc_mac = token.split('.', 1)
        email = _b64d(enc_email).decode()
        mac = _b64d(enc_mac)
    except Exception:
        return None
    if email and _hmac.compare_digest(mac, _unsub_mac(email)):
        return email
    return None


def unsub_url(email):
    helpers = _get_app_helpers()
    return f"{helpers['base_url']()}/unsubscribe/{make_unsub_token(email)}"


def _generate_unsub_token(email):
    """Unsubscribe token stored on new subscriber rows (HMAC-based)."""
    return make_unsub_token(email)


def _send_confirmation(db, email):
    """Double opt-in: email a single-use confirmation link. Rate-limited per
    address so /subscribe cannot be used to mail-bomb someone."""
    from flask import current_app
    rate_fn = current_app.config.get('_rate_limited')
    if rate_fn and rate_fn(email, window=86400, max_attempts=3,
                           scope='subscribe-confirm-mail'):
        return False
    helpers = _get_app_helpers()
    cfg = helpers['config']
    token = secrets.token_urlsafe(32)
    db.execute(
        "UPDATE email_subscribers SET confirm_token_hash = ?, confirm_sent_at = ?, "
        "updated_at = ? WHERE LOWER(email) = ?",
        (hashlib.sha256(token.encode()).hexdigest(), now_iso(), now_iso(), email))
    db.commit()
    business = html.escape(cfg.get('business_name', 'Our Business'))
    link = f"{helpers['base_url']()}/subscribe/confirm/{token}"
    body = (f"<p>Please confirm that you want to receive emails from {business}.</p>"
            f"<p><a href=\"{html.escape(link)}\">Confirm my subscription</a></p>"
            f"<p style=\"font-size: 12px; color: #999;\">If you did not ask for "
            f"this, ignore this email and you will not be subscribed.</p>")
    result = helpers['send_email'](
        email, f"Confirm your subscription to {cfg.get('business_name', 'us')}", body)
    if result is None:
        sys.stderr.write("[EMAIL] confirmation email not sent (email not "
                         "configured or provider error); subscriber stays pending\n")
    return result is not None


def _add_subscriber(db, email, name=None, phone=None, source='manual', tags=None,
                    public=False):
    """Add or update a subscriber. Returns the subscriber row.

    public=True (anonymous /subscribe): never flips an opted-out address back
    on and never edits an existing row's name. New and previously
    unsubscribed addresses get a double opt-in confirmation email instead;
    they only start receiving mail after clicking it.
    public=False (admin action): the admin asserts consent; direct add.
    """
    email = (email or '').strip().lower()
    existing = db.execute(
        "SELECT * FROM email_subscribers WHERE LOWER(email) = ?", (email,)
    ).fetchone()
    if existing:
        if public:
            if not existing['subscribed']:
                _send_confirmation(db, email)
            return existing
        if name:
            db.execute(
                "UPDATE email_subscribers SET name = ?, updated_at = ? WHERE id = ?",
                (name, now_iso(), existing['id']))
        if not existing['subscribed']:
            db.execute(
                "UPDATE email_subscribers SET subscribed = 1, updated_at = ? WHERE id = ?",
                (now_iso(), existing['id']))
        db.commit()
        return db.execute(
            "SELECT * FROM email_subscribers WHERE id = ?", (existing['id'],)
        ).fetchone()
    token = _generate_unsub_token(email)
    db.execute(
        "INSERT INTO email_subscribers (email, name, phone, tags, source, "
        "subscribed, unsubscribe_token, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (email, name, phone, json.dumps(tags or []), source,
         0 if public else 1, token, now_iso(), now_iso())
    )
    db.commit()
    if public:
        _send_confirmation(db, email)
    return db.execute(
        "SELECT * FROM email_subscribers WHERE LOWER(email) = ?", (email,)
    ).fetchone()


def _send_campaign_email(subscriber, subject, body, campaign_id=None):
    """Send a single campaign email to a subscriber via the app's _send_email."""
    helpers = _get_app_helpers()
    send_email = helpers['send_email']
    cfg = helpers['config']

    first_name = subscriber.get('first_name') or (
        (subscriber.get('name', '') or '').split()[0]
        if subscriber.get('name') else 'Friend')
    first_name = ' '.join(
        w.capitalize() for w in (first_name or '').split()) or 'Friend'

    # Merge values are visitor-controlled: plain text in the subject (no
    # line breaks), HTML-escaped in the body.
    subj_name = ' '.join(first_name.split())[:100]
    body_name = html.escape(subj_name)
    rendered_subject = subject.replace(
        '{{first_name}}', subj_name).replace(
        '{{ first_name }}', subj_name)
    rendered_body = body.replace(
        '{{first_name}}', body_name).replace(
        '{{ first_name }}', body_name)

    full_body, headers = _with_unsubscribe_footer(rendered_body, subscriber['email'])
    tags = []
    if campaign_id:
        tags = [{'name': 'campaign_id', 'value': str(campaign_id)}]
    return send_email(subscriber['email'], rendered_subject, full_body, tags=tags,
                      headers=headers)


def _with_unsubscribe_footer(body_html, email):
    """Append the business footer + a working per-recipient unsubscribe link,
    and return RFC 8058 one-click List-Unsubscribe headers."""
    cfg = _get_app_helpers()['config']
    url = unsub_url(email)
    business_name = html.escape(cfg.get('business_name', 'Our Business'))
    full_body = f"""{body_html}
<hr style="margin-top: 40px; border: none; border-top: 1px solid #ccc;">
<p style="font-size: 12px; color: #999; text-align: center;">
{business_name}<br>
<a href="{html.escape(url)}" style="color: #999;">Unsubscribe</a>
</p>"""
    headers = {'List-Unsubscribe': f'<{url}>',
               'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click'}
    return full_body, headers


# ── Workflow engine ─────────────────────────────────────────────────────

def enroll_in_workflows(db, contact_id, trigger_type, trigger_context=None):
    """Check for active workflows matching this trigger and enroll the contact."""
    trigger_context = trigger_context or {}
    now = now_iso()
    workflows = db.execute(
        "SELECT * FROM workflows WHERE trigger_type = ? AND status = 'active'",
        (trigger_type,)
    ).fetchall()

    for w in workflows:
        config = json.loads(w['trigger_config']) if w['trigger_config'] else {}

        if trigger_type == 'tag_added' and config.get('tag_name'):
            if trigger_context.get('tag_name') != config['tag_name']:
                continue
        elif trigger_type == 'form_submitted' and config.get('form_name'):
            if trigger_context.get('form_name') != config['form_name']:
                continue
        elif trigger_type == 'order_placed' and config.get('product_match'):
            if trigger_context.get('product_match') != config['product_match']:
                continue

        existing = db.execute(
            "SELECT id FROM workflow_enrollments "
            "WHERE workflow_id = ? AND contact_id = ? AND status = 'active'",
            (w['id'], contact_id)
        ).fetchone()
        if existing:
            continue

        first_step = db.execute(
            "SELECT delay_minutes FROM workflow_steps "
            "WHERE workflow_id = ? ORDER BY step_order LIMIT 1",
            (w['id'],)
        ).fetchone()
        delay = first_step['delay_minutes'] if first_step else 0
        next_at = (datetime.fromisoformat(now) + timedelta(minutes=delay)).isoformat()

        db.execute(
            """INSERT INTO workflow_enrollments
               (id, workflow_id, contact_id, current_step, status,
                next_action_at, enrolled_at)
               VALUES (?, ?, ?, 0, 'active', ?, ?)""",
            (str(uuid.uuid4()), w['id'], contact_id, next_at, now))

    db.commit()


# ── Admin: Subscribers ──────────────────────────────────────────────────

def _admin_required(f):
    """Local admin check (delegates to app's pattern)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _is_admin():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def _cron_key_required(f):
    """Local cron key check (X-Cron-Key header only; URLs get logged)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import current_app
        cfg = current_app.config['_helpers']['config']
        cron_key = cfg.get('cron_key', '')
        key = request.headers.get('X-Cron-Key', '')
        if not cron_key or not _hmac.compare_digest(key, cron_key):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


@email_bp.route('/admin/subscribers')
@_admin_required
def admin_subscribers():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    tag_filter = request.args.get('tag', '')
    if tag_filter:
        subscribers = db.execute(
            "SELECT * FROM email_subscribers WHERE tags LIKE ? ORDER BY created_at DESC",
            (f'%"{tag_filter}"%',)
        ).fetchall()
    else:
        subscribers = db.execute(
            "SELECT * FROM email_subscribers ORDER BY created_at DESC"
        ).fetchall()
    active = sum(1 for s in subscribers if s['subscribed'])
    all_tags = set()
    for s in subscribers:
        try:
            for t in json.loads(s['tags'] or '[]'):
                all_tags.add(t)
        except (json.JSONDecodeError, TypeError):
            pass
    return render_template('admin/subscribers.html',
                           subscribers=subscribers,
                           active_count=active,
                           all_tags=sorted(all_tags),
                           current_tag=tag_filter)


@email_bp.route('/admin/subscribers/add', methods=['POST'])
@_admin_required
def admin_subscriber_add():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    email = request.form.get('email', '').strip()
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    tags_str = request.form.get('tags', '').strip()
    tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else []
    if not email:
        flash('Email is required.', 'error')
        return redirect(url_for('email_marketing.admin_subscribers'))
    _add_subscriber(db, email, name=name, phone=phone or None,
                    source='manual', tags=tags)
    flash(f'Subscriber {email} added.', 'success')
    return redirect(url_for('email_marketing.admin_subscribers'))


@email_bp.route('/admin/subscribers/<int:sub_id>/delete', methods=['POST'])
@_admin_required
def admin_subscriber_delete(sub_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    db.execute("DELETE FROM email_subscribers WHERE id = ?", (sub_id,))
    db.commit()
    flash('Subscriber removed.', 'success')
    return redirect(url_for('email_marketing.admin_subscribers'))


@email_bp.route('/admin/subscribers/<int:sub_id>/toggle', methods=['POST'])
@_admin_required
def admin_subscriber_toggle(sub_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    sub = db.execute(
        "SELECT * FROM email_subscribers WHERE id = ?", (sub_id,)
    ).fetchone()
    if sub:
        new_status = 0 if sub['subscribed'] else 1
        db.execute(
            "UPDATE email_subscribers SET subscribed = ?, updated_at = ? WHERE id = ?",
            (new_status, now_iso(), sub_id))
        db.commit()
        flash(f'Subscriber {"resubscribed" if new_status else "unsubscribed"}.', 'success')
    return redirect(url_for('email_marketing.admin_subscribers'))


@email_bp.route('/admin/subscribers/export')
@_admin_required
def admin_subscribers_export():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    subscribers = db.execute(
        "SELECT * FROM email_subscribers ORDER BY created_at DESC"
    ).fetchall()
    def _csv_safe(val):
        """Prefix cell values that could trigger formula injection."""
        val = str(val) if val else ''
        if val and val[0] in ('=', '+', '-', '@', '\t', '\r', '\n'):
            val = "'" + val
        return val.replace('"', '""')

    lines = ['Name,Email,Phone,Tags,Source,Subscribed,Date']
    for s in subscribers:
        tags = json.loads(s['tags'] or '[]')
        lines.append(
            f'"{_csv_safe(s["name"] or "")}","{_csv_safe(s["email"])}",'
            f'"{_csv_safe(s["phone"] or "")}",'
            f'"{_csv_safe(";".join(tags))}","{_csv_safe(s["source"])}",'
            f'{"Yes" if s["subscribed"] else "No"},"{s["created_at"] or ""}"')
    csv_content = '\n'.join(lines)
    return Response(csv_content, mimetype='text/csv',
                    headers={'Content-Disposition':
                             'attachment; filename=subscribers.csv'})


# ── Admin: Campaigns ───────────────────────────────────────────────────

@email_bp.route('/admin/campaigns')
@_admin_required
def admin_campaigns():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    campaigns = db.execute(
        "SELECT * FROM email_campaigns ORDER BY created_at DESC"
    ).fetchall()
    return render_template('admin/campaigns.html', campaigns=campaigns)


@email_bp.route('/admin/campaigns/new', methods=['GET', 'POST'])
@_admin_required
def admin_campaign_new():
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        if not subject or not body:
            flash('Subject and body are required.', 'error')
            return redirect(url_for('email_marketing.admin_campaign_new'))
        helpers = _get_app_helpers()
        db = helpers['get_db']()
        db.execute(
            "INSERT INTO email_campaigns (subject, body, created_at) VALUES (?, ?, ?)",
            (subject, body, now_iso()))
        db.commit()
        flash('Campaign created as draft.', 'success')
        return redirect(url_for('email_marketing.admin_campaigns'))
    return render_template('admin/campaign_edit.html', campaign=None)


@email_bp.route('/admin/campaigns/<int:campaign_id>')
@_admin_required
def admin_campaign_view(campaign_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    campaign = db.execute(
        "SELECT * FROM email_campaigns WHERE id = ?", (campaign_id,)
    ).fetchone()
    if not campaign:
        abort(404)

    sends = db.execute(
        "SELECT cs.*, "
        "COALESCE(cs.recipient_email, es.email) as email, "
        "COALESCE(cs.recipient_name, es.name) as name "
        "FROM campaign_sends cs "
        "LEFT JOIN email_subscribers es ON cs.subscriber_id = es.id "
        "WHERE cs.campaign_id = ? ORDER BY cs.sent_at DESC",
        (campaign_id,)
    ).fetchall()

    # Analytics from campaign_events
    analytics = {'has_data': False}
    try:
        events = db.execute(
            "SELECT * FROM campaign_events WHERE campaign_id = ? ORDER BY timestamp DESC",
            (campaign_id,)
        ).fetchall()
        total_sent = campaign['sent_count'] or 0
        unique_opens = len(set(
            e['subscriber_email'] for e in events if e['event_type'] == 'opened'))
        unique_clicks = len(set(
            e['subscriber_email'] for e in events if e['event_type'] == 'clicked'))
        total_delivered = len(set(
            e['subscriber_email'] for e in events if e['event_type'] == 'delivered'))
        bounces = len(set(
            e['subscriber_email'] for e in events if e['event_type'] == 'bounced'))

        analytics = {
            'total_sent': total_sent,
            'delivered': total_delivered,
            'unique_opens': unique_opens,
            'unique_clicks': unique_clicks,
            'bounces': bounces,
            'open_rate': round(unique_opens / total_sent * 100, 1) if total_sent else 0,
            'click_rate': round(unique_clicks / total_sent * 100, 1) if total_sent else 0,
            'has_data': len(events) > 0,
        }
    except Exception:
        pass

    return render_template('admin/campaign_view.html',
                           campaign=campaign, sends=sends, analytics=analytics)


@email_bp.route('/admin/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
@_admin_required
def admin_campaign_edit(campaign_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    campaign = db.execute(
        "SELECT * FROM email_campaigns WHERE id = ?", (campaign_id,)
    ).fetchone()
    if not campaign or campaign['status'] != 'draft':
        flash('Can only edit draft campaigns.', 'error')
        return redirect(url_for('email_marketing.admin_campaigns'))
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        if not subject or not body:
            flash('Subject and body are required.', 'error')
            return redirect(url_for('email_marketing.admin_campaign_edit',
                                    campaign_id=campaign_id))
        db.execute(
            "UPDATE email_campaigns SET subject = ?, body = ? WHERE id = ?",
            (subject, body, campaign_id))
        db.commit()
        flash('Campaign updated.', 'success')
        return redirect(url_for('email_marketing.admin_campaign_view',
                                campaign_id=campaign_id))
    return render_template('admin/campaign_edit.html', campaign=campaign)


@email_bp.route('/admin/api/campaigns/<int:campaign_id>/progress')
@_admin_required
def admin_campaign_progress(campaign_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    campaign = db.execute(
        "SELECT status, sent_count FROM email_campaigns WHERE id = ?",
        (campaign_id,)
    ).fetchone()
    if not campaign:
        return json.dumps({'error': 'not found'}), 404, {'Content-Type': 'application/json'}
    total_sends = db.execute(
        "SELECT COUNT(*) FROM campaign_sends WHERE campaign_id = ?",
        (campaign_id,)
    ).fetchone()[0]
    failed = db.execute(
        "SELECT COUNT(*) FROM campaign_sends WHERE campaign_id = ? AND status = 'failed'",
        (campaign_id,)
    ).fetchone()[0]
    return json.dumps({
        'status': campaign['status'],
        'sent_count': campaign['sent_count'] or 0,
        'total_sends': total_sends,
        'failed': failed
    }), 200, {'Content-Type': 'application/json'}


@email_bp.route('/admin/campaigns/<int:campaign_id>/send', methods=['GET', 'POST'])
@_admin_required
def admin_campaign_send(campaign_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    campaign = db.execute(
        "SELECT * FROM email_campaigns WHERE id = ?", (campaign_id,)
    ).fetchone()
    if not campaign:
        abort(404)
    if campaign['status'] == 'sent':
        flash('Campaign already sent.', 'error')
        return redirect(url_for('email_marketing.admin_campaign_view',
                                campaign_id=campaign_id))

    if request.method == 'GET':
        subscriber_count = db.execute(
            "SELECT COUNT(*) as c FROM email_subscribers WHERE subscribed = 1"
        ).fetchone()['c']

        all_subs = db.execute(
            "SELECT tags FROM email_subscribers WHERE subscribed = 1 "
            "AND tags IS NOT NULL AND tags != ''"
        ).fetchall()
        tag_counts = {}
        for s in all_subs:
            try:
                tags = json.loads(s['tags'])
                for t in tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
            except Exception:
                pass
        subscriber_tags = sorted(tag_counts.items(), key=lambda x: -x[1])

        contact_tags_raw = db.execute(
            "SELECT t.id, t.name, COUNT(ct.contact_id) as count FROM tags t "
            "JOIN contact_tags ct ON ct.tag_id = t.id "
            "JOIN contacts c ON c.id = ct.contact_id "
            "WHERE c.email IS NOT NULL AND c.email != '' "
            "GROUP BY t.id ORDER BY count DESC"
        ).fetchall()
        contact_tags = [{'id': r['id'], 'name': r['name'], 'count': r['count']}
                        for r in contact_tags_raw]
        contact_count = db.execute(
            "SELECT COUNT(*) as c FROM contacts WHERE email IS NOT NULL AND email != ''"
        ).fetchone()['c']

        return render_template('admin/campaign_send.html',
                               campaign=campaign,
                               subscriber_count=subscriber_count,
                               subscriber_tags=subscriber_tags,
                               contact_tags=contact_tags,
                               contact_count=contact_count)

    # POST -- send campaign
    source = request.form.get('source', 'subscribers')
    recipients = []

    if source == 'contacts':
        selected_tags = request.form.getlist('contact_tag')
        if not selected_tags:
            flash('Please select at least one contact tag.', 'error')
            return redirect(url_for('email_marketing.admin_campaign_send',
                                    campaign_id=campaign_id))
        placeholders = ','.join(['?'] * len(selected_tags))
        rows = db.execute(
            f"SELECT DISTINCT c.id, c.first_name, c.last_name, c.email FROM contacts c "
            f"JOIN contact_tags ct ON ct.contact_id = c.id "
            f"WHERE ct.tag_id IN ({placeholders}) AND c.email IS NOT NULL AND c.email != '' "
            f"AND COALESCE(c.unsubscribed, 0) = 0 "
            f"AND LOWER(c.email) NOT IN (SELECT LOWER(email) FROM email_subscribers "
            f"WHERE subscribed = 0)",
            selected_tags
        ).fetchall()
        for r in rows:
            name = ((r['first_name'] or '') + ' ' + (r['last_name'] or '')).strip()
            recipients.append({
                'id': r['id'], 'email': r['email'],
                'name': name, 'first_name': r['first_name'] or ''})
    else:
        sub_tags = request.form.getlist('sub_tag')
        all_subs = db.execute(
            "SELECT * FROM email_subscribers WHERE subscribed = 1"
        ).fetchall()
        if '__all__' in sub_tags or not sub_tags:
            recipients = [{
                'id': s['id'], 'email': s['email'],
                'name': s['name'] or '',
                'first_name': (s['name'] or '').split()[0] if s['name'] else ''}
                for s in all_subs]
        else:
            for s in all_subs:
                try:
                    stags = json.loads(s['tags']) if s['tags'] else []
                except Exception:
                    stags = []
                if any(t in stags for t in sub_tags):
                    recipients.append({
                        'id': s['id'], 'email': s['email'],
                        'name': s['name'] or '',
                        'first_name': (s['name'] or '').split()[0] if s['name'] else ''})

    if not recipients:
        flash('No recipients found with the selected filters.', 'error')
        return redirect(url_for('email_marketing.admin_campaign_send',
                                campaign_id=campaign_id))

    db.execute(
        "UPDATE email_campaigns SET status = 'sending', sent_count = 0 WHERE id = ?",
        (campaign_id,))
    db.commit()

    recipient_list = [{
        'id': r.get('id'), 'email': r['email'],
        'name': r.get('name', ''), 'first_name': r.get('first_name', '')}
        for r in recipients]

    from flask import current_app
    app_obj = current_app._get_current_object()

    def _background_send(app_obj, cid, rlist, subject, body, src):
        import time as _time
        with app_obj.app_context():
            h = app_obj.config['_helpers']
            db = h['get_db']()
            sent = 0
            failed = 0
            backoff = 0.5

            for i, sub in enumerate(rlist):
                _time.sleep(backoff)
                try:
                    resend_id = _send_campaign_email(
                        sub, subject, body, campaign_id=cid)
                except Exception:
                    resend_id = None

                if resend_id is None:
                    _time.sleep(3)
                    try:
                        resend_id = _send_campaign_email(
                            sub, subject, body, campaign_id=cid)
                    except ValueError:
                        _time.sleep(10)
                        try:
                            resend_id = _send_campaign_email(
                                sub, subject, body, campaign_id=cid)
                        except Exception:
                            resend_id = None
                    except Exception:
                        resend_id = None

                status = 'sent' if resend_id else 'failed'
                db.execute(
                    "INSERT INTO campaign_sends "
                    "(campaign_id, subscriber_id, sent_at, status, resend_email_id, "
                    "recipient_email, recipient_name) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (cid, sub['id'] if isinstance(sub.get('id'), int) else None,
                     now_iso(), status,
                     resend_id if isinstance(resend_id, str) else None,
                     sub['email'], sub.get('name', '')))

                if resend_id:
                    sent += 1
                    backoff = 0.5
                else:
                    failed += 1
                    backoff = min(backoff * 1.5, 5)

                if (i + 1) % 25 == 0:
                    db.execute(
                        "UPDATE email_campaigns SET sent_count = ? WHERE id = ?",
                        (sent, cid))
                    db.commit()

            db.execute(
                "UPDATE email_campaigns SET status = 'sent', sent_count = ?, "
                "sent_at = ? WHERE id = ?",
                (sent, now_iso(), cid))
            db.commit()
            sys.stderr.write(
                f"[CAMPAIGN {cid}] Complete: {sent} sent, {failed} failed "
                f"out of {len(rlist)} recipients\n")

    t = threading.Thread(
        target=_background_send,
        args=(app_obj, campaign_id, recipient_list,
              campaign['subject'], campaign['body'], source),
        daemon=True)
    t.start()

    flash(f'Campaign queued for {len(recipient_list)} recipients. '
          f'Sending at ~2/second.', 'success')
    return redirect(url_for('email_marketing.admin_campaign_view',
                            campaign_id=campaign_id))


@email_bp.route('/admin/campaigns/<int:campaign_id>/delete', methods=['POST'])
@_admin_required
def admin_campaign_delete(campaign_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    db.execute("DELETE FROM campaign_sends WHERE campaign_id = ?", (campaign_id,))
    db.execute("DELETE FROM email_campaigns WHERE id = ?", (campaign_id,))
    db.commit()
    flash('Campaign deleted.', 'success')
    return redirect(url_for('email_marketing.admin_campaigns'))


# ── Public: Unsubscribe ─────────────────────────────────────────────────
# GET = unsubscribe link in the email footer. POST = RFC 8058 one-click
# (List-Unsubscribe-Post), CSRF-exempt in app.py. Both opt the address out of
# the subscriber list AND the CRM contact list.

@email_bp.route('/unsubscribe/<token>', methods=['GET', 'POST'])
def unsubscribe(token):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    email = None
    legacy = db.execute(
        "SELECT email FROM email_subscribers WHERE unsubscribe_token = ?", (token,)
    ).fetchone()
    if legacy:
        email = legacy['email']
    else:
        email = parse_unsub_token(token)
    if not email:
        return render_template('public/unsubscribe.html',
                               success=False, email=None), 404
    email = email.strip().lower()
    now = now_iso()
    db.execute(
        "UPDATE email_subscribers SET subscribed = 0, updated_at = ? "
        "WHERE LOWER(email) = ?", (now, email))
    db.execute(
        "UPDATE contacts SET unsubscribed = 1, unsubscribed_at = ?, updated_at = ? "
        "WHERE LOWER(email) = ?", (now, now, email))
    db.commit()
    if request.method == 'POST':
        return jsonify({'ok': True}), 200
    return render_template('public/unsubscribe.html', success=True, email=email)


# ── Public: Subscribe endpoint (double opt-in) ──────────────────────────

def _same_site_back():
    """Redirect target: the referring page only if it is on this host."""
    from urllib.parse import urlparse
    ref = request.referrer or ''
    parsed = urlparse(ref)
    if parsed.netloc and parsed.netloc == request.host and \
            parsed.path.startswith('/') and not parsed.path.startswith('//'):
        return parsed.path + (('?' + parsed.query) if parsed.query else '')
    return url_for('index')


@email_bp.route('/subscribe', methods=['POST'])
def subscribe():
    from flask import current_app
    rate_fn = current_app.config.get('_rate_limited')
    if rate_fn and rate_fn(request.remote_addr):
        flash('Too many submissions. Please wait a moment.', 'error')
        return redirect(_same_site_back())
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    email = request.form.get('email', '').strip()[:254]
    name = request.form.get('name', '').strip()[:200]
    source = request.form.get('source', 'website').strip()[:50]
    if email and '@' in email:
        _add_subscriber(db, email, name=name, source=source, tags=['website'],
                        public=True)
        # Same message whether or not the address was already known.
        flash('Thanks! Check your inbox to confirm your subscription.', 'success')
    else:
        flash('Email is required.', 'error')
    return redirect(_same_site_back())


@email_bp.route('/subscribe/confirm/<token>', methods=['GET', 'POST'])
def subscribe_confirm(token):
    """GET shows a button (mail scanners prefetch links); POST confirms."""
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    digest = hashlib.sha256(token.encode()).hexdigest()
    sub = db.execute(
        "SELECT id, email, confirm_sent_at FROM email_subscribers "
        "WHERE confirm_token_hash = ?", (digest,)).fetchone()
    valid = bool(sub)
    if valid and sub['confirm_sent_at']:
        try:
            sent = datetime.fromisoformat(sub['confirm_sent_at'])
            valid = datetime.now() - sent < timedelta(days=7)
        except ValueError:
            valid = False
    if not valid:
        return render_template('public/subscribe_confirm.html', state='invalid'), 404
    if request.method == 'POST':
        now = now_iso()
        db.execute(
            "UPDATE email_subscribers SET subscribed = 1, confirmed_at = ?, "
            "confirm_token_hash = NULL, updated_at = ? WHERE id = ?",
            (now, now, sub['id']))
        db.execute(
            "UPDATE contacts SET unsubscribed = 0, unsubscribed_at = NULL "
            "WHERE LOWER(email) = ?", (sub['email'].lower(),))
        db.commit()
        return render_template('public/subscribe_confirm.html', state='done')
    return render_template('public/subscribe_confirm.html', state='ask')


# ── Webhook: Resend email tracking ──────────────────────────────────────

def _verify_svix_signature(payload_bytes, headers, secret):
    """Verify Svix webhook signature (used by Resend).

    Args:
        payload_bytes: Raw request body bytes.
        headers: Request headers dict-like.
        secret: The Resend webhook signing secret (whsec_...).

    Returns:
        True if signature is valid, False otherwise.
    """
    msg_id = headers.get('svix-id', '')
    timestamp = headers.get('svix-timestamp', '')
    signatures = headers.get('svix-signature', '')

    if not msg_id or not timestamp or not signatures:
        return False

    # Check timestamp freshness (reject if > 5 minutes old)
    try:
        ts = int(timestamp)
        now = int(datetime.now().timestamp())
        if abs(now - ts) > 300:
            return False
    except (ValueError, TypeError):
        return False

    # Strip whsec_ prefix if present and decode
    if secret.startswith('whsec_'):
        secret = secret[6:]
    try:
        secret_bytes = base64.b64decode(secret)
    except Exception:
        return False

    # Compute expected signature
    to_sign = f"{msg_id}.{timestamp}.".encode() + payload_bytes
    expected = base64.b64encode(
        _hmac.new(secret_bytes, to_sign, hashlib.sha256).digest()
    ).decode()

    # Check against any of the provided signatures (comma-separated)
    for sig in signatures.split(' '):
        sig_parts = sig.split(',', 1)
        sig_value = sig_parts[-1]  # after version prefix like "v1,"
        if _hmac.compare_digest(sig_value, expected):
            return True
    return False


@email_bp.route('/api/webhook/resend', methods=['POST'])
def resend_webhook():
    # ── C5: Verify Svix signature ──────────────────────────────────
    helpers = _get_app_helpers()
    cfg = helpers['config']
    resend_secret = cfg.get('resend_webhook_secret', '')

    if resend_secret:
        payload_bytes = request.get_data()
        if not _verify_svix_signature(payload_bytes, request.headers, resend_secret):
            return jsonify({'error': 'Invalid signature'}), 401
        # Replay protection beyond the 5-minute window: dedupe on svix-id.
        db = helpers['get_db']()
        cur = db.execute(
            "INSERT OR IGNORE INTO processed_events (source, event_id, received_at) "
            "VALUES ('resend', ?, ?)", (request.headers.get('svix-id', ''), now_iso()))
        db.commit()
        if cur.rowcount == 0:
            return jsonify({'status': 'duplicate'}), 200
    else:
        # No secret configured -- reject in production to prevent
        # unauthenticated writes. Log a warning.
        sys.stderr.write(
            "[EMAIL] WARNING: Resend webhook called but RESEND_WEBHOOK_SECRET "
            "not configured. Rejecting.\n")
        return jsonify({'error': 'Webhook secret not configured'}), 403

    try:
        payload = request.get_json(force=True)
    except Exception:
        return jsonify({'error': 'invalid json'}), 400

    event_type = payload.get('type', '')
    data = payload.get('data', {})
    type_map = {
        'email.delivered': 'delivered',
        'email.opened': 'opened',
        'email.clicked': 'clicked',
        'email.bounced': 'bounced',
        'email.complained': 'spam',
    }
    simple_type = type_map.get(event_type)
    if not simple_type:
        return jsonify({'status': 'ignored'}), 200

    resend_email_id = data.get('email_id', '')
    to_list = data.get('to', [])
    subscriber_email = to_list[0] if to_list else ''
    link_url = (data.get('click', {}).get('link', '')
                if simple_type == 'clicked' else '')
    timestamp = data.get('created_at', now_iso())

    campaign_id = None
    tags = data.get('tags', {})
    if isinstance(tags, dict):
        campaign_id = tags.get('campaign_id')
    elif isinstance(tags, list):
        for t in tags:
            if isinstance(t, dict) and t.get('name') == 'campaign_id':
                campaign_id = t.get('value')
                break

    helpers = _get_app_helpers()
    db = helpers['get_db']()

    if not campaign_id and resend_email_id:
        row = db.execute(
            "SELECT campaign_id FROM campaign_sends WHERE resend_email_id = ?",
            (resend_email_id,)
        ).fetchone()
        if row:
            campaign_id = row['campaign_id']

    db.execute(
        "INSERT INTO campaign_events "
        "(campaign_id, subscriber_email, resend_email_id, event_type, "
        "link_url, timestamp, raw_data) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (campaign_id, subscriber_email, resend_email_id, simple_type,
         link_url, timestamp, json.dumps(data)))
    db.commit()
    return jsonify({'status': 'ok'}), 200


# ── Workflow Processor (cron endpoint) ──────────────────────────────────

@email_bp.route('/api/process-workflows', methods=['POST'])
@_cron_key_required
def api_process_workflows():
    """Process pending workflow steps. Call via cron every 5 minutes."""
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    send_crm_email = helpers.get('send_crm_email', helpers['send_email'])
    now = now_iso()
    processed = 0
    errors = 0

    pending = db.execute("""
        SELECT we.*, w.status as workflow_status
        FROM workflow_enrollments we
        JOIN workflows w ON we.workflow_id = w.id
        WHERE we.status = 'active' AND we.next_action_at <= ? AND w.status = 'active'
        ORDER BY we.next_action_at LIMIT 100
    """, (now,)).fetchall()

    for enrollment in pending:
        try:
            step_num = enrollment['current_step']
            steps = db.execute(
                "SELECT * FROM workflow_steps WHERE workflow_id = ? ORDER BY step_order",
                (enrollment['workflow_id'],)
            ).fetchall()

            if step_num >= len(steps):
                db.execute(
                    "UPDATE workflow_enrollments SET status='completed', "
                    "completed_at=? WHERE id=?",
                    (now, enrollment['id']))
                processed += 1
                continue

            step = steps[step_num]
            config = json.loads(step['action_config']) if step['action_config'] else {}
            contact = db.execute(
                "SELECT * FROM contacts WHERE id = ?",
                (enrollment['contact_id'],)
            ).fetchone()

            if not contact:
                db.execute(
                    "UPDATE workflow_enrollments SET status='error' WHERE id=?",
                    (enrollment['id'],))
                errors += 1
                continue

            if step['action_type'] == 'send_email':
                template = db.execute(
                    "SELECT * FROM email_templates WHERE id = ?",
                    (config.get('template_id', ''),)
                ).fetchone()
                if template and contact['email'] and not contact['unsubscribed']:
                    subj = template['subject'] or ''
                    body = template['body_html'] or ''
                    for field in ['first_name', 'last_name', 'email',
                                  'phone', 'company_name']:
                        # Contact fields can come from public forms: escape
                        # into HTML, strip line breaks from the subject.
                        raw = contact[field] or ''
                        body = body.replace('{{' + field + '}}', html.escape(raw))
                        subj = subj.replace('{{' + field + '}}',
                                            ' '.join(raw.split())[:100])
                    body, list_headers = _with_unsubscribe_footer(body, contact['email'])
                    if send_crm_email is helpers['send_email']:
                        result = send_crm_email(contact['email'], subj, body,
                                                headers=list_headers)
                    else:
                        result = send_crm_email(contact['email'], subj, body)
                    ok = result is not None and result is not False
                    if ok:
                        db.execute(
                            """INSERT INTO email_log
                               (id, contact_id, template_id, workflow_id,
                                to_email, subject, status, sent_at)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            (str(uuid.uuid4()), contact['id'], template['id'],
                             enrollment['workflow_id'], contact['email'],
                             subj, 'sent', now))

            elif step['action_type'] == 'add_tag':
                tag_name = config.get('tag_name', '')
                if tag_name:
                    tag = db.execute(
                        "SELECT id FROM tags WHERE name = ?", (tag_name,)
                    ).fetchone()
                    if not tag:
                        tag_id = str(uuid.uuid4())
                        db.execute(
                            "INSERT INTO tags (id, name, created_at) VALUES (?, ?, ?)",
                            (tag_id, tag_name, now))
                    else:
                        tag_id = tag['id']
                    try:
                        db.execute(
                            "INSERT INTO contact_tags (contact_id, tag_id, added_at) "
                            "VALUES (?, ?, ?)",
                            (contact['id'], tag_id, now))
                    except Exception:
                        pass

            elif step['action_type'] == 'remove_tag':
                tag_name = config.get('tag_name', '')
                if tag_name:
                    tag = db.execute(
                        "SELECT id FROM tags WHERE name = ?", (tag_name,)
                    ).fetchone()
                    if tag:
                        db.execute(
                            "DELETE FROM contact_tags "
                            "WHERE contact_id = ? AND tag_id = ?",
                            (contact['id'], tag['id']))

            # Advance
            next_step = step_num + 1
            if next_step < len(steps):
                next_delay = steps[next_step]['delay_minutes']
                next_at = (datetime.fromisoformat(now)
                           + timedelta(minutes=next_delay)).isoformat()
                db.execute(
                    "UPDATE workflow_enrollments SET current_step = ?, "
                    "next_action_at = ? WHERE id = ?",
                    (next_step, next_at, enrollment['id']))
            else:
                db.execute(
                    "UPDATE workflow_enrollments SET status = 'completed', "
                    "completed_at = ?, current_step = ? WHERE id = ?",
                    (now, next_step, enrollment['id']))

            processed += 1
        except Exception as e:
            errors += 1
            sys.stderr.write(
                f"Workflow error for enrollment {enrollment['id']}: {e}\n")

    db.commit()
    return jsonify({'processed': processed, 'errors': errors, 'pending': len(pending)})


# ── Module registration ─────────────────────────────────────────────────

def get_nav_items():
    """Return nav items for admin sidebar."""
    return [
        {'divider': True},
        {'label': 'Subscribers', 'endpoint': 'email_marketing.admin_subscribers',
         'match': 'email_marketing.admin_subscriber'},
        {'label': 'Campaigns', 'endpoint': 'email_marketing.admin_campaigns',
         'match': 'email_marketing.admin_campaign'},
    ]


def get_metrics(db):
    """Return dashboard KPI metrics."""
    metrics = []
    active_subs = db.execute(
        "SELECT COUNT(*) as c FROM email_subscribers WHERE subscribed = 1"
    ).fetchone()['c']
    metrics.append({'label': 'Subscribers', 'value': active_subs})

    total_campaigns = db.execute(
        "SELECT COUNT(*) as c FROM email_campaigns"
    ).fetchone()['c']
    metrics.append({'label': 'Campaigns', 'value': total_campaigns})

    return metrics


def get_schema():
    """Return SQL schema for this module's tables."""
    return EMAIL_SCHEMA
