# utils.py - Utility functions for decky-send
#
# This module provides stateless utility functions including:
# - IP address detection
# - Port availability checking
# - Port release waiting

import socket
import time
import asyncio
# NOTE: Direct import - Decky adds py_modules/ to sys.path
import config

# =============================================================================
# Network Utilities
# =============================================================================

def get_ip_address():
    """Get the local IP address of the device
    
    Returns:
        str: Local IP address, or "127.0.0.1" if detection fails
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except Exception as e:
        config.logger.error(f"Failed to get IP address: {e}")
        return "127.0.0.1"


def is_port_in_use(port, timeout=1.0, retries=None):
    """Check if a port is in use with retry mechanism
    
    Args:
        port: Port number to check
        timeout: Socket connection timeout in seconds
        retries: Number of retry attempts (default from config)
        
    Returns:
        True if port is in use, False otherwise
    """
    if retries is None:
        retries = config.PORT_CHECK_RETRIES
    
    retry_delay = config.PORT_CHECK_RETRY_DELAY
    
    for attempt in range(retries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect(('127.0.0.1', port))
            return True
        except (ConnectionRefusedError, TimeoutError):
            # Port is not in use or connection refused
            return False
        except OSError as e:
            # Handle specific OS errors
            if e.errno == 111:  # Connection refused on Linux
                return False
            if attempt < retries - 1:
                time.sleep(retry_delay)  # Wait before retry
                continue
            return False
        except Exception as e:
            config.logger.debug(f"Port check error on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(retry_delay)  # Wait before retry
                continue
            return False
    return False


async def wait_for_port_release(port, timeout=None):
    """Wait for a port to be released after server shutdown
    
    Args:
        port: Port number to wait for
        timeout: Maximum time to wait in seconds (default from config)
        
    Returns:
        True if port was released, False if timeout
    """
    if timeout is None:
        timeout = config.PORT_RELEASE_TIMEOUT
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if not is_port_in_use(port):
            config.logger.info(f"Port {port} released successfully")
            return True
        await asyncio.sleep(0.2)
    config.logger.warning(f"Port {port} still in use after {timeout}s timeout")
    return False


def is_service_healthy(port, endpoint='/', timeout=2.0):
    """Check if an HTTP service is healthy by making a request
    
    Args:
        port: Port number to check
        endpoint: HTTP endpoint to request (default '/')
        timeout: Request timeout in seconds
        
    Returns:
        True if service responds with 2xx/3xx status, False otherwise
    """
    import urllib.request
    import urllib.error
    
    url = f"http://127.0.0.1:{port}{endpoint}"
    
    try:
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            if 200 <= status_code < 400:
                config.logger.debug(f"Service health check passed: port {port}, status {status_code}")
                return True
            config.logger.debug(f"Service health check failed: port {port}, status {status_code}")
            return False
    except urllib.error.URLError as e:
        config.logger.debug(f"Service health check failed: port {port}, error: {e}")
        return False
    except Exception as e:
        config.logger.debug(f"Service health check error: port {port}, error: {e}")
        return False


async def wait_for_service_healthy(port, endpoint='/', timeout=None, check_interval=0.5):
    """Wait for an HTTP service to become healthy
    
    Args:
        port: Port number to check
        endpoint: HTTP endpoint to request
        timeout: Maximum time to wait in seconds (default from config)
        check_interval: Time between checks in seconds
        
    Returns:
        True if service became healthy, False if timeout
    """
    if timeout is None:
        timeout = config.FILE_MANAGER_STARTUP_TIMEOUT
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_service_healthy(port, endpoint):
            elapsed = time.time() - start_time
            config.logger.info(f"Service on port {port} became healthy after {elapsed:.1f}s")
            return True
        await asyncio.sleep(check_interval)
    
    config.logger.warning(f"Service on port {port} not healthy after {timeout}s timeout")
    return False
