#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.chenjiannan553-hash.ai-daily-briefing"
UID_NOW="$(id -u)"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs"
TMP_OUT="$(mktemp "${TMPDIR:-/tmp}/codex-auth-check.XXXXXX")"
TMP_ERR="$(mktemp "${TMPDIR:-/tmp}/codex-auth-error.XXXXXX")"
trap 'rm -f "$TMP_OUT" "$TMP_ERR"' EXIT

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
unset OPENAI_API_KEY CODEX_API_KEY

for command_name in python3 codex git; do
  if ! command -v "$command_name" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: $command_name"
    echo "Install/update the official Codex CLI and ensure Python 3 and Git are available."
    exit 2
  fi
done

cd "$REPO_ROOT"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "ERROR: Your local repository has uncommitted changes."
  echo "Commit or back up those changes, then run this installer again."
  exit 3
fi

git switch main
git pull --ff-only origin main

echo "Checking that Codex is signed in with ChatGPT (not an API key)..."
if ! AUTH_STATUS="$(codex login status 2>&1)"; then
  echo "ERROR: Codex has no usable saved login."
  printf '%s\n' "$AUTH_STATUS"
  echo "Complete the official ChatGPT sign-in, then retry."
  exit 4
fi
printf '%s\n' "$AUTH_STATUS"
if printf '%s' "$AUTH_STATUS" | grep -Eiq 'api.?key|apikey'; then
  echo "ERROR: Codex is using API-key authentication. This automation refuses API billing."
  exit 5
fi
if ! printf '%s' "$AUTH_STATUS" | grep -Eiq 'chatgpt'; then
  echo "ERROR: Could not verify that the active Codex login is a ChatGPT account."
  echo "For safety, the installer will not enable scheduled model requests."
  exit 5
fi

echo "Checking ChatGPT-backed model access with a small test request..."
if ! codex exec --ephemeral --sandbox read-only "只输出 AUTH_OK，不执行命令，不读取或修改任何文件。" > "$TMP_OUT" 2> "$TMP_ERR"; then
  echo "ERROR: The ChatGPT-backed Codex request failed."
  cat "$TMP_ERR"
  echo
  echo "Complete the normal Codex sign-in and any required verification."
  echo "If OpenAI requires phone verification, this automation cannot bypass it."
  exit 6
fi
if ! grep -q "AUTH_OK" "$TMP_OUT"; then
  echo "ERROR: Codex login test did not return AUTH_OK."
  cat "$TMP_OUT"
  cat "$TMP_ERR"
  exit 7
fi
echo "Codex login test passed."

echo "Checking GitHub push authorization (dry run; no commit is pushed)..."
if ! git push --dry-run origin main; then
  echo "ERROR: Git can read the repository but does not have working push authorization."
  echo "Sign in to GitHub on this Mac, verify that you can push to main, then retry."
  exit 8
fi

mkdir -p "$PLIST_DIR" "$LOG_DIR"
python3 - "$REPO_ROOT" "$PLIST_PATH" "$LOG_DIR" <<'PY'
import plistlib
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
plist_path = Path(sys.argv[2])
log_dir = Path(sys.argv[3])
label = "com.chenjiannan553-hash.ai-daily-briefing"

config = {
    "Label": label,
    "ProgramArguments": ["/bin/bash", str(repo / "mac-automation" / "schedule_check.sh")],
    "WorkingDirectory": str(repo),
    "StartInterval": 60,
    "RunAtLoad": True,
    "StandardOutPath": str(log_dir / "ai-daily-briefing-scheduler.log"),
    "StandardErrorPath": str(log_dir / "ai-daily-briefing-scheduler.log"),
}
with plist_path.open("wb") as f:
    plistlib.dump(config, f)
PY

# Replace an existing copy of this same LaunchAgent if present.
launchctl bootout "gui/$UID_NOW" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$UID_NOW" "$PLIST_PATH"
launchctl enable "gui/$UID_NOW/$LABEL"

echo
echo "Installed: $PLIST_PATH"
echo "The agent checks every minute and targets 17:20 Asia/Shanghai."
echo "It retries at most three times per China date and never stores API keys in this repository."
echo "Main log: $LOG_DIR/ai-daily-briefing.log"
echo "Scheduler log: $LOG_DIR/ai-daily-briefing-scheduler.log"
echo "To unload: launchctl bootout gui/$UID_NOW '$PLIST_PATH'"
