"""
Decorators for applying rate limiting to functions.
"""

import functools
import asyncio
import logging
from typing import Optional, Callable
from .strategies import RateLimitStrategy, TokenBucketStrategy


logger = logging.getLogger('cterasdk.ratelimit')


def rate_limited(
    strategy: Optional[RateLimitStrategy] = None,
    tokens: int = 1,
    max_retries: int = 3
):
    """
    Decorator to apply rate limiting to a function or coroutine.
    
    :param RateLimitStrategy strategy: Rate limiting strategy (default: TokenBucket)
    :param int tokens: Number of tokens required per call
    :param int max_retries: Maximum retry attempts if rate limited
    
    Example:
        @rate_limited(strategy=FixedWindowStrategy(max_requests=10, window_size=60))
        def my_api_call():
            pass
    """
    if strategy is None:
        strategy = TokenBucketStrategy(rate=10.0, capacity=20)
    
    def decorator(func: Callable):
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                for attempt in range(max_retries):
                    if await strategy.acquire_async(tokens):
                        return await func(*args, **kwargs)
                    
                    wait_time = strategy.wait_time()
                    if wait_time > 0 and attempt < max_retries - 1:
                        logger.debug(
                            "Rate limit reached for %s. Waiting %.2f seconds",
                            func.__name__, wait_time
                        )
                        await asyncio.sleep(wait_time)
                
                logger.warning("Rate limit exceeded for %s after %d attempts", func.__name__, max_retries)
                raise RuntimeError(f"Rate limit exceeded for {func.__name__}")
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                import time
                
                for attempt in range(max_retries):
                    if strategy.acquire(tokens):
                        return func(*args, **kwargs)
                    
                    wait_time = strategy.wait_time()
                    if wait_time > 0 and attempt < max_retries - 1:
                        logger.debug(
                            "Rate limit reached for %s. Waiting %.2f seconds",
                            func.__name__, wait_time
                        )
                        time.sleep(wait_time)
                
                logger.warning("Rate limit exceeded for %s after %d attempts", func.__name__, max_retries)
                raise RuntimeError(f"Rate limit exceeded for {func.__name__}")
            
            return sync_wrapper
    
    return decorator

