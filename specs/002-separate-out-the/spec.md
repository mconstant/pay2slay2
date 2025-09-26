# Feature Specification: Split Akash Deployments (Banano Node & API Separation)

**Feature Branch**: `002-separate-out-the`  
**Created**: 2025-09-25  
**Status**: Draft  
**Input**: User description: "separate out the akash stack into discrete deployments. the banano node needs it's own deployment workflow and separate akash sdl. I need to have the banano_rpc_endpoint as a terraform output and available as an input for the api deployment."

## Clarifications
### Session 2025-09-25
- Q: What retry strategy and total timeout should the Banano deployment workflow use to discover the forwarded RPC port (7072) before declaring failure? → A: Exponential backoff 5s,10s,20s,40s (4 attempts, ~75s max)

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As an operator, I want the Banano blockchain node and the Faucet API deployed as independent Akash deployments so that I can upgrade, scale, or restart either without impacting the other, while automatically wiring the API to the active Banano node RPC endpoint.

### Acceptance Scenarios
1. **Given** a successful Banano node deployment, **When** the workflow completes, **Then** the Terraform outputs include a `banano_rpc_endpoint` value representing `host:external_port` for internal RPC port 7072.
2. **Given** an existing Banano deployment with an exposed RPC endpoint, **When** I trigger the API deployment workflow, **Then** the workflow is able to consume (via input, variable, or fetched artifact) the `banano_rpc_endpoint` and inject it into API configuration.
3. **Given** the Banano deployment is redeployed (endpoint changes), **When** I run the API deployment again providing the new endpoint, **Then** the API uses the updated endpoint without residual references to the old one.
4. **Given** the Banano deployment is still provisioning (endpoint not yet available), **When** the Banano workflow finishes, **Then** it retries for a bounded time and fails clearly if the endpoint never materializes.
5. **Given** a failed Banano deployment (no forwarded port for 7072), **When** the workflow finishes, **Then** it fails and does NOT publish a stale or empty `banano_rpc_endpoint` artifact.

### Edge Cases
- Forwarded ports appear with delay → Banano workflow must implement retry with backoff.
- Multiple forwarded ports including 7071 & 7074 (non-RPC) → Only 7072 mapped to endpoint output.
- Endpoint host blank or placeholder → Treat as failure (no output artifact).
- API workflow invoked without providing endpoint → Hard fail with descriptive message.
- Later migration to secure RPC (TLS) → Output still provides host:port; scheme selection deferred to API config logic.

### UX Acceptance Criteria
Not a user-facing UI feature; surfaced only through CI workflow logs and Terraform outputs. Success criteria framed as operational clarity and deterministic outputs:
- Logs clearly label “Banano RPC endpoint resolved: <host:port>”.
- API workflow run summary echoes the consumed endpoint.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: Banano Terraform stack MUST be isolated in its own directory (e.g., `infra/akash-banano/`) with a dedicated SDL containing ONLY the Banano service.
- **FR-002**: API Terraform stack MUST exclude Banano service and accept an input variable `banano_rpc_endpoint`.
- **FR-003**: Banano deployment workflow MUST output a Terraform output named `banano_rpc_endpoint` capturing `host:external_port` associated with internal port 7072.
- **FR-004**: Banano workflow MUST attempt RPC port (7072) discovery with an exponential backoff schedule of 4 attempts at 5s, 10s, 20s, and 40s delays (≈75s max elapsed). After the 4th failed attempt it MUST hard-fail and NOT emit a partial/empty endpoint artifact.
- **FR-005**: On success, Banano workflow MUST persist the endpoint via artifact AND set a workflow output for downstream/manual copy.
- **FR-006**: API workflow MUST fail fast if `banano_rpc_endpoint` input is absent or empty.
- **FR-007**: API workflow MUST surface the injected endpoint in logs (redacting nothing—no secret content).
- **FR-008**: Changing Banano deployment MUST NOT require changes to API Terraform except updating the endpoint input.
- **FR-009**: Banano Terraform MUST expose ONLY necessary ports (7071, 7072, 7074) per initial design; any removal or addition requires explicit variable or documentation update.
- **FR-010**: Workflows MUST be independently triggerable via `workflow_dispatch` with clear inputs.
- **FR-011**: Banano workflow MUST mark failure if Terraform apply succeeds but no forwarded port 7072 is present.
- **FR-012**: Endpoint resolution MUST disallow an empty `host` value (validate non-whitespace host).
- **FR-013**: If multiple Banano deployments exist, the workflow MUST target exactly one state directory (no ambiguous merges).
- **FR-014**: Documentation MUST describe operator process: 1) Deploy Banano; 2) Copy or reference endpoint; 3) Deploy API with endpoint.
- **FR-015**: Terraform outputs for Banano MUST include `deployment_id` (unchanged) plus the new endpoint for traceability.

### Key Entities
- **Banano Deployment Output**: Conceptual artifact: `{ deployment_id, banano_rpc_endpoint }` consumed by API deployment operator.
- **API Deployment Input**: A simple string value representing the upstream Banano RPC endpoint (`host:port`).

## Security Considerations *(mandatory)*
- Threat model: Risk of pointing API to malicious or stale RPC endpoint if tampered artifact; mitigate by manual verification or future signing (out of scope now).
- Sensitive data: Endpoint is not a secret; no credential leakage risk.
- Secrets management: Unchanged from existing workflows (Akash mnemonic & cert remain in secrets store).
- Supply chain: Splitting deployments reduces blast radius—API redeploy cannot mutate Banano chain state container config.
- Abuse cases: An attacker altering endpoint to a hostile node could falsify balances/payout logic—future mitigation could include node identity verification or health probe (not in current scope).
- Automation / AI Execution Constraints: Workflows MUST NOT attempt destructive operations (e.g., purge unrelated deployments) when resolving endpoint. Limited to read outputs and parse JSON.

## Decentralized Distribution / Blockchain Applicability *(conditional)*
Applicable: The Banano node participates in a decentralized blockchain network.
- Off-chain vs on-chain: This feature manipulates off-chain deployment metadata only; no protocol-layer changes.
- Upgrade strategy: Independent redeploy of Banano node without API downtime.
- Artifact integrity: Future enhancement—image digest pinning & optional cosign verification.

## Performance Targets
- Endpoint discovery latency: 95% of runs resolve within 45s after Terraform apply.
- Added workflow overhead: < 1 minute average compared to combined stack baseline.
- No impact on API runtime latency; change is CI/CD only.

## Review & Acceptance Checklist
### Content Quality
- [ ] No implementation details leaking (spec intentionally avoids exact directory names beyond examples)
- [ ] Business value articulated (operational isolation)
- [ ] Mandatory sections filled
- [ ] Security section present
- [ ] Blockchain relevance addressed

### Requirement Completeness
- [ ] All FRs testable (each can be validated via workflow run + Terraform output inspection)
- [ ] No [NEEDS CLARIFICATION] markers
- [ ] Performance & UX (operational) criteria present
- [ ] Scope bounded: only separation + endpoint propagation

## Execution Status
- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked (none remaining)
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed
