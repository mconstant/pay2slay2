# Distribution & Upgrade Strategy

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

## Immutable Tagging & Rollback (T023, T046)
All production deployments reference the full 40‑character git commit SHA tag (FR-002, FR-005). Mutable tags like `latest`, `main`, `stable` are rejected at deploy-time (T029) and never used in workflows.

Digest Integrity Guards (FR-009):
1. Build-time pre/post digest verification (T041/T042) records the local image digest before push and re-fetches registry digest after push; mismatch → build fails.
2. Deployment-time guard (T028) re-loads recorded metadata and enforces repository mapping (canonical for main, staging otherwise) before applying a deployment; intended future enhancement: real registry query.

Rollback (FR-007, FR-013):
- Dedicated rollback workflow (`api-rollback.yml`, T018) accepts `target_sha` and re-points the deployment without rebuilding; integration tests assert no build steps and digest stability (T021, T045).
- Invariants (T044): must not build, must not alter digest, must reference existing tag; enforced by contract & integration tests.

Signature Escalation Path (FR-014):
- Current: soft verify only (missing/invalid signatures log `signature_status=unverified` with reason, workflow continues).
- Future: Once >90% of deployed SHAs are signed, promote to mandatory verification failing on `unverified`.

SBOM Linkage (FR-008, T031/T047):
- Placeholder SBOM linkage steps exist in build & deploy workflows; contract `sbom-linkage.yaml` documents required invariants. Full SBOM generation to be integrated in a later iteration.

Short Tag Parity (T049):
- 12‑char short tag is published alongside full SHA; parity test ensures both resolve to the same digest. Primary operational tag remains the full SHA.

Single-Arch Constraint (FR-015, T050):
- Images are built `--platform linux/amd64` only. Multi-arch deferred to preserve build determinism & speed.

Structured Log Fields (T006, T054):
- Build metadata JSON & logs include: image_sha, short_sha, image_digest, repository, repository_type, arch, signature_status, signature_reason, build_duration_sec, pre/post push digests, digest_verification.

Metrics (T022, T052):
- Counters: `image_build_total{repository_type}` and `rollback_total{repository_type}` emitted via observability helpers; tests assert increments.

Performance (Targets):
- Build p95 < 10m; Deploy p95 < 5m (representational tests T011, upcoming T033/T058 for deploy/rollback durations).

## Configuration Management
- All secrets via environment/secret manager (never baked).
- Immutable config baked into image only for defaults; overrides via mounted files or env.

## Policy / Admission
- Future: Gate deploy if signature missing or SBOM scan fails policy.

## Operational Metrics to Watch
- `fortnite_errors_total`, `payout_attempts_total{result="failed"}`, `accrual_rows_created_total`, `admin_payout_retry_total{result}`.

## Data Migration Guidelines

## References
- spec: `specs/003-tag-api-container/spec.md`
- contracts: digest verification (T036), sbom linkage (T047), signature verification (T048)
- tests asserting invariants: T037–T039, T041–T045, T049–T054

- Add columns nullable with defaults; backfill asynchronously if needed.
- Avoid destructive schema changes without a multi-step migration (add -> copy -> switch -> drop).
