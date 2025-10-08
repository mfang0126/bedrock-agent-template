"""GitHub Agent Runtime - AgentCore deployment entrypoint.

This module follows the notebook pattern for AWS Bedrock AgentCore Runtime deployment.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

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
    system_prompt="""You are a GitHub assistant. Use your tools to help users with repositories, issues, and pull requests. Authentication is automatic - never ask for tokens."""
)


@app.entrypoint
async def strands_agent_github(payload):
    """AgentCore Runtime entrypoint.

    This function is called by AgentCore Runtime when the agent is invoked.

    IMPORTANT: OAuth is initialized BEFORE agent runs. If OAuth URL is generated,
    we return it to the user immediately.

    Args:
        payload: Request payload containing user input

    Returns:
        Agent response or OAuth URL
    """
    from src.common.auth.github import get_github_access_token, pending_oauth_url

    user_input = payload.get("prompt", "")
    print(f"📥 User input: {user_input}")

    # Initialize GitHub OAuth - this will trigger OAuth flow if no token exists
    print("🔐 Initializing GitHub authentication...")
    try:
        await get_github_access_token()
        print("✅ GitHub authentication successful")
    except Exception as e:
        print(f"⚠️ GitHub authentication pending or failed: {e}")

    # Check if OAuth URL was generated
    if pending_oauth_url:
        oauth_message = f"""🔐 GitHub Authorization Required

Please visit this URL to authorize access to your GitHub account:

{pending_oauth_url}

After authorizing, please run your command again to access your GitHub data."""

        print("📤 Returning OAuth URL to user")
        return {
            "result": {
                "role": "assistant",
                "content": [{"text": oauth_message}]
            }
        }

    # OAuth successful, proceed with agent
    response = agent(user_input)

    print(f"📤 Agent response: {response.message}")

    # Return response message
    return {"result": response.message}


if __name__ == "__main__":
    # Run the app (for local testing with agentcore launch --local)
    app.run()
