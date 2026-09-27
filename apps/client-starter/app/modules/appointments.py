"""
Appointments Module (STUB)
===========================
Booking/scheduling system. Currently a marked stub with schema,
admin list view, and public booking form placeholder.
Toggleable via config: modules.appointments

STATUS: STUB -- Phase 2 incomplete. Admin list + new booking work.
Full calendar integration, availability management, and reminders
need implementation in a future phase.
"""

import json
import uuid
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, abort)

appointments_bp = Blueprint('appointments', __name__,
                            template_folder='../templates')


def _is_admin():
    """Admin check shared with app.py (honours session revocation)."""
    from flask import current_app
    return current_app.config['_helpers']['is_admin']()

# ── Schema extension ────────────────────────────────────────────────────

APPOINTMENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    contact_name TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    contact_phone TEXT,
    appointment_type TEXT DEFAULT 'general',
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    duration_minutes INTEGER DEFAULT 60,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
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


# ── Public: Book appointment ────────────────────────────────────────────

@appointments_bp.route('/book', methods=['GET', 'POST'])
def book():
    if request.method == 'POST':
        from flask import current_app
        rate_fn = current_app.config.get('_rate_limited')
        if rate_fn and rate_fn(request.remote_addr, window=300, max_attempts=10):
            flash('Too many submissions. Please wait a moment.', 'error')
            return render_template('public/book.html'), 429
        helpers = _get_app_helpers()
        db = helpers['get_db']()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        date = request.form.get('date', '').strip()
        time = request.form.get('time', '').strip()
        appt_type = request.form.get('type', 'general').strip()
        notes = request.form.get('notes', '').strip()

        if not name or not email or not date or not time:
            flash('Name, email, date, and time are required.', 'error')
            return render_template('public/book.html')

        appt_id = str(uuid.uuid4())[:12]
        db.execute(
            """INSERT INTO appointments
               (id, contact_name, contact_email, contact_phone,
                appointment_type, date, time, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (appt_id, name, email, phone, appt_type,
             date, time, notes, now_iso(), now_iso()))
        db.commit()

        # CRM sync
        sync = helpers.get('sync_to_crm')
        if sync:
            sync({'first_name': name.split()[0] if name else '',
                  'email': email, 'phone': phone}, 'appointment')

        flash('Appointment request submitted! We will confirm shortly.', 'success')
        return redirect(url_for('appointments.book'))

    return render_template('public/book.html')


# ── Admin: Appointments ────────────────────────────────────────────────

@appointments_bp.route('/admin/appointments')
@_admin_required
def admin_appointments():
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    appointments = db.execute(
        "SELECT * FROM appointments ORDER BY date DESC, time DESC"
    ).fetchall()
    return render_template('admin/appointments.html',
                           appointments=appointments)


@appointments_bp.route('/admin/appointments/<appt_id>/status', methods=['POST'])
@_admin_required
def admin_appointment_status(appt_id):
    helpers = _get_app_helpers()
    db = helpers['get_db']()
    status = request.form.get('status', 'pending')
    db.execute(
        "UPDATE appointments SET status = ?, updated_at = ? WHERE id = ?",
        (status, now_iso(), appt_id))
    db.commit()
    flash(f'Appointment status updated to {status}.', 'success')
    return redirect(url_for('appointments.admin_appointments'))


# ── Module registration ─────────────────────────────────────────────────

def get_nav_items():
    return [
        {'label': 'Appointments', 'endpoint': 'appointments.admin_appointments',
         'match': 'appointments.admin_appointment'},
    ]


def get_metrics(db):
    upcoming = db.execute(
        "SELECT COUNT(*) as c FROM appointments "
        "WHERE status IN ('pending', 'confirmed') AND date >= date('now')"
    ).fetchone()['c']
    return [{'label': 'Upcoming Appts', 'value': upcoming}]


def get_schema():
    return APPOINTMENTS_SCHEMA
