#!/usr/bin/env python3
"""Validate health check endpoint after Akash deployment.

Retries the health check multiple times to allow for deployment startup time.

Exit status:
 0 health check passed
 1 health check failed or invalid URL
"""

from __future__ import annotations

import sys
import time
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    print("ERROR: httpx not installed. Run: pip install httpx", file=sys.stderr)
    sys.exit(1)

DEFAULT_RETRIES = 10
DEFAULT_RETRY_DELAY = 6  # seconds
TIMEOUT = 10  # seconds per request
HTTP_OK = 200  # HTTP OK status code
MIN_ARGS = 2  # Minimum required command line arguments
ARG_INDEX_RETRIES = 2  # sys.argv index for retries parameter
ARG_INDEX_DELAY = 3  # sys.argv index for delay parameter


def validate_health(url: str, retries: int = DEFAULT_RETRIES, delay: int = DEFAULT_RETRY_DELAY) -> bool:
    """Validate health endpoint with retries.
    
    Args:
        url: Base URL of the deployed service (e.g., https://example.com)
        retries: Number of retry attempts
        delay: Delay in seconds between retries
        
    Returns:
        True if health check passed, False otherwise
    """
    # Ensure URL has a scheme
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
        parsed = urlparse(url)
    
    # Construct health check URL
    health_url = f"{parsed.scheme}://{parsed.netloc}/healthz"
    
    print(f"Validating health check at: {health_url}")
    print(f"Will retry up to {retries} times with {delay}s delay between attempts")
    
    for attempt in range(1, retries + 1):
        try:
            print(f"Attempt {attempt}/{retries}...", end=" ", flush=True)
            
            with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
                response = client.get(health_url)
                
                if response.status_code == HTTP_OK:
                    try:
                        data = response.json()
                        if data.get("status") == "ok":
                            print("✓ PASSED")
                            print(f"Health check response: {data}")
                            return True
                        else:
                            print(f"✗ Unexpected response: {data}")
                    except Exception as e:
                        print(f"✗ Invalid JSON response ({type(e).__name__}): {response.text[:200]}...")
                else:
                    print(f"✗ HTTP {response.status_code}")
                    
        except httpx.ConnectError as e:
            print(f"✗ Connection failed: {e}")
        except httpx.TimeoutException:
            print(f"✗ Timeout after {TIMEOUT}s")
        except Exception as e:
            print(f"✗ Error: {e}")
        
        if attempt < retries:
            print(f"Waiting {delay}s before retry...")
            time.sleep(delay)
    
    print(f"\nHealth check FAILED after {retries} attempts")
    return False


def main() -> int:
    if len(sys.argv) < MIN_ARGS:
        print("usage: validate_health.py <url> [retries] [delay]", file=sys.stderr)
        print("  url: Base URL of deployed service (e.g., https://example.com)", file=sys.stderr)
        print(f"  retries: Number of retry attempts (default: {DEFAULT_RETRIES})", file=sys.stderr)
        print(f"  delay: Delay in seconds between retries (default: {DEFAULT_RETRY_DELAY})", file=sys.stderr)
        return 1
    
    url = sys.argv[1]
    retries = int(sys.argv[ARG_INDEX_RETRIES]) if len(sys.argv) > ARG_INDEX_RETRIES else DEFAULT_RETRIES
    delay = int(sys.argv[ARG_INDEX_DELAY]) if len(sys.argv) > ARG_INDEX_DELAY else DEFAULT_RETRY_DELAY
    
    success = validate_health(url, retries, delay)
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
