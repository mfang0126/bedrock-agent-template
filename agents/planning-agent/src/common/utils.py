"""Utilities for normalizing Planning agent responses."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AgentResponse:
    """Standardized response wrapper for the Planning agent."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None
    agent_type: str = "planning"

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
        if not self.agent_type:
            self.agent_type = "planning"

    def to_dict(self) -> Dict[str, Any]:
        """Convert the response into a serializable dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
            "agent_type": self.agent_type,
        }

    def to_json(self) -> str:
        """Render the response as a JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def clean_json_response(raw_response: str, agent_type: str = "planning") -> AgentResponse:
    """Normalize loosely structured JSON output returned by the planning tools."""
    try:
        if raw_response.strip().startswith("{"):
            parsed = json.loads(raw_response)
            return AgentResponse(
                success=parsed.get("success", True),
                message=parsed.get("message", ""),
                data=parsed.get("data"),
                agent_type=agent_type or "planning",
            )
    except json.JSONDecodeError:
        pass

    return AgentResponse(success=True, message=raw_response, agent_type=agent_type or "planning")


def format_planning_response(
    plan_data: Dict[str, Any],
    requirements: Optional[str] = None,
    validation_results: Optional[Dict[str, Any]] = None,
    success: bool = True,
) -> AgentResponse:
    """Create a standardized planning response payload."""
    phase_count = len(plan_data.get("phases", []))
    effort = plan_data.get("estimated_effort", "unspecified effort")
    message = f"Generated implementation plan with {phase_count} phases (effort: {effort})."

    return AgentResponse(
        success=success,
        message=message,
        data={
            "plan": plan_data,
            "requirements": requirements,
            "validation": validation_results,
        },
    )


def create_error_response(error_message: str, agent_type: str = "planning") -> AgentResponse:
    """Create a standardized error response."""
    return AgentResponse(
        success=False,
        message=f"Error: {error_message}",
        agent_type=agent_type,
    )
