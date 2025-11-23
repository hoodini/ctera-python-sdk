"""
Webhook event definitions and filtering.
"""

import re
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from ..common import Object


class EventType(str, Enum):
    """Event types for webhook notifications"""
    
    # File events
    FILE_CREATED = "file.created"
    FILE_MODIFIED = "file.modified"
    FILE_DELETED = "file.deleted"
    FILE_MOVED = "file.moved"
    FILE_RENAMED = "file.renamed"
    
    # Folder events
    FOLDER_CREATED = "folder.created"
    FOLDER_DELETED = "folder.deleted"
    FOLDER_MOVED = "folder.moved"
    FOLDER_RENAMED = "folder.renamed"
    
    # User events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_LOGIN_FAILED = "user.login_failed"
    
    # Device events
    DEVICE_REGISTERED = "device.registered"
    DEVICE_UPDATED = "device.updated"
    DEVICE_DELETED = "device.deleted"
    DEVICE_ONLINE = "device.online"
    DEVICE_OFFLINE = "device.offline"
    
    # Share events
    SHARE_CREATED = "share.created"
    SHARE_UPDATED = "share.updated"
    SHARE_DELETED = "share.deleted"
    
    # Permission events
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"
    
    # Storage events
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"
    
    # Security events
    RANSOMWARE_DETECTED = "security.ransomware_detected"
    ANOMALY_DETECTED = "security.anomaly_detected"
    SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    
    # System events
    BACKUP_COMPLETED = "backup.completed"
    BACKUP_FAILED = "backup.failed"
    SYNC_COMPLETED = "sync.completed"
    SYNC_FAILED = "sync.failed"


class WebhookEvent(Object):
    """
    Represents a webhook event.
    """
    
    def __init__(
        self,
        event_type: EventType,
        event_id: str,
        timestamp: datetime,
        data: Dict[str, Any],
        source: Optional[str] = None,
        user: Optional[str] = None
    ):
        """
        Initialize webhook event.
        
        :param EventType event_type: Type of event
        :param str event_id: Unique event identifier
        :param datetime timestamp: Event timestamp
        :param dict data: Event data payload
        :param str source: Source of the event (e.g., device name, portal)
        :param str user: User associated with the event
        """
        super().__init__()
        self.event_type = event_type
        self.event_id = event_id
        self.timestamp = timestamp
        self.data = data
        self.source = source
        self.user = user
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            'event_type': self.event_type.value if isinstance(self.event_type, EventType) else self.event_type,
            'event_id': self.event_id,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else self.timestamp,
            'data': self.data,
            'source': self.source,
            'user': self.user,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebhookEvent':
        """Create event from dictionary"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            event_type=EventType(data['event_type']),
            event_id=data['event_id'],
            timestamp=timestamp,
            data=data.get('data', {}),
            source=data.get('source'),
            user=data.get('user')
        )


class EventFilter:
    """
    Filter for webhook events.
    """
    
    def __init__(self):
        """Initialize event filter"""
        self.event_types: List[EventType] = []
        self.sources: List[str] = []
        self.users: List[str] = []
        self.path_patterns: List[re.Pattern] = []
        self.custom_filters: List[Callable[[WebhookEvent], bool]] = []
    
    def add_event_type(self, event_type: EventType) -> 'EventFilter':
        """
        Add event type to filter.
        
        :param EventType event_type: Event type to include
        :return: Self for method chaining
        """
        if event_type not in self.event_types:
            self.event_types.append(event_type)
        return self
    
    def add_source(self, source: str) -> 'EventFilter':
        """
        Add source to filter.
        
        :param str source: Source to include
        :return: Self for method chaining
        """
        if source not in self.sources:
            self.sources.append(source)
        return self
    
    def add_user(self, user: str) -> 'EventFilter':
        """
        Add user to filter.
        
        :param str user: User to include
        :return: Self for method chaining
        """
        if user not in self.users:
            self.users.append(user)
        return self
    
    def add_path_pattern(self, pattern: str) -> 'EventFilter':
        """
        Add path pattern to filter (for file events).
        
        :param str pattern: Regex pattern for file paths
        :return: Self for method chaining
        """
        compiled_pattern = re.compile(pattern)
        self.path_patterns.append(compiled_pattern)
        return self
    
    def add_custom_filter(self, filter_func: Callable[[WebhookEvent], bool]) -> 'EventFilter':
        """
        Add custom filter function.
        
        :param callable filter_func: Function that takes WebhookEvent and returns bool
        :return: Self for method chaining
        """
        self.custom_filters.append(filter_func)
        return self
    
    def matches(self, event: WebhookEvent) -> bool:
        """
        Check if event matches filter criteria.
        
        :param WebhookEvent event: Event to check
        :return: True if event matches filter
        """
        # Check event type filter
        if self.event_types and event.event_type not in self.event_types:
            return False
        
        # Check source filter
        if self.sources and event.source not in self.sources:
            return False
        
        # Check user filter
        if self.users and event.user not in self.users:
            return False
        
        # Check path pattern filter (for file events)
        if self.path_patterns:
            path = event.data.get('path')
            if not path or not any(pattern.match(path) for pattern in self.path_patterns):
                return False
        
        # Check custom filters
        for custom_filter in self.custom_filters:
            if not custom_filter(event):
                return False
        
        return True
    
    def clear(self) -> 'EventFilter':
        """Clear all filters"""
        self.event_types.clear()
        self.sources.clear()
        self.users.clear()
        self.path_patterns.clear()
        self.custom_filters.clear()
        return self

