"""GitHub Agent - Pure agent logic without deployment concerns.

This module contains the core GitHub agent logic, independent of AgentCore runtime.
It uses dependency injection for authentication, enabling both local testing and production deployment.
"""

from strands import Agent
from strands.models import BedrockModel

from src.auth import GitHubAuth
from src.tools.repos import github_repo_tools
from src.tools.issues import github_issue_tools
from src.tools.pull_requests import github_pr_tools


# Model configuration
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"  # Sydney


def create_github_agent(auth: GitHubAuth) -> Agent:
    """Create a GitHub agent with injected authentication.

    This factory function creates a fully configured GitHub agent using
    the provided authentication implementation. The agent is testable
    with MockGitHubAuth or production-ready with AgentCoreGitHubAuth.

    Uses function-based tools with closures for stateless operations,
    following Strands best practices.

    Args:
        auth: GitHubAuth implementation (mock or real OAuth)

    Returns:
        Agent: Configured Strands Agent with GitHub tools

    Example:
        >>> # Local testing
        >>> from src.auth import MockGitHubAuth
        >>> auth = MockGitHubAuth()
        >>> agent = create_github_agent(auth)
        >>> response = agent("List my repositories")
        >>>
        >>> # Production with OAuth
        >>> from src.auth import AgentCoreGitHubAuth
        >>> auth = AgentCoreGitHubAuth(oauth_url_callback)
        >>> agent = create_github_agent(auth)
        >>> response = agent.stream_async("Create an issue")
    """
    # Create Bedrock model
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

    # Create agent with all tools from factory functions
    # Each factory returns a sequence of tools with auth captured in closure
    agent = Agent(
        model=model,
        tools=[
            *github_repo_tools(auth),      # Repository tools
            *github_issue_tools(auth),     # Issue tools
            *github_pr_tools(auth),        # Pull request tools
        ],
        system_prompt="""You are a GitHub assistant. Use your tools to help users with repositories, issues, and pull requests.

**Available Capabilities:**
- Repository management: list, create, get details
- Issue tracking: list, create, update, close, comment
- Pull requests: create, list, merge

**Authentication:**
Authentication is handled automatically. Never ask users for tokens or credentials.

**Best Practices:**
- Always confirm actions before making destructive changes
- Provide clear, actionable feedback
- Use markdown formatting for readability
- Include relevant URLs in responses""",
    )

    return agent
