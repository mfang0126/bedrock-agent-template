"""JIRA configuration module.

Manages JIRA connection settings for OAuth 2.0 authentication.
"""

import os


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