# SBOM & Vulnerability Gating (T057)

The CI workflow produces an SPDX JSON Software Bill of Materials (SBOM) using Syft and immediately scans dependencies with Grype.

## What Happens in CI
1. `anchore/sbom-action` creates `sbom.spdx.json` and uploads it as an artifact.
2. `anchore/scan-action` runs with `severity-cutoff: critical` and `fail-build: true`.
3. Any Critical vulnerability causes the CI job to fail (early signal before deploy).

## Rationale
Early SBOM + gating reduces exposure window for newly disclosed Critical issues and provides traceability for future provenance signing (see T058).

## Extending
Future tasks (T058) will attach provenance and (optional) cosign attestations referencing the SBOM digest.

Proposed enhancements (not yet implemented):
- Allowlist file for temporarily accepted findings.
- PR comment bot summarizing new vs baseline vulnerabilities.

## Local Reproduction
Generate an SBOM locally:
```
pip install syft grype  # or use container images
syft . -o spdx-json > sbom.spdx.json
grype sbom:sbom.spdx.json --fail-on critical
```

## Troubleshooting
- If CI fails suddenly without dependency changes, a base image or transitive dep likely published a CVE. Inspect the scan log.
- Pin and upgrade the vulnerable dependency when possible; otherwise consider patching or temporary allowlist (future feature).

## References
- Syft: https://github.com/anchore/syft
- Grype: https://github.com/anchore/grype
