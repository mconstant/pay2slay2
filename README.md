# Pay2Slay Faucet

![Immutable SHA Images](https://img.shields.io/badge/image%20tagging-immutable--sha-success?style=flat)
![Digest Guards](https://img.shields.io/badge/digest-pre%2Fpost%20verified-blue?style=flat)
![Rollback No-Build](https://img.shields.io/badge/rollback-no--build-important?style=flat)

Banano payouts for Fortnite kills. FastAPI backend, SQLAlchemy ORM, Alembic migrations, and a simple scheduler that settles rewards and (optionally) pays out via a Banano node.

## QuickStart

Get up and running in minutes:

```bash
# Clone the repository
git clone https://github.com/mconstant/pay2slay2.git
cd pay2slay2

# Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e '.[dev]'

# Run the API server (in one terminal)
make api

# Run the scheduler (in another terminal)
make scheduler
```

The API will be available at http://localhost:8000 and the scheduler will run with a Prometheus metrics server on port 8001.

For more detailed setup instructions, see `docs/quickstart.md`.

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
### Digest Integrity Guards (T057)
Two layers enforce image immutability and provenance alignment:
1. Build-time pre/post digest verification (scripts/ci/check_digest_post_push.py) ensures the pushed registry digest matches the locally built image (FR-009).
2. Deployment-time guard (scripts/ci/check_existing_digest.py) validates repository mapping and (future: live digest) before applying an immutable SHA reference (FR-004, FR-016).

Rollback uses a dedicated workflow (`api-rollback.yml`) that never rebuilds (FR-013). All deploys reference full 40-char commit SHAs; floating tags are rejected.

### Metrics (Image Supply Chain)
The observability module exposes counters (T022, T060):
- `image_build_total{repository_type}` increments once per successful build (canonical vs staging).
- `rollback_total{repository_type}` increments when a rollback is applied.
If Prometheus is available, counters export via the default registry; tests read in-process mirrors for deterministic assertions.

### Immutable Tag Badge
![Immutable SHA Images](https://img.shields.io/badge/image%20tagging-immutable--sha-success?style=flat)


- Docker (local): `docker build -t pay2slay2:dev .` then `docker-compose up --build`
- CI: GitHub Actions workflow `.github/workflows/ci.yml` runs lint, type, tests, SBOM/scan.
- Akash (Terraform):
   - Prereqs: set `AKASH_MNEMONIC` secret in GitHub, set repository variable `AKASH_ACCOUNT_ADDRESS` (your `akash1...` wallet address), and use `deploy-akash` workflow dispatch with `image_tag`.
   - Infra code under `infra/akash` uses the Akash Terraform provider to submit a simple deployment.
   - Container image is built & pushed to GHCR automatically by the `deploy-akash` workflow.
   - **Provider Selection**: The deployment automatically selects the cheapest audited Akash provider by specifying `audited: true` in the SDL placement attributes and restricting to signed providers.
   - **Deployment Output**: The workflow outputs the deployed UI URL in the GitHub Actions step summary and validates the health check endpoint post-deployment.
   - **Health Check**: After deployment, the workflow automatically validates the `/healthz` endpoint with retry logic to ensure the service is running correctly.
   - NOTE: Workflow must exist on the target branch (use `REF=<branch>` with `make deploy-akash` if deploying a non-default branch).
   - Cert Rotation: use either the GitHub UI (Actions → `rotate-akash-cert`) or the Makefile target `make rotate-akash-cert` to mint a new Akash client certificate and automatically update `AKASH_CERT` (secret) and `AKASH_CERT_ID` (variable). Requires an existing `AKASH_MNEMONIC` repo secret and (for secret/variable mutation via CLI) a `GH_ADMIN_TOKEN` repo secret (classic PAT with `repo` + `actions:write`).

#### Rotate Akash Certificate (Makefile Usage)

The Akash client certificate periodically needs rotation. This project provides a workflow plus a convenience Makefile target to trigger it from your local shell via the GitHub CLI.

Prerequisites:
1. Installed GitHub CLI (`gh auth login`).
2. Repo secret `AKASH_MNEMONIC` (24-word wallet mnemonic).
3. Repo secret `GH_PAT` (classic Personal Access Token) with at minimum the `repo` scope (for private repos) or `public_repo` (if public). This enables the rotation workflow to update repository secrets/variables reliably. (If you already created an older `GH_ADMIN_TOKEN`, you can keep using it, but new setups should prefer `GH_PAT`.)

Default invocation (uses defaults: key `deployer`, network mainnet, chain `akashnet-2`, method `cert-generation` with fallback to `openssl`):

```
make rotate-akash-cert
```

Override inputs (they map 1:1 to workflow_dispatch inputs):

```
# Use a different key name already imported by the Akash CLI action
make rotate-akash-cert KEY_NAME=mykey

# Force OpenSSL fallback method directly
make rotate-akash-cert ROTATE_METHOD=openssl

# Target alternative network / chain (example: edgenet values shown illustratively)
make rotate-akash-cert AKASH_NETWORK=https://rpc.edgenet.akash.network:443 AKASH_CHAIN_ID=edgenet-2
```

Parameters:
- `KEY_NAME` → wallet key name to use inside the workflow (default `deployer`).
- `ROTATE_METHOD` → `cert-generation` attempts Akash CLI cert generation; if it fails (or you set `openssl`) a self-signed placeholder cert is produced.
- `AKASH_NETWORK` → RPC endpoint passed as `--node` (default `https://rpc.akash.network:443`).
- `AKASH_CHAIN_ID` → Chain ID (default `akashnet-2`).

What happens:
1. The Makefile target dispatches the `rotate-akash-cert` workflow with your overrides.
2. Workflow sets up the Akash CLI and tries to generate a client certificate.
3. On success (or fallback), it updates:
   - Secret `AKASH_CERT` (PEM content)
   - Variable `AKASH_CERT_ID` (timestamped identifier)
4. A short run summary appears in the workflow run page; you can also view it via:

```
gh run list --workflow rotate-akash-cert --limit 5
gh run view <run-id>
```

Verification:
1. GitHub → Settings → Secrets and variables → Actions → confirm updated timestamp for `AKASH_CERT`.
2. Check `AKASH_CERT_ID` under variables for the new ID (format `cert-YYYYMMDD-HHMMSS`).
3. (Optional) If your deploy workflow relies on the cert, re-run `make deploy-akash` to pick up the rotated secret.

Failure Modes & Tips:
- Missing `GH_ADMIN_TOKEN`: workflow may not have permission to update the secret—add it and re-run.
- CLI generation command changes: if the Akash CLI subcommand differs in a future release, rotation may fall back to `openssl` (placeholder). Adjust the workflow script accordingly.
- OpenSSL fallback is a stand-in: replace with proper chain-issued client cert flow before production usage.

Security Considerations:
- The mnemonic never leaves GitHub Actions (provided only as an injected secret to the setup step).
- Rotate credentials after suspected compromise; revoke unused keys in your Akash environment.

#### Creating a GitHub Personal Access Token (Classic) as `GH_PAT`

Use this PAT so the rotation workflow can mutate repository secrets/variables. The default `GITHUB_TOKEN` often lacks permission to set secrets.

1. Navigate to GitHub → Settings (your user, not the repo) → Developer settings → Personal access tokens → Tokens (classic).
2. Click "Generate new token (classic)".
3. Give it a descriptive name, e.g. `pay2slay-rotate-cert`.
4. Set an expiration (recommended: 30–90 days). Calendar a reminder to rotate.
5. Select scopes:
   - Private repo: check `repo` (full). (If the repository is public only, `public_repo` is sufficient.)
   - You do NOT need `admin:org` or other broad scopes.
6. Generate the token and copy it (you will not see it again).
7. Store it in the repository:
   - Repo → Settings → Secrets and variables → Actions → New repository secret.
   - Name: `GH_PAT`
   - Value: (paste the token)
   - Save.
8. (Optional) Locally verify you can auth with it (do NOT store permanently in shell history):
   ```bash
   echo "<token>" | gh auth login --with-token
   gh auth status
   ```
9. Re-run `make rotate-akash-cert` and confirm the workflow updates `AKASH_CERT` / `AKASH_CERT_ID`.

Rotation / Revocation:
- Before expiry, generate a new PAT, update the `GH_PAT` secret, then delete the old token.
- If leaked, delete the token immediately and replace the secret.

### Akash Deployment Guide (Cosmos Wallet via Keplr)

1. Install Keplr:
   - Browser extension: https://www.keplr.app/ (Chrome/Brave/Firefox)
   - Create a new wallet (24-word mnemonic). Choose a strong password. Store the mnemonic securely (never commit or screenshot it).

2. Add / Enable Akash Network in Keplr:
   - Open Keplr → Select "Add more chains" → Search for "Akash" → Enable.
   - Confirm you see an `akash1...` address.

3. Fund Your Akash Wallet:
   - Option A (Centralized Exchange Fiat On-Ramp):
     1. Buy ATOM (Cosmos Hub) on an exchange (e.g., Coinbase / Kraken / Binance) with fiat.
     2. Withdraw ATOM to your Keplr Cosmos Hub (ATOM) address.
     3. Use an IBC transfer to move ATOM to Akash (Keplr: Cosmos Hub → Transfer → Select Akash → amount → send).
     4. On Akash, use an on-chain swap (e.g., https://app.osmosis.zone) to convert ATOM → AKT if needed (Keplr will auto prompt to connect). Ensure you have some AKT for deployment fees.
   - Option B (Direct AKT Purchase):
     - Some exchanges list AKT directly; withdraw AKT to your `akash1...` Keplr address.
   - Goal: Have at least a few AKT (plus a little ATOM or AKT dust for fees) for initial deployment.

4. (Optional) Use Fiat→USDC→ATOM Flow:
   - Buy USDC with fiat → Swap to ATOM on exchange → Withdraw to Keplr → IBC to Akash → Swap to AKT.

5. Set GitHub Secret `AKASH_MNEMONIC`:
   - Go to GitHub repo → Settings → Secrets and variables → Actions → New repository secret.
   - Name: `AKASH_MNEMONIC`
   - Value: Your 24-word mnemonic (space separated). DO NOT quote it; ensure there are exactly 24 words.
   - Save.

6. Set Repository Variable `AKASH_ACCOUNT_ADDRESS`:
   - GitHub repo → Settings → Secrets and variables → Actions → Variables → New variable.
   - Name: `AKASH_ACCOUNT_ADDRESS`
   - Value: Your Keplr (or other wallet) Akash address (`akash1...`).
   - This is required so Terraform provider authentication (account address) is wired into the `deploy-akash` workflow via `TF_VAR_akash_account_address`.

7. Trigger Deployment:
   - Build & push via workflow dispatch: GitHub → Actions → `deploy-akash` → Run workflow → provide `image_tag` (e.g., `latest`) and `akash_network` (default OK).
   - Or locally via GitHub CLI (after push):
     - `make deploy-akash IMAGE_TAG=latest AKASH_NETWORK=https://rpc.akash.network:443`

8. Confirm Deployment:
   - Terraform step now outputs: deployment ID, image, and `services` (including `uris`, `ips`, replica counts).  Use the first URI (if present) to reach the API.
   - Fallback: check Keplr → Transactions or an Akash block explorer for the deployment create.

9. Rotating / Revoking Mnemonic:
   - If compromised: create a new wallet, fund it, update the secret, re-run deployment; revoke old by emptying funds.

Security Notes:
 - Never commit keys or mnemonics.
 - Use a hardware wallet for larger AKT balances.
 - Consider splitting funds (operational vs vault).


## Notes
- Dry-run mode short-circuits external calls and assumes a healthy operator balance; use for local testing.
- Alembic migrations are initialized; SQLite dev DB is created automatically on app startup.
