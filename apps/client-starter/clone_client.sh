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
#   7. GOES LIVE through this AI's portal (tools/client_sites.py go-live):
#      starts the instance on 127.0.0.1:<port>, registers it, and checks it
#      through the portal. Public URL: <portal public URL>/site/<slug>/
#      Skip with CLIENT_GO_LIVE=0 (then run the go-live command it prints).
#
# Run it with the shared venv FIRST on PATH (python3 needs the app deps):
#   PATH="$CIV_ROOT/apps/.venv/bin:$PATH" ./clone_client.sh <slug> [port]
# Set PORTAL_PUBLIC_URL (env or ~/.env) so links carry the public address.
#
# HARD RULES:
#   - Touches nothing outside this AI's own files: no DNS, no fleet proxy,
#     no tunnel config. The portal serves /site/<slug>/ from the registry.
#   - The client's OWN domain is a human step (DNS + fleet proxy); it is
#     PRINTED at the end, never applied.
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
SITES_TOOL="$(dirname "$APPS_DIR")/tools/client_sites.py"

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

echo "[1/6] Copying scaffold template..."
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

echo "[2/6] Generating client-specific config..."

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

echo "[3/6] Writing secrets to .env..."

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

echo "[4/6] Creating fresh database..."
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

# Public address of this site through the portal (known if PORTAL_PUBLIC_URL
# is set). Written before the setup link so every absolute link (setup link,
# Stripe return URLs, unsubscribe, magic links) carries it.
SITE_URL=""
if [ -f "$SITES_TOOL" ]; then
    SITE_URL="$(python3 "$SITES_TOOL" url "$CLIENT_SLUG" 2>/dev/null || true)"
fi
if [ -n "$SITE_URL" ]; then
    printf "CLIENT_PUBLIC_BASE_URL='%s'\n" "${SITE_URL%/}" >> "$CLIENT_DIR/.env"
    echo "   Public URL: $SITE_URL"
fi

# ── Step 5: One-time admin setup link + start files ───────────────────

echo "[5/6] Issuing one-time admin setup link and start files..."
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
# ── Step 6: Go live through the portal ────────────────────────────────

GO_LIVE_CMD="python3 $SITES_TOOL go-live $CLIENT_SLUG --port $PORT --dir $CLIENT_DIR"
LIVE_RC=skipped
if [ "${CLIENT_GO_LIVE:-1}" != "0" ] && [ -f "$SITES_TOOL" ]; then
    echo "[6/6] Going live through the portal..."
    set +e
    CLIENT_VENV="$VENV_DIR" python3 "$SITES_TOOL" go-live "$CLIENT_SLUG" --port "$PORT" --dir "$CLIENT_DIR"
    LIVE_RC=$?
    set -e
    echo ""
fi

echo "================================================================"
echo "  GO-LIVE"
echo "================================================================"
echo ""
case "$LIVE_RC" in
  0) echo "  LIVE. Public URL: ${SITE_URL:-<portal public address>/site/$CLIENT_SLUG/}"
     echo "  Admin: ${SITE_URL:-<portal public address>/site/$CLIENT_SLUG/}admin/login" ;;
  3) echo "  Running on 127.0.0.1:$PORT and registered, but the portal did not"
     echo "  serve it (is the portal running and up to date?). Re-check:"
     echo "    python3 $SITES_TOOL verify $CLIENT_SLUG" ;;
  skipped) echo "  Not started (CLIENT_GO_LIVE=0 or tools/client_sites.py missing)."
     echo "  To go live:  $GO_LIVE_CMD" ;;
  *) echo "  Start FAILED (see $CLIENT_DIR/logs/app.log). Retry:"
     echo "    $GO_LIVE_CMD" ;;
esac
echo ""
echo "  It stays up: tools/watchdog.sh runs 'client_sites.py ensure' every"
echo "  minute and restarts any registered site that is down."
echo "  Status: python3 $SITES_TOOL list"
echo "  (Host with systemd instead? See the header of"
echo "   $CLIENT_DIR/deploy/client-$CLIENT_SLUG.service; still register it.)"
echo ""
echo "  NEXT (optional): fill $CLIENT_DIR/.env with Stripe / email /"
echo "  Telegram keys (edit in place; never echo the values), then:"
echo "    python3 $SITES_TOOL stop $CLIENT_SLUG && python3 $SITES_TOOL start $CLIENT_SLUG"
echo ""
echo "  Automations run inside the app (a runner thread per worker; no cron):"
echo "  edit $CLIENT_DIR/app/workflows.json, then in $CLIENT_DIR/app run"
echo "    python3 manage.py sync-workflows   (and: python3 manage.py workflows)."
echo "  Lead/order alerts need TELEGRAM_*; emails need RESEND_API_KEY + EMAIL_FROM."
echo ""
echo "================================================================"
echo "  CLIENT'S OWN DOMAIN (human step; nothing here applies it)"
echo "================================================================"
echo ""
echo "  1. DNS (client's registrar): point the domain at the SAME address"
echo "     as this AI's portal (CNAME to the portal host name, or its A record)."
echo "  2. Fleet TLS proxy (operator): add a site block for the domain that"
echo "     forwards to this AI's portal, exactly like the portal's own block."
echo "  3. Here:  python3 $SITES_TOOL domain $CLIENT_SLUG add <domain>"
echo "     then set CLIENT_PUBLIC_BASE_URL='https://<domain>' in"
echo "     $CLIENT_DIR/.env and restart the site (stop + start)."
echo "================================================================"
