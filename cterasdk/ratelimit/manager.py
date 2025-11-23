"""
Rate limit manager for coordinating rate limiting across endpoints.
"""

import logging
import time
import asyncio
from typing import Dict, Optional
from .strategies import RateLimitStrategy, TokenBucketStrategy


logger = logging.getLogger('cterasdk.ratelimit')


class RateLimitManager:
    """
    Manages rate limiting across multiple endpoints.
    
    Tracks per-endpoint rate limits and provides unified interface.
    """

    def __init__(self, default_strategy: Optional[RateLimitStrategy] = None):
        """
        Initialize rate limit manager.
        
        :param RateLimitStrategy default_strategy: Default rate limiting strategy
        """
        self.default_strategy = default_strategy or TokenBucketStrategy(rate=10.0, capacity=20)
        self.endpoint_strategies: Dict[str, RateLimitStrategy] = {}
        self.stats = {
            'total_requests': 0,
            'throttled_requests': 0,
            'total_wait_time': 0.0,
        }

    def set_endpoint_strategy(self, endpoint: str, strategy: RateLimitStrategy):
        """
        Set a specific rate limiting strategy for an endpoint.
        
        :param str endpoint: Endpoint path or pattern
        :param RateLimitStrategy strategy: Rate limiting strategy
        """
        self.endpoint_strategies[endpoint] = strategy
        logger.debug("Set rate limit strategy for endpoint: %s", endpoint)

    def get_strategy(self, endpoint: str) -> RateLimitStrategy:
        """
        Get the rate limiting strategy for an endpoint.
        
        :param str endpoint: Endpoint path
        :return: Rate limiting strategy
        """
        # Check for exact match
        if endpoint in self.endpoint_strategies:
            return self.endpoint_strategies[endpoint]
        
        # Check for pattern match (simple prefix matching)
        for pattern, strategy in self.endpoint_strategies.items():
            if endpoint.startswith(pattern):
                return strategy
        
        return self.default_strategy

    def acquire(self, endpoint: str, tokens: int = 1, max_retries: int = 3) -> bool:
        """
        Acquire permission to make a request (synchronous).
        
        :param str endpoint: Endpoint path
        :param int tokens: Number of tokens to acquire
        :param int max_retries: Maximum number of retries
        :return: True if acquired, False if failed after retries
        """
        strategy = self.get_strategy(endpoint)
        self.stats['total_requests'] += 1
        
        for attempt in range(max_retries):
            if strategy.acquire(tokens):
                return True
            
            self.stats['throttled_requests'] += 1
            wait_time = strategy.wait_time()
            
            if wait_time > 0 and attempt < max_retries - 1:
                logger.debug(
                    "Rate limit reached for %s. Waiting %.2f seconds (attempt %d/%d)",
                    endpoint, wait_time, attempt + 1, max_retries
                )
                self.stats['total_wait_time'] += wait_time
                time.sleep(wait_time)
            else:
                break
        
        logger.warning("Failed to acquire rate limit after %d attempts for %s", max_retries, endpoint)
        return False

    async def acquire_async(self, endpoint: str, tokens: int = 1, max_retries: int = 3) -> bool:
        """
        Acquire permission to make a request (asynchronous).
        
        :param str endpoint: Endpoint path
        :param int tokens: Number of tokens to acquire
        :param int max_retries: Maximum number of retries
        :return: True if acquired, False if failed after retries
        """
        strategy = self.get_strategy(endpoint)
        self.stats['total_requests'] += 1
        
        for attempt in range(max_retries):
            if await strategy.acquire_async(tokens):
                return True
            
            self.stats['throttled_requests'] += 1
            wait_time = strategy.wait_time()
            
            if wait_time > 0 and attempt < max_retries - 1:
                logger.debug(
                    "Rate limit reached for %s. Waiting %.2f seconds (attempt %d/%d)",
                    endpoint, wait_time, attempt + 1, max_retries
                )
                self.stats['total_wait_time'] += wait_time
                await asyncio.sleep(wait_time)
            else:
                break
        
        logger.warning("Failed to acquire rate limit after %d attempts for %s", max_retries, endpoint)
        return False

    def get_stats(self) -> dict:
        """
        Get rate limiting statistics.
        
        :return: Dictionary with statistics
        """
        stats = self.stats.copy()
        if stats['total_requests'] > 0:
            stats['throttle_rate'] = stats['throttled_requests'] / stats['total_requests']
            stats['avg_wait_time'] = stats['total_wait_time'] / stats['throttled_requests'] if stats['throttled_requests'] > 0 else 0.0
        return stats

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_requests': 0,
            'throttled_requests': 0,
            'total_wait_time': 0.0,
        }
        logger.debug("Rate limit statistics reset")

