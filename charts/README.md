# Agent System Flow Charts

This directory contains Mermaid flow charts documenting the agent system architecture, workflows, and capabilities.

## Chart Overview

### 1. Orchestrator Overview (`01-orchestrator-overview.mmd`)
**Purpose:** High-level view of how the Orchestrator Agent coordinates all other agents

**Shows:**
- Main orchestrator entry point
- Task analysis and routing logic
- All available agents and their tool categories
- Sequential workflow execution for complex tasks

**Use Case:** Understanding the overall system and how agents are selected

---

### 2. Dependency Check Workflow (`02-dependency-check-workflow.mmd`)
**Purpose:** Detailed workflow for security audit and dependency checking

**Shows:**
- Step-by-step process from user request to completion
- Integration between GitHub, Coding, and Jira agents
- Vulnerability detection and fixing process
- Issue tracking and status updates

**Use Case:** Understanding how the system handles security audits and dependency management

---

### 3. Feature Development Workflow (`03-feature-development-workflow.mmd`)
**Purpose:** Complete feature development lifecycle

**Shows:**
- Planning phase with task breakdown
- GitHub issue creation for tracking
- Code implementation with testing
- Pull request creation
- Jira ticket updates

**Use Case:** Understanding end-to-end feature development from planning to PR

---

### 4. Planning Agent Detail (`04-planning-agent-detail.mmd`)
**Purpose:** Deep dive into Planning Agent capabilities

**Shows:**
- `breakdown_task` tool functionality
- Different plan types (Security vs Feature)
- Phase structures and task lists
- Dependencies and effort estimation

**Use Case:** Understanding task planning and breakdown capabilities

---

### 5. GitHub Agent Detail (`05-github-agent-detail.mmd`)
**Purpose:** Deep dive into GitHub Agent capabilities

**Shows:**
- Issue management tools (list, create, close, comment, update)
- Pull request operations (create, list, merge)
- Repository information queries
- GitHub API authentication

**Use Case:** Understanding GitHub integration capabilities

---

### 6. Jira Agent Detail (`06-jira-agent-detail.mmd`)
**Purpose:** Deep dive into Jira Agent capabilities

**Shows:**
- Ticket fetching and parsing
- Smart extraction of acceptance criteria
- Sprint management
- Status updates and GitHub linking

**Use Case:** Understanding Jira integration and project tracking capabilities

---

### 7. Coding Agent Detail (`07-coding-agent-detail.mmd`)
**Purpose:** Deep dive into Coding Agent capabilities

**Shows:**
- File operations (read, write, modify)
- Command execution with timeout controls
- Multi-framework test runner
- Workspace management
- MCP client integration
- Security features (sanitization, sandboxing, validation)

**Use Case:** Understanding code execution and testing capabilities

---

### 8. Usage Scenarios (`08-usage-scenarios.mmd`)
**Purpose:** Common use cases and workflows

**Shows:**
- 5 typical scenarios:
  1. Security Audit
  2. Feature Development
  3. Bug Fix
  4. Code Review
  5. Sprint Planning
- Agent combinations for each scenario
- Step-by-step flows

**Use Case:** Understanding practical applications and which agents work together

---

### 9. System Architecture (`09-system-architecture.mmd`)
**Purpose:** Technical architecture and communication patterns

**Shows:**
- Task analysis engine and routing
- Inter-agent communication (subprocess calls)
- Security layer (validation, auth, rate limiting)
- Configuration management
- API integrations

**Use Case:** Understanding system design and technical implementation

---

## Viewing the Charts

### Online Viewers
1. **Mermaid Live Editor:** https://mermaid.live/
   - Copy and paste the mermaid code
   - View and edit interactively

2. **GitHub/GitLab:**
   - These files render automatically in GitHub/GitLab markdown viewers

3. **VS Code:**
   - Install "Markdown Preview Mermaid Support" extension
   - Open .mmd file and use preview

### Command Line
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Generate PNG/SVG from .mmd file
mmdc -i 01-orchestrator-overview.mmd -o 01-orchestrator-overview.png
```

## Agent Capabilities Summary

| Agent | Primary Purpose | Key Tools | External Dependencies |
|-------|----------------|-----------|----------------------|
| **Orchestrator** | Coordinate agents, route tasks | Task analysis, workflow execution | All other agents |
| **Planning** | Task breakdown, planning | breakdown_task | None |
| **GitHub** | Repository & issue management | Issue/PR/repo operations | GitHub API |
| **Jira** | Project tracking | Ticket fetch/update, sprint management | Jira API |
| **Coding** | Code execution & testing | File ops, command exec, test runner | Local system |

## Key Workflows

1. **Security Audit Flow:** User → Orchestrator → Coding (audit) → GitHub (issue) → Jira (update)

2. **Feature Development:** User → Orchestrator → Planning (breakdown) → GitHub (issues) → Coding (implement) → Coding (test) → GitHub (PR) → Jira (done)

3. **Bug Fix:** User → Orchestrator → GitHub (fetch) → Coding (fix + test) → GitHub (update/PR)

## Color Coding

- 🌸 **Pink (#ffb6c1):** Orchestrator Agent
- 🌊 **Turquoise (#98d8c8):** Planning Agent  
- 💠 **Sky Blue (#87ceeb):** GitHub Agent
- 🔮 **Plum (#dda0dd):** Jira Agent
- 🧡 **Sandy Brown (#f4a460):** Coding Agent
- 🔥 **Light Coral (#ffa07a):** Complex/Sequential Workflows

## Notes

- All agents communicate through the Orchestrator via subprocess calls
- Agents are stateless - each invocation is independent
- Security is enforced at multiple layers (input validation, sandboxing, rate limiting)
- Authentication is managed via environment variables and configuration files
- Error handling includes graceful fallbacks when agents are unavailable

## Updates

Last updated: 2025-10-10

For questions or updates, refer to the main project README or individual agent documentation.
