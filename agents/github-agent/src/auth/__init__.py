"""
GitHub authentication module with dependency injection support.

This module provides authentication abstraction for the GitHub agent,
enabling different implementations for different environments:
- Local: Mock authentication for testing
- Dev/Prod: Real OAuth via AgentCore Identity
"""

import os
import logging
from typing import Optional, Callable

from .interface import GitHubAuth
from .mock import MockGitHubAuth

# Optional import for production/dev environments
try:
    from .agentcore import AgentCoreGitHubAuth
    _AGENTCORE_AVAILABLE = True
except ImportError:
    _AGENTCORE_AVAILABLE = False
    AgentCoreGitHubAuth = None  # type: ignore

logger = logging.getLogger(__name__)

__all__ = ["GitHubAuth", "MockGitHubAuth", "AgentCoreGitHubAuth", "get_auth_provider"]


def get_auth_provider(
    env: Optional[str] = None,
    oauth_url_callback: Optional[Callable[[str], None]] = None
) -> GitHubAuth:
    """Factory function to get appropriate auth provider based on environment.

    Args:
        env: Environment name ("local", "dev", "prod"). If None, reads from AGENT_ENV
        oauth_url_callback: Optional callback for OAuth URL streaming (AgentCore only)

    Returns:
        GitHubAuth: Appropriate authentication implementation

    Examples:
        >>> # Local testing
        >>> auth = get_auth_provider("local")
        >>> # Production with OAuth
        >>> auth = get_auth_provider("prod", oauth_callback)
    """
    if env is None:
        env = os.getenv("AGENT_ENV", "prod")

    env = env.lower()

    if env == "local":
        logger.info(f"🧪 Using mock authentication for environment: {env}")
        return MockGitHubAuth()
    else:
        if not _AGENTCORE_AVAILABLE:
            raise ImportError(
                "bedrock_agentcore is required for production environments. "
                "Install with: uv pip install bedrock-agentcore[strands-agents]"
            )
        logger.info(f"🔐 Using AgentCore OAuth for environment: {env}")
        return AgentCoreGitHubAuth(oauth_url_callback=oauth_url_callback)
