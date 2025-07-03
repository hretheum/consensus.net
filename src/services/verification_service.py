"""
Verification service for handling fact-checking requests.
"""
import time
from typing import Optional, Dict, Any

from agents.simple_agent import SimpleAgent
from agents.verification_result import VerificationResult
from api.models import VerificationRequest


class VerificationService:
    """Service class for handling verification requests."""
    
    def __init__(self):
        """Initialize the verification service."""
        self._agents = {}
    
    def get_or_create_agent(self, agent_id: Optional[str] = None) -> SimpleAgent:
        """
        Get existing agent or create new one.
        
        Args:
            agent_id: Optional agent ID. If None, uses default agent.
            
        Returns:
            SimpleAgent instance
        """
        if agent_id is None:
            agent_id = "default"
        
        if agent_id not in self._agents:
            self._agents[agent_id] = SimpleAgent(agent_id=agent_id)
        
        return self._agents[agent_id]
    
    async def verify_claim(self, request: VerificationRequest) -> VerificationResult:
        """
        Verify a claim using the appropriate agent.
        
        Args:
            request: Verification request containing claim and options
            
        Returns:
            VerificationResult with the verification outcome
        """
        # Get or create agent
        agent = self.get_or_create_agent(request.agent_id)
        
        # Add request metadata to agent context if needed
        if request.metadata:
            # For now, just log the metadata - could be used for context in future
            pass
        
        # Perform verification
        result = agent.verify(request.claim)
        
        # Add any request metadata to result metadata
        if request.metadata:
            result.metadata.update({"request_metadata": request.metadata})
        
        return result
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active agents.
        
        Returns:
            Dictionary with agent statistics
        """
        return {
            "active_agents": len(self._agents),
            "agent_ids": list(self._agents.keys()),
            "agents": {
                agent_id: {
                    "agent_id": agent.agent_id,
                    "class": agent.__class__.__name__
                }
                for agent_id, agent in self._agents.items()
            }
        }


# Global verification service instance
verification_service = VerificationService()