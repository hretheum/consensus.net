"""
Orchestration Module for Multi-Agent System

Manages coordination, task distribution, and result aggregation
across multiple specialized verification agents.
"""

from .agent_pool import AgentPoolManager
from .task_decomposition import TaskDecomposer, VerificationTask
from .consensus_engine import ConsensusEngine, VotingResult

__all__ = [
    "AgentPoolManager",
    "TaskDecomposer",
    "VerificationTask",
    "ConsensusEngine",
    "VotingResult"
]