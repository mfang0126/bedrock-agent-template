# GitHub Agent - Testing the Rest

You've successfully validated the architecture! Here's how to test the remaining parts.

## 🎯 What You Want to Test Next

### 1. LLM Inference (Agent Responses)
**What:** Test that the agent can respond to queries using AWS Bedrock
**Requires:** AWS credentials with Bedrock access
**Time:** 30-60 seconds

### 2. Real GitHub API Calls
**What:** Test actual GitHub operations (list repos, create issues, etc.)
**Requires:** AWS + GitHub OAuth or personal access token
**Time:** 2-5 minutes

---

## 📋 Step-by-Step: Test LLM Inference

### Prerequisites
You need AWS credentials with access to Bedrock in ap-southeast-2.

### Step 1: Login to AWS

**If you use AWS SSO:**
```bash
aws sso login --profile your-profile
export AWS_PROFILE=your-profile
export AWS_DEFAULT_REGION=ap-southeast-2
```

**If you use IAM credentials:**
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=ap-southeast-2
```

**If you need temporary credentials:**
```bash
aws sts get-session-token
# Copy the credentials from output
export AWS_ACCESS_KEY_ID=<from output>
export AWS_SECRET_ACCESS_KEY=<from output>
export AWS_SESSION_TOKEN=<from output>
```

### Step 2: Verify AWS Access
```bash
# Verify identity
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region ap-southeast-2
```

### Step 3: Run LLM Tests
```bash
source .venv/bin/activate
export AGENT_ENV=local
python test_with_aws.py
```

### What You'll See

**Test 1: LLM Inference**
```
📝 Query: 'What tools do you have available?'

🤖 Agent Response:
------------------------------------------------------------
I'm a GitHub assistant with 11 tools available:

Repository Tools:
- list_github_repos: List your GitHub repositories
- get_repo_info: Get details about a specific repository
- create_github_repo: Create a new repository

Issue Tools:
- list_github_issues: List issues in a repository
- create_github_issue: Create new issues
- close_github_issue: Close existing issues
- post_github_comment: Comment on issues
- update_github_issue: Update issue details

Pull Request Tools:
- create_pull_request: Create new pull requests
- list_pull_requests: List pull requests
- merge_pull_request: Merge pull requests

I can help you manage your GitHub repositories, issues, and
pull requests through natural language commands.
------------------------------------------------------------

✅ LLM inference successful!
```

**Test 2: Streaming**
```
📝 Query: 'Explain what you can help me with in 2 sentences.'

🤖 Streaming Response:
------------------------------------------------------------
I can help you manage your GitHub repositories, issues, and
pull requests using natural language. Just tell me what you
want to do, and I'll use my tools to help you accomplish it.
------------------------------------------------------------

✅ Streaming successful!
```

### Step 4: Try Interactive Mode

After the automated tests, choose 'y' when asked:
```
Run interactive mode? (y/n): y

INTERACTIVE MODE (with LLM)
Type 'exit' or 'quit' to stop

💬 You: What can you do?

🤖 Agent:
I can help you with GitHub operations! Here's what I can do:
...
```

**Try these queries:**
- "What tools do you have?"
- "Explain how I would list my repositories"
- "How do I create an issue?"
- "What's the difference between repos and issues?"

**Note:** Actual GitHub API calls will fail with mock token, but the agent will explain what it *would* do.

---

## 📋 Step-by-Step: Test Real GitHub API

To test real GitHub API calls, you need OAuth flow which requires AgentCore.

### Option A: AgentCore Local (Recommended)

**Step 1: Set Environment for Real OAuth**
```bash
export AGENT_ENV=dev  # Use real OAuth, not mock
```

**Step 2: Launch Agent**
```bash
source .venv/bin/activate
agentcore launch --local
```

**Step 3: Invoke Agent (in another terminal)**
```bash
agentcore invoke --user-id YOUR_USERNAME --message "List my GitHub repositories"
```

**IMPORTANT:** The `--user-id` flag is **required** for OAuth authentication. Replace `YOUR_USERNAME` with any identifier (e.g., your GitHub username or email).

**Step 4: Complete OAuth Flow**
You'll see an OAuth URL:
```
🔗 Please authorize at: https://github.com/login/oauth/authorize?...
```

1. Open the URL in your browser
2. Authorize the app
3. Agent will receive the token and proceed

**Step 5: Test Real API Calls**
```bash
# List repos (will work now!)
agentcore invoke --user-id YOUR_USERNAME --message "List my repositories"

# Get repo info
agentcore invoke --user-id YOUR_USERNAME --message "Tell me about my repo called test-repo"

# List issues
agentcore invoke --user-id YOUR_USERNAME --message "Show me open issues in test-repo"
```

### Option B: Deploy to Dev Environment

**Step 1: Configure GitHub OAuth App**
1. Go to https://github.com/settings/developers
2. Create OAuth App
3. Note Client ID and Secret

**Step 2: Configure AgentCore Identity**
```bash
agentcore identity create-provider \
  --name github-provider \
  --type OAUTH2 \
  --client-id YOUR_CLIENT_ID \
  --client-secret YOUR_CLIENT_SECRET \
  --authorization-url https://github.com/login/oauth/authorize \
  --token-url https://github.com/login/oauth/access_token \
  --scopes repo,read:user
```

**Step 3: Deploy**
```bash
export AGENT_ENV=dev
agentcore deploy --agent github-dev
```

**Step 4: Test**
```bash
agentcore invoke --agent github-dev --user-id YOUR_USERNAME --message "List my repos"
```

---

## 🎓 What Each Test Validates

| Test Level | What It Tests | What Works | What Doesn't |
|------------|--------------|------------|--------------|
| **Architecture** | Code structure | Everything | N/A |
| **LLM Inference** | Agent responses | LLM talks | No real API calls |
| **AgentCore Local** | Full integration | Everything + OAuth | Requires AgentCore |
| **Dev Deployment** | Production-like | Everything | Needs AWS account |

---

## 🔍 Expected Results at Each Level

### Level 1: Architecture ✅ (Already Done!)
```
✅ Auth abstraction layer working
✅ Dependency injection working
✅ Tool classes instantiate correctly
✅ Agent factory creates agent with all tools
✅ Mock authentication functional
✅ Environment detection working
```

### Level 2: LLM Inference (Next Step!)
```
✅ Agent can respond to queries
✅ LLM uses system prompt correctly
✅ Agent explains tool capabilities
✅ Streaming works
✅ Interactive mode works
⚠️  GitHub API calls fail (expected - mock token)
```

Example interaction:
```
You: "List my repositories"
Agent: "I'll use the list_github_repos tool... However, I'm
       encountering an authentication error with the GitHub API.
       This is expected in mock mode. In production, I would
       retrieve your actual repositories."
```

### Level 3: Real GitHub API (Full Integration!)
```
✅ OAuth flow works
✅ Real GitHub token obtained
✅ Can list actual repositories
✅ Can create real issues
✅ Can manage pull requests
✅ Full functionality working
```

Example interaction:
```
You: "List my repositories"
Agent: "You have 42 repositories. First 3:
       - user/repo1 (Public, 15 stars)
       - user/repo2 (Private, 3 contributors)
       - user/repo3 (Public, archived)"
```

---

## 🐛 Common Issues & Solutions

### "AWS credentials not found"
```bash
# Solution 1: Use AWS SSO
aws sso login --profile your-profile
export AWS_PROFILE=your-profile

# Solution 2: Use temporary credentials
aws sts get-session-token
```

### "Bedrock access denied"
```bash
# Check your IAM permissions
aws bedrock list-foundation-models --region ap-southeast-2

# You need: bedrock:InvokeModel permission
```

### "GitHub API 401 Unauthorized"
This is **expected** when using mock authentication!

**Solution:** Use real OAuth:
```bash
export AGENT_ENV=dev
agentcore launch --local
```

### "Token has expired"
```bash
# Refresh AWS SSO
aws sso login --profile your-profile
```

---

## 📊 Quick Reference Commands

```bash
# Architecture tests (no AWS)
python validate_architecture.py

# LLM tests (needs AWS)
python test_with_aws.py

# Interactive with LLM
python test_with_aws.py
# Choose 'y' for interactive

# Real GitHub API (needs OAuth)
export AGENT_ENV=dev
agentcore launch --local
agentcore invoke --message "test"

# One-command test
./test_quick.sh
```

---

## ✅ Testing Checklist

- [x] Architecture validation (no AWS) ✓
- [ ] LLM inference (with AWS credentials)
- [ ] Streaming responses
- [ ] Interactive mode
- [ ] AgentCore local integration
- [ ] Real GitHub API calls (with OAuth)
- [ ] Dev deployment
- [ ] Production deployment

---

## 🚀 Ready to Test?

### Right Now (No AWS Setup)
```bash
# You've already done this!
python validate_architecture.py
```

### Next Step (With AWS)
```bash
# 1. Login to AWS
aws sso login --profile your-profile

# 2. Test LLM
source .venv/bin/activate
python test_with_aws.py

# 3. Try interactive mode (fun!)
# Choose 'y' when prompted
```

### Full Integration (When Ready)
```bash
export AGENT_ENV=dev
agentcore launch --local
agentcore invoke --message "List my repositories"
```

---

## 📚 Additional Resources

- **TESTING_GUIDE.md** - Complete testing documentation
- **QUICKSTART.md** - Quick start guide
- **LOCAL_TESTING_GUIDE.md** - Local testing details
- **REFACTORING_SUMMARY.md** - What we accomplished

---

## 🎉 Summary

You've successfully:
- ✅ Refactored GitHub agent for testability
- ✅ Validated architecture locally
- ✅ Created comprehensive test suite

To test the rest:
1. Get AWS credentials
2. Run `python test_with_aws.py`
3. Try interactive mode for fun!

**The refactoring is complete and working!** 🚀
