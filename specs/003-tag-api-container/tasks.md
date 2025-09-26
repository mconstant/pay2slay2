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
AVAILABLE_DOCS=[research.md,data-model.md,quickstart.md,contracts/*]
```

Legend: [ ] pending, [x] done, [~] partial/stub, [P] parallel-capable.
Guiding Principles: TDD-first (contract tests before workflow edits), immutability, supply-chain integrity, minimal surface area (single-arch, clean builds), auditable logs.

 ## Phase 3.1: Setup & Scaffolding
 - [x] T001 Create `specs/003-tag-api-container/research.md` capturing Decisions/Rationale/Alternatives for topics (immutable tags, clean build, soft verify, single-arch, staging namespace, rollback workflow, short tag parity, SBOM linkage, metrics strategy). Include future escalation criteria for mandatory signing.
- [x] T002 Create `specs/003-tag-api-container/data-model.md` documenting ImageArtifact & RollbackEvent logical entities (fields, relationships, no persistence) + structured log JSON schema.
- [x] T003 Create `specs/003-tag-api-container/contracts/` with three contract descriptor files:
  - `build-workflow.yaml` (inputs: GIT_SHA; outputs: image_ref, digest, signature_status; failure modes)
  - `deploy-workflow.yaml` (inputs: IMAGE_SHA; validations: tag exists, repo canonical; outputs: deployment_ref)
  - `rollback-workflow.yaml` (inputs: IMAGE_SHA; constraints: existing tag; outputs: previous_sha, new_sha)
- [x] T004 Create `specs/003-tag-api-container/quickstart.md` (build → verify digest/signature_status → deploy → rollback example) referencing FR IDs.
- [x] T005 Run `.specify/scripts/bash/update-agent-context.sh copilot` to update agent context with new feature tech references (immutable tagging, cosign soft verify, rollback workflow separation).

## Phase 3.2: Contract & Integration Tests (TDD First)
 - [x] T006 [P] Add `tests/contract/test_image_build_contract.py` asserting build contract: simulated function emits JSON with keys {image_sha, image_digest, signature_status, signature_reason, repository, repository_type, short_sha, arch, build_duration_sec}; test initially fails (placeholder stub returning empty dict).
 - [x] T007 [P] Add `tests/contract/test_deploy_requires_image.py` simulating missing tag scenario; expect custom exception or error code path (deploy stub raises MissingImageTagError). Initially failing.
 - [x] T008 [P] Add `tests/contract/test_rollback_workflow_contract.py` verifying rollback stub only logs prior & target SHAs, does not invoke rebuild function; initially failing.
 - [x] T009 [P] Add `tests/contract/test_signature_soft_verify.py` verifying soft verification logs `signature_status` (verified/unverified) plus `signature_reason` (e.g. missing, key_not_found) without failing when signature absent; initially failing.
 - [x] T010 Integration test `tests/integration/test_build_deploy_rollback_flow.py`: orchestrates stub build → deploy → rollback; asserts consistent digest reuse; initially failing.
 - [x] T011 Performance smoke test `tests/perf/test_build_step_duration.py` (skippable via PAY2SLAY_SKIP_PERF=1) asserting simulated build completes within provisional budget (<600s stubbed); initially failing until instrumentation added.

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
  - Steps: checkout → derive GIT_SHA → docker build (no cache flags, single-arch linux/amd64) → push SHA tag (+ optional 12-char short tag) → capture digest → run cosign verify (soft) → run emit_image_metadata.py (now includes arch & repository_type) → upload artifact (metadata.json)
  - Include log line with `image_ref`, `image_digest`, `signature_status`.
- [ ] T017 Update `.github/workflows/api-deploy.yml` to:
  - Require metadata artifact from build job
  - Validate SHA tag existence (script placeholder) & repo canonical for main
  - Inject SHA into Akash SDL / Terraform var (immutable reference)
  - Fail fast if tag missing (FR-004)
 - [ ] T018 Create new `.github/workflows/api-rollback.yml` with workflow_dispatch (input IMAGE_SHA) performing: validate tag existence → update deployment reference → emit rollback event log (previous_sha,new_sha, duration_sec) → skip rebuild (assert no build step present).

## Phase 3.5: Implementation & Test Pass
 - [ ] T019 Flesh out signature soft verify step: stub cosign command wrapper `scripts/ci/soft_verify.sh` (returns 0 + status json; failure to find signature sets status=unverified, signature_reason=missing) and include arch detection.
- [ ] T020 Update contract tests to consume actual helper functions (remove placeholder stubs) ensuring they pass.
 - [ ] T021 Enhance integration test to assert rollback reverts deployment reference variable/state representation and preserves digest & arch, repository selection unchanged.
 - [ ] T022 Add metrics emission (optional) gauge/counter via existing observability: `image_build_total`, `rollback_total` + ensure counters labeled by repository_type (canonical|staging) (guarded to avoid noise if metrics disabled).

## Phase 3.6: Documentation & Governance
- [ ] T023 Expand `docs/distribution.md` with Immutable Tagging section referencing FR-001..FR-017, including rollback procedure and signature escalation path.
- [ ] T024 Add `docs/operations/rollback.md` runbook with examples (workflow_dispatch JSON, expected logs, troubleshooting missing tag).
- [ ] T025 Update `CHANGELOG.md` with new feature entry (Added: Immutable SHA-based image tagging & rollback workflows).
- [ ] T026 Update `README.md` quick start snippet with note on immutable image tags & rollback command.
- [ ] T027 Generate / refine `specs/003-tag-api-container/quickstart.md` if not finalized after workflow specifics (ensure examples match final file names).

## Phase 3.7: Security & Compliance Enhancements
 - [ ] T028 Add simple digest mismatch guard script `scripts/ci/check_existing_digest.py` (compares registry digest vs recorded; if mismatch → fail) fulfilling FR-009 safety (deployment-time) and confirm repository matches expected canonical/staging mapping.
- [ ] T029 Add policy check pre-deploy ensuring no floating tag pattern (regex guard) even if misconfigured (defense-in-depth) in `src/lib/deploy_validate.py`.
- [ ] T030 Add unit tests for deploy_validate & rollback modules in `tests/unit/test_deploy_validate.py` and `tests/unit/test_rollback.py`.
 - [ ] T031 Add SBOM linkage step update in build workflow referencing SHA tag (FR-008); if SBOM generation not yet implemented, create explicit TODO plus link to new `sbom-linkage.yaml` contract (T047) rather than generic comment.

## Phase 3.8: Polish & Performance
 - [ ] T032 Add timing capture & log for deploy and rollback workflows (start/end) appended to structured output including fields {deploy_duration_sec, rollback_duration_sec}.
- [ ] T033 Add performance assertion in integration test ensuring deploy simulation <300s (mock) for p95 target representational check.
- [ ] T034 Refactor any duplicated SHA handling utilities into `src/lib/image_artifact.py` (dedupe logic from scripts) + run ruff/mypy.
- [ ] T035 Add README badge or status snippet referencing use of immutable SHA images (optional marketing value).

## Phase 3.9: High Severity Remediation (Digest & Rollback Invariants)
Rationale: Close high severity analysis gaps for FR-009 (digest mismatch safety) & FR-013 (rollback must not rebuild) without waiting for medium items.

- [x] T036 Add new contract descriptor `specs/003-tag-api-container/contracts/digest-verification.yaml` describing pre-push digest capture, post-push registry digest retrieval, mismatch failure condition, and logging fields (phase: pre_push, post_push, status: ok/mismatch).
 - [x] T037 Extend `tests/contract/test_image_build_contract.py` (T006) or create adjunct `tests/contract/test_digest_verification_contract.py` asserting presence of pre & post digest fields and equality; initially failing until workflow instrumentation (reference T042).
 - [x] T038 Add negative test `tests/contract/test_digest_mismatch_failure.py` simulating mismatch (monkeypatch registry lookup returning different digest) expecting `DigestMismatchError` (new custom exception in guard script/module).
 - [x] T039 Add dedicated rollback no-build test `tests/contract/test_rollback_no_build_side_effect.py` asserting that invoking rollback does NOT call any build/rebuild function (use monkeypatch counter) – complements T008 but explicitly enforces FR-013 invariant.
- [ ] T040 Add sentinel in `src/lib/rollback.py` (e.g., module-level flag or injected callback) to detect unintended build invocation; used only in tests (guarded by ENV var) to keep production path clean.
- [ ] T041 Introduce script `scripts/ci/check_digest_post_push.py` performing: (a) load recorded digest from metadata artifact, (b) query registry (placeholder stub), (c) compare; exit non-zero on mismatch.
- [ ] T042 Update build workflow (T016) adding steps: compute local image digest BEFORE push (docker image inspect), store in metadata; AFTER push run `check_digest_post_push.py` to enforce FR-009; ensure both digests logged with structured context.
- [ ] T043 Refine existing digest guard task T028: clarify it now covers deployment-time verification (pre-deploy) while T041 handles build-time post-push; update its description inline (do not renumber) to avoid duplication.
- [ ] T044 Amend `rollback-workflow.yaml` (T003) to explicitly declare invariants: must not build, must not alter digest, must reference existing tag only.
- [ ] T045 Extend integration test `tests/integration/test_build_deploy_rollback_flow.py` (T010/T021) to assert digest remains unchanged across rollback and that attempting a forced rebuild path would raise/flag (simulate by setting sentinel and expecting no trigger).
- [ ] T046 Update `docs/distribution.md` & `specs/003-tag-api-container/spec.md` to explicitly call out digest integrity and rollback no-build guarantees (reference FR-009, FR-013) and link to new contract file.

## Phase 3.10: Medium Remediation & Completeness
Rationale: Close medium severity analysis gaps (parity, single-arch explicit verification, staging/canonical separation tests, SBOM linkage formalization, metrics validation, structured log completeness, foreign repo defense-in-depth, performance gating, documentation validation).

- [x] T047 Add contract descriptor `specs/003-tag-api-container/contracts/sbom-linkage.yaml` (inputs: image_sha, outputs: sbom_ref, invariant: sbom_ref digest matches image digest, FR-008 reference).
- [x] T048 Add contract descriptor `specs/003-tag-api-container/contracts/signature-verification.yaml` codifying soft verification semantics (fields: signature_status, signature_reason; no-fail policy) linking FR-011.
 - [x] T049 Add short tag parity test `tests/contract/test_short_tag_parity.py` ensuring 12-char short tag resolves to same digest as full 40-char SHA (both simulated lookups).
 - [x] T050 Add single-arch manifest test `tests/contract/test_single_arch_manifest.py` asserting only linux/amd64 present (simulate manifest JSON) fulfilling FR-015 scope constraint.
 - [x] T051 Add staging vs canonical repo selection test `tests/contract/test_repo_selection_policy.py` (main branch -> canonical, feature branch -> staging) referencing FR-016.
 - [x] T052 Add metrics emission unit test `tests/unit/test_metrics_emission.py` verifying counters increment and include repository_type label.
 - [x] T053 Add foreign repo rejection security test `tests/security/test_foreign_repo_rejected.py` ensuring `ensure_repo_allowed` rejects unexpected repo prefixes.
 - [x] T054 Add structured log schema completeness test `tests/contract/test_log_schema_completeness.py` validating presence of required keys (image_sha, short_sha, image_digest, repository, repository_type, arch, signature_status, signature_reason, build_duration_sec).
- [ ] T055 Implement docs validation script `scripts/ci/validate_docs.sh` asserting `distribution.md` and `quickstart.md` mention: digest verification, rollback no-build, short tag parity, SBOM linkage, single-arch constraint, metrics counters.
- [ ] T056 Update `scripts/ci/emit_image_metadata.py` to include `arch` and `repository_type` fields; adjust related tests (T006, T054) accordingly.
- [ ] T057 Clarify T028 guard script description inline (no code duplication) documenting it is deployment-time digest & repo mapping check; ensure README references both build-time (T041) and deploy-time (T028) checks.
- [ ] T058 Add performance test `tests/perf/test_deploy_rollback_duration.py` (skippable) asserting simulated deploy <300s & rollback <120s capturing durations.
- [ ] T059 Update `docs/distribution.md` & quickstart (T027) adding sections for short tag parity, single-arch verification, SBOM linkage contract, metrics emission, and structured log field list.
- [ ] T060 Update `src/lib/observability.py` docstrings & README snippet to enumerate new counters & labels.

## Validation Checklist
- All contract tests (T006–T009) pass before modifying workflows (T016–T018)
- Integration build→deploy→rollback test (T010, T021) passes before docs are finalized (T023–T027)
- Security guards (FR-004, FR-009, FR-016, FR-017) enforced via tests and scripts (T028, T029)
- Performance smoke (T011, T033) within target thresholds
- Structured logs verified contain required fields (T006, T019)
 - Digest invariants enforced (T036–T042) and negative mismatch case covered (T038)
 - Rollback no-build invariant enforced (T039, T045) and codified in contract (T044)
 - Medium completeness: short tag parity (T049), single-arch verification (T050), repo selection (T051), SBOM linkage contract (T047), signature contract (T048), metrics tests (T052), foreign repo defense (T053), log schema completeness (T054), docs validation (T055), performance deploy/rollback timings (T058)

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
