# Coding Agent Implementation Plan

**Status Legend:**
- ⬜ Not Started
- 🟡 In Progress
- ✅ Completed
- ❌ Blocked

**Last Updated:** 2024

**Project Location:** `/Users/ming.fang/Code/ai-coding-agents/app`

---

## 📊 Implementation Progress

**Overall Status:** ⬜ 0% Complete (Not Started)

| Phase | Status | Progress | Remaining Work |
|-------|--------|----------|----------------|
| Phase 1: Core Infrastructure | ⬜ | 0% | Setup agent + MCP |
| Phase 2: Workspace Management | ⬜ | 0% | Clone, setup workspace |
| Phase 3: Code Execution | ⬜ | 0% | File ops, commands |
| Phase 4: Testing Integration | ⬜ | 0% | Run tests, parse results |
| Phase 5: Error Handling | ⬜ | 0% | Inline validation |
| Phase 6: Integration Testing | ⬜ | 0% | Real code execution |
| Phase 7: Documentation | ⬜ | 0% | API docs |

**Simplified Approach:**
- ❌ No CLI interface
- ❌ No unit tests with mocks
- ✅ Only real integration tests
- ✅ MCP for code execution

---

## 🎯 Quick Reference

**What Needs to Be Built:**
```bash
# Deploy the coding agent
authenticate --to=wealth-dev-au
agentcore launch

# Invoke the agent
agentcore invoke '{
    "prompt": "Execute the plan from Planning Agent",
    "plan": {...},
    "repo_path": "/tmp/workspace/repo"
}' --user-id "user-123"
```

**Core Functionality:**
1. Set up isolated workspace
2. Execute file operations (read, write, modify)
3. Run shell commands with timeout
4. Execute test suites
5. Capture and format results

**Key Technology:**
- **MCP (Model Context Protocol)** for safe code execution
- Isolated workspace per execution
- Timeout protection
- Result aggregation

---

## Overview

The Coding Agent executes implementation plans by modifying code files, running commands, and executing tests. It uses MCP (Model Context Protocol) for safe, sandboxed code execution.

**Key Responsibilities:**
- Set up isolated workspace
- Read/write/modify code files
- Execute shell commands safely
- Run test suites
- Capture execution results
- Clean up workspace

---

## Phase 1: Core Infrastructure ⬜

### 1.1 MCP Integration Setup ⬜

**Implementation Details:**
- Integrate MCP client for code execution
- Configure sandbox limits
- Set up workspace isolation

**Files to Create:**
- `src/agents/coding_agent/runtime.py` - AgentCore entrypoint
- `src/tools/coding/` - Coding tools directory
- `src/common/mcp/client.py` - MCP client wrapper

**Core Logic:**
```
CLASS CodingAgent:
    PROPERTIES:
        - mcp_client: MCPClient
        - workspace_base: "/tmp/workspaces"
        - timeout_default: 30 seconds
        - max_file_size: 10MB
    
    METHOD handle_request(payload):
        plan = payload.get("plan")
        repo_path = payload.get("repo_path")
        
        workspace = setup_workspace(repo_path)
        TRY:
            results = execute_plan(plan, workspace)
            RETURN format_results(results)
        FINALLY:
            cleanup_workspace(workspace)
```

**System Prompt:**
```
You are a Coding Agent specialized in executing implementation plans safely.

Your responsibilities:
1. Set up isolated workspaces
2. Execute file operations (read, write, modify)
3. Run shell commands with timeout protection
4. Execute test suites
5. Capture and format results

Guidelines:
- Always validate file paths (no directory traversal)
- Sanitize shell commands (no dangerous operations)
- Use timeouts for all commands
- Capture stdout and stderr
- Clean up workspaces after execution

Security:
- Never execute: rm -rf /, sudo, curl | bash
- Validate all file paths are within workspace
- Limit command execution time
- Restrict network access if possible

Input Format:
{
    "plan": {
        "steps": [...],
        "files_to_modify": [...]
    },
    "repo_path": "/tmp/workspace/repo"
}

Output Format:
{
    "files_modified": [...],
    "tests_passed": true/false,
    "test_output": "...",
    "commands_executed": [...],
    "logs": [...]
}
```

---

### 1.2 MCP Client Wrapper ⬜

**Implementation Details:**
- Wrap MCP client for easier use
- Add timeout protection
- Handle errors gracefully

**Core Logic:**
```
CLASS MCPClient:
    FUNCTION read_file(file_path, workspace):
        # Validate path
        IF NOT is_within_workspace(file_path, workspace):
            RAISE SecurityError("Path outside workspace")
        
        # Read via MCP
        content = mcp.read_file(file_path)
        RETURN content
    
    FUNCTION write_file(file_path, content, workspace):
        # Validate path
        IF NOT is_within_workspace(file_path, workspace):
            RAISE SecurityError("Path outside workspace")
        
        # Check file size
        IF len(content) > MAX_FILE_SIZE:
            RAISE ValueError("File too large")
        
        # Write via MCP
        mcp.write_file(file_path, content)
        RETURN True
    
    FUNCTION run_command(command, workspace, timeout=30):
        # Sanitize command
        IF is_dangerous_command(command):
            RAISE SecurityError("Dangerous command blocked")
        
        # Execute with timeout
        result = mcp.execute_command(
            command,
            cwd=workspace,
            timeout=timeout
        )
        
        RETURN {
            "exit_code": result.exit_code,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
```

---

## Phase 2: Workspace Management ⬜

### 2.1 Setup Workspace Tool ⬜

**Implementation Details:**
- Create isolated workspace directory
- Clone repository if needed
- Set up environment

**Core Logic:**
```
FUNCTION setup_workspace(repo_path=None):
    # Create unique workspace
    workspace_id = generate_uuid()
    workspace_path = f"/tmp/workspaces/{workspace_id}"
    
    # Create directory
    os.makedirs(workspace_path, exist_ok=True)
    
    # Clone repo if provided
    IF repo_path:
        # Copy repo to workspace
        shutil.copytree(repo_path, f"{workspace_path}/repo")
        workspace_path = f"{workspace_path}/repo"
    
    # Set permissions
    os.chmod(workspace_path, 0o755)
    
    RETURN {
        "workspace_id": workspace_id,
        "workspace_path": workspace_path
    }
```

**Tool Signature:**
```python
@tool
def setup_coding_workspace(repo_path: str = None) -> str
```

---

### 2.2 Cleanup Workspace Tool ⬜

**Implementation Details:**
- Save logs before cleanup
- Remove workspace directory
- Handle cleanup errors

**Core Logic:**
```
FUNCTION cleanup_workspace(workspace_path):
    TRY:
        # Save logs if any
        log_file = f"{workspace_path}/execution.log"
        IF os.path.exists(log_file):
            save_to_persistent_storage(log_file)
        
        # Remove workspace
        shutil.rmtree(workspace_path)
        
        RETURN "✅ Workspace cleaned up"
    CATCH Exception as e:
        LOG_ERROR(f"Cleanup failed: {e}")
        RETURN f"⚠️ Cleanup warning: {e}"
```

---

## Phase 3: Code Execution ⬜

### 3.1 File Operations Tool ⬜

**Implementation Details:**
- Read, write, modify files
- Validate paths
- Handle encoding

**Core Logic:**
```
FUNCTION execute_file_operation(operation, file_path, content=None, workspace):
    # Validate path
    full_path = os.path.join(workspace, file_path)
    IF NOT is_within_workspace(full_path, workspace):
        RETURN "❌ Invalid file path"
    
    IF operation == "read":
        IF NOT os.path.exists(full_path):
            RETURN f"❌ File not found: {file_path}"
        
        content = read_file(full_path)
        RETURN f"📄 {file_path}:\n{content}"
    
    ELIF operation == "write":
        IF NOT content:
            RETURN "❌ No content provided"
        
        # Create parent directories
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Write file
        write_file(full_path, content)
        RETURN f"✅ Created/updated: {file_path}"
    
    ELIF operation == "modify":
        IF NOT os.path.exists(full_path):
            RETURN f"❌ File not found: {file_path}"
        
        # Read existing
        existing = read_file(full_path)
        
        # Apply modifications (content contains diff or new version)
        modified = apply_modifications(existing, content)
        
        # Write back
        write_file(full_path, modified)
        RETURN f"✅ Modified: {file_path}"
```

**Tool Signature:**
```python
@tool
def file_operation(operation: str, file_path: str, content: str = None, workspace: str = None) -> str
```

---

### 3.2 Execute Command Tool ⬜

**Implementation Details:**
- Run shell commands safely
- Timeout protection
- Capture output

**Core Logic:**
```
FUNCTION execute_command(command, workspace, timeout=30):
    # Sanitize command
    dangerous_patterns = [
        "rm -rf /",
        "sudo",
        "curl.*|.*bash",
        "wget.*|.*sh",
        "> /dev/",
        "mkfs",
        "dd if="
    ]
    
    FOR pattern IN dangerous_patterns:
        IF re.search(pattern, command):
            RETURN f"❌ Dangerous command blocked: {command}"
    
    # Execute with timeout
    TRY:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        output = {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
        
        IF output["success"]:
            RETURN f"✅ Command succeeded:\n{result.stdout}"
        ELSE:
            RETURN f"❌ Command failed (exit {result.returncode}):\n{result.stderr}"
            
    CATCH TimeoutExpired:
        RETURN f"❌ Command timed out after {timeout}s"
    CATCH Exception as e:
        RETURN f"❌ Error executing command: {e}"
```

**Tool Signature:**
```python
@tool
def run_command(command: str, workspace: str, timeout: int = 30) -> str
```

---

## Phase 4: Testing Integration ⬜

### 4.1 Run Tests Tool ⬜

**Implementation Details:**
- Detect test framework (pytest, jest, junit)
- Execute tests with extended timeout
- Parse test output

**Core Logic:**
```
FUNCTION run_tests(workspace, test_command=None):
    # Auto-detect test framework if not specified
    IF NOT test_command:
        IF os.path.exists(f"{workspace}/pytest.ini") OR os.path.exists(f"{workspace}/tests"):
            test_command = "pytest -v"
        ELIF os.path.exists(f"{workspace}/package.json"):
            test_command = "npm test"
        ELIF os.path.exists(f"{workspace}/pom.xml"):
            test_command = "mvn test"
        ELSE:
            RETURN "❌ Could not detect test framework"
    
    # Run tests with extended timeout
    result = execute_command(test_command, workspace, timeout=120)
    
    # Parse test output
    test_results = parse_test_output(result["stdout"], test_command)
    
    # Format results
    IF test_results["passed"] == test_results["total"]:
        status = "✅ All tests passed"
    ELSE:
        status = f"❌ {test_results['failed']} tests failed"
    
    RETURN f"""
{status}

Tests: {test_results['passed']}/{test_results['total']} passed
Duration: {test_results['duration']}

{result['stdout']}
"""
```

**Tool Signature:**
```python
@tool
def run_test_suite(workspace: str, test_command: str = None) -> str
```

---

### 4.2 Parse Test Results ⬜

**Implementation Details:**
- Parse pytest output
- Parse jest output
- Extract pass/fail counts

**Core Logic:**
```
FUNCTION parse_test_output(output, framework):
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "duration": "unknown"
    }
    
    IF "pytest" in framework:
        # Parse pytest output
        # Example: "5 passed, 2 failed in 1.23s"
        match = re.search(r'(\d+) passed', output)
        IF match:
            results["passed"] = int(match.group(1))
        
        match = re.search(r'(\d+) failed', output)
        IF match:
            results["failed"] = int(match.group(1))
        
        match = re.search(r'in ([\d.]+s)', output)
        IF match:
            results["duration"] = match.group(1)
    
    ELIF "jest" in framework OR "npm test" in framework:
        # Parse jest output
        # Example: "Tests: 2 failed, 5 passed, 7 total"
        match = re.search(r'(\d+) passed', output)
        IF match:
            results["passed"] = int(match.group(1))
        
        match = re.search(r'(\d+) failed', output)
        IF match:
            results["failed"] = int(match.group(1))
    
    results["total"] = results["passed"] + results["failed"] + results["skipped"]
    
    RETURN results
```

---

## Phase 5: Error Handling (Simplified) ⬜

**Approach:** Inline error handling with security focus

**Example:**
```python
@tool
def run_command(command: str, workspace: str, timeout: int = 30) -> str:
    # Security validation
    if any(danger in command for danger in ["rm -rf /", "sudo", "curl | bash"]):
        return "❌ Dangerous command blocked for security"
    
    # Path validation
    if not os.path.exists(workspace):
        return f"❌ Workspace not found: {workspace}"
    
    # Timeout validation
    if timeout > 300:
        return "❌ Timeout too long (max 300s)"
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            timeout=timeout,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return f"✅ Success:\n{result.stdout}"
        else:
            return f"❌ Failed (exit {result.returncode}):\n{result.stderr}"
            
    except subprocess.TimeoutExpired:
        return f"❌ Command timed out after {timeout}s"
    except Exception as e:
        return f"❌ Error: {str(e)}"
```

---

## Phase 6: Integration Testing ⬜

**Test Script:** `tests/integration/test_coding_agent.sh`

```bash
#!/bin/bash
# Integration tests for Coding Agent

authenticate --to=wealth-dev-au

USER_ID="test-user-$(date +%s)"
AGENT_ARN="arn:aws:bedrock-agentcore:ap-southeast-2:xxx:agent/coding-agent"

# Test 1: Setup workspace
echo "Test 1: Setup workspace"
agentcore invoke '{"prompt": "Setup a new workspace"}' \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"

# Test 2: Create file
echo "Test 2: Create Python file"
agentcore invoke '{
    "prompt": "Create a file hello.py with print(\"Hello World\")"
}' --user-id "$USER_ID" --agent-arn "$AGENT_ARN"

# Test 3: Run command
echo "Test 3: Run Python file"
agentcore invoke '{"prompt": "Run python hello.py"}' \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"

# Test 4: Run tests
echo "Test 4: Run test suite"
agentcore invoke '{"prompt": "Run pytest"}' \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
```

---

## Timeline Estimate

**Total: 4-5 days**

- ⬜ **Phase 1:** MCP integration + agent setup (1 day)
- ⬜ **Phase 2:** Workspace management (0.5 day)
- ⬜ **Phase 3:** Code execution (1 day)
- ⬜ **Phase 4:** Testing integration (1 day)
- ⬜ **Phase 5:** Error handling + security (0.5 day)
- ⬜ **Phase 6:** Integration testing (0.5 day)
- ⬜ **Phase 7:** Documentation (0.5 day)

---

## Dependencies

**Python Packages:**
- ✅ `bedrock-agentcore[strands-agents]>=0.1.0`
- ⬜ **MCP client library** (need to identify correct package)
- ✅ `subprocess` (built-in)

**To Research:**
- MCP (Model Context Protocol) client library
- Alternative: Use AgentCore Code Interpreter if available

---

## Success Metrics

**Functional Requirements:**
- ✅ Set up isolated workspaces
- ✅ Execute file operations safely
- ✅ Run commands with timeout
- ✅ Execute test suites
- ✅ Parse test results
- ✅ Clean up workspaces

**Security Requirements:**
- Block dangerous commands
- Validate all file paths
- Enforce timeouts
- Isolate workspaces

---

## 📝 Implementation Checklist

**Phase 1: Core Infrastructure (0% → 100%)**
- [ ] Research MCP client library
- [ ] Create `src/agents/coding_agent/runtime.py`
- [ ] Create `src/tools/coding/` directory
- [ ] Set up MCP client wrapper
- [ ] Test basic MCP operations

**Phase 2: Workspace Management (0% → 100%)**
- [ ] Create `setup_workspace` tool
- [ ] Create `cleanup_workspace` tool
- [ ] Test workspace isolation

**Phase 3: Code Execution (0% → 100%)**
- [ ] Create `file_operation` tool
- [ ] Add read/write/modify operations
- [ ] Create `run_command` tool
- [ ] Add command sanitization
- [ ] Test file operations

**Phase 4: Testing Integration (0% → 100%)**
- [ ] Create `run_test_suite` tool
- [ ] Detect test frameworks
- [ ] Parse test output
- [ ] Format results

**Phase 5: Error Handling (0% → 100%)**
- [ ] Add security validation
- [ ] Add path validation
- [ ] Add timeout protection
- [ ] Test error cases

**Phase 6: Integration Testing (0% → 100%)**
- [ ] Create test script
- [ ] Test with real code
- [ ] Verify security
- [ ] Test cleanup

**Phase 7: Documentation (0% → 100%)**
- [ ] Write API documentation
- [ ] Document security measures
- [ ] Add usage examples

---

## Notes

- **Security is critical** - validate everything
- MCP integration needs research
- Consider using AgentCore Code Interpreter as alternative
- Workspace isolation is essential
- Always clean up after execution

---

**End of Implementation Plan**

**Document Version:** 1.0  
**Status:** ⬜ Not Started  
**Estimated Effort:** 4-5 days  
**Complexity:** High (MCP integration + security)
