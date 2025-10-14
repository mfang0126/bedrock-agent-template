# Local Invocation Guide - GitHub Agent

Complete guide for testing the GitHub agent locally using agentcore CLI and curl.

---

## Prerequisites

1. **Install agentcore**:
   ```bash
   pip install bedrock-agentcore-starter-toolkit
   # OR
   uv pip install bedrock-agentcore-starter-toolkit
   ```

2. **Verify installation**:
   ```bash
   agentcore --version
   ```

3. **Set environment**:
   ```bash
   export AGENT_ENV=local  # Use mock authentication
   ```

---

## Method 1: AgentCore CLI (Recommended)

### Step 1: Launch Agent Locally

Open **Terminal 1**:
```bash
cd agents/github-agent
export AGENT_ENV=local
agentcore launch --local
```

**Expected output**:
```
🚀 Launching agent locally...
🔐 Initializing GitHub authentication...
🧪 Mock GitHub Auth initialized - LOCAL TESTING MODE
✅ GitHub authentication successful
🎯 Agent ready and listening...
```

### Step 2: Invoke Agent

Open **Terminal 2**:
```bash
cd agents/github-agent

# Basic query
agentcore invoke \
  --user-id "test-user" \
  --message "What can you help me with?"

# List tools
agentcore invoke \
  --user-id "test-user" \
  --message "What tools do you have available?"

# Test specific tool (will use mock data)
agentcore invoke \
  --user-id "test-user" \
  --message "List my GitHub repositories"

# Create issue (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Create an issue called 'Test Issue' in my repo"
```

### Important Notes:
- ⚠️ `--user-id` is **required** for OAuth authentication
- ⚠️ Use the same `--user-id` across invocations to maintain session
- ⚠️ Mock mode won't make real GitHub API calls

---

## Method 2: Direct Runtime Invocation

If `agentcore launch` doesn't work:

```bash
cd agents/github-agent
export AGENT_ENV=local

# Run the runtime directly
uv run python -m src.runtime
```

This starts the agent without the agentcore CLI wrapper.

---

## Method 3: Curl Invocation (HTTP API)

### Step 1: Launch Agent with HTTP Server

If your runtime exposes an HTTP endpoint:

```bash
cd agents/github-agent
export AGENT_ENV=local
export PORT=8080

# Launch with HTTP server (if supported)
agentcore launch --local --port 8080
```

### Step 2: Invoke with Curl

```bash
# Basic invocation
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What can you help me with?"}'

# Test with different queries
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "List my GitHub repositories"}'

# Pretty print response with jq
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What tools do you have?"}' | jq .
```

### Streaming Response

```bash
# With streaming enabled (if supported)
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"prompt": "Tell me about your capabilities", "stream": true}'
```

---

## Method 4: Python Script Invocation

Create a test script for programmatic invocation:

```python
#!/usr/bin/env python3
"""test_invocation.py - Test GitHub agent invocation"""

import asyncio
from src.agent import create_github_agent
from src.auth import get_auth_provider

async def test_agent():
    # Create agent with mock auth
    auth = get_auth_provider(env="local")
    agent = create_github_agent(auth)

    # Test queries
    queries = [
        "What can you help me with?",
        "What tools do you have available?",
        "List my GitHub repositories",
        "Explain how to create an issue",
    ]

    for query in queries:
        print(f"\n{'='*70}")
        print(f"📝 Query: {query}")
        print('='*70)

        try:
            # Invoke agent (sync)
            if hasattr(agent, 'run'):
                response = agent.run(query)
            elif hasattr(agent, '__call__'):
                response = agent(query)
            else:
                response = await agent.invoke_async(query)

            print(f"🤖 Response:\n{response}\n")
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(test_agent())
```

**Run it**:
```bash
uv run python test_invocation.py
```

---

## Testing Scenarios

### 1. Basic Capabilities

```bash
# What can you do?
agentcore invoke \
  --user-id "test-user" \
  --message "What are your capabilities?"

# Expected: Lists repository, issue, and PR management tools
```

### 2. Repository Operations

```bash
# List repos (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "List my GitHub repositories"

# Get repo info (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Tell me about my repository called 'test-repo'"

# Create repo (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Create a new repository called 'my-new-project'"
```

### 3. Issue Management

```bash
# List issues (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Show me open issues in my test-repo repository"

# Create issue (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Create an issue titled 'Bug in login' with description 'Users cannot log in'"

# Close issue (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Close issue #42 in test-repo"
```

### 4. Pull Request Operations

```bash
# List PRs (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "List all pull requests in test-repo"

# Create PR (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Create a pull request from feature-branch to main"

# Merge PR (mock)
agentcore invoke \
  --user-id "test-user" \
  --message "Merge pull request #5"
```

---

## Expected Behavior in Mock Mode

### ✅ What Works:
- Agent responds to queries
- Tool selection logic
- Conversation flow
- Streaming responses
- Error handling
- LLM reasoning about GitHub operations

### ⚠️ What's Mocked:
- GitHub API calls return mock data
- OAuth flow is bypassed
- No real repositories/issues/PRs are modified
- Token is always "ghp_mock_token..."

### Example Mock Response:
```
🤖 Agent: I'll help you list your repositories. Let me use the
list_github_repos tool...

[Tool Call: list_github_repos]

Based on the results, you have 3 repositories:
1. test-repo (Public, 5 stars)
2. my-project (Private, 2 contributors)
3. demo-app (Public, archived)

Note: This is mock data for local testing.
```

---

## Testing with Real GitHub API

To test with **real GitHub API calls**:

### Step 1: Switch to Dev Mode
```bash
export AGENT_ENV=dev  # Enable real OAuth
```

### Step 2: Configure GitHub OAuth App

1. Go to: https://github.com/settings/developers
2. Create OAuth App:
   - **Name**: GitHub Agent Dev
   - **Homepage**: http://localhost:8080
   - **Callback**: http://localhost:8080/callback
3. Copy Client ID and Secret

### Step 3: Set Credentials
```bash
export GITHUB_CLIENT_ID="your_client_id"
export GITHUB_CLIENT_SECRET="your_client_secret"
```

### Step 4: Launch and Authorize
```bash
agentcore launch --local
```

You'll see:
```
🔗 Please authorize at: https://github.com/login/oauth/authorize?...
```

1. Open the URL in browser
2. Authorize the app
3. Agent receives token and continues

### Step 5: Invoke with Real API
```bash
agentcore invoke \
  --user-id "your-github-username" \
  --message "List my actual repositories"
```

Now you'll get **real** repository data! 🎉

---

## Troubleshooting

### Error: "Command not found: agentcore"

**Solution**:
```bash
pip install bedrock-agentcore-starter-toolkit
# OR
uv pip install bedrock-agentcore-starter-toolkit
```

### Error: "No module named 'src'"

**Solution**:
```bash
cd agents/github-agent
export PYTHONPATH=$(pwd)
```

### Error: "Token has expired"

**Solution**:
```bash
# For mock testing, this shouldn't happen
export AGENT_ENV=local

# For dev/prod, refresh AWS SSO
aws sso login --profile your-profile
```

### Error: "GitHub API 401 Unauthorized"

**Expected in mock mode!** This means:
- Mock token can't access real GitHub API
- To fix: Use `AGENT_ENV=dev` with real OAuth

### Agent doesn't respond

**Check**:
1. Is agent still running in Terminal 1?
2. Are you in the correct directory?
3. Try restarting the agent

---

## Quick Reference Commands

```bash
# Start agent (mock)
export AGENT_ENV=local
agentcore launch --local

# Invoke agent
agentcore invoke --user-id "test" --message "your query here"

# With curl (if HTTP endpoint available)
curl -X POST http://localhost:8080/invocations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "your query here"}'

# Direct Python invocation
uv run python -m src.runtime

# Stop agent
Ctrl+C in Terminal 1
```

---

## Testing Checklist

- [ ] Agent launches without errors
- [ ] Agent responds to basic queries
- [ ] Tool selection works (lists correct tools)
- [ ] Mock authentication shows warning
- [ ] Repository operations return mock data
- [ ] Issue operations return mock data
- [ ] PR operations return mock data
- [ ] Error handling works for invalid inputs
- [ ] Streaming responses work (if enabled)
- [ ] Sessions persist across invocations

---

## Next Steps

1. **Test locally** with mock auth (this guide)
2. **Configure real OAuth** for GitHub API testing
3. **Deploy to dev** environment
4. **Test in production** with monitoring

Happy testing! 🚀
