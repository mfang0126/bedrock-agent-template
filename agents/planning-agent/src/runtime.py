"""Planning Agent runtime entrypoint for AgentCore."""

import sys
from pathlib import Path
from typing import Any, Dict

sys.path.insert(0, str(Path(__file__).parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from tools.task_planner import breakdown_task
from common.utils import format_planning_response, create_error_response

app = BedrockAgentCoreApp()


@app.entrypoint
async def strands_agent_planning(payload: Dict[str, Any]):
    """Handle Planning Agent requests with simple plain text output."""

    user_input = payload.get("prompt") or payload.get("input") or ""
    context = payload.get("context") or {}

    if not user_input.strip():
        yield "❌ Error: Planning prompt is required"
        return

    try:
        plan = breakdown_task(prompt=user_input, context=context)
        response = format_planning_response(plan, requirements=user_input)
        yield response.message
    except Exception as exc:  # pragma: no cover - defensive logging only
        yield f"❌ Error: {str(exc)}"


if __name__ == "__main__":
    app.run()
