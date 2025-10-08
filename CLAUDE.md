# Multi-Agent Platform Testing Strategy

## Agent Structure

```
src/agents/
  github_agent/runtime.py     # GitHub agent with OAuth 3LO
  planning_agent/runtime.py   # Planning agent (stateless)
```

## Command Patterns

**AWS/AgentCore commands** (require authentication):
```bash
# GitHub Agent (requires --user-id for OAuth)
aws_use mingfang && uv run agentcore launch -a github_agent
aws_use mingfang && uv run agentcore invoke -a github_agent '{"prompt": "list my repos"}' --user-id "test"

# Planning Agent
aws_use mingfang && uv run agentcore launch -a planning_agent
aws_use mingfang && uv run agentcore invoke -a planning_agent '{"prompt": "plan auth feature"}' --user-id "test"
```

**IMPORTANT**: `--user-id` parameter is REQUIRED for OAuth USER_FEDERATION flow (GitHub agent).
Without it, the agent cannot trigger GitHub OAuth and will fail to access GitHub APIs.

**Local development** (no authentication):
```bash
uv run pytest tests/
uv run python -m src.agents.github_agent.runtime
uv run python -m src.agents.planning_agent.runtime
```

## Poe Tasks

```bash
# Development
uv run poe sync              # Install dependencies
uv run poe sync-dev          # Install with dev extras

# Testing
uv run poe test-github       # Test GitHub agent
uv run poe test-planning     # Test Planning agent
uv run poe test-agent <path> # Run specific test file

# Deployment (requires aws_use mingfang first)
uv run poe deploy-github     # Deploy GitHub agent
uv run poe deploy-planning   # Deploy Planning agent

# Invocation
uv run poe invoke-github '{"prompt": "list repos"}' --user-id "test"
uv run poe invoke-planning '{"prompt": "plan feature"}' --user-id "test"
```

## Quality Gates

Before marking implementation complete:
1. `uv run pytest tests/` - all tests pass
2. `aws_use mingfang && uv run poe deploy-<agent>` - deployment succeeds
3. `uv run poe invoke-<agent>` - at least 2 real invoke tests with agent tools