"""GitHub issues tools - Following notebook pattern.

These tools make direct API calls using httpx and the global access token
from the auth module.

KEY PATTERN: Tools DO NOT have @requires_access_token decorator.
They reference the github_access_token that is set by the entrypoint.
"""

import httpx
from strands import tool
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import auth module (not the variable directly!)
from src.common.auth import github as github_auth


@tool
def list_github_issues(repo_name: str, state: str = "open") -> str:
    """List issues in a GitHub repository.

    Args:
        repo_name: Repository name (format: owner/repo)
        state: Issue state - "open", "closed", or "all"

    Returns:
        Formatted string with issue information
    """
    # Access token via module

    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            response = client.get(
                f"https://api.github.com/repos/{repo_name}/issues",
                headers=headers,
                params={"state": state},
                timeout=30.0
            )
            response.raise_for_status()
            issues = response.json()

            if not issues:
                return f"No {state} issues found in {repo_name}."

            # Format issues
            result_lines = [f"Issues in {repo_name} ({state}):\n"]

            for issue in issues:
                # Issue number and title
                issue_line = f"🔴 #{issue['number']}: {issue['title']}"
                result_lines.append(issue_line)

                # Labels
                if issue.get('labels'):
                    label_names = [label['name'] for label in issue['labels']]
                    result_lines.append(f"   Labels: {', '.join(label_names)}")

                # Created date and author
                created = issue['created_at'][:10]
                author = issue['user']['login']
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
def create_github_issue(
    repo_name: str,
    title: str,
    body: str = "",
    labels: str = ""
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
    # Access token via module

    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    headers = {"Authorization": f"Bearer {access_token}"}

    # Prepare issue data
    issue_data = {
        "title": title,
        "body": body
    }

    # Parse labels
    if labels:
        label_list = [label.strip() for label in labels.split(",")]
        issue_data["labels"] = label_list

    try:
        with httpx.Client() as client:
            response = client.post(
                f"https://api.github.com/repos/{repo_name}/issues",
                headers=headers,
                json=issue_data,
                timeout=30.0
            )
            response.raise_for_status()
            issue = response.json()

            labels_str = ""
            if issue.get('labels'):
                label_names = [label['name'] for label in issue['labels']]
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
def close_github_issue(repo_name: str, issue_number: int) -> str:
    """Close an issue in a GitHub repository.

    Args:
        repo_name: Repository name (format: owner/repo)
        issue_number: Issue number to close

    Returns:
        Success message
    """
    # Access token via module

    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            response = client.patch(
                f"https://api.github.com/repos/{repo_name}/issues/{issue_number}",
                headers=headers,
                json={"state": "closed"},
                timeout=30.0
            )
            response.raise_for_status()
            issue = response.json()

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
def post_github_comment(repo_name: str, issue_number: int, comment: str) -> str:
    """Post a comment on a GitHub issue.

    Args:
        repo_name: Repository name (format: owner/repo)
        issue_number: Issue number to comment on
        comment: Comment text (supports markdown)

    Returns:
        Success message with comment details
    """
    # Access token via module

    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            response = client.post(
                f"https://api.github.com/repos/{repo_name}/issues/{issue_number}/comments",
                headers=headers,
                json={"body": comment},
                timeout=30.0
            )
            response.raise_for_status()
            comment_data = response.json()

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
def update_github_issue(
    repo_name: str,
    issue_number: int,
    state: str = None,
    labels: str = None,
    assignees: str = None
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
    # Access token via module

    access_token = github_auth.github_access_token

    if not access_token:
        return "❌ GitHub authentication required. Please contact support."

    headers = {"Authorization": f"Bearer {access_token}"}

    # Build update payload
    update_data = {}
    if state:
        update_data["state"] = state
    if labels:
        update_data["labels"] = [label.strip() for label in labels.split(",")]
    if assignees:
        update_data["assignees"] = [assignee.strip() for assignee in assignees.split(",")]

    if not update_data:
        return "❌ No updates provided. Specify at least one of: state, labels, assignees."

    try:
        with httpx.Client() as client:
            response = client.patch(
                f"https://api.github.com/repos/{repo_name}/issues/{issue_number}",
                headers=headers,
                json=update_data,
                timeout=30.0
            )
            response.raise_for_status()
            issue = response.json()

            # Format response
            updates = []
            if state:
                updates.append(f"State: {issue['state']}")
            if labels and issue.get('labels'):
                label_names = [label['name'] for label in issue['labels']]
                updates.append(f"Labels: {', '.join(label_names)}")
            if assignees and issue.get('assignees'):
                assignee_names = [assignee['login'] for assignee in issue['assignees']]
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
