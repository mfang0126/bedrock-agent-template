"""
Command execution tools for Coding Agent.

Provides safe command execution with timeout and security validation.
"""

import subprocess
import re
from typing import Optional
from strands.tools import tool


# Dangerous command patterns that should be blocked
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",
    r"sudo\s+",
    r"curl.*\|.*bash",
    r"curl.*\|.*sh",
    r"wget.*\|.*bash",
    r"wget.*\|.*sh",
    r">\s*/dev/",
    r"mkfs",
    r"dd\s+if=",
    r":\(\)\{.*\|.*&.*\};:",  # Fork bomb
    r"chmod.*777",
    r"chown.*root",
]


def is_dangerous_command(command: str) -> bool:
    """
    Check if a command contains dangerous patterns.

    Args:
        command: Command to validate

    Returns:
        True if command is dangerous, False otherwise
    """
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


@tool
async def run_command(command: str, workspace: str, timeout: int = 30) -> str:
    """
    Execute a shell command in the workspace.

    Args:
        command: Shell command to execute
        workspace: Workspace directory to run command in
        timeout: Maximum execution time in seconds (default 30, max 300)

    Returns:
        Command output or error message
    """
    try:
        # Security validation
        if is_dangerous_command(command):
            return f"❌ Dangerous command blocked for security: {command}"

        # Validate timeout
        if timeout < 1 or timeout > 300:
            return "❌ Invalid timeout: must be between 1 and 300 seconds"

        # Validate workspace exists
        import os
        if not os.path.exists(workspace):
            return f"❌ Workspace not found: {workspace}"

        # Execute command
        result = subprocess.run(
            command,
            shell=True,
            cwd=workspace,
            timeout=timeout,
            capture_output=True,
            text=True
        )

        # Format output
        if result.returncode == 0:
            output = f"""✅ Command succeeded

Command: {command}
Exit Code: 0

--- Output ---
{result.stdout}"""
            if result.stderr:
                output += f"\n\n--- Stderr ---\n{result.stderr}"
            return output
        else:
            return f"""❌ Command failed

Command: {command}
Exit Code: {result.returncode}

--- Stderr ---
{result.stderr}

--- Stdout ---
{result.stdout}"""

    except subprocess.TimeoutExpired:
        return f"❌ Command timed out after {timeout} seconds: {command}"
    except Exception as e:
        return f"❌ Error executing command: {str(e)}"


@tool
async def run_test_suite(workspace: str, test_command: Optional[str] = None, timeout: int = 120) -> str:
    """
    Run test suite in the workspace.

    Auto-detects test framework if test_command not provided.

    Args:
        workspace: Workspace directory
        test_command: Test command to run (auto-detected if not provided)
        timeout: Maximum execution time in seconds (default 120)

    Returns:
        Test results or error message
    """
    try:
        import os

        # Validate workspace exists
        if not os.path.exists(workspace):
            return f"❌ Workspace not found: {workspace}"

        # Auto-detect test framework if not specified
        if not test_command:
            if os.path.exists(os.path.join(workspace, "pytest.ini")) or \
               os.path.exists(os.path.join(workspace, "tests")):
                test_command = "pytest -v"
            elif os.path.exists(os.path.join(workspace, "package.json")):
                test_command = "npm test"
            elif os.path.exists(os.path.join(workspace, "pom.xml")):
                test_command = "mvn test"
            elif os.path.exists(os.path.join(workspace, "Gemfile")):
                test_command = "bundle exec rspec"
            else:
                return "❌ Could not auto-detect test framework. Please provide test_command."

        # Run tests using run_command
        result = await run_command(test_command, workspace, timeout)

        # Parse test results
        test_summary = _parse_test_output(result, test_command)

        # Add summary to result
        if test_summary:
            return f"""{test_summary}

{result}"""
        else:
            return result

    except Exception as e:
        return f"❌ Error running tests: {str(e)}"


def _parse_test_output(output: str, test_command: str) -> Optional[str]:
    """
    Parse test output to extract summary.

    Args:
        output: Test command output
        test_command: Test command that was run

    Returns:
        Test summary string or None
    """
    try:
        summary = {}

        # Parse pytest output
        if "pytest" in test_command:
            match = re.search(r'(\d+) passed', output)
            if match:
                summary['passed'] = int(match.group(1))

            match = re.search(r'(\d+) failed', output)
            if match:
                summary['failed'] = int(match.group(1))

            match = re.search(r'(\d+) skipped', output)
            if match:
                summary['skipped'] = int(match.group(1))

            match = re.search(r'in ([\d.]+s)', output)
            if match:
                summary['duration'] = match.group(1)

        # Parse jest/npm test output
        elif "jest" in test_command or "npm test" in test_command:
            match = re.search(r'(\d+) passed', output)
            if match:
                summary['passed'] = int(match.group(1))

            match = re.search(r'(\d+) failed', output)
            if match:
                summary['failed'] = int(match.group(1))

            match = re.search(r'Time:\s+([\d.]+\s*s)', output)
            if match:
                summary['duration'] = match.group(1)

        # Parse mvn test output
        elif "mvn test" in test_command:
            match = re.search(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)', output)
            if match:
                total = int(match.group(1))
                failures = int(match.group(2))
                errors = int(match.group(3))
                summary['passed'] = total - failures - errors - int(match.group(4))
                summary['failed'] = failures + errors
                summary['skipped'] = int(match.group(4))

        # Format summary
        if summary:
            total = summary.get('passed', 0) + summary.get('failed', 0) + summary.get('skipped', 0)
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)
            duration = summary.get('duration', 'unknown')

            status = "✅ All tests passed" if failed == 0 and passed > 0 else f"❌ {failed} test(s) failed"

            return f"""
📊 Test Summary:
{status}
Tests: {passed}/{total} passed
Duration: {duration}
"""

        return None

    except Exception:
        return None
