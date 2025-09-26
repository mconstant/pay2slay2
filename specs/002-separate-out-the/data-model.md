# Data Model: Split Akash Deployments

Scope: Logical (deployment-level) entities and artifacts introduced by feature.

## Entities

### 1. Banano Deployment
- Fields:
  - deployment_id: string (Terraform/Akash output)
  - banano_rpc_endpoint: string (`<host>:<port>`; produced only on success)
- Invariants:
  - `banano_rpc_endpoint` absent if resolution failed (never empty string)
  - Port corresponds to internal 7072 mapping

### 2. Endpoint Artifact
- File: `endpoint.json`
- Schema:
  ```json
  { "banano_rpc_endpoint": "<host>:<port>" }
  ```
- Validation:
  - host regex: `^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$` (simplified RFC 1123 subset) OR IPv4 `^([0-9]{1,3}\.){3}[0-9]{1,3}$`
  - port: integer 1024–65535

### 3. API Deployment Input
- Field:
  - banano_rpc_endpoint: string (required unless alternative override variable provided in future)
- Constraints:
  - MUST pass same validation rules as artifact schema

## Relationships
- Banano Deployment -> Endpoint Artifact (1:1 on success)
- Endpoint Artifact -> API Deployment Input (consumed exactly once per API deploy; may be reused until Banano redeploy)

## State Transitions
1. Banano Deploy Applied → (retry discovery) → Endpoint Resolved → Artifact Published
2. Banano Redeploy → Old Artifact considered stale → New Artifact Published
3. API Deploy → Reads latest successful Artifact → Injects config

## Error States
- Discovery Timeout: No artifact; workflow failure
- Invalid Host/Port (post-discovery parsing): Treat as failure; no artifact
- Corrupted Artifact (API workflow): API workflow fails fast; no partial deploy

## Non-Persistent Data
- All new data (artifact, outputs) ephemeral within CI system; no DB schema change required.

## Rationale
Entities intentionally minimal; introducing database persistence for endpoint introduces inconsistency risk and unnecessary coupling for current scale.
