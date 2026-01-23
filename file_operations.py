# file_operations.py - File system operations for decky-send
#
# This module provides file system CRUD operations including:
# - Directory listing
# - File read/write
# - File/directory creation
# - Copy, move, delete operations
# - File download
# - Text content management

import os
import shutil
import subprocess
from pathlib import Path
from aiohttp import web
# NOTE: Direct import - Decky adds py_modules/ to sys.path
import config

# =============================================================================
# System Detection Helpers
# =============================================================================

def _find_sdcard_mount():
    """Find the SD card mount path on Steam Deck.

    Returns:
        str | None: Mount path if found, otherwise None
    """
    candidates = []

    def add_candidate(path):
        if path and os.path.isdir(path) and path not in candidates:
            candidates.append(path)

    # Common direct mount points
    add_candidate("/run/media/mmcblk0p1")
    add_candidate("/media/mmcblk0p1")

    # SteamOS user mount root
    deck_media_root = "/run/media/deck"
    if os.path.isdir(deck_media_root):
        try:
            for name in sorted(os.listdir(deck_media_root)):
                add_candidate(os.path.join(deck_media_root, name))
        except Exception as e:
            config.logger.debug(f"Failed to list {deck_media_root}: {e}")

    # Fallback: other mounts under /run/media
    media_root = "/run/media"
    if os.path.isdir(media_root):
        try:
            for name in sorted(os.listdir(media_root)):
                if name == "deck":
                    continue
                add_candidate(os.path.join(media_root, name))
        except Exception as e:
            config.logger.debug(f"Failed to list {media_root}: {e}")

    # Prefer actual mount points
    for path in candidates:
        try:
            if os.path.ismount(path):
                return path
        except Exception:
            continue

    # Fallback: look for common Steam library markers
    for path in candidates:
        try:
            if os.path.isdir(os.path.join(path, "steamapps")) or os.path.isdir(os.path.join(path, "SteamLibrary")):
                return path
        except Exception:
            continue

    return candidates[0] if candidates else None

# =============================================================================
# HTTP API Handlers (for aiohttp routes)
# =============================================================================

async def get_file_list(request):
    """Get list of files in a directory
    
    POST /api/files/list
    Body: {"path": "/some/path"}
    """
    try:
        # Get path from request
        data = await request.json()
        path = data.get('path', str(Path.home()))
        
        # Validate path to prevent directory traversal
        path = os.path.abspath(path)
        
        # Check if path exists
        if not os.path.exists(path):
            return web.json_response({"status": "error", "message": "Path not found"}, status=404)
        
        # Check if path is a directory
        if not os.path.isdir(path):
            return web.json_response({"status": "error", "message": "Path is not a directory"}, status=400)
        
        # Get file list
        files = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                # Check if item still exists (might have been deleted during traversal)
                if not os.path.exists(item_path):
                    continue
                
                is_dir = os.path.isdir(item_path)
                size = os.path.getsize(item_path) if not is_dir else 0
                mtime = os.path.getmtime(item_path)
                
                files.append({
                    "name": item,
                    "path": item_path,
                    "is_dir": is_dir,
                    "size": size,
                    "mtime": mtime
                })
            except Exception as e:
                # Skip files that can't be accessed (e.g., permission errors, special files)
                config.logger.debug(f"Skipping file {item_path}: {e}")
                continue
        
        # Sort files: directories first, then by name
        files.sort(key=lambda x: (not x['is_dir'], x['name']))
        
        return web.json_response({
            "status": "success",
            "files": files,
            "current_path": path
        })
    except Exception as e:
        config.logger.error(f"Failed to get file list: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def read_file(request):
    """Read file content
    
    POST /api/files/read
    Body: {"path": "/some/file.txt"}
    """
    try:
        # Get path from request
        data = await request.json()
        path = data.get('path')
        
        if not path:
            return web.json_response({"status": "error", "message": "Path is required"}, status=400)
        
        # Validate path
        path = os.path.abspath(path)
        
        # Check if path exists and is a file
        if not os.path.exists(path):
            return web.json_response({"status": "error", "message": "File not found"}, status=404)
        
        if os.path.isdir(path):
            return web.json_response({"status": "error", "message": "Path is a directory"}, status=400)
        
        # Read file content
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return web.json_response({
            "status": "success",
            "content": content,
            "path": path
        })
    except UnicodeDecodeError:
        return web.json_response({"status": "error", "message": "Cannot read binary file"}, status=400)
    except Exception as e:
        config.logger.error(f"Failed to read file: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def write_file(request):
    """Write content to file
    
    POST /api/files/write
    Body: {"path": "/some/file.txt", "content": "file content"}
    """
    try:
        # Get data from request
        data = await request.json()
        path = data.get('path')
        content = data.get('content')
        
        if not path:
            return web.json_response({"status": "error", "message": "Path is required"}, status=400)
        
        # Validate path
        path = os.path.abspath(path)
        
        # Write content to file
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return web.json_response({
            "status": "success",
            "message": "File written successfully",
            "path": path
        })
    except Exception as e:
        config.logger.error(f"Failed to write file: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def create_file(request):
    """Create a new file
    
    POST /api/files/create
    Body: {"path": "/some/dir", "filename": "newfile.txt"}
    """
    try:
        # Get data from request
        data = await request.json()
        path = data.get('path')
        filename = data.get('filename')
        
        if not path or not filename:
            return web.json_response({"status": "error", "message": "Path and filename are required"}, status=400)
        
        # Validate path
        path = os.path.abspath(path)
        file_path = os.path.join(path, filename)
        
        # Check if file already exists
        if os.path.exists(file_path):
            return web.json_response({"status": "error", "message": "File already exists"}, status=400)
        
        # Create file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('')
        
        return web.json_response({
            "status": "success",
            "message": "File created successfully",
            "path": file_path
        })
    except Exception as e:
        config.logger.error(f"Failed to create file: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def create_directory(request):
    """Create a new directory
    
    POST /api/files/create-dir
    Body: {"path": "/some/dir", "dirname": "newdir"}
    """
    try:
        # Get data from request
        data = await request.json()
        path = data.get('path')
        dirname = data.get('dirname')
        
        if not path or not dirname:
            return web.json_response({"status": "error", "message": "Path and dirname are required"}, status=400)
        
        # Validate path
        path = os.path.abspath(path)
        dir_path = os.path.join(path, dirname)
        
        # Check if directory already exists
        if os.path.exists(dir_path):
            return web.json_response({"status": "error", "message": "Directory already exists"}, status=400)
        
        # Create directory
        os.makedirs(dir_path, exist_ok=True)
        
        return web.json_response({
            "status": "success",
            "message": "Directory created successfully",
            "path": dir_path
        })
    except Exception as e:
        config.logger.error(f"Failed to create directory: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def copy_file(request):
    """Copy file or directory
    
    POST /api/files/copy
    Body: {"source": "/source/path", "destination": "/dest/path"}
    """
    try:
        # Get data from request
        data = await request.json()
        source = data.get('source')
        destination = data.get('destination')
        
        if not source or not destination:
            return web.json_response({"status": "error", "message": "Source and destination are required"}, status=400)
        
        # Validate paths
        source = os.path.abspath(source)
        destination = os.path.abspath(destination)
        
        # Check if source exists
        if not os.path.exists(source):
            return web.json_response({"status": "error", "message": "Source not found"}, status=404)
        
        # Check if destination directory exists
        dest_dir = os.path.dirname(destination)
        if not os.path.exists(dest_dir):
            return web.json_response({"status": "error", "message": "Destination directory not found"}, status=404)
        
        # Copy file or directory
        if os.path.isdir(source):
            # Copy directory recursively
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            # Copy file
            shutil.copy2(source, destination)
        
        return web.json_response({
            "status": "success",
            "message": "File copied successfully",
            "source": source,
            "destination": destination
        })
    except Exception as e:
        config.logger.error(f"Failed to copy file: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def move_file(request):
    """Move file or directory
    
    POST /api/files/move
    Body: {"source": "/source/path", "destination": "/dest/path"}
    """
    try:
        # Get data from request
        data = await request.json()
        source = data.get('source')
        destination = data.get('destination')
        
        if not source or not destination:
            return web.json_response({"status": "error", "message": "Source and destination are required"}, status=400)
        
        # Validate paths
        source = os.path.abspath(source)
        destination = os.path.abspath(destination)
        
        # Check if source exists
        if not os.path.exists(source):
            return web.json_response({"status": "error", "message": "Source not found"}, status=404)
        
        # Check if destination directory exists
        dest_dir = os.path.dirname(destination)
        if not os.path.exists(dest_dir):
            return web.json_response({"status": "error", "message": "Destination directory not found"}, status=404)
        
        # Move file or directory
        shutil.move(source, destination)
        
        return web.json_response({
            "status": "success",
            "message": "File moved successfully",
            "source": source,
            "destination": destination
        })
    except Exception as e:
        config.logger.error(f"Failed to move file: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def delete_file(request):
    """Delete file or directory
    
    POST /api/files/delete
    Body: {"path": "/some/path"}
    """
    try:
        # Get data from request
        data = await request.json()
        path = data.get('path')
        
        if not path:
            return web.json_response({"status": "error", "message": "Path is required"}, status=400)
        
        # Validate path
        path = os.path.abspath(path)
        
        # Check if path exists
        if not os.path.exists(path):
            return web.json_response({"status": "error", "message": "Path not found"}, status=404)
        
        # Delete file or directory
        if os.path.isdir(path):
            # Delete directory recursively
            shutil.rmtree(path)
        else:
            # Delete file
            os.remove(path)
        
        return web.json_response({
            "status": "success",
            "message": "File deleted successfully",
            "path": path
        })
    except Exception as e:
        config.logger.error(f"Failed to delete file: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def download_file(request):
    """Download file
    
    GET /api/files/download?path=/some/file.txt
    """
    try:
        # Get path from query parameters
        path = request.query.get('path')
        
        if not path:
            return web.json_response({"status": "error", "message": "Path is required"}, status=400)
        
        # Validate path
        path = os.path.abspath(path)
        
        # Check if path exists
        if not os.path.exists(path):
            return web.json_response({"status": "error", "message": "File not found"}, status=404)
        
        # Check if path is a file
        if not os.path.isfile(path):
            return web.json_response({"status": "error", "message": "Path is not a file"}, status=400)
        
        # Get file name for download
        filename = os.path.basename(path)
        
        # Open file and return as stream
        return web.FileResponse(
            path,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Content-Type': 'application/octet-stream'
            }
        )
    except Exception as e:
        config.logger.error(f"Failed to download file: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def get_sdcard_info(request):
    """Get SD card mount information
    
    GET /api/system/sdcard
    """
    try:
        mount_path = _find_sdcard_mount()
        if mount_path:
            return web.json_response({
                "status": "success",
                "mounted": True,
                "path": mount_path
            })
        return web.json_response({
            "status": "success",
            "mounted": False,
            "path": ""
        })
    except Exception as e:
        config.logger.error(f"Failed to detect SD card mount: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


async def add_file_to_steam(request):
    """Add a file as a non-Steam game to Steam using steamos-add-to-steam command
    
    POST /api/files/add-to-steam
    Body: {"path": "/path/to/executable"}
    """
    try:
        # Get path from request
        data = await request.json()
        file_path = data.get('path')
        
        if not file_path:
            return web.json_response({"status": "error", "message": "File path is required"}, status=400)
        
        config.logger.info(f"Adding file to Steam: {file_path}")
        
        # Execute the steamos-add-to-steam command with -ui flag
        # To avoid symbol lookup errors in SteamOS environment, use a minimal environment
        cmd = ["steamos-add-to-steam", "-ui", file_path]
        
        # Create a minimal, clean environment to avoid readline/library conflicts
        minimal_env = {
            'PATH': '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
            'HOME': os.environ.get('HOME', ''),
            'USER': os.environ.get('USER', ''),
            'LANG': os.environ.get('LANG', 'en_US.UTF-8'),
            'LC_ALL': os.environ.get('LC_ALL', 'en_US.UTF-8'),
        }
        
        result = subprocess.run(cmd, capture_output=True, text=True, env=minimal_env)
        
        if result.returncode == 0:
            config.logger.info(f"Successfully added to Steam: {file_path}")
            return web.json_response({
                "status": "success",
                "message": f"Successfully added {os.path.basename(file_path)} to Steam"
            })
        else:
            config.logger.error(f"Failed to add to Steam: {result.stderr}")
            return web.json_response({
                "status": "error",
                "message": f"Failed to add to Steam: {result.stderr}"
            }, status=500)
            
    except subprocess.SubprocessError as e:
        config.logger.error(f"Subprocess error when adding to Steam: {e}")
        return web.json_response({"status": "error", "message": f"Subprocess error: {str(e)}"}, status=500)
    except Exception as e:
        config.logger.error(f"Error adding to Steam: {e}")
        return web.json_response({"status": "error", "message": str(e)}, status=500)


# =============================================================================
# Plugin API Methods (called via callPluginMethod)
# =============================================================================

async def get_text_content(plugin) -> dict:
    """Get the current text content from the file
    
    Args:
        plugin: Plugin instance to access text_file_path
        
    Returns:
        dict with status and content
    """
    try:
        # Check if text file exists
        if os.path.exists(plugin.text_file_path):
            with open(plugin.text_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return {
                "status": "success",
                "content": content
            }
        else:
            return {
                "status": "success",
                "content": ""
            }
    except Exception as e:
        config.logger.error(f"Failed to read text file: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


async def clear_text_content(plugin) -> dict:
    """Clear the text content from the file
    
    Args:
        plugin: Plugin instance to access text_file_path and decky_send_dir
        
    Returns:
        dict with status and message
    """
    try:
        # Ensure decky-send directory exists
        os.makedirs(plugin.decky_send_dir, exist_ok=True)
        
        # Write empty content to file
        with open(plugin.text_file_path, 'w', encoding='utf-8') as f:
            f.write('')
        config.logger.info(f"Cleared text file: {plugin.text_file_path}")
        return {
            "status": "success",
            "message": "Text file cleared successfully"
        }
    except Exception as e:
        config.logger.error(f"Failed to clear text file: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
