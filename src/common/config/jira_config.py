"""JIRA configuration module.

Manages JIRA connection settings and environment configuration.
"""

import os
from typing import Optional


def get_jira_url() -> str:
    """Get JIRA base URL from environment.

    Returns:
        JIRA URL (e.g., https://your-domain.atlassian.net)

    Raises:
        ValueError: If JIRA_URL not configured
    """
    jira_url = os.getenv("JIRA_URL")
    if not jira_url:
        raise ValueError("JIRA_URL environment variable not set")

    # Remove trailing slash
    return jira_url.rstrip("/")


def get_jira_email() -> str:
    """Get JIRA user email from environment.

    Returns:
        User email for JIRA authentication

    Raises:
        ValueError: If JIRA_EMAIL not configured
    """
    email = os.getenv("JIRA_EMAIL")
    if not email:
        raise ValueError("JIRA_EMAIL environment variable not set")

    return email


def get_jira_api_token() -> Optional[str]:
    """Get JIRA API token from environment (for testing only).

    Note: In production, tokens come from AgentCore Identity.
    This is only for local development/testing.

    Returns:
        API token if available, None otherwise
    """
    return os.getenv("JIRA_API_TOKEN")
