#!/usr/bin/env python3
"""Setup Atlassian OAuth credential provider for JIRA in AWS Bedrock AgentCore.

This script creates the Atlassian OAuth2 credential provider required for the JIRA agent.
Run this BEFORE deploying the JIRA agent.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from common.auth.credential_provider import CredentialProviderManager
from common.config.config import Config

def main():
    print("=" * 70)
    print("🔐 Atlassian OAuth Credential Provider Setup (JIRA)")
    print("=" * 70)
    print()

    # Get configuration
    config = Config(environment="local")

    try:
        credentials = config.get_atlassian_credentials()
    except ValueError as e:
        print(f"❌ Error: {e}")
        print()
        print("📝 Setup instructions:")
        print("   1. Create an Atlassian OAuth 2.0 app at:")
        print("      https://developer.atlassian.com/console/myapps/")
        print("   2. Configure OAuth 2.0 integration")
        print("   3. Add callback URL for AgentCore (provided after app creation)")
        print("   4. Add credentials to .env file:")
        print("      ATLASSIAN_CLIENT_ID=your_client_id")
        print("      ATLASSIAN_CLIENT_SECRET=your_client_secret")
        print("      JIRA_URL=https://your-domain.atlassian.net")
        print("   5. Run this script again")
        return 1

    client_id = credentials["client_id"]
    client_secret = credentials["client_secret"]
    region = config.get_aws_region()

    print("✅ Atlassian OAuth credentials loaded")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Region: {region}")
    print()

    # Create credential provider
    print("📡 Creating Atlassian credential provider in AgentCore...")
    print()

    try:
        manager = CredentialProviderManager(region=region)

        response = manager.create_atlassian_provider(
            name="jira-provider",
            client_id=client_id,
            client_secret=client_secret
        )

        print()
        print("=" * 70)
        print("✅ SUCCESS! Atlassian credential provider created")
        print("=" * 70)
        print()
        print(f"Provider ARN: {response['credentialProviderArn']}")
        print()
        print("📝 Next steps:")
        print("   1. Deploy your JIRA agent:")
        print("      uv run poe deploy-jira")
        print()
        print("   2. Test your agent (user will authorize via browser):")
        print("      uv run poe invoke-jira '{\"prompt\": \"Get details for PROJ-123\"}' --user-id \"test\"")
        print()
        print("   Note: Each user must authorize the app on first use.")
        print("   Tokens are stored securely per-user in AgentCore Identity.")
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
        print("   - Atlassian OAuth vendor not supported in this region")
        print()
        print("🔧 To fix:")
        print("   - Run: aws configure")
        print("   - Check region has AgentCore: us-east-1, us-west-2, ap-southeast-2, eu-central-1")
        print("   - Delete existing provider: aws bedrock-agentcore-control delete-oauth2-credential-provider")
        print("   - Verify Atlassian OAuth support: aws bedrock-agentcore-control list-oauth2-credential-provider-vendors")
        print()

        return 1


if __name__ == "__main__":
    sys.exit(main())
