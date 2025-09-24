# Feature Specification: [FEATURE NAME]

**Feature Branch**: `[###-feature-name]`  
**Created**: [DATE]  
**Status**: Draft  
**Input**: User description: "$ARGUMENTS"

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

Additional mandatory guidance: Every spec MUST include explicit UX Acceptance Criteria (if feature is user-facing) and Performance Targets (if feature impacts latency/throughput/resource usage). When these sections are not applicable, state `N/A` with rationale.
Security is first-class: Every spec MUST include a Security Considerations section. When decentralized distribution or blockchain elements apply, explicitly mark applicability and include the required details in their sections below.

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")
 
**Mandatory sections updated for constitution alignment**:
- User Scenarios & Testing (mandatory)
- Requirements (mandatory) — all FRs MUST be testable and measurable
- UX Acceptance Criteria (mandatory if user-facing)
- Performance Targets (mandatory if feature has performance impact)
- Security Considerations (mandatory)
- Decentralized Distribution / Blockchain Applicability (conditional)

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies  
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
[Describe the main user journey in plain language]

### Acceptance Scenarios
1. **Given** [initial state], **When** [action], **Then** [expected outcome]
2. **Given** [initial state], **When** [action], **Then** [expected outcome]

### Edge Cases
- What happens when [boundary condition]?
- How does system handle [error scenario]?

### UX Acceptance Criteria (if applicable)
- Visual expectations: [screens, components, states]
- Accessibility requirements: keyboard nav, ARIA roles, color contrast
- Success metrics: conversion, error rate, response time targets

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: System MUST [specific capability, e.g., "allow users to create accounts"]
- **FR-002**: System MUST [specific capability, e.g., "validate email addresses"]  
- **FR-003**: Users MUST be able to [key interaction, e.g., "reset their password"]
- **FR-004**: System MUST [data requirement, e.g., "persist user preferences"]
- **FR-005**: System MUST [behavior, e.g., "log all security events"]

*Example of marking unclear requirements:*
- **FR-006**: System MUST authenticate users via [NEEDS CLARIFICATION: auth method not specified - email/password, SSO, OAuth?]
- **FR-007**: System MUST retain user data for [NEEDS CLARIFICATION: retention period not specified]

### Key Entities *(include if feature involves data)*
- **[Entity 1]**: [What it represents, key attributes without implementation]
- **[Entity 2]**: [What it represents, relationships to other entities]

## Security Considerations *(mandatory)*
- Threat model summary: [assets, actors, entry points]
- Sensitive data handling: [PII/keys/secrets storage, encryption at rest/in transit]
- Secrets management: [where stored, rotation policy]
- Dependency and supply chain risks: [notable libs, native code, crypto]
- Abuse/misuse cases and mitigations

## Decentralized Distribution / Blockchain Applicability *(conditional)*
If the feature uses decentralized distribution or blockchain, specify:
- Distribution topology and trust model: [P2P/federated/content-addressed]
- Artifact signing and reproducible builds: [signing scheme, verification]
- Upgrade/migration strategy
- On-chain vs off-chain responsibilities
- Gas/fee impact and constraints (if on-chain)
- Audit requirements and status (if smart contracts)

If not applicable, state: `N/A` with a brief rationale.

## Performance Targets (if applicable)
- Declare measurable targets (latency p50/p95/p99, throughput, memory/CPU budgets)
- List performance test(s) that will validate targets and where they will run (CI, staging)

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs) unless justified
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed, including UX & Performance where applicable
 - [ ] Security Considerations completed
 - [ ] Decentralized/Blockchain section completed or explicitly N/A

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Performance targets present when applicable
- [ ] Accessibility/UX criteria present when applicable
 - [ ] Licensing constraints identified (if any new dependencies)

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [ ] No implementation details (languages, frameworks, APIs)
- [ ] Focused on user value and business needs
- [ ] Written for non-technical stakeholders
- [ ] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous  
- [ ] Success criteria are measurable
- [ ] Scope is clearly bounded
- [ ] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed

---
