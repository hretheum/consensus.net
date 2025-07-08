"""
Rate limiting middleware for the ConsensusNet API.
"""
import time
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


class RateLimiter:
    """Simple in-memory rate limiter for API endpoints."""
    
    def __init__(self, requests_per_minute: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute per IP
        """
        self.requests_per_minute = requests_per_minute
        self.request_history: Dict[str, list] = {}
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, Dict]:
        """
        Check if request is allowed for given client IP.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Initialize or clean old requests for this IP
        if client_ip not in self.request_history:
            self.request_history[client_ip] = []
        
        # Remove requests older than 1 minute
        self.request_history[client_ip] = [
            req_time for req_time in self.request_history[client_ip] 
            if req_time > minute_ago
        ]
        
        # Check if under limit
        current_requests = len(self.request_history[client_ip])
        is_allowed = current_requests < self.requests_per_minute
        
        if is_allowed:
            # Add current request
            self.request_history[client_ip].append(current_time)
        
        # Calculate reset time (next minute boundary)
        reset_time = datetime.fromtimestamp(current_time + 60)
        
        rate_limit_info = {
            "limit": self.requests_per_minute,
            "remaining": max(0, self.requests_per_minute - current_requests - (1 if is_allowed else 0)),
            "reset_time": reset_time
        }
        
        return is_allowed, rate_limit_info


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=10)


async def rate_limit_middleware(request: Request, call_next):
    """
    Rate limiting middleware for FastAPI.
    
    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in chain
        
    Returns:
        Response with rate limit headers or 429 error
    """
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/", "/api/health", "/api/docs", "/api/redoc", "/openapi.json", "/api/verify/stats"]:
        response = await call_next(request)
        return response
    
    # Get client IP
    client_ip = "127.0.0.1"  # Default for test cases
    if request.client and request.client.host:
        client_ip = request.client.host
    if "x-forwarded-for" in request.headers:
        client_ip = request.headers["x-forwarded-for"].split(",")[0].strip()
    
    # Check rate limit
    is_allowed, rate_info = rate_limiter.is_allowed(client_ip)
    
    if not is_allowed:
        # Return 429 Too Many Requests
        error_response = {
            "success": False,
            "error": "Rate limit exceeded. Please try again later.",
            "error_code": "RATE_LIMIT_EXCEEDED",
            "timestamp": datetime.now().isoformat(),
            "rate_limit": {
                "limit": rate_info["limit"],
                "remaining": rate_info["remaining"],
                "reset_time": rate_info["reset_time"].isoformat()
            }
        }
        return JSONResponse(
            status_code=429,
            content=error_response,
            headers={
                "X-RateLimit-Limit": str(rate_info["limit"]),
                "X-RateLimit-Remaining": str(rate_info["remaining"]),
                "X-RateLimit-Reset": rate_info["reset_time"].isoformat(),
                "Retry-After": "60"
            }
        )
    
    # Process request
    response = await call_next(request)
    
    # Add rate limit headers to successful responses
    response.headers["X-RateLimit-Limit"] = str(rate_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_info["remaining"])
    response.headers["X-RateLimit-Reset"] = rate_info["reset_time"].isoformat()
    
    return response