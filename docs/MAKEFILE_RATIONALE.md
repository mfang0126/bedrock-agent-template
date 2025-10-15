# Why We Chose Makefile Over pyproject.toml

## Decision: Makefile ✅

For this project, we chose **Makefile** over **pyproject.toml scripts**.

## Reasoning

### Project Context
- ✅ No root-level `pyproject.toml` (each agent has its own)
- ✅ Existing bash scripts in `scripts/` folder
- ✅ Cross-agent coordination needed
- ✅ Deployment tasks are shell-based
- ✅ Multi-language potential (Python + bash + future)

### Comparison

| Aspect | Makefile | pyproject.toml |
|--------|----------|----------------|
| No root config needed | ✅ Yes | ❌ Need to create one |
| Shell integration | ✅ Native | ⚠️ Limited |
| Cross-agent ops | ✅ Easy | ⚠️ Complex |
| Deployment automation | ✅ Perfect | ❌ Awkward |
| Learning curve | ✅ Universal | ⚠️ Python-only |
| Dynamic arguments | ✅ Easy | ⚠️ Harder |

## Implementation

### What We Built
```bash
# Simple commands
make test-coding        # Test locally
make deploy            # Deploy to AWS
make clean             # Clean up
make help              # Show all commands
```

### Makefile Benefits
1. **No new dependencies** - `make` is standard
2. **Shell-native** - Perfect for bash scripts
3. **Cross-language** - Can add Go, Rust, etc later
4. **Clear syntax** - Easy to read and modify
5. **Universal** - Everyone knows `make`

## Alternative: pyproject.toml

Would require:
```toml
[project]
name = "coding-agent-agentcore"
version = "0.1.0"

[tool.uv.scripts]
test-coding = "python scripts/test_coding_local.py 'what can you do'"
```

**Problems:**
- Creates root pyproject.toml just for scripts
- Can't easily wrap bash deployment scripts
- Less flexible for dynamic arguments
- Python-specific (limits future options)

## When pyproject.toml Would Be Better

Use `pyproject.toml` if:
- Root-level pyproject.toml already exists
- Pure Python project (no bash)
- All operations are Python commands
- Using Poetry/PDM ecosystem
- Python-native workflow required

## Examples

### Makefile Projects
- Django, Kubernetes, Redis, Linux kernel
- Multi-language, deployment-heavy

### pyproject.toml Projects
- FastAPI, Pydantic, Black, Ruff
- Pure Python, library-focused

## Result

**Commands available:**
```bash
make help              # Show all commands
make test-all          # Test all agents locally
make test-coding       # Test Coding agent
make invoke-coding     # Test deployed agent
make setup             # Setup AWS resources
make deploy            # Deploy all agents
make status            # Show agent status
make clean             # Clean temporary files
```

**Benefits achieved:**
- ✅ Simple: `make test-coding` vs `uv run scripts/test_coding_local.py`
- ✅ Flexible: Can add deployment, testing, cleanup tasks
- ✅ Standard: No learning curve for developers
- ✅ Universal: Works with any language/tool

---

**Decision Date:** 2025-10-15
**Status:** ✅ Implemented
**Files Modified:** `Makefile`, `README.md`, `TESTING.md`
