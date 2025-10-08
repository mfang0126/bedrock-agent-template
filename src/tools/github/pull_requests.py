"""GitHub pull request tools - Following notebook pattern.

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
async def create_pull_request(
    repo_name: str,
    title: str,
    head_branch: str,
    base_branch: str = "main",
    body: str = "",
    draft: bool = False,
    *,
    access_token: str
) -> str:
    """Create a new pull request in a GitHub repository.

    Args:
        repo_name: Repository name (format: owner/repo)
        title: Pull request title
        head_branch: Branch containing changes
        base_branch: Target branch (default: main)
        body: Pull request description
        draft: Create as draft PR (default: False)

    Returns:
        Success message with PR details
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    pr_data = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": body,
        "draft": draft
    }

    try:
        with httpx.Client() as client:
            response = client.post(
                f"https://api.github.com/repos/{repo_name}/pulls",
                headers=headers,
                json=pr_data,
                timeout=30.0
            )
            response.raise_for_status()
            pr = response.json()

            draft_str = " (Draft)" if pr.get('draft') else ""
            return f"""✅ Pull request created successfully!

🔀 #{pr['number']}: {pr['title']}{draft_str}
   Repository: {repo_name}
   {head_branch} → {base_branch}

📝 Description:
{body if body else '(No description provided)'}

Status: {pr['state']}
Mergeable: {pr.get('mergeable', 'Unknown')}

🔗 {pr['html_url']}"""

    except httpx.HTTPStatusError as e:
        return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"❌ Error creating pull request: {str(e)}"


@tool
@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow='USER_FEDERATION',
)
async def list_pull_requests(repo_name: str, state: str = "open", *, access_token: str) -> str:
    """List pull requests in a GitHub repository.

    Args:
        repo_name: Repository name (format: owner/repo)
        state: PR state - "open", "closed", or "all"

    Returns:
        Formatted string with PR information
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        with httpx.Client() as client:
            response = client.get(
                f"https://api.github.com/repos/{repo_name}/pulls",
                headers=headers,
                params={"state": state, "per_page": 30},
                timeout=30.0
            )
            response.raise_for_status()
            prs = response.json()

            if not prs:
                return f"No {state} pull requests found in {repo_name}."

            # Format PRs
            result_lines = [f"Pull Requests in {repo_name} ({state}):\n"]

            for pr in prs:
                draft_str = " (Draft)" if pr.get('draft') else ""
                pr_line = f"🔀 #{pr['number']}: {pr['title']}{draft_str}"
                result_lines.append(pr_line)

                # Branch info
                result_lines.append(f"   {pr['head']['ref']} → {pr['base']['ref']}")

                # Author and date
                author = pr['user']['login']
                created = pr['created_at'][:10]
                result_lines.append(f"   👤 {author} | Created: {created}")

                # Status
                mergeable = pr.get('mergeable')
                status = "✅ Mergeable" if mergeable else "⚠️ Conflicts" if mergeable is False else "❓ Unknown"
                result_lines.append(f"   Status: {status}")
                result_lines.append("")

            result_lines.append(f"Total: {len(prs)} {state} pull requests")
            return "\n".join(result_lines)

    except httpx.HTTPStatusError as e:
        return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"❌ Error fetching pull requests: {str(e)}"


@tool
@requires_access_token(
    provider_name="github-provider",
    scopes=["repo", "read:user"],
    auth_flow='USER_FEDERATION',
)
async def merge_pull_request(
    repo_name: str,
    pr_number: int,
    merge_method: str = "squash",
    *,
    access_token: str
) -> str:
    """Merge a pull request in a GitHub repository.

    Args:
        repo_name: Repository name (format: owner/repo)
        pr_number: Pull request number to merge
        merge_method: Merge method - "merge", "squash", or "rebase" (default: squash)

    Returns:
        Success message with merge details
    """
    headers = {"Authorization": f"Bearer {access_token}"}

    # Validate merge method
    valid_methods = ["merge", "squash", "rebase"]
    if merge_method not in valid_methods:
        return f"❌ Invalid merge method. Use one of: {', '.join(valid_methods)}"

    # Check if PR is mergeable first
    try:
        with httpx.Client() as client:
            # Get PR info
            pr_response = client.get(
                f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}",
                headers=headers,
                timeout=30.0
            )
            pr_response.raise_for_status()
            pr = pr_response.json()

            if pr['state'] != 'open':
                return f"❌ Pull request is {pr['state']}, cannot merge."

            if pr.get('mergeable') is False:
                return "❌ Pull request has conflicts and cannot be merged."

            # Merge the PR
            merge_response = client.put(
                f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}/merge",
                headers=headers,
                json={"merge_method": merge_method},
                timeout=30.0
            )
            merge_response.raise_for_status()
            merge_result = merge_response.json()

            return f"""✅ Pull request merged successfully!

Repository: {repo_name}
PR: #{pr_number}
Title: {pr['title']}

Merge method: {merge_method}
Commit SHA: {merge_result['sha'][:7]}

{pr['head']['ref']} → {pr['base']['ref']}

The pull request has been successfully merged into {pr['base']['ref']}."""

    except httpx.HTTPStatusError as e:
        return f"❌ GitHub API error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"❌ Error merging pull request: {str(e)}"
