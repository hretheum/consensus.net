"""
Authentication and authorization for ConsensusNet API.

This module provides API key-based authentication and rate limiting
for the ConsensusNet API endpoints.
"""
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from collections import defaultdict, deque

from .models import APIKeyInfo, RateLimitInfo


# Simple in-memory store for API keys (in production, this would be a database)
API_KEYS_DB = {
    "demo_key_12345": {
        "key_id": "demo_key_12345",
        "name": "Demo API Key",
        "tier": "free",
        "permissions": ["verify", "status"],
        "created_at": datetime.now(),
        "last_used": None,
        "rate_limit": {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "requests_per_day": 1000
        }
    },
    "test_premium_67890": {
        "key_id": "test_premium_67890", 
        "name": "Premium Test Key",
        "tier": "premium",
        "permissions": ["verify", "status", "admin"],
        "created_at": datetime.now(),
        "last_used": None,
        "rate_limit": {
            "requests_per_minute": 100,
            "requests_per_hour": 5000,
            "requests_per_day": 50000
        }
    }
}

# Rate limiting store: key -> {window -> deque of timestamps}
rate_limit_store: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))

security = HTTPBearer(auto_error=False)


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = defaultdict(lambda: defaultdict(deque))
    
    def is_allowed(self, key: str, window_seconds: int, max_requests: int) -> tuple[bool, RateLimitInfo]:
        """
        Check if a request is allowed within the rate limit.
        
        Returns:
            (is_allowed, rate_limit_info)
        """
        now = time.time()
        window_key = f"{window_seconds}s"
        
        # Clean old entries
        while (self.requests[key][window_key] and 
               self.requests[key][window_key][0] <= now - window_seconds):
            self.requests[key][window_key].popleft()
        
        current_count = len(self.requests[key][window_key])
        allowed = current_count < max_requests
        
        if allowed:
            self.requests[key][window_key].append(now)
        
        reset_time = datetime.fromtimestamp(now + window_seconds)
        
        rate_limit_info = RateLimitInfo(
            limit=max_requests,
            remaining=max(0, max_requests - current_count - (1 if allowed else 0)),
            reset_time=reset_time,
            window_seconds=window_seconds
        )
        
        return allowed, rate_limit_info


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_api_key_info(api_key: str) -> Optional[APIKeyInfo]:
    """
    Retrieve API key information from the store.
    
    Args:
        api_key: The API key to look up
        
    Returns:
        APIKeyInfo if key exists, None otherwise
    """
    key_data = API_KEYS_DB.get(api_key)
    if not key_data:
        return None
    
    # Update last used timestamp
    key_data["last_used"] = datetime.now()
    
    # Get current rate limit info for the primary window (1 minute)
    allowed, rate_limit_info = rate_limiter.is_allowed(
        api_key, 60, key_data["rate_limit"]["requests_per_minute"]
    )
    
    return APIKeyInfo(
        key_id=key_data["key_id"],
        name=key_data["name"],
        tier=key_data["tier"],
        rate_limit=rate_limit_info,
        permissions=key_data["permissions"],
        created_at=key_data["created_at"],
        last_used=key_data["last_used"]
    )


def check_rate_limit(api_key: str) -> RateLimitInfo:
    """
    Check rate limits for an API key.
    
    Args:
        api_key: The API key to check
        
    Returns:
        RateLimitInfo with current rate limit status
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    key_data = API_KEYS_DB.get(api_key)
    if not key_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    # Check 1-minute rate limit
    allowed, rate_limit_info = rate_limiter.is_allowed(
        api_key, 60, key_data["rate_limit"]["requests_per_minute"]
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before making more requests.",
            headers={
                "X-RateLimit-Limit": str(rate_limit_info.limit),
                "X-RateLimit-Remaining": str(rate_limit_info.remaining),
                "X-RateLimit-Reset": rate_limit_info.reset_time.isoformat(),
                "Retry-After": str(rate_limit_info.window_seconds)
            }
        )
    
    return rate_limit_info


async def get_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Optional[APIKeyInfo]:
    """
    Validate API key from Authorization header.
    
    This function can be used as a dependency in FastAPI routes to enforce authentication.
    It's optional by default - routes can choose to require authentication or not.
    
    Args:
        credentials: HTTP Bearer credentials from the Authorization header
        
    Returns:
        APIKeyInfo if valid key is provided, None if no credentials
        
    Raises:
        HTTPException: If invalid credentials are provided
    """
    if not credentials:
        return None
    
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme. Use Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    api_key = credentials.credentials
    key_info = get_api_key_info(api_key)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return key_info


async def require_api_key(api_key_info: Optional[APIKeyInfo] = Security(get_api_key)) -> APIKeyInfo:
    """
    Require a valid API key for accessing an endpoint.
    
    This dependency enforces authentication by raising an exception if no valid key is provided.
    
    Args:
        api_key_info: API key info from get_api_key dependency
        
    Returns:
        APIKeyInfo for the authenticated key
        
    Raises:
        HTTPException: If no valid API key is provided
    """
    if not api_key_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include your API key in the Authorization header as 'Bearer <your-key>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return api_key_info


def check_permission(api_key_info: APIKeyInfo, permission: str) -> None:
    """
    Check if an API key has a specific permission.
    
    Args:
        api_key_info: The API key information
        permission: The permission to check for
        
    Raises:
        HTTPException: If the key doesn't have the required permission
    """
    if permission not in api_key_info.permissions:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"API key does not have permission: {permission}"
        )