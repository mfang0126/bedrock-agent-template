"""Utilities for normalizing GitHub agent responses."""

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
    timestamp: str = None
    agent_type: str = None

    def __post_init__(self):
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
    raw_response: str, agent_type: str = "unknown"
) -> AgentResponse:
    """
    Clean and standardize agent responses into a consistent JSON structure.

    Args:
        raw_response: Raw response from agent
        agent_type: Type of agent (planning, github, etc.)

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


def format_github_response(
    action: str,
    result_data: Dict[str, Any],
    repository: str = None,
    success: bool = True,
) -> AgentResponse:
    """
    Format GitHub agent responses into standardized structure.

    Args:
        action: GitHub action performed (list_repos, create_issue, etc.)
        result_data: Result data from GitHub API
        repository: Repository name if applicable
        success: Whether the action was successful

    Returns:
        Formatted AgentResponse for GitHub operations
    """
    data = {
        "action": action,
        "repository": repository,
        "result": result_data,
        "items_count": len(result_data) if isinstance(result_data, list) else 1,
    }

    # Generate contextual message
    messages = {
        "list_repos": f"Found {len(result_data)} repositories",
        "create_repo": f"Successfully created repository: {result_data.get('name', 'Unknown') if isinstance(result_data, dict) else 'Unknown'}",
        "list_issues": f"Found {len(result_data)} issues in {repository}",
        "create_issue": f"Created issue #{result_data.get('number', 'Unknown') if isinstance(result_data, dict) else 'Unknown'}: {result_data.get('title', 'Unknown') if isinstance(result_data, dict) else 'Unknown'}",
        "close_issue": f"Closed issue #{result_data.get('number', 'Unknown') if isinstance(result_data, dict) else 'Unknown'} in {repository}",
    }

    message = messages.get(action, f"Completed {action} operation")

    return AgentResponse(
        success=success, message=message, data=data, agent_type="github"
    )
