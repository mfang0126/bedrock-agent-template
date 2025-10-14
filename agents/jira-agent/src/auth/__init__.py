"""Jira Authentication Module - Factory for environment-specific auth.

This module provides a factory function to get the appropriate
authentication implementation based on the environment.
"""

import os
from typing import Callable, Optional

from .interface import JiraAuth
from .mock import MockJiraAuth
from .agentcore import AgentCoreJiraAuth


def get_auth_provider(
    env: str = "prod",
    oauth_url_callback: Optional[Callable[[str], None]] = None
) -> JiraAuth:
    """Get environment-specific Jira authentication provider.

    This factory function returns the appropriate authentication
    implementation based on the environment:
    - local: MockJiraAuth (no OAuth, instant token)
    - dev/prod: AgentCoreJiraAuth (OAuth 2.0 flow)

    Args:
        env: Environment name ('local', 'dev', 'prod')
        oauth_url_callback: Optional callback for OAuth URL streaming
                           (only used for dev/prod)

    Returns:
        JiraAuth: Authentication implementation for the environment

    Example:
        >>> # Local testing
        >>> auth = get_auth_provider(env="local")
        >>> token = await auth.get_token()  # Returns mock token
        >>>
        >>> # Production with OAuth
        >>> def stream_url(url: str):
        ...     print(f"Visit: {url}")
        >>> auth = get_auth_provider(env="prod", oauth_url_callback=stream_url)
        >>> token = await auth.get_token()  # Triggers OAuth if needed
    """
    if env == "local":
        print(f"🧪 Using Mock Jira Auth (LOCAL environment)")
        return MockJiraAuth()
    else:
        print(f"🔐 Using AgentCore Jira Auth ({env.upper()} environment)")
        return AgentCoreJiraAuth(oauth_url_callback=oauth_url_callback)


__all__ = [
    "JiraAuth",
    "MockJiraAuth",
    "AgentCoreJiraAuth",
    "get_auth_provider",
]
