#!/bin/bash

# Deploy GitHub and Jira agents to AWS AgentCore

set -e  # Exit on error

echo "=========================================="
echo "🚀 Deploying Agents to AWS AgentCore"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to deploy an agent
deploy_agent() {
    local agent_name=$1
    local agent_dir=$2
    
    echo -e "${BLUE}📦 Deploying ${agent_name} agent...${NC}"
    echo "   Directory: ${agent_dir}"
    
    cd "${agent_dir}"
    
    # Check if .bedrock_agentcore.yaml exists
    if [ ! -f ".bedrock_agentcore.yaml" ]; then
        echo -e "${RED}❌ Error: .bedrock_agentcore.yaml not found${NC}"
        return 1
    fi
    
    # Deploy using agentcore
    echo "   Running: agentcore launch"
    if agentcore launch; then
        echo -e "${GREEN}✅ ${agent_name} agent deployed successfully${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ Failed to deploy ${agent_name} agent${NC}"
        return 1
    fi
}

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENTS_DIR="${SCRIPT_DIR}/agents"

# Deploy GitHub Agent
echo "1️⃣  GitHub Agent"
echo "=================="
if deploy_agent "GitHub" "${AGENTS_DIR}/github-agent"; then
    GITHUB_DEPLOYED=true
else
    GITHUB_DEPLOYED=false
fi

# Deploy Jira Agent
echo "2️⃣  Jira Agent"
echo "=================="
if deploy_agent "Jira" "${AGENTS_DIR}/jira-agent"; then
    JIRA_DEPLOYED=true
else
    JIRA_DEPLOYED=false
fi

# Summary
echo ""
echo "=========================================="
echo "📊 Deployment Summary"
echo "=========================================="
if [ "$GITHUB_DEPLOYED" = true ]; then
    echo -e "✅ GitHub Agent: ${GREEN}DEPLOYED${NC}"
else
    echo -e "❌ GitHub Agent: ${RED}FAILED${NC}"
fi

if [ "$JIRA_DEPLOYED" = true ]; then
    echo -e "✅ Jira Agent: ${GREEN}DEPLOYED${NC}"
else
    echo -e "❌ Jira Agent: ${RED}FAILED${NC}"
fi

echo ""
echo "=========================================="
echo "📝 Next Steps"
echo "=========================================="
echo "1. Test agents using invoke scripts"
echo "2. Check CloudWatch logs for any issues"
echo "3. Get agent ARNs from deployment output"
echo ""
echo "Use: ./invoke_github.sh or ./invoke_jira.sh to test"
echo "=========================================="
