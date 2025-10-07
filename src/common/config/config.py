"""Configuration management for multi-agent platform.

Supports both local development (env vars) and production (AWS Secrets Manager).
"""

import os
import json
from typing import Dict, Optional
from dotenv import load_dotenv


class Config:
    """Configuration manager for multi-agent platform."""

    def __init__(self, environment: str = "local"):
        """Initialize configuration.

        Args:
            environment: "local" or "production"
        """
        self.environment = environment

        # Load .env file if in local mode
        if environment == "local":
            load_dotenv()

    def get_github_credentials(self) -> Dict[str, str]:
        """Get GitHub OAuth credentials.

        Returns:
            Dict with 'client_id' and 'client_secret'

        Raises:
            ValueError: If credentials are not configured
        """
        if self.environment == "local":
            return self._get_from_env()
        else:
            return self._get_from_secrets_manager()

    def _get_from_env(self) -> Dict[str, str]:
        """Get credentials from environment variables."""
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise ValueError(
                "GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set. "
                "Copy .env.example to .env and add your credentials."
            )

        return {
            "client_id": client_id,
            "client_secret": client_secret,
        }

    def _get_from_secrets_manager(self) -> Dict[str, str]:
        """Get credentials from AWS Secrets Manager (production)."""
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError:
            raise ImportError("boto3 is required for AWS Secrets Manager integration")

        secret_name = "github-agent/credentials"
        region = os.getenv("AWS_REGION", "us-east-1")

        client = boto3.client("secretsmanager", region_name=region)

        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response["SecretString"])

            return {
                "client_id": secret["client_id"],
                "client_secret": secret["client_secret"],
            }
        except ClientError as e:
            print(f"❌ Error fetching secrets from AWS Secrets Manager: {e}")
            raise

    def get_aws_region(self) -> str:
        """Get AWS region."""
        return os.getenv("AWS_REGION", "us-east-1")
