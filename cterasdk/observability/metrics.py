"""
Metrics collection for SDK operations.
"""

import time
import threading
from enum import Enum
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from datetime import datetime


class MetricType(str, Enum):
    """Types of metrics"""
    COUNTER = "counter"  # Monotonically increasing value
    GAUGE = "gauge"  # Point-in-time value
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Statistical summary


class Metric:
    """Represents a metric measurement"""
    
    def __init__(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Initialize metric.
        
        :param str name: Metric name
        :param MetricType metric_type: Type of metric
        :param float value: Metric value
        :param dict tags: Optional tags/labels
        :param datetime timestamp: Timestamp (defaults to now)
        """
        self.name = name
        self.metric_type = metric_type
        self.value = value
        self.tags = tags or {}
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary"""
        return {
            'name': self.name,
            'type': self.metric_type.value,
            'value': self.value,
            'tags': self.tags,
            'timestamp': self.timestamp.isoformat(),
        }


class MetricsCollector:
    """
    Collects and aggregates metrics from SDK operations.
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize metrics collector.
        
        :param int max_history: Maximum number of historical data points to keep
        """
        self.max_history = max_history
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._summaries: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        
        # Built-in SDK metrics
        self._initialize_builtin_metrics()
    
    def _initialize_builtin_metrics(self):
        """Initialize built-in SDK metrics"""
        self.increment("sdk.requests.total", 0)
        self.increment("sdk.requests.success", 0)
        self.increment("sdk.requests.error", 0)
        self.set_gauge("sdk.active_connections", 0)
    
    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """
        Increment a counter metric.
        
        :param str name: Metric name
        :param float value: Value to add
        :param dict tags: Optional tags
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Set a gauge metric value.
        
        :param str name: Metric name
        :param float value: Current value
        :param dict tags: Optional tags
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._gauges[key] = value
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Record a histogram value.
        
        :param str name: Metric name
        :param float value: Value to record
        :param dict tags: Optional tags
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._histograms[key].append(value)
    
    def observe_summary(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """
        Observe a value for summary statistics.
        
        :param str name: Metric name
        :param float value: Value to observe
        :param dict tags: Optional tags
        """
        key = self._make_key(name, tags)
        with self._lock:
            self._summaries[key].append(value)
            # Keep only recent observations
            if len(self._summaries[key]) > self.max_history:
                self._summaries[key] = self._summaries[key][-self.max_history:]
    
    def get_counter(self, name: str, tags: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, tags)
        with self._lock:
            return self._counters.get(key, 0.0)
    
    def get_gauge(self, name: str, tags: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Get gauge value"""
        key = self._make_key(name, tags)
        with self._lock:
            return self._gauges.get(key)
    
    def get_histogram_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Get histogram statistics.
        
        :return: Dictionary with min, max, mean, p50, p95, p99
        """
        key = self._make_key(name, tags)
        with self._lock:
            values = list(self._histograms.get(key, []))
        
        if not values:
            return {}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        
        return {
            'count': count,
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'mean': sum(sorted_values) / count,
            'p50': sorted_values[int(count * 0.50)],
            'p95': sorted_values[int(count * 0.95)],
            'p99': sorted_values[int(count * 0.99)],
        }
    
    def get_summary_stats(self, name: str, tags: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """
        Get summary statistics.
        
        :return: Dictionary with count, sum, mean, min, max
        """
        key = self._make_key(name, tags)
        with self._lock:
            values = list(self._summaries.get(key, []))
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'sum': sum(values),
            'mean': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
        }
    
    def get_all_metrics(self) -> List[Metric]:
        """
        Get all current metrics.
        
        :return: List of all metrics
        """
        metrics = []
        
        with self._lock:
            # Counters
            for key, value in self._counters.items():
                name, tags = self._parse_key(key)
                metrics.append(Metric(name, MetricType.COUNTER, value, tags))
            
            # Gauges
            for key, value in self._gauges.items():
                name, tags = self._parse_key(key)
                metrics.append(Metric(name, MetricType.GAUGE, value, tags))
        
        return metrics
    
    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._summaries.clear()
            self._initialize_builtin_metrics()
    
    @staticmethod
    def _make_key(name: str, tags: Optional[Dict[str, str]] = None) -> str:
        """Create a unique key from name and tags"""
        if not tags:
            return name
        tag_str = ','.join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}{{{tag_str}}}"
    
    @staticmethod
    def _parse_key(key: str) -> tuple:
        """Parse key back into name and tags"""
        if '{' not in key:
            return key, {}
        
        name, tag_str = key.split('{', 1)
        tag_str = tag_str.rstrip('}')
        
        tags = {}
        if tag_str:
            for pair in tag_str.split(','):
                k, v = pair.split('=', 1)
                tags[k] = v
        
        return name, tags


class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, collector: MetricsCollector, metric_name: str, tags: Optional[Dict[str, str]] = None):
        """
        Initialize performance timer.
        
        :param MetricsCollector collector: Metrics collector
        :param str metric_name: Name for the timing metric
        :param dict tags: Optional tags
        """
        self.collector = collector
        self.metric_name = metric_name
        self.tags = tags
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and record metric"""
        duration = time.time() - self.start_time
        self.collector.record_histogram(self.metric_name, duration, self.tags)
        
        # Also track success/error
        if exc_type is None:
            self.collector.increment("sdk.requests.success", 1, self.tags)
        else:
            self.collector.increment("sdk.requests.error", 1, self.tags)

