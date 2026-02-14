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

# Start API server (foreground) — scheduler runs as a background thread inside the API process
echo "Starting API server..."
exec uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --log-level "$LOG_LEVEL"
