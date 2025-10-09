"""
Runtime module for the Coding Agent

This module provides the entry point for running the coding agent
with proper initialization and error handling.
"""

import json
import os
import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir))

from coding_agent import create_coding_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for the coding agent runtime."""
    try:
        # Initialize workspace root
        workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
        logger.info(f"Initializing coding agent with workspace: {workspace_root}")
        
        # Create the coding agent
        agent = create_coding_agent(workspace_root)
        
        # Start the agent (this will depend on your specific runtime requirements)
        logger.info("Coding agent initialized successfully")
        
        # For AgentCore, the agent should be available for invocation
        # The actual runtime loop is handled by the AgentCore framework
        return agent
        
    except Exception as e:
        logger.error(f"Failed to initialize coding agent: {e}")
        sys.exit(1)

async def strands_agent_coding(user_input: str, user_id: str = "default") -> str:
    """
    AgentCore entrypoint for the Coding Agent with streaming support.
    
    Args:
        user_input: User's coding request
        user_id: User identifier for session management
        
    Yields:
        Streaming response chunks
    """
    from .common.response_formatter import format_coding_response, create_error_response
    
    try:
        # Initialize workspace root
        workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
        logger.info(f"Initializing coding agent with workspace: {workspace_root}")
        
        # Create the coding agent
        agent = create_coding_agent(workspace_root)
        
        # Stream progress for initialization
        yield f"data: {json.dumps({'type': 'progress', 'message': 'Coding agent initialized successfully'})}\n\n"
        
        # Process user input with streaming
        try:
            # Use async streaming if available
            if hasattr(agent, 'stream_async'):
                async for chunk in agent.stream_async(user_input, user_id=user_id):
                    if chunk:
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            else:
                # Fallback to synchronous processing
                logger.warning("Agent does not support streaming, falling back to synchronous processing")
                response = agent(user_input, user_id=user_id)
                
                # Format the response using the coding response formatter
                formatted_response = format_coding_response(
                    operation="agent_response",
                    result_data={"response": response},
                    success=True
                )
                
                yield f"data: {json.dumps({'type': 'response', 'content': formatted_response.to_dict()})}\n\n"
                
        except Exception as e:
            logger.error(f"Error during agent processing: {e}")
            error_response = create_error_response(str(e), "agent_processing")
            yield f"data: {json.dumps({'type': 'error', 'content': error_response.to_dict()})}\n\n"
            
        # Signal completion
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
    except Exception as e:
        logger.error(f"Failed to initialize coding agent: {e}")
        error_response = create_error_response(str(e), "agent_initialization")
        yield f"data: {json.dumps({'type': 'error', 'content': error_response.to_dict()})}\n\n"


if __name__ == "__main__":
    main()