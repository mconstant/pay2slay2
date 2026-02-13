# Pay2Slay Production Runbook (T068)

## Overview
This document summarizes operational procedures, alert responses, and routine maintenance tasks for the Pay2Slay faucet service.

## 1. Environment & Configuration
- dry_run flag (integrations.dry_run): must be false in production payouts environment.
- SESSION_SECRET: MUST be non-default; startup guard fails if 'dev-secret'.
- Banano node_rpc: Should be a production node (not localhost) when dry_run=false.
- Alembic migrations: Run `alembic upgrade head` before scaling application pods.

## 2. Core Services
- Accrual job: Periodic kill accrual; monitor for lag > 2 cycles.
- Settlement & payout: Use Decimal(18,8) amounts; payout idempotency key prevents duplicates.
- HODL balance scan: Runs every accrual cycle. Scans all users with a linked Solana wallet, fetches on-chain $JPMT balance from Solana RPC, and updates their tier/multiplier. Controlled by `hodl_boost_enabled` in `configs/payout.yaml`.

## 3. Metrics (Prometheus)
- http_requests_total / http_request_duration_seconds
- payouts_by_region_total / kills_by_region_total / flagged_users_total
- payout_amount_ban (histogram)
- payout_accrual_lag_minutes (gauge)
- payout_attempts_total (counter)
- payout_retry_latency_seconds (histogram)
- app_dry_run_mode (gauge)
- hodl_scan_users_total / hodl_scan_updated_total (HODL scan counters)

## 4. Alerting Suggestions
| Condition | Threshold | Action |
|-----------|-----------|--------|
| app_dry_run_mode == 1 in prod | >5m | Validate deployment config; block payouts until false |
| payout_accrual_lag_minutes | >30 | Investigate scheduler health / DB contention |
| payout_attempts_total{result="failed"} / sum(payout_attempts_total) | >5% over 15m | Inspect Banano node / balance |
| http_request_duration_seconds_p95 | >750ms sustained 10m | Profile DB queries / external calls |
| flagged_users_total increase | Sudden spike (>X/h) | Review abuse heuristics / false positives |

## 5. Operational Procedures
### Deployment
1. Build & sign image (cosign).  
2. Apply migrations.  
3. Deploy new version (blue/green or rolling).  
4. Verify health endpoints and key metrics (payout_amount_ban histogram updates).

### Rollback
1. Scale down current deployment.  
2. Deploy previous signed image.  
3. Validate metrics & logs; consider DB schema compatibility (additive migrations preferred).

### Secret Rotation
1. Generate new SESSION_SECRET.  
2. Inject into deployment environment.  
3. Restart API pods (sessions invalidated gracefully).  

## 6. Balance & Safety
- Use has_min_balance check pre-send (10% margin).  
- Monitor operator wallet externally; top-up strategy documented separately.

## 7. Data Retention (Preview - T070)
- Accruals & payouts older than N days to be pruned (placeholder command added).

## 8. Incident Response
1. Declare severity (S1 user payout corruption, S2 prolonged lag, S3 degraded latency).  
2. Capture logs with trace IDs (structured logging).  
3. Export recent metrics snapshot.  
4. Mitigate (enable dry_run mode, halt scheduler, or scale DB).  

## 9. Future Enhancements
- Automated pruning script scheduling.  
- Wallet balance anomaly detection.  
- Advanced kill delta reconciliation story.

## 10. HODL Boost Operations
- **Config:** `configs/payout.yaml` — `hodl_boost_enabled`, `hodl_boost_token_ca`, `hodl_boost_solana_rpc`
- **Scanner:** Runs in the scheduler loop every accrual cycle (`src/jobs/hodl_scan.py`). Fetches on-chain $JPMT balances for all users with linked Solana wallets and updates their tier.
- **Manual verify:** Users can also verify on-demand via Dashboard → Verify $JPMT Holdings.
- **Tiers:** No Bag (1.0×) → Bronze 10K (1.10×) → Silver 100K (1.20×) → Gold 1M (1.35×) → Diamond 10M (1.50×) → Whale 100M (1.75×).
- **RPC rate limits:** Default public Solana RPC has rate limits. For large user bases, configure a dedicated RPC endpoint via `SOLANA_RPC_URL` env var.
- **Disabling:** Set `hodl_boost_enabled: false` in `payout.yaml` or at runtime via scheduler overrides.

_Last updated: 2026-02-13._
