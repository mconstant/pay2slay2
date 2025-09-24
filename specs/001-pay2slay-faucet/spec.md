# Feature Specification: Pay2Slay Faucet

**Feature Branch**: `001-pay2slay-faucet`  
**Created**: 2025-09-24  
**Status**: Draft  
**Input**: User description: "/plan The application uses Yunite to register and check EpicIDs of users, the Fortnite API to check their kills in fortnite, pays the users in banano using a Banano Node and Pippen, infrastructure is deployed on Akash Network, the frontend for users is a webapp that allows them to register their EpicID and link it to a Banano wallet. This all should be made as a repository meant to be shared as open source, deployable by any user that chooses to run this Pay2Slay Faucet, it should therefore also be customizable as a sort of WhiteLabel experience where a user can specify their name or their organization's name and load in a banner or mediakit to run it on their own and own their instance personally"

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

## Clarifications
### Session 2025-09-24
- Q: What payout policy should we use for v1? → A: Threshold-based per verified session
- Q: Allowed kill counting scope? → A: All modes, any time
- Q: Threshold and caps application? → A: 20 kills = 1 payout; max 1 payout/day; max 3 payouts/week; payouts processed every 20 minutes (still capped)
- Q: YAML configuration scope and structure? → A: Three YAMLs: payout.yaml (A), integrations.yaml (C), product.yaml (D)
- Q: Payout amount? → A: 2.1 BAN per kill for a qualifying session (payout triggered once session reaches threshold)
- Update: Do not wait for a session to hit 20 kills. Instead, on a configurable interval, run a settlement that pays all arrears to all users owed, by settling each user's kill delta since last settlement (only verified users with EpicID and wallet), processing users in random order. This supersedes the 20‑kill session trigger.
- Identity proof: Users MUST authenticate via Discord, be a member of the specified Discord server where Yunite is installed, and have their EpicID linked to their Discord account via Yunite. Verification relies on Yunite's mapping of Discord user → EpicID.
- KYC/eligibility: No KYC required. Collect regional statistics solely to detect potential regional abuse patterns; do not gate eligibility based on region.
- Operator wallet floor: Default minimum operator balance is 50 BAN before settlements execute.

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

---

## User Scenarios & Testing (mandatory)

### Primary User Story
As a Fortnite player, I want to link my EpicID and Banano wallet so that I can automatically receive Banano payouts based on my verified Fortnite kills.

### Acceptance Scenarios
1. Given a user with a valid EpicID and Banano wallet, When they register and link accounts, Then the system confirms linkage and shows payout eligibility status.
2. Given a linked user with N verified kills, When payout criteria are met, Then the system schedules and executes a Banano payout and records a receipt.

### Edge Cases
- Invalid or unverified EpicID.
- Duplicate account linking attempts (same EpicID or same Banano wallet linked to multiple accounts).
- Fortnite API or Yunite downtime/rate-limits.
- Discord OAuth fails or user not a member of the configured guild.
- User leaves the Discord guild after linking; eligibility should be revoked until they rejoin and re-verify.
- Yunite mapping stale or removed; payouts blocked until re-verified.
- Unknown or ambiguous region (e.g., VPN/Tor) — count as "unknown" and include in aggregates without blocking eligibility.
- Invalid Banano address format or wallet not reachable.
- Payout failure (insufficient funds, network issue, node out of sync).
- Cheating/abuse detection (e.g., botting, kill farming, time-window abuse).
- No minimum threshold: small kill deltas may accrue; payout occurs on next settlement.
- Daily/weekly caps may cause partial settlement; unpaid remainder rolls over.
- Settlement randomization ensures fairness when batch_size < total users; users not processed roll over to next run.
- Idempotency must prevent duplicate payments after retries.

### UX Acceptance Criteria (if applicable)
- Users can:
  - Enter EpicID and Banano wallet address with validation and clear error states.
  - View linkage status and last verification timestamp.
  - View accrued rewards, payout thresholds, and payout history.
- Accessibility: keyboard navigable, semantic headings, color contrast AA.
- Theming/WhiteLabel: configurable app name, org name, banner/media kit assets displayed in header and share cards.

## Requirements (mandatory)

### Functional Requirements
- FR-001: System MUST allow users to register with EpicID and link a Banano wallet.
- FR-002: System MUST verify EpicID ownership via Yunite and retrieve kill counts via the Fortnite API.
- FR-003: System MUST accrue rewards per kill at 2.1 BAN/kill and, on each scheduler interval, compute each verified user's unsettled kill delta since last settlement and pay the corresponding amount, subject to caps and idempotency.
- FR-004: System MUST execute Banano payouts via a Banano node using Pippen (or compatible client) and record receipts.
- FR-005: System MUST provide an admin view to monitor linkage status, payouts, and system health.
- FR-006: System MUST expose an API for linkage, verification status, rewards, and payout history.
- FR-007: System MUST provide a whitelabel configuration (name, org, banner/media kit) and apply it to UI and share metadata.
- FR-008: System MUST make deployment artifacts suitable for Akash Network.
- FR-009: System MUST support reproducible, open-source friendly deployment (docs, LICENSE, sample configs).
- FR-010: System MUST persist user profiles, wallet links, verification records, reward accruals, and payout receipts.
- FR-011: System MUST provide an audit trail for verification and payouts (timestamps, amounts, tx hashes).
- FR-012: System MUST provide a self-serve re-verify action and manual re-try payout action (with safeguards).
- FR-013: System MUST provide rate-limit protection and abuse detection heuristics.
- FR-014: System MUST provide observability: structured logs, metrics for payouts/verifications, and tracing for critical flows.
- FR-015: System MUST provide a configuration to toggle testnet/mainnet for Banano and dry-run mode for payouts.
- FR-016: System MUST support i18n-ready copy for whitelabel deployments.
- FR-017: System MUST expose OpenAPI schema for all public APIs.
- FR-018: System MUST provide a quickstart guide for operators deploying their own faucet instance.
- FR-019: Kill counting applies to all modes at all times (24/7), subject to anti‑abuse protections.
- FR-020: Settlement cadence and caps: scheduler runs every 20 minutes (configurable); max 1 payout per user per day; max 3 payouts per user per week; caps reset at 00:00 UTC daily and Monday 00:00 UTC weekly.
- FR-021: Configuration MUST be provided via three YAML files loaded at startup:
  - payout.yaml: { payout_amount_ban_per_kill, scheduler_minutes, daily_payout_cap, weekly_payout_cap, reset_tz, settlement_order, batch_size }
  - integrations.yaml: { chain_env, node_rpc, min_operator_balance_ban, dry_run, yunite_api_key, yunite_guild_id, discord_guild_id, discord_oauth_client_id, discord_oauth_client_secret, discord_redirect_uri, oauth_scopes, fortnite_api_key, rate_limits, abuse_heuristics }
  - product.yaml: { app_name, org_name, banner_url, media_kit_url, default_locale, feature_flags }
  Defaults MUST match clarified policy above (payout_amount_ban_per_kill=2.1, scheduler_minutes=20, daily_payout_cap=1, weekly_payout_cap=3, reset_tz=UTC, settlement_order=random, batch_size=0 meaning unlimited, min_operator_balance_ban=50, oauth_scopes=["identify","guilds"]) ; secrets MUST be injected via secret store, not committed.
- FR-022: Settlement MUST process eligible users in random order per run, be idempotent (no double-paying the same kills), persist a per-user cursor (e.g., last_settled_kill_count and last_settlement_at), and enforce caps before issuing payments; if caps would be exceeded, partial or zero payout MUST be applied and the remainder deferred.
- FR-023: Users MUST authenticate via Discord OAuth2 and MUST be members of the configured Discord server; only such users are eligible for verification and payout.
- FR-024: The system MUST confirm EpicID ownership by querying Yunite for the authenticated Discord user and verifying the presence of a linked EpicID; absence or mismatch MUST block payouts until resolved.
- FR-025: The system MUST allow re-linking or updating the EpicID association via Yunite and provide a re-verify flow to refresh the mapping; changes MUST take effect on the next verification run.
- FR-026: The system MUST collect regional statistics for abuse detection in a privacy-preserving manner (e.g., aggregate by country/region code without storing raw IPs), and expose dashboards/metrics; eligibility MUST NOT be gated by region.

### Key Entities (include if feature involves data)
- User: id, epic_id, status, created_at
- WalletLink: user_id, banano_address, verified_at, status, chain_env
- VerificationRecord: user_id, source (Yunite/Fortnite), kills, period, verified_at
- RewardAccrual: user_id, period, kills_counted, reward_amount, calculated_at
- Payout: user_id, amount, tx_hash, status, attempted_at, completed_at, failure_reason
- AdminUser/Operator: id, roles, audit actions

### Outstanding Clarifications
- None

## Security Considerations (mandatory)
- Threat model summary: user auth/verification endpoints, payout execution path, node access.
- Sensitive data handling: store minimal PII; secure storage for API keys and wallet seeds (never in repo).
- Secrets management: use secret store or Akash secrets; define rotation policy.
- OAuth security: request least-privilege Discord scopes (identify, guilds), validate OAuth state and redirect URIs, avoid storing long-lived tokens when not required.
- No KYC: do not collect government IDs; avoid storing unnecessary personal data.
- Regional analytics privacy: derive coarse region codes (e.g., ISO country) without retaining raw IPs; aggregate metrics; document retention and opt-out.
- Dependency and supply chain risks: SDKs for Yunite, Fortnite, Banano client; ensure license compatibility.
- Abuse/misuse: bot detection, kill farming detection; admin controls and audit logs.

## Decentralized Distribution / Blockchain Applicability (conditional)
- Distribution: target Akash Network; document deploy topology, artifact signing, and upgrade plan. [NEEDS CLARIFICATION]
- Blockchain: Banano payments; define on/off-chain responsibilities (off-chain verification; on-chain payouts). [NEEDS CLARIFICATION]
- Gas/fee constraints: Banano specifics and node requirements (no fees vs. workload). [NEEDS CLARIFICATION]
- Audit: smart contracts not in scope (payments via node), but perform security review of payout module. [NEEDS CLARIFICATION]

## Performance Targets (if applicable)
- API p95 latency: < 300ms for linkage and status endpoints.
- Verification batch processing: >= 50 users/minute at p95 < 2s per verification.
- Payout executor: queue throughput >= 10 payouts/minute with idempotency; retries exponential backoff.
- Node resource budget: Banano node container memory < 512MB; CPU < 1 vCPU average.

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

## Execution Status
*Updated by main() during processing*

- [ ] User description parsed
- [ ] Key concepts extracted
- [ ] Ambiguities marked
- [ ] User scenarios defined
- [ ] Requirements generated
- [ ] Entities identified
- [ ] Review checklist passed
