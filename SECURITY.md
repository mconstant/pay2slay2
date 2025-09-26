# Security Policy

## Supported Versions
Until first tagged release (>=1.0.0), all commits on the default branch receive security updates.

## Reporting a Vulnerability
Please open a private security advisory on GitHub (Security > Advisories > Report a vulnerability) or email security@example.org with details.

Provide:
- Affected endpoints / components
- Reproduction steps or PoC
- Impact assessment (confidentiality / integrity / availability)

We aim to acknowledge within 48h and provide a fix or mitigation timeline within 5 business days.

## Key Areas
- OAuth state & session HMAC
- Rate limiting (global & per-IP)
- Abuse heuristics & flags (kill rate spikes)
- Payout idempotency and retry safety

## Hardening Roadmap
- Expanded fuzz & replay tests (T055)
- Secrets management audit (T044)
- SBOM + provenance (T057, T058)

## Supply Chain & SBOM
The CI pipeline (T057) generates an SPDX JSON SBOM using Syft and scans it with Grype.

Gating policy:
- Build fails if any Critical severity vulnerability is detected (action: anchore/scan-action).
- SBOM artifact (sbom.spdx.json) is uploaded for each CI run for downstream tooling and provenance workflows (T058).

Provenance & Signing (T058):
- Deployment workflow builds container image and performs keyless Cosign signing.
- SBOM for the pushed image is generated (Syft) and attached as a Cosign attestation (predicate type spdxjson).
- This enables downstream verification (cosign verify --certificate-identity ... --certificate-oidc-issuer ...).

Planned enhancements (future):
- Allow temporary suppression via signed allowlist file checked into `security/allowlist.yaml` (not yet implemented).
- Policy controller / admission checks verifying SBOM + signature (OCI attestations) before deploy.

If a build fails due to a newly disclosed vulnerability, contributors should:
1. Review the failing Grype step logs.
2. Attempt to bump the impacted dependency (raise PR).
3. If immediate remediation is not possible, open a security advisory to discuss a temporary mitigation.

## Disclosure
Please practice coordinated disclosure; do not publicize issues before a patch release.

## OAuth State & Session Integrity
- OAuth state tokens are HMAC-signed opaque values containing entropy + issued timestamp.
- Single-use enforcement: consumed state is placed in an in-memory replay cache; any reuse returns 400.
- Tests cover: tamper, mismatch, replay, and legacy fallback path.

## Abuse Heuristics
- Current heuristic flags unusually high kill deltas in a sliding window (threshold driven).
- Flags written to `abuse_flags` table with severity for later review / potential automatic mitigation.
- Future work: probabilistic anomaly detection (EWMA / z-score) and rate-of-change models.

## Regional Privacy
- Region inferred heuristically (header + placeholder IP logic) and stored as short code only.
- No raw IP addresses persisted; region usage limited to aggregate metrics counters.
- Middleware can be disabled or replaced for stricter privacy requirements.

## Future Enhancements
- Differential privacy noise addition for public metrics exports.
- Signed vulnerability allowlist with expiration metadata.
- Formal threat model document (STRIDE) and security architecture diagram.
