#!/bin/bash
# Setup GitHub OAuth credential provider

set -e

REGION="${AWS_REGION:-ap-southeast-2}"
PROVIDER_NAME="github-provider"

# Load credentials from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$GITHUB_CLIENT_ID" ] || [ -z "$GITHUB_CLIENT_SECRET" ]; then
    echo "❌ Missing credentials in .env"
    echo "   GITHUB_CLIENT_ID=..."
    echo "   GITHUB_CLIENT_SECRET=..."
    exit 1
fi

echo "🔐 GitHub Provider Setup (region: $REGION)"

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
    --credential-provider-vendor GithubOauth2 \
    --oauth2-provider-config-input "{
        \"githubOauth2ProviderConfig\": {
            \"clientId\": \"$GITHUB_CLIENT_ID\",
            \"clientSecret\": \"$GITHUB_CLIENT_SECRET\"
        }
    }" \
    --region "$REGION" \
    --output json | jq -r '.credentialProviderArn' | xargs echo "✅ Provider ready:"
