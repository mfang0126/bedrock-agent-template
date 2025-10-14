"""GitHub Agent - Pure agent logic without deployment concerns.

This module contains the core GitHub agent logic, independent of AgentCore runtime.
It uses dependency injection for authentication, enabling both local testing and production deployment.
"""

from strands import Agent
from strands.models import BedrockModel

from src.auth import GitHubAuth
from src.tools.repos import GitHubRepoTools
from src.tools.issues import GitHubIssueTools
from src.tools.pull_requests import GitHubPRTools


# Model configuration
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"  # Sydney


def create_github_agent(auth: GitHubAuth) -> Agent:
    """Create a GitHub agent with injected authentication.

    This factory function creates a fully configured GitHub agent using
    the provided authentication implementation. The agent is testable
    with MockGitHubAuth or production-ready with AgentCoreGitHubAuth.

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
    # Initialize tool classes with auth injection
    repo_tools = GitHubRepoTools(auth)
    issue_tools = GitHubIssueTools(auth)
    pr_tools = GitHubPRTools(auth)

    # Create Bedrock model
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

    # Create agent with all tools from tool classes
    agent = Agent(
        model=model,
        tools=[
            # Repository tools
            repo_tools.list_github_repos,
            repo_tools.get_repo_info,
            repo_tools.create_github_repo,
            # Issue tools
            issue_tools.list_github_issues,
            issue_tools.create_github_issue,
            issue_tools.close_github_issue,
            issue_tools.post_github_comment,
            issue_tools.update_github_issue,
            # Pull request tools
            pr_tools.create_pull_request,
            pr_tools.list_pull_requests,
            pr_tools.merge_pull_request,
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
