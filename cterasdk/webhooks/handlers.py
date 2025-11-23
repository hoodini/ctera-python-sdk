"""
Webhook handlers for processing events.
"""

import json
import logging
import aiohttp
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from .events import WebhookEvent


logger = logging.getLogger('cterasdk.webhooks')


class WebhookHandler(ABC):
    """Base class for webhook handlers"""
    
    @abstractmethod
    async def handle(self, event: WebhookEvent) -> bool:
        """
        Handle a webhook event.
        
        :param WebhookEvent event: Event to handle
        :return: True if handled successfully, False otherwise
        """
        pass
    
    @abstractmethod
    async def close(self):
        """Clean up resources"""
        pass


class HTTPWebhookHandler(WebhookHandler):
    """
    HTTP webhook handler that sends events to HTTP endpoints.
    """
    
    def __init__(
        self,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30,
        retry_attempts: int = 3
    ):
        """
        Initialize HTTP webhook handler.
        
        :param str url: Target URL for webhook
        :param str method: HTTP method (POST, PUT, etc.)
        :param dict headers: Additional HTTP headers
        :param int timeout: Request timeout in seconds
        :param int retry_attempts: Number of retry attempts on failure
        """
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Ensure Content-Type is set
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def handle(self, event: WebhookEvent) -> bool:
        """
        Send event to HTTP endpoint.
        
        :param WebhookEvent event: Event to send
        :return: True if sent successfully, False otherwise
        """
        session = await self._get_session()
        payload = json.dumps(event.to_dict())
        
        for attempt in range(self.retry_attempts):
            try:
                async with session.request(
                    self.method,
                    self.url,
                    data=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status < 400:
                        logger.debug(
                            "Successfully sent webhook event %s to %s (status: %d)",
                            event.event_id, self.url, response.status
                        )
                        return True
                    else:
                        logger.warning(
                            "Failed to send webhook event %s to %s (status: %d, attempt %d/%d)",
                            event.event_id, self.url, response.status, attempt + 1, self.retry_attempts
                        )
            except Exception as e:
                logger.error(
                    "Error sending webhook event %s to %s (attempt %d/%d): %s",
                    event.event_id, self.url, attempt + 1, self.retry_attempts, str(e)
                )
        
        return False
    
    async def close(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            await self.session.close()


class CallbackWebhookHandler(WebhookHandler):
    """
    Callback webhook handler that calls a Python function.
    """
    
    def __init__(self, callback):
        """
        Initialize callback webhook handler.
        
        :param callable callback: Async or sync function to call with event
        """
        self.callback = callback
        import asyncio
        self.is_async = asyncio.iscoroutinefunction(callback)
    
    async def handle(self, event: WebhookEvent) -> bool:
        """
        Call callback function with event.
        
        :param WebhookEvent event: Event to handle
        :return: True if callback succeeded, False otherwise
        """
        try:
            if self.is_async:
                await self.callback(event)
            else:
                self.callback(event)
            return True
        except Exception as e:
            logger.error("Error in webhook callback: %s", str(e))
            return False
    
    async def close(self):
        """No cleanup needed for callback handler"""
        pass


class QueueWebhookHandler(WebhookHandler):
    """
    Queue webhook handler that puts events into an asyncio queue.
    """
    
    def __init__(self, queue):
        """
        Initialize queue webhook handler.
        
        :param asyncio.Queue queue: Queue to put events into
        """
        self.queue = queue
    
    async def handle(self, event: WebhookEvent) -> bool:
        """
        Put event into queue.
        
        :param WebhookEvent event: Event to queue
        :return: True if queued successfully, False otherwise
        """
        try:
            await self.queue.put(event)
            return True
        except Exception as e:
            logger.error("Error queuing webhook event: %s", str(e))
            return False
    
    async def close(self):
        """No cleanup needed for queue handler"""
        pass

