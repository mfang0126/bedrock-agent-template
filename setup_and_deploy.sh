#!/bin/bash

# Complete setup for GitHub and Jira agents

set -e

echo "=========================================="
echo "🔧 Agent Setup & Deployment Pipeline"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Step 1: Make scripts executable
echo -e "${BLUE}Step 1: Making scripts executable${NC}"
chmod +x deploy_agents.sh
chmod +x invoke_github.sh
chmod +x invoke_jira.sh
chmod +x test_agents_local.sh
echo -e "${GREEN}✅ Scripts are now executable${NC}"
echo ""

# Step 2: Check prerequisites
echo -e "${BLUE}Step 2: Checking prerequisites${NC}"

# Check for uv
if command -v uv &> /dev/null; then
    echo "✅ uv is installed"
else
    echo -e "${RED}❌ uv is not installed${NC}"
    echo "   Install with: pip install uv"
    exit 1
fi

# Check for AWS CLI
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI is installed"
else
    echo -e "${RED}❌ AWS CLI is not installed${NC}"
    echo "   Install from: https://aws.amazon.com/cli/"
    exit 1
fi

# Check for agentcore
if command -v agentcore &> /dev/null; then
    echo "✅ AgentCore CLI is installed"
else
    echo -e "${YELLOW}⚠️  AgentCore CLI not found in PATH${NC}"
    echo "   Trying with uv run..."
fi

echo ""

# Step 3: Environment check
echo -e "${BLUE}Step 3: Checking environment variables${NC}"

ENV_ISSUES=false

# GitHub
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN not set${NC}"
    ENV_ISSUES=true
else
    echo "✅ GITHUB_TOKEN is set"
fi

# Jira
if [ -z "$JIRA_API_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  JIRA_API_TOKEN not set${NC}"
    ENV_ISSUES=true
else
    echo "✅ JIRA_API_TOKEN is set"
fi

if [ -z "$JIRA_EMAIL" ]; then
    echo -e "${YELLOW}⚠️  JIRA_EMAIL not set${NC}"
    ENV_ISSUES=true
else
    echo "✅ JIRA_EMAIL is set"
fi

if [ -z "$JIRA_CLOUD_ID" ]; then
    echo -e "${YELLOW}⚠️  JIRA_CLOUD_ID not set${NC}"
    ENV_ISSUES=true
else
    echo "✅ JIRA_CLOUD_ID is set"
fi

if [ "$ENV_ISSUES" = true ]; then
    echo ""
    echo -e "${YELLOW}Note: Some environment variables are missing.${NC}"
    echo "You may need to set them in .env files or export them."
    echo ""
fi

echo ""

# Step 4: Run local tests
echo -e "${BLUE}Step 4: Running local tests${NC}"
echo ""

if ./test_agents_local.sh; then
    echo ""
    echo -e "${GREEN}✅ Local tests passed!${NC}"
    
    # Step 5: Ask about deployment
    echo ""
    echo -e "${BLUE}Step 5: Deploy to AWS?${NC}"
    read -p "Do you want to deploy to AWS now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo -e "${YELLOW}🚀 Starting deployment...${NC}"
        ./deploy_agents.sh
    else
        echo ""
        echo -e "${BLUE}Deployment skipped.${NC}"
        echo "Run ./deploy_agents.sh when ready to deploy."
    fi
else
    echo ""
    echo -e "${RED}❌ Local tests failed!${NC}"
    echo "Fix the issues before deploying."
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  • Test with: ./invoke_github.sh 'your prompt'"
echo "  • Test with: ./invoke_jira.sh 'your prompt'"
echo "  • View logs in CloudWatch"
echo ""
