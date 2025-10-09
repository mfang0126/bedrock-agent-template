"""
File Operations Tool for Coding Agent

Provides secure file operations within workspace boundaries with comprehensive
path validation and safety checks.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileOperationError(Exception):
    """Raised when file operations fail"""
    pass


class SecurityError(Exception):
    """Raised when security validation fails"""
    pass


class FileOperations:
    """
    Secure file operations manager for coding agent workspace
    """
    
    def __init__(self, workspace_root: str):
        """
        Initialize file operations with workspace root
        
        Args:
            workspace_root: Root directory for all file operations
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
        self.allowed_extensions = {
            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.hpp',
            '.html', '.css', '.json', '.yaml', '.yml', '.xml', '.md',
            '.txt', '.sh', '.bat', '.ps1', '.sql', '.go', '.rs', '.rb',
            '.php', '.swift', '.kt', '.scala', '.r', '.m', '.dockerfile'
        }
        self.forbidden_paths = {
            '/etc', '/usr', '/bin', '/sbin', '/root', '/home',
            'C:\\Windows', 'C:\\Program Files', 'C:\\System32'
        }
        
    def _validate_path(self, file_path: Union[str, Path]) -> Path:
        """
        Validate that path is within workspace and safe
        
        Args:
            file_path: Path to validate
            
        Returns:
            Resolved path within workspace
            
        Raises:
            SecurityError: If path is unsafe
        """
        try:
            # If path is relative, make it relative to workspace root
            path = Path(file_path)
            if not path.is_absolute():
                path = self.workspace_root / path
            path = path.resolve()
            
            # Check if path is within workspace
            try:
                path.relative_to(self.workspace_root)
            except ValueError:
                raise SecurityError(f"Path {path} is outside workspace {self.workspace_root}")
            
            # Check for forbidden path components
            path_str = str(path)
            for forbidden in self.forbidden_paths:
                if forbidden in path_str:
                    raise SecurityError(f"Path contains forbidden component: {forbidden}")
            
            # Check for path traversal attempts
            if '..' in path.parts:
                raise SecurityError("Path traversal detected")
            
            return path
            
        except Exception as e:
            if isinstance(e, SecurityError):
                raise
            raise SecurityError(f"Invalid path: {e}")
    
    def _validate_file_extension(self, file_path: Path) -> bool:
        """
        Check if file extension is allowed
        
        Args:
            file_path: Path to check
            
        Returns:
            True if extension is allowed
        """
        return file_path.suffix.lower() in self.allowed_extensions or file_path.suffix == ''
    
    def _check_file_size(self, file_path: Path) -> None:
        """
        Check if file size is within limits
        
        Args:
            file_path: Path to check
            
        Raises:
            FileOperationError: If file is too large
        """
        if file_path.exists() and file_path.stat().st_size > self.max_file_size:
            raise FileOperationError(f"File {file_path} exceeds size limit of {self.max_file_size} bytes")
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Read file content safely
        
        Args:
            file_path: Path to file to read
            encoding: File encoding (default: utf-8)
            
        Returns:
            Dictionary with file content and metadata
            
        Raises:
            FileOperationError: If file cannot be read
            SecurityError: If path is unsafe
        """
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                raise FileOperationError(f"File {path} does not exist")
            
            if not path.is_file():
                raise FileOperationError(f"Path {path} is not a file")
            
            self._check_file_size(path)
            
            # Read file content
            try:
                with open(path, 'r', encoding=encoding) as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try binary mode for non-text files
                with open(path, 'rb') as f:
                    content = f.read()
                    content = f"<binary file: {len(content)} bytes>"
            
            # Get file metadata
            stat = path.stat()
            
            return {
                'success': True,
                'content': content,
                'path': str(path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'encoding': encoding,
                'lines': len(content.splitlines()) if isinstance(content, str) else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'path': file_path
            }
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                   create_dirs: bool = True) -> Dict[str, Any]:
        """
        Write content to file safely
        
        Args:
            file_path: Path to file to write
            content: Content to write
            encoding: File encoding (default: utf-8)
            create_dirs: Whether to create parent directories
            
        Returns:
            Dictionary with operation result
            
        Raises:
            FileOperationError: If file cannot be written
            SecurityError: If path is unsafe
        """
        try:
            path = self._validate_path(file_path)
            
            if not self._validate_file_extension(path):
                raise SecurityError(f"File extension {path.suffix} not allowed")
            
            # Check content size
            content_size = len(content.encode(encoding))
            if content_size > self.max_file_size:
                raise FileOperationError(f"Content size {content_size} exceeds limit of {self.max_file_size} bytes")
            
            # Create parent directories if needed
            if create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if file exists
            backup_path = None
            if path.exists():
                backup_path = path.with_suffix(path.suffix + '.backup')
                shutil.copy2(path, backup_path)
            
            # Write file
            with open(path, 'w', encoding=encoding) as f:
                f.write(content)
            
            # Get file metadata
            stat = path.stat()
            
            result = {
                'success': True,
                'path': str(path),
                'size': stat.st_size,
                'lines': len(content.splitlines()),
                'encoding': encoding,
                'created_dirs': create_dirs and not path.parent.exists(),
                'backup_created': backup_path is not None
            }
            
            if backup_path:
                result['backup_path'] = str(backup_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'path': file_path
            }
    
    def modify_file(self, file_path: str, modifications: List[Dict[str, Any]], 
                    encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Apply modifications to file (insert, replace, delete lines)
        
        Args:
            file_path: Path to file to modify
            modifications: List of modification operations
            encoding: File encoding
            
        Returns:
            Dictionary with operation result
            
        Modification format:
        {
            'operation': 'insert|replace|delete',
            'line': line_number (1-based),
            'content': content_to_insert_or_replace (for insert/replace),
            'count': number_of_lines_to_delete (for delete)
        }
        """
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                raise FileOperationError(f"File {path} does not exist")
            
            # Read current content
            read_result = self.read_file(str(path), encoding)
            if not read_result['success']:
                return read_result
            
            lines = read_result['content'].splitlines()
            original_line_count = len(lines)
            
            # Sort modifications by line number (descending) to avoid index issues
            modifications = sorted(modifications, key=lambda x: x.get('line', 0), reverse=True)
            
            # Apply modifications
            applied_modifications = []
            for mod in modifications:
                operation = mod.get('operation')
                line_num = mod.get('line', 1) - 1  # Convert to 0-based
                
                if line_num < 0:
                    continue
                
                if operation == 'insert':
                    content = mod.get('content', '')
                    if line_num > len(lines):
                        line_num = len(lines)
                    lines.insert(line_num, content)
                    applied_modifications.append(f"Inserted at line {line_num + 1}")
                    
                elif operation == 'replace':
                    content = mod.get('content', '')
                    if line_num < len(lines):
                        lines[line_num] = content
                        applied_modifications.append(f"Replaced line {line_num + 1}")
                    
                elif operation == 'delete':
                    count = mod.get('count', 1)
                    if line_num < len(lines):
                        end_line = min(line_num + count, len(lines))
                        del lines[line_num:end_line]
                        applied_modifications.append(f"Deleted {end_line - line_num} lines from {line_num + 1}")
            
            # Write modified content
            modified_content = '\n'.join(lines)
            write_result = self.write_file(str(path), modified_content, encoding)
            
            if write_result['success']:
                write_result.update({
                    'original_lines': original_line_count,
                    'modified_lines': len(lines),
                    'modifications_applied': applied_modifications
                })
            
            return write_result
            
        except Exception as e:
            logger.error(f"Failed to modify file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'path': file_path
            }
    
    def list_files(self, directory: str = '', pattern: str = '*', 
                   recursive: bool = False) -> Dict[str, Any]:
        """
        List files in directory with optional pattern matching
        
        Args:
            directory: Directory to list (relative to workspace)
            pattern: File pattern to match
            recursive: Whether to search recursively
            
        Returns:
            Dictionary with file list and metadata
        """
        try:
            if directory:
                dir_path = self._validate_path(directory)
            else:
                dir_path = self.workspace_root
            
            if not dir_path.exists():
                raise FileOperationError(f"Directory {dir_path} does not exist")
            
            if not dir_path.is_dir():
                raise FileOperationError(f"Path {dir_path} is not a directory")
            
            # Get file list
            files = []
            directories = []
            
            if recursive:
                items = dir_path.rglob(pattern)
            else:
                items = dir_path.glob(pattern)
            
            for item in items:
                try:
                    # Skip if outside workspace
                    item.relative_to(self.workspace_root)
                    
                    stat = item.stat()
                    item_info = {
                        'name': item.name,
                        'path': str(item.relative_to(self.workspace_root)),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'is_file': item.is_file(),
                        'is_dir': item.is_dir()
                    }
                    
                    if item.is_file():
                        item_info['extension'] = item.suffix
                        files.append(item_info)
                    elif item.is_dir():
                        directories.append(item_info)
                        
                except ValueError:
                    # Skip items outside workspace
                    continue
            
            return {
                'success': True,
                'directory': str(dir_path.relative_to(self.workspace_root)),
                'pattern': pattern,
                'recursive': recursive,
                'files': sorted(files, key=lambda x: x['name']),
                'directories': sorted(directories, key=lambda x: x['name']),
                'total_files': len(files),
                'total_directories': len(directories)
            }
            
        except Exception as e:
            logger.error(f"Failed to list files in {directory}: {e}")
            return {
                'success': False,
                'error': str(e),
                'directory': directory
            }
    
    def copy_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy file within workspace
        
        Args:
            source: Source file path
            destination: Destination file path
            
        Returns:
            Dictionary with operation result
        """
        try:
            src_path = self._validate_path(source)
            dst_path = self._validate_path(destination)
            
            if not src_path.exists():
                raise FileOperationError(f"Source file {src_path} does not exist")
            
            if not src_path.is_file():
                raise FileOperationError(f"Source {src_path} is not a file")
            
            self._check_file_size(src_path)
            
            if not self._validate_file_extension(dst_path):
                raise SecurityError(f"Destination file extension {dst_path.suffix} not allowed")
            
            # Create destination directory if needed
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(src_path, dst_path)
            
            # Get destination file metadata
            stat = dst_path.stat()
            
            return {
                'success': True,
                'source': str(src_path.relative_to(self.workspace_root)),
                'destination': str(dst_path.relative_to(self.workspace_root)),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to copy file from {source} to {destination}: {e}")
            return {
                'success': False,
                'error': str(e),
                'source': source,
                'destination': destination
            }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        Delete file safely
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            Dictionary with operation result
        """
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                return {
                    'success': True,
                    'message': f"File {path} does not exist (already deleted)",
                    'path': str(path.relative_to(self.workspace_root))
                }
            
            if not path.is_file():
                raise FileOperationError(f"Path {path} is not a file")
            
            # Get file info before deletion
            stat = path.stat()
            file_info = {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
            # Delete file
            path.unlink()
            
            return {
                'success': True,
                'path': str(path.relative_to(self.workspace_root)),
                'deleted_file_info': file_info
            }
            
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'path': file_path
            }
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed file information
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        try:
            path = self._validate_path(file_path)
            
            if not path.exists():
                raise FileOperationError(f"File {path} does not exist")
            
            stat = path.stat()
            
            info = {
                'success': True,
                'path': str(path.relative_to(self.workspace_root)),
                'name': path.name,
                'extension': path.suffix,
                'size': stat.st_size,
                'size_human': self._format_size(stat.st_size),
                'is_file': path.is_file(),
                'is_dir': path.is_dir(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:],
                'extension_allowed': self._validate_file_extension(path)
            }
            
            # Add line count for text files
            if path.is_file() and self._validate_file_extension(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        info['lines'] = len(content.splitlines())
                        info['characters'] = len(content)
                except:
                    info['lines'] = 'unknown'
                    info['characters'] = 'unknown'
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get file info for {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'path': file_path
            }
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"