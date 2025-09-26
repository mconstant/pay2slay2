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
