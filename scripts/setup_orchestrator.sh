#!/bin/bash

# Setup script for multi-agent orchestration
# Run this after deploying all agents to configure the orchestrator

echo "🚀 Multi-Agent Orchestration Setup"
echo "=================================="
echo ""

# Function to get agent ARN
get_agent_arn() {
    local agent_name=$1
    echo "Getting ARN for ${agent_name}..."
    
    # Try to get the agent status
    output=$(agentcore status --agent ${agent_name} 2>&1)
    
    # Extract ARN from output (adjust pattern as needed)
    arn=$(echo "$output" | grep -oP 'arn:aws:bedrock-agentcore:[^:]+:[^:]+:runtime/[^\s]+' | head -1)
    
    if [ -n "$arn" ]; then
        echo "✅ Found ARN: $arn"
        echo "$arn"
    else
        echo "❌ Could not find ARN for ${agent_name}"
        echo "Make sure the agent is deployed: poe deploy-${agent_name}"
        echo ""
    fi
}

echo "Step 1: Deploy all agents (if not already done)"
echo "------------------------------------------------"
echo "Run these commands if agents are not deployed:"
echo "  poe deploy-github"
echo "  poe deploy-planning"
echo "  poe deploy-jira"
echo "  poe deploy-coding"
echo ""
read -p "Press Enter when all agents are deployed..."

echo ""
echo "Step 2: Collecting Agent ARNs"
echo "-----------------------------"

# Get ARNs for each agent
GITHUB_ARN=$(get_agent_arn "github_agent")
PLANNING_ARN=$(get_agent_arn "planning_agent")
JIRA_ARN=$(get_agent_arn "jira_agent")
CODING_ARN=$(get_agent_arn "coding_agent")

echo ""
echo "Step 3: Export Configuration"
echo "----------------------------"
echo "Add these to your .env file or export them:"
echo ""

# Create export commands
cat << EOF
# Agent ARNs for Orchestrator
export GITHUB_AGENT_ARN="${GITHUB_ARN}"
export PLANNING_AGENT_ARN="${PLANNING_ARN}"
export JIRA_AGENT_ARN="${JIRA_ARN}"
export CODING_AGENT_ARN="${CODING_ARN}"
EOF

echo ""
echo "Step 4: Update .env file"
echo "------------------------"
read -p "Would you like to append these to your .env file? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat << EOF >> .env

# Agent ARNs for Orchestrator (added by setup script)
GITHUB_AGENT_ARN="${GITHUB_ARN}"
PLANNING_AGENT_ARN="${PLANNING_ARN}"
JIRA_AGENT_ARN="${JIRA_ARN}"
CODING_AGENT_ARN="${CODING_ARN}"
EOF
    echo "✅ ARNs added to .env file"
else
    echo "⚠️  Remember to set the environment variables before deploying the orchestrator"
fi

echo ""
echo "Step 5: Deploy Orchestrator"
echo "---------------------------"
echo "Now you can deploy the orchestrator with the configured ARNs:"
echo "  poe deploy-orchestrator"
echo ""
echo "After deployment, test with:"
echo "  poe invoke-orchestrator '{\"prompt\": \"check agent status\"}' --user-id test"
echo ""
echo "✅ Setup complete!"
