#!/bin/bash
# Toggle automatic daily heatmap updates on/off.
#
# Usage:
#   ./toggle.sh enable    — install Launch Agent (runs daily at 9 AM)
#   ./toggle.sh disable   — uninstall Launch Agent
#   ./toggle.sh status    — show whether auto-update is active

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/com.ankidailyreviews.heatmap.plist"
PLIST_LABEL="com.ankidailyreviews.heatmap"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_LABEL.plist"

is_loaded() {
  launchctl list | grep -q "$PLIST_LABEL"
}

case "$1" in
  enable)
    if is_loaded; then
      echo "Auto-update is already enabled."
      exit 0
    fi
    # Substitute the real repo path into the plist
    sed "s|REPO_PATH|$SCRIPT_DIR|g" "$PLIST_SRC" > "$PLIST_DEST"
    launchctl load "$PLIST_DEST"
    echo "Auto-update enabled. Heatmap will refresh daily at 9:00 AM."
    ;;

  disable)
    if ! is_loaded; then
      echo "Auto-update is already disabled."
      exit 0
    fi
    launchctl unload "$PLIST_DEST"
    rm -f "$PLIST_DEST"
    echo "Auto-update disabled."
    ;;

  status)
    if is_loaded; then
      echo "Auto-update: ENABLED (runs daily at 9:00 AM)"
    else
      echo "Auto-update: DISABLED"
    fi
    ;;

  *)
    echo "Usage: $0 {enable|disable|status}"
    exit 1
    ;;
esac
