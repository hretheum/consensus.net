"""
ConsensusNet API - Main entry point
Container-first FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

# Create FastAPI app
app = FastAPI(
    title="ConsensusNet API",
    description="Decentralized fact-checking through multi-agent consensus",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": "ConsensusNet API",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "checks": {
            "api": "operational",
            "database": "pending",  # Will be implemented
            "redis": "pending",     # Will be implemented
            "agents": "pending"     # Will be implemented
        }
    }

# This will be used when running directly (not in container)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
