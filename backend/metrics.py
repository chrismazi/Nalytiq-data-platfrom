"""
Enhanced Metrics Module

Production-grade metrics collection for:
- API performance
- Business metrics
- System resources
- Custom application metrics
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta
from collections import defaultdict
from threading import Lock
import asyncio

logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Comprehensive metrics collector for the platform.
    Collects API, business, and system metrics.
    """
    
    def __init__(self):
        self._lock = Lock()
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, list] = defaultdict(list)
        self._summaries: Dict[str, Dict[str, float]] = {}
        self._start_time = datetime.utcnow()
        
        # API metrics
        self._request_count = 0
        self._request_latencies: Dict[str, list] = defaultdict(list)
        self._status_codes: Dict[int, int] = defaultdict(int)
        self._endpoint_hits: Dict[str, int] = defaultdict(int)
        
        # Business metrics
        self._active_users = 0
        self._dataset_accesses = 0
        self._queries_executed = 0
        self._ml_trainings = 0
        
        # Error tracking
        self._errors: Dict[str, int] = defaultdict(int)
        self._last_errors: list = []
    
    # ==========================================
    # Counter Operations
    # ==========================================
    
    def increment(self, name: str, value: int = 1, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._counters[key] += value
    
    def get_counter(self, name: str, labels: Dict[str, str] = None) -> int:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)
    
    # ==========================================
    # Gauge Operations
    # ==========================================
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric"""
        key = self._make_key(name, labels)
        with self._lock:
            self._gauges[key] = value
    
    def get_gauge(self, name: str, labels: Dict[str, str] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)
    
    # ==========================================
    # Histogram Operations
    # ==========================================
    
    def observe(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Add observation to histogram"""
        key = self._make_key(name, labels)
        with self._lock:
            self._histograms[key].append(value)
            # Keep last 1000 observations
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
    
    def get_histogram(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0, "p50": 0, "p90": 0, "p99": 0}
        
        sorted_values = sorted(values)
        count = len(sorted_values)
        return {
            "count": count,
            "sum": sum(sorted_values),
            "avg": sum(sorted_values) / count,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[int(count * 0.5)],
            "p90": sorted_values[int(count * 0.9)],
            "p99": sorted_values[min(int(count * 0.99), count - 1)],
        }
    
    # ==========================================
    # API Metrics
    # ==========================================
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float
    ) -> None:
        """Record API request metrics"""
        with self._lock:
            self._request_count += 1
            self._status_codes[status_code] += 1
            self._endpoint_hits[f"{method}:{endpoint}"] += 1
            self._request_latencies[endpoint].append(duration_ms)
            
            # Keep last 1000 latencies per endpoint
            if len(self._request_latencies[endpoint]) > 1000:
                self._request_latencies[endpoint] = self._request_latencies[endpoint][-1000:]
    
    def record_error(self, error_type: str, message: str) -> None:
        """Record error occurrence"""
        with self._lock:
            self._errors[error_type] += 1
            self._last_errors.append({
                "type": error_type,
                "message": message[:200],
                "timestamp": datetime.utcnow().isoformat()
            })
            # Keep last 100 errors
            if len(self._last_errors) > 100:
                self._last_errors = self._last_errors[-100:]
    
    # ==========================================
    # Business Metrics
    # ==========================================
    
    def record_user_activity(self, user_id: str) -> None:
        """Record user activity"""
        with self._lock:
            self._active_users += 1
    
    def record_dataset_access(self, dataset_id: str) -> None:
        """Record dataset access"""
        with self._lock:
            self._dataset_accesses += 1
            self.increment("dataset_access", labels={"dataset_id": dataset_id})
    
    def record_query(self, query_type: str, duration_ms: float) -> None:
        """Record query execution"""
        with self._lock:
            self._queries_executed += 1
            self.observe("query_duration_ms", duration_ms, labels={"type": query_type})
    
    def record_ml_training(self, model_type: str, duration_s: float) -> None:
        """Record ML training"""
        with self._lock:
            self._ml_trainings += 1
            self.observe("ml_training_duration_s", duration_s, labels={"type": model_type})
    
    # ==========================================
    # Export Metrics
    # ==========================================
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all metrics"""
        uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        # Calculate latency stats per endpoint
        latency_stats = {}
        for endpoint, latencies in self._request_latencies.items():
            if latencies:
                sorted_lat = sorted(latencies)
                count = len(sorted_lat)
                latency_stats[endpoint] = {
                    "count": count,
                    "avg_ms": sum(sorted_lat) / count,
                    "p50_ms": sorted_lat[int(count * 0.5)],
                    "p90_ms": sorted_lat[int(count * 0.9)],
                    "p99_ms": sorted_lat[min(int(count * 0.99), count - 1)],
                }
        
        return {
            "system": {
                "uptime_seconds": uptime,
                "start_time": self._start_time.isoformat(),
            },
            "api": {
                "total_requests": self._request_count,
                "status_codes": dict(self._status_codes),
                "endpoint_hits": dict(self._endpoint_hits),
                "latency_by_endpoint": latency_stats,
            },
            "business": {
                "active_users": self._active_users,
                "dataset_accesses": self._dataset_accesses,
                "queries_executed": self._queries_executed,
                "ml_trainings": self._ml_trainings,
            },
            "errors": {
                "by_type": dict(self._errors),
                "total": sum(self._errors.values()),
                "recent": self._last_errors[-10:],
            },
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
        }
    
    def to_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []
        metrics = self.get_all_metrics()
        
        # Uptime
        lines.append("# HELP nalytiq_uptime_seconds Application uptime in seconds")
        lines.append("# TYPE nalytiq_uptime_seconds gauge")
        lines.append(f'nalytiq_uptime_seconds {metrics["system"]["uptime_seconds"]:.2f}')
        
        # Request count
        lines.append("# HELP nalytiq_http_requests_total Total HTTP requests")
        lines.append("# TYPE nalytiq_http_requests_total counter")
        lines.append(f'nalytiq_http_requests_total {metrics["api"]["total_requests"]}')
        
        # Status codes
        lines.append("# HELP nalytiq_http_requests_by_status HTTP requests by status code")
        lines.append("# TYPE nalytiq_http_requests_by_status counter")
        for code, count in metrics["api"]["status_codes"].items():
            lines.append(f'nalytiq_http_requests_by_status{{status="{code}"}} {count}')
        
        # Business metrics
        lines.append("# HELP nalytiq_dataset_accesses_total Total dataset accesses")
        lines.append("# TYPE nalytiq_dataset_accesses_total counter")
        lines.append(f'nalytiq_dataset_accesses_total {metrics["business"]["dataset_accesses"]}')
        
        lines.append("# HELP nalytiq_queries_total Total queries executed")
        lines.append("# TYPE nalytiq_queries_total counter")
        lines.append(f'nalytiq_queries_total {metrics["business"]["queries_executed"]}')
        
        lines.append("# HELP nalytiq_ml_trainings_total Total ML trainings")
        lines.append("# TYPE nalytiq_ml_trainings_total counter")
        lines.append(f'nalytiq_ml_trainings_total {metrics["business"]["ml_trainings"]}')
        
        # Errors
        lines.append("# HELP nalytiq_errors_total Total errors")
        lines.append("# TYPE nalytiq_errors_total counter")
        lines.append(f'nalytiq_errors_total {metrics["errors"]["total"]}')
        
        # Custom counters
        for key, value in metrics["counters"].items():
            safe_key = key.replace(".", "_").replace("-", "_")
            lines.append(f'nalytiq_counter_{safe_key} {value}')
        
        # Custom gauges
        for key, value in metrics["gauges"].items():
            safe_key = key.replace(".", "_").replace("-", "_")
            lines.append(f'nalytiq_gauge_{safe_key} {value}')
        
        return "\n".join(lines)
    
    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


def timed(metric_name: str):
    """Decorator to time function execution"""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                metrics_collector.observe(metric_name, duration_ms)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration_ms = (time.perf_counter() - start) * 1000
                metrics_collector.observe(metric_name, duration_ms)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


# Global metrics collector
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector"""
    return metrics_collector
