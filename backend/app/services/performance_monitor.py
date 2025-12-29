"""
Performance monitoring service for HealthInsightCore
Tracks API response times, database query performance, and system metrics
"""

import asyncio
import time
import psutil
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Performance metric data structure"""
    timestamp: datetime
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    user_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SystemMetrics:
    """System resource metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_connections: int


class PerformanceMonitor:
    """Performance monitoring and metrics collection service"""
    
    def __init__(self, max_metrics: int = 10000, retention_hours: int = 24):
        self.max_metrics = max_metrics
        self.retention_hours = retention_hours
        self.metrics: deque = deque(maxlen=max_metrics)
        self.system_metrics: deque = deque(maxlen=max_metrics)
        self.endpoint_stats = defaultdict(list)
        self.slow_queries = deque(maxlen=100)
        self._lock = asyncio.Lock()
        self._monitoring_task = None
        self._is_monitoring = False
    
    async def start_monitoring(self):
        """Start background monitoring task"""
        if not self._is_monitoring:
            self._is_monitoring = True
            self._monitoring_task = asyncio.create_task(self._monitor_system_metrics())
            logger.info("Performance monitoring started")
    
    async def stop_monitoring(self):
        """Stop background monitoring task"""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Performance monitoring stopped")
    
    async def record_request(
        self,
        endpoint: str,
        method: str,
        response_time_ms: float,
        status_code: int,
        user_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Record API request performance metric"""
        async with self._lock:
            metric = PerformanceMetric(
                timestamp=datetime.utcnow(),
                endpoint=endpoint,
                method=method,
                response_time_ms=response_time_ms,
                status_code=status_code,
                user_id=user_id,
                error=error
            )
            
            self.metrics.append(metric)
            self.endpoint_stats[f"{method} {endpoint}"].append(response_time_ms)
            
            # Track slow requests
            if response_time_ms > 1000:  # Requests slower than 1 second
                self.slow_queries.append(metric)
            
            # Clean up old endpoint stats
            await self._cleanup_endpoint_stats()
    
    async def record_database_query(
        self,
        operation: str,
        collection: str,
        execution_time_ms: float,
        query_details: Optional[Dict[str, Any]] = None
    ):
        """Record database query performance"""
        if execution_time_ms > 500:  # Slow queries > 500ms
            slow_query = {
                "timestamp": datetime.utcnow(),
                "operation": operation,
                "collection": collection,
                "execution_time_ms": execution_time_ms,
                "query_details": query_details
            }
            self.slow_queries.append(slow_query)
    
    async def _monitor_system_metrics(self):
        """Background task to monitor system metrics"""
        while self._is_monitoring:
            try:
                # Get system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Get network connections (approximate active connections)
                connections = len(psutil.net_connections(kind='inet'))
                
                system_metric = SystemMetrics(
                    timestamp=datetime.utcnow(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    memory_used_mb=memory.used / (1024 * 1024),
                    memory_available_mb=memory.available / (1024 * 1024),
                    disk_usage_percent=disk.percent,
                    active_connections=connections
                )
                
                async with self._lock:
                    self.system_metrics.append(system_metric)
                
                # Clean up old metrics
                await self._cleanup_old_metrics()
                
                # Wait before next collection
                await asyncio.sleep(60)  # Collect every minute
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        # Clean up request metrics
        while self.metrics and self.metrics[0].timestamp < cutoff_time:
            self.metrics.popleft()
        
        # Clean up system metrics
        while self.system_metrics and self.system_metrics[0].timestamp < cutoff_time:
            self.system_metrics.popleft()
    
    async def _cleanup_endpoint_stats(self):
        """Keep only recent endpoint stats"""
        max_stats_per_endpoint = 1000
        for endpoint in self.endpoint_stats:
            if len(self.endpoint_stats[endpoint]) > max_stats_per_endpoint:
                # Keep only the most recent stats
                self.endpoint_stats[endpoint] = self.endpoint_stats[endpoint][-max_stats_per_endpoint:]
    
    async def get_performance_summary(self, hours_back: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period"""
        async with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Filter recent metrics
            recent_metrics = [
                m for m in self.metrics 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    "period_hours": hours_back,
                    "total_requests": 0,
                    "message": "No metrics available for the specified period"
                }
            
            # Calculate statistics
            response_times = [m.response_time_ms for m in recent_metrics]
            status_codes = [m.status_code for m in recent_metrics]
            
            # Group by endpoint
            endpoint_stats = defaultdict(list)
            for metric in recent_metrics:
                endpoint_key = f"{metric.method} {metric.endpoint}"
                endpoint_stats[endpoint_key].append(metric.response_time_ms)
            
            # Calculate endpoint statistics
            endpoint_summary = {}
            for endpoint, times in endpoint_stats.items():
                endpoint_summary[endpoint] = {
                    "request_count": len(times),
                    "avg_response_time_ms": round(sum(times) / len(times), 2),
                    "min_response_time_ms": round(min(times), 2),
                    "max_response_time_ms": round(max(times), 2),
                    "p95_response_time_ms": round(self._percentile(times, 95), 2),
                    "p99_response_time_ms": round(self._percentile(times, 99), 2)
                }
            
            # Error analysis
            error_count = len([m for m in recent_metrics if m.status_code >= 400])
            error_rate = (error_count / len(recent_metrics)) * 100 if recent_metrics else 0
            
            # Slow requests
            slow_requests = [m for m in recent_metrics if m.response_time_ms > 1000]
            
            return {
                "period_hours": hours_back,
                "total_requests": len(recent_metrics),
                "avg_response_time_ms": round(sum(response_times) / len(response_times), 2),
                "min_response_time_ms": round(min(response_times), 2),
                "max_response_time_ms": round(max(response_times), 2),
                "p95_response_time_ms": round(self._percentile(response_times, 95), 2),
                "p99_response_time_ms": round(self._percentile(response_times, 99), 2),
                "error_count": error_count,
                "error_rate_percent": round(error_rate, 2),
                "slow_requests_count": len(slow_requests),
                "endpoint_stats": endpoint_summary,
                "status_code_distribution": self._get_status_code_distribution(status_codes)
            }
    
    async def get_system_metrics_summary(self, hours_back: int = 1) -> Dict[str, Any]:
        """Get system metrics summary"""
        async with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            recent_metrics = [
                m for m in self.system_metrics 
                if m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    "period_hours": hours_back,
                    "message": "No system metrics available for the specified period"
                }
            
            # Calculate averages
            cpu_values = [m.cpu_percent for m in recent_metrics]
            memory_values = [m.memory_percent for m in recent_metrics]
            disk_values = [m.disk_usage_percent for m in recent_metrics]
            connection_values = [m.active_connections for m in recent_metrics]
            
            return {
                "period_hours": hours_back,
                "data_points": len(recent_metrics),
                "cpu": {
                    "avg_percent": round(sum(cpu_values) / len(cpu_values), 2),
                    "max_percent": round(max(cpu_values), 2),
                    "min_percent": round(min(cpu_values), 2)
                },
                "memory": {
                    "avg_percent": round(sum(memory_values) / len(memory_values), 2),
                    "max_percent": round(max(memory_values), 2),
                    "min_percent": round(min(memory_values), 2),
                    "avg_used_mb": round(sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics), 2)
                },
                "disk": {
                    "avg_percent": round(sum(disk_values) / len(disk_values), 2),
                    "max_percent": round(max(disk_values), 2),
                    "min_percent": round(min(disk_values), 2)
                },
                "connections": {
                    "avg_count": round(sum(connection_values) / len(connection_values), 2),
                    "max_count": max(connection_values),
                    "min_count": min(connection_values)
                }
            }
    
    async def get_slow_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent slow queries"""
        async with self._lock:
            slow_queries = list(self.slow_queries)[-limit:]
            return [
                {
                    "timestamp": q.timestamp.isoformat() if hasattr(q, 'timestamp') else q.get('timestamp', '').isoformat(),
                    "endpoint": getattr(q, 'endpoint', q.get('operation', 'unknown')),
                    "method": getattr(q, 'method', q.get('collection', 'unknown')),
                    "response_time_ms": getattr(q, 'response_time_ms', q.get('execution_time_ms', 0)),
                    "status_code": getattr(q, 'status_code', None),
                    "error": getattr(q, 'error', None)
                }
                for q in reversed(slow_queries)
            ]
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        try:
            # Get recent performance data
            perf_summary = await self.get_performance_summary(hours_back=1)
            system_summary = await self.get_system_metrics_summary(hours_back=1)
            
            # Determine health status
            health_issues = []
            
            # Check error rate
            error_rate = perf_summary.get("error_rate_percent", 0)
            if error_rate > 5:  # More than 5% errors
                health_issues.append(f"High error rate: {error_rate}%")
            
            # Check response times
            avg_response_time = perf_summary.get("avg_response_time_ms", 0)
            if avg_response_time > 2000:  # Average response time > 2 seconds
                health_issues.append(f"Slow response times: {avg_response_time}ms average")
            
            # Check system resources
            if system_summary.get("cpu", {}).get("avg_percent", 0) > 80:
                health_issues.append("High CPU usage")
            
            if system_summary.get("memory", {}).get("avg_percent", 0) > 85:
                health_issues.append("High memory usage")
            
            if system_summary.get("disk", {}).get("avg_percent", 0) > 90:
                health_issues.append("High disk usage")
            
            # Determine overall status
            if not health_issues:
                status = "healthy"
            elif len(health_issues) <= 2:
                status = "warning"
            else:
                status = "critical"
            
            return {
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
                "issues": health_issues,
                "performance_summary": perf_summary,
                "system_summary": system_summary
            }
            
        except Exception as e:
            logger.error(f"Error getting health status: {e}")
            return {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of a list of numbers"""
        if not data:
            return 0.0
        
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower_index = int(index)
            upper_index = lower_index + 1
            weight = index - lower_index
            return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def _get_status_code_distribution(self, status_codes: List[int]) -> Dict[str, int]:
        """Get distribution of HTTP status codes"""
        distribution = defaultdict(int)
        for code in status_codes:
            if 200 <= code < 300:
                distribution["2xx"] += 1
            elif 300 <= code < 400:
                distribution["3xx"] += 1
            elif 400 <= code < 500:
                distribution["4xx"] += 1
            elif 500 <= code < 600:
                distribution["5xx"] += 1
            else:
                distribution["other"] += 1
        
        return dict(distribution)


# Performance monitoring middleware
class PerformanceMiddleware:
    """Middleware to automatically track API performance"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
    
    async def __call__(self, request, call_next):
        """Process request and record performance metrics"""
        start_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time_ms = (time.time() - start_time) * 1000
            
            # Extract user ID if available
            user_id = None
            if hasattr(request.state, 'user'):
                user_id = getattr(request.state.user, 'uid', None)
            
            # Record the metric
            await self.monitor.record_request(
                endpoint=request.url.path,
                method=request.method,
                response_time_ms=response_time_ms,
                status_code=response.status_code,
                user_id=user_id
            )
            
            return response
            
        except Exception as e:
            # Record error metric
            response_time_ms = (time.time() - start_time) * 1000
            
            await self.monitor.record_request(
                endpoint=request.url.path,
                method=request.method,
                response_time_ms=response_time_ms,
                status_code=500,
                error=str(e)
            )
            
            raise


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return performance_monitor