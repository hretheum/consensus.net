"""
ConsensusNet API - Main entry point
Container-first FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from .config import get_config

# Load configuration
config = get_config()

# Create FastAPI app with configuration
app = FastAPI(
    title=config.app_name,
    description="Decentralized fact-checking through multi-agent consensus",
    version=config.version,
    docs_url=f"{config.api_prefix}/docs",
    redoc_url=f"{config.api_prefix}/redoc",
    debug=config.debug
)

# Configure CORS with configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": config.app_name,
        "version": config.version,
        "environment": config.environment
    }

@app.get(f"{config.api_prefix}/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "config_loaded": True,
        "agent_config_available": config.default_agent_config is not None,
        "checks": {
            "api": "operational",
            "database": "pending",  # Will be implemented
            "redis": "pending",     # Will be implemented
            "agents": "pending"     # Will be implemented
        }
    }

@app.get(f"{config.api_prefix}/config")
async def get_config_info():
    """Get current configuration information (non-sensitive)"""
    return {
        "app_name": config.app_name,
        "version": config.version,
        "environment": config.environment,
        "debug": config.debug,
        "agent_pool_size": config.agent_pool_size,
        "max_verification_time": config.max_verification_time,
        "has_default_agent_config": config.default_agent_config is not None
    }

# This will be used when running directly (not in container)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.debug
    )
