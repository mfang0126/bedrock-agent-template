# Agent Migration Guide

This guide documents the process for creating new agents in the AWS AgentCore multi-agent platform, based on the successful GitHub Agent implementation pattern.

## 📋 Overview

This migration guide provides a step-by-step checklist for implementing new agents using the established GitHub Agent pattern. Each agent is designed as an independent project with its own ECR image, AgentCore Runtime instance, and configuration.

## 🏗️ GitHub Agent Pattern (Reference Implementation)

The GitHub Agent serves as our reference implementation with the following structure:

```
agents/github-agent/
├── .bedrock_agentcore.yaml     # AgentCore configuration
├── .dockerignore               # Docker ignore rules
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── Dockerfile                 # Container configuration
├── pyproject.toml             # Python project configuration
├── setup_github_provider.sh   # OAuth credential provider setup
├── src/                       # Source code
│   ├── __init__.py
│   ├── runtime.py             # AgentCore Runtime entrypoint
│   ├── common/                # Shared utilities
│   │   ├── auth/              # Authentication handling
│   │   └── config/            # Configuration management
│   └── tools/                 # Agent-specific tools
└── uv.lock                    # Dependency lock file
```

## 🚀 Agent Creation Checklist

### Phase 1: Project Structure Setup

- [ ] **Create Agent Directory**
  ```bash
  mkdir -p agents/{agent-name}
  cd agents/{agent-name}
  ```

- [ ] **Copy Base Structure from GitHub Agent**
  ```bash
  # Copy configuration files
  cp ../github-agent/.dockerignore .
  cp ../github-agent/.env.example .
  cp ../github-agent/.gitignore .
  cp ../github-agent/Dockerfile .
  cp ../github-agent/pyproject.toml .
  
  # Copy source structure
  cp -r ../github-agent/src .
  ```

- [ ] **Update pyproject.toml**
  - Change project name: `name = "{agent-name}"`
  - Update description
  - Modify dependencies as needed
  - Update entry points if applicable

### Phase 2: AgentCore Configuration

- [ ] **Generate .bedrock_agentcore.yaml using AgentCore CLI**
  ```bash
  # Generate initial configuration
  uv run agentcore configure \
    --name {agent-name} \
    --entrypoint src/runtime.py \
    --non-interactive \
    --disable-otel \
    --region ap-southeast-2
  ```

- [ ] **Test Agent Locally**
  ```bash
  # Test basic functionality
  uv run agentcore launch --local
  
  # Test with user ID (required for OAuth agents)
  uv run agentcore invoke --user-id "test-user" --message "Hello"
  ```

- [ ] **Add OAuth Configuration (if needed)**
  - For OAuth-based agents, manually add to `.bedrock_agentcore.yaml`:
  ```yaml
  oauth_configuration:
    workload_name: {agent-name}-agent-workload
    credential_providers:
    - {provider-name}
  ```

- [ ] **Update Runtime Entry Point (src/runtime.py)**
  - Modify agent description and instructions
  - Update tool imports and registrations
  - Configure authentication if needed
  - Set appropriate model and parameters

- [ ] **Verify Configuration Works**
  ```bash
  # Ensure agent launches without errors
  uv run agentcore launch --local
  
  # Test basic invocation
  uv run agentcore invoke --user-id "test-user" --message "Test configuration"
  ```

### Phase 3: Authentication Setup (If Required)

#### For OAuth-based Agents (GitHub, JIRA, etc.)

- [ ] **Create Credential Provider Setup Script**
  ```bash
  # For JIRA Agent - move existing script to agent directory
  cp scripts/setup_jira_provider.sh agents/jira-agent/
  
  # For other agents - create based on pattern
  # Example: setup_{agent}_provider.sh
  ```

- [ ] **Configure OAuth Provider**
  - Set up OAuth application (GitHub App, JIRA App, etc.)
  - Configure environment variables in `.env`:
    ```bash
    # For JIRA
    ATLASSIAN_CLIENT_ID=your_client_id
    ATLASSIAN_CLIENT_SECRET=your_client_secret
    
    # For GitHub  
    GITHUB_CLIENT_ID=your_client_id
    GITHUB_CLIENT_SECRET=your_client_secret
    ```
  - Run setup script to create credential provider:
    ```bash
    # From agent directory
    ./setup_{agent}_provider.sh
    ```
  - Add OAuth configuration to `.bedrock_agentcore.yaml`:
    ```yaml
    oauth_configuration:
      workload_name: {agent-name}-agent-workload
      credential_providers:
      - {provider-name}  # e.g., jira-provider, github-provider
    ```
  - Test OAuth flow with user ID:
    ```bash
    uv run agentcore invoke --user-id "test-user" --message "Test OAuth"
    ```

#### For API Token-based Agents

- [ ] **Configure API Token Authentication**
  - Update `src/common/auth/` modules
  - Configure token retrieval from AWS Secrets Manager
  - Update runtime.py to handle token-based auth

### Phase 4: Tool Implementation

- [ ] **Implement Agent-Specific Tools**
  - Create tool modules in `src/tools/`
  - Follow existing patterns from GitHub Agent
  - Implement error handling and logging
  - Add input validation

- [ ] **Update Tool Registration**
  - Register tools in `src/runtime.py`
  - Configure tool descriptions and parameters
  - Test tool functionality

### Phase 5: Deployment and Testing

- [ ] **Build and Deploy Agent**
  ```bash
  # From agent directory
  uv run agentcore build
  uv run agentcore deploy
  ```

- [ ] **Test Agent Functionality**
  ```bash
  # Test basic invocation
  uv run agentcore invoke --user-id "test-user" --message "Hello"
  
  # Test specific tools
  uv run agentcore invoke --user-id "test-user" --message "Test specific functionality"
  ```

- [ ] **Verify Authentication (if applicable)**
  - Test OAuth flow
  - Verify token storage and retrieval
  - Test authenticated API calls

## 🎯 Agent-Specific Implementation Plans

### Planning Agent
- **Priority**: High
- **Authentication**: None (uses Bedrock directly)
- **Key Tools**: Plan generation, validation, formatting
- **Estimated Effort**: 3-4 days

### JIRA Agent  
- **Priority**: Medium
- **Authentication**: OAuth via Atlassian (using existing `setup_jira_provider.sh`)
- **Key Tools**: Ticket operations, status updates, commenting
- **Estimated Effort**: 2-3 days
- **Setup Steps**:
  1. Move `scripts/setup_jira_provider.sh` to `agents/jira-agent/`
  2. Configure ATLASSIAN_CLIENT_ID and ATLASSIAN_CLIENT_SECRET in `.env`
  3. Run setup script to create `jira-provider`
  4. Add OAuth configuration to `.bedrock_agentcore.yaml`

### Coding Agent
- **Priority**: Medium  
- **Authentication**: None (uses MCP)
- **Key Tools**: Code generation, file operations, testing
- **Estimated Effort**: 4-5 days
- **Special Requirements**: MCP integration research needed

### Orchestrator Agent
- **Priority**: Low
- **Authentication**: None (coordinates other agents)
- **Key Tools**: Agent invocation, workflow management
- **Estimated Effort**: 3-4 days
- **Dependencies**: All other agents must be implemented first

## 🔧 Shared Resources Setup

Before creating multiple agents, ensure shared AWS resources are configured:

- [ ] **Run Shared Resources Setup**
  ```bash
  ./scripts/configure_agents.sh
  ```

- [ ] **Verify IAM Roles and Policies**
  - AgentCore execution roles
  - CodeBuild roles
  - ECR repository permissions

- [ ] **Configure Networking**
  - VPC configuration (if needed)
  - Security groups
  - Network access policies

## 📚 Reference Documentation

- **AgentCore CLI Reference**: `docs/AgentCore-CLI-Reference.md`
- **AWS AgentCore Setup**: `docs/AWS-AgentCore-Setup.md`
- **Individual Agent Plans**: `docs/{Agent}-Implementation-Plan.md`
- **Multi-Agent Workflow**: `docs/Multi-Agent-Workflow.md`

## 🚨 Common Pitfalls and Solutions

### Authentication Issues
- **Problem**: OAuth flow not working locally
- **Solution**: Ensure `--user-id` is used for OAuth-enabled agents
- **Verification**: Check credential provider configuration

### Deployment Failures
- **Problem**: ECR repository not found
- **Solution**: Run `configure_agents.sh` to create shared resources
- **Verification**: Check ECR repository exists in AWS console

### Tool Registration Errors
- **Problem**: Tools not available in agent
- **Solution**: Verify tool imports and registration in `runtime.py`
- **Verification**: Check agent logs for import errors

### Memory Configuration
- **Problem**: Agent losing context between invocations
- **Solution**: Configure memory settings in `.bedrock_agentcore.yaml`
- **Verification**: Test multi-turn conversations

## 📈 Progress Tracking

Use the following checklist to track overall implementation progress:

- [ ] **GitHub Agent** ✅ (Reference Implementation)
- [ ] **Planning Agent** (High Priority)
- [ ] **JIRA Agent** (Medium Priority)  
- [ ] **Coding Agent** (Medium Priority)
- [ ] **Orchestrator Agent** (Low Priority)

### Integration Testing
- [ ] **Individual Agent Testing**
- [ ] **Multi-Agent Workflow Testing**
- [ ] **End-to-End Integration Testing**
- [ ] **Performance and Load Testing**

## 🎉 Success Criteria

An agent implementation is considered complete when:

1. ✅ Agent builds and deploys successfully
2. ✅ Basic invocation works without errors
3. ✅ All agent-specific tools function correctly
4. ✅ Authentication works (if applicable)
5. ✅ Integration tests pass
6. ✅ Documentation is updated
7. ✅ Agent responds appropriately to test scenarios

---

**Next Steps**: Start with the Planning Agent as it has no authentication dependencies and can be implemented quickly using the GitHub Agent pattern.