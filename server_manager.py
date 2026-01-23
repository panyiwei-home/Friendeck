# server_manager.py - Server management functions for decky-send
#
# This module provides server lifecycle management including:
# - File manager server start/stop
# - Main HTTP server start/stop
# - Switch file monitoring
# - Server status management
# - Settings persistence

import os
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
        last_modified = os.path.getmtime(plugin.switch_file_path) if os.path.exists(plugin.switch_file_path) else 0
        
        # Create a single event loop for this thread and reuse it
        monitor_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(monitor_loop)
        
        try:
            while not plugin.monitor_stop_event.is_set():
                try:
                    if os.path.exists(plugin.switch_file_path):
                        current_modified = os.path.getmtime(plugin.switch_file_path)
                        if current_modified != last_modified:
                            # Add debounce: wait a bit to avoid reacting to our own writes
                            time.sleep(0.5)
                            
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
                
                # Sleep for 1 second before checking again, but check stop event more frequently
                for _ in range(10):  # Check every 100ms
                    if plugin.monitor_stop_event.is_set():
                        break
                    time.sleep(0.1)
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
        
        # Track last correction time to avoid too frequent corrections
        last_main_correction_time = 0
        correction_cooldown = 60  # seconds between corrections for same issue
        
        while not plugin.watchdog_stop_event.is_set():
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
            
            # Sleep for the configured interval, checking stop event periodically
            for _ in range(int(config.WATCHDOG_CHECK_INTERVAL * 10)):
                if plugin.watchdog_stop_event.is_set():
                    break
                time.sleep(0.1)
        
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
        plugin.app = web.Application(middlewares=[cors_middleware])
        
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
        
        # Run until stop event is set, checking periodically
        # Use local reference to avoid NoneType error if plugin.server_stop_event is set to None
        while stop_event and not stop_event.is_set():
            loop.run_until_complete(asyncio.sleep(0.5))
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
    # Check if server is actually running by verifying runner exists or port is in use
    port_in_use = utils.is_port_in_use(plugin.server_port)
    
    # Only update status if server is actually running but we think it's not
    # This prevents automatic switch toggling off when server is manually stopped
    if port_in_use and not plugin.server_running:
        plugin.server_running = True
        # Save updated status and update switch file
        await save_settings(plugin)
        try:
            with open(plugin.switch_file_path, 'w') as f:
                f.write('1')
            config.logger.info("Updated switch file to 1 from get_server_status")
        except Exception as e:
            config.logger.error(f"Failed to update switch file: {e}")
    
    return {
        "running": plugin.server_running,
        "port": plugin.server_port,
        "host": plugin.server_host,
        "ip_address": utils.get_ip_address()
    }


# =============================================================================
# Settings Management
# =============================================================================

async def load_settings(plugin):
    """Load server settings from decky settings
    
    Args:
        plugin: Plugin instance containing server state
    """
    try:
        # Get all settings
        settings = decky.settings.getSetting(plugin.SETTINGS_KEY, {})
        
        # Load server running state
        plugin.server_running = settings.get(plugin.SETTING_RUNNING, False)
        
        # Load server port
        plugin.server_port = settings.get(plugin.SETTING_PORT, config.DEFAULT_SERVER_PORT)
        
        config.logger.info(f"Loaded settings: running={plugin.server_running}, port={plugin.server_port}")
        
    except Exception as e:
        config.logger.error(f"Failed to load settings: {e}")


async def save_settings(plugin):
    """Save server settings to decky settings
    
    Args:
        plugin: Plugin instance containing server state
    """
    try:
        # Create settings dictionary
        settings = {
            plugin.SETTING_RUNNING: plugin.server_running,
            plugin.SETTING_PORT: plugin.server_port
        }
        
        # Save settings
        decky.settings.setSetting(plugin.SETTINGS_KEY, settings)
        
        config.logger.info(f"Saved settings: {settings}")
        
    except Exception as e:
        config.logger.error(f"Failed to save settings: {e}")


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
    
    # Upload endpoints (need plugin for paths)
    app.router.add_post('/upload', lambda request: html_templates.handle_upload(request, plugin))
    app.router.add_post('/upload-text', lambda request: html_templates.handle_text_upload(request, plugin))
    
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
    app.router.add_post('/api/files/add-to-steam', file_operations.add_file_to_steam)
    app.router.add_get('/api/system/sdcard', file_operations.get_sdcard_info)
    
    # Add OPTIONS handler for CORS preflight
    app.router.add_route('OPTIONS', '/{path:.*}', lambda r: web.Response())


# =============================================================================
# Public API aliases
# =============================================================================

# Expose _monitor_switch_file as monitor_switch_file for external use
monitor_switch_file = _monitor_switch_file
