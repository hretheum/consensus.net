"""
ConsensusNet API - Main entry point
Container-first FastAPI application
"""
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os

from api.models import VerificationRequest, VerificationResponse, ErrorResponse
from api.rate_limiter import rate_limit_middleware
from services.verification_service import verification_service

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

# Add rate limiting middleware
app.middleware("http")(rate_limit_middleware)

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


@app.post(
    "/api/verify",
    response_model=VerificationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Invalid input"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Verify a factual claim",
    description="Submit a factual claim for verification by the ConsensusNet system. Returns a structured verification result with verdict, confidence, reasoning, and sources."
)
async def verify_claim(request: VerificationRequest) -> VerificationResponse:
    """
    Verify a factual claim using the ConsensusNet verification system.
    
    This endpoint processes factual claims and returns comprehensive verification results
    including verdict (TRUE/FALSE/UNCERTAIN), confidence score, reasoning, and sources.
    
    Rate limited to 10 requests per minute per IP address.
    """
    start_time = time.time()
    
    try:
        # Perform verification using the service
        result = await verification_service.verify_claim(request)
        
        processing_time = time.time() - start_time
        
        return VerificationResponse(
            success=True,
            result=result,
            processing_time=processing_time
        )
    
    except ValueError as e:
        # Handle validation errors
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=400,
            detail={
                "success": False,
                "error": str(e),
                "error_code": "VALIDATION_ERROR",
                "processing_time": processing_time
            }
        )
    
    except Exception as e:
        # Handle unexpected errors
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": "Internal server error during verification",
                "error_code": "INTERNAL_ERROR",
                "processing_time": processing_time
            }
        )


@app.get("/api/verify/stats")
async def get_verification_stats():
    """Get statistics about the verification service."""
    return {
        "status": "operational",
        "service": "verification",
        **verification_service.get_agent_stats()
    }

# This will be used when running directly (not in container)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
