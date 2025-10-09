#!/bin/bash

# Check Atlassian OAuth Configuration
echo "🔍 Atlassian OAuth Configuration Check"
echo "======================================="
echo ""

# Load .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

echo "📋 Configuration:"
echo "  JIRA URL: $JIRA_URL"
echo "  Client ID: ${ATLASSIAN_CLIENT_ID:0:15}..."
echo ""

echo "💡 Required Configuration in Atlassian Developer Console:"
echo "==========================================================="
echo ""
echo "1. Go to: https://developer.atlassian.com/console/myapps/"
echo ""
echo "2. Select your OAuth 2.0 (3LO) app with Client ID: ${ATLASSIAN_CLIENT_ID:0:15}..."
echo ""
echo "3. Verify Settings:"
echo "   ✓ Authorization callback URL includes:"
echo "     - AgentCore's OAuth callback endpoint"
echo "   ✓ Permissions tab includes these scopes:"
echo "     - read:jira-work (Read data from Jira)"
echo "     - write:jira-work (Write data to Jira)"
echo "     - offline_access (For refresh tokens)"
echo ""
echo "4. Verify Distribution:"
echo "   ✓ App is either:"
echo "     - Public (available to all users)"
echo "     - OR authorized for your organization"
echo ""
echo "5. OAuth Flow:"
echo "   The user (you) needs to authorize this app by visiting:"
echo "   https://auth.atlassian.com/authorize?"
echo "     client_id=${ATLASSIAN_CLIENT_ID}"
echo "     "&scope=read:jira-work%20write:jira-work%20offline_access"
echo "     "&redirect_uri=YOUR_AGENTCORE_CALLBACK"
echo "     "&response_type=code"
echo "     "&prompt=consent"
echo ""
echo "======================================="
echo ""
echo "🧪 Next Steps:"
echo "1. Verify OAuth app configuration above"
echo "2. Run: uv run agentcore invoke \"{ 'prompt': 'test' }\" --user-id \"new-user-\$(date +%s)\""
echo "3. Look for OAuth URL in output"
echo "4. Visit that URL and authorize access to kookaburra.atlassian.net"
echo "5. Try again after authorization"
