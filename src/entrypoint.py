"""GitHub Agent Runtime - AgentCore deployment entrypoint.

This module follows the notebook pattern for AWS Bedrock AgentCore Runtime deployment.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Import tools
from src.tools.github.repos import list_github_repos, get_repo_info, create_github_repo
from src.tools.github.issues import (
    list_github_issues,
    create_github_issue,
    close_github_issue,
    post_github_comment,
    update_github_issue
)
from src.tools.github.pull_requests import (
    create_pull_request,
    list_pull_requests,
    merge_pull_request
)

# Create AgentCore app
app = BedrockAgentCoreApp()

# Model configuration (Claude 3.5 Sonnet for Sydney region)
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"  # Sydney

# Create Bedrock model
model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

# Create GitHub agent
agent = Agent(
    model=model,
    tools=[
        list_github_repos,
        get_repo_info,
        create_github_repo,
        list_github_issues,
        create_github_issue,
        close_github_issue,
        post_github_comment,
        update_github_issue,
        create_pull_request,
        list_pull_requests,
        merge_pull_request,
    ],
    system_prompt="""You are a helpful GitHub assistant that helps users manage their GitHub repositories, issues, and pull requests.

You have access to tools for:
- Listing repositories
- Getting repository information
- Creating repositories
- Listing issues
- Creating issues
- Closing issues
- Posting comments on issues
- Updating issues (state, labels, assignees)
- Creating pull requests
- Listing pull requests
- Merging pull requests

When users ask about their GitHub account, use the appropriate tools to help them.
Provide clear, friendly responses with relevant information formatted nicely."""
)


@app.entrypoint
async def strands_agent_github(payload):
    """AgentCore Runtime entrypoint.

    This function is called by AgentCore Runtime when the agent is invoked.
    GitHub OAuth authentication is handled automatically by the @requires_access_token decorators.

    Args:
        payload: Request payload containing user input

    Returns:
        Agent response
    """
    user_input = payload.get("prompt", "")
    print(f"📥 User input: {user_input}")

    response = agent(user_input)

    print(f"📤 Agent response: {response.message}")

    # Return response message
    return {"result": response.message}


if __name__ == "__main__":
    # Run the app (for local testing with agentcore launch --local)
    app.run()
