"""GitHub Agent Runtime - AgentCore deployment entrypoint.

This module follows the notebook pattern for AWS Bedrock AgentCore Runtime deployment.
"""

import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Import tools
from tools.github.repos import list_github_repos, get_repo_info, create_github_repo
from tools.github.issues import list_github_issues, create_github_issue, close_github_issue

# Create AgentCore app
app = BedrockAgentCoreApp()

# Model configuration (Claude 3.7 Sonnet)
# Use cross-region inference for regions outside US
# For us-east-1/us-west-2: use "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
# For other regions: use "anthropic.claude-3-5-sonnet-20241022-v2:0" (latest available)
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"

# Create Bedrock model
model = BedrockModel(model_id=MODEL_ID)

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
    ],
    system_prompt="""You are a helpful GitHub assistant that helps users manage their GitHub repositories and issues.

You have access to tools for:
- Listing repositories
- Getting repository information
- Creating repositories
- Listing issues
- Creating issues
- Closing issues

When users ask about their GitHub account, use the appropriate tools to help them.
Provide clear, friendly responses with relevant information formatted nicely."""
)


@app.entrypoint
async def strands_agent_github(payload):
    """AgentCore Runtime entrypoint.

    This function is called by AgentCore Runtime when the agent is invoked.
    Handles GitHub OAuth authentication flow automatically.

    Args:
        payload: Request payload containing user input

    Returns:
        Agent response
    """
    user_input = payload.get("prompt", "")
    print(f"📥 User input: {user_input}")

    # Import the OAuth function
    from common.auth.github import get_github_access_token, github_access_token

    # Check if we need to get the token (first call or token expired)
    if not github_access_token:
        print("🔐 GitHub token not available, triggering OAuth flow...")
        try:
            await get_github_access_token()
            print("✅ GitHub OAuth completed, token available")
        except Exception as e:
            print(f"❌ GitHub OAuth failed: {e}")
            return {"result": {"role": "assistant", "content": [{"text": f"GitHub authentication failed: {e}. Please complete the OAuth flow to continue."}]}}

    # Run agent with authenticated token
    response = agent(user_input)

    print(f"📤 Agent response: {response.message}")

    # Return response message
    return {"result": response.message}


if __name__ == "__main__":
    # Run the app (for local testing with agentcore launch --local)
    app.run()
