"""Jira Authentication Interface - Abstract base for dependency injection.

This module defines the interface for Jira authentication implementations,
enabling both local testing (mock) and production deployment (OAuth).
"""

from abc import ABC, abstractmethod


class JiraAuth(ABC):
    """Abstract interface for Jira authentication.

    This interface enables dependency injection, allowing different
    authentication implementations for different environments:
    - MockJiraAuth: For local testing without OAuth
    - AgentCoreJiraAuth: For production with OAuth 2.0

    Example:
        >>> # Local testing
        >>> auth = MockJiraAuth()
        >>> token = await auth.get_token()  # Returns mock token
        >>>
        >>> # Production
        >>> auth = AgentCoreJiraAuth(oauth_url_callback)
        >>> token = await auth.get_token()  # Triggers OAuth if needed
    """

    @abstractmethod
    async def get_token(self) -> str:
        """Get Jira access token.

        Returns:
            Access token string for Jira API authentication

        Raises:
            Exception: If authentication fails
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if token is available, False otherwise
        """
        pass

    @abstractmethod
    def get_jira_url(self) -> str:
        """Get Jira API base URL.

        For OAuth 2.0: Returns cloud-based API URL with cloud ID
        For testing: Returns configured Jira URL

        Returns:
            Jira API base URL
        """
        pass

    @abstractmethod
    def get_auth_headers(self) -> dict:
        """Get authentication headers for HTTP requests.

        Returns:
            Dictionary with Authorization and other headers

        Raises:
            Exception: If not authenticated
        """
        pass
