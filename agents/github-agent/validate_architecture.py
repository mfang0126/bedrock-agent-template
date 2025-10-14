#!/usr/bin/env python3
"""Architecture validation script - tests without calling AWS Bedrock.

This script validates that the refactored architecture works correctly:
- Auth abstraction layer
- Dependency injection
- Tool instantiation
- Agent creation

Does NOT test LLM inference (which requires AWS credentials).
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.agent import create_github_agent
from src.auth import MockGitHubAuth, get_auth_provider
from src.tools.repos import GitHubRepoTools
from src.tools.issues import GitHubIssueTools
from src.tools.pull_requests import GitHubPRTools

print("=" * 60)
print("GitHub Agent Architecture Validation")
print("=" * 60)
print()

# Test 1: Auth Factory
print("✓ TEST 1: Auth Factory")
try:
    auth_local = get_auth_provider("local")
    assert isinstance(auth_local, MockGitHubAuth)
    print("  ✅ Local auth returns MockGitHubAuth")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 2: Mock Auth
print("\n✓ TEST 2: Mock Authentication")
try:
    auth = MockGitHubAuth()
    assert auth.is_authenticated() == True
    import asyncio
    token = asyncio.run(auth.get_token())
    assert token == "ghp_mock_token_for_local_testing"
    print("  ✅ Mock auth returns test token")
    print(f"  ✅ Token: {token[:30]}...")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 3: Tool Classes with Dependency Injection
print("\n✓ TEST 3: Tool Classes (Dependency Injection)")
try:
    auth = MockGitHubAuth()
    repo_tools = GitHubRepoTools(auth)
    issue_tools = GitHubIssueTools(auth)
    pr_tools = GitHubPRTools(auth)

    assert repo_tools.auth == auth
    assert issue_tools.auth == auth
    assert pr_tools.auth == auth

    print("  ✅ GitHubRepoTools instantiated with auth")
    print("  ✅ GitHubIssueTools instantiated with auth")
    print("  ✅ GitHubPRTools instantiated with auth")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 4: Tool Methods Exist
print("\n✓ TEST 4: Tool Methods")
try:
    tool_methods = {
        "repo_tools": ["list_github_repos", "get_repo_info", "create_github_repo"],
        "issue_tools": ["list_github_issues", "create_github_issue", "close_github_issue",
                       "post_github_comment", "update_github_issue"],
        "pr_tools": ["create_pull_request", "list_pull_requests", "merge_pull_request"]
    }

    for tool_class, methods in tool_methods.items():
        for method in methods:
            if tool_class == "repo_tools":
                assert hasattr(repo_tools, method)
            elif tool_class == "issue_tools":
                assert hasattr(issue_tools, method)
            elif tool_class == "pr_tools":
                assert hasattr(pr_tools, method)

    print(f"  ✅ All 11 tool methods exist")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 5: Agent Creation
print("\n✓ TEST 5: Agent Creation (Factory Pattern)")
try:
    auth = MockGitHubAuth()
    agent = create_github_agent(auth)

    # Check agent has tools
    assert len(agent.tool_names) == 11
    print(f"  ✅ Agent created with {len(agent.tool_names)} tools")
    print(f"  ✅ Tools: {', '.join(agent.tool_names[:3])}...")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Test 6: Environment Detection
print("\n✓ TEST 6: Environment Detection")
try:
    import os
    os.environ["AGENT_ENV"] = "local"
    from src.common.config import get_environment

    env = get_environment()
    assert env == "local"
    print(f"  ✅ Environment detected: {env}")
except Exception as e:
    print(f"  ❌ Failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ ALL ARCHITECTURE TESTS PASSED!")
print("=" * 60)
print()
print("Architecture validation complete:")
print("  ✓ Auth abstraction layer working")
print("  ✓ Dependency injection working")
print("  ✓ Tool classes instantiate correctly")
print("  ✓ Agent factory creates agent with all tools")
print("  ✓ Mock authentication functional")
print()
print("Note: LLM inference testing requires AWS credentials")
print("      Use AWS credentials to test actual agent responses")
print()
sys.exit(0)
