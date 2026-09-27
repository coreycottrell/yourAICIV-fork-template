"""
Affiliates Module
==================
Affiliate/referral program: apply, dashboard, admin management,
click tracking, commission tracking, payouts.
Toggleable via config: modules.affiliates
"""

import json
import uuid
import html
import time
import secrets
import hashlib
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, g, jsonify, abort, session,
                   after_this_request)

affiliates_bp = Blueprint('affiliates', __name__,
                          template_folder='../templates')


def _is_admin():
    """Admin check shared with app.py (honours session revocation)."""
    from flask import current_app
    return current_app.config['_helpers']['is_admin']()

# ── Schema extension ────────────────────────────────────────────────────

AFFILIATES_SCHEMA = """
CREATE TABLE IF NOT EXISTS affiliates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    website TEXT,
    social_media TEXT,
    how_promote TEXT,
    referral_code TEXT UNIQUE NOT NULL,
    commission_rate REAL DEFAULT 0.20,
    recurring_rate REAL DEFAULT 0.10,
    tier INTEGER DEFAULT 1,
    payout_method TEXT DEFAULT 'zelle',
    zelle_address TEXT,
    status TEXT DEFAULT 'pending',
    total_clicks INTEGER DEFAULT 0,
    total_sales INTEGER DEFAULT 0,
    total_revenue REAL DEFAULT 0.0,
    total_earned REAL DEFAULT 0.0,
    total_paid REAL DEFAULT 0.0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS referral_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    affiliate_id TEXT REFERENCES affiliates(id),
    ip_address TEXT,
    landing_page TEXT,
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS commissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    affiliate_id TEXT REFERENCES affiliates(id),
    order_id TEXT,
    order_total REAL NOT NULL,
    commission_rate REAL NOT NULL,
    commission_amount REAL NOT NULL,
    commission_type TEXT DEFAULT 'initial',
    status TEXT DEFAULT 'pending',
    payout_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    paid_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS affiliate_payouts (
    id TEXT PRIMARY KEY,
    affiliate_id TEXT REFERENCES affiliates(id),
    amount REAL NOT NULL,
    payout_method TEXT NOT NULL,
    reference TEXT,
    status TEXT DEFAULT 'pending',
    commission_ids TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Magic-link sign-in: only the SHA-256 of each single-use token is stored.
CREATE TABLE IF NOT EXISTS affiliate_login_tokens (
    token_hash TEXT PRIMARY KEY,
    affiliate_id TEXT NOT NULL REFERENCES affiliates(id),
    expires_at REAL NOT NULL,
    used_at REAL
);
"""

LOGIN_LINK_TTL_SECONDS = 30 * 60


def now_iso():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _get_app_helpers():
    from flask import current_app
    return current_app.config['_helpers']


def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not _is_admin():
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


# ── Referral tracking (before_request) ──────────────────────────────────

@affiliates_bp.before_app_request
def track_affiliate_referral():
    """Capture affiliate referral code from URL and store in cookie."""
    ref = request.args.get('ref')
    if ref and request.endpoint not in ('static',):
        helpers = _get_app_helpers()
        db = helpers['get_db']()
        aff = db.execute(
            "SELECT id FROM affiliates WHERE referral_code = ? AND status = 'approved'",
            (ref,)
        ).fetchone()
        if aff:
            db.execute(
                "INSERT INTO referral_clicks "
                "(affiliate_id, ip_address, landing_page) VALUES (?, ?, ?)",
                (aff['id'], request.remote_addr, request.path))
            db.execute(
                "UPDATE affiliates SET total_clicks = total_clicks + 1 WHERE id = ?",
                (aff['id'],))
            db.commit()

            @after_this_request
            def set_ref_cookie(response):
                response.set_cookie(
                    'aff_ref', ref,
                    max_age=60 * 60 * 24 * 60,
                    httponly=True, samesite='Lax')
                return response


def attribute_order_to_affiliate(order_id, order_total):
    """Check for affiliate cookie and create commission record.
    Call from checkout flow after order creation."""
    ref_code = request.cookies.get('aff_ref')
    if not ref_code:
        return None
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    aff = db.execute(
        "SELECT * FROM affiliates WHERE referral_code = ? AND status = 'approved'",
        (ref_code,)
    ).fetchone()
    if not aff:
        return None
    existing = db.execute(
        "SELECT id FROM commissions WHERE order_id = ? AND affiliate_id = ?",
        (order_id, aff['id'])
    ).fetchone()
    if existing:
        return aff['id']
    commission_amount = round(order_total * aff['commission_rate'], 2)
    db.execute(
        "INSERT INTO commissions "
        "(affiliate_id, order_id, order_total, commission_rate, "
        "commission_amount, commission_type, status) "
        "VALUES (?, ?, ?, ?, ?, 'initial', 'pending')",
        (aff['id'], order_id, order_total, aff['commission_rate'],
         commission_amount))
    db.execute(
        "UPDATE affiliates SET total_sales = total_sales + 1, "
        "total_revenue = total_revenue + ?, total_earned = total_earned + ? "
        "WHERE id = ?",
        (order_total, commission_amount, aff['id']))
    db.commit()
    return aff['id']


# ── Public: Affiliate apply ────────────────────────────────────────────

@affiliates_bp.route('/affiliate/apply', methods=['GET', 'POST'])
def affiliate_apply():
    if request.method == 'POST':
        from flask import current_app
        rate_fn = current_app.config.get('_rate_limited')
        if rate_fn and rate_fn(request.remote_addr):
            flash('Too many submissions. Please wait a moment.', 'error')
            return redirect(url_for('affiliates.affiliate_apply'))
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        if not name or not email:
            flash('Name and email are required.', 'error')
            return redirect(url_for('affiliates.affiliate_apply'))
        helpers = _get_app_helpers()
        db = helpers['get_db']()
        existing = db.execute(
            "SELECT id FROM affiliates WHERE email = ?", (email,)
        ).fetchone()
        if existing:
            flash('An application with this email already exists.', 'info')
            return redirect(url_for('affiliates.affiliate_apply'))
        aff_id = str(uuid.uuid4())[:8]
        code = None
        for _ in range(10):
            first = name.upper().split()[0][:10] if name else 'AFF'
            suffix = uuid.uuid4().hex[:4].upper()
            code = f"REF-{first}-{suffix}"
            dup = db.execute(
                "SELECT id FROM affiliates WHERE referral_code = ?", (code,)
            ).fetchone()
            if not dup:
                break
        payout_method = request.form.get('payout_method', 'zelle')
        zelle_address = request.form.get('zelle_address', '').strip()
        db.execute(
            """INSERT INTO affiliates
               (id, name, email, phone, website, social_media, how_promote,
                referral_code, payout_method, zelle_address, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (aff_id, name, email,
             request.form.get('phone', '').strip(),
             request.form.get('website', '').strip(),
             request.form.get('social_media', '').strip(),
             request.form.get('how_promote', '').strip(),
             code, payout_method, zelle_address,
             datetime.now().isoformat()))
        db.commit()
        helpers['notify_owner'](
            f"New affiliate application: {name} ({email}). "
            "Review it under Admin > Affiliates.", event="affiliate")
        flash('Your affiliate application has been submitted!', 'success')
        return redirect(url_for('affiliates.affiliate_apply'))
    return render_template('public/affiliate_apply.html')


# ── Public: Affiliate login (magic link) ───────────────────────────────
# The referral code is PUBLIC (it is in every ?ref= link), so it is never a
# credential. Sign-in = a single-use, 30-minute link emailed to the
# affiliate's address (or handed over by the admin), approved affiliates only.

def _issue_login_link(db, aff_id):
    token = secrets.token_urlsafe(32)
    now = time.time()
    db.execute("DELETE FROM affiliate_login_tokens WHERE expires_at < ?", (now,))
    db.execute(
        "INSERT INTO affiliate_login_tokens (token_hash, affiliate_id, expires_at) "
        "VALUES (?, ?, ?)",
        (hashlib.sha256(token.encode()).hexdigest(), aff_id,
         now + LOGIN_LINK_TTL_SECONDS))
    db.commit()
    base = _get_app_helpers()['base_url']()
    return f"{base}/affiliate/login/{token}"


def _approved_affiliate(db, aff_id):
    return db.execute(
        "SELECT * FROM affiliates WHERE id = ? AND status = 'approved'",
        (aff_id,)).fetchone()


@affiliates_bp.route('/affiliate/login', methods=['GET', 'POST'])
def affiliate_login():
    if request.method == 'POST':
        from flask import current_app
        rate_fn = current_app.config.get('_rate_limited')
        if rate_fn and rate_fn(request.remote_addr, window=300, max_attempts=10):
            flash('Too many attempts. Try again later.', 'error')
            return render_template('public/affiliate_login.html'), 429

        aff_email = request.form.get('email', '').strip().lower()[:254]
        if not aff_email:
            flash('Email is required.', 'error')
            return render_template('public/affiliate_login.html')

        helpers = _get_app_helpers()
        db = helpers['get_db']()
        aff = db.execute(
            "SELECT id, name FROM affiliates WHERE email = ? AND status = 'approved'",
            (aff_email,)).fetchone()
        # Per-address cap so this form cannot be used to mail-bomb anyone.
        if aff and not (rate_fn and rate_fn(aff_email, window=3600, max_attempts=3,
                                            scope='affiliate-login-mail')):
            link = _issue_login_link(db, aff['id'])
            business = helpers['config'].get('business_name', 'our affiliate program')
            body = (f"<p>Hi {html.escape(aff['name'] or '')},</p>"
                    f"<p><a href=\"{html.escape(link)}\">Sign in to your affiliate "
                    f"dashboard</a>. The link works once and expires in 30 minutes.</p>"
                    f"<p style=\"font-size: 12px; color: #999;\">If you did not "
                    f"request this, ignore this email.</p>")
            if helpers['send_email'](aff_email, f"Your sign-in link for {business}",
                                     body) is None:
                current_app.logger.warning(
                    "affiliate login link not emailed (email not configured); "
                    "admin can issue one from the affiliate's admin page")
        # Same answer whether or not the address is an approved affiliate.
        flash('If that email belongs to an approved affiliate, a sign-in link '
              'is on its way.', 'success')
        return render_template('public/affiliate_login.html')

    return render_template('public/affiliate_login.html')


@affiliates_bp.route('/affiliate/login/<token>', methods=['GET', 'POST'])
def affiliate_login_token(token):
    """GET shows a button (mail scanners prefetch links); POST signs in."""
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    digest = hashlib.sha256(token.encode()).hexdigest()
    row = db.execute(
        "SELECT * FROM affiliate_login_tokens WHERE token_hash = ?",
        (digest,)).fetchone()
    now = time.time()
    if not row or row['used_at'] or row['expires_at'] < now or \
            not _approved_affiliate(db, row['affiliate_id']):
        flash('That sign-in link is invalid, used, or expired. Request a new one.',
              'error')
        return render_template('public/affiliate_login.html'), 410
    if request.method == 'POST':
        cur = db.execute(
            "UPDATE affiliate_login_tokens SET used_at = ? "
            "WHERE token_hash = ? AND used_at IS NULL", (now, digest))
        db.commit()
        if cur.rowcount != 1:
            abort(410)
        session.pop('affiliate_id', None)
        session.pop('affiliate_email', None)
        session['affiliate_id'] = row['affiliate_id']
        return redirect(url_for('affiliates.affiliate_dashboard'))
    return render_template('public/affiliate_login.html', confirm_token=True)


@affiliates_bp.route('/affiliate/logout', methods=['POST'])
def affiliate_logout():
    session.pop('affiliate_id', None)
    session.pop('affiliate_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('affiliates.affiliate_login'))


# ── Public: Affiliate dashboard (session-gated) ───────────────────────

@affiliates_bp.route('/affiliate/dashboard')
def affiliate_dashboard():
    aff_id = session.get('affiliate_id')
    if not aff_id:
        return redirect(url_for('affiliates.affiliate_login'))

    helpers = _get_app_helpers()
    db = helpers['get_db']()
    aff = _approved_affiliate(db, aff_id)   # suspension applies immediately
    if not aff:
        session.pop('affiliate_id', None)
        session.pop('affiliate_email', None)
        flash('Session expired. Please log in again.', 'error')
        return redirect(url_for('affiliates.affiliate_login'))

    commissions = db.execute(
        "SELECT * FROM commissions WHERE affiliate_id = ? ORDER BY created_at DESC LIMIT 50",
        (aff['id'],)
    ).fetchall()
    pending_amount = db.execute(
        "SELECT COALESCE(SUM(commission_amount), 0) as total FROM commissions "
        "WHERE affiliate_id = ? AND status IN ('pending', 'approved')",
        (aff['id'],)
    ).fetchone()['total']

    from flask import current_app
    client_cfg = current_app.config['_helpers']['config']
    domain = client_cfg.get('domain', 'example.com')
    referral_url = f"https://{domain}/?ref={aff['referral_code']}"
    stats = {
        'total_clicks': aff['total_clicks'],
        'total_conversions': aff['total_sales'],
        'total_earned': aff['total_earned'],
        'pending': pending_amount,
    }
    return render_template('public/affiliate_dashboard.html',
                           aff=aff, commissions=commissions,
                           pending_amount=pending_amount,
                           stats=stats, referral_url=referral_url)


# ── Admin: Affiliates ──────────────────────────────────────────────────

@affiliates_bp.route('/admin/affiliates')
@_admin_required
def admin_affiliates():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    affiliates_list = db.execute(
        "SELECT * FROM affiliates ORDER BY created_at DESC"
    ).fetchall()
    pending_count = db.execute(
        "SELECT COUNT(*) as c FROM affiliates WHERE status = 'pending'"
    ).fetchone()['c']
    total_commissions = db.execute(
        "SELECT COALESCE(SUM(commission_amount), 0) as total FROM commissions"
    ).fetchone()['total']
    return render_template('admin/affiliates.html',
                           affiliates=affiliates_list,
                           pending_count=pending_count,
                           total_commissions=total_commissions)


@affiliates_bp.route('/admin/affiliates/<aff_id>')
@_admin_required
def admin_affiliate_detail(aff_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    aff = db.execute(
        "SELECT * FROM affiliates WHERE id = ?", (aff_id,)
    ).fetchone()
    if not aff:
        flash('Affiliate not found.', 'error')
        return redirect(url_for('affiliates.admin_affiliates'))
    commissions = db.execute(
        "SELECT * FROM commissions WHERE affiliate_id = ? ORDER BY created_at DESC",
        (aff_id,)
    ).fetchall()
    clicks_30d = db.execute(
        "SELECT COUNT(*) as c FROM referral_clicks "
        "WHERE affiliate_id = ? AND clicked_at > datetime('now', '-30 days')",
        (aff_id,)
    ).fetchone()['c']
    pending = db.execute(
        "SELECT COALESCE(SUM(commission_amount), 0) as total FROM commissions "
        "WHERE affiliate_id = ? AND status IN ('pending', 'approved')",
        (aff_id,)
    ).fetchone()['total']
    return render_template('admin/affiliate_detail.html',
                           aff=aff, commissions=commissions,
                           clicks_30d=clicks_30d, pending=pending)


@affiliates_bp.route('/admin/affiliates/<aff_id>/approve', methods=['POST'])
@_admin_required
def admin_affiliate_approve(aff_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    db.execute(
        "UPDATE affiliates SET status = 'approved', approved_at = ? WHERE id = ?",
        (datetime.now().isoformat(), aff_id))
    db.commit()
    flash('Affiliate approved!', 'success')
    return redirect(url_for('affiliates.admin_affiliate_detail', aff_id=aff_id))


@affiliates_bp.route('/admin/affiliates/<aff_id>/login-link', methods=['POST'])
@_admin_required
def admin_affiliate_login_link(aff_id):
    """Issue a single-use sign-in link for manual delivery (e.g. when email
    is not configured). Shown once to the admin, never stored in clear."""
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    if not _approved_affiliate(db, aff_id):
        flash('Only approved affiliates can sign in.', 'error')
    else:
        link = _issue_login_link(db, aff_id)
        flash(f'One-time sign-in link (30 min, single use): {link}', 'success')
    return redirect(url_for('affiliates.admin_affiliate_detail', aff_id=aff_id))


@affiliates_bp.route('/admin/affiliates/<aff_id>/suspend', methods=['POST'])
@_admin_required
def admin_affiliate_suspend(aff_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    db.execute(
        "UPDATE affiliates SET status = 'suspended' WHERE id = ?", (aff_id,))
    db.commit()
    flash('Affiliate suspended.', 'success')
    return redirect(url_for('affiliates.admin_affiliate_detail', aff_id=aff_id))


# ── Module registration ─────────────────────────────────────────────────

def get_nav_items():
    return [
        {'label': 'Affiliates', 'endpoint': 'affiliates.admin_affiliates',
         'match': 'affiliates.admin_affiliate'},
    ]


def get_metrics(db):
    total = db.execute(
        "SELECT COUNT(*) as c FROM affiliates WHERE status = 'approved'"
    ).fetchone()['c']
    pending = db.execute(
        "SELECT COUNT(*) as c FROM affiliates WHERE status = 'pending'"
    ).fetchone()['c']
    metrics = [{'label': 'Affiliates', 'value': total}]
    if pending:
        metrics.append({'label': 'Pending Affiliates', 'value': pending})
    return metrics


def get_schema():
    return AFFILIATES_SCHEMA
