"""
Adversarial Debate Framework

Implements prosecutor/defender/moderator agents for adversarial verification.
This module provides the core infrastructure for debate-based consensus.
"""

from src.consensus.adversarial.prosecutor_agent import ProsecutorAgent
from src.consensus.adversarial.defender_agent import DefenderAgent
from src.consensus.adversarial.moderator_agent import ModeratorAgent
from src.consensus.adversarial.debate_engine import DebateEngine, DebateResult, DebateRound
from src.consensus.adversarial.challenge_system import Challenge, ChallengeType, ChallengeResponse

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