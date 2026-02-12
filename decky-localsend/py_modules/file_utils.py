"""
File utilities for file operations.
Note: This module does NOT use decky directly. Logging is done via callbacks.
"""

import os
import glob
import time
import json
from typing import Dict, List, Any, Callable, Optional


def list_folder_files(
    folder_path: str,
    logger: Callable[[str], None] = None
) -> Dict[str, Any]:
    """
    List all files in a folder recursively.
    
    Args:
        folder_path: Path to the folder
        logger: Optional logging callback
    
    Returns:
        Dictionary with success status and file list
    """
    if not folder_path or not os.path.isdir(folder_path):
        return {"success": False, "error": "Invalid folder path", "files": []}
    
    try:
        files = []
        base_name = os.path.basename(os.path.normpath(folder_path))
        
        for root, _, filenames in os.walk(folder_path):
            for filename in filenames:
                abs_path = os.path.join(root, filename)
                rel_path = os.path.relpath(abs_path, folder_path)
                # Display path includes the folder name for clarity
                display_path = os.path.join(base_name, rel_path)
                
                files.append({
                    "path": abs_path,
                    "displayPath": display_path,
                    "fileName": filename,
                })
        
        return {
            "success": True,
            "files": files,
            "folderName": base_name,
            "count": len(files)
        }
    except Exception as e:
        if logger:
            logger(f"Failed to list folder files: {e}")
        return {"success": False, "error": str(e), "files": []}


def load_receive_history(
    history_path: str,
    logger: Callable[[str], None] = None
) -> List[Dict[str, Any]]:
    """
    Load file receive history from disk.
    
    Args:
        history_path: Path to the history file
        logger: Optional logging callback
    
    Returns:
        List of history entries
    """
    try:
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        
        # Create empty receive history file if it doesn't exist
        if not os.path.exists(history_path):
            if logger:
                logger(f"Receive history file not found, creating empty: {history_path}")
            with open(history_path, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return []
        
        # Load existing receive history
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        
        if logger:
            logger(f"Loaded {len(history)} receive history records")
        return history
    except Exception as e:
        if logger:
            logger(f"Failed to load receive history: {e}")
        return []


def save_receive_history(
    history_path: str,
    history: List[Dict[str, Any]],
    logger: Callable[[str], None] = None
) -> bool:
    """
    Save receive history to disk.
    
    Args:
        history_path: Path to the history file
        history: List of history entries
        logger: Optional logging callback
    
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(os.path.dirname(history_path), exist_ok=True)
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        if logger:
            logger(f"Failed to save receive history: {e}")
        return False


def write_temp_text_file(
    base_dir: str,
    text_content: str,
    file_name: str,
    logger: Callable[[str], None] = None
) -> Dict[str, Any]:
    """
    Write text content to a temp file for share session (e.g. Download API).
    Uses a unique suffix to avoid collisions.

    Args:
        base_dir: Base directory for temp files (e.g. upload_dir/share_temp)
        text_content: Text content to write
        file_name: Desired file name (e.g. "text-123.txt")
        logger: Optional logging callback

    Returns:
        { success: bool, path?: str, error?: str }
    """
    try:
        import uuid
        os.makedirs(base_dir, exist_ok=True)
        base, ext = os.path.splitext(file_name)
        if not ext:
            ext = ".txt"
        unique_name = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(base_dir, unique_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
        return {"success": True, "path": file_path}
    except Exception as e:
        if logger:
            logger(f"Failed to write temp text file: {e}")
        return {"success": False, "error": str(e)}


def create_receive_history_entry(
    folder_path: str,
    files: List[str],
    title: str = "",
    is_text: bool = False,
    text_content: str = "",
    current_count: int = 0,
    total_files: Optional[int] = None,
    success_files: Optional[int] = None,
    failed_files: Optional[int] = None,
    failed_file_ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Create a new receive history entry.
    
    Args:
        folder_path: Path to the received files folder
        files: List of file names (may be truncated)
        title: Optional title
        is_text: Whether this is a text-only entry
        text_content: Text content (for text entries)
        current_count: Current history count (for generating ID)
        total_files: Actual total file count (overrides fileCount when set)
        success_files: Number of successfully received files
        failed_files: Number of failed files
        failed_file_ids: List of failed file IDs
    
    Returns:
        History entry dictionary
    """
    file_count = total_files if total_files is not None else len(files)
    entry: Dict[str, Any] = {
        "id": f"recv-{int(time.time() * 1000)}-{current_count}",
        "timestamp": time.time(),
        "title": title or ("Text Received" if is_text else "File Received"),
        "folderPath": folder_path,
        "fileCount": file_count,
        "files": files,
        "isText": is_text,
    }
    if total_files is not None:
        entry["totalFiles"] = total_files
    if success_files is not None:
        entry["successFiles"] = success_files
    if failed_files is not None:
        entry["failedFiles"] = failed_files
    if failed_file_ids is not None:
        entry["failedFileIds"] = failed_file_ids
    
    # Add text content preview for text items (truncate if too long)
    if is_text and text_content:
        entry["textPreview"] = text_content[:200] + ("..." if len(text_content) > 200 else "")
        entry["textContent"] = text_content
    
    return entry
