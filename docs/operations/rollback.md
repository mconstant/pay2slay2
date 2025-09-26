---
title: Rollback Runbook
description: Operational procedure for reverting to a prior immutable image SHA
---

# Rollback Runbook (T024)

## Overview
Rollback uses a dedicated GitHub Actions workflow `api-rollback.yml` (T018) that accepts a `target_sha` input (40 hex characters) and redeploys without rebuilding. This preserves digest integrity (FR-009) and ensures no unintended builds (FR-013).

## Preconditions
- Target SHA tag exists in the appropriate registry repository:
  - main branch: `ghcr.io/mconstant/pay2slay-api:<sha>`
  - feature branch: `ghcr.io/mconstant/pay2slay-api-staging:<sha>`
- Build metadata artifact for the target SHA was produced previously (optional now, required once deployment guard uses live registry lookups).

## Workflow Dispatch (UI)
1. Navigate to Actions → API Rollback.
2. Click "Run workflow"; supply `target_sha` (full 40 chars).
3. Confirm log line: `Rolled back to ghcr.io/...:<sha>` and rollback event JSON with `rollback_duration_sec`.

## CLI Example
```bash
gh workflow run api-rollback.yml -f target_sha=<40charsha>
gh run watch
```

## Invariants (T044)
- MUST NOT build or push a new image.
- MUST reuse existing digest.
- MUST fail if tag missing or length invalid.

## Validation Signals
- Log includes previously deployed SHA (future enhancement: capture prior ref via state store) and new target ref.
- No build steps appear in logs.
- `rollback_total{repository_type}` metric increments (if metrics enabled).

## Troubleshooting
| Symptom | Cause | Action |
|---------|-------|--------|
| `Target image not found` | Tag never built or pruned | Verify build workflow succeeded for commit; rebuild if necessary. |
| `Invalid SHA length` | Typo / truncated input | Re-run with full 40-char SHA. |
| Unexpected build step present | Workflow drift | Revert workflow to version referencing T044 invariants. |

## Future Enhancements
- Persist previous deployment ref to include both `previous_sha` and `new_sha` in rollback event.
- Emit structured rollback event artifact for audit history.
