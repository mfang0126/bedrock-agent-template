"""
GitHub OAuth authentication using AgentCore Identity.

This module implements real GitHub OAuth using bedrock_agentcore's
@requires_access_token decorator. This is the production authentication
implementation used when deployed to AWS AgentCore Runtime.
"""

import asyncio
import logging
from typing import Callable, Optional

from bedrock_agentcore.identity.auth import requires_access_token
from .interface import GitHubAuth

logger = logging.getLogger(__name__)


class AgentCoreGitHubAuth(GitHubAuth):
    """GitHub OAuth authentication via AgentCore Identity.

    Implements real GitHub OAuth 3LO (three-legged OAuth) flow using
    AWS Bedrock AgentCore's identity management system.

    The @requires_access_token decorator handles:
    - OAuth flow with GitHub
    - Token exchange and secure storage
    - Automatic token refresh
    - User federation (on-behalf-of semantics)

    This implementation is used in dev and production environments.
    """

    def __init__(self, oauth_url_callback: Optional[Callable[[str], None]] = None):
        """Initialize AgentCore GitHub authentication.

        Args:
            oauth_url_callback: Optional callback to stream OAuth URLs back to runtime
                              for display to user
        """
        self._token: Optional[str] = None
        self._oauth_url_callback = oauth_url_callback
        self._pending_oauth_url: Optional[str] = None
        logger.info("🔐 AgentCore GitHub Auth initialized - PRODUCTION MODE")

    async def _on_auth_url(self, url: str):
        """Callback for authorization URL.

        Stores URL and triggers callback to stream back to user.

        Args:
            url: Authorization URL for user to visit
        """
        self._pending_oauth_url = url

        logger.info("=" * 60)
        logger.info("🔐 GitHub Authorization Required")
        logger.info("=" * 60)
        logger.info(f"🌐 Authorization URL generated: {url}")
        logger.info("=" * 60)

        # Trigger immediate callback to stream URL back to user
        if self._oauth_url_callback:
            try:
                if asyncio.iscoroutinefunction(self._oauth_url_callback):
                    await self._oauth_url_callback(url)
                else:
                    self._oauth_url_callback(url)
            except Exception as e:
                logger.error(f"⚠️ Error in OAuth URL callback: {e}")

    @requires_access_token(
        provider_name="github-provider",  # Must match credential provider name
        scopes=["repo", "read:user"],  # GitHub OAuth scopes
        auth_flow="USER_FEDERATION",  # 3LO (on-behalf-of user)
        # Note: on_auth_url will be bound to instance method in get_token()
        force_authentication=False,  # Don't force re-auth if token exists
    )
    async def _get_github_access_token(self, *, access_token: str) -> str:
        """Get GitHub access token via AgentCore Identity.

        This method is decorated with @requires_access_token which handles OAuth.

        Args:
            access_token: Access token injected by decorator

        Returns:
            Access token string
        """
        self._token = access_token
        logger.info(f"✅ GitHub access token received")
        logger.debug(f"   Token: {access_token[:20]}...")
        return access_token

    async def get_token(self) -> str:
        """Get a valid GitHub access token.

        Initiates OAuth flow if not already authenticated.

        Returns:
            str: GitHub personal access token with repo and read:user scopes

        Raises:
            ValueError: If authentication fails
        """
        if not self._token:
            logger.info("🔄 Retrieving GitHub access token via OAuth...")
            try:
                # Dynamically bind on_auth_url callback to the decorator
                # This is necessary because the decorator is applied at method definition
                # but we need instance-specific callback
                original_decorator = self._get_github_access_token.__wrapped__

                # Create new decorated function with our callback
                @requires_access_token(
                    provider_name="github-provider",
                    scopes=["repo", "read:user"],
                    auth_flow="USER_FEDERATION",
                    on_auth_url=self._on_auth_url,
                    force_authentication=False,
                )
                async def _oauth_with_callback(*, access_token: str) -> str:
                    self._token = access_token
                    logger.info("✅ GitHub access token received")
                    logger.debug(f"   Token: {access_token[:20]}...")
                    return access_token

                await _oauth_with_callback()

            except Exception as e:
                logger.error(f"❌ Failed to get GitHub token: {e}")
                raise ValueError(f"GitHub authentication failed: {e}")

        return self._token

    def is_authenticated(self) -> bool:
        """Check if authentication is complete and token is available.

        Returns:
            bool: True if authenticated, False otherwise
        """
        return self._token is not None

    def get_pending_oauth_url(self) -> Optional[str]:
        """Get pending OAuth URL if available.

        Returns:
            Optional[str]: OAuth URL waiting for user action, or None
        """
        return self._pending_oauth_url
