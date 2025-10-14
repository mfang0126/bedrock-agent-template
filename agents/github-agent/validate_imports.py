#!/usr/bin/env python3
"""
Validate imports before Docker build.

This script validates that all imports work correctly before building
the Docker image, preventing deployment of broken code.
"""
import sys
import traceback


def test_imports():
    """Test all critical imports for the GitHub agent."""
    print("🔍 Validating GitHub Agent imports...")
    print()

    errors = []

    # Test auth imports
    try:
        from src.auth.interface import GitHubAuth
        from src.auth.mock import MockGitHubAuth
        print("✅ Auth Protocol imports OK")
    except ImportError as e:
        errors.append(f"❌ Auth imports failed: {e}")
        traceback.print_exc()

    # Test tool factory imports
    try:
        from src.tools.repos import github_repo_tools
        from src.tools.issues import github_issue_tools
        from src.tools.pull_requests import github_pr_tools
        print("✅ Tool factory imports OK")
    except ImportError as e:
        errors.append(f"❌ Tool imports failed: {e}")
        traceback.print_exc()

    # Test agent import
    try:
        from src.agent import create_github_agent
        print("✅ Agent factory import OK")
    except ImportError as e:
        errors.append(f"❌ Agent import failed: {e}")
        traceback.print_exc()

    # Test runtime import
    try:
        import src.runtime
        print("✅ Runtime module import OK")
    except ImportError as e:
        errors.append(f"❌ Runtime import failed: {e}")
        traceback.print_exc()

    print()

    if errors:
        print("=" * 60)
        print("❌ IMPORT VALIDATION FAILED")
        print("=" * 60)
        for error in errors:
            print(f"  {error}")
        print()
        print("Fix these imports before building Docker image!")
        return False
    else:
        print("=" * 60)
        print("✅ ALL IMPORTS VALIDATED SUCCESSFULLY")
        print("=" * 60)
        print()
        print("Ready for Docker build!")
        return True


if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
