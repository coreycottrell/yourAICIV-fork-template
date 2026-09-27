-- Client-Starter Scaffold: Core Schema
-- ======================================
-- Generic tables only. domain-specific tables (e.g. domain-specific,
-- member_applications, ceremony_*, dream_catalyst_*) are NOT included.
-- Module-specific tables (ecommerce, blog, affiliates, etc.) will be
-- added in Phase 2 as module schema extensions.

-- ── CRM Core ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    first_name TEXT DEFAULT '',
    last_name TEXT DEFAULT '',
    email TEXT DEFAULT '',
    phone TEXT DEFAULT '',
    address TEXT DEFAULT '',
    city TEXT DEFAULT '',
    state TEXT DEFAULT '',
    postal_code TEXT DEFAULT '',
    country TEXT DEFAULT '',
    source TEXT DEFAULT '',
    date_of_birth TEXT DEFAULT '',
    company_name TEXT DEFAULT '',
    website TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    custom_fields TEXT DEFAULT '{}',
    unsubscribed INTEGER DEFAULT 0,
    unsubscribed_at TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#6b7280',
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS contact_tags (
    contact_id TEXT NOT NULL,
    tag_id TEXT NOT NULL,
    added_at TEXT,
    PRIMARY KEY (contact_id, tag_id),
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id TEXT,
    type TEXT DEFAULT 'note',
    details TEXT DEFAULT '',
    created_at TEXT,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
);

-- ── Contact Messages ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS contact_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    message TEXT NOT NULL,
    submitted_at TEXT,
    read INTEGER DEFAULT 0
);

-- ── Settings (key-value store) ──────────────────────────────────────────

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- ── Form Submissions (generic form archive) ─────────────────────────────

CREATE TABLE IF NOT EXISTS form_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id TEXT,
    contact_email TEXT,
    form_type TEXT NOT NULL,
    form_data TEXT NOT NULL,
    submission_date TEXT,
    source_url TEXT,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Email Templates ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS email_templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    subject TEXT DEFAULT '',
    body_html TEXT DEFAULT '',
    body_text TEXT DEFAULT '',
    category TEXT DEFAULT 'general',
    merge_fields TEXT DEFAULT '[]',
    created_at TEXT,
    updated_at TEXT
);

-- ── Email Log ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS email_log (
    id TEXT PRIMARY KEY,
    contact_id TEXT,
    template_id TEXT,
    workflow_id TEXT,
    to_email TEXT,
    subject TEXT,
    status TEXT DEFAULT 'sent',
    sent_at TEXT,
    opened_at TEXT,
    FOREIGN KEY (contact_id) REFERENCES contacts(id),
    FOREIGN KEY (template_id) REFERENCES email_templates(id)
);

-- ── Security bookkeeping (yourAICIV hardening) ─────────────────────────
-- Admin password hash, setup-token hash and session_version live in
-- `settings`. These tables back the shared rate limiter, per-account login
-- backoff, and webhook replay protection (event-id deduplication).

CREATE TABLE IF NOT EXISTS rate_limits (
    key TEXT PRIMARY KEY,
    count INTEGER NOT NULL DEFAULT 0,
    reset_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS login_failures (
    account TEXT PRIMARY KEY,
    failures INTEGER NOT NULL DEFAULT 0,
    locked_until REAL,
    updated_at REAL
);

CREATE TABLE IF NOT EXISTS processed_events (
    source TEXT NOT NULL,
    event_id TEXT NOT NULL,
    received_at TEXT,
    PRIMARY KEY (source, event_id)
);

-- ── Indexes ─────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(last_name, first_name);
CREATE INDEX IF NOT EXISTS idx_contact_tags_contact ON contact_tags(contact_id);
CREATE INDEX IF NOT EXISTS idx_contact_tags_tag ON contact_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_activity_contact ON activity_log(contact_id);
CREATE INDEX IF NOT EXISTS idx_email_log_contact ON email_log(contact_id);
CREATE INDEX IF NOT EXISTS idx_form_sub_contact ON form_submissions(contact_id);
CREATE INDEX IF NOT EXISTS idx_form_sub_email ON form_submissions(contact_email);
CREATE INDEX IF NOT EXISTS idx_form_sub_type ON form_submissions(form_type);
CREATE INDEX IF NOT EXISTS idx_rate_limits_reset ON rate_limits(reset_at);
