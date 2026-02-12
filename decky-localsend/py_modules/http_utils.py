"""
HTTP utilities for making requests with retry logic.
Note: This module does NOT use decky directly. Logging is done via callbacks.
"""

import ssl
import time
import json
import urllib.request
import urllib.error
from typing import Callable, Tuple, Any


def get_ssl_context() -> ssl.SSLContext:
    """Create SSL context that ignores certificate verification"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def do_request(
    method: str,
    url: str,
    data: bytes = None,
    headers: dict = None,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    timeout: int = 30,
    logger: Callable[[str], None] = None
) -> Tuple[bytes, int, str]:
    """
    Execute HTTP request with retry logic using urllib.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Target URL
        data: Request body data
        headers: Request headers
        max_retries: Maximum number of retries
        backoff_factor: Exponential backoff factor
        timeout: Request timeout in seconds
        logger: Optional logging callback for errors
    
    Returns:
        Tuple of (response_data, status_code, content_type)
    """
    retry_status_codes = {500, 502, 503, 504}
    last_error = None
    
    req_headers = headers or {}
    
    for attempt in range(max_retries + 1):
        try:
            request = urllib.request.Request(url, data=data, headers=req_headers, method=method)
            ctx = get_ssl_context()
            
            with urllib.request.urlopen(request, context=ctx, timeout=timeout) as response:
                response_data = response.read()
                status_code = response.status
                content_type = response.headers.get('Content-Type', '')
                
                return response_data, status_code, content_type
                
        except urllib.error.HTTPError as e:
            status_code = e.code
            if status_code in retry_status_codes and attempt < max_retries:
                time.sleep(backoff_factor * (2 ** attempt))
                last_error = e
                continue
            # Return error response
            try:
                response_data = e.read()
            except:
                response_data = b''
            content_type = e.headers.get('Content-Type', '') if e.headers else ''
            return response_data, status_code, content_type
            
        except urllib.error.URLError as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(backoff_factor * (2 ** attempt))
                continue
            raise
            
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(backoff_factor * (2 ** attempt))
                continue
            raise
    
    raise last_error if last_error else Exception("Max retries exceeded")


def parse_response(
    response_data: bytes,
    content_type: str
) -> Any:
    """
    Parse response data based on content type.
    
    Args:
        response_data: Raw response bytes
        content_type: Content-Type header value
    
    Returns:
        Parsed data (dict for JSON, base64 string for binary, str for text)
    """
    import base64
    
    if 'application/json' in content_type:
        try:
            return json.loads(response_data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return response_data.decode('utf-8', errors='replace')
    elif 'image/' in content_type or 'application/octet-stream' in content_type:
        # For binary data (images, etc.), return as base64
        return base64.b64encode(response_data).decode('utf-8')
    else:
        return response_data.decode('utf-8', errors='replace')
