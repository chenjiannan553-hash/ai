#!/usr/bin/env bash
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$HOME/Library/Application Support/ai-daily-briefing"
SUCCESS_FILE="$STATE_DIR/last-successful-date"
ATTEMPT_FILE="$STATE_DIR/attempts"
LOCK_DIR="$STATE_DIR/run.lock"
mkdir -p "$STATE_DIR"

TODAY="$(TZ=Asia/Shanghai date '+%Y-%m-%d')"
CLOCK="$(TZ=Asia/Shanghai date '+%H:%M')"

# LaunchAgent checks once per minute. Run at/after 17:20 China time, with
# catch-up after sleep or a missed trigger, but only once successfully per day.
if [[ "$CLOCK" < "17:20" ]]; then
  exit 0
fi
if [[ -f "$SUCCESS_FILE" ]] && [[ "$(cat "$SUCCESS_FILE")" == "$TODAY" ]]; then
  exit 0
fi

# Avoid overlapping launches while Codex is still running.
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  exit 0
fi
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

# Recheck success and bounded retry count after acquiring the lock.
if [[ -f "$SUCCESS_FILE" ]] && [[ "$(cat "$SUCCESS_FILE")" == "$TODAY" ]]; then
  exit 0
fi

ATTEMPT_DATE=""
ATTEMPTS=0
if [[ -f "$ATTEMPT_FILE" ]]; then
  read -r ATTEMPT_DATE ATTEMPTS < "$ATTEMPT_FILE" || true
fi
if [[ "$ATTEMPT_DATE" != "$TODAY" ]]; then
  ATTEMPTS=0
fi
if [[ "$ATTEMPTS" -ge 3 ]]; then
  exit 0
fi

ATTEMPTS=$((ATTEMPTS + 1))
printf '%s %s\n' "$TODAY" "$ATTEMPTS" > "$ATTEMPT_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Attempt $ATTEMPTS for Beijing date $TODAY"

if /bin/bash "$REPO_ROOT/mac-automation/run_daily_briefing.sh" "$TODAY"; then
  printf '%s\n' "$TODAY" > "$SUCCESS_FILE"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scheduled briefing completed."
else
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scheduled briefing failed. Will retry later today if attempts remain."
  exit 1
fi
