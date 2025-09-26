# Image Provenance & Signing (T058)

The deploy workflow performs:

1. Container image build & push to GHCR.
2. SBOM generation for the image using Syft (spdx-json output).
3. Keyless Cosign signing of the image (OIDC token from GitHub Actions).
4. Cosign attestation attaching the SBOM predicate (type: spdxjson).

## Verifying Locally
```
cosign verify ghcr.io/<org>/<repo>:<tag>
cosign verify-attestation --type spdxjson ghcr.io/<org>/<repo>:<tag>
```

## Notes
- Keyless signing ties signature to GitHub workflow identity (OIDC issuer: token.actions.githubusercontent.com).
- SBOM attestation allows downstream scanners / policy engines to enforce dependency policies at deploy/runtime.
- Future: integrate policy admission (e.g., kyverno, cosign verify at cluster gate) and allowlist handling.
