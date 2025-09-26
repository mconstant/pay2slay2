# Performance Harness (T051)

Goal: Assess accrual + settlement throughput and latency under parallel simulated users.

## Scope
- Simulate N users with varying kill deltas.
- Measure time to process full accrual + settlement cycle.
- Capture p95 latency for critical endpoints (`/me/status`).

## Proposed Approach
1. Synthetic user generator seeds DB with users, wallet link, epic IDs.
2. Mock / patch `FortniteService.get_kills_since` to return controlled deltas.
3. Run accrual job concurrently with settlement job in loop for M iterations.
4. Record metrics snapshots (delta of counters) per iteration.

## Tooling
- Pytest performance marker + optional `--perf` flag.
- Reuse existing Prometheus client metrics (scrape programmatically).

## Metrics Collected
- Accruals created per minute.
- Payouts sent per minute.
- Error rates (fortnite_errors_total, payout_attempts_total{result="failed"}).
- CPU / memory (optional via psutil if enabled).

## Pass Criteria (MVP Targets)
- Accrual pipeline supports 500 users with < 2s end-to-end accrual+settlement latency (dry-run).
- No error spike >1% during sustained run.

## Future Enhancements
- Mixed workload with intermittent spikes (burst kills).
- Distributed harness using Locust or k6 driving HTTP for end-user endpoints.
