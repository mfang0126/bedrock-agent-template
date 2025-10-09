"""JIRA authentication using AgentCore Identity with Atlassian OAuth 2.0.

Production-only implementation using OAuth 2.0 tokens from AgentCore Identity.
Uses @requires_access_token decorator for OAuth flow management.
"""

import asyncio
from typing import Callable, Dict, Optional

from bedrock_agentcore.identity.auth import requires_access_token

from src.common.config import get_jira_url


# Global state
_jira_access_token: Optional[str] = None
_jira_headers: Optional[Dict[str, str]] = None
_jira_url: Optional[str] = None

# Global storage for OAuth URL to return to user
pending_oauth_url: Optional[str] = None

# Global callback to stream OAuth URL back to runtime
oauth_url_callback: Optional[Callable[[str], None]] = None


async def on_jira_auth_url(url: str):
    """Callback for JIRA authorization URL.

    Stores URL globally and triggers immediate streaming back to user via callback.

    Args:
        url: Authorization URL for user to visit
    """
    global pending_oauth_url, oauth_url_callback
    pending_oauth_url = url

    print(f"\n{'=' * 60}")
    print(f"🔐 JIRA Authorization Required")
    print(f"{'=' * 60}")
    print(f"\n🌐 Authorization URL:")
    print(f"   {url}")
    print(f"\n{'=' * 60}\n")

    # Trigger immediate callback to stream URL back to user
    if oauth_url_callback:
        try:
            if asyncio.iscoroutinefunction(oauth_url_callback):
                await oauth_url_callback(url)
            else:
                oauth_url_callback(url)
        except Exception as e:
            print(f"⚠️ Error in OAuth URL callback: {e}")


@requires_access_token(
    provider_name="jira-provider",  # Must match credential provider name
    scopes=["read:jira-work", "write:jira-work"],  # JIRA OAuth scopes
    auth_flow="USER_FEDERATION",  # 3LO (on-behalf-of user)
    on_auth_url=on_jira_auth_url,  # Authorization URL callback
    force_authentication=False,  # Don't force re-auth if token exists
)
async def get_jira_access_token(*, access_token: str) -> str:
    """Get JIRA access token via AgentCore Identity.

    This function is decorated with @requires_access_token which handles:
    - OAuth flow with JIRA/Atlassian
    - Token exchange
    - Secure token storage via AgentCore Identity
    - Automatic token refresh

    Args:
        access_token: Access token injected by decorator

    Returns:
        Access token string
    """
    global _jira_access_token, _jira_url
    _jira_access_token = access_token
    _jira_url = get_jira_url()  # Cache JIRA URL at token initialization
    print(f"✅ JIRA access token received")
    print(f"   Token: {access_token[:20]}...")
    return access_token


def get_jira_auth_headers() -> Dict[str, str]:
    """Get JIRA authentication headers from cached token.

    Returns:
        HTTP headers with OAuth Bearer token

    Raises:
        Exception: If no token available
    """
    global _jira_access_token

    if not _jira_access_token:
        raise Exception(
            "❌ JIRA token not initialized. Authentication must be called first."
        )

    return {
        "Authorization": f"Bearer {_jira_access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }


def get_jira_url_cached() -> str:
    """Get cached JIRA URL.

    Returns:
        JIRA base URL
    """
    if _jira_url:
        return _jira_url
    return get_jira_url()


def reset_jira_auth():
    """Reset JIRA authentication (for testing)."""
    global _jira_headers, _jira_url
    _jira_headers = None
    _jira_url = None