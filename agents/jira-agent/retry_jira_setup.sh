#!/bin/bash

# Retry JIRA Provider Setup with Better Error Handling
set -e

REGION="${AWS_REGION:-ap-southeast-2}"
PROVIDER_NAME="jira-provider"

echo "🔍 Diagnostic Information:"
echo "=========================="

# Check AWS credentials
echo "✓ AWS Identity:"
aws sts get-caller-identity --output table 2>/dev/null || echo "❌ AWS credentials not configured"

# Check for existing provider
echo ""
echo "✓ Checking existing providers:"
aws bedrock-agentcore-control list-oauth2-credential-providers --region "$REGION" 2>/dev/null | jq -r '.credentialProviders[] | "\(.name) - \(.credentialProviderVendor)"' || echo "❌ Cannot list providers"

# Check Secrets Manager
echo ""
echo "✓ Checking Secrets Manager:"
aws secretsmanager list-secrets --region "$REGION" --query "SecretList[?contains(Name, 'oauth')].Name" --output table 2>/dev/null || echo "❌ Cannot list secrets"

# Load credentials
echo ""
echo "✓ Loading JIRA credentials from .env:"
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    if [ -n "$ATLASSIAN_CLIENT_ID" ]; then
        echo "  ATLASSIAN_CLIENT_ID: ${ATLASSIAN_CLIENT_ID:0:10}..."
    else
        echo "  ❌ ATLASSIAN_CLIENT_ID not set"
        exit 1
    fi
    if [ -n "$ATLASSIAN_CLIENT_SECRET" ]; then
        echo "  ATLASSIAN_CLIENT_SECRET: ${ATLASSIAN_CLIENT_SECRET:0:10}..."
    else
        echo "  ❌ ATLASSIAN_CLIENT_SECRET not set"
        exit 1
    fi
else
    echo "❌ .env file not found"
    exit 1
fi

echo ""
echo "=========================="
echo "🚀 Attempting to create provider with detailed error output:"
echo ""

# Try to create provider with full error output
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
    --output json 2>&1 | tee /tmp/jira_provider_output.txt

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    echo "✅ Provider created successfully!"
    cat /tmp/jira_provider_output.txt | jq -r '.credentialProviderArn' | xargs echo "   ARN:"
else
    echo ""
    echo "❌ Provider creation failed. Error details above."
    echo ""
    echo "💡 Possible solutions:"
    echo "   1. Wait 30 seconds and try again (transient AWS issue)"
    echo "   2. Check IAM permissions for Secrets Manager"
    echo "   3. Check Secrets Manager service quotas"
    echo "   4. Check if there's a pending deletion secret"
    exit 1
fi
