# 🚀 Quick Reference Card

## Setup & Deploy (First Time)

```bash
# 1. Make scripts executable
bash make_executable.sh

# 2. Complete setup and deploy
./setup_and_deploy.sh
```

## Testing Agents

### Local Testing
```bash
# Test both agents locally
./test_agents_local.sh
```

### GitHub Agent
```bash
# What can you do
./invoke_github.sh "what can you do"

# List repositories
./invoke_github.sh "list my repositories"

# Create issue
./invoke_github.sh "create an issue titled 'Bug Fix' with label 'bug'"

# Get repository info
./invoke_github.sh "show details of repository my-repo"
```

### Jira Agent
```bash
# What can you do
./invoke_jira.sh "what can you do"

# List projects
./invoke_jira.sh "list my projects"

# Create issue
./invoke_jira.sh "create an issue in project ABC with title 'New Feature'"

# List issues
./invoke_jira.sh "show open issues in project ABC"
```

## Deployment

### Deploy Both Agents
```bash
./deploy_agents.sh
```

### Deploy Individual Agent
```bash
# GitHub
cd agents/github-agent
agentcore launch

# Jira
cd agents/jira-agent
agentcore launch
```

## Viewing Logs

### GitHub Agent Logs
```bash
# Real-time
aws logs tail /aws/bedrock-agentcore/runtimes/github-agent-XXXXX \
    --log-stream-name-prefix "2025/10/15/[runtime-logs]" --follow

# Last hour
aws logs tail /aws/bedrock-agentcore/runtimes/github-agent-XXXXX \
    --log-stream-name-prefix "2025/10/15/[runtime-logs]" --since 1h
```

### Jira Agent Logs
```bash
# Real-time
aws logs tail /aws/bedrock-agentcore/runtimes/jira-agent-XXXXX \
    --log-stream-name-prefix "2025/10/15/[runtime-logs]" --follow

# Last hour
aws logs tail /aws/bedrock-agentcore/runtimes/jira-agent-XXXXX \
    --log-stream-name-prefix "2025/10/15/[runtime-logs]" --since 1h
```

## Environment Variables

### GitHub
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### Jira
```bash
export JIRA_API_TOKEN="your_api_token"
export JIRA_EMAIL="your@email.com"
export JIRA_CLOUD_ID="your_cloud_id"
```

## Troubleshooting

### Check Agent Status
```bash
agentcore list
```

### Delete Agent
```bash
agentcore delete <agent-arn>
```

### Update Agent
```bash
cd agents/github-agent  # or jira-agent
agentcore launch --update
```

## File Locations

```
coding-agent-agentcore/
├── agents/
│   ├── common/               # Shared response protocol
│   ├── github-agent/         # GitHub agent
│   └── jira-agent/           # Jira agent
├── setup_and_deploy.sh       # Complete setup
├── deploy_agents.sh          # Deploy only
├── test_agents_local.sh      # Local tests
├── invoke_github.sh          # Test GitHub
├── invoke_jira.sh            # Test Jira
├── DEPLOYMENT_GUIDE.md       # Full guide
└── IMPLEMENTATION_SUMMARY.md # What we built
```

## Mode Detection

### Client Mode (Default)
```json
{
  "prompt": "your command"
}
```
**Result**: Streaming text with emojis

### Agent Mode (A2A)
```json
{
  "prompt": "your command",
  "_agent_call": true
}
```
**Result**: Structured JSON response

## Quick Health Check

```bash
# 1. Check if scripts are executable
ls -la *.sh

# 2. Test locally
./test_agents_local.sh

# 3. Check deployments
agentcore list

# 4. Test invocation
./invoke_github.sh "what can you do"
```

## Common Commands

```bash
# Full reset and redeploy
./setup_and_deploy.sh

# Just deploy
./deploy_agents.sh

# Quick test
./invoke_github.sh "list my repositories"

# View logs
aws logs tail /aws/bedrock-agentcore/runtimes/github-agent-XXXXX --follow
```

## Getting Help

1. Check logs in CloudWatch
2. Review `DEPLOYMENT_GUIDE.md`
3. Read `IMPLEMENTATION_SUMMARY.md`
4. Check `.bedrock_agentcore.yaml` config
5. Verify environment variables

---

**Pro Tip**: Bookmark this file for quick reference! 🔖
