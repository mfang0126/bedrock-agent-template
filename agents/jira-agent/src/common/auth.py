"""JIRA authentication using AgentCore Identity with Atlassian OAuth 2.0.

Uses OAuth 2.0 tokens stored in AgentCore Identity per user.
Fallback to API token for local testing.
"""

import os
from typing import Dict, Optional

# Import AgentCore Identity
try:
    import bedrock_agentcore.identity.gettoken as identity_gettoken
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False

from src.common.config import get_jira_url


# Global state
_jira_headers: Optional[Dict[str, str]] = None
_jira_url: Optional[str] = None


async def get_jira_auth_headers() -> Dict[str, str]:
    """Get JIRA authentication headers using OAuth 2.0 or API token.

    Priority:
    1. AgentCore Identity OAuth token (production)
    2. JIRA_API_TOKEN environment variable (local testing)
    3. JIRA_EMAIL + JIRA_API_TOKEN for Basic Auth (local testing)

    Returns:
        HTTP headers with authentication

    Raises:
        Exception: If no authentication method available
    """
    global _jira_headers, _jira_url

    if _jira_headers:
        return _jira_headers

    # Get JIRA URL
    _jira_url = get_jira_url()

    # Try AgentCore Identity OAuth first (production)
    if IDENTITY_AVAILABLE:
        try:
            token_response = await identity_gettoken.get_token(
                provider="jira-provider"
            )
            if token_response and "accessToken" in token_response:
                access_token = token_response["accessToken"]
                print("✅ Using JIRA OAuth token from AgentCore Identity")

                _jira_headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                return _jira_headers
        except Exception as e:
            print(f"⚠️ AgentCore Identity OAuth failed: {e}")
            print("   Falling back to API token authentication...")

    # Fallback: API Token for local testing
    jira_email = os.getenv("JIRA_EMAIL")
    jira_api_token = os.getenv("JIRA_API_TOKEN")

    if jira_email and jira_api_token:
        import base64

        # Basic Auth: base64(email:api_token)
        credentials = f"{jira_email}:{jira_api_token}"
        encoded = base64.b64encode(credentials.encode()).decode()

        print(f"✅ Using JIRA API Token (Basic Auth) for {jira_email}")

        _jira_headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        return _jira_headers

    # No authentication available
    raise Exception(
        "No JIRA authentication available. Set either:\n"
        "  - AgentCore Identity OAuth (production)\n"
        "  - JIRA_EMAIL and JIRA_API_TOKEN (local testing)"
    )


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