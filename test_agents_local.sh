#!/bin/bash

# Test agents locally before deployment

set -e

echo "=========================================="
echo "🧪 Local Agent Testing"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to test an agent
test_agent() {
    local agent_name=$1
    local agent_dir=$2
    local test_prompt=$3
    
    echo -e "${BLUE}Testing ${agent_name} Agent${NC}"
    echo "────────────────────────────────────────"
    echo "📁 Directory: ${agent_dir}"
    echo "💬 Prompt: ${test_prompt}"
    echo ""
    
    cd "${agent_dir}"
    
    # Create payload
    PAYLOAD=$(cat <<EOF
{
  "prompt": "$test_prompt"
}
EOF
)
    
    echo -e "${YELLOW}🚀 Running local test...${NC}"
    echo ""
    
    # Test with local runtime
    if uv run agentcore invoke "$PAYLOAD" --user-id "test-local" 2>&1; then
        echo ""
        echo -e "${GREEN}✅ ${agent_name} test passed${NC}"
        return 0
    else
        echo ""
        echo -e "${RED}❌ ${agent_name} test failed${NC}"
        return 1
    fi
}

# Test GitHub Agent
echo "1️⃣  GitHub Agent Test"
echo "=========================================="
if test_agent "GitHub" \
    "${SCRIPT_DIR}/agents/github-agent" \
    "what can you do"; then
    GITHUB_TEST=true
else
    GITHUB_TEST=false
fi

echo ""
echo ""

# Test Jira Agent  
echo "2️⃣  Jira Agent Test"
echo "=========================================="
if test_agent "Jira" \
    "${SCRIPT_DIR}/agents/jira-agent" \
    "what can you do"; then
    JIRA_TEST=true
else
    JIRA_TEST=false
fi

echo ""
echo ""

# Summary
echo "=========================================="
echo "📊 Test Summary"
echo "=========================================="

if [ "$GITHUB_TEST" = true ]; then
    echo -e "✅ GitHub Agent: ${GREEN}PASSED${NC}"
else
    echo -e "❌ GitHub Agent: ${RED}FAILED${NC}"
fi

if [ "$JIRA_TEST" = true ]; then
    echo -e "✅ Jira Agent: ${GREEN}PASSED${NC}"
else
    echo -e "❌ Jira Agent: ${RED}FAILED${NC}"
fi

echo ""

# Final verdict
if [ "$GITHUB_TEST" = true ] && [ "$JIRA_TEST" = true ]; then
    echo -e "${GREEN}🎉 All tests passed! Ready to deploy.${NC}"
    echo ""
    echo "Run: ./deploy_agents.sh to deploy to AWS"
    exit 0
else
    echo -e "${RED}⚠️  Some tests failed. Fix issues before deploying.${NC}"
    echo ""
    echo "Check the output above for error details."
    exit 1
fi
