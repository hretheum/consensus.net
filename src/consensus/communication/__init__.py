"""
Inter-Agent Communication Module

Implements message passing protocols and communication infrastructure
for the multi-agent consensus system.
"""

from src.consensus.communication.message_passing import AgentMessage, MessageType, MessageBus
from src.consensus.communication.agent_discovery import AgentRegistry, AgentCapability

__all__ = [
    "AgentMessage",
    "MessageType", 
    "MessageBus",
    "AgentRegistry",
    "AgentCapability"
]