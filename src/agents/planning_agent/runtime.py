"""Planning Agent Runtime - AgentCore deployment entrypoint.

This module follows the proven GitHub agent pattern for AWS Bedrock AgentCore Runtime deployment.
Simple, synchronous, minimal complexity.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Import planning tools
from src.tools.planning import (
    generate_implementation_plan,
    parse_requirements,
    validate_plan
)

# Create AgentCore app
app = BedrockAgentCoreApp()

# Model configuration (Claude 3.5 Sonnet for Sydney region)
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"  # Sydney

# Create Bedrock model
model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

# Create Planning agent
agent = Agent(
    model=model,
    tools=[
        generate_implementation_plan,
        parse_requirements,
        validate_plan,
    ],
    system_prompt="""You are a planning assistant. Use your tools to help users create implementation plans, parse requirements, and validate plans."""
)


@app.entrypoint
async def strands_agent_planning(payload):
    """AgentCore Runtime entrypoint for Planning Agent.

    This function is called by AgentCore Runtime when the agent is invoked.

    Args:
        payload: Request payload containing user input

    Returns:
        Agent response
    """
    user_input = payload.get("prompt", "")
    print(f"📥 Planning agent input: {user_input}")

    # Execute planning agent
    response = agent(user_input)

    print(f"📤 Planning agent response: {response.message}")

    # Return response message
    return {"result": response.message}


if __name__ == "__main__":
    # Run the app (for local testing with agentcore launch --local)
    app.run()
