#!/bin/bash
set -e

AGENTS=("github" "jira" "planning" "coding")

echo "🚀 Deploying all agents..."
echo ""

for agent in "${AGENTS[@]}"; do
  echo "📦 Deploying: $agent"
  uv run agentcore launch --agent "$agent"
  echo "✅ $agent deployed!"
  echo ""
done

echo "✅ All agents deployed!"
echo ""
echo "📋 Check status:"
echo "   agentcore status --agent orchestrator"
