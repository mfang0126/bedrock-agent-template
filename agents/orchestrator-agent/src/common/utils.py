"""Utilities for orchestrator agent response handling."""

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
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
            "agent_type": self.agent_type,
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def clean_json_response(
    raw_response: str, agent_type: str = "orchestrator"
) -> AgentResponse:
    """
    Clean and standardize agent responses into a consistent JSON structure.

    Args:
        raw_response: Raw response from agent
        agent_type: Type of agent (orchestrator)

    Returns:
        Standardized AgentResponse object
    """
    try:
        # Try to parse if it's already JSON
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

    # Handle plain text responses
    return AgentResponse(success=True, message=raw_response, agent_type=agent_type)


def create_error_response(error_message: str, agent_type: str = "orchestrator") -> AgentResponse:
    """
    Create a standardized error response.

    Args:
        error_message: Error message text
        agent_type: Type of agent

    Returns:
        AgentResponse with error details
    """
    return AgentResponse(
        success=False,
        message=f"Error: {error_message}",
        agent_type=agent_type,
    )
