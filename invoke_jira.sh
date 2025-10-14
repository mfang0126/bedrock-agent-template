#!/bin/bash

# Invoke Jira Agent

set -e

echo "=========================================="
echo "📋 Invoking Jira Agent"
echo "=========================================="
echo ""

# Check if prompt is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 'your prompt here'"
    echo ""
    echo "Examples:"
    echo "  $0 'list my projects'"
    echo "  $0 'create an issue in project ABC'"
    echo "  $0 'what can you do'"
    exit 1
fi

PROMPT="$1"

echo "📝 Prompt: $PROMPT"
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
AGENT_DIR="${SCRIPT_DIR}/agents/jira-agent"

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
