#!/bin/bash

# Fix JIRA OAuth Permissions
# Adds GetResourceOauth2Token permission to the AgentCore runtime role

set -e

REGION="ap-southeast-2"
ROLE_NAME="AmazonBedrockAgentCoreSDKRuntime-ap-southeast-2-c0b0109d94"
POLICY_NAME="BedrockAgentCoreOAuthAccess"

echo "🔧 Adding OAuth permissions to JIRA agent runtime role..."

# Create inline policy with OAuth permissions
cat > /tmp/oauth-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:GetResourceOauth2Token"
      ],
      "Resource": "*"
    }
  ]
}
EOF

echo "📋 Policy document:"
cat /tmp/oauth-policy.json

echo ""
echo "➕ Adding inline policy to role: $ROLE_NAME"

aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --policy-document file:///tmp/oauth-policy.json \
  --region "$REGION"

echo ""
echo "✅ Successfully added OAuth permissions!"
echo ""
echo "🔍 Verifying policy..."
aws iam get-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name "$POLICY_NAME" \
  --region "$REGION" \
  --query 'PolicyDocument' \
  --output json

echo ""
echo "✅ Done! JIRA agent can now access OAuth tokens."
echo ""
echo "🧪 Test with:"
echo "   cd agents/jira-agent"
echo "   uv run agentcore invoke \"{ 'prompt': 'Get details for ticket RE-1' }\" --user-id \"test\""

rm /tmp/oauth-policy.json
