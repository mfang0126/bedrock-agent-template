#!/usr/bin/env python3
"""Test GitHub agent invocation locally without agentcore CLI"""

import asyncio
from src.agent import create_github_agent
from src.auth import get_auth_provider


async def test_agent():
    """Test agent with various queries."""
    print("\n" + "="*70)
    print("GITHUB AGENT LOCAL INVOCATION TEST")
    print("="*70)
    print()

    # Create agent with mock auth
    print("🔧 Creating agent with mock authentication...")
    auth = get_auth_provider(env="local")
    agent = create_github_agent(auth)
    print("✅ Agent created successfully!")
    print()

    # Test queries
    test_queries = [
        "What can you help me with?",
        "What tools do you have available?",
        "List my GitHub repositories",
        "How do I create an issue?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(test_queries)}")
        print('='*70)
        print(f"📝 Query: {query}")
        print('='*70)

        try:
            # Invoke agent
            print("\n🤖 Agent Response:")
            print("-" * 70)

            # Try different invocation methods
            if hasattr(agent, 'run'):
                response = agent.run(query)
            elif hasattr(agent, '__call__'):
                response = agent(query)
            elif hasattr(agent, 'invoke_async'):
                response = await agent.invoke_async(query)
            else:
                response = "⚠️  Agent doesn't have expected invocation methods"

            print(response)
            print("-" * 70)
            print()

            # Wait a bit between queries
            if i < len(test_queries):
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            print()

    print("\n" + "="*70)
    print("✅ TEST COMPLETED")
    print("="*70)
    print()
    print("Notes:")
    print("  • Mock authentication was used (no real GitHub API calls)")
    print("  • To test with real GitHub API, use AGENT_ENV=dev")
    print("  • See LOCAL_INVOCATION_GUIDE.md for more options")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(test_agent())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
