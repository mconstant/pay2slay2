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

## 6) Database migrations
If using Alembic (Postgres / persistent DB) you can apply migrations:
```
PAY2SLAY_AUTO_MIGRATE=1 python -m src.api.app  # triggers upgrade on start
```
Or manually:
```
alembic upgrade head
```

## 7) Image build & signing (supply chain)
Build container image locally:
```
docker build -t pay2slay:local .
```
Generate SBOM (Syft) and sign (Cosign) (example):
```
syft packages pay2slay:local -o spdx-json > sbom.json
cosign sign --key cosign.key pay2slay:local
cosign attest --predicate sbom.json --type spdxjson pay2slay:local
```
Verify:
```
cosign verify pay2slay:local
```

## 8) Deployment (Akash)
See the **Deploy** section in `README.md` for full instructions. Quick summary:
1. Set all GitHub secrets and variables (see tables in README).
2. Update Discord app redirect URI to `https://yourdomain.com/auth/discord/callback`.
3. Run: `gh workflow run deploy-akash.yml -f domain_name=yourdomain.com -f image_tag=latest`
4. Point your domain CNAME to the Akash provider hostname shown in the workflow output.

## 9) Makefile shortcuts
  - `make api` — start API (reload)
  - `make scheduler` — start scheduler (reads env)
  - `make test` — run tests
  - `make lint` — lint
  - `make type` — type-check
  - `make all` — lint + type + tests

## 10) Architecture Notes
- The container runs both the API server (uvicorn) and the scheduler as a background process via `docker-entrypoint.sh`.
- Banano transactions use the public Kalium RPC (`https://kaliumapi.appditto.com/api`) — no self-hosted node needed.
- The operator seed for signing Banano transactions is stored encrypted in the `SecureConfig` DB table (use the admin panel to set it).

## 11) Immutable Tagging & Rollback (CI Workflows)
Build workflow (push trigger) produces an image tagged with the full 40-char git SHA and short 12-char tag. Deployment & rollback workflows only accept full SHA tags (immutable) and enforce:
 - Pre/post push digest verification (build-time) to catch tampering.
 - Deployment-time repository mapping + digest guard.
 - Dedicated rollback workflow reuses existing image without rebuild.

Reference: `docs/distribution.md` for digest integrity guards, metrics, SBOM linkage, short tag parity, and single-arch constraint.