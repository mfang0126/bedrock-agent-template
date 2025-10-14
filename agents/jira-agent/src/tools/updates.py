"""JIRA ticket update tools with dependency injection.

Tools for updating ticket status and adding comments.
Refactored to use dependency injection for authentication.
"""

import re
import httpx
from strands import tool

from src.auth import JiraAuth


class JiraUpdateTools:
    """JIRA ticket update operations with injected authentication.

    This class provides tools for updating JIRA ticket status,
    adding comments, and linking GitHub issues using dependency-injected authentication.

    Args:
        auth: JiraAuth implementation (mock or real OAuth)

    Example:
        >>> from src.auth import MockJiraAuth
        >>> auth = MockJiraAuth()
        >>> tools = JiraUpdateTools(auth)
        >>> result = await tools.update_jira_status("PROJ-123", "In Progress")
    """

    def __init__(self, auth: JiraAuth):
        """Initialize JIRA update tools with authentication.

        Args:
            auth: JiraAuth implementation for API access
        """
        self.auth = auth

    @tool
    async def update_jira_status(self, ticket_id: str, status: str) -> str:
        """Update JIRA ticket status.

        Args:
            ticket_id: JIRA ticket ID (e.g., "PROJ-123")
            status: New status (e.g., "In Progress", "Done")

        Returns:
            Success or error message
        """
        # Validate ticket ID
        if not ticket_id or not re.match(r'^[A-Z]{2,10}-\d+$', ticket_id):
            return f"❌ Invalid ticket ID format: {ticket_id}"

        if not status:
            return "❌ Status cannot be empty"

        try:
            # Get authentication from injected auth
            headers = self.auth.get_auth_headers()
            jira_url = self.auth.get_jira_url()

            async with httpx.AsyncClient() as client:
                # Get available transitions
                transitions_response = await client.get(
                    f"{jira_url}/rest/api/3/issue/{ticket_id}/transitions",
                    headers=headers,
                    timeout=30.0
                )

                if transitions_response.status_code != 200:
                    return f"❌ Error fetching transitions: {transitions_response.status_code}"

                transitions = transitions_response.json().get("transitions", [])

                # Find matching transition
                transition_id = None
                transition_name = None
                for transition in transitions:
                    if transition["name"].lower() == status.lower():
                        transition_id = transition["id"]
                        transition_name = transition["name"]
                        break

                if not transition_id:
                    available = [t["name"] for t in transitions]
                    return f"❌ Cannot transition to '{status}'. Available transitions: {', '.join(available)}"

                # Execute transition
                response = await client.post(
                    f"{jira_url}/rest/api/3/issue/{ticket_id}/transitions",
                    headers=headers,
                    json={"transition": {"id": transition_id}},
                    timeout=30.0
                )

                if response.status_code == 204:
                    return f"✅ Ticket {ticket_id} moved to '{transition_name}'"
                else:
                    return f"❌ Error updating status: {response.status_code} - {response.text}"

        except httpx.TimeoutException:
            return "❌ Request timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @tool
    async def add_jira_comment(self, ticket_id: str, comment: str, github_url: str = None) -> str:
        """Add comment to JIRA ticket.

        Args:
            ticket_id: JIRA ticket ID
            comment: Comment text
            github_url: Optional GitHub issue/PR URL to include

        Returns:
            Success or error message
        """
        # Validate inputs
        if not ticket_id or not re.match(r'^[A-Z]{2,10}-\d+$', ticket_id):
            return f"❌ Invalid ticket ID format: {ticket_id}"

        if not comment:
            return "❌ Comment cannot be empty"

        try:
            # Get authentication from injected auth
            headers = self.auth.get_auth_headers()
            jira_url = self.auth.get_jira_url()

            # Format comment with GitHub link if provided
            comment_body = comment
            if github_url:
                comment_body += f"\n\n🔗 GitHub: {github_url}"

            # JIRA Cloud uses Atlassian Document Format (ADF) for comments
            # Simplified version with plain text
            comment_data = {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": comment_body
                                }
                            ]
                        }
                    ]
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{jira_url}/rest/api/3/issue/{ticket_id}/comment",
                    headers=headers,
                    json=comment_data,
                    timeout=30.0
                )

                if response.status_code == 201:
                    return f"✅ Comment added to {ticket_id}"
                else:
                    return f"❌ Error adding comment: {response.status_code} - {response.text}"

        except httpx.TimeoutException:
            return "❌ Request timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"

    @tool
    async def link_github_issue(self, ticket_id: str, github_url: str) -> str:
        """Link GitHub issue/PR to JIRA ticket.

        Args:
            ticket_id: JIRA ticket ID
            github_url: GitHub issue or PR URL

        Returns:
            Success or error message
        """
        # Validate inputs
        if not ticket_id or not re.match(r'^[A-Z]{2,10}-\d+$', ticket_id):
            return f"❌ Invalid ticket ID format: {ticket_id}"

        if not github_url or "github.com" not in github_url:
            return "❌ Invalid GitHub URL"

        try:
            # Get authentication from injected auth
            headers = self.auth.get_auth_headers()
            jira_url = self.auth.get_jira_url()

            # Extract issue/PR number from URL
            github_title = "GitHub Issue"
            if "/pull/" in github_url:
                github_title = "GitHub Pull Request"

            # Create remote link
            link_data = {
                "object": {
                    "url": github_url,
                    "title": github_title,
                    "icon": {
                        "url16x16": "https://github.com/favicon.ico"
                    }
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{jira_url}/rest/api/3/issue/{ticket_id}/remotelink",
                    headers=headers,
                    json=link_data,
                    timeout=30.0
                )

                if response.status_code == 201:
                    return f"✅ Linked GitHub to {ticket_id}: {github_url}"
                else:
                    return f"❌ Error linking: {response.status_code} - {response.text}"

        except httpx.TimeoutException:
            return "❌ Request timed out"
        except Exception as e:
            return f"❌ Error: {str(e)}"
