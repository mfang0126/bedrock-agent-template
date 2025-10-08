"""JIRA Agent Runtime - AgentCore deployment entrypoint.

This agent manages JIRA ticket operations including fetching details,
updating status, and adding comments.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Import JIRA tools
from src.tools.jira import (
    fetch_jira_ticket,
    parse_ticket_requirements,
    update_jira_status,
    add_jira_comment,
    link_github_issue
)

# Create AgentCore app
app = BedrockAgentCoreApp()

# Model configuration (Claude 3.5 Sonnet for Sydney region)
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"  # Sydney

# Create Bedrock model
model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

# Create JIRA agent
agent = Agent(
    model=model,
    tools=[
        fetch_jira_ticket,
        parse_ticket_requirements,
        update_jira_status,
        add_jira_comment,
        link_github_issue,
    ],
    system_prompt="""You are a JIRA Agent specialized in fetching and managing JIRA tickets.

Your responsibilities:
1. Fetch ticket details from JIRA
2. Extract requirements and acceptance criteria
3. Update ticket status (transitions)
4. Add comments to tickets
5. Link GitHub issues to JIRA tickets

Guidelines:
- Always validate ticket IDs (format: PROJECT-123)
- Extract structured data from ticket descriptions
- Handle JIRA API errors gracefully
- Return formatted, readable responses
- When fetching tickets, include all relevant details
- When updating status, verify the transition is available
- When adding comments, format them clearly

Available Tools:
- fetch_jira_ticket: Get complete ticket details
- parse_ticket_requirements: Extract structured requirements for planning
- update_jira_status: Change ticket status (e.g., "To Do" → "In Progress")
- add_jira_comment: Add comment to ticket
- link_github_issue: Link GitHub issue/PR to JIRA ticket

Security:
- Tickets are fetched using user-specific JIRA tokens from AgentCore Identity
- Each user can only access tickets they have permission to view
- All API calls are authenticated per-user

Example Requests:
- "Get details for JIRA-123"
- "Move PROJ-456 to In Progress"
- "Add comment to JIRA-789: Implementation started"
- "Link GitHub issue #42 to JIRA-123"
"""
)


@app.entrypoint
async def strands_agent_jira(payload):
    """AgentCore Runtime entrypoint for JIRA Agent.

    Args:
        payload: Request payload containing user input

    Returns:
        Agent response
    """
    user_input = payload.get("prompt", "")
    print(f"📥 JIRA agent input: {user_input}")

    # Execute JIRA agent
    response = agent(user_input)

    print(f"📤 JIRA agent response: {response.message}")

    # Return response message
    return {"result": response.message}


if __name__ == "__main__":
    # Run the app (for local testing with agentcore launch --local)
    app.run()
