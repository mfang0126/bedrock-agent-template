"""JIRA authentication using AgentCore Identity.

Similar pattern to GitHub OAuth, but using JIRA API Token.
Tokens are stored in AgentCore Identity per user.
"""

import base64
import os
from typing import Dict, Optional

# Import AgentCore Identity
try:
    import bedrock_agentcore.identity.gettoken as identity_gettoken
    IDENTITY_AVAILABLE = True
except ImportError:
    IDENTITY_AVAILABLE = False

from src.common.config.jira_config import get_jira_url, get_jira_email, get_jira_api_token


# Global state
_jira_headers: Optional[Dict[str, str]] = None
_jira_url: Optional[str] = None


async def get_jira_auth_headers() -> Dict[str, str]:
    """Get JIRA authentication headers.

    Returns API token from AgentCore Identity if available,
    otherwise falls back to environment variable (for testing).

    Returns:
        HTTP headers with Basic authentication

    Raises:
        Exception: If no token available
    """
    global _jira_headers, _jira_url

    if _jira_headers:
        return _jira_headers

    # Get JIRA URL and email
    _jira_url = get_jira_url()
    email = get_jira_email()

    # Try to get token from AgentCore Identity first
    api_token = None
    if IDENTITY_AVAILABLE:
        try:
            # Get token from AgentCore Identity
            token_response = await identity_gettoken.get_token(
                provider="jira-provider"
            )
            if token_response and "accessToken" in token_response:
                api_token = token_response["accessToken"]
                print("✅ Using JIRA token from AgentCore Identity")
        except Exception as e:
            print(f"⚠️ Could not get JIRA token from Identity: {e}")

    # Fallback to environment variable (for testing)
    if not api_token:
        api_token = get_jira_api_token()
        if api_token:
            print("⚠️ Using JIRA token from environment (testing only)")

    if not api_token:
        raise Exception("No JIRA API token available. Configure AgentCore Identity or set JIRA_API_TOKEN env var.")

    # Create Basic Auth header
    # JIRA uses: email:api_token encoded in base64
    credentials = f"{email}:{api_token}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    _jira_headers = {
        "Authorization": f"Basic {encoded_credentials}",
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
