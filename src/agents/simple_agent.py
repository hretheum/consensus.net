"""
Simple implementation of the Core Agent Architecture.

This module provides a concrete example of how the components described in
docs/architecture/core-agent-architecture.md work together in practice.

This is a simplified implementation for demonstration purposes and testing.
Production agents would include more sophisticated LLM integration, evidence
gathering, and verification logic.
"""
import uuid
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from .base_agent import BaseAgent
from .verification_result import VerificationResult
from .agent_models import (
    ProcessedClaim, ClaimComplexity, AgentState, AgentConfig,
    Evidence, EvidenceBundle, LLMRequest, LLMResponse,
    VerificationStep, VerificationChain, PerformanceMetrics,
    InputError, VerificationError
)


class InputProcessor:
    """Handles input claim processing and normalization."""
    
    def parse_claim(self, raw_claim: str) -> ProcessedClaim:
        """Parse and normalize incoming claim."""
        if not raw_claim or not raw_claim.strip():
            raise InputError("Empty or invalid claim provided")
        
        # Basic normalization
        normalized = raw_claim.strip().lower()
        
        # Simple domain detection (in production, this would use ML)
        domain = self._detect_domain(normalized)
        
        # Simple complexity assessment
        complexity = self._assess_complexity(normalized)
        
        return ProcessedClaim(
            original_text=raw_claim,
            normalized_text=normalized,
            domain=domain,
            complexity=complexity,
            context={
                "word_count": len(raw_claim.split()),
                "has_numbers": any(char.isdigit() for char in raw_claim),
                "has_dates": self._contains_dates(raw_claim)
            },
            preprocessing_metadata={
                "processor_version": "1.0",
                "processing_time": time.time()
            }
        )
    
    def _detect_domain(self, text: str) -> str:
        """Simple domain detection based on keywords."""
        science_keywords = ["study", "research", "scientist", "data", "experiment", "scattering", "quantum", "physics"]
        news_keywords = ["breaking", "report", "announced", "today", "yesterday"]
        health_keywords = ["health", "medical", "doctor", "treatment", "disease", "exercise"]
        
        if any(keyword in text for keyword in science_keywords):
            return "science"
        elif any(keyword in text for keyword in health_keywords):
            return "health"
        elif any(keyword in text for keyword in news_keywords):
            return "news"
        else:
            return "general"
    
    def _assess_complexity(self, text: str) -> ClaimComplexity:
        """Simple complexity assessment."""
        word_count = len(text.split())
        
        if word_count < 8:
            return ClaimComplexity.SIMPLE
        elif word_count < 15:
            return ClaimComplexity.MODERATE
        else:
            return ClaimComplexity.COMPLEX
    
    def _contains_dates(self, text: str) -> bool:
        """Check if text contains date-like patterns."""
        date_indicators = ["2020", "2021", "2022", "2023", "2024", "2025", 
                          "january", "february", "march", "april", "may", "june",
                          "july", "august", "september", "october", "november", "december"]
        return any(indicator in text.lower() for indicator in date_indicators)


class StateManager:
    """Manages agent state and session information."""
    
    def __init__(self):
        self.sessions: Dict[str, AgentState] = {}
    
    def initialize_session(self, agent_id: str, claim: ProcessedClaim) -> str:
        """Initialize a new verification session."""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = AgentState(
            agent_id=agent_id,
            session_id=session_id,
            current_claim=claim,
            verification_history=[],
            intermediate_results={},
            confidence_calibration=1.0,
            domain_expertise={}
        )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[AgentState]:
        """Retrieve session state."""
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, key: str, value: Any) -> None:
        """Update session intermediate results."""
        if session_id in self.sessions:
            self.sessions[session_id].intermediate_results[key] = value
    
    def store_verification(self, session_id: str, result: VerificationResult) -> None:
        """Store completed verification result."""
        if session_id in self.sessions:
            self.sessions[session_id].add_verification(result)
    
    def cleanup_session(self, session_id: str) -> None:
        """Clean up completed session."""
        if session_id in self.sessions:
            del self.sessions[session_id]


class SimpleLLMInteraction:
    """Simple LLM interaction simulation for demonstration."""
    
    def generate_verification_prompt(self, claim: ProcessedClaim) -> str:
        """Generate verification prompt for the claim."""
        return f"""
        Please verify the following claim: "{claim.original_text}"
        
        Domain: {claim.domain}
        Complexity: {claim.complexity.value}
        
        Provide a clear assessment of whether this claim is true, false, or uncertain.
        Include your reasoning and any concerns about the claim.
        """
    
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """Simulate LLM call with simple rule-based responses."""
        # This is a simulation - in production, this would call actual LLM APIs
        
        claim_text = request.prompt.lower()
        
        # Simple rule-based verification simulation
        if "earth is flat" in claim_text:
            verdict = "FALSE"
            confidence = 0.99
            reasoning = "The Earth is scientifically proven to be spherical through multiple lines of evidence."
        elif "sky is blue" in claim_text:
            verdict = "TRUE"
            confidence = 0.95
            reasoning = "The sky appears blue due to Rayleigh scattering of light in the atmosphere."
        elif "2+2=4" in claim_text or "two plus two equals four" in claim_text:
            verdict = "TRUE"
            confidence = 1.0
            reasoning = "This is a basic mathematical fact."
        else:
            verdict = "UNCERTAIN"
            confidence = 0.3
            reasoning = "Insufficient information available for verification in this simulation."
        
        return LLMResponse(
            content=f"Verdict: {verdict}\nConfidence: {confidence}\nReasoning: {reasoning}",
            metadata={"simulation": True, "model": "rule-based"},
            model_used=request.model,
            tokens_used=len(request.prompt) + 50,  # Simulated token usage
            confidence=confidence
        )


class SimpleEvidenceEngine:
    """Simple evidence gathering simulation."""
    
    def search_sources(self, claim: ProcessedClaim) -> List[str]:
        """Simulate source discovery."""
        # Simulate finding relevant sources based on domain
        domain_sources = {
            "science": ["pubmed.gov", "arxiv.org", "nature.com"],
            "health": ["who.int", "cdc.gov", "mayoclinic.org"],
            "news": ["reuters.com", "bbc.com", "apnews.com"],
            "general": ["wikipedia.org", "britannica.com"]
        }
        
        return domain_sources.get(claim.domain, domain_sources["general"])
    
    def retrieve_evidence(self, sources: List[str], claim: ProcessedClaim) -> EvidenceBundle:
        """Simulate evidence retrieval."""
        # Simulate gathering evidence from sources
        supporting = [
            Evidence(
                content=f"Supporting evidence from {sources[0]} for claim about {claim.domain}",
                source=sources[0],
                credibility_score=0.8,
                relevance_score=0.9,
                timestamp=datetime.now()
            )
        ]
        
        contradicting = [
            Evidence(
                content=f"Contradicting evidence from {sources[1] if len(sources) > 1 else sources[0]}",
                source=sources[1] if len(sources) > 1 else sources[0],
                credibility_score=0.7,
                relevance_score=0.8,
                timestamp=datetime.now()
            )
        ]
        
        return EvidenceBundle(
            supporting_evidence=supporting,
            contradicting_evidence=contradicting,
            neutral_evidence=[],
            overall_quality=0.75
        )


class VerificationLogic:
    """Core verification reasoning engine."""
    
    def __init__(self, llm_interaction: SimpleLLMInteraction, evidence_engine: SimpleEvidenceEngine):
        self.llm = llm_interaction
        self.evidence = evidence_engine
    
    def verify_claim(self, claim: ProcessedClaim, state: AgentState) -> VerificationChain:
        """Execute the verification logic."""
        chain = VerificationChain()
        start_time = time.time()
        
        try:
            # Step 1: Claim structure analysis
            claim_components = self._analyze_claim_structure(claim)
            chain.steps.append(VerificationStep(
                step_type="claim_analysis",
                input_data={"original_claim": claim.original_text},
                output_data={"components": claim_components, "component_count": len(claim_components)},
                confidence=0.9,  # High confidence in structural analysis
                reasoning=f"Analyzed claim structure, identified {len(claim_components)} verifiable components"
            ))
            
            # Step 2: Evidence gathering
            sources = self.evidence.search_sources(claim)
            evidence_bundle = self.evidence.retrieve_evidence(sources, claim)
            
            chain.steps.append(VerificationStep(
                step_type="evidence_gathering",
                input_data={"sources": sources},
                output_data={"evidence_count": evidence_bundle.total_evidence_count},
                confidence=evidence_bundle.overall_quality,
                reasoning=f"Gathered {evidence_bundle.total_evidence_count} pieces of evidence from {len(sources)} sources"
            ))
            
            # Step 3: LLM analysis
            prompt = self.llm.generate_verification_prompt(claim)
            llm_request = LLMRequest(
                prompt=prompt,
                model="gpt-4o-mini",
                parameters={}
            )
            llm_response = self.llm.call_llm(llm_request)
            
            chain.steps.append(VerificationStep(
                step_type="llm_analysis",
                input_data={"prompt_length": len(prompt)},
                output_data={"tokens_used": llm_response.tokens_used},
                confidence=llm_response.confidence or 0.5,
                reasoning="LLM provided verification analysis with contextual reasoning"
            ))
            
            # Step 4: Bias detection and mitigation
            bias_indicators = self._detect_potential_biases(claim, evidence_bundle)
            chain.steps.append(VerificationStep(
                step_type="bias_detection",
                input_data={"claim_domain": claim.domain},
                output_data={"bias_indicators": bias_indicators, "bias_count": len(bias_indicators)},
                confidence=0.8 if len(bias_indicators) == 0 else max(0.4, 0.8 - len(bias_indicators) * 0.1),
                reasoning=f"Analyzed potential biases, found {len(bias_indicators)} indicators requiring attention"
            ))
            
            # Step 5: Uncertainty assessment
            uncertainty_factors = self._assess_uncertainty_factors(claim, evidence_bundle, llm_response)
            chain.uncertainty_factors.extend(uncertainty_factors)
            
            chain.steps.append(VerificationStep(
                step_type="uncertainty_assessment",
                input_data={"evidence_quality": evidence_bundle.overall_quality},
                output_data={"uncertainty_count": len(uncertainty_factors)},
                confidence=max(0.3, 1.0 - (len(uncertainty_factors) * 0.15)),
                reasoning=f"Identified {len(uncertainty_factors)} uncertainty factors affecting verification"
            ))
            
            # Step 6: Final verdict calculation
            verdict = self._extract_verdict(llm_response.content)
            confidence = self._calculate_final_confidence(evidence_bundle, llm_response)
            
            # Apply bias penalty to confidence
            if bias_indicators:
                bias_penalty = min(len(bias_indicators) * 0.05, 0.15)
                confidence = max(0.0, confidence - bias_penalty)
            
            chain.steps.append(VerificationStep(
                step_type="verdict_calculation",
                input_data={"evidence_quality": evidence_bundle.overall_quality, "component_count": len(claim_components)},
                output_data={"final_verdict": verdict, "bias_penalty": len(bias_indicators) * 0.05},
                confidence=confidence,
                reasoning="Combined multi-factor analysis with bias mitigation for final verdict"
            ))
            
            chain.overall_verdict = verdict
            chain.final_confidence = confidence
            chain.processing_time = time.time() - start_time
            
        except Exception as e:
            chain.uncertainty_factors.append(f"Processing error: {str(e)}")
            chain.overall_verdict = "ERROR"
            chain.final_confidence = 0.0
        
        return chain
    
    def _extract_verdict(self, llm_content: str) -> str:
        """Extract verdict from LLM response."""
        content_lower = llm_content.lower()
        if "verdict: true" in content_lower:
            return "TRUE"
        elif "verdict: false" in content_lower:
            return "FALSE"
        elif "verdict: uncertain" in content_lower:
            return "UNCERTAIN"
        else:
            return "UNCERTAIN"
    
    def _calculate_final_confidence(self, evidence: EvidenceBundle, llm_response: LLMResponse) -> float:
        """Calculate final confidence score using multi-factor analysis."""
        evidence_confidence = evidence.overall_quality
        llm_confidence = llm_response.confidence or 0.5
        
        # Factor in evidence consistency
        supporting_count = len(evidence.supporting_evidence)
        contradicting_count = len(evidence.contradicting_evidence)
        total_evidence = evidence.total_evidence_count
        
        if total_evidence > 0:
            evidence_consistency = abs(supporting_count - contradicting_count) / total_evidence
        else:
            evidence_consistency = 0.0
        
        # Factor in evidence quality distribution
        if total_evidence > 0:
            all_evidence = evidence.supporting_evidence + evidence.contradicting_evidence + evidence.neutral_evidence
            quality_variance = self._calculate_evidence_quality_variance(all_evidence)
            quality_penalty = min(quality_variance * 0.3, 0.2)  # Cap penalty at 0.2
        else:
            quality_penalty = 0.1
        
        # Weighted confidence calculation
        base_confidence = (evidence_confidence * 0.4) + (llm_confidence * 0.6)
        consistency_boost = evidence_consistency * 0.1
        final_confidence = base_confidence + consistency_boost - quality_penalty
        
        # Ensure confidence is within valid range [0.0, 1.0]
        return max(0.0, min(1.0, final_confidence))
    
    def _calculate_evidence_quality_variance(self, evidence_list: List[Evidence]) -> float:
        """Calculate variance in evidence quality scores."""
        if len(evidence_list) <= 1:
            return 0.0
        
        qualities = [evidence.credibility_score for evidence in evidence_list]
        mean_quality = sum(qualities) / len(qualities)
        variance = sum((q - mean_quality) ** 2 for q in qualities) / len(qualities)
        return variance
    
    def _analyze_claim_structure(self, claim: ProcessedClaim) -> List[str]:
        """Break down complex claims into verifiable components."""
        components = []
        text = claim.normalized_text
        
        # Look for compound statements (and, or, but)
        connectors = [" and ", " or ", " but ", " however ", " although ", " because "]
        
        # Split by connectors
        current_text = text
        for connector in connectors:
            if connector in current_text:
                parts = current_text.split(connector)
                components.extend([part.strip() for part in parts if part.strip()])
                break
        else:
            # No connectors found, treat as single component
            components.append(text.strip())
        
        # Filter out very short components (likely incomplete)
        meaningful_components = [comp for comp in components if len(comp.split()) >= 3]
        
        return meaningful_components if meaningful_components else [text.strip()]
    
    def _assess_uncertainty_factors(self, claim: ProcessedClaim, evidence: EvidenceBundle, llm_response: LLMResponse) -> List[str]:
        """Identify factors that contribute to uncertainty in verification."""
        factors = []
        
        # Evidence-based uncertainty factors
        if evidence.total_evidence_count == 0:
            factors.append("No evidence found for verification")
        elif evidence.total_evidence_count < 3:
            factors.append("Limited evidence available")
        
        if len(evidence.contradicting_evidence) > len(evidence.supporting_evidence):
            factors.append("More contradicting than supporting evidence")
        
        if evidence.overall_quality < 0.5:
            factors.append("Low overall evidence quality")
        
        # Claim complexity factors
        if claim.complexity == ClaimComplexity.COMPLEX:
            factors.append("High claim complexity requires careful analysis")
        
        # Domain-specific factors
        if claim.domain == "general":
            factors.append("General domain claims may lack specialized verification")
        
        # LLM confidence factors
        if llm_response.confidence and llm_response.confidence < 0.6:
            factors.append("Low LLM analysis confidence")
        
        # Content-based factors
        if any(word in claim.normalized_text for word in ["predict", "future", "will", "tomorrow", "next"]):
            factors.append("Predictive claims are inherently uncertain")
        
        if any(word in claim.normalized_text for word in ["always", "never", "all", "none", "every"]):
            factors.append("Absolute statements are difficult to verify completely")
        
        return factors
    
    def _detect_potential_biases(self, claim: ProcessedClaim, evidence: EvidenceBundle) -> List[str]:
        """Detect potential biases in claim verification process."""
        bias_indicators = []
        
        # Source diversity bias
        if evidence.total_evidence_count > 0:
            all_evidence = evidence.supporting_evidence + evidence.contradicting_evidence + evidence.neutral_evidence
            sources = set(ev.source for ev in all_evidence)
            if len(sources) < max(2, evidence.total_evidence_count // 2):
                bias_indicators.append("Limited source diversity may introduce bias")
        
        # Confirmation bias indicators
        supporting_count = len(evidence.supporting_evidence)
        contradicting_count = len(evidence.contradicting_evidence)
        if supporting_count > 0 and contradicting_count == 0:
            bias_indicators.append("Only supporting evidence found - potential confirmation bias")
        elif contradicting_count > 0 and supporting_count == 0:
            bias_indicators.append("Only contradicting evidence found - potential negative bias")
        
        # Quality bias
        if evidence.total_evidence_count > 1:
            all_evidence = evidence.supporting_evidence + evidence.contradicting_evidence + evidence.neutral_evidence
            high_quality_count = sum(1 for ev in all_evidence if ev.credibility_score > 0.8)
            if high_quality_count / len(all_evidence) < 0.5:
                bias_indicators.append("Majority of evidence from lower-quality sources")
        
        # Domain expertise bias
        specialized_domains = ["science", "health", "economics", "law"]
        if claim.domain in specialized_domains and claim.complexity == ClaimComplexity.COMPLEX:
            bias_indicators.append(f"Complex {claim.domain} claim may require specialized expertise")
        
        # Temporal bias for news claims
        if claim.domain == "news" and not any(word in claim.normalized_text for word in ["today", "yesterday", "recent"]):
            bias_indicators.append("News claims without temporal context may be outdated")
        
        # Language bias indicators
        emotional_words = ["amazing", "terrible", "shocking", "outrageous", "incredible", "unbelievable"]
        if any(word in claim.normalized_text for word in emotional_words):
            bias_indicators.append("Emotionally charged language may indicate bias")
        
        return bias_indicators


class OutputGenerator:
    """Generates final verification results."""
    
    def format_result(self, claim: ProcessedClaim, chain: VerificationChain, agent_id: str) -> VerificationResult:
        """Format the verification chain into a VerificationResult."""
        
        # Compile evidence sources
        sources = []
        evidence_list = []
        
        for step in chain.steps:
            if step.step_type == "evidence_gathering" and "sources" in step.input_data:
                sources.extend(step.input_data["sources"])
            
            evidence_list.append(f"{step.step_type}: {step.reasoning}")
        
        # Generate reasoning chain
        reasoning_parts = []
        for i, step in enumerate(chain.steps, 1):
            reasoning_parts.append(f"{i}. {step.reasoning} (confidence: {step.confidence:.2f})")
        
        reasoning = " | ".join(reasoning_parts)
        
        return VerificationResult(
            claim=claim.original_text,
            verdict=chain.overall_verdict,
            confidence=chain.final_confidence,
            reasoning=reasoning,
            sources=sources,
            evidence=evidence_list,
            metadata={
                "processing_time": chain.processing_time,
                "steps_count": len(chain.steps),
                "domain": claim.domain,
                "complexity": claim.complexity.value,
                "uncertainty_factors": chain.uncertainty_factors
            },
            agent_id=agent_id
        )


class SimpleAgent(BaseAgent):
    """
    Concrete implementation of BaseAgent demonstrating the core architecture.
    
    This agent implements all the components described in the core agent architecture:
    - Input Processor
    - State Manager
    - LLM Interaction
    - Evidence Engine
    - Verification Logic
    - Output Generator
    """
    
    def __init__(self, agent_id: str = None, config: Optional[AgentConfig] = None):
        super().__init__(agent_id)
        
        self.config = config or AgentConfig(agent_id=self.agent_id)
        
        # Initialize components
        self.input_processor = InputProcessor()
        self.state_manager = StateManager()
        self.llm_interaction = SimpleLLMInteraction()
        self.evidence_engine = SimpleEvidenceEngine()
        self.verification_logic = VerificationLogic(self.llm_interaction, self.evidence_engine)
        self.output_generator = OutputGenerator()
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
    
    def verify(self, claim: str) -> VerificationResult:
        """
        Verify a claim using the complete agent architecture pipeline.
        
        This method orchestrates all components to process the claim from
        input to final verification result.
        """
        start_time = time.time()
        
        try:
            # Step 1: Input Processing
            processed_claim = self.input_processor.parse_claim(claim)
            
            # Step 2: State Management
            session_id = self.state_manager.initialize_session(self.agent_id, processed_claim)
            state = self.state_manager.get_session(session_id)
            
            # Step 3: Core Verification
            verification_chain = self.verification_logic.verify_claim(processed_claim, state)
            
            # Step 4: Output Generation
            result = self.output_generator.format_result(
                processed_claim, 
                verification_chain, 
                self.agent_id
            )
            
            # Step 5: State Persistence
            self.state_manager.store_verification(session_id, result)
            self.state_manager.cleanup_session(session_id)
            
            # Update performance metrics
            self.metrics.verification_time = time.time() - start_time
            self.metrics.api_calls_made = 1  # Simulated LLM call
            self.metrics.tokens_used = sum(step.output_data.get("tokens_used", 0) 
                                         for step in verification_chain.steps 
                                         if isinstance(step.output_data, dict))
            
            return result
            
        except Exception as e:
            # Error handling
            error_result = VerificationResult(
                claim=claim,
                verdict="ERROR",
                confidence=0.0,
                reasoning=f"Verification failed: {str(e)}",
                sources=[],
                evidence=[],
                metadata={"error": str(e), "error_type": type(e).__name__},
                agent_id=self.agent_id
            )
            
            self.metrics.verification_time = time.time() - start_time
            return error_result
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        return self.metrics
    
    def get_domain_expertise(self) -> Dict[str, float]:
        """Get current domain expertise scores."""
        # Aggregate from recent sessions
        expertise = {}
        for session in self.state_manager.sessions.values():
            for domain, score in session.domain_expertise.items():
                if domain not in expertise:
                    expertise[domain] = []
                expertise[domain].append(score)
        
        # Calculate averages
        return {domain: sum(scores) / len(scores) 
                for domain, scores in expertise.items()}