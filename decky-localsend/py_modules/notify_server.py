"""
Unix Domain Socket notification server.
Note: This module does NOT use decky directly. All callbacks are passed in.
"""

import os
import json
import socket
import threading
from typing import Callable, Optional, Dict, Any


class NotifyServer:
    """Unix Domain Socket notification server."""
    
    def __init__(
        self,
        socket_path: str = "/tmp/localsend-notify.sock",
        logger_info: Callable[[str], None] = None,
        logger_error: Callable[[str], None] = None,
        logger_warning: Callable[[str], None] = None,
    ):
        """
        Initialize the notification server.
        
        Args:
            socket_path: Path to the Unix socket
            logger_info: Callback for info logging
            logger_error: Callback for error logging
            logger_warning: Callback for warning logging
        """
        self.socket_path = socket_path
        self.notify_socket: Optional[socket.socket] = None
        self.notify_thread: Optional[threading.Thread] = None
        self.notify_shutdown = threading.Event()
        
        # Logging callbacks
        self._log_info = logger_info or (lambda msg: None)
        self._log_error = logger_error or (lambda msg: None)
        self._log_warning = logger_warning or (lambda msg: None)
        
        # Notification handler callback
        self._notification_handler: Optional[Callable[[Dict[str, Any]], None]] = None
    
    def set_notification_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Set the callback function to handle incoming notifications."""
        self._notification_handler = handler
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self.notify_thread is not None and self.notify_thread.is_alive()
    
    def start(self) -> bool:
        """
        Start the notification server.
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.is_running():
            self._log_info("Notification server is already running")
            return True
        
        # Cleanup existing socket
        if os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except Exception as e:
                self._log_warning(f"Failed to remove existing socket: {e}")
        
        self.notify_shutdown.clear()
        
        def run_notify_server():
            try:
                # Create Unix socket
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.bind(self.socket_path)
                sock.listen(5)
                sock.settimeout(1.0)  # Allow periodic checks for shutdown
                self.notify_socket = sock
                
                self._log_info(f"📡 Notification server listening on: {self.socket_path}")
                
                while not self.notify_shutdown.is_set():
                    try:
                        conn, _ = sock.accept()
                        # Handle connection in the same thread (simple implementation)
                        try:
                            # Length-prefixed: 4 bytes little-endian uint32, then payload
                            length_buf = conn.recv(4)
                            if len(length_buf) != 4:
                                continue
                            length = int.from_bytes(length_buf, 'little')
                            if length <= 0 or length > 32 * 1024:  # cap 32KB
                                self._log_error(f"Invalid notify payload length: {length}")
                                continue
                            data = b''
                            while len(data) < length:
                                chunk = conn.recv(min(65536, length - len(data)))
                                if not chunk:
                                    break
                                data += chunk
                            if len(data) == length and data:
                                notification = json.loads(data.decode('utf-8'))
                                if self._notification_handler:
                                    self._notification_handler(notification)
                                
                                # Send response
                                response = {"ok": True}
                                conn.send(json.dumps(response).encode('utf-8'))
                        except json.JSONDecodeError as e:
                            self._log_error(f"Failed to parse notification JSON: {e}")
                        except Exception as e:
                            self._log_error(f"Error handling connection: {e}")
                        finally:
                            conn.close()
                    except socket.timeout:
                        # Timeout is expected, continue loop
                        continue
                    except Exception as e:
                        if not self.notify_shutdown.is_set():
                            self._log_error(f"Socket accept error: {e}")
                        break
                
            except Exception as e:
                self._log_error(f"Notification server error: {e}")
            finally:
                if self.notify_socket:
                    try:
                        self.notify_socket.close()
                    except:
                        pass
                    self.notify_socket = None
                
                # Cleanup socket file
                if os.path.exists(self.socket_path):
                    try:
                        os.remove(self.socket_path)
                    except:
                        pass
                
                self._log_info("📡 Notification server stopped")
        
        self.notify_thread = threading.Thread(target=run_notify_server, daemon=True)
        self.notify_thread.start()
        return True
    
    def stop(self):
        """Stop the notification server."""
        if not self.is_running():
            return
        
        self._log_info("Stopping notification server...")
        self.notify_shutdown.set()
        
        # Wait for thread to finish
        if self.notify_thread:
            self.notify_thread.join(timeout=3)
        
        self.notify_thread = None
        self._log_info("Notification server stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get the status of the notification server."""
        return {
            "running": self.is_running(),
            "socket_path": self.socket_path,
            "socket_exists": os.path.exists(self.socket_path)
        }
