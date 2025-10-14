"""GitHub pull request tools with dependency injection.

These tools make direct API calls using httpx and accept a GitHubAuth
interface for authentication, enabling both local testing and production OAuth.
"""

import httpx
from strands import tool

from src.auth import GitHubAuth


class GitHubPRTools:
    """GitHub pull request operations with injected authentication.

    This class encapsulates PR tools and accepts a GitHubAuth
    implementation via dependency injection, enabling:
    - Local testing with MockGitHubAuth
    - Production OAuth with AgentCoreGitHubAuth
    """

    def __init__(self, auth: GitHubAuth):
        """Initialize PR tools with authentication provider.

        Args:
            auth: GitHubAuth implementation (mock or real OAuth)
        """
        self.auth = auth

    @tool
    async def create_pull_request(
        self,
        repo_name: str,
        title: str,
        head_branch: str,
        base_branch: str = "main",
        body: str = "",
        draft: bool = False,
    ) -> str:
        """Create a new pull request in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            title: PR title
            head_branch: Branch with changes
            base_branch: Target branch (default: "main")
            body: PR description/body
            draft: Create as draft PR

        Returns:
            Success message with PR details
        """
        if not self.auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        access_token = await self.auth.get_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Prepare PR data
        pr_data = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body,
            "draft": draft,
        }

        try:
            with httpx.Client() as client:
                response = client.post(
                    f"https://api.github.com/repos/{repo_name}/pulls",
                    headers=headers,
                    json=pr_data,
                    timeout=30.0,
                )
                response.raise_for_status()
                pr = response.json()

                draft_status = " (Draft)" if draft else ""
                return f"""✅ Pull request created successfully!

📝 PR #{pr['number']}: {pr['title']}{draft_status}
   Repository: {repo_name}
   {head_branch} → {base_branch}

Description:
{body if body else '(No description provided)'}

🔗 {pr['html_url']}"""

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error creating pull request: {str(e)}"

    @tool
    async def list_pull_requests(self, repo_name: str, state: str = "open") -> str:
        """List pull requests in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            state: PR state - "open", "closed", or "all"

        Returns:
            Formatted string with PR information
        """
        if not self.auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        access_token = await self.auth.get_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.github.com/repos/{repo_name}/pulls",
                    headers=headers,
                    params={"state": state},
                    timeout=30.0,
                )
                response.raise_for_status()
                prs = response.json()

                if not prs:
                    return f"No {state} pull requests found in {repo_name}."

                # Format PRs
                result_lines = [f"Pull Requests in {repo_name} ({state}):\n"]

                for pr in prs:
                    # PR number and title
                    draft_indicator = " [DRAFT]" if pr.get("draft") else ""
                    pr_line = f"📝 #{pr['number']}: {pr['title']}{draft_indicator}"
                    result_lines.append(pr_line)

                    # Branch info
                    result_lines.append(f"   {pr['head']['ref']} → {pr['base']['ref']}")

                    # Created date and author
                    created = pr["created_at"][:10]
                    author = pr["user"]["login"]
                    result_lines.append(f"   Created: {created}")
                    result_lines.append(f"   👤 Created by: {author}")

                    # Status
                    if pr.get("mergeable_state"):
                        result_lines.append(f"   Status: {pr['mergeable_state']}")

                    result_lines.append("")  # Empty line

                result_lines.append(f"Total: {len(prs)} {state} pull requests")
                return "\n".join(result_lines)

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error fetching pull requests: {str(e)}"

    @tool
    async def merge_pull_request(
        self, repo_name: str, pr_number: int, merge_method: str = "merge"
    ) -> str:
        """Merge a pull request in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            pr_number: PR number to merge
            merge_method: Merge method - "merge", "squash", or "rebase"

        Returns:
            Success message
        """
        if not self.auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        access_token = await self.auth.get_token()
        headers = {"Authorization": f"Bearer {access_token}"}

        # Validate merge method
        if merge_method not in ["merge", "squash", "rebase"]:
            return "❌ Invalid merge method. Use 'merge', 'squash', or 'rebase'."

        try:
            with httpx.Client() as client:
                # Get PR details first
                pr_response = client.get(
                    f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}",
                    headers=headers,
                    timeout=30.0,
                )
                pr_response.raise_for_status()
                pr = pr_response.json()

                # Merge the PR
                merge_response = client.put(
                    f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/merge",
                    headers=headers,
                    json={"merge_method": merge_method},
                    timeout=30.0,
                )
                merge_response.raise_for_status()

                return f"""✅ Pull request merged successfully!

Repository: {repo_name}
PR: #{pr_number}
Title: {pr['title']}
Merge Method: {merge_method}
Status: Merged

The changes have been merged into {pr['base']['ref']}."""

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error merging pull request: {str(e)}"
