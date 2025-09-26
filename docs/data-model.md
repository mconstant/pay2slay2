# Data Model (T047)

Entity overview with key relationships and fields.

## Users (`users`)
- `discord_user_id` (unique) primary external identity.
- `epic_account_id` optional (populated after Yunite lookup).
- Cursor fields: `last_settled_kill_count`, `last_settlement_at` for idempotent accrual→settlement.
- Regional + abuse: `region_code`, `abuse_flags` (string/json placeholder).

## WalletLink (`wallet_links`)
- 1:N user -> wallets (currently one primary assumed).
- `verified` indicates ownership verification (future: signature or micro-transfer).

## VerificationRecord (`verification_records`)
- Historical audit of verification events; includes `source`, `status`, and optional detail.

## RewardAccrual (`reward_accruals`)
- Represents kills delta for a user in a minute bucket (`epoch_minute`).
- Unique constraint `(user_id, epoch_minute)` ensures idempotency.
- `settled`/`payout_id` link indicates whether included in a payout.

## Payout (`payouts`)
- Sum of a group of unsettled accruals at settlement time.
- Idempotency via SHA-256 over sorted accrual IDs (`idempotency_key`).
- Retry metadata: `attempt_count`, `first_attempt_at`, `last_attempt_at`.

## AdminAudit (`admin_audit`)
- Captures actions performed through admin endpoints.
- Optional `actor_email`, `target_type`, `target_id`, and summary/detail.

## AbuseFlag (`abuse_flags`)
- Structured flags for anomaly detection / heuristics (type, severity, detail).

## Relationships Diagram (conceptual)
```
User --< WalletLink
User --< VerificationRecord
User --< RewardAccrual -- Payout
User --< Payout
Payout --< RewardAccrual (backref)
User --< AbuseFlag
```

## Monetary Precision Strategy
- Current: Numeric(18,8) mapped to Python float (acceptable for MVP dry-run).
- Planned (T052): use `Decimal` context with quantization for exact arithmetic; enforce serialization via helper.

## Cursor Semantics
- `last_settled_kill_count` advanced ONLY after payout `status=sent` (idempotent crash recovery).
- Accrual uses previous settled cursor to compute delta from lifetime kills snapshot.

## Audit & Provenance
- Admin actions recorded; supply chain provenance via signed container + SBOM attestation.
