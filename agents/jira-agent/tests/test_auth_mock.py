"""Tests for mock JIRA authentication.

Tests the MockJiraAuth implementation for local testing and development.
"""

import pytest
from src.auth.mock import MockJiraAuth


class TestMockJiraAuth:
    """Test suite for MockJiraAuth class."""

    @pytest.mark.asyncio
    async def test_mock_auth_returns_token(self):
        """Test that mock auth returns a valid token immediately.

        Verifies:
        - Token is returned without network calls
        - Token has expected format
        - Token is consistent across calls
        """
        auth = MockJiraAuth()
        token = await auth.get_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        assert token == "mock_jira_token_for_local_testing"

    @pytest.mark.asyncio
    async def test_mock_auth_returns_consistent_token(self):
        """Test that mock auth returns the same token on multiple calls.

        Verifies:
        - Token is stable across calls
        - No randomization or regeneration
        """
        auth = MockJiraAuth()
        token1 = await auth.get_token()
        token2 = await auth.get_token()

        assert token1 == token2

    def test_mock_auth_headers(self):
        """Test that mock auth returns proper HTTP headers.

        Verifies:
        - Authorization header with Bearer token
        - Content-Type and Accept headers
        - Headers format matches JIRA API requirements
        """
        auth = MockJiraAuth()
        headers = auth.get_auth_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")
        assert "mock_jira_token_for_local_testing" in headers["Authorization"]
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    def test_mock_auth_jira_url(self):
        """Test that mock auth returns configured JIRA URL.

        Verifies:
        - URL is returned from environment
        - URL format is valid
        - No trailing slashes
        """
        auth = MockJiraAuth()
        url = auth.get_jira_url()

        assert url is not None
        assert isinstance(url, str)
        assert url.startswith("https://")
        assert not url.endswith("/")
        # From test environment setup
        assert "atlassian.net" in url

    def test_mock_auth_is_authenticated(self):
        """Test that mock auth always reports as authenticated.

        Verifies:
        - is_authenticated returns True
        - No OAuth flow required
        - Immediate authentication status
        """
        auth = MockJiraAuth()
        assert auth.is_authenticated() is True

    def test_mock_auth_cloud_id(self):
        """Test that mock auth provides a cloud ID.

        Verifies:
        - Cloud ID is available
        - Cloud ID format is consistent
        """
        auth = MockJiraAuth()
        cloud_id = auth.get_cloud_id()

        assert cloud_id is not None
        assert isinstance(cloud_id, str)
        assert len(cloud_id) > 0
        assert cloud_id == "mock_cloud_id"

    def test_mock_auth_initialization(self, capsys):
        """Test that mock auth prints initialization message.

        Verifies:
        - Initialization message is printed
        - Message indicates testing mode
        - Warning about API call limitations
        """
        MockJiraAuth()
        captured = capsys.readouterr()

        assert "Mock Jira Auth initialized" in captured.out
        assert "LOCAL TESTING MODE" in captured.out
        assert "API calls will fail" in captured.out

    @pytest.mark.asyncio
    async def test_mock_auth_multiple_instances(self):
        """Test that multiple mock auth instances work independently.

        Verifies:
        - Multiple instances can be created
        - Each instance has its own state
        - Tokens are consistent across instances
        """
        auth1 = MockJiraAuth()
        auth2 = MockJiraAuth()

        token1 = await auth1.get_token()
        token2 = await auth2.get_token()

        assert token1 == token2
        assert auth1.is_authenticated()
        assert auth2.is_authenticated()

    def test_mock_auth_base_url_format(self):
        """Test JIRA base URL configuration.

        Verifies:
        - Base URL from environment is properly formatted
        - URL doesn't have trailing slash
        - URL includes protocol
        """
        auth = MockJiraAuth()
        base_url = auth.get_jira_url()

        assert base_url.startswith("https://")
        assert not base_url.endswith("/")

    def test_mock_auth_header_structure(self):
        """Test authentication header structure.

        Verifies:
        - All required headers are present
        - Header values are properly formatted
        - No extra or missing headers
        """
        auth = MockJiraAuth()
        headers = auth.get_auth_headers()

        required_headers = ["Authorization", "Content-Type", "Accept"]
        for header in required_headers:
            assert header in headers

        assert len(headers) == 3  # Exactly the required headers
