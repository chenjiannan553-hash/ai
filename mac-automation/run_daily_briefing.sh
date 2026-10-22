#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DATE="${1:-$(TZ=Asia/Shanghai date '+%Y-%m-%d')}"
LOG_DIR="$HOME/Library/Logs"
mkdir -p "$LOG_DIR"
exec >> "$LOG_DIR/ai-daily-briefing.log" 2>&1

echo
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting AI briefing for Beijing date $TARGET_DATE"

# Use only saved Codex/ChatGPT account auth. Do not route through API-key auth.
unset OPENAI_API_KEY CODEX_API_KEY
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

for command_name in python3 codex git; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: $command_name"
    exit 10
  fi
done

AUTH_STATUS="$(codex login status 2>&1)" || {
  echo "ERROR: Codex login is missing or expired."
  printf '%s\n' "$AUTH_STATUS"
  exit 9
}
if printf '%s' "$AUTH_STATUS" | grep -Eiq 'api.?key|apikey'; then
  echo "ERROR: Active Codex login is API-key based; refusing to risk API billing."
  exit 9
fi
if ! printf '%s' "$AUTH_STATUS" | grep -Eiq 'chatgpt'; then
  echo "ERROR: Active Codex login is not verified as ChatGPT authentication."
  printf '%s\n' "$AUTH_STATUS"
  exit 9
fi

cd "$REPO_ROOT"

# Never overwrite local user edits or attempt a merge automatically.
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: Local repository has uncommitted changes; refusing to overwrite them."
  exit 11
fi

git switch main
git pull --ff-only origin main

# Collect current RSS source material and build a complete prompt file.
TZ=Asia/Shanghai python3 scripts/daily_briefing.py

PROMPT_FILE="$REPO_ROOT/reports/$TARGET_DATE-chatgpt-prompt.md"
REPORT_FILE="$REPO_ROOT/reports/$TARGET_DATE.md"
if [[ ! -s "$PROMPT_FILE" ]]; then
  echo "ERROR: No prompt/source file was generated: $PROMPT_FILE"
  exit 12
fi

TMP_REPORT="$(mktemp "${TMPDIR:-/tmp}/ai-briefing.XXXXXX.md")"
trap 'rm -f "$TMP_REPORT"' EXIT

# codex exec reads the prepared task + RSS material from stdin. Read-only mode
# keeps model-generated shell commands from modifying this repository.
if ! codex exec --ephemeral --sandbox read-only - < "$PROMPT_FILE" > "$TMP_REPORT"; then
  echo "ERROR: Codex did not complete. Check login verification, plan usage limits, and network."
  exit 13
fi

python3 - "$TMP_REPORT" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
text = p.read_text(encoding="utf-8").strip()
if len(text) < 700:
    raise SystemExit("ERROR: Generated response is too short to be a complete briefing.")
if "全球 AI 新闻简报" not in text and "全球AI新闻简报" not in text:
    raise SystemExit("ERROR: Generated response does not look like the requested briefing.")
p.write_text(text + "\n", encoding="utf-8")
PY

mv "$TMP_REPORT" "$REPORT_FILE"
trap - EXIT

git add "$REPORT_FILE" "$PROMPT_FILE"
if git diff --cached --quiet; then
  echo "No report changes to commit."
  exit 0
fi

git config user.name "AI News Briefing Automation"
git config user.email "ai-news-briefing@users.noreply.github.com"
git commit -m "Daily AI news briefing ($TARGET_DATE)"
git push origin main

echo "[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: AI-generated briefing pushed to GitHub."
