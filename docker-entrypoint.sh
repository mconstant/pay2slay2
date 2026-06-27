#!/bin/sh
set -e

# Run Alembic migrations if auto-migrate is enabled
if [ "${PAY2SLAY_AUTO_MIGRATE}" = "1" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head || echo "Migration warning (non-fatal): tables may already exist"
fi

# Log level for uvicorn access logs (default: warning to reduce volume)
LOG_LEVEL="${P2S_LOG_LEVEL:-warning}"

# ── Periodic cleanup (prevent disk fill from temp files / stale data) ──
# Runs every 6 hours: cleans /tmp files older than 24h
(
  while true; do
    sleep 21600
    find /tmp -type f -mtime +1 -delete 2>/dev/null || true
    echo "[cleanup] tmp files pruned at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  done
) &

# ── DR: optional integrity check of the existing restic repo on startup ──
if [ "${CHECK_BACKUP}" = "true" ]; then
  bash /app/scripts/infra/check_backup.sh || true
fi

# ── DR: restore from latest snapshot before first run on a fresh volume ──
DATA_DIR="$(dirname "${DB_PATH:-/data/pay2slay.db}")"
if [ ! -f "${DATA_DIR}/.restored" ] && [ "${RESTORE_FROM_BACKUP}" = "true" ]; then
  bash /app/scripts/infra/restore.sh
fi

# ── DR: periodic restic backup of the live DB to Storj ──
# Loud failures (no `|| echo swallow`) — the previous loop was silently
# 403'ing for months because of misscoped creds.
bash /app/scripts/infra/backup.sh &

# Start API server (foreground) — scheduler runs as a background thread inside the API process
echo "Starting API server..."
exec uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --log-level "$LOG_LEVEL"
