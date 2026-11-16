#!/usr/bin/env bash
# Nightly encrypted backup of a life archive with rclone (Mac, Linux). Setup: docs/backup.md.
#   ./backup.sh           # what cron or launchd runs every night
#   ./backup.sh --dry-run # show what would change, send nothing
# Each folder below is mirrored to <remote>:current/<name>. A file that changed or was deleted here isn't lost:
# its previous copy moves to <remote>:old/<date>/<name>, kept for KEEP_DAYS days.
set -euo pipefail

# ---- edit these ----
REMOTE="archive-crypt"                       # your rclone crypt remote (rclone config)
PARTS=(                                      # name=folder on this computer
  "exports=$HOME/my-archive/exports"         # the originals
  "derived=$HOME/my-archive/derived"         # catalog, timeline, corrections
)
KEEP_DAYS=30
# --------------------

DRY=""
[[ "${1:-}" == "--dry-run" ]] && DRY="--dry-run"
LOGS="$HOME/my-archive/backup-logs"
mkdir -p "$LOGS"
TODAY=$(date +%F)
LOG="$LOGS/$TODAY.log"
FILTER=$(mktemp)
printf '%s\n' '**/*token*' '**/*secret*' '**/*.key' '**/rclone.conf' '**/__pycache__/**' '**/node_modules/**' \
  '._*' '.DS_Store' 'backup-logs/**' > "$FILTER"

for part in "${PARTS[@]}"; do
  name="${part%%=*}"
  source="${part#*=}"
  if [[ ! -d "$source" ]]; then echo "skipped $name (not found: $source)" >> "$LOG"; continue; fi
  echo "=== $name ($source) $(date +%FT%T)" >> "$LOG"
  rclone sync "$source" "$REMOTE:current/$name" --backup-dir "$REMOTE:old/$TODAY/$name" --exclude-from "$FILTER" \
    --transfers 4 --checkers 8 --fast-list --log-file "$LOG" --log-level INFO $DRY || echo "=== $name failed" >> "$LOG"
done

# old copies are kept KEEP_DAYS days, so the cloud doesn't fill up with every version forever
if [[ -z "$DRY" ]]; then
  if date -v-1d +%F >/dev/null 2>&1; then CUTOFF=$(date -v-"${KEEP_DAYS}"d +%F); else CUTOFF=$(date -d "-${KEEP_DAYS} days" +%F); fi
  rclone lsf --dirs-only "$REMOTE:old" 2>/dev/null | while read -r day; do
    day="${day%/}"
    if [[ "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ && "$day" < "$CUTOFF" ]]; then
      echo "=== removing old copies from $day" >> "$LOG"
      rclone purge "$REMOTE:old/$day" --log-file "$LOG" --log-level INFO
    fi
  done
fi
rm -f "$FILTER"
echo "=== all done $(date +%FT%T)" >> "$LOG"
