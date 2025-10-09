# Agent Test Prompts

Quick reference for testing each agent with the CLI. Copy and paste these commands to test agent functionality.

---

## Coding Agent

### Test 1: Simple File Creation + Archive
```bash
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "Create a simple hello.js file that prints Hello World, then archive the session"
}' --user-id "test-$(date +%s)"
```

### Test 2: Node.js Project with Tests
```bash
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "Create a Node.js calculator project with functions for add, subtract, multiply, divide. Include tests and run them. Archive when done."
}' --user-id "test-$(date +%s)"
```

### Test 3: Clone Repository and Audit
```bash
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "Clone https://github.com/mfang0126/grab-youtube, run npm audit, and show me the results. Archive the session after."
}' --user-id "test-$(date +%s)"
```

---

## Planning Agent

### Test 1: Simple Feature Planning
```bash
cd agents/planning-agent && uv run agentcore invoke '{
  "prompt": "Create a plan to build a REST API for a todo list application"
}' --user-id "test-$(date +%s)"
```

### Test 2: Complex Project Planning
```bash
cd agents/planning-agent && uv run agentcore invoke '{
  "prompt": "Plan the implementation of a user authentication system with OAuth 2.0, including database schema, API endpoints, and security considerations"
}' --user-id "test-$(date +%s)"
```

### Test 3: Migration Planning
```bash
cd agents/planning-agent && uv run agentcore invoke '{
  "prompt": "Create a phased plan to migrate a monolithic Node.js application to microservices architecture"
}' --user-id "test-$(date +%s)"
```

---

## GitHub Agent

### Test 1: Create Issue
```bash
cd agents/github-agent && uv run agentcore invoke '{
  "prompt": "Create a GitHub issue titled \"Add unit tests for calculator module\" with description explaining we need comprehensive test coverage"
}' --user-id "test-$(date +%s)"
```

### Test 2: List Recent Issues
```bash
cd agents/github-agent && uv run agentcore invoke '{
  "prompt": "List the 5 most recent issues in the repository, showing their status and labels"
}' --user-id "test-$(date +%s)"
```

### Test 3: Create Pull Request
```bash
cd agents/github-agent && uv run agentcore invoke '{
  "prompt": "Create a pull request from feature/auth-improvements to main with title \"Improve OAuth authentication flow\" and detailed description"
}' --user-id "test-$(date +%s)"
```

---

## JIRA Agent

### Test 1: Create Simple Task
```bash
cd agents/jira-agent && uv run agentcore invoke '{
  "prompt": "Create a JIRA task titled \"Update API documentation\" with description about documenting new endpoints"
}' --user-id "test-$(date +%s)"
```

### Test 2: Create Bug with Details
```bash
cd agents/jira-agent && uv run agentcore invoke '{
  "prompt": "Create a bug ticket for \"Login page not loading on mobile devices\" with high priority and detailed reproduction steps"
}' --user-id "test-$(date +%s)"
```

### Test 3: List Sprint Tasks
```bash
cd agents/jira-agent && uv run agentcore invoke '{
  "prompt": "Show me all tasks in the current sprint, grouped by status"
}' --user-id "test-$(date +%s)"
```

---

## Orchestrator Agent

### Test 1: Simple Multi-Agent Workflow
```bash
cd agents/orchestrator-agent && uv run agentcore invoke '{
  "prompt": "Create a simple Express hello world app and create a GitHub issue to track it"
}' --user-id "test-$(date +%s)"
```

### Test 2: Full Development Workflow
```bash
cd agents/orchestrator-agent && uv run agentcore invoke '{
  "prompt": "Plan and create a Node.js REST API for a todo list, run tests, create a GitHub issue, and create a JIRA ticket for deployment. Archive when done."
}' --user-id "test-$(date +%s)"
```

### Test 3: Dependency Audit Workflow
```bash
cd agents/orchestrator-agent && uv run agentcore invoke '{
  "prompt": "Clone the grab-youtube repository, run dependency audit, fix any vulnerabilities, create a GitHub issue with results, and create a JIRA ticket if manual fixes are needed"
}' --user-id "test-$(date +%s)"
```

---

## Session Management (Coding Agent)

### Test 1: List Archived Sessions
```bash
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "List all archived sessions and show me their details"
}' --user-id "test-$(date +%s)"
```

### Test 2: Archive Current Session
```bash
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "Archive the current session with name express_app_v1"
}' --user-id "test-$(date +%s)"
```

### Test 3: Restore Previous Session
```bash
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "Restore the most recent archived session"
}' --user-id "test-$(date +%s)"
```

---

## Progress Streaming Verification

### Test: Long-Running Operation
```bash
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "Create a Node.js project with Express, install all dependencies, create 5 endpoint files, write tests for each, run the test suite, and archive the session. Show progress at each step."
}' --user-id "test-$(date +%s)"
```

**Expected Output Pattern:**
```
🔍 Starting...
  → Sub-step 1...
  ✓ Complete

📦 Operation 2...
  → Sub-step...
  ✓ Complete

✅ All done!
```

---

## Quick Test Script

Save this as `test-agents.sh` for quick testing:

```bash
#!/bin/bash

# Test Coding Agent
echo "🔍 Testing Coding Agent..."
cd agents/coding-agent && uv run agentcore invoke '{
  "prompt": "Create hello.js with Hello World and archive"
}' --user-id "test-coding-$(date +%s)"

# Test Planning Agent
echo "🔍 Testing Planning Agent..."
cd agents/planning-agent && uv run agentcore invoke '{
  "prompt": "Plan a REST API for todo list"
}' --user-id "test-planning-$(date +%s)"

# Test GitHub Agent
echo "🔍 Testing GitHub Agent..."
cd agents/github-agent && uv run agentcore invoke '{
  "prompt": "List recent issues"
}' --user-id "test-github-$(date +%s)"

# Test JIRA Agent
echo "🔍 Testing JIRA Agent..."
cd agents/jira-agent && uv run agentcore invoke '{
  "prompt": "Create a task for API documentation"
}' --user-id "test-jira-$(date +%s)"

# Test Orchestrator
echo "🔍 Testing Orchestrator..."
cd agents/orchestrator-agent && uv run agentcore invoke '{
  "prompt": "Create Express app and GitHub issue"
}' --user-id "test-orchestrator-$(date +%s)"

echo "✅ All agent tests complete!"
```

---

## Environment Setup

Before running tests, ensure:

1. **AWS Credentials**
```bash
aws_use mingfang
```

2. **GitHub Token** (for github-agent)
```bash
export GITHUB_TOKEN="your_github_token"
```

3. **JIRA OAuth** (for jira-agent)
```bash
# Configured in .bedrock_agentcore.yaml
```

---

## Expected Response Times

| Agent | Simple Task | Complex Task |
|-------|------------|--------------|
| Coding Agent | 5-10s | 30-60s |
| Planning Agent | 3-5s | 10-15s |
| GitHub Agent | 2-5s | 5-10s |
| JIRA Agent | 3-7s | 10-15s |
| Orchestrator | 10-20s | 60-120s |

---

## Troubleshooting

### If agent doesn't respond:
```bash
# Check agent status
uv run agentcore status --agent <agent-name>

# Check CloudWatch logs
aws logs tail /aws/bedrock-agentcore/runtimes/<agent-arn> --follow
```

### If authentication fails:
```bash
# Verify credentials
aws sts get-caller-identity

# Check GitHub token
echo $GITHUB_TOKEN

# Verify JIRA OAuth in .bedrock_agentcore.yaml
```

---

## Copy-Paste Quick Tests

### Minimal Test (Single Agent)
```bash
cd agents/coding-agent && uv run agentcore invoke '{"prompt": "Create hello.js"}' --user-id "test-$(date +%s)"
```

### Medium Test (Two Agents)
```bash
cd agents/orchestrator-agent && uv run agentcore invoke '{"prompt": "Create Express app and GitHub issue"}' --user-id "test-$(date +%s)"
```

### Full Test (All Agents)
```bash
cd agents/orchestrator-agent && uv run agentcore invoke '{"prompt": "Plan, create, test Node.js app. Create GitHub issue and JIRA ticket. Archive session."}' --user-id "test-$(date +%s)"
```
