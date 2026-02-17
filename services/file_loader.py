"""
Safe file loader for ai_sandbox files
Provides secure access to files under ai_sandbox/ with path traversal protection
"""

import os
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class FileLoaderError(Exception):
    """Custom exception for file loading errors"""
    pass

MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB limit
ALLOWED_DIRECTORIES = {
    "repo_snapshots": "../ai_sandbox/repo_snapshots/",
    "pilot_data_exports": "../ai_sandbox/pilot_data_exports/", 
    "outputs": "../ai_sandbox/outputs/"
}

def load_file(directory_type: str, file_key: str) -> Optional[str]:
    """
    Safely load a file from ai_sandbox directories
    
    Args:
        directory_type: One of 'repo_snapshots', 'pilot_data_exports', 'outputs'
        file_key: Filename or path within the directory
        
    Returns:
        File contents as string, or None if file doesn't exist
        
    Raises:
        FileLoaderError: If path is invalid, file too large, or other security issues
    """
    
    # Validate directory type
    if directory_type not in ALLOWED_DIRECTORIES:
        raise FileLoaderError(f"Invalid directory type: {directory_type}")
    
    # Prevent path traversal attacks
    if ".." in file_key or "/" in file_key or "\\" in file_key:
        raise FileLoaderError("Invalid file key: path traversal not allowed")
    
    # Build safe file path
    base_dir = ALLOWED_DIRECTORIES[directory_type]
    file_path = Path(base_dir) / file_key
    
    # Resolve path and ensure it's still within allowed directory
    try:
        resolved_path = file_path.resolve()
        allowed_base = Path(base_dir).resolve()
        
        # Check that resolved path is within allowed directory
        if not str(resolved_path).startswith(str(allowed_base)):
            raise FileLoaderError("Path traversal attempt detected")
            
    except Exception as e:
        logger.error(f"Path resolution error: {str(e)}")
        raise FileLoaderError("Invalid file path")
    
    # Check if file exists
    if not resolved_path.exists():
        logger.info(f"File not found: {resolved_path}")
        return None
    
    # Check if it's actually a file
    if not resolved_path.is_file():
        raise FileLoaderError("Path is not a file")
    
    # Check file size
    try:
        file_size = resolved_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise FileLoaderError(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")
    except Exception as e:
        logger.error(f"Error checking file size: {str(e)}")
        raise FileLoaderError("Error accessing file")
    
    # Read file content
    try:
        with open(resolved_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        logger.info(f"Successfully loaded file: {resolved_path} ({len(content)} characters)")
        return content
        
    except UnicodeDecodeError:
        raise FileLoaderError("File is not valid UTF-8 text")
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise FileLoaderError("Error reading file content")

def load_multiple_files(file_refs: dict) -> dict:
    """
    Load multiple files based on parameter references
    
    Args:
        file_refs: Dict with keys like 'repo_snapshot_key', 'data_export_key', 'notes_key'
                  and values as file keys
    
    Returns:
        Dict with loaded file contents, keyed by reference type
    """
    loaded_files = {}
    
    # Map parameter names to directory types
    param_to_dir = {
        "repo_snapshot_key": "repo_snapshots",
        "data_export_key": "pilot_data_exports", 
        "notes_key": "outputs"
    }
    
    for param_name, file_key in file_refs.items():
        if param_name in param_to_dir and file_key:
            try:
                content = load_file(param_to_dir[param_name], file_key)
                if content:
                    loaded_files[param_name] = content
                    logger.info(f"Loaded {param_name}: {file_key}")
                else:
                    logger.info(f"File not found for {param_name}: {file_key}")
            except FileLoaderError as e:
                logger.warning(f"Failed to load {param_name} ({file_key}): {str(e)}")
                # Continue processing other files rather than failing completely
    
    return loaded_files