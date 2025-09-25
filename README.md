# Pay2Slay Faucet

Banano payouts for Fortnite kills. FastAPI backend, SQLAlchemy ORM, Alembic migrations, and a simple scheduler that settles rewards and (optionally) pays out via a Banano node.

## Features (current)
- Discord OAuth + Yunite EpicID mapping (dry-run friendly)
- User endpoints: link wallet, status (with last verification details)
- Admin endpoints (cookie-based session): login, reverify (stub), payout retry (stub)
- Domain services for accrual, settlement, payout; Banano RPC client (dry-run supported)
- Scheduler loop with UTC daily/weekly caps, operator balance probe, Prometheus counters

## Requirements
- Python 3.11+
- SQLite (local dev default)

## Quickstart (dev)
See `docs/quickstart.md` for step-by-step setup.

1) Create a virtual environment and install the project (editable):
   - Use your preferred venv manager; packages are defined in `pyproject.toml`.
2) Set environment variables as needed (optional; sensible dev defaults):
   - `DATABASE_URL` (default: `sqlite:///pay2slay.db`)
   - `SESSION_SECRET` (default: `dev-secret`)
   - `P2S_DRY_RUN` (default: `true`)
   - `P2S_MIN_OPERATOR_BALANCE_BAN` (default: `50`)
   - `P2S_INTERVAL_SECONDS` (default: `1200`) – scheduler interval
   - `P2S_OPERATOR_ACCOUNT` (only needed when not dry-run)
   - `P2S_METRICS_PORT` (default: `8001`)

## Run the API (dev)
- App factory is `src/api/app.py:create_app()`; run with your ASGI server of choice.
- Example (uvicorn): `uvicorn src.api.app:create_app --reload`

## Run the Scheduler (dev)
- Metrics: the scheduler starts a Prometheus HTTP server (default port `8001`).
- Start the loop (blocking): `python -m src.jobs`
- Graceful shutdown: Ctrl-C (SIGINT) or SIGTERM.

Makefile shortcuts are available:
- `make api` to run the API
- `make scheduler` to run the scheduler
- `make all` to lint, type-check, and test

## Configuration
- YAML configs under `configs/`: `payout.yaml`, `integrations.yaml`, `product.yaml`
- Environment variables are supported in these configs (see `src/lib/config.py`).

## Testing
- Contract tests live under `tests/contract/`. Run the full suite with `pytest`.

## Documentation
- Quickstart: `docs/quickstart.md`
- API: `docs/api.md`

## Runtime notes
- Scheduler and metrics can be started via the CLI entrypoint (`python -m src.jobs`).
- Metrics default to port 8001; set `P2S_METRICS_PORT` to change.

## Deploy
- Docker (local): `docker build -t pay2slay2:dev .` then `docker-compose up --build`
- CI: GitHub Actions workflow `.github/workflows/ci.yml` runs lint, type, tests, SBOM/scan.
- Akash (Terraform):
   - Prereqs: set `AKASH_MNEMONIC` secret in GitHub, and use `deploy-akash` workflow dispatch with `image_tag`.
   - Infra code under `infra/akash` uses the Akash Terraform provider to submit a simple deployment.

## Notes
- Dry-run mode short-circuits external calls and assumes a healthy operator balance; use for local testing.
- Alembic migrations are initialized; SQLite dev DB is created automatically on app startup.
