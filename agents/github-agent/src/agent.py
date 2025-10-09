"""GitHub Agent - Strands agent with GitHub tools."""

# Import GitHub tools
import sys
from pathlib import Path
from typing import Optional

from strands import Agent
from strands.models import BedrockModel

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.issues import close_github_issue, create_github_issue, list_github_issues
from tools.repos import create_github_repo, get_repo_info, list_github_repos


def create_github_agent(mock_mode: bool = True) -> Agent:
    """Create a GitHub agent with Strands framework.

    Args:
        mock_mode: If True, use mock tools (no real API calls)

    Returns:
        Configured Strands Agent
    """
    # Model configuration (Claude 3.5 Sonnet for Sydney region)
    model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

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
        Agent's response as clean JSON
    """
    # Import from local common module
    from src.common.utils import clean_json_response, format_github_response

    if mock_mode:
        # In mock mode, directly call tools for demo
        print(f"🤖 GitHub Agent (Mock Mode)")
        print(f"📝 Query: {query}\n")

        # Simple keyword matching for demo
        query_lower = query.lower()

        if "list" in query_lower and "repo" in query_lower:
            # Mock repository data
            repos_data = [
                {"name": "awesome-project", "stars": 42, "language": "Python"},
                {"name": "web-app", "stars": 15, "language": "JavaScript"},
                {"name": "mobile-app", "stars": 8, "language": "Swift"},
            ]
            response = format_github_response("list_repos", repos_data)
            return response.to_json()

        elif "create" in query_lower and "repo" in query_lower:
            # Mock repository creation
            repo_data = {
                "name": "new-project",
                "url": "https://github.com/user/new-project",
                "private": False,
            }
            response = format_github_response("create_repo", repo_data)
            return response.to_json()

        elif "issue" in query_lower:
            if "list" in query_lower:
                # Mock issues data
                issues_data = [
                    {"number": 1, "title": "Bug in login system", "state": "open"},
                    {"number": 2, "title": "Add dark mode", "state": "closed"},
                    {"number": 3, "title": "Performance optimization", "state": "open"},
                ]
                response = format_github_response(
                    "list_issues", issues_data, "mock_user/awesome-project"
                )
                return response.to_json()
            elif "create" in query_lower:
                # Mock issue creation
                issue_data = {
                    "number": 4,
                    "title": "New feature request",
                    "state": "open",
                }
                response = format_github_response(
                    "create_issue", issue_data, "mock_user/awesome-project"
                )
                return response.to_json()

        # Default response
        raw_response = f"I can help you with GitHub operations. Try:\n- 'list my repositories'\n- 'create a repository'\n- 'list issues in a repo'"
        response = clean_json_response(raw_response, "github")
        return response.to_json()

    # Real agent execution (Phase 4)
    agent = create_github_agent(mock_mode=False)
    response = agent(query)

    # Clean and format the real response
    clean_response = clean_json_response(response.message, "github")
    return clean_response.to_json()


if __name__ == "__main__":
    # Quick test
    print("Testing GitHub Agent...")
    result = run_agent_query("list my repositories", mock_mode=True)
    print(result)
