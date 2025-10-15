"""Utilities for normalizing Planning agent responses."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class AgentResponse:
    """Standardized agent response structure."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    agent_type: Optional[str] = None

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()

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
                agent_type=agent_type,
            )
    except json.JSONDecodeError:
        pass

    return AgentResponse(success=True, message=raw_response, agent_type=agent_type)


def create_error_response(error_message: str, agent_type: str = "planning") -> AgentResponse:
    """Create a standardized error response."""
    return AgentResponse(
        success=False,
        message=f"Error: {error_message}",
        agent_type=agent_type,
    )


def format_planning_response(
    plan_data: Dict[str, Any],
    requirements: Optional[str] = None,
    validation_results: Optional[Dict[str, Any]] = None,
    success: bool = True,
) -> AgentResponse:
    """Create a standardized planning response payload with formatted markdown."""
    phase_count = len(plan_data.get("phases", []))
    effort = plan_data.get("estimated_effort", "unspecified effort")
    risk_level = plan_data.get("risk_level", "Unknown")
    title = plan_data.get("title", "Task Plan")
    summary = plan_data.get("summary", "")

    # Build formatted markdown message
    message_parts = [
        f"# 📋 {title}",
        "",
        f"**Summary:** {summary}",
        f"**Estimated Effort:** {effort}",
        f"**Risk Level:** {risk_level}",
        f"**Phases:** {phase_count}",
        "",
    ]

    # Add phases with tasks
    phases = plan_data.get("phases", [])
    for i, phase in enumerate(phases, 1):
        phase_title = phase.get("title", f"Phase {i}")
        duration = phase.get("duration", "N/A")
        tasks = phase.get("tasks", [])

        message_parts.append(f"## Phase {i}: {phase_title}")
        message_parts.append(f"**Duration:** {duration}")
        message_parts.append("")
        message_parts.append("**Tasks:**")
        for task in tasks:
            message_parts.append(f"- {task}")
        message_parts.append("")

    # Add dependencies if present
    dependencies = plan_data.get("dependencies", [])
    if dependencies:
        message_parts.append("## 🔗 Dependencies")
        for dep in dependencies:
            message_parts.append(f"- {dep}")
        message_parts.append("")

    message = "\n".join(message_parts)

    return AgentResponse(
        success=success,
        message=message,
        data={
            "plan": plan_data,
            "requirements": requirements,
            "validation": validation_results,
        },
        agent_type="planning"
    )
