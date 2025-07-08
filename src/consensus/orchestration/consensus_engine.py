"""
Consensus Engine for Multi-Agent Verification

Implements various consensus mechanisms to aggregate verification results
from multiple agents into a single, reliable verdict.
"""

import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum

from agents.verification_result import VerificationResult


class ConsensusMethod(Enum):
    """Available consensus methods."""
    SIMPLE_MAJORITY = "simple_majority"
    WEIGHTED_VOTING = "weighted_voting" 
    CONFIDENCE_WEIGHTED = "confidence_weighted"
    REPUTATION_WEIGHTED = "reputation_weighted"
    BYZANTINE_FAULT_TOLERANT = "byzantine_fault_tolerant"


class VerdictAgreement(Enum):
    """Levels of agreement between agents."""
    UNANIMOUS = "unanimous"        # All agents agree
    STRONG_MAJORITY = "strong_majority"  # >75% agree
    SIMPLE_MAJORITY = "simple_majority"  # >50% agree
    NO_CONSENSUS = "no_consensus"  # No clear majority
    STRONG_DISAGREEMENT = "strong_disagreement"  # Agents strongly divided


@dataclass
class VotingResult:
    """Result of a consensus voting process."""
    
    final_verdict: str
    final_confidence: float
    consensus_method: ConsensusMethod
    agreement_level: VerdictAgreement
    
    # Voting details
    verdict_distribution: Dict[str, int] = field(default_factory=dict)
    confidence_distribution: List[float] = field(default_factory=list)
    agent_votes: Dict[str, Tuple[str, float]] = field(default_factory=dict)
    
    # Metadata
    total_voters: int = 0
    winning_margin: float = 0.0
    disagreement_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class ConsensusEngine:
    """
    Engine for building consensus from multiple verification results.
    
    Implements various voting and aggregation mechanisms to combine
    results from multiple agents into a single consensus verdict.
    """
    
    def __init__(self):
        """Initialize the consensus engine."""
        self.default_method = ConsensusMethod.CONFIDENCE_WEIGHTED
        self.min_confidence_threshold = 0.3
        self.unanimous_threshold = 1.0
        self.strong_majority_threshold = 0.75
        self.simple_majority_threshold = 0.5
    
    def build_consensus(
        self,
        results: List[VerificationResult],
        method: Optional[ConsensusMethod] = None,
        agent_reputations: Optional[Dict[str, float]] = None
    ) -> VotingResult:
        """
        Build consensus from multiple verification results.
        
        Args:
            results: List of verification results from different agents
            method: Consensus method to use (defaults to confidence weighted)
            agent_reputations: Optional reputation scores for agents
            
        Returns:
            VotingResult with consensus verdict and metadata
        """
        if not results:
            raise ValueError("Cannot build consensus with no results")
        
        consensus_method = method or self.default_method
        
        # Extract votes and confidences
        votes = [(r.verdict, r.confidence, r.agent_id) for r in results]
        
        # Apply the selected consensus method
        if consensus_method == ConsensusMethod.SIMPLE_MAJORITY:
            return self._simple_majority_vote(votes)
        elif consensus_method == ConsensusMethod.CONFIDENCE_WEIGHTED:
            return self._confidence_weighted_vote(votes)
        elif consensus_method == ConsensusMethod.WEIGHTED_VOTING:
            return self._weighted_vote(votes, agent_reputations or {})
        else:
            # Default to confidence weighted
            return self._confidence_weighted_vote(votes)
    
    def _simple_majority_vote(self, votes: List[Tuple[str, float, str]]) -> VotingResult:
        """Simple majority voting - each agent gets one vote."""
        verdict_counts = {}
        confidence_sum = {}
        agent_votes = {}
        
        for verdict, confidence, agent_id in votes:
            verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
            confidence_sum[verdict] = confidence_sum.get(verdict, 0) + confidence
            agent_votes[agent_id] = (verdict, confidence)
        
        # Find winning verdict
        total_votes = len(votes)
        winning_verdict = max(verdict_counts.keys(), key=lambda v: verdict_counts[v])
        winning_count = verdict_counts[winning_verdict]
        
        # Calculate final confidence (average of winning voters)
        final_confidence = confidence_sum[winning_verdict] / winning_count
        
        # Determine agreement level
        agreement_ratio = winning_count / total_votes
        agreement_level = self._calculate_agreement_level(agreement_ratio)
        
        return VotingResult(
            final_verdict=winning_verdict,
            final_confidence=final_confidence,
            consensus_method=ConsensusMethod.SIMPLE_MAJORITY,
            agreement_level=agreement_level,
            verdict_distribution=verdict_counts,
            confidence_distribution=[conf for _, conf, _ in votes],
            agent_votes=agent_votes,
            total_voters=total_votes,
            winning_margin=agreement_ratio,
            disagreement_score=1.0 - agreement_ratio
        )
    
    def _confidence_weighted_vote(self, votes: List[Tuple[str, float, str]]) -> VotingResult:
        """Confidence-weighted voting - higher confidence votes count more."""
        verdict_weights = {}
        confidence_weighted_sum = {}
        total_weight = 0
        agent_votes = {}
        
        for verdict, confidence, agent_id in votes:
            # Use confidence as weight
            weight = max(confidence, self.min_confidence_threshold)
            
            verdict_weights[verdict] = verdict_weights.get(verdict, 0) + weight
            confidence_weighted_sum[verdict] = confidence_weighted_sum.get(verdict, 0) + (confidence * weight)
            total_weight += weight
            agent_votes[agent_id] = (verdict, confidence)
        
        # Find winning verdict based on weighted votes
        winning_verdict = max(verdict_weights.keys(), key=lambda v: verdict_weights[v])
        winning_weight = verdict_weights[winning_verdict]
        
        # Calculate final confidence (weighted average)
        final_confidence = confidence_weighted_sum[winning_verdict] / winning_weight
        
        # Agreement level based on weight ratio
        agreement_ratio = winning_weight / total_weight
        agreement_level = self._calculate_agreement_level(agreement_ratio)
        
        # Convert weights to counts for distribution
        verdict_counts = {v: int(w * 10) for v, w in verdict_weights.items()}  # Scale for display
        
        return VotingResult(
            final_verdict=winning_verdict,
            final_confidence=final_confidence,
            consensus_method=ConsensusMethod.CONFIDENCE_WEIGHTED,
            agreement_level=agreement_level,
            verdict_distribution=verdict_counts,
            confidence_distribution=[conf for _, conf, _ in votes],
            agent_votes=agent_votes,
            total_voters=len(votes),
            winning_margin=agreement_ratio,
            disagreement_score=1.0 - agreement_ratio
        )
    
    def _weighted_vote(
        self, 
        votes: List[Tuple[str, float, str]], 
        agent_reputations: Dict[str, float]
    ) -> VotingResult:
        """Reputation-weighted voting - agent reputation affects vote weight."""
        verdict_weights = {}
        confidence_weighted_sum = {}
        total_weight = 0
        agent_votes = {}
        
        for verdict, confidence, agent_id in votes:
            # Combine confidence and reputation for weight
            reputation = agent_reputations.get(agent_id, 0.5)  # Default neutral reputation
            weight = confidence * reputation
            
            verdict_weights[verdict] = verdict_weights.get(verdict, 0) + weight
            confidence_weighted_sum[verdict] = confidence_weighted_sum.get(verdict, 0) + (confidence * weight)
            total_weight += weight
            agent_votes[agent_id] = (verdict, confidence)
        
        # Find winning verdict
        winning_verdict = max(verdict_weights.keys(), key=lambda v: verdict_weights[v])
        winning_weight = verdict_weights[winning_verdict]
        
        # Calculate final confidence
        final_confidence = confidence_weighted_sum[winning_verdict] / winning_weight
        
        # Agreement level
        agreement_ratio = winning_weight / total_weight
        agreement_level = self._calculate_agreement_level(agreement_ratio)
        
        # Convert weights to counts
        verdict_counts = {v: int(w * 10) for v, w in verdict_weights.items()}
        
        return VotingResult(
            final_verdict=winning_verdict,
            final_confidence=final_confidence,
            consensus_method=ConsensusMethod.WEIGHTED_VOTING,
            agreement_level=agreement_level,
            verdict_distribution=verdict_counts,
            confidence_distribution=[conf for _, conf, _ in votes],
            agent_votes=agent_votes,
            total_voters=len(votes),
            winning_margin=agreement_ratio,
            disagreement_score=1.0 - agreement_ratio
        )
    
    def _calculate_agreement_level(self, agreement_ratio: float) -> VerdictAgreement:
        """Calculate agreement level based on ratio."""
        if agreement_ratio >= self.unanimous_threshold:
            return VerdictAgreement.UNANIMOUS
        elif agreement_ratio >= self.strong_majority_threshold:
            return VerdictAgreement.STRONG_MAJORITY
        elif agreement_ratio >= self.simple_majority_threshold:
            return VerdictAgreement.SIMPLE_MAJORITY
        elif agreement_ratio < 0.3:
            return VerdictAgreement.STRONG_DISAGREEMENT
        else:
            return VerdictAgreement.NO_CONSENSUS
    
    def detect_disagreement(self, results: List[VerificationResult]) -> Dict[str, Any]:
        """
        Detect and analyze disagreement patterns between agents.
        
        Returns analysis of where and why agents disagree.
        """
        if len(results) < 2:
            return {"disagreement_detected": False}
        
        verdicts = [r.verdict for r in results]
        confidences = [r.confidence for r in results]
        
        # Check verdict disagreement
        unique_verdicts = len(set(verdicts))
        verdict_disagreement = unique_verdicts > 1
        
        # Check confidence variance
        confidence_variance = statistics.variance(confidences) if len(confidences) > 1 else 0
        high_confidence_variance = confidence_variance > 0.1
        
        # Identify conflicting pairs
        conflicts = []
        for i, result1 in enumerate(results):
            for j, result2 in enumerate(results[i+1:], i+1):
                if result1.verdict != result2.verdict:
                    conflicts.append({
                        "agent1": result1.agent_id,
                        "agent2": result2.agent_id,
                        "verdict1": result1.verdict,
                        "verdict2": result2.verdict,
                        "confidence1": result1.confidence,
                        "confidence2": result2.confidence
                    })
        
        return {
            "disagreement_detected": verdict_disagreement or high_confidence_variance,
            "verdict_disagreement": verdict_disagreement,
            "unique_verdicts": unique_verdicts,
            "confidence_variance": confidence_variance,
            "high_confidence_variance": high_confidence_variance,
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
            "agreement_ratio": verdicts.count(max(set(verdicts), key=verdicts.count)) / len(verdicts)
        }