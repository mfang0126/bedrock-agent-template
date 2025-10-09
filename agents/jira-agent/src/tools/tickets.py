"""JIRA ticket operations tools.

Tools for fetching, parsing, and managing JIRA tickets.
"""

import re
import httpx
from strands import tool
from src.common.auth import get_jira_auth_headers, get_jira_url_cached


@tool
async def fetch_jira_ticket(ticket_id: str) -> str:
    """Fetch JIRA ticket details.

    Args:
        ticket_id: JIRA ticket ID (e.g., "PROJ-123")

    Returns:
        Formatted ticket details including title, description, acceptance criteria
    """
    # Validate ticket ID format
    if not ticket_id or not re.match(r'^[A-Z]{2,10}-\d+$', ticket_id):
        return f"❌ Invalid ticket ID format. Expected: PROJECT-123, got: {ticket_id}"

    try:
        # Get authentication headers (token set by runtime)
        headers = get_jira_auth_headers()
        jira_url = get_jira_url_cached()

        # Fetch ticket from JIRA API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{jira_url}/rest/api/3/issue/{ticket_id}",
                headers=headers,
                timeout=30.0
            )

            if response.status_code == 404:
                return f"❌ Ticket {ticket_id} not found"
            elif response.status_code == 401:
                return "❌ Authentication failed. Check JIRA credentials"
            elif response.status_code != 200:
                return f"❌ JIRA API error: {response.status_code} - {response.text}"

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
            return output

    except httpx.TimeoutException:
        return f"❌ Request timed out. JIRA may be slow or unreachable."
    except Exception as e:
        return f"❌ Error fetching ticket: {str(e)}"


def _extract_acceptance_criteria(description: str) -> list:
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


def _format_acceptance_criteria(criteria: list) -> str:
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


def _extract_sprint(fields: dict) -> str:
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
                    return sprint.get("name", "Unknown Sprint")
                elif isinstance(sprint, str):
                    # Parse sprint string (format: "name=Sprint 24,...")
                    name_match = re.search(r'name=([^,]+)', sprint)
                    if name_match:
                        return name_match.group(1)

    return "No sprint"


@tool
async def parse_ticket_requirements(ticket_id: str) -> str:
    """Parse ticket and extract structured requirements for Planning Agent.

    Args:
        ticket_id: JIRA ticket ID

    Returns:
        Structured requirements in JSON-like format
    """
    # First fetch the ticket
    ticket_details = await fetch_jira_ticket(ticket_id)

    if ticket_details.startswith("❌"):
        return ticket_details

    # For now, return the ticket details
    # Planning Agent will parse this
    return f"""
Requirements from {ticket_id}:

{ticket_details}

Note: This data should be sent to Planning Agent for plan generation.
"""