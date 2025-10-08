#!/bin/bash
# Integration tests for GitHub Agent
# Must run with: authenticate --to=wealth-dev-au && ./tests/integration/test_github_agent.sh

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
AGENT_ARN="${AGENT_ARN:-arn:aws:bedrock-agentcore:ap-southeast-2:xxx:agent/github-agent}"
USER_ID="test-user-$(date +%s)"
TEST_REPO="${TEST_REPO:-your-org/test-repo}"

echo -e "${YELLOW}=== GitHub Agent Integration Tests ===${NC}"
echo "Agent ARN: $AGENT_ARN"
echo "User ID: $USER_ID"
echo "Test Repo: $TEST_REPO"
echo ""

# Test 1: List repositories
echo -e "${YELLOW}Test 1: List repositories${NC}"
agentcore invoke '{"prompt": "list my repositories"}' \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
echo -e "${GREEN}✓ Test 1 passed${NC}\n"

# Test 2: Get repo info
echo -e "${YELLOW}Test 2: Get repository info${NC}"
agentcore invoke "{\"prompt\": \"get info about $TEST_REPO\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
echo -e "${GREEN}✓ Test 2 passed${NC}\n"

# Test 3: List issues
echo -e "${YELLOW}Test 3: List issues${NC}"
agentcore invoke "{\"prompt\": \"list issues in $TEST_REPO\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
echo -e "${GREEN}✓ Test 3 passed${NC}\n"

# Test 4: Create issue
echo -e "${YELLOW}Test 4: Create issue${NC}"
agentcore invoke "{\"prompt\": \"create an issue in $TEST_REPO titled 'Integration Test Issue' with body 'This is a test'\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
echo -e "${GREEN}✓ Test 4 passed${NC}\n"

# Test 5: Post comment (requires issue number from previous test)
echo -e "${YELLOW}Test 5: Post comment on issue${NC}"
agentcore invoke "{\"prompt\": \"comment on issue #1 in $TEST_REPO: 'Integration test comment'\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
echo -e "${GREEN}✓ Test 5 passed${NC}\n"

# Test 6: Close issue
echo -e "${YELLOW}Test 6: Close issue${NC}"
agentcore invoke "{\"prompt\": \"close issue #1 in $TEST_REPO\"}" \
  --user-id "$USER_ID" \
  --agent-arn "$AGENT_ARN"
echo -e "${GREEN}✓ Test 6 passed${NC}\n"

echo -e "${GREEN}=== All tests passed! ===${NC}"
