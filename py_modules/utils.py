# utils.py - Utility functions for decky-send
#
# This module provides stateless utility functions including:
# - IP address detection
# - Port availability checking
# - Port release waiting

import socket
import time
import asyncio
import os
import shutil
import subprocess
import json
import glob
from typing import List, Dict, Any
# NOTE: Direct import - Decky adds py_modules/ to sys.path
import config

# =============================================================================
# Network Utilities
# =============================================================================

def _is_vpn_interface(name: str) -> bool:
    if not name:
        return True
    lowered = name.lower()
    vpn_prefixes = (
        "tun",
        "tap",
        "wg",
        "ppp",
        "pptp",
        "utun",
        "tailscale",
        "ts",
        "docker",
        "br-",
        "virbr",
        "vmnet",
        "vboxnet",
        "lo",
    )
    return lowered.startswith(vpn_prefixes)


def _get_ip_from_ip_cmd() -> str | None:
    ip_bin = shutil.which("ip") or "/sbin/ip" or "/usr/sbin/ip"
    if not os.path.exists(ip_bin):
        return None
    try:
        result = subprocess.run(
            [ip_bin, "-4", "-o", "addr", "show"],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.splitlines()
    except Exception as e:
        config.logger.debug(f"Failed to read ip addr output: {e}")
        return None

    candidates: list[tuple[int, str]] = []
    for line in lines:
        parts = line.split()
        if len(parts) < 4:
            continue
        iface = parts[1]
        ip_with_mask = parts[3]
        ip = ip_with_mask.split("/")[0]

        if ip.startswith("127.") or ip.startswith("169.254."):
            continue
        if _is_vpn_interface(iface):
            continue

        priority = 1
        if iface.startswith(("wl", "wlan", "wlp", "wifi", "eth", "en", "eno", "ens", "enp")):
            priority = 0
        candidates.append((priority, ip))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def get_ip_address():
    """Get the local LAN IP address of the device (prefers non-VPN interfaces).
    
    Returns:
        str: Local IP address, or "127.0.0.1" if detection fails
    """
    try:
        ip_address = _get_ip_from_ip_cmd()
        if ip_address:
            return ip_address

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


# =============================================================================
# Notification Utilities
# =============================================================================

def send_system_notification(title: str, body: str, duration: float = 5.0) -> bool:
    """Send a system notification without relying on the plugin UI.
    
    Returns True if a notification command was launched, False otherwise.
    """
    try:
        notify_bin = shutil.which("notify-send") or "/usr/bin/notify-send"
        if not os.path.exists(notify_bin):
            config.logger.debug("notify-send not found")
            return False
        
        env = os.environ.copy()
        uid = os.getuid()
        runtime_dir = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
        env.setdefault("XDG_RUNTIME_DIR", runtime_dir)
        env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path={runtime_dir}/bus")
        env.setdefault("DISPLAY", ":0")
        env.setdefault("WAYLAND_DISPLAY", "wayland-0")
        
        timeout_ms = str(int(max(duration, 0) * 1000))
        cmd = [
            notify_bin,
            "--app-name", "Decky-send",
            "--expire-time", timeout_ms,
            title,
            body,
        ]
        
        subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        return True
    except Exception as e:
        config.logger.debug(f"System notification failed: {e}")
        return False


# =============================================================================
# Clipboard Utilities
# =============================================================================

def set_clipboard_text(text: str) -> bool:
    """Set system clipboard text using available clipboard utilities."""
    try:
        if text is None:
            return False
        if not isinstance(text, str):
            text = str(text)
        if text == "":
            return False

        env = os.environ.copy()
        uid = os.getuid()
        runtime_dir = env.get("XDG_RUNTIME_DIR") or f"/run/user/{uid}"
        env.setdefault("XDG_RUNTIME_DIR", runtime_dir)
        env.setdefault("DBUS_SESSION_BUS_ADDRESS", f"unix:path={runtime_dir}/bus")
        env.setdefault("DISPLAY", ":0")
        # Pick an existing wayland socket if possible
        if "WAYLAND_DISPLAY" not in env:
            try:
                wayland_sockets = sorted(glob.glob(os.path.join(runtime_dir, "wayland-*")))
                if wayland_sockets:
                    env["WAYLAND_DISPLAY"] = os.path.basename(wayland_sockets[0])
                else:
                    env["WAYLAND_DISPLAY"] = "wayland-0"
            except Exception:
                env["WAYLAND_DISPLAY"] = "wayland-0"

        commands = [
            ["/usr/bin/wl-copy"],
            ["/usr/local/bin/wl-copy"],
            ["/usr/bin/xclip", "-selection", "clipboard"],
            ["/usr/bin/xsel", "--clipboard", "--input"],
            ["wl-copy"],
            ["xclip", "-selection", "clipboard"],
            ["xsel", "--clipboard", "--input"],
        ]

        for cmd in commands:
            bin_path = cmd[0] if os.path.isabs(cmd[0]) else shutil.which(cmd[0])
            if not bin_path or not os.path.exists(bin_path):
                continue
            try:
                subprocess.run(
                    [bin_path] + cmd[1:],
                    input=text.encode("utf-8"),
                    env=env,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception as e:
                config.logger.debug(f"Clipboard command failed ({cmd[0]}): {e}")

        # KDE Plasma / SteamOS (Game Mode) clipboard via Klipper
        qdbus_path = shutil.which("qdbus") or "/usr/bin/qdbus"
        if os.path.exists(qdbus_path):
            try:
                subprocess.run(
                    [qdbus_path, "org.kde.klipper", "/klipper", "setClipboardContents", text],
                    env=env,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True
            except Exception as e:
                config.logger.debug(f"Clipboard command failed (qdbus): {e}")

        config.logger.debug("No clipboard utility available for auto copy")
        return False
    except Exception as e:
        config.logger.debug(f"Clipboard set failed: {e}")
        return False


# =============================================================================
# Toast Queue Utilities
# =============================================================================

def queue_notification(title: str, body: str, urgency: str = "normal") -> bool:
    """Queue a toast notification for frontend polling.

    Returns True if queued successfully, False otherwise.
    """
    try:
        os.makedirs(config.DECKY_SEND_DIR, exist_ok=True)
        entry = {
            "title": title,
            "body": body,
            "urgency": urgency,
            "timestamp": time.time()
        }
        notifications: List[Dict[str, Any]] = []
        if os.path.exists(config.NOTIFICATION_QUEUE_PATH):
            try:
                with open(config.NOTIFICATION_QUEUE_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        notifications = data
            except Exception as e:
                config.logger.debug(f"Failed to read notification queue: {e}")
                notifications = []
        notifications.append(entry)
        with open(config.NOTIFICATION_QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump(notifications, f, ensure_ascii=False)
        return True
    except Exception as e:
        config.logger.debug(f"Queue notification failed: {e}")
        return False


def pop_notifications() -> List[Dict[str, Any]]:
    """Read and clear queued toast notifications."""
    try:
        if not os.path.exists(config.NOTIFICATION_QUEUE_PATH):
            return []
        with open(config.NOTIFICATION_QUEUE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            return []
        # Clear the queue after reading
        with open(config.NOTIFICATION_QUEUE_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        return data
    except Exception as e:
        config.logger.debug(f"Pop notification failed: {e}")
        return []
