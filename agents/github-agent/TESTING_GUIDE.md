# Complete Testing Guide

This guide shows you how to test the GitHub agent at different levels, from local architecture validation to full production deployment.

## Testing Pyramid

```
                    ┌─────────────────────┐
                    │  Production Test    │  Slowest (5-10 min)
                    │  (Real OAuth + API) │  Requires: AWS + GitHub OAuth
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
source .venv/bin/activate
export AGENT_ENV=local
```

### Run Tests
```bash
python validate_architecture.py
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
```

### When to Use
- ✅ After refactoring code structure
- ✅ Before committing code changes
- ✅ Quick validation during development
- ✅ CI/CD pipeline (no credentials needed)

---

## Level 2: LLM Inference Testing (AWS Bedrock Required)

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
source .venv/bin/activate
export AGENT_ENV=local

# Automated tests
python test_with_aws.py

# Or interactive mode
python -c "
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
   Tools: 11 available

📝 Query: 'What tools do you have available?'

🤖 Agent Response:
------------------------------------------------------------
I'm a GitHub assistant with these tools:
- list_github_repos: List your repositories
- create_github_issue: Create new issues
- merge_pull_request: Merge pull requests
...
------------------------------------------------------------

✅ LLM inference successful!
```

### What Will Fail
❌ **Actual GitHub API calls** - Mock token won't work with real GitHub API
✅ **LLM responses** - Agent can talk about what it would do
✅ **Tool selection** - Agent can decide which tools to use

### When to Use
- ✅ Test LLM behavior and responses
- ✅ Test streaming functionality
- ✅ Test tool selection logic
- ✅ Validate system prompt changes
- ✅ Test conversation flow

---

## Level 3: AgentCore Local Testing (Full Integration)

**What it tests:** Complete agent with OAuth flow, real GitHub API (optional)

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

# In another terminal, invoke it (IMPORTANT: --user-id is required for OAuth)
agentcore invoke --user-id YOUR_USERNAME --message "List my repositories"

# Or test OAuth flow with dev environment
export AGENT_ENV=dev
agentcore launch --local
agentcore invoke --user-id YOUR_USERNAME --message "List my repositories"
```

**Note:** Replace `YOUR_USERNAME` with any identifier (e.g., your GitHub username). The `--user-id` flag is required for OAuth authentication to work properly.

### Expected Flow

**With `AGENT_ENV=local` (Mock Auth):**
```
🔐 Initializing GitHub authentication...
🧪 Mock GitHub Auth initialized - LOCAL TESTING MODE
✅ GitHub authentication successful
🤖 I can help with repositories, issues, and pull requests.
    To list repositories, I'll use list_github_repos...
```

**With `AGENT_ENV=dev` (Real OAuth):**
```
🔐 Initializing GitHub authentication...
🔗 Please authorize at: https://github.com/login/oauth/authorize?...

[After you authorize in browser]
✅ GitHub authentication successful
🤖 You have 42 repositories. First 3: repo1, repo2, repo3
```

### When to Use
- ✅ Test OAuth flow end-to-end
- ✅ Test with real GitHub API
- ✅ Test AgentCore Memory integration
- ✅ Test streaming responses through AgentCore
- ✅ Final validation before deployment

---

## Level 4: Development Deployment Testing

**What it tests:** Agent in real AgentCore environment

**Time:** 5-10 minutes
**Requires:** AWS credentials, AgentCore account, GitHub OAuth app

### Setup GitHub OAuth App

1. Go to https://github.com/settings/developers
2. Create new OAuth App:
   - **Application name:** GitHub Agent Dev
   - **Homepage URL:** https://your-app.com
   - **Authorization callback URL:** https://agentcore-runtime-url/oauth/callback
3. Note the **Client ID** and **Client Secret**

### Configure AgentCore Identity

```bash
# Configure GitHub OAuth provider in AgentCore
agentcore identity create-provider \
  --name github-provider \
  --type OAUTH2 \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --authorization-url https://github.com/login/oauth/authorize \
  --token-url https://github.com/login/oauth/access_token \
  --scopes repo,read:user
```

### Deploy
```bash
export AGENT_ENV=dev
agentcore deploy --agent github-dev
```

### Test
```bash
# First invocation (will trigger OAuth)
agentcore invoke --agent github-dev --user-id YOUR_USERNAME --message "List my repositories"

# Follow OAuth URL, authorize

# Second invocation (uses cached token)
agentcore invoke --agent github-dev --user-id YOUR_USERNAME --message "Create an issue in test-repo"
```

### When to Use
- ✅ Test before production deployment
- ✅ Validate OAuth flow in real environment
- ✅ Test with real GitHub API
- ✅ Validate AgentCore Memory works
- ✅ Test error handling and edge cases

---

## Level 5: Production Deployment

**What it tests:** Agent in production

**Time:** 10+ minutes
**Requires:** Production AWS account, production GitHub OAuth app

### Deploy
```bash
export AGENT_ENV=prod
agentcore deploy --agent github-prod --environment production
```

### Monitor
```bash
# View logs
agentcore logs --agent github-prod

# Check CloudWatch
aws logs tail /aws/lambda/github-agent-prod --follow
```

### Smoke Tests
```bash
# Test basic functionality
agentcore invoke --agent github-prod --user-id YOUR_USERNAME --message "What can you help me with?"

# Test repository listing
agentcore invoke --agent github-prod --user-id YOUR_USERNAME --message "List my repositories"
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
vim src/tools/repos.py

# 2. Validate architecture (<5 sec)
python validate_architecture.py

# 3. Test with LLM (30-60 sec, if needed)
python test_with_aws.py

# 4. Commit when ready
git add . && git commit -m "Update tool"
```

### 🧪 Pre-Deployment Checklist
```bash
# 1. Architecture tests pass
python validate_architecture.py

# 2. LLM inference works
python test_with_aws.py

# 3. AgentCore local works
agentcore launch --local
agentcore invoke --user-id YOUR_USERNAME --message "test"

# 4. Deploy to dev
AGENT_ENV=dev agentcore deploy --agent github-dev

# 5. Test OAuth flow
agentcore invoke --agent github-dev --user-id YOUR_USERNAME --message "List repos"
```

### 🔍 Debugging

#### Architecture Issues
```bash
# Test components individually
python -c "
from src.auth import MockGitHubAuth
from src.tools.repos import GitHubRepoTools
from src.agent import create_github_agent

auth = MockGitHubAuth()
tools = GitHubRepoTools(auth)
agent = create_github_agent(auth)
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
python test_with_aws.py
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
# Clear AWS credentials and use fake ones for local testing
unset AWS_PROFILE
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=ap-southeast-2

# Or login again with SSO
aws sso login --profile your-profile
```

### "UnrecognizedClientException"
```bash
# Use real AWS credentials for LLM testing
aws sso login --profile your-profile
export AWS_PROFILE=your-profile

# Or get temporary credentials
aws sts get-session-token
```

### "GitHub API error: 401"
```bash
# Expected with mock auth - LLM will explain it can't access real API
# To test real API, use AGENT_ENV=dev with OAuth
export AGENT_ENV=dev
agentcore launch --local
```

---

## Test Scripts Summary

| Script | Speed | Requires | Tests |
|--------|-------|----------|-------|
| `validate_architecture.py` | <5s | Nothing | Auth, DI, tools, factory |
| `test_with_aws.py` | 30-60s | AWS creds | LLM inference, streaming |
| `test_local.py` | 30-60s | AWS creds | Full integration (limited) |
| `agentcore launch --local` | 2-5min | AWS + AgentCore | Full integration |
| `agentcore deploy` | 5-10min | AWS + OAuth app | Production deployment |

---

## Best Practices

### 1. Test Pyramid Approach
- **Most tests:** Architecture (fast, no dependencies)
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
```

### 5. Automate with Scripts
Create a `test.sh` script:
```bash
#!/bin/bash
set -e

echo "Running architecture tests..."
python validate_architecture.py

if [ -n "$AWS_PROFILE" ]; then
    echo "Running AWS integration tests..."
    python test_with_aws.py
fi

echo "✅ All tests passed!"
```

---

## Next Steps

1. **Start with architecture tests** to validate the refactoring
2. **Add AWS credentials** to test LLM inference
3. **Test with AgentCore local** for full integration
4. **Deploy to dev** when ready for OAuth testing
5. **Deploy to prod** after validation

Happy testing! 🚀
