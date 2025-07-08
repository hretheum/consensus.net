"""
Specialized Agents for Multi-Agent Consensus System

Contains domain-specific agents that provide specialized verification
capabilities for different types of claims and evidence sources.
"""

from .specialized_agents import SpecializedAgent, ScienceAgent, NewsAgent, TechAgent

__all__ = [
    "SpecializedAgent",
    "ScienceAgent", 
    "NewsAgent",
    "TechAgent"
]