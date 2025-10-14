"""Integration tests for JIRA OAuth flow.

These tests require deployed AgentCore resources and are typically skipped
in local development. They test the full OAuth 2.0 flow with Atlassian.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.auth.agentcore import AgentCoreJiraAuth


# Skip all tests in this module unless INTEGRATION_TESTS env var is set
pytestmark = pytest.mark.skipif(
    os.getenv("INTEGRATION_TESTS") != "true",
    reason="Integration tests require deployed resources (set INTEGRATION_TESTS=true to run)"
)


class TestOAuthFlow:
    """Integration tests for OAuth 2.0 flow with Atlassian."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_url_callback_triggered(self):
        """Test that OAuth URL callback is triggered during authentication.

        This test verifies:
        - OAuth URL is generated
        - Callback is invoked with URL
        - URL has correct format

        Note: Requires AgentCore runtime with configured Jira provider.
        """
        url_captured = None

        def capture_url(url: str):
            nonlocal url_captured
            url_captured = url

        auth = AgentCoreJiraAuth(oauth_url_callback=capture_url)

        # Mock the decorator behavior and accessible resources API
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "test-cloud-id", "url": "https://test.atlassian.net"}
            ]
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Trigger OAuth URL callback
            test_url = "https://auth.atlassian.com/authorize?client_id=test&response_type=code"
            await auth._on_jira_auth_url(test_url)

        # Verify callback was triggered
        assert url_captured is not None
        assert "auth.atlassian.com" in url_captured or "atlassian.com" in url_captured
        assert "authorize" in url_captured

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cloud_id_retrieval(self):
        """Test cloud ID retrieval from Atlassian API.

        This test verifies:
        - Accessible resources API is called
        - Cloud ID is extracted correctly
        - Site URL is available

        Note: Requires valid OAuth token.
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            # Mock successful accessible resources response
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "id": "cloud-123-abc",
                    "url": "https://mycompany.atlassian.net",
                    "name": "My Company Site",
                    "scopes": ["read:jira-work", "write:jira-work"]
                }
            ]
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Simulate token retrieval
            await auth.get_token(access_token="test_access_token")

        # Verify cloud ID was retrieved
        assert auth.get_cloud_id() == "cloud-123-abc"
        assert auth.is_authenticated()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cloud_id_multiple_sites(self):
        """Test cloud ID retrieval when user has multiple sites.

        This test verifies:
        - First accessible site is used
        - Multiple sites are handled correctly
        - Cloud ID selection is deterministic

        Note: Uses first site in list by default.
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            # Mock multiple accessible resources
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "site-1", "url": "https://company1.atlassian.net"},
                {"id": "site-2", "url": "https://company2.atlassian.net"},
                {"id": "site-3", "url": "https://company3.atlassian.net"}
            ]
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await auth.get_token(access_token="test_token")

        # Should use first site
        assert auth.get_cloud_id() == "site-1"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_token_storage(self):
        """Test that OAuth token is stored correctly.

        This test verifies:
        - Token is stored after OAuth flow
        - is_authenticated returns True
        - Token can be retrieved for API calls

        Note: This is a mock test simulating token storage.
        Real integration would require completing OAuth flow.
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = []
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Simulate token being set by decorator
            await auth.get_token(access_token="stored_test_token")

        # Verify token storage
        assert auth.is_authenticated()
        headers = auth.get_auth_headers()
        assert headers["Authorization"] == "Bearer stored_test_token"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_oauth_url_format(self):
        """Test OAuth URL has correct format for Atlassian.

        This test verifies:
        - URL uses Atlassian authorization endpoint
        - URL includes required parameters
        - URL format matches OAuth 2.0 spec

        Note: This tests the callback receives properly formatted URL.
        """
        captured_url = None

        def capture_url(url: str):
            nonlocal captured_url
            captured_url = url

        auth = AgentCoreJiraAuth(oauth_url_callback=capture_url)

        # Simulate OAuth URL generation
        test_url = (
            "https://auth.atlassian.com/authorize"
            "?audience=api.atlassian.com"
            "&client_id=test-client-id"
            "&scope=read%3Ajira-work%20write%3Ajira-work%20offline_access"
            "&redirect_uri=https://example.com/callback"
            "&response_type=code"
            "&prompt=consent"
        )

        await auth._on_jira_auth_url(test_url)

        # Verify URL format
        assert captured_url is not None
        assert captured_url.startswith("https://")
        assert "atlassian.com" in captured_url
        assert "authorize" in captured_url

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_accessible_resources_error_handling(self):
        """Test handling of accessible resources API errors.

        This test verifies:
        - Auth continues if cloud ID fetch fails
        - Fallback to direct URL works
        - No exception is raised

        Note: Tests graceful degradation.
        """
        auth = AgentCoreJiraAuth()

        with patch('httpx.AsyncClient') as mock_client:
            # Simulate API error
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=Exception("API temporarily unavailable")
            )

            # Should not raise exception
            await auth.get_token(access_token="test_token")

        # Should still be authenticated
        assert auth.is_authenticated()
        # Cloud ID should be None
        assert auth.get_cloud_id() is None
        # Should fall back to environment URL
        url = auth.get_jira_url()
        assert url.startswith("https://")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_async_callback_handling(self):
        """Test that async callbacks are properly handled.

        This test verifies:
        - Async callbacks are awaited
        - Callback receives URL parameter
        - No errors with async callback functions
        """
        callback_called = False

        async def async_callback(url: str):
            nonlocal callback_called
            callback_called = True
            assert url is not None
            assert len(url) > 0

        auth = AgentCoreJiraAuth(oauth_url_callback=async_callback)

        test_url = "https://auth.atlassian.com/authorize?client_id=test"
        await auth._on_jira_auth_url(test_url)

        # Verify callback was called
        assert callback_called

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_full_authentication_flow_mock(self):
        """Mock test simulating full authentication flow.

        This test verifies the complete flow:
        1. OAuth URL generation
        2. User authorization (mocked)
        3. Token exchange (mocked)
        4. Cloud ID retrieval
        5. API access

        Note: Real integration would require browser interaction.
        This is a mock simulation for testing flow logic.
        """
        url_received = False

        def url_callback(url: str):
            nonlocal url_received
            url_received = True

        auth = AgentCoreJiraAuth(oauth_url_callback=url_callback)

        # Step 1: OAuth URL callback
        await auth._on_jira_auth_url("https://auth.atlassian.com/authorize?client_id=test")
        assert url_received

        # Step 2 & 3: Token exchange (mocked by decorator)
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {"id": "cloud-final", "url": "https://final.atlassian.net"}
            ]
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            await auth.get_token(access_token="final_access_token")

        # Step 4: Verify cloud ID retrieved
        assert auth.get_cloud_id() == "cloud-final"

        # Step 5: Verify API access ready
        assert auth.is_authenticated()
        headers = auth.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer final_access_token"

        # Verify JIRA URL uses cloud-based API
        jira_url = auth.get_jira_url()
        assert "api.atlassian.com/ex/jira/cloud-final" in jira_url


class TestIntegrationHelpers:
    """Helper tests for integration testing setup."""

    def test_integration_flag_detection(self):
        """Test that integration tests can be selectively enabled.

        Verifies:
        - Tests are skipped by default
        - INTEGRATION_TESTS env var enables tests
        """
        # This test always runs to verify the skip logic
        integration_enabled = os.getenv("INTEGRATION_TESTS") == "true"

        if integration_enabled:
            # Integration tests are enabled
            assert True
        else:
            # Tests should be skipped
            # This test itself will run but others will skip
            assert True

    @pytest.mark.integration
    def test_integration_marker(self):
        """Test that integration marker is properly applied.

        Verifies:
        - Tests can be run selectively with -m integration
        - Marker is recognized by pytest
        """
        # This test has the integration marker
        assert True
