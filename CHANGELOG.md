# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Donations system** — DonationLedger model, donation tracking service with 10 milestone tiers (Fresh Spawn 1x → Potassium Singularity 3x), donation progress API endpoint, payout multiplier driven by community donations toward 1M BAN goal.
- **Leaderboard & activity feed** — Public `/api/leaderboard`, `/api/feed`, `/api/donate-info`, `/api/scheduler/countdown` endpoints. Live leaderboard with kills, earnings, and recent activity.
- **Demo mode** — `/auth/demo-login`, `/demo/seed`, `/demo/run-scheduler`, `/demo/clear` for local testing without real APIs.
- **Admin panel expansion** — Scheduler control (`trigger`, `settle`, `status`, `config`), payout config (`ban_per_kill`, caps), operator seed management (encrypted via SecureConfig), audit log, system stats, extended health check.
- **User endpoints** — `/me/payouts`, `/me/accruals`, `/me/reverify` for self-service.
- **SecureConfig model** — Encrypted key-value store for sensitive runtime configuration.
- **Frontend SPA** — Vanilla JS single-page app with hash routing: leaderboard, donations page with thermometer, activity feed, wallet linking, login hero.
- **Banano brand theme** — Official press kit colors (Yellow #FBDD11, Green #4CBF4B), Overpass Mono font, gradient header, card hover glow.
- **Flapping stickers** — Animated GitHub, Banano, and Kalium wallet icons.
- **PAY2SLAY brand treatment** — Split-color logo text, floating logo on login, tactical gaming-inspired UI touches.
- Immutable SHA tagging workflows with digest verification guards.
- Soft signature verification and structured image metadata artifact.
- Deployment-time repository mapping & floating tag rejection.
- Akash deployment: auto-selection of cheapest audited providers, UI URL extraction, post-deployment health checks.

### Changed
- Leaderboard table: merged Accrued+Paid into single "Earned" column, removed Date column, linked tx hashes to Banano creeper.
- Accrual now applies milestone payout multiplier (1x–3x based on donation progress).
- Documentation fully rewritten for accuracy and conciseness.

## [0.2.0] - 2025-09-25
### Added
- Split Akash deployments: separate Banano node and API Terraform stacks.
- Banano discovery script with retry/backoff and structured logging.
- Endpoint validation script and artifact contract.
- GitHub Actions workflows: `banano-deploy.yml`, `api-deploy.yml`.
- Operations guide for split deployments.
- Terraform linting workflow.

### Security
- Artifact contains no secrets; validation hardened with explicit host/port rules.

## [0.1.0] - 2025-09-25
- Initial release (baseline prior to split deployments feature).
