"""
Rate limiting exceptions.
"""

from .base import CTERAException


class RateLimitException(CTERAException):
    """Base exception for rate limiting errors"""
    
    def __init__(self, message: str, endpoint: str = None, retry_after: float = None):
        super().__init__(message)
        self.endpoint = endpoint
        self.retry_after = retry_after


class RateLimitExceeded(RateLimitException):
    """Raised when rate limit is exceeded and retries are exhausted"""
    
    def __init__(self, endpoint: str, max_retries: int):
        message = f"Rate limit exceeded for endpoint '{endpoint}' after {max_retries} retries"
        super().__init__(message, endpoint)
        self.max_retries = max_retries


class TooManyRequests(RateLimitException):
    """Raised when server returns 429 Too Many Requests"""
    
    def __init__(self, endpoint: str, retry_after: float = None):
        message = f"Too many requests to '{endpoint}'"
        if retry_after:
            message += f". Retry after {retry_after} seconds"
        super().__init__(message, endpoint, retry_after)

