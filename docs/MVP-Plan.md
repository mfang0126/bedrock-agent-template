# Multi-Agent System Development Plan - Core MVP

**⚠️ NOTE: This document describes the original complex plan. See `SIMPLIFIED_APPROACH.md` for the current simplified implementation.**

## Goal
Build a minimal agent system that can read a ticket, pull code, create a GitHub issue with a plan, execute the code, and aggregate responses back to the issue.

## Current Status (Simplified Approach)

**What's Implemented:**
- ✅ GitHub Agent with OAuth 3LO authentication
- ✅ Repository tools (list, get_info, create)
- ✅ Issue tools (list, create, close)
- ✅ Deployed to AgentCore Runtime

**What's Different from Original Plan:**
- ❌ No complex orchestrator (keep it simple)
- ❌ No response_builder.py (inline formatting)
- ❌ No rate_limiter.py (GitHub handles it)
- ❌ No validators.py (inline validation)
- ❌ No CLI interface (use agentcore invoke)
- ✅ Only real integration tests (no mocks)

**See:** `docs/Git-Agent-Implementation-Plan.md` for current implementation plan

## Core Workflow Example
**Input**: "Based on JIRA-123, implement the user authentication feature"
**Output**: GitHub issue created with plan, code executed, results posted as comments

## Development Specifications

### Core Classes and Functions

#### BaseAgent Class
```python
class BaseAgent:
    def __init__(self, config)
    def execute(self, request) -> dict
    def validate_request(self, request) -> bool
    def format_response(self, status, result, error) -> dict
```

**Logic:**
- `validate_request`: Check required fields, validate schema
- `format_response`: Ensure consistent output format across all agents
- `execute`: Abstract method, implemented by each agent

## Step 1: Core Agents (MVP)

### 1. Orchestrator Agent

**Class: `OrchestratorAgent`**

**Functions to Develop:**

```python
__init__(self, agents_config)
```
**Logic:** Initialize all agent instances, load config, set MAX_RETRIES=3

```python
parse_user_request(self, input_text: str) -> dict
```
**Logic:**
1. Extract JIRA ticket ID using regex pattern "JIRA-\d+"
2. Extract GitHub repo from format "org/repo"
3. Determine request type (implement/fix/test/review)
4. Return structured dict with extracted data

```python
create_execution_plan(self, parsed_request: dict) -> list
```
**Logic:**
1. Based on request type, determine agent sequence
2. For "implement": [jira, planning, git_create_issue, coding, git_post_comment]
3. Add dependencies between steps
4. Return ordered list of agent calls

```python
execute_with_retry(self, agent: BaseAgent, request: dict) -> dict
```
**Logic:**
1. For retry_count in range(3):
   - Try agent.execute(request)
   - If success, return response
   - If failure, sleep(2^retry_count) seconds
   - On third failure, return error response
2. Log each retry attempt

```python
maintain_context(self, step_name: str, result: dict) -> None
```
**Logic:**
1. Store result in self.execution_context[step_name]
2. Update self.context_chain with new data
3. Merge relevant data for next agent

```python
aggregate_final_response(self, all_results: dict) -> dict
```
**Logic:**
1. Extract key outcomes from each agent
2. Build summary with success/failure status
3. Include GitHub issue URL, test results, modified files
4. Format as markdown for user display

**Data It Manages:**
```python
self.execution_context = {
    "jira_data": {},
    "plan": {},
    "github_issue": {},
    "execution_results": {},
    "retry_counts": {}
}

### 2. Planning Agent

**Class: `PlanningAgent`**

**Functions to Develop:**

```python
__init__(self, llm_client, prompt_templates)
```
**Logic:** Initialize LLM client (Claude/OpenAI), load prompt templates

```python
extract_requirements(self, jira_data: dict) -> dict
```
**Logic:**
1. Parse description and acceptance criteria
2. Identify technical requirements (APIs, database, auth)
3. Extract constraints (performance, security)
4. Return structured requirements dict

```python
generate_plan_prompt(self, requirements: dict, repo_info: dict) -> str
```
**Logic:**
1. Load base prompt template
2. Insert requirements as bullet points
3. Add repo context (language, framework)
4. Include JSON schema for expected output
5. Return complete prompt string

```python
call_llm_for_plan(self, prompt: str) -> str
```
**Logic:**
1. Send prompt to LLM with temperature=0.3 for consistency
2. Set max_tokens based on complexity
3. Retry if response is not valid JSON
4. Return raw LLM response

```python
validate_plan_json(self, plan_json: str) -> dict
```
**Logic:**
1. Parse JSON, catch exceptions
2. Validate required fields: title, steps[]
3. Ensure each step has: id, action, details
4. Check step dependencies are valid
5. Return parsed dict or raise ValidationError

```python
optimize_plan_steps(self, plan: dict) -> dict
```
**Logic:**
1. Identify parallelizable steps (no dependencies)
2. Group related file modifications
3. Merge redundant test runs
4. Add estimated_time per step
5. Return optimized plan

**Input Data:**
```python
{
    "jira_data": {
        "title": "...",
        "description": "...",
        "acceptance_criteria": [...]
    },
    "repo_url": "github.com/org/repo"
}
```

**Output Data:**
```python
{
    "plan": {
        "title": "Implement user authentication",
        "steps": [
            {
                "id": 1,
                "action": "setup_workspace",
                "details": "Clone repo and create branch",
                "depends_on": []
            },
            {
                "id": 2,
                "action": "implement_auth_module",
                "details": "Create auth.py with JWT logic",
                "depends_on": [1]
            },
            {
                "id": 3,
                "action": "add_tests",
                "details": "Write unit tests for auth",
                "depends_on": [2]
            },
            {
                "id": 4,
                "action": "run_test_suite",
                "details": "Execute all tests",
                "depends_on": [3]
            }
        ],
        "files_to_modify": ["src/auth.py", "tests/test_auth.py"],
        "estimated_time": "2 hours"
    }
}
```

### 3. Coding Agent

**Class: `CodingAgent`**

**Functions to Develop:**

```python
__init__(self, mcp_client, workspace_path)
```
**Logic:** Initialize MCP client, set workspace directory, configure sandbox limits

```python
setup_workspace(self, repo_path: str, branch: str) -> str
```
**Logic:**
1. Create temp directory with UUID
2. Copy repo to workspace
3. Git checkout to specified branch
4. Return workspace path

```python
parse_plan_step(self, step: dict) -> dict
```
**Logic:**
1. Extract action type (implement/modify/test)
2. Parse file paths from details
3. Identify required commands
4. Return structured action dict

```python
execute_file_operation(self, operation: str, file_path: str, content: str = None) -> dict
```
**Logic:**
1. Validate file_path is within workspace
2. If read: MCP.read_file(path)
3. If write: backup existing, MCP.write_file(path, content)
4. If modify: read, apply changes, write
5. Return operation result with success/error

```python
run_command_with_timeout(self, command: str, timeout: int = 30) -> dict
```
**Logic:**
1. Sanitize command for security
2. MCP.run_command(command, cwd=workspace)
3. Kill process if exceeds timeout
4. Capture stdout, stderr
5. Return exit_code, output, error

```python
implement_code_changes(self, plan: dict) -> dict
```
**Logic:**
1. For each file in plan.files_to_modify:
   - Read existing content
   - Apply modifications per plan
   - Validate syntax (language-specific)
   - Write updated file
2. Track all modifications
3. Return list of changed files

```python
run_test_suite(self, test_command: str = None) -> dict
```
**Logic:**
1. Detect test framework (pytest/jest/junit)
2. Build appropriate test command
3. Execute with extended timeout (60s)
4. Parse test output for pass/fail count
5. Return test results and coverage

```python
cleanup_workspace(self, workspace_path: str) -> None
```
**Logic:**
1. Save any logs to persistent storage
2. Remove temp directory
3. Clear MCP file handles

**Input Data:**
```python
{
    "plan": {
        "steps": [...],
        "files_to_modify": ["src/auth.py", "tests/test_auth.py"]
    },
    "repo_path": "/tmp/workspace/repo",
    "github_issue": 42
}
```

**Output Data:**
```python
{
    "files_modified": ["src/auth.py", "tests/test_auth.py"],
    "tests_passed": true,
    "test_output": "15/15 tests passed",
    "coverage": "87%",
    "commands_executed": [
        {"cmd": "pytest", "status": "success", "output": "..."},
        {"cmd": "flake8 src/", "status": "success", "output": "no issues"}
    ],
    "logs": [
        "Setup workspace: /tmp/workspace/uuid",
        "Modified src/auth.py: added JWT validation",
        "Created tests/test_auth.py: 5 test cases",
        "All tests passed"
    ],
    "error": null
}
```

### 4. Git Agent

**What It Does**
- Clones repositories
- Creates branches and commits
- Opens pull requests
- Posts comments to issues

**Technical Approach**
- PyGithub or GitPython library
- Personal Access Token authentication
- Simple git operations wrapper
- GitHub API for issues/PRs

**Input/Output for Different Actions**

**Create Issue:**
```python
# Input
{
    "action": "create_issue",
    "title": "Implement: user auth",
    "body": "markdown_formatted_plan",  # From Planning Agent
    "repo": "org/repo"
}
# Output
{
    "issue_url": "github.com/org/repo/issues/42",
    "issue_number": 42
}
```

**Post Comment:**
```python
# Input
{
    "action": "post_comment",
    "issue_number": 42,
    "comment": "execution_results",  # From Coding Agent
    "repo": "org/repo"
}
# Output
{
    "comment_url": "github.com/org/repo/issues/42#comment-123",
    "comment_id": 123
}
```

**Clone & Branch:**
```python
# Input
{
    "action": "setup_workspace",
    "repo_url": "github.com/org/repo",
    "branch_name": "feature/auth-implementation"
}
# Output
{
    "repo_path": "/tmp/workspace/repo",
    "branch": "feature/auth-implementation",
    "commit_sha": "abc123..."
}
```

### 5. JIRA Agent

**What It Does**
- Fetches ticket details
- Extracts requirements and acceptance criteria
- Updates ticket status
- Links GitHub issues to JIRA

**Technical Approach**
- JIRA REST API client
- API token authentication
- Simple field mapping
- Basic JQL queries

**Input/Output for Different Actions**

**Fetch Ticket:**
```python
# Input
{
    "action": "fetch_ticket",
    "ticket_id": "JIRA-123"
}
# Output
{
    "title": "Implement user authentication",
    "description": "As a user, I want to...",
    "acceptance_criteria": [
        "Users can register with email",
        "Password must be encrypted",
        "Session timeout after 30 mins"
    ],
    "priority": "high",
    "assignee": "john.doe",
    "sprint": "Sprint 24"
}
```

**Update Status:**
```python
# Input
{
    "action": "update_ticket",
    "ticket_id": "JIRA-123",
    "status": "In Progress",
    "github_issue": "github.com/org/repo/issues/42"
}
# Output
{
    "updated": true,
    "transition_id": 21
}
```

**Add Comment:**
```python
# Input
{
    "action": "add_comment",
    "ticket_id": "JIRA-123",
    "comment": "GitHub issue created: #42\nExecution started."
}
# Output
{
    "comment_id": "10234",
    "created_at": "2024-01-10T10:00:00Z"
}
```

## Agent Communication Protocol

### Data Passing Structure
Each agent receives and returns standardized message objects:

```python
# Input Message
{
    "request_id": "uuid",
    "source_agent": "orchestrator",
    "action": "create_plan",
    "payload": {...},
    "context": {
        "jira_ticket": "JIRA-123",
        "github_repo": "org/repo",
        "retry_count": 0  # Max 3
    }
}

# Output Message
{
    "request_id": "uuid",
    "agent": "planning_agent",
    "status": "success|failure",
    "result": {...},
    "error": null,
    "metadata": {
        "execution_time": 2.5,
        "tokens_used": 1500
    }
}
```

### Agent Communication Flow

**1. Orchestrator → JIRA Agent**
```python
# Request
{
    "action": "fetch_ticket",
    "payload": {"ticket_id": "JIRA-123"}
}

# Response
{
    "status": "success",
    "result": {
        "title": "Implement user auth",
        "description": "...",
        "acceptance_criteria": ["..."],
        "priority": "high"
    }
}
```

**2. Orchestrator → Planning Agent**
```python
# Request
{
    "action": "create_plan",
    "payload": {
        "jira_data": {...},  # From JIRA Agent
        "repo_url": "github.com/org/repo"
    }
}

# Response
{
    "status": "success",
    "result": {
        "plan": {
            "title": "Implementation Plan",
            "steps": [...],
            "files_to_modify": ["src/auth.py"]
        }
    }
}
```

**3. Orchestrator → Git Agent**
```python
# Request
{
    "action": "create_issue",
    "payload": {
        "title": "Implement: user auth",
        "body": "...",  # From Planning Agent
        "repo": "org/repo"
    }
}

# Response
{
    "status": "success",
    "result": {
        "issue_url": "github.com/org/repo/issues/42",
        "issue_number": 42
    }
}
```

**4. Orchestrator → Coding Agent**
```python
# Request
{
    "action": "execute_plan",
    "payload": {
        "plan": {...},  # From Planning Agent
        "repo_path": "/tmp/workspace/repo",
        "github_issue": 42  # From Git Agent
    }
}

# Response
{
    "status": "success",
    "result": {
        "files_modified": ["src/auth.py"],
        "tests_passed": true,
        "output": "All tests passed (15/15)",
        "logs": ["..."]
    }
}
```

**5. Orchestrator → Git Agent (Update)**
```python
# Request
{
    "action": "post_comment",
    "payload": {
        "issue_number": 42,
        "comment": "Execution complete:\n...",  # From Coding Agent
        "repo": "org/repo"
    }
}
```

### Retry Logic (Hardcoded 3 attempts)
```python
MAX_RETRIES = 3

def execute_with_retry(agent, request):
    for attempt in range(MAX_RETRIES):
        try:
            response = agent.execute(request)
            if response["status"] == "success":
                return response
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                return {"status": "failure", "error": str(e)}
            time.sleep(2 ** attempt)  # Exponential backoff
```

## Implementation Flow

### Phase 1: Basic Pipeline (Week 1-2)

1. **Orchestrator Shell**
   - Basic request routing
   - Sequential execution
   - Error handling

2. **Planning Agent**
   - LLM integration
   - JSON output generation
   - Plan validation

3. **Simple Integration**
   - JIRA ticket reading
   - GitHub issue creation
   - Basic state passing

### Phase 2: Code Execution (Week 3-4)

1. **Coding Agent with MCP**
   - MCP server setup
   - File operations
   - CLI command execution
   - Output capture

2. **Git Operations**
   - Repository cloning
   - Branch management
   - Commit creation

3. **Result Aggregation**
   - Collect execution outputs
   - Format for GitHub comments
   - Post results

## Simple System Prompt Examples

### Planning Agent Prompt
```
You are a planning agent. Given a JIRA ticket or request, create a step-by-step implementation plan.
Output must be valid JSON with steps array.
Each step should have: id, action, details, estimated_time.
Focus on clarity and actionability.
```

### Coding Agent Prompt
```
You are a coding agent with file system access via MCP tools.
Execute the given coding tasks using available tools.
Always validate paths exist before operations.
Return execution results with success/failure status.
Include relevant output or error messages.
```

## Running the MVP

### Basic Usage
```python
# Pseudocode flow
orchestrator = Orchestrator()
request = "Based on JIRA-123, implement the feature"

# Step 1: Get JIRA details
jira_data = orchestrator.jira_agent.get_ticket("JIRA-123")

# Step 2: Generate plan
plan = orchestrator.planning_agent.create_plan(jira_data)

# Step 3: Create GitHub issue
issue_url = orchestrator.git_agent.create_issue(plan)

# Step 4: Execute plan
results = orchestrator.coding_agent.execute(plan)

# Step 5: Post results
orchestrator.git_agent.post_comment(issue_url, results)
```

## Data Flow
```
JIRA Ticket → Planning Agent → GitHub Issue
     ↓                              ↓
Requirements                   Execution Plan
     ↓                              ↓
Coding Agent ← ← ← ← ← ← ← ← ← ← ← ↓
     ↓
Test Results → GitHub Comment
```

## Step 2: Advanced Features (Future)

### Event-Driven Monitoring
- GitHub webhooks for issue comments
- JIRA webhooks for ticket updates
- Automatic re-execution on changes
- Real-time status updates

### Enhanced Orchestration
- Parallel execution where possible
- Complex dependency resolution
- Multi-agent collaboration
- State persistence with database

### Production Features
- AWS deployment with Lambda/Fargate
- Message queues for reliability
- Comprehensive logging
- Security hardening

## Success Criteria for MVP

1. Can read a JIRA ticket and extract requirements
2. Creates a GitHub issue with clear implementation plan
3. Successfully clones and modifies code repository
4. Executes tests and captures output
5. Posts execution results back to GitHub issue
6. Full pipeline completes in under 5 minutes for simple tasks

## Tools Assessment

### Existing Tools (Available from StrandsAgent/AgentCore)

1. **AgentCore Gateway**
   - OAuth2/JWT token management
   - Request routing capabilities
   - Built-in retry mechanisms

2. **StrandsAgent Tools**
   - `file_operations`: Basic file read/write
   - `cli_executor`: Command line execution
   - `http_client`: REST API calls
   - `json_validator`: Schema validation
   - `logger`: Structured logging

3. **MCP Tools (if integrated)**
   - `mcp_file_read`
   - `mcp_file_write`
   - `mcp_run_command`
   - `mcp_list_directory`

### New Tools to Build

#### 1. **Planning Tools**
- `plan_generator`: LLM-based plan creation from requirements
- `plan_validator`: Validates plan structure and dependencies
- `step_decomposer`: Breaks complex tasks into atomic steps

#### 2. **Git Integration Tools**
- `github_issue_manager`: Create/update GitHub issues
- `github_comment_poster`: Post comments with formatting
- `git_branch_manager`: Create/switch branches
- `git_commit_handler`: Stage and commit changes

#### 3. **JIRA Integration Tools**  
- `jira_ticket_fetcher`: Get ticket details with field mapping
- `jira_status_updater`: Transition ticket states
- `jira_comment_adder`: Add formatted comments
- `jira_github_linker`: Link GitHub issues to JIRA

#### 4. **Orchestration Tools**
- `agent_router`: Route requests to appropriate agents
- `state_manager`: Maintain execution context
- `retry_handler`: Implement retry with exponential backoff
- `result_aggregator`: Combine multi-agent responses

#### 5. **Execution Tools**
- `workspace_manager`: Create/cleanup temp workspaces
- `test_runner`: Execute tests with output capture
- `dependency_installer`: Install npm/pip packages
- `sandbox_executor`: Docker-based safe execution

## Tech Stack for MVP

- **Language**: Python 3.10+
- **LLM**: Claude API or OpenAI API
- **Existing**: AgentCore Gateway, StrandsAgent base tools
- **MCP**: Official MCP SDK for file/CLI operations
- **Git**: PyGithub library
- **JIRA**: atlassian-python-api
- **Execution**: Docker for sandboxing
- **Config**: YAML/JSON files

## Next Immediate Steps

1. Set up MCP server with basic file/CLI tools
2. Create agent base class with common functionality
3. Implement Planning Agent with LLM integration
4. Build JIRA → GitHub issue pipeline
5. Add code execution capability
6. Test with simple use case

---

*Focus: Get a working pipeline first, optimize later*