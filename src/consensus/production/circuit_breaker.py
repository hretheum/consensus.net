"""
Circuit Breaker Pattern - Fault Tolerance & Cascade Prevention

Implements circuit breaker pattern to:
- Prevent cascade failures
- Handle service degradation gracefully
- Monitor service health
- Provide fallback mechanisms
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, calls fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5         # Failures before opening
    success_threshold: int = 3         # Successes before closing
    timeout_duration: float = 60.0    # Seconds before trying half-open
    request_timeout: float = 30.0     # Request timeout
    volume_threshold: int = 10         # Minimum requests before evaluating
    error_percentage: float = 50.0    # Error % threshold
    rolling_window: int = 60           # Rolling window in seconds

@dataclass
class CircuitStats:
    """Circuit breaker statistics"""
    total_requests: int = 0
    failed_requests: int = 0
    successful_requests: int = 0
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    state_change_time: datetime = field(default_factory=datetime.now)

class CircuitBreakerError(Exception):
    """Circuit breaker specific error"""
    pass

class CircuitBreaker:
    """Production-grade circuit breaker implementation"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig = None,
                 fallback_function: Optional[Callable] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.fallback_function = fallback_function
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.recent_requests = []  # For rolling window
        self.state_listeners = []
        
    def add_state_listener(self, listener: Callable):
        """Add listener for state changes"""
        self.state_listeners.append(listener)
        
    def _notify_state_change(self, old_state: CircuitState, new_state: CircuitState):
        """Notify listeners of state change"""
        for listener in self.state_listeners:
            try:
                listener(self.name, old_state, new_state, self.stats)
            except Exception as e:
                logger.error(f"State listener error: {e}")
                
    def _record_request(self, success: bool):
        """Record request result"""
        now = datetime.now()
        self.recent_requests.append((now, success))
        
        # Clean old requests outside rolling window
        cutoff = now - timedelta(seconds=self.config.rolling_window)
        self.recent_requests = [(t, s) for t, s in self.recent_requests if t > cutoff]
        
        # Update stats
        self.stats.total_requests += 1
        if success:
            self.stats.successful_requests += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
        else:
            self.stats.failed_requests += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = now
            
    def _should_open_circuit(self) -> bool:
        """Determine if circuit should be opened"""
        # Check if we have enough volume
        if len(self.recent_requests) < self.config.volume_threshold:
            return False
            
        # Check consecutive failures
        if self.stats.consecutive_failures >= self.config.failure_threshold:
            return True
            
        # Check error percentage in rolling window
        failed_in_window = sum(1 for _, success in self.recent_requests if not success)
        error_rate = (failed_in_window / len(self.recent_requests)) * 100
        
        return error_rate >= self.config.error_percentage
        
    def _should_close_circuit(self) -> bool:
        """Determine if circuit should be closed"""
        return self.stats.consecutive_successes >= self.config.success_threshold
        
    def _can_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.stats.last_failure_time is None:
            return True
            
        time_since_failure = datetime.now() - self.stats.last_failure_time
        return time_since_failure.total_seconds() >= self.config.timeout_duration
        
    def _transition_state(self, new_state: CircuitState):
        """Transition to new state"""
        if new_state == self.state:
            return
            
        old_state = self.state
        self.state = new_state
        self.stats.state_change_time = datetime.now()
        
        logger.info(f"🔄 Circuit breaker '{self.name}' state: {old_state.value} → {new_state.value}")
        self._notify_state_change(old_state, new_state)
        
    async def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        # Check current state
        if self.state == CircuitState.OPEN:
            if self._can_attempt_reset():
                self._transition_state(CircuitState.HALF_OPEN)
            else:
                # Circuit is open, fail fast
                if self.fallback_function:
                    logger.debug(f"Circuit breaker '{self.name}' OPEN - using fallback")
                    return await self._execute_fallback(*args, **kwargs)
                else:
                    raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")
                    
        # Execute the function
        try:
            # Apply timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.config.request_timeout
            )
            
            # Record success
            self._record_request(success=True)
            
            # Check if we should close the circuit
            if self.state == CircuitState.HALF_OPEN and self._should_close_circuit():
                self._transition_state(CircuitState.CLOSED)
                
            return result
            
        except Exception as e:
            # Record failure
            self._record_request(success=False)
            
            # Check if we should open the circuit
            if self.state == CircuitState.CLOSED and self._should_open_circuit():
                self._transition_state(CircuitState.OPEN)
            elif self.state == CircuitState.HALF_OPEN:
                # Half-open failed, go back to open
                self._transition_state(CircuitState.OPEN)
                
            # Try fallback if available
            if self.fallback_function:
                logger.warning(f"Circuit breaker '{self.name}' - function failed, using fallback: {e}")
                return await self._execute_fallback(*args, **kwargs)
            else:
                raise e
                
    async def _execute_fallback(self, *args, **kwargs):
        """Execute fallback function"""
        try:
            if asyncio.iscoroutinefunction(self.fallback_function):
                return await self.fallback_function(*args, **kwargs)
            else:
                return self.fallback_function(*args, **kwargs)
        except Exception as e:
            logger.error(f"Fallback function failed for '{self.name}': {e}")
            raise CircuitBreakerError(f"Both primary and fallback failed for '{self.name}'")
            
    def force_open(self):
        """Manually force circuit open"""
        self._transition_state(CircuitState.OPEN)
        logger.warning(f"🚫 Circuit breaker '{self.name}' manually opened")
        
    def force_close(self):
        """Manually force circuit closed"""
        self._transition_state(CircuitState.CLOSED)
        self.stats.consecutive_failures = 0
        logger.info(f"✅ Circuit breaker '{self.name}' manually closed")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        recent_failed = sum(1 for _, success in self.recent_requests if not success)
        recent_total = len(self.recent_requests)
        error_rate = (recent_failed / recent_total * 100) if recent_total > 0 else 0
        
        return {
            "name": self.name,
            "state": self.state.value,
            "total_requests": self.stats.total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "error_rate_recent": round(error_rate, 2),
            "last_failure": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "state_changed": self.stats.state_change_time.isoformat(),
            "can_attempt_reset": self._can_attempt_reset(),
            "recent_requests_count": recent_total
        }

class CircuitBreakerRegistry:
    """Global registry for circuit breakers"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.global_listeners = []
        
    def register(self, circuit_breaker: CircuitBreaker):
        """Register a circuit breaker"""
        self.circuit_breakers[circuit_breaker.name] = circuit_breaker
        
        # Add global listeners to this circuit breaker
        for listener in self.global_listeners:
            circuit_breaker.add_state_listener(listener)
            
        logger.info(f"📝 Registered circuit breaker: {circuit_breaker.name}")
        
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)
        
    def create(self, name: str, config: CircuitBreakerConfig = None,
              fallback_function: Optional[Callable] = None) -> CircuitBreaker:
        """Create and register new circuit breaker"""
        if name in self.circuit_breakers:
            return self.circuit_breakers[name]
            
        circuit_breaker = CircuitBreaker(name, config, fallback_function)
        self.register(circuit_breaker)
        return circuit_breaker
        
    def add_global_listener(self, listener: Callable):
        """Add listener to all circuit breakers"""
        self.global_listeners.append(listener)
        
        # Add to existing circuit breakers
        for cb in self.circuit_breakers.values():
            cb.add_state_listener(listener)
            
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get stats for all circuit breakers"""
        return {name: cb.get_stats() for name, cb in self.circuit_breakers.items()}
        
    def reset_all(self):
        """Reset all circuit breakers to closed state"""
        for cb in self.circuit_breakers.values():
            cb.force_close()
        logger.info("🔄 All circuit breakers reset to CLOSED")

# Global circuit breaker registry
circuit_registry = CircuitBreakerRegistry()

# Decorator for easy circuit breaker usage
def circuit_breaker(name: str, config: CircuitBreakerConfig = None,
                   fallback_function: Optional[Callable] = None):
    """Decorator to add circuit breaker protection"""
    def decorator(func):
        cb = circuit_registry.create(name, config, fallback_function)
        
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        return wrapper
    return decorator

# Built-in fallback functions
async def default_cache_fallback(*args, **kwargs):
    """Default fallback for cache operations"""
    logger.info("Using cache fallback - returning None")
    return None

async def default_search_fallback(query: str, *args, **kwargs):
    """Default fallback for search operations"""
    logger.info(f"Using search fallback for query: {query}")
    return {
        "results": [],
        "fallback": True,
        "message": "Search service unavailable, using cached results"
    }

async def default_llm_fallback(prompt: str, *args, **kwargs):
    """Default fallback for LLM operations"""
    logger.info("Using LLM fallback - returning templated response")
    return {
        "response": "I'm temporarily unable to process this request. Please try again later.",
        "fallback": True,
        "confidence": 0.0
    }

# Pre-configured circuit breakers for common services
def setup_production_circuit_breakers():
    """Setup circuit breakers for production services"""
    
    # Database circuit breaker
    db_config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_duration=30.0,
        request_timeout=10.0,
        volume_threshold=5,
        error_percentage=50.0
    )
    circuit_registry.create("database", db_config)
    
    # Cache circuit breaker
    cache_config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_duration=15.0,
        request_timeout=5.0,
        volume_threshold=10,
        error_percentage=60.0
    )
    circuit_registry.create("cache", cache_config, default_cache_fallback)
    
    # External API circuit breaker
    api_config = CircuitBreakerConfig(
        failure_threshold=4,
        success_threshold=3,
        timeout_duration=60.0,
        request_timeout=20.0,
        volume_threshold=8,
        error_percentage=40.0
    )
    circuit_registry.create("external_api", api_config)
    
    # LLM service circuit breaker
    llm_config = CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout_duration=120.0,
        request_timeout=60.0,
        volume_threshold=5,
        error_percentage=30.0
    )
    circuit_registry.create("llm_service", llm_config, default_llm_fallback)
    
    # Search service circuit breaker
    search_config = CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=3,
        timeout_duration=45.0,
        request_timeout=15.0,
        volume_threshold=10,
        error_percentage=50.0
    )
    circuit_registry.create("search_service", search_config, default_search_fallback)
    
    logger.info("✅ Production circuit breakers configured")

# Global state change listener for monitoring
def circuit_breaker_monitor(name: str, old_state: CircuitState, new_state: CircuitState, stats: CircuitStats):
    """Monitor circuit breaker state changes"""
    if new_state == CircuitState.OPEN:
        logger.warning(f"🚨 Circuit breaker '{name}' OPENED - {stats.consecutive_failures} consecutive failures")
    elif new_state == CircuitState.CLOSED and old_state == CircuitState.HALF_OPEN:
        logger.info(f"✅ Circuit breaker '{name}' CLOSED - service recovered")
    elif new_state == CircuitState.HALF_OPEN:
        logger.info(f"🔍 Circuit breaker '{name}' HALF-OPEN - testing service recovery")

# Register global monitor
circuit_registry.add_global_listener(circuit_breaker_monitor)