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
            # Step 1: Evidence gathering
            sources = self.evidence.search_sources(claim)
            evidence_bundle = self.evidence.retrieve_evidence(sources, claim)
            
            chain.steps.append(VerificationStep(
                step_type="evidence_gathering",
                input_data={"sources": sources},
                output_data={"evidence_count": evidence_bundle.total_evidence_count},
                confidence=evidence_bundle.overall_quality,
                reasoning=f"Gathered {evidence_bundle.total_evidence_count} pieces of evidence"
            ))
            
            # Step 2: LLM analysis
            prompt = self.llm.generate_verification_prompt(claim)
            llm_request = LLMRequest(
                prompt=prompt,
                model="gpt-4.1-mini",  # Updated to correct 2025 model
                parameters={}
            )
            llm_response = self.llm.call_llm(llm_request)
            
            chain.steps.append(VerificationStep(
                step_type="llm_analysis",
                input_data={"prompt_length": len(prompt)},
                output_data={"tokens_used": llm_response.tokens_used},
                confidence=llm_response.confidence or 0.5,
                reasoning="LLM provided verification analysis"
            ))
            
            # Step 3: Final verdict calculation
            verdict = self._extract_verdict(llm_response.content)
            confidence = self._calculate_final_confidence(evidence_bundle, llm_response)
            
            chain.steps.append(VerificationStep(
                step_type="verdict_calculation",
                input_data={"evidence_quality": evidence_bundle.overall_quality},
                output_data={"final_verdict": verdict},
                confidence=confidence,
                reasoning="Combined evidence and LLM analysis for final verdict"
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
        """Calculate final confidence score."""
        evidence_confidence = evidence.overall_quality
        llm_confidence = llm_response.confidence or 0.5
        
        # Simple weighted average
        return (evidence_confidence * 0.4) + (llm_confidence * 0.6)


class OutputGenerator:
    """
    Generates final verification results with comprehensive formatting and delivery options.
    
    Supports multiple output formats (text, JSON, structured) and delivery channels
    (API response, message queue) as specified in the core agent architecture.
    """
    
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
        reasoning = self.generate_reasoning_chain(chain.steps)
        
        # Normalize confidence to valid range before creating result
        normalized_confidence = max(0.0, min(1.0, chain.final_confidence))
        
        result = VerificationResult(
            claim=claim.original_text,
            verdict=chain.overall_verdict,
            confidence=normalized_confidence,
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
        
        # Validate result quality and add warning if needed
        if not self.validate_result_quality(result):
            # Add warning to metadata if quality is insufficient
            result.metadata["quality_warning"] = "Result may have incomplete or low-quality information"
        
        # Add warning if confidence was normalized
        if chain.final_confidence != normalized_confidence:
            result.metadata["confidence_normalized"] = f"Original confidence {chain.final_confidence} was normalized to {normalized_confidence}"
        
        return result
    
    def compile_evidence_summary(self, evidence: EvidenceBundle) -> List[str]:
        """Organize supporting/contradicting evidence into a structured summary."""
        summary = []
        
        if evidence.supporting_evidence:
            summary.append(f"Supporting Evidence ({len(evidence.supporting_evidence)} items):")
            for i, ev in enumerate(evidence.supporting_evidence, 1):
                summary.append(f"  {i}. {ev.content[:100]}{'...' if len(ev.content) > 100 else ''} (credibility: {ev.credibility_score:.2f})")
        
        if evidence.contradicting_evidence:
            summary.append(f"Contradicting Evidence ({len(evidence.contradicting_evidence)} items):")
            for i, ev in enumerate(evidence.contradicting_evidence, 1):
                summary.append(f"  {i}. {ev.content[:100]}{'...' if len(ev.content) > 100 else ''} (credibility: {ev.credibility_score:.2f})")
        
        if evidence.neutral_evidence:
            summary.append(f"Neutral Evidence ({len(evidence.neutral_evidence)} items):")
            for i, ev in enumerate(evidence.neutral_evidence, 1):
                summary.append(f"  {i}. {ev.content[:100]}{'...' if len(ev.content) > 100 else ''} (credibility: {ev.credibility_score:.2f})")
        
        summary.append(f"Overall Evidence Quality: {evidence.overall_quality:.2f}")
        
        return summary
    
    def generate_reasoning_chain(self, steps: List[VerificationStep]) -> str:
        """Document the complete verification process in a readable format."""
        reasoning_parts = []
        for i, step in enumerate(steps, 1):
            reasoning_parts.append(f"{i}. {step.reasoning} (confidence: {step.confidence:.2f})")
        
        return " | ".join(reasoning_parts)
    
    def handle_verification_errors(self, error: Exception) -> VerificationResult:
        """Manage and report verification failures with appropriate error formatting."""
        error_type = type(error).__name__
        error_message = str(error)
        
        return VerificationResult(
            claim="[Error during verification]",
            verdict="ERROR",
            confidence=0.0,
            reasoning=f"Verification failed due to {error_type}: {error_message}",
            sources=[],
            evidence=[f"Error: {error_message}"],
            metadata={
                "error_type": error_type,
                "error_message": error_message,
                "processing_time": 0.0,
                "steps_count": 0
            },
            agent_id="error_handler"
        )
    
    def validate_result_quality(self, result: VerificationResult) -> bool:
        """Validate result completeness and consistency."""
        # Check for basic completeness
        if not result.claim or not result.verdict or not result.reasoning:
            return False
        
        # Check confidence is within valid range
        if not (0.0 <= result.confidence <= 1.0):
            return False
        
        # Check verdict is valid
        valid_verdicts = {"TRUE", "FALSE", "UNCERTAIN", "ERROR"}
        if result.verdict not in valid_verdicts:
            return False
        
        # Check reasoning has sufficient detail (basic heuristic)
        if len(result.reasoning) < 10:
            return False
        
        return True
    
    # Output Format Methods
    def to_text_format(self, result: VerificationResult, detailed: bool = False) -> str:
        """Convert VerificationResult to human-readable text format."""
        text_parts = [
            f"CLAIM: {result.claim}",
            f"VERDICT: {result.verdict}",
            f"CONFIDENCE: {result.confidence:.2%}",
            f"REASONING: {result.reasoning}"
        ]
        
        if detailed:
            if result.sources:
                text_parts.append(f"SOURCES: {', '.join(result.sources)}")
            
            if result.evidence:
                text_parts.append("EVIDENCE:")
                for i, evidence in enumerate(result.evidence, 1):
                    text_parts.append(f"  {i}. {evidence}")
            
            if result.metadata:
                text_parts.append("METADATA:")
                for key, value in result.metadata.items():
                    text_parts.append(f"  {key}: {value}")
        
        text_parts.append(f"Verified at: {result.timestamp.isoformat()}")
        if result.agent_id:
            text_parts.append(f"Agent ID: {result.agent_id}")
        
        return "\n".join(text_parts)
    
    def to_json_format(self, result: VerificationResult, pretty: bool = False) -> str:
        """Convert VerificationResult to JSON format."""
        import json
        
        json_data = result.model_dump()  # Updated Pydantic method
        
        if pretty:
            return json.dumps(json_data, indent=2, default=str)
        else:
            return json.dumps(json_data, default=str)
    
    def to_structured_format(self, result: VerificationResult) -> Dict[str, Any]:
        """Convert VerificationResult to structured dictionary format for API responses."""
        return {
            "status": "success" if result.verdict != "ERROR" else "error",
            "data": {
                "claim": result.claim,
                "verdict": result.verdict,
                "confidence": result.confidence,
                "reasoning": result.reasoning,
                "sources": result.sources,
                "evidence_count": len(result.evidence),
                "processing_metadata": {
                    "timestamp": result.timestamp.isoformat(),
                    "agent_id": result.agent_id,
                    **result.metadata
                }
            }
        }
    
    # Delivery Channel Methods
    def format_for_api_response(self, result: VerificationResult, format_type: str = "json") -> Dict[str, Any]:
        """Format result for API response delivery."""
        if format_type.lower() == "json":
            return {
                "success": True,
                "result": result.model_dump(),
                "format": "json",
                "timestamp": result.timestamp.isoformat()
            }
        elif format_type.lower() == "text":
            return {
                "success": True,
                "result": self.to_text_format(result, detailed=True),
                "format": "text",
                "timestamp": result.timestamp.isoformat()
            }
        else:
            return {
                "success": True,
                "result": self.to_structured_format(result),
                "format": "structured",
                "timestamp": result.timestamp.isoformat()
            }
    
    def format_for_message_queue(self, result: VerificationResult, queue_type: str = "standard") -> Dict[str, Any]:
        """Format result for message queue delivery."""
        base_message = {
            "message_type": "verification_result",
            "timestamp": result.timestamp.isoformat(),
            "agent_id": result.agent_id,
            "claim_id": hash(result.claim),  # Simple claim identifier
            "payload": result.model_dump()
        }
        
        if queue_type == "compact":
            # Compact format for high-throughput scenarios
            return {
                "type": "verification",
                "claim": result.claim,
                "verdict": result.verdict,
                "confidence": result.confidence,
                "timestamp": result.timestamp.isoformat()
            }
        elif queue_type == "detailed":
            # Detailed format with all metadata
            base_message["format"] = "detailed"
            base_message["metadata"] = result.metadata
            return base_message
        else:
            # Standard format
            return base_message
    
    def format_user_friendly(self, result: VerificationResult) -> str:
        """Generate a user-friendly, conversational format of the result."""
        confidence_desc = self._get_confidence_description(result.confidence)
        
        if result.verdict == "TRUE":
            verdict_desc = f"✅ This claim appears to be **TRUE** with {confidence_desc} confidence."
        elif result.verdict == "FALSE":
            verdict_desc = f"❌ This claim appears to be **FALSE** with {confidence_desc} confidence."
        elif result.verdict == "UNCERTAIN":
            verdict_desc = f"❓ This claim is **UNCERTAIN** - we couldn't find enough reliable evidence to verify it."
        else:  # ERROR
            verdict_desc = f"⚠️ We encountered an error while verifying this claim."
        
        friendly_text = [
            f"**Claim:** {result.claim}",
            "",
            verdict_desc,
            "",
            f"**Our reasoning:** {result.reasoning}",
        ]
        
        if result.sources:
            friendly_text.extend([
                "",
                f"**Sources checked:** {len(result.sources)} sources including {', '.join(result.sources[:3])}{'...' if len(result.sources) > 3 else ''}"
            ])
        
        return "\n".join(friendly_text)
    
    def _get_confidence_description(self, confidence: float) -> str:
        """Convert numerical confidence to descriptive text."""
        if confidence >= 0.9:
            return "very high"
        elif confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "moderate"
        elif confidence >= 0.3:
            return "low"
        else:
            return "very low"


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