# Quick Reference - All Commands

Quick copy-paste reference for all AgentCore commands.

## Setup Commands (One-Time)

### All-in-one Bootstrap
```bash
AWS_REGION=ap-southeast-2 ./scripts/setup-aws-flexible.sh
```

### Install Dependencies
```bash
uv sync --all-extras
```

### Configure All Agents
```bash
export AWS_REGION=ap-southeast-2

agentcore configure -e src/agents/github_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/planning_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/jira_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/coding_agent/runtime.py --region $AWS_REGION --non-interactive
agentcore configure -e src/agents/orchestrator_agent/runtime.py --region $AWS_REGION --non-interactive
```

### Create ECR Repositories
```bash
aws ecr create-repository --repository-name bedrock-agentcore-github_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-planning_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-jira_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-coding_agent --region $AWS_REGION
aws ecr create-repository --repository-name bedrock-agentcore-orchestrator_agent --region $AWS_REGION
```

### Setup OAuth Providers
```bash
# GitHub OAuth (required for GitHub agent)
uv run python setup_github_provider.py
# Replace an existing provider after credential changes
uv run python setup_github_provider.py --update --force

# JIRA OAuth (optional - can use environment variables for testing)
uv run python setup_jira_provider.py
# Replace an existing provider after credential changes
uv run python setup_jira_provider.py --update --force
```

## Deployment Commands

### Deploy All Agents
```bash
aws_use mingfang  # or your AWS profile

uv run poe deploy-github
uv run poe deploy-planning
uv run poe deploy-jira
uv run poe deploy-coding
uv run poe deploy-orchestrator
```

### Deploy Individual Agent
```bash
uv run poe deploy-github      # GitHub integration
uv run poe deploy-planning    # Implementation planning
uv run poe deploy-jira        # JIRA integration
uv run poe deploy-coding      # Code execution
uv run poe deploy-orchestrator # Workflow coordination
```

## Testing Commands

### Quick Tests (One-Liner Per Agent)
```bash
# GitHub Agent
uv run poe invoke-github '{"prompt": "list my repositories"}' --user-id "test-user"

# Planning Agent
uv run poe invoke-planning '{"prompt": "Create a plan for implementing user authentication"}' --user-id "test"

# JIRA Agent
uv run poe invoke-jira '{"prompt": "Get details for PROJ-123"}' --user-id "test"

# Coding Agent
uv run poe invoke-coding '{"prompt": "Setup a new workspace"}' --user-id "test"

# Orchestrator Agent
uv run poe invoke-orchestrator '{"prompt": "Based on PROJ-123, implement feature in myorg/myrepo"}' --user-id "test"
```

### GitHub Agent Test Suite
```bash
# List repositories
uv run poe invoke-github '{"prompt": "list my repositories"}' --user-id "alice"

# Get repo info
uv run poe invoke-github '{"prompt": "show me details about myorg/myrepo"}' --user-id "alice"

# Create repository
uv run poe invoke-github '{"prompt": "create a new repository called test-project"}' --user-id "alice"

# List issues
uv run poe invoke-github '{"prompt": "show issues in myorg/myrepo"}' --user-id "alice"

# Create issue
uv run poe invoke-github '{"prompt": "create an issue about fixing login bug"}' --user-id "alice"
```

### Planning Agent Test Suite
```bash
# Generate implementation plan
uv run poe invoke-planning '{"prompt": "Create a plan for adding JWT authentication"}' --user-id "test"

# Create architecture plan
uv run poe invoke-planning '{"prompt": "Design a microservices architecture for e-commerce"}' --user-id "test"
```

### JIRA Agent Test Suite
```bash
# Fetch ticket
uv run poe invoke-jira '{"prompt": "Get details for PROJ-123"}' --user-id "test"

# Parse requirements
uv run poe invoke-jira '{"prompt": "Parse requirements from PROJ-456"}' --user-id "test"

# Update status
uv run poe invoke-jira '{"prompt": "Move PROJ-123 to In Progress"}' --user-id "test"

# Add comment
uv run poe invoke-jira '{"prompt": "Add comment to PROJ-123: Implementation started"}' --user-id "test"

# Link GitHub issue
uv run poe invoke-jira '{"prompt": "Link GitHub issue #42 to PROJ-123"}' --user-id "test"
```

### Coding Agent Test Suite
```bash
# Setup workspace
uv run poe invoke-coding '{"prompt": "Setup a new workspace"}' --user-id "test"

# Create file
uv run poe invoke-coding '{"prompt": "Create a file hello.py with print(\"Hello World\")"}' --user-id "test"

# Run command
uv run poe invoke-coding '{"prompt": "Run python hello.py"}' --user-id "test"

# List files
uv run poe invoke-coding '{"prompt": "List files in current directory"}' --user-id "test"

# Run tests
uv run poe invoke-coding '{"prompt": "Run the test suite"}' --user-id "test"
```

### Orchestrator Agent Test Suite
```bash
# Full workflow
uv run poe invoke-orchestrator '{"prompt": "Based on PROJ-123, implement user login in acme/webapp"}' --user-id "test"

# Parse request
uv run poe invoke-orchestrator '{"prompt": "Parse this: Fix bug in PROJ-456"}' --user-id "test"

# Test workflow
uv run poe invoke-orchestrator '{"prompt": "Run tests for authentication module"}' --user-id "test"
```

## Monitoring Commands

### Check Status
```bash
# All agents
agentcore status

# Specific agent
agentcore status --agent github_agent
```

### View Logs
```bash
# Replace AGENT_ID with actual ID from deployment
AGENT_ID="github_agent-xyz123"

# Tail logs (follow)
aws logs tail /aws/bedrock-agentcore/runtimes/${AGENT_ID}/DEFAULT --follow --region $AWS_REGION

# View recent logs (last 1 hour)
aws logs tail /aws/bedrock-agentcore/runtimes/${AGENT_ID}/DEFAULT --since 1h --region $AWS_REGION

# View logs from specific time
aws logs tail /aws/bedrock-agentcore/runtimes/${AGENT_ID}/DEFAULT --since "2025-10-09T10:00:00" --region $AWS_REGION
```

### List All Runtimes
```bash
aws bedrock-agentcore list-runtimes --region $AWS_REGION
```

## Update/Redeploy Commands

### Redeploy After Code Changes
```bash
# Redeploy specific agent
uv run poe deploy-github

# Or use agentcore CLI
agentcore launch -a github_agent
```

### Update All Agents
```bash
uv run poe deploy-github
uv run poe deploy-planning
uv run poe deploy-jira
uv run poe deploy-coding
uv run poe deploy-orchestrator
```

## Environment Variables

### Required for GitHub Agent
```bash
export GITHUB_CLIENT_ID="your_github_oauth_client_id"
export GITHUB_CLIENT_SECRET="your_github_oauth_client_secret"
```

### Required for JIRA Agent
```bash
# Atlassian OAuth 2.0 (required)
export ATLASSIAN_CLIENT_ID="your_atlassian_client_id"
export ATLASSIAN_CLIENT_SECRET="your_atlassian_client_secret"
export JIRA_URL="https://your-domain.atlassian.net"
```

### AWS Configuration
```bash
export AWS_REGION="ap-southeast-2"  # Sydney region
```

## Troubleshooting Commands

### Check IAM Permissions
```bash
aws sts get-caller-identity
```

### Verify Bedrock Access
```bash
aws bedrock list-foundation-models --region $AWS_REGION
```

### Check ECR Repositories
```bash
aws ecr describe-repositories --region $AWS_REGION
```

### Delete and Recreate Agent
```bash
# Delete agent
aws bedrock-agentcore delete-runtime --runtime-arn <AGENT_ARN> --region $AWS_REGION

# Redeploy
uv run poe deploy-github
```

## Agent Overview

| Agent | Purpose | OAuth | Port |
|-------|---------|-------|------|
| **github_agent** | GitHub integration | ✅ Yes | 8000 |
| **planning_agent** | Implementation planning | ❌ No | 8000 |
| **jira_agent** | JIRA integration | ❌ No | 8000 |
| **coding_agent** | Code execution | ❌ No | 8000 |
| **orchestrator_agent** | Workflow coordination | ❌ No | 8000 |

## Documentation Links

- **Main README**: [README.md](README.md)
- **AWS Setup Guide**: [docs/AWS-AgentCore-Setup.md](docs/AWS-AgentCore-Setup.md)
- **GitHub Agent**: Main README
- **Planning Agent**: [docs/Planning-Agent-Implementation-Plan.md](docs/Planning-Agent-Implementation-Plan.md)
- **JIRA Agent**: [docs/JIRA-Agent-Setup.md](docs/JIRA-Agent-Setup.md)
- **Coding Agent**: [docs/Coding-Agent-Setup.md](docs/Coding-Agent-Setup.md)
- **Orchestrator Agent**: [docs/Orchestrator-Agent-Setup.md](docs/Orchestrator-Agent-Setup.md)

## Common Workflows

### End-to-End Feature Implementation
```bash
# 1. Fetch JIRA requirements
uv run poe invoke-jira '{"prompt": "Parse requirements from PROJ-123"}' --user-id "dev"

# 2. Generate implementation plan
uv run poe invoke-planning '{"prompt": "Create plan for: [paste requirements]"}' --user-id "dev"

# 3. Execute implementation
uv run poe invoke-coding '{"prompt": "Execute the plan"}' --user-id "dev"

# 4. Update JIRA
uv run poe invoke-jira '{"prompt": "Add comment to PROJ-123: Implementation complete"}' --user-id "dev"
```

### Or Use Orchestrator (All-in-One)
```bash
uv run poe invoke-orchestrator '{"prompt": "Based on PROJ-123, implement feature in myorg/myrepo"}' --user-id "dev"
```
