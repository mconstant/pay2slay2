# API Overview

This project exposes a small FastAPI backend with user and admin endpoints. Cookies are used for sessions.

## Cookies
- `p2s_session` (HttpOnly, SameSite=Lax): user session issued by `/auth/discord/callback`.
- `p2s_admin` (HttpOnly, SameSite=Lax): admin session issued by `/admin/login`.

## User Endpoints
- POST `/auth/discord/callback?state=...&code=...`
  - Side effects: sets `p2s_session` cookie.
  - Response 200: `{ discord_user_id, discord_username, epic_account_id }`
  - Errors: 400 (missing params), 403 (not in guild / missing Yunite mapping).

- POST `/link/wallet`
  - Auth: requires `p2s_session` cookie.
  - Body: `{ "banano_address": "ban_..." }`
  - Response 200/202: `{ linked: true, address: "..." }`
  - Errors: 400 (invalid address), 401 (unauthorized).

- GET `/me/status`
  - Auth: requires `p2s_session` cookie.
  - Response 200: `{ linked, last_verified_at, last_verified_status, last_verified_source, accrued_rewards_ban }`
  - Errors: 401 (unauthorized).

## Admin Endpoints
- POST `/admin/login`
  - Body: `{ "email": "admin@example.com" }`
  - Requires an active AdminUser; side effects: sets `p2s_admin` cookie.
  - Response 200: `{ email }`
  - Errors: 400 (missing), 401 (unauthorized).

- POST `/admin/reverify`
  - Auth: requires `p2s_admin` cookie.
  - Body: `{ "discord_id": "..." }`
  - Response 202-like: `{ status: "accepted", discord_id }` (stubbed behavior).
  - Errors: 401 (unauthorized), 404 (user not found).

- POST `/admin/payouts/retry`
  - Auth: requires `p2s_admin` cookie.
  - Body: `{ "payout_id": 123 }`
  - Response 202-like: `{ status: "accepted", payout_id }` (stubbed behavior).
  - Errors: 401 (unauthorized), 404 (payout not found).

## Health
- GET `/healthz` → `{ status: "ok" }`

## Notes
- Dry-run mode avoids external network calls and blockchain transfers; see `P2S_DRY_RUN`.
- Sessions are HMAC-signed with `SESSION_SECRET` and include expiry.
- Error responses follow standard HTTP codes as noted above.
