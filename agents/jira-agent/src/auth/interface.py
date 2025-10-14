"""Jira Authentication Interface - Protocol-based for dependency injection.

This module defines the interface for Jira authentication implementations,
enabling both local testing (mock) and production deployment (OAuth).
"""

from typing import Protocol, runtime_checkable


@runtime_checkable


class JiraAuth(Protocol):
    """Protocol interface for Jira authentication.

    This protocol enables dependency injection through structural subtyping,
    allowing different authentication implementations for different environments:
    - MockJiraAuth: For local testing without OAuth
    - AgentCoreJiraAuth: For production with OAuth 2.0

    Any class implementing these methods satisfies the protocol, enabling
    flexible authentication strategies without explicit inheritance.

    Example:
        >>> # Local testing
        >>> auth = MockJiraAuth()
        >>> token = await auth.get_token()  # Returns mock token
        >>>
        >>> # Production
        >>> auth = AgentCoreJiraAuth(oauth_url_callback)
        >>> token = await auth.get_token()  # Triggers OAuth if needed
    """

    async def get_token(self) -> str:
        """Get Jira access token.

        Returns:
            Access token string for Jira API authentication

        Raises:
            Exception: If authentication fails
        """
        ...

    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if token is available, False otherwise
        """
        ...

    def get_jira_url(self) -> str:
        """Get Jira API base URL.

        For OAuth 2.0: Returns cloud-based API URL with cloud ID
        For testing: Returns configured Jira URL

        Returns:
            Jira API base URL
        """
        ...

    def get_auth_headers(self) -> dict:
        """Get authentication headers for HTTP requests.

        Returns:
            Dictionary with Authorization and other headers

        Raises:
            Exception: If not authenticated
        """
        ...
