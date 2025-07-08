"""
Challenge System for Adversarial Debates

Defines the structure and types of challenges that can be raised
in adversarial verification debates.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

from ...agents.verification_result import VerificationResult
from ...agents.agent_models import Evidence


class ChallengeType(Enum):
    """Types of challenges in adversarial debates."""
    SOURCE_CREDIBILITY = "source_credibility"       # Challenge source reliability
    EVIDENCE_RELEVANCE = "evidence_relevance"       # Challenge evidence relevance
    LOGICAL_FALLACY = "logical_fallacy"             # Challenge reasoning logic
    FACTUAL_ACCURACY = "factual_accuracy"           # Challenge specific facts
    CONTEXT_MISSING = "context_missing"             # Challenge lack of context
    BIAS_DETECTION = "bias_detection"               # Challenge potential bias
    METHODOLOGY_FLAW = "methodology_flaw"           # Challenge research methods
    TEMPORAL_VALIDITY = "temporal_validity"         # Challenge time relevance


class ChallengeStrength(Enum):
    """Strength levels of challenges."""
    WEAK = "weak"               # Minor issue, doesn't affect conclusion
    MODERATE = "moderate"       # Notable issue, may affect confidence
    STRONG = "strong"          # Serious issue, likely affects conclusion
    CRITICAL = "critical"       # Fatal flaw, invalidates claim


@dataclass
class Challenge:
    """A specific challenge raised against a verification result or evidence."""
    
    challenge_id: str = field(default_factory=lambda: f"chall_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    challenge_type: ChallengeType = ChallengeType.FACTUAL_ACCURACY
    strength: ChallengeStrength = ChallengeStrength.MODERATE
    
    # Challenge content
    description: str = ""
    reasoning: str = ""
    supporting_evidence: List[Evidence] = field(default_factory=list)
    
    # Target of challenge
    target_claim: Optional[str] = None
    target_evidence: Optional[Evidence] = None
    target_reasoning_segment: Optional[str] = None
    
    # Challenge metadata
    raised_by: str = ""  # Agent ID
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Challenge analysis
    specificity_score: float = 0.0      # How specific is this challenge
    verifiability_score: float = 0.0    # How easy to verify this challenge
    impact_score: float = 0.0           # Potential impact on conclusion
    
    def get_priority_score(self) -> float:
        """Calculate priority score for addressing this challenge."""
        strength_weights = {
            ChallengeStrength.WEAK: 0.2,
            ChallengeStrength.MODERATE: 0.5,
            ChallengeStrength.STRONG: 0.8,
            ChallengeStrength.CRITICAL: 1.0
        }
        
        base_score = strength_weights[self.strength]
        specificity_bonus = self.specificity_score * 0.2
        impact_bonus = self.impact_score * 0.3
        
        return min(1.0, base_score + specificity_bonus + impact_bonus)


@dataclass
class ChallengeResponse:
    """Response to a challenge in adversarial debate."""
    
    response_id: str = field(default_factory=lambda: f"resp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}")
    challenge_id: str = ""
    
    # Response content
    response_type: str = "defense"  # defense, concession, counter-challenge
    explanation: str = ""
    counter_evidence: List[Evidence] = field(default_factory=list)
    
    # Response metadata
    responded_by: str = ""  # Agent ID
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Response assessment
    adequacy_score: float = 0.0      # How well does this address the challenge
    confidence: float = 0.0          # Confidence in this response
    
    def is_adequate(self) -> bool:
        """Check if response adequately addresses the challenge."""
        return self.adequacy_score >= 0.7


class ChallengeGenerator:
    """
    Generates systematic challenges for verification results.
    
    Used by ProsecutorAgent to create comprehensive challenges.
    """
    
    def __init__(self):
        """Initialize the challenge generator."""
        self.challenge_templates = self._load_challenge_templates()
        
    def generate_challenges(self, result: VerificationResult, max_challenges: int = 5) -> List[Challenge]:
        """
        Generate systematic challenges for a verification result.
        
        Args:
            result: The verification result to challenge
            max_challenges: Maximum number of challenges to generate
            
        Returns:
            List of generated challenges
        """
        challenges = []
        
        # Challenge source credibility
        source_challenges = self._challenge_sources(result)
        challenges.extend(source_challenges[:2])  # Limit to top 2
        
        # Challenge evidence relevance
        evidence_challenges = self._challenge_evidence(result)
        challenges.extend(evidence_challenges[:2])
        
        # Challenge reasoning logic
        logic_challenges = self._challenge_reasoning(result)
        challenges.extend(logic_challenges[:2])
        
        # Challenge factual accuracy
        factual_challenges = self._challenge_facts(result)
        challenges.extend(factual_challenges[:2])
        
        # Sort by priority and limit
        challenges.sort(key=lambda c: c.get_priority_score(), reverse=True)
        return challenges[:max_challenges]
    
    def _challenge_sources(self, result: VerificationResult) -> List[Challenge]:
        """Generate challenges to source credibility."""
        challenges = []
        
        for source in result.sources:
            # Check for low-credibility domains
            if any(domain in source.lower() for domain in ["blog", "forum", "social"]):
                challenge = Challenge(
                    challenge_type=ChallengeType.SOURCE_CREDIBILITY,
                    strength=ChallengeStrength.MODERATE,
                    description=f"Source '{source}' may not be authoritative",
                    reasoning="This source appears to be user-generated content rather than authoritative information",
                    target_claim=result.claim,
                    raised_by="prosecutor_agent",
                    specificity_score=0.8,
                    verifiability_score=0.9,
                    impact_score=0.6
                )
                challenges.append(challenge)
        
        return challenges
    
    def _challenge_evidence(self, result: VerificationResult) -> List[Challenge]:
        """Generate challenges to evidence relevance."""
        challenges = []
        
        # Challenge if too little evidence
        if len(result.evidence) < 2:
            challenge = Challenge(
                challenge_type=ChallengeType.EVIDENCE_RELEVANCE,
                strength=ChallengeStrength.STRONG,
                description="Insufficient evidence provided for this claim",
                reasoning="Only one piece of evidence is not sufficient for reliable verification",
                target_claim=result.claim,
                raised_by="prosecutor_agent",
                specificity_score=0.9,
                verifiability_score=1.0,
                impact_score=0.8
            )
            challenges.append(challenge)
        
        # Challenge evidence diversity
        sources_count = len(set(result.sources))
        if sources_count < 2:
            challenge = Challenge(
                challenge_type=ChallengeType.EVIDENCE_RELEVANCE,
                strength=ChallengeStrength.MODERATE,
                description="Evidence comes from too few independent sources",
                reasoning="Verification should rely on multiple independent sources for reliability",
                target_claim=result.claim,
                raised_by="prosecutor_agent",
                specificity_score=0.7,
                verifiability_score=0.8,
                impact_score=0.5
            )
            challenges.append(challenge)
        
        return challenges
    
    def _challenge_reasoning(self, result: VerificationResult) -> List[Challenge]:
        """Generate challenges to reasoning logic."""
        challenges = []
        
        reasoning_lower = result.reasoning.lower()
        
        # Check for weak reasoning indicators
        weak_indicators = ["maybe", "possibly", "seems like", "appears to", "might be"]
        if any(indicator in reasoning_lower for indicator in weak_indicators):
            challenge = Challenge(
                challenge_type=ChallengeType.LOGICAL_FALLACY,
                strength=ChallengeStrength.MODERATE,
                description="Reasoning contains uncertain language",
                reasoning="The verification uses tentative language suggesting low confidence",
                target_reasoning_segment=result.reasoning,
                raised_by="prosecutor_agent",
                specificity_score=0.6,
                verifiability_score=0.7,
                impact_score=0.4
            )
            challenges.append(challenge)
        
        # Check for confirmation bias
        if result.verdict in ["TRUE", "FALSE"] and result.confidence > 0.9:
            challenge = Challenge(
                challenge_type=ChallengeType.BIAS_DETECTION,
                strength=ChallengeStrength.WEAK,
                description="Very high confidence may indicate confirmation bias",
                reasoning="Extremely high confidence levels warrant scrutiny for potential bias",
                target_claim=result.claim,
                raised_by="prosecutor_agent",
                specificity_score=0.5,
                verifiability_score=0.6,
                impact_score=0.3
            )
            challenges.append(challenge)
        
        return challenges
    
    def _challenge_facts(self, result: VerificationResult) -> List[Challenge]:
        """Generate challenges to specific factual claims."""
        challenges = []
        
        # Challenge if verdict doesn't match confidence
        if result.verdict == "TRUE" and result.confidence < 0.6:
            challenge = Challenge(
                challenge_type=ChallengeType.FACTUAL_ACCURACY,
                strength=ChallengeStrength.STRONG,
                description="Verdict-confidence mismatch detected",
                reasoning="Claiming 'TRUE' with low confidence is inconsistent",
                target_claim=result.claim,
                raised_by="prosecutor_agent",
                specificity_score=0.9,
                verifiability_score=1.0,
                impact_score=0.9
            )
            challenges.append(challenge)
        
        return challenges
    
    def _load_challenge_templates(self) -> Dict[str, str]:
        """Load challenge templates for systematic generation."""
        return {
            "source_credibility": "The source '{source}' may not be reliable because {reason}",
            "evidence_relevance": "The evidence provided does not directly support the claim because {reason}",
            "logical_fallacy": "The reasoning contains a logical fallacy: {fallacy_type}",
            "factual_accuracy": "The factual claim '{fact}' appears to be incorrect based on {source}",
            "context_missing": "Important context is missing: {missing_context}",
            "bias_detection": "Potential bias detected in {area}: {bias_description}",
            "methodology_flaw": "The research methodology has a flaw: {flaw_description}",
            "temporal_validity": "The information may be outdated: {temporal_issue}"
        }


class ChallengeValidator:
    """
    Validates the quality and legitimacy of challenges.
    
    Used by ModeratorAgent to assess challenge quality.
    """
    
    def __init__(self):
        """Initialize the challenge validator."""
        self.validation_criteria = {
            "specificity": 0.6,      # Minimum specificity score
            "verifiability": 0.5,    # Minimum verifiability score
            "relevance": 0.7         # Minimum relevance score
        }
    
    def validate_challenge(self, challenge: Challenge) -> Dict[str, Any]:
        """
        Validate a challenge for quality and legitimacy.
        
        Args:
            challenge: The challenge to validate
            
        Returns:
            Validation result with scores and feedback
        """
        validation_result = {
            "is_valid": True,
            "validity_score": 0.0,
            "issues": [],
            "feedback": ""
        }
        
        # Check specificity
        if challenge.specificity_score < self.validation_criteria["specificity"]:
            validation_result["issues"].append("Challenge is too vague or non-specific")
            validation_result["is_valid"] = False
        
        # Check verifiability
        if challenge.verifiability_score < self.validation_criteria["verifiability"]:
            validation_result["issues"].append("Challenge cannot be objectively verified")
            validation_result["is_valid"] = False
        
        # Check description quality
        if len(challenge.description) < 20:
            validation_result["issues"].append("Challenge description is too brief")
            validation_result["is_valid"] = False
        
        # Check reasoning quality
        if len(challenge.reasoning) < 30:
            validation_result["issues"].append("Challenge reasoning is insufficient")
            validation_result["is_valid"] = False
        
        # Calculate overall validity score
        validity_components = [
            challenge.specificity_score,
            challenge.verifiability_score,
            challenge.impact_score,
            min(1.0, len(challenge.description) / 50),  # Description length score
            min(1.0, len(challenge.reasoning) / 100)    # Reasoning length score
        ]
        
        validation_result["validity_score"] = sum(validity_components) / len(validity_components)
        
        # Generate feedback
        if validation_result["is_valid"]:
            validation_result["feedback"] = "Challenge meets quality standards"
        else:
            validation_result["feedback"] = f"Challenge has {len(validation_result['issues'])} issues"
        
        return validation_result
    
    def rank_challenges(self, challenges: List[Challenge]) -> List[Challenge]:
        """
        Rank challenges by their quality and priority.
        
        Args:
            challenges: List of challenges to rank
            
        Returns:
            Ranked list of challenges
        """
        # Validate each challenge and assign quality scores
        ranked_challenges = []
        
        for challenge in challenges:
            validation = self.validate_challenge(challenge)
            if validation["is_valid"]:
                # Combine priority score with validity score
                combined_score = (challenge.get_priority_score() + validation["validity_score"]) / 2
                challenge.context["quality_score"] = combined_score
                ranked_challenges.append(challenge)
        
        # Sort by combined quality and priority score
        ranked_challenges.sort(
            key=lambda c: c.context.get("quality_score", 0.0), 
            reverse=True
        )
        
        return ranked_challenges