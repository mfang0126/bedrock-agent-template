"""Jira Agent - Pure agent logic without deployment concerns.

This module contains the core Jira agent logic, independent of AgentCore runtime.
It uses dependency injection for authentication, enabling both local testing and production deployment.
"""

import os
from strands import Agent
from strands.models import BedrockModel

from src.auth import JiraAuth
from src.tools.tickets import JiraTicketTools
from src.tools.updates import JiraUpdateTools


# Model configuration
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
REGION = "ap-southeast-2"  # Sydney


def create_jira_agent(auth: JiraAuth) -> Agent:
    """Create a Jira agent with injected authentication.

    This factory function creates a fully configured Jira agent using
    the provided authentication implementation. The agent is testable
    with MockJiraAuth or production-ready with AgentCoreJiraAuth.

    Args:
        auth: JiraAuth implementation (mock or real OAuth)

    Returns:
        Agent: Configured Strands Agent with Jira tools

    Example:
        >>> # Local testing
        >>> from src.auth import MockJiraAuth
        >>> auth = MockJiraAuth()
        >>> agent = create_jira_agent(auth)
        >>> response = agent("Get ticket PROJ-123")
        >>>
        >>> # Production with OAuth
        >>> from src.auth import AgentCoreJiraAuth
        >>> auth = AgentCoreJiraAuth(oauth_url_callback)
        >>> agent = create_jira_agent(auth)
        >>> response = agent.stream_async("Update PROJ-123 to In Progress")
    """
    # Initialize tool classes with auth injection
    ticket_tools = JiraTicketTools(auth)
    update_tools = JiraUpdateTools(auth)

    # Create Bedrock model
    model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

    # Create agent with all tools from tool classes
    agent = Agent(
        model=model,
        tools=[
            # Ticket tools
            ticket_tools.fetch_jira_ticket,
            ticket_tools.parse_ticket_requirements,
            # Update tools
            update_tools.update_jira_status,
            update_tools.add_jira_comment,
            update_tools.link_github_issue,
        ],
        system_prompt="""You are a JIRA Agent specialized in managing JIRA tickets.

**Your Responsibilities:**
- Fetch and parse JIRA ticket details
- Update ticket status (transitions)
- Add comments to tickets
- Link GitHub issues/PRs to tickets

**Available Capabilities:**
- Ticket operations: fetch, parse requirements
- Status updates: change ticket status with valid transitions
- Comments: add comments with optional GitHub links
- GitHub integration: link issues and PRs to tickets

**Authentication:**
Authentication is handled automatically. Never ask users for tokens or credentials.

**Best Practices:**
- Always validate ticket IDs (format: PROJECT-123)
- Handle authentication errors gracefully
- Provide clear success/error messages
- Use markdown formatting for readability
- Include relevant URLs in responses

**Ticket ID Format:**
- Valid: PROJ-123, ABC-456, MYPROJECT-789
- Invalid: proj-123, P-123, TOOLONGPROJECT-123

**Status Transitions:**
- Check available transitions before attempting status update
- Provide helpful error messages with available options
- Confirm successful status changes

**Examples:**
- "Get details for ticket PROJ-123"
- "Update PROJ-123 to In Progress"
- "Add comment to PROJ-123: Work started"
- "Link GitHub PR https://github.com/org/repo/pull/456 to PROJ-123"
""",
    )

    return agent
