# Research & Rationale: Immutable SHA Tagging Feature (003)

Date: 2025-09-26
Status: Draft (initial population per T001)

## Decision Records

### DR-001 Immutable Tags vs Floating Tags (latest)
Decision: Use full 40-char git commit SHA tags only (with optional short 12-char convenience tag).  
Rationale: Eliminates drift risk; guarantees deterministic rollback & audit.  
Alternatives: latest / semver tags (rejected – mutable or extra versioning complexity).  
FR Mapping: FR-002, FR-005, FR-007.

### DR-002 Clean Build (No Cache) vs Layer Cache Reuse
Decision: Always execute clean builds with `--no-cache` / disable BuildKit cache export/import.  
Rationale: Avoids cache poisoning & stale dependency risk; simplifies supply-chain trust baseline.  
Risk: Increased build time (performance tradeoff).  
Mitigation: Performance iteration later; baseline p95 <10m.  
FR Mapping: FR-017; Security Considerations.

### DR-003 Soft Signature Verification vs Mandatory
Decision: Attempt cosign/provenance verification; never fail deployment solely for missing/invalid signature (log `signature_status=unverified` & `signature_reason`).  
Rationale: Enables incremental adoption; avoids blocking pipeline before signing coverage high.  
Escalation Criteria: Switch to mandatory once >90% of last 30 deployed SHAs are signed & failure rate <1%.  
FR Mapping: FR-014.

### DR-004 Single-Arch (linux/amd64) vs Multi-Arch
Decision: Build only linux/amd64 image.  
Rationale: Faster builds; reduces complexity (manifest lists, per-arch signing).  
Future Path: Introduce arm64 once digest verification, signing, and rollback invariants mature.  
FR Mapping: FR-015.

### DR-005 Staging Namespace vs Single Shared Repository
Decision: Use `ghcr.io/mconstant/pay2slay-api-staging` for non-main builds; canonical `ghcr.io/mconstant/pay2slay-api` only for main.  
Rationale: Prevent accidental promotion; clear provenance boundary.  
FR Mapping: FR-016.  
Security: Deploy workflow will assert canonical repo for production path.

### DR-006 Dedicated Rollback Workflow vs Overloading Deploy
Decision: Separate `api-rollback` workflow with explicit `IMAGE_SHA` input.  
Rationale: Principle of least surprise; prevents accidental rollback during routine deploy.  
FR Mapping: FR-013.

### DR-007 Digest Verification Layers
Decision: Enforce digest consistency pre/post push and again pre-deploy (two-stage).  
Rationale: Detect registry tampering or race conditions early; defense-in-depth.  
FR Mapping: FR-009 (expanded by remediation tasks T036–T043).

### DR-008 Short Tag Parity
Decision: Provide optional 12-char short tag pointing to same digest; treat as convenience only, never primary deploy reference.  
Rationale: Operator UX (copy/paste) while preserving authoritative 40-char tag.  
FR Mapping: FR-002 (optional short tag).  
Test Coverage: T049 parity contract, fails if digest mismatch.

### DR-009 SBOM Linkage
Decision: Reference image SHA in SBOM/provenance artifact name/path; if SBOM generation not yet implemented, track explicit TODO plus contract stub (`sbom-linkage.yaml`).  
Rationale: Future-ready supply-chain attestation.  
FR Mapping: FR-008.

### DR-010 Metrics Strategy
Decision: Emit counters `image_build_total{repository_type}` and `rollback_total{repository_type}` with optional enable flag.  
Rationale: Simple observability baseline; future histogram for durations possible.  
FR Mapping: (observability extension supporting FR-006/FR-013 traceability).

## Risk Matrix (Selected)
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Registry digest mismatch (corruption) | High | Low | Dual-phase digest verification (build & deploy) T041/T028 |
| Unsigned image deployed | Medium | High early | Soft verify logs + escalation threshold (DR-003) |
| Accidental rollback | Medium | Low | Dedicated workflow with explicit SHA input (DR-006) |
| Build time increase (no cache) | Medium | Medium | Perf tracking tests (T011, T033) + future caching iteration |
| Repo misroute (staging image to prod) | High | Low | `ensure_repo_allowed` + tests (T051, T053) |

## Open Questions (Deferred)
- When to introduce multi-arch? (Trigger: arm64 user demand + signing matured)
- When to move signature to mandatory? (Threshold metrics instrumentation pending)
- Which SBOM generator & format? (cyclonedx vs syft) — postpone until baseline stable.

## Future Enhancements (Backlog)
- Mandatory cosign verification (fail on unverified)
- Multi-arch build matrix (amd64, arm64) with manifest signing
- Build caching with attestation of reproducibility
- SBOM generation pipeline & attestation integration
- Provenance attestation ingestion dashboard

## References
- GitHub Container Registry Docs
- Sigstore Cosign Docs
- OCI Image Spec
- Akash Deployment Workflow Patterns

---
Generated for tasks T001. Further edits require referencing FR IDs in commit messages.
