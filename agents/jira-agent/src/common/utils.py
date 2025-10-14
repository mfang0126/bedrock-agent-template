"""Utilities for runtime response handling and logging."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


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
    raw_response: str, agent_type: str = "unknown"
) -> AgentResponse:
    """
    Clean and standardize agent responses into a consistent JSON structure.

    Args:
        raw_response: Raw response from agent
        agent_type: Type of agent (planning, github, jira, etc.)

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


def extract_text_from_event(event: Dict[str, Any]) -> List[str]:
    """
    Extract text content from different agent event formats.

    Handles two formats:
    1. Standard result format: result -> content -> text
    2. Tool result format: message -> content -> toolResult -> content -> text

    Args:
        event: Agent streaming event dictionary

    Returns:
        List of extracted text strings
    """
    extracted_texts = []

    # Format 1: result -> content -> text
    if isinstance(event, dict) and "result" in event:
        result = event["result"]
        if isinstance(result, dict) and "content" in result:
            for content_item in result["content"]:
                if isinstance(content_item, dict) and "text" in content_item:
                    extracted_texts.append(content_item["text"])

    # Format 2: message -> content -> toolResult -> content -> text
    if isinstance(event, dict) and "message" in event:
        message = event["message"]
        if isinstance(message, dict) and "content" in message:
            for content_item in message["content"]:
                # Check for toolResult
                if isinstance(content_item, dict) and "toolResult" in content_item:
                    tool_result = content_item["toolResult"]
                    if isinstance(tool_result, dict) and "content" in tool_result:
                        for tool_content in tool_result["content"]:
                            if isinstance(tool_content, dict) and "text" in tool_content:
                                extracted_texts.append(tool_content["text"])

    return extracted_texts


def log_server_event(event: Dict[str, Any], prefix: str = "Full event") -> None:
    """
    Log event on server side with consistent formatting.

    Args:
        event: Event to log
        prefix: Log message prefix (default: "Full event")
    """
    print(f"📤 Server log - {prefix}: {event}")


def log_server_message(message: str, level: str = "info") -> None:
    """
    Log message on server side with emoji indicators.

    Args:
        message: Message to log
        level: Log level (info, success, warning, error)
    """
    emoji_map = {
        "info": "📤",
        "success": "✅",
        "warning": "⚠️",
        "error": "🚨",
    }
    emoji = emoji_map.get(level, "📤")
    print(f"{emoji} Server log - {message}")


def format_client_text(text: str, add_newline: bool = True) -> str:
    """
    Format text for client output with optional newline.

    Args:
        text: Text to format
        add_newline: Whether to add newline at end (default: True)

    Returns:
        Formatted text string
    """
    return text + "\n" if add_newline else text


def create_error_response(error_message: str, agent_type: str = "unknown") -> AgentResponse:
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


def create_oauth_message(oauth_url: str, service: str = "JIRA") -> str:
    """
    Create standardized OAuth authorization message.

    Args:
        oauth_url: OAuth authorization URL
        service: Service name (GitHub, JIRA, etc.)

    Returns:
        Formatted OAuth message string
    """
    return f"""🔐 {service} Authorization Required

Please visit this URL to authorize access to your {service} account:

{oauth_url}

After authorizing, please run your command again to access your {service} data."""
