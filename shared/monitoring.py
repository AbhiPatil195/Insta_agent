"""Monitoring and metrics utilities."""
import time
from contextlib import contextmanager
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)


@contextmanager
def track_duration(operation: str):
    """
    Context manager to track operation duration.
    
    Usage:
        with track_duration("process_message"):
            # do work
            pass
    """
    start = time.time()
    try:
        yield
    finally:
        duration_ms = (time.time() - start) * 1000
        logger.info(f"{operation} completed", extra={"duration_ms": duration_ms, "operation": operation})


class Metrics:
    """Simple in-memory metrics collector (replace with Prometheus/StatsD in prod)."""
    
    def __init__(self):
        self._counters = {}
        self._gauges = {}
        self._histograms = {}
    
    def increment(self, metric: str, value: int = 1, tags: dict = None):
        """Increment a counter metric."""
        key = self._make_key(metric, tags)
        self._counters[key] = self._counters.get(key, 0) + value
        logger.debug(f"Metric {metric} incremented by {value}", extra={"metric": metric, "value": value, "tags": tags})
    
    def gauge(self, metric: str, value: float, tags: dict = None):
        """Set a gauge metric."""
        key = self._make_key(metric, tags)
        self._gauges[key] = value
        logger.debug(f"Metric {metric} set to {value}", extra={"metric": metric, "value": value, "tags": tags})
    
    def histogram(self, metric: str, value: float, tags: dict = None):
        """Record a histogram value."""
        key = self._make_key(metric, tags)
        if key not in self._histograms:
            self._histograms[key] = []
        self._histograms[key].append(value)
        logger.debug(f"Metric {metric} recorded {value}", extra={"metric": metric, "value": value, "tags": tags})
    
    def _make_key(self, metric: str, tags: dict = None) -> str:
        if not tags:
            return metric
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{metric}[{tag_str}]"
    
    def get_stats(self) -> dict:
        """Get all collected metrics."""
        return {
            "counters": self._counters,
            "gauges": self._gauges,
            "histograms": {
                k: {
                    "count": len(v),
                    "min": min(v) if v else 0,
                    "max": max(v) if v else 0,
                    "avg": sum(v) / len(v) if v else 0
                }
                for k, v in self._histograms.items()
            }
        }
    
    def reset(self):
        """Reset all metrics."""
        self._counters.clear()
        self._gauges.clear()
        self._histograms.clear()


# Global metrics instance
_metrics = Metrics()


def get_metrics() -> Metrics:
    """Get the global metrics instance."""
    return _metrics


# Health check utilities
class HealthCheck:
    """Health check coordinator."""
    
    def __init__(self):
        self._checks = {}
    
    def register(self, name: str, check_fn: Callable[[], bool], critical: bool = False):
        """
        Register a health check.
        
        Args:
            name: Check name
            check_fn: Function that returns True if healthy
            critical: If True, service is unhealthy if this check fails
        """
        self._checks[name] = {"fn": check_fn, "critical": critical}
    
    def run_checks(self) -> dict:
        """Run all health checks and return status."""
        results = {}
        overall_status = "healthy"
        
        for name, check in self._checks.items():
            try:
                is_healthy = check["fn"]()
                results[name] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "critical": check["critical"]
                }
                if not is_healthy and check["critical"]:
                    overall_status = "unhealthy"
                elif not is_healthy:
                    overall_status = "degraded" if overall_status == "healthy" else overall_status
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e),
                    "critical": check["critical"]
                }
                if check["critical"]:
                    overall_status = "unhealthy"
        
        return {
            "status": overall_status,
            "checks": results
        }


# Global health check instance
_health_check = HealthCheck()


def get_health_check() -> HealthCheck:
    """Get the global health check instance."""
    return _health_check


# Alerting helpers (extend with actual alerting service)
class Alert:
    """Simple alerting utility."""
    
    @staticmethod
    def critical(message: str, context: dict = None):
        """Send critical alert."""
        logger.critical(f"ALERT: {message}", extra=context or {})
        # TODO: Integrate with PagerDuty, Slack, email, etc.
    
    @staticmethod
    def warning(message: str, context: dict = None):
        """Send warning alert."""
        logger.warning(f"WARNING: {message}", extra=context or {})
        # TODO: Integrate with notification service
    
    @staticmethod
    def info(message: str, context: dict = None):
        """Send info notification."""
        logger.info(f"INFO: {message}", extra=context or {})
