"""
Distributed tracing support for SDK operations.
"""

import time
import uuid
import threading
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class SpanKind(str, Enum):
    """Span kind enumeration"""
    CLIENT = "client"
    SERVER = "server"
    INTERNAL = "internal"


class SpanStatus(str, Enum):
    """Span status enumeration"""
    OK = "ok"
    ERROR = "error"
    UNSET = "unset"


class Span:
    """Represents a trace span"""
    
    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL
    ):
        """
        Initialize span.
        
        :param str name: Span name
        :param str trace_id: Trace ID
        :param str span_id: Span ID
        :param str parent_span_id: Parent span ID
        :param SpanKind kind: Span kind
        """
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.kind = kind
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = SpanStatus.UNSET
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []
    
    def set_attribute(self, key: str, value: Any):
        """
        Set span attribute.
        
        :param str key: Attribute key
        :param value: Attribute value
        """
        self.attributes[key] = value
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to the span.
        
        :param str name: Event name
        :param dict attributes: Event attributes
        """
        event = {
            'name': name,
            'timestamp': time.time(),
            'attributes': attributes or {}
        }
        self.events.append(event)
    
    def set_status(self, status: SpanStatus, description: Optional[str] = None):
        """
        Set span status.
        
        :param SpanStatus status: Status
        :param str description: Status description
        """
        self.status = status
        if description:
            self.attributes['status.description'] = description
    
    def end(self):
        """End the span"""
        if self.end_time is None:
            self.end_time = time.time()
    
    @property
    def duration(self) -> Optional[float]:
        """Get span duration in seconds"""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            'name': self.name,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'kind': self.kind.value,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'status': self.status.value,
            'attributes': self.attributes,
            'events': self.events,
        }


class TracingManager:
    """
    Manages distributed tracing for SDK operations.
    """
    
    def __init__(self, enabled: bool = True):
        """
        Initialize tracing manager.
        
        :param bool enabled: Whether tracing is enabled
        """
        self.enabled = enabled
        self._current_span = threading.local()
        self._completed_spans: List[Span] = []
        self._lock = threading.Lock()
    
    def start_span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Span:
        """
        Start a new span.
        
        :param str name: Span name
        :param SpanKind kind: Span kind
        :param dict attributes: Initial attributes
        :return: New span
        """
        if not self.enabled:
            return self._create_noop_span()
        
        parent_span = self.get_current_span()
        
        if parent_span:
            trace_id = parent_span.trace_id
            parent_span_id = parent_span.span_id
        else:
            trace_id = self._generate_trace_id()
            parent_span_id = None
        
        span_id = self._generate_span_id()
        span = Span(name, trace_id, span_id, parent_span_id, kind)
        
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        self._current_span.span = span
        return span
    
    def end_span(self, span: Span):
        """
        End a span.
        
        :param Span span: Span to end
        """
        if not self.enabled:
            return
        
        span.end()
        
        with self._lock:
            self._completed_spans.append(span)
        
        # Clear current span
        if hasattr(self._current_span, 'span') and self._current_span.span == span:
            self._current_span.span = None
    
    def get_current_span(self) -> Optional[Span]:
        """
        Get the current span in this thread.
        
        :return: Current span or None
        """
        return getattr(self._current_span, 'span', None)
    
    def get_completed_spans(self, limit: Optional[int] = None) -> List[Span]:
        """
        Get completed spans.
        
        :param int limit: Maximum number of spans to return
        :return: List of completed spans
        """
        with self._lock:
            if limit:
                return self._completed_spans[-limit:]
            return self._completed_spans.copy()
    
    def clear_completed_spans(self):
        """Clear all completed spans"""
        with self._lock:
            self._completed_spans.clear()
    
    @staticmethod
    def _generate_trace_id() -> str:
        """Generate a unique trace ID"""
        return uuid.uuid4().hex
    
    @staticmethod
    def _generate_span_id() -> str:
        """Generate a unique span ID"""
        return uuid.uuid4().hex[:16]
    
    @staticmethod
    def _create_noop_span() -> Span:
        """Create a no-op span when tracing is disabled"""
        return Span("noop", "0", "0")


class TracingContext:
    """Context manager for tracing operations"""
    
    def __init__(
        self,
        tracing_manager: TracingManager,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize tracing context.
        
        :param TracingManager tracing_manager: Tracing manager
        :param str name: Span name
        :param SpanKind kind: Span kind
        :param dict attributes: Initial attributes
        """
        self.tracing_manager = tracing_manager
        self.name = name
        self.kind = kind
        self.attributes = attributes
        self.span: Optional[Span] = None
    
    def __enter__(self) -> Span:
        """Start span"""
        self.span = self.tracing_manager.start_span(self.name, self.kind, self.attributes)
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End span"""
        if self.span:
            if exc_type is not None:
                self.span.set_status(SpanStatus.ERROR, str(exc_val))
            else:
                self.span.set_status(SpanStatus.OK)
            self.tracing_manager.end_span(self.span)

