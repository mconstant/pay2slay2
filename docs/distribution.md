# Distribution & Upgrade Strategy (T050)

## Release Artifacts
- Container image (signed + SBOM attested)
- `openapi.json` contract snapshot
- Changelog entry summarizing security / schema changes

## Versioning
- Pre-1.0: minor increments for additive, patch for fixes.
- Post-1.0: SemVer. Breaking API change => major.

## Upgrade Flow
1. Pull new signed image.
2. Verify cosign signature & SBOM attestation.
3. Run DB migrations (if any) with backward-compatible additive changes first.
4. Roll out pods with maxUnavailable=1 (or blue/green) to maintain service.
5. Monitor metrics (payout errors, fortnite errors, accrual creation) & traces.

## Rollback
- Keep previous N signed image digests and SBOMs.
- If rollback triggered, redeploy previous digest without re-migrating (ensure migrations are additive & reversible if necessary).

## Configuration Management
- All secrets via environment/secret manager (never baked).
- Immutable config baked into image only for defaults; overrides via mounted files or env.

## Policy / Admission
- Future: Gate deploy if signature missing or SBOM scan fails policy.

## Operational Metrics to Watch
- `fortnite_errors_total`, `payout_attempts_total{result="failed"}`, `accrual_rows_created_total`, `admin_payout_retry_total{result}`.

## Data Migration Guidelines
- Add columns nullable with defaults; backfill asynchronously if needed.
- Avoid destructive schema changes without a multi-step migration (add -> copy -> switch -> drop).
