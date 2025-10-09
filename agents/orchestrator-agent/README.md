# Master Orchestrator Agent

Intelligent orchestrator that coordinates multiple specialized agents to accomplish complex tasks.

## Overview

The Master Orchestrator Agent analyzes tasks and delegates work to the appropriate specialized agents:

- **Coding Agent**: Code execution, dependency management, testing, workspace operations
- **GitHub Agent**: GitHub operations (issues, commits, PRs, repository management)
- **Jira Agent**: Project tracking, sprint management, team communication
- **Planning Agent**: Task breakdown, implementation planning, architecture design

## Key Features

- **Intelligent Task Analysis**: Automatically determines which agents to use based on task content
- **Multi-Agent Coordination**: Orchestrates complex workflows across multiple agents
- **Sequential Workflow Execution**: Manages task dependencies and execution order
- **Error Handling**: Graceful fallbacks when agents are unavailable
- **Flexible Agent Calling**: Multiple methods to invoke agents based on availability

## Architecture

The orchestrator uses a simple but effective architecture:

1. **Task Analysis**: Examines the request to identify required agents
2. **Agent Selection**: Chooses appropriate agents based on keywords and context
3. **Sequential Execution**: Runs agents in logical order for complex workflows
4. **Result Aggregation**: Combines outputs from multiple agents

## How It Works

### Task Detection

The orchestrator analyzes tasks for keywords to determine routing:

- **Dependency tasks**: "dependency", "audit", "vulnerability", "npm", "yarn"
  - Routes to: GitHub → Coding → Jira
- **Planning tasks**: "plan", "breakdown", "design", "architect"
  - Routes to: Planning
- **GitHub tasks**: "github", "issue", "pull request", "commit"
  - Routes to: GitHub
- **Jira tasks**: "jira", "ticket", "sprint", "story"
  - Routes to: Jira
- **Coding tasks**: "code", "run", "execute", "test", "debug"
  - Routes to: Coding

### Workflow Example: Dependency Check

For a request like "Check dependencies for my project", the orchestrator:

1. Creates a GitHub issue for tracking
2. Runs dependency audit via Coding agent
3. Attempts to fix vulnerabilities
4. Creates detailed issue if fixes fail
5. Updates Jira with final status

## Usage Examples

### Basic Request
```
"Check dependencies for /Users/mingfang/Code/grab-youtube"
```

### Complex Workflow
```
"Plan and implement a new authentication feature, create GitHub issues for each task"
```

### Direct Agent Call
```
"Create a GitHub issue for the video optimization feature"
```

## Testing

### Standalone Test
Test the orchestrator logic without dependencies:
```bash
python test_standalone.py
```

### Full Test Suite
Run complete agent coordination tests:
```bash
python test_orchestrator.py
```

### Grab-YouTube Example
Test with your specific project:
```bash
python example_grab_youtube.py
```

### Custom Prompt
Test with any prompt:
```bash
python test_orchestrator.py "Your custom task here"
```

## Installation

The orchestrator requires minimal setup:
```bash
cd agents/orchestrator-agent
# Ensure bedrock-agentcore is installed
pip install bedrock-agentcore
```

## Agent Communication

The orchestrator communicates with agents through subprocess calls, trying multiple methods:

1. AgentCore CLI invoke
2. Direct runtime.py execution
3. Standard agentcore invoke

This ensures compatibility with different agent implementations.

## Workflow Capabilities

### Dependency Management Workflow
- Automated vulnerability scanning
- Progressive fix attempts
- Issue creation for blockers
- Project tracking updates

### Feature Development Workflow
- Task breakdown via Planning agent
- Issue creation via GitHub agent
- Code implementation via Coding agent
- Progress tracking via Jira agent

## Dependencies

- bedrock-agentcore[strands-agents]
- bedrock-agentcore-starter-toolkit
- Python 3.8+

## File Structure

```
orchestrator-agent/
├── src/
│   └── runtime.py          # Main orchestrator implementation
├── test_orchestrator.py    # Test suite
├── test_standalone.py      # Standalone logic test
├── example_grab_youtube.py # Specific use case example
├── pyproject.toml          # Project configuration
└── README.md              # This file
```

## How Agents Are Coordinated

1. **Task Reception**: Orchestrator receives a high-level task
2. **Analysis**: Task is analyzed for keywords and intent
3. **Planning**: Workflow steps are determined
4. **Execution**: Agents are called in sequence
5. **Aggregation**: Results are combined and returned

## Benefits

- **No Complex Dependencies**: Simple subprocess-based coordination
- **Flexible Integration**: Works with different agent implementations
- **Intelligent Routing**: Automatic agent selection based on task
- **Error Resilience**: Continues even if some agents fail
- **Easy to Extend**: Add new agents by updating the routing logic

## Troubleshooting

If agents aren't responding:
1. Check agent directories exist
2. Verify runtime.py files are present
3. Ensure Python environment is activated
4. Check agent-specific dependencies

## Future Enhancements

- Parallel agent execution for independent tasks
- State persistence across workflow steps
- Dynamic workflow generation based on agent responses
- Real-time progress tracking
- Advanced retry and fallback strategies
