# JIRA Agent

AWS Bedrock AgentCore agent for JIRA integration with OAuth 2.0 authentication.

[![Type Checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue)](https://mypy-lang.org/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-green)](https://pytest.org/)
[![Coverage: >85%](https://img.shields.io/badge/coverage-%3E85%25-brightgreen)](https://coverage.readthedocs.io/)

---

## Overview

The JIRA Agent enables seamless integration between AWS Bedrock AgentCore and Atlassian JIRA, providing AI-powered ticket management, status updates, and GitHub integration through natural language interactions.

### Key Features

✅ **OAuth 2.0 Authentication** - Secure Atlassian 3-Legged OAuth flow
✅ **Cloud ID Resolution** - Automatic Atlassian cloud ID retrieval
✅ **Ticket Operations** - Fetch and parse JIRA tickets
✅ **Update Operations** - Status changes, comments, GitHub links
✅ **Protocol-Based Architecture** - Modern Python patterns with structural subtyping
✅ **Async-First** - Full async support with httpx
✅ **Type-Safe** - mypy strict mode compliance
✅ **Comprehensive Testing** - 89 tests with >85% coverage
✅ **Local Testing** - Mock authentication for rapid development

---

## Quick Start

### Installation

```bash
# Navigate to agent directory
cd agents/jira-agent

# Install dependencies
uv pip install -e .

# Install with test dependencies
uv pip install -e ".[test]"
```

### Configuration

1. **Copy environment template**:
   ```bash
   cp .env.example .env.local
   ```

2. **Configure environment variables**:
   ```bash
   # .env.local
   AGENT_ENV=local  # local, dev, or prod
   LOG_LEVEL=INFO
   JIRA_URL=https://your-company.atlassian.net
   ```

### Local Testing (Mock Auth)

```bash
# Set environment for mock authentication
export AGENT_ENV=local
export JIRA_URL=https://your-company.atlassian.net

# Launch agent locally
agentcore launch --local

# Invoke agent (no --user-id needed for mock)
agentcore invoke --message "Get details for ticket PROJ-123"
```

### Production Deployment (OAuth)

```bash
# Deploy to AWS
export AGENT_ENV=prod
agentcore deploy --agent jira-prod

# Invoke with OAuth (--user-id REQUIRED)
agentcore invoke --agent jira-prod --user-id YOUR_USERNAME --message "Update PROJ-123 to In Progress"
```

---

## Capabilities

### Ticket Operations

#### Fetch JIRA Ticket
```
"Get details for ticket PROJ-123"
"Show me JIRA ticket ABC-456"
"What's the status of RE-789?"
```

**Returns**: Structured ticket information including:
- Title and description
- Current status and priority
- Assignee
- Sprint information
- Acceptance criteria
- Labels

#### Parse Requirements
```
"Parse requirements from ticket PROJ-123 for planning"
"Extract requirements from ABC-456"
```

**Returns**: Structured requirements formatted for Planning Agent integration.

### Update Operations

#### Update Status
```
"Update PROJ-123 to In Progress"
"Move ticket ABC-456 to Done"
"Change status of RE-789 to Code Review"
```

**Features**:
- Case-insensitive status matching
- Validates available transitions
- Helpful error messages with valid statuses

#### Add Comments
```
"Add comment to PROJ-123: Implementation complete"
"Comment on ABC-456 with GitHub PR link https://github.com/org/repo/pull/42"
```

**Features**:
- Atlassian Document Format (ADF)
- GitHub URL detection and formatting
- Rich text support

#### Link GitHub Issues/PRs
```
"Link GitHub PR https://github.com/org/repo/pull/42 to PROJ-123"
"Connect JIRA ticket ABC-456 to GitHub issue https://github.com/org/repo/issues/123"
```

**Features**:
- Automatic PR/issue detection
- Remote link creation
- Bidirectional linking

---

## Architecture

### Protocol-Based Design

The JIRA Agent uses modern Python Protocol patterns for flexible, type-safe authentication:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class JiraAuth(Protocol):
    """No inheritance required - structural subtyping."""
    async def get_token(self) -> str: ...
    def is_authenticated(self) -> bool: ...
    def get_jira_url(self) -> str: ...
    def get_auth_headers(self) -> dict: ...
```

**Benefits**:
- No rigid inheritance hierarchy
- Flexible authentication strategies
- Easy testing with mock implementations
- Type-safe with runtime validation

### Dependency Injection

Tools receive authentication through constructor injection:

```python
class JiraTicketTools:
    def __init__(self, auth: JiraAuth):
        self.auth = auth  # Any JiraAuth implementation

    @tool
    async def fetch_jira_ticket(self, ticket_id: str) -> Dict[str, Any]:
        headers = self.auth.get_auth_headers()  # Injected auth
        # ...
```

### Standardized Responses

All tools return structured dictionaries:

```python
# Success
{
    "success": True,
    "data": {
        "ticket_id": "PROJ-123",
        "title": "Implement feature X",
        "status": "In Progress",
        # ... more fields
    },
    "message": "Successfully fetched ticket PROJ-123"
}

# Failure
{
    "success": False,
    "data": {},
    "message": "❌ Ticket PROJ-123 not found"
}
```

---

## Testing

### Run Tests

```bash
# All unit tests
pytest

# With coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html

# View HTML coverage report
open htmlcov/index.html
```

### Test Categories

```bash
# Authentication tests (25 tests)
pytest tests/test_auth_*.py

# Tool tests (39 tests)
pytest tests/test_tools_*.py

# Agent tests (15 tests)
pytest tests/test_agent.py

# Skip integration tests (default)
pytest -m "not integration"

# Run integration tests (requires setup)
INTEGRATION_TESTS=true pytest -m integration
```

### Test Coverage

- **MockJiraAuth**: 100%
- **AgentCoreJiraAuth**: >85%
- **JiraTicketTools**: >90%
- **JiraUpdateTools**: >90%
- **create_jira_agent**: 100%
- **Overall**: >85%

### Type Checking

```bash
# Run mypy type checking
mypy src/

# Should output: Success: no issues found
```

---

## Development

### Project Structure

```
agents/jira-agent/
├── src/
│   ├── runtime.py              # AgentCore entrypoint
│   ├── agent.py                # Agent factory function
│   ├── auth/                   # Authentication
│   │   ├── interface.py        # Protocol interface
│   │   ├── mock.py             # Mock implementation
│   │   └── agentcore.py        # OAuth implementation
│   ├── tools/                  # Tool implementations
│   │   ├── tickets.py          # Ticket operations
│   │   └── updates.py          # Update operations
│   └── common/                 # Shared utilities
│       ├── auth.py             # OAuth helpers
│       ├── config.py           # Configuration
│       └── utils.py            # Utilities
├── tests/                      # Test suite (89 tests)
│   ├── conftest.py             # Shared fixtures
│   ├── test_auth_*.py          # Auth tests
│   ├── test_tools_*.py         # Tool tests
│   ├── test_agent.py           # Agent tests
│   └── integration/            # Integration tests
├── pyproject.toml              # Dependencies & config
├── pytest.ini                  # Test configuration
├── Dockerfile                  # Container build
├── .env.example                # Environment template
├── README.md                   # This file
├── REFACTORING_SUMMARY.md      # Architecture details
├── CLOUD_ID_IMPLEMENTATION.md  # OAuth setup guide
├── CHANGELOG.md                # Version history
└── TEST_SUITE_SUMMARY.md       # Test metrics
```

### Code Standards

- **Formatter**: Black (88 character line length)
- **Import Sorting**: isort (black profile)
- **Type Hints**: mypy strict mode
- **Docstrings**: Google style
- **Naming**:
  - Functions/variables: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`

### Adding New Tools

1. **Create tool method** in appropriate class:
   ```python
   class JiraTicketTools:
       @tool
       async def your_new_tool(self, param: str) -> Dict[str, Any]:
           """Tool description.

           Args:
               param: Parameter description

           Returns:
               Structured response dict
           """
           try:
               # Implementation
               return {
                   "success": True,
                   "data": {...},
                   "message": "Success message"
               }
           except Exception as e:
               return {
                   "success": False,
                   "data": {},
                   "message": f"Error: {e}"
               }
   ```

2. **Register tool** in `src/agent.py`:
   ```python
   tools=[
       # ... existing tools
       ticket_tools.your_new_tool,
   ]
   ```

3. **Write tests** in appropriate test file:
   ```python
   async def test_your_new_tool(ticket_tools):
       result = await ticket_tools.your_new_tool("test-param")
       assert result["success"] is True
       assert "expected_data" in result["data"]
   ```

---

## OAuth Setup

### Prerequisites

1. **Atlassian OAuth App** configured in Atlassian Developer Console
2. **AgentCore Identity** credential provider configured
3. **Scopes**: `read:jira-work`, `write:jira-work`, `offline_access`

### OAuth Flow

1. Agent requests token via `@requires_access_token` decorator
2. User receives authorization URL
3. User visits URL and authorizes access
4. AgentCore Identity stores token securely
5. Agent fetches Atlassian cloud ID
6. Tools use cloud-based API URLs

### Cloud ID Resolution

The agent automatically resolves your Atlassian cloud ID:

```
JIRA URL: https://your-company.atlassian.net
        ↓
Cloud ID: 366af8cd-d73d-4eca-826c-8ce96624d1e7
        ↓
API URL: https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/
```

This enables OAuth 2.0 tokens to work with JIRA's cloud-based API.

**See [CLOUD_ID_IMPLEMENTATION.md](./CLOUD_ID_IMPLEMENTATION.md) for detailed setup.**

---

## Environment Variables

### Required

- `JIRA_URL` - Your Atlassian JIRA URL (e.g., `https://your-company.atlassian.net`)

### Optional

- `AGENT_ENV` - Environment: `local`, `dev`, or `prod` (default: `prod`)
- `LOG_LEVEL` - Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` (default: `INFO`)
- `BEDROCK_MODEL_ID` - Model ID (default: `anthropic.claude-3-5-sonnet-20241022-v2:0`)
- `AWS_REGION` - AWS region (default: `ap-southeast-2`)

---

## Troubleshooting

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure PYTHONPATH is set (automatic in container):
```bash
export PYTHONPATH=/path/to/agents/jira-agent:$PYTHONPATH
```

### OAuth Issues

**Problem**: `401 Unauthorized` when calling JIRA API

**Solutions**:
1. Verify OAuth authorization completed successfully
2. Check cloud ID was retrieved (see logs)
3. Confirm scopes include `read:jira-work` and `write:jira-work`
4. Verify token hasn't expired (1 hour expiry)

**Problem**: `--user-id` not provided

**Solution**: OAuth mode requires user ID:
```bash
agentcore invoke --agent jira --user-id YOUR_USERNAME --message "..."
```

### Test Failures

**Problem**: Tests fail with HTTP errors

**Solution**: Ensure pytest-httpx is installed and fixtures are used:
```bash
uv pip install -e ".[test]"
pytest -v  # Verbose mode for details
```

### Type Checking Issues

**Problem**: mypy errors after code changes

**Solution**:
1. Ensure all functions have type hints
2. Check Protocol implementations match interface
3. Use `Dict[str, Any]` for structured responses
4. Run `mypy src/` to verify

---

## Performance

### Response Times
- **Ticket Fetch**: 200-500ms (JIRA API latency)
- **Status Update**: 300-700ms (includes transition lookup)
- **Comment Add**: 200-400ms
- **GitHub Link**: 300-600ms

### Optimization Tips
1. **Batch Operations**: Group multiple updates when possible
2. **Caching**: Consider caching ticket data for repeated access
3. **Parallel Calls**: Use async operations for independent tasks

---

## Security

### Authentication
- OAuth 2.0 tokens managed by AgentCore Identity
- Tokens encrypted at rest
- Automatic token refresh
- No tokens stored in agent code

### Best Practices
- Never commit `.env.local` or OAuth credentials
- Use `AGENT_ENV=local` only for testing
- Rotate OAuth apps periodically
- Monitor AgentCore logs for suspicious activity

---

## Contributing

### Development Workflow

1. **Create feature branch**
2. **Make changes** with tests
3. **Run quality checks**:
   ```bash
   pytest                    # Tests pass
   mypy src/                 # Type checking
   black src/ tests/         # Formatting
   isort src/ tests/         # Import sorting
   ```
4. **Update documentation**
5. **Submit for review**

### Pull Request Checklist

- [ ] Tests added for new functionality
- [ ] All tests passing
- [ ] Type checking passing (mypy)
- [ ] Code formatted (Black)
- [ ] Imports sorted (isort)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

---

## Documentation

- **[README.md](./README.md)** - This file (getting started)
- **[REFACTORING_SUMMARY.md](./REFACTORING_SUMMARY.md)** - Architecture and patterns
- **[CLOUD_ID_IMPLEMENTATION.md](./CLOUD_ID_IMPLEMENTATION.md)** - OAuth setup guide
- **[CHANGELOG.md](./CHANGELOG.md)** - Version history
- **[TEST_SUITE_SUMMARY.md](./TEST_SUITE_SUMMARY.md)** - Test metrics
- **[tests/README.md](./tests/README.md)** - Testing guide

---

## Related Agents

- **GitHub Agent** - GitHub integration with OAuth
- **Planning Agent** - Project planning and task breakdown
- **Coding Agent** - Code generation and modification
- **Orchestrator Agent** - Multi-agent workflow coordination

---

## Support

### Issues
Report issues through your team's issue tracking system.

### Questions
Contact the development team for questions about:
- Agent configuration
- OAuth setup
- Custom tool development
- Testing strategies

---

## License

Proprietary - Internal use only

---

## Acknowledgments

- **AWS Bedrock AgentCore** - Runtime framework
- **Strands SDK** - Agent development framework
- **Atlassian** - JIRA API and OAuth

---

**Version**: 1.0.0
**Last Updated**: 2024-10-15
**Status**: ✅ Production Ready
