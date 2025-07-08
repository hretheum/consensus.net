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
            "agents": "operational",
            "llm_services": "checking..."
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


@app.post(
    "/api/verify/enhanced",
    response_model=VerificationResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request - Invalid input"},
        422: {"model": ErrorResponse, "description": "Validation Error"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    },
    summary="Verify a claim using enhanced LLM integration",
    description="Submit a factual claim for verification using real LLM APIs with fallback to simulation. Provides more sophisticated analysis than the standard verification endpoint."
)
async def verify_claim_enhanced(request: VerificationRequest) -> VerificationResponse:
    """
    Verify a factual claim using enhanced LLM integration.
    
    This endpoint uses real LLM APIs (OpenAI, Anthropic, Ollama) for verification
    with automatic fallback strategies. It provides more sophisticated analysis
    and better confidence calibration than the standard endpoint.
    
    To use this endpoint, ensure you have set the appropriate API keys:
    - OPENAI_API_KEY for GPT-4o-mini
    - ANTHROPIC_API_KEY for Claude 3 Haiku
    - Local Ollama for Llama 3.2 (fallback)
    
    Rate limited to 10 requests per minute per IP address.
    """
    start_time = time.time()
    
    try:
        # Force enhanced agent usage
        if not request.metadata:
            request.metadata = {}
        request.metadata["agent_type"] = "enhanced"
        
        # Perform verification using the enhanced service
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
                "error": "Internal server error during enhanced verification",
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


@app.get("/api/llm/status")
async def get_llm_status():
    """Get status and availability of LLM services."""
    try:
        llm_status = verification_service.get_llm_service_status()
        
        return {
            "status": "operational",
            "service": "llm_integration",
            "llm_services": llm_status,
            "timestamp": time.time()
        }
    
    except Exception as e:
        return {
            "status": "error",
            "service": "llm_integration",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/api/system/info")
async def get_system_info():
    """Get comprehensive system information and status."""
    try:
        agent_stats = verification_service.get_agent_stats()
        llm_status = verification_service.get_llm_service_status()
        
        return {
            "system": {
                "api_version": "0.1.0",
                "environment": os.getenv("ENVIRONMENT", "development"),
                "status": "operational"
            },
            "agents": agent_stats,
            "llm_services": llm_status,
            "capabilities": {
                "simple_verification": True,
                "enhanced_verification": True,
                "real_llm_integration": True,
                "fallback_simulation": True,
                "multi_provider_support": True
            },
            "endpoints": {
                "verify": "/api/verify",
                "verify_enhanced": "/api/verify/enhanced",
                "stats": "/api/verify/stats",
                "llm_status": "/api/llm/status",
                "docs": "/api/docs"
            },
            "timestamp": time.time()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Failed to get system info: {str(e)}",
                "error_code": "SYSTEM_INFO_ERROR"
            }
        )


# This will be used when running directly (not in container)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
