# server_manager.py - Server management functions for decky-send
#
# This module provides server lifecycle management including:
# - File manager server start/stop
# - Main HTTP server start/stop
# - Switch file monitoring
# - Server status management
# - Settings persistence

import os
import json
import threading
import asyncio
import time
from aiohttp import web
import decky

# NOTE: Direct imports - Decky adds py_modules/ to sys.path
import config
import utils
import file_operations
import html_templates

# =============================================================================
# Switch File Monitoring
# =============================================================================

def _monitor_switch_file(plugin):
    """Monitor the switch file for changes with proper resource management
    
    Args:
        plugin: Plugin instance containing server state
    """
    # Create stop event for monitor thread
    plugin.monitor_stop_event = threading.Event()
    
    def monitor_thread_func():
        config.logger.info("Switch file monitor thread started")
        stop_event = plugin.monitor_stop_event
        last_modified = os.path.getmtime(plugin.switch_file_path) if os.path.exists(plugin.switch_file_path) else 0
        
        # Create a single event loop for this thread and reuse it
        monitor_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(monitor_loop)
        
        try:
            while not stop_event.is_set():
                try:
                    if os.path.exists(plugin.switch_file_path):
                        current_modified = os.path.getmtime(plugin.switch_file_path)
                        if current_modified != last_modified:
                            # Add debounce: wait a bit to avoid reacting to our own writes
                            if stop_event.wait(0.5):
                                break
                            
                            # Re-check if file was modified again (debounce)
                            new_modified = os.path.getmtime(plugin.switch_file_path)
                            if new_modified != current_modified:
                                # File is still being modified, skip this cycle
                                last_modified = new_modified
                                continue
                            
                            last_modified = current_modified
                            
                            # Read the new value
                            with open(plugin.switch_file_path, 'r') as f:
                                switch_value = f.read().strip()
                            
                            config.logger.info(f"Switch file changed to: {switch_value}")
                            
                            # Use the monitor thread's event loop for async operations
                            if switch_value == '1':
                                # Check if server is already running correctly
                                port_in_use = utils.is_port_in_use(plugin.server_port)
                                
                                if port_in_use and plugin.server_running:
                                    # Server is already running correctly, no action needed
                                    config.logger.info("Switch is 1, server already running - no action needed")
                                elif port_in_use and not plugin.server_running:
                                    # Port in use but we don't know about it - just update state
                                    config.logger.info("Switch is 1, port in use - updating state only")
                                    plugin.server_running = True
                                elif not port_in_use:
                                    # Server is not running, start it
                                    config.logger.info("Switch is 1, server not running - starting server")
                                    monitor_loop.run_until_complete(start_server(plugin, plugin.server_port))
                                
                            elif switch_value == '0':
                                # Force stop server
                                config.logger.info("Switch file is 0, forcing server to stop")
                                
                                # Stop server if running
                                if plugin.server_running or utils.is_port_in_use(plugin.server_port):
                                    monitor_loop.run_until_complete(stop_server(plugin))
                            
                except Exception as e:
                    config.logger.error(f"Error in switch file monitor: {e}")
                
                # Wait until next cycle or exit immediately when stop is requested.
                if stop_event.wait(1.0):
                    break
        finally:
            # Clean up the event loop properly
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(monitor_loop)
                for task in pending:
                    task.cancel()
                if pending:
                    monitor_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                config.logger.error(f"Error cleaning up monitor loop: {e}")
            finally:
                monitor_loop.close()
                config.logger.info("Switch file monitor thread stopped cleanly")
    
    # Start the monitor thread
    monitor_thread = threading.Thread(target=monitor_thread_func, daemon=True, name="switch_file_monitor")
    monitor_thread.start()


# =============================================================================
# Watchdog Health Monitor
# =============================================================================

def _watchdog_monitor(plugin):
    """Monitor service health and correct inconsistent states
    
    This watchdog thread periodically checks if the actual service state
    matches the expected state (plugin.server_running) and corrects any inconsistencies.
    
    Args:
        plugin: Plugin instance containing server state
    """
    # Create stop event for watchdog thread
    plugin.watchdog_stop_event = threading.Event()
    
    def watchdog_thread_func():
        config.logger.info("Watchdog health monitor thread started")
        stop_event = plugin.watchdog_stop_event
        
        # Track last correction time to avoid too frequent corrections
        last_main_correction_time = 0
        correction_cooldown = 60  # seconds between corrections for same issue
        
        while not stop_event.is_set():
            try:
                current_time = time.time()
                
                # Check main server health
                main_port_in_use = utils.is_port_in_use(plugin.server_port)
                
                if plugin.server_running and not main_port_in_use:
                    # State inconsistency: we think server is running but port is not in use
                    if current_time - last_main_correction_time > correction_cooldown:
                        config.logger.warning(
                            f"Watchdog: Main server state inconsistency detected - "
                            f"server_running={plugin.server_running} but port {plugin.server_port} not in use"
                        )
                        # Correct the state
                        plugin.server_running = False
                        last_main_correction_time = current_time
                        
                        # Update switch file to reflect actual state
                        try:
                            with open(plugin.switch_file_path, 'w') as f:
                                f.write('0')
                            config.logger.info("Watchdog: Updated switch file to 0 due to main server not running")
                        except Exception as e:
                            config.logger.error(f"Watchdog: Failed to update switch file: {e}")
                
                elif not plugin.server_running and main_port_in_use:
                    # State inconsistency: server is running but we don't know about it
                    if current_time - last_main_correction_time > correction_cooldown:
                        config.logger.info(
                            f"Watchdog: Main server running externally - "
                            f"server_running={plugin.server_running} but port {plugin.server_port} is in use"
                        )
                        # Correct the state
                        plugin.server_running = True
                        last_main_correction_time = current_time
                        
                        # Update switch file to reflect actual state
                        try:
                            with open(plugin.switch_file_path, 'w') as f:
                                f.write('1')
                            config.logger.info("Watchdog: Updated switch file to 1 due to main server running")
                        except Exception as e:
                            config.logger.error(f"Watchdog: Failed to update switch file: {e}")
                
            except Exception as e:
                config.logger.error(f"Watchdog: Error during health check: {e}")
            
            # Wait until next check or exit immediately when stop is requested.
            if stop_event.wait(config.WATCHDOG_CHECK_INTERVAL):
                break
        
        config.logger.info("Watchdog health monitor thread stopped cleanly")
    
    # Start the watchdog thread
    plugin.watchdog_thread = threading.Thread(
        target=watchdog_thread_func, 
        daemon=True, 
        name="watchdog_health_monitor"
    )
    plugin.watchdog_thread.start()


def stop_watchdog(plugin):
    """Stop the watchdog health monitor thread
    
    Args:
        plugin: Plugin instance containing server state
    """
    if hasattr(plugin, 'watchdog_stop_event') and plugin.watchdog_stop_event:
        config.logger.info("Stopping watchdog health monitor...")
        plugin.watchdog_stop_event.set()
        
        if hasattr(plugin, 'watchdog_thread') and plugin.watchdog_thread:
            plugin.watchdog_thread.join(timeout=2.0)
            if plugin.watchdog_thread.is_alive():
                config.logger.warning("Watchdog thread did not stop in time")
        
        plugin.watchdog_stop_event = None
        plugin.watchdog_thread = None
        config.logger.info("Watchdog health monitor stopped")


# Expose watchdog functions for external use
start_watchdog = _watchdog_monitor


# =============================================================================
# Main Server Management
# =============================================================================

async def start_server_async(plugin):
    """Start the HTTP server asynchronously
    
    Args:
        plugin: Plugin instance containing server state
    """
    try:
        # Clean up any existing resources if server was not properly stopped
        if plugin.runner:
            try:
                await plugin.runner.cleanup()
            except Exception:
                pass  # Ignore errors during cleanup
            plugin.runner = None
            plugin.site = None
        
        # Create aiohttp application with CORS middleware
        # Allow very large uploads (default is 1MB in aiohttp)
        plugin.app = web.Application(
            middlewares=[cors_middleware],
            client_max_size=1024 ** 4  # 1 TB limit for large file transfers
        )
        
        # Setup main server routes
        setup_main_server_routes(plugin.app, plugin)
        
        # Create runner and start server
        plugin.runner = web.AppRunner(plugin.app)
        await plugin.runner.setup()
        plugin.site = web.TCPSite(plugin.runner, plugin.server_host, plugin.server_port)
        await plugin.site.start()
        
        config.logger.info(f"HTTP server started on {plugin.server_host}:{plugin.server_port}")
        plugin.server_running = True
        
    except Exception as e:
        config.logger.error(f"Failed to start server: {e}")
        plugin.server_running = False
        # Clean up resources if startup failed
        if plugin.runner:
            try:
                await plugin.runner.cleanup()
            except Exception:
                pass
            plugin.runner = None
            plugin.site = None


async def _wait_for_stop_event(stop_event):
    """Block without polling until a stop event is set."""
    await asyncio.to_thread(stop_event.wait)


def start_server_thread(plugin):
    """Start the server in a separate thread with graceful shutdown support
    
    Args:
        plugin: Plugin instance containing server state
    """
    # Create stop event for this thread
    plugin.server_stop_event = threading.Event()
    stop_event = plugin.server_stop_event  # Local reference to avoid race condition
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    plugin.server_loop = loop  # Store loop reference for later cleanup
    
    try:
        loop.run_until_complete(start_server_async(plugin))
        
        # Block until stop is requested without wakeups from periodic sleep loops.
        if stop_event and not stop_event.is_set():
            loop.run_until_complete(_wait_for_stop_event(stop_event))
    except Exception as e:
        config.logger.error(f"Server thread error: {e}")
    finally:
        # Clean up the loop properly
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception as e:
            config.logger.error(f"Error cancelling server tasks: {e}")
        finally:
            loop.close()
            plugin.server_loop = None
            config.logger.info("Server thread stopped cleanly")


async def start_server(plugin, port=config.DEFAULT_SERVER_PORT):
    """Start HTTP server
    
    Args:
        plugin: Plugin instance containing server state
        port: Port number to start server on
        
    Returns:
        dict: Status response with server URL and connection info
    """
    # Check if server is already running by trying to connect to the port
    if utils.is_port_in_use(port):
        # Server is already running
        config.logger.info(f"Server is already running on port {port}")
        plugin.server_running = True
        plugin.server_port = port
        
        # Update switch file
        try:
            with open(plugin.switch_file_path, 'w') as f:
                f.write('1')
            config.logger.info("Updated switch file to 1")
        except Exception as e:
            config.logger.error(f"Failed to update switch file: {e}")
        await save_settings(plugin)
        
        # Return success with current server info
        ip_address = utils.get_ip_address()
        url = f"http://{ip_address}:{port}"
        return {
            "status": "success",
            "message": "服务器已在运行",
            "ip_address": ip_address,
            "port": port,
            "url": url
        }
    
    try:
        plugin.server_port = port
        
        # Clean up any existing resources first to ensure a fresh start
        config.logger.info("Cleaning up existing resources before starting server")
        plugin.site = None
        plugin.runner = None
        plugin.app = None
        plugin.server_thread = None
        plugin.server_running = False
        
        # Start server in a new thread
        config.logger.info(f"Starting server thread on port {port}")
        plugin.server_thread = threading.Thread(
            target=start_server_thread,
            args=(plugin,),
            daemon=True
        )
        plugin.server_thread.start()
        
        # Wait for server to start and check if port is open
        max_wait_time = config.SERVER_STARTUP_TIMEOUT
        wait_interval = 0.5  # Check every 500ms
        elapsed_time = 0
        
        while elapsed_time < max_wait_time:
            await asyncio.sleep(wait_interval)
            elapsed_time += wait_interval
            
            if utils.is_port_in_use(port):
                config.logger.info(f"Server started successfully on port {port} after {elapsed_time} seconds")
                break
        
        # Check if server is actually running by testing the port
        if utils.is_port_in_use(port):
            # Server is running, update status
            plugin.server_running = True
            
            # Get IP address
            ip_address = utils.get_ip_address()
            url = f"http://{ip_address}:{port}"
            
            # Update switch file
            try:
                with open(plugin.switch_file_path, 'w') as f:
                    f.write('1')
                config.logger.info("Updated switch file to 1")
            except Exception as e:
                config.logger.error(f"Failed to update switch file: {e}")
            
            # Save settings
            await save_settings(plugin)
            
            config.logger.info(f"Server started successfully at {url}")
            return {
                "status": "success",
                "message": "服务器已启动",
                "ip_address": ip_address,
                "port": port,
                "url": url
            }
        else:
            # Ensure all resources are cleaned up if start fails
            config.logger.error(f"Server start failed: port {port} is not open after {max_wait_time} seconds")
            plugin.server_thread = None
            plugin.server_running = False
            plugin.site = None
            plugin.runner = None
            plugin.app = None
            # Ensure switch file is set to 0 on failure
            try:
                with open(plugin.switch_file_path, 'w') as f:
                    f.write('0')
                config.logger.info("Updated switch file to 0 after failed start")
            except Exception as e:
                config.logger.error(f"Failed to update switch file after failed start: {e}")
            await save_settings(plugin)
            return {"status": "error", "message": "服务器启动失败"}
            
    except Exception as e:
        config.logger.error(f"Failed to start server: {e}")
        # Ensure all resources are cleaned up if exception occurs
        plugin.server_thread = None
        plugin.server_running = False
        plugin.site = None
        plugin.runner = None
        plugin.app = None
        # Ensure switch file is set to 0 on exception
        try:
            with open(plugin.switch_file_path, 'w') as f:
                f.write('0')
            config.logger.info("Updated switch file to 0 after exception")
        except Exception as switch_error:
            config.logger.error(f"Failed to update switch file after exception: {switch_error}")
        await save_settings(plugin)
        return {"status": "error", "message": str(e)}


async def stop_server(plugin):
    """Stop HTTP server with proper thread cleanup
    
    Args:
        plugin: Plugin instance containing server state
        
    Returns:
        dict: Status response with success message
    """
    # Check if server is actually running by verifying runner exists or server_running is True
    if not plugin.server_running and not plugin.runner and not plugin.server_thread:
        config.logger.info("Server is already stopped")
        return {"status": "success", "message": "服务器已停止"}
    
    try:
        config.logger.info("Stopping server...")
        
        # Signal the server thread to stop
        if plugin.server_stop_event:
            plugin.server_stop_event.set()
        
        # Stop the server if runner exists
        if plugin.runner:
            config.logger.info("Cleaning up server runner")
            try:
                await plugin.runner.cleanup()
            except Exception as e:
                config.logger.error(f"Error cleaning up runner: {e}")
        
        # Wait for server thread to finish with timeout
        if plugin.server_thread and plugin.server_thread.is_alive():
            config.logger.info("Waiting for server thread to stop...")
            plugin.server_thread.join(timeout=config.THREAD_SHUTDOWN_TIMEOUT)
            if plugin.server_thread.is_alive():
                config.logger.warning("Server thread did not stop in time")
        
        # Clean up all references regardless of runner status
        config.logger.info("Cleaning up server resources")
        plugin.site = None
        plugin.runner = None
        plugin.app = None
        plugin.server_thread = None
        plugin.server_stop_event = None
        
        # Update server running status
        plugin.server_running = False
        
        # Wait for port to be released
        await utils.wait_for_port_release(plugin.server_port, timeout=config.PORT_RELEASE_TIMEOUT)
        
        # Update switch file
        try:
            with open(plugin.switch_file_path, 'w') as f:
                f.write('0')
            config.logger.info("Updated switch file to 0")
        except Exception as e:
            config.logger.error(f"Failed to update switch file: {e}")
        
        # Save settings
        await save_settings(plugin)
        
        config.logger.info("Server stopped successfully")
        
        return {
            "status": "success",
            "message": "服务器已停止"
        }
        
    except Exception as e:
        config.logger.error(f"Failed to stop server: {e}")
        # Ensure all resources are cleaned up even if there's an error
        plugin.server_running = False
        plugin.server_thread = None
        plugin.server_stop_event = None
        plugin.site = None
        plugin.runner = None
        plugin.app = None
        
        # Update switch file even if there's an error
        try:
            with open(plugin.switch_file_path, 'w') as f:
                f.write('0')
            config.logger.info("Updated switch file to 0 during error")
        except Exception as switch_error:
            config.logger.error(f"Failed to update switch file during error handling: {switch_error}")
        
        await save_settings(plugin)
        config.logger.info("Server resources cleaned up after error")
        return {
            "status": "success", 
            "message": "服务器已停止" 
        }  # Return success even if there was an error, since we've cleaned up all resources


async def get_server_status(plugin):
    """Get current server status, checking actual resources
    
    Args:
        plugin: Plugin instance containing server state
        
    Returns:
        dict: Server status including running state, port, host, IP address
    """
    # Reconcile runtime status from actual resources so external control actions
    # (e.g. web/Flutter stop) stay consistent with the Decky UI toggle.
    port_in_use = utils.is_port_in_use(plugin.server_port)
    thread_alive = bool(plugin.server_thread and plugin.server_thread.is_alive())
    runner_alive = bool(plugin.runner is not None)
    service_healthy = bool(
        port_in_use and utils.is_service_healthy(plugin.server_port, endpoint='/', timeout=0.8)
    )
    # Treat "running" as a healthy HTTP service (or a short transitional state
    # where the server thread is still alive and owns the port).
    actual_running = bool(service_healthy or (thread_alive and port_in_use))

    # Clear obviously stale runtime handles that can keep UI toggles "stuck on".
    if not actual_running:
        if not thread_alive:
            plugin.server_thread = None
            plugin.server_stop_event = None
        if runner_alive and not service_healthy:
            plugin.runner = None
            plugin.site = None
            plugin.app = None

    if plugin.server_running != actual_running:
        plugin.server_running = actual_running
        await save_settings(plugin)
        try:
            with open(plugin.switch_file_path, 'w') as f:
                f.write('1' if actual_running else '0')
            config.logger.info(
                "Updated switch file to %s from get_server_status",
                '1' if actual_running else '0'
            )
        except Exception as e:
            config.logger.error(f"Failed to update switch file: {e}")
    
    return {
        "running": actual_running,
        "port": plugin.server_port,
        "host": plugin.server_host,
        "ip_address": utils.get_ip_address()
    }


# =============================================================================
# Settings Management
# =============================================================================

def _get_settings_store(plugin):
    """Resolve the preferred settings store exposed by Decky."""
    plugin_store = getattr(plugin, "settings", None)
    if plugin_store and hasattr(plugin_store, "getSetting") and hasattr(plugin_store, "setSetting"):
        return plugin_store, "plugin.settings"

    decky_store = getattr(decky, "settings", None)
    if decky_store and hasattr(decky_store, "getSetting") and hasattr(decky_store, "setSetting"):
        return decky_store, "decky.settings"

    return None, "none"


def _get_settings_backup_path(plugin):
    settings_dir = getattr(decky, "DECKY_PLUGIN_SETTINGS_DIR", None)
    if not settings_dir:
        settings_dir = getattr(plugin, "decky_send_dir", config.DECKY_SEND_DIR)
    return os.path.join(settings_dir, "settings.json")


def _load_settings_backup(plugin):
    path = _get_settings_backup_path(plugin)
    if not os.path.exists(path):
        return {}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        return data

    config.logger.warning(f"Ignoring invalid backup settings format at {path}")
    return {}


def _save_settings_backup(plugin, settings):
    path = _get_settings_backup_path(plugin)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temp_path = f"{path}.tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)
    return path

async def load_settings(plugin):
    """Load server settings from Decky settings, with file backup fallback.
    
    Args:
        plugin: Plugin instance containing server state
    """
    try:
        settings = {}
        store, store_name = _get_settings_store(plugin)

        if store:
            try:
                value = store.getSetting(plugin.SETTINGS_KEY, {})
                if isinstance(value, dict):
                    settings = value
                elif value is not None:
                    config.logger.warning(f"Unexpected settings value type from {store_name}: {type(value)}")
            except Exception as e:
                config.logger.error(f"Failed to read settings from {store_name}: {e}")
        else:
            config.logger.warning("No Decky settings store available, trying backup file only")

        if not settings:
            try:
                settings = _load_settings_backup(plugin)
                if settings:
                    config.logger.info("Loaded settings from backup file")
                    if store:
                        try:
                            store.setSetting(plugin.SETTINGS_KEY, settings)
                            config.logger.info(f"Restored backup settings into {store_name}")
                        except Exception as restore_error:
                            config.logger.error(f"Failed to restore backup into {store_name}: {restore_error}")
            except Exception as backup_error:
                config.logger.error(f"Failed to load backup settings: {backup_error}")
                settings = {}
        
        # Load server running state
        plugin.server_running = bool(settings.get(plugin.SETTING_RUNNING, False))
        
        # Load server port
        try:
            plugin.server_port = int(settings.get(plugin.SETTING_PORT, config.DEFAULT_SERVER_PORT))
        except Exception:
            plugin.server_port = config.DEFAULT_SERVER_PORT

        # Load download directory
        downloads_dir = settings.get(plugin.SETTING_DOWNLOAD_DIR, config.DOWNLOADS_DIR)
        if isinstance(downloads_dir, str) and downloads_dir.strip():
            plugin.downloads_dir = downloads_dir
        else:
            plugin.downloads_dir = config.DOWNLOADS_DIR

        # Load auto copy text setting
        plugin.auto_copy_text_enabled = bool(settings.get(plugin.SETTING_AUTO_COPY_TEXT, False))
        plugin.prompt_upload_path_enabled = bool(settings.get(plugin.SETTING_PROMPT_UPLOAD_PATH, False))
        plugin.language_preference = settings.get(plugin.SETTING_LANGUAGE, "auto")

        # Ensure downloads directory exists
        try:
            os.makedirs(plugin.downloads_dir, exist_ok=True)
        except Exception as e:
            config.logger.error(f"Failed to create downloads directory: {e}")
        
        config.logger.info(
            "Loaded settings: running=%s, port=%s, downloads_dir=%s, auto_copy_text=%s, prompt_upload_path=%s, language=%s",
            plugin.server_running,
            plugin.server_port,
            plugin.downloads_dir,
            plugin.auto_copy_text_enabled,
            plugin.prompt_upload_path_enabled,
            plugin.language_preference,
        )
        
    except Exception as e:
        config.logger.error(f"Failed to load settings: {e}")


async def save_settings(plugin):
    """Save server settings to Decky settings and backup file.
    
    Args:
        plugin: Plugin instance containing server state
    """
    settings = {
        plugin.SETTING_RUNNING: bool(plugin.server_running),
        plugin.SETTING_PORT: int(plugin.server_port),
        plugin.SETTING_DOWNLOAD_DIR: plugin.downloads_dir,
        plugin.SETTING_AUTO_COPY_TEXT: bool(plugin.auto_copy_text_enabled),
        plugin.SETTING_PROMPT_UPLOAD_PATH: bool(plugin.prompt_upload_path_enabled),
        plugin.SETTING_LANGUAGE: getattr(plugin, "language_preference", "auto"),
    }

    persisted = False
    store_error = None
    store, store_name = _get_settings_store(plugin)
    if store:
        try:
            store.setSetting(plugin.SETTINGS_KEY, settings)
            persisted = True
        except Exception as e:
            store_error = f"{store_name} save failed: {e}"
    else:
        store_error = "Decky settings store unavailable"

    backup_path = None
    backup_error = None
    try:
        backup_path = _save_settings_backup(plugin, settings)
        persisted = True
    except Exception as e:
        backup_error = f"backup save failed: {e}"

    if not persisted:
        message = "; ".join([msg for msg in (store_error, backup_error) if msg]) or "unknown settings save failure"
        config.logger.error(f"Failed to save settings: {message}")
        raise RuntimeError(message)

    if store_error:
        config.logger.warning(store_error)
    if backup_error:
        config.logger.warning(backup_error)

    config.logger.info(
        f"Saved settings via {store_name} and backup file {backup_path}: {settings}"
    )


# =============================================================================
# CORS Middleware
# =============================================================================

@web.middleware
async def cors_middleware(request, handler):
    """Add CORS headers to allow requests from local HTML files (file:// protocol)"""
    # Handle preflight OPTIONS requests
    if request.method == 'OPTIONS':
        response = web.Response()
    else:
        try:
            response = await handler(request)
        except web.HTTPException as ex:
            response = ex
    
    # Add CORS headers to all responses
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '3600'
    
    return response


# =============================================================================
# Route Setup Helpers
# =============================================================================

def setup_main_server_routes(app, plugin):
    """Configure main server routes
    
    Args:
        app: aiohttp web.Application instance
        plugin: Plugin instance for accessing handlers
    """
    # Main page (doesn't need plugin)
    app.router.add_get('/', html_templates.handle_index)
    app.router.add_get('/file-manager', html_templates.handle_file_manager_index)
    
    # Upload endpoints (need plugin for paths)
    app.router.add_post('/upload', lambda request: html_templates.handle_upload(request, plugin))
    app.router.add_post('/upload-chunk', lambda request: html_templates.handle_upload_chunk(request, plugin))
    app.router.add_post('/upload-status', lambda request: html_templates.handle_upload_status(request, plugin))
    app.router.add_post('/upload-text', lambda request: html_templates.handle_text_upload(request, plugin))
    app.router.add_get('/api/settings/upload-options', lambda request: html_templates.handle_upload_options(request, plugin))
    
    # File management routes
    app.router.add_post('/api/files/list', file_operations.get_file_list)
    app.router.add_post('/api/files/read', file_operations.read_file)
    app.router.add_post('/api/files/write', file_operations.write_file)
    app.router.add_post('/api/files/create', file_operations.create_file)
    app.router.add_post('/api/files/create-dir', file_operations.create_directory)
    app.router.add_post('/api/files/copy', file_operations.copy_file)
    app.router.add_post('/api/files/move', file_operations.move_file)
    app.router.add_post('/api/files/delete', file_operations.delete_file)
    app.router.add_get('/api/files/download', file_operations.download_file)
    app.router.add_post('/api/files/unpack', file_operations.unpack_archive)
    app.router.add_post('/api/files/add-to-steam', file_operations.add_file_to_steam)
    app.router.add_get('/api/system/sdcard', file_operations.get_sdcard_info)
    app.router.add_get('/api/system/overview', lambda request: html_templates.handle_system_overview(request, plugin))
    app.router.add_post('/api/system/control', lambda request: html_templates.handle_system_control(request, plugin))
    app.router.add_get('/api/media/list', file_operations.get_media_list)
    app.router.add_get('/api/media/preview', file_operations.get_media_preview)
    app.router.add_get('/api/settings/language', lambda request: html_templates.handle_language_settings(request, plugin))
    
    # Add OPTIONS handler for CORS preflight
    app.router.add_route('OPTIONS', '/{path:.*}', lambda r: web.Response())


# =============================================================================
# Public API aliases
# =============================================================================

# Expose _monitor_switch_file as monitor_switch_file for external use
monitor_switch_file = _monitor_switch_file
