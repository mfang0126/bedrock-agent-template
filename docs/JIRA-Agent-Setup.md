# JIRA Agent Setup Guide

## Prerequisites

1. JIRA instance (Cloud or Server)
2. JIRA API Token
3. AWS credentials configured (`aws_use mingfang`)

## Environment Variables

Set these before deploying:

```bash
export JIRA_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@company.com"
export JIRA_API_TOKEN="your_api_token_here"  # For testing only
```

**Production:** Tokens should be stored in AgentCore Identity, not environment variables.

## AgentCore Configuration

Add this to your `.bedrock_agentcore.yaml` file:

```yaml
agents:
  # ... existing agents ...

  jira_agent:
    name: jira_agent
    entrypoint: src/agents/jira_agent/runtime.py
    platform: linux/arm64
    container_runtime: docker
    aws:
      execution_role: arn:aws:iam::670326884047:role/AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-d92c6a81b2
      execution_role_auto_create: true
      account: '670326884047'
      region: ap-southeast-2
      ecr_repository: 670326884047.dkr.ecr.ap-southeast-2.amazonaws.com/bedrock-agentcore-jira_agent
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

1. **Deploy the agent:**
```bash
aws_use mingfang && uv run poe deploy-jira
```

2. **Test the agent:**
```bash
# Fetch a ticket
uv run poe invoke-jira '{"prompt": "Get details for PROJ-123"}' --user-id "test"

# Update ticket status
uv run poe invoke-jira '{"prompt": "Move PROJ-123 to In Progress"}' --user-id "test"

# Add comment
uv run poe invoke-jira '{"prompt": "Add comment to PROJ-123: Implementation started"}' --user-id "test"
```

## Available Tools

### 1. fetch_jira_ticket
Fetch complete ticket details including:
- Title and description
- Status and priority
- Assignee and sprint
- Acceptance criteria (auto-extracted)
- Labels

**Example:** "Get details for PROJ-123"

### 2. parse_ticket_requirements
Extract structured requirements for Planning Agent.

**Example:** "Parse requirements from PROJ-123"

### 3. update_jira_status
Change ticket status (workflow transitions).

**Example:** "Move PROJ-456 to In Progress"

### 4. add_jira_comment
Add comment to ticket, optionally with GitHub link.

**Example:** "Add comment to PROJ-123: PR merged successfully"

### 5. link_github_issue
Link GitHub issue/PR to JIRA ticket.

**Example:** "Link GitHub issue #42 to PROJ-123"

## Authentication

### Development (Environment Variables)
For local testing, use environment variables:
```bash
export JIRA_API_TOKEN="your_token"
```

### Production (AgentCore Identity)
Set up a JIRA credential provider in AgentCore Identity:

```bash
# Create JIRA provider (similar to GitHub provider)
aws bedrock-agentcore create-credential-provider \
  --name jira-provider \
  --type API_TOKEN \
  --config '{
    "api_endpoint": "https://your-domain.atlassian.net",
    "auth_type": "basic",
    "email_field": "JIRA_EMAIL",
    "token_field": "JIRA_API_TOKEN"
  }'
```

Then add to agent configuration:
```yaml
oauth_configuration:
  workload_name: jira-agent-workload
  credential_providers:
  - jira-provider
```

## Troubleshooting

### Error: "Agent 'jira_agent' not found"
- Make sure you added the jira_agent configuration to `.bedrock_agentcore.yaml`
- The file is gitignored, so you need to add it manually

### Error: "Authentication failed"
- Check JIRA_EMAIL and JIRA_API_TOKEN are set correctly
- Verify your JIRA API token is valid
- For JIRA Cloud, tokens are from: https://id.atlassian.com/manage-profile/security/api-tokens

### Error: "Ticket not found"
- Verify ticket ID format: PROJECT-123
- Check you have permission to view the ticket in JIRA
- Ensure JIRA URL is correct (with or without trailing slash doesn't matter)

## Integration with Other Agents

### With Planning Agent
```bash
# 1. Fetch JIRA ticket
uv run poe invoke-jira '{"prompt": "Parse requirements from PROJ-123"}' --user-id "test"

# 2. Send to Planning Agent
uv run poe invoke-planning '{"prompt": "Generate plan for: [paste requirements]"}' --user-id "test"
```

### With GitHub Agent
```bash
# 1. Create GitHub issue from JIRA ticket
# (Use Orchestrator Agent for this workflow)

# 2. Link them
uv run poe invoke-jira '{"prompt": "Link GitHub issue #42 to PROJ-123"}' --user-id "test"
```

## CloudWatch Logs

Monitor JIRA agent execution:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/jira_agent-*/DEFAULT \
  --log-stream-name-prefix "2025/10/08/[runtime-logs]" \
  --follow
```

## Next Steps

After JIRA Agent is working:
1. ✅ Test all tools with real JIRA instance
2. ⬜ Implement Coding Agent
3. ⬜ Implement Orchestrator Agent
4. ⬜ Test end-to-end workflow: JIRA → Planning → GitHub → Coding → JIRA update
