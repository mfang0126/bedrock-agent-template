#!/bin/bash
set -e

# Load from .env if not already exported
if [ -z "$SHARED_EXECUTION_ROLE_ARN" ]; then
  source .env
fi

REGION="${AWS_REGION:-ap-southeast-2}"

# Agent names and entrypoints
AGENT_NAMES=("orchestrator" "github" "jira" "planning" "coding")
AGENT_ENTRYPOINTS=(
  "src/agents/orchestrator_agent/runtime.py"
  "src/agents/github_agent/runtime.py"
  "src/agents/jira_agent/runtime.py"
  "src/agents/planning_agent/runtime.py"
  "src/agents/coding_agent/runtime.py"
)

echo "🔧 Configuring agents with shared resources..."
echo "Execution Role: $SHARED_EXECUTION_ROLE_ARN"
echo "ECR Repository: $SHARED_ECR_REPOSITORY"
echo "Memory ID: $SHARED_MEMORY_ID"
echo ""

for i in "${!AGENT_NAMES[@]}"; do
  name="${AGENT_NAMES[$i]}"
  entrypoint="${AGENT_ENTRYPOINTS[$i]}"
  echo "⚙️  Configuring: $name ($entrypoint)"
  uv run agentcore configure \
    -e "$entrypoint" \
    --name "$name" \
    --execution-role "$SHARED_EXECUTION_ROLE_ARN" \
    --ecr "$SHARED_ECR_REPOSITORY" \
    --region "$REGION" \
    --disable-otel \
    --non-interactive
  echo ""
done

# Update memory IDs in config
echo "🧠 Updating memory configuration..."
sed -i.bak "s/memory_id: null/memory_id: $SHARED_MEMORY_ID/g" .bedrock_agentcore.yaml
sed -i.bak "s/memory_id: None/memory_id: $SHARED_MEMORY_ID/g" .bedrock_agentcore.yaml
rm -f .bedrock_agentcore.yaml.bak

# Set default agent
echo "🎯 Setting default agent to orchestrator..."
uv run agentcore configure set-default orchestrator

echo "✅ All agents configured with shared resources!"
