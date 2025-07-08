"""
Production & Scale Module - Phase 4

This module provides production-ready features including:
- Performance optimization (caching, batching, connection pooling)
- Scalability features (horizontal scaling, job queues, auto-scaling)
- Monitoring and observability
- Deployment utilities
"""

from .cache_manager import CacheManager
from .batch_processor import BatchProcessor
from .connection_pool import ConnectionPoolManager
from .job_queue import JobQueueManager
from .scaling_controller import AutoScalingController
from .circuit_breaker import CircuitBreaker
from .monitoring import MetricsCollector, HealthChecker

__all__ = [
    "CacheManager",
    "BatchProcessor", 
    "ConnectionPoolManager",
    "JobQueueManager",
    "AutoScalingController",
    "CircuitBreaker",
    "MetricsCollector",
    "HealthChecker"
]

__version__ = "4.0.0"