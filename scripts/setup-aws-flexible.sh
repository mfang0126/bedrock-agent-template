#!/bin/bash
# Flexible AWS AgentCore setup script
# Checks for existing resources and reuses them where possible

set -euo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

pushd "$PROJECT_ROOT" > /dev/null
trap 'popd > /dev/null' EXIT

echo "========================================================================="
echo "🚀 AWS Bedrock AgentCore - Flexible Setup"
echo "========================================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default region
AWS_REGION=${AWS_REGION:-ap-southeast-2}
PYTHON_RUNNER=${PYTHON_RUNNER:-"uv run python"}

# Function to check if a credential provider exists
check_provider_exists() {
    local provider_name=$1
    echo "Checking if provider '$provider_name' exists..."
    
    # Try to list providers and check if ours exists
    if aws bedrock-agentcore list-credential-providers --region "$AWS_REGION" 2>/dev/null | grep -q "\"name\": \"$provider_name\""; then
        return 0  # Provider exists
    else
        return 1  # Provider doesn't exist
    fi
}

# Function to get provider ARN
get_provider_arn() {
    local provider_name=$1
    aws bedrock-agentcore list-credential-providers --region "$AWS_REGION" 2>/dev/null | \
        jq -r ".credentialProviders[] | select(.name == \"$provider_name\") | .arn"
}

# Step 0: Verify prerequisites
echo "📋 Step 0: Verifying prerequisites..."
echo "----------------------------------------"

# Check AWS credentials
if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found${NC}"
    echo "Install AWS CLI v2: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html"
    exit 1
fi

if ! aws sts get-caller-identity > /dev/null 2>&1; then
    echo -e "${RED}❌ AWS credentials not configured or expired${NC}"
    echo "Please authenticate with your AWS SSO or profile helper"
    echo "Example: authenticate --to=<profile> or aws_use <profile>"
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

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${RED}❌ jq not found${NC}"
    echo "Install jq to continue (e.g. brew install jq)"
    exit 1
fi

# Check if agentcore CLI is available
if ! command -v agentcore &> /dev/null; then
    echo -e "${YELLOW}⚠️  agentcore CLI not found, installing...${NC}"
    uv tool install bedrock-agentcore
fi

echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing dependencies..."
echo "----------------------------------------"
UV_SYNC_FLAGS=${UV_SYNC_FLAGS:-"--all-extras"}
uv sync $UV_SYNC_FLAGS
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 2: Configure all agents
echo "⚙️  Step 2: Configuring agents with AgentCore..."
echo "----------------------------------------"
echo "This creates/updates .bedrock_agentcore.yaml"
echo ""

# Check if config already exists
if [ -f ".bedrock_agentcore.yaml" ]; then
    echo -e "${BLUE}ℹ️  Existing configuration found${NC}"
    read -p "Update existing configuration? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}⚠️  Keeping existing configuration${NC}"
    else
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
    fi
else
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
fi

echo ""

# Step 3: Create ECR repositories (if needed)
echo "🐳 Step 3: Checking/Creating ECR repositories..."
echo "----------------------------------------"

REPO_NAMES=(
    "bedrock-agentcore-github_agent"
    "bedrock-agentcore-planning_agent"
    "bedrock-agentcore-jira_agent"
    "bedrock-agentcore-coding_agent"
    "bedrock-agentcore-orchestrator_agent"
)

ECR_CREATED=0
ECR_EXISTING=0

for repo in "${REPO_NAMES[@]}"; do
    if aws ecr describe-repositories --repository-names "$repo" --region "$AWS_REGION" > /dev/null 2>&1; then
        echo -e "${BLUE}ℹ️  Repository $repo already exists${NC}"
        ((ECR_EXISTING++))
    else
        echo "Creating repository: $repo"
        aws ecr create-repository --repository-name "$repo" --region "$AWS_REGION" > /dev/null
        echo -e "${GREEN}✅ Created $repo${NC}"
        ((ECR_CREATED++))
    fi
done

echo -e "${GREEN}Summary: $ECR_CREATED created, $ECR_EXISTING existing${NC}"
echo ""

# Step 4: Setup OAuth providers (check if they exist first)
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

# Load environment variables
source .env

# Setup GitHub provider
echo ""
echo "Checking GitHub OAuth provider..."
if check_provider_exists "github-provider"; then
    GITHUB_PROVIDER_ARN=$(get_provider_arn "github-provider")
    echo -e "${BLUE}ℹ️  GitHub provider already exists${NC}"
    echo "   ARN: $GITHUB_PROVIDER_ARN"
    
    read -p "Update existing GitHub provider? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -n "$GITHUB_CLIENT_ID" ] && [ -n "$GITHUB_CLIENT_SECRET" ]; then
            echo "Updating GitHub provider..."
            $PYTHON_RUNNER setup_github_provider.py --update --force --region "$AWS_REGION"
            echo -e "${GREEN}✅ GitHub provider updated${NC}"
        else
            echo -e "${YELLOW}⚠️  GitHub credentials not configured in .env${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  Using existing GitHub provider${NC}"
    fi
else
    if [ -n "$GITHUB_CLIENT_ID" ] && [ -n "$GITHUB_CLIENT_SECRET" ]; then
        echo "Creating GitHub provider..."
        $PYTHON_RUNNER setup_github_provider.py --region "$AWS_REGION"
        echo -e "${GREEN}✅ GitHub provider created${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping GitHub provider (credentials not configured)${NC}"
        echo "   Configure in .env and run: uv run python setup_github_provider.py --region $AWS_REGION"
    fi
fi

# Setup JIRA provider
echo ""
echo "Checking JIRA OAuth provider..."
if check_provider_exists "jira-provider"; then
    JIRA_PROVIDER_ARN=$(get_provider_arn "jira-provider")
    echo -e "${BLUE}ℹ️  JIRA provider already exists${NC}"
    echo "   ARN: $JIRA_PROVIDER_ARN"
    
    read -p "Update existing JIRA provider? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -n "$ATLASSIAN_CLIENT_ID" ] && [ -n "$ATLASSIAN_CLIENT_SECRET" ]; then
            echo "Updating JIRA provider..."
            $PYTHON_RUNNER setup_jira_provider.py --update --force --region "$AWS_REGION"
            echo -e "${GREEN}✅ JIRA provider updated${NC}"
        else
            echo -e "${YELLOW}⚠️  JIRA credentials not configured in .env${NC}"
        fi
    else
        echo -e "${BLUE}ℹ️  Using existing JIRA provider${NC}"
    fi
else
    if [ -n "$ATLASSIAN_CLIENT_ID" ] && [ -n "$ATLASSIAN_CLIENT_SECRET" ]; then
        echo "Creating JIRA provider..."
        $PYTHON_RUNNER setup_jira_provider.py --region "$AWS_REGION"
        echo -e "${GREEN}✅ JIRA provider created${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping JIRA provider (credentials not configured)${NC}"
        echo "   Configure in .env and run: uv run python setup_jira_provider.py --region $AWS_REGION"
    fi
fi

echo ""

# Step 5: Check deployed agents and offer deployment
echo "🚀 Step 5: Checking deployed agents..."
echo "----------------------------------------"

# Function to check if agent is deployed
check_agent_deployed() {
    local agent_name=$1
    if agentcore status --agent "$agent_name" 2>/dev/null | grep -q "Active"; then
        return 0  # Agent is deployed
    else
        return 1  # Agent not deployed
    fi
}

# Arrays to track agent status
DEPLOYED_AGENTS=()
NOT_DEPLOYED_AGENTS=()

AGENTS_TO_CHECK=(
    "github_agent"
    "planning_agent"
    "jira_agent"
    "coding_agent"
    "orchestrator_agent"
)

for agent in "${AGENTS_TO_CHECK[@]}"; do
    echo -n "Checking $agent... "
    if check_agent_deployed "$agent"; then
        echo -e "${GREEN}Deployed${NC}"
        DEPLOYED_AGENTS+=("$agent")
        
        # Get and store the ARN
        AGENT_ARN=$(agentcore status --agent "$agent" 2>/dev/null | grep -oP 'arn:aws:bedrock-agentcore:[^:]+:[^:]+:runtime/[^\s]+' | head -1)
        if [ -n "$AGENT_ARN" ]; then
            echo "   ARN: $AGENT_ARN"
        fi
    else
        echo -e "${YELLOW}Not deployed${NC}"
        NOT_DEPLOYED_AGENTS+=("$agent")
    fi
done

echo ""
echo -e "${GREEN}Deployed agents: ${#DEPLOYED_AGENTS[@]}${NC}"
echo -e "${YELLOW}Not deployed: ${#NOT_DEPLOYED_AGENTS[@]}${NC}"

if [ ${#NOT_DEPLOYED_AGENTS[@]} -gt 0 ]; then
    echo ""
    echo "The following agents are not deployed:"
    for agent in "${NOT_DEPLOYED_AGENTS[@]}"; do
        echo "  - $agent"
    done
    
    echo ""
    read -p "Deploy missing agents now? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for agent in "${NOT_DEPLOYED_AGENTS[@]}"; do
            deploy_cmd="deploy-${agent%_agent}"  # Remove _agent suffix
            echo ""
            echo "Deploying $agent..."
            echo "----------------------------------------"
            if uv run poe "$deploy_cmd"; then
                echo -e "${GREEN}✅ $agent deployed${NC}"
            else
                echo -e "${RED}❌ Failed to deploy $agent${NC}"
                echo "You can retry later with: uv run poe $deploy_cmd"
            fi
        done
    else
        echo -e "${YELLOW}⚠️  Skipping deployment. Deploy manually with:${NC}"
        for agent in "${NOT_DEPLOYED_AGENTS[@]}"; do
            deploy_cmd="deploy-${agent%_agent}"
            echo "   uv run poe $deploy_cmd"
        done
    fi
fi

echo ""

# Step 6: Update orchestrator configuration with agent ARNs
if [[ " ${DEPLOYED_AGENTS[@]} " =~ " orchestrator_agent " ]] || [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📝 Step 6: Updating orchestrator configuration..."
    echo "----------------------------------------"
    
    # Collect ARNs for all agents
    echo "Collecting agent ARNs..."
    
    GITHUB_ARN=$(agentcore status --agent github_agent 2>/dev/null | grep -oP 'arn:aws:bedrock-agentcore:[^:]+:[^:]+:runtime/[^\s]+' | head -1 || echo "")
    PLANNING_ARN=$(agentcore status --agent planning_agent 2>/dev/null | grep -oP 'arn:aws:bedrock-agentcore:[^:]+:[^:]+:runtime/[^\s]+' | head -1 || echo "")
    JIRA_ARN=$(agentcore status --agent jira_agent 2>/dev/null | grep -oP 'arn:aws:bedrock-agentcore:[^:]+:[^:]+:runtime/[^\s]+' | head -1 || echo "")
    CODING_ARN=$(agentcore status --agent coding_agent 2>/dev/null | grep -oP 'arn:aws:bedrock-agentcore:[^:]+:[^:]+:runtime/[^\s]+' | head -1 || echo "")
    
    if [ -n "$GITHUB_ARN" ] || [ -n "$PLANNING_ARN" ] || [ -n "$JIRA_ARN" ] || [ -n "$CODING_ARN" ]; then
        echo ""
        echo "Found agent ARNs:"
        [ -n "$GITHUB_ARN" ] && echo "  GitHub: $GITHUB_ARN"
        [ -n "$PLANNING_ARN" ] && echo "  Planning: $PLANNING_ARN"
        [ -n "$JIRA_ARN" ] && echo "  JIRA: $JIRA_ARN"
        [ -n "$CODING_ARN" ] && echo "  Coding: $CODING_ARN"
        
        echo ""
        echo "Add these to your .env file or .bedrock_agentcore.yaml:"
        echo ""
        echo "# Agent ARNs for Orchestrator"
        [ -n "$GITHUB_ARN" ] && echo "GITHUB_AGENT_ARN=$GITHUB_ARN"
        [ -n "$PLANNING_ARN" ] && echo "PLANNING_AGENT_ARN=$PLANNING_ARN"
        [ -n "$JIRA_ARN" ] && echo "JIRA_AGENT_ARN=$JIRA_ARN"
        [ -n "$CODING_ARN" ] && echo "CODING_AGENT_ARN=$CODING_ARN"
        
        echo ""
        read -p "Append these to .env file? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            {
                echo ""
                echo "# Agent ARNs for Orchestrator (added by setup script)"
                [ -n "$GITHUB_ARN" ] && echo "GITHUB_AGENT_ARN=$GITHUB_ARN"
                [ -n "$PLANNING_ARN" ] && echo "PLANNING_AGENT_ARN=$PLANNING_ARN"
                [ -n "$JIRA_ARN" ] && echo "JIRA_AGENT_ARN=$JIRA_ARN"
                [ -n "$CODING_ARN" ] && echo "CODING_AGENT_ARN=$CODING_ARN"
            } >> .env
            echo -e "${GREEN}✅ ARNs added to .env file${NC}"
        fi
    fi
fi

echo ""

# Step 7: Summary and next steps
echo "========================================================================="
echo "✅ Setup Complete!"
echo "========================================================================="
echo ""

if [ ${#DEPLOYED_AGENTS[@]} -gt 0 ]; then
    echo "🎯 Test your deployed agents:"
    echo ""
    
    if [[ " ${DEPLOYED_AGENTS[@]} " =~ " planning_agent " ]]; then
        echo "1. Planning Agent (no OAuth required):"
        echo "   uv run poe invoke-planning '{\"prompt\": \"Hello\"}' --user-id \"test\""
        echo ""
    fi
    
    if [[ " ${DEPLOYED_AGENTS[@]} " =~ " github_agent " ]]; then
        echo "2. GitHub Agent (requires user OAuth on first use):"
        echo "   uv run poe invoke-github '{\"prompt\": \"list my repositories\"}' --user-id \"test\""
        echo ""
    fi
    
    if [[ " ${DEPLOYED_AGENTS[@]} " =~ " jira_agent " ]]; then
        echo "3. JIRA Agent (requires user OAuth on first use):"
        echo "   uv run poe invoke-jira '{\"prompt\": \"Get details for PROJ-123\"}' --user-id \"test\""
        echo ""
    fi
    
    if [[ " ${DEPLOYED_AGENTS[@]} " =~ " coding_agent " ]]; then
        echo "4. Coding Agent:"
        echo "   uv run poe invoke-coding '{\"prompt\": \"Setup a new workspace\"}' --user-id \"test\""
        echo ""
    fi
    
    if [[ " ${DEPLOYED_AGENTS[@]} " =~ " orchestrator_agent " ]]; then
        echo "5. Orchestrator Agent:"
        echo "   uv run poe invoke-orchestrator '{\"prompt\": \"check agent status\"}' --user-id \"test\""
        echo ""
    fi
fi

echo "📚 Documentation:"
echo "   - Quick Reference: QUICK_REFERENCE.md"
echo "   - AWS Setup Guide: docs/AWS-AgentCore-Setup.md"
echo "   - Individual agent docs in docs/"
echo ""

if [ ${#NOT_DEPLOYED_AGENTS[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Some agents are not deployed. Deploy them with:${NC}"
    for agent in "${NOT_DEPLOYED_AGENTS[@]}"; do
        deploy_cmd="deploy-${agent%_agent}"
        echo "   uv run poe $deploy_cmd"
    done
    echo ""
fi

echo "⚠️  Remember: --user-id parameter is REQUIRED for OAuth agents"
echo ""
