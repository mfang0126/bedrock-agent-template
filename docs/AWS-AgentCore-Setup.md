# AWS AgentCore Setup Guide for New AWS Accounts

Complete guide for setting up AWS Bedrock AgentCore from scratch in a new AWS account.

## Prerequisites

- AWS Account with admin access
- AWS CLI installed and configured
- Python 3.10+ installed
- `uv` package manager installed

---

## 🚀 Quick Start (Copy & Paste All Commands)

**For experienced users - complete setup in 5 minutes:**

```bash
# 1. Set region
export AWS_REGION=ap-southeast-2

# 2. Verify Bedrock access
aws bedrock-agentcore list-runtimes --region $AWS_REGION

# 3. Install dependencies
uv sync --all-extras

# 4. Configure all agents
agentcore configure -e src/agents/github_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/planning_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/jira_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/coding_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/orchestrator_agent/runtime.py --region $AWS_REGION --non-interactive

# 5. Create ECR repositories
aws ecr create-repository --repository-name bedrock-agentcore-github_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-planning_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-jira_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-coding_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-orchestrator_agent --region $AWS_REGION

# 6. Setup OAuth providers
uv run python setup_github_provider.py  # For GitHub agent
uv run python setup_github_provider.py --update --force  # Replace GitHub provider (optional)
uv run python setup_jira_provider.py    # For JIRA agent (optional - can use API token)
uv run python setup_jira_provider.py --update --force    # Replace JIRA provider (optional)

# 7. Deploy all agents
uv run poe deploy-github
uv run poe deploy-planning
uv run poe deploy-jira
uv run poe deploy-coding
uv run poe deploy-orchestrator

# 8. Test
uv run poe invoke-planning '{"prompt": "Hello"}' --user-id "test"
```

> 💡 Prefer an interactive helper? Run `AWS_REGION=ap-southeast-2 ./scripts/setup-aws-flexible.sh` to execute the same steps with guardrails and idempotent checks.

**Continue reading for detailed explanations of each step.**

---

## Step 1: AWS Account Setup

### 1.1 Set AWS Region

This repository is configured for Sydney region:

```bash
# Set region to Sydney
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

### 6.1 Available Agents in This Repository

This repository contains 5 production-ready agents:

| Agent | Purpose | OAuth Required | Key Features |
|-------|---------|----------------|--------------|
| **github_agent** | GitHub integration | ✅ Yes (3LO) | Repos, issues, PRs management |
| **planning_agent** | Implementation planning | ❌ No | Generate plans from requirements |
| **jira_agent** | JIRA integration | ❌ No (API token) | Fetch tickets, update status |
| **coding_agent** | Code execution | ❌ No | Execute plans in isolated workspaces |
| **orchestrator_agent** | Workflow coordination | ❌ No | Coordinate multi-agent workflows |

### 6.2 Configure All Agents (Copy & Run)

Run these commands to configure all agents. The first agent creates `.bedrock_agentcore.yaml`, subsequent agents add to it.

#### Option 1: Configure All Agents at Once

```bash
# Set your AWS region
export AWS_REGION=ap-southeast-2

# 1. GitHub Agent (OAuth required)
agentcore configure \
  --entrypoint src/agents/github_agent/runtime.py \
  --region $AWS_REGION \
  --non-interactive

# 2. Planning Agent
agentcore configure \
  --entrypoint src/agents/planning_agent/runtime.py \
  --region $AWS_REGION \
  --non-interactive

# 3. JIRA Agent
agentcore configure \
  --entrypoint src/agents/jira_agent/runtime.py \
  --region $AWS_REGION \
  --non-interactive

# 4. Coding Agent
agentcore configure \
  --entrypoint src/agents/coding_agent/runtime.py \
  --region $AWS_REGION \
  --non-interactive

# 5. Orchestrator Agent
agentcore configure \
  --entrypoint src/agents/orchestrator_agent/runtime.py \
  --region $AWS_REGION \
  --non-interactive
```

#### Option 2: Configure Individual Agents

Choose which agents you need:

**GitHub Agent** (OAuth - list repos, create issues):
```bash
agentcore configure -e src/agents/github_agent/runtime.py --region ap-southeast-2 --non-interactive
```

**Planning Agent** (Generate implementation plans):
```bash
agentcore configure -e src/agents/planning_agent/runtime.py --region ap-southeast-2 --non-interactive
```

**JIRA Agent** (Fetch tickets, update status):
```bash
agentcore configure -e src/agents/jira_agent/runtime.py --region ap-southeast-2 --non-interactive
```

**Coding Agent** (Execute code in isolated workspaces):
```bash
agentcore configure -e src/agents/coding_agent/runtime.py --region ap-southeast-2 --non-interactive
```

**Orchestrator Agent** (Coordinate multi-agent workflows):
```bash
agentcore configure -e src/agents/orchestrator_agent/runtime.py --region ap-southeast-2 --non-interactive
```

### 6.3 What This Creates

After running configure, you'll have `.bedrock_agentcore.yaml` with:
- AWS account ID and region
- Default execution roles
- ECR repository settings
- Memory configuration
- Agent-specific settings (OAuth, observability, etc.)

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
uv run python setup_github_provider.py

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

## Step 8: Deploy All Agents

### 8.1 Create ECR Repositories (One-Time Setup)

Create ECR repositories for all agents before deployment:

```bash
# Set your AWS region
export AWS_REGION=ap-southeast-2

# Create ECR repositories for all agents
aws ecr create-repository --repository-name bedrock-agentcore-github_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-planning_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-jira_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-coding_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-orchestrator_agent --region $AWS_REGION
```

**Note:** If repository already exists, you'll get an error - that's okay, skip to next step.

### 8.2 Deploy All Agents Using Poe Tasks

This repository includes `poethepoet` tasks in `pyproject.toml` for easy deployment:

```bash
# Ensure you're authenticated to AWS
aws_use mingfang  # or your AWS profile

# Deploy all agents (one by one)
uv run poe deploy-github
uv run poe deploy-planning
uv run poe deploy-jira
uv run poe deploy-coding
uv run poe deploy-orchestrator
```

**What each deploy command does:**
1. Copies agent-specific Dockerfile to root
2. Creates IAM execution roles (if auto_create: true)
3. Creates CodeBuild project for ARM64 builds
4. Builds Docker image in the cloud (no local Docker!)
5. Pushes to ECR
6. Creates AgentCore runtime
7. Sets up CloudWatch logging
8. Activates endpoint

### 8.3 Alternative: Deploy Using AgentCore CLI

If you prefer using `agentcore` CLI directly:

```bash
# Deploy each agent individually
agentcore launch -a github_agent
agentcore launch -a planning_agent
agentcore launch -a jira_agent
agentcore launch -a coding_agent
agentcore launch -a orchestrator_agent
```

### 8.4 Verify All Deployments

```bash
# Check status of all agents
agentcore status

# List all deployed runtimes
aws bedrock-agentcore list-runtimes --region $AWS_REGION

# Check specific agent
agentcore status --agent github_agent
```

**Expected Output:**
```
✅ Agent: github_agent
   ARN: arn:aws:bedrock-agentcore:ap-southeast-2:123456789012:runtime/github_agent-xyz
   Status: ACTIVE
   Endpoint: READY

✅ Agent: planning_agent
   ARN: arn:aws:bedrock-agentcore:ap-southeast-2:123456789012:runtime/planning_agent-abc
   Status: ACTIVE
   Endpoint: READY

... (and so on for all agents)
```

## Step 9: Test All Agents

### 9.1 Test Each Agent Using Poe Tasks

Quick test commands for all agents:

```bash
# 1. GitHub Agent (requires OAuth - user will authorize via browser)
uv run poe invoke-github '{"prompt": "list my repositories"}' --user-id "test-user"

# 2. Planning Agent (generate implementation plan)
uv run poe invoke-planning '{"prompt": "Create a plan for implementing user authentication"}' --user-id "test"

# 3. JIRA Agent (fetch JIRA ticket - replace PROJ-123 with real ticket)
uv run poe invoke-jira '{"prompt": "Get details for PROJ-123"}' --user-id "test"

# 4. Coding Agent (setup workspace and execute code)
uv run poe invoke-coding '{"prompt": "Setup a new workspace"}' --user-id "test"

# 5. Orchestrator Agent (coordinate workflow)
uv run poe invoke-orchestrator '{"prompt": "Based on PROJ-123, implement feature in myorg/myrepo"}' --user-id "test"
```

### 9.2 Detailed Test Examples Per Agent

#### GitHub Agent Tests
```bash
# List repositories
uv run poe invoke-github '{"prompt": "list my repositories"}' --user-id "alice"

# Get repo info
uv run poe invoke-github '{"prompt": "show me details about myorg/myrepo"}' --user-id "alice"

# Create repository
uv run poe invoke-github '{"prompt": "create a new repository called test-project"}' --user-id "alice"

# List issues
uv run poe invoke-github '{"prompt": "show issues in myorg/myrepo"}' --user-id "alice"
```

#### Planning Agent Tests
```bash
# Generate implementation plan
uv run poe invoke-planning '{"prompt": "Create a plan for adding JWT authentication"}' --user-id "test"

# Create architecture plan
uv run poe invoke-planning '{"prompt": "Design a microservices architecture for e-commerce"}' --user-id "test"
```

#### JIRA Agent Tests
```bash
# Fetch ticket (replace with your ticket ID)
uv run poe invoke-jira '{"prompt": "Get details for PROJ-123"}' --user-id "test"

# Parse requirements
uv run poe invoke-jira '{"prompt": "Parse requirements from PROJ-456"}' --user-id "test"

# Update status
uv run poe invoke-jira '{"prompt": "Move PROJ-123 to In Progress"}' --user-id "test"

# Add comment
uv run poe invoke-jira '{"prompt": "Add comment to PROJ-123: Implementation started"}' --user-id "test"
```

#### Coding Agent Tests
```bash
# Setup workspace
uv run poe invoke-coding '{"prompt": "Setup a new workspace"}' --user-id "test"

# Create file
uv run poe invoke-coding '{"prompt": "Create a file hello.py with print(\"Hello World\")"}' --user-id "test"

# Run command
uv run poe invoke-coding '{"prompt": "Run python hello.py"}' --user-id "test"

# Run tests
uv run poe invoke-coding '{"prompt": "Run the test suite"}' --user-id "test"
```

#### Orchestrator Agent Tests
```bash
# Full workflow
uv run poe invoke-orchestrator '{"prompt": "Based on PROJ-123, implement user login in acme/webapp"}' --user-id "test"

# Parse request
uv run poe invoke-orchestrator '{"prompt": "Parse this: Fix bug in PROJ-456"}' --user-id "test"

# Test workflow
uv run poe invoke-orchestrator '{"prompt": "Run tests for authentication module"}' --user-id "test"
```

### 9.3 View Logs for Specific Agent

```bash
# Set your agent ID (get from deployment output or agentcore status)
GITHUB_AGENT_ID="github_agent-xyz123"
PLANNING_AGENT_ID="planning_agent-abc456"
JIRA_AGENT_ID="jira_agent-def789"
CODING_AGENT_ID="coding_agent-ghi012"
ORCHESTRATOR_AGENT_ID="orchestrator_agent-jkl345"

# Tail logs for any agent
aws logs tail /aws/bedrock-agentcore/runtimes/${GITHUB_AGENT_ID}/DEFAULT \
  --follow \
  --region $AWS_REGION

# View recent logs (last 1 hour)
aws logs tail /aws/bedrock-agentcore/runtimes/${JIRA_AGENT_ID}/DEFAULT \
  --since 1h \
  --region $AWS_REGION
```

### 9.4 Using AgentCore CLI Directly

Alternative to poe tasks:

```bash
# Invoke any agent
agentcore invoke -a github_agent '{"prompt": "list my repositories"}' --user-id "alice"
agentcore invoke -a planning_agent '{"prompt": "create a plan"}' --user-id "test"
agentcore invoke -a jira_agent '{"prompt": "get PROJ-123"}' --user-id "test"
agentcore invoke -a coding_agent '{"prompt": "setup workspace"}' --user-id "test"
agentcore invoke -a orchestrator_agent '{"prompt": "coordinate workflow"}' --user-id "test"
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
