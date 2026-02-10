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

## Deploy (Akash Network)

The project deploys as a single container on Akash Network. The container runs both the API server and the scheduler. Banano transactions use the public Kalium RPC (no self-hosted node required).

### Prerequisites

1. An Akash wallet with AKT funds (see [Wallet Setup](#akash-wallet-setup-keplr) below)
2. GitHub CLI installed (`gh auth login`)
3. A domain name with DNS you control (e.g. `pay2slay.cc`)

### GitHub Secrets (required)

Set these in your repo: Settings > Secrets and variables > Actions > Secrets.

| Secret | Description |
|--------|-------------|
| `AKASH_MNEMONIC` | 24-word Akash wallet mnemonic |
| `AKASH_CERT` | Akash TLS client cert (PEM). Generate via `rotate-akash-cert` workflow |
| `GH_PAT` | GitHub PAT (classic) with `repo` scope — for TF state artifact and cert rotation |
| `SESSION_SECRET` | Long random string for session signing (e.g. `openssl rand -hex 32`) |
| `DISCORD_CLIENT_ID` | Discord OAuth application client ID |
| `DISCORD_CLIENT_SECRET` | Discord OAuth application client secret |
| `DISCORD_REDIRECT_URI` | Full callback URL, e.g. `https://pay2slay.cc/auth/discord/callback` |
| `YUNITE_API_KEY` | Yunite API key for Epic account resolution |
| `FORTNITE_API_KEY` | fortnite-api.com API key |

### GitHub Variables (required)

Set these in: Settings > Secrets and variables > Actions > Variables.

| Variable | Description | Example |
|----------|-------------|---------|
| `AKASH_ACCOUNT_ADDRESS` | Your `akash1...` wallet address | `akash1abc...xyz` |
| `AKASH_CERT_ID` | Cert identifier (set by rotate-cert workflow) | `cert-20250101-120000` |
| `YUNITE_GUILD_ID` | Discord server ID for Yunite lookups | `123456789` |
| `BANANO_NODE_RPC` | Banano RPC endpoint (default: Kalium) | `https://kaliumapi.appditto.com/api` |
| `P2S_OPERATOR_ACCOUNT` | Operator Banano address for balance checks | `ban_3geytkg...` |
| `MIN_OPERATOR_BALANCE_BAN` | Min BAN balance to continue payouts (default: `50`) | `50` |
| `ADMIN_DISCORD_USERNAMES` | Comma-separated Discord usernames for admin access | `mconstant` |

### Discord App Configuration

In the Discord Developer Portal, set the OAuth2 redirect URI to match your domain:
```
https://yourdomain.com/auth/discord/callback
```

### Trigger Deployment

Via GitHub CLI:
```bash
gh workflow run deploy-akash.yml \
  -f domain_name=pay2slay.cc \
  -f image_tag=latest
```

Or via GitHub UI: Actions > `deploy-akash` > Run workflow.

### After Deployment — DNS Setup

The workflow summary will show the Akash provider hostname. Point your domain to it:
```
pay2slay.cc  CNAME  <provider-hostname-from-workflow-output>
```
The Akash provider handles TLS via Let's Encrypt automatically.

### Docker (local)

```bash
docker build -t pay2slay:dev .
docker run -p 8000:8000 --env-file .env pay2slay:dev
```

The container runs both the API (port 8000) and scheduler as background process. Set `PAY2SLAY_AUTO_MIGRATE=1` to run Alembic migrations on startup.

### Akash Wallet Setup (Keplr)

1. Install [Keplr](https://www.keplr.app/) browser extension and create a wallet (save the 24-word mnemonic securely).
2. Enable Akash Network in Keplr (Add chains > search "Akash").
3. Fund your wallet with AKT:
   - Buy ATOM on an exchange > withdraw to Keplr > IBC transfer to Akash > swap to AKT on [Osmosis](https://app.osmosis.zone), or
   - Buy AKT directly on an exchange that lists it > withdraw to your `akash1...` address.
4. Set the `AKASH_MNEMONIC` secret and `AKASH_ACCOUNT_ADDRESS` variable in GitHub (see tables above).

### Certificate Rotation

Akash client certs need periodic rotation:
```bash
make rotate-akash-cert
```
This dispatches the `rotate-akash-cert` workflow which updates `AKASH_CERT` (secret) and `AKASH_CERT_ID` (variable). Requires `AKASH_MNEMONIC` and `GH_PAT`.

### Creating a `GH_PAT`

1. GitHub > Settings (user) > Developer settings > Personal access tokens > Tokens (classic).
2. Generate new token with `repo` scope (or `public_repo` if repo is public).
3. Store as repository secret named `GH_PAT`.

### Supply Chain Security

- Images are signed with Cosign (keyless/Sigstore) and attested with SBOM (Syft/SPDX).
- Build-time digest verification ensures pushed image matches local build.
- Rollback workflow (`api-rollback.yml`) reuses existing images without rebuild.


## Notes
- Dry-run mode short-circuits external calls and assumes a healthy operator balance; use for local testing.
- Alembic migrations are initialized; SQLite dev DB is created automatically on app startup.
