#!/usr/bin/env python3
"""Validate all critical imports before Docker build.

This script tests that all critical imports can be resolved,
catching import errors before expensive Docker builds.

Usage:
    ./validate_imports.py

Exit codes:
    0: All imports successful
    1: One or more imports failed
"""

import sys
from typing import List, Tuple


def test_import(module_path: str, description: str) -> Tuple[bool, str]:
    """Test a single import.

    Args:
        module_path: Module import path (e.g., 'src.auth.interface')
        description: Human-readable description

    Returns:
        Tuple of (success, message)
    """
    try:
        __import__(module_path)
        return True, f"✅ {description}"
    except ImportError as e:
        return False, f"❌ {description}: {e}"
    except Exception as e:
        return False, f"❌ {description}: Unexpected error: {e}"


def main() -> int:
    """Run all import validations.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 60)
    print("JIRA AGENT - Import Validation")
    print("=" * 60)
    print()

    # List of critical imports to test
    tests: List[Tuple[str, str]] = [
        # Auth module
        ("src.auth.interface", "Auth Protocol interface"),
        ("src.auth.mock", "Mock auth implementation"),
        ("src.auth", "Auth factory"),

        # Tools module
        ("src.tools.tickets", "Ticket tools"),
        ("src.tools.updates", "Update tools"),

        # Common module
        ("src.common.config", "Configuration"),
        ("src.common.utils", "Utilities"),

        # Agent module
        ("src.agent", "Agent factory"),

        # Runtime module
        ("src.runtime", "AgentCore runtime"),
    ]

    errors: List[str] = []
    successes: List[str] = []

    # Run all tests
    for module_path, description in tests:
        success, message = test_import(module_path, description)
        if success:
            successes.append(message)
        else:
            errors.append(message)

    # Print results
    print("Results:")
    print("-" * 60)
    for msg in successes:
        print(msg)
    for msg in errors:
        print(msg)

    print()
    print("=" * 60)

    if errors:
        print(f"❌ VALIDATION FAILED: {len(errors)} import(s) failed")
        print("=" * 60)
        return 1
    else:
        print(f"✅ ALL IMPORTS VALIDATED: {len(successes)} import(s) successful")
        print("=" * 60)
        return 0


if __name__ == "__main__":
    sys.exit(main())
