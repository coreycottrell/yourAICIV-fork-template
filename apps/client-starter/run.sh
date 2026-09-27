#!/usr/bin/env bash
# Production start for THIS client instance (no systemd available):
#   nohup ./run.sh >/dev/null 2>&1 &        # start
#   kill "$(cat logs/gunicorn.pid)"          # stop
# Serves with gunicorn on 127.0.0.1:<CLIENT_PORT> only -- publish it through
# the reverse proxy / tunnel, never by binding a public interface.
# Logs go to logs/app.log (mode 0600); there is no access log, because URLs
# can carry one-time tokens. Secrets are read from .env by app/config.py.
# app/gunicorn.conf.py starts the workflow runner in each worker, so
# automation emails go out as long as this process is up (no cron needed).
set -euo pipefail
umask 077
INSTANCE_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="${CLIENT_VENV:-$(cd "$INSTANCE_DIR/.." && pwd)/.venv}"
PORT="$(sed -n "s/^CLIENT_PORT='\{0,1\}\([0-9]*\)'\{0,1\}$/\1/p" "$INSTANCE_DIR/.env" | head -1)"
if ! [[ "$PORT" =~ ^[0-9]{4,5}$ ]] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
    echo "run.sh: CLIENT_PORT missing or invalid in $INSTANCE_DIR/.env" >&2
    exit 1
fi
if [ ! -x "$VENV/bin/gunicorn" ]; then
    echo "run.sh: gunicorn not found in $VENV (install requirements.txt into the venv)" >&2
    exit 1
fi
mkdir -p "$INSTANCE_DIR/logs"
exec "$VENV/bin/gunicorn" \
    --config "$INSTANCE_DIR/app/gunicorn.conf.py" \
    --chdir "$INSTANCE_DIR/app" \
    --bind "127.0.0.1:$PORT" \
    --workers 2 --threads 4 \
    --pid "$INSTANCE_DIR/logs/gunicorn.pid" \
    --error-logfile "$INSTANCE_DIR/logs/app.log" \
    --capture-output \
    app:app
