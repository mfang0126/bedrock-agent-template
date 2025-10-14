#!/bin/bash
# Quick test script for JIRA agent
# Runs architecture tests automatically, asks before running AWS tests

set -e

echo "============================================================"
echo "JIRA AGENT - Quick Test"
echo "============================================================"
echo ""

# Ensure AGENT_ENV is set
if [ -z "$AGENT_ENV" ]; then
    echo "Setting AGENT_ENV=local for testing..."
    export AGENT_ENV=local
    echo ""
fi

# Step 1: Architecture tests (always run, no AWS needed)
echo "Step 1: Running architecture tests (no AWS needed)..."
echo "------------------------------------------------------------"

# Use .venv python if available, otherwise use system python
if [ -f ".venv/bin/python" ]; then
    .venv/bin/python validate_architecture.py
else
    python3 validate_architecture.py
fi

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Architecture tests failed. Please fix before continuing."
    exit 1
fi

echo ""
echo "✅ Architecture tests passed!"
echo ""

# Step 2: Ask about AWS tests
echo "============================================================"
echo "Step 2: AWS Bedrock Tests"
echo "============================================================"
echo ""
echo "These tests require AWS credentials and will test LLM inference."
echo ""
read -p "Do you want to run AWS Bedrock tests? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Running AWS Bedrock tests..."
    echo "------------------------------------------------------------"

    # Check if AWS credentials are configured
    if ! aws sts get-caller-identity &> /dev/null; then
        echo ""
        echo "⚠️  AWS credentials not found or expired."
        echo ""
        echo "Please configure AWS credentials:"
        echo "  Option 1: aws sso login --profile your-profile"
        echo "  Option 2: export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
        echo ""
        exit 1
    fi

    # Run AWS tests if test_with_aws.py exists
    if [ -f "test_with_aws.py" ]; then
        uv run test_with_aws.py
    else
        echo "⚠️  test_with_aws.py not found. Skipping AWS tests."
    fi
else
    echo ""
    echo "Skipping AWS tests."
fi

echo ""
echo "============================================================"
echo "✅ Quick test complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  - Run full test suite: pytest"
echo "  - Test with AgentCore: agentcore launch --local"
echo "  - Deploy to dev: AGENT_ENV=dev agentcore deploy"
echo ""
