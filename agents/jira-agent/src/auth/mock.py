"""Mock Jira Authentication - For local testing without OAuth.

This module provides a mock authentication implementation that:
- Returns fake tokens immediately
- No network calls or OAuth flows
- Perfect for local development and testing
"""

from .interface import JiraAuth
from src.common.config import get_jira_url


class MockJiraAuth(JiraAuth):
    """Mock Jira authentication for local testing.

    This implementation provides instant authentication without
    requiring OAuth flows or network calls. Perfect for:
    - Local development
    - Unit testing
    - Architecture validation
    - Fast iteration cycles (<5 seconds)

    Example:
        >>> auth = MockJiraAuth()
        >>> token = await auth.get_token()
        >>> print(token)
        'mock_jira_token_for_local_testing'
        >>>
        >>> headers = auth.get_auth_headers()
        >>> print(headers['Authorization'])
        'Bearer mock_jira_token_for_local_testing'
    """

    def __init__(self) -> None:
        """Initialize mock authentication."""
        self._token = "mock_jira_token_for_local_testing"
        self._cloud_id = "mock_cloud_id"
        print("🧪 Mock Jira Auth initialized - LOCAL TESTING MODE")
        print("   Note: API calls will fail with mock token (testing structure only)")

    async def get_token(self) -> str:
        """Get mock Jira token.

        Returns immediately without any OAuth flow.

        Returns:
            Mock token string
        """
        return self._token

    def is_authenticated(self) -> bool:
        """Check if authenticated.

        Always returns True for mock auth.

        Returns:
            True
        """
        return True

    def get_jira_url(self) -> str:
        """Get Jira API URL for testing.

        Returns configured Jira URL from environment.
        For testing, this might point to a test instance or local mock.

        Returns:
            Jira API base URL
        """
        return get_jira_url()

    def get_auth_headers(self) -> dict:
        """Get mock authentication headers.

        Returns headers with mock Bearer token.

        Returns:
            Dictionary with Authorization header
        """
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_cloud_id(self) -> str:
        """Get mock cloud ID.

        Returns:
            Mock cloud ID string
        """
        return self._cloud_id
