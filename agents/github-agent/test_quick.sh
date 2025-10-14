#!/bin/bash
# Quick test script - runs appropriate tests based on available credentials

set -e

echo "============================================================"
echo "GitHub Agent Quick Test"
echo "============================================================"
echo ""

# Activate virtual environment
source .venv/bin/activate
export AGENT_ENV=local

# Test 1: Architecture (always runs)
echo "✓ Running architecture tests (no AWS needed)..."
python validate_architecture.py
echo ""

# Test 2: Check for AWS credentials
echo "Checking AWS credentials..."
if aws sts get-caller-identity >/dev/null 2>&1; then
    echo "✅ AWS credentials found"
    echo ""

    # Confirm before running AWS tests
    read -p "Run LLM inference tests with AWS Bedrock? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "✓ Running LLM inference tests..."
        echo "n" | python test_with_aws.py
    fi
else
    echo "⚠️  AWS credentials not found or expired"
    echo ""
    echo "To test LLM inference, refresh your credentials:"
    echo "  aws sso login --profile your-profile"
    echo "  export AWS_PROFILE=your-profile"
    echo ""
    echo "Or use temporary credentials:"
    echo "  aws sts get-session-token"
fi

echo ""
echo "============================================================"
echo "Testing Complete!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  • Architecture validation: ✅ Complete"
echo "  • LLM inference: Run 'test_with_aws.py' with AWS credentials"
echo "  • Full integration: Run 'agentcore launch --local'"
echo ""
