"""
ConsensusNet API - Main entry point
Container-first FastAPI application with comprehensive AI agent API
"""
import json
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import uvicorn
import os
import time

from api.routes import router as api_router
from api.errors import (
    validation_exception_handler,
    http_exception_handler, 
    general_exception_handler
)


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# Application metadata
APP_VERSION = "1.0.0"
APP_START_TIME = time.time()

# Create FastAPI app with comprehensive OpenAPI documentation
app = FastAPI(
    title="ConsensusNet API",
    description="""
    # ConsensusNet API
    
    A comprehensive API for AI-powered fact-checking and claim verification.
    
    ## Features
    
    * **Claim Verification**: Submit claims for AI-powered fact-checking
    * **Agent Status Monitoring**: Real-time status of verification agents
    * **Rate Limiting**: Configurable rate limits based on API key tiers
    * **Authentication**: API key-based authentication with multiple tiers
    * **Comprehensive Error Handling**: Structured error responses
    
    ## Authentication
    
    This API supports optional API key authentication:
    
    * **No API Key**: Limited rate limits (5 requests/minute)
    * **Free Tier**: 10 requests/minute, 100/hour, 1000/day
    * **Premium Tier**: 100 requests/minute, 5000/hour, 50000/day
    
    Include your API key in the Authorization header:
    ```
    Authorization: Bearer your-api-key-here
    ```
    
    ## Demo API Keys
    
    For testing purposes, you can use these demo keys:
    
    * **Free Tier**: `demo_key_12345`
    * **Premium Tier**: `test_premium_67890`
    
    ## Rate Limiting
    
    All endpoints are rate-limited. Rate limit information is included in response headers:
    
    * `X-RateLimit-Limit`: Maximum requests in the time window
    * `X-RateLimit-Remaining`: Requests remaining in current window
    * `X-RateLimit-Reset`: When the rate limit window resets
    
    ## Support
    
    For API support, please contact the development team or check the documentation.
    """,
    version=APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    contact={
        "name": "ConsensusNet Team",
        "url": "https://github.com/hretheum/consensus.net",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API routes
app.include_router(api_router)

@app.get("/", 
         summary="Root endpoint",
         description="Basic API information and health check",
         tags=["Health"])
async def root():
    """Root endpoint - basic API information"""
    uptime = time.time() - APP_START_TIME
    return {
        "service": "ConsensusNet API",
        "version": APP_VERSION,
        "status": "operational",
        "description": "AI-powered fact-checking and claim verification API",
        "uptime_seconds": uptime,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "documentation": "/api/docs",
        "api_version": "v1",
        "endpoints": {
            "verify": "/api/v1/verify",
            "agent_status": "/api/v1/agent/status", 
            "health": "/api/v1/health",
            "docs": "/api/docs"
        }
    }

# Legacy health endpoint for backward compatibility
@app.get("/api/health",
         summary="Legacy health check", 
         description="Legacy health endpoint - use /api/v1/health for detailed information",
         tags=["Health"])
async def legacy_health_check():
    """Legacy health check endpoint"""
    uptime = time.time() - APP_START_TIME
    return {
        "status": "healthy",
        "version": APP_VERSION,
        "uptime_seconds": uptime,
        "checks": {
            "api": "operational",
            "agents": "operational",
            "database": "pending",  # Will be implemented
            "redis": "pending",     # Will be implemented
        },
        "message": "Use /api/v1/health for comprehensive health information"
    }

# This will be used when running directly (not in container)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )

# This will be used when running directly (not in container)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
