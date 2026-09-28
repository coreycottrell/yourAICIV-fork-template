#!/usr/bin/env bash
# template-watchdog.sh — CIV-universal process watchdog
# Monitors: Portal, Telegram bot, Tmux session, Claude Code
# Runs every 60s. Self-contained for born AiCIV containers.
# Does NOT monitor relay.py (has its own watchdog in entrypoint.sh).

set -euo pipefail

# ── Configuration ────────────────────────────────────────────────────
# The civ tree is the one this script lives in (<civ>/tools/watchdog.sh) unless
# CLAUDE_PROJECT_DIR says otherwise. In the fleet the template is checked out at
# /home/aiciv (= HOME); a fixed civ/ subdir would point client_sites,
# partner_notify, the portal env and the log at a tree without those tools.
WATCHDOG_TREE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd -P)"
CLAUDE_PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$WATCHDOG_TREE}"
export CLAUDE_PROJECT_DIR
USER_HOME="${HOME:-/home/aiciv}"
# restart-self.sh records the primary session in <civ>/.current_session and ~/.current_session.
SESSION_NAME="$(head -1 "${CLAUDE_PROJECT_DIR}/.current_session" 2>/dev/null || true)"
[[ -n "$SESSION_NAME" ]] || SESSION_NAME="$(head -1 "${USER_HOME}/.current_session" 2>/dev/null || true)"
SESSION_NAME="${SESSION_NAME:-${CIV_NAME:-aiciv}-primary}"
# The running portal records its install dir in ~/.portal_dir.
PORTAL_DIR="$(head -1 "${USER_HOME}/.portal_dir" 2>/dev/null || true)"
PORTAL_DIR="${PORTAL_DIR:-${USER_HOME}/purebrain_portal}"
CHECK_INTERVAL=60
LOG_MAX_LINES=5000
LOG_KEEP_LINES=1000
MAX_RESTARTS=3
RESTART_WINDOW=600
LOG_DIR="${CLAUDE_PROJECT_DIR}/logs"
LOG="${LOG_DIR}/watchdog.log"
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
        # After a container restart the pidfile can survive while its PID now belongs to
        # an unrelated process -- only a live watchdog.sh counts as "already running".
        if kill -0 "$old_pid" 2>/dev/null && \
           tr '\0' ' ' 2>/dev/null < "/proc/${old_pid}/cmdline" | grep -q "watchdog\.sh"; then
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
        partner_health "crash_loop_${name}" "${name} keeps failing: restarted ${recent} times in ${RESTART_WINDOW}s, the watchdog backed off."
        return 1
    fi
    return 0
}

# ── Portal environment ──────────────────────────────────────────────
# Birth gives the portal PORTAL_PUBLIC_URL (also written to ~/.env) and, for M3 trials,
# TRIAL_CONFIG_PATH (the operator copy, e.g. /etc/aiciv/trial.json; also recorded in
# .claude/settings.json env). A portal restarted from here must keep both: any that is
# missing from this watchdog's own env is read from ~/.env, then <civ>/.env, and
# TRIAL_CONFIG_PATH finally from .claude/settings.json env. The process env wins.
PORTAL_ENV_VARS=(PORTAL_PUBLIC_URL TRIAL_CONFIG_PATH)

# env_file_get <file> <VAR> -- last VAR=value line (optional "export ", quotes stripped)
env_file_get() {
    [[ -r "$1" ]] || return 0
    grep -E "^[[:space:]]*(export[[:space:]]+)?$2=" "$1" 2>/dev/null | tail -1 | \
        sed -E "s/^[[:space:]]*(export[[:space:]]+)?$2=//; s/[[:space:]]+\$//; s/^\"(.*)\"\$/\1/; s/^'(.*)'\$/\1/" || true
}

portal_env() {
    local var val src summary=""
    for var in "${PORTAL_ENV_VARS[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            summary+=" ${var}=env"
            continue
        fi
        val=""; src=""
        for src in "${HOME:-/home/aiciv}/.env" "${CLAUDE_PROJECT_DIR}/.env"; do
            val=$(env_file_get "$src" "$var")
            [[ -n "$val" ]] && break
        done
        if [[ -z "$val" && "$var" == "TRIAL_CONFIG_PATH" ]]; then
            src="${CLAUDE_PROJECT_DIR}/.claude/settings.json"
            val=$(python3 -c 'import json,sys; print((json.load(open(sys.argv[1])).get("env") or {}).get("TRIAL_CONFIG_PATH",""))' \
                  "$src" 2>/dev/null || true)
        fi
        if [[ -n "$val" ]]; then
            export "${var}=${val}"
            summary+=" ${var}=${src}"
        else
            summary+=" ${var}=unset"
        fi
    done
    log "Portal env:${summary}"
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
    pid=$(pgrep -f "portal_server.py|node.*server" 2>/dev/null | head -1) || true
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
        portal_env
        cd "$PORTAL_DIR"
        if [[ -f "$PORTAL_DIR/start.sh" ]]; then   # Python portal (portal_server.py)
            nohup bash "$PORTAL_DIR/start.sh" >> "${LOG_DIR}/portal.log" 2>&1 &
        else
            nohup node server.js >> "${LOG_DIR}/portal.log" 2>&1 &
        fi
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
        nohup python3 "$tg_script" >> "${LOG_DIR}/telegram.log" 2>&1 &
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
    echo "$SESSION_NAME" > "${CLAUDE_PROJECT_DIR}/.current_session" 2>/dev/null || true
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
            echo "$(date -Iseconds)" > /tmp/claude-down-alert   # keeps the first-down time
        elif (( $(date +%s) - $(stat -c %Y /tmp/claude-down-alert) >= 600 )); then
            partner_health "aiciv_down" "The AiCIV's Claude Code process has been down for 10+ minutes (since $(cat /tmp/claude-down-alert)). The watchdog never restarts it; it needs a restart."
        fi
    fi
    # NEVER restart Claude — alert only
}

# Client business sites (apps/<slug>, published at <portal>/site/<slug>/).
# Registered by tools/client_sites.py go-live; restarted here if down.
CLIENT_SITES_DOWN=0
client_sites_check() {
    local tool="${CLAUDE_PROJECT_DIR}/tools/client_sites.py"
    [[ -f "$tool" ]] || return 0
    CLIENT_SITES_DOWN=$(python3 "$tool" list 2>/dev/null | grep -c " DOWN " || true)
    (( CLIENT_SITES_DOWN > 0 )) || return 0
    if ! track_restart "client-sites"; then
        return
    fi
    log "Client sites down: ${CLIENT_SITES_DOWN} -- starting"
    CLIENT_VENV="${CLAUDE_PROJECT_DIR}/apps/.venv" python3 "$tool" ensure >> "$LOG" 2>&1 || \
        log "Client sites: some did not start (see apps/<slug>/logs/app.log)"
}

# Partner notifications (skill: partner-notifications): OFF by default -- reseller
# notifications come from True Bearing, and both functions return at once while
# config/partner.json has no notify_emails. When an operator switches it on, `tick`
# reports what the disk shows, probes the model router, and sends the outbox.
# Never fails the cycle.
partner_check() {
    local tool="${CLAUDE_PROJECT_DIR}/tools/partner_notify.py"
    [[ -f "$tool" ]] || return 0
    python3 "$tool" enabled --root "$CLAUDE_PROJECT_DIR" 2>/dev/null || return 0
    timeout 50 python3 "$tool" tick --root "$CLAUDE_PROJECT_DIR" >> "$LOG" 2>&1 || true
}

# partner_health <kind> <summary>  -- at most one email per kind per day
partner_health() {
    local tool="${CLAUDE_PROJECT_DIR}/tools/partner_notify.py"
    [[ -f "$tool" ]] || return 0
    python3 "$tool" enabled --root "$CLAUDE_PROJECT_DIR" 2>/dev/null || return 0
    timeout 30 python3 "$tool" send --root "$CLAUDE_PROJECT_DIR" --event health \
        --kind "$1" --summary "$2" >> "$LOG" 2>&1 || true
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
  "client_sites_down": ${CLIENT_SITES_DOWN},
  "session_name": "${SESSION_NAME}",
  "pid": $$
}
EOJSON
}

# ── Main Loop ────────────────────────────────────────────────────────
if [[ "${1:-}" == "--config" ]]; then   # print the resolved paths and exit (operators, tests)
    printf 'CLAUDE_PROJECT_DIR=%s\nSESSION_NAME=%s\nPORTAL_DIR=%s\nLOG=%s\n' \
        "$CLAUDE_PROJECT_DIR" "$SESSION_NAME" "$PORTAL_DIR" "$LOG"
    exit 0
fi
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
    client_sites_check
    partner_check
    write_status_json
    sleep "$CHECK_INTERVAL"
done
