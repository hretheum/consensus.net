"""
Tests for the enhanced OutputGenerator module.

Validates all the new output processing capabilities including:
- Multiple output formats (text, JSON, structured)
- Delivery channel support (API, message queue)
- Error handling and quality validation
- User-friendly formatting
"""
import json
from datetime import datetime
from typing import Dict, Any

import pytest

from src.agents.simple_agent import OutputGenerator
from src.agents.agent_models import (
    ProcessedClaim, ClaimComplexity, Evidence, EvidenceBundle,
    VerificationStep, VerificationChain
)
from src.agents.verification_result import VerificationResult


class TestOutputGeneratorCore:
    """Test the core functionality of the enhanced OutputGenerator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.output_generator = OutputGenerator()
        
        # Create sample data for testing
        self.sample_claim = ProcessedClaim(
            original_text="The Earth is round.",
            normalized_text="the earth is round.",
            domain="science",
            complexity=ClaimComplexity.SIMPLE,
            context={"word_count": 4},
            preprocessing_metadata={"processor_version": "1.0"}
        )
        
        self.sample_evidence = EvidenceBundle(
            supporting_evidence=[
                Evidence(
                    content="Scientific measurements confirm Earth's spherical shape",
                    source="nasa.gov",
                    credibility_score=0.95,
                    relevance_score=0.98,
                    timestamp=datetime.now()
                )
            ],
            contradicting_evidence=[],
            neutral_evidence=[],
            overall_quality=0.9
        )
        
        self.sample_chain = VerificationChain(
            steps=[
                VerificationStep(
                    step_type="evidence_gathering",
                    input_data={"sources": ["nasa.gov", "wikipedia.org"]},
                    output_data={"evidence_count": 1},
                    confidence=0.9,
                    reasoning="Gathered scientific evidence about Earth's shape"
                ),
                VerificationStep(
                    step_type="llm_analysis",
                    input_data={"prompt_length": 100},
                    output_data={"tokens_used": 50},
                    confidence=0.95,
                    reasoning="LLM analysis confirms scientific consensus"
                )
            ],
            overall_verdict="TRUE",
            final_confidence=0.92,
            processing_time=1.5,
            uncertainty_factors=[]
        )
    
    def test_format_result_with_validation(self):
        """Test that format_result works and includes quality validation."""
        result = self.output_generator.format_result(
            self.sample_claim, self.sample_chain, "test_agent"
        )
        
        assert isinstance(result, VerificationResult)
        assert result.claim == "The Earth is round."
        assert result.verdict == "TRUE"
        assert result.confidence == 0.92
        assert result.agent_id == "test_agent"
        
        # Should not have quality warning for this good result
        assert "quality_warning" not in result.metadata
    
    def test_format_result_with_quality_warning(self):
        """Test that poor quality results get flagged."""
        # Create a poor quality chain
        poor_chain = VerificationChain(
            steps=[],  # No steps
            overall_verdict="TRUE",
            final_confidence=1.5,  # Invalid confidence
            processing_time=0.1,
            uncertainty_factors=[]
        )
        
        result = self.output_generator.format_result(
            self.sample_claim, poor_chain, "test_agent"
        )
        
        # Should have quality warning due to no steps
        assert "quality_warning" in result.metadata
        # Should have confidence normalization warning
        assert "confidence_normalized" in result.metadata
        # Confidence should be normalized to 1.0
        assert result.confidence == 1.0


class TestOutputGeneratorArchitectureMethods:
    """Test the methods specified in the core agent architecture."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.output_generator = OutputGenerator()
        self.sample_evidence = EvidenceBundle(
            supporting_evidence=[
                Evidence(
                    content="Scientific evidence supports this claim with detailed measurements and observations",
                    source="scientific_journal.com",
                    credibility_score=0.95,
                    relevance_score=0.98,
                    timestamp=datetime.now()
                )
            ],
            contradicting_evidence=[
                Evidence(
                    content="Some alternative theories suggest different interpretations",
                    source="alternative_source.com",
                    credibility_score=0.6,
                    relevance_score=0.7,
                    timestamp=datetime.now()
                )
            ],
            neutral_evidence=[],
            overall_quality=0.8
        )
    
    def test_compile_evidence_summary(self):
        """Test evidence summary compilation."""
        summary = self.output_generator.compile_evidence_summary(self.sample_evidence)
        
        assert len(summary) > 0
        assert "Supporting Evidence (1 items):" in summary
        assert "Contradicting Evidence (1 items):" in summary
        assert "Overall Evidence Quality: 0.80" in summary
        
        # Check that evidence content is truncated appropriately
        supporting_line = next(line for line in summary if "Scientific evidence supports" in line)
        assert len(supporting_line) <= 150  # Should be truncated with "..."
    
    def test_generate_reasoning_chain(self):
        """Test reasoning chain generation."""
        steps = [
            VerificationStep(
                step_type="analysis",
                input_data={},
                output_data={},
                confidence=0.8,
                reasoning="First step of analysis"
            ),
            VerificationStep(
                step_type="verification",
                input_data={},
                output_data={},
                confidence=0.9,
                reasoning="Second step verification"
            )
        ]
        
        chain = self.output_generator.generate_reasoning_chain(steps)
        
        assert "1. First step of analysis (confidence: 0.80)" in chain
        assert "2. Second step verification (confidence: 0.90)" in chain
        assert " | " in chain  # Should be joined with separator
    
    def test_handle_verification_errors(self):
        """Test error handling for verification failures."""
        test_error = ValueError("Test error message")
        
        error_result = self.output_generator.handle_verification_errors(test_error)
        
        assert isinstance(error_result, VerificationResult)
        assert error_result.verdict == "ERROR"
        assert error_result.confidence == 0.0
        assert "ValueError" in error_result.reasoning
        assert "Test error message" in error_result.reasoning
        assert error_result.metadata["error_type"] == "ValueError"
        assert error_result.metadata["error_message"] == "Test error message"
    
    def test_validate_result_quality_valid(self):
        """Test quality validation with valid result."""
        valid_result = VerificationResult(
            claim="Test claim",
            verdict="TRUE",
            confidence=0.8,
            reasoning="This is a detailed reasoning explanation that meets minimum length requirements.",
            sources=["source1.com"],
            evidence=["evidence1"],
            metadata={},
            agent_id="test_agent"
        )
        
        assert self.output_generator.validate_result_quality(valid_result) is True
    
    def test_validate_result_quality_invalid(self):
        """Test quality validation with invalid results."""
        # Test empty claim
        empty_claim = VerificationResult(
            claim="",  # Empty claim
            verdict="TRUE",
            confidence=0.8,
            reasoning="Good reasoning",
            sources=[],
            evidence=[],
            metadata={},
            agent_id="test_agent"
        )
        assert self.output_generator.validate_result_quality(empty_claim) is False
        
        # Test invalid verdict
        invalid_verdict = VerificationResult(
            claim="Test claim",
            verdict="INVALID",  # Not in valid set
            confidence=0.8,
            reasoning="Good reasoning",
            sources=[],
            evidence=[],
            metadata={},
            agent_id="test_agent"
        )
        assert self.output_generator.validate_result_quality(invalid_verdict) is False
        
        # Test insufficient reasoning
        short_reasoning = VerificationResult(
            claim="Test claim",
            verdict="TRUE",
            confidence=0.8,
            reasoning="Short",  # Too short
            sources=[],
            evidence=[],
            metadata={},
            agent_id="test_agent"
        )
        assert self.output_generator.validate_result_quality(short_reasoning) is False


class TestOutputFormats:
    """Test different output format methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.output_generator = OutputGenerator()
        self.sample_result = VerificationResult(
            claim="The Earth is round.",
            verdict="TRUE",
            confidence=0.92,
            reasoning="Scientific evidence from multiple sources confirms this.",
            sources=["nasa.gov", "wikipedia.org"],
            evidence=["Satellite imagery", "Mathematical calculations"],
            metadata={"processing_time": 1.5, "domain": "science"},
            agent_id="test_agent"
        )
    
    def test_to_text_format_basic(self):
        """Test basic text format conversion."""
        text_output = self.output_generator.to_text_format(self.sample_result)
        
        assert "CLAIM: The Earth is round." in text_output
        assert "VERDICT: TRUE" in text_output
        assert "CONFIDENCE: 92.00%" in text_output
        assert "REASONING:" in text_output
        assert "Verified at:" in text_output
        assert "Agent ID: test_agent" in text_output
    
    def test_to_text_format_detailed(self):
        """Test detailed text format conversion."""
        text_output = self.output_generator.to_text_format(self.sample_result, detailed=True)
        
        assert "SOURCES: nasa.gov, wikipedia.org" in text_output
        assert "EVIDENCE:" in text_output
        assert "1. Satellite imagery" in text_output
        assert "2. Mathematical calculations" in text_output
        assert "METADATA:" in text_output
        assert "processing_time: 1.5" in text_output
    
    def test_to_json_format(self):
        """Test JSON format conversion."""
        json_output = self.output_generator.to_json_format(self.sample_result)
        
        # Should be valid JSON
        parsed = json.loads(json_output)
        assert parsed["claim"] == "The Earth is round."
        assert parsed["verdict"] == "TRUE"
        assert parsed["confidence"] == 0.92
        
        # Test pretty format
        pretty_json = self.output_generator.to_json_format(self.sample_result, pretty=True)
        assert "\n" in pretty_json  # Should have newlines for pretty formatting
    
    def test_to_structured_format(self):
        """Test structured format conversion."""
        structured = self.output_generator.to_structured_format(self.sample_result)
        
        assert structured["status"] == "success"
        assert structured["data"]["claim"] == "The Earth is round."
        assert structured["data"]["verdict"] == "TRUE"
        assert structured["data"]["confidence"] == 0.92
        assert "processing_metadata" in structured["data"]
        assert structured["data"]["evidence_count"] == 2
    
    def test_structured_format_error_status(self):
        """Test structured format with error status."""
        error_result = VerificationResult(
            claim="Test claim",
            verdict="ERROR",
            confidence=0.0,
            reasoning="Error occurred",
            sources=[],
            evidence=[],
            metadata={},
            agent_id="test_agent"
        )
        
        structured = self.output_generator.to_structured_format(error_result)
        assert structured["status"] == "error"


class TestDeliveryChannels:
    """Test delivery channel formatting methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.output_generator = OutputGenerator()
        self.sample_result = VerificationResult(
            claim="The Earth is round.",
            verdict="TRUE",
            confidence=0.92,
            reasoning="Scientific evidence confirms this.",
            sources=["nasa.gov"],
            evidence=["Evidence 1"],
            metadata={"processing_time": 1.5},
            agent_id="test_agent"
        )
    
    def test_format_for_api_response_json(self):
        """Test API response formatting with JSON."""
        api_response = self.output_generator.format_for_api_response(
            self.sample_result, format_type="json"
        )
        
        assert api_response["success"] is True
        assert api_response["format"] == "json"
        assert "timestamp" in api_response
        assert "result" in api_response
        assert api_response["result"]["claim"] == "The Earth is round."
    
    def test_format_for_api_response_text(self):
        """Test API response formatting with text."""
        api_response = self.output_generator.format_for_api_response(
            self.sample_result, format_type="text"
        )
        
        assert api_response["success"] is True
        assert api_response["format"] == "text"
        assert isinstance(api_response["result"], str)
        assert "CLAIM:" in api_response["result"]
    
    def test_format_for_api_response_structured(self):
        """Test API response formatting with structured format."""
        api_response = self.output_generator.format_for_api_response(
            self.sample_result, format_type="structured"
        )
        
        assert api_response["success"] is True
        assert api_response["format"] == "structured"
        assert api_response["result"]["status"] == "success"
    
    def test_format_for_message_queue_standard(self):
        """Test message queue formatting with standard format."""
        queue_message = self.output_generator.format_for_message_queue(
            self.sample_result, queue_type="standard"
        )
        
        assert queue_message["message_type"] == "verification_result"
        assert queue_message["agent_id"] == "test_agent"
        assert "claim_id" in queue_message
        assert "payload" in queue_message
        assert "timestamp" in queue_message
    
    def test_format_for_message_queue_compact(self):
        """Test message queue formatting with compact format."""
        queue_message = self.output_generator.format_for_message_queue(
            self.sample_result, queue_type="compact"
        )
        
        assert queue_message["type"] == "verification"
        assert queue_message["claim"] == "The Earth is round."
        assert queue_message["verdict"] == "TRUE"
        assert queue_message["confidence"] == 0.92
        assert len(queue_message.keys()) <= 5  # Should be compact
    
    def test_format_for_message_queue_detailed(self):
        """Test message queue formatting with detailed format."""
        queue_message = self.output_generator.format_for_message_queue(
            self.sample_result, queue_type="detailed"
        )
        
        assert queue_message["format"] == "detailed"
        assert "metadata" in queue_message
        assert queue_message["metadata"]["processing_time"] == 1.5


class TestUserFriendlyFormatting:
    """Test user-friendly formatting capabilities."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.output_generator = OutputGenerator()
    
    def test_format_user_friendly_true(self):
        """Test user-friendly format for TRUE verdict."""
        result = VerificationResult(
            claim="The sky is blue.",
            verdict="TRUE",
            confidence=0.95,
            reasoning="Scientific explanation of light scattering.",
            sources=["physics.org", "science.edu"],
            evidence=["Evidence 1"],
            metadata={},
            agent_id="test_agent"
        )
        
        friendly = self.output_generator.format_user_friendly(result)
        
        assert "✅" in friendly
        assert "**TRUE**" in friendly
        assert "very high confidence" in friendly
        assert "The sky is blue." in friendly
        assert "Scientific explanation" in friendly
        assert "2 sources" in friendly
    
    def test_format_user_friendly_false(self):
        """Test user-friendly format for FALSE verdict."""
        result = VerificationResult(
            claim="The Earth is flat.",
            verdict="FALSE",
            confidence=0.98,
            reasoning="Overwhelming scientific evidence contradicts this.",
            sources=["nasa.gov"],
            evidence=["Evidence 1"],
            metadata={},
            agent_id="test_agent"
        )
        
        friendly = self.output_generator.format_user_friendly(result)
        
        assert "❌" in friendly
        assert "**FALSE**" in friendly
        assert "very high confidence" in friendly
    
    def test_format_user_friendly_uncertain(self):
        """Test user-friendly format for UNCERTAIN verdict."""
        result = VerificationResult(
            claim="Some uncertain claim.",
            verdict="UNCERTAIN",
            confidence=0.3,
            reasoning="Insufficient evidence available.",
            sources=[],
            evidence=[],
            metadata={},
            agent_id="test_agent"
        )
        
        friendly = self.output_generator.format_user_friendly(result)
        
        assert "❓" in friendly
        assert "**UNCERTAIN**" in friendly
        assert "couldn't find enough reliable evidence" in friendly
    
    def test_format_user_friendly_error(self):
        """Test user-friendly format for ERROR verdict."""
        result = VerificationResult(
            claim="Error claim.",
            verdict="ERROR",
            confidence=0.0,
            reasoning="System error occurred.",
            sources=[],
            evidence=[],
            metadata={},
            agent_id="test_agent"
        )
        
        friendly = self.output_generator.format_user_friendly(result)
        
        assert "⚠️" in friendly
        assert "encountered an error" in friendly
    
    def test_confidence_descriptions(self):
        """Test confidence level descriptions."""
        # Test the private method through different confidence values
        assert "very high" in self.output_generator._get_confidence_description(0.95)
        assert "high" in self.output_generator._get_confidence_description(0.8)
        assert "moderate" in self.output_generator._get_confidence_description(0.6)
        assert "low" in self.output_generator._get_confidence_description(0.4)
        assert "very low" in self.output_generator._get_confidence_description(0.1)


class TestOutputGeneratorIntegration:
    """Test integration of OutputGenerator with existing system."""
    
    def test_backwards_compatibility(self):
        """Test that existing functionality still works."""
        from src.agents.simple_agent import SimpleAgent
        
        # This should work exactly as before
        agent = SimpleAgent("test_agent")
        result = agent.verify("The Earth is round.")
        
        assert isinstance(result, VerificationResult)
        assert result.claim == "The Earth is round."
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN", "ERROR"]
        assert 0.0 <= result.confidence <= 1.0
    
    def test_new_functionality_integration(self):
        """Test that new functionality integrates well."""
        from src.agents.simple_agent import SimpleAgent
        
        agent = SimpleAgent("test_agent")
        result = agent.verify("The sky is blue.")
        
        # Test new format methods work with real agent output
        output_gen = OutputGenerator()
        
        # Should not raise exceptions
        text_format = output_gen.to_text_format(result)
        json_format = output_gen.to_json_format(result)
        structured_format = output_gen.to_structured_format(result)
        api_format = output_gen.format_for_api_response(result)
        queue_format = output_gen.format_for_message_queue(result)
        friendly_format = output_gen.format_user_friendly(result)
        
        # Basic validation
        assert len(text_format) > 0
        assert len(json_format) > 0
        assert len(structured_format) > 0
        assert len(api_format) > 0
        assert len(queue_format) > 0
        assert len(friendly_format) > 0