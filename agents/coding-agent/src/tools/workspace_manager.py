"""Workspace management tools for setup and cleanup operations."""

import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Optional, Any, List
import json
import shlex
from datetime import datetime
import tarfile
import zipfile

from .mcp_client import MCPClient, SecurityError, ExecutionError


class WorkspaceManager:
    """
    Manages isolated workspaces for safe code execution.
    
    Provides functionality to create, configure, backup, and cleanup
    workspaces with proper security controls.
    """
    
    def __init__(self, base_path: str = "/tmp/workspaces"):
        """
        Initialize workspace manager.
        
        Args:
            base_path: Base directory for all workspaces
        """
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions on base directory
        os.chmod(self.base_path, 0o700)
        
        self.active_workspaces: Dict[str, Dict[str, Any]] = {}

    def _resolve_workspace_path(self, workspace_path: str) -> Path:
        """Resolve a workspace path relative to the base directory."""
        path = Path(workspace_path)
        if not path.is_absolute():
            path = self.base_path / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.resolve()

    def _run_command(self, command: List[str], cwd: Optional[Path] = None, timeout: int = 600) -> Dict[str, Any]:
        """Run a command inside the workspace and capture output."""
        display = " ".join(command)
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd) if cwd else None,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "command": display,
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "success": completed.returncode == 0,
            }
        except subprocess.TimeoutExpired as exc:
            return {
                "command": display,
                "returncode": None,
                "stdout": exc.stdout or "",
                "stderr": (exc.stderr or "") + "\nCommand timed out.",
                "success": False,
            }

    def setup_workspace(
        self,
        workspace_path: str,
        repo_url: Optional[str] = None,
        branch: str = "main",
        commands: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Prepare a workspace by cloning/updating a repo and running setup commands.
        """
        resolved_path = self._resolve_workspace_path(workspace_path)
        command_results: List[Dict[str, Any]] = []

        # Step 1: Clone or update repository when requested.
        if repo_url:
            git_dir = resolved_path / ".git"
            if git_dir.exists():
                git_cmd = ["git", "-C", str(resolved_path), "pull", "origin", branch]
                command_results.append(self._run_command(git_cmd, cwd=None))
            else:
                if resolved_path.exists() and any(resolved_path.iterdir()):
                    # If directory is populated, run clone into the directory via git pull alternative.
                    git_cmd = ["git", "-C", str(resolved_path), "init"]
                    command_results.append(self._run_command(git_cmd, cwd=None))
                    command_results.append(self._run_command(["git", "-C", str(resolved_path), "remote", "add", "origin", repo_url], cwd=None))
                    command_results.append(self._run_command(["git", "-C", str(resolved_path), "fetch", "--all"], cwd=None))
                    command_results.append(self._run_command(["git", "-C", str(resolved_path), "checkout", branch], cwd=None))
                    command_results.append(self._run_command(["git", "-C", str(resolved_path), "pull", "origin", branch], cwd=None))
                else:
                    git_cmd = ["git", "clone", "--branch", branch, "--single-branch", repo_url, str(resolved_path)]
                    command_results.append(self._run_command(git_cmd, cwd=None))

        # Step 2: Run installation/audit commands.
        if commands is None:
            commands = ["yarn install", "npm install", "npm audit --json"]

        for raw_command in commands:
            cmd_parts = shlex.split(raw_command)
            command_results.append(self._run_command(cmd_parts, cwd=resolved_path))

        overall_success = all(item["success"] for item in command_results)
        return {
            "success": overall_success,
            "workspace_path": str(resolved_path),
            "repo_url": repo_url,
            "branch": branch,
            "commands_executed": commands,
            "command_results": command_results,
        }
    
    def create_workspace(
        self, 
        workspace_id: Optional[str] = None,
        template: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new isolated workspace.
        
        Args:
            workspace_id: Optional custom workspace ID
            template: Optional template to initialize workspace
            config: Optional configuration for workspace
            
        Returns:
            Dictionary with workspace information
            
        Raises:
            ExecutionError: If workspace creation fails
        """
        try:
            # Generate workspace ID if not provided
            if not workspace_id:
                workspace_id = f"ws_{uuid.uuid4().hex[:8]}"
            
            # Validate workspace ID
            if not workspace_id.replace('_', '').replace('-', '').isalnum():
                raise ExecutionError(f"Invalid workspace ID: {workspace_id}")
            
            workspace_path = self.base_path / workspace_id
            
            # Check if workspace already exists
            if workspace_path.exists():
                raise ExecutionError(f"Workspace already exists: {workspace_id}")
            
            # Create workspace directory
            workspace_path.mkdir(parents=True)
            os.chmod(workspace_path, 0o700)
            
            # Initialize workspace structure
            self._initialize_workspace_structure(workspace_path, template)
            
            # Create MCP client for this workspace
            mcp_client = MCPClient(str(workspace_path))
            
            # Store workspace information
            workspace_info = {
                'id': workspace_id,
                'path': str(workspace_path),
                'created_at': datetime.now().isoformat(),
                'template': template,
                'config': config or {},
                'mcp_client': mcp_client,
                'status': 'active'
            }
            
            self.active_workspaces[workspace_id] = workspace_info
            
            # Create workspace metadata file
            self._save_workspace_metadata(workspace_path, workspace_info)
            
            return {
                'workspace_id': workspace_id,
                'path': str(workspace_path),
                'status': 'created',
                'created_at': workspace_info['created_at'],
                'template': template
            }
            
        except Exception as e:
            if isinstance(e, ExecutionError):
                raise
            raise ExecutionError(f"Failed to create workspace: {e}")
    
    def _initialize_workspace_structure(
        self, 
        workspace_path: Path, 
        template: Optional[str] = None
    ) -> None:
        """
        Initialize the workspace directory structure.
        
        Args:
            workspace_path: Path to the workspace
            template: Template to use for initialization
        """
        # Create standard directories
        directories = ['src', 'tests', 'docs', 'config', 'temp']
        for dir_name in directories:
            (workspace_path / dir_name).mkdir(exist_ok=True)
        
        # Apply template if specified
        if template:
            self._apply_template(workspace_path, template)
        
        # Create basic files
        self._create_basic_files(workspace_path)
    
    def _apply_template(self, workspace_path: Path, template: str) -> None:
        """
        Apply a template to the workspace.
        
        Args:
            workspace_path: Path to the workspace
            template: Template name to apply
        """
        templates = {
            'python': self._create_python_template,
            'javascript': self._create_javascript_template,
            'java': self._create_java_template,
            'cpp': self._create_cpp_template,
            'web': self._create_web_template
        }
        
        if template in templates:
            templates[template](workspace_path)
    
    def _create_python_template(self, workspace_path: Path) -> None:
        """Create Python project template."""
        # Create requirements.txt
        (workspace_path / 'requirements.txt').write_text(
            "# Python dependencies\n"
            "pytest>=7.0.0\n"
            "black>=23.0.0\n"
            "isort>=5.12.0\n"
        )
        
        # Create setup.py
        (workspace_path / 'setup.py').write_text(
            'from setuptools import setup, find_packages\n\n'
            'setup(\n'
            '    name="workspace-project",\n'
            '    version="0.1.0",\n'
            '    packages=find_packages(),\n'
            '    python_requires=">=3.8",\n'
            ')\n'
        )
        
        # Create main.py
        (workspace_path / 'src' / 'main.py').write_text(
            '#!/usr/bin/env python3\n'
            '"""Main module for the workspace project."""\n\n'
            'def main():\n'
            '    """Main function."""\n'
            '    print("Hello from workspace!")\n\n'
            'if __name__ == "__main__":\n'
            '    main()\n'
        )
        
        # Create test file
        (workspace_path / 'tests' / 'test_main.py').write_text(
            'import pytest\n'
            'from src.main import main\n\n'
            'def test_main():\n'
            '    """Test main function."""\n'
            '    # Add your tests here\n'
            '    assert True\n'
        )
    
    def _create_javascript_template(self, workspace_path: Path) -> None:
        """Create JavaScript/Node.js project template."""
        # Create package.json
        package_json = {
            "name": "workspace-project",
            "version": "1.0.0",
            "description": "Workspace project",
            "main": "src/index.js",
            "scripts": {
                "start": "node src/index.js",
                "test": "jest",
                "lint": "eslint src/"
            },
            "devDependencies": {
                "jest": "^29.0.0",
                "eslint": "^8.0.0"
            }
        }
        
        (workspace_path / 'package.json').write_text(
            json.dumps(package_json, indent=2)
        )
        
        # Create main file
        (workspace_path / 'src' / 'index.js').write_text(
            '#!/usr/bin/env node\n'
            '/**\n'
            ' * Main module for the workspace project.\n'
            ' */\n\n'
            'function main() {\n'
            '    console.log("Hello from workspace!");\n'
            '}\n\n'
            'if (require.main === module) {\n'
            '    main();\n'
            '}\n\n'
            'module.exports = { main };\n'
        )
        
        # Create test file
        (workspace_path / 'tests' / 'index.test.js').write_text(
            'const { main } = require("../src/index");\n\n'
            'describe("Main function", () => {\n'
            '    test("should run without errors", () => {\n'
            '        expect(() => main()).not.toThrow();\n'
            '    });\n'
            '});\n'
        )
    
    def _create_java_template(self, workspace_path: Path) -> None:
        """Create Java project template."""
        # Create Maven structure
        java_src = workspace_path / 'src' / 'main' / 'java' / 'com' / 'workspace'
        java_test = workspace_path / 'src' / 'test' / 'java' / 'com' / 'workspace'
        java_src.mkdir(parents=True)
        java_test.mkdir(parents=True)
        
        # Create pom.xml
        (workspace_path / 'pom.xml').write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<project xmlns="http://maven.apache.org/POM/4.0.0"\n'
            '         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
            '         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 \n'
            '         http://maven.apache.org/xsd/maven-4.0.0.xsd">\n'
            '    <modelVersion>4.0.0</modelVersion>\n'
            '    <groupId>com.workspace</groupId>\n'
            '    <artifactId>workspace-project</artifactId>\n'
            '    <version>1.0.0</version>\n'
            '    <properties>\n'
            '        <maven.compiler.source>11</maven.compiler.source>\n'
            '        <maven.compiler.target>11</maven.compiler.target>\n'
            '    </properties>\n'
            '</project>\n'
        )
        
        # Create main Java file
        (java_src / 'Main.java').write_text(
            'package com.workspace;\n\n'
            'public class Main {\n'
            '    public static void main(String[] args) {\n'
            '        System.out.println("Hello from workspace!");\n'
            '    }\n'
            '}\n'
        )
    
    def _create_cpp_template(self, workspace_path: Path) -> None:
        """Create C++ project template."""
        # Create CMakeLists.txt
        (workspace_path / 'CMakeLists.txt').write_text(
            'cmake_minimum_required(VERSION 3.10)\n'
            'project(WorkspaceProject)\n\n'
            'set(CMAKE_CXX_STANDARD 17)\n\n'
            'add_executable(main src/main.cpp)\n'
        )
        
        # Create main.cpp
        (workspace_path / 'src' / 'main.cpp').write_text(
            '#include <iostream>\n\n'
            'int main() {\n'
            '    std::cout << "Hello from workspace!" << std::endl;\n'
            '    return 0;\n'
            '}\n'
        )
    
    def _create_web_template(self, workspace_path: Path) -> None:
        """Create web project template."""
        # Create index.html
        (workspace_path / 'index.html').write_text(
            '<!DOCTYPE html>\n'
            '<html lang="en">\n'
            '<head>\n'
            '    <meta charset="UTF-8">\n'
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            '    <title>Workspace Project</title>\n'
            '    <link rel="stylesheet" href="styles.css">\n'
            '</head>\n'
            '<body>\n'
            '    <h1>Hello from workspace!</h1>\n'
            '    <script src="script.js"></script>\n'
            '</body>\n'
            '</html>\n'
        )
        
        # Create styles.css
        (workspace_path / 'styles.css').write_text(
            'body {\n'
            '    font-family: Arial, sans-serif;\n'
            '    margin: 0;\n'
            '    padding: 20px;\n'
            '    background-color: #f5f5f5;\n'
            '}\n\n'
            'h1 {\n'
            '    color: #333;\n'
            '    text-align: center;\n'
            '}\n'
        )
        
        # Create script.js
        (workspace_path / 'script.js').write_text(
            'document.addEventListener("DOMContentLoaded", function() {\n'
            '    console.log("Workspace loaded!");\n'
            '});\n'
        )
    
    def _create_basic_files(self, workspace_path: Path) -> None:
        """Create basic workspace files."""
        # Create README.md
        (workspace_path / 'README.md').write_text(
            '# Workspace Project\n\n'
            'This is a workspace for safe code execution.\n\n'
            '## Structure\n\n'
            '- `src/`: Source code\n'
            '- `tests/`: Test files\n'
            '- `docs/`: Documentation\n'
            '- `config/`: Configuration files\n'
            '- `temp/`: Temporary files\n'
        )
        
        # Create .gitignore
        (workspace_path / '.gitignore').write_text(
            '# Temporary files\n'
            'temp/\n'
            '*.tmp\n'
            '*.log\n\n'
            '# Build artifacts\n'
            'build/\n'
            'dist/\n'
            '*.o\n'
            '*.exe\n\n'
            '# IDE files\n'
            '.vscode/\n'
            '.idea/\n'
            '*.swp\n'
            '*.swo\n'
        )
    
    def _save_workspace_metadata(
        self, 
        workspace_path: Path, 
        workspace_info: Dict[str, Any]
    ) -> None:
        """Save workspace metadata to file."""
        metadata = {
            'id': workspace_info['id'],
            'created_at': workspace_info['created_at'],
            'template': workspace_info['template'],
            'config': workspace_info['config'],
            'status': workspace_info['status']
        }
        
        metadata_file = workspace_path / '.workspace_metadata.json'
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Set secure permissions
        os.chmod(metadata_file, 0o600)
    
    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workspace information.
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            Workspace information or None if not found
        """
        return self.active_workspaces.get(workspace_id)
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all active workspaces.
        
        Returns:
            List of workspace information dictionaries
        """
        workspaces = []
        for workspace_info in self.active_workspaces.values():
            workspaces.append({
                'id': workspace_info['id'],
                'path': workspace_info['path'],
                'created_at': workspace_info['created_at'],
                'template': workspace_info['template'],
                'status': workspace_info['status']
            })
        return workspaces
    
    def backup_workspace(
        self, 
        workspace_id: str, 
        backup_path: Optional[str] = None
    ) -> str:
        """
        Create a backup of a workspace.
        
        Args:
            workspace_id: ID of the workspace to backup
            backup_path: Optional custom backup path
            
        Returns:
            Path to the backup file
            
        Raises:
            ExecutionError: If backup fails
        """
        try:
            workspace_info = self.active_workspaces.get(workspace_id)
            if not workspace_info:
                raise ExecutionError(f"Workspace not found: {workspace_id}")
            
            workspace_path = Path(workspace_info['path'])
            if not workspace_path.exists():
                raise ExecutionError(f"Workspace path does not exist: {workspace_path}")
            
            # Generate backup filename
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_filename = f"{workspace_id}_backup_{timestamp}.tar.gz"
                backup_path = str(self.base_path / backup_filename)
            
            # Create tar.gz backup
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(workspace_path, arcname=workspace_id)
            
            return backup_path
            
        except Exception as e:
            if isinstance(e, ExecutionError):
                raise
            raise ExecutionError(f"Failed to backup workspace {workspace_id}: {e}")
    
    def restore_workspace(
        self, 
        backup_path: str, 
        workspace_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Restore a workspace from backup.
        
        Args:
            backup_path: Path to the backup file
            workspace_id: Optional custom workspace ID
            
        Returns:
            Restored workspace information
            
        Raises:
            ExecutionError: If restore fails
        """
        try:
            backup_file = Path(backup_path)
            if not backup_file.exists():
                raise ExecutionError(f"Backup file does not exist: {backup_path}")
            
            # Generate workspace ID if not provided
            if not workspace_id:
                workspace_id = f"restored_{uuid.uuid4().hex[:8]}"
            
            workspace_path = self.base_path / workspace_id
            
            # Check if workspace already exists
            if workspace_path.exists():
                raise ExecutionError(f"Workspace already exists: {workspace_id}")
            
            # Extract backup
            with tarfile.open(backup_path, 'r:gz') as tar:
                tar.extractall(self.base_path)
            
            # Load workspace metadata if available
            metadata_file = workspace_path / '.workspace_metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            # Create MCP client for restored workspace
            mcp_client = MCPClient(str(workspace_path))
            
            # Update workspace information
            workspace_info = {
                'id': workspace_id,
                'path': str(workspace_path),
                'created_at': datetime.now().isoformat(),
                'template': metadata.get('template'),
                'config': metadata.get('config', {}),
                'mcp_client': mcp_client,
                'status': 'active',
                'restored_from': backup_path
            }
            
            self.active_workspaces[workspace_id] = workspace_info
            
            return {
                'workspace_id': workspace_id,
                'path': str(workspace_path),
                'status': 'restored',
                'restored_from': backup_path
            }
            
        except Exception as e:
            if isinstance(e, ExecutionError):
                raise
            raise ExecutionError(f"Failed to restore workspace: {e}")
    
    def cleanup_workspace(self, workspace_id: str) -> bool:
        """
        Clean up and remove a workspace.
        
        Args:
            workspace_id: ID of the workspace to cleanup
            
        Returns:
            True if successful
            
        Raises:
            ExecutionError: If cleanup fails
        """
        try:
            workspace_info = self.active_workspaces.get(workspace_id)
            if not workspace_info:
                raise ExecutionError(f"Workspace not found: {workspace_id}")
            
            workspace_path = Path(workspace_info['path'])
            
            # Cleanup MCP client
            if 'mcp_client' in workspace_info:
                workspace_info['mcp_client'].cleanup()
            
            # Remove workspace directory
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
            
            # Remove from active workspaces
            del self.active_workspaces[workspace_id]
            
            return True
            
        except Exception as e:
            if isinstance(e, ExecutionError):
                raise
            raise ExecutionError(f"Failed to cleanup workspace {workspace_id}: {e}")
    
    def cleanup_all_workspaces(self) -> Dict[str, bool]:
        """
        Clean up all active workspaces.
        
        Returns:
            Dictionary mapping workspace IDs to cleanup success status
        """
        results = {}
        workspace_ids = list(self.active_workspaces.keys())
        
        for workspace_id in workspace_ids:
            try:
                results[workspace_id] = self.cleanup_workspace(workspace_id)
            except Exception as e:
                results[workspace_id] = False
                print(f"Warning: Failed to cleanup workspace {workspace_id}: {e}")
        
        return results
