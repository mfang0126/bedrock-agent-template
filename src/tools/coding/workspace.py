"""
Workspace management tools for Coding Agent.

Provides isolated workspace creation and cleanup for safe code execution.
"""

import os
import shutil
import uuid
from typing import Dict
from strands.tools import tool


WORKSPACE_BASE = "/tmp/coding_workspaces"


@tool
async def setup_coding_workspace(repo_path: str = None) -> str:
    """
    Set up an isolated workspace for code execution.

    Creates a unique workspace directory and optionally copies a repository into it.

    Args:
        repo_path: Optional path to repository to copy into workspace

    Returns:
        JSON string with workspace_id and workspace_path
    """
    try:
        # Create unique workspace
        workspace_id = str(uuid.uuid4())
        workspace_path = os.path.join(WORKSPACE_BASE, workspace_id)

        # Create base directory if it doesn't exist
        os.makedirs(WORKSPACE_BASE, exist_ok=True)

        # Create workspace directory
        os.makedirs(workspace_path, exist_ok=True)

        # Copy repo if provided
        if repo_path:
            if not os.path.exists(repo_path):
                shutil.rmtree(workspace_path)
                return f"❌ Repository path does not exist: {repo_path}"

            # Copy repository contents to workspace
            repo_dest = os.path.join(workspace_path, "repo")
            shutil.copytree(repo_path, repo_dest)
            workspace_path = repo_dest

        # Set permissions
        os.chmod(workspace_path, 0o755)

        return f"""✅ Workspace created successfully

Workspace ID: {workspace_id}
Workspace Path: {workspace_path}

The workspace is isolated and ready for code execution."""

    except Exception as e:
        return f"❌ Failed to create workspace: {str(e)}"


@tool
async def cleanup_coding_workspace(workspace_path: str) -> str:
    """
    Clean up a workspace after code execution.

    Removes the workspace directory and all its contents.

    Args:
        workspace_path: Path to the workspace to clean up

    Returns:
        Success or error message
    """
    try:
        # Validate workspace path is within our base directory
        abs_workspace = os.path.abspath(workspace_path)
        abs_base = os.path.abspath(WORKSPACE_BASE)

        if not abs_workspace.startswith(abs_base):
            return f"❌ Invalid workspace path: must be within {WORKSPACE_BASE}"

        # Check if workspace exists
        if not os.path.exists(workspace_path):
            return f"⚠️ Workspace does not exist: {workspace_path}"

        # Remove workspace
        shutil.rmtree(workspace_path)

        return f"✅ Workspace cleaned up successfully: {workspace_path}"

    except Exception as e:
        return f"⚠️ Cleanup warning: {str(e)}"


def is_within_workspace(file_path: str, workspace: str) -> bool:
    """
    Validate that a file path is within the workspace (security check).

    Args:
        file_path: Path to validate
        workspace: Workspace root path

    Returns:
        True if path is within workspace, False otherwise
    """
    try:
        # Get absolute paths
        abs_file = os.path.abspath(os.path.join(workspace, file_path))
        abs_workspace = os.path.abspath(workspace)

        # Check if file path starts with workspace path
        return abs_file.startswith(abs_workspace)
    except Exception:
        return False
