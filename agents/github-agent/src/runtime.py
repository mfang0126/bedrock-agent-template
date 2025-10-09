"""GitHub Agent Runtime - AgentCore deployment entrypoint.

This module follows the notebook pattern for AWS Bedrock AgentCore Runtime deployment.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

from src.tools.issues import (
    close_github_issue,
    create_github_issue,
    list_github_issues,
    post_github_comment,
    update_github_issue,
)
from src.tools.pull_requests import (
    create_pull_request,
    list_pull_requests,
    merge_pull_request,
)

# Import tools
from src.tools.repos import create_github_repo, get_repo_info, list_github_repos

# Create AgentCore app
app = BedrockAgentCoreApp()

# Model configuration (Claude 3.5 Sonnet for Sydney region)
MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
REGION = "ap-southeast-2"  # Sydney

# Create Bedrock model
model = BedrockModel(model_id=MODEL_ID, region_name=REGION)

# Create GitHub agent
agent = Agent(
    model=model,
    tools=[
        list_github_repos,
        get_repo_info,
        create_github_repo,
        list_github_issues,
        create_github_issue,
        close_github_issue,
        post_github_comment,
        update_github_issue,
        create_pull_request,
        list_pull_requests,
        merge_pull_request,
    ],
    system_prompt="""You are a GitHub assistant. Use your tools to help users with repositories, issues, and pull requests. Authentication is automatic - never ask for tokens.""",
)


@app.entrypoint
async def strands_agent_github(payload):
    """AgentCore Runtime entrypoint with streaming support.

    This function is called by AgentCore Runtime when the agent is invoked.

    IMPORTANT: OAuth URLs are streamed back immediately when generated via callback.

    Args:
        payload: Request payload containing user input

    Yields:
        Streaming agent response events or OAuth URL
    """
    import asyncio

    from src.common import auth
    from src.common.utils import (
        AgentResponse,
        clean_json_response,
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

    # Register callback to capture OAuth URL immediately
    auth.oauth_url_callback = stream_oauth_url_callback

    # Initialize GitHub OAuth - this will trigger OAuth flow if no token exists
    print("🔐 Initializing GitHub authentication...")

    # Yield OAuth initialization progress (plain text with newline)
    yield "🔐 Initializing GitHub authentication...\n"

    # Create task to monitor OAuth URL queue and stream immediately
    async def monitor_oauth_queue():
        try:
            # Wait for URL with short timeout to avoid blocking
            url = await asyncio.wait_for(oauth_url_queue.get(), timeout=2.0)

            oauth_message = f"""🔐 GitHub Authorization Required

Please visit this URL to authorize access to your GitHub account:

{url}

After authorizing, please run your command again to access your GitHub data."""

            print("✅ Streaming OAuth URL to user immediately")

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
    auth_task = asyncio.create_task(auth.get_github_access_token())
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
            # Stream OAuth URL immediately (plain text with newline)
            yield oauth_response.message + "\n"
            # Cancel auth task and return early
            auth_task.cancel()
            return

    # Authentication completed without OAuth URL, proceed normally
    try:
        if not auth_task.done():
            await auth_task
        print("✅ GitHub authentication successful")

        # Yield authentication success (plain text with newline)
        yield "✅ GitHub authentication successful\n"

    except Exception as e:
        print(f"⚠️ GitHub authentication pending or failed: {e}")

        # Fallback: Check if OAuth URL was set but not streamed
        if auth.pending_oauth_url and not oauth_url_received:
            oauth_message = f"""🔐 GitHub Authorization Required

Please visit this URL to authorize access to your GitHub account:

{auth.pending_oauth_url}

After authorizing, please run your command again to access your GitHub data."""

            # Yield OAuth URL (plain text with newline)
            yield oauth_message + "\n"
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
            print(f"📤 Server log - Full event: {event}")

            # Extract text from different event formats
            extracted_texts = []

            # Format 1: result -> content -> text
            if isinstance(event, dict) and "result" in event:
                result = event["result"]
                if isinstance(result, dict) and "content" in result:
                    for content_item in result["content"]:
                        if "text" in content_item:
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

            # Yield all extracted texts to client (with newlines)
            for text in extracted_texts:
                response_chunks.append(text)
                yield text + "\n"

        # Format final response using response formatter
        if response_chunks:
            combined_response = "".join(response_chunks)
            formatted_response = clean_json_response(combined_response, "github")

            # Yield formatted summary (plain text with newline)
            final_message = f"✅ GitHub operation complete: {formatted_response.message}"
            print(f"📤 Server log - Final summary: {final_message}")
            yield final_message + "\n"

    except Exception as e:
        error_message = f"❌ Error processing GitHub request: {str(e)}"
        # Log full error on server
        print(f"🚨 Server log - Error: {error_message}")

        # Yield simple error to client (plain text with newline)
        yield error_message + "\n"


if __name__ == "__main__":
    # Run the app (for local testing with agentcore launch --local)
    app.run()
