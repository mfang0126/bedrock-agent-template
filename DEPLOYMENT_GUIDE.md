# GitHub and Jira Agents - Quick Start Guide

This guide will help you deploy and invoke the GitHub and Jira agents with dual-mode support (client and agent-to-agent communication).

## 🏗️ Architecture Overview

Both agents now support **dual-mode communication**:

1. **Client Mode** (default): Streaming human-readable text with progress indicators
2. **Agent Mode**: Structured JSON responses for agent-to-agent (A2A) communication

### Mode Detection

The agents automatically detect the mode based on payload markers:
- Presence of `_agent_call` or `source_agent` → Agent mode
- A2A protocol headers → Agent mode
- Default → Client mode

## 📁 Project Structure

```
coding-agent-agentcore/
├── agents/
│   ├── common/                      # Shared response protocol
│   │   ├── __init__.py
│   │   └── response_protocol.py    # Dual-mode handler
│   ├── github-agent/                # GitHub operations
│   │   └── src/
│   │       └── runtime.py          # Fixed dual-mode runtime
│   └── jira-agent/                  # Jira operations
│       └── src/
│           └── runtime.py          # Fixed dual-mode runtime
├── deploy_agents.sh                 # Deploy both agents
├── invoke_github.sh                 # Test GitHub agent
└── invoke_jira.sh                   # Test Jira agent
```

## 🚀 Deployment

### Prerequisites

1. AWS CLI configured
2. AgentCore CLI installed: `pip install bedrock-agentcore`
3. `uv` package manager installed
4. Proper AWS permissions for AgentCore

### Step 1: Make Scripts Executable

```bash
chmod +x deploy_agents.sh scripts/invoke_github.sh scripts/invoke_jira.sh
```

### Step 2: Deploy Both Agents

```bash
./deploy_agents.sh
```

This will:
- Deploy GitHub agent to AWS AgentCore
- Deploy Jira agent to AWS AgentCore
- Show deployment summary with ARNs

### Step 3: Note the Agent ARNs

After deployment, save the ARN for each agent:

```
GitHub Agent ARN: arn:aws:bedrock-agentcore:region:account:runtime/github-agent-XXXXX
Jira Agent ARN: arn:aws:bedrock-agentcore:region:account:runtime/jira-agent-XXXXX
```

## 🧪 Testing the Agents

### Test GitHub Agent

```bash
# Basic test
scripts/invoke_github.sh "what can you do"

# List repositories
scripts/invoke_github.sh "list my repositories"

# Create an issue
scripts/invoke_github.sh "create an issue titled 'Test Issue' with label 'bug'"
```

### Test Jira Agent

```bash
# Basic test
scripts/invoke_jira.sh "what can you do"

# List projects
scripts/invoke_jira.sh "list my projects"

# Create an issue
scripts/invoke_jira.sh "create an issue in project ABC with title 'Test Task'"
```

## 📊 Understanding the Output

### Client Mode Output (Default)

When you invoke directly, you'll see:
```
============================================================
📥 GitHub Agent Request
   Mode: CLIENT
   Input: what can you do
============================================================

🔐 Authenticating with GitHub...
✅ GitHub authentication successful

🚀 Processing in CLIENT mode (streaming)...

[Streaming agent response with real-time events]

✅ GitHub operation completed
```

### Agent Mode Output (A2A Communication)

When called by another agent:
```json
{
  "success": true,
  "message": "GitHub operation completed successfully",
  "data": {
    "output": "..."
  },
  "agent_type": "github",
  "timestamp": "2025-10-15T...",
  "metadata": {
    "command": "...",
    "output_length": 1234
  }
}
```

## 🔧 Troubleshooting

### Issue: Authentication Failed

**Solution**: Ensure environment variables are set:

```bash
# For GitHub
export GITHUB_TOKEN="your_github_token"

# For Jira
export JIRA_API_TOKEN="your_jira_token"
export JIRA_EMAIL="your_email"
export JIRA_CLOUD_ID="your_cloud_id"
```

### Issue: Module Not Found

**Solution**: The common module needs to be accessible:

```bash
# The runtime.py files use sys.path to add the common directory
# Make sure the path structure is correct
```

### Issue: Deployment Failed

**Solution**: Check CloudWatch logs:

```bash
aws logs tail /aws/bedrock-agentcore/runtimes/github-agent-XXXXX \
    --log-stream-name-prefix "2025/10/15/[runtime-logs]" --follow
```

## 🔗 Agent-to-Agent Communication

To enable A2A protocol between agents, add markers to the payload:

```python
# From orchestrator agent
payload = {
    "prompt": "list repositories",
    "_agent_call": True,  # Triggers agent mode
    "source_agent": "orchestrator"
}
```

This will return structured JSON instead of streaming text.

## 📝 Customization

### Adding New Agents

1. Copy the structure from github-agent or jira-agent
2. Update `runtime.py` to use the common response protocol
3. Implement agent-specific logic
4. Add to deployment script

### Modifying Response Format

Edit `/agents/common/response_protocol.py` to change:
- Response structure
- Mode detection logic
- Text extraction from events

## 🔒 Security Notes

- Agents run in isolated microVMs on AgentCore
- OAuth tokens are managed securely
- Session data persists for up to 8 hours
- Each user session is completely isolated

## 📚 Next Steps

1. **Deploy Orchestrator**: Create master agent to coordinate GitHub and Jira
2. **Add A2A Protocol**: Implement full A2A server for each agent
3. **Build Workflows**: Create complex multi-agent workflows
4. **Add Monitoring**: Set up CloudWatch dashboards for agent metrics

## 🆘 Getting Help

- Check CloudWatch logs for detailed error messages
- Review `.bedrock_agentcore.yaml` configuration
- Verify authentication credentials
- Test locally before deploying: `agentcore launch --local`

## 📖 Related Documentation

- [Strands Agents Documentation](https://strandsagents.com)
- [AgentCore Runtime Guide](https://docs.aws.amazon.com/bedrock/agentcore)
- [A2A Protocol Specification](https://a2aprotocol.ai)
