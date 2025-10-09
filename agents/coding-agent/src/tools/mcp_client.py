"""MCP Client wrapper for safe code execution with security validation."""

import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
import shutil
import psutil
from datetime import datetime, timedelta


class SecurityError(Exception):
    """Raised when a security violation is detected."""
    pass


class ExecutionError(Exception):
    """Raised when code execution fails."""
    pass


class MCPClient:
    """
    MCP Client wrapper for safe code execution with comprehensive security validation.
    
    This class provides a secure interface for executing code and commands while
    maintaining strict security controls and resource limits.
    """
    
    # Dangerous commands that should never be executed
    DANGEROUS_COMMANDS = {
        'rm', 'rmdir', 'del', 'format', 'fdisk', 'mkfs', 'dd',
        'sudo', 'su', 'chmod', 'chown', 'passwd', 'useradd', 'userdel',
        'systemctl', 'service', 'kill', 'killall', 'pkill',
        'reboot', 'shutdown', 'halt', 'poweroff',
        'mount', 'umount', 'fsck', 'crontab',
        'iptables', 'ufw', 'firewall-cmd',
        'curl', 'wget', 'nc', 'netcat', 'telnet', 'ssh', 'scp', 'rsync'
    }
    
    # Allowed file extensions for reading/writing
    ALLOWED_EXTENSIONS = {
        '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
        '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt',
        '.html', '.css', '.scss', '.less', '.xml', '.json', '.yaml', '.yml',
        '.md', '.txt', '.cfg', '.conf', '.ini', '.toml',
        '.sql', '.sh', '.bat', '.ps1', '.dockerfile', '.gitignore'
    }
    
    def __init__(self, workspace_path: str, max_file_size: int = 10 * 1024 * 1024):
        """
        Initialize MCP Client with security settings.
        
        Args:
            workspace_path: Base path for workspace operations
            max_file_size: Maximum allowed file size in bytes (default: 10MB)
        """
        self.workspace_path = Path(workspace_path).resolve()
        self.max_file_size = max_file_size
        self.session_id = str(uuid.uuid4())
        
        # Ensure workspace exists and is secure
        self._setup_secure_workspace()
    
    def _setup_secure_workspace(self) -> None:
        """Set up a secure workspace with proper permissions."""
        try:
            self.workspace_path.mkdir(parents=True, exist_ok=True)
            # Set restrictive permissions (owner read/write/execute only)
            os.chmod(self.workspace_path, 0o700)
        except Exception as e:
            raise SecurityError(f"Failed to setup secure workspace: {e}")
    
    def _validate_path(self, file_path: Union[str, Path]) -> Path:
        """
        Validate that a file path is safe and within the workspace.
        
        Args:
            file_path: Path to validate
            
        Returns:
            Resolved and validated Path object
            
        Raises:
            SecurityError: If path is unsafe
        """
        try:
            path = Path(file_path).resolve()
            
            # Check if path is within workspace
            if not str(path).startswith(str(self.workspace_path)):
                raise SecurityError(f"Path outside workspace: {path}")
            
            # Check for path traversal attempts
            if '..' in str(file_path) or '~' in str(file_path):
                raise SecurityError(f"Path traversal detected: {file_path}")
            
            # Check file extension if it's a file
            if path.suffix and path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
                raise SecurityError(f"File extension not allowed: {path.suffix}")
            
            return path
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Invalid path: {file_path} - {e}")
    
    def _validate_command(self, command: str) -> None:
        """
        Validate that a command is safe to execute.
        
        Args:
            command: Command to validate
            
        Raises:
            SecurityError: If command is dangerous
        """
        # Check for dangerous commands
        cmd_parts = command.lower().split()
        if not cmd_parts:
            raise SecurityError("Empty command")
        
        base_cmd = cmd_parts[0].split('/')[-1]  # Get command name without path
        
        if base_cmd in self.DANGEROUS_COMMANDS:
            raise SecurityError(f"Dangerous command not allowed: {base_cmd}")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[;&|`$()]',  # Command injection characters
            r'>\s*/dev/',  # Writing to device files
            r'<\s*/dev/',  # Reading from device files
            r'/etc/',      # System configuration access
            r'/proc/',     # Process information access
            r'/sys/',      # System information access
            r'sudo',       # Privilege escalation
            r'su\s',       # User switching
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise SecurityError(f"Suspicious pattern in command: {pattern}")
    
    def _check_resource_limits(self, process: subprocess.Popen, timeout: int) -> None:
        """
        Monitor process resource usage and enforce limits.
        
        Args:
            process: Process to monitor
            timeout: Maximum execution time in seconds
        """
        try:
            ps_process = psutil.Process(process.pid)
            start_time = datetime.now()
            
            while process.poll() is None:
                # Check timeout
                if (datetime.now() - start_time).seconds > timeout:
                    process.terminate()
                    raise ExecutionError(f"Command timed out after {timeout} seconds")
                
                # Check memory usage (limit to 512MB)
                memory_info = ps_process.memory_info()
                if memory_info.rss > 512 * 1024 * 1024:  # 512MB
                    process.terminate()
                    raise ExecutionError("Process exceeded memory limit (512MB)")
                
                # Check CPU usage (limit to 80% for more than 10 seconds)
                cpu_percent = ps_process.cpu_percent()
                if cpu_percent > 80:
                    # Wait a bit and check again
                    import time
                    time.sleep(1)
                    if ps_process.cpu_percent() > 80:
                        process.terminate()
                        raise ExecutionError("Process exceeded CPU limit (80%)")
                
        except psutil.NoSuchProcess:
            # Process already finished
            pass
        except Exception as e:
            if process.poll() is None:
                process.terminate()
            raise ExecutionError(f"Resource monitoring failed: {e}")
    
    def read_file(self, file_path: str) -> str:
        """
        Safely read a file from the workspace.
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            File contents as string
            
        Raises:
            SecurityError: If path is unsafe
            ExecutionError: If file cannot be read
        """
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                raise ExecutionError(f"File does not exist: {path}")
            
            if not path.is_file():
                raise ExecutionError(f"Path is not a file: {path}")
            
            # Check file size
            if path.stat().st_size > self.max_file_size:
                raise ExecutionError(f"File too large: {path.stat().st_size} bytes")
            
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
                
        except UnicodeDecodeError:
            raise ExecutionError(f"File is not valid UTF-8: {file_path}")
        except Exception as e:
            if isinstance(e, (SecurityError, ExecutionError)):
                raise
            raise ExecutionError(f"Failed to read file {file_path}: {e}")
    
    def write_file(self, file_path: str, content: str, overwrite: bool = False) -> bool:
        """
        Safely write content to a file in the workspace.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            overwrite: Whether to overwrite existing files
            
        Returns:
            True if successful
            
        Raises:
            SecurityError: If path is unsafe
            ExecutionError: If file cannot be written
        """
        try:
            path = self._validate_path(file_path)
            
            # Check if file exists and overwrite is not allowed
            if path.exists() and not overwrite:
                raise ExecutionError(f"File exists and overwrite not allowed: {path}")
            
            # Check content size
            content_bytes = content.encode('utf-8')
            if len(content_bytes) > self.max_file_size:
                raise ExecutionError(f"Content too large: {len(content_bytes)} bytes")
            
            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to temporary file first, then move (atomic operation)
            with tempfile.NamedTemporaryFile(
                mode='w', 
                encoding='utf-8', 
                dir=path.parent, 
                delete=False
            ) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            # Move temporary file to final location
            shutil.move(tmp_path, path)
            
            # Set secure permissions
            os.chmod(path, 0o600)
            
            return True
            
        except Exception as e:
            if isinstance(e, (SecurityError, ExecutionError)):
                raise
            raise ExecutionError(f"Failed to write file {file_path}: {e}")
    
    def execute_command(
        self, 
        command: str, 
        timeout: int = 30,
        cwd: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Safely execute a command in the workspace.
        
        Args:
            command: Command to execute
            timeout: Maximum execution time in seconds
            cwd: Working directory (must be within workspace)
            
        Returns:
            Dictionary with execution results
            
        Raises:
            SecurityError: If command is unsafe
            ExecutionError: If execution fails
        """
        try:
            # Validate command
            self._validate_command(command)
            
            # Validate and set working directory
            if cwd:
                work_dir = self._validate_path(cwd)
                if not work_dir.is_dir():
                    raise ExecutionError(f"Working directory does not exist: {cwd}")
            else:
                work_dir = self.workspace_path
            
            # Prepare environment
            env = os.environ.copy()
            env['PATH'] = '/usr/local/bin:/usr/bin:/bin'  # Restricted PATH
            env.pop('LD_PRELOAD', None)  # Remove potentially dangerous env vars
            env.pop('LD_LIBRARY_PATH', None)
            
            # Execute command
            start_time = datetime.now()
            
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(work_dir),
                env=env,
                text=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Monitor resource usage
            self._check_resource_limits(process, timeout)
            
            # Wait for completion
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise ExecutionError(f"Command timed out after {timeout} seconds")
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                'command': command,
                'return_code': process.returncode,
                'stdout': stdout,
                'stderr': stderr,
                'execution_time': execution_time,
                'success': process.returncode == 0,
                'timestamp': start_time.isoformat()
            }
            
        except Exception as e:
            if isinstance(e, (SecurityError, ExecutionError)):
                raise
            raise ExecutionError(f"Command execution failed: {e}")
    
    def list_files(self, directory: str = ".") -> List[Dict[str, Any]]:
        """
        List files in a directory within the workspace.
        
        Args:
            directory: Directory to list (relative to workspace)
            
        Returns:
            List of file information dictionaries
            
        Raises:
            SecurityError: If path is unsafe
            ExecutionError: If listing fails
        """
        try:
            dir_path = self._validate_path(directory)
            
            if not dir_path.exists():
                raise ExecutionError(f"Directory does not exist: {directory}")
            
            if not dir_path.is_dir():
                raise ExecutionError(f"Path is not a directory: {directory}")
            
            files = []
            for item in dir_path.iterdir():
                try:
                    stat = item.stat()
                    files.append({
                        'name': item.name,
                        'path': str(item.relative_to(self.workspace_path)),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': stat.st_size if item.is_file() else None,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'permissions': oct(stat.st_mode)[-3:]
                    })
                except (OSError, ValueError):
                    # Skip files we can't access
                    continue
            
            return sorted(files, key=lambda x: (x['type'], x['name']))
            
        except Exception as e:
            if isinstance(e, (SecurityError, ExecutionError)):
                raise
            raise ExecutionError(f"Failed to list directory {directory}: {e}")
    
    def cleanup(self) -> None:
        """Clean up workspace and resources."""
        try:
            if self.workspace_path.exists():
                # Remove all files in workspace
                for item in self.workspace_path.rglob('*'):
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        item.rmdir()
        except Exception as e:
            # Log error but don't raise - cleanup is best effort
            print(f"Warning: Cleanup failed: {e}")