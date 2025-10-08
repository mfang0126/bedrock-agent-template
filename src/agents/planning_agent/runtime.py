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

# Import planning tools (sync)
from src.tools.planning import (
    generate_implementation_plan,
    parse_requirements,
    validate_plan
)

# Import async planning tools
from src.tools.planning.async_tools import (
    submit_plan_generation,
    submit_requirements_parsing,
    submit_plan_validation,
    get_task_result
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
        # Sync tools (immediate results)
        generate_implementation_plan,
        parse_requirements,
        validate_plan,
        # Async tools (submit + poll pattern)
        submit_plan_generation,
        submit_requirements_parsing,
        submit_plan_validation,
        get_task_result,
    ],
    system_prompt="""You are a planning assistant. You have two modes:

SYNC MODE (default for simple requests):
- Use generate_implementation_plan, parse_requirements, validate_plan
- Returns results immediately
- Best for: Quick requests, simple plans

ASYNC MODE (for complex operations):
- Use submit_plan_generation, submit_requirements_parsing, submit_plan_validation
- These tools return a task_id immediately (< 1 second)
- IMPORTANT: After calling a submit_* tool, STOP and return the task_id message to the user
- DO NOT call get_task_result() in the same conversation
- User will call you again later with the task_id to check status
- Best for: Complex plans, detailed analysis, when user prefers async

Choose async mode if:
1. User explicitly requests async/"in background"/"submit task"
2. Request is complex and detailed
3. User wants to continue doing other things while waiting

get_task_result(task_id) is ONLY used when:
- User provides a task_id from a previous submission
- User asks to "check status" or "get result" for a task_id

Otherwise use sync mode for simplicity."""
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
