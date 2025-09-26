# Abuse Heuristics (T054)

This document describes the current and planned heuristics for detecting abnormal gameplay behavior.

## Current Implementation
- Threshold-based kill spike detection: if total kills within recent window (e.g. 15 minutes) exceeds configured `kill_rate_per_min * window` the user is flagged.
- Flags persisted in `abuse_flags` table with `flag_type=kill_rate_spike` and severity tiers (currently simple mapping based on multiplier over threshold).
- Region dimension captured for aggregate analysis (non-PII coarse code only).

## Data Sources
- RewardAccrual rows provide minute-bucketed kill deltas.
- Aggregation over configurable recent window (default 15m) inside `AbuseAnalyticsService`.

## Response Strategy (Future)
- Progressive responses: warn -> temporary suspension -> manual review.
- Dynamic threshold adaptation based on rolling percentiles per region/time-of-day.
- Integration with admin dashboard for reviewing flags and clearing false positives.

## Planned Heuristics
1. Negative or impossible deltas (already guarded by max(0) logic; log for investigation).
2. Sudden variance spikes (standard deviation over sliding window > multiplier).
3. Cross-account correlation (shared wallet / device fingerprint once available).
4. Rate of flag accrual (excessive flags over time) -> escalation.

## Privacy Considerations
- Only coarse region codes stored; no IP address persistence.
- Kill counts treated as operational metrics; could be aggregated for public stats with noise addition later.

## Operational Metrics
- `flagged_users_total` increments on new flags.
- Potential future: histogram of kill deltas for distribution analysis.

## Limitations
- Threshold static per deployment; may underfit or overfit across diverse player bases.
- Dry-run environment produces zero deltas; abuse system inert there.

## Future Work
- ML anomaly detection (unsupervised clustering or isolation forest) once dataset size sufficient.
- Admin UI to annotate flags (true/false positive) feeding back into adaptive model.
