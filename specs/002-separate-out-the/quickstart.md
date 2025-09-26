# Quickstart: Split Akash Deployments

Goal: Deploy Banano node, obtain its RPC endpoint, deploy API consuming it.

## Prerequisites
- Akash credentials & provider configuration secrets already configured in GitHub Actions
- Terraform installed locally (optional for manual validation)

## Steps
1. Run Banano Workflow (GitHub Actions → `workflow_dispatch`).
2. Wait for success; confirm log line: `Banano RPC endpoint resolved: <host:port>`.
3. Download artifact `endpoint.json` (optional manual check):
   ```json
   { "banano_rpc_endpoint": "example.banano.net:12345" }
   ```
4. Trigger API Workflow (no manual endpoint input required) – it fetches latest artifact automatically.
5. Verify API workflow logs include: `Using Banano RPC endpoint: <host:port>`.
6. (Optional) Redeploy Banano workflow; repeat steps 2–5 ensuring updated endpoint propagates.

## Validation
- Contract Tests: Run `pytest tests/contract/test_endpoint_artifact.py` (to be added) – should fail until implementation complete.
- Manual: Curl API `/health` or internal status endpoint ensuring connectivity (out of scope for automation now).

## Troubleshooting
| Symptom | Cause | Action |
|---------|-------|--------|
| API workflow fails: missing artifact | Banano workflow not run or failed | Run Banano workflow; ensure success |
| Invalid host/port validation failure | Malformed forwarded port data | Re-run Banano; inspect logs for port mapping |
| Stale endpoint after redeploy | API workflow used cached artifact | Trigger fresh API workflow; confirm artifact timestamp |

## Cleanup
Independent destroy (if needed): run `terraform destroy` inside either `infra/akash-banano` or `infra/akash-api` directory—does not impact the other.

