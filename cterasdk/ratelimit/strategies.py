"""
Rate limiting strategies for API request management.
"""

import time
import asyncio
import threading
from abc import ABC, abstractmethod
from collections import deque
from typing import Optional


class RateLimitStrategy(ABC):
    """Base class for rate limiting strategies"""

    @abstractmethod
    def acquire(self, tokens: int = 1) -> bool:
        """
        Attempt to acquire tokens for making a request.
        
        :param int tokens: Number of tokens to acquire
        :return: True if tokens were acquired, False otherwise
        """
        pass

    @abstractmethod
    async def acquire_async(self, tokens: int = 1) -> bool:
        """
        Async version of acquire.
        
        :param int tokens: Number of tokens to acquire
        :return: True if tokens were acquired, False otherwise
        """
        pass

    @abstractmethod
    def wait_time(self) -> float:
        """
        Get the time to wait before next request can be made.
        
        :return: Time in seconds to wait
        """
        pass


class FixedWindowStrategy(RateLimitStrategy):
    """
    Fixed window rate limiting strategy.
    
    Allows a fixed number of requests per time window.
    """

    def __init__(self, max_requests: int, window_size: float):
        """
        Initialize fixed window rate limiter.
        
        :param int max_requests: Maximum number of requests allowed per window
        :param float window_size: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = deque()
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def _cleanup_old_requests(self):
        """Remove requests outside the current window"""
        current_time = time.time()
        window_start = current_time - self.window_size
        while self.requests and self.requests[0] < window_start:
            self.requests.popleft()

    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens in sync context"""
        with self._lock:
            self._cleanup_old_requests()
            if len(self.requests) + tokens <= self.max_requests:
                current_time = time.time()
                for _ in range(tokens):
                    self.requests.append(current_time)
                return True
            return False

    async def acquire_async(self, tokens: int = 1) -> bool:
        """Acquire tokens in async context"""
        async with self._async_lock:
            self._cleanup_old_requests()
            if len(self.requests) + tokens <= self.max_requests:
                current_time = time.time()
                for _ in range(tokens):
                    self.requests.append(current_time)
                return True
            return False

    def wait_time(self) -> float:
        """Calculate wait time until next request can be made"""
        with self._lock:
            self._cleanup_old_requests()
            if len(self.requests) < self.max_requests:
                return 0.0
            oldest_request = self.requests[0]
            return max(0.0, (oldest_request + self.window_size) - time.time())


class TokenBucketStrategy(RateLimitStrategy):
    """
    Token bucket rate limiting strategy.
    
    Tokens are added at a fixed rate. Requests consume tokens.
    Allows for bursts up to bucket capacity.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket rate limiter.
        
        :param float rate: Rate at which tokens are added (tokens per second)
        :param int capacity: Maximum number of tokens the bucket can hold
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_update = time.time()
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def _refill(self):
        """Refill tokens based on elapsed time"""
        current_time = time.time()
        elapsed = current_time - self.last_update
        self.tokens = min(self.capacity, self.tokens + (elapsed * self.rate))
        self.last_update = current_time

    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens in sync context"""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def acquire_async(self, tokens: int = 1) -> bool:
        """Acquire tokens in async context"""
        async with self._async_lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_time(self) -> float:
        """Calculate wait time until enough tokens are available"""
        with self._lock:
            self._refill()
            if self.tokens >= 1:
                return 0.0
            tokens_needed = 1 - self.tokens
            return tokens_needed / self.rate


class LeakyBucketStrategy(RateLimitStrategy):
    """
    Leaky bucket rate limiting strategy.
    
    Requests are queued and processed at a fixed rate.
    Provides smooth request rate without bursts.
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize leaky bucket rate limiter.
        
        :param float rate: Rate at which requests leak out (requests per second)
        :param int capacity: Maximum queue size
        """
        self.rate = rate
        self.capacity = capacity
        self.queue_size = 0
        self.last_leak = time.time()
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def _leak(self):
        """Process (leak) requests based on elapsed time"""
        current_time = time.time()
        elapsed = current_time - self.last_leak
        leaked = int(elapsed * self.rate)
        self.queue_size = max(0, self.queue_size - leaked)
        if leaked > 0:
            self.last_leak = current_time

    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens in sync context"""
        with self._lock:
            self._leak()
            if self.queue_size + tokens <= self.capacity:
                self.queue_size += tokens
                return True
            return False

    async def acquire_async(self, tokens: int = 1) -> bool:
        """Acquire tokens in async context"""
        async with self._async_lock:
            self._leak()
            if self.queue_size + tokens <= self.capacity:
                self.queue_size += tokens
                return True
            return False

    def wait_time(self) -> float:
        """Calculate wait time until space is available in queue"""
        with self._lock:
            self._leak()
            if self.queue_size < self.capacity:
                return 0.0
            overflow = self.queue_size - self.capacity + 1
            return overflow / self.rate


class AdaptiveStrategy(RateLimitStrategy):
    """
    Adaptive rate limiting strategy that adjusts based on server responses.
    
    Monitors 429 (Too Many Requests) responses and adjusts rate automatically.
    """

    def __init__(self, initial_rate: float, min_rate: float, max_rate: float):
        """
        Initialize adaptive rate limiter.
        
        :param float initial_rate: Initial request rate (requests per second)
        :param float min_rate: Minimum request rate
        :param float max_rate: Maximum request rate
        """
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.current_rate = initial_rate
        self.tokens = 1.0
        self.last_update = time.time()
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()
        self.consecutive_successes = 0
        self.consecutive_failures = 0

    def _refill(self):
        """Refill tokens based on current rate"""
        current_time = time.time()
        elapsed = current_time - self.last_update
        self.tokens = min(1.0, self.tokens + (elapsed * self.current_rate))
        self.last_update = current_time

    def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens in sync context"""
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    async def acquire_async(self, tokens: int = 1) -> bool:
        """Acquire tokens in async context"""
        async with self._async_lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_time(self) -> float:
        """Calculate wait time"""
        with self._lock:
            self._refill()
            if self.tokens >= 1:
                return 0.0
            tokens_needed = 1 - self.tokens
            return tokens_needed / self.current_rate

    def on_success(self):
        """Called when a request succeeds - gradually increase rate"""
        with self._lock:
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            if self.consecutive_successes >= 10:
                self.current_rate = min(self.max_rate, self.current_rate * 1.1)
                self.consecutive_successes = 0

    def on_rate_limit(self, retry_after: Optional[float] = None):
        """
        Called when a 429 response is received - decrease rate.
        
        :param float retry_after: Retry-After header value in seconds, if provided
        """
        with self._lock:
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            # Decrease rate by 50% on rate limit
            self.current_rate = max(self.min_rate, self.current_rate * 0.5)
            if retry_after:
                # Adjust tokens to respect retry_after
                self.tokens = 0.0
                self.last_update = time.time() + retry_after

