#!/usr/bin/env python3
"""Test GitHub agent with AWS Bedrock (requires valid AWS credentials).

This script tests the full agent including LLM inference, which requires:
- Valid AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
- AWS Bedrock access in ap-southeast-2 region
- IAM permissions for bedrock:InvokeModel

Note: GitHub API calls will fail with mock token, but LLM inference will work.
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
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_llm_inference():
    """Test LLM inference with AWS Bedrock."""
    print("\n" + "="*60)
    print("TEST: LLM Inference with AWS Bedrock")
    print("="*60)
    print()

    try:
        # Create agent with mock auth
        auth = MockGitHubAuth()
        agent = create_github_agent(auth)
        print("✅ Agent created successfully")
        print(f"   Tools: {len(agent.tool_names)} available")
        print()

        # Test simple query that doesn't require GitHub API
        query = "What tools do you have available?"
        print(f"📝 Query: '{query}'")
        print()
        print("🤖 Agent Response:")
        print("-" * 60)

        # Use invoke_async for complete response
        response = await agent.invoke_async(query)
        print(response)
        print("-" * 60)
        print()
        print("✅ LLM inference successful!")
        print()
        print("Note: GitHub API calls would fail with mock token.")
        print("      For real API testing, use AgentCore OAuth.")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Full error:")
        return False


async def test_streaming():
    """Test streaming responses from agent."""
    print("\n" + "="*60)
    print("TEST: Streaming LLM Response")
    print("="*60)
    print()

    try:
        auth = MockGitHubAuth()
        agent = create_github_agent(auth)

        query = "Explain what you can help me with in 2 sentences."
        print(f"📝 Query: '{query}'")
        print()
        print("🤖 Streaming Response:")
        print("-" * 60)

        # Use stream_async for streaming
        stream = agent.stream_async(query)

        full_response = ""
        async for chunk in stream:
            # Extract text from chunk
            if hasattr(chunk, 'text'):
                text = chunk.text
            elif hasattr(chunk, 'content'):
                if isinstance(chunk.content, str):
                    text = chunk.content
                elif isinstance(chunk.content, list):
                    text = ''.join([c.text if hasattr(c, 'text') else str(c)
                                   for c in chunk.content])
                else:
                    text = str(chunk.content)
            else:
                text = str(chunk)

            print(text, end='', flush=True)
            full_response += text

        print()
        print("-" * 60)
        print()
        print("✅ Streaming successful!")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("Full error:")
        return False


async def interactive_mode():
    """Interactive testing mode with LLM."""
    print("\n" + "="*60)
    print("INTERACTIVE MODE (with LLM)")
    print("="*60)
    print("Type 'exit' or 'quit' to stop")
    print("Note: GitHub API calls will fail with mock token")
    print()

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
            print("-" * 60)

            # Stream the response
            stream = agent.stream_async(user_input)
            async for chunk in stream:
                # Extract text from chunk
                if hasattr(chunk, 'text'):
                    text = chunk.text
                elif hasattr(chunk, 'content'):
                    if isinstance(chunk.content, str):
                        text = chunk.content
                    elif isinstance(chunk.content, list):
                        text = ''.join([c.text if hasattr(c, 'text') else str(c)
                                       for c in chunk.content])
                    else:
                        text = str(chunk.content)
                else:
                    text = str(chunk)

                print(text, end='', flush=True)

            print()
            print("-" * 60)

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.exception("Full error:")


async def main():
    """Run AWS integration tests."""
    print("\n" + "="*60)
    print("GitHub Agent AWS Integration Tests")
    print("="*60)
    print("Testing LLM inference with AWS Bedrock")
    print()

    # Check AWS credentials
    import os
    aws_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_profile = os.getenv("AWS_PROFILE")
    aws_region = os.getenv("AWS_DEFAULT_REGION") or os.getenv("AWS_REGION", "ap-southeast-2")

    if not aws_key and not aws_profile:
        print("⚠️  WARNING: AWS credentials not found")
        print()
        print("To test LLM inference, set AWS credentials:")
        print()
        print("Option 1 - AWS SSO (recommended):")
        print("  aws sso login --profile your-profile")
        print("  export AWS_PROFILE=your-profile")
        print()
        print("Option 2 - Direct credentials:")
        print("  export AWS_ACCESS_KEY_ID=your_key")
        print("  export AWS_SECRET_ACCESS_KEY=your_secret")
        print("  export AWS_DEFAULT_REGION=ap-southeast-2")
        print()
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            print("Exiting...")
            return False
    else:
        if aws_profile:
            print(f"✅ AWS credentials found (SSO Profile: {aws_profile})")
        else:
            print(f"✅ AWS credentials found (Direct)")
        print(f"   Region: {aws_region}")
        print()

    # Run tests
    results = []

    # Test 1: LLM Inference
    results.append(await test_llm_inference())

    # Test 2: Streaming
    results.append(await test_streaming())

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print()

    if passed == total:
        print("✅ All AWS integration tests passed!")
    else:
        print(f"⚠️  {total - passed} test(s) failed")
        print()
        print("Common issues:")
        print("  - Invalid AWS credentials")
        print("  - No Bedrock access in region")
        print("  - Missing IAM permissions")

    # Ask for interactive mode
    print("\n" + "="*60)
    user_choice = input("\nRun interactive mode? (y/n): ").strip().lower()
    if user_choice == 'y':
        await interactive_mode()

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
