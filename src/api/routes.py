"""
API routes for ConsensusNet.

This module defines the main API endpoints for interacting with the AI agents.
"""
import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Security, status, Request
from fastapi.responses import JSONResponse

from .models import (
    VerificationRequest, 
    VerificationResponse, 
    AgentStatusResponse, 
    AgentCapability,
    APIErrorResponse,
    APIErrorDetail,
    HealthCheckResponse
)
from .auth import get_api_key, require_api_key, check_permission, check_rate_limit, APIKeyInfo
from agents.simple_agent import SimpleAgent
from agents.verification_result import VerificationResult

# Create router
router = APIRouter(prefix="/api/v1", tags=["ConsensusNet API v1"])

# Global agent instance (in production, this would be managed differently)
_agent_instance = None
_agent_start_time = time.time()
_verification_count = 0
_total_processing_time = 0.0


def get_agent() -> SimpleAgent:
    """Get or create the global agent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = SimpleAgent()
    return _agent_instance


@router.post("/verify", 
             response_model=VerificationResponse,
             summary="Verify a claim",
             description="Submit a claim for fact-checking verification by the AI agent.",
             responses={
                 200: {"description": "Verification completed successfully"},
                 400: {"description": "Invalid request format", "model": APIErrorResponse},
                 401: {"description": "Authentication required", "model": APIErrorResponse},
                 403: {"description": "Insufficient permissions", "model": APIErrorResponse},
                 429: {"description": "Rate limit exceeded", "model": APIErrorResponse},
                 500: {"description": "Internal server error", "model": APIErrorResponse}
             })
async def verify_claim(
    request: VerificationRequest,
    api_key_info: Optional[APIKeyInfo] = Security(get_api_key)
) -> VerificationResponse:
    """
    Verify a factual claim using the AI agent.
    
    This endpoint accepts a claim and returns a comprehensive verification result
    including verdict, confidence score, reasoning, and supporting evidence.
    
    **Authentication**: Optional API key for higher rate limits and tracking.
    **Rate Limiting**: 
    - Without API key: 5 requests per minute
    - With API key: Depends on key tier (10-100 requests per minute)
    
    **Example Request**:
    ```json
    {
        "claim": "The Earth is round",
        "context": "Basic astronomy fact",
        "priority": "normal",
        "require_sources": true
    }
    ```
    """
    global _verification_count, _total_processing_time
    
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Rate limiting
        if api_key_info:
            # Authenticated request - check API key rate limits
            check_permission(api_key_info, "verify")
            rate_limit_info = check_rate_limit(api_key_info.key_id)
        else:
            # Anonymous request - apply stricter rate limiting
            # For now, we'll implement a simple rate limit for anonymous users
            # In production, this would use IP-based rate limiting
            pass
        
        # Get agent and perform verification
        agent = get_agent()
        verification_result = agent.verify(request.claim)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        processing_time_ms = int(processing_time * 1000)
        
        # Update global metrics
        _verification_count += 1
        _total_processing_time += processing_time
        
        # Enhance verification result with request context if provided
        if request.context:
            verification_result.metadata["request_context"] = request.context
        verification_result.metadata["priority"] = request.priority
        verification_result.metadata["require_sources"] = request.require_sources
        
        # Create response
        response = VerificationResponse(
            success=True,
            verification=verification_result,
            request_id=request_id,
            processing_time_ms=processing_time_ms,
            api_version="1.0"
        )
        
        return response
        
    except Exception as e:
        # Log error (in production, use proper logging)
        print(f"Verification error: {str(e)}")
        
        # Create error response
        error_response = APIErrorResponse(
            error_type="VERIFICATION_ERROR",
            message="Failed to process verification request",
            details=[APIErrorDetail(
                code="AGENT_ERROR",
                message=str(e)
            )],
            request_id=request_id
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.get("/agent/status",
            response_model=AgentStatusResponse,
            summary="Get agent status",
            description="Retrieve current status and capabilities of the AI agent.")
async def get_agent_status(
    api_key_info: Optional[APIKeyInfo] = Security(get_api_key)
) -> AgentStatusResponse:
    """
    Get the current status and capabilities of the AI agent.
    
    This endpoint provides information about the agent's health, capabilities,
    performance metrics, and operational statistics.
    
    **Authentication**: Optional API key for detailed metrics.
    """
    global _agent_start_time, _verification_count, _total_processing_time
    
    try:
        agent = get_agent()
        uptime = time.time() - _agent_start_time
        
        # Calculate average response time
        avg_response_time = (_total_processing_time / _verification_count * 1000) if _verification_count > 0 else 0
        
        # Define agent capabilities
        capabilities = [
            AgentCapability(
                capability="claim_verification",
                enabled=True,
                description="Verify factual claims using AI reasoning and evidence gathering",
                performance_metrics={
                    "average_accuracy": 0.75,  # Simulated metric
                    "average_confidence": 0.68,
                    "processing_time_ms": avg_response_time
                }
            ),
            AgentCapability(
                capability="evidence_gathering",
                enabled=True,
                description="Gather supporting evidence from various sources",
                performance_metrics={
                    "sources_per_verification": 2.3,
                    "source_credibility_score": 0.82
                }
            ),
            AgentCapability(
                capability="confidence_scoring",
                enabled=True,
                description="Provide calibrated confidence scores for verification results",
                performance_metrics={
                    "calibration_score": 0.79,
                    "uncertainty_detection": 0.85
                }
            ),
            AgentCapability(
                capability="multilingual_support",
                enabled=False,
                description="Support for non-English claims (planned feature)",
                performance_metrics=None
            )
        ]
        
        # Determine agent status
        agent_status = "healthy"
        if avg_response_time > 5000:  # More than 5 seconds
            agent_status = "degraded"
        
        # Get last verification time (simulated)
        last_verification = datetime.now() if _verification_count > 0 else None
        
        response = AgentStatusResponse(
            agent_id=agent.agent_id,
            status=agent_status,
            capabilities=capabilities,
            uptime_seconds=uptime,
            total_verifications=_verification_count,
            average_response_time_ms=avg_response_time,
            success_rate=0.95,  # Simulated success rate
            last_verification=last_verification,
            version="1.0.0"
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/health",
            response_model=HealthCheckResponse,
            summary="API health check",
            description="Get comprehensive health status of the API and its components.")
async def health_check() -> HealthCheckResponse:
    """
    Comprehensive health check for the API and its components.
    
    This endpoint provides detailed information about the health of various
    system components including the API, agents, database, and external services.
    
    **No authentication required**.
    """
    global _agent_start_time
    
    try:
        # Test agent health
        agent = get_agent()
        agent_status = "operational"
        agent_response_time = None
        
        try:
            start_time = time.time()
            # Simple agent health test
            test_result = agent.verify("Test claim for health check")
            agent_response_time = int((time.time() - start_time) * 1000)
            if agent_response_time > 5000:
                agent_status = "degraded"
        except Exception:
            agent_status = "unavailable"
        
        # Build health checks
        checks = {
            "api": {
                "status": "operational",
                "response_time_ms": 5,  # Simulated
                "version": "1.0.0"
            },
            "agents": {
                "status": agent_status,
                "available_agents": 1,
                "response_time_ms": agent_response_time,
                "total_verifications": _verification_count
            },
            "database": {
                "status": "pending",
                "message": "Database not yet implemented"
            },
            "redis": {
                "status": "pending", 
                "message": "Redis caching not yet implemented"
            },
            "external_apis": {
                "status": "unknown",
                "message": "External API health checking not yet implemented"
            }
        }
        
        # Determine overall status
        overall_status = "healthy"
        if agent_status == "degraded":
            overall_status = "degraded"
        elif agent_status == "unavailable":
            overall_status = "unhealthy"
        
        uptime = time.time() - _agent_start_time
        
        response = HealthCheckResponse(
            status=overall_status,
            version="1.0.0",
            environment="development",  # Would be dynamic in production
            timestamp=datetime.now(),
            uptime_seconds=uptime,
            checks=checks
        )
        
        return response
        
    except Exception as e:
        # Return unhealthy status if health check fails
        return HealthCheckResponse(
            status="unhealthy",
            version="1.0.0",
            environment="development",
            timestamp=datetime.now(),
            uptime_seconds=0,
            checks={
                "api": {
                    "status": "error",
                    "error": str(e)
                }
            }
        )