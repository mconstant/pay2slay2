# Research Notes (T046)

This document aggregates background research that informed implementation choices.

## Fortnite API
- Assumed endpoint: `/players/{epic_account_id}/stats` returning JSON with `lifetime_kills`.
- Real endpoints may require OAuth or service-to-service credentials; current design abstracts through `FortniteService` with configurable auth header name + scheme.
- Rate limits: Conservative local token bucket with adaptive tuning (T062) to avoid burst bans.

## Yunite
- Provides mapping Discord user -> Epic account ID.
- Reverification triggers idempotent refresh; stored in `VerificationRecord` with source.
- Guild membership tracked (boolean) for potential future gating / entitlements.

## Banano Node
- RPC methods used (planned/implemented): `account_balance`, `process` (send block), raw unit conversions.
- Dry-run mode avoids real RPC side-effects; tx_hash set to `dryrun`.
- Future: handle pow generation latency, block confirmation polling, and atomic batch payouts.

## Security & OAuth State
- HMAC state token includes entropy + timestamp; single-use replay cache prevents reuse.
- Tamper, mismatch, and replay tests enforce contract.

## Tracing / Observability
- OpenTelemetry instrumentation for HTTP client, DB, and custom spans in jobs.
- Exemplars optional via `PAY2SLAY_METRICS_EXEMPLARS=1` to link traces.

## Future Research
- Request signing for Fortnite upstream if required (HMAC or JWT scheme).
- Adaptive abuse heuristics leveraging time-series anomaly detection (e.g., EWMA + z-score) beyond static threshold.
- Multi-region wallet settlement latencies and operator wallet hot/cold separation.
