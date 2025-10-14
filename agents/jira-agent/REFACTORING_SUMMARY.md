# Jira Agent Refactoring Summary

**Date**: 2025-10-14
**Status**: ✅ Complete
**Goal**: Separate testable agent logic from AgentCore deployment wrapper

---

## What Changed

### Before (Tightly Coupled)
```
src/
├── runtime.py          # Mixed: AgentCore + Agent logic + OAuth
├── common/auth.py      # Global state, @requires_access_token decorator
└── tools/              # Direct dependency on global auth
    ├── tickets.py
    └── updates.py
```

**Problem**: Cannot test without deploying to AgentCore (2-5 minute cycle).

### After (Dependency Injection)
```
src/
├── runtime.py                  # Thin wrapper: AgentCore concerns only
├── agent.py                    # NEW: Pure agent factory function
├── auth/                       # NEW: Auth abstraction layer
│   ├── __init__.py            # Factory: get_auth_provider()
│   ├── interface.py           # Abstract JiraAuth interface
│   ├── mock.py                # Mock for local testing
│   └── agentcore.py           # Real OAuth for production
├── tools/                      # Refactored with dependency injection
│   ├── tickets.py             # JiraTicketTools class
│   └── updates.py             # JiraUpdateTools class
└── common/
    └── config.py              # Jira URL configuration

.env.local                      # NEW: Local environment config
.env.example                    # NEW: Example configuration
```

**Benefits**:
- Test locally with AgentCore in ~30 seconds (vs 2-5 minutes deployment)
- Mock authentication for rapid iteration without OAuth
- Clean separation of concerns with dependency injection
- Deploy only validates OAuth and real APIs

---

## Architecture Pattern

### 1. Auth Abstraction (Dependency Injection)

**Interface** (`src/auth/interface.py`):
```python
class JiraAuth(ABC):
    @abstractmethod
    async def get_token(self) -> str: ...

    @abstractmethod
    def is_authenticated(self) -> bool: ...

    @abstractmethod
    def get_jira_url(self) -> str: ...

    @abstractmethod
    def get_auth_headers(self) -> dict: ...
```

**Mock Implementation** (`src/auth/mock.py`):
```python
class MockJiraAuth(JiraAuth):
    async def get_token(self) -> str:
        return "mock_jira_token_for_local_testing"

    def get_jira_url(self) -> str:
        return get_jira_url()  # From config
```

**AgentCore Implementation** (`src/auth/agentcore.py`):
```python
class AgentCoreJiraAuth(JiraAuth):
    # Uses @requires_access_token decorator
    # Handles OAuth URL streaming
    # Fetches Atlassian cloud ID for API access
```

**Factory** (`src/auth/__init__.py`):
```python
def get_auth_provider(env: str) -> JiraAuth:
    if env == "local":
        return MockJiraAuth()
    else:
        return AgentCoreJiraAuth(oauth_url_callback)
```

### 2. Tool Classes with Injection

**Before**:
```python
@tool
async def fetch_jira_ticket(ticket_id: str) -> str:
    headers = get_jira_auth_headers()  # Global function
    jira_url = get_jira_url_cached()   # Global state
    # ...
```

**After**:
```python
class JiraTicketTools:
    def __init__(self, auth: JiraAuth):
        self.auth = auth

    @tool
    async def fetch_jira_ticket(self, ticket_id: str) -> str:
        headers = self.auth.get_auth_headers()  # Injected dependency
        jira_url = self.auth.get_jira_url()     # From auth provider
        # ...
```

### 3. Pure Agent Factory

**`src/agent.py`**:
```python
def create_jira_agent(auth: JiraAuth) -> Agent:
    """Create Jira agent with injected auth."""
    ticket_tools = JiraTicketTools(auth)
    update_tools = JiraUpdateTools(auth)

    return Agent(
        model=BedrockModel(...),
        tools=[
            ticket_tools.fetch_jira_ticket,
            ticket_tools.parse_ticket_requirements,
            update_tools.update_jira_status,
            update_tools.add_jira_comment,
            update_tools.link_github_issue,
        ]
    )
```

### 4. Thin Runtime Wrapper

**`src/runtime.py`**:
```python
@app.entrypoint
async def strands_agent_jira(payload):
    # Get environment-specific auth
    env = os.getenv("AGENT_ENV", "prod")
    auth = get_auth_provider(env, oauth_url_callback)

    # Create agent using factory
    agent = create_jira_agent(auth)

    # Handle OAuth URL streaming (AgentCore-specific)
    # Stream agent responses
    async for event in agent.stream_async(user_input):
        yield format_client_text(event)
```

---

## Usage Examples

### AgentCore Local Testing (Mock Auth)

```bash
# Set environment for mock
export AGENT_ENV=local

# Launch with AgentCore
agentcore launch --local

# Invoke (--user-id not strictly required for mock mode)
agentcore invoke --message "Get ticket details for PROJ-123"
```

### AgentCore with Real OAuth

```bash
# Set environment for real OAuth
export AGENT_ENV=dev

# Launch with AgentCore
agentcore launch --local

# Invoke (--user-id REQUIRED for OAuth)
agentcore invoke --user-id YOUR_USERNAME --message "Update PROJ-123 to In Progress"
```

**IMPORTANT:** The `--user-id` flag is **required** when using real OAuth (`AGENT_ENV=dev` or `AGENT_ENV=prod`). See `docs/OAuth-Testing-Guide.md` for details.

### Production Deployment

```bash
# Deploy to dev
AGENT_ENV=dev agentcore deploy --agent jira-dev

# Test with OAuth
agentcore invoke --agent jira-dev --user-id YOUR_USERNAME --message "List my tickets"

# Deploy to prod
AGENT_ENV=prod agentcore deploy --agent jira-prod

# Test production
agentcore invoke --agent jira-prod --user-id YOUR_USERNAME --message "Add comment to PROJ-123"
```

---

## Environment Configuration

### `.env.local` (Local Testing)
```bash
AGENT_ENV=local
LOG_LEVEL=DEBUG
JIRA_URL=https://your-company.atlassian.net
```

### `.env.dev` (Dev Deployment)
```bash
AGENT_ENV=dev
LOG_LEVEL=INFO
JIRA_URL=https://your-company.atlassian.net
# OAuth configured in AgentCore Identity
```

### `.env.prod` (Production)
```bash
AGENT_ENV=prod
LOG_LEVEL=INFO
JIRA_URL=https://your-company.atlassian.net
# OAuth configured in AgentCore Identity
```

---

## Testing Strategy

### Local Development Testing
- Agent structure validation via AgentCore local mode
- Mock authentication for rapid iteration
- Docker container import verification
- **Time**: ~30 seconds per build + test cycle

### Deployment Testing
- OAuth flow validation
- Real Jira API integration
- Atlassian cloud ID retrieval
- AgentCore Memory persistence
- **Time**: 2-5 minutes per deployment

---

## Migration Notes

### No Breaking Changes
- Existing deployed agents continue to work
- OAuth flow behavior unchanged
- AgentCore Memory integration preserved
- Response streaming maintained

### New Capabilities
- ✅ Local testing with AgentCore (30s vs 2-5min deployment)
- ✅ Mock authentication for rapid iteration
- ✅ Dependency injection enabling testability
- ✅ Clean architecture with separated concerns
- ✅ Environment-specific configuration
- ✅ Docker container properly configured

---

## Files Modified

### Created
- `src/auth/interface.py` - Auth abstraction
- `src/auth/mock.py` - Mock implementation
- `src/auth/agentcore.py` - OAuth implementation with cloud ID retrieval
- `src/auth/__init__.py` - Auth factory
- `src/agent.py` - Pure agent factory
- `.env.local` - Local environment
- `.env.example` - Example configuration

### Refactored
- `src/runtime.py` - Thin wrapper (OAuth streaming only)
- `src/tools/tickets.py` - JiraTicketTools class with DI
- `src/tools/updates.py` - JiraUpdateTools class with DI
- `src/tools/__init__.py` - Updated exports for tool classes

### Updated
- `Dockerfile` - Added `PYTHONPATH=/app` for proper module resolution in container

---

## Success Criteria

- [x] ✅ Can test agent with AgentCore local mode
- [x] ✅ Docker image builds successfully
- [x] ✅ All imports resolve correctly in container
- [x] ✅ Code is cleaner and more maintainable
- [x] ✅ Dependency injection pattern implemented

**Deployment Testing** (requires AWS access):
- [ ] OAuth flow still works in dev/prod
- [ ] Real Jira API integration works in dev/prod
- [ ] Atlassian cloud ID retrieval works
- [ ] AgentCore Memory persists across sessions

---

## Next Steps

### For This Agent
1. ✅ Test with AgentCore local: `AGENT_ENV=local agentcore launch --local` - **PASSED**
2. Deploy to dev: `AGENT_ENV=dev agentcore deploy`
3. Validate OAuth flow in dev environment
4. Test real Jira API integration

### For Other Agents
This pattern has been successfully applied to:
1. ✅ **GitHub Agent** - OAuth with GitHub API
2. ✅ **Jira Agent** - OAuth with Atlassian API

Apply same pattern to remaining agents:
1. **Planning Agent** (simplest - no OAuth)
2. **Coding Agent** (no OAuth)
3. **Orchestrator Agent** (uses Agents-as-Tools pattern)

---

## Jira-Specific Implementation Notes

### Atlassian OAuth Flow
The Jira agent uses Atlassian's OAuth 2.0 (3LO - Three-Legged OAuth) flow with additional cloud ID retrieval:

1. **OAuth Token**: Obtained via AgentCore Identity using `@requires_access_token`
2. **Cloud ID Retrieval**: After OAuth, fetch accessible resources to get Atlassian cloud ID
3. **API Access**: Use cloud ID in Jira API URLs: `https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/...`

### Tool Categories

**Ticket Operations** (`JiraTicketTools`):
- `fetch_jira_ticket` - Retrieve ticket details
- `parse_ticket_requirements` - Extract structured requirements

**Update Operations** (`JiraUpdateTools`):
- `update_jira_status` - Change ticket status/transitions
- `add_jira_comment` - Add comments to tickets
- `link_github_issue` - Link GitHub PRs/issues to Jira tickets

### Environment Variables
- `AGENT_ENV`: `local`, `dev`, or `prod`
- `JIRA_URL`: Your Atlassian instance URL (e.g., `https://your-company.atlassian.net`)
- `LOG_LEVEL`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `BEDROCK_MODEL_ID`: (Optional) Override default Claude 3.5 Sonnet model

---

## Resources

- **GitHub Agent Refactoring**: `agents/github-agent/REFACTORING_SUMMARY.md` (pattern reference)
- **Environment Example**: `.env.example`
- **Auth Factory**: `src/auth/__init__.py`
- **Agent Factory**: `src/agent.py`
- **OAuth Guide**: `docs/OAuth-Testing-Guide.md`
