"""Jira Agent Runtime - Dual-mode client/agent communication.

This runtime supports both:
1. Client mode: Streaming human-readable text with progress
2. Agent mode: Structured JSON responses for A2A communication
"""

import os
from typing import Dict, Any, AsyncIterator

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent import create_jira_agent
from src.auth import get_auth_provider

# Import response protocol from src
from src.response_protocol import (
    ResponseMode,
    create_response,
    detect_mode,
    extract_text_from_event,
)

# Create AgentCore app
app = BedrockAgentCoreApp()


async def handle_client_mode(agent, user_input: str) -> AsyncIterator[str]:
    """Stream response for human clients with real-time progress.
    
    Args:
        agent: Jira agent instance
        user_input: User's prompt
        
    Yields:
        Streaming text responses
    """
    try:
        print("🚀 Processing in CLIENT mode (streaming)...")
        
        # Stream agent events
        response_chunks = []
        
        async for event in agent.stream_async(user_input):
            # Yield raw event for streaming UI
            yield event
            
            # Collect text for final summary
            texts = extract_text_from_event(event)
            response_chunks.extend(texts)
        
        # Create final summary
        if response_chunks:
            combined = "".join(response_chunks)
            final_response = create_response(
                success=True,
                message=f"✅ Jira operation completed\n\n{combined[:200]}{'...' if len(combined) > 200 else ''}",
                data={"full_output": combined},
                agent_type="jira"
            )
            yield "\n" + final_response.to_client_text()
        
    except Exception as e:
        error_response = create_response(
            success=False,
            message=f"❌ Error: {str(e)}",
            agent_type="jira"
        )
        yield "\n" + error_response.to_client_text()


async def handle_agent_mode(agent, user_input: str) -> Dict[str, Any]:
    """Execute request for agent-to-agent communication.
    
    Args:
        agent: Jira agent instance
        user_input: Agent's command
        
    Returns:
        Structured JSON response dictionary
    """
    try:
        print("🤖 Processing in AGENT mode (structured)...")
        
        # Collect full response
        response_chunks = []
        
        async for event in agent.stream_async(user_input):
            texts = extract_text_from_event(event)
            response_chunks.extend(texts)
        
        combined = "".join(response_chunks)
        
        # Try to parse as JSON if possible
        import json
        structured_data = None
        try:
            if combined.strip().startswith("{"):
                structured_data = json.loads(combined)
        except json.JSONDecodeError:
            structured_data = {"output": combined}
        
        # Return structured response
        response = create_response(
            success=True,
            message="Jira operation completed successfully",
            data=structured_data or {"output": combined},
            agent_type="jira",
            metadata={
                "command": user_input,
                "output_length": len(combined)
            }
        )
        
        return response.to_dict()
        
    except Exception as e:
        error_response = create_response(
            success=False,
            message=f"Jira operation failed: {str(e)}",
            agent_type="jira"
        )
        return error_response.to_dict()


@app.entrypoint
async def strands_agent_jira(payload: Dict[str, Any]):
    """Jira Agent entrypoint with dual-mode support.
    
    Automatically detects if caller is:
    - Human client: Returns streaming text with progress
    - Another agent: Returns structured JSON
    
    Args:
        payload: Request payload with 'prompt' and optional mode indicators
        
    Yields:
        Streaming responses (client mode) or structured dict (agent mode)
    """
    # Detect communication mode
    mode = detect_mode(payload)
    user_input = payload.get("prompt", "")
    
    print("\n" + "="*60)
    print("📥 Jira Agent Request")
    print(f"   Mode: {mode.value.upper()}")
    print(f"   Input: {user_input[:100]}{'...' if len(user_input) > 100 else ''}")
    print("="*60 + "\n")
    
    # Validate input
    if not user_input:
        error_msg = "❌ Error: No input provided"
        if mode == ResponseMode.AGENT:
            yield create_response(False, error_msg, agent_type="jira").to_dict()
        else:
            yield error_msg
        return
    
    # Initialize agent
    env = os.getenv("AGENT_ENV", "prod")
    
    # Get auth provider (without OAuth callback for now)
    auth = get_auth_provider(env=env)
    agent = create_jira_agent(auth)
    
    # Handle authentication
    try:
        print("🔐 Authenticating with Jira...")
        await auth.get_token()
        print("✅ Jira authentication successful\n")
        
        if mode == ResponseMode.CLIENT:
            yield "✅ Jira authentication successful\n"
        
    except Exception as e:
        error_msg = f"❌ Authentication failed: {str(e)}"
        print(error_msg)
        
        if mode == ResponseMode.AGENT:
            yield create_response(False, error_msg, agent_type="jira").to_dict()
        else:
            yield error_msg
        return
    
    # Execute based on mode
    if mode == ResponseMode.AGENT:
        # Agent-to-agent: Return structured response
        result = await handle_agent_mode(agent, user_input)
        yield result
    else:
        # Client: Stream human-readable response
        async for chunk in handle_client_mode(agent, user_input):
            yield chunk


if __name__ == "__main__":
    # Run the app
    app.run()
