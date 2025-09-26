# Research: Split Akash Deployments

Date: 2025-09-26  
Feature: Split Akash Deployments (Banano Node & API Separation)  
Branch: 002-separate-out-the

## Decision Log

### 1. Deployment Separation Strategy
- Decision: Two Terraform directories (`infra/akash-banano`, `infra/akash-api`) each with its own Akash SDL.
- Rationale: Enables independent lifecycle operations, clearer blast radius, simpler variable surface.
- Alternatives:
  - Single monolithic Terraform module with conditional resources: rejected (re-apply risk, slower iterations).
  - Helm-like templating overlay: not needed; complexity > benefit.

### 2. Endpoint Discovery Mechanism
- Decision: Parse Terraform outputs for forwarded port mapping + retry loop (5s,10s,20s,40s) until external port for internal 7072 appears.
- Rationale: Deterministic bounded wait (≈75s max) with minimal tooling.
- Alternatives:
  - Long unbounded polling: rejected (uncapped CI time cost).
  - Event-based callback (webhook): not available in Akash workflow context.

### 3. Artifact Format
- Decision: `endpoint.json` at workflow artifact root: `{ "banano_rpc_endpoint": "<host>:<port>" }`.
- Rationale: Simplest schema; trivial to parse with `jq` or Python; future extensibility by adding new keys.
- Alternatives:
  - Plain text file: harder to extend safely.
  - Terraform state parsing during API workflow: couples workflows to internal state format.

### 4. Validation Rules
- Decision: Regex host `[a-z0-9.-]+` (must not start with dot/hyphen after normalization, length <= 253); numeric port 1024–65535.
- Rationale: Basic hygiene; prevents empty or reserved ports.
- Alternatives:
  - Full RFC 1123 DNS validation: overkill.
  - Accept anything and rely on runtime failure: poor operator feedback.

### 5. Failure Semantics
- Decision: Hard fail (exit 1) if endpoint not resolved after retries; produce no artifact/output.
- Rationale: Avoids stale or placeholder data propagating and misconfiguring API.
- Alternatives:
  - Emit empty value: risk of silent mis-wire.
  - Extend retries beyond 75s: diminishing returns; operator can re-run.

### 6. Security Posture
- Decision: Treat endpoint as non-secret; no signing initially; document future signing (cosign or checksum) as enhancement.
- Rationale: Low sensitivity; integrity risk manageable by logs + manual verify.
- Alternatives:
  - Immediate artifact signing: adds complexity/time now with low marginal benefit.

### 7. Tooling for Terraform Validation
- Decision: Skip tflint / checkov integration for first cut; rely on small module simplicity & peer review.
- Rationale: Speed; limited scope.
- Alternatives:
  - Add tflint now: increases PR surface; can be incremental.

### 8. Testing Approach
- Decision: Introduce contract tests for `endpoint.json` shape and a simulated API workflow step that fails when artifact absent or invalid.
- Rationale: Ensures FR-005 / FR-006 / FR-012 are verifiable.
- Alternatives:
  - Rely solely on manual CI run checks: brittle.

### 9. Observability
- Decision: Mandatory log: `Banano RPC endpoint resolved: <value>`; on failure log final attempt summary.
- Rationale: Explicit operator feedback aids incident triage.
- Alternatives:
  - Silent failure with generic exit: poor ergonomics.

### 10. Future Enhancements (Not In Scope)
- Node endpoint health probe & identity pinning.
- Artifact signing & verification.
- Multi-environment matrix (staging/prod) artifact namespace segregation.
- Automatic API re-deploy trigger on Banano re-deploy.

## Open Items (None Blocking)
- Consider tflint adoption post initial merge.
- Decide later if we need environment tagging in artifact filename (`endpoint-<env>.json`).

## Summary
All clarifications resolved; no outstanding blockers. Ready for Phase 1 design & contracts.
