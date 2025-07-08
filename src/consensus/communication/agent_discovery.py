"""
Agent Discovery and Capability Registration System

Allows agents to:
- Register their capabilities and expertise
- Discover other agents with specific skills
- Form collaborative networks based on complementary abilities
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Set, Optional, Any
from collections import defaultdict


class AgentType(Enum):
    """Types of agents in the system."""
    GENERALIST = "generalist"        # Can handle any claim type
    SCIENCE = "science"             # Scientific claims and papers
    NEWS = "news"                   # Current events and breaking news
    TECH = "tech"                   # Technical documentation and specs
    HEALTH = "health"               # Medical and health claims
    FINANCE = "finance"             # Financial and economic claims
    SOCIAL = "social"               # Social media and cultural claims
    ORCHESTRATOR = "orchestrator"   # Coordinates other agents
    VALIDATOR = "validator"         # Validates and cross-checks results


class CapabilityType(Enum):
    """Specific capabilities agents can have."""
    
    # Data sources
    PUBMED_SEARCH = "pubmed_search"
    ARXIV_SEARCH = "arxiv_search"
    WIKIPEDIA_SEARCH = "wikipedia_search"
    NEWS_API = "news_api"
    SOCIAL_MEDIA = "social_media"
    WEB_SCRAPING = "web_scraping"
    
    # Language processing
    FACT_EXTRACTION = "fact_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"
    
    # Domain expertise
    SCIENTIFIC_ANALYSIS = "scientific_analysis"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    MEDICAL_KNOWLEDGE = "medical_knowledge"
    TECHNICAL_DOCS = "technical_docs"
    FINANCIAL_ANALYSIS = "financial_analysis"
    
    # Meta capabilities
    CLAIM_DECOMPOSITION = "claim_decomposition"
    EVIDENCE_SYNTHESIS = "evidence_synthesis"
    CONTRADICTION_DETECTION = "contradiction_detection"
    BIAS_DETECTION = "bias_detection"


@dataclass
class AgentCapability:
    """Represents a specific capability of an agent."""
    
    capability_type: CapabilityType
    confidence_level: float  # 0.0 to 1.0 - how good the agent is at this
    cost_estimate: float     # Relative cost of using this capability
    avg_response_time: float # Average response time in seconds
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_recent(self, max_age_hours: int = 24) -> bool:
        """Check if capability info is recent."""
        age = datetime.now() - self.last_updated
        return age < timedelta(hours=max_age_hours)


@dataclass 
class AgentProfile:
    """Complete profile of an agent including all capabilities."""
    
    agent_id: str
    agent_type: AgentType
    display_name: str
    description: str
    
    # Capabilities and performance
    capabilities: Dict[CapabilityType, AgentCapability] = field(default_factory=dict)
    domain_expertise: Dict[str, float] = field(default_factory=dict)
    
    # Runtime information
    is_active: bool = True
    current_load: float = 0.0  # 0.0 = idle, 1.0 = fully loaded
    last_heartbeat: datetime = field(default_factory=datetime.now)
    
    # Performance history
    total_requests: int = 0
    successful_requests: int = 0
    avg_response_time: float = 0.0
    reputation_score: float = 0.5  # 0.0 to 1.0
    
    # Contact information
    message_handler: Optional[str] = None
    api_endpoint: Optional[str] = None
    
    def add_capability(self, capability: AgentCapability) -> None:
        """Add or update a capability."""
        self.capabilities[capability.capability_type] = capability
    
    def has_capability(self, capability_type: CapabilityType, min_confidence: float = 0.5) -> bool:
        """Check if agent has a capability above minimum confidence."""
        cap = self.capabilities.get(capability_type)
        return cap is not None and cap.confidence_level >= min_confidence
    
    def get_capability_confidence(self, capability_type: CapabilityType) -> float:
        """Get confidence level for a specific capability."""
        cap = self.capabilities.get(capability_type)
        return cap.confidence_level if cap else 0.0
    
    def is_available(self, max_load: float = 0.8) -> bool:
        """Check if agent is available for new requests."""
        return (
            self.is_active and 
            self.current_load < max_load and
            self.is_responsive()
        )
    
    def is_responsive(self, max_age_minutes: int = 5) -> bool:
        """Check if agent has sent recent heartbeat."""
        age = datetime.now() - self.last_heartbeat
        return age < timedelta(minutes=max_age_minutes)
    
    def update_performance(self, response_time: float, success: bool) -> None:
        """Update performance metrics after a request."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        
        # Update average response time (exponential moving average)
        alpha = 0.1
        self.avg_response_time = (
            alpha * response_time + 
            (1 - alpha) * self.avg_response_time
        )
        
        # Update reputation (simple success rate)
        self.reputation_score = (
            self.successful_requests / self.total_requests
            if self.total_requests > 0 else 0.5
        )


class AgentRegistry:
    """
    Central registry for agent discovery and capability matching.
    
    Maintains profiles of all active agents and provides methods
    to find the best agents for specific tasks.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self.agents: Dict[str, AgentProfile] = {}
        self.capability_index: Dict[CapabilityType, Set[str]] = defaultdict(set)
        self.type_index: Dict[AgentType, Set[str]] = defaultdict(set)
        self.registration_history: List[Dict[str, Any]] = []
    
    def register_agent(self, profile: AgentProfile) -> bool:
        """
        Register a new agent or update existing profile.
        
        Args:
            profile: Complete agent profile
            
        Returns:
            True if registration successful
        """
        try:
            # Store the profile
            self.agents[profile.agent_id] = profile
            
            # Update indexes
            self.type_index[profile.agent_type].add(profile.agent_id)
            
            for capability_type in profile.capabilities:
                self.capability_index[capability_type].add(profile.agent_id)
            
            # Log registration
            self.registration_history.append({
                "agent_id": profile.agent_id,
                "action": "register",
                "timestamp": datetime.now().isoformat(),
                "agent_type": profile.agent_type.value,
                "capabilities": [cap.value for cap in profile.capabilities.keys()]
            })
            
            return True
            
        except Exception as e:
            print(f"Agent registration failed for {profile.agent_id}: {e}")
            return False
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id not in self.agents:
            return False
        
        profile = self.agents[agent_id]
        
        # Remove from indexes
        self.type_index[profile.agent_type].discard(agent_id)
        for capability_type in profile.capabilities:
            self.capability_index[capability_type].discard(agent_id)
        
        # Remove profile
        del self.agents[agent_id]
        
        # Log unregistration
        self.registration_history.append({
            "agent_id": agent_id,
            "action": "unregister", 
            "timestamp": datetime.now().isoformat()
        })
        
        return True
    
    def find_agents_by_capability(
        self,
        capability_type: CapabilityType,
        min_confidence: float = 0.5,
        max_load: float = 0.8,
        limit: int = 10
    ) -> List[AgentProfile]:
        """
        Find agents with a specific capability.
        
        Args:
            capability_type: The capability to search for
            min_confidence: Minimum confidence level required
            max_load: Maximum load level for availability
            limit: Maximum number of agents to return
            
        Returns:
            List of matching agent profiles, sorted by suitability
        """
        candidates = []
        
        # Get agents with this capability
        agent_ids = self.capability_index.get(capability_type, set())
        
        for agent_id in agent_ids:
            profile = self.agents.get(agent_id)
            if not profile:
                continue
            
            # Check if agent meets requirements
            if (profile.has_capability(capability_type, min_confidence) and
                profile.is_available(max_load)):
                
                # Calculate suitability score
                capability = profile.capabilities[capability_type]
                suitability = self._calculate_suitability_score(profile, capability)
                
                candidates.append((suitability, profile))
        
        # Sort by suitability (higher is better) and return top candidates
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [profile for _, profile in candidates[:limit]]
    
    def find_agents_by_type(
        self,
        agent_type: AgentType,
        max_load: float = 0.8,
        limit: int = 10
    ) -> List[AgentProfile]:
        """Find available agents of a specific type."""
        candidates = []
        
        agent_ids = self.type_index.get(agent_type, set())
        
        for agent_id in agent_ids:
            profile = self.agents.get(agent_id)
            if profile and profile.is_available(max_load):
                candidates.append(profile)
        
        # Sort by reputation and load
        candidates.sort(
            key=lambda p: (p.reputation_score, -p.current_load),
            reverse=True
        )
        
        return candidates[:limit]
    
    def find_best_agent_for_claim(
        self,
        claim: str,
        domain: str,
        complexity: str,
        required_capabilities: Optional[List[CapabilityType]] = None
    ) -> Optional[AgentProfile]:
        """
        Find the best agent to handle a specific claim.
        
        Args:
            claim: The claim to be verified
            domain: Domain of the claim (science, news, etc.)
            complexity: Complexity level (simple, moderate, complex)
            required_capabilities: Specific capabilities needed
            
        Returns:
            Best matching agent profile or None
        """
        candidates = []
        
        # Determine agent types suitable for this domain
        suitable_types = self._get_suitable_agent_types(domain)
        
        for agent_type in suitable_types:
            type_agents = self.find_agents_by_type(agent_type, limit=5)
            candidates.extend(type_agents)
        
        # If specific capabilities required, filter further
        if required_capabilities:
            filtered_candidates = []
            for agent in candidates:
                if all(agent.has_capability(cap) for cap in required_capabilities):
                    filtered_candidates.append(agent)
            candidates = filtered_candidates
        
        if not candidates:
            return None
        
        # Score candidates based on multiple factors
        scored_candidates = []
        for agent in candidates:
            score = self._calculate_claim_suitability(agent, claim, domain, complexity)
            scored_candidates.append((score, agent))
        
        # Return the highest scoring agent
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        return scored_candidates[0][1] if scored_candidates else None
    
    def get_collaboration_suggestions(
        self,
        primary_agent_id: str,
        claim: str,
        domain: str
    ) -> List[AgentProfile]:
        """
        Suggest agents that could collaborate with the primary agent.
        
        Returns agents with complementary capabilities.
        """
        primary_agent = self.agents.get(primary_agent_id)
        if not primary_agent:
            return []
        
        # Find gaps in primary agent's capabilities
        all_capabilities = set(CapabilityType)
        primary_capabilities = set(primary_agent.capabilities.keys())
        missing_capabilities = all_capabilities - primary_capabilities
        
        # Find agents that have the missing capabilities
        collaborators = []
        
        for capability in missing_capabilities:
            suitable_agents = self.find_agents_by_capability(capability, limit=3)
            collaborators.extend(suitable_agents)
        
        # Remove duplicates and the primary agent itself
        unique_collaborators = []
        seen_ids = {primary_agent_id}
        
        for agent in collaborators:
            if agent.agent_id not in seen_ids:
                unique_collaborators.append(agent)
                seen_ids.add(agent.agent_id)
        
        return unique_collaborators[:5]
    
    def _calculate_suitability_score(
        self, 
        profile: AgentProfile, 
        capability: AgentCapability
    ) -> float:
        """Calculate how suitable an agent is for a task."""
        # Base score is the capability confidence
        score = capability.confidence_level
        
        # Adjust for reputation
        score *= (0.5 + 0.5 * profile.reputation_score)
        
        # Adjust for availability (lower load is better)
        load_factor = 1.0 - profile.current_load
        score *= (0.7 + 0.3 * load_factor)
        
        # Adjust for responsiveness
        if profile.is_responsive():
            score *= 1.1
        else:
            score *= 0.8
        
        return min(1.0, score)
    
    def _get_suitable_agent_types(self, domain: str) -> List[AgentType]:
        """Get agent types suitable for a domain."""
        domain_mapping = {
            "science": [AgentType.SCIENCE, AgentType.GENERALIST],
            "health": [AgentType.HEALTH, AgentType.SCIENCE, AgentType.GENERALIST],
            "tech": [AgentType.TECH, AgentType.GENERALIST],
            "news": [AgentType.NEWS, AgentType.GENERALIST],
            "finance": [AgentType.FINANCE, AgentType.GENERALIST],
            "social": [AgentType.SOCIAL, AgentType.GENERALIST],
            "general": [AgentType.GENERALIST]
        }
        
        return domain_mapping.get(domain, [AgentType.GENERALIST])
    
    def _calculate_claim_suitability(
        self,
        agent: AgentProfile,
        claim: str,
        domain: str,
        complexity: str
    ) -> float:
        """Calculate how suitable an agent is for a specific claim."""
        # Base score from reputation
        score = agent.reputation_score
        
        # Domain expertise bonus
        domain_expertise = agent.domain_expertise.get(domain, 0.5)
        score += 0.3 * domain_expertise
        
        # Complexity handling (simpler claims for overloaded agents)
        complexity_weights = {"simple": 0.9, "moderate": 1.0, "complex": 1.1}
        complexity_weight = complexity_weights.get(complexity, 1.0)
        
        if agent.current_load > 0.6:  # If agent is busy, prefer simpler claims
            complexity_weight *= (1.5 - agent.current_load)
        
        score *= complexity_weight
        
        # Availability factor
        if agent.is_available():
            score *= 1.2
        else:
            score *= 0.5
        
        return min(1.0, score)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent registry."""
        total_agents = len(self.agents)
        active_agents = sum(1 for a in self.agents.values() if a.is_active)
        responsive_agents = sum(1 for a in self.agents.values() if a.is_responsive())
        
        # Capability distribution
        capability_counts = {
            cap.value: len(agents) 
            for cap, agents in self.capability_index.items()
        }
        
        # Type distribution
        type_counts = {
            agent_type.value: len(agents)
            for agent_type, agents in self.type_index.items()
        }
        
        return {
            "total_agents": total_agents,
            "active_agents": active_agents,
            "responsive_agents": responsive_agents,
            "avg_reputation": sum(a.reputation_score for a in self.agents.values()) / total_agents if total_agents > 0 else 0,
            "avg_load": sum(a.current_load for a in self.agents.values()) / total_agents if total_agents > 0 else 0,
            "capability_distribution": capability_counts,
            "type_distribution": type_counts,
            "registrations_today": len([
                r for r in self.registration_history 
                if datetime.fromisoformat(r["timestamp"]).date() == datetime.now().date()
            ])
        }
    
    def cleanup_inactive_agents(self, max_age_hours: int = 24) -> int:
        """Remove agents that haven't sent heartbeat recently."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        inactive_agents = [
            agent_id for agent_id, profile in self.agents.items()
            if profile.last_heartbeat < cutoff_time
        ]
        
        for agent_id in inactive_agents:
            self.unregister_agent(agent_id)
        
        return len(inactive_agents)


# Global agent registry instance
agent_registry = AgentRegistry()