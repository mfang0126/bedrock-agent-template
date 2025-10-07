# Multi-Agent Platform - GitHub Agent

Production-ready multi-agent platform with AWS Bedrock AgentCore integration using OAuth 2.0 authentication.

## ✅ **Status: Ready for Runtime Deployment!**

Following the official AWS notebook pattern - tools use real GitHub API with `@requires_access_token` decorator.

---

## 🚀 Quick Deployment Guide

### Prerequisites

1. **GitHub OAuth App** (Device Flow enabled)
   - Create at: https://github.com/settings/developers
   - Copy Client ID and Client Secret

2. **AWS Setup**
   - AWS credentials configured (`aws configure`)
   - Bedrock AgentCore access in supported region
   - Regions: `us-east-1`, `us-west-2`, `ap-southeast-2`, `eu-central-1`

3. **Dependencies**
   ```bash
   uv sync --all-extras  # Includes agentcore-starter-toolkit
   ```

### Step 1: Configure Credentials

```bash
# Copy example and add your GitHub OAuth credentials
cp .env.example .env

# Edit .env:
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
AWS_REGION=us-east-1
```

### Step 2: Create GitHub Credential Provider

```bash
# This creates the OAuth provider in AgentCore Identity
uv run python setup_github_provider.py
```

**Output:**
```
✅ SUCCESS! GitHub credential provider created
Provider ARN: arn:aws:bedrock-agentcore:...
```

###Step 3: Deploy to AgentCore Runtime

```bash
# Configure deployment
agentcore configure -e src/agents/github_agent/runtime.py --non-interactive

# Deploy to AWS (uses CodeBuild - no local Docker needed!)
agentcore launch

# This will:
# - Build ARM64 container via AWS CodeBuild
# - Push to ECR
# - Deploy to AgentCore Runtime
# - Set up CloudWatch logging
# - Activate endpoint
```

### Step 4: Test Your Agent

```bash
# Invoke the agent
agentcore invoke '{"prompt": "list my repositories"}'

# You'll be prompted to authorize via browser (OAuth Device Flow)
# Then the agent will list your GitHub repositories!
```

---

## 📁 Project Structure (Following Notebook Pattern)

```
outbound_auth_github/
├── src/
│   ├── agents/
│   │   └── github_agent/
│   │       ├── runtime.py          # ✅ BedrockAgentCoreApp entrypoint
│   │       ├── agent.py            # Agent logic (if needed)
│   │       └── __main__.py         # CLI (not used in runtime)
│   ├── tools/
│   │   └── github/
│   │       ├── repos.py            # ✅ @tool with httpx API calls
│   │       └── issues.py           # ✅ @tool with httpx API calls
│   └── common/
│       ├── auth/
│       │   ├── github.py           # ✅ @requires_access_token
│       │   └── credential_provider.py  # Provider management
│       └── config/
│           └── config.py           # Config management
├── setup_github_provider.py       # ✅ Setup script
├── pyproject.toml                  # Dependencies + tasks
└── .env                            # Your credentials
```

### Key Files (Notebook Pattern)

**`runtime.py`** - AgentCore entrypoint:
```python
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent

app = BedrockAgentCoreApp()

agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    tools=[list_github_repos, ...]
)

@app.entrypoint
def strands_agent_github(payload):
    response = agent(payload.get("prompt"))
    return {"result": response.message}
```

**`tools/github/repos.py`** - Tools with real API:
```python
from common.auth.github import github_access_token

@tool
def list_github_repos() -> str:
    headers = {"Authorization": f"Bearer {github_access_token}"}
    response = httpx.get("https://api.github.com/user", headers=headers)
    # ... process and return results
```

**`common/auth/github.py`** - OAuth decorator:
```python
@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow='USER_FEDERATION',
    on_auth_url=on_auth_url,
    force_authentication=True,
)
async def get_github_access_token(*, access_token: str) -> str:
    global github_access_token
    github_access_token = access_token
    return access_token
```

---

## 🔧 Available Tools

The agent has access to:

**Repository Tools:**
- `list_github_repos` - List user's repositories with stats
- `get_repo_info` - Get detailed repository information
- `create_github_repo` - Create a new repository

**Issue Tools:**
- `list_github_issues` - List issues in a repository
- `create_github_issue` - Create a new issue
- `close_github_issue` - Close an existing issue

---

## 🧪 Local Testing (Optional)

You can test locally before deploying:

```bash
# Test locally (requires Docker)
agentcore launch --local

# Invoke locally
agentcore invoke '{"prompt": "test query"}' --local
```

---

## 🌐 OAuth Flow (User Experience)

When a user invokes the agent:

1. **First Time / No Token:**
   - Agent returns authorization URL
   - User visits URL in browser
   - User authorizes the GitHub app
   - AgentCore Identity stores the token

2. **Subsequent Calls:**
   - AgentCore automatically uses stored token
   - No re-authorization needed

---

## 🔐 Security & Credentials

### Production (AgentCore Runtime)
- ✅ Credentials managed by AgentCore Identity
- ✅ Tokens stored securely by AWS
- ✅ OAuth flow handled automatically
- ✅ No manual token management

### Local Development (.env file)
```bash
GITHUB_CLIENT_ID=your_oauth_client_id
GITHUB_CLIENT_SECRET=your_oauth_client_secret
AWS_REGION=us-east-1
```

---

## 📊 Monitoring

### CloudWatch Logs
```bash
# View logs
aws logs tail /aws/bedrock-agentcore/runtime/github-agent --follow
```

### Agent Status
```bash
# Check deployment status
agentcore status --agent github-agent
```

---

## 🔄 Updates & Redeployment

To update the agent:

```bash
# Make code changes, then:
agentcore launch

# This rebuilds and redeploys automatically
```

---

## 🎯 Example Queries

Once deployed, users can ask:

```bash
agentcore invoke '{"prompt": "list my repositories"}'
agentcore invoke '{"prompt": "create a repository called my-new-project"}'
agentcore invoke '{"prompt": "show me issues in my awesome-project repo"}'
agentcore invoke '{"prompt": "create an issue about fixing the bug in login flow"}'
```

---

## 🚧 Troubleshooting

### "Credential provider not found"
```bash
# Run setup again
uv run python setup_github_provider.py
```

### "No access to Bedrock AgentCore"
- Check your AWS region (must be: us-east-1, us-west-2, ap-southeast-2, eu-central-1)
- Verify IAM permissions for bedrock-agentcore

### "OAuth authorization failed"
- Check GitHub OAuth App settings
- Verify Client ID/Secret in .env
- Ensure Device Flow is enabled

---

## 📚 Documentation

- **AWS Notebook**: [runtime_with_strands_and_egress_github_3lo.ipynb](https://github.com/awslabs/amazon-bedrock-agentcore-samples/blob/main/01-tutorials/03-AgentCore-identity/06-Outbound_Auth_Github/runtime_with_strands_and_egress_github_3lo.ipynb)
- **AgentCore Docs**: https://docs.aws.amazon.com/bedrock-agentcore/
- **Strands Framework**: https://strandsagents.com/

---

## 🏗️ Adding More Agents

This structure supports multiple agents:

```bash
# Copy template
cp -r src/agents/github_agent src/agents/jira_agent

# Create tools
mkdir src/tools/jira
# ... implement tools

# Deploy separately
agentcore configure -e src/agents/jira_agent/runtime.py
agentcore launch
```

---

## Tech Stack

- **Framework**: Strands Agents
- **Runtime**: AWS Bedrock AgentCore
- **Model**: Claude 3.7 Sonnet
- **OAuth**: AgentCore Identity (3LO)
- **HTTP**: httpx
- **Package Manager**: uv
- **Deployment**: agentcore CLI

---

**Status**: ✅ Production-ready, following official AWS notebook pattern!
