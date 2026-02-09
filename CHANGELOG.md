# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]
- Added immutable SHA tagging workflows (build, deploy, rollback) with digest verification guards (pre/post push & deploy-time) and rollback invariants.
- Introduced soft signature verification and structured image metadata artifact (image_sha, digest, signature_status, repository_type, arch, pre/post digests).
- Added deployment-time repository mapping & floating tag rejection.
- Added SBOM linkage and signature verification contract descriptors (placeholders pending full SBOM generation).
- **Akash deployment enhancements**:
  - Added automatic selection of cheapest audited Akash providers via SDL attributes (`audited: true`) and `signedBy` constraints.
  - Added UI URL extraction and output in deployment workflow with GitHub Actions step summary.
  - Added post-deployment health check validation with configurable retry logic (`scripts/infra/validate_health.py`).
  - Updated Terraform outputs to expose `api_url` and `api_endpoints` for easy access to deployed services.
  - Added comprehensive unit tests for health check validation script.

## [0.2.0] - 2025-09-25
### Added
- Split Akash deployments: separate Banano node and API Terraform stacks (`infra/akash-banano`, `infra/akash-api`).
- Banano discovery script with retry/backoff and structured logging (`scripts/infra/discover_banano_endpoint.sh`).
- Endpoint validation script (`scripts/infra/validate_endpoint.py`).
- Artifact contract `endpoint.json` + JSON Schema (`specs/002-separate-out-the/contracts/endpoint.schema.json`).
- GitHub Actions workflows: `banano-deploy.yml`, `api-deploy.yml` orchestrating artifact production/consumption.
- Redeploy simulation script (`scripts/infra/test_redeploy.sh`).
- Operations guide (`docs/operations/split-deployments.md`).
- Terraform linting workflow + `.tflint.hcl`.

### Changed
- Contract and integration tests updated to enforce endpoint artifact schema & validation.

### Security
- Ensured artifact contains no secrets; validation hardened with explicit host/port rules.

## [0.1.0] - 2025-xx-xx
- Initial release (baseline prior to split deployments feature).
