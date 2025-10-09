"""
Coding Agent - Clean Implementation for AWS Bedrock AgentCore

A comprehensive coding assistant that provides safe code execution, file operations,
workspace management, and test running capabilities using the Strands framework.
"""

import os
import logging
import shutil
import json
from typing import Dict, List, Optional, Any, Generator
from pathlib import Path
from datetime import datetime
import glob

from strands import Agent, tool
from strands.models import BedrockModel

# Import tools
from tools.workspace_manager import WorkspaceManager
from tools.file_operations import FileOperations
from tools.command_executor import CommandExecutor
from tools.test_runner import TestRunner

logger = logging.getLogger(__name__)


@tool
def create_workspace(project_name: str, project_type: str = "python", template_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new coding workspace with project template.

    Args:
        project_name: Name of the project
        project_type: Type of project (python, javascript, java, etc.)
        template_config: Optional template configuration

    Returns:
        Dict containing workspace creation results
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    workspace_manager = WorkspaceManager(workspace_root)

    try:
        # Call with correct parameters: workspace_id, template, config
        result = workspace_manager.create_workspace(
            workspace_id=project_name,
            template=project_type,
            config=template_config or {}
        )
        return {
            "success": True,
            "workspace_path": result["path"],  # Fixed: use 'path' not 'workspace_path'
            "project_type": project_type,
            "files_created": [],
            "message": f"Created {project_type} workspace: {project_name} at {result['path']}"
        }
    except Exception as e:
        logger.error(f"Failed to create workspace {project_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create workspace: {project_name}"
        }


@tool
def setup_workspace(workspace_path: str, dependencies: Optional[Any] = None) -> Dict[str, Any]:
    """Setup workspace by cloning code and running Node install/audit commands.
    
    Args:
        workspace_path: Path to the workspace
        dependencies: Optional configuration dict or command list
        
    Returns:
        Dict containing setup results
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    workspace_manager = WorkspaceManager(workspace_root)

    repo_url: Optional[str] = None
    branch = "main"
    commands: Optional[List[str]] = None

    if isinstance(dependencies, dict):
        repo_url = dependencies.get("repo_url")
        branch = dependencies.get("branch", branch)
        candidate = dependencies.get("commands") or dependencies.get("scripts")
        if isinstance(candidate, list):
            commands = candidate
    elif isinstance(dependencies, list):
        commands = dependencies

    try:
        result = workspace_manager.setup_workspace(
            workspace_path=workspace_path,
            repo_url=repo_url,
            branch=branch,
            commands=commands,
        )
        message = "Workspace setup completed successfully" if result.get("success") else "Workspace setup completed with errors"
        return {
            "success": result.get("success", False),
            "workspace_path": result.get("workspace_path", workspace_path),
            "repo_url": result.get("repo_url"),
            "branch": result.get("branch"),
            "commands_executed": result.get("commands_executed", []),
            "command_results": result.get("command_results", []),
            "message": message
        }
    except Exception as e:
        logger.error(f"Failed to setup workspace {workspace_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "workspace_path": workspace_path,
            "message": f"Failed to setup workspace: {workspace_path}"
        }


@tool
def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """Read file content safely within workspace.
    
    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: utf-8)
        
    Returns:
        Dict containing file content or error
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    file_ops = FileOperations(workspace_root)
    
    try:
        result = file_ops.read_file(file_path, encoding)
        if result.get('success'):
            return {
                "success": True,
                "content": result['content'],
                "file_path": file_path,
                "size": len(result['content']),
                "message": f"Successfully read file: {file_path}"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "message": f"Failed to read file: {file_path}"
            }
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to read file: {file_path}"
        }


@tool
def write_file(file_path: str, content: str, encoding: str = "utf-8", create_dirs: bool = True) -> Dict[str, Any]:
    """Write content to file safely within workspace.
    
    Args:
        file_path: Path to the file to write
        content: Content to write
        encoding: File encoding (default: utf-8)
        create_dirs: Whether to create parent directories
        
    Returns:
        Dict containing write results
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    file_ops = FileOperations(workspace_root)
    
    try:
        result = file_ops.write_file(file_path, content, encoding, create_dirs)
        if result.get('success'):
            return {
                "success": True,
                "file_path": file_path,
                "bytes_written": len(content.encode(encoding)),
                "created_dirs": result.get("created_dirs", []),
                "message": f"Successfully wrote file: {file_path}"
            }
        else:
            return {
                "success": False,
                "error": result.get('error', 'Unknown error'),
                "message": f"Failed to write file: {file_path}"
            }
    except Exception as e:
        logger.error(f"Failed to write file {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to write file: {file_path}"
        }


@tool
def modify_file(file_path: str, search_pattern: str, replacement: str, use_regex: bool = False) -> Dict[str, Any]:
    """Modify file content by replacing patterns.
    
    Args:
        file_path: Path to the file to modify
        search_pattern: Pattern to search for
        replacement: Replacement text
        use_regex: Whether to use regex matching
        
    Returns:
        Dict containing modification results
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    file_ops = FileOperations(workspace_root)
    
    try:
        result = file_ops.modify_file(file_path, search_pattern, replacement, use_regex)
        return {
            "success": True,
            "file_path": file_path,
            "replacements_made": result["replacements_made"],
            "message": f"Made {result['replacements_made']} replacements in {file_path}"
        }
    except Exception as e:
        logger.error(f"Failed to modify file {file_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to modify file: {file_path}"
        }


@tool
def list_files(directory: str = "", pattern: str = "*", recursive: bool = False) -> Dict[str, Any]:
    """List files in directory with optional pattern matching.
    
    Args:
        directory: Directory to list (empty for workspace root)
        pattern: File pattern to match
        recursive: Whether to search recursively
        
    Returns:
        Dict containing file list
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    file_ops = FileOperations(workspace_root)
    
    try:
        files = file_ops.list_files(directory, pattern, recursive)
        return {
            "success": True,
            "directory": directory or "workspace",
            "files": files,
            "count": len(files),
            "message": f"Found {len(files)} files in {directory or 'workspace'}"
        }
    except Exception as e:
        logger.error(f"Failed to list files in {directory}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to list files in directory: {directory}"
        }


@tool
def execute_command(command: str, timeout: int = 30, capture_output: bool = True) -> Dict[str, Any]:
    """Execute command safely within workspace.
    
    Args:
        command: Command to execute
        timeout: Timeout in seconds
        capture_output: Whether to capture command output
        
    Returns:
        Dict containing command execution results
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    command_executor = CommandExecutor(workspace_root)
    
    try:
        result = command_executor.execute_command(command, timeout=timeout, capture_output=capture_output)
        return {
            "success": result.get("success", False),
            "command": command,
            "exit_code": result.get("exit_code", 0),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "duration": result.get("duration", 0),
            "message": f"Command executed: {command}"
        }
    except Exception as e:
        logger.error(f"Failed to execute command {command}: {e}")
        return {
            "success": False,
            "error": str(e),
            "command": command,
            "message": f"Failed to execute command: {command}"
        }


@tool
def execute_script(script_content: str, script_type: str = "python", timeout: int = 300) -> Dict[str, Any]:
    """Execute script content safely within workspace.
    
    Args:
        script_content: Script content to execute
        script_type: Type of script (python, bash, etc.)
        timeout: Timeout in seconds
        
    Returns:
        Dict containing script execution results
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    command_executor = CommandExecutor(workspace_root)
    
    try:
        result = command_executor.execute_script(script_content, script_type, timeout)
        return {
            "success": result.get("success", False),
            "script_type": script_type,
            "exit_code": result.get("exit_code", 0),
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "duration": result.get("duration", 0),
            "script_path": result.get("script_path", ""),
            "message": f"Executed {script_type} script"
        }
    except Exception as e:
        logger.error(f"Failed to execute {script_type} script: {e}")
        return {
            "success": False,
            "error": str(e),
            "script_type": script_type,
            "message": f"Failed to execute {script_type} script"
        }


@tool
def run_tests(test_path: str = ".", framework: Optional[str] = None, timeout: int = 300, verbose: bool = True) -> Dict[str, Any]:
    """Run tests with framework detection and result parsing.
    
    Args:
        test_path: Path to test files or directory
        framework: Optional framework override
        timeout: Test execution timeout
        verbose: Whether to include verbose output
        
    Returns:
        Dict containing test results
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    test_runner = TestRunner(workspace_root)
    
    try:
        result = test_runner.run_tests(framework, test_path, timeout, verbose)
        return {
            "success": result.get("success", False),
            "test_path": test_path,
            "framework": result.get("framework", "unknown"),
            "test_suite": result.get("test_suite", {}),
            "command": result.get("command", ""),
            "duration": result.get("duration", 0),
            "raw_output": result.get("raw_output", ""),
            "error_output": result.get("error_output", ""),
            "message": f"Tests completed for: {test_path}"
        }
    except Exception as e:
        logger.error(f"Failed to run tests for {test_path}: {e}")
        return {
            "success": False,
            "error": str(e),
            "test_path": test_path,
            "message": f"Failed to run tests: {test_path}"
        }


@tool
def detect_test_frameworks(directory: str = "") -> Dict[str, Any]:
    """Detect available testing frameworks in the workspace.

    Args:
        directory: Directory to scan (empty for workspace root)

    Returns:
        Dict containing detected frameworks
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    test_runner = TestRunner(workspace_root)

    try:
        frameworks = test_runner.detect_frameworks(directory)
        return {
            "success": True,
            "directory": directory or "workspace",
            "frameworks": frameworks,
            "count": len(frameworks),
            "message": f"Detected {len(frameworks)} testing frameworks"
        }
    except Exception as e:
        logger.error(f"Failed to detect frameworks in {directory}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to detect frameworks in directory: {directory}"
        }


@tool
def archive_session_work(session_id: Optional[str] = None, cleanup_temp: bool = True) -> Dict[str, Any]:
    """Archive current session work with progress streaming.

    This tool archives all files in the workspace (except .archive and .git) to a session archive,
    cleans up temporary files, and verifies workspace is clean for the next session.

    Args:
        session_id: Optional custom session identifier (auto-generated if not provided)
        cleanup_temp: Whether to clean temporary files after archiving

    Returns:
        Dict containing archive results with session_id, files_archived count, and archive location
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')

    # Generate session_id if not provided
    if not session_id:
        session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")

    # Archive directory setup
    archive_root = os.path.join(workspace_root, '.archive')
    archive_path = os.path.join(archive_root, session_id)

    try:
        # Create archive directory
        os.makedirs(archive_path, exist_ok=True)

        # Identify files to archive (exclude .archive and .git)
        session_files = []
        for root, dirs, files in os.walk(workspace_root):
            # Skip .archive and .git directories
            dirs[:] = [d for d in dirs if d not in {'.archive', '.git', 'node_modules'}]

            for file in files:
                file_path = os.path.join(root, file)
                session_files.append(file_path)

        # Archive files preserving directory structure
        archived_count = 0
        for file_path in session_files:
            rel_path = os.path.relpath(file_path, workspace_root)
            dest_path = os.path.join(archive_path, rel_path)

            # Create parent directories
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Copy file
            shutil.copy2(file_path, dest_path)
            archived_count += 1

        # Clean temporary files if requested
        temp_files_removed = 0
        if cleanup_temp:
            temp_patterns = [
                '**/*.tmp', '**/*.temp', '**/*.log',
                '**/__pycache__', '**/*.pyc', '**/.pytest_cache',
                '**/.DS_Store', '**/.cache'
            ]

            for pattern in temp_patterns:
                for temp_file in glob.glob(os.path.join(workspace_root, pattern), recursive=True):
                    if '.archive' not in temp_file and '.git' not in temp_file:
                        if os.path.isfile(temp_file):
                            os.remove(temp_file)
                            temp_files_removed += 1
                        elif os.path.isdir(temp_file):
                            shutil.rmtree(temp_file)
                            temp_files_removed += 1

        # Create session summary
        summary = {
            "session_id": session_id,
            "archived_at": datetime.now().isoformat(),
            "files_archived": archived_count,
            "temp_files_removed": temp_files_removed,
            "archive_location": archive_path,
            "workspace_state": "clean"
        }

        summary_path = os.path.join(archive_path, 'session_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        # Verify workspace is clean
        remaining_files = []
        for root, dirs, files in os.walk(workspace_root):
            dirs[:] = [d for d in dirs if d not in {'.archive', '.git', 'node_modules'}]
            remaining_files.extend(files)

        workspace_clean = len(remaining_files) == 0

        return {
            "success": True,
            "session_id": session_id,
            "files_archived": archived_count,
            "temp_files_removed": temp_files_removed,
            "archive_location": archive_path,
            "workspace_clean": workspace_clean,
            "message": f"Session {session_id} archived successfully. Workspace {'is clean' if workspace_clean else 'has remaining files'}."
        }

    except Exception as e:
        logger.error(f"Failed to archive session {session_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "message": f"Failed to archive session: {session_id}"
        }


@tool
def list_archived_sessions() -> Dict[str, Any]:
    """List all archived sessions with metadata.

    Returns:
        Dict containing list of archived sessions with their metadata
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    archive_root = os.path.join(workspace_root, '.archive')

    try:
        if not os.path.exists(archive_root):
            return {
                "success": True,
                "sessions": [],
                "total_sessions": 0,
                "message": "No archived sessions found"
            }

        sessions = []
        for session_dir in os.listdir(archive_root):
            session_path = os.path.join(archive_root, session_dir)
            if not os.path.isdir(session_path):
                continue

            summary_path = os.path.join(session_path, 'session_summary.json')
            if os.path.exists(summary_path):
                with open(summary_path, 'r') as f:
                    summary = json.load(f)
                    sessions.append(summary)
            else:
                # Session without summary - create minimal info
                sessions.append({
                    "session_id": session_dir,
                    "archive_location": session_path,
                    "archived_at": "Unknown"
                })

        # Sort by archived_at (newest first)
        sessions.sort(key=lambda x: x.get('archived_at', ''), reverse=True)

        return {
            "success": True,
            "sessions": sessions,
            "total_sessions": len(sessions),
            "message": f"Found {len(sessions)} archived sessions"
        }

    except Exception as e:
        logger.error(f"Failed to list archived sessions: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to list archived sessions"
        }


@tool
def restore_session(session_id: str) -> Dict[str, Any]:
    """Restore files from an archived session.

    Args:
        session_id: The session identifier to restore

    Returns:
        Dict containing restore results with files_restored list and count
    """
    workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    archive_root = os.path.join(workspace_root, '.archive')
    archive_path = os.path.join(archive_root, session_id)

    try:
        if not os.path.exists(archive_path):
            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "message": f"Session {session_id} does not exist in archive"
            }

        # Get list of files to restore
        files_to_restore = []
        for root, dirs, files in os.walk(archive_path):
            for file in files:
                if file == 'session_summary.json':
                    continue
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, archive_path)
                files_to_restore.append(rel_path)

        # Restore files
        restored_count = 0
        for rel_path in files_to_restore:
            src_path = os.path.join(archive_path, rel_path)
            dest_path = os.path.join(workspace_root, rel_path)

            # Create parent directories
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)

            # Copy file
            shutil.copy2(src_path, dest_path)
            restored_count += 1

        return {
            "success": True,
            "session_id": session_id,
            "files_restored": files_to_restore,
            "total_restored": restored_count,
            "message": f"Restored {restored_count} files from session {session_id}"
        }

    except Exception as e:
        logger.error(f"Failed to restore session {session_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "message": f"Failed to restore session: {session_id}"
        }


def create_coding_agent(workspace_root: Optional[str] = None) -> Agent:
    """Create a coding agent with Strands framework.
    
    Args:
        workspace_root: Root directory for workspaces
        
    Returns:
        Configured Strands Agent
    """
    # Model configuration
    model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    region = "ap-southeast-2"  # Sydney
    
    # Create Bedrock model
    try:
        model = BedrockModel(model_id=model_id, region_name=region)
    except Exception as e:
        logger.warning(f"Could not initialize Bedrock model: {e}")
        model = None
    
    # Initialize workspace root
    if workspace_root is None:
        workspace_root = os.getenv('WORKSPACE_ROOT', '/tmp/coding_workspace')
    Path(workspace_root).mkdir(parents=True, exist_ok=True)
    
    # System prompt
    system_prompt = """You are an expert coding assistant that helps users with software development tasks.

You have access to comprehensive tools for:
- Creating and managing coding workspaces with project templates
- Reading, writing, and modifying files safely within workspace boundaries
- Executing commands and scripts with security controls and timeout protection
- Running tests with automatic framework detection and result parsing
- Listing and organizing files with pattern matching
- Session archiving and workspace cleanup for organized development

When users ask for coding help, follow these best practices:
1. Create or setup appropriate workspaces for their projects
2. Read existing code to understand the context and requirements
3. Write clean, well-documented code following best practices
4. Execute commands to build, install dependencies, or run programs
5. Run comprehensive tests to validate code functionality
6. Provide clear explanations of what you're doing and why

Workspace Management Best Practices:
- At the end of each session, use archive_session_work() to archive completed work
- This keeps the workspace clean and organized for the next session
- All session work is preserved in .archive/ directory with timestamps
- Use list_archived_sessions() to see previous work
- Use restore_session() to recover files from previous sessions if needed

Always prioritize security by working within designated workspace boundaries.
Use appropriate timeouts for long-running operations.
Provide detailed feedback on command execution and test results.
Stream progress updates for long-running operations so users can see what's happening."""

    # Create agent with all coding tools
    agent = Agent(
        model=model,
        tools=[
            create_workspace,
            setup_workspace,
            read_file,
            write_file,
            modify_file,
            list_files,
            execute_command,
            execute_script,
            run_tests,
            detect_test_frameworks,
            archive_session_work,
            list_archived_sessions,
            restore_session,
        ],
        system_prompt=system_prompt,
    )

    return agent
