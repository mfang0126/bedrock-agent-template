#!/usr/bin/env python3
"""Setup GitHub OAuth credential provider in AWS Bedrock AgentCore.

This script creates the GitHub OAuth2 credential provider required for the agent.
Run this BEFORE deploying the agent.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.auth.credential_provider import CredentialProviderManager
from common.config.config import Config

def main():
    print("=" * 70)
    print("🔐 GitHub OAuth Credential Provider Setup")
    print("=" * 70)
    print()

    # Get configuration
    config = Config(environment="local")

    try:
        credentials = config.get_github_credentials()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print()
        print("📝 Setup instructions:")
        print("   1. Create a GitHub OAuth App at:")
        print("      https://github.com/settings/developers")
        print("   2. Add credentials to .env file:")
        print("      GITHUB_CLIENT_ID=your_client_id")
        print("      GITHUB_CLIENT_SECRET=your_client_secret")
        print("   3. Run this script again")
        return 1

    client_id = credentials["client_id"]
    client_secret = credentials["client_secret"]
    region = config.get_aws_region()

    print(f"✅ GitHub OAuth credentials loaded")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Region: {region}")
    print()

    # Create credential provider
    print("📡 Creating GitHub credential provider in AgentCore...")
    print()

    try:
        manager = CredentialProviderManager(region=region)

        response = manager.create_github_provider(
            name="github-provider",
            client_id=client_id,
            client_secret=client_secret
        )

        print()
        print("=" * 70)
        print("✅ SUCCESS! GitHub credential provider created")
        print("=" * 70)
        print()
        print(f"Provider ARN: {response['credentialProviderArn']}")
        print()
        print("📝 Next steps:")
        print("   1. Deploy your agent:")
        print("      agentcore configure -e src/agents/github_agent/runtime.py")
        print("      agentcore launch")
        print()
        print("   2. Test your agent:")
        print("      agentcore invoke '{\"prompt\": \"list my repositories\"}'")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR: Failed to create credential provider")
        print("=" * 70)
        print()
        print(f"Error: {e}")
        print()
        print("💡 Common issues:")
        print("   - AWS credentials not configured")
        print("   - No Bedrock AgentCore access in your region")
        print("   - Credential provider with same name already exists")
        print()
        print("🔧 To fix:")
        print("   - Run: aws configure")
        print("   - Check region has AgentCore: ap-southeast-2, us-west-2, ap-southeast-2, eu-central-1")
        print("   - Delete existing provider if needed")
        print()

        return 1


if __name__ == "__main__":
    sys.exit(main())
