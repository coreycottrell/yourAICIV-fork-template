#!/usr/bin/env bash
# ============================================================
# clone_client.sh -- Stand up a NEW client instance from the
#                    client-starter scaffold.
#
# Usage:
#   ./clone_client.sh <client_slug> [port]
#
# Example:
#   ./clone_client.sh janes-wellness 5101
#
# What it does:
#   1. Copies the scaffold template to a new client dir
#   2. Creates a fresh empty SQLite DB
#   3. Brands config.py with client-specific (non-secret) values
#   4. Writes secrets ONLY to <instance>/.env (mode 0600, umask 077)
#   5. Issues a single-use admin set-password link to <instance>/.setup-link
#      (0600). No admin password is generated, stored, printed or sent.
#   6. Assigns its own port (default: auto-assign starting at 5100)
#   7. Renders run.sh / systemd start options and PRINTS manual deploy steps
#      (does NOT modify live infra)
#
# Run it with the shared venv FIRST on PATH (python3 needs the app deps):
#   PATH="$CIV_ROOT/apps/.venv/bin:$PATH" ./clone_client.sh <slug> [port]
#
# HARD RULES:
#   - Does NOT modify reverse_proxy.py
#   - Does NOT modify start_all.sh
#   - Does NOT modify cloudflared config
#   - Does NOT modify DNS
#   - PRINTS the exact manual steps for a human to apply
# ============================================================
set -euo pipefail
umask 077            # everything this script creates is private to its owner

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APPS_DIR="$(dirname "$SCRIPT_DIR")"

# ── Parse arguments ─────────────────────────────────────────────────────

if [ $# -lt 1 ]; then
    echo "Usage: $0 <client_slug> [port]"
    echo ""
    echo "  client_slug  Lowercase hyphenated name (e.g. janes-wellness)"
    echo "  port         Optional port number (default: auto-assign from 5100)"
    echo ""
    echo "Example:"
    echo "  $0 janes-wellness 5101"
    exit 1
fi

CLIENT_SLUG="$1"

# Validate slug: lowercase letters, numbers, hyphens only
if ! echo "$CLIENT_SLUG" | grep -qE '^[a-z0-9][a-z0-9-]*[a-z0-9]$'; then
    echo "ERROR: client_slug must be lowercase letters, numbers, and hyphens."
    echo "       Must start and end with a letter or number."
    echo "       Got: '$CLIENT_SLUG'"
    exit 1
fi

CLIENT_DIR="$APPS_DIR/$CLIENT_SLUG"

# Check if directory already exists
if [ -d "$CLIENT_DIR" ]; then
    echo "ERROR: Directory already exists: $CLIENT_DIR"
    echo "       Choose a different slug or remove the existing directory first."
    exit 1
fi

# ── Determine port ──────────────────────────────────────────────────────

if [ $# -ge 2 ]; then
    PORT="$2"
    if ! [[ "$PORT" =~ ^[0-9]{4,5}$ ]] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
        echo "ERROR: port must be a number between 1024 and 65535. Got: '$PORT'"
        exit 1
    fi
else
    # Auto-assign: find highest port in use by client-starter clones
    # Start scanning from 5100
    PORT=5100
    while [ -d "$APPS_DIR" ] && ss -tlnp 2>/dev/null | grep -q ":${PORT} " 2>/dev/null; do
        PORT=$((PORT + 1))
        if [ "$PORT" -gt 5199 ]; then
            echo "ERROR: Could not find a free port in range 5100-5199."
            echo "       Specify a port manually: $0 $CLIENT_SLUG <port>"
            exit 1
        fi
    done
    # Also check existing client-starter dirs for port claims
    for dir in "$APPS_DIR"/*/; do
        if [ -f "${dir}.env" ]; then
            claimed=$(sed -n "s/^CLIENT_PORT='\{0,1\}\([0-9]*\)'\{0,1\}$/\1/p" "${dir}.env" 2>/dev/null | head -1 || true)
            if [ "$claimed" = "$PORT" ]; then
                PORT=$((PORT + 1))
            fi
        fi
    done
fi

# Deps check: manage.py (setup link) imports the app.
if ! python3 -c "import flask, dotenv, flask_wtf, nh3" 2>/dev/null; then
    echo "ERROR: python3 on PATH lacks the scaffold dependencies."
    echo "       Run with the venv first on PATH:"
    echo "       PATH=\"\$CIV_ROOT/apps/.venv/bin:\$PATH\" $0 $CLIENT_SLUG $PORT"
    exit 1
fi

VENV_DIR="${CLIENT_VENV:-$APPS_DIR/.venv}"

# Check port not already bound
if ss -tlnp 2>/dev/null | grep -q ":${PORT} " 2>/dev/null; then
    echo "WARNING: Port $PORT appears to be in use. The app may fail to start."
    echo "         Check with: ss -tlnp | grep :$PORT"
fi

echo "================================================================"
echo "  Creating new client: $CLIENT_SLUG"
echo "  Directory:           $CLIENT_DIR"
echo "  Port:                $PORT"
echo "================================================================"
echo ""

# ── Step 1: Copy scaffold ──────────────────────────────────────────────

echo "[1/5] Copying scaffold template..."
cp -r "$SCRIPT_DIR" "$CLIENT_DIR"

# Remove pycache, any existing db/secrets/logs that leaked into the scaffold
find "$CLIENT_DIR" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
rm -f "$CLIENT_DIR"/app/client.db* "$CLIENT_DIR/.env" "$CLIENT_DIR/.setup-link" 2>/dev/null || true
rm -rf "$CLIENT_DIR/logs" 2>/dev/null || true

# Remove template-only tooling from the copy (client doesn't need it)
rm -f "$CLIENT_DIR/clone_client.sh" "$CLIENT_DIR/preflight.sh" \
      "$CLIENT_DIR/deploy/client-instance.service.in" 2>/dev/null || true

# The instance MUST carry the .gitignore (secrets + PII never enter git)
if [ ! -f "$CLIENT_DIR/.gitignore" ]; then
    echo "ERROR: scaffold .gitignore missing; refusing to create an instance without it."
    rm -rf "$CLIENT_DIR"
    exit 1
fi

# Remove backups directory from the copy
rm -rf "$CLIENT_DIR/backups-qa-hardening-20260925" 2>/dev/null || true

echo "   Done. Files copied to $CLIENT_DIR"

# ── Step 2: Generate config from template ──────────────────────────────

echo "[2/5] Generating client-specific config..."

# Generate a random secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Generate a random cron key
CRON_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# Generate a random payment webhook secret
PAYMENT_WEBHOOK_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

# Convert slug to display name (janes-wellness -> Janes Wellness)
DISPLAY_NAME=$(echo "$CLIENT_SLUG" | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')

# Brand config.py (NON-secret values only; the secret key lives in .env)
sed -i \
    -e "s|\"business_name\": \"Acme Business\"|\"business_name\": \"$DISPLAY_NAME\"|g" \
    -e "s|\"domain\": \"example.com\"|\"domain\": \"$CLIENT_SLUG.example.com\"|g" \
    -e "s|\"admin_title\": \"Admin Panel\"|\"admin_title\": \"$DISPLAY_NAME Admin\"|g" \
    -e "s|\"heading\": \"Welcome\"|\"heading\": \"Welcome to $DISPLAY_NAME\"|g" \
    "$CLIENT_DIR/app/config.py"

# Patch app.py default port
sed -i \
    -e "s|port = int(sys.argv\[1\]) if len(sys.argv) > 1 else 5099|port = int(sys.argv[1]) if len(sys.argv) > 1 else $PORT|g" \
    "$CLIENT_DIR/app/app.py"

# ── Step 3: Create .env with secrets ───────────────────────────────────

echo "[3/5] Writing secrets to .env..."

# Values are single-quoted so the file is safe for python-dotenv, systemd
# EnvironmentFile= and `set -a; . .env` alike. No admin password is written:
# the client sets it through the one-time link (step 5).
( umask 077; cat > "$CLIENT_DIR/.env" << ENVEOF
# Client instance: $CLIENT_SLUG
# Generated by clone_client.sh -- SECRET. Mode 0600. Never commit, copy into
# memories, paste into chat, or print this file.

CLIENT_SECRET_KEY='$SECRET_KEY'
CLIENT_ADMIN_USER='admin'
CLIENT_CRON_KEY='$CRON_KEY'
CLIENT_PORT='$PORT'
PAYMENT_WEBHOOK_SECRET='$PAYMENT_WEBHOOK_SECRET'

# Public URL (absolute links: Stripe return URLs, magic links, unsubscribe).
# Empty = https://<domain from config.py>.
# CLIENT_PUBLIC_BASE_URL='https://$CLIENT_SLUG.example.com'

# Stripe (default provider; the client's OWN account):
# STRIPE_SECRET_KEY=''
# STRIPE_WEBHOOK_SECRET=''

# Email (fill in when ready):
# RESEND_API_KEY=''
# EMAIL_FROM='noreply@$CLIENT_SLUG.example.com'
# RESEND_WEBHOOK_SECRET=''

# Telegram (fill in when ready):
# TELEGRAM_BOT_TOKEN=''
# TELEGRAM_CHAT_ID=''
ENVEOF
)
chmod 600 "$CLIENT_DIR/.env"

echo "   Done. Secrets written to $CLIENT_DIR/.env (mode 0600)"

echo "   Done. Config set for '$DISPLAY_NAME' on port $PORT"

# ── Step 4: Initialize fresh database ─────────────────────────────────

echo "[4/5] Creating fresh database..."
cd "$CLIENT_DIR/app"
python3 -c "
import sqlite3, os
db_path = os.path.join(os.path.dirname(os.path.abspath('app.py')), 'client.db')
db = sqlite3.connect(db_path)
db.execute('PRAGMA journal_mode=WAL')
with open('db/schema.sql') as f:
    db.executescript(f.read())
db.commit()
db.close()
print(f'   Database created: {db_path}')
"
cd "$APPS_DIR"

echo "   Done."

# ── Step 5: One-time admin setup link + start files ───────────────────

echo "[5/5] Issuing one-time admin setup link and start files..."
( cd "$CLIENT_DIR/app" && python3 manage.py issue-setup-link --port "$PORT" )

RUN_USER="client-$CLIENT_SLUG"
sed -e "s|@SLUG@|$CLIENT_SLUG|g" \
    -e "s|@RUN_USER@|$RUN_USER|g" \
    -e "s|@INSTANCE_DIR@|$CLIENT_DIR|g" \
    -e "s|@VENV@|$VENV_DIR|g" \
    -e "s|@PORT@|$PORT|g" \
    "$SCRIPT_DIR/deploy/client-instance.service.in" > "$CLIENT_DIR/deploy/client-$CLIENT_SLUG.service"
chmod 755 "$CLIENT_DIR/run.sh"

echo "   Complete!"
echo ""
echo "================================================================"
echo "  CLIENT INSTANCE READY: $CLIENT_SLUG"
echo "================================================================"
echo ""
echo "  Directory: $CLIENT_DIR"
echo "  Port:      $PORT (127.0.0.1 only)"
echo "  Admin:     username=admin; the client sets the password via the"
echo "             ONE-TIME link in $CLIENT_DIR/.setup-link"
echo "             (0600; single use; expires in 24h). Send it privately,"
echo "             then delete the file. Lost password or expired link:"
echo "             cd $CLIENT_DIR/app && python3 manage.py issue-setup-link --port $PORT"
echo ""
echo "  Secrets are stored in: $CLIENT_DIR/.env (mode 0600)"
echo "  (Never commit, print, or copy .env; the instance .gitignore excludes it)"
echo ""
echo "================================================================"
echo "  MANUAL DEPLOY STEPS (do NOT skip these)"
echo "================================================================"
echo ""
echo "  1. REVIEW $CLIENT_DIR/.env and fill in email / Stripe / Telegram keys"
echo "     as needed (edit in place; never echo the values)."
echo ""
echo "  2. START (production = gunicorn on 127.0.0.1, never the dev server):"
echo "     a) systemd available (preferred; isolates the instance as its own"
echo "        unprivileged user $RUN_USER):"
echo "          see the header of $CLIENT_DIR/deploy/client-$CLIENT_SLUG.service"
echo "     b) no systemd (e.g. inside a container):"
echo "          (cd $CLIENT_DIR && nohup ./run.sh >/dev/null 2>&1 &)"
echo "          logs: $CLIENT_DIR/logs/app.log (0600); stop: kill \$(cat $CLIENT_DIR/logs/gunicorn.pid)"
echo "        Add the same line to start_all.sh so it restarts on reboot."
echo ""
echo "  3. ADD TO reverse_proxy.py (so it's reachable via domain):"
echo "     Add route entry for '/$CLIENT_SLUG' -> localhost:$PORT"
echo "     Example in ROUTES dict:"
echo "       '$CLIENT_SLUG': {'port': $PORT, 'strip_prefix': True},"
echo ""
echo "  4. OPTIONAL: Add to cloudflared config (if using Cloudflare Tunnel):"
echo "     Add ingress rule for $CLIENT_SLUG subdomain or path."
echo ""
echo "  5. OPTIONAL: Set up DNS for custom domain:"
echo "     CNAME record pointing to your tunnel or server IP."
echo ""
echo "================================================================"
echo "  DO NOT modify these files automatically -- a human should"
echo "  review and apply each step deliberately."
echo "================================================================"
