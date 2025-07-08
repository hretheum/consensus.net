"""
Connection Pool Manager - Database & Service Connection Optimization

Manages connection pools for:
- Database connections (PostgreSQL, Redis)
- External API connections (LLM providers, search APIs)
- WebSocket connections
- HTTP client sessions
"""

import asyncio
import asyncpg
import aioredis
import aiohttp
from typing import Dict, Any, Optional, List, Callable, AsyncContextManager
from dataclasses import dataclass
from contextlib import asynccontextmanager
import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)

class PoolType(Enum):
    DATABASE = "database"
    REDIS = "redis"
    HTTP = "http"
    WEBSOCKET = "websocket"

@dataclass
class PoolConfig:
    """Configuration for connection pools"""
    min_size: int = 5
    max_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    timeout: float = 60.0
    retry_attempts: int = 3
    retry_delay: float = 1.0

class ConnectionPoolManager:
    """Centralized connection pool management"""
    
    def __init__(self):
        self.pools: Dict[str, Any] = {}
        self.pool_configs: Dict[str, PoolConfig] = {}
        self.pool_stats: Dict[str, Dict[str, Any]] = {}
        self.is_initialized = False
        
    async def initialize(self, configs: Dict[str, Dict[str, Any]]):
        """Initialize all connection pools"""
        if self.is_initialized:
            return
            
        logger.info("Initializing connection pools...")
        
        for pool_name, config in configs.items():
            try:
                await self._create_pool(pool_name, config)
                logger.info(f"✅ Connection pool '{pool_name}' created successfully")
            except Exception as e:
                logger.error(f"❌ Failed to create pool '{pool_name}': {e}")
                
        self.is_initialized = True
        logger.info("🎉 All connection pools initialized")
    
    async def _create_pool(self, name: str, config: Dict[str, Any]):
        """Create a specific connection pool"""
        pool_type = PoolType(config.get('type'))
        pool_config = PoolConfig(**config.get('pool_config', {}))
        self.pool_configs[name] = pool_config
        
        if pool_type == PoolType.DATABASE:
            await self._create_database_pool(name, config, pool_config)
        elif pool_type == PoolType.REDIS:
            await self._create_redis_pool(name, config, pool_config)
        elif pool_type == PoolType.HTTP:
            await self._create_http_pool(name, config, pool_config)
        elif pool_type == PoolType.WEBSOCKET:
            await self._create_websocket_pool(name, config, pool_config)
            
        # Initialize stats
        self.pool_stats[name] = {
            "connections_created": 0,
            "connections_borrowed": 0,
            "connections_returned": 0,
            "connection_errors": 0,
            "active_connections": 0,
            "pool_size": 0,
            "last_activity": time.time()
        }
    
    async def _create_database_pool(self, name: str, config: Dict, pool_config: PoolConfig):
        """Create PostgreSQL connection pool"""
        db_config = config['connection']
        
        self.pools[name] = await asyncpg.create_pool(
            host=db_config['host'],
            port=db_config['port'],
            database=db_config['database'],
            user=db_config['user'],
            password=db_config['password'],
            min_size=pool_config.min_size,
            max_size=pool_config.max_size,
            max_queries=pool_config.max_queries,
            max_inactive_connection_lifetime=pool_config.max_inactive_connection_lifetime,
            command_timeout=pool_config.timeout
        )
    
    async def _create_redis_pool(self, name: str, config: Dict, pool_config: PoolConfig):
        """Create Redis connection pool"""
        redis_config = config['connection']
        
        self.pools[name] = aioredis.ConnectionPool.from_url(
            redis_config['url'],
            max_connections=pool_config.max_size,
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError]
        )
    
    async def _create_http_pool(self, name: str, config: Dict, pool_config: PoolConfig):
        """Create HTTP client session pool"""
        session_config = config.get('session_config', {})
        
        connector = aiohttp.TCPConnector(
            limit=pool_config.max_size,
            limit_per_host=pool_config.max_size // 2,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=pool_config.timeout,
            sock_connect=10,
            sock_read=30
        )
        
        self.pools[name] = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            **session_config
        )
    
    async def _create_websocket_pool(self, name: str, config: Dict, pool_config: PoolConfig):
        """Create WebSocket connection pool (custom implementation)"""
        # This would be a custom WebSocket pool implementation
        # For now, we'll use a simple connection manager
        self.pools[name] = WebSocketPool(pool_config)
    
    @asynccontextmanager
    async def get_connection(self, pool_name: str):
        """Get a connection from the specified pool"""
        if pool_name not in self.pools:
            raise ValueError(f"Pool '{pool_name}' not found")
            
        pool = self.pools[pool_name]
        connection = None
        
        try:
            # Update stats
            self.pool_stats[pool_name]["connections_borrowed"] += 1
            self.pool_stats[pool_name]["last_activity"] = time.time()
            
            # Get connection based on pool type
            if isinstance(pool, asyncpg.Pool):
                async with pool.acquire() as conn:
                    self.pool_stats[pool_name]["active_connections"] += 1
                    yield conn
                    self.pool_stats[pool_name]["active_connections"] -= 1
                    
            elif isinstance(pool, aioredis.ConnectionPool):
                connection = aioredis.Redis(connection_pool=pool)
                self.pool_stats[pool_name]["active_connections"] += 1
                yield connection
                self.pool_stats[pool_name]["active_connections"] -= 1
                if connection:
                    await connection.close()
                    
            elif isinstance(pool, aiohttp.ClientSession):
                self.pool_stats[pool_name]["active_connections"] += 1
                yield pool
                self.pool_stats[pool_name]["active_connections"] -= 1
                
            else:
                # Custom pool implementation
                async with pool.get_connection() as conn:
                    self.pool_stats[pool_name]["active_connections"] += 1
                    yield conn
                    self.pool_stats[pool_name]["active_connections"] -= 1
            
            # Update return stats
            self.pool_stats[pool_name]["connections_returned"] += 1
            
        except Exception as e:
            self.pool_stats[pool_name]["connection_errors"] += 1
            logger.error(f"Connection error in pool '{pool_name}': {e}")
            raise
    
    async def execute_query(self, pool_name: str, query: str, *args) -> List[Dict]:
        """Execute database query with connection pooling"""
        async with self.get_connection(pool_name) as conn:
            if not isinstance(conn, asyncpg.Connection):
                raise ValueError(f"Pool '{pool_name}' is not a database pool")
                
            result = await conn.fetch(query, *args)
            return [dict(row) for row in result]
    
    async def execute_redis_command(self, pool_name: str, command: str, *args):
        """Execute Redis command with connection pooling"""
        async with self.get_connection(pool_name) as redis:
            if not hasattr(redis, command):
                raise ValueError(f"Redis command '{command}' not supported")
                
            redis_command = getattr(redis, command)
            return await redis_command(*args)
    
    async def make_http_request(self, pool_name: str, method: str, url: str, **kwargs):
        """Make HTTP request with session pooling"""
        async with self.get_connection(pool_name) as session:
            if not isinstance(session, aiohttp.ClientSession):
                raise ValueError(f"Pool '{pool_name}' is not an HTTP pool")
                
            async with session.request(method, url, **kwargs) as response:
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'data': await response.text()
                }
    
    def get_pool_stats(self, pool_name: str = None) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if pool_name:
            if pool_name not in self.pool_stats:
                return {}
                
            stats = self.pool_stats[pool_name].copy()
            
            # Add current pool size
            pool = self.pools.get(pool_name)
            if isinstance(pool, asyncpg.Pool):
                stats["pool_size"] = pool.get_size()
                stats["pool_type"] = "database"
            elif isinstance(pool, aioredis.ConnectionPool):
                stats["pool_size"] = len(pool._available_connections)
                stats["pool_type"] = "redis"
            elif isinstance(pool, aiohttp.ClientSession):
                stats["pool_size"] = pool.connector.limit
                stats["pool_type"] = "http"
            else:
                stats["pool_type"] = "custom"
                
            return stats
        else:
            # Return stats for all pools
            all_stats = {}
            for name in self.pools:
                all_stats[name] = self.get_pool_stats(name)
            return all_stats
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all connection pools"""
        health_status = {}
        
        for pool_name, pool in self.pools.items():
            try:
                if isinstance(pool, asyncpg.Pool):
                    async with pool.acquire() as conn:
                        await conn.fetchval("SELECT 1")
                        health_status[pool_name] = True
                        
                elif isinstance(pool, aioredis.ConnectionPool):
                    redis = aioredis.Redis(connection_pool=pool)
                    await redis.ping()
                    await redis.close()
                    health_status[pool_name] = True
                    
                elif isinstance(pool, aiohttp.ClientSession):
                    # HTTP sessions are generally healthy if they exist
                    health_status[pool_name] = not pool.closed
                    
                else:
                    # Custom pool health check
                    health_status[pool_name] = await pool.health_check()
                    
            except Exception as e:
                logger.error(f"Health check failed for pool '{pool_name}': {e}")
                health_status[pool_name] = False
        
        return health_status
    
    async def cleanup_idle_connections(self):
        """Clean up idle connections across all pools"""
        logger.info("Cleaning up idle connections...")
        
        for pool_name, pool in self.pools.items():
            try:
                if isinstance(pool, asyncpg.Pool):
                    # AsyncPG handles this automatically
                    pass
                elif isinstance(pool, aioredis.ConnectionPool):
                    # Redis connection pool cleanup
                    await pool.disconnect()
                elif isinstance(pool, aiohttp.ClientSession):
                    # HTTP connector cleanup
                    await pool.connector.close()
                else:
                    # Custom pool cleanup
                    await pool.cleanup()
                    
                logger.debug(f"Cleaned up pool '{pool_name}'")
                
            except Exception as e:
                logger.error(f"Cleanup failed for pool '{pool_name}': {e}")
    
    async def close_all_pools(self):
        """Close all connection pools"""
        logger.info("Closing all connection pools...")
        
        for pool_name, pool in self.pools.items():
            try:
                if isinstance(pool, asyncpg.Pool):
                    await pool.close()
                elif isinstance(pool, aioredis.ConnectionPool):
                    await pool.disconnect()
                elif isinstance(pool, aiohttp.ClientSession):
                    await pool.close()
                else:
                    await pool.close()
                    
                logger.debug(f"Closed pool '{pool_name}'")
                
            except Exception as e:
                logger.error(f"Error closing pool '{pool_name}': {e}")
        
        self.pools.clear()
        self.pool_stats.clear()
        self.is_initialized = False
        logger.info("✅ All connection pools closed")

class WebSocketPool:
    """Custom WebSocket connection pool implementation"""
    
    def __init__(self, config: PoolConfig):
        self.config = config
        self.connections = []
        self.available_connections = asyncio.Queue()
        self.active_connections = set()
        
    @asynccontextmanager
    async def get_connection(self):
        """Get WebSocket connection from pool"""
        try:
            # This is a simplified implementation
            # Real implementation would manage actual WebSocket connections
            connection = f"ws_connection_{len(self.active_connections)}"
            self.active_connections.add(connection)
            yield connection
        finally:
            self.active_connections.discard(connection)
    
    async def health_check(self) -> bool:
        """Check WebSocket pool health"""
        return True  # Simplified
    
    async def cleanup(self):
        """Clean up WebSocket connections"""
        self.active_connections.clear()
    
    async def close(self):
        """Close WebSocket pool"""
        await self.cleanup()

# Global connection pool manager
connection_manager = ConnectionPoolManager()

# Configuration templates
DEFAULT_POOL_CONFIGS = {
    "main_db": {
        "type": "database",
        "connection": {
            "host": "localhost",
            "port": 5432,
            "database": "consensus",
            "user": "consensus_user",
            "password": "consensus_pass"
        },
        "pool_config": {
            "min_size": 5,
            "max_size": 20,
            "max_queries": 50000,
            "timeout": 60.0
        }
    },
    "cache": {
        "type": "redis",
        "connection": {
            "url": "redis://localhost:6379"
        },
        "pool_config": {
            "min_size": 2,
            "max_size": 10,
            "timeout": 30.0
        }
    },
    "http_client": {
        "type": "http",
        "session_config": {
            "headers": {"User-Agent": "ConsensusNet/4.0"}
        },
        "pool_config": {
            "max_size": 50,
            "timeout": 120.0
        }
    }
}

# Convenience functions
async def get_db_connection(pool_name: str = "main_db"):
    """Get database connection from pool"""
    return connection_manager.get_connection(pool_name)

async def get_redis_connection(pool_name: str = "cache"):
    """Get Redis connection from pool"""
    return connection_manager.get_connection(pool_name)

async def get_http_session(pool_name: str = "http_client"):
    """Get HTTP session from pool"""
    return connection_manager.get_connection(pool_name)