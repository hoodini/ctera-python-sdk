"""Type stubs for rate limiting module."""
from typing import Optional, Callable
from .strategies import RateLimitStrategy, FixedWindowStrategy, TokenBucketStrategy, LeakyBucketStrategy
from .manager import RateLimitManager
from .decorators import rate_limited

__all__ = [
    'RateLimitStrategy',
    'FixedWindowStrategy',
    'TokenBucketStrategy',
    'LeakyBucketStrategy',
    'RateLimitManager',
    'rate_limited',
]

def rate_limited(
    strategy: Optional[RateLimitStrategy] = None,
    tokens: int = 1,
    max_retries: int = 3
) -> Callable: ...

