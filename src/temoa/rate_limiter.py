"""Simple in-memory rate limiter for Temoa endpoints."""
from collections import defaultdict
from time import time
from typing import Dict, List


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.

    Tracks requests per client per endpoint and enforces configurable limits.
    Note: This is an in-memory implementation and resets on server restart.
    For distributed deployments, consider using Redis or similar.
    """

    def __init__(self):
        """Initialize rate limiter with empty request tracking."""
        # Structure: {client_id: {endpoint: [timestamps]}}
        self._requests: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

    def check_limit(
        self,
        client_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int = 3600
    ) -> bool:
        """
        Check if request is within rate limit.

        Uses sliding window algorithm: removes requests outside the time window,
        then checks if the count is below the limit.

        Args:
            client_id: Client identifier (typically IP address)
            endpoint: Endpoint name (e.g., "reindex", "search")
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds (default: 3600 = 1 hour)

        Returns:
            True if within limit (request allowed), False if exceeded (request blocked)

        Example:
            >>> limiter = RateLimiter()
            >>> limiter.check_limit("192.168.1.1", "reindex", max_requests=5)
            True  # First request allowed
            >>> # ... 4 more requests ...
            >>> limiter.check_limit("192.168.1.1", "reindex", max_requests=5)
            False  # 6th request blocked
        """
        now = time()
        requests = self._requests[client_id][endpoint]

        # Remove old requests outside the sliding window
        requests[:] = [t for t in requests if now - t < window_seconds]

        # Check if limit exceeded
        if len(requests) >= max_requests:
            return False

        # Within limit - record this request
        requests.append(now)
        return True

    def get_remaining(
        self,
        client_id: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int = 3600
    ) -> int:
        """
        Get remaining requests available for this client/endpoint.

        Args:
            client_id: Client identifier
            endpoint: Endpoint name
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Number of requests remaining in current window
        """
        now = time()
        requests = self._requests[client_id][endpoint]

        # Remove old requests outside window
        requests[:] = [t for t in requests if now - t < window_seconds]

        return max(0, max_requests - len(requests))

    def reset(self, client_id: str = None, endpoint: str = None):
        """
        Reset rate limit tracking.

        Args:
            client_id: If provided, reset only this client. If None, reset all.
            endpoint: If provided (with client_id), reset only this endpoint.

        Examples:
            >>> limiter.reset()  # Reset everything
            >>> limiter.reset("192.168.1.1")  # Reset one client
            >>> limiter.reset("192.168.1.1", "search")  # Reset one endpoint
        """
        if client_id is None:
            # Reset everything
            self._requests.clear()
        elif endpoint is None:
            # Reset all endpoints for this client
            if client_id in self._requests:
                del self._requests[client_id]
        else:
            # Reset specific endpoint for this client
            if client_id in self._requests and endpoint in self._requests[client_id]:
                del self._requests[client_id][endpoint]
