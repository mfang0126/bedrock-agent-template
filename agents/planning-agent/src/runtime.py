"""Planning Agent runtime entrypoint for AgentCore."""

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.tools.task_planner import breakdown_task
from src.common.utils import format_planning_response, create_error_response

app = BedrockAgentCoreApp()


@app.entrypoint
async def strands_agent_planning(payload: Dict[str, Any]):
    """Handle Planning Agent requests with a simple synchronous workflow."""

    user_input = payload.get("prompt") or payload.get("input") or ""
    context = payload.get("context") or {}

    if not user_input.strip():
        error = create_error_response("Planning prompt is required", agent_type="planning")
        return {
            "result": {
                "role": "assistant",
                "content": [{"text": error.message, "data": error.to_dict()}],
            }
        }

    try:
        plan = breakdown_task(prompt=user_input, context=context)
        response = format_planning_response(plan, requirements=user_input)
        return {
            "result": {
                "role": "assistant",
                "content": [
                    {
                        "text": response.message,
                        "data": response.to_dict(),
                    }
                ],
            }
        }
    except Exception as exc:  # pragma: no cover - defensive logging only
        error = create_error_response(str(exc), agent_type="planning")
        return {
            "result": {
                "role": "assistant",
                "content": [{"text": error.message, "data": error.to_dict()}],
            }
        }


if __name__ == "__main__":
    app.run()
