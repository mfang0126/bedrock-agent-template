# AWS AgentCore Setup Guide for New AWS Accounts

Complete guide for setting up AWS Bedrock AgentCore from scratch in a new AWS account.

## Prerequisites

- AWS Account with admin access
- AWS CLI installed and configured
- Python 3.10+ installed
- `uv` package manager installed

## Step 1: AWS Account Setup

### 1.1 Choose AWS Region

AgentCore is available in these regions:
- `us-east-1` (US East - N. Virginia)
- `us-west-2` (US West - Oregon)
- `ap-southeast-2` (Asia Pacific - Sydney)
- `eu-central-1` (Europe - Frankfurt)

```bash
# Set your preferred region
export AWS_REGION=ap-southeast-2
```

### 1.2 Verify AWS CLI Configuration

```bash
# Verify credentials
aws sts get-caller-identity

# Should return your AWS account ID and ARN
```

## Step 2: Enable AWS Bedrock Services

### 2.1 Enable Bedrock Access

1. Go to AWS Console → Bedrock
2. Request model access for:
   - **Anthropic Claude 3.5 Sonnet v2** (required for agents)
   - **Anthropic Claude 3.7 Sonnet** (recommended)

```bash
# Check model access via CLI
aws bedrock list-foundation-models --region $AWS_REGION
```

### 2.2 Verify AgentCore Availability

```bash
# List AgentCore runtimes (should return empty list, not an error)
aws bedrock-agentcore list-runtimes --region $AWS_REGION
```

If you get "InvalidAction" or "AccessDenied", you may need to:
- Update AWS CLI: `pip install --upgrade awscli`
- Verify region supports AgentCore
- Check IAM permissions (see next step)

## Step 3: IAM Permissions

### 3.1 Required IAM Permissions

Your AWS user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:*",
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:PassRole",
        "iam:GetRole",
        "iam:CreatePolicy",
        "iam:PutRolePolicy",
        "ecr:CreateRepository",
        "ecr:DescribeRepositories",
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "codebuild:CreateProject",
        "codebuild:BatchGetBuilds",
        "codebuild:StartBuild",
        "s3:CreateBucket",
        "s3:PutObject",
        "s3:GetObject",
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:DescribeLogStreams"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3.2 Create IAM Policy (Optional)

If you don't have these permissions, create a custom policy:

```bash
# Save above JSON to file: agentcore-policy.json

aws iam create-policy \
  --policy-name AgentCoreDevelopmentPolicy \
  --policy-document file://agentcore-policy.json

# Attach to your user
aws iam attach-user-policy \
  --user-name YOUR_USERNAME \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/AgentCoreDevelopmentPolicy
```

## Step 4: Install AgentCore CLI

```bash
# Install bedrock-agentcore toolkit
pip install bedrock-agentcore[strands-agents]

# Or with uv
uv pip install bedrock-agentcore[strands-agents]

# Verify installation
agentcore --version
```

## Step 5: Project Setup

### 5.1 Clone/Setup Your Project

```bash
# If starting from this repository
git clone <your-repo>
cd outbound_auth_github

# Install dependencies
uv sync --all-extras
```

### 5.2 Create .env File

```bash
# Copy example
cp .env.example .env

# Edit .env with your credentials
# For GitHub agent:
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
AWS_REGION=ap-southeast-2

# For JIRA agent:
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your_jira_api_token
```

## Step 6: Initialize AgentCore Configuration

### 6.1 Create `.bedrock_agentcore.yaml`

The AgentCore CLI generates this file automatically on first deployment, but you can create it manually:

```bash
# For first agent deployment
agentcore configure \
  --entrypoint src/agents/github_agent/runtime.py \
  --region $AWS_REGION \
  --non-interactive
```

This creates `.bedrock_agentcore.yaml` with:
- AWS account ID and region
- Default execution roles
- ECR repository settings
- Memory configuration

### 6.2 Manual `.bedrock_agentcore.yaml` Template

If you prefer to create it manually:

```yaml
default_agent: github_agent
agents:
  github_agent:
    name: github_agent
    entrypoint: src/agents/github_agent/runtime.py
    platform: linux/arm64
    container_runtime: docker
    aws:
      execution_role_auto_create: true
      account: 'YOUR_AWS_ACCOUNT_ID'
      region: ap-southeast-2
      ecr_auto_create: true
      network_configuration:
        network_mode: PUBLIC
      protocol_configuration:
        server_protocol: HTTP
      observability:
        enabled: true
    authorizer_configuration: null
    request_header_configuration: null
    oauth_configuration:
      workload_name: runtime-github-workload
      credential_providers:
      - github-provider
```

**Important:**
- Replace `YOUR_AWS_ACCOUNT_ID` with your AWS account ID
- The file is `.gitignore`d for security (contains account-specific info)
- Each agent you add will get its own section

## Step 7: Set Up Credential Providers (OAuth)

### 7.1 GitHub Credential Provider

If using GitHub agent:

```bash
# Create GitHub OAuth App first
# https://github.com/settings/developers
# Enable Device Flow

# Run setup script
python setup_github_provider.py

# This creates the credential provider in AgentCore Identity
```

### 7.2 JIRA Credential Provider (Optional)

For JIRA agent:

```bash
aws bedrock-agentcore create-credential-provider \
  --region $AWS_REGION \
  --name jira-provider \
  --type API_TOKEN \
  --configuration '{
    "api_endpoint": "https://your-domain.atlassian.net",
    "auth_type": "basic",
    "email_field": "JIRA_EMAIL",
    "token_field": "JIRA_API_TOKEN"
  }'
```

## Step 8: First Agent Deployment

### 8.1 Create ECR Repository

```bash
# Create repository for your agent
aws ecr create-repository \
  --repository-name bedrock-agentcore-github_agent \
  --region $AWS_REGION
```

### 8.2 Deploy Agent

```bash
# Deploy using AgentCore CLI
agentcore launch

# What happens:
# 1. Creates IAM execution roles (if auto_create: true)
# 2. Creates CodeBuild project for ARM64 container builds
# 3. Builds Docker image in the cloud (no local Docker needed!)
# 4. Pushes to ECR
# 5. Creates AgentCore runtime
# 6. Sets up CloudWatch logging
# 7. Activates endpoint
```

### 8.3 Verify Deployment

```bash
# Check agent status
agentcore status

# List deployed agents
aws bedrock-agentcore list-runtimes --region $AWS_REGION
```

## Step 9: Test Your Agent

### 9.1 Invoke Agent

```bash
# Invoke with user ID (required for OAuth)
agentcore invoke '{"prompt": "Hello"}' --user-id "test-user"

# For GitHub agent
agentcore invoke '{"prompt": "list my repositories"}' --user-id "user-123"
```

### 9.2 View Logs

```bash
# Get agent ARN from deployment output or status
AGENT_ARN="arn:aws:bedrock-agentcore:ap-southeast-2:123456789012:runtime/github_agent-xyz"

# Tail logs
aws logs tail /aws/bedrock-agentcore/runtimes/github_agent-xyz/DEFAULT \
  --follow \
  --region $AWS_REGION
```

## Step 10: Deploy Additional Agents

### 10.1 Add More Agents to Configuration

Edit `.bedrock_agentcore.yaml` and add new agent sections:

```yaml
agents:
  github_agent:
    # ... existing config ...

  jira_agent:
    name: jira_agent
    entrypoint: src/agents/jira_agent/runtime.py
    platform: linux/arm64
    # ... similar config ...

  coding_agent:
    name: coding_agent
    entrypoint: src/agents/coding_agent/runtime.py
    # ... similar config ...
```

### 10.2 Deploy Each Agent

```bash
# Create ECR repositories
aws ecr create-repository --repository-name bedrock-agentcore-jira_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-coding_agent --region $AWS_REGION

# Deploy agents (using poe tasks from pyproject.toml)
uv run poe deploy-jira
uv run poe deploy-coding
uv run poe deploy-orchestrator
```

## Common Issues and Solutions

### Issue: "Access Denied" during deployment

**Solution:**
- Verify IAM permissions (see Step 3)
- Check AWS region supports AgentCore
- Ensure Bedrock model access is enabled

### Issue: "Credential provider not found"

**Solution:**
```bash
# List existing providers
aws bedrock-agentcore list-credential-providers --region $AWS_REGION

# Create if missing (see Step 7)
```

### Issue: "CodeBuild not authorized to assume role"

**Solution:**
- Wait 10 seconds for IAM role propagation
- Retry deployment: `agentcore launch`

### Issue: "ECR repository does not exist"

**Solution:**
```bash
# Create repository manually
aws ecr create-repository \
  --repository-name bedrock-agentcore-AGENT_NAME \
  --region $AWS_REGION
```

### Issue: ".bedrock_agentcore.yaml is gitignored but I need to share config"

**Solution:**
- Create a template file: `.bedrock_agentcore.yaml.template`
- Remove sensitive info (account IDs, ARNs)
- Document required values in README
- Each developer creates their own local copy

## Configuration Files Reference

### .bedrock_agentcore.yaml Structure

```yaml
default_agent: agent_name  # Default agent for `agentcore invoke`

agents:
  agent_name:
    name: agent_name
    entrypoint: src/agents/agent_name/runtime.py
    platform: linux/arm64  # or linux/amd64
    container_runtime: docker

    aws:
      execution_role: arn:aws:iam::... (auto-filled after first deploy)
      execution_role_auto_create: true
      account: 'YOUR_ACCOUNT_ID'
      region: ap-southeast-2
      ecr_repository: ACCOUNT.dkr.ecr.REGION.amazonaws.com/repo-name
      ecr_auto_create: false
      network_configuration:
        network_mode: PUBLIC  # or VPC
      protocol_configuration:
        server_protocol: HTTP
      observability:
        enabled: true

    bedrock_agentcore:
      agent_id: null  # Auto-filled after deployment
      agent_arn: null  # Auto-filled after deployment
      agent_session_id: null

    codebuild:
      project_name: null  # Auto-filled
      execution_role: null  # Auto-filled
      source_bucket: null  # Auto-filled

    memory:
      mode: STM_ONLY  # Short-term memory only
      memory_id: null  # Auto-filled
      memory_arn: null  # Auto-filled
      memory_name: agent_name_mem
      event_expiry_days: 30
      first_invoke_memory_check_done: false

    authorizer_configuration: null
    request_header_configuration: null

    oauth_configuration:
      workload_name: agent-workload-name
      credential_providers:
      - provider-name  # From Step 7
```

## Next Steps

After successful setup:

1. ✅ Test each agent individually
2. ✅ Set up CI/CD for automated deployments
3. ✅ Configure CloudWatch alarms for monitoring
4. ✅ Set up VPC networking if needed
5. ✅ Implement multi-environment setup (dev/staging/prod)

## Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/agents-agentcore.html)
- [Strands Framework](https://strandsagents.com/)
- [AgentCore Samples Repository](https://github.com/awslabs/amazon-bedrock-agentcore-samples)

## Support

If you encounter issues:

1. Check CloudWatch logs for detailed error messages
2. Verify IAM permissions
3. Ensure region supports AgentCore
4. Check AWS Service Health Dashboard
5. Review AgentCore quotas and limits
