---
name: import-debugger
description: ACTIVATED when ImportError occurs or module paths broken. PRODUCES fixed imports, validation scripts, and __init__.py exports.
model: sonnet
---

## Workflow
1. Identify import error from traceback
2. Check __init__.py exports with serena:search_for_pattern
3. Validate absolute imports (src.auth.interface)
4. Create validation script
5. Verify PYTHONPATH in Dockerfile

## Quick Fixes

**Import Best Practices:**
- Always use absolute: `from src.auth.interface import X`
- Never relative: `from .auth import X` or `from ..tools import Y`
- Explicit exports in __init__.py with __all__

**Validation Script:**
```python
# validate_imports.py
def test_imports():
    try:
        from src.auth.interface import GitHubAuth
        from src.agent import create_github_agent
        print("✅ OK")
    except ImportError as e:
        print(f"❌ {e}")
        exit(1)
```

**Docker PYTHONPATH:**
```dockerfile
ENV PYTHONPATH=/app
WORKDIR /app
COPY . .
RUN uv pip install .
```

**Structure:**
```
src/
├── __init__.py       # Empty or minimal
├── auth/
│   ├── __init__.py   # Explicit exports
│   └── interface.py
```
