"""GitHub repository tools - Following notebook pattern.

These tools make direct API calls using httpx and the global access token
from the auth module.

KEY PATTERN: Tools DO NOT have @requires_access_token decorator.
They reference the global github_access_token that is set by the entrypoint.
"""

import sys
from pathlib import Path

import httpx
from strands import tool

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import auth module (not the variable directly!)
from src.common import auth as github_auth


@tool
def list_github_repos() -> str:
    """List user's GitHub repositories.

    Returns:
        Formatted string with repository information
    """
    # Access token via module attribute (not direct import)
    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    print(f"🔍 Fetching GitHub repositories...")
    print(f"🔑 Using access token: {access_token[:20]}...")

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            # Get user information
            user_response = client.get(
                "https://api.github.com/user", headers=headers, timeout=30.0
            )
            user_response.raise_for_status()
            username = user_response.json().get("login", "Unknown")
            print(f"✅ User: {username}")

            # Search for user's repositories
            repos_response = client.get(
                f"https://api.github.com/search/repositories?q=user:{username}",
                headers=headers,
                timeout=30.0,
            )
            repos_response.raise_for_status()
            repos_data = repos_response.json()
            print(f"✅ Found {len(repos_data.get('items', []))} repositories")

            repos = repos_data.get("items", [])

            if not repos:
                return f"No repositories found for {username}."

            # Limit to first 3 repos to avoid timeout
            repos = repos[:3]
            total_count = repos_data.get("total_count", len(repos))

            # Minimal plain text format
            repo_names = [repo["name"] for repo in repos]

            return (
                f"You have {total_count} repositories. First 3: {', '.join(repo_names)}"
            )

    except httpx.HTTPStatusError as e:
        return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"❌ Error fetching GitHub repositories: {str(e)}"


@tool
def get_repo_info(repo_name: str) -> str:
    """Get detailed information about a specific repository.

    Args:
        repo_name: Repository name (format: owner/repo or just repo for user's own)

    Returns:
        Detailed repository information
    """
    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            # If no owner specified, get current user's repo
            if "/" not in repo_name:
                user_response = client.get(
                    "https://api.github.com/user", headers=headers, timeout=30.0
                )
                user_response.raise_for_status()
                username = user_response.json().get("login")
                repo_name = f"{username}/{repo_name}"

            # Get repository information
            repo_response = client.get(
                f"https://api.github.com/repos/{repo_name}",
                headers=headers,
                timeout=30.0,
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
def create_github_repo(name: str, description: str = "", private: bool = False) -> str:
    """Create a new GitHub repository.

    Args:
        name: Repository name
        description: Repository description
        private: Whether the repository should be private

    Returns:
        Success message with repository details
    """
    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            response = client.post(
                "https://api.github.com/user/repos",
                headers=headers,
                json={"name": name, "description": description, "private": private},
                timeout=30.0,
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
