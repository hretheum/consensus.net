"""
API request and response models for the ConsensusNet API.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from agents.verification_result import VerificationResult


class VerificationRequest(BaseModel):
    """Request model for the /verify endpoint."""
    
    claim: str = Field(
        ..., 
        min_length=1,
        max_length=2000,
        description="The factual claim to be verified",
        examples=["The sky is blue", "2+2=4", "The Earth is flat"]
    )
    
    agent_id: Optional[str] = Field(
        None,
        description="Optional agent ID to use for verification",
        max_length=100
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Optional metadata to include with the request"
    )


class VerificationResponse(BaseModel):
    """Response model for the /verify endpoint."""
    
    success: bool = Field(..., description="Whether the verification was successful")
    result: VerificationResult = Field(..., description="The verification result")
    processing_time: float = Field(..., description="Time taken to process the request in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the response was generated")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Error response model for API endpoints."""
    
    success: bool = Field(False, description="Indicates the request failed")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RateLimitInfo(BaseModel):
    """Rate limit information included in responses."""
    
    limit: int = Field(..., description="Maximum requests allowed per minute")
    remaining: int = Field(..., description="Remaining requests in current window")
    reset_time: datetime = Field(..., description="When the rate limit window resets")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }