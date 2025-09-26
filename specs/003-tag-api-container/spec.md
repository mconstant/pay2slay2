# Feature Specification: Tag & Deploy API Container Images by Git SHA

**Feature Branch**: `[003-tag-api-container]`  
**Created**: 2025-09-26  
**Status**: Draft  
**Input**: User description: "Tag API container images with git SHA and deploy using that immutable reference on Akash workflows"

## Clarifications
### Session 2025-09-26
- Q: Which registry and naming convention should be the canonical source of truth for SHA-tagged API images? → A: GitHub Container Registry (ghcr.io/mconstant/pay2slay-api)

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As an operator I want every deployed API container on Akash to reference an immutable image tag (the exact git commit SHA) so that I can trace running code to source and ensure reproducible rollbacks.

### Acceptance Scenarios
1. **Given** a commit pushed to the main branch, **When** the build workflow runs, **Then** it MUST build an image tagged with the full 40‑char commit SHA and push it to the registry.
2. **Given** the Banano/API deploy workflows, **When** they run after the image is built, **Then** they MUST reference only the commit SHA tag (not latest or a mutable tag) in Terraform / SDL and apply successfully.
3. **Given** an existing deployment using SHA X, **When** a new commit SHA Y is built and deployed, **Then** the prior deployment reference remains queryable for rollback and the new deployment uses SHA Y.
4. **Given** a deployment error, **When** an operator decides to rollback, **Then** they can redeploy using a previous git SHA tag without rebuilding.

### Edge Cases
- Build skipped (e.g., CI failure) → Deploy workflow MUST fail fast if the requested SHA tag is absent in registry.
- Force rebuild of same SHA (cache bust) → System SHOULD detect existing tag and either reuse or rebuild deterministically (clarify policy below).
- Branch builds (non-main) → SHOULD produce SHA-tagged images but MAY be excluded from production deploy triggers (needs explicit policy).
- Signed images & provenance (future) → Tagging MUST not interfere with signing/predicate naming.

### UX Acceptance Criteria
Not user-facing UI; operator experience criteria:
- Deployment logs MUST show the exact image reference (registry/name@digest and :sha tag) in a single line for copy/paste.
- Documentation MUST include a rollback example referencing a prior SHA.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST build an API container image for each main branch commit.
- **FR-002**: System MUST tag the image with the full git commit SHA (40 chars) and optionally a short 12-char convenience tag.
- **FR-003**: System MUST push the image (sha tag) before any deploy workflow attempts to reference it.
- **FR-004**: Deploy workflows MUST fail if the expected SHA tag does not exist in the registry.
- **FR-005**: Deploy workflows MUST reference only immutable tags (SHA) and MUST NOT use floating tags (e.g., latest) for production.
- **FR-006**: System MUST record (in workflow logs) the built image digest (sha256:...) and map it to the git SHA.
- **FR-007**: System MUST allow rollback by re-running deploy with a prior SHA without rebuilding.
- **FR-008**: System SHOULD create a provenance or SBOM linkage referencing the same SHA tag (if SBOM generation already exists).
- **FR-009**: System MUST ensure cache safety: if an image with the same SHA tag exists, it MUST verify digest matches; if mismatch (corruption), fail.
- **FR-010**: System SHOULD optionally sign (cosign) the SHA-tagged image (if signing pipeline present) without altering tag semantics.
- **FR-011**: System MUST document the workflow steps for building, tagging, deploying, and rolling back.
- **FR-012**: Canonical image repository MUST be `ghcr.io/mconstant/pay2slay-api`; all SHA tags published there first (any future mirrors are secondary and MUST NOT drive deploy references).

### Key Entities
- **Image Artifact**: Immutable container image identified by (registry, name, digest) and tagged with git SHA.
- **Deployment Reference**: Configuration pointer (Terraform variable / Akash SDL) storing the SHA tag used for current deployment.
- **Rollback Catalog (implicit)**: Historical list of SHAs (available via git + registry tag listing) enabling redeploy.

## Security Considerations *(mandatory)*
- Threat model: Prevent unauthorized image tampering or ambiguous version deployment.
- Immutable tag usage removes risk of mutable tag drift (e.g., latest) causing unexpected code changes.
- Supply chain: Requires verifying digest printed in logs; future enhancement: enforce signature verification prior to deploy.
- Secrets: Build process MUST avoid leaking registry credentials in logs.
- Abuse/Misuse: Prevent deploying unreviewed commit by limiting production deploy triggers to protected branches.
- Automation / AI Execution Constraints: Automated agent MUST NOT delete or overwrite existing SHA tags unless explicitly instructed; MUST escalate if digest mismatch is detected for an existing SHA tag.
- Registry Access: GitHub Container Registry scopes (repo / write:packages) MUST be restricted to CI workflows; deploy workflows require read:packages only.

## Decentralized Distribution / Blockchain Applicability *(conditional)*
Not directly applicable to tagging; underlying deployment (Akash) already in decentralized infrastructure. No on-chain logic introduced. (Rationale: image tagging is a CI/CD concern, not protocol layer.)

## Performance Targets
- Build pipeline SHOULD complete image build + push within 10 minutes (p95) for standard codebase size.
- Deployment job SHOULD fetch and apply new image reference within 5 minutes (p95).

## Review & Acceptance Checklist
### Content Quality
- [x] No implementation details (avoids specific build tool commands)
- [x] Focused on user (operator) value & governance
- [x] Mandatory sections completed
- [x] Security considerations included
- [x] Decentralized/Blockchain applicability addressed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain (assumed policies noted; can refine in planning)
- [x] Requirements testable & measurable
- [x] Performance targets present
- [x] Scope bounded (image tagging & deploy reference only)
- [x] Dependencies identified implicitly (registry access, existing deploy workflows)

## Execution Status
- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities (none blocking) marked as assumptions in text
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

