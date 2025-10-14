"""GitHub pull request tools with function factories and closures.

These tools use function factories with closures for auth injection,
following Strands best practices for stateless operations.
"""

import httpx
from collections.abc import Sequence
from typing import Callable
from strands import tool

from src.auth import GitHubAuth


def github_pr_tools(auth: GitHubAuth) -> Sequence[Callable]:
    """Factory returns pull request tools with auth in closure.

    Args:
        auth: GitHubAuth implementation (mock or real OAuth)

    Returns:
        Sequence of tool functions with auth captured in closure
    """

    async def _api_call(method: str, endpoint: str, **kwargs) -> dict:
        """Shared async HTTP helper - DRY principle.

        Args:
            method: HTTP method (get, post, patch, put, etc.)
            endpoint: API endpoint (e.g., "/repos/owner/repo/pulls")
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
    async def create_pull_request(
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
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        # Prepare PR data
        pr_data = {
            "title": title,
            "head": head_branch,
            "base": base_branch,
            "body": body,
            "draft": draft,
        }

        try:
            pr = await _api_call(
                "post",
                f"/repos/{repo_name}/pulls",
                json=pr_data
            )

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
    async def list_pull_requests(repo_name: str, state: str = "open") -> str:
        """List pull requests in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            state: PR state - "open", "closed", or "all"

        Returns:
            Formatted string with PR information
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        try:
            prs = await _api_call(
                "get",
                f"/repos/{repo_name}/pulls",
                params={"state": state}
            )

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
        repo_name: str, pr_number: int, merge_method: str = "merge"
    ) -> str:
        """Merge a pull request in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            pr_number: PR number to merge
            merge_method: Merge method - "merge", "squash", or "rebase"

        Returns:
            Success message
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        # Validate merge method
        if merge_method not in ["merge", "squash", "rebase"]:
            return "❌ Invalid merge method. Use 'merge', 'squash', or 'rebase'."

        try:
            # Get PR details first
            pr = await _api_call(
                "get",
                f"/repos/{repo_name}/pulls/{pr_number}"
            )

            # Merge the PR
            await _api_call(
                "put",
                f"/repos/{repo_name}/pulls/{pr_number}/merge",
                json={"merge_method": merge_method}
            )

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

    return [create_pull_request, list_pull_requests, merge_pull_request]
