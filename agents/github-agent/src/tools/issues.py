"""GitHub issues tools with function factories and closures.

These tools use function factories with closures for auth injection,
following Strands best practices for stateless operations.
"""

import httpx
from collections.abc import Sequence
from typing import Callable
from strands import tool

from src.auth import GitHubAuth


def github_issue_tools(auth: GitHubAuth) -> Sequence[Callable]:
    """Factory returns issue tools with auth in closure.

    Args:
        auth: GitHubAuth implementation (mock or real OAuth)

    Returns:
        Sequence of tool functions with auth captured in closure
    """

    async def _api_call(method: str, endpoint: str, **kwargs) -> dict:
        """Shared async HTTP helper - DRY principle.

        Args:
            method: HTTP method (get, post, patch, etc.)
            endpoint: API endpoint (e.g., "/repos/owner/repo/issues")
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
    async def list_github_issues(repo_name: str, state: str = "open") -> str:
        """List issues in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            state: Issue state - "open", "closed", or "all"

        Returns:
            Formatted string with issue information
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        try:
            issues = await _api_call(
                "get",
                f"/repos/{repo_name}/issues",
                params={"state": state}
            )

            if not issues:
                return f"No {state} issues found in {repo_name}."

            # Format issues
            result_lines = [f"Issues in {repo_name} ({state}):\n"]

            for issue in issues:
                # Issue number and title
                issue_line = f"🔴 #{issue['number']}: {issue['title']}"
                result_lines.append(issue_line)

                # Labels
                if issue.get("labels"):
                    label_names = [label["name"] for label in issue["labels"]]
                    result_lines.append(f"   Labels: {', '.join(label_names)}")

                # Created date and author
                created = issue["created_at"][:10]
                author = issue["user"]["login"]
                result_lines.append(f"   Created: {created}")
                result_lines.append(f"   👤 Created by: {author}")
                result_lines.append("")  # Empty line

            result_lines.append(f"Total: {len(issues)} {state} issues")
            return "\n".join(result_lines)

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error fetching issues: {str(e)}"

    @tool
    async def create_github_issue(
        repo_name: str, title: str, body: str = "", labels: str = ""
    ) -> str:
        """Create a new issue in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            title: Issue title
            body: Issue description/body
            labels: Comma-separated list of labels

        Returns:
            Success message with issue details
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        # Prepare issue data
        issue_data = {"title": title, "body": body}

        # Parse labels
        if labels:
            label_list = [label.strip() for label in labels.split(",")]
            issue_data["labels"] = label_list

        try:
            issue = await _api_call(
                "post",
                f"/repos/{repo_name}/issues",
                json=issue_data
            )

            labels_str = ""
            if issue.get("labels"):
                label_names = [label["name"] for label in issue["labels"]]
                labels_str = f"\n   Labels: {', '.join(label_names)}"

            return f"""✅ Issue created successfully!

🔴 #{issue['number']}: {issue['title']}
   Repository: {repo_name}{labels_str}

📝 Description:
{body if body else '(No description provided)'}

🔗 {issue['html_url']}"""

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error creating issue: {str(e)}"

    @tool
    async def close_github_issue(repo_name: str, issue_number: int) -> str:
        """Close an issue in a GitHub repository.

        Args:
            repo_name: Repository name (format: owner/repo)
            issue_number: Issue number to close

        Returns:
            Success message
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        try:
            issue = await _api_call(
                "patch",
                f"/repos/{repo_name}/issues/{issue_number}",
                json={"state": "closed"}
            )

            return f"""✅ Issue closed successfully!

Repository: {repo_name}
Issue: #{issue_number}
Title: {issue['title']}
Status: Closed

The issue has been marked as resolved."""

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error closing issue: {str(e)}"

    @tool
    async def post_github_comment(repo_name: str, issue_number: int, comment: str) -> str:
        """Post a comment on a GitHub issue.

        Args:
            repo_name: Repository name (format: owner/repo)
            issue_number: Issue number to comment on
            comment: Comment text (supports markdown)

        Returns:
            Success message with comment details
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        try:
            comment_data = await _api_call(
                "post",
                f"/repos/{repo_name}/issues/{issue_number}/comments",
                json={"body": comment}
            )

            return f"""✅ Comment posted successfully!

Repository: {repo_name}
Issue: #{issue_number}
Author: {comment_data['user']['login']}

💬 Comment:
{comment}

🔗 {comment_data['html_url']}"""

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error posting comment: {str(e)}"

    @tool
    async def update_github_issue(
        repo_name: str,
        issue_number: int,
        state: str = None,
        labels: str = None,
        assignees: str = None,
    ) -> str:
        """Update an issue's state, labels, or assignees.

        Args:
            repo_name: Repository name (format: owner/repo)
            issue_number: Issue number to update
            state: Issue state - "open" or "closed" (optional)
            labels: Comma-separated list of labels (optional)
            assignees: Comma-separated list of usernames (optional)

        Returns:
            Success message with updated issue details
        """
        if not auth.is_authenticated():
            return "❌ GitHub authentication required. Please authenticate first."

        # Build update payload
        update_data = {}
        if state:
            update_data["state"] = state
        if labels:
            update_data["labels"] = [label.strip() for label in labels.split(",")]
        if assignees:
            update_data["assignees"] = [
                assignee.strip() for assignee in assignees.split(",")
            ]

        if not update_data:
            return (
                "❌ No updates provided. Specify at least one of: state, labels, assignees."
            )

        try:
            issue = await _api_call(
                "patch",
                f"/repos/{repo_name}/issues/{issue_number}",
                json=update_data
            )

            # Format response
            updates = []
            if state:
                updates.append(f"State: {issue['state']}")
            if labels and issue.get("labels"):
                label_names = [label["name"] for label in issue["labels"]]
                updates.append(f"Labels: {', '.join(label_names)}")
            if assignees and issue.get("assignees"):
                assignee_names = [assignee["login"] for assignee in issue["assignees"]]
                updates.append(f"Assignees: {', '.join(assignee_names)}")

            return f"""✅ Issue updated successfully!

Repository: {repo_name}
Issue: #{issue_number}
Title: {issue['title']}

Updates:
{chr(10).join(f"   {update}" for update in updates)}

🔗 {issue['html_url']}"""

        except httpx.HTTPStatusError as e:
            return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            return f"❌ Error updating issue: {str(e)}"

    return [
        list_github_issues,
        create_github_issue,
        close_github_issue,
        post_github_comment,
        update_github_issue,
    ]
