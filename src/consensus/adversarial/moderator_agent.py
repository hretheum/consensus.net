"""
Moderator Agent for Adversarial Verification

The ModeratorAgent oversees adversarial debates between prosecutor and defender,
synthesizes their arguments, and reaches balanced conclusions.
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from ...agents.base_agent import BaseAgent
from ...agents.verification_result import VerificationResult
from ...agents.agent_models import Evidence
from .challenge_system import (
    Challenge, ChallengeType, ChallengeStrength, 
    ChallengeResponse, ChallengeValidator
)


@dataclass
class DebateAnalysis:
    """Analysis of a debate between prosecutor and defender."""
    
    original_result: VerificationResult
    challenges: List[Challenge] = field(default_factory=list)
    responses: List[ChallengeResponse] = field(default_factory=list)
    
    # Analysis metrics
    total_challenges: int = 0
    valid_challenges: int = 0
    addressed_challenges: int = 0
    successful_defenses: int = 0
    successful_prosecutions: int = 0
    
    # Quality scores
    debate_quality_score: float = 0.0
    challenge_quality_score: float = 0.0
    response_quality_score: float = 0.0
    
    # Final assessment
    confidence_adjustment: float = 0.0  # How much to adjust original confidence
    verdict_stability: float = 0.0      # How stable is the original verdict
    requires_further_investigation: bool = False
    
    # Synthesis
    synthesis_summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    remaining_concerns: List[str] = field(default_factory=list)


class ModeratorAgent(BaseAgent):
    """
    Moderator Agent for adversarial verification debates.
    
    Oversees debates between prosecutor and defender, validates arguments,
    and synthesizes conclusions for improved verification results.
    """
    
    def __init__(self, agent_id: str = "moderator_agent"):
        """Initialize the moderator agent."""
        super().__init__(agent_id)
        
        self.challenge_validator = ChallengeValidator()
        
        # Moderator configuration
        self.debate_rounds_limit = 3
        self.synthesis_thoroughness = 0.9
        self.confidence_adjustment_sensitivity = 0.2
        
        # Moderator statistics
        self.stats = {
            "total_debates_moderated": 0,
            "debates_improved_results": 0,
            "debates_unchanged_results": 0,
            "debates_degraded_results": 0,
            "average_debate_quality": 0.0,
            "average_confidence_adjustment": 0.0,
            "verdicts_changed": 0
        }
    
    def verify(self, claim: str) -> VerificationResult:
        """
        Moderator agents don't verify claims directly.
        They moderate debates about verification results.
        """
        return VerificationResult(
            claim=claim,
            verdict="ERROR",
            confidence=0.0,
            reasoning="Moderator agents moderate debates, they don't verify claims directly",
            sources=[],
            evidence=[],
            metadata={"agent_role": "moderator"},
            agent_id=self.agent_id
        )
    
    def moderate_debate(
        self,
        original_result: VerificationResult,
        challenges: List[Challenge],
        responses: List[ChallengeResponse]
    ) -> DebateAnalysis:
        """
        Moderate a debate and provide synthesis.
        
        Args:
            original_result: The original verification result
            challenges: Challenges raised by prosecutor
            responses: Responses provided by defender
            
        Returns:
            Analysis and synthesis of the debate
        """
        print(f"⚖️ Moderator analyzing debate for: {original_result.claim[:50]}...")
        
        # Create debate analysis
        analysis = DebateAnalysis(
            original_result=original_result,
            challenges=challenges,
            responses=responses
        )
        
        # Validate challenges
        valid_challenges = self._validate_challenges(challenges)
        analysis.valid_challenges = len(valid_challenges)
        analysis.total_challenges = len(challenges)
        
        # Assess response quality
        response_quality = self._assess_response_quality(responses, valid_challenges)
        analysis.addressed_challenges = len([r for r in responses if r.adequacy_score >= 0.6])
        
        # Calculate debate metrics
        analysis.successful_defenses = len([r for r in responses if r.response_type == "defense" and r.adequacy_score >= 0.7])
        analysis.successful_prosecutions = len([c for c in valid_challenges if not any(r.challenge_id == c.challenge_id and r.adequacy_score >= 0.7 for r in responses)])
        
        # Calculate quality scores
        analysis.challenge_quality_score = self._calculate_challenge_quality(valid_challenges)
        analysis.response_quality_score = response_quality
        analysis.debate_quality_score = (analysis.challenge_quality_score + analysis.response_quality_score) / 2
        
        # Perform synthesis
        synthesis = self._synthesize_debate(original_result, valid_challenges, responses)
        analysis.confidence_adjustment = synthesis["confidence_adjustment"]
        analysis.verdict_stability = synthesis["verdict_stability"]
        analysis.requires_further_investigation = synthesis["requires_investigation"]
        analysis.synthesis_summary = synthesis["summary"]
        analysis.key_findings = synthesis["key_findings"]
        analysis.remaining_concerns = synthesis["remaining_concerns"]
        
        # Update statistics
        self._update_stats(analysis)
        
        print(f"⚖️ Debate analysis complete: quality={analysis.debate_quality_score:.2f}, adjustment={analysis.confidence_adjustment:.2f}")
        
        return analysis
    
    def synthesize_improved_result(
        self,
        original_result: VerificationResult,
        debate_analysis: DebateAnalysis
    ) -> VerificationResult:
        """
        Create an improved verification result based on debate analysis.
        
        Args:
            original_result: Original verification result
            debate_analysis: Analysis of the adversarial debate
            
        Returns:
            Improved verification result
        """
        # Calculate adjusted confidence
        adjusted_confidence = max(0.0, min(1.0, 
            original_result.confidence + debate_analysis.confidence_adjustment
        ))
        
        # Determine if verdict should change
        new_verdict = original_result.verdict
        if debate_analysis.verdict_stability < 0.5:
            # Verdict is unstable, consider changing to UNCERTAIN
            if original_result.verdict in ["TRUE", "FALSE"]:
                new_verdict = "UNCERTAIN"
                adjusted_confidence = min(adjusted_confidence, 0.6)
        
        # Enhanced reasoning incorporating debate insights
        enhanced_reasoning = self._create_enhanced_reasoning(
            original_result, debate_analysis
        )
        
        # Combine evidence and sources
        enhanced_evidence = list(original_result.evidence)
        enhanced_sources = list(original_result.sources)
        
        # Add any new evidence from responses
        for response in debate_analysis.responses:
            enhanced_evidence.extend(response.counter_evidence)
        
        # Create enhanced metadata
        enhanced_metadata = {
            **original_result.metadata,
            "adversarial_debate": True,
            "debate_quality": debate_analysis.debate_quality_score,
            "challenges_raised": debate_analysis.total_challenges,
            "valid_challenges": debate_analysis.valid_challenges,
            "successful_defenses": debate_analysis.successful_defenses,
            "successful_prosecutions": debate_analysis.successful_prosecutions,
            "confidence_adjustment": debate_analysis.confidence_adjustment,
            "verdict_stability": debate_analysis.verdict_stability,
            "moderated_by": self.agent_id,
            "requires_further_investigation": debate_analysis.requires_further_investigation
        }
        
        return VerificationResult(
            claim=original_result.claim,
            verdict=new_verdict,
            confidence=adjusted_confidence,
            reasoning=enhanced_reasoning,
            sources=list(set(enhanced_sources)),  # Remove duplicates
            evidence=enhanced_evidence,
            metadata=enhanced_metadata,
            agent_id=f"{original_result.agent_id}_moderated",
            timestamp=datetime.now()
        )
    
    def _validate_challenges(self, challenges: List[Challenge]) -> List[Challenge]:
        """Validate challenges using the challenge validator."""
        valid_challenges = []
        
        for challenge in challenges:
            validation = self.challenge_validator.validate_challenge(challenge)
            if validation["is_valid"]:
                valid_challenges.append(challenge)
        
        return valid_challenges
    
    def _assess_response_quality(
        self, 
        responses: List[ChallengeResponse], 
        challenges: List[Challenge]
    ) -> float:
        """Assess the overall quality of responses to challenges."""
        if not responses:
            return 0.0
        
        quality_scores = []
        
        for response in responses:
            # Find the corresponding challenge
            challenge = next(
                (c for c in challenges if c.challenge_id == response.challenge_id),
                None
            )
            
            if challenge:
                # Base quality from response adequacy
                base_quality = response.adequacy_score
                
                # Adjust based on challenge strength
                if challenge.strength == ChallengeStrength.CRITICAL:
                    # Responding to critical challenges is more valuable
                    base_quality *= 1.3
                elif challenge.strength == ChallengeStrength.WEAK:
                    # Responding to weak challenges is less impressive
                    base_quality *= 0.8
                
                # Adjust based on response type
                if response.response_type == "concession":
                    # Honest concessions are valuable
                    base_quality *= 1.1
                elif response.response_type == "counter-challenge":
                    # Counter-challenges add complexity
                    base_quality *= 1.2
                
                quality_scores.append(min(1.0, base_quality))
        
        return sum(quality_scores) / len(quality_scores)
    
    def _calculate_challenge_quality(self, challenges: List[Challenge]) -> float:
        """Calculate overall quality of challenges raised."""
        if not challenges:
            return 0.0
        
        quality_scores = [
            (c.specificity_score + c.verifiability_score + c.impact_score) / 3
            for c in challenges
        ]
        
        return sum(quality_scores) / len(quality_scores)
    
    def _synthesize_debate(
        self,
        original_result: VerificationResult,
        challenges: List[Challenge],
        responses: List[ChallengeResponse]
    ) -> Dict[str, Any]:
        """Synthesize debate into actionable insights."""
        
        # Calculate confidence adjustment
        confidence_adjustment = 0.0
        key_findings = []
        remaining_concerns = []
        
        # Analyze each challenge-response pair
        for challenge in challenges:
            corresponding_response = next(
                (r for r in responses if r.challenge_id == challenge.challenge_id),
                None
            )
            
            if corresponding_response:
                if corresponding_response.response_type == "concession":
                    # Defender conceded - reduce confidence
                    strength_impact = {
                        ChallengeStrength.WEAK: -0.05,
                        ChallengeStrength.MODERATE: -0.1,
                        ChallengeStrength.STRONG: -0.15,
                        ChallengeStrength.CRITICAL: -0.25
                    }
                    confidence_adjustment += strength_impact.get(challenge.strength, -0.1)
                    remaining_concerns.append(f"{challenge.challenge_type.value}: {challenge.description}")
                
                elif corresponding_response.adequacy_score >= 0.8:
                    # Strong defense - slight confidence boost
                    confidence_adjustment += 0.02
                    key_findings.append(f"Successfully defended against {challenge.challenge_type.value}")
                
                elif corresponding_response.adequacy_score < 0.5:
                    # Weak defense - reduce confidence
                    confidence_adjustment -= 0.05
                    remaining_concerns.append(f"Weak defense of {challenge.challenge_type.value}")
            
            else:
                # Unaddressed challenge - significant confidence reduction
                strength_impact = {
                    ChallengeStrength.WEAK: -0.03,
                    ChallengeStrength.MODERATE: -0.08,
                    ChallengeStrength.STRONG: -0.15,
                    ChallengeStrength.CRITICAL: -0.3
                }
                confidence_adjustment += strength_impact.get(challenge.strength, -0.1)
                remaining_concerns.append(f"Unaddressed {challenge.challenge_type.value}: {challenge.description}")
        
        # Calculate verdict stability
        critical_challenges = [c for c in challenges if c.strength == ChallengeStrength.CRITICAL]
        strong_challenges = [c for c in challenges if c.strength == ChallengeStrength.STRONG]
        
        verdict_stability = 1.0
        if critical_challenges:
            # Critical challenges significantly reduce stability
            unaddressed_critical = len([c for c in critical_challenges 
                                       if not any(r.challenge_id == c.challenge_id and r.adequacy_score >= 0.7 
                                                 for r in responses)])
            verdict_stability -= unaddressed_critical * 0.4
        
        if strong_challenges:
            unaddressed_strong = len([c for c in strong_challenges 
                                     if not any(r.challenge_id == c.challenge_id and r.adequacy_score >= 0.7 
                                               for r in responses)])
            verdict_stability -= unaddressed_strong * 0.2
        
        verdict_stability = max(0.0, verdict_stability)
        
        # Determine if further investigation is needed
        requires_investigation = (
            len(remaining_concerns) > 2 or
            any(c.strength == ChallengeStrength.CRITICAL for c in challenges) or
            verdict_stability < 0.6
        )
        
        # Create synthesis summary
        summary_parts = []
        
        if len(challenges) > 0:
            summary_parts.append(f"Adversarial analysis raised {len(challenges)} challenges")
        
        if confidence_adjustment != 0:
            direction = "increased" if confidence_adjustment > 0 else "decreased"
            summary_parts.append(f"confidence {direction} by {abs(confidence_adjustment):.2f}")
        
        if remaining_concerns:
            summary_parts.append(f"{len(remaining_concerns)} concerns remain unresolved")
        
        if key_findings:
            summary_parts.append(f"{len(key_findings)} key defenses validated")
        
        synthesis_summary = ". ".join(summary_parts) + "." if summary_parts else "No significant challenges raised."
        
        return {
            "confidence_adjustment": confidence_adjustment,
            "verdict_stability": verdict_stability,
            "requires_investigation": requires_investigation,
            "summary": synthesis_summary,
            "key_findings": key_findings,
            "remaining_concerns": remaining_concerns
        }
    
    def _create_enhanced_reasoning(
        self,
        original_result: VerificationResult,
        debate_analysis: DebateAnalysis
    ) -> str:
        """Create enhanced reasoning incorporating debate insights."""
        
        reasoning_parts = [
            f"Original verification: {original_result.reasoning}"
        ]
        
        if debate_analysis.challenges:
            reasoning_parts.append(
                f"Adversarial analysis raised {len(debate_analysis.challenges)} challenges, "
                f"{debate_analysis.valid_challenges} of which were validated."
            )
        
        if debate_analysis.key_findings:
            reasoning_parts.append(
                f"Key strengths identified: {'; '.join(debate_analysis.key_findings[:3])}"
            )
        
        if debate_analysis.remaining_concerns:
            reasoning_parts.append(
                f"Remaining concerns: {'; '.join(debate_analysis.remaining_concerns[:3])}"
            )
        
        if debate_analysis.requires_further_investigation:
            reasoning_parts.append(
                "Further investigation recommended due to unresolved challenges."
            )
        
        reasoning_parts.append(debate_analysis.synthesis_summary)
        
        return " | ".join(reasoning_parts)
    
    def _update_stats(self, analysis: DebateAnalysis) -> None:
        """Update moderator statistics."""
        self.stats["total_debates_moderated"] += 1
        
        # Determine if results improved, unchanged, or degraded
        if abs(analysis.confidence_adjustment) > 0.05:
            if analysis.confidence_adjustment > 0:
                self.stats["debates_improved_results"] += 1
            else:
                # Consider this improvement if it correctly reduces overconfidence
                if analysis.original_result.confidence > 0.8:
                    self.stats["debates_improved_results"] += 1
                else:
                    self.stats["debates_degraded_results"] += 1
        else:
            self.stats["debates_unchanged_results"] += 1
        
        if analysis.verdict_stability < 0.5:
            self.stats["verdicts_changed"] += 1
        
        # Update rolling averages
        total_debates = self.stats["total_debates_moderated"]
        
        # Average debate quality
        old_avg_quality = self.stats["average_debate_quality"]
        self.stats["average_debate_quality"] = (
            (old_avg_quality * (total_debates - 1) + analysis.debate_quality_score) / total_debates
        )
        
        # Average confidence adjustment
        old_avg_adjustment = self.stats["average_confidence_adjustment"]
        self.stats["average_confidence_adjustment"] = (
            (old_avg_adjustment * (total_debates - 1) + analysis.confidence_adjustment) / total_debates
        )
    
    def get_moderator_stats(self) -> Dict[str, Any]:
        """Get moderator performance statistics."""
        total_debates = self.stats["total_debates_moderated"]
        
        improvement_rate = 0.0
        if total_debates > 0:
            improvement_rate = self.stats["debates_improved_results"] / total_debates
        
        return {
            **self.stats,
            "improvement_rate": improvement_rate,
            "verdict_change_rate": self.stats["verdicts_changed"] / max(1, total_debates),
            "agent_id": self.agent_id,
            "role": "moderator"
        }
    
    async def moderate_debate_async(
        self,
        original_result: VerificationResult,
        challenges: List[Challenge],
        responses: List[ChallengeResponse]
    ) -> DebateAnalysis:
        """Async version of moderate_debate."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.moderate_debate, original_result, challenges, responses
        )