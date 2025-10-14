#!/usr/bin/env python3
"""Local testing script for GitHub agent.

This script allows testing the GitHub agent logic locally without deploying
to AWS AgentCore. It uses mock authentication to bypass OAuth requirements.

Usage:
    python test_local.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import create_github_agent
from src.auth import MockGitHubAuth

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_agent_creation():
    """Test that agent can be created successfully."""
    print("\n" + "="*60)
    print("TEST 1: Agent Creation")
    print("="*60)

    try:
        auth = MockGitHubAuth()
        agent = create_github_agent(auth)
        print("✅ Agent created successfully")
        print(f"   Tool names: {', '.join(agent.tool_names)}")
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False


async def test_list_repos():
    """Test listing repositories with mock auth."""
    print("\n" + "="*60)
    print("TEST 2: List Repositories")
    print("="*60)

    try:
        auth = MockGitHubAuth()
        agent = create_github_agent(auth)

        print("📝 Query: 'List my repositories'")
        response = await agent.invoke_async("List my repositories")

        print("\n📤 Response:")
        print(response)
        print("\n✅ Test completed")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Full error:")
        return False


async def test_repo_info():
    """Test getting repository info with mock auth."""
    print("\n" + "="*60)
    print("TEST 3: Get Repository Info")
    print("="*60)

    try:
        auth = MockGitHubAuth()
        agent = create_github_agent(auth)

        print("📝 Query: 'Get info about test-repo'")
        response = await agent.invoke_async("Get info about test-repo")

        print("\n📤 Response:")
        print(response)
        print("\n✅ Test completed")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Full error:")
        return False


async def test_create_issue():
    """Test creating an issue with mock auth."""
    print("\n" + "="*60)
    print("TEST 4: Create Issue")
    print("="*60)

    try:
        auth = MockGitHubAuth()
        agent = create_github_agent(auth)

        print("📝 Query: 'Create a test issue in my-repo'")
        response = await agent.invoke_async("Create a test issue in my-repo titled 'Test Issue'")

        print("\n📤 Response:")
        print(response)
        print("\n✅ Test completed")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Full error:")
        return False


async def interactive_mode():
    """Interactive testing mode."""
    print("\n" + "="*60)
    print("INTERACTIVE MODE")
    print("="*60)
    print("Type 'exit' or 'quit' to stop\n")

    auth = MockGitHubAuth()
    agent = create_github_agent(auth)

    while True:
        try:
            user_input = input("\n💬 You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("\n🤖 Agent:")
            response = await agent.invoke_async(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.exception("Full error:")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("GitHub Agent Local Testing")
    print("="*60)
    print("Testing agent logic with mock authentication")
    print("No AWS deployment or OAuth required")

    # Run automated tests
    results = []
    results.append(await test_agent_creation())
    results.append(await test_list_repos())
    results.append(await test_repo_info())
    results.append(await test_create_issue())

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"⚠️ {total - passed} test(s) failed")

    # Ask for interactive mode
    print("\n" + "="*60)
    user_choice = input("\nRun interactive mode? (y/n): ").strip().lower()
    if user_choice == 'y':
        await interactive_mode()

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
