#!/usr/bin/env bash
# Run at container start (when CHECK_BACKUP=true) to verify the restic repo is
# sound and to log what snapshots are available. Mirrors bananocraft's
# check_backup.sh — uses `|| true` everywhere because the worst outcome of a
# check is "we logged a problem"; we don't want to block the API from starting.
set -x

: "${SERVER_NAME:=prod}"
: "${RESTIC_REPO_PATH:=pay2slay2-backups/${SERVER_NAME}-backup}"
REPO="rclone:storj:${RESTIC_REPO_PATH}"

echo "[check_backup] verifying repo $REPO"
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" unlock || true
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" check || true
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" rebuild-index || true
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" unlock || true
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" check || true

echo "[check_backup] snapshots available for restore:"
RESTIC_PASSWORD="$RESTIC_PASSWORD" restic --no-lock --repo "$REPO" snapshots || true
echo "[check_backup] done"
