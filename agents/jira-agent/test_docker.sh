#!/bin/bash
set -e

echo "🧪 Testing JIRA Agent Docker image..."

# Run container with test environment
docker run --rm \
  --platform linux/arm64 \
  -e AGENT_ENV=local \
  -e LOG_LEVEL=DEBUG \
  -e JIRA_URL=https://test.atlassian.net \
  jira-agent:latest \
  python -c "
import sys
sys.path.insert(0, '/app')
from src.agent import create_jira_agent
from src.auth.mock import MockJiraAuth

# Test agent creation
auth = MockJiraAuth(base_url='https://test.atlassian.net')
agent = create_jira_agent(auth)
print('✅ Agent creation successful!')
print(f'📦 Tools: {len(agent.tools)} registered')
"

echo "✅ Docker image tests passed!"
