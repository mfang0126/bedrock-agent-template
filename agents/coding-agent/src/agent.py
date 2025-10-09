"""
Coding Agent - Clean Implementation for AWS Bedrock AgentCore

A comprehensive coding assistant that provides safe code execution, file operations,
workspace management, and test running capabilities using the Strands framework.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from strands import Agent
from strands.models import BedrockModel

# Import tools
from .tools.coding.workspace_manager import WorkspaceManager
from .tools.coding.file_operations import FileOperations
from .tools.coding.command_executor import CommandExecutor
from .tools.coding.test_runner import TestRunner

logger = logging.getLogger(__name__)


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
        result = workspace_manager.create_workspace(project_name, project_type, template_config or {})
        return {
            "success": True,
            "workspace_path": result["workspace_path"],
            "project_type": project_type,
            "files_created": result.get("files_created", []),
            "message": f"Created {project_type} workspace: {project_name}"
        }
    except Exception as e:
        logger.error(f"Failed to create workspace {project_name}: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to create workspace: {project_name}"
        }


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

When users ask for coding help, follow these best practices:
1. Create or setup appropriate workspaces for their projects
2. Read existing code to understand the context and requirements
3. Write clean, well-documented code following best practices
4. Execute commands to build, install dependencies, or run programs
5. Run comprehensive tests to validate code functionality
6. Provide clear explanations of what you're doing and why

Always prioritize security by working within designated workspace boundaries.
Use appropriate timeouts for long-running operations.
Provide detailed feedback on command execution and test results."""

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
        ],
        system_prompt=system_prompt,
    )
    
    return agent
