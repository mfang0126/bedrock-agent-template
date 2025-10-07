"""GitHub Agent - Strands agent with GitHub tools."""

from strands import Agent
from strands.models import BedrockModel
from typing import Optional

# Import GitHub tools
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.github.repos import list_github_repos, create_github_repo, get_repo_info
from tools.github.issues import list_github_issues, create_github_issue, close_github_issue


def create_github_agent(mock_mode: bool = True) -> Agent:
    """Create a GitHub agent with Strands framework.

    Args:
        mock_mode: If True, use mock tools (no real API calls)

    Returns:
        Configured Strands Agent
    """
    # Model configuration (Claude 3.7 Sonnet)
    model_id = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

    # Create Bedrock model
    # Note: In mock mode, this still needs AWS credentials but won't be called
    # In Phase 4, we'll add proper error handling
    try:
        model = BedrockModel(model_id=model_id)
    except Exception as e:
        print(f"⚠️  Warning: Could not initialize Bedrock model: {e}")
        print("   This is expected in mock mode without AWS credentials.")
        print("   CLI will still work with mock responses.\n")
        model = None

    # System prompt
    system_prompt = """You are a helpful GitHub assistant that helps users manage their GitHub repositories, issues, and pull requests.

You have access to tools for:
- Listing repositories
- Creating repositories
- Getting repository information
- Listing issues
- Creating issues
- Closing issues

When users ask about their GitHub account, use the appropriate tools to help them.
Provide clear, friendly responses with relevant information."""

    # Create agent with GitHub tools
    agent = Agent(
        model=model,
        tools=[
            list_github_repos,
            create_github_repo,
            get_repo_info,
            list_github_issues,
            create_github_issue,
            close_github_issue,
        ],
        system_prompt=system_prompt,
    )

    return agent


def run_agent_query(query: str, mock_mode: bool = True) -> str:
    """Run a query against the GitHub agent.

    Args:
        query: User's question or request
        mock_mode: If True, use mock mode

    Returns:
        Agent's response
    """
    if mock_mode:
        # In mock mode, directly call tools for demo
        # In Phase 4, real agent will handle this intelligently
        print(f"🤖 GitHub Agent (Mock Mode)")
        print(f"📝 Query: {query}\n")

        # Simple keyword matching for demo
        query_lower = query.lower()

        if "list" in query_lower and "repo" in query_lower:
            return list_github_repos(mock_mode=True)
        elif "create" in query_lower and "repo" in query_lower:
            return "To create a repository, use: github-agent invoke 'create repository named test-project'"
        elif "issue" in query_lower:
            if "list" in query_lower:
                return list_github_issues("mock_user/awesome-project", mock_mode=True)
            elif "create" in query_lower:
                return "To create an issue, use: github-agent invoke 'create issue about bug in login'"

        return f"I can help you with GitHub operations. Try:\n- 'list my repositories'\n- 'create a repository'\n- 'list issues in a repo'"

    # Real agent execution (Phase 4)
    agent = create_github_agent(mock_mode=False)
    response = agent(query)
    return response.message


if __name__ == "__main__":
    # Quick test
    print("Testing GitHub Agent...")
    result = run_agent_query("list my repositories", mock_mode=True)
    print(result)
