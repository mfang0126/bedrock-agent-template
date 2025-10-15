"""Planning Agent Runtime - Dual-mode client/agent communication.

This runtime supports both:
1. Client mode: Streaming human-readable text with progress
2. Agent mode: Structured JSON responses for A2A communication
"""

from typing import Any, Dict

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.tools.task_planner import breakdown_task
from src.common.utils import format_planning_response
from src.response_protocol import (
    ResponseMode,
    create_response,
    detect_mode,
)

app = BedrockAgentCoreApp()


async def handle_client_mode(user_input: str, context: Dict[str, Any]) -> str:
    """Stream response for human clients.

    Args:
        user_input: User's planning request
        context: Additional context for planning

    Returns:
        Formatted planning response message
    """
    try:
        print("🚀 Processing in CLIENT mode (streaming)...")

        plan = breakdown_task(prompt=user_input, context=context)
        response = format_planning_response(plan, requirements=user_input)

        # Return the formatted message
        return response.message

    except Exception as e:
        error_response = create_response(
            success=False,
            message=f"❌ Error: {str(e)}",
            agent_type="planning"
        )
        return error_response.to_client_text()


async def handle_agent_mode(user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Execute request for agent-to-agent communication.

    Args:
        user_input: Agent's planning command
        context: Additional context for planning

    Returns:
        Structured JSON response dictionary
    """
    try:
        print("🤖 Processing in AGENT mode (structured)...")

        plan = breakdown_task(prompt=user_input, context=context)
        response = format_planning_response(plan, requirements=user_input)

        # Return structured response with plan data
        return create_response(
            success=True,
            message="Planning completed successfully",
            data={
                "plan": plan,
                "formatted_plan": response.message
            },
            agent_type="planning",
            metadata={
                "requirements": user_input,
                "context_provided": bool(context)
            }
        ).to_dict()

    except Exception as e:
        error_response = create_response(
            success=False,
            message=f"Planning operation failed: {str(e)}",
            agent_type="planning"
        )
        return error_response.to_dict()


@app.entrypoint
async def strands_agent_planning(payload: Dict[str, Any]):
    """Planning Agent entrypoint with dual-mode support.

    Automatically detects if caller is:
    - Human client: Returns streaming text with progress
    - Another agent: Returns structured JSON

    Args:
        payload: Request payload with 'prompt' and optional mode indicators

    Yields:
        Streaming responses (client mode) or structured dict (agent mode)
    """
    # Detect communication mode
    mode = detect_mode(payload)
    user_input = payload.get("prompt") or payload.get("input") or ""
    context = payload.get("context") or {}

    print("\n" + "="*60)
    print("📥 Planning Agent Request")
    print(f"   Mode: {mode.value.upper()}")
    print(f"   Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
    print("="*60 + "\n")

    # Validate input
    if not user_input.strip():
        error_msg = "❌ Error: Planning prompt is required"
        if mode == ResponseMode.AGENT:
            yield create_response(False, error_msg, agent_type="planning").to_dict()
        else:
            yield error_msg
        return

    # Execute based on mode
    if mode == ResponseMode.AGENT:
        # Agent-to-agent: Return structured response
        result = await handle_agent_mode(user_input, context)
        yield result
    else:
        # Client: Stream human-readable response
        result = await handle_client_mode(user_input, context)
        yield result


if __name__ == "__main__":
    app.run()
