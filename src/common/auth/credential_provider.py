"""Helper for creating and managing AgentCore credential providers.

This module provides utilities for setting up OAuth credential providers
in Amazon Bedrock AgentCore Identity service.
"""

import boto3
from typing import Dict, Optional


class CredentialProviderManager:
    """Manager for AgentCore OAuth credential providers."""

    def __init__(self, region: str = "ap-southeast-2"):
        """Initialize credential provider manager.

        Args:
            region: AWS region
        """
        self.region = region
        self.client = boto3.client('bedrock-agentcore-control', region_name=region)

    def create_github_provider(
        self,
        name: str,
        client_id: str,
        client_secret: str
    ) -> Dict:
        """Create GitHub OAuth2 credential provider.

        Args:
            name: Provider name (e.g., 'github-provider')
            client_id: GitHub OAuth App client ID
            client_secret: GitHub OAuth App client secret

        Returns:
            Provider creation response with ARN

        Example:
            >>> manager = CredentialProviderManager()
            >>> provider = manager.create_github_provider(
            ...     name='github-provider',
            ...     client_id='Ov23li...',
            ...     client_secret='64e941...'
            ... )
            >>> print(provider['credentialProviderArn'])
        """
        response = self.client.create_oauth2_credential_provider(
            name=name,
            credentialProviderVendor='GithubOauth2',
            oauth2ProviderConfigInput={
                'githubOauth2ProviderConfig': {
                    'clientId': client_id,
                    'clientSecret': client_secret
                }
            }
        )

        print(f"✅ GitHub credential provider created")
        print(f"   ARN: {response['credentialProviderArn']}")
        return response

    def create_atlassian_provider(
        self,
        name: str,
        client_id: str,
        client_secret: str
    ) -> Dict:
        """Create Atlassian OAuth2 credential provider for JIRA using custom OAuth.

        Args:
            name: Provider name (e.g., 'jira-provider')
            client_id: Atlassian OAuth App client ID
            client_secret: Atlassian OAuth App client secret

        Returns:
            Provider creation response with ARN

        Example:
            >>> manager = CredentialProviderManager()
            >>> provider = manager.create_atlassian_provider(
            ...     name='jira-provider',
            ...     client_id='abc123...',
            ...     client_secret='xyz789...'
            ... )
            >>> print(provider['credentialProviderArn'])

        Note:
            Uses customOauth2ProviderConfig since Atlassian is not a native provider.
            Supported native providers: GitHub, Google, Slack, Salesforce, Microsoft.
        """
        response = self.client.create_oauth2_credential_provider(
            name=name,
            credentialProviderVendor='CustomOauth2',
            oauth2ProviderConfigInput={
                'customOauth2ProviderConfig': {
                    'oauthDiscovery': {
                        'discoveryUrl': 'https://auth.atlassian.com/.well-known/openid-configuration'
                    },
                    'clientId': client_id,
                    'clientSecret': client_secret
                }
            }
        )

        print(f"✅ Atlassian credential provider created")
        print(f"   ARN: {response['credentialProviderArn']}")
        return response

    def list_providers(self) -> list:
        """List all credential providers.

        Returns:
            List of credential provider summaries
        """
        response = self.client.list_oauth2_credential_providers()
        return response.get('credentialProviderSummaries', [])

    def find_provider_by_name(self, name: str) -> Optional[Dict]:
        """Return provider summary for the given name if it exists."""
        for provider in self.list_providers():
            if provider.get('name') == name:
                return provider
        return None

    def delete_provider_by_name(self, name: str) -> bool:
        """Delete credential provider by name.

        Returns:
            True if a provider was deleted, False if not found.
        """
        provider = self.find_provider_by_name(name)
        if not provider:
            return False

        arn = provider.get('arn') or provider.get('credentialProviderArn')
        if not arn:
            raise ValueError(f"Provider {name} missing ARN")

        self.delete_provider(arn)
        return True

    def _delete_existing_provider(
        self,
        existing: Dict,
        provider_name: str
    ) -> None:
        """Delete provider referenced by an existing summary."""
        arn = existing.get('arn') or existing.get('credentialProviderArn')
        if not arn:
            raise ValueError(f"Existing provider '{provider_name}' missing ARN")

        print(f"♻️  Replacing existing provider '{provider_name}'")
        self.delete_provider(arn)

    def create_or_replace_github_provider(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        replace_existing: bool = False
    ) -> Dict:
        """Create GitHub provider, optionally replacing an existing one."""
        existing = self.find_provider_by_name(name)
        if existing and replace_existing:
            self._delete_existing_provider(existing, name)
        elif existing:
            raise ValueError(f"Provider '{name}' already exists")

        return self.create_github_provider(
            name=name,
            client_id=client_id,
            client_secret=client_secret
        )

    def create_or_replace_atlassian_provider(
        self,
        name: str,
        client_id: str,
        client_secret: str,
        replace_existing: bool = False
    ) -> Dict:
        """Create Atlassian provider, optionally replacing an existing one."""
        existing = self.find_provider_by_name(name)
        if existing and replace_existing:
            self._delete_existing_provider(existing, name)
        elif existing:
            raise ValueError(f"Provider '{name}' already exists")

        return self.create_atlassian_provider(
            name=name,
            client_id=client_id,
            client_secret=client_secret
        )

    def get_provider(self, provider_arn: str) -> Dict:
        """Get credential provider details.

        Args:
            provider_arn: Provider ARN

        Returns:
            Provider details
        """
        response = self.client.get_oauth2_credential_provider(
            credentialProviderArn=provider_arn
        )
        return response

    def delete_provider(self, provider_arn: str) -> None:
        """Delete credential provider.

        Args:
            provider_arn: Provider ARN
        """
        self.client.delete_oauth2_credential_provider(
            credentialProviderArn=provider_arn
        )
        print(f"✅ Credential provider deleted: {provider_arn}")


def setup_github_provider_from_env(replace_existing: bool = False) -> Optional[str]:
    """Setup GitHub credential provider using environment variables.

    Reads credentials from:
    - GITHUB_CLIENT_ID
    - GITHUB_CLIENT_SECRET
    - AWS_REGION (optional, defaults to ap-southeast-2)

    Returns:
        Provider ARN if successful, None otherwise
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    client_id = os.getenv('GITHUB_CLIENT_ID')
    client_secret = os.getenv('GITHUB_CLIENT_SECRET')
    region = os.getenv('AWS_REGION', 'ap-southeast-2')

    if not client_id or not client_secret:
        print("❌ Error: GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET required")
        return None

    try:
        manager = CredentialProviderManager(region=region)
        response = manager.create_or_replace_github_provider(
            name='github-provider',
            client_id=client_id,
            client_secret=client_secret,
            replace_existing=replace_existing
        )
        return response['credentialProviderArn']

    except Exception as e:
        print(f"❌ Failed to create credential provider: {e}")
        return None


if __name__ == "__main__":
    # Quick setup script
    print("🔐 GitHub Credential Provider Setup")
    print("=" * 60)

    arn = setup_github_provider_from_env()

    if arn:
        print(f"\n✅ Setup complete!")
        print(f"\nYou can now use this provider in your agent:")
        print(f"   provider_name='github-provider'")
    else:
        print(f"\n❌ Setup failed. Check your credentials.")
