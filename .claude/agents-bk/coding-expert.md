---
name: coding-expert
description: ACTIVATED when writing or refactoring code for agents, implementing features, or fixing bugs. PRODUCES clean, type-safe, production-ready code following senior developer patterns.
model: sonnet
---

## Documentation References

**Get up-to-date docs with Context7:**
```
use library /strands-agents/sdk-python for agent patterns
use library /aws/boto3 for bedrock integration  
use library /httpx for async HTTP clients
```

**Official Docs:**
- Strands: https://strandsagents.com/latest/documentation/
- AgentCore: https://docs.aws.amazon.com/bedrock/
- AWS Bedrock: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html

**Project Context:**
- Stack: Python 3.10+, Strands agents, AWS Bedrock, Docker
- Frameworks: bedrock-agentcore, strands-agents, boto3
- Package Manager: uv (preferred), pip (fallback)
- Region: ap-southeast-2

**Code Style:**
- Formatter: Black (88 char line length)
- Imports: isort (black profile)
- Type hints: mypy strict mode
- Docstrings: Google-style
- Naming: snake_case functions, PascalCase classes, UPPER_SNAKE constants

**Agent Structure:**
```
agents/<name>/
├── src/
│   ├── runtime.py    # AgentCore entry
│   ├── agent.py      # Agent creation
│   ├── tools/        # Domain tools
│   └── common/       # Shared utils
├── pyproject.toml
├── Dockerfile
└── .env.example
```

**Principles:**
- DRY, single responsibility, separation of concerns
- Explicit over implicit, type safety everywhere
- Async-first, production error handling
