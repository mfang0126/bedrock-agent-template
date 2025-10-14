"""JIRA ticket operations tools with dependency injection.

Tools for fetching, parsing, and managing JIRA tickets.
Refactored to use dependency injection for authentication.
"""

import re
from typing import Any, Dict, List, cast
import httpx
from strands import tool

from src.auth import JiraAuth


class JiraTicketTools:
    """JIRA ticket operations with injected authentication.

    This class provides tools for fetching and parsing JIRA tickets
    using dependency-injected authentication.

    Args:
        auth: JiraAuth implementation (mock or real OAuth)

    Example:
        >>> from src.auth import MockJiraAuth
        >>> auth = MockJiraAuth()
        >>> tools = JiraTicketTools(auth)
        >>> result = await tools.fetch_jira_ticket("PROJ-123")
    """

    def __init__(self, auth: JiraAuth):
        """Initialize JIRA ticket tools with authentication.

        Args:
            auth: JiraAuth implementation for API access
        """
        self.auth = auth

    @tool
    async def fetch_jira_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Fetch JIRA ticket details.

        Args:
            ticket_id: JIRA ticket ID (e.g., "PROJ-123")

        Returns:
            Dictionary with success, data (ticket details), and message
        """
        # Validate ticket ID format
        if not ticket_id or not re.match(r'^[A-Z]{2,10}-\d+$', ticket_id):
            return {
                "success": False,
                "data": {},
                "message": f"❌ Invalid ticket ID format. Expected: PROJECT-123, got: {ticket_id}"
            }

        try:
            # Get authentication from injected auth
            headers = self.auth.get_auth_headers()
            jira_url = self.auth.get_jira_url()

            # Fetch ticket from JIRA API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{jira_url}/rest/api/3/issue/{ticket_id}",
                    headers=headers,
                    timeout=30.0
                )

                if response.status_code == 404:
                    return {
                        "success": False,
                        "data": {},
                        "message": f"❌ Ticket {ticket_id} not found"
                    }
                elif response.status_code == 401:
                    return {
                        "success": False,
                        "data": {},
                        "message": "❌ Authentication failed. Check JIRA credentials"
                    }
                elif response.status_code != 200:
                    return {
                        "success": False,
                        "data": {},
                        "message": f"❌ JIRA API error: {response.status_code} - {response.text}"
                    }

                # Parse ticket data
                ticket = response.json()
                fields = ticket.get("fields", {})

                # Extract fields
                title = fields.get("summary", "No title")
                description = fields.get("description", "No description")
                status = fields.get("status", {}).get("name", "Unknown")
                priority = fields.get("priority", {}).get("name", "Unknown")
                assignee = fields.get("assignee")
                assignee_name = assignee.get("displayName") if assignee else "Unassigned"
                labels = fields.get("labels", [])

                # Extract acceptance criteria from description
                acceptance_criteria = _extract_acceptance_criteria(description)

                # Extract sprint info
                sprint_info = _extract_sprint(fields)

                # Format output
                output = f"""📋 {ticket_id}: {title}

**Status:** {status}
**Priority:** {priority}
**Assignee:** {assignee_name}
**Sprint:** {sprint_info}

**Description:**
{_format_description(description)}

**Acceptance Criteria:**
{_format_acceptance_criteria(acceptance_criteria)}

**Labels:** {', '.join(labels) if labels else 'None'}
"""

                # Return structured response
                return {
                    "success": True,
                    "data": {
                        "ticket_id": ticket_id,
                        "title": title,
                        "description": description,
                        "status": status,
                        "priority": priority,
                        "assignee": assignee_name,
                        "sprint": sprint_info,
                        "labels": labels,
                        "acceptance_criteria": acceptance_criteria,
                        "formatted_output": output
                    },
                    "message": f"Successfully fetched ticket {ticket_id}"
                }

        except httpx.TimeoutException:
            return {
                "success": False,
                "data": {},
                "message": "❌ Request timed out. JIRA may be slow or unreachable."
            }
        except Exception as e:
            return {
                "success": False,
                "data": {},
                "message": f"❌ Error fetching ticket: {str(e)}"
            }

    @tool
    async def parse_ticket_requirements(self, ticket_id: str) -> Dict[str, Any]:
        """Parse ticket and extract structured requirements for Planning Agent.

        Args:
            ticket_id: JIRA ticket ID

        Returns:
            Dictionary with success, data (requirements), and message
        """
        # First fetch the ticket
        ticket_response = await self.fetch_jira_ticket(ticket_id)  # type: ignore[arg-type,call-arg]

        if not ticket_response["success"]:
            return ticket_response

        # Extract data from successful response
        ticket_data = ticket_response["data"]
        formatted_output = ticket_data.get("formatted_output", "")

        # Build requirements structure
        requirements_text = f"""
Requirements from {ticket_id}:

{formatted_output}

Note: This data should be sent to Planning Agent for plan generation.
"""

        return {
            "success": True,
            "data": {
                "ticket_id": ticket_id,
                "requirements": ticket_data,
                "formatted_requirements": requirements_text
            },
            "message": f"Successfully parsed requirements from {ticket_id}"
        }


# Helper functions (module-level, not part of class)

def _extract_acceptance_criteria(description: str) -> List[str]:
    """Extract acceptance criteria from ticket description.

    Looks for sections like:
    - "Acceptance Criteria:"
    - "AC:"
    - Bullet points
    """
    if not description:
        return []

    criteria = []

    # Look for "Acceptance Criteria" section
    ac_match = re.search(
        r'(?:acceptance criteria|ac|criteria):\s*\n(.*?)(?:\n\n|\Z)',
        description,
        re.IGNORECASE | re.DOTALL
    )

    if ac_match:
        ac_text = ac_match.group(1)
        # Extract bullet points
        lines = ac_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or line.startswith('•')):
                # Remove bullet point
                criterion = line.lstrip('-*• ').strip()
                if criterion:
                    criteria.append(criterion)

    return criteria


def _format_acceptance_criteria(criteria: List[str]) -> str:
    """Format acceptance criteria list."""
    if not criteria:
        return "No acceptance criteria specified"

    formatted = []
    for criterion in criteria:
        formatted.append(f"✓ {criterion}")

    return '\n'.join(formatted)


def _format_description(description: str) -> str:
    """Format description text.

    Handles JIRA's description format (may be JSON or plain text).
    """
    if not description:
        return "No description provided"

    # If description is very long, truncate
    max_length = 1000
    if len(description) > max_length:
        return description[:max_length] + "...\n(truncated)"

    return description


def _extract_sprint(fields: Dict[str, Any]) -> str:
    """Extract sprint information from ticket fields."""
    # Sprint field varies by JIRA configuration
    # Common field names: sprint, customfield_10020, etc.

    # Try common sprint fields
    sprint_fields = ["sprint", "customfield_10020", "customfield_10010"]

    for field_name in sprint_fields:
        sprint_data = fields.get(field_name)
        if sprint_data:
            if isinstance(sprint_data, list) and sprint_data:
                # Get latest sprint
                sprint = sprint_data[-1]
                if isinstance(sprint, dict):
                    return cast(str, sprint.get("name", "Unknown Sprint"))
                elif isinstance(sprint, str):
                    # Parse sprint string (format: "name=Sprint 24,...")
                    name_match = re.search(r'name=([^,]+)', sprint)
                    if name_match:
                        return name_match.group(1)

    return "No sprint"
