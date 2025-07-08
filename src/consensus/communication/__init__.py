"""
Inter-Agent Communication Module

Implements message passing protocols and communication infrastructure
for the multi-agent consensus system.
"""

from .message_passing import AgentMessage, MessageType, MessageBus
from .agent_discovery import AgentRegistry, AgentCapability

__all__ = [
    "AgentMessage",
    "MessageType", 
    "MessageBus",
    "AgentRegistry",
    "AgentCapability"
]