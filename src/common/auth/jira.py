"""JIRA authentication using AgentCore Identity with Atlassian OAuth 2.0.

Uses OAuth 2.0 tokens stored in AgentCore Identity per user.
No API token fallback - OAuth only.
"""

from typing import Dict, Optional

# Import AgentCore Identity
try:
    import bedrock_agentcore.identity.gettoken as identity_gettoken
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False

from src.common.config.jira_config import get_jira_url


# Global state
_jira_headers: Optional[Dict[str, str]] = None
_jira_url: Optional[str] = None


async def get_jira_auth_headers() -> Dict[str, str]:
    """Get JIRA authentication headers using OAuth 2.0.

    Gets OAuth access token from AgentCore Identity jira-provider.
    No fallback - requires proper OAuth setup.

    Returns:
        HTTP headers with Bearer token authentication

    Raises:
        Exception: If OAuth token not available
    """
    global _jira_headers, _jira_url

    if _jira_headers:
        return _jira_headers

    # Get JIRA URL
    _jira_url = get_jira_url()

    # Get OAuth token from AgentCore Identity
    if not IDENTITY_AVAILABLE:
        raise Exception("AgentCore Identity not available. Cannot authenticate with JIRA.")

    try:
        token_response = await identity_gettoken.get_token(
            provider="jira-provider"
        )
        if not token_response or "accessToken" not in token_response:
            raise Exception("No access token in response from AgentCore Identity")

        access_token = token_response["accessToken"]
        print("✅ Using JIRA OAuth token from AgentCore Identity")

    except Exception as e:
        raise Exception(f"Failed to get JIRA OAuth token from AgentCore Identity: {e}")

    # Create Bearer token header for OAuth 2.0
    _jira_headers = {
        "Authorization": f"Bearer {access_token}",
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
