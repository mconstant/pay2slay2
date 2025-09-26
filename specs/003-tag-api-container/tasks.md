# Tasks: Tag & Deploy API Container Images by Git SHA

Input Sources:
- spec.md (functional requirements FR-001..FR-017, user scenarios, security considerations)
- plan.md (design & contracts strategy, logging schema, workflow separation, rollback design)
- research.md (to be generated already per plan; rationale topics enumerated)
- data-model.md (logical workflow entities ImageArtifact, RollbackEvent) – doc only
- quickstart.md (to be produced in Phase 1 before some implementation tasks)

Prerequisite Script Output:
```
FEATURE_DIR=/Users/mconstant/src/pay2slay2/specs/003-tag-api-container
AVAILABLE_DOCS=[]
```

Legend: [ ] pending, [x] done, [~] partial/stub, [P] parallel-capable.
Guiding Principles: TDD-first (contract tests before workflow edits), immutability, supply-chain integrity, minimal surface area (single-arch, clean builds), auditable logs.

## Phase 3.1: Setup & Scaffolding
- [ ] T001 Create `specs/003-tag-api-container/research.md` capturing Decisions/Rationale/Alternatives for topics (immutable tags, clean build, soft verify, single-arch, staging namespace, rollback workflow). Include future escalation criteria for mandatory signing.
- [ ] T002 Create `specs/003-tag-api-container/data-model.md` documenting ImageArtifact & RollbackEvent logical entities (fields, relationships, no persistence) + structured log JSON schema.
- [ ] T003 Create `specs/003-tag-api-container/contracts/` with three contract descriptor files:
  - `build-workflow.yaml` (inputs: GIT_SHA; outputs: image_ref, digest, signature_status; failure modes)
  - `deploy-workflow.yaml` (inputs: IMAGE_SHA; validations: tag exists, repo canonical; outputs: deployment_ref)
  - `rollback-workflow.yaml` (inputs: IMAGE_SHA; constraints: existing tag; outputs: previous_sha, new_sha)
- [ ] T004 Create `specs/003-tag-api-container/quickstart.md` (build → verify digest/signature_status → deploy → rollback example) referencing FR IDs.
- [ ] T005 Run `.specify/scripts/bash/update-agent-context.sh copilot` to update agent context with new feature tech references (immutable tagging, cosign soft verify, rollback workflow separation).

## Phase 3.2: Contract & Integration Tests (TDD First)
- [ ] T006 [P] Add `tests/contract/test_image_build_contract.py` asserting build contract: simulated function emits JSON with keys {image_sha, image_digest, signature_status, repository, short_sha, build_duration_sec}; test initially fails (placeholder stub returning empty dict).
- [ ] T007 [P] Add `tests/contract/test_deploy_requires_image.py` simulating missing tag scenario; expect custom exception or error code path (deploy stub raises MissingImageTagError). Initially failing.
- [ ] T008 [P] Add `tests/contract/test_rollback_workflow_contract.py` verifying rollback stub only logs prior & target SHAs, does not invoke rebuild function; initially failing.
- [ ] T009 [P] Add `tests/contract/test_signature_soft_verify.py` verifying soft verification logs `signature_status` (verified/unverified) without failing when signature absent; initially failing.
- [ ] T010 Integration test `tests/integration/test_build_deploy_rollback_flow.py`: orchestrates stub build → deploy → rollback; asserts consistent digest reuse; initially failing.
- [ ] T011 Performance smoke test `tests/perf/test_build_step_duration.py` (skippable via PAY2SLAY_SKIP_PERF=1) asserting simulated build completes within provisional budget (<600s stubbed); initially failing until instrumentation added.

## Phase 3.3: Core Workflow Support Code
- [ ] T012 Implement helper script `scripts/ci/emit_image_metadata.py` producing structured JSON (fields per spec) to stdout; include high-resolution duration measurement.
- [ ] T013 Implement Python module `src/lib/image_artifact.py` with pure functions:
  - `build_metadata(git_sha: str, repo: str, digest: str, signature_status: str, start_time: float) -> dict`
  - `validate_sha_tag(tag: str) -> None` (40 hex chars) raising ValueError else.
  - `calc_short_sha(tag: str) -> str` (first 12 chars) with guard for 40-length.
- [ ] T014 Implement deploy validation stub `src/lib/deploy_validate.py` with:
  - `ensure_tag_exists(repo: str, sha: str) -> None` (later shell/API integration) currently raises MissingImageTagError if sha endswith 'deadbeef' (test sentinel)
  - `ensure_repo_allowed(repo: str, is_main: bool) -> None` (enforces staging vs canonical per FR-016)
- [ ] T015 Implement rollback logic stub `src/lib/rollback.py` capturing RollbackEvent (in-memory list for tests) and enforcing no rebuild call.

## Phase 3.4: Workflow Files (GitHub Actions) - Draft (No Production Changes Until Tests Pass)
- [ ] T016 Add/modify `.github/workflows/api-build.yml` to:
  - Trigger on push (any branch)
  - Condition: if main → push to canonical repo; else → staging repo
  - Steps: checkout → derive GIT_SHA → docker build (no cache flags) → push SHA tag → capture digest → run cosign verify (soft) → run emit_image_metadata.py → upload artifact (metadata.json)
  - Include log line with `image_ref`, `image_digest`, `signature_status`.
- [ ] T017 Update `.github/workflows/api-deploy.yml` to:
  - Require metadata artifact from build job
  - Validate SHA tag existence (script placeholder) & repo canonical for main
  - Inject SHA into Akash SDL / Terraform var (immutable reference)
  - Fail fast if tag missing (FR-004)
- [ ] T018 Create new `.github/workflows/api-rollback.yml` with workflow_dispatch (input IMAGE_SHA) performing: validate tag existence → update deployment reference → emit rollback event log (previous_sha,new_sha) → skip rebuild.

## Phase 3.5: Implementation & Test Pass
- [ ] T019 Flesh out signature soft verify step: stub cosign command wrapper `scripts/ci/soft_verify.sh` (returns 0 + status json; failure to find signature sets status=unverified, reason=missing).
- [ ] T020 Update contract tests to consume actual helper functions (remove placeholder stubs) ensuring they pass.
- [ ] T021 Enhance integration test to assert rollback reverts deployment reference variable/state representation.
- [ ] T022 Add metrics emission (optional) gauge/counter via existing observability: `image_build_total`, `rollback_total` in `src/lib/observability.py` extensions (guarded to avoid noise if metrics disabled).

## Phase 3.6: Documentation & Governance
- [ ] T023 Expand `docs/distribution.md` with Immutable Tagging section referencing FR-001..FR-017, including rollback procedure and signature escalation path.
- [ ] T024 Add `docs/operations/rollback.md` runbook with examples (workflow_dispatch JSON, expected logs, troubleshooting missing tag).
- [ ] T025 Update `CHANGELOG.md` with new feature entry (Added: Immutable SHA-based image tagging & rollback workflows).
- [ ] T026 Update `README.md` quick start snippet with note on immutable image tags & rollback command.
- [ ] T027 Generate / refine `specs/003-tag-api-container/quickstart.md` if not finalized after workflow specifics (ensure examples match final file names).

## Phase 3.7: Security & Compliance Enhancements
- [ ] T028 Add simple digest mismatch guard script `scripts/ci/check_existing_digest.py` (compares registry digest vs recorded; if mismatch → fail) fulfilling FR-009 safety.
- [ ] T029 Add policy check pre-deploy ensuring no floating tag pattern (regex guard) even if misconfigured (defense-in-depth) in `src/lib/deploy_validate.py`.
- [ ] T030 Add unit tests for deploy_validate & rollback modules in `tests/unit/test_deploy_validate.py` and `tests/unit/test_rollback.py`.
- [ ] T031 Add SBOM linkage step update in build workflow referencing SHA tag (FR-008) if current SBOM workflow exists; else add TODO comment referencing future enhancement.

## Phase 3.8: Polish & Performance
- [ ] T032 Add timing capture & log for deploy and rollback workflows (start/end) appended to structured output.
- [ ] T033 Add performance assertion in integration test ensuring deploy simulation <300s (mock) for p95 target representational check.
- [ ] T034 Refactor any duplicated SHA handling utilities into `src/lib/image_artifact.py` (dedupe logic from scripts) + run ruff/mypy.
- [ ] T035 Add README badge or status snippet referencing use of immutable SHA images (optional marketing value).

## Validation Checklist
- All contract tests (T006–T009) pass before modifying workflows (T016–T018)
- Integration build→deploy→rollback test (T010, T021) passes before docs are finalized (T023–T027)
- Security guards (FR-004, FR-009, FR-016, FR-017) enforced via tests and scripts (T028, T029)
- Performance smoke (T011, T033) within target thresholds
- Structured logs verified contain required fields (T006, T019)

## Dependencies Summary
Setup → Contracts/Tests → Helper Code → Workflows → Implementation Hardening → Docs → Security → Polish
- T006–T009 before T012–T015 finalization (stubs may exist earlier)
- T012–T015 before T016–T018
- T016 before T017 (build before deploy)
- T017 before T018 (deploy baseline before rollback creation) unless rollback can be stubbed; kept linear for clarity
- T019 after T016 (needs workflow context)
- T028 after T016 (needs pushed image to compare)

## Parallel Execution Examples
Early contract test batch:
```
T006 T007 T008 T009 [P]
```
Helper code parallel set:
```
T012 T013 T014 T015 [P]
```
Documentation batch (post core workflows stabilized):
```
T023 T024 T026 T027 [P]
```
Security/unit add-ons:
```
T028 T029 T030 [P]
```
Polish improvements:
```
T032 T034 T035 [P]
```

## Notes
- Keep workflow edits minimal; prefer adding new steps vs rewriting entire files for clarity in diff review.
- Use explicit FR references in commit messages (e.g., "ci(build): add digest log (FR-006)").
- Ensure rollback workflow has explicit permission scope (read:packages, deploy infra) but not image build.
- Avoid prematurely adding multi-arch logic (deferred per FR-015 deferral note).
- Clean build requirement: pass `--no-cache` for docker build; ensure this is documented in quickstart & distribution docs.
- Soft signature verification: treat cosign not found as status=unverified (log reason), not build failure.

Generated on 2025-09-26 (automated per tasks.prompt).
