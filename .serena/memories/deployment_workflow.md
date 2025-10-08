# Deployment Workflow

## Prerequisites

### 1. GitHub OAuth App Setup
1. Go to https://github.com/settings/developers
2. Create new OAuth App:
   - Application name: GitHub Agent (or your choice)
   - Homepage URL: https://your-domain.com
   - Device Flow: **ENABLED** (critical!)
3. Copy Client ID and Client Secret
4. Add to .env file locally

### 2. AWS Setup
- AWS credentials configured: `aws configure`
- Bedrock AgentCore access in supported region
- Supported regions: ap-southeast-2, us-west-2, ap-southeast-2, eu-central-1

## Step-by-Step Deployment

### Step 1: Local Setup & Testing
```bash
# Clone and setup
cd app
uv sync --all-extras

# Configure credentials
cp .env.example .env
# Edit .env:
#   GITHUB_CLIENT_ID=your_client_id
#   GITHUB_CLIENT_SECRET=your_client_secret
#   AWS_REGION=ap-southeast-2  (or your preferred region)
```

### Step 2: Create Credential Provider (One-Time)
```bash
# This creates the OAuth provider in AgentCore Identity
uv run python setup_github_provider.py

# Expected output:
# ✅ SUCCESS! GitHub credential provider created
# Provider ARN: arn:aws:bedrock-agentcore:...
```

**What this does**:
- Creates "github-provider" in AgentCore Identity
- Stores GitHub OAuth app credentials
- Enables user-specific token management

### Step 3: Deploy to AgentCore Runtime
```bash
# Configure deployment (tells agentcore CLI about your runtime.py)
agentcore configure -e src/agents/github_agent/runtime.py --non-interactive

# Deploy (builds ARM64 container via AWS CodeBuild, pushes to ECR, deploys)
agentcore launch

# This process:
# 1. Builds ARM64 Docker container via AWS CodeBuild
# 2. Pushes to ECR (Elastic Container Registry)
# 3. Deploys to AgentCore Runtime
# 4. Sets up CloudWatch logging
# 5. Activates endpoint
```

### Step 4: Test Deployed Agent
```bash
# Invoke with user ID (required for 3LO)
agentcore invoke '{"prompt": "list my repositories"}' --user-id "user-123"

# First-time flow:
# 1. Agent generates authorization URL (visible in logs)
# 2. User visits URL in browser
# 3. User authorizes GitHub app
# 4. AgentCore stores user's token (encrypted, isolated)
# 5. Agent uses token to list repositories

# Subsequent calls (same user):
# - AgentCore retrieves user's existing token
# - No re-authorization needed
```

## Multi-User Testing
```bash
# Different user = separate OAuth flow
agentcore invoke '{"prompt": "list my repositories"}' --user-id "alice"
agentcore invoke '{"prompt": "list my repositories"}' --user-id "bob"

# Each user:
# - Gets their own authorization flow
# - Has their own isolated token
# - Can NEVER access other users' tokens
# - Sees only their own GitHub data
```

## Monitoring Deployment
```bash
# Check agent status
agentcore status --agent github-agent

# View CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtime/github-agent --follow
```

## Updating the Agent
```bash
# Make code changes, then:
agentcore launch

# This rebuilds and redeploys automatically
# AgentCore handles versioning and rollout
```

## Troubleshooting

### "Credential provider not found"
```bash
# Re-run setup
uv run python setup_github_provider.py
```

### "No access to Bedrock AgentCore"
- Check AWS region (must be supported)
- Verify IAM permissions for bedrock-agentcore

### "OAuth authorization failed"
- Check GitHub OAuth App settings
- Verify Device Flow is enabled
- Check Client ID/Secret in .env
- Ensure credentials match what was registered

## Production Considerations

### Security
- Each user ID gets isolated OAuth tokens
- Tokens encrypted at rest by AWS KMS
- IAM policies enforce strict access boundaries
- Audit trail in CloudWatch

### Scalability
- Serverless architecture (pay-per-use)
- Auto-scales based on demand
- Up to 8-hour agent sessions
- No infrastructure management needed

### Cost Optimization
- Only pay for actual invocations
- No idle server costs
- Token caching reduces API calls
- CloudWatch logs retention configurable
