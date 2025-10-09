"""JIRA authentication using AgentCore Identity with Atlassian OAuth 2.0.

Production-only implementation using OAuth 2.0 tokens from AgentCore Identity.
"""

from typing import Dict, Optional
import bedrock_agentcore.identity.gettoken as identity_gettoken

from src.common.config import get_jira_url


# Global state
_jira_headers: Optional[Dict[str, str]] = None
_jira_url: Optional[str] = None


async def get_jira_auth_headers() -> Dict[str, str]:
    """Get JIRA authentication headers using AgentCore Identity OAuth 2.0.

    Returns:
        HTTP headers with OAuth Bearer token

    Raises:
        Exception: If OAuth authentication fails
    """
    global _jira_headers, _jira_url

    if _jira_headers:
        return _jira_headers

    # Get JIRA URL
    _jira_url = get_jira_url()

    # Get OAuth token from AgentCore Identity
    token_response = await identity_gettoken.get_token(
        provider="jira-provider"
    )

    if not token_response or "accessToken" not in token_response:
        raise Exception(
            "Failed to get JIRA OAuth token from AgentCore Identity.\n"
            "Ensure jira-provider is configured in your AgentCore deployment."
        )

    access_token = token_response["accessToken"]
    print("✅ Using JIRA OAuth token from AgentCore Identity")

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