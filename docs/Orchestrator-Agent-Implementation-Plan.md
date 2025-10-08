# Orchestrator Agent Implementation Plan

**Status Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed
- ❌ Blocked

**Last Updated:** 2024

**Project Location:** `/Users/ming.fang/Code/ai-coding-agents/app`

---

## 📊 Implementation Progress

**Overall Status:** ⬜ 0% Complete (Not Started - Build Last)

| Phase | Status | Progress | Remaining Work |
|-------|--------|----------|----------------|
| Phase 1: Core Infrastructure | ⬜ | 0% | Setup agent |
| Phase 2: Agent Coordination | ⬜ | 0% | Call other agents |
| Phase 3: Workflow Management | ⬜ | 0% | Sequence, retry logic |
| Phase 4: Context Management | ⬜ | 0% | Pass data between agents |
| Phase 5: Error Handling | ⬜ | 0% | Inline validation |
| Phase 6: Integration Testing | ⬜ | 0% | End-to-end tests |
| Phase 7: Documentation | ⬜ | 0% | API docs |

**Simplified Approach:**
- ❌ No complex state machine
- ❌ No database for state
- ✅ Simple sequential execution
- ✅ In-memory context passing

---

## 🎯 Quick Reference

**What Needs to Be Built:**
```bash
# Deploy the orchestrator
authenticate --to=wealth-dev-au
agentcore launch

# Invoke end-to-end workflow
agentcore invoke '{
    "prompt": "Based on JIRA-123, implement the feature in myorg/myrepo"
}' --user-id "user-123"
```

**Core Functionality:**
1. Parse user request (extract JIRA ID, repo)
2. Coordinate agent execution sequence
3. Pass context between agents
4. Handle retries (max 3)
5. Aggregate final results

**Workflow:**
```
User Request
    ↓
JIRA Agent (fetch ticket)
    ↓
Planning Agent (create plan)
    ↓
Git Agent (create issue)
    ↓
Coding Agent (execute plan)
    ↓
Git Agent (post results)
    ↓
JIRA Agent (update status)
    ↓
Final Response
```

---

## Overview

The Orchestrator Agent coordinates all other agents to execute end-to-end workflows. It's the "conductor" that ensures agents work together in the right sequence.

**Key Responsibilities:**
- Parse user requests
- Determine agent execution sequence
- Call agents in order
- Pass context between agents
- Handle retries and errors
- Aggregate final results

**Important:** Build this LAST after all other agents are working!

---

## Phase 1: Core Infrastructure ⬜

### 1.1 Agent Setup ⬜

**Implementation Details:**
- Create orchestrator agent
- Configure to call other agents
- Set up context management

**Files to Create:**
- `src/agents/orchestrator_agent/runtime.py` - AgentCore entrypoint
- `src/tools/orchestrator/` - Orchestration tools

**Core Logic:**
```
CLASS OrchestratorAgent:
    PROPERTIES:
        - agents: {
            "jira": JIRAAgentClient,
            "planning": PlanningAgentClient,
            "git": GitAgentClient,
            "coding": CodingAgentClient
        }
        - max_retries: 3
        - context: {}
    
    METHOD handle_request(payload):
        user_request = payload.get("prompt")
        
        # Parse request
        parsed = parse_request(user_request)
        
        # Determine workflow
        workflow = determine_workflow(parsed)
        
        # Execute workflow
        results = execute_workflow(workflow, parsed)
        
        # Aggregate results
        RETURN aggregate_results(results)
```

**System Prompt:**
```
You are an Orchestrator Agent that coordinates multiple specialized agents to complete complex workflows.

Your responsibilities:
1. Parse user requests to extract key information
2. Determine the correct sequence of agent calls
3. Execute agents in order
4. Pass context between agents
5. Handle errors and retries
6. Aggregate final results

Available Agents:
- JIRA Agent: Fetch tickets, update status
- Planning Agent: Generate implementation plans
- Git Agent: Manage GitHub (issues, PRs, comments)
- Coding Agent: Execute code changes and tests

Guidelines:
- Always validate user input
- Call agents in logical sequence
- Pass relevant context to each agent
- Retry failed operations (max 3 times)
- Provide clear status updates
- Aggregate results into coherent response

Input Format:
{
    "prompt": "Based on JIRA-123, implement feature in org/repo"
}

Output Format:
{
    "status": "success|failure",
    "workflow_executed": [...],
    "results": {
        "jira_ticket": {...},
        "plan": {...},
        "github_issue": {...},
        "execution": {...}
    },
    "summary": "..."
}
```

---

## Phase 2: Agent Coordination ⬜

### 2.1 Parse Request Tool ⬜

**Implementation Details:**
- Extract JIRA ticket ID
- Extract GitHub repo
- Determine request type

**Core Logic:**
```
FUNCTION parse_request(user_input):
    parsed = {
        "jira_ticket": None,
        "github_repo": None,
        "request_type": "implement",  # implement|fix|test|review
        "raw_input": user_input
    }
    
    # Extract JIRA ticket ID
    jira_match = re.search(r'(JIRA|[A-Z]{2,10})-\d+', user_input)
    IF jira_match:
        parsed["jira_ticket"] = jira_match.group(0)
    
    # Extract GitHub repo
    repo_match = re.search(r'([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)', user_input)
    IF repo_match:
        parsed["github_repo"] = repo_match.group(1)
    
    # Determine request type
    IF "fix" in user_input.lower() OR "bug" in user_input.lower():
        parsed["request_type"] = "fix"
    ELIF "test" in user_input.lower():
        parsed["request_type"] = "test"
    ELIF "review" in user_input.lower():
        parsed["request_type"] = "review"
    
    RETURN parsed
```

**Tool Signature:**
```python
@tool
def parse_user_request(prompt: str) -> str
```

---

### 2.2 Determine Workflow Tool ⬜

**Implementation Details:**
- Based on request type, determine agent sequence
- Return ordered list of agent calls

**Core Logic:**
```
FUNCTION determine_workflow(parsed_request):
    request_type = parsed_request["request_type"]
    
    IF request_type == "implement":
        workflow = [
            {"agent": "jira", "action": "fetch_ticket"},
            {"agent": "planning", "action": "generate_plan"},
            {"agent": "git", "action": "create_issue"},
            {"agent": "coding", "action": "execute_plan"},
            {"agent": "git", "action": "post_comment"},
            {"agent": "jira", "action": "update_status"}
        ]
    
    ELIF request_type == "fix":
        workflow = [
            {"agent": "jira", "action": "fetch_ticket"},
            {"agent": "planning", "action": "generate_fix_plan"},
            {"agent": "coding", "action": "execute_plan"},
            {"agent": "git", "action": "create_pr"}
        ]
    
    ELIF request_type == "test":
        workflow = [
            {"agent": "coding", "action": "run_tests"},
            {"agent": "git", "action": "post_results"}
        ]
    
    RETURN workflow
```

---

### 2.3 Execute Agent Tool ⬜

**Implementation Details:**
- Call specific agent via AgentCore
- Pass context
- Handle response

**Core Logic:**
```
FUNCTION execute_agent(agent_name, action, context):
    # Get agent ARN
    agent_arn = get_agent_arn(agent_name)
    
    # Build payload
    payload = {
        "action": action,
        "context": context
    }
    
    # Call agent via AgentCore
    TRY:
        response = agentcore_client.invoke_agent(
            agent_arn=agent_arn,
            payload=payload,
            user_id=context.get("user_id")
        )
        
        RETURN {
            "status": "success",
            "agent": agent_name,
            "action": action,
            "result": response
        }
        
    CATCH Exception as e:
        RETURN {
            "status": "failure",
            "agent": agent_name,
            "action": action,
            "error": str(e)
        }
```

---

## Phase 3: Workflow Management ⬜

### 3.1 Execute Workflow Tool ⬜

**Implementation Details:**
- Execute agents in sequence
- Pass context between steps
- Handle failures

**Core Logic:**
```
FUNCTION execute_workflow(workflow, initial_context):
    context = initial_context
    results = []
    
    FOR step IN workflow:
        agent_name = step["agent"]
        action = step["action"]
        
        # Execute with retry
        result = execute_with_retry(agent_name, action, context)
        
        # Check if failed
        IF result["status"] == "failure":
            RETURN {
                "status": "failure",
                "failed_at": f"{agent_name}.{action}",
                "error": result["error"],
                "completed_steps": results
            }
        
        # Update context with result
        context[f"{agent_name}_result"] = result["result"]
        results.append(result)
    
    RETURN {
        "status": "success",
        "results": results,
        "context": context
    }
```

---

### 3.2 Retry Logic ⬜

**Implementation Details:**
- Retry failed operations
- Exponential backoff
- Max 3 attempts

**Core Logic:**
```
FUNCTION execute_with_retry(agent_name, action, context, max_retries=3):
    FOR attempt IN range(1, max_retries + 1):
        result = execute_agent(agent_name, action, context)
        
        IF result["status"] == "success":
            RETURN result
        
        # Log retry
        LOG(f"Retry {attempt}/{max_retries} for {agent_name}.{action}")
        
        # Exponential backoff
        IF attempt < max_retries:
            sleep(2 ** attempt)  # 2s, 4s, 8s
    
    # All retries failed
    RETURN {
        "status": "failure",
        "agent": agent_name,
        "action": action,
        "error": f"Failed after {max_retries} attempts"
    }
```

---

## Phase 4: Context Management ⬜

### 4.1 Context Passing ⬜

**Implementation Details:**
- Maintain execution context
- Pass relevant data to each agent
- Merge results

**Core Logic:**
```
FUNCTION build_agent_context(agent_name, action, global_context):
    # Base context
    agent_context = {
        "user_id": global_context["user_id"],
        "request_id": global_context["request_id"]
    }
    
    # Add agent-specific context
    IF agent_name == "jira":
        agent_context["ticket_id"] = global_context.get("jira_ticket")
    
    ELIF agent_name == "planning":
        agent_context["requirements"] = global_context.get("jira_result")
        agent_context["repo"] = global_context.get("github_repo")
    
    ELIF agent_name == "git":
        IF action == "create_issue":
            agent_context["plan"] = global_context.get("planning_result")
            agent_context["repo"] = global_context.get("github_repo")
        ELIF action == "post_comment":
            agent_context["issue_number"] = global_context.get("github_issue_number")
            agent_context["results"] = global_context.get("coding_result")
    
    ELIF agent_name == "coding":
        agent_context["plan"] = global_context.get("planning_result")
        agent_context["repo_path"] = global_context.get("repo_path")
    
    RETURN agent_context
```

---

## Phase 5: Error Handling (Simplified) ⬜

**Approach:** Inline error handling with clear messages

**Example:**
```python
@tool
def execute_workflow(workflow_type: str, jira_ticket: str = None, repo: str = None) -> str:
    # Inline validation
    if not jira_ticket and not repo:
        return "❌ Error: Need either JIRA ticket or GitHub repo"
    
    if workflow_type not in ["implement", "fix", "test"]:
        return f"❌ Unknown workflow type: {workflow_type}"
    
    try:
        # Parse and execute
        context = {"jira_ticket": jira_ticket, "github_repo": repo}
        workflow = determine_workflow(workflow_type)
        results = execute_workflow_steps(workflow, context)
        
        if results["status"] == "success":
            return format_success_response(results)
        else:
            return format_error_response(results)
            
    except Exception as e:
        return f"❌ Workflow error: {str(e)}"
```

---

## Phase 6: Integration Testing ⬜

**Test Script:** `tests/integration/test_orchestrator_agent.sh`

```bash
#!/bin/bash
# End-to-end integration tests

authenticate --to=wealth-dev-au

USER_ID="test-user-$(date +%s)"
ORCHESTRATOR_ARN="arn:aws:bedrock-agentcore:ap-southeast-2:xxx:agent/orchestrator"

# Test 1: Full workflow (JIRA → Planning → Git → Coding)
echo "Test 1: Full implementation workflow"
agentcore invoke '{
    "prompt": "Based on JIRA-123, implement user authentication in myorg/myrepo"
}' --user-id "$USER_ID" --agent-arn "$ORCHESTRATOR_ARN"

# Test 2: Partial workflow (just planning)
echo "Test 2: Planning only workflow"
agentcore invoke '{
    "prompt": "Create a plan for adding health check endpoint"
}' --user-id "$USER_ID" --agent-arn "$ORCHESTRATOR_ARN"

# Test 3: Error handling
echo "Test 3: Invalid JIRA ticket"
agentcore invoke '{
    "prompt": "Based on INVALID-999, implement feature"
}' --user-id "$USER_ID" --agent-arn "$ORCHESTRATOR_ARN"
```

---

## Timeline Estimate

**Total: 3-4 days (Build LAST!)**

- ⬜ **Phase 1:** Agent setup (0.5 day)
- ⬜ **Phase 2:** Agent coordination (1 day)
- ⬜ **Phase 3:** Workflow management (1 day)
- ⬜ **Phase 4:** Context management (0.5 day)
- ⬜ **Phase 5:** Error handling (0.5 day)
- ⬜ **Phase 6:** Integration testing (1 day)
- ⬜ **Phase 7:** Documentation (0.5 day)

**Prerequisites:**
- ✅ Git Agent must be complete
- ✅ Planning Agent must be complete
- ✅ JIRA Agent must be complete
- ✅ Coding Agent must be complete

---

## Dependencies

**Python Packages:**
- ✅ `bedrock-agentcore[strands-agents]>=0.1.0`
- ✅ `boto3>=1.39.15` (for calling other agents)

**Agent Dependencies:**
- All other agents must be deployed first
- Need ARNs for all agents

---

## Success Metrics

**Functional Requirements:**
- ✅ Parse user requests correctly
- ✅ Execute agents in sequence
- ✅ Pass context between agents
- ✅ Handle retries (max 3)
- ✅ Aggregate results

**Quality Requirements:**
- Workflows should complete end-to-end
- Errors should be handled gracefully
- Context should be passed correctly
- Results should be aggregated clearly

---

## 📝 Implementation Checklist

**Phase 1: Core Infrastructure (0% → 100%)**
- [ ] Create `src/agents/orchestrator_agent/runtime.py`
- [ ] Create `src/tools/orchestrator/` directory
- [ ] Set up agent client wrappers
- [ ] Test basic agent invocation

**Phase 2: Agent Coordination (0% → 100%)**
- [ ] Create `parse_request` tool
- [ ] Create `determine_workflow` tool
- [ ] Create `execute_agent` tool
- [ ] Test agent calls

**Phase 3: Workflow Management (0% → 100%)**
- [ ] Create `execute_workflow` tool
- [ ] Implement retry logic
- [ ] Test sequential execution

**Phase 4: Context Management (0% → 100%)**
- [ ] Implement context passing
- [ ] Build agent-specific contexts
- [ ] Test data flow

**Phase 5: Error Handling (0% → 100%)**
- [ ] Add input validation
- [ ] Handle agent failures
- [ ] Return clear error messages

**Phase 6: Integration Testing (0% → 100%)**
- [ ] Create end-to-end test script
- [ ] Test full workflows
- [ ] Test error scenarios
- [ ] Verify all agents work together

**Phase 7: Documentation (0% → 100%)**
- [ ] Write API documentation
- [ ] Document workflows
- [ ] Add usage examples

---

## Notes

- **Build this LAST** after all other agents work
- Keep it simple - no complex state machines
- Focus on sequential execution
- In-memory context is fine for MVP
- Test end-to-end workflows thoroughly

---

**End of Implementation Plan**

**Document Version:** 1.0  
**Status:** ⬜ Not Started (Build Last!)  
**Estimated Effort:** 3-4 days  
**Prerequisites:** All other agents must be complete
