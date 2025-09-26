# Data Model & Log Schema (Feature 003)

Status: Draft (T002)

## Logical Entities (Documentation Only)

### ImageArtifact
Represents a built container image associated with a git commit.
Fields:
- git_sha (40 hex)
- short_sha (12 hex convenience)
- repository (string; canonical or staging registry path)
- repository_type (enum: canonical|staging)
- digest (sha256:...)
- arch (string: linux/amd64)
- signature_status (verified|unverified)
- signature_reason (text; missing|key_not_found|error|n/a)
- build_duration_sec (float)
- created_at (ISO8601 timestamp)

### RollbackEvent
Represents an operator-initiated rollback action.
Fields:
- requested_sha (target image SHA)
- previous_sha (deployment reference before rollback)
- repository (canonical repo ref)
- initiated_by (workflow actor / github actor)
- rollback_duration_sec (float)
- timestamp (ISO8601)

## Relationships
No persisted relational storage; artifacts are discoverable via registry and logs. RollbackEvent references two ImageArtifact SHAs.

## Structured Log Schemas
### Build Log (post-build)
```
{
  "phase": "build",
  "image_sha": "<40-hex>",
  "short_sha": "<12-hex>",
  "image_digest": "sha256:<digest>",
  "repository": "ghcr.io/mconstant/pay2slay-api[-staging]?",
  "repository_type": "canonical|staging",
  "arch": "linux/amd64",
  "signature_status": "verified|unverified",
  "signature_reason": "missing|key_not_found|error|n/a",
  "build_duration_sec": <float>,
  "pre_push_digest": "sha256:<digest>",
  "post_push_digest": "sha256:<digest>",
  "digest_verification": "ok|mismatch"
}
```

### Deploy Log
```
{
  "phase": "deploy",
  "image_sha": "<40-hex>",
  "image_digest": "sha256:<digest>",
  "repository": "...",
  "repository_type": "canonical|staging",
  "deploy_duration_sec": <float>
}
```

### Rollback Log
```
{
  "phase": "rollback",
  "previous_sha": "<40-hex>",
  "image_sha": "<40-hex>",
  "image_digest": "sha256:<digest>",
  "rollback_duration_sec": <float>,
  "repository": "...",
  "repository_type": "canonical"
}
```

## Constraints & Validation
- git_sha: 40 hex enforced by `validate_sha_tag` (T013)
- short_sha: derived; must correspond to prefix of git_sha
- digest fields: must match regex `^sha256:[0-9a-f]{64}$`
- repository_type determined by branch (main → canonical)
- arch fixed to linux/amd64 (FR-015)
- digest_verification: present only in build log after remediation tasks (T041/T042)

## Metrics (T022/T060)
- Counter: image_build_total{repository_type}
- Counter: rollback_total{repository_type}

(Optional future) histogram gauges for durations.

---
Generated for T002. Update only with FR references in commits.
