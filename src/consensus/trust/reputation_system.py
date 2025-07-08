"""
Reputation System for Trust Network

Tracks and manages agent reputation based on verification performance,
accuracy, reliability, and other behavioral factors.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import statistics

from ...agents.verification_result import VerificationResult


class ReputationEventType(Enum):
    """Types of events that affect reputation."""
    ACCURATE_VERIFICATION = "accurate_verification"
    INACCURATE_VERIFICATION = "inaccurate_verification"
    CHALLENGE_RAISED = "challenge_raised"
    CHALLENGE_REFUTED = "challenge_refuted"
    CONSENSUS_CONTRIBUTION = "consensus_contribution"
    RELIABILITY_BONUS = "reliability_bonus"
    BIAS_PENALTY = "bias_penalty"
    INNOVATION_BONUS = "innovation_bonus"
    COLLABORATION_BONUS = "collaboration_bonus"


@dataclass
class ReputationEvent:
    """A single event affecting agent reputation."""
    
    event_id: str = field(default_factory=lambda: f"rep_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    agent_id: str = ""
    event_type: ReputationEventType = ReputationEventType.ACCURATE_VERIFICATION
    
    # Event details
    impact: float = 0.0           # Positive or negative impact on reputation
    confidence: float = 1.0       # How confident we are in this assessment
    context: str = ""             # Description of the event
    
    # Related data
    verification_result: Optional[VerificationResult] = None
    related_agents: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Timing
    timestamp: datetime = field(default_factory=datetime.now)
    decay_start: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=30))
    
    def get_current_impact(self) -> float:
        """Get current impact considering time decay."""
        if datetime.now() < self.decay_start:
            return self.impact
        
        # Apply exponential decay after decay_start
        days_since_decay = (datetime.now() - self.decay_start).days
        decay_factor = 0.95 ** days_since_decay  # 5% decay per day
        
        return self.impact * decay_factor


@dataclass
class ReputationScore:
    """Comprehensive reputation score for an agent."""
    
    agent_id: str = ""
    
    # Core reputation metrics
    overall_score: float = 0.5          # Overall reputation (0-1)
    accuracy_score: float = 0.5         # Accuracy in verifications (0-1)
    reliability_score: float = 0.5      # Consistency and reliability (0-1)
    expertise_score: float = 0.5        # Domain expertise level (0-1)
    collaboration_score: float = 0.5    # Quality of collaboration (0-1)
    
    # Detailed metrics
    total_verifications: int = 0
    accurate_verifications: int = 0
    challenges_raised: int = 0
    successful_challenges: int = 0
    consensus_contributions: int = 0
    
    # Performance tracking
    recent_accuracy: float = 0.5        # Accuracy in last 30 days
    consistency_score: float = 0.5      # Consistency over time
    improvement_trend: float = 0.0      # Positive if improving, negative if declining
    
    # Domain-specific reputation
    domain_expertise: Dict[str, float] = field(default_factory=dict)
    
    # Temporal information
    last_updated: datetime = field(default_factory=datetime.now)
    reputation_age_days: int = 0        # How long reputation has been tracked
    
    def get_weighted_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Get weighted reputation score."""
        if weights is None:
            weights = {
                "overall": 0.3,
                "accuracy": 0.25,
                "reliability": 0.2,
                "expertise": 0.15,
                "collaboration": 0.1
            }
        
        return (
            self.overall_score * weights.get("overall", 0.3) +
            self.accuracy_score * weights.get("accuracy", 0.25) +
            self.reliability_score * weights.get("reliability", 0.2) +
            self.expertise_score * weights.get("expertise", 0.15) +
            self.collaboration_score * weights.get("collaboration", 0.1)
        )


class ReputationSystem:
    """
    Comprehensive reputation tracking and management system.
    
    Tracks agent performance, calculates reputation scores, and provides
    trust-based weighting for consensus mechanisms.
    """
    
    def __init__(self):
        """Initialize the reputation system."""
        
        # Reputation storage
        self.agent_reputations: Dict[str, ReputationScore] = {}
        self.reputation_events: List[ReputationEvent] = []
        self.agent_events: Dict[str, List[ReputationEvent]] = {}
        
        # Configuration
        self.accuracy_weight = 0.4
        self.reliability_weight = 0.3
        self.consistency_weight = 0.2
        self.collaboration_weight = 0.1
        
        # Thresholds
        self.min_verifications_for_stable_reputation = 10
        self.recent_period_days = 30
        self.decay_start_days = 30
        
        # System statistics
        self.stats = {
            "total_agents_tracked": 0,
            "total_events_recorded": 0,
            "average_reputation": 0.5,
            "reputation_updates": 0
        }
    
    def get_reputation(self, agent_id: str) -> ReputationScore:
        """Get current reputation score for an agent."""
        if agent_id not in self.agent_reputations:
            self.agent_reputations[agent_id] = ReputationScore(agent_id=agent_id)
            self.stats["total_agents_tracked"] += 1
        
        return self.agent_reputations[agent_id]
    
    def record_verification_result(
        self, 
        agent_id: str, 
        result: VerificationResult, 
        actual_outcome: Optional[str] = None,
        accuracy_assessment: Optional[float] = None
    ) -> None:
        """
        Record a verification result and update reputation.
        
        Args:
            agent_id: The agent who performed the verification
            result: The verification result
            actual_outcome: The actual correct outcome (for accuracy assessment)
            accuracy_assessment: Direct accuracy score (0-1) if available
        """
        
        # Determine accuracy
        if accuracy_assessment is not None:
            accuracy = accuracy_assessment
            is_accurate = accuracy >= 0.7
        elif actual_outcome is not None:
            is_accurate = result.verdict == actual_outcome
            accuracy = 1.0 if is_accurate else 0.0
        else:
            # Estimate accuracy based on confidence and other factors
            accuracy = self._estimate_verification_accuracy(result)
            is_accurate = accuracy >= 0.7
        
        # Create reputation event
        event_type = ReputationEventType.ACCURATE_VERIFICATION if is_accurate else ReputationEventType.INACCURATE_VERIFICATION
        impact = accuracy * 0.1 if is_accurate else -((1.0 - accuracy) * 0.1)
        
        event = ReputationEvent(
            agent_id=agent_id,
            event_type=event_type,
            impact=impact,
            confidence=result.confidence,
            context=f"Verification: {result.claim[:50]}... (accuracy: {accuracy:.2f})",
            verification_result=result,
            metadata={
                "accuracy": accuracy,
                "verdict": result.verdict,
                "confidence": result.confidence
            }
        )
        
        self._record_event(event)
        self._update_reputation(agent_id)
    
    def record_challenge_outcome(
        self, 
        challenger_id: str, 
        challenge_successful: bool,
        challenge_quality: float = 0.5,
        context: str = ""
    ) -> None:
        """Record the outcome of a challenge raised by an agent."""
        
        if challenge_successful:
            event = ReputationEvent(
                agent_id=challenger_id,
                event_type=ReputationEventType.CHALLENGE_RAISED,
                impact=0.05 * challenge_quality,  # Positive impact for successful challenges
                confidence=0.9,
                context=f"Successful challenge: {context}",
                metadata={"challenge_quality": challenge_quality}
            )
        else:
            event = ReputationEvent(
                agent_id=challenger_id,
                event_type=ReputationEventType.CHALLENGE_REFUTED,
                impact=-0.02,  # Small negative impact for unsuccessful challenges
                confidence=0.8,
                context=f"Unsuccessful challenge: {context}",
                metadata={"challenge_quality": challenge_quality}
            )
        
        self._record_event(event)
        self._update_reputation(challenger_id)
    
    def record_consensus_contribution(
        self, 
        agent_id: str, 
        contribution_quality: float,
        consensus_accuracy: float = 0.5,
        context: str = ""
    ) -> None:
        """Record an agent's contribution to consensus."""
        
        impact = contribution_quality * consensus_accuracy * 0.03
        
        event = ReputationEvent(
            agent_id=agent_id,
            event_type=ReputationEventType.CONSENSUS_CONTRIBUTION,
            impact=impact,
            confidence=0.8,
            context=f"Consensus contribution: {context}",
            metadata={
                "contribution_quality": contribution_quality,
                "consensus_accuracy": consensus_accuracy
            }
        )
        
        self._record_event(event)
        self._update_reputation(agent_id)
    
    def record_collaboration_event(
        self, 
        agent_id: str, 
        collaboration_type: str,
        quality_score: float,
        context: str = ""
    ) -> None:
        """Record a collaboration event (helping other agents, etc.)."""
        
        impact = quality_score * 0.02  # Small positive impact for collaboration
        
        event = ReputationEvent(
            agent_id=agent_id,
            event_type=ReputationEventType.COLLABORATION_BONUS,
            impact=impact,
            confidence=0.7,
            context=f"Collaboration ({collaboration_type}): {context}",
            metadata={
                "collaboration_type": collaboration_type,
                "quality_score": quality_score
            }
        )
        
        self._record_event(event)
        self._update_reputation(agent_id)
    
    def get_agent_rankings(self, limit: int = 10) -> List[Tuple[str, ReputationScore]]:
        """Get top agents by reputation score."""
        
        ranked_agents = sorted(
            self.agent_reputations.items(),
            key=lambda x: x[1].overall_score,
            reverse=True
        )
        
        return ranked_agents[:limit]
    
    def get_domain_experts(self, domain: str, limit: int = 5) -> List[Tuple[str, float]]:
        """Get top experts in a specific domain."""
        
        domain_experts = []
        
        for agent_id, reputation in self.agent_reputations.items():
            if domain in reputation.domain_expertise:
                expertise_score = reputation.domain_expertise[domain]
                overall_weight = reputation.overall_score * 0.3  # Weight by overall reputation
                combined_score = expertise_score * 0.7 + overall_weight
                domain_experts.append((agent_id, combined_score))
        
        domain_experts.sort(key=lambda x: x[1], reverse=True)
        return domain_experts[:limit]
    
    def get_trust_weights(self, agent_ids: List[str]) -> Dict[str, float]:
        """Get trust-based weights for a set of agents."""
        
        weights = {}
        total_reputation = 0.0
        
        # Calculate raw reputation scores
        for agent_id in agent_ids:
            reputation = self.get_reputation(agent_id)
            weights[agent_id] = reputation.overall_score
            total_reputation += reputation.overall_score
        
        # Normalize to sum to 1.0
        if total_reputation > 0:
            for agent_id in weights:
                weights[agent_id] /= total_reputation
        else:
            # Equal weights if no reputation data
            equal_weight = 1.0 / len(agent_ids)
            for agent_id in agent_ids:
                weights[agent_id] = equal_weight
        
        return weights
    
    def _record_event(self, event: ReputationEvent) -> None:
        """Record a reputation event."""
        
        self.reputation_events.append(event)
        
        if event.agent_id not in self.agent_events:
            self.agent_events[event.agent_id] = []
        
        self.agent_events[event.agent_id].append(event)
        self.stats["total_events_recorded"] += 1
    
    def _update_reputation(self, agent_id: str) -> None:
        """Update reputation score for an agent based on recent events."""
        
        reputation = self.get_reputation(agent_id)
        agent_events = self.agent_events.get(agent_id, [])
        
        if not agent_events:
            return
        
        # Calculate accuracy score
        verification_events = [e for e in agent_events 
                             if e.event_type in [ReputationEventType.ACCURATE_VERIFICATION, 
                                               ReputationEventType.INACCURATE_VERIFICATION]]
        
        if verification_events:
            accurate_count = len([e for e in verification_events 
                                if e.event_type == ReputationEventType.ACCURATE_VERIFICATION])
            reputation.total_verifications = len(verification_events)
            reputation.accurate_verifications = accurate_count
            reputation.accuracy_score = accurate_count / len(verification_events)
            
            # Recent accuracy (last 30 days)
            recent_events = [e for e in verification_events 
                           if e.timestamp > datetime.now() - timedelta(days=self.recent_period_days)]
            if recent_events:
                recent_accurate = len([e for e in recent_events 
                                     if e.event_type == ReputationEventType.ACCURATE_VERIFICATION])
                reputation.recent_accuracy = recent_accurate / len(recent_events)
        
        # Calculate reliability score (consistency over time)
        reputation.reliability_score = self._calculate_reliability(agent_events)
        
        # Calculate expertise score
        reputation.expertise_score = self._calculate_expertise(agent_events)
        
        # Calculate collaboration score
        collaboration_events = [e for e in agent_events 
                              if e.event_type == ReputationEventType.COLLABORATION_BONUS]
        reputation.collaboration_score = min(0.5 + len(collaboration_events) * 0.1, 1.0)
        
        # Calculate overall score
        reputation.overall_score = self._calculate_overall_score(reputation)
        
        # Update metadata
        reputation.last_updated = datetime.now()
        reputation.reputation_age_days = (datetime.now() - agent_events[0].timestamp).days if agent_events else 0
        
        self.stats["reputation_updates"] += 1
        
        # Update system averages
        self._update_system_stats()
    
    def _calculate_reliability(self, events: List[ReputationEvent]) -> float:
        """Calculate reliability score based on consistency."""
        
        if len(events) < 3:
            return 0.5  # Neutral for insufficient data
        
        # Look at verification events only
        verification_events = [e for e in events 
                             if e.event_type in [ReputationEventType.ACCURATE_VERIFICATION, 
                                               ReputationEventType.INACCURATE_VERIFICATION]]
        
        if len(verification_events) < 3:
            return 0.5
        
        # Calculate variance in performance over time
        accuracies = []
        for i in range(0, len(verification_events), 5):  # Sample every 5 events
            sample = verification_events[i:i+5]
            if sample:
                sample_accuracy = len([e for e in sample 
                                     if e.event_type == ReputationEventType.ACCURATE_VERIFICATION]) / len(sample)
                accuracies.append(sample_accuracy)
        
        if len(accuracies) < 2:
            return 0.7  # Good reliability for consistent performance
        
        # Lower variance = higher reliability
        variance = statistics.variance(accuracies)
        reliability = max(0.0, 1.0 - (variance * 2))  # Scale variance to 0-1
        
        return reliability
    
    def _calculate_expertise(self, events: List[ReputationEvent]) -> float:
        """Calculate expertise score based on challenge success and accuracy."""
        
        challenge_events = [e for e in events 
                          if e.event_type == ReputationEventType.CHALLENGE_RAISED]
        
        if not challenge_events:
            return 0.5  # Neutral if no challenges raised
        
        # Expertise based on successful challenges and overall accuracy
        base_expertise = 0.5
        challenge_bonus = min(len(challenge_events) * 0.05, 0.3)  # Up to 0.3 bonus
        
        return min(base_expertise + challenge_bonus, 1.0)
    
    def _calculate_overall_score(self, reputation: ReputationScore) -> float:
        """Calculate overall reputation score from component scores."""
        
        return (
            reputation.accuracy_score * self.accuracy_weight +
            reputation.reliability_score * self.reliability_weight +
            reputation.expertise_score * self.consistency_weight +
            reputation.collaboration_score * self.collaboration_weight
        )
    
    def _estimate_verification_accuracy(self, result: VerificationResult) -> float:
        """Estimate accuracy of a verification result when ground truth is unknown."""
        
        # This is a heuristic estimation - in practice you'd have better methods
        base_accuracy = result.confidence
        
        # Adjust based on evidence quality
        if result.sources:
            source_bonus = min(len(result.sources) * 0.05, 0.2)
            base_accuracy += source_bonus
        
        if result.evidence:
            evidence_bonus = min(len(result.evidence) * 0.1, 0.3)
            base_accuracy += evidence_bonus
        
        # Penalize for inconsistencies
        if result.verdict == "TRUE" and result.confidence < 0.6:
            base_accuracy -= 0.2  # Inconsistent verdict/confidence
        
        return max(0.0, min(1.0, base_accuracy))
    
    def _update_system_stats(self) -> None:
        """Update system-wide statistics."""
        
        if self.agent_reputations:
            total_reputation = sum(rep.overall_score for rep in self.agent_reputations.values())
            self.stats["average_reputation"] = total_reputation / len(self.agent_reputations)
    
    def get_reputation_stats(self) -> Dict[str, Any]:
        """Get comprehensive reputation system statistics."""
        
        return {
            **self.stats,
            "agents_with_high_reputation": len([rep for rep in self.agent_reputations.values() 
                                              if rep.overall_score >= 0.8]),
            "agents_with_low_reputation": len([rep for rep in self.agent_reputations.values() 
                                             if rep.overall_score <= 0.3]),
            "total_verification_events": len([e for e in self.reputation_events 
                                            if e.event_type in [ReputationEventType.ACCURATE_VERIFICATION,
                                                              ReputationEventType.INACCURATE_VERIFICATION]]),
            "recent_events": len([e for e in self.reputation_events 
                                if e.timestamp > datetime.now() - timedelta(days=7)])
        }
    
    def cleanup_old_events(self, days_to_keep: int = 90) -> None:
        """Clean up events older than specified days."""
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Remove old events
        self.reputation_events = [e for e in self.reputation_events if e.timestamp > cutoff_date]
        
        # Update agent events
        for agent_id in self.agent_events:
            self.agent_events[agent_id] = [e for e in self.agent_events[agent_id] 
                                         if e.timestamp > cutoff_date]
        
        print(f"Cleaned up reputation events older than {days_to_keep} days")