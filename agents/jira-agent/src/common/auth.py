"""JIRA authentication using AgentCore Identity with Atlassian OAuth 2.0.

Production-only implementation using OAuth 2.0 tokens from AgentCore Identity.
Uses @requires_access_token decorator for OAuth flow management.
"""

from typing import Dict, Optional

from bedrock_agentcore.identity.auth import requires_access_token

from src.common.config import get_jira_url


# Global state
_jira_access_token: Optional[str] = None
_jira_headers: Optional[Dict[str, str]] = None
_jira_url: Optional[str] = None


async def on_jira_auth_url(url: str):
    """Callback for JIRA authorization URL.

    Args:
        url: Authorization URL for user to visit
    """
    print(f"\n{'=' * 60}")
    print(f"🔐 JIRA Authorization Required")
    print(f"{'=' * 60}")
    print(f"\n🌐 Authorization URL:")
    print(f"   {url}")
    print(f"\n{'=' * 60}\n")


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
    global _jira_access_token
    _jira_access_token = access_token
    print(f"✅ JIRA access token received")
    print(f"   Token: {access_token[:20]}...")
    return access_token


async def get_jira_auth_headers() -> Dict[str, str]:
    """Get JIRA authentication headers using AgentCore Identity OAuth 2.0.

    Returns:
        HTTP headers with OAuth Bearer token

    Raises:
        Exception: If OAuth authentication fails
    """
    global _jira_headers, _jira_url, _jira_access_token

    if _jira_headers:
        return _jira_headers

    # Get JIRA URL
    _jira_url = get_jira_url()

    # Get OAuth token via decorator
    if not _jira_access_token:
        print("🔄 Retrieving JIRA access token...")
        await get_jira_access_token()

    print("✅ Using JIRA OAuth token from AgentCore Identity")

    _jira_headers = {
        "Authorization": f"Bearer {_jira_access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    return _jira_headers


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