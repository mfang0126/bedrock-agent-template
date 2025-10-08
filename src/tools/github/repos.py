"""GitHub repository tools - Following notebook pattern.

These tools make direct API calls using httpx and the global access token
from the auth module.
"""

import httpx
from strands import tool
from bedrock_agentcore.identity.auth import requires_access_token
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@tool
@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow='USER_FEDERATION',
)
async def list_github_repos(*, access_token: str) -> str:
    """List user's private GitHub repositories.

    Returns:
        Formatted string with repository information
    """
    print(f"🔍 Fetching GitHub repositories...")
    print(f"🔑 Access token received: {access_token[:20]}..." if access_token else "❌ No access token!")

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            # Get user information
            user_response = client.get(
                "https://api.github.com/user",
                headers=headers,
                timeout=30.0
            )
            user_response.raise_for_status()
            username = user_response.json().get("login", "Unknown")
            print(f"✅ User: {username}")

            # Search for user's repositories
            repos_response = client.get(
                f"https://api.github.com/search/repositories?q=user:{username}",
                headers=headers,
                timeout=30.0
            )
            repos_response.raise_for_status()
            repos_data = repos_response.json()
            print(f"✅ Found {len(repos_data.get('items', []))} repositories")

            repos = repos_data.get('items', [])

            if not repos:
                return f"No repositories found for {username}."

            # Format repository information
            result_lines = [f"GitHub repositories for {username}:\n"]

            for repo in repos:
                repo_line = f"📁 {repo['name']}"
                if repo.get('language'):
                    repo_line += f" ({repo['language']})"
                repo_line += f" - ⭐ {repo['stargazers_count']}"
                result_lines.append(repo_line)

                if repo.get('description'):
                    result_lines.append(f"   {repo['description']}")
                result_lines.append("")  # Empty line for spacing

            return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"❌ Error fetching GitHub repositories: {str(e)}"


@tool
@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow='USER_FEDERATION',
)
async def get_repo_info(repo_name: str, *, access_token: str) -> str:
    """Get detailed information about a specific repository.

    Args:
        repo_name: Repository name (format: owner/repo or just repo for user's own)

    Returns:
        Detailed repository information
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            # If no owner specified, get current user's repo
            if "/" not in repo_name:
                user_response = client.get(
                    "https://api.github.com/user",
                    headers=headers,
                    timeout=30.0
                )
                user_response.raise_for_status()
                username = user_response.json().get("login")
                repo_name = f"{username}/{repo_name}"

            # Get repository information
            repo_response = client.get(
                f"https://api.github.com/repos/{repo_name}",
                headers=headers,
                timeout=30.0
            )
            repo_response.raise_for_status()
            repo = repo_response.json()

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

            if repo.get('language'):
                result += f"💻 Language: {repo['language']}\n"

            if repo.get('topics'):
                result += f"🏷️  Topics: {', '.join(repo['topics'])}\n"

            if repo.get('description'):
                result += f"\n📄 Description:\n   {repo['description']}\n"

            return result

    except httpx.HTTPStatusError as e:
        return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"❌ Error fetching repository info: {str(e)}"


@tool
@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow='USER_FEDERATION',
)
async def create_github_repo(
    name: str,
    description: str = "",
    private: bool = False,
    *,
    access_token: str
) -> str:
    """Create a new GitHub repository.

    Args:
        name: Repository name
        description: Repository description
        private: Whether the repository should be private

    Returns:
        Success message with repository details
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            response = client.post(
                "https://api.github.com/user/repos",
                headers=headers,
                json={
                    "name": name,
                    "description": description,
                    "private": private
                },
                timeout=30.0
            )
            response.raise_for_status()
            repo = response.json()

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
