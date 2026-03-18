#!/bin/bash
# Regenerates heatmap.svg and pushes to GitHub.
# Called by the Launch Agent when auto-update is enabled.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$SCRIPT_DIR" || exit 1

python3 "$SCRIPT_DIR/generate_heatmap.py" --out "$SCRIPT_DIR/heatmap.svg" \
  >> "$SCRIPT_DIR/update.log" 2>&1

git add heatmap.svg
git diff --cached --quiet && exit 0   # nothing changed, skip commit

git commit -m "chore: update heatmap $(date +%Y-%m-%d)" \
  >> "$SCRIPT_DIR/update.log" 2>&1
git push >> "$SCRIPT_DIR/update.log" 2>&1
