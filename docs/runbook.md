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

## 3. Metrics (Prometheus)
- http_requests_total / http_request_duration_seconds
- payouts_by_region_total / kills_by_region_total / flagged_users_total
- payout_amount_ban (histogram)
- payout_accrual_lag_minutes (gauge)
- payout_attempts_total (counter)
- payout_retry_latency_seconds (histogram)
- app_dry_run_mode (gauge)

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

_Last updated: 2025-09-25._
