# Coding Agent AgentCore

Multi-agent system for software development automation on AWS Bedrock AgentCore.

## Quick Start

```bash
# Test agents locally (no AWS required)
make test-all

# Deploy to AWS
make setup
make deploy

# Test deployed agents
make invoke-coding
```

## Project Structure

```
agents/
├── coding-agent/         # Code generation and file operations
├── github-agent/         # GitHub repository management
├── jira-agent/          # JIRA project management
├── orchestrator-agent/  # Multi-agent coordination
└── planning-agent/      # Task planning and breakdown

scripts/
├── invoke_*.sh          # AWS deployment testing
├── test_*_local.py      # Local testing scripts
└── setup*.sh            # Deployment automation

docs/
├── TESTING.md           # Testing guide
├── DEPLOYMENT_GUIDE.md  # Deployment instructions
└── INVOCATION.md        # Agent invocation reference
```

## Available Commands

```bash
make help              # Show all commands

# Local Testing (fast, no AWS)
make test-coding       # Test Coding agent
make test-github       # Test GitHub agent (mock)
make test-jira         # Test JIRA agent (mock)
make test-all          # Test all agents

# AWS Testing (requires deployment)
make invoke-coding     # Invoke deployed Coding agent
make invoke-github     # Invoke deployed GitHub agent
make invoke-jira       # Invoke deployed JIRA agent

# Deployment
make setup             # Setup AWS resources
make deploy            # Deploy all agents
make deploy-agent A=<name>  # Deploy specific agent

# Utilities
make status            # Show agent status
make clean             # Clean temporary files
```

## Documentation

- **[TESTING.md](TESTING.md)** - Complete testing guide (local + AWS)
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - AWS deployment instructions
- **[INVOCATION.md](INVOCATION.md)** - Agent invocation reference
- **[scripts/README.md](scripts/README.md)** - Scripts documentation

## Key Features

### Local Development
- ✅ Test agents locally without AWS deployment
- ✅ Mock authentication for GitHub/JIRA (no OAuth needed)
- ✅ Fast iteration cycle
- ✅ Structure and logic testing

### AWS Deployment
- ✅ Production-ready multi-agent system
- ✅ OAuth 2.0 / 3LO for GitHub and JIRA
- ✅ Shared AWS resources (IAM, ECR, Memory)
- ✅ Real API integration testing

### Agent Capabilities

**Coding Agent:**
- Create workspaces and projects
- Read, write, and modify files
- Execute code and run tests
- Project structure analysis

**GitHub Agent:**
- Repository management
- Issue creation and updates
- Pull request operations
- OAuth 3-Legged authentication

**JIRA Agent:**
- Project and issue management
- Status updates and transitions
- Search and filtering
- OAuth 2.0 authentication

**Orchestrator Agent:**
- Multi-agent coordination
- Task delegation
- Workflow management
- Agent-to-agent communication

**Planning Agent:**
- Task breakdown and planning
- Dependency analysis
- Resource estimation
- Implementation roadmaps

## Technology Stack

- **Language:** Python 3.10+
- **Framework:** [Strands Agents](https://strandsagents.com)
- **Runtime:** AWS Bedrock AgentCore
- **Model:** Claude 3.5 Sonnet
- **Region:** ap-southeast-2 (Sydney)
- **Package Manager:** uv
- **Container:** Docker (ARM64)

## Getting Started

### 1. Local Testing (No AWS Required)

```bash
# Install dependencies
uv sync

# Test an agent locally
make test-coding

# Or use direct command
uv run scripts/test_coding_local.py 'create a hello world script'
```

### 2. AWS Deployment

```bash
# Setup AWS resources (one-time)
make setup

# Deploy all agents (~60-75 minutes)
make deploy

# Test deployed agent
make invoke-coding
```

### 3. Development Workflow

```bash
# 1. Develop locally
make test-coding

# 2. Deploy specific agent
make deploy-agent A=coding

# 3. Test in AWS
make invoke-coding

# 4. Check status
make status
```

## Requirements

- AWS CLI configured
- Python 3.10+
- `uv` package manager ([install](https://docs.astral.sh/uv/))
- Docker (for deployment)
- `make` (usually pre-installed)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

## Architecture

### Shared Resources
- **IAM Role:** Single execution role for all agents
- **ECR Repository:** Shared container registry (per-agent tags)
- **Memory:** STM_ONLY mode with shared context

### Agent Isolation
- Separate runtime instances per agent
- Unique ARNs and session management
- Independent scaling and deployment

### Communication Patterns
- **Client Mode:** Streaming text for human interaction
- **Agent Mode:** Structured JSON for A2A communication
- **OAuth:** Callback-based token management

## Contributing

1. Test changes locally first (`make test-all`)
2. Follow existing code patterns
3. Update documentation as needed
4. Deploy and test in AWS before committing

## License

[Add license information]

## Support

For issues or questions:
1. Check [TESTING.md](TESTING.md) for common problems
2. Review logs: `uv run agentcore logs --agent <name> --follow`
3. Check agent status: `make status`
