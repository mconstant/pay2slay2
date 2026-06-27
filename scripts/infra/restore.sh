#!/usr/bin/env bash
# Restore pay2slay sqlite DB from a restic snapshot on Storj.
# Triggered from docker-entrypoint when RESTORE_FROM_BACKUP=true and there is
# no /data/.restored marker. Defaults to the latest snapshot; override with
# RESTORE_VERSION=<snapshot-id>.
set -eE -o pipefail

: "${SERVER_NAME:=prod}"
: "${RESTORE_VERSION:=latest}"
: "${DB_PATH:=/data/pay2slay.db}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD is required}"
: "${RESTIC_REPO_PATH:=pay2slay2-backups/${SERVER_NAME}-backup}"

REPO="rclone:storj:${RESTIC_REPO_PATH}"
RESTORE_DIR=$(mktemp -d)
DATA_DIR=$(dirname "$DB_PATH")
mkdir -p "$DATA_DIR"

echo "[restore] restoring snapshot $RESTORE_VERSION from $REPO"
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" unlock || true

# If the repo doesn't exist yet (first-ever deploy, no backups taken), don't
# brick the container — mark as "restored" and let backup.sh populate the
# repo on its first run.
if ! RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" snapshots --last >/dev/null 2>&1; then
  echo "[restore] no snapshots available (fresh repo) — skipping restore"
  touch "${DATA_DIR}/.restored"
  rm -rf "$RESTORE_DIR"
  exit 0
fi

RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --repo "$REPO" restore "$RESTORE_VERSION" --target "$RESTORE_DIR"

# Snapshot path inside the archive depends on where backup.sh ran; locate the
# DB by name rather than hardcoding the path.
RESTORED_DB=$(find "$RESTORE_DIR" -name "pay2slay.db" -type f | head -1)
if [ -z "$RESTORED_DB" ]; then
  echo "[restore] FATAL: no pay2slay.db in restored snapshot" >&2
  exit 1
fi

INT=$(sqlite3 "$RESTORED_DB" "PRAGMA integrity_check;")
if [ "$INT" != "ok" ]; then
  echo "[restore] FATAL: restored DB failed integrity_check: $INT" >&2
  exit 1
fi

# Preserve whatever was on disk (empty after a fresh deploy, but be safe).
if [ -f "$DB_PATH" ]; then
  mv "$DB_PATH" "${DB_PATH}.pre-restore.$(date -u +%s)"
fi
cp "$RESTORED_DB" "$DB_PATH"

rm -rf "$RESTORE_DIR"
touch "${DATA_DIR}/.restored"
echo "[restore] OK — DB restored to $DB_PATH"
