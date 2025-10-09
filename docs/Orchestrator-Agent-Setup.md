# Orchestrator Agent Setup Guide

## Overview

The Orchestrator Agent coordinates multiple specialized agents to execute end-to-end workflows. It parses user requests, determines workflow sequences, and coordinates agent execution.

## Prerequisites

1. AWS credentials configured (`aws_use mingfang`)
2. AgentCore CLI installed
3. All other agents deployed (JIRA, Planning, GitHub, Coding)
4. Orchestrator agent added to `.bedrock_agentcore.yaml`

## AgentCore Configuration

Add this to your `.bedrock_agentcore.yaml` file:

```yaml
agents:
  # ... existing agents ...

  orchestrator_agent:
    name: orchestrator_agent
    entrypoint: src/agents/orchestrator_agent/runtime.py
    platform: linux/arm64
    container_runtime: docker
    aws:
      execution_role: arn:aws:iam::670326884047:role/AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-d92c6a81b2
      execution_role_auto_create: true
      account: '670326884047'
      region: ap-southeast-2
      ecr_repository: 670326884047.dkr.ecr.ap-southeast-2.amazonaws.com/bedrock-agentcore-orchestrator_agent
      ecr_auto_create: false
      network_configuration:
        network_mode: PUBLIC
      protocol_configuration:
        server_protocol: HTTP
      observability:
        enabled: true
    authorizer_configuration: null
    request_header_configuration: null
    oauth_configuration: null
```

## Deployment

1. **Create ECR repository first** (if not exists):
```bash
aws ecr create-repository --repository-name bedrock-agentcore-orchestrator_agent --region ap-southeast-2
```

2. **Deploy the agent:**
```bash
aws_use mingfang && uv run poe deploy-orchestrator
```

3. **Test the agent:**
```bash
# Parse a request
uv run poe invoke-orchestrator '{
  "prompt": "Based on PROJ-123, implement user authentication in myorg/myrepo"
}' --user-id "test"

# Simple workflow
uv run poe invoke-orchestrator '{
  "prompt": "Run tests for authentication module"
}' --user-id "test"
```

## Available Tools

### 1. parse_user_request
Extract JIRA ticket, GitHub repo, and request type from natural language input.

**Example:** "Based on PROJ-123, implement feature in myorg/myrepo"

**Extracts:**
- JIRA Ticket: PROJ-123
- GitHub Repo: myorg/myrepo
- Request Type: implement

### 2. determine_workflow
Determine the sequence of agent calls based on request type.

**Request Types:**
- **implement**: Feature implementation workflow
- **fix**: Bug fixing workflow
- **test**: Testing workflow
- **review**: Code review workflow

**Example:** determine_workflow("implement", has_jira=True, has_repo=True)

### 3. execute_workflow_sequence
Coordinate execution of multiple agents in sequence.

**Example:** execute_workflow_sequence("implement", "PROJ-123", "myorg/myrepo", "user-123")

## Workflow Types

### Implementation Workflow
**Trigger:** Keywords: implement, add, create, build, feature

**Steps:**
1. JIRA Agent: Fetch ticket requirements
2. Planning Agent: Generate implementation plan
3. GitHub Agent: Create GitHub issue (if repo provided)
4. Coding Agent: Execute the plan
5. GitHub Agent: Post implementation results (if repo provided)
6. JIRA Agent: Update ticket status

**Example Request:** "Based on JIRA-123, implement user authentication in myorg/myrepo"

### Fix Workflow
**Trigger:** Keywords: fix, bug, issue, error

**Steps:**
1. JIRA Agent: Fetch bug details
2. Planning Agent: Generate fix plan
3. Coding Agent: Execute fix
4. JIRA Agent: Update bug status

**Example Request:** "Fix the bug in PROJ-456"

### Test Workflow
**Trigger:** Keywords: test, testing, validate

**Steps:**
1. Coding Agent: Run test suite
2. GitHub Agent: Post test results (if repo provided)

**Example Request:** "Run tests for the authentication module"

### Review Workflow
**Trigger:** Keywords: review, check, audit

**Steps:**
1. JIRA Agent: Fetch item for review
2. Planning Agent: Generate review checklist

**Example Request:** "Review the implementation in PROJ-789"

## Example Workflows

### End-to-End Feature Implementation

```bash
uv run poe invoke-orchestrator '{
  "prompt": "Based on PROJ-123, implement user login feature in acme/webapp"
}' --user-id "user-123"
```

**Expected Flow:**
1. Parse request → Extract PROJ-123, acme/webapp, type: implement
2. Determine workflow → Implementation workflow with 6 steps
3. Execute:
   - JIRA: Fetch PROJ-123 requirements
   - Planning: Generate implementation plan
   - GitHub: Create issue in acme/webapp
   - Coding: Execute implementation
   - GitHub: Post results
   - JIRA: Update PROJ-123 status

### Bug Fix

```bash
uv run poe invoke-orchestrator '{
  "prompt": "Fix the authentication bug in PROJ-456"
}' --user-id "user-123"
```

**Expected Flow:**
1. Parse request → Extract PROJ-456, type: fix
2. Determine workflow → Fix workflow with 4 steps
3. Execute:
   - JIRA: Fetch PROJ-456 bug details
   - Planning: Generate fix plan
   - Coding: Execute fix
   - JIRA: Update PROJ-456 status

### Testing

```bash
uv run poe invoke-orchestrator '{
  "prompt": "Run tests for authentication module in myorg/api"
}' --user-id "user-123"
```

**Expected Flow:**
1. Parse request → Extract myorg/api, type: test
2. Determine workflow → Test workflow with 2 steps
3. Execute:
   - Coding: Run test suite
   - GitHub: Post test results to myorg/api

## Integration with Other Agents

The Orchestrator Agent is designed to coordinate all other agents:

- **JIRA Agent**: Fetch tickets, update status
- **Planning Agent**: Generate plans from requirements
- **GitHub Agent**: Manage GitHub issues and PRs
- **Coding Agent**: Execute code changes and tests

## CloudWatch Logs

Monitor Orchestrator Agent execution:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/orchestrator_agent-*/DEFAULT \
  --log-stream-name-prefix "2025/10/08/[runtime-logs]" \
  --follow
```

## Troubleshooting

### Error: "Agent 'orchestrator_agent' not found"
- Make sure you added the orchestrator_agent configuration to `.bedrock_agentcore.yaml`
- The file is gitignored, so you need to add it manually

### Error: "Repository does not exist"
- Create ECR repository first: `aws ecr create-repository --repository-name bedrock-agentcore-orchestrator_agent`

### Error: "Cannot determine workflow"
- Provide either JIRA ticket or GitHub repo
- Use clear request type keywords (implement, fix, test, review)
- Example: "Based on PROJ-123, implement feature"

### Error: "Agent ARN not configured"
- The Orchestrator needs ARNs of other agents
- Set environment variables for agent ARNs (in production)
- For testing, workflows provide execution plans without actual agent calls

## Current Implementation

**Note:** The current implementation provides workflow planning and descriptions. To execute actual agent calls:

1. Configure agent ARNs in environment variables:
   - `JIRA_AGENT_ARN`
   - `PLANNING_AGENT_ARN`
   - `GITHUB_AGENT_ARN`
   - `CODING_AGENT_ARN`

2. Implement boto3 bedrock-agent-runtime client calls in `coordinator.py`

3. Add error handling and retry logic for agent invocations

## Architecture

```
User Request
    ↓
Orchestrator Agent
    ↓
Parse Request (extract JIRA, repo, type)
    ↓
Determine Workflow (select agent sequence)
    ↓
Execute Workflow
    ├─→ JIRA Agent
    ├─→ Planning Agent
    ├─→ GitHub Agent
    ├─→ Coding Agent
    └─→ Final Results
```

## Next Steps

After Orchestrator Agent is working:
1. ✅ Test request parsing
2. ✅ Test workflow determination
3. ⬜ Implement actual agent invocation via boto3
4. ⬜ Add retry logic with exponential backoff
5. ⬜ Test end-to-end workflow: JIRA → Planning → GitHub → Coding → JIRA update
6. ⬜ Add context passing between agents
7. ⬜ Implement error recovery strategies
