# Quick Testing Guide - GitHub Agent

Fast reference for testing the GitHub agent locally.

---

## ⚡ Quick Start (No AgentCore CLI)

Since `agentcore` CLI is not installed, here are alternative testing methods:

### Option 1: Run Test Suite (Recommended)
```bash
cd agents/github-agent

# Run comprehensive test suite
uv run python test_github_agent.py
```

**Tests:**
- ✅ Import validation
- ✅ Agent instantiation
- ✅ Tool registration (11 tools)
- ✅ Mock authentication
- ✅ LLM inference (optional, needs AWS)

---

### Option 2: Run Invocation Test
```bash
cd agents/github-agent

# Test agent with sample queries
uv run python test_invocation.py
```

**What it does:**
- Creates agent with mock auth
- Runs 4 sample queries
- Shows agent responses
- Tests tool invocation flow

**Note:** Requires AWS credentials for LLM to work. Without AWS, you'll see connection errors (expected).

---

### Option 3: Interactive Python Test

```bash
cd agents/github-agent

# Start Python REPL
uv run python

# Then run:
>>> from src.agent import create_github_agent
>>> from src.auth import get_auth_provider
>>>
>>> # Create agent
>>> auth = get_auth_provider(env="local")
>>> agent = create_github_agent(auth)
>>>
>>> # Check tools
>>> print(f"Tools: {agent.tool_names}")
>>>
>>> # Try a query (needs AWS Bedrock)
>>> # response = agent.run("What can you help me with?")
>>> # print(response)
```

---

## 🔧 Install AgentCore CLI (Optional)

If you want to use `agentcore` commands:

```bash
# Install
uv pip install bedrock-agentcore-starter-toolkit

# Verify
agentcore --version
```

Then you can use:

```bash
# Terminal 1: Launch agent
cd agents/github-agent
export AGENT_ENV=local
agentcore launch --local

# Terminal 2: Invoke agent
agentcore invoke \
  --user-id "test-user" \
  --message "What can you help me with?"
```

**Benefits:**
- ✅ More realistic runtime environment
- ✅ Session management
- ✅ Easier OAuth testing
- ✅ Better for integration testing

---

## 🧪 Testing Without AWS Credentials

All architecture tests work **without AWS**:

```bash
# Import validation
uv run python validate_imports.py

# Protocol compatibility
uv run python test_protocol.py

# Full test suite (architecture only)
uv run python test_github_agent.py
```

**What works:**
- ✅ Agent creation
- ✅ Tool registration
- ✅ Mock authentication
- ✅ Code validation

**What requires AWS:**
- ❌ LLM inference (agent responses)
- ❌ Actual conversations
- ❌ Tool execution with reasoning

---

## 🔐 Testing With AWS Credentials

To test **full agent functionality** (LLM + tools):

### Step 1: Configure AWS

```bash
# Option A: AWS SSO (recommended)
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
export AWS_DEFAULT_REGION=ap-southeast-2

# Option B: Direct credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=ap-southeast-2
```

### Step 2: Test

```bash
cd agents/github-agent
export AGENT_ENV=local

# Run invocation test (now with LLM)
uv run python test_invocation.py
```

**Expected:**
- ✅ Agent responds to queries
- ✅ LLM reasons about GitHub operations
- ✅ Tools selected appropriately
- ⚠️ GitHub API calls return mock data (not real)

---

## 🌐 Testing With Real GitHub API

To make **real GitHub API calls**:

### Prerequisites

1. Create GitHub OAuth App:
   - Go to: https://github.com/settings/developers
   - Create OAuth App
   - Note Client ID and Secret

2. Set environment:
   ```bash
   export AGENT_ENV=dev  # Switch to dev mode
   export GITHUB_CLIENT_ID="your_client_id"
   export GITHUB_CLIENT_SECRET="your_client_secret"
   ```

3. Launch and authorize:
   ```bash
   agentcore launch --local
   # Follow OAuth URL to authorize
   ```

4. Invoke with real API:
   ```bash
   agentcore invoke \
     --user-id "your-github-username" \
     --message "List my actual repositories"
   ```

---

## 📋 Test Commands Summary

```bash
# Quick architecture validation
uv run python validate_imports.py         # <5 seconds
uv run python test_protocol.py            # <5 seconds
uv run python test_github_agent.py        # ~30 seconds

# Invocation testing (needs AWS)
uv run python test_invocation.py          # ~60 seconds

# With AgentCore CLI (needs installation)
agentcore launch --local                  # Launch in background
agentcore invoke --user-id "test" \       # Invoke agent
  --message "your query"
```

---

## 🐛 Common Issues

### "No module named 'src'"
```bash
cd agents/github-agent  # Make sure you're in the right directory
export PYTHONPATH=$(pwd)
```

### "Token has expired"
```bash
# Refresh AWS credentials
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
```

### "GitHub API 401 Unauthorized"
**Expected in mock mode!**
- Mock token can't access real GitHub
- To fix: Use `AGENT_ENV=dev` with real OAuth

### Agent doesn't respond
**Likely cause:** No AWS credentials for Bedrock
```bash
# Check AWS access
aws sts get-caller-identity

# Check Bedrock access
aws bedrock list-foundation-models --region ap-southeast-2
```

---

## ✅ Testing Checklist

**Without AWS:**
- [x] Imports validate: `uv run python validate_imports.py`
- [x] Protocol works: `uv run python test_protocol.py`
- [x] Tests pass: `uv run python test_github_agent.py`
- [x] Agent creates: Check test output
- [x] Tools registered: Should show 11 tools

**With AWS:**
- [ ] LLM responds: Agent answers questions
- [ ] Tools selected: Agent chooses appropriate tools
- [ ] Mock data: GitHub API returns mock responses
- [ ] Error handling: Graceful failures

**With Real GitHub (Optional):**
- [ ] OAuth flow: Successfully authorize app
- [ ] Real repos: List actual repositories
- [ ] Real issues: Create/list actual issues
- [ ] Real PRs: Manage actual pull requests

---

## 🎯 Recommended Testing Flow

1. **Start here** (5 min, no setup):
   ```bash
   uv run python test_github_agent.py
   ```

2. **If you have AWS** (10 min):
   ```bash
   aws sso login --profile your-profile
   uv run python test_invocation.py
   ```

3. **For full testing** (30 min):
   ```bash
   # Install agentcore
   uv pip install bedrock-agentcore-starter-toolkit

   # Launch and test
   agentcore launch --local  # Terminal 1
   agentcore invoke --user-id "test" --message "test"  # Terminal 2
   ```

4. **Production ready** (60 min):
   - Configure GitHub OAuth
   - Test with real API
   - Deploy to AWS

---

## 📚 Documentation

- **LOCAL_INVOCATION_GUIDE.md** - Complete invocation guide with curl examples
- **TESTING_GUIDE.md** - Comprehensive testing documentation
- **QUICKSTART.md** - Quick start guide
- **README_TESTING.md** - What to test next

---

Happy testing! 🚀

**Need help?** Check the guides above or ask for assistance.
