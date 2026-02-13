# API Reference

FastAPI backend. All sessions use HttpOnly, SameSite=Lax cookies.

## Authentication

| Cookie | Set by | Purpose |
|--------|--------|---------|
| `p2s_session` | `/auth/discord/callback` | User session |
| `p2s_admin` | `/admin/login` | Admin session |

## Health & Infrastructure

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthz` | Health check → `{ status: "ok" }` |
| GET | `/livez` | Liveness probe |
| GET | `/readyz` | Readiness probe |
| GET | `/metrics` | Prometheus metrics |

## Auth

| Method | Path | Description |
|--------|------|-------------|
| GET | `/auth/discord/login` | Redirects to Discord OAuth |
| GET | `/auth/discord/callback` | OAuth callback — sets `p2s_session` cookie |

## User Endpoints

Require `p2s_session` cookie.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/link/wallet` | Link a `ban_` address. Body: `{ "banano_address": "ban_..." }` |
| POST | `/me/reverify` | Re-trigger Yunite verification |
| GET | `/me/status` | Current user status, wallet, accrued rewards |
| GET | `/me/payouts` | User's payout history |
| GET | `/me/accruals` | User's accrual history |

## Public API

No authentication required.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/leaderboard` | Top players by kills and earnings |
| GET | `/api/feed` | Recent activity feed (payouts, accruals) |
| GET | `/api/donate-info` | Operator wallet address + balance for donations |
| GET | `/api/scheduler/countdown` | Seconds until next accrual/settlement cycle |
| GET | `/api/donations` | Donation progress, milestones, current multiplier |
| GET | `/config/product` | Public product config (app name, feature flags) |

## Admin Endpoints

Require `p2s_admin` cookie.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/admin/login` | Admin login. Body: `{ "email": "..." }` |
| POST | `/admin/reverify` | Force reverify a user. Body: `{ "discord_id": "..." }` |
| POST | `/admin/payouts/retry` | Retry a failed payout. Body: `{ "payout_id": 123 }` |
| GET | `/admin/audit` | Admin audit log |
| GET | `/admin/stats` | System statistics |
| GET | `/admin/health/extended` | Extended health check |
| POST | `/admin/config/operator-seed` | Set encrypted operator seed |
| GET | `/admin/config/operator-seed/status` | Check if operator seed is configured |
| GET | `/admin/scheduler/status` | Current scheduler state |
| POST | `/admin/scheduler/trigger` | Trigger scheduler run |
| POST | `/admin/scheduler/settle` | Trigger settlement only |
| GET | `/admin/scheduler/config` | Get scheduler config |
| POST | `/admin/scheduler/config` | Update scheduler config |
| GET | `/admin/payout/config` | Get payout config (ban_per_kill, caps) |
| POST | `/admin/payout/config` | Update payout config |

## Demo Endpoints

Available in development/demo mode.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/demo-login` | Login without Discord OAuth |
| POST | `/demo/seed` | Seed database with test data |
| POST | `/demo/run-scheduler` | Run scheduler cycle immediately |
| POST | `/demo/clear` | Clear all demo data |

## Debug

| Method | Path | Description |
|--------|------|-------------|
| GET | `/debug/yunite` | Test Yunite API connectivity |

## Notes

- **Dry-run mode** (`P2S_DRY_RUN=true`): skips external API calls and blockchain transfers.
- Sessions are HMAC-signed with `SESSION_SECRET` and include expiry.
- Error responses use standard HTTP status codes (400, 401, 403, 404).
