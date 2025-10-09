#!/bin/bash

# Test JIRA OAuth Token
set -e

echo "🧪 JIRA OAuth Token Test"
echo "========================"
echo ""

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

if [ -z "$JIRA_URL" ]; then
    echo "❌ JIRA_URL not set in .env"
    exit 1
fi

echo "📍 JIRA Instance: $JIRA_URL"
echo ""

# Get the OAuth token from CloudWatch logs
echo "🔐 Checking for recent OAuth token..."
echo ""

# Get today's date in YYYY/MM/DD format for log stream prefix
LOG_DATE=$(date -u +"%Y/%m/%d")

# Try to get token from recent logs
TOKEN=$(aws logs tail /aws/bedrock-agentcore/runtimes/jira_agent-WboCCb8qfb-DEFAULT \
    --log-stream-name-prefix "${LOG_DATE}/[runtime-logs]" \
    --since 5m \
    --format short 2>/dev/null | \
    grep "Token:" | \
    tail -1 | \
    awk '{print $NF}' | \
    sed 's/\.\.\.//')

# If no token found, invoke agent to generate one
if [ -z "$TOKEN" ]; then
    echo "⚠️  No recent token found, invoking agent..."
    uv run agentcore invoke "{ 'prompt': 'Test auth' }" --user-id "test" > /dev/null 2>&1 &
    INVOKE_PID=$!

    echo "⏳ Waiting for authentication (10s)..."
    sleep 10

    # Kill the invoke if still running
    kill $INVOKE_PID 2>/dev/null || true
    wait $INVOKE_PID 2>/dev/null || true

    # Try extracting token again
    TOKEN=$(aws logs tail /aws/bedrock-agentcore/runtimes/jira_agent-WboCCb8qfb-DEFAULT \
        --log-stream-name-prefix "${LOG_DATE}/[runtime-logs]" \
        --since 1m \
        --format short 2>/dev/null | \
        grep "Token:" | \
        tail -1 | \
        awk '{print $NF}' | \
        sed 's/\.\.\.//')

    if [ -z "$TOKEN" ]; then
        echo "❌ Could not extract OAuth token"
        echo "💡 Make sure you've authorized the OAuth app first"
        exit 1
    fi
fi

echo "✅ OAuth token extracted: ${TOKEN:0:50}..."
echo ""

# Test 1: Check token format
echo "📊 Test 1: Token Format Check"
echo "Token starts with: ${TOKEN:0:10}"
if [[ $TOKEN == eyJ* ]]; then
    echo "✅ Token format looks like JWT"
else
    echo "⚠️  Unexpected token format"
fi
echo ""

# Test 2: Try to access JIRA API directly
echo "📊 Test 2: JIRA API Access Test"
echo "Testing: GET $JIRA_URL/rest/api/3/myself"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    "$JIRA_URL/rest/api/3/myself")

HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)

echo "HTTP Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ SUCCESS! Token works with JIRA API"
    echo ""
    echo "User Info:"
    echo "$BODY" | jq -r '. | "  Account ID: \(.accountId)\n  Email: \(.emailAddress)\n  Display Name: \(.displayName)"' 2>/dev/null || echo "$BODY"
elif [ "$HTTP_CODE" = "401" ]; then
    echo "❌ AUTHENTICATION FAILED (401)"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    echo "💡 This means:"
    echo "   1. The OAuth app needs to be authorized for this JIRA instance"
    echo "   2. Go to: https://kookaburra.atlassian.net/plugins/servlet/oauth/authorize"
    echo "   3. Or the OAuth scopes might be insufficient"
    echo "   4. Or the app isn't configured for this Atlassian site"
    echo ""
    echo "🔧 Next steps:"
    echo "   1. Check OAuth app configuration in Atlassian Developer Console"
    echo "   2. Verify callback URLs are set correctly"
    echo "   3. Ensure scopes include: read:jira-work, write:jira-work"
    echo "   4. User may need to authorize the app at:"
    echo "      https://auth.atlassian.com/authorize?..."
elif [ "$HTTP_CODE" = "403" ]; then
    echo "❌ FORBIDDEN (403)"
    echo "   Token is valid but lacks permissions"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
else
    echo "⚠️  Unexpected response code: $HTTP_CODE"
    echo ""
    echo "Response:"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
fi

echo ""
echo "========================"
echo "🏁 Test Complete"
