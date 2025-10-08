# Suggested Commands

## Development Setup
```bash
# Install dependencies
uv sync --all-extras

# Copy environment template
cp .env.example .env
# Edit .env with your GitHub OAuth credentials

# Setup OAuth credential provider (one-time, before deployment)
uv run python setup_github_provider.py
```

## Local Testing (CLI)
```bash
# Test locally with CLI (not AgentCore)
uv run python -m agents.github_agent invoke "list my repositories"

# Alternative direct CLI command
uv run github-agent invoke "show my repos"
```

## Deployment to AgentCore
```bash
# Configure deployment
agentcore configure -e src/agents/github_agent/runtime.py --non-interactive

# Deploy to AWS (uses CodeBuild - no local Docker needed)
agentcore launch

# Check deployment status
agentcore status --agent github-agent
```

## Testing Deployed Agent
```bash
# Invoke with user ID (required for OAuth 3LO)
agentcore invoke '{"prompt": "list my repositories"}' --user-id "user-123"

# What happens:
# 1. First time: You'll get authorization URL in logs
# 2. Visit URL and authorize the GitHub app
# 3. AgentCore stores YOUR token (isolated per user)
# 4. Agent lists YOUR repositories
```

## Monitoring
```bash
# View CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtime/github-agent --follow
```

## Testing
```bash
# Run tests (when implemented)
pytest tests/

# Run specific test file
pytest tests/agents/test_github_agent.py
```

## Git Operations (macOS/Darwin)
```bash
# Standard git commands work as expected on macOS
git status
git branch
git checkout -b feature/new-agent
git add .
git commit -m "feat: add new agent"
git push origin feature/new-agent
```

## Package Management
```bash
# Sync dependencies
uv sync

# Sync with dev dependencies
uv sync --all-extras

# Add new dependency
uv add package-name

# Update dependencies
uv sync --upgrade
```
