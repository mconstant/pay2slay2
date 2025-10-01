# Data Model: Non-Dry Run Testing Environment

## Core Entities

### TestSession
Represents a bounded period of collaborative testing with defined scope and participants.

**Attributes**:
- `id`: UUID - Unique session identifier
- `name`: str - Human-readable session name
- `description`: str - Optional session description
- `status`: enum - ACTIVE, PAUSED, COMPLETED, FAILED
- `created_at`: datetime - Session creation timestamp
- `started_at`: datetime - When testing actually began
- `ended_at`: datetime - When session was completed/terminated
- `tester_id`: str - Identifier of the assigned tester
- `configuration`: dict - Session-specific configuration settings

**Relationships**:
- One-to-many with TestResult
- One-to-many with FeedbackReport
- One-to-many with IntegrationHealthStatus

**State Transitions**:
```
CREATED → ACTIVE (when tester starts testing)
ACTIVE → PAUSED (manual pause or system issue)
PAUSED → ACTIVE (resume testing)
ACTIVE → COMPLETED (successful completion)
ACTIVE → FAILED (critical failure requiring termination)
PAUSED → FAILED (timeout or manual termination)
```

### IntegrationEndpoint
External service connections that process real transactions and return live data.

**Attributes**:
- `id`: UUID - Unique endpoint identifier
- `name`: str - Service name (yunite, discord, banano, wallet, admin)
- `base_url`: str - Base URL for the service
- `health_check_url`: str - Specific health check endpoint
- `auth_type`: enum - NONE, API_KEY, OAUTH, BEARER_TOKEN
- `rate_limit_per_minute`: int - Maximum requests per minute
- `timeout_seconds`: int - Request timeout configuration
- `retry_attempts`: int - Maximum retry attempts
- `enabled`: bool - Whether endpoint is active for testing

**Relationships**:
- One-to-many with IntegrationHealthStatus
- One-to-many with TestResult

### IntegrationHealthStatus
Real-time monitoring data showing availability, response times, and error rates.

**Attributes**:
- `id`: UUID - Unique status record identifier
- `endpoint_id`: UUID - Foreign key to IntegrationEndpoint
- `session_id`: UUID - Foreign key to TestSession
- `status`: enum - HEALTHY, DEGRADED, UNHEALTHY, TIMEOUT
- `response_time_ms`: int - Response time in milliseconds
- `status_code`: int - HTTP status code received
- `error_message`: str - Error details if unhealthy
- `checked_at`: datetime - When health check was performed
- `metadata`: dict - Additional service-specific health data

**Relationships**:
- Many-to-one with IntegrationEndpoint
- Many-to-one with TestSession

### TestResult
Results of executing specific test workflows against integrations.

**Attributes**:
- `id`: UUID - Unique test result identifier
- `session_id`: UUID - Foreign key to TestSession
- `endpoint_id`: UUID - Foreign key to IntegrationEndpoint
- `test_name`: str - Name of the test workflow executed
- `status`: enum - PASSED, FAILED, SKIPPED, ERROR
- `started_at`: datetime - Test execution start time
- `completed_at`: datetime - Test completion time
- `request_data`: dict - Data sent to external service
- `response_data`: dict - Response received from service
- `assertions`: list - List of assertion results
- `error_details`: str - Error information if test failed

**Relationships**:
- Many-to-one with TestSession
- Many-to-one with IntegrationEndpoint

### FeedbackReport
Structured documentation of issues, observations, and recommendations from testing activities.

**Attributes**:
- `id`: UUID - Unique feedback identifier
- `session_id`: UUID - Foreign key to TestSession
- `title`: str - Brief issue/observation title
- `description`: str - Detailed feedback description
- `category`: enum - INTEGRATION, UX, PERFORMANCE, SECURITY, OTHER
- `priority`: enum - LOW, MEDIUM, HIGH, CRITICAL
- `status`: enum - OPEN, IN_PROGRESS, RESOLVED, CLOSED
- `github_issue_number`: int - Associated GitHub issue number
- `github_issue_url`: str - Direct link to GitHub issue
- `reported_by`: str - Identifier of person who reported
- `reported_at`: datetime - When feedback was submitted
- `resolved_at`: datetime - When issue was resolved
- `metadata`: dict - Additional context data

**Relationships**:
- Many-to-one with TestSession
- One-to-many with FeedbackAttachment

### FeedbackAttachment
Files or screenshots attached to feedback reports.

**Attributes**:
- `id`: UUID - Unique attachment identifier
- `feedback_id`: UUID - Foreign key to FeedbackReport
- `filename`: str - Original filename
- `file_path`: str - Storage path for the file
- `content_type`: str - MIME type of the file
- `file_size`: int - Size in bytes
- `uploaded_at`: datetime - Upload timestamp

**Relationships**:
- Many-to-one with FeedbackReport

## Data Relationships

```
TestSession 1──────── * IntegrationHealthStatus
     │                        │
     │                        │
     │                        * ────────── 1 IntegrationEndpoint
     │                                            │
     * ────────── TestResult * ───────────────────┘
     │
     * ────────── FeedbackReport 1──────── * FeedbackAttachment
```

## Validation Rules

### TestSession
- `name` must be unique within active sessions
- `ended_at` must be after `started_at` when both are set
- Only one session can be ACTIVE per tester at a time
- Configuration must contain valid JSON

### IntegrationEndpoint
- `base_url` must be valid HTTP/HTTPS URL
- `health_check_url` must be valid URL
- `rate_limit_per_minute` must be positive integer
- `timeout_seconds` must be between 1 and 300
- `retry_attempts` must be between 0 and 10

### IntegrationHealthStatus
- `response_time_ms` must be non-negative
- `status_code` must be valid HTTP status code (100-599)
- `checked_at` cannot be in the future

### TestResult
- `completed_at` must be after `started_at` when both are set
- `request_data` and `response_data` must be valid JSON
- `assertions` must be a list of objects with 'name', 'expected', 'actual', 'passed' fields

### FeedbackReport
- `title` cannot be empty
- `description` cannot be empty
- `github_issue_number` must be positive integer when set
- `resolved_at` can only be set when status is RESOLVED or CLOSED

## Storage Schema

### Database Tables
Using SQLAlchemy with existing SQLite database, with migration support for production PostgreSQL.

### Indexes
- `test_sessions.status` - For filtering active sessions
- `integration_health_status.checked_at` - For time-series queries
- `integration_health_status.endpoint_id, checked_at` - For endpoint health history
- `test_results.session_id, completed_at` - For session test history
- `feedback_reports.status, priority` - For feedback queue management
- `feedback_reports.github_issue_number` - For GitHub integration lookups

### Data Retention
- Health status records: Keep latest 1000 per endpoint, archive older records
- Test results: Keep for duration of session + 30 days
- Feedback reports: Keep indefinitely (linked to GitHub issues)
- Session data: Keep for 90 days after completion

## Data Access Patterns

### Real-time Monitoring
- Frequent reads of latest IntegrationHealthStatus per endpoint
- WebSocket subscriptions to health status changes
- Dashboard aggregation queries for status summaries

### Test Execution
- Session-scoped reads and writes during active testing
- Batch inserts for test results and health checks
- Transaction isolation for test data consistency

### Feedback Management
- CRUD operations on feedback reports
- GitHub API integration for issue creation/updates
- Search and filtering capabilities for feedback history

### Reporting
- Aggregation queries for session summaries
- Time-series analysis of integration health trends
- Export capabilities for stakeholder review