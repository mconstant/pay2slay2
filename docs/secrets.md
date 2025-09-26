# Secrets & Configuration (T044)

This document outlines how Pay2Slay handles sensitive configuration values and recommended operational practices.

## Sources of Configuration

1. YAML files in `configs/` (payout.yaml, integrations.yaml, product.yaml)
2. Environment variables (override portions of YAML using shell expansion like `${VAR}`)
3. Process environment for runtime toggles:
   - `PAY2SLAY_METRICS_EXEMPLARS=1` enables trace exemplars
   - `OTEL_EXPORTER_OTLP_ENDPOINT` / `PAY2SLAY_OTLP_ENDPOINT` toggles OTLP tracing export
   - `CONFIG_DIR` overrides the default `configs/` path

## Sensitive Fields

The following keys are treated as secrets (masked in logs):
- Any key containing: `key`, `secret`, `token`, `password`

Examples in `integrations.yaml`:
- `yunite_api_key`
- `fortnite_api_key`
- `discord_oauth_client_secret`

## Masking Logic

`AppConfig.safe_dict()` returns a redacted structure for logging & diagnostics:
- Secret-y keys replaced with `***`
- Non-secret values preserved
- Shape retained for troubleshooting (presence/absence, list lengths)

Usage example:
```python
from src.lib.config import get_config
from src.lib.observability import get_logger

log = get_logger(__name__)
conf = get_config()
log.info("config_loaded", config=conf.safe_dict())
```

## DO / DO NOT

| Do | Avoid |
|----|-------|
| Use `safe_dict()` when logging config | Logging raw `AppConfig` model directly |
| Inject secrets via env or secret mount | Committing secrets into Git or YAML defaults |
| Rotate API keys periodically | Relying on a single long-lived key |
| Limit secret exposure in trace attributes | Attaching secret values as span/log attributes |

## Recommended Deployment Patterns

| Platform | Recommendation |
|----------|---------------|
| Docker Compose | Use an `.env` (gitignored) + docker secrets for production |
| Akash | Use provider secret store or SOPS-encrypted manifests rendered at deploy time |
| Kubernetes | Store YAML minus secrets in ConfigMap; secrets in `Secret` objects; reference via envFrom |

## Future Enhancements (Open Items)
- Enforce required secrets presence on startup with clear error (fail-fast)
- Integrate secret version / rotation metadata logging (hashed fingerprint)
- Optional Vault/SOPS loader plugin
- Document cosign provenance (T058) once pipeline created

## Testing

Add tests to ensure:
- `safe_dict()` masks expected keys
- Non-secret keys remain unchanged

(Planned in follow-up PR) 

## Incident Response

If a secret leaks (e.g., appears in a log aggregation system):
1. Revoke/rotate at source (Discord/Yunite/Fortnite/Banano node)
2. Purge impacted logs if feasible
3. Deploy with new secret
4. Add regression test if root cause was missing masking logic

---
Last updated: 2025-09-25
