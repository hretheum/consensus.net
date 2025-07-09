"""
Defender Agent for Adversarial Verification

The DefenderAgent responds to challenges raised by the ProsecutorAgent,
providing counter-arguments and additional evidence to defend verification results.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from ...agents.base_agent import BaseAgent
from ...agents.verification_result import VerificationResult
from ...agents.agent_models import Evidence
from src.consensus.adversarial.challenge_system import (
    Challenge, ChallengeType, ChallengeStrength, 
    ChallengeResponse
)


class DefenderAgent(BaseAgent):
    """
    Defender Agent for adversarial verification debates.
    
    Responds to challenges by providing counter-arguments,
    additional evidence, and defense of verification results.
    """
    
    def __init__(self, agent_id: str = "defender_agent"):
        """Initialize the defender agent."""
        super().__init__(agent_id)
        
        # Defender configuration
        self.defense_thoroughness = 0.8  # How thoroughly to address challenges
        self.evidence_gathering_enabled = True
        self.counter_challenge_enabled = True
        
        # Defender statistics
        self.stats = {
            "total_challenges_received": 0,
            "challenges_addressed": 0,
            "challenges_refuted": 0,
            "challenges_conceded": 0,
            "counter_challenges_raised": 0,
            "defense_types": {},
            "average_response_quality": 0.0
        }
    
    def verify(self, claim: str) -> VerificationResult:
        """
        Defender agents don't verify claims directly.
        They defend existing verification results.
        """
        return VerificationResult(
            claim=claim,
            verdict="ERROR",
            confidence=0.0,
            reasoning="Defender agents defend results, they don't verify claims directly",
            sources=[],
            evidence=[],
            metadata={"agent_role": "defender"},
            agent_id=self.agent_id
        )
    
    def defend_against_challenges(
        self, 
        result: VerificationResult, 
        challenges: List[Challenge]
    ) -> List[ChallengeResponse]:
        """
        Generate responses to a list of challenges.
        
        Args:
            result: The original verification result being defended
            challenges: List of challenges to respond to
            
        Returns:
            List of challenge responses
        """
        print(f"🛡️ Defender responding to {len(challenges)} challenges for: {result.claim[:50]}...")
        
        responses = []
        
        for challenge in challenges:
            response = self._generate_response(result, challenge)
            if response:
                responses.append(response)
        
        # Update statistics
        self._update_stats(challenges, responses)
        
        print(f"🎯 Defender generated {len(responses)} responses")
        return responses
    
    def defend_against_challenge(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """
        Generate a response to a specific challenge.
        
        Args:
            result: The original verification result being defended
            challenge: The specific challenge to respond to
            
        Returns:
            Challenge response or None if unable to respond
        """
        return self._generate_response(result, challenge)
    
    def _generate_response(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Generate a response to a specific challenge."""
        
        # Route to specific defense strategy based on challenge type
        if challenge.challenge_type == ChallengeType.SOURCE_CREDIBILITY:
            return self._defend_source_credibility(result, challenge)
        elif challenge.challenge_type == ChallengeType.EVIDENCE_RELEVANCE:
            return self._defend_evidence_relevance(result, challenge)
        elif challenge.challenge_type == ChallengeType.LOGICAL_FALLACY:
            return self._defend_logical_reasoning(result, challenge)
        elif challenge.challenge_type == ChallengeType.FACTUAL_ACCURACY:
            return self._defend_factual_accuracy(result, challenge)
        elif challenge.challenge_type == ChallengeType.BIAS_DETECTION:
            return self._defend_against_bias_claims(result, challenge)
        elif challenge.challenge_type == ChallengeType.CONTEXT_MISSING:
            return self._defend_context_completeness(result, challenge)
        elif challenge.challenge_type == ChallengeType.METHODOLOGY_FLAW:
            return self._defend_methodology(result, challenge)
        elif challenge.challenge_type == ChallengeType.TEMPORAL_VALIDITY:
            return self._defend_temporal_validity(result, challenge)
        else:
            return self._generate_generic_defense(result, challenge)
    
    def _defend_source_credibility(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against source credibility challenges."""
        
        # Analyze the sources to provide a defense
        reputable_sources = []
        questionable_sources = []
        
        for source in result.sources:
            if any(domain in source.lower() for domain in [
                "edu", "gov", "org", "nature", "science", "britannica", 
                "reuters", "bbc", "npr", "wikipedia"
            ]):
                reputable_sources.append(source)
            else:
                questionable_sources.append(source)
        
        if reputable_sources:
            # Strong defense: we have reputable sources
            explanation = f"While some sources may be questioned, this verification includes {len(reputable_sources)} reputable sources: {', '.join(reputable_sources[:3])}{'...' if len(reputable_sources) > 3 else ''}. The diversity of sources strengthens the verification."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="defense",
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.8,
                confidence=0.85
            )
        
        elif len(result.sources) > 3:
            # Moderate defense: multiple sources provide cross-verification
            explanation = f"While individual source credibility may vary, the verification uses {len(result.sources)} independent sources. Cross-verification between multiple sources helps mitigate individual source limitations."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="defense",
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.6,
                confidence=0.7
            )
        
        else:
            # Weak defense: acknowledge the limitation
            explanation = "The concern about source credibility is noted. This verification would benefit from additional authoritative sources. The conclusion should be considered preliminary."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="concession",
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.4,
                confidence=0.5
            )
    
    def _defend_evidence_relevance(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against evidence relevance challenges."""
        
        if len(result.evidence) == 0:
            # Must concede this challenge - no evidence is a serious flaw
            explanation = "The challenge is valid. No supporting evidence significantly weakens this verification. Additional evidence gathering is recommended before reaching a conclusion."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="concession",
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.3,
                confidence=0.4
            )
        
        elif len(result.evidence) < 2:
            # Acknowledge limitation but defend process
            explanation = f"While the verification relies on limited evidence, the single piece of evidence ({result.evidence[0].source if result.evidence else 'available'}) directly addresses the core claim. Additional evidence would strengthen the conclusion, but the current evidence is directly relevant."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="defense",
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.6,
                confidence=0.65
            )
        
        else:
            # Strong defense: multiple pieces of evidence
            explanation = f"The verification includes {len(result.evidence)} pieces of evidence from {len(set(e.source for e in result.evidence))} distinct sources. This provides triangulation and cross-verification of the claim."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="defense",
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.8,
                confidence=0.8
            )
    
    def _defend_logical_reasoning(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against logical reasoning challenges."""
        
        reasoning = result.reasoning.lower()
        
        # Check if the challenge points to a specific logical fallacy
        if "everyone knows" in reasoning:
            explanation = "While the phrase 'everyone knows' appears informal, it refers to well-established facts with broad consensus. The verification is based on evidence, not just common belief."
        
        elif "obviously" in reasoning:
            explanation = "The term 'obviously' is used to describe conclusions that follow clearly from the evidence presented. The conclusion is supported by the evidence gathered, not just assertion."
        
        elif "correlation" in reasoning and "causation" in challenge.description.lower():
            explanation = "The verification acknowledges the distinction between correlation and causation. Where causal relationships are claimed, they are supported by the evidence or explicitly noted as correlational."
        
        else:
            # Generic defense against logical fallacy claims
            explanation = f"The reasoning follows a systematic approach: evidence gathering, analysis, and conclusion. While the language may appear informal, the underlying logic is sound and based on the available evidence."
        
        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            response_type="defense",
            explanation=explanation,
            responded_by=self.agent_id,
            adequacy_score=0.7,
            confidence=0.75
        )
    
    def _defend_factual_accuracy(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against factual accuracy challenges."""
        
        # Address verdict-confidence misalignment
        if "verdict" in challenge.description.lower() and "confidence" in challenge.description.lower():
            
            if result.verdict == "TRUE" and result.confidence < 0.6:
                explanation = f"The 'TRUE' verdict with {result.confidence:.2f} confidence reflects the balance of available evidence. While not definitive, the evidence supports the claim more than it contradicts it. A more cautious verdict of 'LIKELY TRUE' might be more appropriate."
                
                return ChallengeResponse(
                    challenge_id=challenge.challenge_id,
                    response_type="concession",
                    explanation=explanation,
                    responded_by=self.agent_id,
                    adequacy_score=0.5,
                    confidence=0.6
                )
            
            elif result.verdict == "FALSE" and result.confidence < 0.7:
                explanation = f"The challenge raises a valid point about the confidence level. Disproving claims typically requires stronger evidence. The {result.confidence:.2f} confidence suggests the verdict should perhaps be 'LIKELY FALSE' or 'UNCERTAIN' rather than definitively 'FALSE'."
                
                return ChallengeResponse(
                    challenge_id=challenge.challenge_id,
                    response_type="concession",
                    explanation=explanation,
                    responded_by=self.agent_id,
                    adequacy_score=0.6,
                    confidence=0.65
                )
        
        # Generic factual accuracy defense
        explanation = "The factual claims in the verification are based on the sources and evidence gathered. While interpretation may vary, the facts presented are consistent with the available information."
        
        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            response_type="defense",
            explanation=explanation,
            responded_by=self.agent_id,
            adequacy_score=0.7,
            confidence=0.7
        )
    
    def _defend_against_bias_claims(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against bias detection challenges."""
        
        if result.confidence > 0.95:
            explanation = f"While the {result.confidence:.2f} confidence is high, it reflects the strength of available evidence. High confidence is appropriate when evidence strongly supports a conclusion. However, maintaining epistemological humility is important."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="defense",
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.6,
                confidence=0.7
            )
        
        # Defense against confirmation bias claims
        if "strong language" in challenge.description.lower():
            explanation = "Strong language reflects the degree of evidence support, not confirmation bias. The verification process systematically gathered evidence rather than seeking to confirm preconceptions."
            
            return ChallengeResponse(
                challenge_id=challenge.challenge_id,
                response_type="defense", 
                explanation=explanation,
                responded_by=self.agent_id,
                adequacy_score=0.7,
                confidence=0.75
            )
        
        # Generic bias defense
        explanation = "The verification process followed systematic evidence gathering and analysis. While bias is always a concern, the multi-source approach and structured reasoning help mitigate bias effects."
        
        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            response_type="defense",
            explanation=explanation,
            responded_by=self.agent_id,
            adequacy_score=0.65,
            confidence=0.7
        )
    
    def _defend_context_completeness(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against missing context challenges."""
        
        explanation = "Context is inherently limited in any verification process. The verification addresses the core claim with available information. Additional context could always enhance understanding, but the current context is sufficient for the conclusion reached."
        
        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            response_type="defense",
            explanation=explanation,
            responded_by=self.agent_id,
            adequacy_score=0.6,
            confidence=0.65
        )
    
    def _defend_methodology(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against methodology flaw challenges."""
        
        explanation = "The verification methodology follows established practices: evidence gathering from multiple sources, systematic analysis, and reasoned conclusion. While no methodology is perfect, this approach balances thoroughness with practical constraints."
        
        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            response_type="defense",
            explanation=explanation,
            responded_by=self.agent_id,
            adequacy_score=0.7,
            confidence=0.75
        )
    
    def _defend_temporal_validity(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Defend against temporal validity challenges."""
        
        explanation = f"The verification was conducted at {result.timestamp} and reflects information available at that time. While information can become outdated, the core factual claims remain valid unless new contradictory evidence emerges."
        
        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            response_type="defense",
            explanation=explanation,
            responded_by=self.agent_id,
            adequacy_score=0.75,
            confidence=0.8
        )
    
    def _generate_generic_defense(
        self, 
        result: VerificationResult, 
        challenge: Challenge
    ) -> Optional[ChallengeResponse]:
        """Generate a generic defense for unspecified challenge types."""
        
        explanation = f"The challenge raises important points about {challenge.challenge_type.value}. The verification process aimed to be systematic and evidence-based. While improvements are always possible, the conclusion is supported by the available evidence and reasoning."
        
        return ChallengeResponse(
            challenge_id=challenge.challenge_id,
            response_type="defense",
            explanation=explanation,
            responded_by=self.agent_id,
            adequacy_score=0.5,
            confidence=0.6
        )
    
    def _update_stats(self, challenges: List[Challenge], responses: List[ChallengeResponse]) -> None:
        """Update defender statistics."""
        self.stats["total_challenges_received"] += len(challenges)
        self.stats["challenges_addressed"] += len(responses)
        
        # Count response types
        for response in responses:
            if response.response_type == "defense":
                self.stats["challenges_refuted"] += 1
            elif response.response_type == "concession":
                self.stats["challenges_conceded"] += 1
            elif response.response_type == "counter-challenge":
                self.stats["counter_challenges_raised"] += 1
            
            # Track defense types
            challenge_type = next(
                (c.challenge_type.value for c in challenges if c.challenge_id == response.challenge_id),
                "unknown"
            )
            self.stats["defense_types"][challenge_type] = (
                self.stats["defense_types"].get(challenge_type, 0) + 1
            )
        
        # Calculate average response quality
        if responses:
            avg_quality = sum(r.adequacy_score for r in responses) / len(responses)
            
            # Update rolling average
            total_responses = self.stats["challenges_addressed"]
            if total_responses > len(responses):
                old_avg = self.stats["average_response_quality"]
                old_count = total_responses - len(responses)
                new_count = len(responses)
                
                self.stats["average_response_quality"] = (
                    (old_avg * old_count + avg_quality * new_count) / total_responses
                )
            else:
                self.stats["average_response_quality"] = avg_quality
    
    def get_defender_stats(self) -> Dict[str, Any]:
        """Get defender performance statistics."""
        total_received = self.stats["total_challenges_received"]
        
        response_rate = 0.0
        refutation_rate = 0.0
        concession_rate = 0.0
        
        if total_received > 0:
            response_rate = self.stats["challenges_addressed"] / total_received
            refutation_rate = self.stats["challenges_refuted"] / total_received
            concession_rate = self.stats["challenges_conceded"] / total_received
        
        return {
            **self.stats,
            "response_rate": response_rate,
            "refutation_rate": refutation_rate,
            "concession_rate": concession_rate,
            "agent_id": self.agent_id,
            "role": "defender"
        }
    
    async def defend_against_challenges_async(
        self, 
        result: VerificationResult, 
        challenges: List[Challenge]
    ) -> List[ChallengeResponse]:
        """Async version of defend_against_challenges."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self.defend_against_challenges, result, challenges
        )