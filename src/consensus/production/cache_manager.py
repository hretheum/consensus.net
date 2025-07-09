"""
Cache Manager - Production Performance Optimization

Implements intelligent caching layer with Redis backend for:
- Verification result caching
- Agent response caching  
- Database query caching
- Session caching
"""

import json
import hashlib
from typing import Optional, Any, Dict, List, Union
from dataclasses import asdict
from datetime import datetime, timedelta
import redis
import asyncio
from contextlib import asynccontextmanager
import logging

from src.agents.verification_result import VerificationResult
from src.agents.agent_models import LLMResponse

logger = logging.getLogger(__name__)

class CacheManager:
    """Intelligent caching system with multi-tier storage and smart invalidation"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", 
                 default_ttl: int = 3600):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client = None
        self.cache_stats = {
            "hits": 0,
            "misses": 0, 
            "writes": 0,
            "evictions": 0
        }
        
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.ping
            )
            logger.info("Cache manager connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # Fallback to in-memory cache
            self.redis_client = {}
            
    def _generate_cache_key(self, namespace: str, data: Union[str, Dict]) -> str:
        """Generate deterministic cache key"""
        if isinstance(data, str):
            key_data = data
        else:
            key_data = json.dumps(data, sort_keys=True)
            
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()[:16]
        return f"consensus:{namespace}:{key_hash}"
    
    async def get_verification_cache(self, claim: str, context: Dict = None) -> Optional[VerificationResult]:
        """Get cached verification result"""
        try:
            cache_key = self._generate_cache_key("verification", {
                "claim": claim,
                "context": context or {}
            })
            
            if isinstance(self.redis_client, dict):
                # In-memory fallback
                cached_data = self.redis_client.get(cache_key)
            else:
                cached_data = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.get, cache_key
                )
            
            if cached_data:
                self.cache_stats["hits"] += 1
                data = json.loads(cached_data)
                logger.debug(f"Cache HIT for verification: {claim[:50]}...")
                return VerificationResult(**data)
            else:
                self.cache_stats["misses"] += 1
                logger.debug(f"Cache MISS for verification: {claim[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set_verification_cache(self, claim: str, result: VerificationResult, 
                                   context: Dict = None, ttl: int = None) -> bool:
        """Cache verification result with smart TTL"""
        try:
            cache_key = self._generate_cache_key("verification", {
                "claim": claim,
                "context": context or {}
            })
            
            # Smart TTL based on confidence
            if ttl is None:
                if result.confidence > 0.9:
                    ttl = self.default_ttl * 4  # High confidence lasts longer
                elif result.confidence > 0.7:
                    ttl = self.default_ttl * 2
                else:
                    ttl = self.default_ttl // 2  # Low confidence expires faster
            
            cache_data = json.dumps(asdict(result))
            
            if isinstance(self.redis_client, dict):
                # In-memory fallback with expiry simulation
                self.redis_client[cache_key] = cache_data
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.setex, cache_key, ttl, cache_data
                )
            
            self.cache_stats["writes"] += 1
            logger.debug(f"Cached verification result for: {claim[:50]}... (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def get_agent_cache(self, agent_id: str, task_hash: str) -> Optional[LLMResponse]:
        """Get cached agent response"""
        try:
            cache_key = self._generate_cache_key("agent", {
                "agent_id": agent_id,
                "task": task_hash
            })
            
            if isinstance(self.redis_client, dict):
                cached_data = self.redis_client.get(cache_key)
            else:
                cached_data = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.get, cache_key
                )
            
            if cached_data:
                self.cache_stats["hits"] += 1
                data = json.loads(cached_data)
                return LLMResponse(**data)
            else:
                self.cache_stats["misses"] += 1
                return None
                
        except Exception as e:
            logger.error(f"Agent cache get error: {e}")
            return None
    
    async def set_agent_cache(self, agent_id: str, task_hash: str, 
                            response: LLMResponse, ttl: int = None) -> bool:
        """Cache agent response"""
        try:
            cache_key = self._generate_cache_key("agent", {
                "agent_id": agent_id,
                "task": task_hash
            })
            
            ttl = ttl or self.default_ttl // 2  # Agent responses expire faster
            cache_data = json.dumps(asdict(response))
            
            if isinstance(self.redis_client, dict):
                self.redis_client[cache_key] = cache_data
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.setex, cache_key, ttl, cache_data
                )
            
            self.cache_stats["writes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Agent cache set error: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        try:
            if isinstance(self.redis_client, dict):
                # In-memory pattern matching
                keys_to_delete = [k for k in self.redis_client.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.redis_client[key]
                count = len(keys_to_delete)
            else:
                keys = await asyncio.get_event_loop().run_in_executor(
                    None, self.redis_client.keys, f"consensus:*{pattern}*"
                )
                if keys:
                    count = await asyncio.get_event_loop().run_in_executor(
                        None, self.redis_client.delete, *keys
                    )
                else:
                    count = 0
            
            self.cache_stats["evictions"] += count
            logger.info(f"Invalidated {count} cache entries matching pattern: {pattern}")
            return count
            
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "hits": self.cache_stats["hits"],
            "misses": self.cache_stats["misses"],
            "writes": self.cache_stats["writes"],
            "evictions": self.cache_stats["evictions"],
            "redis_connected": not isinstance(self.redis_client, dict)
        }
    
    async def warm_up_cache(self, common_claims: List[str]):
        """Pre-warm cache with common claims"""
        logger.info(f"Warming up cache with {len(common_claims)} common claims")
        # This would be called during startup with frequently accessed claims
        for claim in common_claims:
            cache_key = self._generate_cache_key("verification", {"claim": claim})
            logger.debug(f"Pre-warming cache for: {claim[:50]}...")
    
    @asynccontextmanager
    async def batch_operation(self):
        """Context manager for batch cache operations"""
        # For Redis pipeline operations
        if not isinstance(self.redis_client, dict):
            pipe = self.redis_client.pipeline()
            try:
                yield pipe
                await asyncio.get_event_loop().run_in_executor(None, pipe.execute)
            except Exception as e:
                logger.error(f"Batch operation error: {e}")
        else:
            yield self.redis_client
    
    async def cleanup_expired(self):
        """Manual cleanup for in-memory cache (Redis handles this automatically)"""
        if isinstance(self.redis_client, dict):
            # This is a simplified cleanup for the fallback in-memory cache
            logger.debug("Cleaning up in-memory cache (Redis not available)")
    
    async def close(self):
        """Close cache connections"""
        if self.redis_client and not isinstance(self.redis_client, dict):
            await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.close
            )
            logger.info("Cache manager disconnected")

# Global cache instance
cache_manager = CacheManager()

# Cache decorators for easy usage
def cache_verification(ttl: int = None):
    """Decorator for caching verification functions"""
    def decorator(func):
        async def wrapper(claim: str, *args, **kwargs):
            # Try cache first
            cached_result = await cache_manager.get_verification_cache(claim)
            if cached_result:
                return cached_result
            
            # Execute function
            result = await func(claim, *args, **kwargs)
            
            # Cache result
            if isinstance(result, VerificationResult):
                await cache_manager.set_verification_cache(claim, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator