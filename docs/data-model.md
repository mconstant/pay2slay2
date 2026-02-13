# Data Model

Entity overview with key relationships and fields.

## Users (`users`)
- `discord_user_id` (unique) — primary external identity.
- `epic_account_id` — populated after Yunite lookup.
- Cursor fields: `last_settled_kill_count`, `last_settlement_at` for idempotent accrual→settlement.
- `region_code`, `abuse_flags` for analytics and abuse detection.

## WalletLink (`wallet_links`)
- 1:N user → wallets (one primary assumed).
- `verified` indicates ownership verification.

## VerificationRecord (`verification_records`)
- Audit trail of verification events: `source`, `status`, detail.

## RewardAccrual (`reward_accruals`)
- Kill delta for a user in a minute bucket (`epoch_minute`).
- Unique constraint `(user_id, epoch_minute)` ensures idempotency.
- `settled`/`payout_id` links to payout when included.

## Payout (`payouts`)
- Aggregated unsettled accruals at settlement time.
- Idempotency via SHA-256 over sorted accrual IDs (`idempotency_key`).
- Retry metadata: `attempt_count`, `first_attempt_at`, `last_attempt_at`.
- Status: `pending` → `sent` or `failed`.

## AdminAudit (`admin_audit`)
- Actions performed through admin endpoints.
- `actor_email`, `target_type`, `target_id`, summary/detail.

## AbuseFlag (`abuse_flags`)
- Structured anomaly flags: `flag_type`, `severity`, `detail`.

## SecureConfig (`secure_config`)
- Encrypted key-value store for sensitive runtime config (e.g., operator seed).
- Fields: `key`, `encrypted_value`, `set_by`, `description`.

## DonationLedger (`donation_ledger`)
- Tracks incoming BAN donations to the operator wallet.
- Fields: `amount_ban`, `blocks_received`, `source`, `note`.
- Drives milestone progression and payout multipliers.

## Relationships

```
User ──< WalletLink
User ──< VerificationRecord
User ──< RewardAccrual ──> Payout
User ──< Payout
User ──< AbuseFlag
Payout ──< RewardAccrual (backref)
```

## Monetary Precision
- Numeric(18,8) mapped to Python `Decimal` for exact arithmetic.
- Serialization via helper to avoid floating-point drift.

## Cursor Semantics
- `last_settled_kill_count` advances only after payout `status=sent` (crash-safe).
- Accrual computes delta from lifetime kills snapshot against settled cursor.
