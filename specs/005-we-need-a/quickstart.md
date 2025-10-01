# Quickstart: Non-Dry Run Testing Environment

## Overview
This quickstart guide walks through setting up and using the collaborative testing environment with live integrations for the pay2slay2 system.

## Prerequisites
- Python 3.13+ with pip
- Docker (for containerized deployment)
- Access to external integration services:
  - Yunite API credentials
  - Discord OAuth application
  - Banano node connection
  - Wallet service access
  - Admin service credentials
- GitHub personal access token or GitHub App for issue integration

## Quick Setup

### 1. Environment Configuration
Create a `.env` file in the project root:

```bash
# Testing Environment Configuration
TESTING_MODE=non_dry_run
TESTING_DATABASE_URL=sqlite:///testing.db

# External Integration Endpoints
YUNITE_API_URL=https://api.yunite.io
YUNITE_API_KEY=your_yunite_api_key
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret
DISCORD_REDIRECT_URI=http://localhost:8000/auth/discord/callback
BANANO_NODE_URL=https://api.banano.land
WALLET_SERVICE_URL=https://wallet.example.com
ADMIN_SERVICE_URL=https://admin.example.com

# GitHub Integration
GITHUB_TOKEN=your_github_personal_access_token
GITHUB_REPO=mconstant/pay2slay2

# Performance Settings
HEALTH_CHECK_INTERVAL=30
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=30
```

### 2. Install Dependencies
```bash
# Install testing environment dependencies
pip install -e .
pip install pytest-asyncio aiohttp websockets pygithub tenacity

# Run database migrations
alembic upgrade head
```

### 3. Start the Testing Environment
```bash
# Start the testing API server
python -m src.api.app --testing-mode

# In another terminal, start the dashboard
python -m src.testing.dashboard_server
```

## Testing Workflow

### Step 1: Create a Test Session
```bash
# Using curl to create a test session
curl -X POST http://localhost:8000/testing/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "End-to-End Integration Test",
    "description": "Testing all integrations with real endpoints",
    "tester_id": "test-user-001",
    "configuration": {
      "enable_all_integrations": true,
      "auto_create_github_issues": true
    }
  }'
```

Expected response:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "End-to-End Integration Test",
  "status": "ACTIVE",
  "created_at": "2025-09-30T10:00:00Z",
  "tester_id": "test-user-001"
}
```

### Step 2: Monitor Integration Health
```bash
# Check health of all integrations
curl http://localhost:8000/testing/integrations

# Check specific integration health
curl http://localhost:8000/testing/integrations/{endpoint_id}/health
```

Expected response for healthy integration:
```json
{
  "status": "HEALTHY",
  "response_time_ms": 150,
  "status_code": 200,
  "checked_at": "2025-09-30T10:01:00Z",
  "metadata": {
    "service_version": "1.2.3",
    "region": "us-east-1"
  }
}
```

### Step 3: Execute Test Workflows

#### Test Yunite Integration
```bash
curl -X POST http://localhost:8000/testing/sessions/{session_id}/results \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "yunite-endpoint-id",
    "test_name": "yunite_user_lookup",
    "test_data": {
      "user_id": "test_user_123"
    }
  }'
```

#### Test Discord OAuth Flow
```bash
curl -X POST http://localhost:8000/testing/sessions/{session_id}/results \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "discord-endpoint-id", 
    "test_name": "discord_oauth_flow",
    "test_data": {
      "user_id": "test_user_123",
      "scope": ["identify", "email"]
    }
  }'
```

#### Test Banano Payment
```bash
curl -X POST http://localhost:8000/testing/sessions/{session_id}/results \
  -H "Content-Type: application/json" \
  -d '{
    "endpoint_id": "banano-endpoint-id",
    "test_name": "banano_payment",
    "test_data": {
      "recipient_address": "ban_test123...",
      "amount": "1.0",
      "memo": "Test payment"
    }
  }'
```

### Step 4: Access Testing Dashboard
Open your browser to `http://localhost:8000/testing/dashboard` to view:
- Real-time integration health status
- Test execution progress
- Live test results
- Integration response times

### Step 5: Submit Feedback
```bash
curl -X POST http://localhost:8000/testing/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "title": "Banano node slow startup",
    "description": "Banano integration takes 45+ seconds to respond during initial startup, exceeding 30-second timeout threshold.",
    "category": "PERFORMANCE",
    "priority": "MEDIUM",
    "reported_by": "test-user-001",
    "metadata": {
      "affected_endpoint": "banano",
      "response_time": 47000,
      "error_type": "timeout"
    }
  }'
```

Expected response:
```json
{
  "id": "feedback-uuid",
  "github_issue_number": 123,
  "github_issue_url": "https://github.com/mconstant/pay2slay2/issues/123",
  "status": "OPEN",
  "reported_at": "2025-09-30T10:15:00Z"
}
```

## Validation Steps

### Integration Health Validation
```bash
# All integrations should be healthy
curl http://localhost:8000/testing/integrations | jq '.[] | select(.enabled == true) | .name + ": " + .status'

# Expected output:
# "yunite: HEALTHY"
# "discord: HEALTHY" 
# "banano: HEALTHY"
# "wallet: HEALTHY"
# "admin: HEALTHY"
```

### Test Result Validation
```bash
# All test workflows should pass
curl http://localhost:8000/testing/sessions/{session_id}/results | jq '.[] | .test_name + ": " + .status'

# Expected output:
# "yunite_user_lookup: PASSED"
# "discord_oauth_flow: PASSED"
# "banano_payment: PASSED"
# "wallet_balance_check: PASSED"
# "admin_user_creation: PASSED"
```

### Feedback Integration Validation
```bash
# Check that GitHub issue was created
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/mconstant/pay2slay2/issues | \
  jq '.[] | select(.title | contains("Banano node slow startup"))'
```

## Real-time Monitoring

### WebSocket Connection
```javascript
// Connect to real-time dashboard updates
const ws = new WebSocket('ws://localhost:8000/testing/dashboard/ws');

ws.onmessage = function(event) {
  const update = JSON.parse(event.data);
  console.log('Dashboard update:', update);
  
  // Handle different update types
  switch(update.type) {
    case 'health_status_update':
      updateHealthIndicator(update.data);
      break;
    case 'test_result':
      addTestResult(update.data);
      break;
    case 'feedback_submitted':
      showFeedbackConfirmation(update.data);
      break;
  }
};
```

### Performance Metrics
Monitor key performance indicators:
- Integration response times < 30 seconds
- Test environment uptime > 99.5%
- Feedback submission latency < 2 seconds
- Health check frequency every 30 seconds

## Troubleshooting

### Common Issues

#### Banano Node Slow Startup
**Symptom**: Health checks timeout for Banano integration
**Solution**: Increase timeout for Banano endpoint to 60 seconds during startup
```bash
curl -X PATCH http://localhost:8000/testing/integrations/banano \
  -d '{"timeout_seconds": 60}'
```

#### GitHub Issue Creation Fails
**Symptom**: Feedback submission succeeds but no GitHub issue created
**Solution**: Verify GitHub token has `repo` and `issues` permissions
```bash
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user/repos | jq '.[0].permissions'
```

#### Rate Limiting Triggered
**Symptom**: External service returns 429 Too Many Requests
**Solution**: Check rate limit configuration and current usage
```bash
curl http://localhost:8000/testing/integrations/{endpoint_id}/rate-limit-status
```

### Recovery Procedures

#### Reset Test Session
```bash
# Mark current session as failed and create new one
curl -X PATCH http://localhost:8000/testing/sessions/{session_id} \
  -d '{"status": "FAILED"}'

# Create fresh session
curl -X POST http://localhost:8000/testing/sessions \
  -d '{"name": "Recovery Session", "tester_id": "test-user-001"}'
```

#### Clear Test Data
```bash
# Clean up test artifacts (preserves feedback/GitHub issues)
curl -X DELETE http://localhost:8000/testing/sessions/{session_id}/cleanup
```

## Success Criteria
✅ All 5 integrations report HEALTHY status  
✅ End-to-end test workflows complete successfully  
✅ Real-time dashboard updates function correctly  
✅ Feedback submission creates GitHub issues automatically  
✅ Performance targets met (response times, uptime, etc.)  
✅ Test session can be paused/resumed without data loss  
✅ Rate limiting handles external service quotas gracefully  

## Next Steps
After successful validation:
1. Deploy to staging environment for extended testing
2. Configure production-like integration credentials
3. Set up monitoring and alerting for production deployment
4. Train manual testers and product owners on the testing workflow