# Decision 001: Agent Communication Pattern

**Status**: Decided  
**Date**: 2025-10-14  
**Decision Makers**: Architecture Team  

## Decision

**We will use the Agents-as-Tools pattern from Strands 1.0 for our orchestrator agent to communicate with specialized agents (GitHub, Planning, Coding, JIRA).**

This replaces our current boto3 API-based communication approach with Strands' native multi-agent primitives, providing simpler code, better context preservation, and automatic error handling.

---

## Context

Our multi-agent platform consists of:
- **Orchestrator Agent**: Coordinates workflow and delegates tasks
- **Specialized Agents**: GitHub, Planning, Coding, JIRA (each with independent runtime)

We evaluated three communication methods available in AWS AgentCore and Strands 1.0 (July 2025):
1. Agents-as-Tools (Strands native)
2. A2A Protocol (Agent-to-Agent)
3. Boto3 API calls (AWS native)

---

## Communication Methods Analysis

### 1. Agents-as-Tools Pattern

**What it is**: Specialized agents are exposed as callable tools that the orchestrator can invoke. The LLM decides dynamically which agent-tool to call based on user requests.

**How it works**:
```python
from strands import Agent

# Define specialized agents
github_agent = Agent(
    agent_id="github-Hn7UKwBMRj",
    as_tool=True,
    name="github_specialist",
    description="Handles GitHub operations: PRs, issues, commits"
)

planning_agent = Agent(
    agent_id="planning-xxx",
    as_tool=True,
    name="planning_specialist", 
    description="Creates task breakdowns and project plans"
)

# Orchestrator uses agents as tools
orchestrator = Agent(
    tools=[github_agent, planning_agent],
    prompt="You coordinate specialized agents to complete user requests"
)

# Execution
result = orchestrator("Create a feature plan and open GitHub issues")
# LLM automatically:
# 1. Calls planning_specialist tool → gets JSON response
# 2. Calls github_specialist tool with planning data → gets JSON response
# 3. Synthesizes final answer
```

**✅ Plus Points**:
- **Simplicity**: 3 lines vs 15+ lines of boto3 boilerplate
- **Automatic context**: Strands handles conversation flow between agents
- **Dynamic routing**: LLM decides which agent to call based on request
- **Built-in error handling**: Framework manages retries and failures
- **Type safety**: Tool schemas validated automatically
- **Native to Strands 1.0**: Official recommended pattern

**Scenarios to Use**:
- ✅ **Hierarchical delegation** (orchestrator → specialists)
- ✅ **Dynamic agent selection** (LLM chooses appropriate agent)
- ✅ **Multi-step workflows** (planning → coding → deployment)
- ✅ **Result synthesis** (combining outputs from multiple agents)

**Example Use Case**:
```
User: "Build auth feature for myapp and create GitHub issues"

Orchestrator thinks:
1. "I need a plan" → Calls planning_specialist
2. Receives: {"phases": [...], "tasks": [...]}
3. "Now create issues" → Calls github_specialist with task data
4. Receives: {"created_issues": [1234, 1235]}
5. Returns: "Created auth feature plan with 2 GitHub issues"
```

---

### 2. A2A Protocol (Agent-to-Agent)

**What it is**: Peer-to-peer communication protocol where agents discover and invoke each other as equals without hierarchy.

**How it works**:
```python
from strands.protocols import A2AClient

# Peer-to-peer invocation
a2a_client = A2AClient()

response = await a2a_client.invoke(
    agent_uri="a2a://github-agent",
    message={
        "action": "sync_with_jira",
        "issue_id": "PROJ-123"
    },
    context={"user_id": "user123"}
)
```

**✅ Plus Points**:
- **Peer equality**: No parent-child relationship required
- **Service discovery**: Agents can discover each other dynamically
- **Cross-organization**: Standardized protocol for inter-org communication
- **Platform agnostic**: Works across different cloud providers
- **Marketplace ready**: Enables agent marketplaces/networks

**Scenarios to Use**:
- ✅ **Peer collaboration** (GitHub agent ↔ JIRA agent syncing data)
- ✅ **Agent discovery** (finding available agents dynamically)
- ✅ **Cross-platform** (AWS agent talking to Azure agent)
- ✅ **Agent ecosystems** (building agent networks/marketplaces)

**Example Use Case**:
```
Scenario: GitHub and JIRA agents collaborate as equals

GitHub Agent detects PR merge:
1. Discovers JIRA agent via A2A registry
2. Sends message: {"event": "pr_merged", "pr_id": 456}
3. JIRA agent receives and updates ticket status
4. JIRA sends back: {"ticket_updated": "PROJ-123"}
5. Both agents maintain equal status
```

---

### 3. Boto3 API Calls

**What it is**: Direct AWS Bedrock Agent Runtime API invocation using boto3 SDK.

**How it works**:
```python
import boto3
import json

bedrock_runtime = boto3.client('bedrock-agent-runtime')

response = bedrock_runtime.invoke_agent(
    agentId='github-Hn7UKwBMRj',
    agentAliasId='TSTALIASID',
    sessionId='session-123',
    inputText=json.dumps({
        "action": "create_pr",
        "repo": "myrepo"
    })
)

# Manual response parsing and streaming handling
for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']
        # Process streaming data...
```

**✅ Plus Points**:
- **Raw control**: Full access to AWS API parameters
- **Infrastructure automation**: Perfect for Lambda/Step Functions/ECS
- **Language flexibility**: Works with any language (not just Python)
- **Custom routing**: Implement custom load balancing/retry logic
- **Monitoring**: Direct CloudWatch/X-Ray integration

**Scenarios to Use**:
- ✅ **Infrastructure triggers** (CloudWatch alarm → Lambda → agent)
- ✅ **Custom orchestration** (Step Functions workflow)
- ✅ **Non-Python services** (Java/Go services invoking agents)
- ✅ **Advanced AWS features** (VPC endpoints, PrivateLink)

**Example Use Case**:
```
Scenario: CloudWatch alarm triggers security audit

1. CloudWatch detects vulnerability CVE
2. EventBridge rule triggers Lambda function
3. Lambda uses boto3 to invoke security-audit-agent:
   
   boto3.client('bedrock-agent-runtime').invoke_agent(
       agentId='security-audit-agent',
       inputText=json.dumps({"cve": "CVE-2024-1234"})
   )
   
4. Lambda processes streaming response
5. Posts results to SNS topic
```

---

## Decision Matrix

| Criteria | Agents-as-Tools | A2A Protocol | Boto3 API |
|----------|----------------|--------------|-----------|
| **Simplicity** | ⭐⭐⭐⭐⭐ (3 lines) | ⭐⭐⭐ (moderate) | ⭐⭐ (15+ lines) |
| **Orchestration** | ⭐⭐⭐⭐⭐ (designed for) | ⭐⭐ (not ideal) | ⭐⭐⭐ (manual) |
| **Context Handling** | ⭐⭐⭐⭐⭐ (automatic) | ⭐⭐⭐ (manual) | ⭐⭐ (manual) |
| **Error Handling** | ⭐⭐⭐⭐⭐ (built-in) | ⭐⭐⭐ (custom) | ⭐⭐ (custom) |
| **Peer Collaboration** | ⭐⭐ (hierarchical) | ⭐⭐⭐⭐⭐ (designed for) | ⭐⭐⭐ (possible) |
| **AWS Integration** | ⭐⭐⭐ (abstracted) | ⭐⭐⭐ (standard) | ⭐⭐⭐⭐⭐ (native) |
| **Infrastructure Use** | ⭐⭐ (agent only) | ⭐⭐⭐ (flexible) | ⭐⭐⭐⭐⭐ (Lambda/ECS) |

---

## Why Agents-as-Tools for Our Project

### ✅ Perfect Match for Our Architecture

**Our Requirements**:
1. Orchestrator delegates to specialized agents
2. Dynamic agent selection based on user requests
3. Multi-step workflows with result synthesis
4. Minimize boilerplate and maintenance

**Agents-as-Tools delivers**:
- Native hierarchical delegation
- LLM-driven dynamic routing
- Automatic context propagation
- Minimal code overhead

### Code Comparison

**Before (boto3)**:
```python
# orchestrator-agent/src/runtime.py (15+ lines per agent call)
import boto3
import json

bedrock = boto3.client('bedrock-agent-runtime')

# Call planning agent
planning_response = bedrock.invoke_agent(
    agentId='planning-xxx',
    agentAliasId='TSTALIASID',
    sessionId=session_id,
    inputText=json.dumps({"task": user_request})
)

# Parse streaming response
planning_result = ""
for event in planning_response['completion']:
    if 'chunk' in event:
        planning_result += event['chunk']['bytes'].decode()

# Call github agent with planning data
github_response = bedrock.invoke_agent(
    agentId='github-Hn7UKwBMRj',
    agentAliasId='TSTALIASID',
    sessionId=session_id,
    inputText=json.dumps({
        "action": "create_issues",
        "tasks": json.loads(planning_result)
    })
)

# More parsing and error handling...
```

**After (Agents-as-Tools)**:
```python
# orchestrator-agent/src/runtime.py (3 lines)
from strands import Agent

planning_agent = Agent(agent_id="planning-xxx", as_tool=True)
github_agent = Agent(agent_id="github-Hn7UKwBMRj", as_tool=True)

orchestrator = Agent(
    tools=[planning_agent, github_agent],
    prompt="Coordinate specialized agents for user requests"
)

# That's it! LLM handles orchestration automatically
```

---

## When NOT to Use Agents-as-Tools

Use alternatives when:

1. **A2A Protocol**:
   - Agents need peer-to-peer collaboration (no hierarchy)
   - Building cross-organization agent networks
   - Example: GitHub agent syncing with external JIRA system

2. **Boto3 API**:
   - Infrastructure automation (Lambda triggers)
   - Non-Python services need to invoke agents
   - Custom routing/monitoring requirements
   - Example: Step Functions orchestrating complex workflows

---

## Implementation Plan

### Phase 1: Orchestrator Agent (High Priority)
1. Create `agents/orchestrator-agent/` following GitHub agent pattern
2. Implement Agents-as-Tools pattern:
   ```python
   # agents/orchestrator-agent/src/runtime.py
   from strands import Agent
   from bedrock_agentcore.runtime import BedrockAgentCoreApp
   
   # Convert existing agents to tools
   github = Agent(agent_id="github-Hn7UKwBMRj", as_tool=True)
   planning = Agent(agent_id="planning-xxx", as_tool=True)
   coding = Agent(agent_id="coding-xxx", as_tool=True)
   jira = Agent(agent_id="jira-xxx", as_tool=True)
   
   orchestrator = Agent(
       tools=[github, planning, coding, jira],
       prompt="You coordinate specialized agents..."
   )
   
   app = BedrockAgentCoreApp()
   
   @app.entrypoint
   def invoke(payload):
       return orchestrator(payload.get("prompt"))
   ```

3. Test multi-agent workflows
4. Deploy orchestrator to AgentCore Runtime

### Phase 2: Optional A2A for Peer Scenarios (Low Priority)
- Implement A2A between GitHub ↔ JIRA for bidirectional sync
- Use only when agents need to collaborate as equals

### Phase 3: Boto3 for Infrastructure (As Needed)
- Keep boto3 for Lambda/Step Functions triggers
- Use for monitoring and infrastructure automation

---

## Consequences

### Positive
- **90% code reduction** in orchestrator (15+ lines → 3 lines per agent call)
- **Native Strands 1.0 support** (framework handles complexity)
- **Better maintainability** (less custom error handling)
- **Automatic scaling** (Strands manages agent lifecycle)
- **Future-proof** (official AWS/Strands recommended pattern)

### Negative
- **Lock-in to Strands SDK** (requires Python and Strands dependency)
- **Less AWS API control** (abstracted by framework)
- **Learning curve** (team needs to understand Strands patterns)

### Mitigations
- Keep boto3 option for infrastructure automation scenarios
- Document Strands patterns for team onboarding
- Use hybrid approach where appropriate

---

## References

- [Strands Agents 1.0 Announcement](https://aws.amazon.com/blogs/opensource/introducing-strands-agents-1-0-production-ready-multi-agent-orchestration-made-simple/) (July 2025)
- [Agents-as-Tools Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/multi-agent/agents-as-tools/)
- [Amazon Bedrock AgentCore](https://aws.amazon.com/bedrock/agentcore/)
- [A2A Protocol Specification](https://a2a-protocol.org/)

---

## Status

**Decided**: Agents-as-Tools for orchestrator → specialist communication  
**Next Steps**: Implement orchestrator agent following this pattern  
**Review Date**: After orchestrator implementation (estimated 2 weeks)
