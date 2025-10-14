"""Tests for AgentCore JIRA authentication.

Tests the AgentCoreJiraAuth implementation for production OAuth flows.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.auth.agentcore import AgentCoreJiraAuth


class TestAgentCoreJiraAuth:
    """Test suite for AgentCoreJiraAuth class."""

    def test_agentcore_auth_initialization(self):
        """Test AgentCore auth initialization without callback.

        Verifies:
        - Auth can be created without callback
        - Initial state is not authenticated
        - No token or cloud ID initially
        """
        auth = AgentCoreJiraAuth()

        assert auth.oauth_url_callback is None
        assert auth.is_authenticated() is False
        assert auth._token is None
        assert auth._cloud_id is None

    def test_agentcore_auth_initialization_with_callback(self):
        """Test AgentCore auth initialization with callback.

        Verifies:
        - Callback is stored correctly
        - Initial state remains not authenticated
        """
        callback = MagicMock()
        auth = AgentCoreJiraAuth(oauth_url_callback=callback)

        assert auth.oauth_url_callback is callback
        assert auth.is_authenticated() is False

    @pytest.mark.asyncio
    async def test_oauth_url_callback_triggered(self, capsys):
        """Test that OAuth URL callback is triggered.

        Verifies:
        - Callback is called with OAuth URL
        - URL is printed to console
        - Pending URL is stored
        """
        callback = MagicMock()
        auth = AgentCoreJiraAuth(oauth_url_callback=callback)

        test_url = "https://auth.atlassian.com/authorize?client_id=test"
        await auth._on_jira_auth_url(test_url)

        captured = capsys.readouterr()
        assert "JIRA Authorization Required" in captured.out
        assert test_url in captured.out
        assert auth._pending_oauth_url == test_url
        callback.assert_called_once_with(test_url)

    @pytest.mark.asyncio
    async def test_oauth_url_callback_async(self):
        """Test async OAuth URL callback.

        Verifies:
        - Async callbacks are properly awaited
        - No errors with async callback functions
        """
        async_callback = AsyncMock()
        auth = AgentCoreJiraAuth(oauth_url_callback=async_callback)

        test_url = "https://auth.atlassian.com/authorize?client_id=test"
        await auth._on_jira_auth_url(test_url)

        async_callback.assert_called_once_with(test_url)

    @pytest.mark.asyncio
    async def test_oauth_url_callback_error_handling(self):
        """Test OAuth URL callback error handling.

        Verifies:
        - Callback errors are caught
        - Auth flow continues despite callback errors
        - Pending URL is still stored
        """
        def failing_callback(url):
            raise Exception("Callback failed")

        auth = AgentCoreJiraAuth(oauth_url_callback=failing_callback)
        test_url = "https://auth.atlassian.com/authorize?client_id=test"

        # Should not raise exception
        await auth._on_jira_auth_url(test_url)

        # URL should still be stored
        assert auth._pending_oauth_url == test_url

    @pytest.mark.asyncio
    async def test_get_token_sets_authentication_state(self):
        """Test that getting token updates authentication state.

        Note: This test mocks the decorator behavior since we can't
        actually test the full OAuth flow without AgentCore runtime.

        Verifies:
        - Token is stored correctly
        - is_authenticated returns True after token
        - JIRA URL is cached
        """
        auth = AgentCoreJiraAuth()

        # Mock the accessible resources API call
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "test-cloud-id", "url": "https://test.atlassian.net"}
            ]
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Simulate decorator injecting access token
            await auth.get_token(access_token="test_access_token")

        assert auth.is_authenticated() is True
        assert auth._token == "test_access_token"
        assert auth._cloud_id == "test-cloud-id"

    def test_get_auth_headers_without_token(self):
        """Test that getting headers without token raises error.

        Verifies:
        - Exception is raised when no token
        - Error message is descriptive
        """
        auth = AgentCoreJiraAuth()

        with pytest.raises(Exception) as exc_info:
            auth.get_auth_headers()

        assert "token not initialized" in str(exc_info.value).lower()
        assert "authentication must be called first" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_auth_headers_with_token(self):
        """Test getting auth headers after token is set.

        Verifies:
        - Headers include Bearer token
        - All required headers are present
        - Header format is correct
        """
        auth = AgentCoreJiraAuth()

        # Mock the accessible resources API call
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await auth.get_token(access_token="test_token")

        headers = auth.get_auth_headers()

        assert headers["Authorization"] == "Bearer test_token"
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"

    @pytest.mark.asyncio
    async def test_get_jira_url_with_cloud_id(self):
        """Test JIRA URL construction with cloud ID.

        Verifies:
        - Cloud-based API URL is used when cloud ID available
        - URL format matches Atlassian OAuth 2.0 pattern
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "cloud123", "url": "https://test.atlassian.net"}
            ]
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await auth.get_token(access_token="test_token")

        url = auth.get_jira_url()
        assert url == "https://api.atlassian.com/ex/jira/cloud123"

    @pytest.mark.asyncio
    async def test_get_jira_url_without_cloud_id(self):
        """Test JIRA URL fallback without cloud ID.

        Verifies:
        - Direct URL is used when cloud ID unavailable
        - Fallback to environment configuration
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = []  # No resources
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await auth.get_token(access_token="test_token")

        url = auth.get_jira_url()
        # Should fall back to environment URL
        assert url.startswith("https://")

    @pytest.mark.asyncio
    async def test_cloud_id_retrieval_error_handling(self):
        """Test cloud ID retrieval handles API errors gracefully.

        Verifies:
        - Auth continues even if cloud ID fetch fails
        - Token is still stored
        - No exception raised
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            # Simulate API error
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("API error")
            )

            # Should not raise exception
            await auth.get_token(access_token="test_token")

        # Token should still be set
        assert auth._token == "test_token"
        assert auth.is_authenticated()
        # Cloud ID should be None
        assert auth._cloud_id is None

    def test_get_pending_oauth_url_initially_none(self):
        """Test pending OAuth URL is None initially.

        Verifies:
        - No pending URL before OAuth flow
        - Returns None properly
        """
        auth = AgentCoreJiraAuth()
        assert auth.get_pending_oauth_url() is None

    @pytest.mark.asyncio
    async def test_get_pending_oauth_url_after_callback(self):
        """Test pending OAuth URL is available after callback.

        Verifies:
        - URL is stored during OAuth flow
        - URL can be retrieved for streaming
        """
        auth = AgentCoreJiraAuth()
        test_url = "https://auth.atlassian.com/authorize?client_id=test"

        await auth._on_jira_auth_url(test_url)

        assert auth.get_pending_oauth_url() == test_url

    def test_get_cloud_id_initially_none(self):
        """Test cloud ID is None before authentication.

        Verifies:
        - No cloud ID before token exchange
        - Returns None properly
        """
        auth = AgentCoreJiraAuth()
        assert auth.get_cloud_id() is None

    @pytest.mark.asyncio
    async def test_get_cloud_id_after_authentication(self):
        """Test cloud ID is available after authentication.

        Verifies:
        - Cloud ID is retrieved from Atlassian API
        - Cloud ID is stored correctly
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "cloud-xyz", "url": "https://test.atlassian.net"}
            ]
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await auth.get_token(access_token="test_token")

        assert auth.get_cloud_id() == "cloud-xyz"
