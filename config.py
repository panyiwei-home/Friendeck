# config.py - Configuration constants and logger setup for decky-send
#
# This module provides centralized configuration management including:
# - Logger setup (similar to ToMoon style)
# - Path constants
# - Server configuration constants
# - Settings keys

import os
import logging
from pathlib import Path

# =============================================================================
# Logger Setup
# =============================================================================

def setup_logger():
    """Setup and configure the logger for decky-send"""
    try:
        logging.basicConfig(
            level=logging.INFO,
            filename="/tmp/decky-send.log",
            format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s",
            filemode="a",
            force=True,
        )
    except Exception:
        # If file logging fails, fall back to console logging
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s | %(filename)s:%(lineno)s:%(funcName)s] %(levelname)s: %(message)s",
            force=True,
        )
    return logging.getLogger("decky-send")

# Global logger instance
logger = setup_logger()
logger.setLevel(logging.INFO)

# =============================================================================
# Path Constants
# =============================================================================

# User home directory
HOME_DIR = str(Path.home())

# Downloads directory
DOWNLOADS_DIR = str(Path.home() / "Downloads")

# Decky-send data directory
SHARE_DIR = str(Path.home() / ".local" / "share")
DECKY_SEND_DIR = os.path.join(SHARE_DIR, "Decky-send")

# Text file path (for text transfer feature)
TEXT_FILE_PATH = os.path.join(DECKY_SEND_DIR, "Decky-sendtxt.txt")

# Switch file path (for service control)
SWITCH_FILE_PATH = os.path.join(DECKY_SEND_DIR, "decky-sendswitch.txt")

# =============================================================================
# Server Configuration
# =============================================================================

# Default server host (bind to all interfaces)
DEFAULT_SERVER_HOST = "0.0.0.0"

# Main server port
DEFAULT_SERVER_PORT = 59271

# =============================================================================
# Timeout Configuration
# =============================================================================

# Server startup timeout (seconds) - time to wait for port to become available
SERVER_STARTUP_TIMEOUT = 10.0

# Thread shutdown timeout (seconds)
THREAD_SHUTDOWN_TIMEOUT = 5.0

# Port release timeout (seconds)
PORT_RELEASE_TIMEOUT = 5.0

# Watchdog health check interval (seconds)
WATCHDOG_CHECK_INTERVAL = 3.0

# Port check retry configuration
PORT_CHECK_RETRIES = 5
PORT_CHECK_RETRY_DELAY = 0.5

# =============================================================================
# Settings Keys
# =============================================================================

# Key for storing server settings in decky settings
SETTINGS_KEY = "server_settings"

# Individual setting keys
SETTING_RUNNING = "running"
SETTING_PORT = "port"
