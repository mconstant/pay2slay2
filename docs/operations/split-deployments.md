# Operations Guide: Split Akash Deployments (Banano Node + API)

This document describes the day‑2 operational flow for managing the separated Banano node and API Akash deployments.

## Overview
Two independent Terraform stacks:
- infra/akash-banano: Manages the Banano node (exposes RPC internally; external provider mapped port discovered post-apply).
- infra/akash-api: Deploys the API service which requires an injected Banano RPC endpoint.

GitHub Actions Workflows:
- banano-deploy.yml: Applies Banano stack then runs discovery to produce `endpoint.json` artifact.
- api-deploy.yml: Consumes the artifact, validates it, and applies the API stack with `-var "banano_rpc_endpoint=..."`.

## Artifact Contract
File: infra/akash-banano/endpoint.json
Schema (informal): { "banano_rpc_endpoint": "<host:port>" }
Validation rules:
- host: valid DNS label(s) or IPv4 literal.
- port: 1024-65535.

## Discovery Process
1. Terraform apply allocates provider resources.
2. Script `scripts/infra/discover_banano_endpoint.sh` retries on a backoff (5,10,20,40s) parsing provider output / mock.
3. Candidate host:port validated via `scripts/infra/validate_endpoint.py`.
4. On success writes artifact + emits structured log lines:
   - [discover][attempt] n=..
   - [discover][success] endpoint=.. attempts=.. elapsed_s=..
   - On failure: [discover][failure] attempts=.. elapsed_s=.. message=unresolved

## Redeploy Scenario
Redeploy (e.g. lease migration) may change the external port. Use helper:
```
bash scripts/infra/test_redeploy.sh
```
This simulates consecutive discoveries and ensures:
- New endpoint value differs.
- Artifact mtime increases.
- Endpoint passes validation again.

## Operator Workflow
1. Trigger Banano deployment: manual workflow dispatch or schedule.
2. Wait for success log line; confirm artifact uploaded in run summary.
3. Trigger API deployment (or let dependent pipeline run) which downloads artifact and applies stack.
4. Validate API service health (future health check endpoint) referencing the injected endpoint.

## Failure Handling
- If Banano discovery fails: API deployment should NOT proceed (artifact absent). Re-run Banano workflow after investigating provider logs.
- If API fails validation step (missing or malformed artifact): abort, fix root cause, retrigger.
- Discovery retries exhausted: treat as transient provider propagation delay; if persistent across multiple runs escalate.

## Observability & Metrics
Structured logs already in place. Future enhancement (T021) reserves metric stub lines (commented) within discovery script to emit Prometheus-compatible gauges, enabling sidecar scrape without code changes.

## Security Considerations
- Artifact contains only non-secret endpoint metadata.
- Ensure no sensitive provider credentials are logged (scripts avoid echoing secrets).

## Performance Notes
Discovery should typically resolve within first or second attempt (<30s). Elapsed seconds recorded in success/failure log for manual monitoring.

## Manual Validation Snippet
```
python3 scripts/infra/validate_endpoint.py $(jq -r '.banano_rpc_endpoint' infra/akash-banano/endpoint.json)
```
Exit code 0 indicates valid.

## Change Log Hook
Update CHANGELOG (T026) upon feature completion summarizing operational impact and new workflows.

---
Revision: initial (T020)
