# Strands Native Orchestration Analysis

**Date**: 2025-10-14
**Purpose**: Compare custom workflow implementation vs Strands native agents-as-tools pattern
**Conclusion**: ✅ Use Strands native pattern - simpler, more powerful, already available

---

## Key Finding: Strands Has Native Agents-as-Tools Pattern

You were right to question the custom `WorkflowStep` dataclass! Strands framework has a built-in **agents-as-tools pattern** that makes complex orchestration much simpler.

---

## Strands Native Approach

### Pattern: Agents as Tools

**Core Concept**: Wrap specialized agents as `@tool` decorated functions that the orchestrator agent can call.

### Implementation Example

```python
from strands import Agent, tool
from strands_tools import calculator

# 1. Create specialized agents as tools
@tool
def github_operations(query: str) -> str:
    """Execute GitHub operations like creating issues, PRs, listing repos."""
    try:
        print("🐙 Routing to GitHub Agent")

        # Create GitHub agent with its tools
        auth = get_auth_provider("dev", oauth_callback)
        github_agent = create_github_agent(auth)

        # Let GitHub agent handle the request
        response = github_agent(query)
        return response

    except Exception as e:
        return f"Error in GitHub operations: {str(e)}"

@tool
def jira_operations(query: str) -> str:
    """Execute Jira operations like creating tickets, updating sprints."""
    try:
        print("📋 Routing to Jira Agent")

        # Create Jira agent with its tools
        auth = get_auth_provider("dev", oauth_callback)
        jira_agent = create_jira_agent(auth)

        response = jira_agent(query)
        return response

    except Exception as e:
        return f"Error in Jira operations: {str(e)}"

@tool
def coding_operations(query: str) -> str:
    """Execute coding operations like dependency audits, testing, code execution."""
    try:
        print("💻 Routing to Coding Agent")

        coding_agent = create_coding_agent()
        response = coding_agent(query)
        return response

    except Exception as e:
        return f"Error in coding operations: {str(e)}"

@tool
def planning_operations(query: str) -> str:
    """Break down complex tasks into implementation plans."""
    try:
        print("📋 Routing to Planning Agent")

        planning_agent = create_planning_agent()
        response = planning_agent(query)
        return response

    except Exception as e:
        return f"Error in planning operations: {str(e)}"

# 2. Create orchestrator with agents-as-tools
orchestrator = Agent(
    model=BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
    system_prompt="""You are the Master Orchestrator Agent.

You coordinate between specialized agents to accomplish complex tasks:
• github_operations: GitHub issues, PRs, commits, repositories
• jira_operations: Jira tickets, sprints, project tracking
• coding_operations: Code execution, dependency audits, testing
• planning_operations: Task breakdown and implementation planning

**Your Strategy**:
1. Analyze the user's request
2. Determine which agent(s) can help
3. Call the appropriate agent tools
4. Coordinate multi-step workflows when needed
5. Synthesize results into clear responses

**Multi-step Workflows**:
- You can call multiple agents in sequence
- Pass results from one agent to another
- Make decisions based on agent responses
- Handle errors gracefully

Always explain which agents you're using and why.""",
    tools=[
        github_operations,
        jira_operations,
        coding_operations,
        planning_operations
    ]
)

# 3. Use the orchestrator
response = orchestrator("Check dependencies for my project and create a GitHub issue if there are vulnerabilities")
```

---

## Comparison: Custom vs Native

### Custom WorkflowStep Approach (What I Proposed)

```python
@dataclass
class WorkflowStep:
    step: int
    agent: str
    action: str
    params: Dict[str, Any]
    depends_on: List[int] = None
    success_criteria: Optional[str] = None

@dataclass
class Workflow:
    workflow_name: str
    steps: List[WorkflowStep]

class WorkflowExecutor:
    def __init__(self, sub_agents: Dict[str, Agent]):
        self.sub_agents = sub_agents
        self.step_results = {}

    async def execute_workflow(self, workflow: Workflow) -> Dict[str, Any]:
        # Custom execution logic
        # Manual dependency tracking
        # Manual error handling
        # Manual result passing
```

**Problems**:
- ❌ Reinventing the wheel - Strands already has this
- ❌ More code to maintain and test
- ❌ Less flexible than LLM-driven orchestration
- ❌ Requires explicit workflow definition
- ❌ Doesn't leverage model reasoning capabilities
- ❌ Manual dependency management

### Strands Native Approach (What You Suggested)

```python
@tool
def github_operations(query: str) -> str:
    auth = get_auth_provider("dev", oauth_callback)
    github_agent = create_github_agent(auth)
    return github_agent(query)

orchestrator = Agent(
    tools=[github_operations, jira_operations, ...],
    system_prompt="Coordinate specialized agents..."
)
```

**Benefits**:
- ✅ Uses Strands' built-in agents-as-tools pattern
- ✅ Simpler implementation (fewer lines of code)
- ✅ LLM decides orchestration strategy dynamically
- ✅ Automatic multi-step coordination
- ✅ Natural error handling
- ✅ Framework-supported pattern
- ✅ Model can reason about which agents to call
- ✅ No manual workflow definition needed

---

## Why Strands Native is Better

### 1. Model-Driven Orchestration

**Strands Philosophy**: Let the LLM decide the workflow, not hardcoded logic.

Instead of:
```python
# Hardcoded workflow
steps = [
    WorkflowStep(1, "github", "create_issue", {...}),
    WorkflowStep(2, "coding", "run_audit", {...}, depends_on=[1]),
    WorkflowStep(3, "jira", "update_sprint", {...}, depends_on=[2])
]
```

The LLM decides:
```
User: "Check dependencies and track the work"

Orchestrator thinks:
1. First, I'll use coding_operations to run dependency audit
2. If vulnerabilities found, use github_operations to create issue
3. Then use jira_operations to track in sprint
4. Synthesize results for user
```

### 2. Automatic Multi-Step Coordination

The orchestrator can call tools in sequence automatically:

```python
# User request
"Check dependencies for /path/to/project and create GitHub issue if vulnerabilities found"

# Orchestrator automatically:
# 1. Calls coding_operations("run dependency audit for /path/to/project")
# 2. Analyzes results
# 3. Calls github_operations("create issue for dependency vulnerabilities: [details]")
# 4. Returns synthesized response
```

No workflow definition needed!

### 3. Dynamic Decision Making

```python
# Orchestrator can adapt based on results
result = coding_operations("run npm audit")

if "vulnerabilities found" in result:
    # LLM decides to create GitHub issue
    github_operations("create issue with severity: high")
else:
    # LLM decides just to inform user
    return "No vulnerabilities found"
```

### 4. Natural Error Recovery

```python
@tool
def github_operations(query: str) -> str:
    try:
        # Execute GitHub operations
        return result
    except Exception as e:
        # Error becomes tool output
        return f"Error: {str(e)}"

# Orchestrator sees the error and can:
# - Try alternative approach
# - Inform user
# - Use different agent
```

---

## Recommended Implementation

### Phase 1: Refactor Orchestrator to Agents-as-Tools

**File**: `agents/orchestrator-agent/src/runtime.py`

```python
"""
Master Orchestrator Agent Runtime - Using Strands Native Agents-as-Tools
"""

from strands import Agent, tool
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp

# Import agent factories
from agents.github_agent.src.agent import create_github_agent
from agents.jira_agent.src.agent import create_jira_agent
from agents.coding_agent.src.agent import create_coding_agent
from agents.planning_agent.src.agent import create_planning_agent

# Import auth
from agents.github_agent.src.auth import get_auth_provider
from agents.jira_agent.src.auth import get_auth_provider as get_jira_auth

app = BedrockAgentCoreApp()

# OAuth callback for streaming URLs
def oauth_url_callback(url: str):
    """Stream OAuth URL to user"""
    # Implementation from current runtime
    pass

# Create specialized agents as tools
@tool
def github_operations(query: str) -> str:
    """Execute GitHub operations: create/list repos, issues, PRs, comments."""
    try:
        print("🐙 Routing to GitHub Agent")
        auth = get_auth_provider("dev", oauth_url_callback)
        github_agent = create_github_agent(auth)
        response = github_agent(query)
        return response.message if hasattr(response, 'message') else str(response)
    except Exception as e:
        return f"GitHub error: {str(e)}"

@tool
def jira_operations(query: str) -> str:
    """Execute Jira operations: create/update tickets, manage sprints."""
    try:
        print("📋 Routing to Jira Agent")
        auth = get_jira_auth("dev", oauth_url_callback)
        jira_agent = create_jira_agent(auth)
        response = jira_agent(query)
        return response.message if hasattr(response, 'message') else str(response)
    except Exception as e:
        return f"Jira error: {str(e)}"

@tool
def coding_operations(query: str) -> str:
    """Execute coding operations: dependency audits, testing, code execution."""
    try:
        print("💻 Routing to Coding Agent")
        coding_agent = create_coding_agent()
        response = coding_agent(query)
        return response.message if hasattr(response, 'message') else str(response)
    except Exception as e:
        return f"Coding error: {str(e)}"

@tool
def planning_operations(query: str) -> str:
    """Break down complex tasks into structured implementation plans."""
    try:
        print("📋 Routing to Planning Agent")
        planning_agent = create_planning_agent()
        response = planning_agent(query)
        return response.message if hasattr(response, 'message') else str(response)
    except Exception as e:
        return f"Planning error: {str(e)}"

# Create orchestrator with agents-as-tools
def create_orchestrator() -> Agent:
    """Create the master orchestrator agent."""
    model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="ap-southeast-2"
    )

    return Agent(
        model=model,
        tools=[
            github_operations,
            jira_operations,
            coding_operations,
            planning_operations
        ],
        system_prompt="""You are the Master Orchestrator Agent.

**Your Role**: Coordinate specialized agents to accomplish complex multi-step tasks.

**Available Agents**:
• github_operations: GitHub repos, issues, PRs, commits
• jira_operations: Jira tickets, sprints, project tracking
• coding_operations: Dependency audits, testing, code execution
• planning_operations: Task breakdown and implementation planning

**Orchestration Strategy**:
1. Analyze user requests to identify required agents
2. Call agents in appropriate sequence
3. Pass results between agents when needed
4. Handle errors gracefully and try alternatives
5. Synthesize multi-agent results into clear responses

**Multi-Step Workflows**:
- You can call multiple agents for complex tasks
- Share context and results between agent calls
- Make decisions based on agent responses
- Coordinate parallel operations when possible

**Example Workflows**:
- Dependency check: coding_operations → github_operations (create issue) → jira_operations (track)
- Feature planning: planning_operations → github_operations (create issues) → jira_operations (sprint)
- Bug fix: github_operations (get issue) → coding_operations (analyze) → github_operations (comment)

Always explain which agents you're coordinating and why."""
    )

@app.entrypoint
async def strands_agent_orchestrator(payload: Dict[str, Any]):
    """Master Orchestrator Agent entrypoint with streaming."""
    try:
        user_input = _extract_user_input(payload)

        if not user_input:
            yield """Hello! I'm the Master Orchestrator Agent.

I coordinate specialized agents for complex workflows:
• GitHub Agent: Repository and issue management
• Jira Agent: Project tracking and sprints
• Coding Agent: Code execution and testing
• Planning Agent: Task breakdown and planning

What would you like me to orchestrate?"""
            return

        # Create orchestrator
        orchestrator = create_orchestrator()

        # Stream response
        async for event in orchestrator.stream_async(user_input):
            yield format_client_text(event)

    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}", exc_info=True)
        yield f"❌ Error: {str(e)}"

if __name__ == "__main__":
    app.run()
```

---

## Migration Plan

### Step 1: Refactor Sub-Agents (GitHub Done ✅, Others TODO)

**Pattern**: Each agent needs a `create_agent()` factory function.

Already done for GitHub:
```python
# agents/github-agent/src/agent.py
def create_github_agent(auth: GitHubAuth) -> Agent:
    """Create GitHub agent with injected authentication."""
    # Implementation...
    return agent
```

Need to do for Jira and Coding agents:
```python
# agents/jira-agent/src/agent.py
def create_jira_agent(auth: JiraAuth) -> Agent:
    """Create Jira agent with injected authentication."""
    # TODO: Apply same DI pattern as GitHub agent
    return agent

# agents/coding-agent/src/agent.py
def create_coding_agent() -> Agent:
    """Create coding agent (no auth needed)."""
    # TODO: Extract from runtime.py
    return agent

# agents/planning-agent/src/agent.py
def create_planning_agent() -> Agent:
    """Create planning agent (no auth needed)."""
    # TODO: Extract from runtime.py
    return agent
```

### Step 2: Update Orchestrator Runtime

Replace subprocess calls with agents-as-tools:

**Before** (subprocess approach):
```python
result = subprocess.run(
    ["python", "-m", "bedrock_agentcore.cli", "invoke", payload],
    capture_output=True,
    timeout=300
)
```

**After** (agents-as-tools):
```python
@tool
def github_operations(query: str) -> str:
    github_agent = create_github_agent(auth)
    return github_agent(query)

orchestrator = Agent(tools=[github_operations, ...])
```

### Step 3: Test Orchestration

```bash
# Test individual agents as tools
python -c "
from src.runtime import github_operations, jira_operations
print(github_operations('List my repositories'))
print(jira_operations('Show current sprint'))
"

# Test orchestrator
agentcore launch --local
agentcore invoke --user-id orchestrator-test "Check dependencies and create GitHub issue"
```

---

## Benefits Summary

| Aspect | Custom Workflow | Strands Native | Winner |
|--------|----------------|---------------|--------|
| Code Complexity | High (100+ lines) | Low (30 lines) | ✅ Native |
| Flexibility | Static workflows | Dynamic LLM decisions | ✅ Native |
| Maintenance | Custom logic to maintain | Framework-supported | ✅ Native |
| Error Handling | Manual | Automatic | ✅ Native |
| Multi-step | Explicit definition | LLM coordination | ✅ Native |
| Learning Curve | Custom patterns | Standard Strands | ✅ Native |
| Testing | Custom test suite | Standard agent tests | ✅ Native |

---

## Conclusion

**Your instinct was correct!**

Strands framework has a native **agents-as-tools** pattern that is:
1. ✅ **Simpler**: Fewer lines of code
2. ✅ **More powerful**: LLM-driven orchestration
3. ✅ **Framework-supported**: Not reinventing the wheel
4. ✅ **Flexible**: Dynamic decision making
5. ✅ **Maintainable**: Standard patterns

**Recommendation**:
- Don't create custom `WorkflowStep` dataclass
- Use Strands' `@tool` decorator pattern
- Let LLM handle orchestration logic
- Focus on making individual agents excellent

---

## Next Steps

1. ✅ Document this finding
2. ⏳ Refactor Jira agent to use DI pattern (like GitHub)
3. ⏳ Refactor Coding agent to use factory pattern
4. ⏳ Refactor orchestrator to use agents-as-tools
5. ⏳ Test multi-agent workflows
6. ⏳ Deploy and validate

---

## References

- **Strands Agents Multi-Agent Example**: https://strandsagents.com/latest/documentation/docs/examples/python/multi_agent_example/
- **Strands GitHub Samples**: https://github.com/strands-agents/samples
- **AWS Blog - Multi-Agent Orchestration**: https://aws.amazon.com/blogs/opensource/introducing-strands-agents-1-0/
- **GitHub Agent Refactoring** (our completed example): `agents/github-agent/REFACTORING_SUMMARY.md`
