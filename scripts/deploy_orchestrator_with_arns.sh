#!/bin/bash
# Deploy orchestrator agent with sub-agent ARNs
set -e

REGION="${AWS_REGION:-ap-southeast-2}"

echo "🔍 Fetching sub-agent ARNs..."

# Get ARNs from .bedrock_agentcore.yaml or agentcore status
GITHUB_ARN=$(grep -A 20 "github_agent:" .bedrock_agentcore.yaml | grep "agent_arn:" | awk '{print $2}' | tr -d "'\"")
PLANNING_ARN=$(grep -A 20 "planning_agent:" .bedrock_agentcore.yaml | grep "agent_arn:" | awk '{print $2}' | tr -d "'\"")
JIRA_ARN=$(grep -A 20 "jira_agent:" .bedrock_agentcore.yaml | grep "agent_arn:" | awk '{print $2}' | tr -d "'\"")
CODING_ARN=$(grep -A 20 "coding_agent:" .bedrock_agentcore.yaml | grep "agent_arn:" | awk '{print $2}' | tr -d "'\"")

echo "📋 Sub-agent ARNs:"
echo "  GitHub:   ${GITHUB_ARN:-not deployed}"
echo "  Planning: ${PLANNING_ARN:-not deployed}"
echo "  JIRA:     ${JIRA_ARN:-not deployed}"
echo "  Coding:   ${CODING_ARN:-not deployed}"

# Build env args
ENV_ARGS=""
[ -n "$GITHUB_ARN" ] && ENV_ARGS="$ENV_ARGS --env GITHUB_AGENT_ARN=$GITHUB_ARN"
[ -n "$PLANNING_ARN" ] && ENV_ARGS="$ENV_ARGS --env PLANNING_AGENT_ARN=$PLANNING_ARN"
[ -n "$JIRA_ARN" ] && ENV_ARGS="$ENV_ARGS --env JIRA_AGENT_ARN=$JIRA_ARN"
[ -n "$CODING_ARN" ] && ENV_ARGS="$ENV_ARGS --env CODING_AGENT_ARN=$CODING_ARN"

echo ""
echo "🚀 Deploying orchestrator agent..."
agentcore launch --agent orchestrator_agent $ENV_ARGS

echo ""
echo "✅ Orchestrator deployed with sub-agent ARNs!"
