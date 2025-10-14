"""
GitHub authentication interface for dependency injection.

This module defines the Protocol interface for GitHub authentication,
enabling different implementations (mock for local testing, real OAuth for production).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class GitHubAuth(Protocol):
    """Protocol for GitHub authentication providers.

    This interface allows the GitHub agent to work with different authentication
    strategies without coupling to a specific implementation:
    - MockGitHubAuth: For local testing without OAuth
    - AgentCoreGitHubAuth: For production with OAuth 3LO flow

    Uses structural subtyping (PEP 544) - any class implementing these methods
    is compatible without explicit inheritance.
    """

    async def get_token(self) -> str:
        """Get a valid GitHub access token.

        Returns:
            str: GitHub personal access token with required scopes (repo, read:user)

        Raises:
            ValueError: If authentication has not been completed or token is invalid
        """
        ...

    def is_authenticated(self) -> bool:
        """Check if authentication is complete and token is available.

        Returns:
            bool: True if authenticated, False otherwise
        """
        ...
