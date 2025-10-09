# Coding Agent

A specialized agent for executing implementation plans by safely modifying code files, running commands, and executing tests.

## Features

- **Safe Code Execution**: Sandboxed environment for running code
- **File Operations**: Read, write, and modify files with path validation
- **Command Execution**: Run shell commands with timeout and security controls
- **Test Suite Runner**: Detect and run various testing frameworks
- **Workspace Management**: Isolated workspace setup and cleanup
- **Security**: Input sanitization and resource limits

## Configuration

The agent is configured via `.bedrock_agentcore.yaml`:

```yaml
agent_name: coding-agent
agent_description: "Coding Agent for executing implementation plans"
```

## Environment Variables

- `WORKSPACE_BASE_PATH`: Base path for workspaces (default: `/tmp/workspaces`)
- `MAX_FILE_SIZE`: Maximum file size in bytes (default: `10485760` - 10MB)
- `DEFAULT_TIMEOUT`: Default command timeout in seconds (default: `30`)
- `MAX_TIMEOUT`: Maximum allowed timeout in seconds (default: `300`)

## Usage

### Local Development

```bash
# Install dependencies
uv sync

# Run the agent locally
AWS_PROFILE=mingfang uv run agentcore launch --local
```

### Docker

```bash
# Build the image
docker build -t coding-agent .

# Run the container
docker run -p 8080:8080 coding-agent
```

## Tools

### File Operations
- `read_file`: Read file contents with validation
- `write_file`: Write content to files safely
- `modify_file`: Apply targeted modifications

### Command Execution
- `execute_command`: Run shell commands with security controls
- `execute_with_timeout`: Run commands with custom timeouts

### Test Suite Runner
- `run_tests`: Detect and run test frameworks
- `parse_test_results`: Parse test output for structured results

### Workspace Management
- `setup_workspace`: Create isolated workspace
- `cleanup_workspace`: Clean up workspace resources

## Security

- Input sanitization for all file paths and commands
- Sandboxed execution environment
- Resource limits (file size, timeout, memory)
- Path traversal protection
- Command injection prevention

## Development

```bash
# Install development dependencies
uv sync --extra dev

# Run tests
pytest

# Format code
black src/
isort src/

# Type checking
mypy src/
```