# Example Workflows - Real-World Usage

## Workflow 1: Refactor GitHub Agent to Modern Patterns

**Goal:** Convert class-based tools to function-based with Protocol interface

**Steps:**
```bash
# 1. Architecture review
@agent-architect analyze agents/github-agent/src structure and recommend refactoring approach

# 2. Update interface  
@python-refactor convert src/auth/interface.py from ABC to Protocol

# 3. Convert tools
@python-refactor convert src/tools/repos.py from GitHubRepoTools class to github_repo_tools() factory function with closures

# 4. Fix any imports
@import-debugger validate all imports and create validation script

# 5. Test in Docker
@docker-expert verify Dockerfile works with new structure
```

**Expected Output:**
- Protocol-based GitHubAuth interface
- Function factories returning tool lists
- Closures for auth encapsulation
- Import validation script
- Working Docker build

## Workflow 2: Fix Jira Agent Import Error

**Goal:** Resolve "cannot import JiraAuth" in Docker

**Steps:**
```bash
# 1. Diagnose
@import-debugger analyze the ImportError traceback and identify root cause

# 2. Fix structure
@import-debugger fix src/auth/__init__.py exports and ensure absolute imports

# 3. Create validator
@import-debugger create validate_imports.py script

# 4. Update Dockerfile
@docker-expert ensure PYTHONPATH=/app and verify module resolution

# 5. Test
Run: python validate_imports.py
Build: docker build -t jira-agent .
```

**Expected Output:**
- Fixed __init__.py with __all__ exports
- Absolute imports throughout (from src.auth.interface import)
- Validation script that passes
- Working Docker build

## Workflow 3: Create New Orchestrator Agent

**Goal:** Build planning agent that delegates to GitHub and Jira agents

**Steps:**
```bash
# 1. Design architecture
@agent-architect design an orchestrator pattern that coordinates github-agent and jira-agent using agents-as-tools pattern. Use context7 for Strands patterns: use library /strands-agents/sdk-python

# 2. Implement structure
@coding-expert create agents/orchestrator-agent/ with:
- src/agent.py (factory function)
- src/runtime.py (AgentCore entry)
- src/tools/delegation.py (@tool wrappers for sub-agents)

# 3. Add tool wrappers
@coding-expert implement github_operations() and jira_operations() tools that delegate to specialized agents

# 4. Test integration
@docker-expert create Dockerfile and test local deployment

# 5. Validate
@import-debugger ensure all imports work correctly
```

**Expected Output:**
- Orchestrator agent structure
- @tool wrappers for delegation
- AgentCore-compatible runtime
- Working multi-agent coordination

## Workflow 4: Add Security Constraints to Terminal Tool

**Goal:** Implement command whitelist for safe terminal execution

**Steps:**
```bash
# 1. Review security
@agent-architect review terminal tool security and recommend whitelist approach. Reference Strands patterns: use library /strands-agents/sdk-python

# 2. Implement whitelist
@coding-expert add terminal_operations() tool with:
- Command validation against whitelist
- Safe command patterns (npm test, git status)
- Rejection of dangerous commands (rm -rf, sudo)

# 3. Add error handling
@coding-expert implement clear error messages for blocked commands

# 4. Document
@coding-expert add docstrings explaining security constraints
```

**Expected Output:**
- Whitelisted terminal tool
- Command validation logic
- Security documentation
- Safe execution patterns

## Workflow 5: Optimize Docker Build Performance

**Goal:** Reduce build time and image size

**Steps:**
```bash
# 1. Analyze current Dockerfile
@docker-expert analyze agents/github-agent/Dockerfile and identify optimization opportunities

# 2. Apply optimizations
@docker-expert implement:
- Layer caching (COPY requirements first)
- Multi-stage build if needed
- .dockerignore improvements
- Single RUN commands

# 3. Verify
@docker-expert test build time before/after
@docker-expert check image size before/after

# 4. Document
@coding-expert add comments explaining optimization choices
```

**Expected Output:**
- Optimized Dockerfile
- Reduced build time
- Smaller image size
- Documentation

## Workflow 6: Implement New Feature End-to-End

**Goal:** Add GitHub PR review capability

**Steps:**
```bash
# 1. Plan
"think hard about implementing GitHub PR review capability"
@agent-architect design the feature structure

# 2. Get docs
use library /strands-agents/sdk-python for tool patterns

# 3. Implement tools
@coding-expert create src/tools/pull_requests.py with:
- review_pull_request() tool
- GitHub API integration
- Comment formatting

# 4. Refactor if needed
@python-refactor ensure async patterns and type hints

# 5. Integration
@coding-expert add tool to agent.py

# 6. Test
@docker-expert verify Docker build
@import-debugger validate imports

# 7. Commit
git add .
git commit -m "feat: add PR review capability"
```

**Expected Output:**
- New PR review tool
- Integrated with agent
- Type-safe, async implementation
- Tested and deployed

## Workflow 7: Debug Production Issue

**Goal:** Agent failing with "Authentication required" error

**Steps:**
```bash
# 1. Diagnose
@coding-expert read the error logs and identify the authentication flow

# 2. Check auth implementation
@coding-expert analyze src/auth/agentcore.py OAuth flow

# 3. Fix issue
@coding-expert implement proper token refresh or error handling

# 4. Add logging
@coding-expert add debug logs for OAuth flow

# 5. Test locally
@docker-expert test with agentcore launch --local

# 6. Deploy
@docker-expert verify Docker build for production
```

## Quick Commands for Common Tasks

### Get Documentation
```bash
# Strands agent patterns
use library /strands-agents/sdk-python for agents-as-tools examples

# AWS Bedrock
use library /aws/boto3 for bedrock-agent-runtime

# HTTP clients
use library /httpx for async HTTP examples

# Type validation
use library /pydantic/pydantic for model examples
```

### Debug Imports
```bash
@import-debugger fix import errors in agents/github-agent
@import-debugger create validation script for all agents
```

### Refactor Code
```bash
@python-refactor convert src/tools to function-based patterns
@python-refactor make all API calls async with httpx.AsyncClient
```

### Review Architecture
```bash
@agent-architect review the orchestrator pattern
@agent-architect design security constraints for tools
```

### Fix Docker Issues
```bash
@docker-expert optimize Dockerfile layer caching
@docker-expert fix PYTHONPATH import issues
```

## Pro Tips

### 1. Chain Subagents
Let subagents call each other:
```
@agent-architect (designs) → @coding-expert (implements) → @python-refactor (modernizes)
```

### 2. Use Context7 Proactively
Add to your workflow:
```
use library /strands-agents/sdk-python
[then proceed with implementation]
```

### 3. Validate Early
Always run validation before committing:
```bash
@import-debugger create and run validation script
@docker-expert test build
```

### 4. Document Decisions
Have subagents explain:
```
@agent-architect explain why you chose this pattern
@python-refactor document the refactoring rationale
```

### 5. Iterate with Extended Thinking
For complex problems:
```
think harder about [problem]
@agent-architect review approach
[implement based on analysis]
```

## Troubleshooting

### Subagent Not Activating
- Check description is action-oriented
- Use explicit invocation: `@subagent-name`
- Verify .claude/agents/*.md exists

### Import Errors Persist
```bash
@import-debugger analyze complete import chain
@import-debugger check __init__.py exports
@docker-expert verify PYTHONPATH in container
```

### Docker Build Fails
```bash
@docker-expert read error logs
@docker-expert compare against standard template
@docker-expert test minimal Dockerfile first
```

### Context Getting Crowded
- Use subagents for deep research
- They return summaries, not full context
- Terminate subagents when done
- Start fresh conversation if needed

## Success Metrics

**You're using subagents well when:**
- ✅ Main conversation stays high-level
- ✅ Subagents handle specialized tasks
- ✅ Clear handoffs between agents
- ✅ Consistent patterns across codebase
- ✅ Fast iteration cycles
- ✅ Less context pollution
