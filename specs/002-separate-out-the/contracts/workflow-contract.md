# Workflow Contract: Split Akash Deployments

## Banano Workflow Outputs (FR-003, FR-005, FR-011)
- Terraform Output: `banano_rpc_endpoint` (string; absent on failure)
- Terraform Output: `deployment_id` (string)
- Artifact: `endpoint.json`
  - JSON Schema:
    ```json
    {
      "type": "object",
      "required": ["banano_rpc_endpoint"],
      "additionalProperties": false,
      "properties": {
        "banano_rpc_endpoint": { "type": "string", "pattern": "^[^:]+:[0-9]+$" }
      }
    }
    ```
  - Semantic Validation (performed by API workflow):
    - Host portion matches DNS or IPv4 regex
    - Port numeric 1024–65535

## API Workflow Inputs (FR-002, FR-006)
- Primary Source: Downloaded artifact `endpoint.json`
- Derived Environment Variable (example): `BANANO_RPC_ENDPOINT=<value>`
- Failure Modes:
  - Artifact missing → hard fail
  - JSON parse error → hard fail
  - Validation failure → hard fail

## Validation Rules (FR-012)
- Host Regex (DNS): `^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)*$`
- IPv4 Regex: `^([0-9]{1,3}\.){3}[0-9]{1,3}$`
- Combined Acceptance: host matches one of above
- Port Range: 1024–65535 inclusive

## Retry Logic (FR-004)
- Attempts: 4
- Backoff Delays Between Attempts: 5s, 10s, 20s (cumulative ~35s) with final wait completing at ~75s total elapsed including resolution operations.
- Failure Condition: After 4th unsuccessful port discovery, exit 1 (no outputs / no artifact creation)

## Logging Requirements (FR-007)
- Success: `Banano RPC endpoint resolved: <host:port>`
- Each Attempt: `Attempt <n>/4: probing Akash forwarded ports for internal 7072` (optional enhancement)
- Failure: `Banano RPC endpoint resolution failed after 4 attempts` (exit code 1)

## Contract Test Coverage
| Test | Scenario | Expected |
|------|----------|----------|
| CT-001 | Valid endpoint.json schema | Pass schema + semantic validation |
| CT-002 | Missing artifact | API workflow simulation fails fast |
| CT-003 | Invalid host pattern | Validation rejects, fail fast |
| CT-004 | Port out of range | Validation rejects |
| CT-005 | Empty JSON object | Schema validation fails |
| CT-006 | Multiple redeploys produce distinct artifacts | Latest artifact used |

## Non-Goals
- Health checking the Banano RPC endpoint
- Artifact signing / integrity verification
- Automated API redeploy trigger

## Future Extensibility
Add keys to endpoint.json (e.g., `version`, `height`) without breaking consumer by permitting additive properties only after updating schema (current schema forbids extras by design; version bump would relax `additionalProperties`).
