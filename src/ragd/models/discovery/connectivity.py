"""Connectivity detection for offline-first architecture.

Provides cached connectivity checks to avoid blocking operations
when network is unavailable.
"""

from __future__ import annotations

import logging
import socket
import urllib.request
from functools import lru_cache
from time import time

logger = logging.getLogger(__name__)

# Cache TTL in seconds
_CONNECTIVITY_CACHE_TTL = 60


@lru_cache(maxsize=1)
def _check_internet_cached(cache_key: int) -> bool:
    """Cached internet connectivity check.

    Args:
        cache_key: Time-based cache key for TTL invalidation

    Returns:
        True if internet is available
    """
    try:
        # Try DNS resolution via Cloudflare (fast, reliable)
        socket.create_connection(("1.1.1.1", 53), timeout=3)
        return True
    except OSError:
        pass

    # Fallback: try Google DNS
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        pass

    return False


def is_internet_available() -> bool:
    """Check if internet is available (cached for 60s).

    Uses DNS connectivity check to avoid slow HTTP timeouts.
    Result is cached to prevent repeated checks.

    Returns:
        True if internet is available
    """
    # Round timestamp to TTL for cache invalidation
    cache_key = int(time()) // _CONNECTIVITY_CACHE_TTL
    return _check_internet_cached(cache_key)


def is_ollama_available(base_url: str = "http://localhost:11434") -> bool:
    """Check if local Ollama is reachable.

    Args:
        base_url: Ollama API base URL

    Returns:
        True if Ollama API is responding
    """
    try:
        # Use /api/version for minimal response
        url = f"{base_url}/api/version"
        request = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status == 200
    except Exception as e:
        logger.debug("Ollama not available at %s: %s", base_url, e)
        return False


def clear_connectivity_cache() -> None:
    """Clear the connectivity cache.

    Useful for testing or when network state changes.
    """
    _check_internet_cached.cache_clear()
