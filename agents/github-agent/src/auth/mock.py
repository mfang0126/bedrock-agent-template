"""
Mock GitHub authentication for local testing.

This module provides a mock authentication implementation that returns
a fake token, enabling local development and testing without OAuth flow.
"""

import logging
from .interface import GitHubAuth

logger = logging.getLogger(__name__)


class MockGitHubAuth(GitHubAuth):
    """Mock GitHub authentication for local testing.

    Returns a hardcoded token for development and testing purposes.
    This allows testing agent logic without deploying to AgentCore
    or completing OAuth flows.

    Warning:
        This should NEVER be used in production environments.
        Set AGENT_ENV=local to enable mock mode.
    """

    def __init__(self):
        """Initialize mock authentication."""
        self._token = "ghp_mock_token_for_local_testing"
        logger.info("🧪 Mock GitHub Auth initialized - LOCAL TESTING MODE")
        logger.warning("⚠️  Using mock authentication - not for production!")

    async def get_token(self) -> str:
        """Get the mock GitHub access token.

        Returns:
            str: Mock token for testing
        """
        logger.debug("Returning mock GitHub token")
        return self._token

    def is_authenticated(self) -> bool:
        """Check if mock authentication is available.

        Returns:
            bool: Always True for mock auth
        """
        return True
