"""
Client-Starter Scaffold -- Configuration Surface
=================================================
ALL per-client variation lives here. Edit this one file to brand and
configure a new client instance.  Everything else in the scaffold reads
from CLIENT_CONFIG at import time.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# ── Load the instance .env (written by clone_client.sh) ──────────────────
# yourAICIV hardening: .env is the ONLY home of this instance's secrets.
# Values already present in the real environment (systemd EnvironmentFile=,
# run.sh, docker env) always win (override=False).
INSTANCE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(INSTANCE_DIR / ".env", override=False)


# ── Fail closed on a missing / weak / published secret key ───────────────
# Admin auth is a signed client-side session cookie, so anyone who knows the
# key can mint an admin session. The scaffold is PUBLIC; any key that ever
# appeared in it (or any obvious placeholder) is treated as compromised.
_KNOWN_PLACEHOLDER_KEYS = {
    "dev-secret-key-change-in-prod",   # shipped in the upstream scaffold
    "change-me", "changeme", "change_me", "secret", "secret-key", "dev",
    "development", "test", "replace-me", "replace_me", "your-secret-key",
    "your_secret_key", "<generated>", "xxx",
}
_MIN_SECRET_KEY_BYTES = 32


def _require_secret_key():
    key = os.environ.get("CLIENT_SECRET_KEY", "")
    if not key:
        sys.exit("[CONFIG] FATAL: CLIENT_SECRET_KEY is not set. It must live in "
                 f"{INSTANCE_DIR / '.env'} (clone_client.sh generates one). "
                 "Refusing to start.")
    low = key.strip().lower()
    if low in _KNOWN_PLACEHOLDER_KEYS or ("change" in low and "prod" in low):
        sys.exit("[CONFIG] FATAL: CLIENT_SECRET_KEY is a known placeholder. "
                 "Generate one: python3 -c 'import secrets; print(secrets.token_hex(32))'")
    if len(key.encode()) < _MIN_SECRET_KEY_BYTES:
        sys.exit(f"[CONFIG] FATAL: CLIENT_SECRET_KEY must be at least "
                 f"{_MIN_SECRET_KEY_BYTES} bytes. Refusing to start.")
    if len(set(key)) < 8:
        sys.exit("[CONFIG] FATAL: CLIENT_SECRET_KEY has too little variety to be random.")
    return key


_SECRET_KEY = _require_secret_key()


# ── Reseller partner (who else hears about this client's business) ───────
# The AiCIV's partner profile (<civ>/config/partner.json, "notify_emails") is
# the source; PARTNER_NOTIFY_EMAILS (env / .env, comma separated) wins when
# set. Every owner alert (lead / order / booking / affiliate application) is
# also emailed to these addresses. Empty = the partner is not notified.
def _partner_profile():
    import json as _json
    import re as _re
    rx = _re.compile(r"^[^@\s,;<>]+@[^@\s,;<>]+\.[^@\s,;<>]+$")
    brand, emails = "yourAICIV", []
    civ = os.environ.get("CIV_ROOT", "").strip()
    civ_root = Path(civ) if civ and "${" not in civ else INSTANCE_DIR.parent.parent
    try:
        raw = _json.loads((civ_root / "config" / "partner.json").read_text())
        if isinstance(raw, dict):
            brand = str(raw.get("brand") or brand).strip() or brand
            emails = [str(e).strip() for e in (raw.get("notify_emails") or [])]
    except (OSError, ValueError):
        brand = "AiCIV"
    env = os.environ.get("PARTNER_NOTIFY_EMAILS", "").strip()
    if env:
        emails = _re.split(r"[\s,;]+", env)
    out = []
    for e in emails:
        if e and rx.match(e) and e.lower() not in {o.lower() for o in out}:
            out.append(e)
    return brand, out


_PARTNER_BRAND, _PARTNER_EMAILS = _partner_profile()

CLIENT_CONFIG = {
    # ── Identity ──────────────────────────────────────────────────────────
    "business_name": "Acme Business",
    "domain": "example.com",
    "tagline": "Your tagline here",
    "admin_title": "Admin Panel",

    # ── Branding ──────────────────────────────────────────────────────────
    "logo_path": "images/brand/logo.png",           # relative to static/
    "favicon_path": "images/brand/favicon.png",      # relative to static/
    "colors": {
        "primary":      "#1e40af",     # nav, buttons, sidebar
        "primary_light": "#3b82f6",    # links, hover states
        "primary_mid":  "#6b7faa",     # muted text
        "secondary":    "#d97706",     # accents, badges
        "background":   "#f5f5f5",     # admin main bg
        "sidebar_bg":   "#1e293b",     # sidebar background
        "sidebar_text": "#e2e8f0",     # sidebar text
        "text":         "#1e293b",     # body text
        "text_muted":   "#64748b",     # secondary text
        "public_bg":    "#ffffff",     # public site bg
        "card_bg":      "#ffffff",     # card/table bg
        "border":       "#e2e8f0",     # borders
    },
    "font_family": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",

    # ── Auth ──────────────────────────────────────────────────────────────
    "admin_user": os.environ.get("CLIENT_ADMIN_USER", "admin"),
    # The admin password is NOT configured here. Its hash lives in the
    # instance database (settings.admin_pass_hash) and is set by the client
    # through a single-use setup link (python3 app/manage.py issue-setup-link)
    # or changed at /admin/password. No plaintext password exists anywhere.
    "secret_key": _SECRET_KEY,

    # Public base URL used to build absolute links (Stripe success/cancel
    # URLs, magic links, unsubscribe links). Empty = https://<domain>.
    "public_base_url": os.environ.get("CLIENT_PUBLIC_BASE_URL", ""),

    # ── Email ─────────────────────────────────────────────────────────────
    "email_provider": "resend",                      # resend | smtp | none
    "resend_api_key": os.environ.get("RESEND_API_KEY", ""),
    "email_from": os.environ.get("EMAIL_FROM", "noreply@example.com"),
    "notification_email": os.environ.get("NOTIFICATION_EMAIL", ""),

    # ── Notifications ─────────────────────────────────────────────────────
    # When both are set, the owner gets a plain-text Telegram alert on every
    # new lead (contact form), order, booking and affiliate application.
    # Fire-and-forget (CLIENT_TELEGRAM_TIMEOUT, default 5s): a Telegram
    # outage never slows or fails the visitor's request; results are logged.
    "telegram_bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
    "telegram_chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),

    # Reseller partner: gets an email copy of every owner alert above (see
    # _partner_profile). Sent through this app's email provider (Resend);
    # when email is not configured or the send fails, the alert is queued to
    # logs/partner-outbox.jsonl and the AiCIV sends it from its own inbox
    # (tools/partner_notify.py flush). Never slows or fails the request.
    "partner_notify_emails": _PARTNER_EMAILS,
    "partner_brand": _PARTNER_BRAND,

    # ── Payments (enable what client needs) ───────────────────────────────
    "payment_providers": [],    # ["clickbrick", "barterpay", "stripe"]

    # ── Modules (toggle on/off) ───────────────────────────────────────────
    "modules": {
        "crm":              True,      # Contacts, tags, activity log -- core
        "email_marketing":  False,     # Subscribers, campaigns, send engine
        "workflows":        True,      # Automation engine: app/workflows.json
                                       # (welcome sequence on new leads; the
                                       # runner sends due steps every minute)
        "ecommerce":        False,     # Products, orders, cart, checkout
        "blog":             False,     # Blog CRUD + public display
        "affiliates":       False,     # Affiliate / referral program
        "shipping":         False,     # Shippo integration
        "appointments":     False,     # Booking / scheduling
        "subscriptions":    False,     # Recurring billing
    },

    # ── CRM Tag Map ───────────────────────────────────────────────────────
    # Maps form_type -> (tag_name, tag_color) for auto-tagging on form submit
    "tag_map": {
        "contact":    ("Contact Form", "#3b82f6"),
        "order":      ("Customer",     "#10b981"),
        "subscriber": ("Newsletter",   "#8b5cf6"),
    },

    # ── Admin Sidebar ─────────────────────────────────────────────────────
    # Core nav items are auto-generated from enabled modules.
    # Add extra custom items here.
    "admin_nav_extra": [],

    # ── Cron / API Protection ─────────────────────────────────────────────
    "cron_key": os.environ.get("CLIENT_CRON_KEY", ""),

    # ── Public Site Configuration ─────────────────────────────────────────
    # Everything the public-facing site needs, driven from config.
    "site": {
        # SEO / meta tags
        "seo": {
            "title_suffix": "",               # e.g. " | Acme Business" (appended to page titles)
            "meta_description": "",            # default meta description
            "og_image": "",                    # path relative to static/ or full URL
            "og_type": "website",
            "robots": "index, follow",
        },

        # Hero section on home page
        "hero": {
            "heading": "Welcome",
            "subheading": "Your tagline here",
            "cta_text": "Get in Touch",
            "cta_url": "/contact",             # absolute path or url_for endpoint
            "background_image": "",            # path relative to static/ (empty = gradient)
        },

        # Configurable content sections on home page (rendered in order)
        # Each section has a "type" that selects a rendering template.
        # Supported types: text, features, cta
        "sections": [
            {
                "type": "text",
                "heading": "About Us",
                "content": "Tell your visitors about your business. This section is fully "
                           "configurable from config.py -- no template edits needed.",
            },
            {
                "type": "features",
                "heading": "What We Offer",
                "items": [
                    {"title": "Feature One", "description": "Describe what you offer."},
                    {"title": "Feature Two", "description": "Another key offering."},
                    {"title": "Feature Three", "description": "A third highlight."},
                ],
            },
            {
                "type": "cta",
                "heading": "Ready to get started?",
                "content": "Reach out today and let us help you.",
                "cta_text": "Contact Us",
                "cta_url": "/contact",
            },
        ],

        # Navigation links in the public navbar (auto-populated from modules if empty)
        # Each entry: {"label": "Store", "url": "/store"} or {"label": "Blog", "url": "/blog"}
        # If empty list, auto-generated from enabled modules + always-on pages.
        "nav_links": [],

        # Footer
        "footer": {
            "text": "",                        # override copyright line (empty = auto)
            "links": [],                       # extra footer links: [{"label": "...", "url": "..."}]
        },
    },

    # ── Payment Providers ─────────────────────────────────────────────────
    # OPERATOR: CHOOSE PAYMENT PROCESSOR
    # Default is Stripe (industry standard, recommended).
    # Alternatives available if a particular operator can't use Stripe.
    "payment": {
        "active_provider": "stripe",           # OPERATOR: set to chosen provider
        "providers": {
            # ── DEFAULT (recommended) ────────────────────────────────────
            "stripe": {
                "enabled": True,
                "label": "Credit / Debit Card (Stripe)",
                "description": "Pay securely with any major credit or debit card.",
                # OPERATOR: Set these env vars in .env
                "secret_key_env": "STRIPE_SECRET_KEY",
                "webhook_secret_env": "STRIPE_WEBHOOK_SECRET",
                "currency": "usd",
                # success/cancel URLs are built as ABSOLUTE URLs from
                # public_base_url (or https://<domain>) at checkout time:
                #   success -> <base>/order/<order_id>?token=<access token>
                #   (the order page moves the token into the session and
                #   redirects to the clean URL; it sends no-referrer)
                #   cancel  -> <base>/cart
                # Register the webhook endpoint <base>/api/payment/webhook in
                # the Stripe Dashboard (events: checkout.session.completed,
                # checkout.session.async_payment_succeeded,
                # checkout.session.expired) and put its signing secret in
                # STRIPE_WEBHOOK_SECRET.
            },
            "manual": {
                "enabled": True,
                "label": "Pay Later / Invoice",
                "description": "Your order will be placed. Payment details will be sent separately.",
            },
            # ── Alternative providers ────────────────────────────────────
            "ach_direct": {
                "enabled": False,
                "label": "ACH Bank Transfer",
                "description": "Pay directly from your bank account.",
                # OPERATOR: fill in when provider is chosen
                "api_key_env": "ACH_API_KEY",
                "vendor_id": "",
            },
            "barterpay": {
                "enabled": False,
                "label": "BarterPay",
                "description": "Pay with BarterPay balance.",
                "api_key_env": "BARTERPAY_API_KEY",
                "merchant_url": "",
            },
            "clickbrick": {
                "enabled": False,
                "label": "ClickBrick ACH",
                "description": "Secure ACH payment via ClickBrick.",
                "api_key_env": "CLICKBRICK_API_KEY",
                "vendor_id": "",
            },
            "crypto": {
                "enabled": False,
                "label": "Cryptocurrency",
                "description": "Pay with Bitcoin, Ethereum, or other crypto.",
                "wallet_address": "",
                "accepted_coins": ["BTC", "ETH"],
            },
        },
    },

    # ── Webhook Secrets ───────────────────────────────────────────────────
    "payment_webhook_secret": os.environ.get("PAYMENT_WEBHOOK_SECRET", ""),
    "resend_webhook_secret": os.environ.get("RESEND_WEBHOOK_SECRET", ""),
}


# ── Convenience accessors ────────────────────────────────────────────────
def get(key, default=None):
    """Get a config value by dot-path: get('colors.primary')."""
    keys = key.split(".")
    val = CLIENT_CONFIG
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, default)
        else:
            return default
    return val


# Keys that templates may see. Everything else (API keys, bot token, cron
# key, webhook secrets, secret_key) stays server-side.
PUBLIC_CONFIG_KEYS = (
    "business_name", "domain", "tagline", "admin_title", "logo_path",
    "favicon_path", "colors", "font_family", "modules", "site",
)


def public_config():
    """Whitelisted, template-safe subset of CLIENT_CONFIG."""
    return {k: CLIENT_CONFIG[k] for k in PUBLIC_CONFIG_KEYS if k in CLIENT_CONFIG}


def base_url():
    """Absolute public base URL, no trailing slash."""
    url = (CLIENT_CONFIG.get("public_base_url") or "").strip().rstrip("/")
    if url:
        return url
    return "https://" + CLIENT_CONFIG.get("domain", "example.com").strip().rstrip("/")


def modules_enabled():
    """Return a list of enabled module names."""
    return [m for m, enabled in CLIENT_CONFIG["modules"].items() if enabled]


def is_module_enabled(module_name):
    """Check if a specific module is enabled."""
    return CLIENT_CONFIG["modules"].get(module_name, False)
