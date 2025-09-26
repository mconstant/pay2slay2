# Quickstart: Immutable SHA Image Build, Deploy & Rollback (Feature 003)

Status: Draft (T004)

## Prerequisites
- GitHub Actions secrets: GHCR credentials with write:packages (build), read:packages (deploy/rollback)
- Cosign installed in build job (optional, soft verify)
- Akash deployment workflow already configured

## 1. Build (Triggered on Push)
Outputs: SHA-tagged image, metadata artifact.

Structured log example:
```
{"phase":"build","image_sha":"<40>","short_sha":"<12>","image_digest":"sha256:...","repository":"ghcr.io/mconstant/pay2slay-api","repository_type":"canonical","signature_status":"unverified","signature_reason":"missing","arch":"linux/amd64","build_duration_sec":42.18}
```

## 2. Deploy (Main Branch)
Consumes metadata artifact; injects immutable tag into Akash Terraform/SDL.
Failure if tag missing (FR-004) or floating tag attempted (FR-005).

Deploy log example:
```
{"phase":"deploy","image_sha":"<40>","image_digest":"sha256:...","repository":"ghcr.io/mconstant/pay2slay-api","repository_type":"canonical","deploy_duration_sec":18.4}
```

## 3. Rollback
Dispatch `api-rollback` workflow with input `IMAGE_SHA`:
- Validates tag existence
- Does NOT rebuild (FR-013)
- Updates deployment reference only

Rollback log example:
```
{"phase":"rollback","previous_sha":"<40-old>","image_sha":"<40-new>","image_digest":"sha256:...","rollback_duration_sec":15.2,"repository":"ghcr.io/mconstant/pay2slay-api","repository_type":"canonical"}
```

## 4. Digest Verification Stages (Remediation)
- Pre-push digest capture (local)
- Post-push digest verification (registry) → mismatch fails (FR-009)
- Deploy-time digest re-check (defense-in-depth)

## 5. Short Tag Parity
Optional short tag (12 chars) points to identical digest; never used directly for deploy commands.

## 6. SBOM Linkage (Placeholder)
Future SBOM artifact will include full SHA; see `contracts/sbom-linkage.yaml`.

## 7. Metrics (Optional)
Counters: `image_build_total{repository_type}` and `rollback_total{repository_type}` if observability enabled.

## 8. Security Notes
- Soft signature verification: missing signature logs unverified, not failure (FR-014)
- Clean builds disable cache (FR-017)
- Staging namespace isolation (FR-016)

## 9. Rollback Example Command
In GitHub UI: Actions → api-rollback → Run workflow → enter IMAGE_SHA (40-char) → Run.

## 10. Troubleshooting
| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| Deploy fails MISSING_TAG | Build not completed or wrong SHA | Re-run build workflow, verify logs |
| Digest mismatch fail | Registry corruption / rare race | Investigate, do not proceed; rebuild and compare |
| Signature_reason=missing | No signature uploaded | Proceed (soft policy), plan signing adoption |

---
Generated for T004. Update after workflows (T016–T018, T042) finalize.
