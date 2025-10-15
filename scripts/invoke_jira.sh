#!/bin/bash

# Invoke Jira Agent (AWS Deployed)
# This script invokes the DEPLOYED agent in AWS Bedrock AgentCore

set -e

echo "=========================================="
echo "📋 Invoking Jira Agent (AWS)"
echo "=========================================="
echo ""

# Check if prompt is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 'your prompt here'"
    echo ""
    echo "⚠️  NOTE: This invokes the DEPLOYED agent in AWS (requires OAuth)"
    echo ""
    echo "Examples:"
    echo "  $0 'list my projects'"
    echo "  $0 'create an issue in project ABC'"
    echo "  $0 'what can you do'"
    echo ""
    echo "For LOCAL testing with mock auth (no AWS needed):"
    echo "  uv run scripts/test_jira_local.py 'your prompt here'"
    exit 1
fi

PROMPT="$1"

echo "📝 Prompt: $PROMPT"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENT_DIR="${SCRIPT_DIR}/../agents/jira-agent"

cd "${AGENT_DIR}"

# Create payload
PAYLOAD=$(cat <<EOF
{
  "prompt": "$PROMPT"
}
EOF
)

echo "🚀 Invoking agent..."
echo ""

# Invoke using agentcore CLI
uv run agentcore invoke "$PAYLOAD" --user-id "test-user"

echo ""
echo "=========================================="
echo "✅ Invocation complete"
echo "=========================================="
