"""
File operation tools for Coding Agent.

Provides safe file read/write/modify operations with security validation.
"""

import os
from typing import Optional
from strands.tools import tool
from src.tools.coding.workspace import is_within_workspace


MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@tool
async def read_file(file_path: str, workspace: str) -> str:
    """
    Read a file from the workspace.

    Args:
        file_path: Relative path to file within workspace
        workspace: Workspace root path

    Returns:
        File contents or error message
    """
    try:
        # Validate path is within workspace
        if not is_within_workspace(file_path, workspace):
            return f"❌ Security error: Path outside workspace: {file_path}"

        # Build full path
        full_path = os.path.join(workspace, file_path)

        # Check if file exists
        if not os.path.exists(full_path):
            return f"❌ File not found: {file_path}"

        # Check if it's a file (not directory)
        if not os.path.isfile(full_path):
            return f"❌ Not a file: {file_path}"

        # Check file size
        file_size = os.path.getsize(full_path)
        if file_size > MAX_FILE_SIZE:
            return f"❌ File too large: {file_size} bytes (max {MAX_FILE_SIZE} bytes)"

        # Read file
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return f"""✅ File read successfully: {file_path}

{content}"""

    except UnicodeDecodeError:
        return f"❌ Cannot read file: {file_path} (binary file or encoding error)"
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"


@tool
async def write_file(file_path: str, content: str, workspace: str) -> str:
    """
    Write content to a file in the workspace.

    Creates parent directories if needed. Overwrites existing file.

    Args:
        file_path: Relative path to file within workspace
        content: Content to write
        workspace: Workspace root path

    Returns:
        Success or error message
    """
    try:
        # Validate path is within workspace
        if not is_within_workspace(file_path, workspace):
            return f"❌ Security error: Path outside workspace: {file_path}"

        # Validate content size
        if len(content) > MAX_FILE_SIZE:
            return f"❌ Content too large: {len(content)} bytes (max {MAX_FILE_SIZE} bytes)"

        # Build full path
        full_path = os.path.join(workspace, file_path)

        # Create parent directories
        parent_dir = os.path.dirname(full_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"✅ File written successfully: {file_path} ({len(content)} bytes)"

    except Exception as e:
        return f"❌ Error writing file: {str(e)}"


@tool
async def modify_file(file_path: str, old_content: str, new_content: str, workspace: str) -> str:
    """
    Modify a file by replacing old_content with new_content.

    Args:
        file_path: Relative path to file within workspace
        old_content: Content to find and replace
        new_content: Content to replace with
        workspace: Workspace root path

    Returns:
        Success or error message
    """
    try:
        # Validate path is within workspace
        if not is_within_workspace(file_path, workspace):
            return f"❌ Security error: Path outside workspace: {file_path}"

        # Build full path
        full_path = os.path.join(workspace, file_path)

        # Check if file exists
        if not os.path.exists(full_path):
            return f"❌ File not found: {file_path}"

        # Read existing content
        with open(full_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()

        # Check if old_content exists in file
        if old_content not in existing_content:
            return f"❌ Content to replace not found in file: {file_path}"

        # Replace content
        modified_content = existing_content.replace(old_content, new_content)

        # Validate size
        if len(modified_content) > MAX_FILE_SIZE:
            return f"❌ Modified content too large: {len(modified_content)} bytes"

        # Write modified content
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)

        # Count replacements
        replacements = existing_content.count(old_content)

        return f"✅ File modified successfully: {file_path} ({replacements} replacement(s))"

    except UnicodeDecodeError:
        return f"❌ Cannot modify file: {file_path} (binary file or encoding error)"
    except Exception as e:
        return f"❌ Error modifying file: {str(e)}"


@tool
async def list_files(directory: str, workspace: str) -> str:
    """
    List files and directories in a workspace directory.

    Args:
        directory: Relative path to directory within workspace (use "." for root)
        workspace: Workspace root path

    Returns:
        List of files and directories or error message
    """
    try:
        # Validate path is within workspace
        if not is_within_workspace(directory, workspace):
            return f"❌ Security error: Path outside workspace: {directory}"

        # Build full path
        full_path = os.path.join(workspace, directory) if directory != "." else workspace

        # Check if directory exists
        if not os.path.exists(full_path):
            return f"❌ Directory not found: {directory}"

        # Check if it's a directory
        if not os.path.isdir(full_path):
            return f"❌ Not a directory: {directory}"

        # List contents
        items = []
        for item in sorted(os.listdir(full_path)):
            item_path = os.path.join(full_path, item)
            if os.path.isdir(item_path):
                items.append(f"📁 {item}/")
            else:
                size = os.path.getsize(item_path)
                items.append(f"📄 {item} ({size} bytes)")

        if not items:
            return f"📂 Directory is empty: {directory}"

        return f"""📂 Directory listing: {directory}

{chr(10).join(items)}"""

    except Exception as e:
        return f"❌ Error listing directory: {str(e)}"
