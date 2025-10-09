#!/bin/bash
# First-time AWS AgentCore setup script
# Run this after SSO login to configure and deploy all agents

set -e  # Exit on error

echo "========================================================================="
echo "🚀 AWS Bedrock AgentCore - First-Time Setup"
echo "========================================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default region
AWS_REGION=${AWS_REGION:-ap-southeast-2}

# Step 0: Verify prerequisites
echo "📋 Step 0: Verifying prerequisites..."
echo "----------------------------------------"

# Check AWS credentials
if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured or expired${NC}"
    echo "Please run: authenticate --to=wealth-dev-au"
    echo "Or: aws_use mingfang"
    exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}✅ AWS credentials verified${NC}"
echo "   Account ID: $ACCOUNT_ID"
echo "   Region: $AWS_REGION"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ uv package manager not found${NC}"
    echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo -e "${GREEN}✅ uv package manager found${NC}"

# Check if agentcore CLI is available
if ! command -v agentcore &> /dev/null; then
    echo -e "${YELLOW}⚠️  agentcore CLI not found, will install...${NC}"
fi

echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
echo "----------------------------------------"
uv sync --all-extras
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 2: Configure all agents
echo "⚙️  Step 2: Configuring agents with AgentCore..."
echo "----------------------------------------"
echo "This creates .bedrock_agentcore.yaml (gitignored, required for deployment)"
echo ""

AGENTS=(
    "src/agents/github_agent/runtime.py"
    "src/agents/planning_agent/runtime.py"
    "src/agents/jira_agent/runtime.py"
    "src/agents/coding_agent/runtime.py"
    "src/agents/orchestrator_agent/runtime.py"
)

for agent in "${AGENTS[@]}"; do
    agent_name=$(basename $(dirname "$agent"))
    echo "Configuring ${agent_name}..."
    agentcore configure -e "$agent" --region "$AWS_REGION" --non-interactive
done

echo -e "${GREEN}✅ All agents configured${NC}"
echo ""

# Step 3: Create ECR repositories
echo "🐳 Step 3: Creating ECR repositories..."
echo "----------------------------------------"

REPO_NAMES=(
    "bedrock-agentcore-github_agent"
    "bedrock-agentcore-planning_agent"
    "bedrock-agentcore-jira_agent"
    "bedrock-agentcore-coding_agent"
    "bedrock-agentcore-orchestrator_agent"
)

for repo in "${REPO_NAMES[@]}"; do
    echo "Creating repository: $repo"
    if aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Repository $repo already exists, skipping${NC}"
    else
        aws ecr create-repository --repository-name "$repo" --region "$AWS_REGION" > /dev/null
        echo -e "${GREEN}✅ Created $repo${NC}"
    fi
done

echo ""

# Step 4: Setup OAuth providers
echo "🔐 Step 4: Setting up OAuth providers..."
echo "----------------------------------------"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}⚠️  Please edit .env file with your credentials:${NC}"
    echo "   - GITHUB_CLIENT_ID"
    echo "   - GITHUB_CLIENT_SECRET"
    echo "   - ATLASSIAN_CLIENT_ID (for JIRA)"
    echo "   - ATLASSIAN_CLIENT_SECRET (for JIRA)"
    echo "   - JIRA_URL (for JIRA)"
    echo ""
    read -p "Press Enter after you've updated .env file..."
fi

# Setup GitHub provider
echo "Setting up GitHub OAuth provider..."
if [ -z "$GITHUB_CLIENT_ID" ] || [ -z "$GITHUB_CLIENT_SECRET" ]; then
    echo -e "${YELLOW}⚠️  GitHub credentials not in environment, loading from .env...${NC}"
    source .env
fi

if [ -n "$GITHUB_CLIENT_ID" ] && [ -n "$GITHUB_CLIENT_SECRET" ]; then
    python setup_github_provider.py
    echo -e "${GREEN}✅ GitHub provider setup complete${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping GitHub provider (credentials not configured)${NC}"
fi

# Setup JIRA provider
echo ""
echo "Setting up JIRA OAuth provider..."
if [ -n "$ATLASSIAN_CLIENT_ID" ] && [ -n "$ATLASSIAN_CLIENT_SECRET" ]; then
    python setup_jira_provider.py
    echo -e "${GREEN}✅ JIRA provider setup complete${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping JIRA provider (credentials not configured)${NC}"
    echo "   You can run 'python setup_jira_provider.py' later"
fi

echo ""

# Step 5: Deploy agents
echo "🚀 Step 5: Deploying agents..."
echo "----------------------------------------"
echo -e "${YELLOW}Note: This may take 10-15 minutes per agent (ARM64 builds in CodeBuild)${NC}"
echo ""

read -p "Deploy all agents now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    DEPLOY_AGENTS=(
        "deploy-github"
        "deploy-planning"
        "deploy-jira"
        "deploy-coding"
        "deploy-orchestrator"
    )

    for deploy_cmd in "${DEPLOY_AGENTS[@]}"; do
        agent_name=${deploy_cmd#deploy-}
        echo ""
        echo "Deploying ${agent_name} agent..."
        echo "----------------------------------------"
        if uv run poe "$deploy_cmd"; then
            echo -e "${GREEN}✅ ${agent_name} agent deployed${NC}"
        else
            echo -e "${RED}❌ Failed to deploy ${agent_name} agent${NC}"
            echo "You can retry later with: uv run poe $deploy_cmd"
        fi
    done
else
    echo -e "${YELLOW}⚠️  Skipping deployment. Deploy manually later with:${NC}"
    echo "   uv run poe deploy-github"
    echo "   uv run poe deploy-planning"
    echo "   uv run poe deploy-jira"
    echo "   uv run poe deploy-coding"
    echo "   uv run poe deploy-orchestrator"
fi

echo ""

# Step 6: Summary and next steps
echo "========================================================================="
echo "✅ Setup Complete!"
echo "========================================================================="
echo ""
echo "🎯 Next steps:"
echo ""
echo "1. Test Planning Agent (no OAuth required):"
echo "   uv run poe invoke-planning '{\"prompt\": \"Hello\"}' --user-id \"test\""
echo ""
echo "2. Test GitHub Agent (requires user OAuth on first use):"
echo "   uv run poe invoke-github '{\"prompt\": \"list my repositories\"}' --user-id \"test\""
echo ""
echo "3. Test JIRA Agent (requires user OAuth on first use):"
echo "   uv run poe invoke-jira '{\"prompt\": \"Get details for PROJ-123\"}' --user-id \"test\""
echo ""
echo "4. Test Coding Agent:"
echo "   uv run poe invoke-coding '{\"prompt\": \"Setup a new workspace\"}' --user-id \"test\""
echo ""
echo "5. Test Orchestrator Agent:"
echo "   uv run poe invoke-orchestrator '{\"prompt\": \"Parse this: Fix bug in PROJ-456\"}' --user-id \"test\""
echo ""
echo "📚 Documentation:"
echo "   - Quick Reference: QUICK_REFERENCE.md"
echo "   - AWS Setup Guide: docs/AWS-AgentCore-Setup.md"
echo "   - Individual agent docs in docs/"
echo ""
echo "⚠️  Remember: --user-id parameter is REQUIRED for OAuth agents"
echo ""
