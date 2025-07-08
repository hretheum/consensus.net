"""
Verification service for handling fact-checking requests.
"""
import time
import asyncio
from typing import Optional, Dict, Any

from agents.simple_agent import SimpleAgent
from agents.enhanced_agent import EnhancedAgent
from agents.verification_result import VerificationResult
from api.models import VerificationRequest


class VerificationService:
    """Service class for handling verification requests."""
    
    def __init__(self):
        """Initialize the verification service."""
        self._simple_agents = {}
        self._enhanced_agents = {}
    
    def get_or_create_simple_agent(self, agent_id: Optional[str] = None) -> SimpleAgent:
        """
        Get existing simple agent or create new one.
        
        Args:
            agent_id: Optional agent ID. If None, uses default agent.
            
        Returns:
            SimpleAgent instance
        """
        if agent_id is None:
            agent_id = "default"
        
        if agent_id not in self._simple_agents:
            self._simple_agents[agent_id] = SimpleAgent(agent_id=agent_id)
        
        return self._simple_agents[agent_id]
    
    def get_or_create_enhanced_agent(self, agent_id: Optional[str] = None) -> EnhancedAgent:
        """
        Get existing enhanced agent or create new one.
        
        Args:
            agent_id: Optional agent ID. If None, uses default agent.
            
        Returns:
            EnhancedAgent instance
        """
        if agent_id is None:
            agent_id = "enhanced_default"
        
        if agent_id not in self._enhanced_agents:
            self._enhanced_agents[agent_id] = EnhancedAgent(agent_id=agent_id)
        
        return self._enhanced_agents[agent_id]
    
    async def verify_claim(self, request: VerificationRequest) -> VerificationResult:
        """
        Verify a claim using the appropriate agent.
        
        Args:
            request: Verification request containing claim and options
            
        Returns:
            VerificationResult with the verification outcome
        """
        # Determine agent type from metadata or default to simple
        agent_type = "simple"
        if request.metadata:
            agent_type = request.metadata.get("agent_type", "simple")
        
        # Get or create appropriate agent
        if agent_type == "enhanced":
            agent = self.get_or_create_enhanced_agent(request.agent_id)
            # Use async verify for enhanced agent
            result = await agent.verify_async(request.claim)
        else:
            agent = self.get_or_create_simple_agent(request.agent_id)
            # Use sync verify for simple agent
            result = agent.verify(request.claim)
        
        # Add any request metadata to result metadata
        if request.metadata:
            result.metadata.update({"request_metadata": request.metadata})
        
        return result
    
    def verify_claim_sync(self, request: VerificationRequest) -> VerificationResult:
        """
        Synchronous wrapper for verify_claim.
        
        Args:
            request: Verification request containing claim and options
            
        Returns:
            VerificationResult with the verification outcome
        """
        return asyncio.run(self.verify_claim(request))
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active agents.
        
        Returns:
            Dictionary with agent statistics
        """
        stats = {
            "simple_agents": {
                "count": len(self._simple_agents),
                "agent_ids": list(self._simple_agents.keys()),
                "agents": {
                    agent_id: {
                        "agent_id": agent.agent_id,
                        "class": agent.__class__.__name__
                    }
                    for agent_id, agent in self._simple_agents.items()
                }
            },
            "enhanced_agents": {
                "count": len(self._enhanced_agents),
                "agent_ids": list(self._enhanced_agents.keys()),
                "agents": {
                    agent_id: {
                        "agent_id": agent.agent_id,
                        "class": agent.__class__.__name__,
                        "llm_stats": agent.get_llm_stats()
                    }
                    for agent_id, agent in self._enhanced_agents.items()
                }
            }
        }
        
        return stats
    
    def get_llm_service_status(self) -> Dict[str, Any]:
        """
        Get status of LLM services and API availability.
        
        Returns:
            Dictionary with LLM service status
        """
        # Try to get status from an enhanced agent
        if self._enhanced_agents:
            agent = next(iter(self._enhanced_agents.values()))
            return agent.get_llm_stats()
        else:
            # Create a temporary enhanced agent to check status
            temp_agent = EnhancedAgent(agent_id="temp_status_check")
            return temp_agent.get_llm_stats()


# Global verification service instance
verification_service = VerificationService()