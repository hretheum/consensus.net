"""
Adversarial Debate Framework

Implements prosecutor/defender/moderator agents for adversarial verification.
This module provides the core infrastructure for debate-based consensus.
"""

from .prosecutor_agent import ProsecutorAgent
from .defender_agent import DefenderAgent  
from .moderator_agent import ModeratorAgent
from .debate_engine import DebateEngine, DebateResult, DebateRound
from .challenge_system import Challenge, ChallengeType, ChallengeResponse

__all__ = [
    "ProsecutorAgent",
    "DefenderAgent", 
    "ModeratorAgent",
    "DebateEngine",
    "DebateResult",
    "DebateRound",
    "Challenge",
    "ChallengeType", 
    "ChallengeResponse"
]