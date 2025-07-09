"""
Production & Scale Module - Phase 4

This module provides production-ready features including:
- Performance optimization (caching, batching, connection pooling)
- Scalability features (horizontal scaling, job queues, auto-scaling)
- Monitoring and observability
- Deployment utilities
"""

from src.consensus.production.cache_manager import CacheManager
from src.consensus.production.batch_processor import BatchProcessor
from src.consensus.production.connection_pool import ConnectionPoolManager
from src.consensus.production.job_queue import JobQueueManager
from src.consensus.production.scaling_controller import AutoScalingController
from src.consensus.production.circuit_breaker import CircuitBreaker
from src.consensus.production.monitoring import MetricsCollector, HealthChecker

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