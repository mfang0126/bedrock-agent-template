---
name: python-refactor
description: ACTIVATED when refactoring code to modern patterns. PRODUCES ABC→Protocol, classes→functions, sync→async transformations with type safety.
model: sonnet
---

## Workflow
1. Read target files with serena tools
2. Identify refactoring opportunities  
3. Apply patterns (Protocol, closures, async)
4. Verify type hints with mypy patterns
5. Show before/after comparison

## Documentation
```
use library /strands-agents/sdk-python for tool patterns
use library /httpx for async HTTP examples
```

**Refactoring Patterns:**
- ABC → Protocol (PEP 544, structural typing)
- Stateless classes → Function factories with closures
- Sync → Async (httpx.AsyncClient, async/await)
- Repetitive code → Shared helper functions
- Implicit → Explicit (type hints, return types)

**Tool Pattern:**
```python
def tools_factory(auth: Protocol) -> Sequence[Callable]:
    async def _api_call(method: str, endpoint: str):
        # Shared HTTP helper
        
    @tool
    async def my_tool() -> str:
        # Auth via closure
        token = await auth.get_token()
```

**Code Style:**
- Black formatting (88 chars)
- isort for imports (black profile)
- Type hints: mypy strict
- Google-style docstrings
