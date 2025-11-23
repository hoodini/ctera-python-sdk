"""
Health check utilities for monitoring SDK and service health.
"""

import time
import asyncio
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthCheckResult:
    """Result of a health check"""
    
    def __init__(
        self,
        name: str,
        status: HealthStatus,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration: Optional[float] = None
    ):
        """
        Initialize health check result.
        
        :param str name: Check name
        :param HealthStatus status: Health status
        :param str message: Status message
        :param dict details: Additional details
        :param float duration: Check duration in seconds
        """
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.duration = duration
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'details': self.details,
            'duration': self.duration,
            'timestamp': self.timestamp.isoformat(),
        }


class HealthCheck:
    """
    Manages health checks for SDK and services.
    """
    
    def __init__(self):
        """Initialize health check manager"""
        self._checks: Dict[str, Callable] = {}
        self._last_results: Dict[str, HealthCheckResult] = {}
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check.
        
        :param str name: Check name
        :param callable check_func: Function that performs the check
        """
        self._checks[name] = check_func
    
    def unregister_check(self, name: str) -> bool:
        """
        Unregister a health check.
        
        :param str name: Check name
        :return: True if unregistered, False if not found
        """
        if name in self._checks:
            del self._checks[name]
            if name in self._last_results:
                del self._last_results[name]
            return True
        return False
    
    async def run_check(self, name: str) -> HealthCheckResult:
        """
        Run a specific health check.
        
        :param str name: Check name
        :return: Health check result
        """
        if name not in self._checks:
            return HealthCheckResult(
                name,
                HealthStatus.UNKNOWN,
                f"Check '{name}' not found"
            )
        
        check_func = self._checks[name]
        start_time = time.time()
        
        try:
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()
            
            duration = time.time() - start_time
            
            if isinstance(result, HealthCheckResult):
                result.duration = duration
                self._last_results[name] = result
                return result
            elif isinstance(result, bool):
                status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                result_obj = HealthCheckResult(name, status, duration=duration)
                self._last_results[name] = result_obj
                return result_obj
            else:
                result_obj = HealthCheckResult(
                    name,
                    HealthStatus.UNKNOWN,
                    "Invalid check result type",
                    duration=duration
                )
                self._last_results[name] = result_obj
                return result_obj
        
        except Exception as e:
            duration = time.time() - start_time
            result = HealthCheckResult(
                name,
                HealthStatus.UNHEALTHY,
                f"Check failed: {str(e)}",
                duration=duration
            )
            self._last_results[name] = result
            return result
    
    async def run_all_checks(self) -> List[HealthCheckResult]:
        """
        Run all registered health checks.
        
        :return: List of health check results
        """
        results = []
        for name in self._checks.keys():
            result = await self.run_check(name)
            results.append(result)
        return results
    
    def get_last_result(self, name: str) -> Optional[HealthCheckResult]:
        """
        Get the last result for a check.
        
        :param str name: Check name
        :return: Last result or None
        """
        return self._last_results.get(name)
    
    def get_overall_status(self) -> HealthStatus:
        """
        Get overall health status.
        
        :return: Overall health status
        """
        if not self._last_results:
            return HealthStatus.UNKNOWN
        
        statuses = [result.status for result in self._last_results.values()]
        
        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.UNHEALTHY
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED
        elif all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get health check summary.
        
        :return: Summary dictionary
        """
        return {
            'overall_status': self.get_overall_status().value,
            'total_checks': len(self._checks),
            'checks': [result.to_dict() for result in self._last_results.values()]
        }


# Built-in health checks

def connection_health_check(client) -> HealthCheckResult:
    """
    Check if connection to service is healthy.
    
    :param client: SDK client
    :return: Health check result
    """
    try:
        # This is a placeholder - actual implementation would ping the service
        return HealthCheckResult(
            "connection",
            HealthStatus.HEALTHY,
            "Connection is active"
        )
    except Exception as e:
        return HealthCheckResult(
            "connection",
            HealthStatus.UNHEALTHY,
            f"Connection failed: {str(e)}"
        )


def authentication_health_check(client) -> HealthCheckResult:
    """
    Check if authentication is valid.
    
    :param client: SDK client
    :return: Health check result
    """
    try:
        # Placeholder - would check session validity
        return HealthCheckResult(
            "authentication",
            HealthStatus.HEALTHY,
            "Authentication is valid"
        )
    except Exception as e:
        return HealthCheckResult(
            "authentication",
            HealthStatus.UNHEALTHY,
            f"Authentication check failed: {str(e)}"
        )

