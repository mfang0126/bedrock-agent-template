# GitHub Agent Testing Strategy

## Command Patterns

**AWS/AgentCore commands** (require authentication):
```bash
authenticate --to=wealth-dev-au && uv run agentcore launch
authenticate --to=wealth-dev-au && uv run agentcore invoke '{"prompt": "..."}' --user-id "test"
```

**IMPORTANT**: `--user-id` parameter is REQUIRED for OAuth USER_FEDERATION flow to work.
Without it, the agent cannot trigger GitHub OAuth and will fail to access GitHub APIs.

**Local development** (no authentication):
```bash
uv run pytest tests/
uv run python -m agents.github_agent
```

## Poe Tasks

```bash
# Development
uv run poe sync              # Install dependencies
uv run poe sync-dev          # Install with dev extras

# Testing (requires authenticate --to=wealth-dev-au first)
uv run poe test-agent <path>  # Run integration test file

# Deployment (requires authenticate --to=wealth-dev-au first)
uv run poe deploy            # Launch to AgentCore runtime
uv run poe invoke <prompt>   # Test deployed agent
```

## Quality Gates

Before marking Wave complete:
1. `uv run pytest tests/` - all tests pass
2. `authenticate --to=wealth-dev-au && uv run poe deploy` - deployment succeeds
3. `uv run poe invoke` - at least 2 real invoke tests with new tools