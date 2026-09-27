#!/usr/bin/env bash
# template-watchdog.sh — CIV-universal process watchdog
# Monitors: Portal, Telegram bot, Tmux session, Claude Code
# Runs every 60s. Self-contained for born AiCIV containers.
# Does NOT monitor relay.py (has its own watchdog in entrypoint.sh).

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────
SESSION_NAME="$(cat /home/aiciv/civ/.current_session 2>/dev/null || echo "${CIV_NAME:-aiciv}-primary")"
CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/aiciv/civ}"
PORTAL_DIR="/home/aiciv/purebrain_portal"
CHECK_INTERVAL=60
LOG_MAX_LINES=5000
LOG_KEEP_LINES=1000
MAX_RESTARTS=3
RESTART_WINDOW=600
LOG="/home/aiciv/civ/logs/watchdog.log"
PIDFILE="/tmp/watchdog.pid"
RESTART_TRACK_DIR="/tmp"

# ── Helpers ──────────────────────────────────────────────────────────
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG"
}

rotate_log() {
    local lines
    lines=$(wc -l < "$LOG" 2>/dev/null || echo 0)
    if (( lines > LOG_MAX_LINES )); then
        tail -n "$LOG_KEEP_LINES" "$LOG" > "${LOG}.tmp"
        mv "${LOG}.tmp" "$LOG"
        log "Log rotated: ${lines} -> ${LOG_KEEP_LINES} lines"
    fi
}

check_already_running() {
    if [[ -f "$PIDFILE" ]]; then
        local old_pid
        old_pid=$(cat "$PIDFILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            echo "Watchdog already running (PID $old_pid). Exiting."
            exit 0
        fi
        rm -f "$PIDFILE"
    fi
    echo $$ > "$PIDFILE"
    trap 'rm -f "$PIDFILE"' EXIT
}

# track_restart <process_name>
# Returns 0 if restart allowed, 1 if crash-looping
track_restart() {
    local name="$1"
    local track_file="${RESTART_TRACK_DIR}/watchdog-restarts-${name}"
    local now
    now=$(date +%s)

    # Append timestamp
    echo "$now" >> "$track_file"

    # Prune entries older than RESTART_WINDOW
    local cutoff=$(( now - RESTART_WINDOW ))
    local recent=0
    local tmp_file="${track_file}.tmp"
    > "$tmp_file"
    while IFS= read -r ts; do
        if (( ts >= cutoff )); then
            echo "$ts" >> "$tmp_file"
            (( recent++ )) || true
        fi
    done < "$track_file"
    mv "$tmp_file" "$track_file"

    if (( recent >= MAX_RESTARTS )); then
        log "CRASH-LOOP: ${name} restarted ${recent} times in ${RESTART_WINDOW}s — backing off"
        return 1
    fi
    return 0
}

# ── Process Checks ───────────────────────────────────────────────────
PORTAL_HEALTHY=false
TELEGRAM_ALIVE=false
CLAUDE_ALIVE=false
TMUX_ALIVE=false

portal_check() {
    # HTTP health check first
    if curl -sf --max-time 2 http://localhost:8097/health >/dev/null 2>&1; then
        PORTAL_HEALTHY=true
        return
    fi

    # Process alive but not responding? Kill hung process
    local pid
    pid=$(pgrep -f "node.*server" 2>/dev/null | head -1) || true
    if [[ -n "$pid" ]]; then
        log "Portal process alive (PID $pid) but health check failed — killing"
        kill "$pid" 2>/dev/null || true
        sleep 1
    fi

    PORTAL_HEALTHY=false

    if ! track_restart "portal"; then
        return
    fi

    log "Restarting portal from ${PORTAL_DIR}"
    if [[ -d "$PORTAL_DIR" ]]; then
        cd "$PORTAL_DIR"
        nohup node server.js >> /home/aiciv/civ/logs/portal.log 2>&1 &
        cd - >/dev/null
        sleep 2
        if curl -sf --max-time 2 http://localhost:8097/health >/dev/null 2>&1; then
            PORTAL_HEALTHY=true
            log "Portal restarted successfully"
        else
            log "Portal restart — health check still failing"
        fi
    else
        log "Portal directory not found: ${PORTAL_DIR}"
    fi
}

telegram_check() {
    if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
        TELEGRAM_ALIVE=true  # Not applicable — mark OK
        return
    fi

    if pgrep -f "telegram_unified.py" >/dev/null 2>&1; then
        TELEGRAM_ALIVE=true
        return
    fi

    TELEGRAM_ALIVE=false

    if ! track_restart "telegram"; then
        return
    fi

    local tg_script="${CLAUDE_PROJECT_DIR}/tools/telegram_unified.py"
    if [[ -f "$tg_script" ]]; then
        log "Restarting Telegram bot"
        nohup python3 "$tg_script" >> /home/aiciv/civ/logs/telegram.log 2>&1 &
        sleep 2
        if pgrep -f "telegram_unified.py" >/dev/null 2>&1; then
            TELEGRAM_ALIVE=true
            log "Telegram bot restarted successfully"
        else
            log "Telegram bot restart failed"
        fi
    else
        log "Telegram script not found: ${tg_script}"
    fi
}

tmux_check() {
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        TMUX_ALIVE=true
        return
    fi

    TMUX_ALIVE=false

    if ! track_restart "tmux"; then
        return
    fi

    log "Recreating tmux session: ${SESSION_NAME}"
    tmux new-session -d -s "$SESSION_NAME"
    echo "$SESSION_NAME" > /home/aiciv/civ/.current_session
    if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
        TMUX_ALIVE=true
        log "Tmux session recreated"
    else
        log "Tmux session recreation failed"
    fi
}

claude_check() {
    if pgrep -f "claude" >/dev/null 2>&1; then
        CLAUDE_ALIVE=true
        rm -f /tmp/claude-down-alert
    else
        CLAUDE_ALIVE=false
        if [[ ! -f /tmp/claude-down-alert ]]; then
            log "ALERT: Claude Code is DOWN — manual intervention required"
        fi
        echo "$(date -Iseconds)" > /tmp/claude-down-alert
    fi
    # NEVER restart Claude — alert only
}

# ── Status Output ────────────────────────────────────────────────────
write_status_json() {
    cat > /tmp/watchdog-status.json <<EOJSON
{
  "running": true,
  "last_cycle": "$(date -Iseconds)",
  "claude_alive": ${CLAUDE_ALIVE},
  "portal_healthy": ${PORTAL_HEALTHY},
  "telegram_alive": ${TELEGRAM_ALIVE},
  "tmux_alive": ${TMUX_ALIVE},
  "session_name": "${SESSION_NAME}",
  "pid": $$
}
EOJSON
}

# ── Main Loop ────────────────────────────────────────────────────────
mkdir -p "$(dirname "$LOG")"
check_already_running
log "Watchdog started (PID $$, session=${SESSION_NAME})"

while true; do
    rotate_log
    log "--- cycle start ---"
    portal_check
    telegram_check
    tmux_check
    claude_check
    write_status_json
    sleep "$CHECK_INTERVAL"
done
