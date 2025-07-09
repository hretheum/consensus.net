"""
Prosecutor Agent for Adversarial Verification

The ProsecutorAgent systematically challenges verification results
to identify weaknesses and improve overall accuracy.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...agents.base_agent import BaseAgent
from ...agents.verification_result import VerificationResult
from ...agents.agent_models import Evidence
from src.consensus.adversarial.challenge_system import (
    Challenge, ChallengeType, ChallengeStrength, 
    ChallengeGenerator, ChallengeResponse
)


class ProsecutorAgent(BaseAgent):
    """
    Prosecutor Agent for adversarial verification debates.
    
    Systematically challenges verification results to identify
    weaknesses, biases, and logical fallacies.
    """
    
    def __init__(self, agent_id: str = "prosecutor_agent"):
        """Initialize the prosecutor agent."""
        super().__init__(agent_id)
        
        self.challenge_generator = ChallengeGenerator()
        
        # Prosecutor configuration
        self.max_challenges_per_result = 5
        self.challenge_aggressiveness = 0.7  # How aggressively to challenge
        self.focus_areas = [
            ChallengeType.SOURCE_CREDIBILITY,
            ChallengeType.EVIDENCE_RELEVANCE,
            ChallengeType.LOGICAL_FALLACY,
            ChallengeType.FACTUAL_ACCURACY
        ]
        
        # Prosecutor statistics
        self.stats = {
            "total_challenges_raised": 0,
            "successful_challenges": 0,
            "challenge_types": {},
            "average_challenge_strength": 0.0,
            "results_challenged": 0
        }
    
    def verify(self, claim: str) -> VerificationResult:
        """
        Prosecutor agents don't verify claims directly.
        They challenge existing verification results.
        """
        return VerificationResult(
            claim=claim,
            verdict="ERROR",
            confidence=0.0,
            reasoning="Prosecutor agents challenge results, they don't verify claims directly",
            sources=[],
            evidence=[],
            metadata={"agent_role": "prosecutor"},
            agent_id=self.agent_id
        )
    
    def challenge_result(self, result: VerificationResult) -> List[Challenge]:
        """
        Generate systematic challenges for a verification result.
        
        Args:
            result: The verification result to challenge
            
        Returns:
            List of challenges raised against the result
        """
        print(f"🚨 Prosecutor challenging result for: {result.claim[:50]}...")
        
        # Generate challenges using the challenge generator
        challenges = self.challenge_generator.generate_challenges(
            result, 
            max_challenges=self.max_challenges_per_result
        )
        
        # Apply prosecutor-specific filtering and prioritization
        filtered_challenges = self._filter_challenges(challenges)
        prioritized_challenges = self._prioritize_challenges(filtered_challenges)
        
        # Update statistics
        self._update_stats(prioritized_challenges)
        
        print(f"🎯 Prosecutor raised {len(prioritized_challenges)} challenges")
        return prioritized_challenges
    
    def challenge_specific_aspect(
        self, 
        result: VerificationResult, 
        challenge_type: ChallengeType,
        specific_target: str = ""
    ) -> Optional[Challenge]:
        """
        Generate a specific type of challenge for a verification result.
        
        Args:
            result: The verification result to challenge
            challenge_type: The specific type of challenge to raise
            specific_target: Specific aspect to target
            
        Returns:
            A targeted challenge or None if not applicable
        """
        if challenge_type == ChallengeType.SOURCE_CREDIBILITY:
            return self._challenge_source_credibility(result, specific_target)
        elif challenge_type == ChallengeType.EVIDENCE_RELEVANCE:
            return self._challenge_evidence_relevance(result)
        elif challenge_type == ChallengeType.LOGICAL_FALLACY:
            return self._challenge_logical_reasoning(result)
        elif challenge_type == ChallengeType.FACTUAL_ACCURACY:
            return self._challenge_factual_accuracy(result, specific_target)
        elif challenge_type == ChallengeType.BIAS_DETECTION:
            return self._challenge_potential_bias(result)
        else:
            return None
    
    def _filter_challenges(self, challenges: List[Challenge]) -> List[Challenge]:
        """Filter challenges based on prosecutor strategy."""
        filtered = []
        
        print(f"📋 Prosecutor filtering {len(challenges)} initial challenges...")
        
        for challenge in challenges:
            priority = challenge.get_priority_score()
            print(f"   🎯 Challenge {challenge.challenge_type.value}: priority={priority:.2f}")
            
            # More lenient filtering - accept challenges with priority >= 0.2
            if priority >= 0.2:
                # Apply aggressiveness factor (lowered threshold)
                if priority >= (1.0 - self.challenge_aggressiveness):
                    filtered.append(challenge)
                    print(f"     ✅ Accepted (high priority)")
                elif challenge.challenge_type in self.focus_areas:
                    filtered.append(challenge)
                    print(f"     ✅ Accepted (focus area)")
                elif priority >= 0.4:  # Additional threshold for medium priority
                    filtered.append(challenge)
                    print(f"     ✅ Accepted (medium priority)")
                else:
                    print(f"     ❌ Rejected (low priority)")
            else:
                print(f"     ❌ Rejected (below threshold)")
        
        print(f"📋 Filtered to {len(filtered)} challenges")
        return filtered
    
    def _prioritize_challenges(self, challenges: List[Challenge]) -> List[Challenge]:
        """Prioritize challenges based on prosecutor strategy."""
        # Sort by priority score and focus areas
        def challenge_priority(challenge: Challenge) -> float:
            base_priority = challenge.get_priority_score()
            
            # Boost priority for focus areas
            if challenge.challenge_type in self.focus_areas:
                base_priority *= 1.2
            
            # Boost priority for critical issues
            if challenge.strength == ChallengeStrength.CRITICAL:
                base_priority *= 1.5
            
            return min(1.0, base_priority)
        
        challenges.sort(key=challenge_priority, reverse=True)
        return challenges
    
    def _challenge_source_credibility(self, result: VerificationResult, target_source: str = "") -> Optional[Challenge]:
        """Challenge the credibility of sources used."""
        sources_to_challenge = [target_source] if target_source else result.sources
        
        for source in sources_to_challenge:
            if source:
                # Check for questionable domains
                questionable_indicators = [
                    "blog", "forum", "social", "user", "wiki", "personal",
                    ".tk", ".ml", ".ga", "bit.ly", "tinyurl"
                ]
                
                if any(indicator in source.lower() for indicator in questionable_indicators):
                    return Challenge(
                        challenge_type=ChallengeType.SOURCE_CREDIBILITY,
                        strength=ChallengeStrength.MODERATE,
                        description=f"Source '{source}' may lack editorial oversight",
                        reasoning="This source appears to be user-generated or lacks institutional credibility",
                        target_claim=result.claim,
                        raised_by=self.agent_id,
                        specificity_score=0.8,
                        verifiability_score=0.9,
                        impact_score=0.6
                    )
        
        return None
    
    def _challenge_evidence_relevance(self, result: VerificationResult) -> Optional[Challenge]:
        """Challenge the relevance of evidence to the claim."""
        if len(result.evidence) == 0:
            return Challenge(
                challenge_type=ChallengeType.EVIDENCE_RELEVANCE,
                strength=ChallengeStrength.CRITICAL,
                description="No supporting evidence provided for this claim",
                reasoning="A verification without evidence cannot be considered reliable",
                target_claim=result.claim,
                raised_by=self.agent_id,
                specificity_score=1.0,
                verifiability_score=1.0,
                impact_score=1.0
            )
        
        elif len(result.evidence) < 2:
            return Challenge(
                challenge_type=ChallengeType.EVIDENCE_RELEVANCE,
                strength=ChallengeStrength.STRONG,
                description="Insufficient evidence for reliable verification",
                reasoning="Single-source verification is vulnerable to source-specific bias",
                target_claim=result.claim,
                raised_by=self.agent_id,
                specificity_score=0.9,
                verifiability_score=1.0,
                impact_score=0.8
            )
        
        return None
    
    def _challenge_logical_reasoning(self, result: VerificationResult) -> Optional[Challenge]:
        """Challenge the logical reasoning in the verification."""
        reasoning = result.reasoning.lower()
        
        # Check for logical fallacies
        fallacy_indicators = {
            "everyone knows": "Appeal to common knowledge",
            "obviously": "Assertion without evidence",
            "always" and "never": "Absolute statements",
            "correlation": "Potential correlation-causation confusion",
            "because": "Need to verify causal claims"
        }
        
        for indicator, fallacy in fallacy_indicators.items():
            if indicator in reasoning:
                return Challenge(
                    challenge_type=ChallengeType.LOGICAL_FALLACY,
                    strength=ChallengeStrength.MODERATE,
                    description=f"Potential logical fallacy detected: {fallacy}",
                    reasoning=f"The phrase '{indicator}' suggests {fallacy.lower()}",
                    target_reasoning_segment=result.reasoning,
                    raised_by=self.agent_id,
                    specificity_score=0.7,
                    verifiability_score=0.8,
                    impact_score=0.5
                )
        
        return None
    
    def _challenge_factual_accuracy(self, result: VerificationResult, specific_fact: str = "") -> Optional[Challenge]:
        """Challenge specific factual claims in the result."""
        # Check for verdict-confidence misalignment
        if result.verdict == "TRUE" and result.confidence < 0.6:
            return Challenge(
                challenge_type=ChallengeType.FACTUAL_ACCURACY,
                strength=ChallengeStrength.STRONG,
                description="Verdict 'TRUE' with low confidence is problematic",
                reasoning="Claims should not be marked as 'TRUE' without adequate confidence",
                target_claim=result.claim,
                raised_by=self.agent_id,
                specificity_score=0.9,
                verifiability_score=1.0,
                impact_score=0.9
            )
        
        elif result.verdict == "FALSE" and result.confidence < 0.7:
            return Challenge(
                challenge_type=ChallengeType.FACTUAL_ACCURACY,
                strength=ChallengeStrength.MODERATE,
                description="Verdict 'FALSE' requires high confidence",
                reasoning="Disproving claims requires stronger evidence than proving them",
                target_claim=result.claim,
                raised_by=self.agent_id,
                specificity_score=0.8,
                verifiability_score=0.9,
                impact_score=0.7
            )
        
        return None
    
    def _challenge_potential_bias(self, result: VerificationResult) -> Optional[Challenge]:
        """Challenge potential bias in the verification."""
        # Check for extremely high confidence (potential overconfidence)
        if result.confidence > 0.95:
            return Challenge(
                challenge_type=ChallengeType.BIAS_DETECTION,
                strength=ChallengeStrength.WEAK,
                description="Extremely high confidence may indicate overconfidence bias",
                reasoning="Very few claims warrant >95% confidence; this suggests possible overconfidence",
                target_claim=result.claim,
                raised_by=self.agent_id,
                specificity_score=0.6,
                verifiability_score=0.7,
                impact_score=0.4
            )
        
        # Check for confirmation bias indicators
        if result.verdict in ["TRUE", "FALSE"]:
            strong_language = ["definitely", "absolutely", "certainly", "without doubt"]
            if any(word in result.reasoning.lower() for word in strong_language):
                return Challenge(
                    challenge_type=ChallengeType.BIAS_DETECTION,
                    strength=ChallengeStrength.WEAK,
                    description="Strong language may indicate confirmation bias",
                    reasoning="Overly strong language suggests the agent may be seeking to confirm rather than test the claim",
                    target_reasoning_segment=result.reasoning,
                    raised_by=self.agent_id,
                    specificity_score=0.5,
                    verifiability_score=0.6,
                    impact_score=0.3
                )
        
        return None
    
    def _update_stats(self, challenges: List[Challenge]) -> None:
        """Update prosecutor statistics."""
        self.stats["total_challenges_raised"] += len(challenges)
        self.stats["results_challenged"] += 1
        
        # Update challenge type counts
        for challenge in challenges:
            challenge_type = challenge.challenge_type.value
            self.stats["challenge_types"][challenge_type] = (
                self.stats["challenge_types"].get(challenge_type, 0) + 1
            )
        
        # Calculate average challenge strength
        if challenges:
            strength_values = {
                ChallengeStrength.WEAK: 0.25,
                ChallengeStrength.MODERATE: 0.5,
                ChallengeStrength.STRONG: 0.75,
                ChallengeStrength.CRITICAL: 1.0
            }
            
            avg_strength = sum(strength_values[c.strength] for c in challenges) / len(challenges)
            
            # Update rolling average
            total_challenges = self.stats["total_challenges_raised"]
            if total_challenges > len(challenges):
                old_avg = self.stats["average_challenge_strength"]
                old_count = total_challenges - len(challenges)
                new_count = len(challenges)
                
                self.stats["average_challenge_strength"] = (
                    (old_avg * old_count + avg_strength * new_count) / total_challenges
                )
            else:
                self.stats["average_challenge_strength"] = avg_strength
    
    def get_prosecutor_stats(self) -> Dict[str, Any]:
        """Get prosecutor performance statistics."""
        total_challenges = self.stats["total_challenges_raised"]
        success_rate = 0.0
        
        if total_challenges > 0:
            success_rate = self.stats["successful_challenges"] / total_challenges
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "challenges_per_result": total_challenges / max(1, self.stats["results_challenged"]),
            "agent_id": self.agent_id,
            "role": "prosecutor"
        }
    
    def mark_challenge_successful(self, challenge_id: str) -> None:
        """Mark a challenge as successful (used by moderator)."""
        self.stats["successful_challenges"] += 1
    
    async def challenge_result_async(self, result: VerificationResult) -> List[Challenge]:
        """Async version of challenge_result."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.challenge_result, result
        )