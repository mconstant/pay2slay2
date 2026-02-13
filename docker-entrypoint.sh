#!/bin/sh
set -e

# Run Alembic migrations if auto-migrate is enabled
if [ "${PAY2SLAY_AUTO_MIGRATE}" = "1" ]; then
    echo "Running database migrations..."
    python -m alembic upgrade head || echo "Migration warning (non-fatal): tables may already exist"
fi

# Log level for uvicorn access logs (default: warning to reduce volume)
LOG_LEVEL="${P2S_LOG_LEVEL:-warning}"

# Start scheduler in background (log output so crashes aren't silent)
echo "Starting scheduler..."
python -m src.jobs 2>&1 | while IFS= read -r line; do echo "[scheduler] $line"; done &

# Start API server (foreground)
echo "Starting API server..."
exec uvicorn src.api.app:create_app --factory --host 0.0.0.0 --port 8000 --log-level "$LOG_LEVEL"
