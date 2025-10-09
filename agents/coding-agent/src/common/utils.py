"""Common utilities for coding agent response handling and standardization."""

import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CodingResponse:
    """Standardized coding agent response structure."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


def format_coding_response(
    operation: str,
    result_data: Dict[str, Any],
    success: bool = True,
    error_message: str = None
) -> CodingResponse:
    """
    Format coding agent responses into standardized structure.
    
    Args:
        operation: Coding operation performed (read_file, write_file, execute_command, etc.)
        result_data: Result data from the operation
        success: Whether the operation was successful
        error_message: Error message if operation failed
    
    Returns:
        Formatted CodingResponse
    """
    if not success and error_message:
        return CodingResponse(
            success=False,
            message=f"Error in {operation}: {error_message}",
            data={"operation": operation, "error": error_message}
        )
    
    # Generate contextual messages based on operation
    messages = {
        "create_workspace": f"Created workspace: {result_data.get('workspace_path', 'Unknown')}",
        "setup_workspace": f"Ran {len(result_data.get('commands_executed', []))} setup commands",
        "read_file": f"Read file: {result_data.get('file_path', 'Unknown')} ({result_data.get('size', 0)} bytes)",
        "write_file": f"Wrote file: {result_data.get('file_path', 'Unknown')} ({result_data.get('bytes_written', 0)} bytes)",
        "modify_file": f"Modified file: {result_data.get('file_path', 'Unknown')} ({result_data.get('replacements_made', 0)} changes)",
        "list_files": f"Listed {result_data.get('count', 0)} files in {result_data.get('directory', 'workspace')}",
        "execute_command": f"Executed command: {result_data.get('command', 'Unknown')} (exit code: {result_data.get('exit_code', 0)})",
        "execute_script": f"Executed {result_data.get('script_type', 'unknown')} script (exit code: {result_data.get('exit_code', 0)})",
        "run_tests": f"Ran tests using {result_data.get('framework', 'unknown')} framework",
        "detect_frameworks": f"Detected {result_data.get('count', 0)} testing frameworks"
    }
    
    message = messages.get(operation, f"Completed {operation} operation")
    
    return CodingResponse(
        success=success,
        message=message,
        data={
            "operation": operation,
            "result": result_data
        }
    )


def create_error_response(error_message: str, operation: str = "unknown") -> CodingResponse:
    """
    Create standardized error response for coding operations.
    
    Args:
        error_message: Error description
        operation: Operation that encountered the error
    
    Returns:
        Error CodingResponse
    """
    return CodingResponse(
        success=False,
        message=f"Error in {operation}: {error_message}",
        data={"operation": operation, "error_type": "coding_error"}
    )
