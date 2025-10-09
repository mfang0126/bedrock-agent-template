"""
Command Execution Tool for Coding Agent

Provides secure command execution within workspace boundaries with comprehensive
security validation, timeout handling, and output capture.
"""

from datetime import datetime
import logging
import os
from pathlib import Path
import re
import shlex
import signal
import subprocess
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import psutil

logger = logging.getLogger(__name__)


class CommandExecutionError(Exception):
    """Raised when command execution fails"""
    pass


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


class TimeoutError(Exception):
    """Raised when command execution times out"""
    pass


class CommandExecutor:
    """
    Secure command executor for coding agent workspace
    """
    
    def __init__(self, workspace_root: str):
        """
        Initialize command executor with workspace root
        
        Args:
            workspace_root: Root directory for command execution
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.default_timeout = 300  # 5 minutes
        self.max_timeout = 1800  # 30 minutes
        self.max_output_size = 1024 * 1024  # 1MB
        
        # Allowed commands and their patterns
        self.allowed_commands = {
            # Development tools - Python
            'python', 'python3', 'pip', 'pip3', 'poetry', 'pipenv', 'pdm', 'hatch',
            'uv',  # Modern Python package manager
            
            # Development tools - Node.js/JavaScript/TypeScript
            'node', 'npm', 'yarn', 'pnpm', 'npx', 'bun',
            'corepack',  # Yarn 4 package manager enabler
            
            # Development tools - Java
            'java', 'javac', 'maven', 'mvn', 'gradle', 'gradlew',
            
            # Development tools - C/C++
            'gcc', 'g++', 'clang', 'clang++', 'make', 'cmake', 'ninja',
            
            # Development tools - Other languages
            'go', 'cargo', 'rustc', 'rustup',
            'ruby', 'gem', 'bundle', 'rbenv',
            'php', 'composer',
            'dotnet', 'nuget',
            
            # Testing frameworks - Python
            'pytest', 'unittest', 'nose2', 'tox', 'coverage', 'bandit',
            
            # Testing frameworks - JavaScript/TypeScript
            'jest', 'mocha', 'karma', 'cypress', 'playwright', 'vitest',
            
            # Testing frameworks - Other
            'junit', 'testng',
            'gtest', 'catch2',
            'rspec', 'minitest',
            
            # Build tools - JavaScript/TypeScript
            'webpack', 'rollup', 'vite', 'parcel', 'esbuild', 'swc',
            'babel', 'tsc', 'eslint', 'prettier', 'biome',
            
            # Build tools - Python
            'black', 'flake8', 'mypy', 'isort', 'ruff', 'pylint', 'autopep8',
            'bandit', 'safety', 'pre-commit',
            
            # Build tools - Other
            'rubocop', 'standardrb',
            
            # Version control - Git (comprehensive support)
            'git',  # All git subcommands will be validated separately
            
            # File operations
            'ls', 'cat', 'head', 'tail', 'grep', 'find', 'wc', 'sort', 'uniq',
            'cp', 'mv', 'mkdir', 'touch', 'tree',
            
            # Text processing
            'sed', 'awk', 'cut', 'tr', 'jq',  # JSON processor
            
            # Archive operations
            'tar', 'gzip', 'gunzip', 'zip', 'unzip',
            
            # System info (safe)
            'pwd', 'whoami', 'date', 'uname', 'which', 'where', 'env',
            'echo', 'printf',  # Output commands
            
            # Development servers (safe local development)
            'serve',  # Simple HTTP server
        }
        
        # Dangerous commands that are never allowed
        self.forbidden_commands = {
            # System modification
            'rm', 'rmdir', 'del', 'rd', 'format', 'fdisk',
            'sudo', 'su', 'chmod', 'chown', 'chgrp',
            'mount', 'umount', 'fsck', 'mkfs',
            
            # Network operations
            'curl', 'wget', 'nc', 'netcat', 'telnet', 'ssh', 'scp', 'rsync',
            'ping', 'nmap', 'netstat', 'ss', 'lsof',
            
            # Process control
            'kill', 'killall', 'pkill', 'ps', 'top', 'htop',
            'systemctl', 'service', 'launchctl',
            
            # Package management (system-wide)
            'apt', 'apt-get', 'yum', 'dnf', 'pacman', 'brew',
            'choco', 'winget', 'snap',
            
            # Dangerous utilities
            'dd', 'shred', 'wipe', 'srm',
            'crontab', 'at', 'batch',
            'eval', 'exec', 'source', '.',
            
            # Shells and interpreters (direct execution)
            'sh', 'bash', 'zsh', 'fish', 'csh', 'tcsh',
            'cmd', 'powershell', 'pwsh'
        }
        
        # Dangerous patterns in commands
        self.forbidden_patterns = [
            r'>\s*/dev/',  # Writing to device files
            r'<\s*/dev/',  # Reading from device files
            r'\|\s*sh\b',  # Piping to shell
            r'\|\s*bash\b',  # Piping to bash
            r'\|\s*eval\b',  # Piping to eval
            r'`[^`]*`',  # Command substitution
            r'\$\([^)]*\)',  # Command substitution
            r'&&\s*(rm|del|format)',  # Chained dangerous commands
            r';\s*(rm|del|format)',  # Sequential dangerous commands
            r'sudo\s+',  # Sudo usage
            r'su\s+',  # Su usage
            r'--privileged',  # Docker privileged mode
            r'--user\s+root',  # Running as root
        ]
    
    def _validate_command(self, command: str) -> None:
        """
        Validate command for security
        
        Args:
            command: Command to validate
            
        Raises:
            SecurityError: If command is not allowed
        """
        # Parse command to get the base command
        try:
            parts = shlex.split(command)
        except ValueError as e:
            raise SecurityError(f"Invalid command syntax: {e}")
        
        if not parts:
            raise SecurityError("Empty command")
        
        base_command = parts[0]
        
        # Check if base command is forbidden
        if base_command in self.forbidden_commands:
            raise SecurityError(f"Command '{base_command}' is forbidden")
        
        # Check if base command is allowed
        if base_command not in self.allowed_commands:
            # Allow relative paths to executables in workspace
            if not (base_command.startswith('./') or base_command.startswith('../')):
                raise SecurityError(f"Command '{base_command}' is not in allowed list")
        
        # Special validation for git commands
        if base_command == 'git':
            self._validate_git_command(parts)
        
        # Special validation for package managers
        if base_command in ['npm', 'yarn', 'pnpm']:
            self._validate_package_manager_command(base_command, parts)
        
        # Special validation for Python tools
        if base_command in ['pip', 'pip3', 'poetry', 'pipenv', 'pdm', 'hatch', 'uv']:
            self._validate_python_tool_command(base_command, parts)
        
        # Special validation for Node.js/TypeScript tools
        if base_command in ['npx', 'tsc', 'eslint', 'prettier', 'jest', 'mocha', 'cypress', 'playwright']:
            self._validate_nodejs_tool_command(base_command, parts)
        
        # Check for dangerous patterns
        for pattern in self.forbidden_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                raise SecurityError(f"Command contains forbidden pattern: {pattern}")
        
        # Check for path traversal in arguments
        for part in parts[1:]:
            if '../' in part and not part.startswith('./'):
                # Allow relative paths within workspace
                try:
                    resolved = (self.workspace_root / part).resolve()
                    resolved.relative_to(self.workspace_root)
                except (ValueError, OSError):
                    raise SecurityError(f"Path traversal detected in argument: {part}")
    
    def _validate_git_command(self, parts: List[str]) -> None:
        """
        Validate git command for security
        
        Args:
            parts: Command parts from shlex.split()
            
        Raises:
            SecurityError: If git command is not allowed
        """
        if len(parts) < 2:
            raise SecurityError("Git command requires subcommand")
        
        git_subcommand = parts[1]
        
        # Allowed git subcommands (safe operations)
        allowed_git_commands = {
            # Repository operations
            'clone', 'init', 'status', 'log', 'show', 'diff', 'blame',
            
            # Branch operations
            'branch', 'checkout', 'switch', 'merge', 'rebase',
            
            # File operations
            'add', 'commit', 'rm', 'mv', 'reset', 'restore',
            
            # Remote operations
            'remote', 'fetch', 'pull', 'push',
            
            # Information commands
            'config', 'help', 'version', 'rev-parse', 'describe',
            'ls-files', 'ls-tree', 'cat-file', 'rev-list',
            
            # Stash operations
            'stash',
            
            # Tag operations
            'tag',
            
            # Submodule operations (read-only)
            'submodule'
        }
        
        if git_subcommand not in allowed_git_commands:
            raise SecurityError(f"Git subcommand '{git_subcommand}' is not allowed")
        
        # Additional validation for specific commands
        if git_subcommand == 'clone':
            # Ensure clone URLs are safe (no file:// or dangerous protocols)
            for part in parts[2:]:
                if part.startswith('file://') or part.startswith('ftp://'):
                    raise SecurityError(f"Unsafe git clone protocol: {part}")
        
        elif git_subcommand == 'config':
            # Prevent dangerous git config operations
            for part in parts[2:]:
                if any(dangerous in part.lower() for dangerous in ['core.editor', 'core.pager', 'alias']):
                    raise SecurityError(f"Dangerous git config operation: {part}")
    
    def _validate_package_manager_command(self, manager: str, parts: List[str]) -> None:
        """
        Validate package manager commands for security
        
        Args:
            manager: Package manager name (npm, yarn, pnpm)
            parts: Command parts from shlex.split()
            
        Raises:
            SecurityError: If package manager command is not allowed
        """
        if len(parts) < 2:
            # Allow bare commands like 'npm' or 'yarn' (they show help)
            return
        
        subcommand = parts[1]
        
        # Common allowed subcommands for all package managers
        allowed_common = {
            # Installation and management
            'install', 'add', 'remove', 'uninstall', 'update', 'upgrade',
            
            # Information commands
            'list', 'ls', 'info', 'show', 'view', 'search', 'outdated',
            'audit', 'doctor', 'check',
            
            # Script execution
            'run', 'start', 'test', 'build', 'dev', 'serve',
            
            # Configuration
            'config', 'get', 'set',
            
            # Cache operations
            'cache',
            
            # Help and version
            'help', 'version', '--version', '-v',
            
            # Workspace operations
            'workspace', 'workspaces'
        }
        
        # Manager-specific allowed commands
        manager_specific = {
            'npm': {
                'init', 'publish', 'unpublish', 'pack', 'link', 'unlink',
                'ci', 'prune', 'rebuild', 'dedupe', 'shrinkwrap',
                'access', 'adduser', 'logout', 'whoami', 'team',
                'dist-tag', 'deprecate', 'owner', 'repo', 'bugs', 'docs'
            },
            'yarn': {
                'init', 'create', 'publish', 'pack', 'link', 'unlink',
                'dlx', 'exec', 'node', 'up', 'why', 'patch', 'patch-commit',
                'stage', 'commit', 'version', 'constraints', 'dedupe',
                'plugin', 'set', 'unplug', 'rebuild', 'bin'
            },
            'pnpm': {
                'init', 'create', 'publish', 'pack', 'link', 'unlink',
                'dlx', 'exec', 'why', 'patch', 'patch-commit',
                'deploy', 'fetch', 'rebuild', 'prune', 'store'
            }
        }
        
        allowed_commands = allowed_common | manager_specific.get(manager, set())
        
        if subcommand not in allowed_commands:
            raise SecurityError(f"{manager} subcommand '{subcommand}' is not allowed")
        
        # Additional validation for specific commands
        if subcommand in ['config', 'set']:
            # Prevent dangerous configuration changes
            for part in parts[2:]:
                if any(dangerous in part.lower() for dangerous in [
                    'registry', 'proxy', 'https-proxy', 'ca', 'cafile',
                    'cert', 'key', 'user-agent', 'git', 'editor'
                ]):
                    raise SecurityError(f"Dangerous {manager} config operation: {part}")
        
        elif subcommand == 'run':
            # Validate script names to prevent dangerous operations
            if len(parts) > 2:
                script_name = parts[2]
                if any(dangerous in script_name.lower() for dangerous in [
                    'postinstall', 'preinstall', 'install', 'uninstall'
                ]):
                    # Allow common lifecycle scripts but be cautious
                    pass
    
    def _validate_python_tool_command(self, tool: str, parts: List[str]) -> None:
        """
        Validate Python tool commands for security
        
        Args:
            tool: Python tool name (pip, poetry, etc.)
            parts: Command parts from shlex.split()
            
        Raises:
            SecurityError: If Python tool command is not allowed
        """
        if len(parts) < 2:
            # Allow bare commands (they show help)
            return
        
        subcommand = parts[1]
        
        # Tool-specific allowed commands
        allowed_commands = {
            'pip': {
                'install', 'uninstall', 'list', 'show', 'freeze', 'check',
                'search', 'wheel', 'hash', 'help', 'version', 'config',
                'debug', 'cache', 'index', 'inspect', 'download'
            },
            'pip3': {
                'install', 'uninstall', 'list', 'show', 'freeze', 'check',
                'search', 'wheel', 'hash', 'help', 'version', 'config',
                'debug', 'cache', 'index', 'inspect', 'download'
            },
            'poetry': {
                'new', 'init', 'install', 'add', 'remove', 'update', 'lock',
                'build', 'publish', 'config', 'run', 'shell', 'show',
                'search', 'check', 'version', 'cache', 'source', 'env',
                'export', 'debug', 'help', 'self', 'plugin'
            },
            'pipenv': {
                'install', 'uninstall', 'lock', 'requirements', 'check',
                'graph', 'shell', 'run', 'sync', 'clean', 'where',
                'venv', 'py', 'scripts', 'open', 'verify'
            },
            'pdm': {
                'add', 'remove', 'install', 'update', 'lock', 'sync',
                'list', 'show', 'search', 'build', 'publish', 'run',
                'script', 'config', 'cache', 'info', 'init', 'use',
                'venv', 'export', 'import', 'fix', 'check'
            },
            'hatch': {
                'new', 'init', 'build', 'publish', 'version', 'env',
                'run', 'shell', 'test', 'fmt', 'clean', 'config',
                'status', 'dep', 'project', 'python'
            },
            'uv': {
                'add', 'remove', 'sync', 'lock', 'run', 'init', 'venv',
                'pip', 'tool', 'python', 'cache', 'version', 'help',
                'build', 'publish', 'tree', 'export'
            }
        }
        
        tool_commands = allowed_commands.get(tool, set())
        
        if subcommand not in tool_commands:
            raise SecurityError(f"{tool} subcommand '{subcommand}' is not allowed")
        
        # Additional validation for specific commands
        if subcommand == 'install' and tool in ['pip', 'pip3']:
            # Check for dangerous pip install options
            for part in parts[2:]:
                if any(dangerous in part for dangerous in [
                    '--trusted-host', '--index-url', '--extra-index-url',
                    '--find-links', '--process-dependency-links'
                ]):
                    raise SecurityError(f"Dangerous {tool} install option: {part}")
        
        elif subcommand == 'config':
            # Prevent dangerous configuration changes
            for part in parts[2:]:
                if any(dangerous in part.lower() for dangerous in [
                    'index-url', 'trusted-host', 'cert', 'client-cert',
                    'proxy', 'timeout', 'retries'
                ]):
                    raise SecurityError(f"Dangerous {tool} config operation: {part}")
    
    def _validate_nodejs_tool_command(self, tool: str, parts: List[str]) -> None:
        """
        Validate Node.js/TypeScript tool commands for security
        
        Args:
            tool: Node.js tool name (npx, tsc, eslint, etc.)
            parts: Command parts from shlex.split()
            
        Raises:
            SecurityError: If Node.js tool command is not allowed
        """
        # For npx, validate the package being executed
        if tool == 'npx':
            if len(parts) < 2:
                raise SecurityError("npx requires a package name")
            
            package_name = parts[1]
            
            # Allow common development packages
            allowed_packages = {
                # Build tools
                'webpack', 'rollup', 'vite', 'parcel', 'esbuild', 'swc',
                'babel', 'tsc', 'typescript',
                
                # Linting and formatting
                'eslint', 'prettier', 'biome', 'standard',
                
                # Testing
                'jest', 'mocha', 'karma', 'cypress', 'playwright', 'vitest',
                
                # Generators and scaffolding
                'create-react-app', 'create-next-app', 'create-vue',
                'create-svelte', 'create-vite', 'degit',
                
                # Development servers
                'serve', 'http-server', 'live-server',
                
                # Package management
                'npm-check-updates', 'ncu', 'depcheck',
                
                # Documentation
                'typedoc', 'jsdoc', 'storybook',
                
                # Common CLI tools
                'rimraf', 'cross-env', 'concurrently', 'nodemon',
                'ts-node', 'tsx', 'tsup'
            }
            
            # Extract package name (remove version specifiers)
            clean_package = package_name.split('@')[0] if '@' in package_name[1:] else package_name
            
            if clean_package not in allowed_packages:
                raise SecurityError(f"npx package '{clean_package}' is not allowed")
        
        # For other tools, they're generally safe as they're already in allowed_commands
        # Additional validation can be added here if needed for specific tools
        
        # Validate TypeScript compiler options
        if tool == 'tsc':
            for part in parts[1:]:
                if any(dangerous in part for dangerous in [
                    '--outDir /', '--outFile /', '--rootDir /',
                    '--baseUrl /', '--paths'
                ]):
                    if part.startswith('/') or '../' in part:
                        raise SecurityError(f"Dangerous tsc path option: {part}")
        
        # Validate ESLint options
        elif tool == 'eslint':
            for part in parts[1:]:
                if part.startswith('--rulesdir') and ('/' in part or '../' in part):
                    raise SecurityError(f"Dangerous eslint rulesdir option: {part}")
        
        # Validate Jest options
        elif tool == 'jest':
            for part in parts[1:]:
                if any(dangerous in part for dangerous in [
                    '--setupFilesAfterEnv', '--setupFiles', '--globalSetup',
                    '--globalTeardown', '--testEnvironment'
                ]):
                    if '../' in part or part.startswith('/'):
                        raise SecurityError(f"Dangerous jest option: {part}")
    
    def _setup_environment(self, env_vars: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Setup secure environment for command execution
        
        Args:
            env_vars: Additional environment variables
            
        Returns:
            Environment dictionary
        """
        # Start with minimal environment
        env = {
            'PATH': os.environ.get('PATH', ''),
            'HOME': str(self.workspace_root),
            'PWD': str(self.workspace_root),
            'USER': 'coding-agent',
            'SHELL': '/bin/sh',
            'TERM': 'xterm',
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8'
        }
        
        # Add language-specific environment variables
        python_path = str(self.workspace_root)
        env.update({
            'PYTHONPATH': python_path,
            'PYTHONDONTWRITEBYTECODE': '1',
            'PYTHONUNBUFFERED': '1',
            'NODE_ENV': 'development',
            'JAVA_HOME': os.environ.get('JAVA_HOME', ''),
            'GOPATH': str(self.workspace_root / 'go'),
            'CARGO_HOME': str(self.workspace_root / '.cargo'),
            'RUSTUP_HOME': str(self.workspace_root / '.rustup')
        })
        
        # Add custom environment variables
        if env_vars:
            for key, value in env_vars.items():
                # Validate environment variable names
                if re.match(r'^[A-Z_][A-Z0-9_]*$', key):
                    env[key] = str(value)
                else:
                    logger.warning(f"Invalid environment variable name: {key}")
        
        return env
    
    def _kill_process_tree(self, pid: int) -> None:
        """
        Kill process and all its children
        
        Args:
            pid: Process ID to kill
        """
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            
            # Kill children first
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass
            
            # Kill parent
            try:
                parent.kill()
            except psutil.NoSuchProcess:
                pass
                
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            logger.warning(f"Error killing process tree {pid}: {e}")
    
    def execute_command(self, command: str, timeout: Optional[int] = None,
                       cwd: Optional[str] = None, env_vars: Optional[Dict[str, str]] = None,
                       capture_output: bool = True) -> Dict[str, Any]:
        """
        Execute command safely with timeout and output capture
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds (default: 300)
            cwd: Working directory (relative to workspace)
            env_vars: Additional environment variables
            capture_output: Whether to capture stdout/stderr
            
        Returns:
            Dictionary with execution result
        """
        start_time = datetime.now()
        
        try:
            # Validate command
            self._validate_command(command)
            
            # Set timeout
            if timeout is None:
                timeout = self.default_timeout
            elif timeout > self.max_timeout:
                timeout = self.max_timeout
            
            # Set working directory
            if cwd:
                work_dir = self.workspace_root / cwd
                work_dir = work_dir.resolve()
                # Ensure working directory is within workspace
                work_dir.relative_to(self.workspace_root)
            else:
                work_dir = self.workspace_root
            
            # Ensure working directory exists
            work_dir.mkdir(parents=True, exist_ok=True)
            
            # Setup environment
            env = self._setup_environment(env_vars)
            
            # Prepare command execution
            if capture_output:
                stdout = subprocess.PIPE
                stderr = subprocess.PIPE
            else:
                stdout = None
                stderr = None
            
            # Execute command
            logger.info(f"Executing command: {command} in {work_dir}")
            
            process = subprocess.Popen(
                command,
                shell=True,
                cwd=str(work_dir),
                env=env,
                stdout=stdout,
                stderr=stderr,
                text=True,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
            
            # Wait for completion with timeout
            try:
                stdout_data, stderr_data = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Kill process tree
                self._kill_process_tree(process.pid)
                process.kill()
                process.wait()
                
                raise TimeoutError(f"Command timed out after {timeout} seconds")
            
            # Check output size
            if stdout_data and len(stdout_data) > self.max_output_size:
                stdout_data = stdout_data[:self.max_output_size] + "\n... (output truncated)"
            
            if stderr_data and len(stderr_data) > self.max_output_size:
                stderr_data = stderr_data[:self.max_output_size] + "\n... (output truncated)"
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return {
                'success': process.returncode == 0,
                'exit_code': process.returncode,
                'stdout': stdout_data or '',
                'stderr': stderr_data or '',
                'command': command,
                'cwd': str(work_dir.relative_to(self.workspace_root)),
                'duration': duration,
                'timeout': timeout,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'command': command,
                'duration': duration,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            }
    
    def execute_script(self, script_content: str, script_type: str = 'python',
                      timeout: Optional[int] = None, cwd: Optional[str] = None,
                      env_vars: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Execute script content safely
        
        Args:
            script_content: Script content to execute
            script_type: Type of script (python, javascript, bash, etc.)
            timeout: Timeout in seconds
            cwd: Working directory
            env_vars: Additional environment variables
            
        Returns:
            Dictionary with execution result
        """
        try:
            # Create temporary script file
            script_extensions = {
                'python': '.py',
                'javascript': '.js',
                'bash': '.sh',
                'shell': '.sh',
                'java': '.java',
                'cpp': '.cpp',
                'c': '.c'
            }
            
            extension = script_extensions.get(script_type, '.txt')
            script_name = f"temp_script_{int(time.time())}{extension}"
            
            if cwd:
                script_dir = self.workspace_root / cwd
            else:
                script_dir = self.workspace_root
            
            script_path = script_dir / script_name
            
            # Write script content
            script_path.write_text(script_content, encoding='utf-8')
            
            # Determine execution command
            execution_commands = {
                'python': f'python3 {script_name}',
                'javascript': f'node {script_name}',
                'bash': f'bash {script_name}',
                'shell': f'sh {script_name}',
                'java': f'javac {script_name} && java {script_name[:-5]}',
                'cpp': f'g++ -o {script_name[:-4]} {script_name} && ./{script_name[:-4]}',
                'c': f'gcc -o {script_name[:-2]} {script_name} && ./{script_name[:-2]}'
            }
            
            command = execution_commands.get(script_type, f'cat {script_name}')
            
            # Execute script
            result = self.execute_command(
                command=command,
                timeout=timeout,
                cwd=cwd,
                env_vars=env_vars
            )
            
            # Add script information to result
            result.update({
                'script_type': script_type,
                'script_name': script_name,
                'script_content': script_content[:500] + '...' if len(script_content) > 500 else script_content
            })
            
            # Clean up script file
            try:
                script_path.unlink()
                if script_type in ['java', 'cpp', 'c']:
                    # Clean up compiled files
                    compiled_files = [
                        script_path.with_suffix('.class'),
                        script_path.with_suffix(''),
                        script_path.with_name(script_name[:-5] + '.class')
                    ]
                    for compiled_file in compiled_files:
                        if compiled_file.exists():
                            compiled_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up script file {script_path}: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'script_type': script_type,
                'script_content': script_content[:200] + '...' if len(script_content) > 200 else script_content
            }
    
    def get_command_help(self, command: str) -> Dict[str, Any]:
        """
        Get help information for a command
        
        Args:
            command: Command to get help for
            
        Returns:
            Dictionary with help information
        """
        try:
            # Validate command
            if command not in self.allowed_commands:
                return {
                    'success': False,
                    'error': f"Command '{command}' is not allowed",
                    'command': command
                }
            
            # Try different help options
            help_commands = [
                f'{command} --help',
                f'{command} -h',
                f'{command} help',
                f'man {command}'
            ]
            
            for help_cmd in help_commands:
                result = self.execute_command(help_cmd, timeout=30)
                if result['success'] and result['stdout']:
                    return {
                        'success': True,
                        'command': command,
                        'help_command': help_cmd,
                        'help_text': result['stdout']
                    }
            
            return {
                'success': False,
                'error': f"No help available for command '{command}'",
                'command': command
            }
            
        except Exception as e:
            logger.error(f"Failed to get help for command {command}: {e}")
            return {
                'success': False,
                'error': str(e),
                'command': command
            }
    
    def list_allowed_commands(self) -> Dict[str, Any]:
        """
        List all allowed commands
        
        Returns:
            Dictionary with allowed commands categorized
        """
        categories = {
            'Development Tools': [
                'python', 'python3', 'pip', 'pip3', 'poetry', 'pipenv',
                'node', 'npm', 'yarn', 'pnpm', 'npx',
                'java', 'javac', 'maven', 'mvn', 'gradle',
                'gcc', 'g++', 'clang', 'clang++', 'make', 'cmake',
                'go', 'cargo', 'rustc',
                'ruby', 'gem', 'bundle',
                'php', 'composer'
            ],
            'Testing Frameworks': [
                'pytest', 'unittest', 'nose2', 'tox',
                'jest', 'mocha', 'karma', 'cypress',
                'junit', 'testng',
                'gtest', 'catch2',
                'rspec', 'minitest'
            ],
            'Build Tools': [
                'webpack', 'rollup', 'vite', 'parcel',
                'babel', 'tsc', 'eslint', 'prettier',
                'black', 'flake8', 'mypy', 'isort',
                'rubocop', 'standardrb'
            ],
            'Version Control': ['git'],
            'File Operations': [
                'ls', 'cat', 'head', 'tail', 'grep', 'find', 'wc',
                'cp', 'mv', 'mkdir', 'touch'
            ],
            'System Info': [
                'pwd', 'whoami', 'date', 'uname', 'which', 'where'
            ]
        }
        
        return {
            'success': True,
            'categories': categories,
            'total_commands': len(self.allowed_commands),
            'forbidden_commands': list(self.forbidden_commands)
        }