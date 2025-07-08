"""
Message Passing System for Inter-Agent Communication

Implements the communication protocol that allows agents to:
- Share verification findings
- Request assistance from specialists
- Coordinate on complex claims
- Share context and evidence
"""

import asyncio
import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Set
import json

from agents.verification_result import VerificationResult


class MessageType(Enum):
    """Types of messages exchanged between agents."""
    
    # Verification messages
    VERIFICATION_REQUEST = "verification_request"
    VERIFICATION_RESULT = "verification_result"
    VERIFICATION_CHALLENGE = "verification_challenge"
    
    # Evidence sharing
    EVIDENCE_SHARE = "evidence_share"
    EVIDENCE_REQUEST = "evidence_request"
    
    # Coordination messages
    TASK_ASSIGNMENT = "task_assignment"
    CONSENSUS_VOTE = "consensus_vote"
    CONSENSUS_RESULT = "consensus_result"
    
    # System messages
    AGENT_REGISTRATION = "agent_registration"
    AGENT_HEARTBEAT = "agent_heartbeat"
    AGENT_SHUTDOWN = "agent_shutdown"
    
    # Help and collaboration
    HELP_REQUEST = "help_request"
    KNOWLEDGE_SHARE = "knowledge_share"


class MessagePriority(Enum):
    """Message priority levels."""
    URGENT = 1      # System critical
    HIGH = 2        # Time-sensitive verification
    NORMAL = 3      # Standard operations  
    LOW = 4         # Background tasks


@dataclass
class AgentMessage:
    """
    Standard message format for inter-agent communication.
    
    All communication between agents uses this structured format
    to ensure consistency and enable message routing/filtering.
    """
    
    # Message identity
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_type: MessageType = MessageType.VERIFICATION_REQUEST
    priority: MessagePriority = MessagePriority.NORMAL
    
    # Routing information
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None = broadcast
    conversation_id: Optional[str] = None  # For threaded conversations
    
    # Message content
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timing and lifecycle
    timestamp: datetime = field(default_factory=datetime.now)
    ttl_seconds: int = 300  # 5 minutes default TTL
    reply_expected: bool = False
    
    def is_expired(self) -> bool:
        """Check if message has exceeded its TTL."""
        return (datetime.now() - self.timestamp).total_seconds() > self.ttl_seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "priority": self.priority.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "conversation_id": self.conversation_id,
            "payload": self.payload,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "ttl_seconds": self.ttl_seconds,
            "reply_expected": self.reply_expected
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary."""
        return cls(
            message_id=data["message_id"],
            message_type=MessageType(data["message_type"]),
            priority=MessagePriority(data["priority"]),
            sender_id=data["sender_id"],
            recipient_id=data.get("recipient_id"),
            conversation_id=data.get("conversation_id"),
            payload=data["payload"],
            metadata=data["metadata"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            ttl_seconds=data["ttl_seconds"],
            reply_expected=data["reply_expected"]
        )


class MessageBus:
    """
    Central message bus for agent communication.
    
    Handles message routing, delivery, and lifecycle management.
    Supports both direct messaging and publish/subscribe patterns.
    """
    
    def __init__(self):
        """Initialize the message bus."""
        self.subscribers: Dict[str, Set[Callable]] = {}  # topic -> handlers
        self.direct_handlers: Dict[str, Callable] = {}  # agent_id -> handler
        self.message_history: List[AgentMessage] = []
        self.delivery_stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "messages_expired": 0,
            "delivery_failures": 0
        }
    
    def register_agent(self, agent_id: str, handler: Callable[[AgentMessage], None]) -> None:
        """
        Register an agent for direct messaging.
        
        Args:
            agent_id: Unique identifier for the agent
            handler: Async function to handle incoming messages
        """
        self.direct_handlers[agent_id] = handler
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent from the message bus."""
        if agent_id in self.direct_handlers:
            del self.direct_handlers[agent_id]
    
    def subscribe(self, topic: str, handler: Callable[[AgentMessage], None]) -> None:
        """
        Subscribe to messages of a specific type or topic.
        
        Args:
            topic: Message type or custom topic to subscribe to
            handler: Function to handle messages for this topic
        """
        if topic not in self.subscribers:
            self.subscribers[topic] = set()
        self.subscribers[topic].add(handler)
    
    def unsubscribe(self, topic: str, handler: Callable[[AgentMessage], None]) -> None:
        """Unsubscribe from a topic."""
        if topic in self.subscribers:
            self.subscribers[topic].discard(handler)
            if not self.subscribers[topic]:
                del self.subscribers[topic]
    
    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send a message through the bus.
        
        Args:
            message: The message to send
            
        Returns:
            True if message was delivered successfully
        """
        self.delivery_stats["messages_sent"] += 1
        
        # Check if message is expired
        if message.is_expired():
            self.delivery_stats["messages_expired"] += 1
            return False
        
        # Store in history
        self.message_history.append(message)
        
        # Keep only last 1000 messages
        if len(self.message_history) > 1000:
            self.message_history = self.message_history[-1000:]
        
        try:
            delivered = False
            
            # Direct delivery to specific recipient
            if message.recipient_id and message.recipient_id in self.direct_handlers:
                handler = self.direct_handlers[message.recipient_id]
                await self._deliver_message(handler, message)
                delivered = True
            
            # Broadcast to topic subscribers
            topic = message.message_type.value
            if topic in self.subscribers:
                for handler in self.subscribers[topic]:
                    await self._deliver_message(handler, message)
                    delivered = True
            
            # Broadcast to all if no specific recipient and no topic subscribers
            if not message.recipient_id and topic not in self.subscribers:
                for handler in self.direct_handlers.values():
                    await self._deliver_message(handler, message)
                    delivered = True
            
            if delivered:
                self.delivery_stats["messages_delivered"] += 1
            
            return delivered
            
        except Exception as e:
            self.delivery_stats["delivery_failures"] += 1
            print(f"Message delivery failed: {e}")
            return False
    
    async def _deliver_message(self, handler: Callable, message: AgentMessage) -> None:
        """Deliver message to a specific handler."""
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(message)
            else:
                handler(message)
        except Exception as e:
            print(f"Handler error for message {message.message_id}: {e}")
    
    def get_conversation_history(self, conversation_id: str) -> List[AgentMessage]:
        """Get all messages in a conversation."""
        return [
            msg for msg in self.message_history 
            if msg.conversation_id == conversation_id
        ]
    
    def get_agent_messages(self, agent_id: str, limit: int = 100) -> List[AgentMessage]:
        """Get recent messages sent by or to a specific agent."""
        agent_messages = [
            msg for msg in self.message_history
            if msg.sender_id == agent_id or msg.recipient_id == agent_id
        ]
        return agent_messages[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        return {
            **self.delivery_stats,
            "active_agents": len(self.direct_handlers),
            "active_subscriptions": len(self.subscribers),
            "message_history_size": len(self.message_history),
            "avg_messages_per_agent": (
                self.delivery_stats["messages_sent"] / len(self.direct_handlers) 
                if self.direct_handlers else 0
            )
        }
    
    def cleanup_expired_messages(self) -> int:
        """Remove expired messages from history."""
        initial_count = len(self.message_history)
        self.message_history = [
            msg for msg in self.message_history if not msg.is_expired()
        ]
        removed = initial_count - len(self.message_history)
        self.delivery_stats["messages_expired"] += removed
        return removed


# Global message bus instance
message_bus = MessageBus()


# Convenience functions for common message types

def create_verification_request(
    sender_id: str,
    claim: str,
    recipient_id: Optional[str] = None,
    priority: MessagePriority = MessagePriority.NORMAL
) -> AgentMessage:
    """Create a verification request message."""
    return AgentMessage(
        message_type=MessageType.VERIFICATION_REQUEST,
        sender_id=sender_id,
        recipient_id=recipient_id,
        priority=priority,
        payload={
            "claim": claim,
            "requested_at": datetime.now().isoformat()
        },
        reply_expected=True
    )


def create_verification_result(
    sender_id: str,
    result: VerificationResult,
    conversation_id: Optional[str] = None,
    recipient_id: Optional[str] = None
) -> AgentMessage:
    """Create a verification result message."""
    return AgentMessage(
        message_type=MessageType.VERIFICATION_RESULT,
        sender_id=sender_id,
        recipient_id=recipient_id,
        conversation_id=conversation_id,
        payload={
            "verification_result": result.model_dump(),
            "completed_at": datetime.now().isoformat()
        }
    )


def create_evidence_share(
    sender_id: str,
    evidence: List[Dict[str, Any]],
    claim: str,
    recipient_id: Optional[str] = None
) -> AgentMessage:
    """Create an evidence sharing message."""
    return AgentMessage(
        message_type=MessageType.EVIDENCE_SHARE,
        sender_id=sender_id,
        recipient_id=recipient_id,
        payload={
            "claim": claim,
            "evidence": evidence,
            "shared_at": datetime.now().isoformat()
        }
    )


def create_help_request(
    sender_id: str,
    help_type: str,
    details: Dict[str, Any],
    recipient_id: Optional[str] = None
) -> AgentMessage:
    """Create a help request message."""
    return AgentMessage(
        message_type=MessageType.HELP_REQUEST,
        sender_id=sender_id,
        recipient_id=recipient_id,
        priority=MessagePriority.HIGH,
        payload={
            "help_type": help_type,
            "details": details,
            "requested_at": datetime.now().isoformat()
        },
        reply_expected=True
    )