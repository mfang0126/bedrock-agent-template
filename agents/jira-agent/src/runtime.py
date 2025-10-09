"""JIRA Agent Runtime - AgentCore deployment entrypoint.

A specialized agent for managing JIRA ticket operations including:
- Fetching and parsing ticket details
- Updating ticket status
- Adding comments to tickets
- Linking GitHub issues/PRs to tickets

This agent uses OAuth 2.0 authentication through AgentCore Identity.
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

# Import JIRA tools
from src.tools import (
    fetch_jira_ticket,
    parse_ticket_requirements,
    update_jira_status,
    add_jira_comment,
    link_github_issue,
)

# Bedrock model configuration
import os
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the AgentCore app
app = BedrockAgentCoreApp()

# Create the agent with tools and system prompt
agent = Agent(
    model=BedrockModel(model_id=MODEL_ID),
    tools=[
        fetch_jira_ticket,
        parse_ticket_requirements,
        update_jira_status,
        add_jira_comment,
        link_github_issue,
    ],
    system_prompt="""You are a JIRA Agent specialized in managing JIRA tickets.

Your responsibilities:
- Fetch and parse JIRA ticket details
- Update ticket status (transitions)
- Add comments to tickets
- Link GitHub issues/PRs to tickets

Guidelines:
- Always validate ticket IDs (format: PROJECT-123)
- Handle authentication errors gracefully
- Provide clear success/error messages
- Use OAuth 2.0 tokens from AgentCore Identity

Available tools:
- fetch_jira_ticket: Get ticket details
- parse_ticket_requirements: Parse ticket for Planning Agent
- update_jira_status: Change ticket status
- add_jira_comment: Add comments to tickets
- link_github_issue: Link GitHub issues/PRs

Security:
- Uses user-specific OAuth tokens
- Respects JIRA permissions
- No API token fallback

Example requests:
- "Get details for ticket PROJ-123"
- "Update PROJ-123 to In Progress"
- "Add comment to PROJ-123: Work started"
- "Link GitHub PR https://github.com/org/repo/pull/456 to PROJ-123"
"""
)

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
async def strands_agent_jira(payload):
    """JIRA Agent entrypoint for processing user requests with streaming support.

    Handles JIRA ticket operations with OAuth 2.0 authentication.
    """
    import asyncio

    from src.common import auth as jira_auth
    from src.common.utils import (
        AgentResponse,
        clean_json_response,
        create_error_response,
        create_oauth_message,
        extract_text_from_event,
        format_client_text,
        log_server_event,
        log_server_message,
    )

    try:
        # Extract user input from payload with better error handling
        user_input = _extract_user_input(payload)

        # Validate input
        if not user_input:
            logger.info("Empty input received, returning greeting message")
            yield format_client_text("Hello! I'm the JIRA Agent. Please provide a request related to JIRA tickets.")
            return

        # Queue to receive OAuth URLs from callback immediately
        oauth_url_queue: asyncio.Queue[str] = asyncio.Queue()
        oauth_url_received = False

        # Callback that puts OAuth URL into queue for immediate streaming
        def stream_oauth_url_callback(url: str):
            nonlocal oauth_url_received
            try:
                oauth_url_queue.put_nowait(url)
                oauth_url_received = True
                logger.info(f"📤 OAuth URL queued for immediate streaming: {url[:50]}...")
            except Exception as e:
                logger.error(f"⚠️ Error queuing OAuth URL: {e}")

        # Register callback to capture OAuth URL immediately
        jira_auth.oauth_url_callback = stream_oauth_url_callback

        # Initialize JIRA OAuth
        logger.info("🔐 Initializing JIRA authentication...")
        yield format_client_text("🔐 Initializing JIRA authentication...")

        # Create task to monitor OAuth URL queue and stream immediately
        async def monitor_oauth_queue():
            try:
                # Wait for URL with short timeout to avoid blocking
                url = await asyncio.wait_for(oauth_url_queue.get(), timeout=2.0)

                oauth_message = create_oauth_message(url, "JIRA")
                log_server_message("Streaming OAuth URL to user immediately", "success")

                # Use response formatter for OAuth response
                oauth_response = AgentResponse(
                    success=False,
                    message=oauth_message,
                    data={"oauth_url": url, "requires_authorization": True},
                    agent_type="jira",
                )

                return oauth_response
            except asyncio.TimeoutError:
                # No OAuth URL generated, authentication succeeded
                return None

        # Start authentication and OAuth URL monitoring concurrently
        auth_task = asyncio.create_task(jira_auth.get_jira_access_token())
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
            logger.info("✅ JIRA authentication successful")
            yield format_client_text("✅ JIRA authentication successful")

        except Exception as e:
            logger.warning(f"⚠️ JIRA authentication pending or failed: {e}")

            # Fallback: Check if OAuth URL was set but not streamed
            if jira_auth.pending_oauth_url and not oauth_url_received:
                oauth_message = create_oauth_message(jira_auth.pending_oauth_url, "JIRA")
                yield format_client_text(oauth_message)
                return

        logger.info(f"📥 Processing JIRA request: {user_input}")

        # Process the request with streaming
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
            formatted_response = clean_json_response(combined_response, "jira")

            # Yield formatted summary
            final_message = f"✅ JIRA operation complete: {formatted_response.message}"
            log_server_message(f"Final summary: {final_message}", "success")
            yield format_client_text(final_message)

    except Exception as e:
        logger.error(f"JIRA Agent error: {str(e)}", exc_info=True)

        # Use response formatter for error handling
        error_response = create_error_response(str(e), agent_type="jira")
        error_message = error_response.message

        # Log full error on server
        log_server_message(f"Error: {error_message}", "error")

        # Yield simple error to client
        yield format_client_text(error_message)


if __name__ == "__main__":
    app.run()