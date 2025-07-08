"""
VerificationResult data model for fact-checking results.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """
    Result of a fact verification process.
    
    This model represents the output of any agent's verification of a claim,
    providing structured information about the verification outcome.
    """
    
    claim: str = Field(..., description="The original claim that was verified")
    verdict: str = Field(..., description="The verification verdict (e.g., 'TRUE', 'FALSE', 'UNCERTAIN')")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    reasoning: str = Field(..., description="Explanation of the verification reasoning")
    sources: List[str] = Field(default_factory=list, description="List of source URLs used for verification")
    evidence: List[str] = Field(default_factory=list, description="Key pieces of evidence found")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the verification")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the verification was performed")
    agent_id: Optional[str] = Field(None, description="Identifier of the agent that performed the verification")
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True
        
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"VerificationResult(verdict={self.verdict}, confidence={self.confidence:.2f})"
    
    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return (
            f"VerificationResult(claim='{self.claim[:50]}...', "
            f"verdict='{self.verdict}', confidence={self.confidence})"
        )