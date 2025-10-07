"""GitHub OAuth integration using AgentCore Identity.

This module implements GitHub OAuth using bedrock_agentcore's @requires_access_token decorator.
Follows the official AWS sample: runtime_with_strands_and_egress_github_3lo.ipynb
"""

import asyncio
from typing import Optional
from bedrock_agentcore.identity.auth import requires_access_token

# Global token storage (set by OAuth flow)
github_access_token: Optional[str] = None


async def on_auth_url(url: str):
    """Callback for authorization URL.

    In AgentCore Runtime, this URL is returned to the user for authorization.
    In local testing, we would print it or open browser.

    Args:
        url: Authorization URL for user to visit
    """
    print(f"\n{'=' * 60}")
    print(f"🔐 GitHub Authorization Required")
    print(f"{'=' * 60}")
    print(f"\n🌐 Please visit this URL to authorize:")
    print(f"   {url}")
    print(f"\n{'=' * 60}\n")


@requires_access_token(
    provider_name="github-provider",  # Must match credential provider name
    scopes=["repo", "read:user"],     # GitHub OAuth scopes
    auth_flow='USER_FEDERATION',       # 3LO (on-behalf-of user)
    on_auth_url=on_auth_url,           # Authorization URL callback
    force_authentication=True,         # Always prompt for auth
)
async def get_github_access_token(*, access_token: str) -> str:
    """Get GitHub access token via AgentCore Identity.

    This function is decorated with @requires_access_token which handles:
    - OAuth flow with GitHub
    - Token exchange
    - Secure token storage via AgentCore Identity

    Args:
        access_token: Access token injected by decorator

    Returns:
        Access token string
    """
    global github_access_token
    github_access_token = access_token
    print(f"✅ GitHub access token received")
    print(f"   Token: {access_token[:20]}...")
    return access_token


async def ensure_github_token() -> str:
    """Ensure GitHub access token is available.

    Calls get_github_access_token if token not yet retrieved.

    Returns:
        Access token string

    Raises:
        Exception: If token retrieval fails
    """
    global github_access_token

    if not github_access_token:
        print("🔄 Retrieving GitHub access token...")
        await get_github_access_token()

    return github_access_token


def get_cached_token() -> Optional[str]:
    """Get cached GitHub token if available.

    Returns:
        Cached token or None
    """
    return github_access_token


# Synchronous wrapper for backwards compatibility
def get_github_token_sync() -> Optional[str]:
    """Synchronous wrapper to get GitHub token.

    Returns:
        Token if available, None otherwise
    """
    global github_access_token

    if github_access_token:
        return github_access_token

    # Try to get token asynchronously
    try:
        return asyncio.run(ensure_github_token())
    except Exception as e:
        print(f"❌ Failed to get GitHub token: {e}")
        return None
