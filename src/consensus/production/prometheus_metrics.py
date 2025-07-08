"""
Prometheus Metrics Exporter for ConsensusNet

Exports all ConsensusNet metrics in Prometheus format.
Integrates with existing MetricsCollector and HealthChecker.
"""

from prometheus_client import (
    Counter, Gauge, Histogram, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.core import GaugeMetricFamily, CounterMetricFamily
import time
from typing import Dict, Any, List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create custom registry to avoid conflicts
REGISTRY = CollectorRegistry()

# ========================================
# API Metrics
# ========================================
api_requests_total = Counter(
    'consensusnet_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

api_request_duration = Histogram(
    'consensusnet_api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY
)

api_errors_total = Counter(
    'consensusnet_api_errors_total',
    'Total number of API errors',
    ['method', 'endpoint', 'error_type'],
    registry=REGISTRY
)

api_response_time = Gauge(
    'consensusnet_api_response_time_seconds',
    'Current average API response time',
    registry=REGISTRY
)

# ========================================
# System Metrics
# ========================================
cpu_usage = Gauge(
    'consensusnet_cpu_usage_percent',
    'Current CPU usage percentage',
    registry=REGISTRY
)

memory_usage = Gauge(
    'consensusnet_memory_usage_percent',
    'Current memory usage percentage',
    registry=REGISTRY
)

memory_used_bytes = Gauge(
    'consensusnet_memory_used_bytes',
    'Memory used in bytes',
    registry=REGISTRY
)

memory_available_bytes = Gauge(
    'consensusnet_memory_available_bytes',
    'Memory available in bytes',
    registry=REGISTRY
)

disk_usage = Gauge(
    'consensusnet_disk_usage_percent',
    'Current disk usage percentage',
    registry=REGISTRY
)

disk_free_bytes = Gauge(
    'consensusnet_disk_free_bytes',
    'Disk free space in bytes',
    registry=REGISTRY
)

# ========================================
# Queue Metrics
# ========================================
queue_size = Gauge(
    'consensusnet_queue_size',
    'Current job queue size',
    registry=REGISTRY
)

jobs_processed_total = Counter(
    'consensusnet_jobs_processed_total',
    'Total number of jobs processed',
    ['job_type', 'status'],
    registry=REGISTRY
)

queue_processing_time = Histogram(
    'consensusnet_queue_processing_time_seconds',
    'Job processing time in seconds',
    ['job_type'],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
    registry=REGISTRY
)

# ========================================
# Cache Metrics
# ========================================
cache_hit_rate = Gauge(
    'consensusnet_cache_hit_rate',
    'Cache hit rate (0-1)',
    registry=REGISTRY
)

cache_requests_total = Counter(
    'consensusnet_cache_requests_total',
    'Total cache requests',
    ['operation', 'result'],  # operation: get/set, result: hit/miss
    registry=REGISTRY
)

# ========================================
# Database Metrics
# ========================================
db_connections_active = Gauge(
    'consensusnet_db_connections_active',
    'Active database connections',
    registry=REGISTRY
)

db_connections_idle = Gauge(
    'consensusnet_db_connections_idle',
    'Idle database connections',
    registry=REGISTRY
)

db_query_duration = Histogram(
    'consensusnet_db_query_duration_seconds',
    'Database query duration',
    ['query_type'],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=REGISTRY
)

# ========================================
# Circuit Breaker Metrics
# ========================================
circuit_breaker_state = Gauge(
    'consensusnet_circuit_breaker_state',
    'Circuit breaker state (1=closed, 0=open, 0.5=half-open)',
    ['name'],
    registry=REGISTRY
)

circuit_breaker_failures = Counter(
    'consensusnet_circuit_breaker_failures_total',
    'Total circuit breaker failures',
    ['name'],
    registry=REGISTRY
)

# ========================================
# Agent Metrics
# ========================================
agents_available = Gauge(
    'consensusnet_agents_available',
    'Number of available agents',
    ['agent_type'],
    registry=REGISTRY
)

agent_tasks_total = Counter(
    'consensusnet_agent_tasks_total',
    'Total agent tasks',
    ['agent_type', 'status'],
    registry=REGISTRY
)

agent_processing_time = Histogram(
    'consensusnet_agent_processing_time_seconds',
    'Agent task processing time',
    ['agent_type'],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
    registry=REGISTRY
)

agent_errors_total = Counter(
    'consensusnet_agent_errors_total',
    'Total agent errors',
    ['agent_type', 'error_type'],
    registry=REGISTRY
)

# ========================================
# Consensus Metrics
# ========================================
consensus_rounds = Counter(
    'consensusnet_consensus_rounds_total',
    'Total consensus rounds',
    ['result'],  # result: consensus_reached, no_consensus
    registry=REGISTRY
)

consensus_confidence = Histogram(
    'consensusnet_consensus_confidence',
    'Consensus confidence score distribution',
    buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0),
    registry=REGISTRY
)

# ========================================
# Debate Metrics
# ========================================
debate_rounds = Counter(
    'consensusnet_debate_rounds_total',
    'Total debate rounds',
    registry=REGISTRY
)

debate_challenges = Counter(
    'consensusnet_debate_challenges_total',
    'Total debate challenges',
    ['challenge_type', 'strength'],
    registry=REGISTRY
)

# ========================================
# Health Check Metrics
# ========================================
health_check_status = Gauge(
    'consensusnet_health_check_status',
    'Health check status (1=healthy, 0=unhealthy, 0.5=degraded)',
    ['check_name'],
    registry=REGISTRY
)

health_check_duration = Gauge(
    'consensusnet_health_check_duration_seconds',
    'Health check duration',
    ['check_name'],
    registry=REGISTRY
)

# ========================================
# Custom Collector for Dynamic Metrics
# ========================================
class ConsensusNetCollector:
    """Custom collector that integrates with existing monitoring system"""
    
    def __init__(self, metrics_collector, health_checker):
        self.metrics_collector = metrics_collector
        self.health_checker = health_checker
        
    def collect(self):
        """Collect metrics from existing monitoring system"""
        # System metrics
        try:
            cpu_summary = self.metrics_collector.get_metric_summary("cpu_usage_percent", 1)
            if cpu_summary:
                cpu_usage.set(cpu_summary.get("current", 0))
                
            memory_summary = self.metrics_collector.get_metric_summary("memory_usage_percent", 1)
            if memory_summary:
                memory_usage.set(memory_summary.get("current", 0))
                
            memory_used_summary = self.metrics_collector.get_metric_summary("memory_used_bytes", 1)
            if memory_used_summary:
                memory_used_bytes.set(memory_used_summary.get("current", 0))
                
            memory_avail_summary = self.metrics_collector.get_metric_summary("memory_available_bytes", 1)
            if memory_avail_summary:
                memory_available_bytes.set(memory_avail_summary.get("current", 0))
                
            disk_summary = self.metrics_collector.get_metric_summary("disk_usage_percent", 1)
            if disk_summary:
                disk_usage.set(disk_summary.get("current", 0))
                
            disk_free_summary = self.metrics_collector.get_metric_summary("disk_free_bytes", 1)
            if disk_free_summary:
                disk_free_bytes.set(disk_free_summary.get("current", 0))
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            
        # Queue metrics
        try:
            queue_size_summary = self.metrics_collector.get_metric_summary("queue_size", 1)
            if queue_size_summary:
                queue_size.set(queue_size_summary.get("current", 0))
        except Exception as e:
            logger.error(f"Error collecting queue metrics: {e}")
            
        # Cache metrics
        try:
            cache_hit_summary = self.metrics_collector.get_metric_summary("cache_hit_rate", 1)
            if cache_hit_summary:
                cache_hit_rate.set(cache_hit_summary.get("current", 0))
        except Exception as e:
            logger.error(f"Error collecting cache metrics: {e}")
            
        # Request metrics
        try:
            request_stats = self.metrics_collector.get_request_stats()
            if request_stats:
                api_response_time.set(request_stats.get("average_response_time", 0))
        except Exception as e:
            logger.error(f"Error collecting request metrics: {e}")
            
        # Health check metrics
        try:
            overall_health = self.health_checker.get_overall_health()
            for check_name, check_data in overall_health.get("checks", {}).items():
                status_value = 1 if check_data["status"] == "healthy" else (
                    0.5 if check_data["status"] == "degraded" else 0
                )
                health_check_status.labels(check_name=check_name).set(status_value)
                health_check_duration.labels(check_name=check_name).set(
                    check_data.get("response_time", 0)
                )
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
            
        # Return empty list as we're using module-level metrics
        return []

# ========================================
# Metrics Export Functions
# ========================================
def setup_prometheus_metrics(metrics_collector_instance, health_checker_instance):
    """Setup Prometheus metrics with existing monitoring instances"""
    collector = ConsensusNetCollector(metrics_collector_instance, health_checker_instance)
    REGISTRY.register(collector)
    logger.info("✅ Prometheus metrics collector registered")

def get_metrics():
    """Get current metrics in Prometheus format"""
    return generate_latest(REGISTRY)

def get_metrics_content_type():
    """Get Prometheus content type"""
    return CONTENT_TYPE_LATEST

# ========================================
# Helper Functions for Metric Updates
# ========================================
def record_api_request(method: str, endpoint: str, status: int, duration: float):
    """Record API request metrics"""
    api_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
    api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
def record_api_error(method: str, endpoint: str, error_type: str):
    """Record API error"""
    api_errors_total.labels(method=method, endpoint=endpoint, error_type=error_type).inc()
    
def record_job_processed(job_type: str, status: str, duration: float):
    """Record job processing metrics"""
    jobs_processed_total.labels(job_type=job_type, status=status).inc()
    queue_processing_time.labels(job_type=job_type).observe(duration)
    
def record_cache_request(operation: str, hit: bool):
    """Record cache request"""
    result = "hit" if hit else "miss"
    cache_requests_total.labels(operation=operation, result=result).inc()
    
def record_agent_task(agent_type: str, status: str, duration: float):
    """Record agent task metrics"""
    agent_tasks_total.labels(agent_type=agent_type, status=status).inc()
    agent_processing_time.labels(agent_type=agent_type).observe(duration)
    
def record_agent_error(agent_type: str, error_type: str):
    """Record agent error"""
    agent_errors_total.labels(agent_type=agent_type, error_type=error_type).inc()
    
def update_circuit_breaker_state(name: str, state: str):
    """Update circuit breaker state"""
    state_value = 1 if state == "closed" else (0.5 if state == "half_open" else 0)
    circuit_breaker_state.labels(name=name).set(state_value)
    
def record_circuit_breaker_failure(name: str):
    """Record circuit breaker failure"""
    circuit_breaker_failures.labels(name=name).inc()
    
def update_agents_available(agent_type: str, count: int):
    """Update available agents count"""
    agents_available.labels(agent_type=agent_type).set(count)
    
def record_consensus_round(reached_consensus: bool, confidence: float = None):
    """Record consensus round"""
    result = "consensus_reached" if reached_consensus else "no_consensus"
    consensus_rounds.labels(result=result).inc()
    if confidence is not None:
        consensus_confidence.observe(confidence)
        
def record_debate_round():
    """Record debate round"""
    debate_rounds.inc()
    
def record_debate_challenge(challenge_type: str, strength: str):
    """Record debate challenge"""
    debate_challenges.labels(challenge_type=challenge_type, strength=strength).inc()