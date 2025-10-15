#!/usr/bin/env python3
"""Local test script for JIRA Agent with mock authentication.

This script tests the JIRA agent locally without AWS deployment.
Uses MockJiraAuth so no real OAuth is needed.
"""

import asyncio
import sys
from pathlib import Path

# Add agent to path
agent_dir = Path(__file__).parent.parent / "agents" / "jira-agent"
sys.path.insert(0, str(agent_dir))

from src.auth import MockJiraAuth
from src.agent import create_jira_agent


async def test_agent(prompt: str):
    """Test the JIRA agent with a prompt."""
    print("=" * 60)
    print("🧪 JIRA Agent Local Test")
    print("=" * 60)
    print(f"\n📝 Prompt: {prompt}\n")

    # Create mock auth (no real OAuth needed)
    auth = MockJiraAuth()

    # Create agent with mock auth
    agent = create_jira_agent(auth)

    # Run agent
    try:
        print("🤖 Agent Response:")
        print("-" * 60)

        async for event in agent.stream_async(prompt):
            # Print text events
            if isinstance(event, dict):
                if "text" in event:
                    print(event["text"], end="", flush=True)
                elif "content" in event:
                    print(event["content"], end="", flush=True)
            elif hasattr(event, "text"):
                print(event.text, end="", flush=True)
            elif isinstance(event, str):
                print(event, end="", flush=True)

        print("\n" + "-" * 60)
        print("✅ Test complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run scripts/test_jira_local.py 'your prompt here'")
        print("\nExamples:")
        print("  uv run scripts/test_jira_local.py 'what can you do'")
        print("  uv run scripts/test_jira_local.py 'list my projects'")
        print("\nNote: Uses mock auth - API calls will fail (testing structure only)")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    asyncio.run(test_agent(prompt))
