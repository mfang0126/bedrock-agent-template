# Coding Agent Setup Guide

## Overview

The Coding Agent executes implementation plans by modifying code files, running commands, and executing tests in isolated workspaces.

## Prerequisites

1. AWS credentials configured (`aws_use mingfang`)
2. AgentCore CLI installed
3. Coding agent added to `.bedrock_agentcore.yaml`

## AgentCore Configuration

Add this to your `.bedrock_agentcore.yaml` file:

```yaml
agents:
  # ... existing agents ...

  coding_agent:
    name: coding_agent
    entrypoint: src/agents/coding_agent/runtime.py
    platform: linux/arm64
    container_runtime: docker
    aws:
      execution_role: arn:aws:iam::670326884047:role/AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-d92c6a81b2
      execution_role_auto_create: true
      account: '670326884047'
      region: ap-southeast-2
      ecr_repository: 670326884047.dkr.ecr.ap-southeast-2.amazonaws.com/bedrock-agentcore-coding_agent
      ecr_auto_create: false
      network_configuration:
        network_mode: PUBLIC
      protocol_configuration:
        server_protocol: HTTP
      observability:
        enabled: true
    authorizer_configuration: null
    request_header_configuration: null
    oauth_configuration: null
```

## Deployment

1. **Create ECR repository first** (if not exists):
```bash
aws ecr create-repository --repository-name bedrock-agentcore-coding_agent --region ap-southeast-2
```

2. **Deploy the agent:**
```bash
aws_use mingfang && uv run poe deploy-coding
```

3. **Test the agent:**
```bash
# Setup workspace
uv run poe invoke-coding '{
  "prompt": "Setup a new workspace"
}' --user-id "test"

# Create a file
uv run poe invoke-coding '{
  "prompt": "Create a file hello.py with print(\"Hello World\")"
}' --user-id "test"

# Run a command
uv run poe invoke-coding '{
  "prompt": "Run python hello.py"
}' --user-id "test"
```

## Available Tools

### 1. setup_coding_workspace
Set up an isolated workspace for code execution.

**Example:** "Setup a new workspace"

**With repo:** "Setup workspace and copy from /path/to/repo"

### 2. cleanup_coding_workspace
Clean up a workspace after execution.

**Example:** "Cleanup workspace /tmp/coding_workspaces/abc-123"

### 3. read_file
Read a file from the workspace.

**Example:** "Read file src/main.py from workspace"

### 4. write_file
Write content to a file in the workspace.

**Example:** "Write 'print(\"hello\")' to hello.py"

### 5. modify_file
Modify a file by replacing content.

**Example:** "In file config.py, replace 'DEBUG = False' with 'DEBUG = True'"

### 6. list_files
List files and directories in the workspace.

**Example:** "List files in src/ directory"

### 7. run_command
Execute a shell command in the workspace.

**Example:** "Run npm install"

**Example:** "Run python -m pytest tests/"

### 8. run_test_suite
Run test suite with auto-detection of test framework.

**Example:** "Run tests"

**Example:** "Run tests with command 'pytest -v'"

## Security Features

### Dangerous Command Blocking
Automatically blocks dangerous commands:
- `rm -rf /`
- `sudo` commands
- `curl | bash` / `wget | sh`
- Fork bombs
- `chmod 777`
- Disk operations (`mkfs`, `dd`)

### File Path Validation
- All file paths validated to be within workspace
- No directory traversal attacks (`../../../etc/passwd`)
- File size limits (10MB max)

### Command Timeout Protection
- Default timeout: 30 seconds
- Maximum timeout: 300 seconds (5 minutes)
- Long-running tests can use extended timeout

### Workspace Isolation
- Each execution in isolated workspace: `/tmp/coding_workspaces/{uuid}`
- Workspaces cleaned up after execution
- No system-wide changes possible

## Test Framework Auto-Detection

The agent automatically detects test frameworks:

- **pytest**: Looks for `pytest.ini` or `tests/` directory
- **Jest/npm**: Looks for `package.json`
- **Maven**: Looks for `pom.xml`
- **RSpec**: Looks for `Gemfile`

Manual override: `"Run tests with command 'pytest -v'"`

## Example Workflows

### Execute Implementation Plan

```bash
uv run poe invoke-coding '{
  "prompt": "Execute this implementation plan",
  "plan": {
    "steps": [
      "Create file auth.py with authentication logic",
      "Write tests in test_auth.py",
      "Run pytest to validate"
    ],
    "files_to_modify": ["auth.py", "test_auth.py"]
  }
}' --user-id "test"
```

### Modify Existing Code

```bash
uv run poe invoke-coding '{
  "prompt": "In file config.py, change DEBUG = False to DEBUG = True, then run tests"
}' --user-id "test"
```

### Run Tests and Parse Results

```bash
uv run poe invoke-coding '{
  "prompt": "Run the test suite and show me the results"
}' --user-id "test"
```

## Integration with Other Agents

### With Planning Agent
```bash
# 1. Planning Agent creates implementation plan
uv run poe invoke-planning '{
  "prompt": "Create implementation plan for user authentication"
}' --user-id "test"

# 2. Coding Agent executes the plan
uv run poe invoke-coding '{
  "prompt": "Execute the plan from Planning Agent",
  "plan": {...}
}' --user-id "test"
```

### With JIRA Agent
```bash
# 1. JIRA Agent fetches requirements
uv run poe invoke-jira '{
  "prompt": "Parse requirements from PROJ-123"
}' --user-id "test"

# 2. Planning Agent creates plan
uv run poe invoke-planning '{
  "prompt": "Create plan for: [requirements]"
}' --user-id "test"

# 3. Coding Agent implements
uv run poe invoke-coding '{
  "prompt": "Execute the implementation plan"
}' --user-id "test"

# 4. JIRA Agent updates ticket
uv run poe invoke-jira '{
  "prompt": "Add comment to PROJ-123: Implementation complete"
}' --user-id "test"
```

## CloudWatch Logs

Monitor Coding Agent execution:
```bash
aws logs tail /aws/bedrock-agentcore/runtimes/coding_agent-*/DEFAULT \
  --log-stream-name-prefix "2025/10/08/[runtime-logs]" \
  --follow
```

## Troubleshooting

### Error: "Agent 'coding_agent' not found"
- Make sure you added the coding_agent configuration to `.bedrock_agentcore.yaml`
- The file is gitignored, so you need to add it manually

### Error: "Repository does not exist"
- Create ECR repository first: `aws ecr create-repository --repository-name bedrock-agentcore-coding_agent`

### Error: "Command blocked for security"
- The agent blocks dangerous commands for safety
- Review the security features section above
- Use safer alternatives or contact admin for exceptions

### Error: "Workspace not found"
- Make sure to setup workspace first with `setup_coding_workspace`
- Workspace paths must be within `/tmp/coding_workspaces/`

### Error: "File too large"
- Maximum file size is 10MB
- For larger files, consider splitting or streaming

## Limitations

- Maximum file size: 10MB
- Maximum command timeout: 300 seconds
- Workspace isolation: Cannot access files outside workspace
- No network access restrictions (yet)
- No persistent storage (workspaces are temporary)

## Next Steps

After Coding Agent is working:
1. ✅ Test all tools with real code execution
2. ⬜ Implement Orchestrator Agent
3. ⬜ Test end-to-end workflow: JIRA → Planning → Coding → JIRA update
4. ⬜ Add integration tests
5. ⬜ Consider adding network isolation
6. ⬜ Add persistent workspace option
