# Claude Code Subagents - Complete Guide

## What Are Subagents?

Specialized AI assistants with:
- **Separate context windows** (no pollution)
- **Custom system prompts** (expert behavior)
- **Scoped tools** (security)
- **Action-oriented activation** (clear triggers)

## Our Subagents

### 1. coding-expert
**Activation:** Writing/refactoring code, implementing features, fixing bugs  
**Output:** Clean, type-safe, production-ready code  
**Tools:** All Serena tools (read, write, search, symbols)

**Usage:**
```
@coding-expert implement user authentication with JWT
@coding-expert refactor this function to be async
```

### 2. python-refactor
**Activation:** Modernizing Python code patterns  
**Output:** ABC→Protocol, classes→functions, sync→async  
**Focus:** Single-purpose refactoring

**Usage:**
```
@python-refactor convert GitHubAuth from ABC to Protocol
@python-refactor make all tools async with closures
```

### 3. import-debugger
**Activation:** ImportError, module path issues  
**Output:** Fixed imports, validation scripts, __init__.py exports  
**Specialization:** Python import system

**Usage:**
```
@import-debugger fix "cannot import GitHubAuth" error
@import-debugger create import validation script
```

### 4. docker-expert
**Activation:** Docker build failures, container issues  
**Output:** Optimized Dockerfiles, PYTHONPATH fixes  
**Expertise:** AgentCore deployment patterns

**Usage:**
```
@docker-expert optimize the Dockerfile for layer caching
@docker-expert fix PYTHONPATH import issues in container
```

### 5. agent-architect
**Activation:** Designing multi-agent systems, architecture review  
**Output:** Structure recommendations, orchestration patterns  
**Expertise:** Strands patterns, agents-as-tools

**Usage:**
```
@agent-architect review my orchestrator pattern
@agent-architect design a multi-agent workflow for CI/CD
```

## Documentation Integration

### Context7 - Get Up-to-Date Library Docs

**Format:** `/org/project` or `/org/project/version`

**Common Libraries:**
```
use library /strands-agents/sdk-python for agent patterns
use library /aws/boto3 for bedrock integration
use library /httpx for async HTTP
use library /pydantic/pydantic for models
use library /vercel/next.js/v14.0.0 for version-specific
```

**How it works:**
1. Agent calls `resolve-library-id` (libraryName)
2. Gets Context7 ID (e.g., `/strands-agents/sdk-python`)
3. Calls `get-library-docs` with ID and optional topic
4. Receives version-specific, accurate documentation

### Official Documentation Links

**Strands Agents:**
- Docs: https://strandsagents.com/latest/documentation/
- GitHub: https://github.com/strands-agents/sdk-python
- Quickstart: https://strandsagents.com/latest/documentation/docs/user-guide/quickstart/

**AWS AgentCore:**
- Docs: https://docs.aws.amazon.com/bedrock/
- Runtime: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-agent-runtime.html

**Context7:**
- Homepage: https://context7.com/
- Search: https://context7.com/search
- Add packages: https://context7.com/add-package

## Best Practices from Research

### 1. Single Responsibility
Each agent has ONE clear goal:
- ✅ `python-refactor` → refactoring only
- ❌ `general-helper` → does everything

### 2. Action-Oriented Descriptions
Use "ACTIVATED when X; PRODUCES Y" format:
```yaml
description: ACTIVATED when Docker build fails. PRODUCES optimized Dockerfiles.
```

### 3. Detailed System Prompts
Include:
- Workflow steps (1, 2, 3...)
- Documentation references
- Code examples
- Success criteria

### 4. Tool Scoping
Only grant necessary tools:
- Read-heavy: `python-refactor` (read, search, find_symbol)
- Write-heavy: `coding-expert` (all tools)
- Execution: `docker-expert` (+ execute_shell_command)

### 5. Context Efficiency
Subagents start clean, summarize results back:
- Main agent stays high-level
- Subagent does deep research
- Returns concise summary
- Prevents context pollution

## Workflow Patterns

### Sequential Pipeline
```
@python-refactor analyze current code
→ @coding-expert implement new pattern  
→ @import-debugger fix any import issues
→ @docker-expert verify container works
```

### Parallel Analysis
```
@agent-architect review architecture
& @import-debugger check imports  
& @docker-expert verify deployment
→ combine recommendations
```

### Chained Delegation
```
Main → @coding-expert (delegates to)
     → @python-refactor (refactors)
     → returns to @coding-expert  
     → returns to Main
```

## Project-Specific Context

All agents know:
- **Stack:** Python 3.10+, Strands, AWS Bedrock, Docker
- **Tools:** bedrock-agentcore, strands-agents, boto3, httpx
- **Patterns:** Protocol interfaces, function tools, closures
- **Style:** Black (88 chars), isort, mypy strict, Google docstrings

## Quick Reference

**Create new subagent:**
```bash
# Interactive
/agents

# Manual
touch .claude/agents/my-agent.md
```

**Invoke subagent:**
```bash
@my-agent do something
```

**Check available subagents:**
```bash
/agents
```

**Best activation phrases:**
- "Use the X subagent to Y"
- "@X do Y"
- "Have X analyze Y"

## Token Efficiency

**Cost consideration:**
- Each subagent = separate context
- 3 active subagents ≈ 3-4x tokens
- Use strategically for complex tasks
- Terminate when done

**Optimization:**
- Use subagents for research/analysis
- Return concise summaries
- Main agent stays focused
- Preserve context budget

## Version Control

```bash
# Commit subagents with your project
git add .claude/agents/
git commit -m "Add project-specific subagents"
```

**Team benefits:**
- Shared expertise
- Consistent patterns
- Faster onboarding
- Collaborative improvements

## Resources

- **Anthropic Best Practices:** https://www.anthropic.com/engineering/claude-code-best-practices
- **PubNub Guide:** https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/
- **Awesome Collection:** https://github.com/VoltAgent/awesome-claude-code-subagents
- **Context7 Tutorial:** https://dev.to/mehmetakar/context7-mcp-tutorial-3he2
