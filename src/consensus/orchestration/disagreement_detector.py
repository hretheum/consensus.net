"""
Advanced Disagreement Detection for Multi-Agent Systems

Detects and analyzes disagreements between agents to improve consensus
quality and identify potential issues in verification results.
"""

import statistics
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from enum import Enum

from ...agents.verification_result import VerificationResult


class DisagreementType(Enum):
    """Types of disagreements between agents."""
    VERDICT_CONFLICT = "verdict_conflict"           # Different verdicts (TRUE vs FALSE)
    CONFIDENCE_VARIANCE = "confidence_variance"     # High variance in confidence scores
    REASONING_CONFLICT = "reasoning_conflict"       # Contradictory reasoning
    EVIDENCE_CONFLICT = "evidence_conflict"         # Conflicting evidence sources
    SYSTEMATIC_BIAS = "systematic_bias"             # One agent consistently differs


class DisagreementSeverity(Enum):
    """Severity levels of disagreements."""
    LOW = "low"                 # Minor differences, still consensus
    MODERATE = "moderate"       # Noticeable differences, consensus uncertain
    HIGH = "high"              # Strong disagreement, no clear consensus
    CRITICAL = "critical"       # Complete contradiction, investigation needed


@dataclass
class DisagreementAnalysis:
    """Analysis of disagreement between verification results."""
    
    disagreement_types: List[DisagreementType] = field(default_factory=list)
    severity: DisagreementSeverity = DisagreementSeverity.LOW
    
    # Disagreement metrics
    verdict_consensus_ratio: float = 1.0      # Ratio of agents agreeing on verdict
    confidence_variance: float = 0.0          # Variance in confidence scores
    reasoning_similarity: float = 1.0         # Similarity of reasoning approaches
    
    # Specific conflicts
    verdict_conflicts: List[Dict[str, Any]] = field(default_factory=list)
    confidence_outliers: List[str] = field(default_factory=list)
    evidence_contradictions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recommendations
    requires_investigation: bool = False
    recommended_actions: List[str] = field(default_factory=list)
    
    # Metadata
    analyzed_agents: List[str] = field(default_factory=list)
    analysis_timestamp: datetime = field(default_factory=datetime.now)


class DisagreementDetector:
    """
    Advanced disagreement detection system.
    
    Analyzes verification results from multiple agents to detect
    and categorize different types of disagreements.
    """
    
    def __init__(self):
        """Initialize the disagreement detector."""
        self.confidence_variance_threshold = 0.15  # High if variance > 0.15
        self.reasoning_similarity_threshold = 0.3   # Low similarity if < 0.3
        self.consensus_ratio_threshold = 0.7        # Poor consensus if < 0.7
        
        # Track disagreement patterns
        self.disagreement_history: List[DisagreementAnalysis] = []
        self.agent_disagreement_patterns: Dict[str, Dict[str, int]] = {}
    
    def analyze_disagreement(self, results: List[VerificationResult]) -> DisagreementAnalysis:
        """
        Comprehensive disagreement analysis of multiple verification results.
        
        Args:
            results: List of verification results from different agents
            
        Returns:
            DisagreementAnalysis with detailed disagreement information
        """
        if len(results) < 2:
            # No disagreement possible with less than 2 results
            return DisagreementAnalysis(
                analyzed_agents=[r.agent_id for r in results],
                severity=DisagreementSeverity.LOW
            )
        
        analysis = DisagreementAnalysis(
            analyzed_agents=[r.agent_id for r in results]
        )
        
        # Analyze different types of disagreements
        self._analyze_verdict_disagreements(results, analysis)
        self._analyze_confidence_variance(results, analysis)
        self._analyze_reasoning_conflicts(results, analysis)
        self._analyze_evidence_conflicts(results, analysis)
        
        # Determine overall severity
        analysis.severity = self._calculate_severity(analysis)
        
        # Generate recommendations
        analysis.recommended_actions = self._generate_recommendations(analysis)
        analysis.requires_investigation = analysis.severity in [
            DisagreementSeverity.HIGH, 
            DisagreementSeverity.CRITICAL
        ]
        
        # Store for pattern analysis
        self.disagreement_history.append(analysis)
        self._update_disagreement_patterns(results, analysis)
        
        return analysis
    
    def _analyze_verdict_disagreements(self, results: List[VerificationResult], analysis: DisagreementAnalysis) -> None:
        """Analyze disagreements in verdicts."""
        verdicts = [r.verdict for r in results]
        unique_verdicts = set(verdicts)
        
        if len(unique_verdicts) > 1:
            analysis.disagreement_types.append(DisagreementType.VERDICT_CONFLICT)
            
            # Calculate consensus ratio
            most_common_verdict = max(set(verdicts), key=verdicts.count)
            consensus_count = verdicts.count(most_common_verdict)
            analysis.verdict_consensus_ratio = consensus_count / len(verdicts)
            
            # Identify specific conflicts
            for i, result1 in enumerate(results):
                for j, result2 in enumerate(results[i+1:], i+1):
                    if result1.verdict != result2.verdict:
                        conflict = {
                            "agent1": result1.agent_id,
                            "agent2": result2.agent_id,
                            "verdict1": result1.verdict,
                            "verdict2": result2.verdict,
                            "confidence1": result1.confidence,
                            "confidence2": result2.confidence,
                            "confidence_difference": abs(result1.confidence - result2.confidence)
                        }
                        analysis.verdict_conflicts.append(conflict)
        else:
            analysis.verdict_consensus_ratio = 1.0
    
    def _analyze_confidence_variance(self, results: List[VerificationResult], analysis: DisagreementAnalysis) -> None:
        """Analyze variance in confidence scores."""
        confidences = [r.confidence for r in results]
        
        if len(confidences) > 1:
            variance = statistics.variance(confidences)
            analysis.confidence_variance = variance
            
            if variance > self.confidence_variance_threshold:
                analysis.disagreement_types.append(DisagreementType.CONFIDENCE_VARIANCE)
                
                # Identify outliers (agents with confidence > 1.5 std deviations from mean)
                mean_confidence = statistics.mean(confidences)
                std_confidence = statistics.stdev(confidences)
                
                for result in results:
                    deviation = abs(result.confidence - mean_confidence)
                    if deviation > 1.5 * std_confidence:
                        analysis.confidence_outliers.append(result.agent_id)
    
    def _analyze_reasoning_conflicts(self, results: List[VerificationResult], analysis: DisagreementAnalysis) -> None:
        """Analyze conflicts in reasoning approaches."""
        reasoning_texts = [r.reasoning for r in results]
        
        # Simple reasoning similarity analysis
        similarity_scores = []
        for i, reasoning1 in enumerate(reasoning_texts):
            for j, reasoning2 in enumerate(reasoning_texts[i+1:], i+1):
                similarity = self._calculate_text_similarity(reasoning1, reasoning2)
                similarity_scores.append(similarity)
        
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            analysis.reasoning_similarity = avg_similarity
            
            if avg_similarity < self.reasoning_similarity_threshold:
                analysis.disagreement_types.append(DisagreementType.REASONING_CONFLICT)
    
    def _analyze_evidence_conflicts(self, results: List[VerificationResult], analysis: DisagreementAnalysis) -> None:
        """Analyze conflicts in evidence sources and content."""
        all_sources = []
        agent_sources = {}
        
        for result in results:
            sources = set(result.sources)
            agent_sources[result.agent_id] = sources
            all_sources.extend(sources)
        
        # Check for contradictory evidence
        for i, result1 in enumerate(results):
            for j, result2 in enumerate(results[i+1:], i+1):
                if result1.verdict != result2.verdict:
                    # Check if they have conflicting sources
                    shared_sources = agent_sources[result1.agent_id] & agent_sources[result2.agent_id]
                    unique_sources1 = agent_sources[result1.agent_id] - shared_sources
                    unique_sources2 = agent_sources[result2.agent_id] - shared_sources
                    
                    if shared_sources and unique_sources1 and unique_sources2:
                        contradiction = {
                            "agent1": result1.agent_id,
                            "agent2": result2.agent_id,
                            "shared_sources": list(shared_sources),
                            "unique_sources1": list(unique_sources1),
                            "unique_sources2": list(unique_sources2),
                            "verdict1": result1.verdict,
                            "verdict2": result2.verdict
                        }
                        analysis.evidence_contradictions.append(contradiction)
        
        if analysis.evidence_contradictions:
            analysis.disagreement_types.append(DisagreementType.EVIDENCE_CONFLICT)
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity between two reasoning texts."""
        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union) if union else 0.0
    
    def _calculate_severity(self, analysis: DisagreementAnalysis) -> DisagreementSeverity:
        """Calculate overall disagreement severity."""
        severity_score = 0
        
        # Verdict disagreement contributes most to severity
        if DisagreementType.VERDICT_CONFLICT in analysis.disagreement_types:
            if analysis.verdict_consensus_ratio < 0.5:
                severity_score += 3  # Critical
            elif analysis.verdict_consensus_ratio < 0.7:
                severity_score += 2  # High
            else:
                severity_score += 1  # Moderate
        
        # Confidence variance
        if DisagreementType.CONFIDENCE_VARIANCE in analysis.disagreement_types:
            if analysis.confidence_variance > 0.3:
                severity_score += 2
            elif analysis.confidence_variance > 0.2:
                severity_score += 1
        
        # Reasoning conflicts
        if DisagreementType.REASONING_CONFLICT in analysis.disagreement_types:
            if analysis.reasoning_similarity < 0.1:
                severity_score += 2
            elif analysis.reasoning_similarity < 0.2:
                severity_score += 1
        
        # Evidence conflicts
        if DisagreementType.EVIDENCE_CONFLICT in analysis.disagreement_types:
            severity_score += 1
        
        # Map score to severity
        if severity_score >= 5:
            return DisagreementSeverity.CRITICAL
        elif severity_score >= 3:
            return DisagreementSeverity.HIGH
        elif severity_score >= 1:
            return DisagreementSeverity.MODERATE
        else:
            return DisagreementSeverity.LOW
    
    def _generate_recommendations(self, analysis: DisagreementAnalysis) -> List[str]:
        """Generate actionable recommendations based on disagreement analysis."""
        recommendations = []
        
        if DisagreementType.VERDICT_CONFLICT in analysis.disagreement_types:
            if analysis.verdict_consensus_ratio < 0.6:
                recommendations.append("Consider adding more specialized agents for this domain")
                recommendations.append("Review claim complexity and potentially decompose it")
            else:
                recommendations.append("Investigate minority opinion agents for potential bias")
        
        if DisagreementType.CONFIDENCE_VARIANCE in analysis.disagreement_types:
            recommendations.append("Calibrate agent confidence scoring mechanisms")
            if analysis.confidence_outliers:
                recommendations.append(f"Review agents with outlier confidence: {', '.join(analysis.confidence_outliers)}")
        
        if DisagreementType.REASONING_CONFLICT in analysis.disagreement_types:
            recommendations.append("Standardize reasoning frameworks across agents")
            recommendations.append("Implement reasoning validation protocols")
        
        if DisagreementType.EVIDENCE_CONFLICT in analysis.disagreement_types:
            recommendations.append("Cross-validate evidence sources")
            recommendations.append("Implement evidence quality scoring")
        
        if analysis.severity == DisagreementSeverity.CRITICAL:
            recommendations.append("URGENT: Manual review required - critical disagreement detected")
            recommendations.append("Consider flagging this claim for expert human review")
        
        return recommendations
    
    def _update_disagreement_patterns(self, results: List[VerificationResult], analysis: DisagreementAnalysis) -> None:
        """Update disagreement patterns for agent performance tracking."""
        for result in results:
            agent_id = result.agent_id
            if agent_id not in self.agent_disagreement_patterns:
                self.agent_disagreement_patterns[agent_id] = {}
            
            for disagreement_type in analysis.disagreement_types:
                type_key = disagreement_type.value
                self.agent_disagreement_patterns[agent_id][type_key] = (
                    self.agent_disagreement_patterns[agent_id].get(type_key, 0) + 1
                )
    
    def get_agent_disagreement_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get disagreement statistics for a specific agent."""
        if agent_id not in self.agent_disagreement_patterns:
            return {"no_data": True}
        
        patterns = self.agent_disagreement_patterns[agent_id]
        total_disagreements = sum(patterns.values())
        
        return {
            "total_disagreements": total_disagreements,
            "disagreement_types": patterns,
            "most_common_disagreement": max(patterns.keys(), key=lambda k: patterns[k]) if patterns else None,
            "disagreement_rate": total_disagreements / len(self.disagreement_history) if self.disagreement_history else 0
        }
    
    def get_system_disagreement_trends(self) -> Dict[str, Any]:
        """Get overall system disagreement trends."""
        if not self.disagreement_history:
            return {"no_data": True}
        
        recent_analyses = self.disagreement_history[-10:]  # Last 10 analyses
        
        severity_counts = {}
        type_counts = {}
        
        for analysis in recent_analyses:
            severity_counts[analysis.severity.value] = severity_counts.get(analysis.severity.value, 0) + 1
            
            for disagreement_type in analysis.disagreement_types:
                type_counts[disagreement_type.value] = type_counts.get(disagreement_type.value, 0) + 1
        
        avg_consensus_ratio = sum(a.verdict_consensus_ratio for a in recent_analyses) / len(recent_analyses)
        avg_confidence_variance = sum(a.confidence_variance for a in recent_analyses) / len(recent_analyses)
        
        return {
            "total_analyses": len(self.disagreement_history),
            "recent_severity_distribution": severity_counts,
            "recent_disagreement_types": type_counts,
            "avg_consensus_ratio": avg_consensus_ratio,
            "avg_confidence_variance": avg_confidence_variance,
            "critical_disagreements": len([a for a in recent_analyses if a.severity == DisagreementSeverity.CRITICAL]),
            "requires_investigation_count": len([a for a in recent_analyses if a.requires_investigation])
        }