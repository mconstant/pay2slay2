# Quickstart

This guide helps you run the API and the scheduler locally in dry-run mode.

## 1) Setup
Create and activate a virtual environment (example):
  - macOS/Linux (zsh):
    - `python3 -m venv .venv`
    - `source .venv/bin/activate`
  - Install project and dev tools:
    - `pip install -e .[dev]`

## 2) Environment
Copy `.env.example` to `.env` and adjust as needed, or export variables manually.

Core (defaults):
  - `DATABASE_URL=sqlite:///pay2slay.db`
  - `SESSION_SECRET=dev-secret` (CHANGE in prod)
  - `P2S_DRY_RUN=true` (set to `false` to use real APIs)
  - `P2S_OPERATOR_ACCOUNT=` (required only when not dry-run for balance check)
  - `P2S_METRICS_PORT=8001`
  - `P2S_INTERVAL_SECONDS=1200` (scheduler loop)

External integrations (required once dry-run=false):
  - `YUNITE_API_KEY=`
  - `YUNITE_GUILD_ID=`
  - `FORTNITE_API_KEY=`
  - `DISCORD_CLIENT_ID=`
  - `DISCORD_CLIENT_SECRET=`
  - `DISCORD_REDIRECT_URI=http://localhost:3000/auth/discord/callback`

Optional observability:
  - `OTEL_EXPORTER_OTLP_ENDPOINT=` or `PAY2SLAY_OTLP_ENDPOINT=`
  - `PAY2SLAY_METRICS_EXEMPLARS=1`

## 3) Run the API
  - `uvicorn src.api.app:create_app --reload --port 8000`
  - Health: http://localhost:8000/healthz

## 4) Run the Scheduler
  - Starts a Prometheus metrics server on `P2S_METRICS_PORT`.
  - Example (dry-run, 10s interval, metrics on 8002):
    - `P2S_INTERVAL_SECONDS=10 P2S_DRY_RUN=true P2S_METRICS_PORT=8002 python -m src.jobs`
  - Stop with Ctrl-C.
  - Metrics: http://localhost:8002/

## 5) Dev loops
  - Tests: `pytest -q`
  - Lint: `ruff check .`
  - Types: `mypy`

## 6) Makefile shortcuts
  - `make api` — start API (reload)
  - `make scheduler` — start scheduler (reads env)
  - `make test` — run tests
  - `make lint` — lint
  - `make type` — type-check
  - `make all` — lint + type + tests