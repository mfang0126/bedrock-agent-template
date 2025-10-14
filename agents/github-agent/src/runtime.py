"""GitHub Agent Runtime - AgentCore deployment entrypoint.

This module is a thin wrapper around the pure agent logic, handling only
AgentCore-specific concerns like OAuth URL streaming and runtime integration.
"""

import asyncio
import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from src.agent import create_github_agent
from src.auth import get_auth_provider

# Create AgentCore app
app = BedrockAgentCoreApp()


@app.entrypoint
async def strands_agent_github(payload):
    """AgentCore Runtime entrypoint with streaming support.

    This function is called by AgentCore Runtime when the agent is invoked.
    It handles OAuth URL streaming and delegates agent logic to the factory.

    IMPORTANT: OAuth URLs are streamed back immediately when generated via callback.

    Args:
        payload: Request payload containing user input

    Yields:
        Streaming agent response events or OAuth URL
    """
    from src.common.utils import (
        AgentResponse,
        clean_json_response,
        create_oauth_message,
        extract_text_from_event,
        format_client_text,
        log_server_event,
        log_server_message,
    )

    user_input = payload.get("prompt", "")
    print(f"📥 User input: {user_input}")

    # Queue to receive OAuth URLs from callback immediately
    oauth_url_queue: asyncio.Queue[str] = asyncio.Queue()
    oauth_url_received = False

    # Callback that puts OAuth URL into queue for immediate streaming
    def stream_oauth_url_callback(url: str):
        nonlocal oauth_url_received
        try:
            # Put URL in queue (non-blocking)
            oauth_url_queue.put_nowait(url)
            oauth_url_received = True
            print(f"📤 OAuth URL queued for immediate streaming: {url[:50]}...")
        except Exception as e:
            print(f"⚠️ Error queuing OAuth URL: {e}")

    # Get environment (local, dev, prod)
    env = os.getenv("AGENT_ENV", "prod")
    print(f"🌍 Environment: {env}")

    # Get appropriate auth provider with OAuth callback
    auth = get_auth_provider(env=env, oauth_url_callback=stream_oauth_url_callback)

    # Create GitHub agent with auth injection
    agent = create_github_agent(auth)

    # Initialize GitHub OAuth - this will trigger OAuth flow if no token exists
    print("🔐 Initializing GitHub authentication...")

    # Yield OAuth initialization progress
    yield format_client_text("🔐 Initializing GitHub authentication...")

    # Create task to monitor OAuth URL queue and stream immediately
    async def monitor_oauth_queue():
        try:
            # Wait for URL with short timeout to avoid blocking
            url = await asyncio.wait_for(oauth_url_queue.get(), timeout=2.0)

            oauth_message = create_oauth_message(url)
            log_server_message("Streaming OAuth URL to user immediately", "success")

            # Use response formatter for OAuth response
            oauth_response = AgentResponse(
                success=False,
                message=oauth_message,
                data={"oauth_url": url, "requires_authorization": True},
                agent_type="github",
            )

            return oauth_response
        except asyncio.TimeoutError:
            # No OAuth URL generated, authentication succeeded
            return None

    # Start authentication and OAuth URL monitoring concurrently
    auth_task = asyncio.create_task(auth.get_token())
    oauth_monitor_task = asyncio.create_task(monitor_oauth_queue())

    # Wait for either authentication to complete or OAuth URL to be generated
    done, pending = await asyncio.wait(
        [auth_task, oauth_monitor_task],
        return_when=asyncio.FIRST_COMPLETED
    )

    # Check if OAuth URL was received
    oauth_response = None
    if oauth_monitor_task in done:
        oauth_response = await oauth_monitor_task
        if oauth_response:
            # Stream OAuth URL immediately
            yield format_client_text(oauth_response.message)
            # Cancel auth task and return early
            auth_task.cancel()
            return

    # Authentication completed without OAuth URL, proceed normally
    try:
        if not auth_task.done():
            await auth_task
        print("✅ GitHub authentication successful")

        # Yield authentication success
        yield format_client_text("✅ GitHub authentication successful")

    except Exception as e:
        print(f"⚠️ GitHub authentication pending or failed: {e}")

        # Fallback: Check if OAuth URL was set but not streamed
        # (for AgentCore auth implementation)
        if hasattr(auth, 'get_pending_oauth_url'):
            pending_url = auth.get_pending_oauth_url()
            if pending_url and not oauth_url_received:
                oauth_message = create_oauth_message(pending_url)
                # Yield OAuth URL
                yield format_client_text(oauth_message)
                return

    # OAuth successful, proceed with agent streaming
    print("🚀 Processing GitHub request with streaming...")

    try:
        # Process with GitHub agent using streaming
        stream = agent.stream_async(user_input)

        # Collect response chunks for formatting
        response_chunks = []

        async for event in stream:
            # Log the full event on server side for debugging
            log_server_event(event)

            # Extract text from different event formats using utility
            extracted_texts = extract_text_from_event(event)

            # Yield all extracted texts to client
            for text in extracted_texts:
                response_chunks.append(text)
                yield format_client_text(text)

        # Format final response using response formatter
        if response_chunks:
            combined_response = "".join(response_chunks)
            formatted_response = clean_json_response(combined_response, "github")

            # Yield formatted summary
            final_message = f"✅ GitHub operation complete: {formatted_response.message}"
            log_server_message(f"Final summary: {final_message}", "success")
            yield format_client_text(final_message)

    except Exception as e:
        error_message = f"❌ Error processing GitHub request: {str(e)}"
        # Log full error on server
        log_server_message(f"Error: {error_message}", "error")

        # Yield simple error to client
        yield format_client_text(error_message)


if __name__ == "__main__":
    # Run the app (for local testing with agentcore launch --local)
    app.run()
