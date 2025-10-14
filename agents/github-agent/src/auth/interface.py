"""
GitHub authentication interface for dependency injection.

This module defines the abstract interface for GitHub authentication,
enabling different implementations (mock for local testing, real OAuth for production).
"""

from abc import ABC, abstractmethod
from typing import Optional


class GitHubAuth(ABC):
    """Abstract base class for GitHub authentication providers.

    This interface allows the GitHub agent to work with different authentication
    strategies without coupling to a specific implementation:
    - MockGitHubAuth: For local testing without OAuth
    - AgentCoreGitHubAuth: For production with OAuth 3LO flow
    """

    @abstractmethod
    async def get_token(self) -> str:
        """Get a valid GitHub access token.

        Returns:
            str: GitHub personal access token with required scopes (repo, read:user)

        Raises:
            ValueError: If authentication has not been completed or token is invalid
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if authentication is complete and token is available.

        Returns:
            bool: True if authenticated, False otherwise
        """
        pass
