"""
Webhook manager for coordinating webhook registrations and event dispatch.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional
from .events import WebhookEvent, EventFilter
from .handlers import WebhookHandler


logger = logging.getLogger('cterasdk.webhooks')


class WebhookRegistration:
    """Represents a webhook registration"""
    
    def __init__(
        self,
        webhook_id: str,
        handler: WebhookHandler,
        event_filter: Optional[EventFilter] = None,
        enabled: bool = True
    ):
        """
        Initialize webhook registration.
        
        :param str webhook_id: Unique webhook identifier
        :param WebhookHandler handler: Handler for processing events
        :param EventFilter event_filter: Filter for selecting events
        :param bool enabled: Whether webhook is enabled
        """
        self.webhook_id = webhook_id
        self.handler = handler
        self.event_filter = event_filter or EventFilter()
        self.enabled = enabled
        self.stats = {
            'events_received': 0,
            'events_matched': 0,
            'events_handled': 0,
            'events_failed': 0,
        }


class WebhookManager:
    """
    Manages webhook registrations and event dispatching.
    """
    
    def __init__(self):
        """Initialize webhook manager"""
        self.webhooks: Dict[str, WebhookRegistration] = {}
        self._event_queue = asyncio.Queue()
        self._processor_task: Optional[asyncio.Task] = None
        self._running = False
    
    def register(
        self,
        handler: WebhookHandler,
        event_filter: Optional[EventFilter] = None,
        webhook_id: Optional[str] = None
    ) -> str:
        """
        Register a new webhook.
        
        :param WebhookHandler handler: Handler for processing events
        :param EventFilter event_filter: Optional filter for selecting events
        :param str webhook_id: Optional custom webhook ID
        :return: Webhook ID
        """
        if webhook_id is None:
            webhook_id = str(uuid.uuid4())
        
        if webhook_id in self.webhooks:
            raise ValueError(f"Webhook with ID '{webhook_id}' already exists")
        
        registration = WebhookRegistration(webhook_id, handler, event_filter)
        self.webhooks[webhook_id] = registration
        
        logger.info("Registered webhook: %s", webhook_id)
        return webhook_id
    
    def unregister(self, webhook_id: str) -> bool:
        """
        Unregister a webhook.
        
        :param str webhook_id: Webhook ID to unregister
        :return: True if unregistered, False if not found
        """
        if webhook_id in self.webhooks:
            registration = self.webhooks.pop(webhook_id)
            logger.info("Unregistered webhook: %s", webhook_id)
            return True
        return False
    
    def enable(self, webhook_id: str) -> bool:
        """
        Enable a webhook.
        
        :param str webhook_id: Webhook ID to enable
        :return: True if enabled, False if not found
        """
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id].enabled = True
            logger.info("Enabled webhook: %s", webhook_id)
            return True
        return False
    
    def disable(self, webhook_id: str) -> bool:
        """
        Disable a webhook.
        
        :param str webhook_id: Webhook ID to disable
        :return: True if disabled, False if not found
        """
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id].enabled = False
            logger.info("Disabled webhook: %s", webhook_id)
            return True
        return False
    
    async def dispatch(self, event: WebhookEvent):
        """
        Dispatch an event to matching webhooks.
        
        :param WebhookEvent event: Event to dispatch
        """
        if self._running:
            await self._event_queue.put(event)
        else:
            # If not running, process immediately
            await self._process_event(event)
    
    async def _process_event(self, event: WebhookEvent):
        """Process a single event"""
        logger.debug("Processing event: %s (%s)", event.event_id, event.event_type)
        
        for webhook_id, registration in self.webhooks.items():
            registration.stats['events_received'] += 1
            
            if not registration.enabled:
                continue
            
            # Check if event matches filter
            if not registration.event_filter.matches(event):
                continue
            
            registration.stats['events_matched'] += 1
            
            # Handle event
            try:
                success = await registration.handler.handle(event)
                if success:
                    registration.stats['events_handled'] += 1
                else:
                    registration.stats['events_failed'] += 1
            except Exception as e:
                logger.error(
                    "Error handling event %s with webhook %s: %s",
                    event.event_id, webhook_id, str(e)
                )
                registration.stats['events_failed'] += 1
    
    async def _event_processor(self):
        """Background task for processing events"""
        logger.info("Webhook event processor started")
        
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._process_event(event)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error("Error in event processor: %s", str(e))
        
        logger.info("Webhook event processor stopped")
    
    async def start(self):
        """Start the webhook manager"""
        if self._running:
            logger.warning("Webhook manager is already running")
            return
        
        self._running = True
        self._processor_task = asyncio.create_task(self._event_processor())
        logger.info("Webhook manager started")
    
    async def stop(self):
        """Stop the webhook manager"""
        if not self._running:
            return
        
        self._running = False
        
        if self._processor_task:
            await self._processor_task
            self._processor_task = None
        
        # Close all handlers
        for registration in self.webhooks.values():
            await registration.handler.close()
        
        logger.info("Webhook manager stopped")
    
    def get_stats(self, webhook_id: Optional[str] = None) -> Dict:
        """
        Get webhook statistics.
        
        :param str webhook_id: Optional webhook ID (returns all stats if None)
        :return: Statistics dictionary
        """
        if webhook_id:
            if webhook_id in self.webhooks:
                return self.webhooks[webhook_id].stats.copy()
            return {}
        
        # Return aggregated stats
        total_stats = {
            'total_webhooks': len(self.webhooks),
            'enabled_webhooks': sum(1 for w in self.webhooks.values() if w.enabled),
            'events_received': sum(w.stats['events_received'] for w in self.webhooks.values()),
            'events_matched': sum(w.stats['events_matched'] for w in self.webhooks.values()),
            'events_handled': sum(w.stats['events_handled'] for w in self.webhooks.values()),
            'events_failed': sum(w.stats['events_failed'] for w in self.webhooks.values()),
        }
        return total_stats
    
    def list_webhooks(self) -> List[str]:
        """
        List all registered webhook IDs.
        
        :return: List of webhook IDs
        """
        return list(self.webhooks.keys())

