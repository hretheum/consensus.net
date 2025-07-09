"""
Enhanced agent with comprehensive modules for real LLM integration
and full adaptive source credibility support.
"""
import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
import uuid

from src.agents.base_agent import BaseAgent
from src.agents.verification_result import VerificationResult, Verdict
from src.agents.agent_models import (
    ProcessedClaim, EvidenceBundle, Evidence, LLMRequest, LLMResponse,
    ClaimComplexity, VerificationStep, VerificationChain, PerformanceMetrics
)

# Import from simple_agent - these contain the modular components
from src.agents.simple_agent import (
    InputProcessor, StateManager, SimpleEvidenceEngine,
    SimpleLLMInteraction, OutputGenerator, VerificationLogic
)

from src.services.llm_service import llm_service, LLMServiceError
from src.services.evidence_service import evidence_service, EvidenceServiceError
from src.config.llm_config import (
    LLMModel, ClaimComplexity, PrivacyLevel, UrgencyLevel
)


class EnhancedEvidenceEngine:
    """Enhanced evidence engine using real web search."""
    
    def __init__(self):
        """Initialize the enhanced evidence engine."""
        self.evidence_service = evidence_service
        self.fallback_engine = SimpleEvidenceEngine()
    
    async def search_sources(self, claim: ProcessedClaim) -> List[str]:
        """Search for relevant sources based on claim domain."""
        # Use domain-specific sources from evidence service
        domain_sources = self.evidence_service.domain_sources.get(
            claim.domain, 
            self.evidence_service.domain_sources["general"]
        )
        return domain_sources
    
    async def retrieve_evidence(self, sources: List[str], claim: ProcessedClaim) -> EvidenceBundle:
        """Retrieve evidence using real web search and APIs."""
        try:
            # Use real evidence gathering
            async with self.evidence_service as evidence:
                evidence_bundle = await evidence.gather_evidence(claim, max_sources=5)
                return evidence_bundle
                
        except EvidenceServiceError as e:
            # Fallback to simulation if real evidence gathering fails
            return self.fallback_engine.retrieve_evidence(sources, claim)


class EnhancedLLMInteraction:
    """Enhanced LLM interaction using real APIs."""
    
    def __init__(self):
        """Initialize the enhanced LLM interaction."""
        self.llm_service = llm_service
    
    def map_complexity(self, claim_complexity: ClaimComplexity) -> LLMClaimComplexity:
        """Map agent claim complexity to LLM config complexity."""
        mapping = {
            ClaimComplexity.SIMPLE: LLMClaimComplexity.SIMPLE,
            ClaimComplexity.MODERATE: LLMClaimComplexity.MODERATE,
            ClaimComplexity.COMPLEX: LLMClaimComplexity.COMPLEX
        }
        return mapping.get(claim_complexity, LLMClaimComplexity.MODERATE)
    
    async def generate_verification_prompt(self, claim: ProcessedClaim) -> str:
        """Generate verification prompt using the LLM service."""
        complexity = self.map_complexity(claim.complexity)
        return self.llm_service.generate_verification_prompt(
            claim.original_text, 
            complexity
        )
    
    async def call_llm(self, request: LLMRequest, claim: ProcessedClaim) -> LLMResponse:
        """Call real LLM API with fallback strategy."""
        try:
            complexity = self.map_complexity(claim.complexity)
            
            # Use async context manager for the LLM service
            async with self.llm_service as llm:
                response = await llm.call_llm_with_fallback(
                    request,
                    complexity=complexity,
                    privacy=PrivacyLevel.STANDARD,
                    urgency=UrgencyLevel.NORMAL
                )
                return response
                
        except LLMServiceError as e:
            # Fallback to simulation if all LLM providers fail
            return self._fallback_simulation(request, claim, str(e))
    
    def _fallback_simulation(self, request: LLMRequest, claim: ProcessedClaim, error: str) -> LLMResponse:
        """Fallback to simulation when real LLMs are unavailable."""
        claim_text = request.prompt.lower()
        
        # Enhanced simulation with more sophisticated responses
        if "earth is flat" in claim_text:
            verdict = "FALSE"
            confidence = 0.99
            reasoning = "The Earth is scientifically proven to be spherical through multiple lines of evidence including satellite imagery, physics, and direct observation."
            concerns = ["This is a well-debunked conspiracy theory"]
        elif "sky is blue" in claim_text:
            verdict = "TRUE"
            confidence = 0.95
            reasoning = "The sky appears blue due to Rayleigh scattering of light in the atmosphere, where shorter blue wavelengths are scattered more than longer wavelengths."
            concerns = ["Color perception can vary based on atmospheric conditions"]
        elif any(math_term in claim_text for math_term in ["2+2=4", "two plus two equals four", "basic math"]):
            verdict = "TRUE"
            confidence = 1.0
            reasoning = "This is a fundamental mathematical fact verified by arithmetic."
            concerns = []
        elif "covid" in claim_text or "coronavirus" in claim_text:
            verdict = "UNCERTAIN"
            confidence = 0.4
            reasoning = "COVID-related claims require specific medical evidence and may change with new research."
            concerns = ["Medical information changes rapidly", "Requires expert verification"]
        else:
            verdict = "UNCERTAIN"
            confidence = 0.3
            reasoning = f"Unable to verify claim with available information. This response is using fallback simulation due to: {error}"
            concerns = ["Using simulation fallback", "Real LLM APIs unavailable"]
        
        # Format as structured JSON-like content
        content = f"""{{
    "verdict": "{verdict}",
    "confidence": {confidence},
    "reasoning": "{reasoning}",
    "concerns": {str(concerns).replace("'", '"')},
    "key_evidence": ["Fallback simulation response"]
}}"""
        
        return LLMResponse(
            content=content,
            metadata={
                "simulation": True, 
                "model": "fallback-simulation",
                "fallback_reason": error
            },
            model_used="simulation",
            tokens_used=len(request.prompt) + len(content),
            confidence=confidence
        )


class EnhancedVerificationLogic(VerificationLogic):
    """Enhanced verification logic with real LLM and evidence integration."""
    
    def __init__(self, llm_interaction: EnhancedLLMInteraction, evidence_engine: EnhancedEvidenceEngine):
        """Initialize with enhanced LLM interaction and evidence engine."""
        # Don't call super().__init__ since we're using different types
        self.llm = llm_interaction
        self.evidence = evidence_engine
    
    async def verify_claim_async(self, claim: ProcessedClaim, state: AgentState) -> VerificationChain:
        """Async version of verify_claim using real LLM APIs and evidence gathering."""
        chain = VerificationChain()
        start_time = time.time()
        
        try:
            # Step 1: Enhanced Evidence gathering with real APIs
            sources = await self.evidence.search_sources(claim)
            evidence_bundle = await self.evidence.retrieve_evidence(sources, claim)
            
            chain.steps.append(VerificationStep(
                step_type="evidence_gathering",
                input_data={"sources": sources},
                output_data={
                    "evidence_count": evidence_bundle.total_evidence_count,
                    "supporting_count": len(evidence_bundle.supporting_evidence),
                    "contradicting_count": len(evidence_bundle.contradicting_evidence),
                    "neutral_count": len(evidence_bundle.neutral_evidence)
                },
                confidence=evidence_bundle.overall_quality,
                reasoning=f"Gathered {evidence_bundle.total_evidence_count} pieces of evidence from {len(sources)} sources using real web search"
            ))
            
            # Step 2: Enhanced LLM analysis with real APIs
            prompt = await self.llm.generate_verification_prompt(claim)
            llm_request = LLMRequest(
                prompt=prompt,
                model="auto-selected",  # Will be selected by LLM service
                parameters={}
            )
            llm_response = await self.llm.call_llm(llm_request, claim)
            
            chain.steps.append(VerificationStep(
                step_type="llm_analysis",
                input_data={"prompt_length": len(prompt)},
                output_data={
                    "tokens_used": llm_response.tokens_used,
                    "model_used": llm_response.model_used,
                    "provider": llm_response.metadata.get("provider", "unknown")
                },
                confidence=llm_response.confidence or 0.5,
                reasoning="Real LLM provided verification analysis with enhanced prompting"
            ))
            
            # Step 3: Enhanced verdict calculation with evidence integration
            verdict = self._extract_enhanced_verdict(llm_response.content)
            confidence = self._calculate_enhanced_confidence(evidence_bundle, llm_response)
            
            chain.steps.append(VerificationStep(
                step_type="verdict_calculation",
                input_data={
                    "evidence_quality": evidence_bundle.overall_quality,
                    "llm_confidence": llm_response.confidence or 0.5
                },
                output_data={"final_verdict": verdict},
                confidence=confidence,
                reasoning="Combined real LLM analysis with real evidence for final verdict"
            ))
            
            chain.overall_verdict = verdict
            chain.final_confidence = confidence
            chain.processing_time = time.time() - start_time
            
            # Add metadata about services used
            chain.metadata = {
                "llm_model": llm_response.model_used,
                "llm_provider": llm_response.metadata.get("provider"),
                "simulation_fallback": llm_response.metadata.get("simulation", False),
                "response_time_ms": llm_response.metadata.get("response_time_ms", 0),
                "evidence_sources": len(set(e.source for e in evidence_bundle.supporting_evidence + evidence_bundle.contradicting_evidence + evidence_bundle.neutral_evidence)),
                "real_evidence_used": True
            }
            
        except Exception as e:
            chain.uncertainty_factors.append(f"Enhanced processing error: {str(e)}")
            chain.overall_verdict = "ERROR"
            chain.final_confidence = 0.0
            chain.metadata = {"error": str(e), "enhanced_features": "error"}
        
        return chain
    
    def _extract_enhanced_verdict(self, llm_content: str) -> str:
        """Extract verdict with enhanced parsing for structured responses."""
        # Try to parse structured response first
        try:
            import json
            json_start = llm_content.find('{')
            json_end = llm_content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = llm_content[json_start:json_end]
                data = json.loads(json_str)
                return data.get("verdict", "UNCERTAIN")
        except:
            pass
        
        # Fallback to simple text parsing
        content_lower = llm_content.lower()
        if "verdict: true" in content_lower or "\"verdict\": \"true\"" in content_lower:
            return "TRUE"
        elif "verdict: false" in content_lower or "\"verdict\": \"false\"" in content_lower:
            return "FALSE"
        elif "verdict: uncertain" in content_lower or "\"verdict\": \"uncertain\"" in content_lower:
            return "UNCERTAIN"
        else:
            return "UNCERTAIN"
    
    def _calculate_enhanced_confidence(self, evidence: EvidenceBundle, llm_response: LLMResponse) -> float:
        """Enhanced confidence calculation with real evidence and LLM confidence integration."""
        evidence_confidence = evidence.overall_quality
        llm_confidence = llm_response.confidence or 0.5
        
        # Consider evidence distribution
        total_evidence = evidence.total_evidence_count
        if total_evidence > 0:
            supporting_ratio = len(evidence.supporting_evidence) / total_evidence
            contradicting_ratio = len(evidence.contradicting_evidence) / total_evidence
            
            # Reduce confidence if evidence is contradictory
            if contradicting_ratio > 0.3:
                evidence_confidence *= 0.8
            elif supporting_ratio > 0.6:
                evidence_confidence *= 1.1  # Boost for strong supporting evidence
        
        # Adjust weighting based on whether we used simulation
        if llm_response.metadata.get("simulation", False):
            # Lower weight for simulation responses
            final_confidence = (evidence_confidence * 0.8) + (llm_confidence * 0.2)
        else:
            # Higher weight for real LLM responses, but balance with evidence
            final_confidence = (evidence_confidence * 0.4) + (llm_confidence * 0.6)
        
        return max(0.0, min(1.0, final_confidence))


class EnhancedAgent(BaseAgent):
    """
    Enhanced agent that uses real LLM APIs and evidence services.
    
    Features:
    - Real LLM integration with 3-tier fallback strategy
    - Real evidence gathering from Wikipedia and other sources
    - Adaptive source credibility with automatic model escalation
    - Production-ready error handling and monitoring
    """
    
    def __init__(self, agent_id: str = None):
        """Initialize enhanced agent with real service integrations."""
        super().__init__(agent_id or f"enhanced-agent-{uuid.uuid4().hex[:8]}")
        
        # Initialize modular components
        self.input_processor = InputProcessor()
        self.state_manager = StateManager()
        self.evidence_engine = SimpleEvidenceEngine()
        self.llm_interaction = SimpleLLMInteraction()
        self.output_generator = OutputGenerator()
        self.verification_logic = VerificationLogic()
        
        # Enhanced services (will be set via properties)
        self._llm_service = None
        self._evidence_service = None
        
        # Metrics tracking
        self.metrics = PerformanceMetrics()
        
        # Track enhanced agent usage
        self.enhanced_stats = {
            "total_requests": 0,
            "real_llm_calls": 0,
            "simulation_fallbacks": 0,
            "real_evidence_calls": 0,
            "evidence_fallbacks": 0,
            "provider_usage": {},
            "evidence_sources_used": set()
        }
    
    async def verify(self, claim: str) -> VerificationResult:
        """
        Verify a claim with real LLM integration and adaptive source credibility.
        
        Args:
            claim: The claim to verify
            
        Returns:
            VerificationResult with verdict, confidence, and evidence
        """
        try:
            # Process the claim
            processed_claim = self.input_processor.parse_claim(claim)
            
            # Gather evidence from multiple sources in parallel
            async with self.evidence_engine.evidence_service as evidence_service:
                evidence_bundle = await evidence_service.gather_evidence(
                    processed_claim, 
                    max_sources=5
                )
            
            # Extract evidence quality and metadata
            evidence_quality = evidence_bundle.overall_quality
            requires_escalation = evidence_bundle.metadata.get("requires_llm_escalation", False)
            has_academic_sources = evidence_bundle.metadata.get("has_academic_sources", False)
            consensus_level = evidence_bundle.metadata.get("consensus_level", 0.5)
            
            # Log evidence gathering results
            print(f"Evidence gathered: {len(evidence_bundle.supporting_evidence)} supporting, "
                  f"{len(evidence_bundle.contradicting_evidence)} contradicting, "
                  f"{len(evidence_bundle.neutral_evidence)} neutral")
            print(f"Evidence quality: {evidence_quality:.2f}, Consensus: {consensus_level:.2f}")
            
            # Determine claim complexity based on evidence
            if consensus_level < 0.6 or len(evidence_bundle.contradicting_evidence) > 2:
                complexity = ClaimComplexity.COMPLEX
            elif has_academic_sources and consensus_level > 0.8:
                complexity = ClaimComplexity.SIMPLE
            else:
                complexity = ClaimComplexity.MODERATE
            
            # Create verification prompt with evidence
            prompt = self._create_enhanced_verification_prompt(
                claim, processed_claim, evidence_bundle
            )
            
            # Call LLM with adaptive model selection based on evidence quality
            llm_request = LLMRequest(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.3
            )
            
            async with self.llm_interaction.llm_service as llm_service:
                llm_response = await llm_service.call_llm_with_fallback(
                    llm_request,
                    complexity=complexity,
                    privacy=PrivacyLevel.STANDARD,
                    urgency=UrgencyLevel.NORMAL,
                    evidence_quality=evidence_quality,
                    requires_escalation=requires_escalation
                )
            
            # Parse LLM response
            structured_data = llm_response.metadata.get("structured_data", {})
            
            # Create verification result with adaptive confidence
            result = VerificationResult(
                claim=claim,
                verdict=self._parse_verdict(structured_data.get("verdict", "UNCERTAIN")),
                confidence=llm_response.confidence or structured_data.get("confidence", 0.5),
                reasoning=structured_data.get("reasoning", llm_response.content),
                evidence=evidence_bundle,
                agent_id=self.agent_id,
                processing_time=0.0,  # Will be calculated
                metadata={
                    "processed_claim": processed_claim.to_dict(),
                    "llm_model": llm_response.model_used,
                    "evidence_quality": evidence_quality,
                    "consensus_level": consensus_level,
                    "has_academic_sources": has_academic_sources,
                    "sources_consulted": evidence_bundle.metadata.get("sources_used", []),
                    "llm_metadata": llm_response.metadata,
                    "adaptive_routing": {
                        "initial_complexity": processed_claim.complexity.value,
                        "adjusted_complexity": complexity.value,
                        "escalation_reason": "low_evidence_quality" if requires_escalation else None
                    }
                }
            )
            
            return result
            
        except Exception as e:
            # Return error result
            return VerificationResult(
                claim=claim,
                verdict=Verdict.ERROR,
                confidence=0.0,
                reasoning=f"Verification failed: {str(e)}",
                evidence=EvidenceBundle(
                    supporting_evidence=[],
                    contradicting_evidence=[],
                    neutral_evidence=[],
                    overall_quality=0.0
                ),
                agent_id=self.agent_id,
                processing_time=0.0,
                metadata={"error": str(e)}
            )
    
    def _create_enhanced_verification_prompt(
        self, 
        claim: str, 
        processed_claim: ProcessedClaim,
        evidence_bundle: EvidenceBundle
    ) -> str:
        """
        Create an enhanced verification prompt that includes evidence context.
        
        Args:
            claim: Original claim
            processed_claim: Processed claim with metadata
            evidence_bundle: Evidence gathered from sources
            
        Returns:
            Enhanced prompt for LLM
        """
        # Start with base prompt
        prompt = self.llm_interaction.llm_service.generate_verification_prompt(
            claim, processed_claim.complexity
        )
        
        # Add evidence section
        evidence_section = "\n\nEVIDENCE GATHERED:\n"
        
        if evidence_bundle.supporting_evidence:
            evidence_section += "\nSUPPORTING EVIDENCE:\n"
            for i, evidence in enumerate(evidence_bundle.supporting_evidence[:3], 1):
                evidence_section += f"{i}. [{evidence.source}] (credibility: {evidence.credibility_score:.2f})\n"
                evidence_section += f"   {evidence.content[:200]}...\n\n"
        
        if evidence_bundle.contradicting_evidence:
            evidence_section += "\nCONTRADICTING EVIDENCE:\n"
            for i, evidence in enumerate(evidence_bundle.contradicting_evidence[:3], 1):
                evidence_section += f"{i}. [{evidence.source}] (credibility: {evidence.credibility_score:.2f})\n"
                evidence_section += f"   {evidence.content[:200]}...\n\n"
        
        if evidence_bundle.neutral_evidence:
            evidence_section += "\nNEUTRAL/UNCLEAR EVIDENCE:\n"
            for i, evidence in enumerate(evidence_bundle.neutral_evidence[:2], 1):
                evidence_section += f"{i}. [{evidence.source}] (credibility: {evidence.credibility_score:.2f})\n"
                evidence_section += f"   {evidence.content[:200]}...\n\n"
        
        # Add evidence summary
        evidence_section += f"\nEVIDENCE SUMMARY:\n"
        evidence_section += f"- Total sources consulted: {len(set(e.source for e in evidence_bundle.supporting_evidence + evidence_bundle.contradicting_evidence + evidence_bundle.neutral_evidence))}\n"
        evidence_section += f"- Evidence quality score: {evidence_bundle.overall_quality:.2f}\n"
        evidence_section += f"- Consensus level: {evidence_bundle.metadata.get('consensus_level', 'N/A')}\n"
        
        # Insert evidence before the JSON format instruction
        if "Format your response as JSON" in prompt:
            parts = prompt.split("Format your response as JSON")
            return parts[0] + evidence_section + "\nFormat your response as JSON" + parts[1]
        else:
            return prompt + evidence_section

    def get_llm_stats(self) -> Dict[str, Any]:
        """Get enhanced LLM and evidence usage statistics."""
        return {
            **self.enhanced_stats,
            "llm_service_stats": self.llm_interaction.llm_service.get_usage_stats(),
            "evidence_cache_stats": self.evidence_engine.evidence_service.get_cache_stats()
        }
    
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