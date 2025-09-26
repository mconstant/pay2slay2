
# Implementation Plan: Tag & Deploy API Container Images by Git SHA

**Branch**: `003-tag-api-container` | **Date**: 2025-09-26 | **Spec**: `specs/003-tag-api-container/spec.md`
**Input**: Feature specification from `specs/003-tag-api-container/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Implement immutable container image tagging for the API using the exact git commit SHA (40 chars) as the deploy reference on Akash. Build workflow produces and pushes single-architecture (linux/amd64) images to GHCR: main branch → `ghcr.io/mconstant/pay2slay-api`, other branches → staging namespace `ghcr.io/mconstant/pay2slay-api-staging`. Deploy workflows consume only SHA tags (no floating tags), verify existence, perform soft cosign/provenance verification (log-only), and update Akash deployment references. A dedicated rollback workflow redeploys a specified historic SHA without rebuilding. Clean builds (no layer cache reuse) ensure deterministic, tamper-resistant supply chain; digest + signature status logged for traceability.

## Technical Context
**Language/Version**: Python 3.13 (project baseline)
**Primary Dependencies**: FastAPI, SQLAlchemy, Alembic, httpx, OpenTelemetry, Cosign (workflow tool), Docker BuildKit
**Storage**: SQLite (dev) / future Postgres (not impacted by this feature)
**Testing**: pytest (existing contract/integration suites)
**Target Platform**: Linux server (Akash deployment)
**Project Type**: single
**Performance Goals**: Build+push ≤10 min p95; deploy apply ≤5 min p95 (from workflow start to Akash update)
**Constraints**: Immutable tags only in production path; no multi-arch; clean build (no cache); soft signature verification non-blocking; rollback must not require rebuild
**Scale/Scope**: Dozens of deployments; rollback history bounded only by git + registry retention; no horizontal scaling change

## Constitution Check
Initial Gate Assessment (Pre-Phase 0):
- Code Quality Tooling: Ruff, mypy, SBOM & cosign steps already exist → PASS
- Test Strategy: Will add new contract tests for build/deploy artifact verification & rollback workflow simulation (pytest) before modifying deploy pipelines → PASS
- UX/Accessibility: Not user-facing UI; operator logs & docs acceptance defined → N/A (documented) → PASS
- Performance Targets: Build/deploy p95 targets declared (spec + Technical Context) → PASS
- Observability Hooks: Plan to add structured log lines (image_ref, image_digest, signature_status, rollback_origin) + metrics counters (optional) → PASS
- AI Autonomy Guardrails: All clarifications resolved; no unsafe destructive ops proposed → PASS
- Security Considerations: Threat model, signature policy, staging namespace isolation, cache integrity defined → PASS
- Licensing/Dependencies: No new runtime deps; workflow-only cosign usage; existing license manifest unaffected → PASS
- Decentralized/Blockchain: Not applicable (Akash deploy is existing infra) → N/A
- On-chain Requirements: None → N/A

Initial Constitution Check: PASS

Post-Design (after Phase 1) Re-evaluation placeholder: (will reconfirm—expected PASS; see Progress Tracking)

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 1 (single project). No frontend/mobile impact.

## Phase 0: Outline & Research
Unknowns Remaining: NONE (all clarifications addressed in spec). Phase 0 will still capture rationale & alternatives for key decisions for auditability.

Research Topics & Rationale to Document:
1. Immutable Tagging vs Floating Tags → decision justification
2. Clean Build (no cache) vs Registry Layer Cache (performance tradeoff, security rationale)
3. Soft Signature Verification vs Mandatory (risk assessment & planned escalation criteria (>90% signed coverage))
4. Single-Arch vs Multi-Arch (build time vs operator need; deferral path)
5. Staging Namespace Strategy vs Single Namespace with Labeling
6. Rollback Workflow Separation vs Extend Deploy Workflow

Method: Consolidate above into `research.md` with Decision / Rationale / Alternatives. No blocking unknowns; timebox to concise entries.

Output Artifact: `research.md`

## Phase 1: Design & Contracts
Prerequisite: `research.md` complete.

1. Data Model (`data-model.md`):
   - Logical Entities (documentation only): ImageArtifact (sha_tag, digest, signature_status, repository, built_at), RollbackEvent (requested_sha, previous_sha, initiated_by, timestamp). These are not DB tables—represented via workflow log/metrics schema.
2. Contracts (`contracts/`):
   - Since feature scope centers on CI workflows, not new HTTP API endpoints, provide contract stubs for: build workflow, deploy workflow, rollback workflow. Represent as pseudo-OpenAPI or structured YAML describing required inputs, outputs, log fields, failure modes.
   - Include schema for structured log line (JSON) emitted post-build: {"image_sha","image_digest","signature_status","repository","short_sha","build_duration_sec"}
3. Contract Tests (failing initially):
   - Test: `tests/contract/test_image_build_contract.py` asserts presence of required structured log fields via invoking a minimal script or fixture stub.
   - Test: `tests/contract/test_deploy_requires_image.py` simulates missing SHA tag scenario expecting failure path.
   - Test: `tests/contract/test_rollback_workflow_contract.py` ensures rollback path references only existing SHA and does not trigger rebuild.
4. Integration Test Scenario (optional if fast): Simulated end-to-end: build stub writes artifact metadata → deploy consumes → rollback switches reference.
5. Quickstart (`quickstart.md`): Steps for building a new commit image, verifying digest & signature status, deploying, and rolling back with example commands.
6. Update Agent File: Run `.specify/scripts/bash/update-agent-context.sh copilot` after artifacts are generated.

Outputs: `data-model.md`, `contracts/` descriptors, `quickstart.md`, failing contract tests, updated Copilot agent context file.

## Phase 2: Task Planning Approach
NOT executed now (handled by /tasks). Strategy:
1. Contract Tests First: build contract, deploy contract, rollback contract, missing image failure, signature soft verify logging.
2. Workflow Implementation: modify existing GitHub Actions (build, deploy, rollback new) referencing FR IDs in commit messages.
3. Logging & Metrics: Add structured log emission script/module (minimal Python helper in `scripts/ci/emit_image_metadata.py`).
4. Documentation: quickstart & rollback section, update distribution doc with immutable tagging subsection.
5. Security Hardening: gating check in deploy workflow ensuring repository matches canonical before proceeding.
6. Post-Implementation Verification: tests green + manual dry-run of workflows (where feasible via workflow_dispatch).

Expected Tasks Count: ~18-22 (smaller than generic 25-30 due to workflow-centric scope).

Parallelization: Logging helper & docs can proceed alongside test authoring; workflow edits serialized after tests exist.

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
No violations or deviations; feature intentionally minimal (no DB schema changes, no new runtime services). Section retained for audit completeness.


## Progress Tracking
**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - described only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [ ] Post-Design Constitution Check: PASS (to be re-affirmed after artifact creation—no violations expected)
- [x] All NEEDS CLARIFICATION resolved
- [x] Complexity deviations documented (none)
- [x] AI autonomy guardrails evaluated (no silent skips)

---
*Based on Constitution v2.4.0 - See `/memory/constitution.md`*
