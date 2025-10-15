"""Unified response protocol for client and agent-to-agent communication.

This module provides a standardized way to handle responses that work for both:
1. Human clients (streaming text with emojis and progress)
2. Agent-to-agent communication (structured JSON data)
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum


class ResponseMode(Enum):
    """Response output mode."""
    CLIENT = "client"  # Human-readable streaming
    AGENT = "agent"    # Structured data for A2A


@dataclass
class AgentResponse:
    """Standardized response structure for all agents."""
    
    success: bool
    message: str  # Human-readable summary
    data: Optional[Dict[str, Any]] = None  # Structured data for agents
    agent_type: Optional[str] = None
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "agent_type": self.agent_type,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {}
        }
    
    def to_json(self) -> str:
        """Convert to JSON for A2A communication."""
        return json.dumps(self.to_dict(), indent=2)
    
    def to_client_text(self) -> str:
        """Convert to human-readable text for clients."""
        return self.message


def detect_mode(payload: Dict[str, Any]) -> ResponseMode:
    """Detect if caller is a client or another agent.
    
    Args:
        payload: Request payload
        
    Returns:
        ResponseMode.AGENT if caller is an agent, ResponseMode.CLIENT otherwise
    """
    # Check for A2A protocol markers
    if payload.get("_agent_call"):
        return ResponseMode.AGENT
    
    if payload.get("source_agent"):
        return ResponseMode.AGENT
    
    # Check headers for A2A user agent
    headers = payload.get("headers", {})
    user_agent = headers.get("user-agent", "").lower()
    if "agent2agent" in user_agent or "a2a" in user_agent:
        return ResponseMode.AGENT
    
    # Default to client mode
    return ResponseMode.CLIENT


def create_response(
    success: bool,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    agent_type: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AgentResponse:
    """Factory function for creating responses.
    
    Args:
        success: Whether the operation succeeded
        message: Human-readable summary
        data: Structured data for agents
        agent_type: Agent identifier
        metadata: Additional metadata
        
    Returns:
        AgentResponse instance
    """
    return AgentResponse(
        success=success,
        message=message,
        data=data,
        agent_type=agent_type,
        metadata=metadata
    )


def extract_text_from_event(event: Dict[str, Any]) -> list:
    """Extract text content from various agent event formats.
    
    Args:
        event: Agent streaming event dictionary
        
    Returns:
        List of extracted text strings
    """
    texts = []
    
    # Format 1: result -> content -> text
    if isinstance(event, dict) and "result" in event:
        result = event["result"]
        if isinstance(result, dict) and "content" in result:
            for item in result["content"]:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
    
    # Format 2: message -> content -> text
    if isinstance(event, dict) and "message" in event:
        message = event["message"]
        if isinstance(message, dict) and "content" in message:
            for item in message["content"]:
                if isinstance(item, dict) and "text" in item:
                    texts.append(item["text"])
                
                # Check for tool results
                if isinstance(item, dict) and "toolResult" in item:
                    tool_result = item["toolResult"]
                    if isinstance(tool_result, dict) and "content" in tool_result:
                        for tool_item in tool_result["content"]:
                            if isinstance(tool_item, dict) and "text" in tool_item:
                                texts.append(tool_item["text"])
    
    return texts
