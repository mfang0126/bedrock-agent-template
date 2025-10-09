#!/bin/bash
# Update orchestrator IAM role with permissions to invoke sub-agents

set -e

echo "🔧 Updating Orchestrator Agent IAM permissions..."

# Load environment variables
source .env 2>/dev/null || true

# IAM role name (from .bedrock_agentcore.yaml)
ORCHESTRATOR_ROLE="AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-d92c6a81b2"
REGION="${AWS_REGION:-ap-southeast-2}"

# Sub-agent ARNs from .env
GITHUB_ARN="${GITHUB_AGENT_ARN}"
PLANNING_ARN="${PLANNING_AGENT_ARN}"
JIRA_ARN="${JIRA_AGENT_ARN}"
CODING_ARN="${CODING_AGENT_ARN}"

# Create IAM policy document
cat > /tmp/orchestrator-policy.json <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:InvokeAgentRuntime"
            ],
            "Resource": [
                "${GITHUB_ARN}",
                "${GITHUB_ARN}/runtime-endpoint/DEFAULT",
                "${PLANNING_ARN}",
                "${PLANNING_ARN}/runtime-endpoint/DEFAULT",
                "${JIRA_ARN}",
                "${JIRA_ARN}/runtime-endpoint/DEFAULT",
                "${CODING_ARN}",
                "${CODING_ARN}/runtime-endpoint/DEFAULT"
            ]
        }
    ]
}
EOF

echo "📋 IAM Policy:"
cat /tmp/orchestrator-policy.json

# Apply the policy to the orchestrator role
echo ""
echo "🚀 Applying policy to role: ${ORCHESTRATOR_ROLE}"

aws iam put-role-policy \
    --role-name "${ORCHESTRATOR_ROLE}" \
    --policy-name "OrchestratorSubAgentInvoke" \
    --policy-document file:///tmp/orchestrator-policy.json \
    --region "${REGION}"

echo "✅ Successfully updated orchestrator IAM permissions!"
echo ""
echo "📝 The orchestrator agent can now invoke:"
echo "  - GitHub Agent: ${GITHUB_ARN}"
echo "  - Planning Agent: ${PLANNING_ARN}"
echo "  - JIRA Agent: ${JIRA_ARN}"
echo "  - Coding Agent: ${CODING_ARN}"
echo ""
echo "🔄 Redeploy the orchestrator agent to apply changes:"
echo "   uv run agentcore launch --agent orchestrator_agent"

# Cleanup
rm /tmp/orchestrator-policy.json
