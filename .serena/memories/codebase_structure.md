# Codebase Structure

## Directory Layout
```
app/
├── src/
│   ├── agents/
│   │   └── github_agent/
│   │       ├── runtime.py          # BedrockAgentCoreApp entrypoint
│   │       ├── agent.py            # Strands agent configuration
│   │       └── __main__.py         # CLI for local testing
│   ├── tools/
│   │   └── github/
│   │       ├── repos.py            # Repository operations (@tool)
│   │       └── issues.py           # Issue operations (@tool)
│   └── common/
│       ├── auth/
│       │   ├── github.py           # @requires_access_token decorator
│       │   └── credential_provider.py  # Provider management
│       ├── clients/
│       └── config/
│           └── config.py           # Env vars + config management
├── docs/
├── setup_github_provider.py       # One-time OAuth provider setup
├── pyproject.toml                  # Dependencies + project config
├── Dockerfile                      # ARM64 container for AgentCore
├── .env.example                    # Credential template
├── .gitignore
└── README.md
```

## Key File Purposes

### Runtime Entry Points
- **runtime.py**: Production entrypoint for AgentCore deployment
  - Exposes `strands_agent_github` function decorated with `@app.entrypoint`
  - Configures Strands Agent with model and tools
  - Handles payload processing from AgentCore Runtime

- **__main__.py**: CLI for local development/testing (not used in production)

### Tools Layer
- **tools/github/repos.py**: Repository management tools
  - Each function decorated with `@tool` from Strands
  - Uses `github_access_token` global from auth layer
  - Makes direct httpx API calls to GitHub

- **tools/github/issues.py**: Issue management tools
  - Same pattern as repos.py

### Authentication Layer
- **common/auth/github.py**: OAuth token management
  - `@requires_access_token` decorator for AgentCore Identity integration
  - Device Flow implementation for local testing
  - Global `github_access_token` variable accessed by tools

- **common/auth/credential_provider.py**: 
  - Setup/management of OAuth credential providers
  - Used by setup_github_provider.py script

### Configuration
- **common/config/config.py**: Environment-aware config management
  - Local: reads from .env file
  - Production: reads from AWS Secrets Manager (future)

## Design Patterns
1. **Global Token Pattern**: `github_access_token` set by auth decorator, accessed by tools
2. **Tool Decorator Pattern**: All tools use `@tool` from Strands for auto-registration
3. **Dual-Mode Design**: Same tools work in local CLI and AgentCore Runtime
4. **Credential Provider Setup**: One-time setup script before deployment
