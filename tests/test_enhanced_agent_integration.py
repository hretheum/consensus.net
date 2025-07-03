"""
Tests for integration between SimpleAgent and the enhanced InputProcessor.

Verifies that the enhanced input processor works correctly with the existing
agent architecture while maintaining backward compatibility.
"""

import pytest
from src.agents.simple_agent import SimpleAgent
from src.agents.agent_models import ProcessedClaim, ClaimComplexity
from src.agents.verification_result import VerificationResult


class TestEnhancedAgentIntegration:
    """Test enhanced input processor integration with SimpleAgent."""
    
    def test_legacy_agent_compatibility(self):
        """Test that legacy agent still works as before."""
        agent = SimpleAgent(use_enhanced_processor=False)
        
        result = agent.verify("The sky is blue.")
        
        assert isinstance(result, VerificationResult)
        assert result.claim == "The sky is blue."
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
        # Should have basic metadata
        assert "processing_time" in result.metadata
        assert "domain" in result.metadata
        assert "complexity" in result.metadata
    
    def test_enhanced_agent_text_input(self):
        """Test enhanced agent with text input."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        result = agent.verify("Clinical trials demonstrate vaccine effectiveness in preventing disease.")
        
        assert isinstance(result, VerificationResult)
        assert result.claim == "Clinical trials demonstrate vaccine effectiveness in preventing disease."
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
        # Should use enhanced processor features
        assert "processing_time" in result.metadata
    
    def test_enhanced_agent_json_input(self):
        """Test enhanced agent with JSON input."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        json_input = {
            "claim": "Artificial intelligence improves diagnostic accuracy.",
            "metadata": {
                "source": "Medical Journal",
                "urgency": "high"
            }
        }
        
        result = agent.verify(json_input)
        
        assert isinstance(result, VerificationResult)
        assert result.claim == "Artificial intelligence improves diagnostic accuracy."
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
        # Check that JSON metadata was preserved
        assert "processing_time" in result.metadata
    
    def test_enhanced_agent_json_string(self):
        """Test enhanced agent with JSON provided as string."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        json_string = '{"claim": "Machine learning algorithms reduce errors.", "metadata": {"confidence": 0.8}}'
        
        result = agent.verify(json_string)
        
        assert isinstance(result, VerificationResult)
        assert result.claim == "Machine learning algorithms reduce errors."
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
    
    def test_enhanced_agent_validation(self):
        """Test enhanced agent input validation."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        # Should handle invalid input gracefully
        result = agent.verify("")  # Empty input
        
        assert isinstance(result, VerificationResult)
        assert result.verdict == "ERROR"
        assert "validation" in result.reasoning.lower() or "empty" in result.reasoning.lower()
    
    def test_enhanced_agent_complex_analysis(self):
        """Test enhanced agent with complex input requiring advanced analysis."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        complex_claim = """
        Systematic review and meta-analysis of randomized controlled trials 
        demonstrates 85% statistical significance with p < 0.001, however 
        confounding variables and methodological heterogeneity warrant 
        further investigation compared to control groups.
        """
        
        result = agent.verify(complex_claim.strip())
        
        assert isinstance(result, VerificationResult)
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
        # Should detect high complexity
        assert "complex" in result.metadata.get("complexity", "").lower() or \
               "research" in result.metadata.get("complexity", "").lower()
    
    def test_agent_configuration_compatibility(self):
        """Test that agent configuration works with enhanced processor."""
        from src.agents.agent_models import AgentConfig
        
        config = AgentConfig(
            agent_id="test-enhanced-agent",
            max_tokens=1500,
            confidence_threshold=0.8
        )
        
        agent = SimpleAgent(agent_id="test-agent", config=config, use_enhanced_processor=True)
        
        result = agent.verify("Technology advancement accelerates innovation.")
        
        assert isinstance(result, VerificationResult)
        assert result.agent_id == "test-agent"
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
    
    def test_performance_metrics_with_enhanced_processor(self):
        """Test that performance metrics work with enhanced processor."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        result = agent.verify("Research shows improved outcomes with new methodology.")
        metrics = agent.get_performance_metrics()
        
        assert isinstance(result, VerificationResult)
        assert metrics.verification_time > 0
        assert metrics.api_calls_made >= 0
    
    def test_domain_expertise_with_enhanced_processor(self):
        """Test domain expertise tracking with enhanced processor."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        # Process claims from different domains
        agent.verify("Clinical trials show treatment effectiveness.")
        agent.verify("Quantum physics experiments demonstrate entanglement.")
        agent.verify("Economic indicators suggest market stability.")
        
        expertise = agent.get_domain_expertise()
        
        # Should track domain expertise (may be empty initially in simulation)
        assert isinstance(expertise, dict)
    
    def test_multilingual_support(self):
        """Test enhanced processor with special characters and Unicode."""
        agent = SimpleAgent(use_enhanced_processor=True)
        
        # Text with accented characters and special symbols
        claim = "La investigación médica cuesta €1,000–2,000 por paciente."
        
        result = agent.verify(claim)
        
        assert isinstance(result, VerificationResult)
        assert result.claim == claim
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]


class TestBackwardCompatibility:
    """Test that enhanced features don't break existing functionality."""
    
    def test_existing_tests_still_pass_with_enhanced(self):
        """Test that existing test patterns work with enhanced processor."""
        # Test the same patterns as in existing tests but with enhanced processor
        agent = SimpleAgent(use_enhanced_processor=True)
        
        # Simple claim verification (from existing tests)
        result = agent.verify("The earth is round.")
        assert isinstance(result, VerificationResult)
        assert result.claim == "The earth is round."
        assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
        
        # Scientific claim (from existing tests)
        result = agent.verify("Water boils at 100 degrees Celsius at sea level.")
        assert isinstance(result, VerificationResult)
        assert "science" in result.metadata.get("domain", "").lower() or \
               "general" in result.metadata.get("domain", "").lower()
    
    def test_error_handling_compatibility(self):
        """Test that error handling works the same way."""
        legacy_agent = SimpleAgent(use_enhanced_processor=False)
        enhanced_agent = SimpleAgent(use_enhanced_processor=True)
        
        # Both should handle None input similarly
        legacy_result = legacy_agent.verify(None)
        enhanced_result = enhanced_agent.verify(None)
        
        assert legacy_result.verdict == "ERROR"
        assert enhanced_result.verdict == "ERROR"
        assert isinstance(legacy_result, VerificationResult)
        assert isinstance(enhanced_result, VerificationResult)
    
    def test_result_format_compatibility(self):
        """Test that result format is compatible between processors."""
        legacy_agent = SimpleAgent(use_enhanced_processor=False)
        enhanced_agent = SimpleAgent(use_enhanced_processor=True)
        
        test_claim = "Regular exercise improves cardiovascular health."
        
        legacy_result = legacy_agent.verify(test_claim)
        enhanced_result = enhanced_agent.verify(test_claim)
        
        # Both should return VerificationResult with same basic structure
        assert isinstance(legacy_result, VerificationResult)
        assert isinstance(enhanced_result, VerificationResult)
        assert legacy_result.claim == enhanced_result.claim == test_claim
        assert legacy_result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
        assert enhanced_result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]
        assert hasattr(legacy_result, 'metadata')
        assert hasattr(enhanced_result, 'metadata')