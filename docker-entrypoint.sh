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

# ── Periodic Backup to Storj ──
# Runs every 4 hours (14400s)
(
  # Wait a bit before initial backup
  sleep 60
  while true; do
    echo "[backup] Starting SQLite database backup to Storj..."
    sqlite3 /app/pay2slay.db ".backup '/tmp/pay2slay.db'"
    rclone copy /tmp/pay2slay.db storj:bananocraftbackups/pay2slay2-backups/pay2slay-$(date -u +%Y%m%d-%H%M%S).db -v || echo "[backup] rclone upload failed"
    rm -f /tmp/pay2slay.db
    echo "[backup] Finished backup run."
    sleep 14400
  done
) &

# Start API server (foreground) — scheduler runs as a background thread inside the API process
echo "Starting API server..."
exec uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --log-level "$LOG_LEVEL"
