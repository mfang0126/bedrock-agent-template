"""AgentCore Jira Authentication - Production OAuth 2.0 implementation.

This module provides OAuth 2.0 authentication for Jira using AgentCore Identity.
Handles token exchange, refresh, and cloud ID retrieval for Atlassian API access.
"""

import asyncio
import httpx
from typing import Callable, Optional

from bedrock_agentcore.identity.auth import requires_access_token

from .interface import JiraAuth
from src.common.config import get_jira_url


# Global reference to current auth instance for OAuth callback
_current_auth_instance: Optional['AgentCoreJiraAuth'] = None


async def _global_on_jira_auth_url(url: str) -> None:
    """Global OAuth URL callback that delegates to current auth instance.

    This is needed because the decorator requires a module-level callable,
    but we need instance-specific callback behavior.

    Args:
        url: Authorization URL for user to visit
    """
    if _current_auth_instance:
        await _current_auth_instance._on_jira_auth_url(url)


class AgentCoreJiraAuth(JiraAuth):
    """Production Jira authentication using AgentCore OAuth 2.0.

    This implementation handles:
    - OAuth 2.0 flow with Atlassian
    - Token exchange and refresh via AgentCore Identity
    - Cloud ID retrieval for Atlassian APIs
    - OAuth URL streaming back to user

    Args:
        oauth_url_callback: Function to call when OAuth URL is generated.
                           Used to stream URL back to user immediately.

    Example:
        >>> def stream_url(url: str):
        ...     print(f"Please visit: {url}")
        >>>
        >>> auth = AgentCoreJiraAuth(oauth_url_callback=stream_url)
        >>> token = await auth.get_token()  # Triggers OAuth if needed
        >>> headers = auth.get_auth_headers()
    """

    def __init__(self, oauth_url_callback: Optional[Callable[[str], None]] = None):
        """Initialize AgentCore Jira authentication.

        Args:
            oauth_url_callback: Optional callback for OAuth URL streaming
        """
        global _current_auth_instance
        _current_auth_instance = self

        self.oauth_url_callback = oauth_url_callback
        self._token: Optional[str] = None
        self._cloud_id: Optional[str] = None
        self._jira_url: Optional[str] = None
        self._pending_oauth_url: Optional[str] = None

    async def _on_jira_auth_url(self, url: str) -> None:
        """Internal callback for JIRA authorization URL.

        Stores URL and triggers immediate streaming back to user via callback.

        Args:
            url: Authorization URL for user to visit
        """
        self._pending_oauth_url = url

        print(f"\n{'=' * 60}")
        print(f"🔐 JIRA Authorization Required")
        print(f"{'=' * 60}")
        print(f"\n🌐 Authorization URL:")
        print(f"   {url}")
        print(f"\n{'=' * 60}\n")

        # Trigger immediate callback to stream URL back to user
        if self.oauth_url_callback:
            try:
                if asyncio.iscoroutinefunction(self.oauth_url_callback):
                    await self.oauth_url_callback(url)
                else:
                    self.oauth_url_callback(url)
            except Exception as e:
                print(f"⚠️ Error in OAuth URL callback: {e}")

    @requires_access_token(
        provider_name="jira-provider",  # Must match AgentCore Identity provider name
        scopes=["read:jira-work", "write:jira-work", "offline_access"],  # Jira OAuth scopes
        auth_flow="USER_FEDERATION",  # 3LO (Three-Legged OAuth)
        on_auth_url=_global_on_jira_auth_url,  # Module-level callback that delegates to instance
        force_authentication=False,  # Don't force re-auth if token exists
    )
    async def get_token(self, *, access_token: str) -> str:
        """Get Jira access token via AgentCore Identity.

        This method is decorated with @requires_access_token which handles:
        - OAuth 2.0 flow with Jira/Atlassian
        - Token exchange and validation
        - Secure token storage via AgentCore Identity
        - Automatic token refresh

        After getting the token, fetches accessible resources to get the cloud ID
        which is required for Atlassian OAuth 2.0 API calls.

        Args:
            access_token: Access token injected by decorator

        Returns:
            Access token string

        Raises:
            Exception: If authentication fails
        """
        self._token = access_token
        self._jira_url = get_jira_url()  # Cache Jira URL at token initialization

        print(f"✅ Jira access token received")
        print(f"   Token: {access_token[:20]}...")

        # Get accessible resources to retrieve cloud ID
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.atlassian.com/oauth/token/accessible-resources",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/json"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                resources = response.json()

                if resources and len(resources) > 0:
                    self._cloud_id = resources[0]["id"]
                    site_url = resources[0]["url"]
                    print(f"✅ Cloud ID retrieved: {self._cloud_id}")
                    print(f"   Site: {site_url}")
                else:
                    print(f"⚠️  No accessible resources found")

        except Exception as e:
            print(f"⚠️  Failed to get cloud ID: {e}")
            # Continue without cloud ID - will fall back to direct URL

        return access_token

    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if token is available, False otherwise
        """
        return self._token is not None

    def get_jira_url(self) -> str:
        """Get Jira API base URL.

        Returns cloud-based API URL if cloud ID is available (Atlassian OAuth 2.0),
        otherwise returns direct Jira URL (legacy/API token auth).

        Returns:
            Jira API base URL
        """
        # Use cloud-based API URL if cloud ID is available (Atlassian OAuth 2.0)
        if self._cloud_id:
            return f"https://api.atlassian.com/ex/jira/{self._cloud_id}"

        # Fallback to direct URL (legacy/API token auth)
        if self._jira_url:
            return self._jira_url
        return get_jira_url()

    def get_auth_headers(self) -> dict:
        """Get authentication headers for HTTP requests.

        Returns:
            Dictionary with OAuth Bearer token and content headers

        Raises:
            Exception: If no token available
        """
        if not self._token:
            raise Exception(
                "❌ Jira token not initialized. Authentication must be called first."
            )

        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def get_pending_oauth_url(self) -> Optional[str]:
        """Get pending OAuth URL if available.

        Used by runtime to check if OAuth URL was generated but not streamed.

        Returns:
            OAuth URL string or None
        """
        return self._pending_oauth_url

    def get_cloud_id(self) -> Optional[str]:
        """Get Atlassian cloud ID.

        Returns:
            Cloud ID string or None if not retrieved
        """
        return self._cloud_id
