"""
Auto-Scaling Controller - Dynamic Resource Management

Implements intelligent auto-scaling based on:
- CPU/Memory utilization
- Queue depth
- Response time trends
- Traffic patterns
"""

import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ScalingDirection(Enum):
    UP = "up"
    DOWN = "down"
    STABLE = "stable"

class MetricType(Enum):
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    QUEUE_DEPTH = "queue_depth"
    RESPONSE_TIME = "response_time"
    REQUEST_RATE = "request_rate"

@dataclass
class ScalingMetric:
    """Individual scaling metric"""
    name: str
    current_value: float
    threshold_up: float
    threshold_down: float
    weight: float = 1.0
    trend: List[float] = None

@dataclass
class ScalingRule:
    """Scaling rule configuration"""
    name: str
    metric_type: MetricType
    scale_up_threshold: float
    scale_down_threshold: float
    cooldown_period: int = 300  # seconds
    min_instances: int = 1
    max_instances: int = 10
    scale_factor: float = 1.5
    enabled: bool = True

class AutoScalingController:
    """Intelligent auto-scaling system"""
    
    def __init__(self):
        self.scaling_rules: Dict[str, ScalingRule] = {}
        self.current_instances = 1
        self.target_instances = 1
        self.last_scaling_time = datetime.now()
        self.metrics_history: Dict[str, List[float]] = {}
        self.is_monitoring = False
        self.monitoring_interval = 30  # seconds
        self.scaling_callbacks: Dict[ScalingDirection, List[Callable]] = {
            ScalingDirection.UP: [],
            ScalingDirection.DOWN: [],
            ScalingDirection.STABLE: []
        }
        
        # Initialize default scaling rules
        self._setup_default_rules()
        
    def _setup_default_rules(self):
        """Setup default scaling rules"""
        self.add_scaling_rule(ScalingRule(
            name="cpu_scaling",
            metric_type=MetricType.CPU_USAGE,
            scale_up_threshold=70.0,
            scale_down_threshold=30.0,
            cooldown_period=300,
            min_instances=1,
            max_instances=10,
            scale_factor=1.5
        ))
        
        self.add_scaling_rule(ScalingRule(
            name="memory_scaling", 
            metric_type=MetricType.MEMORY_USAGE,
            scale_up_threshold=80.0,
            scale_down_threshold=40.0,
            cooldown_period=300,
            min_instances=1,
            max_instances=8,
            scale_factor=1.3
        ))
        
        self.add_scaling_rule(ScalingRule(
            name="queue_scaling",
            metric_type=MetricType.QUEUE_DEPTH,
            scale_up_threshold=100.0,
            scale_down_threshold=10.0,
            cooldown_period=180,
            min_instances=1,
            max_instances=15,
            scale_factor=2.0
        ))
        
    def add_scaling_rule(self, rule: ScalingRule):
        """Add or update scaling rule"""
        self.scaling_rules[rule.name] = rule
        logger.info(f"✅ Added scaling rule: {rule.name}")
        
    def remove_scaling_rule(self, rule_name: str):
        """Remove scaling rule"""
        if rule_name in self.scaling_rules:
            del self.scaling_rules[rule_name]
            logger.info(f"🗑️ Removed scaling rule: {rule_name}")
            
    def register_scaling_callback(self, direction: ScalingDirection, callback: Callable):
        """Register callback for scaling events"""
        self.scaling_callbacks[direction].append(callback)
        logger.info(f"📝 Registered scaling callback for {direction.value}")
        
    async def start_monitoring(self):
        """Start auto-scaling monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        asyncio.create_task(self._monitoring_loop())
        logger.info("🔍 Auto-scaling monitoring started")
        
    async def stop_monitoring(self):
        """Stop auto-scaling monitoring"""
        self.is_monitoring = False
        logger.info("🛑 Auto-scaling monitoring stopped")
        
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect current metrics
                current_metrics = await self._collect_metrics()
                
                # Analyze scaling decision
                scaling_decision = self._analyze_scaling_decision(current_metrics)
                
                # Execute scaling if needed
                if scaling_decision != ScalingDirection.STABLE:
                    await self._execute_scaling(scaling_decision, current_metrics)
                    
                # Update metrics history
                self._update_metrics_history(current_metrics)
                
                # Wait for next monitoring cycle
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"Auto-scaling monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
                
    async def _collect_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        metrics = {}
        
        try:
            # CPU utilization
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics[MetricType.CPU_USAGE.value] = cpu_percent
            
            # Memory utilization
            memory = psutil.virtual_memory()
            metrics[MetricType.MEMORY_USAGE.value] = memory.percent
            
            # Queue depth (would integrate with job queue)
            queue_depth = await self._get_queue_depth()
            metrics[MetricType.QUEUE_DEPTH.value] = queue_depth
            
            # Response time (would integrate with metrics collector)
            response_time = await self._get_average_response_time()
            metrics[MetricType.RESPONSE_TIME.value] = response_time
            
            # Request rate
            request_rate = await self._get_request_rate()
            metrics[MetricType.REQUEST_RATE.value] = request_rate
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            
        return metrics
        
    async def _get_queue_depth(self) -> float:
        """Get current job queue depth"""
        try:
            # This would integrate with the job queue manager
            from src.consensus.production.job_queue import job_queue
            stats = await job_queue.get_queue_stats()
            return float(stats.get("total_queue_size", 0))
        except Exception:
            return 0.0
            
    async def _get_average_response_time(self) -> float:
        """Get average response time"""
        try:
            # This would integrate with metrics collector
            from src.consensus.production.monitoring import metrics_collector
            return metrics_collector.get_average_response_time()
        except Exception:
            return 100.0  # Default value
            
    async def _get_request_rate(self) -> float:
        """Get current request rate per minute"""
        try:
            # This would integrate with metrics collector
            from src.consensus.production.monitoring import metrics_collector
            return metrics_collector.get_request_rate()
        except Exception:
            return 10.0  # Default value
            
    def _analyze_scaling_decision(self, metrics: Dict[str, float]) -> ScalingDirection:
        """Analyze metrics and determine scaling decision"""
        if not self._is_cooldown_period_over():
            return ScalingDirection.STABLE
            
        scale_up_score = 0.0
        scale_down_score = 0.0
        total_weight = 0.0
        
        for rule_name, rule in self.scaling_rules.items():
            if not rule.enabled:
                continue
                
            metric_value = metrics.get(rule.metric_type.value)
            if metric_value is None:
                continue
                
            weight = 1.0  # Could be made configurable per rule
            total_weight += weight
            
            # Check for scale up conditions
            if metric_value > rule.scale_up_threshold:
                scale_up_score += weight * (metric_value - rule.scale_up_threshold) / rule.scale_up_threshold
                
            # Check for scale down conditions
            elif metric_value < rule.scale_down_threshold:
                scale_down_score += weight * (rule.scale_down_threshold - metric_value) / rule.scale_down_threshold
                
        # Normalize scores
        if total_weight > 0:
            scale_up_score /= total_weight
            scale_down_score /= total_weight
            
        # Decision logic with hysteresis
        if scale_up_score > 0.3 and self._can_scale_up():
            return ScalingDirection.UP
        elif scale_down_score > 0.5 and self._can_scale_down():
            return ScalingDirection.DOWN
        else:
            return ScalingDirection.STABLE
            
    def _is_cooldown_period_over(self) -> bool:
        """Check if cooldown period has passed"""
        min_cooldown = min(rule.cooldown_period for rule in self.scaling_rules.values())
        time_since_last_scaling = (datetime.now() - self.last_scaling_time).total_seconds()
        return time_since_last_scaling >= min_cooldown
        
    def _can_scale_up(self) -> bool:
        """Check if scaling up is allowed"""
        max_instances = max(rule.max_instances for rule in self.scaling_rules.values())
        return self.current_instances < max_instances
        
    def _can_scale_down(self) -> bool:
        """Check if scaling down is allowed"""
        min_instances = min(rule.min_instances for rule in self.scaling_rules.values())
        return self.current_instances > min_instances
        
    async def _execute_scaling(self, direction: ScalingDirection, metrics: Dict[str, float]):
        """Execute scaling decision"""
        old_instances = self.current_instances
        
        if direction == ScalingDirection.UP:
            # Calculate scale up factor
            scale_factor = self._calculate_scale_factor(direction, metrics)
            self.target_instances = min(
                int(self.current_instances * scale_factor),
                max(rule.max_instances for rule in self.scaling_rules.values())
            )
            
        elif direction == ScalingDirection.DOWN:
            # Calculate scale down factor
            scale_factor = self._calculate_scale_factor(direction, metrics)
            self.target_instances = max(
                int(self.current_instances / scale_factor),
                min(rule.min_instances for rule in self.scaling_rules.values())
            )
            
        if self.target_instances != self.current_instances:
            logger.info(f"🎯 Scaling {direction.value}: {old_instances} → {self.target_instances} instances")
            
            # Execute scaling callbacks
            for callback in self.scaling_callbacks[direction]:
                try:
                    await callback(old_instances, self.target_instances, metrics)
                except Exception as e:
                    logger.error(f"Scaling callback error: {e}")
                    
            self.current_instances = self.target_instances
            self.last_scaling_time = datetime.now()
            
    def _calculate_scale_factor(self, direction: ScalingDirection, metrics: Dict[str, float]) -> float:
        """Calculate appropriate scale factor based on metrics"""
        if direction == ScalingDirection.UP:
            # Use most aggressive scale factor for urgent situations
            max_scale_factor = max(rule.scale_factor for rule in self.scaling_rules.values())
            
            # Check if any metric is critically high
            critical_threshold = 0.9  # 90% of max threshold
            for rule in self.scaling_rules.values():
                metric_value = metrics.get(rule.metric_type.value, 0)
                if metric_value > (rule.scale_up_threshold * critical_threshold):
                    return max_scale_factor
                    
            # Default scale factor
            return 1.5
            
        else:  # Scale down
            # Be conservative when scaling down
            return 1.3
            
    def _update_metrics_history(self, metrics: Dict[str, float]):
        """Update metrics history for trend analysis"""
        max_history_length = 20
        
        for metric_name, value in metrics.items():
            if metric_name not in self.metrics_history:
                self.metrics_history[metric_name] = []
                
            self.metrics_history[metric_name].append(value)
            
            # Keep only recent history
            if len(self.metrics_history[metric_name]) > max_history_length:
                self.metrics_history[metric_name] = self.metrics_history[metric_name][-max_history_length:]
                
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status"""
        return {
            "current_instances": self.current_instances,
            "target_instances": self.target_instances,
            "is_monitoring": self.is_monitoring,
            "last_scaling_time": self.last_scaling_time.isoformat(),
            "active_rules": len([r for r in self.scaling_rules.values() if r.enabled]),
            "cooldown_remaining": max(0, min(rule.cooldown_period for rule in self.scaling_rules.values()) - 
                                     (datetime.now() - self.last_scaling_time).total_seconds())
        }
        
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary with trends"""
        summary = {}
        
        for metric_name, history in self.metrics_history.items():
            if not history:
                continue
                
            current = history[-1]
            avg = sum(history) / len(history)
            trend = "stable"
            
            if len(history) >= 3:
                recent_avg = sum(history[-3:]) / 3
                if recent_avg > avg * 1.1:
                    trend = "increasing"
                elif recent_avg < avg * 0.9:
                    trend = "decreasing"
                    
            summary[metric_name] = {
                "current": round(current, 2),
                "average": round(avg, 2),
                "trend": trend,
                "history_length": len(history)
            }
            
        return summary
        
    async def force_scaling(self, target_instances: int, reason: str = "manual"):
        """Force scaling to specific number of instances"""
        if target_instances == self.current_instances:
            return
            
        direction = ScalingDirection.UP if target_instances > self.current_instances else ScalingDirection.DOWN
        old_instances = self.current_instances
        
        logger.info(f"🔧 Force scaling {direction.value}: {old_instances} → {target_instances} instances (reason: {reason})")
        
        # Execute scaling callbacks
        for callback in self.scaling_callbacks[direction]:
            try:
                await callback(old_instances, target_instances, {"reason": reason})
            except Exception as e:
                logger.error(f"Force scaling callback error: {e}")
                
        self.current_instances = target_instances
        self.target_instances = target_instances
        self.last_scaling_time = datetime.now()

# Global auto-scaling controller
scaling_controller = AutoScalingController()

# Example scaling callbacks
async def docker_scaling_callback(old_instances: int, new_instances: int, metrics: Dict[str, Any]):
    """Example callback for Docker container scaling"""
    if new_instances > old_instances:
        # Scale up
        containers_to_add = new_instances - old_instances
        logger.info(f"🐳 Scaling up: Starting {containers_to_add} new containers")
        # Docker scaling logic would go here
        
    else:
        # Scale down
        containers_to_remove = old_instances - new_instances
        logger.info(f"🐳 Scaling down: Stopping {containers_to_remove} containers")
        # Docker scaling logic would go here

async def load_balancer_callback(old_instances: int, new_instances: int, metrics: Dict[str, Any]):
    """Example callback for load balancer updates"""
    logger.info(f"⚖️ Updating load balancer: {old_instances} → {new_instances} instances")
    # Load balancer update logic would go here