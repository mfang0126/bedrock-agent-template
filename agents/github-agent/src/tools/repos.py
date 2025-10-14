"""GitHub repository tools with function factories and closures.

These tools use function factories with closures for auth injection,
following Strands best practices for stateless operations.
"""

import httpx
from collections.abc import Sequence
from typing import Callable
from strands import tool

from src.auth import GitHubAuth


def github_repo_tools(auth: GitHubAuth) -> Sequence[Callable]:
    """Factory returns repository tools with auth in closure.

    Args:
        auth: GitHubAuth implementation (mock or real OAuth)

    Returns:
        Sequence of tool functions with auth captured in closure
    """

    async def _api_call(method: str, endpoint: str, **kwargs) -> dict:
        """Shared async HTTP helper - DRY principle.

        Args:
            method: HTTP method (get, post, patch, etc.)
            endpoint: API endpoint (e.g., "/user/repos")
            **kwargs: Additional arguments for httpx request

        Returns:
            JSON response as dict

        Raises:
            httpx.HTTPStatusError: On API errors
        """
        token = await auth.get_token()
        async with httpx.AsyncClient() as client:
            response = await getattr(client, method)(
                f"https://api.github.com{endpoint}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

    @tool
    async def list_github_repos() -> str:
        """List user's GitHub repositories.

        Returns:
            Formatted string with repository information
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        try:
            # Get user information
            user_data = await _api_call("get", "/user")
            username = user_data.get("login", "Unknown")
            print(f"✅ User: {username}")

            # Search for user's repositories
            repos_data = await _api_call(
                "get",
                f"/search/repositories?q=user:{username}"
            )
            print(f"✅ Found {len(repos_data.get('items', []))} repositories")

            repos = repos_data.get("items", [])

            if not repos:
                return f"No repositories found for {username}."

            # Limit to first 3 repos to avoid timeout
            repos = repos[:3]
            total_count = repos_data.get("total_count", len(repos))

            # Minimal plain text format
            repo_names = [repo["name"] for repo in repos]

            return f"You have {total_count} repositories. First 3: {', '.join(repo_names)}"

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error fetching GitHub repositories: {str(e)}"

    @tool
    async def get_repo_info(repo_name: str) -> str:
        """Get detailed information about a specific repository.

        Args:
            repo_name: Repository name (format: owner/repo or just repo for user's own)

        Returns:
            Detailed repository information
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        try:
            # If no owner specified, get current user's repo
            if "/" not in repo_name:
                user_data = await _api_call("get", "/user")
                username = user_data.get("login")
                repo_name = f"{username}/{repo_name}"

            # Get repository information
            repo = await _api_call("get", f"/repos/{repo_name}")

            # Format repository details
            result = f"""Repository: {repo['name']}
Owner: {repo['owner']['login']}
URL: {repo['html_url']}

📊 Statistics:
   ⭐ Stars: {repo['stargazers_count']}
   🔱 Forks: {repo['forks_count']}
   👀 Watchers: {repo['watchers_count']}
   📝 Open Issues: {repo['open_issues_count']}

📅 Dates:
   Created: {repo['created_at'][:10]}
   Last Updated: {repo['updated_at'][:10]}

"""

            if repo.get("language"):
                result += f"💻 Language: {repo['language']}\n"

            if repo.get("topics"):
                result += f"🏷️  Topics: {', '.join(repo['topics'])}\n"

            if repo.get("description"):
                result += f"\n📄 Description:\n   {repo['description']}\n"

            return result

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error fetching repository info: {str(e)}"

    @tool
    async def create_github_repo(name: str, description: str = "", private: bool = False) -> str:
        """Create a new GitHub repository.

        Args:
            name: Repository name
            description: Repository description
            private: Whether the repository should be private

        Returns:
            Success message with repository details
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        try:
            repo = await _api_call(
                "post",
                "/user/repos",
                json={"name": name, "description": description, "private": private}
            )

            visibility = "private" if private else "public"
            return f"""✅ Repository created successfully!

📁 {repo['name']} ({visibility})
📝 {description if description else 'No description'}
🔗 {repo['html_url']}

Repository is ready to use!"""

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error creating repository: {str(e)}"

    return [list_github_repos, get_repo_info, create_github_repo]
