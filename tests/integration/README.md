# Integration Tests

Real integration tests against deployed AgentCore Runtime. No mocks.

## Prerequisites

1. **AWS Authentication**
   ```bash
   authenticate --to=wealth-dev-au
   ```

2. **Deployed Agent**
   - Agent must be deployed to AgentCore Runtime
   - GitHub OAuth provider configured
   - Test repository accessible

3. **Environment Variables**
   ```bash
   export AGENT_ARN="arn:aws:bedrock-agentcore:ap-southeast-2:xxx:agent/github-agent"
   export TEST_REPO="your-org/test-repo"
   ```

## Running Tests

```bash
# Authenticate and run tests
authenticate --to=wealth-dev-au && ./tests/integration/test_github_agent.sh
```

## Test Coverage

1. **List Repositories** - Verify OAuth and API access
2. **Get Repository Info** - Test repo details retrieval
3. **List Issues** - Test issue listing
4. **Create Issue** - Test issue creation
5. **Post Comment** - Test commenting on issues
6. **Close Issue** - Test issue state updates

## Test Repository Setup

Create a test repository with:
- Public or private visibility
- Issues enabled
- At least one existing issue for testing

## Troubleshooting

**Authentication Failed:**
```bash
# Re-authenticate
authenticate --to=wealth-dev-au
```

**Agent Not Found:**
```bash
# Check agent ARN
agentcore list-agents
export AGENT_ARN="<correct-arn>"
```

**OAuth Required:**
- First test run will trigger OAuth flow
- Visit the authorization URL
- Subsequent runs will reuse token
