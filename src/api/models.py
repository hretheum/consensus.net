"""
API data models for ConsensusNet.

This module defines the request and response models for the ConsensusNet API,
extending the existing agent models for external API interactions.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum

from agents.verification_result import VerificationResult


class VerificationRequest(BaseModel):
    """
    Request model for claim verification.
    
    This model defines the structure for incoming verification requests
    through the API endpoint.
    """
    claim: str = Field(
        ..., 
        min_length=1, 
        max_length=5000,
        description="The claim to be verified. Must be a non-empty string with maximum 5000 characters.",
        example="The Earth is round."
    )
    context: Optional[str] = Field(
        None, 
        max_length=2000,
        description="Optional additional context about the claim",
        example="This claim is being fact-checked for a geography textbook."
    )
    priority: Optional[Literal["low", "normal", "high"]] = Field(
        "normal",
        description="Priority level for verification processing",
        example="normal"
    )
    require_sources: Optional[bool] = Field(
        True,
        description="Whether to require source citations in the response",
        example=True
    )
    
    @validator('claim')
    def validate_claim(cls, v):
        """Validate claim content."""
        if not v or v.isspace():
            raise ValueError('Claim cannot be empty or only whitespace')
        return v.strip()


class APIErrorDetail(BaseModel):
    """
    Detailed error information for API responses.
    """
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    field: Optional[str] = Field(None, description="Field that caused the error (for validation errors)")


class APIErrorResponse(BaseModel):
    """
    Standard error response format for the API.
    """
    error: bool = Field(True, description="Always true for error responses")
    error_type: str = Field(..., description="Type of error that occurred")
    message: str = Field(..., description="Main error message")
    details: List[APIErrorDetail] = Field(default_factory=list, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred")
    request_id: Optional[str] = Field(None, description="Unique identifier for this request")


class VerificationResponse(BaseModel):
    """
    Response model for claim verification.
    
    This extends the core VerificationResult with API-specific metadata.
    """
    success: bool = Field(True, description="Whether the verification was successful")
    verification: VerificationResult = Field(..., description="The complete verification result")
    request_id: Optional[str] = Field(None, description="Unique identifier for this request")
    processing_time_ms: Optional[int] = Field(None, description="Time taken to process the request in milliseconds")
    api_version: str = Field("1.0", description="API version used for this response")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentCapability(BaseModel):
    """
    Information about an agent's capabilities.
    """
    capability: str = Field(..., description="Name of the capability")
    enabled: bool = Field(..., description="Whether this capability is currently enabled")
    description: str = Field(..., description="Description of what this capability does")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics for this capability")


class AgentStatusResponse(BaseModel):
    """
    Response model for agent status information.
    """
    agent_id: str = Field(..., description="Unique identifier of the agent")
    status: Literal["healthy", "degraded", "unavailable"] = Field(..., description="Current agent status")
    capabilities: List[AgentCapability] = Field(..., description="List of agent capabilities")
    uptime_seconds: float = Field(..., description="How long the agent has been running in seconds")
    total_verifications: int = Field(..., description="Total number of verifications performed")
    average_response_time_ms: float = Field(..., description="Average response time in milliseconds")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate as a percentage (0-1)")
    last_verification: Optional[datetime] = Field(None, description="Timestamp of the last verification")
    version: str = Field(..., description="Agent version")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """
    Enhanced health check response.
    """
    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="Overall system status")
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Deployment environment")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current server time")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")
    
    # Service checks
    checks: Dict[str, Dict[str, Any]] = Field(
        ..., 
        description="Status of individual service components",
        example={
            "api": {"status": "operational", "response_time_ms": 12},
            "agents": {"status": "operational", "available_agents": 1},
            "database": {"status": "pending", "message": "Not yet implemented"},
            "redis": {"status": "pending", "message": "Not yet implemented"}
        }
    )
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RateLimitInfo(BaseModel):
    """
    Rate limiting information included in API responses.
    """
    limit: int = Field(..., description="Maximum requests allowed in the time window")
    remaining: int = Field(..., description="Requests remaining in the current window")
    reset_time: datetime = Field(..., description="When the rate limit window resets")
    window_seconds: int = Field(..., description="Length of the rate limit window in seconds")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Authentication models
class APIKeyInfo(BaseModel):
    """
    Information about an API key (for authenticated endpoints).
    """
    key_id: str = Field(..., description="Unique identifier for this API key")
    name: Optional[str] = Field(None, description="Human-readable name for this key")
    tier: Literal["free", "standard", "premium"] = Field("free", description="Service tier for this key")
    rate_limit: RateLimitInfo = Field(..., description="Rate limiting information for this key")
    permissions: List[str] = Field(default_factory=list, description="Permissions granted to this key")
    created_at: datetime = Field(..., description="When this key was created")
    last_used: Optional[datetime] = Field(None, description="When this key was last used")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }