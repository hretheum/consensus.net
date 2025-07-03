"""
BaseAgent abstract class for fact-checking agents.
"""
from abc import ABC, abstractmethod
from .verification_result import VerificationResult


class BaseAgent(ABC):
    """
    Abstract base class for all fact-checking agents in the ConsensusNet system.
    
    This class defines the core interface that all agents must implement to participate
    in the consensus-based fact-checking process. Agents can be specialized for different
    domains, sources, or verification strategies.
    """
    
    def __init__(self, agent_id: str = None):
        """
        Initialize the base agent.
        
        Args:
            agent_id: Unique identifier for this agent instance
        """
        self.agent_id = agent_id if agent_id is not None else self.__class__.__name__
    
    @abstractmethod
    def verify(self, claim: str) -> VerificationResult:
        """
        Verify a factual claim and return the result.
        
        This is the core method that all agents must implement. It takes a claim
        as input and returns a structured verification result.
        
        Args:
            claim: The factual claim to be verified
            
        Returns:
            VerificationResult: Structured result of the verification process
            
        Raises:
            NotImplementedError: If the method is not implemented by the subclass
        """
        pass
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.__class__.__name__}(id={self.agent_id})"
    
    def __repr__(self) -> str:
        """Developer-friendly string representation."""
        return f"{self.__class__.__name__}(agent_id='{self.agent_id}')"