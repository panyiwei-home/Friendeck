# main.py - decky-send plugin entry point
#
# This is the main entry point for the decky-send plugin.
# All functionality has been modularized into py_modules/ directory.
#
# Modules:
#   py_modules/config.py          - Configuration and logging
#   py_modules/utils.py           - Utility functions
#   py_modules/file_operations.py - File system operations
#   py_modules/html_templates.py  - HTML templates and HTTP handlers
#   py_modules/server_manager.py  - Server lifecycle management
#
# NOTE: Decky automatically adds py_modules/ to sys.path, so we import
# modules directly (e.g., "import config") instead of using package imports
# (e.g., "from py_modules import config"). This is the same pattern used
# by other Decky plugins like ToMoon.

import os
import threading
import asyncio
from pathlib import Path

# Decky plugin module
import decky

# Import modularized components (direct imports - Decky adds py_modules/ to path)
import config
import utils
import file_operations
import server_manager


class Plugin:
    """Decky-send plugin main class
    
    This plugin provides file transfer functionality for Steam Deck,
    allowing users to upload files and text from other devices.
    """
    
    # ==========================================================================
    # Server Status Variables
    # ==========================================================================
    
    # Main server
    server_running = False
    server_thread = None
    server_host = config.DEFAULT_SERVER_HOST
    server_port = config.DEFAULT_SERVER_PORT
    app = None
    runner = None
    site = None
    
    # ==========================================================================
    # Thread Control Variables (for graceful shutdown)
    # ==========================================================================
    
    server_stop_event = None        # threading.Event for main server stop signal
    server_loop = None              # event loop reference for main server
    main_loop = None                # main event loop reference for _main()
    monitor_stop_event = None       # threading.Event for monitor thread stop signal
    watchdog_stop_event = None      # threading.Event for watchdog thread stop signal
    watchdog_thread = None          # Watchdog health monitor thread
    
    # Lock for preventing race conditions during server operations
    _server_lock = None  # will be initialized as threading.Lock()
    
    # ==========================================================================
    # Path Variables (from config)
    # ==========================================================================
    
    downloads_dir = config.DOWNLOADS_DIR
    share_dir = config.SHARE_DIR
    decky_send_dir = config.DECKY_SEND_DIR
    text_file_path = config.TEXT_FILE_PATH
    switch_file_path = config.SWITCH_FILE_PATH
    auto_copy_text_enabled = False
    prompt_upload_path_enabled = False
    language_preference = "auto"
    
    # ==========================================================================
    # Settings Keys (from config)
    # ==========================================================================
    
    SETTINGS_KEY = config.SETTINGS_KEY
    SETTING_RUNNING = config.SETTING_RUNNING
    SETTING_PORT = config.SETTING_PORT
    SETTING_DOWNLOAD_DIR = config.SETTING_DOWNLOAD_DIR
    SETTING_AUTO_COPY_TEXT = config.SETTING_AUTO_COPY_TEXT
    SETTING_PROMPT_UPLOAD_PATH = config.SETTING_PROMPT_UPLOAD_PATH
    SETTING_LANGUAGE = config.SETTING_LANGUAGE
    
    # ==========================================================================
    # Lifecycle Methods
    # ==========================================================================
    
    async def _main(self):
        """Plugin main entry point - called when plugin is loaded
        
        NOTE: This function must NOT return! Decky expects _main to run indefinitely.
        If _main returns, the plugin may be considered "done" and resources could be cleaned up.
        This is why we have a "while True" loop at the end, similar to ToMoon plugin.
        """
        decky.logger.info("decky-send plugin initialized")
        config.logger.info("decky-send plugin initialized (config logger)")
        
        # Ensure required directories exist
        os.makedirs(self.downloads_dir, exist_ok=True)
        os.makedirs(self.decky_send_dir, exist_ok=True)
        
        # Create switch file if it doesn't exist
        if not os.path.exists(self.switch_file_path):
            with open(self.switch_file_path, 'w') as f:
                f.write('0')  # Default to off
        
        # Create text file if it doesn't exist
        if not os.path.exists(self.text_file_path):
            with open(self.text_file_path, 'w') as f:
                f.write('')  # Empty file by default
        
        # Load saved settings
        await server_manager.load_settings(self)

        # Ensure downloads directory exists after loading settings
        try:
            os.makedirs(self.downloads_dir, exist_ok=True)
        except Exception as e:
            decky.logger.error(f"Failed to ensure downloads directory: {e}")
        
        # Read switch file and enforce server status
        try:
            with open(self.switch_file_path, 'r') as f:
                switch_value = f.read().strip()
            
            decky.logger.info(f"Read switch file value: {switch_value}")
            
            # Enforce server status based on switch file
            if switch_value == '1':
                # Force start servers
                decky.logger.info("Switch file is 1, forcing servers to start")
                
                # Stop servers if they're already running to force restart
                if self.server_running:
                    decky.logger.info("Servers already running, stopping first")
                    await server_manager.stop_server(self)
                
                # Start main server
                await server_manager.start_server(self, self.server_port)
                
            elif switch_value == '0':
                # Force stop servers
                decky.logger.info("Switch file is 0, forcing servers to stop")
                
                # Stop server if running
                if self.server_running:
                    await server_manager.stop_server(self)
                    
        except Exception as e:
            decky.logger.error(f"Failed to handle switch file: {e}")
        
        # Start monitoring the switch file for changes
        decky.logger.info("Setting up switch file monitoring")
        server_manager.monitor_switch_file(self)
        
        # Start watchdog health monitor
        decky.logger.info("Starting watchdog health monitor")
        server_manager.start_watchdog(self)
        
        # IMPORTANT: Keep _main running forever!
        # This is crucial for plugin stability. If _main returns, Decky may clean up
        # plugin resources, causing servers to stop unexpectedly.
        # This pattern is used by ToMoon and other stable Decky plugins.
        decky.logger.info("decky-send plugin entering keep-alive loop")
        while True:
            await asyncio.sleep(1)
    
    async def _unload(self):
        """Plugin unload handler with complete resource cleanup"""
        decky.logger.info("Unloading decky-send plugin")
        
        # Stop watchdog thread first
        try:
            server_manager.stop_watchdog(self)
            decky.logger.info("Stopped watchdog health monitor")
        except Exception as e:
            decky.logger.error(f"Error stopping watchdog: {e}")
        
        # Stop monitor thread
        if self.monitor_stop_event:
            self.monitor_stop_event.set()
            decky.logger.info("Signaled monitor thread to stop")
        
        # Stop main server
        if self.server_running or self.server_thread:
            try:
                await server_manager.stop_server(self)
            except Exception as e:
                decky.logger.error(f"Error stopping server during unload: {e}")
        
        decky.logger.info("decky-send plugin unloaded successfully")
    
    async def _uninstall(self):
        """Plugin uninstall handler"""
        decky.logger.info("Uninstalling decky-send plugin")
    
    # ==========================================================================
    # Frontend API Methods (called via callPluginMethod)
    # ==========================================================================
    
    async def start_server(self, port: int = config.DEFAULT_SERVER_PORT) -> dict:
        """Start HTTP server - delegate to server_manager"""
        return await server_manager.start_server(self, port)
    
    async def stop_server(self) -> dict:
        """Stop HTTP server - delegate to server_manager"""
        return await server_manager.stop_server(self)
    
    async def get_server_status(self) -> dict:
        """Get server status - delegate to server_manager"""
        return await server_manager.get_server_status(self)
    
    async def get_ip_address(self) -> dict:
        """Get device IP address"""
        try:
            ip = utils.get_ip_address()
            return {"status": "success", "ip_address": ip}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_text_content(self) -> dict:
        """Get text content - delegate to file_operations"""
        return await file_operations.get_text_content(self)
    
    async def clear_text_content(self) -> dict:
        """Clear text content - delegate to file_operations"""
        return await file_operations.clear_text_content(self)

    async def get_auto_copy_text(self) -> dict:
        """Get auto copy text setting"""
        try:
            return {"status": "success", "enabled": bool(self.auto_copy_text_enabled)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def set_auto_copy_text(self, enabled: bool) -> dict:
        """Set auto copy text setting"""
        try:
            self.auto_copy_text_enabled = bool(enabled)
            await server_manager.save_settings(self)
            return {"status": "success", "enabled": self.auto_copy_text_enabled}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_prompt_upload_path(self) -> dict:
        """Get upload path prompt setting"""
        try:
            return {"status": "success", "enabled": bool(self.prompt_upload_path_enabled)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def set_prompt_upload_path(self, enabled: bool) -> dict:
        """Set upload path prompt setting"""
        try:
            self.prompt_upload_path_enabled = bool(enabled)
            await server_manager.save_settings(self)
            return {"status": "success", "enabled": self.prompt_upload_path_enabled}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_language_preference(self) -> dict:
        """Get saved UI language preference"""
        try:
            language = getattr(self, "language_preference", "auto") or "auto"
            return {"status": "success", "language": language}
        except Exception as e:
            return {"status": "error", "message": str(e), "language": "auto"}

    async def set_language_preference(self, language: str) -> dict:
        """Save UI language preference"""
        try:
            value = (language or "auto").strip() or "auto"
            self.language_preference = value
            await server_manager.save_settings(self)
            return {"status": "success", "language": value}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def set_server_port(self, port: int) -> dict:
        """Set server port and optionally restart server if running"""
        try:
            try:
                port = int(port)
            except Exception:
                return {"status": "error", "message": "端口必须是数字"}

            if port < 1 or port > 65535:
                return {"status": "error", "message": "端口范围应为 1-65535"}

            if port == self.server_port:
                await server_manager.save_settings(self)
                return {"status": "success", "port": self.server_port}

            if self.server_running:
                await server_manager.stop_server(self)
                if utils.is_port_in_use(port):
                    return {"status": "error", "message": "端口已被占用"}

                self.server_port = port
                start_result = await server_manager.start_server(self, port)
                if start_result.get("status") == "success":
                    return {"status": "success", "port": port}
                return {"status": "error", "message": start_result.get("message", "端口更新失败")}

            if utils.is_port_in_use(port):
                return {"status": "error", "message": "端口已被占用"}

            self.server_port = port
            await server_manager.save_settings(self)
            return {"status": "success", "port": port}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def set_clipboard_text(self, text: str) -> dict:
        """Set clipboard text using system utilities"""
        try:
            if not text:
                return {"status": "error", "message": "文本为空"}
            success = utils.set_clipboard_text(text)
            if success:
                return {"status": "success"}
            return {"status": "error", "message": "剪贴板工具不可用"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_download_dir(self) -> dict:
        """Get current download directory"""
        try:
            return {"status": "success", "path": self.downloads_dir}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def set_download_dir(self, path: str) -> dict:
        """Set download directory for uploaded files"""
        try:
            if not path or not isinstance(path, str):
                return {"status": "error", "message": "无效的目录路径"}
            if "\x00" in path:
                return {"status": "error", "message": "目录路径包含非法字符"}

            resolved_path = os.path.realpath(os.path.expanduser(path.strip()))
            if not resolved_path:
                return {"status": "error", "message": "无效的目录路径"}

            if os.path.exists(resolved_path) and not os.path.isdir(resolved_path):
                return {"status": "error", "message": "目标路径不是文件夹"}

            os.makedirs(resolved_path, exist_ok=True)
            self.downloads_dir = resolved_path

            await server_manager.save_settings(self)
            decky.logger.info(f"Download directory updated: {self.downloads_dir}")
            return {"status": "success", "path": self.downloads_dir}
        except Exception as e:
            decky.logger.error(f"Failed to set download directory: {e}")
            return {"status": "error", "message": str(e)}

    async def get_pending_notifications(self) -> dict:
        """Get and clear queued toast notifications"""
        try:
            notifications = utils.pop_notifications()
            return {"status": "success", "notifications": notifications}
        except Exception as e:
            return {"status": "error", "message": str(e), "notifications": []}
    
    async def get_file_manager_path(self) -> dict:
        """Get the URL to the file manager page served by the web server."""
        try:
            status = await server_manager.get_server_status(self)
            if not status.get("running"):
                return {
                    "status": "error",
                    "message": "服务器未运行",
                    "path": "",
                    "url": ""
                }
            ip_address = status.get("ip_address") or "127.0.0.1"
            port = status.get("port") or self.server_port
            url = f"http://{ip_address}:{port}/file-manager"
            return {
                "status": "success",
                "path": url,
                "url": url
            }
        except Exception as e:
            config.logger.error(f"Error getting file manager URL: {e}")
            return {
                "status": "error",
                "message": str(e),
                "path": "",
                "url": ""
            }
    
    # ==========================================================================
    # Internal Helper Methods (for backward compatibility)
    # ==========================================================================
    
    def _get_ip_address(self):
        """Get IP address - wrapper for utils function"""
        return utils.get_ip_address()
    
    def _is_port_in_use(self, port, timeout=1.0, retries=3):
        """Check if port is in use - wrapper for utils function"""
        return utils.is_port_in_use(port, timeout, retries)
    
    async def _wait_for_port_release(self, port: int, timeout: float = 3.0):
        """Wait for port release - wrapper for utils function"""
        return await utils.wait_for_port_release(port, timeout)
