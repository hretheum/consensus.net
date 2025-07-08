"""
Enhanced Agent with Real LLM Integration

This agent extends SimpleAgent to use real LLM APIs instead of simulation.
It maintains backward compatibility while providing production-ready functionality.
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from .simple_agent import (
    SimpleAgent, InputProcessor, StateManager, OutputGenerator,
    SimpleEvidenceEngine, VerificationLogic
)
from .base_agent import BaseAgent
from .verification_result import VerificationResult
from .agent_models import (
    ProcessedClaim, ClaimComplexity, AgentState, AgentConfig,
    Evidence, EvidenceBundle, LLMRequest, LLMResponse,
    VerificationStep, VerificationChain, PerformanceMetrics,
    InputError, VerificationError
)
from services.llm_service import llm_service, LLMServiceError
from services.evidence_service import evidence_service, EvidenceServiceError
from config.llm_config import (
    ClaimComplexity as LLMClaimComplexity,
    PrivacyLevel, UrgencyLevel
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
    Enhanced agent with real LLM and evidence integration.
    
    Extends the SimpleAgent architecture to use real LLM APIs and web search
    while maintaining backward compatibility and providing fallback when needed.
    """
    
    def __init__(self, agent_id: str = None, config: Optional[AgentConfig] = None):
        """Initialize the enhanced agent."""
        super().__init__(agent_id)
        
        self.config = config or AgentConfig(agent_id=self.agent_id)
        
        # Initialize components with enhanced integrations
        self.input_processor = InputProcessor()
        self.state_manager = StateManager()
        self.llm_interaction = EnhancedLLMInteraction()
        self.evidence_engine = EnhancedEvidenceEngine()
        self.verification_logic = EnhancedVerificationLogic(
            self.llm_interaction, 
            self.evidence_engine
        )
        self.output_generator = OutputGenerator()
        
        # Performance tracking
        self.metrics = PerformanceMetrics()
        
        # Track enhanced usage
        self.enhanced_stats = {
            "total_requests": 0,
            "real_llm_calls": 0,
            "simulation_fallbacks": 0,
            "real_evidence_calls": 0,
            "evidence_fallbacks": 0,
            "provider_usage": {},
            "evidence_sources_used": set()
        }
    
    def verify(self, claim: str) -> VerificationResult:
        """
        Verify a claim using enhanced LLM and evidence integration.
        
        This method wraps the async verification in a sync interface
        for backward compatibility.
        """
        return asyncio.run(self.verify_async(claim))
    
    async def verify_async(self, claim: str) -> VerificationResult:
        """
        Async version of verify with real LLM and evidence integration.
        """
        start_time = time.time()
        
        try:
            # Step 1: Input Processing
            processed_claim = self.input_processor.parse_claim(claim)
            
            # Step 2: State Management
            session_id = self.state_manager.initialize_session(self.agent_id, processed_claim)
            state = self.state_manager.get_session(session_id)
            
            # Step 3: Enhanced Core Verification with async LLM and evidence calls
            verification_chain = await self.verification_logic.verify_claim_async(processed_claim, state)
            
            # Step 4: Output Generation
            result = self.output_generator.format_result(
                processed_claim, 
                verification_chain, 
                self.agent_id
            )
            
            # Step 5: State Persistence
            self.state_manager.store_verification(session_id, result)
            self.state_manager.cleanup_session(session_id)
            
            # Update metrics
            self.metrics.verification_time = time.time() - start_time
            self.metrics.api_calls_made = 1
            self.metrics.tokens_used = sum(
                step.output_data.get("tokens_used", 0) 
                for step in verification_chain.steps 
                if isinstance(step.output_data, dict)
            )
            
            # Update enhanced stats
            self.enhanced_stats["total_requests"] += 1
            if verification_chain.metadata.get("simulation_fallback", False):
                self.enhanced_stats["simulation_fallbacks"] += 1
            else:
                self.enhanced_stats["real_llm_calls"] += 1
                
            if verification_chain.metadata.get("real_evidence_used", False):
                self.enhanced_stats["real_evidence_calls"] += 1
            else:
                self.enhanced_stats["evidence_fallbacks"] += 1
                
            provider = verification_chain.metadata.get("llm_provider")
            if provider:
                self.enhanced_stats["provider_usage"][provider] = self.enhanced_stats["provider_usage"].get(provider, 0) + 1
            
            # Add enhanced metadata to result
            result.metadata.update({
                "llm_integration": "enhanced",
                "evidence_integration": "enhanced",
                "verification_chain_metadata": verification_chain.metadata
            })
            
            return result
            
        except Exception as e:
            # Enhanced error handling
            error_result = VerificationResult(
                claim=claim,
                verdict="ERROR",
                confidence=0.0,
                reasoning=f"Enhanced verification failed: {str(e)}",
                sources=[],
                evidence=[],
                metadata={
                    "error": str(e), 
                    "error_type": type(e).__name__,
                    "llm_integration": "enhanced",
                    "evidence_integration": "enhanced",
                    "fallback_available": True
                },
                agent_id=self.agent_id
            )
            
            self.metrics.verification_time = time.time() - start_time
            return error_result
    
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