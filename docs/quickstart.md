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

## 8) Deployment (Akash example snippet)
Values to template into `infra/akash/*.tf` or manifests:
- Image reference (signed) + digest
- Environment secrets via provider (never bake secrets in image)
- Expose port 8000 (API) and metrics port if required

## 9) Makefile shortcuts
  - `make api` — start API (reload)
  - `make scheduler` — start scheduler (reads env)
  - `make test` — run tests
  - `make lint` — lint
  - `make type` — type-check
  - `make all` — lint + type + tests

## 10) Next steps
 - Review `SECURITY.md` for supply chain & provenance guidelines.
 - Fill out `research.md`, `data-model.md`, and `contracts/` docs (tasks T046–T048).
 - Switch monetary fields to Decimal before production payouts (T052).

## 12) Immutable Tagging & Rollback (CI Workflows)
Build workflow (push trigger) produces an image tagged with the full 40‑char git SHA and short 12‑char tag. Deployment & rollback workflows only accept full SHA tags (immutable) and enforce:
 - Pre/post push digest verification (build-time) to catch tampering (FR-009).
 - Deployment-time repository mapping + digest guard (placeholder registry lookup) (FR-004, FR-016).
 - Dedicated rollback workflow reuses existing image without rebuild (FR-013).

Reference: `docs/distribution.md` for digest integrity guards, metrics, SBOM linkage placeholder, short tag parity, and single-arch constraint.

Metrics counters exposed: `image_build_total{repository_type}`, `rollback_total{repository_type}`.


## 11) Split Akash Deployments (Banano Node + API)
The project supports separated Akash deployments for the Banano node and API service to decouple lifecycle and scaling.

### Workflows
GitHub Actions:
- `banano-deploy.yml` provisions/updates Banano node then emits `infra/akash-banano/endpoint.json`.
- `api-deploy.yml` downloads and validates the artifact and applies the API stack passing `-var="banano_rpc_endpoint=<host:port>"`.

### Trigger (Web UI)
1. Run Banano workflow (workflow_dispatch).
2. Wait for `[discover][success] endpoint=...` log line.
3. Confirm `endpoint.json` artifact in run summary.
4. Run API workflow; verify log shows using the resolved endpoint.

### Trigger (CLI)
```
gh workflow run banano-deploy.yml --ref 002-separate-out-the
gh run watch
gh workflow run api-deploy.yml --ref 002-separate-out-the
```

### Artifact Contract
`infra/akash-banano/endpoint.json`:
```json
{ "banano_rpc_endpoint": "node.example:12345" }
```
Local validation:
```
python3 scripts/infra/validate_endpoint.py $(jq -r '.banano_rpc_endpoint' infra/akash-banano/endpoint.json)
```
Exit code 0 indicates VALID.

### Redeploy Simulation
If provider port changes, re-run Banano then API workflows. Test locally:
```
bash scripts/infra/test_redeploy.sh
```

### Schema
`specs/002-separate-out-the/contracts/endpoint.schema.json` enforces structure (used in contract tests).

### Failure Modes
| Scenario | Symptom | Action |
|----------|---------|--------|
| Discovery timeout | `[discover][failure]` | Re-run Banano; inspect provider logs |
| Invalid candidate(s) | Repeated `[discover][candidate-invalid]` | Check port mapping / lease; redeploy |
| API early failure | Missing BANANO endpoint var | Ensure Banano workflow succeeded |

### Metrics (Planned)
Commented Prometheus gauge stub lives inside `discover_banano_endpoint.sh` for future enablement.