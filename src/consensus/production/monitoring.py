"""
Monitoring & Metrics Collection - Production Observability

Implements comprehensive monitoring including:
- Performance metrics
- Health checks
- Real-time dashboards
- Alerting system
"""

import asyncio
import time
import psutil
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging
import json

logger = logging.getLogger(__name__)

@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: str  # "healthy", "unhealthy", "degraded"
    message: str
    response_time: float
    timestamp: datetime = field(default_factory=datetime.now)

class MetricsCollector:
    """Production metrics collection and aggregation"""
    
    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.health_checks: Dict[str, HealthCheck] = {}
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": deque(maxlen=1000),
            "requests_per_minute": deque(maxlen=60),
            "last_minute_requests": 0
        }
        self.is_collecting = False
        self.collection_interval = 10  # seconds
        
    async def start_collection(self):
        """Start metrics collection"""
        if self.is_collecting:
            return
            
        self.is_collecting = True
        asyncio.create_task(self._collection_loop())
        asyncio.create_task(self._request_rate_tracker())
        logger.info("📊 Metrics collection started")
        
    async def stop_collection(self):
        """Stop metrics collection"""
        self.is_collecting = False
        logger.info("🛑 Metrics collection stopped")
        
    async def _collection_loop(self):
        """Main metrics collection loop"""
        while self.is_collecting:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()
                await self._cleanup_old_metrics()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)
                
    async def _request_rate_tracker(self):
        """Track requests per minute"""
        while self.is_collecting:
            current_requests = self.request_stats["last_minute_requests"]
            self.request_stats["requests_per_minute"].append(current_requests)
            self.request_stats["last_minute_requests"] = 0
            await asyncio.sleep(60)
            
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        now = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        self.record_metric("cpu_usage_percent", cpu_percent)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        self.record_metric("memory_usage_percent", memory.percent)
        self.record_metric("memory_used_bytes", memory.used)
        self.record_metric("memory_available_bytes", memory.available)
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        self.record_metric("disk_usage_percent", (disk.used / disk.total) * 100)
        self.record_metric("disk_free_bytes", disk.free)
        
        # Network metrics
        net_io = psutil.net_io_counters()
        self.record_metric("network_bytes_sent", net_io.bytes_sent)
        self.record_metric("network_bytes_recv", net_io.bytes_recv)
        
    async def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        # Queue metrics
        try:
            from .job_queue import job_queue
            queue_stats = await job_queue.get_queue_stats()
            self.record_metric("queue_size", queue_stats.get("total_queue_size", 0))
            self.record_metric("jobs_processed", queue_stats.get("jobs_processed", 0))
            self.record_metric("average_processing_time", queue_stats.get("average_processing_time", 0))
        except Exception:
            pass
            
        # Cache metrics
        try:
            from .cache_manager import cache_manager
            cache_stats = cache_manager.get_cache_stats()
            self.record_metric("cache_hit_rate", cache_stats.get("hit_rate", 0))
            self.record_metric("cache_total_requests", cache_stats.get("total_requests", 0))
        except Exception:
            pass
            
        # Circuit breaker metrics
        try:
            from .circuit_breaker import circuit_registry
            cb_stats = circuit_registry.get_all_stats()
            for name, stats in cb_stats.items():
                self.record_metric(f"circuit_breaker_{name}_state", 
                                 1 if stats["state"] == "closed" else 0)
                self.record_metric(f"circuit_breaker_{name}_error_rate", 
                                 stats["error_rate_recent"])
        except Exception:
            pass
            
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a metric value"""
        metric = Metric(name, value, tags=tags or {})
        self.metrics[name].append(metric)
        
    def record_request(self, response_time: float, success: bool):
        """Record request statistics"""
        self.request_stats["total_requests"] += 1
        self.request_stats["last_minute_requests"] += 1
        self.request_stats["response_times"].append(response_time)
        
        if success:
            self.request_stats["successful_requests"] += 1
        else:
            self.request_stats["failed_requests"] += 1
            
    def get_metric_summary(self, metric_name: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get summary statistics for a metric"""
        if metric_name not in self.metrics:
            return {}
            
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        recent_metrics = [m for m in self.metrics[metric_name] if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
            
        values = [m.value for m in recent_metrics]
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "current": values[-1] if values else 0,
            "trend": self._calculate_trend(values[-10:] if len(values) >= 10 else values)
        }
        
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"
            
        recent_avg = sum(values[-3:]) / min(3, len(values))
        earlier_avg = sum(values[:-3]) / max(1, len(values) - 3)
        
        if recent_avg > earlier_avg * 1.1:
            return "increasing"
        elif recent_avg < earlier_avg * 0.9:
            return "decreasing"
        else:
            return "stable"
            
    def get_request_stats(self) -> Dict[str, Any]:
        """Get request statistics"""
        response_times = list(self.request_stats["response_times"])
        requests_per_minute = list(self.request_stats["requests_per_minute"])
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        current_rpm = requests_per_minute[-1] if requests_per_minute else 0
        avg_rpm = sum(requests_per_minute) / len(requests_per_minute) if requests_per_minute else 0
        
        success_rate = 0
        if self.request_stats["total_requests"] > 0:
            success_rate = (self.request_stats["successful_requests"] / 
                          self.request_stats["total_requests"]) * 100
            
        return {
            "total_requests": self.request_stats["total_requests"],
            "successful_requests": self.request_stats["successful_requests"],
            "failed_requests": self.request_stats["failed_requests"],
            "success_rate": round(success_rate, 2),
            "average_response_time": round(avg_response_time, 3),
            "current_requests_per_minute": current_rpm,
            "average_requests_per_minute": round(avg_rpm, 1),
            "p95_response_time": self._calculate_percentile(response_times, 95) if response_times else 0
        }
        
    def _calculate_percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile value"""
        if not values:
            return 0
            
        sorted_values = sorted(values)
        index = int((percentile / 100) * len(sorted_values))
        return sorted_values[min(index, len(sorted_values) - 1)]
        
    def get_average_response_time(self) -> float:
        """Get current average response time"""
        response_times = list(self.request_stats["response_times"])
        return sum(response_times) / len(response_times) if response_times else 0
        
    def get_request_rate(self) -> float:
        """Get current request rate per minute"""
        requests_per_minute = list(self.request_stats["requests_per_minute"])
        return requests_per_minute[-1] if requests_per_minute else 0
        
    async def _cleanup_old_metrics(self):
        """Remove old metrics outside retention window"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        for metric_name in self.metrics:
            # Keep only recent metrics
            self.metrics[metric_name] = deque(
                [m for m in self.metrics[metric_name] if m.timestamp > cutoff_time],
                maxlen=self.metrics[metric_name].maxlen
            )

class HealthChecker:
    """System health monitoring"""
    
    def __init__(self):
        self.health_checks: Dict[str, Callable] = {}
        self.last_check_results: Dict[str, HealthCheck] = {}
        self.is_monitoring = False
        self.check_interval = 30  # seconds
        
    def register_health_check(self, name: str, check_function: Callable):
        """Register a health check function"""
        self.health_checks[name] = check_function
        logger.info(f"💚 Registered health check: {name}")
        
    async def start_monitoring(self):
        """Start health monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("💚 Health monitoring started")
        
    async def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_monitoring = False
        logger.info("🛑 Health monitoring stopped")
        
    async def _monitoring_loop(self):
        """Main health monitoring loop"""
        while self.is_monitoring:
            try:
                await self._run_all_health_checks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
                
    async def _run_all_health_checks(self):
        """Run all registered health checks"""
        for name, check_function in self.health_checks.items():
            try:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(check_function):
                    result = await check_function()
                else:
                    result = check_function()
                    
                response_time = time.time() - start_time
                
                # Normalize result
                if isinstance(result, bool):
                    status = "healthy" if result else "unhealthy"
                    message = f"{name} check {'passed' if result else 'failed'}"
                elif isinstance(result, dict):
                    status = result.get("status", "healthy")
                    message = result.get("message", f"{name} check completed")
                else:
                    status = "healthy"
                    message = str(result)
                    
                health_check = HealthCheck(name, status, message, response_time)
                self.last_check_results[name] = health_check
                
            except Exception as e:
                health_check = HealthCheck(
                    name, "unhealthy", f"Health check failed: {e}", 0
                )
                self.last_check_results[name] = health_check
                logger.error(f"Health check '{name}' failed: {e}")
                
    async def run_health_check(self, name: str) -> HealthCheck:
        """Run a specific health check"""
        if name not in self.health_checks:
            return HealthCheck(name, "unknown", "Health check not found", 0)
            
        try:
            start_time = time.time()
            check_function = self.health_checks[name]
            
            if asyncio.iscoroutinefunction(check_function):
                result = await check_function()
            else:
                result = check_function()
                
            response_time = time.time() - start_time
            
            if isinstance(result, bool):
                status = "healthy" if result else "unhealthy"
                message = f"{name} check {'passed' if result else 'failed'}"
            elif isinstance(result, dict):
                status = result.get("status", "healthy")
                message = result.get("message", f"{name} check completed")
            else:
                status = "healthy"
                message = str(result)
                
            return HealthCheck(name, status, message, response_time)
            
        except Exception as e:
            return HealthCheck(name, "unhealthy", f"Health check failed: {e}", 0)
            
    def get_overall_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        if not self.last_check_results:
            return {"status": "unknown", "message": "No health checks configured"}
            
        total_checks = len(self.last_check_results)
        healthy_checks = sum(1 for hc in self.last_check_results.values() 
                           if hc.status == "healthy")
        unhealthy_checks = sum(1 for hc in self.last_check_results.values() 
                             if hc.status == "unhealthy")
        degraded_checks = sum(1 for hc in self.last_check_results.values() 
                            if hc.status == "degraded")
        
        if unhealthy_checks > 0:
            overall_status = "unhealthy"
        elif degraded_checks > 0:
            overall_status = "degraded"
        else:
            overall_status = "healthy"
            
        return {
            "status": overall_status,
            "total_checks": total_checks,
            "healthy": healthy_checks,
            "unhealthy": unhealthy_checks,
            "degraded": degraded_checks,
            "checks": {name: {
                "status": hc.status,
                "message": hc.message,
                "response_time": round(hc.response_time, 3),
                "last_check": hc.timestamp.isoformat()
            } for name, hc in self.last_check_results.items()}
        }

# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()

# Built-in health checks
async def database_health_check():
    """Check database connectivity"""
    try:
        from .connection_pool import connection_manager
        health = await connection_manager.health_check()
        db_healthy = health.get("main_db", False)
        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "message": "Database connection " + ("successful" if db_healthy else "failed")
        }
    except Exception as e:
        return {"status": "unhealthy", "message": f"Database check failed: {e}"}

async def cache_health_check():
    """Check cache connectivity"""
    try:
        from .cache_manager import cache_manager
        stats = cache_manager.get_cache_stats()
        cache_healthy = stats.get("redis_connected", False)
        return {
            "status": "healthy" if cache_healthy else "degraded",
            "message": "Cache " + ("connected" if cache_healthy else "using fallback")
        }
    except Exception as e:
        return {"status": "unhealthy", "message": f"Cache check failed: {e}"}

async def job_queue_health_check():
    """Check job queue status"""
    try:
        from .job_queue import job_queue
        stats = await job_queue.get_queue_stats()
        queue_healthy = stats.get("is_running", False)
        return {
            "status": "healthy" if queue_healthy else "unhealthy",
            "message": f"Job queue {'running' if queue_healthy else 'stopped'}, {stats.get('total_queue_size', 0)} jobs pending"
        }
    except Exception as e:
        return {"status": "unhealthy", "message": f"Job queue check failed: {e}"}

def system_resources_health_check():
    """Check system resource utilization"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    issues = []
    if cpu_percent > 90:
        issues.append(f"High CPU usage: {cpu_percent}%")
    if memory.percent > 90:
        issues.append(f"High memory usage: {memory.percent}%")
    if (disk.used / disk.total) * 100 > 90:
        issues.append(f"High disk usage: {(disk.used / disk.total) * 100:.1f}%")
        
    if issues:
        return {
            "status": "degraded" if len(issues) < 2 else "unhealthy",
            "message": "; ".join(issues)
        }
    else:
        return {
            "status": "healthy",
            "message": f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {(disk.used / disk.total) * 100:.1f}%"
        }

# Register default health checks
def setup_default_health_checks():
    """Setup default health checks"""
    health_checker.register_health_check("database", database_health_check)
    health_checker.register_health_check("cache", cache_health_check)
    health_checker.register_health_check("job_queue", job_queue_health_check)
    health_checker.register_health_check("system_resources", system_resources_health_check)
    logger.info("✅ Default health checks registered")