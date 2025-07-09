"""
Orchestration Module for Multi-Agent System

Manages coordination, task distribution, and result aggregation
across multiple specialized verification agents.
"""

from src.consensus.orchestration.agent_pool import AgentPoolManager
from src.consensus.orchestration.task_decomposition import TaskDecomposer, VerificationTask
from src.consensus.orchestration.consensus_engine import ConsensusEngine, VotingResult

__all__ = [
    "AgentPoolManager",
    "TaskDecomposer",
    "VerificationTask",
    "ConsensusEngine",
    "VotingResult"
]