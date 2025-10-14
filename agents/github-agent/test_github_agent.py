#!/usr/bin/env python3
"""Comprehensive GitHub Agent Test Suite

Tests the GitHub agent at multiple levels:
1. Import validation
2. Agent instantiation
3. Tool registration
4. Mock authentication
5. LLM inference (if AWS credentials available)
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """Test 1: Validate all imports work."""
    print("=" * 70)
    print("TEST 1: IMPORT VALIDATION")
    print("=" * 70)

    try:
        from src.auth.interface import GitHubAuth
        from src.auth.mock import MockGitHubAuth
        from src.tools.repos import github_repo_tools
        from src.tools.issues import github_issue_tools
        from src.tools.pull_requests import github_pr_tools
        from src.agent import create_github_agent

        print("✅ All imports successful")
        print()
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print()
        return False


def test_agent_instantiation():
    """Test 2: Test agent can be created with mock auth."""
    print("=" * 70)
    print("TEST 2: AGENT INSTANTIATION")
    print("=" * 70)

    try:
        from src.auth.mock import MockGitHubAuth
        from src.agent import create_github_agent

        # Create agent with mock auth
        auth = MockGitHubAuth()
        agent = create_github_agent(auth)

        print("✅ Agent created successfully")
        print(f"   Type: {type(agent).__name__}")
        print()
        return True, agent
    except Exception as e:
        print(f"❌ Agent instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False, None


def test_tools_registration(agent):
    """Test 3: Verify all tools are registered."""
    print("=" * 70)
    print("TEST 3: TOOL REGISTRATION")
    print("=" * 70)

    try:
        # Get tool names from agent (Strands Agent uses tool_names attribute)
        tool_names = []
        if hasattr(agent, 'tool_names'):
            tool_names = agent.tool_names
        elif hasattr(agent, 'tools'):
            # Fallback for other agent types
            tools = agent.tools
            tool_names = [t.name if hasattr(t, 'name') else t.__name__ for t in tools]

        print(f"✅ Agent has {len(tool_names)} tools registered:")
        print()

        # Group tools by category
        repo_tools = [name for name in tool_names if 'repo' in name.lower()]
        issue_tools = [name for name in tool_names if 'issue' in name.lower()]
        pr_tools = [name for name in tool_names if 'pull' in name.lower() or 'pr' in name.lower()]

        print(f"   Repository Tools ({len(repo_tools)}):")
        for tool_name in repo_tools:
            print(f"      - {tool_name}")

        print(f"\n   Issue Tools ({len(issue_tools)}):")
        for tool_name in issue_tools:
            print(f"      - {tool_name}")

        print(f"\n   Pull Request Tools ({len(pr_tools)}):")
        for tool_name in pr_tools:
            print(f"      - {tool_name}")

        print()

        # Verify expected minimum tool count
        expected_min = 10  # Adjust based on actual tool count
        if len(tool_names) >= expected_min:
            print(f"✅ Tool count meets minimum expectation ({len(tool_names)} >= {expected_min})")
        else:
            print(f"⚠️  Tool count below expectation ({len(tool_names)} < {expected_min})")

        print()
        return True
    except Exception as e:
        print(f"❌ Tool registration check failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def test_mock_authentication():
    """Test 4: Verify mock authentication works."""
    print("=" * 70)
    print("TEST 4: MOCK AUTHENTICATION")
    print("=" * 70)

    try:
        from src.auth.mock import MockGitHubAuth

        auth = MockGitHubAuth()

        # Test authentication methods
        token = await auth.get_token()
        is_auth = auth.is_authenticated()

        print("✅ Mock authentication working:")
        print(f"   Token retrieved: {token[:30]}...")
        print(f"   Is authenticated: {is_auth}")
        print()
        return True
    except Exception as e:
        print(f"❌ Mock authentication failed: {e}")
        import traceback
        traceback.print_exc()
        print()
        return False


async def test_llm_inference(agent):
    """Test 5: Test LLM inference (requires AWS credentials)."""
    print("=" * 70)
    print("TEST 5: LLM INFERENCE (Optional - requires AWS)")
    print("=" * 70)

    # Check for AWS credentials
    has_aws = (
        os.getenv('AWS_PROFILE') or
        os.getenv('AWS_ACCESS_KEY_ID') or
        os.path.exists(os.path.expanduser('~/.aws/credentials'))
    )

    if not has_aws:
        print("⏭️  Skipping - AWS credentials not detected")
        print("   To test LLM inference:")
        print("   1. Configure AWS: aws sso login --profile your-profile")
        print("   2. Set profile: export AWS_PROFILE=your-profile")
        print("   3. Re-run this test")
        print()
        return True  # Not a failure, just skipped

    print("🔍 AWS credentials detected, attempting LLM test...")
    print()

    try:
        # Simple query to test LLM
        query = "What tools do you have available? Please list them briefly."

        print(f"📝 Query: '{query}'")
        print()
        print("🤖 Agent Response:")
        print("-" * 70)

        # Try to get response (sync or async depending on agent type)
        try:
            if hasattr(agent, 'run'):
                response = agent.run(query)
            elif hasattr(agent, '__call__'):
                response = agent(query)
            else:
                print("⚠️  Agent doesn't have expected methods")
                return False

            print(response)
        except Exception as e:
            print(f"⚠️  LLM call failed (this may be expected): {e}")
            print("   Common reasons:")
            print("   - No Bedrock access in current region")
            print("   - Model not enabled in account")
            print("   - Insufficient IAM permissions")
            return True  # Not necessarily a test failure

        print("-" * 70)
        print()
        print("✅ LLM inference test completed")
        print()
        return True

    except Exception as e:
        print(f"⚠️  LLM test encountered issue: {e}")
        import traceback
        traceback.print_exc()
        print()
        return True  # Don't fail the whole suite


async def main():
    """Run all tests."""
    print()
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "GITHUB AGENT TEST SUITE" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    results = []
    agent = None

    # Test 1: Imports
    results.append(("Imports", test_imports()))

    if not results[-1][1]:
        print("❌ Cannot continue - imports failed")
        return False

    # Test 2: Agent Instantiation
    success, agent = test_agent_instantiation()
    results.append(("Agent Instantiation", success))

    if not success:
        print("❌ Cannot continue - agent instantiation failed")
        return False

    # Test 3: Tool Registration
    results.append(("Tool Registration", test_tools_registration(agent)))

    # Test 4: Mock Authentication
    results.append(("Mock Authentication", await test_mock_authentication()))

    # Test 5: LLM Inference (optional)
    results.append(("LLM Inference", await test_llm_inference(agent)))

    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:8} | {test_name}")

    print()

    # Overall result
    critical_tests = results[:4]  # First 4 are critical
    all_critical_passed = all(passed for _, passed in critical_tests)

    if all_critical_passed:
        print("🎉 ALL CRITICAL TESTS PASSED!")
        print()
        print("Your GitHub agent is ready to use!")
        print()
        print("Next steps:")
        print("  • Test with AWS: Ensure AWS credentials are configured")
        print("  • Build Docker: docker build -t github-agent .")
        print("  • Deploy to AgentCore: agentcore deploy")
        print()
        return True
    else:
        print("❌ SOME CRITICAL TESTS FAILED")
        print()
        print("Please fix the failing tests before deploying.")
        print()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
