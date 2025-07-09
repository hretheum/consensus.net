"""
Data models supporting the core agent architecture.

These models define the data structures used throughout the agent verification pipeline,
as documented in docs/architecture/core-agent-architecture.md
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class ClaimComplexity(Enum):
    """Enumeration of claim complexity levels."""
    SIMPLE = "simple"           # Basic factual claims
    MODERATE = "moderate"       # Claims requiring some analysis
    COMPLEX = "complex"         # Multi-faceted claims requiring deep analysis
    RESEARCH = "research"       # Claims requiring academic/scientific research


@dataclass
class ProcessedClaim:
    """
    Represents a claim after input processing and normalization.
    
    This is the standardized format used throughout the verification pipeline.
    """
    original_text: str
    normalized_text: str
    domain: str
    complexity: ClaimComplexity
    context: Dict[str, Any]
    preprocessing_metadata: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "original_text": self.original_text,
            "normalized_text": self.normalized_text,
            "domain": self.domain,
            "complexity": self.complexity.value,
            "context": self.context,
            "preprocessing_metadata": self.preprocessing_metadata,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Evidence:
    """
    Represents a piece of evidence gathered during verification.
    
    Each piece of evidence includes content, source information, and quality scores.
    """
    content: str
    source: str
    credibility_score: float
    relevance_score: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "content": self.content,
            "source": self.source,
            "credibility_score": self.credibility_score,
            "relevance_score": self.relevance_score,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class EvidenceBundle:
    """Bundle of evidence collected from various sources."""
    supporting_evidence: List[Evidence]
    contradicting_evidence: List[Evidence]
    neutral_evidence: List[Evidence]
    overall_quality: float
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def total_evidence_count(self) -> int:
        """Get total count of all evidence items."""
        return len(self.supporting_evidence) + len(self.contradicting_evidence) + len(self.neutral_evidence)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "supporting_evidence": [e.to_dict() for e in self.supporting_evidence],
            "contradicting_evidence": [e.to_dict() for e in self.contradicting_evidence],
            "neutral_evidence": [e.to_dict() for e in self.neutral_evidence],
            "overall_quality": self.overall_quality,
            "metadata": self.metadata
        }


@dataclass
class LLMRequest:
    """
    Request structure for LLM API calls.
    
    Encapsulates all parameters needed for a structured LLM interaction.
    """
    prompt: str
    model: str
    parameters: Dict[str, Any]
    context: Optional[str] = None
    expected_format: str = "text"
    max_tokens: int = 1000
    temperature: float = 0.1


@dataclass
class LLMResponse:
    """
    Response structure from LLM API calls.
    
    Contains the response content along with metadata about the interaction.
    """
    content: str
    metadata: Dict[str, Any]
    model_used: str
    tokens_used: int
    confidence: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VerificationStep:
    """
    Represents a single step in the verification reasoning chain.
    
    Documents each discrete action taken during the verification process.
    """
    step_type: str
    input_data: Any
    output_data: Any
    confidence: float
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class VerificationChain:
    """
    Complete chain of verification steps leading to a final verdict.
    
    Provides full traceability of the verification reasoning process.
    """
    steps: List[VerificationStep] = field(default_factory=list)
    overall_verdict: str = "PENDING"
    final_confidence: float = 0.0
    uncertainty_factors: List[str] = field(default_factory=list)
    processing_time: float = 0.0


@dataclass
class AgentState:
    """
    Maintains the current state of an agent during verification.
    
    Tracks session information, progress, and accumulated knowledge.
    """
    agent_id: str
    session_id: str
    current_claim: Optional[ProcessedClaim] = None
    verification_history: List['VerificationResult'] = field(default_factory=list)
    intermediate_results: Dict[str, Any] = field(default_factory=dict)
    confidence_calibration: float = 1.0
    domain_expertise: Dict[str, float] = field(default_factory=dict)
    session_start_time: datetime = field(default_factory=datetime.now)
    
    def add_verification(self, result: 'VerificationResult') -> None:
        """Add a completed verification to the agent's history."""
        self.verification_history.append(result)
        
        # Update domain expertise based on verification outcome
        if result.claim and hasattr(self.current_claim, 'domain'):
            domain = self.current_claim.domain
            current_expertise = self.domain_expertise.get(domain, 0.5)
            
            # Simple update: increase expertise if confident result, decrease if uncertain
            if result.confidence > 0.8:
                self.domain_expertise[domain] = min(1.0, current_expertise + 0.01)
            elif result.confidence < 0.3:
                self.domain_expertise[domain] = max(0.0, current_expertise - 0.01)


@dataclass
class AgentConfig:
    """
    Configuration parameters for agent behavior and capabilities.
    
    Defines how an agent should behave, what models to use, and what
    thresholds to apply during verification.
    """
    # Identity
    agent_id: str
    domain_expertise: List[str] = field(default_factory=list)
    
    # LLM Configuration (based on research in docs/research/llm-selection-analysis.md)
    primary_model: str = "gpt-4.1-mini"  # Primary: best balance of cost/performance
    secondary_model: str = "claude-sonnet-4"  # Secondary: complex reasoning tasks
    fallback_model: str = "gpt-4.1-nano"  # Fallback: fastest for urgent tasks
    max_tokens: int = 2000
    temperature: float = 0.1
    
    # Verification Parameters
    confidence_threshold: float = 0.7
    evidence_sources: List[str] = field(default_factory=list)
    max_verification_time: int = 30  # seconds
    
    # Memory Settings
    max_history_items: int = 100
    memory_decay_factor: float = 0.95
    
    # Output Settings
    detailed_reasoning: bool = True
    include_uncertainty: bool = True
    evidence_limit: int = 10


@dataclass
class PerformanceMetrics:
    """
    Performance metrics for monitoring agent efficiency and resource usage.
    
    Tracks key performance indicators during verification processes.
    """
    verification_time: float = 0.0
    tokens_used: int = 0
    api_calls_made: int = 0
    evidence_sources_checked: int = 0
    memory_usage: float = 0.0
    cache_hit_rate: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Calculate derived metrics after initialization."""
        if self.api_calls_made > 0:
            self.avg_tokens_per_call = self.tokens_used / self.api_calls_made
        else:
            self.avg_tokens_per_call = 0.0


# Error handling data structures

class AgentError(Exception):
    """Base exception for agent-related errors."""
    pass


class InputError(AgentError):
    """Exception for input processing errors."""
    pass


class VerificationError(AgentError):
    """Exception for verification process errors."""
    pass


class LLMError(AgentError):
    """Exception for LLM interaction errors."""
    pass


class EvidenceError(AgentError):
    """Exception for evidence gathering errors."""
    pass


# Import the VerificationResult from the existing module to avoid circular imports
# This is a forward reference that will be resolved at runtime
if False:  # Type checking only
    from .verification_result import VerificationResult