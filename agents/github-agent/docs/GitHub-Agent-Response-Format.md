# GitHub Agent Response Format & Orchestrator Compatibility

**Date**: 2025-10-14
**Status**: ✅ Compatible
**Question**: Does GitHub agent's response format work with orchestrator's agents-as-tools pattern?

---

## Quick Answer

**✅ YES - Fully Compatible**

The GitHub agent returns a Strands `AgentResult` object with a `.message` attribute that contains the string response. The orchestrator's `@tool` wrapper can easily extract this string and return it.

---

## GitHub Agent Response Format

### How We Create the Agent

**File**: `agents/github-agent/src/agent.py`

```python
from strands import Agent
from strands.models import BedrockModel

def create_github_agent(auth: GitHubAuth) -> Agent:
    """Create GitHub agent with injected authentication."""

    model = BedrockModel(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        region_name="ap-southeast-2"
    )

    return Agent(
        model=model,
        tools=[...],  # GitHub tools
        system_prompt="You are a GitHub assistant..."
    )
```

### What the Agent Returns

When you call the GitHub agent, it returns a **Strands `AgentResult`** object:

```python
# Synchronous call
agent = create_github_agent(auth)
result = agent("List my repositories")

# result is an AgentResult object with these attributes:
# - result.message: str          # The agent's text response
# - result.metrics: EventLoopMetrics  # Performance metrics
# - result.stop_reason: str      # Why the agent stopped
# - result.state: dict           # Request state
```

### AgentResult Structure

Based on Strands documentation:

```python
class AgentResult:
    """Result returned by Agent.__call__() or Agent.invoke()"""

    message: str                    # ✅ The actual response text
    metrics: EventLoopMetrics       # Performance data
    stop_reason: str                # "stop", "max_turns", etc.
    state: dict                     # Request state

    # Example metrics attributes:
    # - metrics.accumulated_usage['totalTokens']
    # - metrics.cycle_durations (list of floats)
    # - metrics.tool_metrics (dict of tool usage)
```

**Key Attribute**: `result.message` contains the string response we need!

---

## Runtime Streaming Format

### How Runtime Streams Responses

**File**: `agents/github-agent/src/runtime.py`

The runtime uses **`agent.stream_async()`** for real-time streaming:

```python
@app.entrypoint
async def strands_agent_github(payload):
    # Create agent
    agent = create_github_agent(auth)

    # Stream responses
    async for event in agent.stream_async(user_input):
        yield format_client_text(event)
```

**Streaming Format**:
- Runtime: Streams text chunks in real-time → User sees progress
- Final: Combines all chunks into complete response

**Why Streaming?**
- Better UX (user sees thinking/progress)
- AgentCore supports streaming natively
- Works great for direct user interaction

---

## Orchestrator Compatibility

### Pattern: @tool Wrapper

For orchestrator agents-as-tools pattern, we use **synchronous calls** with `.message` extraction:

```python
from strands import tool

@tool
def github_operations(query: str) -> str:
    """Execute GitHub operations like creating issues, PRs, listing repos."""
    try:
        # 1. Create GitHub agent with auth
        auth = get_auth_provider("dev", oauth_url_callback)
        github_agent = create_github_agent(auth)

        # 2. Invoke agent synchronously
        result = github_agent(query)

        # 3. Extract message string from AgentResult
        return result.message  # ✅ Returns the text response

    except Exception as e:
        return f"GitHub error: {str(e)}"
```

### Why This Works Perfectly

| Aspect | GitHub Agent | Orchestrator Needs | Compatible? |
|--------|-------------|-------------------|-------------|
| Return Type | `AgentResult` object | `str` from `@tool` | ✅ Extract `.message` |
| Call Method | `agent(query)` | Synchronous call | ✅ Works directly |
| Error Handling | Raises exceptions | Catch & return error string | ✅ Try/except |
| Response Format | Natural language text | Tool return value | ✅ Perfect match |

### Complete Example

```python
# agents/orchestrator-agent/src/runtime.py

from strands import Agent, tool
from strands.models import BedrockModel

# Import agent factories
from agents.github_agent.src.agent import create_github_agent
from agents.github_agent.src.auth import get_auth_provider

# OAuth callback (for streaming URLs in runtime)
def oauth_url_callback(url: str):
    # Implementation...
    pass

# Wrap GitHub agent as tool
@tool
def github_operations(query: str) -> str:
    """Execute GitHub operations: repos, issues, PRs, comments."""
    try:
        print("🐙 Routing to GitHub Agent")

        # Create GitHub agent with authentication
        auth = get_auth_provider("dev", oauth_url_callback)
        github_agent = create_github_agent(auth)

        # Invoke and extract message
        result = github_agent(query)
        return result.message  # ✅ String response

    except Exception as e:
        return f"GitHub error: {str(e)}"

# Create orchestrator with GitHub as tool
orchestrator = Agent(
    model=BedrockModel(model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"),
    tools=[github_operations],
    system_prompt="Coordinate specialized agents..."
)

# Use orchestrator
response = orchestrator("Create a GitHub issue for testing")
# Orchestrator calls github_operations → gets string → includes in response
```

---

## Response Flow Comparison

### Direct User → GitHub Agent (Current Runtime)

```
User Request
    ↓
runtime.py: strands_agent_github()
    ↓
agent.stream_async(user_input)
    ↓ (streams events)
format_client_text(event)
    ↓ (yields text chunks)
User sees: Real-time streaming response ✅
```

**Format**: Streaming text chunks
**Use Case**: Direct user interaction via AgentCore

### User → Orchestrator → GitHub Agent (Agents-as-Tools)

```
User Request
    ↓
Orchestrator Agent
    ↓ (decides to use github_operations)
github_operations(query)
    ↓
github_agent(query)
    ↓
result.message (string)
    ↓
Orchestrator receives: String response
    ↓
Orchestrator synthesizes: Multi-agent results
    ↓
User sees: Orchestrated response ✅
```

**Format**: String return value
**Use Case**: Multi-agent coordination

---

## Key Differences

### Runtime (Direct User Interaction)

**Purpose**: Direct user → GitHub agent interaction

**Method**: `agent.stream_async(query)`

**Returns**: Async generator yielding events

**Format**:
```python
async for event in agent.stream_async(query):
    # event contains chunks of text
    yield format_client_text(event)
```

**Benefits**:
- Real-time streaming to user
- Shows thinking/progress
- Better UX for long operations

**Use When**: GitHub agent is directly serving user requests

---

### Agents-as-Tools (Orchestration)

**Purpose**: Orchestrator → GitHub agent delegation

**Method**: `agent(query)` (synchronous call)

**Returns**: `AgentResult` object

**Format**:
```python
result = github_agent(query)
response_string = result.message  # ✅ Extract text
return response_string  # Tool returns string
```

**Benefits**:
- Simple function call interface
- Orchestrator coordinates multiple agents
- Results can be passed between agents
- LLM decides orchestration strategy

**Use When**: GitHub agent is a tool for orchestrator

---

## Example: Multi-Agent Workflow

### Scenario: Dependency Check with GitHub Issue Creation

```python
# User asks orchestrator
user_request = "Check dependencies for /path/to/project and create GitHub issue if vulnerabilities found"

# Orchestrator thinks:
# 1. Use coding_operations to audit
# 2. If vulnerabilities, use github_operations to create issue

# Step 1: Orchestrator calls coding_operations
coding_result = coding_operations("run npm audit for /path/to/project")
# Returns: "Found 5 vulnerabilities: 3 high, 2 moderate..."

# Step 2: Orchestrator sees vulnerabilities, calls github_operations
github_result = github_operations(
    "Create issue titled 'Security: 5 dependency vulnerabilities found' "
    "with description: [details from coding_result]"
)
# Returns: "✅ Created issue #123: Security: 5 dependency vulnerabilities found
#           URL: https://github.com/user/repo/issues/123"

# Step 3: Orchestrator synthesizes
final_response = f"""
I completed the dependency check workflow:

1. **Dependency Audit**: {coding_result}
2. **GitHub Issue**: {github_result}

Next steps: Review the issue and prioritize fixes.
"""
# User sees: Complete workflow results with context
```

**Key Points**:
- Each agent returns a string
- Orchestrator coordinates the sequence
- Results flow between agents naturally
- User gets synthesized multi-agent response

---

## OAuth Handling in Orchestration

### Challenge: OAuth URL Streaming

In direct runtime mode, OAuth URLs are streamed to user:
```python
# runtime.py
async def stream_oauth_url_callback(url: str):
    oauth_url_queue.put_nowait(url)
    # Streams to user immediately
```

### Solution for Orchestrator

When orchestrator calls GitHub agent:

**Option 1: Pre-authenticate** (Recommended)
```python
# Orchestrator runtime starts once
# All OAuth happens at orchestrator level
# Sub-agents reuse tokens

@app.entrypoint
async def strands_agent_orchestrator(payload):
    # Handle OAuth at orchestrator level
    github_auth = get_auth_provider("dev", oauth_url_callback)

    # Pre-authenticate (triggers OAuth if needed)
    await github_auth.get_token()

    # Now create orchestrator with pre-authenticated sub-agents
    @tool
    def github_operations(query: str) -> str:
        # Auth already done, just use agent
        github_agent = create_github_agent(github_auth)
        return github_agent(query).message
```

**Option 2: Pass OAuth callback through** (Alternative)
```python
# Each sub-agent can stream OAuth URLs
# Orchestrator runtime handles streaming
@tool
def github_operations(query: str) -> str:
    auth = get_auth_provider("dev", oauth_url_callback)  # Same callback
    github_agent = create_github_agent(auth)
    return github_agent(query).message
```

---

## Documentation Status

### ✅ Already Documented

1. **GitHub Agent Architecture**: `REFACTORING_SUMMARY.md`
   - DI pattern
   - Auth abstraction
   - Agent factory pattern
   - Testing strategy

2. **OAuth Requirements**: `docs/OAuth-Testing-Guide.md`
   - `--user-id` flag requirement
   - User Federation OAuth flow
   - Environment-specific behavior

3. **Response Format**: `src/common/utils.py`
   - `AgentResponse` dataclass
   - Response formatting utilities
   - Event extraction helpers

4. **Orchestrator Pattern**: `claudedocs/Strands-Native-Orchestration-Analysis.md`
   - Agents-as-tools pattern
   - Multi-agent coordination
   - Implementation examples

### ✅ This Document Adds

- **Response format details**: What GitHub agent returns
- **AgentResult structure**: Strands framework response object
- **Compatibility confirmation**: Yes, works with orchestrator
- **Extract pattern**: Use `result.message` for string response
- **OAuth handling**: How to manage auth in orchestration

---

## Summary

### GitHub Agent Response

✅ **Returns**: Strands `AgentResult` object
✅ **Message**: `result.message` contains the text response
✅ **Format**: Natural language string (perfect for tools)

### Orchestrator Compatibility

✅ **Pattern**: Wrap agent call in `@tool` function
✅ **Extract**: Return `result.message` string
✅ **Works**: Fully compatible with agents-as-tools pattern

### Key Insight

```python
# This simple pattern works perfectly:

@tool
def github_operations(query: str) -> str:
    github_agent = create_github_agent(auth)
    result = github_agent(query)
    return result.message  # ✅ That's it!
```

The GitHub agent's response format is **perfectly designed** for the orchestrator's agents-as-tools pattern. No conversion needed, just extract `.message`!

---

## References

- **Strands Agent API**: https://strandsagents.com/latest/documentation/docs/api-reference/agent/
- **Multi-Agent Example**: https://strandsagents.com/latest/documentation/docs/examples/python/multi_agent_example/
- **GitHub Agent Factory**: `src/agent.py`
- **GitHub Runtime**: `src/runtime.py`
- **Orchestrator Analysis**: `claudedocs/Strands-Native-Orchestration-Analysis.md`
