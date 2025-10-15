# GitHub Agent Refactoring Plan

## Core Principles

1. **Protocols > Abstract Classes** (PEP 544)
2. **Functions > Classes** (when no state needed)
3. **Closures for encapsulation**
4. **Explicit over implicit**
5. **Async-first**
6. **Composition over inheritance**

## Current Architecture Issues

```python
# ❌ Current Problems
- ABC instead of Protocol
- Class-based tools (unnecessary overhead)
- Sync httpx.Client() not AsyncClient
- Repetitive auth checks in every tool
- Verbose error handling
```

## Target Architecture

### 1. Protocol-Based Interface
```python
# src/auth/interface.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class GitHubAuth(Protocol):
    async def get_token(self) -> str: ...
    def is_authenticated(self) -> bool: ...
```

### 2. Function-Based Tools with Closures
```python
# src/tools/repos.py
from collections.abc import Sequence
from typing import Callable

def github_repo_tools(auth: GitHubAuth) -> Sequence[Callable]:
    """Factory returns tools with auth in closure."""
    
    async def _api_call(method: str, endpoint: str, **kwargs) -> dict:
        """Shared async HTTP helper - DRY principle."""
        token = await auth.get_token()
        async with httpx.AsyncClient() as client:
            response = await getattr(client, method)(
                f"https://api.github.com{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
    
    @tool
    async def list_repos() -> str:
        """List repositories."""
        if not auth.is_authenticated():
            return "❌ Authentication required"
        try:
            data = await _api_call("get", "/user/repos")
            # Format response
        except httpx.HTTPStatusError as e:
            return f"❌ API error: {e.response.status_code}"
    
    @tool
    async def create_repo(name: str, description: str = "", private: bool = False) -> str:
        """Create repository."""
        # Implementation
    
    return [list_repos, create_repo]
```

### 3. Simplified Agent Factory
```python
# src/agent.py
def create_github_agent(auth: GitHubAuth) -> Agent:
    return Agent(
        model=BedrockModel(model_id=MODEL_ID, region_name=REGION),
        tools=[
            *github_repo_tools(auth),
            *github_issue_tools(auth),
            *github_pr_tools(auth),
        ],
        system_prompt="..."
    )
```

## Import Best Practices

### Absolute Imports Always
```python
# ✅ Use this
from src.auth.interface import GitHubAuth
from src.tools.repos import github_repo_tools

# ❌ Never this
from .auth import GitHubAuth
from ..tools import something
```

### Explicit __init__.py Exports
```python
# src/auth/__init__.py
from src.auth.interface import GitHubAuth
from src.auth.mock import MockGitHubAuth
from src.auth.agentcore import AgentCoreGitHubAuth

__all__ = ["GitHubAuth", "MockGitHubAuth", "AgentCoreGitHubAuth", "get_auth_provider"]
```

### Validation Script
```python
# validate_imports.py (project root)
def test_imports():
    try:
        from src.auth.interface import GitHubAuth
        from src.agent import create_github_agent
        from src.tools.repos import github_repo_tools
        print("✅ All imports OK")
    except ImportError as e:
        print(f"❌ {e}")
        exit(1)

if __name__ == "__main__":
    test_imports()
```

## Migration Steps

### Phase 1: Protocol Interface ✅ COMPLETED
- [x] Replace ABC with Protocol in `src/auth/interface.py`
- [x] Update existing implementations (no breaking changes)
- [x] Run tests

### Phase 2: Function Tools ✅ COMPLETED
- [x] Create `github_repo_tools()` factory
- [x] Create shared `_api_call()` helper
- [x] Implement all repo tools as functions
- [x] Repeat for issues and PRs
- [x] Convert httpx.Client() to AsyncClient

### Phase 3: Agent Integration ✅ COMPLETED
- [x] Update `create_github_agent()` to use new tools
- [x] Test locally with mock auth
- [x] All imports validated successfully

### Phase 4: Cleanup ✅ COMPLETED
- [x] Update auth/__init__.py for optional AgentCore import
- [x] Create validate_imports.py script
- [x] Optimize Dockerfile with PYTHONPATH
- [x] Update REFACTORING_PLAN.md documentation

## Benefits

| Metric | Before | After |
|--------|--------|-------|
| Code lines | ~500 | ~350 |
| Import errors | Common | Caught early |
| Testability | Good | Excellent |
| Maintainability | Medium | High |
| Pythonic | Fair | Excellent |

## Docker Import Fix

```dockerfile
# Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
WORKDIR /app

COPY . .

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

RUN uv pip install .

RUN useradd -m -u 1000 bedrock_agentcore && \
    chown -R bedrock_agentcore:bedrock_agentcore /app

USER bedrock_agentcore

CMD ["python", "-m", "src.runtime"]
```

## Key Patterns

### DRY with Shared Helper
```python
async def _api_call(method: str, endpoint: str, **kwargs):
    """Single point for all API calls."""
    # Auth, headers, error handling in one place
```

### Closure for Auth
```python
def tools_factory(auth: GitHubAuth):
    # Auth available to all tools via closure
    @tool
    async def my_tool():
        token = await auth.get_token()  # No self needed
```

### Type Safety
```python
from typing import Protocol, runtime_checkable
from collections.abc import Sequence, Callable

def tools_factory(auth: GitHubAuth) -> Sequence[Callable]:
    # Explicit types everywhere
```

## Testing Strategy

```python
# Test with mock
mock_auth = Mock(spec=GitHubAuth)
mock_auth.is_authenticated.return_value = True
mock_auth.get_token.return_value = "token"

tools = github_repo_tools(mock_auth)
# Test each tool directly
```

## Success Criteria

- ✅ All imports validated before Docker build
- ✅ 30% less code
- ✅ Async throughout
- ✅ No class overhead for stateless tools
- ✅ Clean separation: interface → implementation → tools → agent
- ✅ Easy to test (DI via closure)
