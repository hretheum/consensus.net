"""
ConsensusNet Multi-Agent System

This module implements the multi-agent consensus architecture for 
distributed fact-checking as defined in Phase 2 of the roadmap.

Key components:
- Agent Pool Management
- Inter-Agent Communication  
- Specialized Verification Agents
- Consensus Mechanisms
"""

__version__ = "2.0.0"
__phase__ = "Multi-Agent System"

from .communication.message_passing import AgentMessage, MessageType
from .orchestration.agent_pool import AgentPoolManager
from .agents.specialized_agents import SpecializedAgent, ScienceAgent, NewsAgent, TechAgent

__all__ = [
    "AgentMessage",
    "MessageType", 
    "AgentPoolManager",
    "SpecializedAgent",
    "ScienceAgent",
    "NewsAgent", 
    "TechAgent"
]