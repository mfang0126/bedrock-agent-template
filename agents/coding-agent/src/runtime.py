"""
Runtime module for the Coding Agent

This module provides the entry point for running the coding agent
with proper initialization and error handling.
"""

import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from agent import create_coding_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Create the agent once at module level
workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
logger.info(f"Initializing coding agent with workspace: {workspace_root}")
agent = create_coding_agent(workspace_root)
logger.info("Coding agent initialized successfully")


def _extract_user_input(payload):
    """Extract user input from various possible payload formats."""
    if not isinstance(payload, dict):
        logger.warning(f"Invalid payload type: {type(payload)}")
        return ""

    # Try common payload keys in order of preference
    for key in ["prompt", "input", "message", "text", "query"]:
        value = payload.get(key, "")
        if value and isinstance(value, str) and value.strip():
            return value.strip()

    logger.warning(f"No valid input found in payload keys: {list(payload.keys())}")
    return ""


@app.entrypoint
async def strands_agent_coding(payload):
    """
    Coding Agent entrypoint for processing user requests with streaming support.

    Handles coding operations with workspace isolation and safety controls.
    """
    try:
        # Extract user input from payload
        user_input = _extract_user_input(payload)

        # Validate input
        if not user_input:
            logger.info("Empty input received, returning greeting message")
            yield "Hello! I'm the Coding Agent. Please provide a coding task or request."
            return

        logger.info(f"📥 Processing coding request: {user_input}")

        # Process the request with streaming
        stream = agent.stream_async(user_input)

        # Stream response chunks
        async for event in stream:
            # Extract text from different event formats
            if isinstance(event, dict):
                if "text" in event:
                    yield event["text"]
                elif "content" in event:
                    yield event["content"]
            elif isinstance(event, str):
                yield event

    except Exception as e:
        logger.error(f"Coding Agent error: {str(e)}", exc_info=True)
        yield f"❌ Error: {str(e)}"


if __name__ == "__main__":
    app.run()