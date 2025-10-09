#!/bin/bash
# Setup JIRA OAuth credential provider

set -e

REGION="${AWS_REGION:-ap-southeast-2}"
PROVIDER_NAME="jira-provider"

# Load credentials from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$ATLASSIAN_CLIENT_ID" ] || [ -z "$ATLASSIAN_CLIENT_SECRET" ]; then
    echo "❌ Missing credentials in .env"
    echo "   ATLASSIAN_CLIENT_ID=..."
    echo "   ATLASSIAN_CLIENT_SECRET=..."
    exit 1
fi

echo "🔐 JIRA Provider Setup (region: $REGION)"

# Delete if exists
if aws bedrock-agentcore-control list-oauth2-credential-providers --region "$REGION" 2>/dev/null | grep -q "\"name\": \"$PROVIDER_NAME\""; then
    echo "♻️  Deleting existing provider..."
    aws bedrock-agentcore-control delete-oauth2-credential-provider \
        --name "$PROVIDER_NAME" \
        --region "$REGION" 2>/dev/null || true
    echo "⏳ Waiting for cleanup..."
    sleep 5
fi

# Create provider
echo "📡 Creating provider '$PROVIDER_NAME'..."
aws bedrock-agentcore-control create-oauth2-credential-provider \
    --name "$PROVIDER_NAME" \
    --credential-provider-vendor CustomOauth2 \
    --oauth2-provider-config-input "{
        \"customOauth2ProviderConfig\": {
            \"oauthDiscovery\": {
                \"discoveryUrl\": \"https://auth.atlassian.com/.well-known/openid-configuration\"
            },
            \"clientId\": \"$ATLASSIAN_CLIENT_ID\",
            \"clientSecret\": \"$ATLASSIAN_CLIENT_SECRET\"
        }
    }" \
    --region "$REGION" \
    --output json | jq -r '.credentialProviderArn' | xargs echo "✅ Provider ready:"
