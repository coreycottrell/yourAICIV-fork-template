"""
Shipping Module (STUB)
=======================
Shippo integration for label generation, tracking, and shipping admin.
Toggleable via config: modules.shipping

STATUS: STUB -- Phase 2 incomplete. Schema + admin list view defined.
Full Shippo API integration, label generation, and tracking need
implementation in a future phase. The e-commerce checkout flow
should call into this module for shipping rate calculation.
"""

import json
import uuid
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, abort, jsonify)

shipping_bp = Blueprint('shipping', __name__,
                        template_folder='../templates')


def _is_admin():
    """Admin check shared with app.py (honours session revocation)."""
    from flask import current_app
    return current_app.config['_helpers']['is_admin']()

# ── Schema extension ────────────────────────────────────────────────────

SHIPPING_SCHEMA = """
CREATE TABLE IF NOT EXISTS shipments (
    id TEXT PRIMARY KEY,
    order_id TEXT,
    carrier TEXT DEFAULT '',
    service TEXT DEFAULT '',
    tracking_number TEXT,
    label_url TEXT,
    rate_amount REAL,
    status TEXT DEFAULT 'pending',
    ship_from TEXT DEFAULT '{}',
    ship_to TEXT DEFAULT '{}',
    parcel TEXT DEFAULT '{}',
    created_at TEXT,
    shipped_at TEXT
);

CREATE TABLE IF NOT EXISTS shipping_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    carrier TEXT NOT NULL,
    config_data TEXT DEFAULT '{}',
    active INTEGER DEFAULT 1,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_shipments_order ON shipments(order_id);
CREATE INDEX IF NOT EXISTS idx_shipments_status ON shipments(status);
"""


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


# ── Admin: Shipments ───────────────────────────────────────────────────

@shipping_bp.route('/admin/shipping')
@_admin_required
def admin_shipping():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    shipments = db.execute(
        "SELECT * FROM shipments ORDER BY created_at DESC"
    ).fetchall()
    return render_template('admin/shipping.html', shipments=shipments)


# ── Module registration ─────────────────────────────────────────────────

def get_nav_items():
    return [
        {'label': 'Shipping', 'endpoint': 'shipping.admin_shipping',
         'match': 'shipping.admin_shipping'},
    ]


def get_metrics(db):
    pending = db.execute(
        "SELECT COUNT(*) as c FROM shipments WHERE status = 'pending'"
    ).fetchone()['c']
    return [{'label': 'Pending Shipments', 'value': pending}]


def get_schema():
    return SHIPPING_SCHEMA
