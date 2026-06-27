#!/usr/bin/env bash
# Periodic backup of the pay2slay sqlite DB to Storj via restic.
# Modeled on bananocraft's backup.sh (encrypted, deduped, retention-pruned)
# but adapted for sqlite (atomic .backup snapshot instead of mc save-off/on).
set -eE -o pipefail

: "${SERVER_NAME:=prod}"
: "${BACKUP_MINUTE_INTERVAL:=240}"          # 4h default
: "${DB_PATH:=/data/pay2slay.db}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD is required}"
: "${RESTIC_REPO_PATH:=pay2slay2-backups/${SERVER_NAME}-backup}"

REPO="rclone:storj:${RESTIC_REPO_PATH}"
SNAP_DIR="/tmp/pay2slay-snapshot"
mkdir -p "$SNAP_DIR"

ts() { date -u +%FT%TZ; }

# Initialise the repo once. `restic init` is idempotent-safe (errors if it
# already exists; we ignore that case but surface real errors via check_backup).
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --repo "$REPO" init >/dev/null 2>&1 || true

while true; do
  echo "[backup $(ts)] sqlite atomic snapshot of $DB_PATH"
  if ! sqlite3 "$DB_PATH" ".backup '$SNAP_DIR/pay2slay.db'"; then
    echo "[backup $(ts)] ERROR: sqlite .backup failed — skipping this run" >&2
    sleep $(( BACKUP_MINUTE_INTERVAL * 60 ))
    continue
  fi

  EXIT_CODE=0
  RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --repo "$REPO" backup "$SNAP_DIR" \
    --tag auto --host "$SERVER_NAME" || EXIT_CODE=$?

  if [ "$EXIT_CODE" -eq 0 ]; then
    echo "[backup $(ts)] OK"
  else
    # Loud — this is what was silent before.
    echo "[backup $(ts)] FAILED with exit code $EXIT_CODE" >&2
  fi

  # Retention policy mirrors bananocraft (deep history is cheap on dedupe).
  RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --repo "$REPO" forget \
    --keep-hourly 24 --keep-daily 7 --keep-weekly 5 --keep-monthly 12 --keep-yearly 75 \
    --prune || echo "[backup $(ts)] retention prune failed (non-fatal)" >&2

  rm -f "$SNAP_DIR/pay2slay.db"
  sleep $(( BACKUP_MINUTE_INTERVAL * 60 ))
done
