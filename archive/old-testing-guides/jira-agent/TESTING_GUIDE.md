# Complete Testing Guide

This guide shows you how to test the JIRA agent at different levels, from local architecture validation to full production deployment.

## Testing Pyramid

```
                    ┌─────────────────────┐
                    │  Production Test    │  Slowest (5-10 min)
                    │  (Real OAuth + API) │  Requires: AWS + JIRA OAuth
                    └─────────────────────┘
                           ▲
                    ┌──────────────────────┐
                    │   AgentCore Local    │  Moderate (2-5 min)
                    │   (Full Integration) │  Requires: AWS credentials
                    └──────────────────────┘
                           ▲
                    ┌──────────────────────┐
                    │    AWS Bedrock       │  Fast (30-60 sec)
                    │   (LLM Inference)    │  Requires: AWS credentials
                    └──────────────────────┘
                           ▲
                    ┌──────────────────────┐
                    │   pytest Suite       │  Fast (~30 sec)
                    │   (89 tests)         │  Requires: Nothing
                    └──────────────────────┘
                           ▲
                    ┌──────────────────────┐
                    │   Architecture       │  Fastest (<5 sec)
                    │  (No AWS needed)     │  Requires: Nothing
                    └──────────────────────┘
```

---

## Level 1: Architecture Validation (No AWS Required)

**What it tests:** Auth abstraction, dependency injection, tool instantiation, agent factory

**Time:** <5 seconds
**Requires:** Nothing (runs completely offline)

### Setup
```bash
export AGENT_ENV=local
```

### Run Tests
```bash
uv run validate_architecture.py
```

### Expected Output
```
============================================================
✅ ALL ARCHITECTURE TESTS PASSED!
============================================================

Architecture validation complete:
  ✓ Auth abstraction layer working
  ✓ Dependency injection working
  ✓ Tool classes instantiate correctly
  ✓ Agent factory creates agent with all tools
  ✓ Mock authentication functional
  ✓ Protocol-based interfaces working
```

### When to Use
- ✅ After refactoring code structure
- ✅ Before committing code changes
- ✅ Quick validation during development
- ✅ CI/CD pipeline (no credentials needed)

---

## Level 2: Full Test Suite (No AWS Required)

**What it tests:** Authentication, tools, agent creation, all with mocked APIs

**Time:** ~30 seconds
**Requires:** Nothing (uses pytest-httpx for API mocking)

### Setup
```bash
export AGENT_ENV=local
```

### Run Tests
```bash
# All unit tests
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Test Categories
```bash
# Authentication tests (25 tests)
pytest tests/test_auth_*.py

# Tool tests (39 tests)
pytest tests/test_tools_*.py

# Agent tests (15 tests)
pytest tests/test_agent.py

# Skip integration tests (default)
pytest -m "not integration"

# Run integration tests (requires setup)
INTEGRATION_TESTS=true pytest -m integration
```

### Expected Output
```
==================== test session starts ====================
collected 89 items

tests/test_auth_mock.py ............ [10 tests]
tests/test_auth_agentcore.py ............... [15 tests]
tests/test_tools_tickets.py .................. [18 tests]
tests/test_tools_updates.py ..................... [21 tests]
tests/test_agent.py ............... [15 tests]
tests/integration/test_oauth_flow.py ssssssssss [10 skipped]

==================== 79 passed, 10 skipped in 28.43s ====================
```

### Test Coverage
- **MockJiraAuth**: 100%
- **AgentCoreJiraAuth**: >85%
- **JiraTicketTools**: >90%
- **JiraUpdateTools**: >90%
- **create_jira_agent**: 100%
- **Overall**: >85%

### When to Use
- ✅ After implementing new features
- ✅ Before commits and PRs
- ✅ Regular development workflow
- ✅ CI/CD pipeline
- ✅ Debugging tool logic

---

## Level 3: LLM Inference Testing (AWS Bedrock Required)

**What it tests:** Agent can interact with AWS Bedrock LLM, streaming works, tool selection logic

**Time:** 30-60 seconds
**Requires:** AWS credentials with Bedrock access

### Setup AWS Credentials

#### Option A: AWS SSO (Recommended)
```bash
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
export AWS_DEFAULT_REGION=ap-southeast-2
```

#### Option B: IAM User Credentials
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=ap-southeast-2
```

#### Option C: Temporary Credentials
```bash
# Get temporary credentials from STS
aws sts get-session-token

# Export the credentials
export AWS_ACCESS_KEY_ID=<AccessKeyId>
export AWS_SECRET_ACCESS_KEY=<SecretAccessKey>
export AWS_SESSION_TOKEN=<SessionToken>
export AWS_DEFAULT_REGION=ap-southeast-2
```

### Verify AWS Access
```bash
# Test AWS credentials
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region ap-southeast-2 --query "modelSummaries[?modelId=='anthropic.claude-3-5-sonnet-20241022-v2:0']"
```

### Run Tests
```bash
export AGENT_ENV=local

# Automated tests
uv run test_with_aws.py

# Or interactive mode
uv run python -c "
import asyncio
from test_with_aws import interactive_mode
asyncio.run(interactive_mode())
"
```

### Expected Output
```
============================================================
TEST: LLM Inference with AWS Bedrock
============================================================

✅ Agent created successfully
   Tools: 5 available

📝 Query: 'What tools do you have available?'

🤖 Agent Response:
------------------------------------------------------------
I'm a JIRA assistant with these tools:
- fetch_jira_ticket: Get ticket details
- parse_ticket_requirements: Extract requirements
- update_jira_status: Change ticket status
- add_jira_comment: Add comments
- link_github_issue: Link GitHub PRs/issues
------------------------------------------------------------

✅ LLM inference successful!
```

### What Will Fail
❌ **Actual JIRA API calls** - Mock token won't work with real JIRA API
✅ **LLM responses** - Agent can talk about what it would do
✅ **Tool selection** - Agent can decide which tools to use

### When to Use
- ✅ Test LLM behavior and responses
- ✅ Test streaming functionality
- ✅ Test tool selection logic
- ✅ Validate system prompt changes
- ✅ Test conversation flow

---

## Level 4: AgentCore Local Testing (Full Integration)

**What it tests:** Complete agent with OAuth flow, real JIRA API (optional)

**Time:** 2-5 minutes
**Requires:** AWS credentials, AgentCore CLI

### Setup
```bash
source .venv/bin/activate
export AGENT_ENV=local  # Use mock auth, or 'dev' for real OAuth
```

### Run with AgentCore
```bash
# Launch agent locally
agentcore launch --local

# In another terminal, invoke it
agentcore invoke --message "Get details for ticket PROJ-123"

# Or test OAuth flow with dev environment
export AGENT_ENV=dev
agentcore launch --local
agentcore invoke --user-id YOUR_USERNAME --message "Get details for ticket PROJ-123"
```

**Note:** Replace `YOUR_USERNAME` with any identifier (e.g., your email). The `--user-id` flag is required for OAuth authentication to work properly.

### Expected Flow

**With `AGENT_ENV=local` (Mock Auth):**
```
🔐 Initializing JIRA authentication...
🧪 Mock JIRA Auth initialized - LOCAL TESTING MODE
✅ JIRA authentication successful
🤖 I can help with JIRA tickets, status updates, and GitHub linking.
    To get ticket details, I'll use fetch_jira_ticket...
```

**With `AGENT_ENV=dev` (Real OAuth):**
```
🔐 Initializing JIRA authentication...
🔗 Please authorize at: https://auth.atlassian.com/authorize?...

[After you authorize in browser]
✅ JIRA authentication successful
✅ Retrieved cloud ID: 366af8cd-d73d-4eca-826c-8ce96624d1e7
🤖 Ticket PROJ-123: "Implement feature X"
   Status: In Progress
   Assignee: john.doe@company.com
```

### When to Use
- ✅ Test OAuth flow end-to-end
- ✅ Test with real JIRA API
- ✅ Test AgentCore Memory integration
- ✅ Test streaming responses through AgentCore
- ✅ Final validation before deployment

---

## Level 5: Development Deployment Testing

**What it tests:** Agent in real AgentCore environment

**Time:** 5-10 minutes
**Requires:** AWS credentials, AgentCore account, JIRA OAuth app

### Setup JIRA OAuth App

1. Go to https://developer.atlassian.com/console/myapps/
2. Create new OAuth 2.0 (3LO) app:
   - **App name:** JIRA Agent Dev
   - **Authorization callback URL:** https://agentcore-runtime-url/oauth/callback
3. Add permissions:
   - `read:jira-work`
   - `write:jira-work`
   - `offline_access`
4. Note the **Client ID** and **Client Secret**

### Configure AgentCore Identity

```bash
# Configure JIRA OAuth provider in AgentCore
agentcore identity create-provider \
  --name jira-provider \
  --type OAUTH2 \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --authorization-url https://auth.atlassian.com/authorize \
  --token-url https://auth.atlassian.com/oauth/token \
  --scopes read:jira-work,write:jira-work,offline_access
```

### Deploy
```bash
export AGENT_ENV=dev
agentcore deploy --agent jira-dev
```

### Test
```bash
# First invocation (will trigger OAuth)
agentcore invoke --agent jira-dev --user-id YOUR_USERNAME --message "Get details for ticket PROJ-123"

# Follow OAuth URL, authorize

# Second invocation (uses cached token)
agentcore invoke --agent jira-dev --user-id YOUR_USERNAME --message "Update PROJ-123 to In Progress"
```

### When to Use
- ✅ Test before production deployment
- ✅ Validate OAuth flow in real environment
- ✅ Test with real JIRA API
- ✅ Validate AgentCore Memory works
- ✅ Test error handling and edge cases

---

## Level 6: Production Deployment

**What it tests:** Agent in production

**Time:** 10+ minutes
**Requires:** Production AWS account, production JIRA OAuth app

### Deploy
```bash
export AGENT_ENV=prod
agentcore deploy --agent jira-prod --environment production
```

### Monitor
```bash
# View logs
agentcore logs --agent jira-prod

# Check CloudWatch
aws logs tail /aws/lambda/jira-agent-prod --follow
```

### Smoke Tests
```bash
# Test basic functionality
agentcore invoke --agent jira-prod --user-id YOUR_USERNAME --message "What can you help me with?"

# Test ticket fetch
agentcore invoke --agent jira-prod --user-id YOUR_USERNAME --message "Get details for ticket PROJ-123"

# Test status update
agentcore invoke --agent jira-prod --user-id YOUR_USERNAME --message "Update PROJ-123 to In Progress"
```

### When to Use
- ✅ Final production validation
- ✅ Smoke tests after deployment
- ✅ Verify monitoring and alerts
- ✅ Test with production data

---

## Quick Reference

### 🚀 Fast Feedback Loop (During Development)
```bash
# 1. Make code changes
vim src/tools/tickets.py

# 2. Validate architecture (<5 sec)
uv run validate_architecture.py

# 3. Run relevant tests (~10 sec)
pytest tests/test_tools_tickets.py

# 4. Run full suite if needed (~30 sec)
pytest

# 5. Test with LLM (30-60 sec, if needed)
uv run test_with_aws.py

# 6. Commit when ready
git add . && git commit -m "Update tool"
```

### 🧪 Pre-Deployment Checklist
```bash
# 1. Architecture tests pass
uv run validate_architecture.py

# 2. Full test suite passes
pytest

# 3. LLM inference works
uv run test_with_aws.py

# 4. AgentCore local works
agentcore launch --local
agentcore invoke --message "test"

# 5. Deploy to dev
AGENT_ENV=dev agentcore deploy --agent jira-dev

# 6. Test OAuth flow
agentcore invoke --agent jira-dev --user-id YOUR_USERNAME --message "Get ticket PROJ-123"
```

### 🔍 Debugging

#### Architecture Issues
```bash
# Test components individually
uv run python -c "
from src.auth import MockJiraAuth
from src.tools.tickets import JiraTicketTools
from src.agent import create_jira_agent

auth = MockJiraAuth()
tools = JiraTicketTools(auth)
agent = create_jira_agent(auth)
print('All components loaded!')
"
```

#### AWS Issues
```bash
# Check credentials
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region ap-southeast-2

# Test with verbose logging
export LOG_LEVEL=DEBUG
uv run test_with_aws.py
```

#### OAuth Issues
```bash
# Check AgentCore Identity
agentcore identity list-providers

# Test OAuth URL generation
export AGENT_ENV=dev
agentcore launch --local
# Check logs for OAuth URL
```

---

## Troubleshooting

### "No module named 'strands'"
```bash
# Install dependencies
source .venv/bin/activate
uv pip install -e .
```

### "Token has expired and refresh failed"
```bash
# Clear AWS credentials and re-login
unset AWS_PROFILE
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

### "UnrecognizedClientException"
```bash
# Use real AWS credentials for LLM testing
aws sso login --profile your-profile
export AWS_PROFILE=your-profile

# Or get temporary credentials
aws sts get-session-token
```

### "JIRA API error: 401"
```bash
# Expected with mock auth - LLM will explain it can't access real API
# To test real API, use AGENT_ENV=dev with OAuth
export AGENT_ENV=dev
agentcore launch --local
```

### "Cloud ID not found"
```bash
# Ensure OAuth token has correct scopes
# Scopes required: read:jira-work, write:jira-work, offline_access

# Verify you have access to at least one Atlassian site
# Check OAuth callback URL is correct
```

---

## Test Scripts Summary

| Script | Speed | Requires | Tests |
|--------|-------|----------|-------|
| `validate_architecture.py` | <5s | Nothing | Auth, DI, tools, factory |
| `pytest` | ~30s | Nothing | 89 tests, >85% coverage |
| `test_with_aws.py` | 30-60s | AWS creds | LLM inference, streaming |
| `test_jira_agent.py` | 30-60s | AWS creds | Full integration (limited) |
| `agentcore launch --local` | 2-5min | AWS + AgentCore | Full integration |
| `agentcore deploy` | 5-10min | AWS + OAuth app | Production deployment |

---

## Best Practices

### 1. Test Pyramid Approach
- **Most tests:** Architecture + pytest (fast, no dependencies)
- **Some tests:** LLM inference (moderate, AWS only)
- **Few tests:** Full integration (slow, all dependencies)

### 2. Fail Fast
Run architecture tests first. If they fail, no need to test higher levels.

### 3. Cache AWS Credentials
Use AWS SSO or credential caching to avoid repeated logins.

### 4. Use Environment Variables
Store credentials and configuration in `.env.local`:
```bash
AGENT_ENV=local
AWS_PROFILE=your-profile
AWS_DEFAULT_REGION=ap-southeast-2
LOG_LEVEL=DEBUG
JIRA_URL=https://your-company.atlassian.net
```

### 5. Automate with Scripts
Create a `test.sh` script:
```bash
#!/bin/bash
set -e

echo "Running architecture tests..."
uv run validate_architecture.py

echo "Running full test suite..."
pytest

if [ -n "$AWS_PROFILE" ]; then
    echo "Running AWS integration tests..."
    uv run test_with_aws.py
fi

echo "✅ All tests passed!"
```

---

## Next Steps

1. **Start with architecture tests** to validate the refactoring
2. **Run pytest suite** for comprehensive coverage
3. **Add AWS credentials** to test LLM inference
4. **Test with AgentCore local** for full integration
5. **Deploy to dev** when ready for OAuth testing
6. **Deploy to prod** after validation

Happy testing! 🚀
