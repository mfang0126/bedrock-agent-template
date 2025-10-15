#!/usr/bin/env python3
"""Local test script for GitHub Agent with mock authentication.

This script tests the GitHub agent locally without AWS deployment.
Uses MockGitHubAuth so no real OAuth is needed.
"""

import asyncio
import sys
from pathlib import Path

# Add agent to path
agent_dir = Path(__file__).parent.parent / "agents" / "github-agent"
sys.path.insert(0, str(agent_dir))

from src.auth import MockGitHubAuth
from src.agent import create_github_agent


async def test_agent(prompt: str):
    """Test the GitHub agent with a prompt."""
    print("=" * 60)
    print("🧪 GitHub Agent Local Test")
    print("=" * 60)
    print(f"\n📝 Prompt: {prompt}\n")

    # Create mock auth (no real OAuth needed)
    auth = MockGitHubAuth()

    # Create agent with mock auth
    agent = create_github_agent(auth)

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
        print("Usage: uv run scripts/test_github_local.py 'your prompt here'")
        print("\nExamples:")
        print("  uv run scripts/test_github_local.py 'what can you do'")
        print("  uv run scripts/test_github_local.py 'list my repositories'")
        print("\nNote: Uses mock auth - API calls will fail (testing structure only)")
        sys.exit(1)

    prompt = " ".join(sys.argv[1:])
    asyncio.run(test_agent(prompt))
