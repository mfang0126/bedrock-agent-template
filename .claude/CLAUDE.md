# Agent Selection Guide - coding-agent-agentcore

This document defines when and which specialized agent to use for specific tasks in this multi-agent AWS Bedrock AgentCore project.

---

## Quick Decision Tree

```
Task Request → Identify Category → Select Agent

├─ Code Implementation → @coding-expert
├─ Python Modernization → @python-refactor
├─ Import/Module Errors → @import-debugger
├─ Docker/Container Issues → @docker-expert
├─ Agent Architecture → @agent-architect OR @strands-architect
└─ AWS CLI Operations → Reference documentation in docs/
```

---

## Agent Catalog

### 🔨 coding-expert
**When to Use:**
- Implementing new features or agents
- Writing production-ready code from scratch
- Fixing bugs in existing code
- Adding new tools to agents
- General code refactoring and improvements

**Trigger Keywords:**
- "implement", "create", "build", "add feature"
- "fix bug", "resolve error", "debug code"
- "write code", "develop", "create function/class"

**Examples:**
```
✅ "implement JWT authentication for the GitHub agent"
✅ "add a new tool for listing pull requests"
✅ "fix the OAuth token refresh logic"
✅ "create a new JIRA agent with basic operations"
```

**Output:** Clean, type-safe, production-ready code following project patterns

**Available Tools:** Full Serena toolset (read, write, search, symbols)

---

### 🔄 python-refactor
**When to Use:**
- Converting ABC classes to Protocol interfaces
- Modernizing sync code to async patterns
- Converting class-based tools to function tools with closures
- Refactoring for Strands best practices
- Single-purpose code modernization

**Trigger Keywords:**
- "refactor", "modernize", "convert to Protocol"
- "make async", "use closures", "function tools"
- "ABC to Protocol", "class to function"

**Examples:**
```
✅ "convert GitHubAuth from ABC to Protocol"
✅ "refactor GitHub tools to use function factories with closures"
✅ "make all API calls async with httpx"
✅ "modernize this class-based tool to a function"
```

**Output:** Modernized Python code following Strands patterns

**Available Tools:** Read-heavy (read, search, find_symbol)

---

### 🔍 import-debugger
**When to Use:**
- ImportError or ModuleNotFoundError
- Circular import issues
- Module path problems
- __init__.py configuration issues
- Creating import validation scripts

**Trigger Keywords:**
- "ImportError", "ModuleNotFoundError", "cannot import"
- "import issue", "module not found", "import fails"
- "circular import", "import path"

**Examples:**
```
✅ "fix ImportError: cannot import name 'GitHubAuth'"
✅ "resolve circular import between agent.py and tools"
✅ "create import validation script for pre-build checks"
✅ "fix __init__.py exports for src.common"
```

**Output:** Fixed imports, validation scripts, proper __init__.py structure

**Available Tools:** Full read/write access for import fixes

---

### 🐳 docker-expert
**When to Use:**
- Docker build failures
- Container runtime errors
- PYTHONPATH configuration issues
- Dockerfile optimization
- Multi-stage build problems
- AgentCore container deployment issues

**Trigger Keywords:**
- "Docker build", "container error", "Dockerfile"
- "PYTHONPATH", "module not found in container"
- "build fails", "deploy error", "ECR push"

**Examples:**
```
✅ "Docker build fails with PYTHONPATH error"
✅ "optimize Dockerfile for better layer caching"
✅ "fix module imports in container but works locally"
✅ "container can't find src.runtime module"
```

**Output:** Optimized Dockerfiles, fixed PYTHONPATH, deployment configs

**Available Tools:** Read/write + shell execution for builds

---

### 🏗️ agent-architect
**When to Use:**
- Designing multi-agent system architecture
- Reviewing orchestration patterns
- Planning agent interaction flows
- Evaluating agents-as-tools patterns
- Security reviews for tool access
- High-level architecture decisions

**Trigger Keywords:**
- "design architecture", "multi-agent system"
- "orchestration pattern", "agent workflow"
- "architecture review", "system design"
- "how should agents communicate"

**Examples:**
```
✅ "design the orchestrator agent to coordinate GitHub, JIRA, and Coding agents"
✅ "review my agents-as-tools implementation"
✅ "plan workflow for automated PR review with multiple agents"
✅ "what's the best pattern for agent-to-agent communication"
```

**Output:** Architecture recommendations, orchestration patterns, security constraints

**Available Documentation:**
- Bedrock AgentCore Control CLI (infrastructure)
- Bedrock AgentCore Runtime CLI (runtime ops)

---

### 🧵 strands-architect
**When to Use:**
- Implementing Strands framework patterns
- AgentCore deployment configuration
- Protocol-based interface design
- Function tools with closures
- Strands-specific refactoring
- Runtime.py and agent.py structure

**Trigger Keywords:**
- "Strands pattern", "AgentCore runtime"
- "Protocol interface", "tool design"
- "agent.py structure", "runtime.py"
- "Strands best practices"

**Examples:**
```
✅ "implement Strands agent with Protocol-based auth"
✅ "configure AgentCore runtime for the GitHub agent"
✅ "refactor tools to follow Strands function pattern"
✅ "review agent.py structure against Strands best practices"
```

**Output:** Strands-compliant code, AgentCore configurations, deployment patterns

**Available Documentation:**
- AgentCore Control CLI reference (in agents folder)
- Strands SDK documentation via Context7

---

## Documentation References

### When to Use Documentation vs. Agents

**Use Documentation Directly:**
- AWS CLI command syntax questions
- Looking up specific API parameters
- Understanding AWS service capabilities
- Reference for deployment workflows

**Use Agents with Documentation:**
- Implementing solutions based on docs
- Applying patterns to your specific code
- Troubleshooting based on doc guidance

### Available Documentation

#### In docs/ Directory
1. **bedrock-agentcore-control-reference.md**
   - Control plane operations (infrastructure)
   - Create/update agent runtimes
   - Gateway and credential provider management
   - Use for: Deployment, infrastructure setup

2. **bedrock-agentcore-runtime-reference.md**
   - Data plane operations (runtime)
   - Invoke agents, manage sessions
   - Memory and event management
   - Use for: Runtime operations, agent invocation

#### In .claude/agents/ Directory
3. **_bedrock-agentcore-control-reference.md**
   - Same as docs version but accessible to strands-architect
   - Includes `aws_use mingfang &&` prefix requirement

#### Access Pattern
```
Question about CLI syntax → Read documentation directly
Implementing based on docs → @agent-architect or @strands-architect with doc reference
```

---

## Context7 Library Integration

### When to Use Context7
Always use Context7 MCP for up-to-date library documentation:

```
use library /strands-agents/sdk-python for agent patterns
use library /aws/boto3 for Bedrock integration
use library /httpx for async HTTP
use library /pydantic/pydantic for data validation
```

### How It Works
1. Agent calls `resolve-library-id` with library name
2. Gets Context7 ID (e.g., `/strands-agents/sdk-python`)
3. Calls `get-library-docs` with topic (optional)
4. Receives current, accurate documentation

**Always prefer Context7 over:**
- Old documentation URLs
- Cached knowledge
- Assumed API patterns

---

## Multi-Agent Workflows

### Sequential Pipeline Pattern
```
User Request
  → @agent-architect (design approach)
  → @coding-expert (implement)
  → @import-debugger (fix imports if needed)
  → @docker-expert (verify container build)
  → Deploy
```

### Parallel Analysis Pattern
```
Complex Architecture Review
  → @agent-architect (system design) \
  → @strands-architect (Strands patterns) → Synthesize
  → @docker-expert (deployment review) /
```

### Refactoring Pipeline
```
Legacy Code
  → @python-refactor (modernize patterns)
  → @coding-expert (implement new features)
  → @import-debugger (validate imports)
  → @docker-expert (test containerization)
```

---

## Agent Decision Matrix

| Task Category | Primary Agent | Secondary Agent | Documentation |
|---------------|---------------|-----------------|---------------|
| New feature implementation | @coding-expert | @agent-architect | Context7 |
| Architecture design | @agent-architect | @strands-architect | Both CLI refs |
| Code modernization | @python-refactor | @coding-expert | Context7 |
| Import errors | @import-debugger | @coding-expert | N/A |
| Container issues | @docker-expert | N/A | Dockerfile patterns |
| Strands patterns | @strands-architect | @coding-expert | Context7 + CLI |
| Deployment config | @strands-architect | @docker-expert | Control CLI ref |
| Runtime operations | @agent-architect | @strands-architect | Runtime CLI ref |

---

## Project-Specific Context

All agents have access to this context:

**Technology Stack:**
- Language: Python 3.10+ (3.12+ for some agents)
- Framework: Strands Agents
- Runtime: AWS Bedrock AgentCore
- Model: Claude 3.5 Sonnet (anthropic.claude-3-5-sonnet-20241022-v2:0)
- Deployment: Lambda + ECR (ARM64)
- Region: ap-southeast-2 (Sydney)
- Package Manager: uv (primary), pip (fallback)

**Code Standards:**
- Formatter: Black (88 char line length)
- Import sorting: isort (black profile)
- Type hints: mypy strict mode
- Docstrings: Google-style
- Naming: snake_case functions, PascalCase classes, UPPER_SNAKE constants

**Architecture Patterns:**
- Protocol interfaces (not ABC)
- Function tools with closures (not classes)
- Async-first with httpx
- Separation: runtime.py → agent.py → tools/ → common/
- Response format: `{"success": bool, "data": {...}, "message": str}`

**Project Structure:**
```
agents/
├── github-agent/     ✅ Implemented (OAuth 3LO)
├── coding-agent/     🔨 In Development
├── planning-agent/   📋 Planned
├── jira-agent/       📋 Planned
└── orchestrator-agent/ 🎯 Planned
```

---

## Common Usage Patterns

### Starting New Agent
```
@agent-architect design the JIRA agent architecture
  → Review design
@strands-architect implement JIRA agent following design
  → Review implementation
@docker-expert create Dockerfile for JIRA agent
  → Test build
```

### Debugging Import Issues
```
@import-debugger fix "cannot import create_jira_agent" error
  → If it involves async refactoring:
@python-refactor modernize the import structure
```

### Architecture Review
```
@agent-architect review orchestrator pattern for multi-agent coordination
  → If Strands-specific concerns:
@strands-architect validate against Strands best practices
```

### Complete Feature Implementation
```
@coding-expert implement issue assignment tool for GitHub agent
  → If import errors occur:
@import-debugger fix import issues
  → Build and test:
@docker-expert build container and verify
```

---

## Anti-Patterns (Don't Do This)

❌ **Wrong:**
```
"@coding-expert design the architecture and implement it"
```
✅ **Right:**
```
"@agent-architect design the architecture"
[Review design]
"@coding-expert implement based on the architecture"
```

❌ **Wrong:**
```
"@docker-expert fix the import error"
```
✅ **Right:**
```
"@import-debugger fix the import error"
[If container-specific]
"@docker-expert adjust PYTHONPATH in Dockerfile"
```

❌ **Wrong:**
```
"@python-refactor implement new OAuth flow"
```
✅ **Right:**
```
"@coding-expert implement new OAuth flow"
[If modernization needed]
"@python-refactor convert to async pattern"
```

---

## Agent Activation Commands

### Explicit Invocation
```bash
@coding-expert implement user authentication
@agent-architect review my orchestrator design
@docker-expert optimize the Dockerfile
```

### Contextual Activation
When you say:
- "implement this feature" → @coding-expert automatically considered
- "Docker build is failing" → @docker-expert automatically considered
- "I'm getting ImportError" → @import-debugger automatically considered

### Multi-Agent Requests
```bash
# Sequential
"First, @agent-architect design the workflow, then @coding-expert implement it"

# Parallel (if supported)
"@agent-architect and @strands-architect review this design"
```

---

## Memory and Learning

### Agent Memories
All agents have access to project memories:
- `project_overview` - Multi-agent system architecture
- `agent_structure_and_patterns` - Standard agent patterns
- `tech_stack_and_dependencies` - Technology choices
- `code_style_and_conventions` - Coding standards

### Session Context
Agents maintain context within their invocation but don't pollute main context:
- Main agent stays high-level
- Subagent does deep work
- Returns concise summary
- Preserves token budget

---

## Best Practices

### 1. Choose the Right Granularity
- **Too broad:** "@coding-expert do everything for the new agent"
- **Too narrow:** "@coding-expert add a semicolon on line 42"
- **Just right:** "@coding-expert implement the OAuth token refresh logic"

### 2. Provide Context
```
# Bad
"@coding-expert fix the bug"

# Good
"@coding-expert fix the OAuth token refresh bug in agents/github-agent/src/common/auth/github.py:45 where tokens expire after 1 hour"
```

### 3. Use Sequential Delegation
```
1. @agent-architect design
2. Review and approve
3. @coding-expert implement
4. Review and test
5. @docker-expert containerize
```

### 4. Reference Documentation
```
"@strands-architect implement using patterns from @_bedrock-agentcore-control-reference.md"
```

### 5. Leverage Context7
```
"@coding-expert implement using latest patterns from /strands-agents/sdk-python"
```

---

## Token Efficiency

### Cost Considerations
- Each agent invocation = separate context window
- 3 active agents ≈ 3-4x token cost
- Use strategically for complex, well-defined tasks
- Terminate when task is complete

### Optimization Strategies
1. **Use agents for deep work:** Research, analysis, implementation
2. **Return concise summaries:** Not full file dumps
3. **Keep main agent coordinating:** Don't let agents delegate to agents
4. **Clear exit criteria:** Know when agent is done

---

## Troubleshooting

### "Agent didn't respond"
- Check activation keywords match agent description
- Verify agent file exists in `.claude/agents/`
- Try explicit `@agent-name` syntax

### "Wrong agent was used"
- Be more explicit with `@agent-name` prefix
- Provide clearer task description
- Check decision tree above

### "Agent lacks context"
- Reference specific files or documentation
- Provide error messages or logs
- Include relevant code snippets

### "Too many token costs"
- Use agents selectively for complex tasks
- Return summaries, not full outputs
- Consider combining related tasks

---

## Version Control

```bash
# Commit agents with your project
git add .claude/
git commit -m "Update agent configurations and documentation"

# Team benefits:
# - Shared expertise patterns
# - Consistent code quality
# - Faster onboarding
# - Collaborative improvements
```

---

## Quick Reference Card

| I need to... | Use this agent | Example |
|-------------|----------------|---------|
| Write new code | @coding-expert | "implement JWT auth" |
| Modernize Python | @python-refactor | "convert to Protocol" |
| Fix imports | @import-debugger | "fix ImportError" |
| Fix Docker | @docker-expert | "fix build failure" |
| Design system | @agent-architect | "design orchestrator" |
| Strands patterns | @strands-architect | "implement runtime" |
| AWS CLI syntax | Documentation | Read CLI reference |
| Get library docs | Context7 | `use library /strands-agents/sdk-python` |

---

## Resources

**Project Documentation:**
- `docs/bedrock-agentcore-control-reference.md` - Infrastructure CLI
- `docs/bedrock-agentcore-runtime-reference.md` - Runtime CLI
- `.claude/agents/README.md` - Agent usage guide
- `.claude/agents/_bedrock-agentcore-control-reference.md` - CLI for agents

**External Resources:**
- Strands Docs: https://strandsagents.com/latest/documentation/
- AWS AgentCore: https://docs.aws.amazon.com/bedrock/
- Context7: https://context7.com/

**Agent Best Practices:**
- Anthropic Guide: https://www.anthropic.com/engineering/claude-code-best-practices
- PubNub Guide: https://www.pubnub.com/blog/best-practices-for-claude-code-sub-agents/

---

## Updates and Maintenance

**Last Updated:** 2024-10-15

**Changelog:**
- Added bedrock-agentcore CLI documentation references
- Defined clear agent selection criteria
- Established multi-agent workflow patterns
- Integrated Context7 MCP documentation

**To Update:**
1. Add new agents to Agent Catalog section
2. Update Decision Matrix
3. Add examples to Common Usage Patterns
4. Update Quick Reference Card
5. Test with real tasks and refine

---

**Remember:** The goal is to use the right specialist for each task, maintain clean separation of concerns, and deliver production-quality multi-agent systems efficiently.
