"""
Comprehensive tests for BaseAgent abstract class.
"""
import pytest
from abc import ABC
from datetime import datetime
import sys
import os

# Add src to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agents.base_agent import BaseAgent
from agents.verification_result import VerificationResult


class ConcreteTestAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing purposes."""
    
    def __init__(self, agent_id: str = None, should_raise: bool = False):
        super().__init__(agent_id)
        self.should_raise = should_raise
        self.verify_call_count = 0
        self.last_claim = None
    
    def verify(self, claim: str) -> VerificationResult:
        """Test implementation of verify method."""
        self.verify_call_count += 1
        self.last_claim = claim
        
        if self.should_raise:
            raise ValueError("Test error")
            
        return VerificationResult(
            claim=claim,
            verdict="TRUE",
            confidence=0.95,
            reasoning="Test verification",
            sources=["http://example.com"],
            evidence=["Test evidence"],
            agent_id=self.agent_id
        )


class TestBaseAgent:
    """Test cases for BaseAgent abstract class."""
    
    def test_base_agent_is_abstract(self):
        """Test that BaseAgent is an abstract class."""
        assert issubclass(BaseAgent, ABC)
        
        # Should not be able to instantiate BaseAgent directly
        with pytest.raises(TypeError):
            BaseAgent()
    
    def test_base_agent_requires_verify_implementation(self):
        """Test that BaseAgent requires verify method to be implemented."""
        
        class IncompleteAgent(BaseAgent):
            pass
        
        # Should not be able to instantiate without implementing verify
        with pytest.raises(TypeError):
            IncompleteAgent()
    
    def test_concrete_agent_instantiation(self):
        """Test that concrete implementations can be instantiated."""
        agent = ConcreteTestAgent()
        assert isinstance(agent, BaseAgent)
        assert agent.agent_id == "ConcreteTestAgent"
    
    def test_custom_agent_id(self):
        """Test agent initialization with custom agent_id."""
        custom_id = "test-agent-123"
        agent = ConcreteTestAgent(agent_id=custom_id)
        assert agent.agent_id == custom_id
    
    def test_default_agent_id(self):
        """Test agent initialization with default agent_id."""
        agent = ConcreteTestAgent()
        assert agent.agent_id == "ConcreteTestAgent"
    
    def test_none_agent_id_uses_class_name(self):
        """Test that None agent_id defaults to class name."""
        agent = ConcreteTestAgent(agent_id=None)
        assert agent.agent_id == "ConcreteTestAgent"
    
    def test_empty_string_agent_id(self):
        """Test agent initialization with empty string agent_id."""
        agent = ConcreteTestAgent(agent_id="")
        assert agent.agent_id == ""
    
    def test_verify_method_signature(self):
        """Test that verify method has correct signature."""
        agent = ConcreteTestAgent()
        
        # Should accept string claim
        result = agent.verify("Test claim")
        assert isinstance(result, VerificationResult)
        assert result.claim == "Test claim"
    
    def test_verify_method_returns_verification_result(self):
        """Test that verify method returns VerificationResult."""
        agent = ConcreteTestAgent()
        result = agent.verify("The sky is blue")
        
        assert isinstance(result, VerificationResult)
        assert result.claim == "The sky is blue"
        assert result.verdict == "TRUE"
        assert result.confidence == 0.95
        assert result.agent_id == agent.agent_id
    
    def test_verify_method_call_tracking(self):
        """Test that verify method calls are tracked correctly."""
        agent = ConcreteTestAgent()
        
        assert agent.verify_call_count == 0
        assert agent.last_claim is None
        
        agent.verify("First claim")
        assert agent.verify_call_count == 1
        assert agent.last_claim == "First claim"
        
        agent.verify("Second claim")
        assert agent.verify_call_count == 2
        assert agent.last_claim == "Second claim"
    
    def test_verify_method_with_empty_claim(self):
        """Test verify method with empty claim."""
        agent = ConcreteTestAgent()
        result = agent.verify("")
        
        assert isinstance(result, VerificationResult)
        assert result.claim == ""
    
    def test_verify_method_with_long_claim(self):
        """Test verify method with very long claim."""
        long_claim = "A" * 1000
        agent = ConcreteTestAgent()
        result = agent.verify(long_claim)
        
        assert isinstance(result, VerificationResult)
        assert result.claim == long_claim
    
    def test_verify_method_with_special_characters(self):
        """Test verify method with special characters in claim."""
        special_claim = "Test claim with émojis 🚀 and symbols @#$%"
        agent = ConcreteTestAgent()
        result = agent.verify(special_claim)
        
        assert isinstance(result, VerificationResult)
        assert result.claim == special_claim
    
    def test_verify_method_exception_handling(self):
        """Test that exceptions in verify method are properly raised."""
        agent = ConcreteTestAgent(should_raise=True)
        
        with pytest.raises(ValueError, match="Test error"):
            agent.verify("Test claim")
    
    def test_str_representation(self):
        """Test string representation of agent."""
        agent = ConcreteTestAgent()
        str_repr = str(agent)
        assert "ConcreteTestAgent" in str_repr
        assert agent.agent_id in str_repr
    
    def test_str_representation_with_custom_id(self):
        """Test string representation with custom agent_id."""
        custom_id = "custom-test-agent"
        agent = ConcreteTestAgent(agent_id=custom_id)
        str_repr = str(agent)
        assert "ConcreteTestAgent" in str_repr
        assert custom_id in str_repr
    
    def test_repr_representation(self):
        """Test repr representation of agent."""
        agent = ConcreteTestAgent()
        repr_str = repr(agent)
        assert "ConcreteTestAgent" in repr_str
        assert "agent_id" in repr_str
        assert agent.agent_id in repr_str
    
    def test_repr_representation_with_custom_id(self):
        """Test repr representation with custom agent_id."""
        custom_id = "custom-test-agent"
        agent = ConcreteTestAgent(agent_id=custom_id)
        repr_str = repr(agent)
        assert "ConcreteTestAgent" in repr_str
        assert "agent_id" in repr_str
        assert custom_id in repr_str
    
    def test_inheritance_chain(self):
        """Test that agent correctly inherits from BaseAgent."""
        agent = ConcreteTestAgent()
        assert isinstance(agent, BaseAgent)
        assert isinstance(agent, ABC)
    
    def test_multiple_agents_independence(self):
        """Test that multiple agent instances are independent."""
        agent1 = ConcreteTestAgent(agent_id="agent1")
        agent2 = ConcreteTestAgent(agent_id="agent2")
        
        agent1.verify("Claim 1")
        agent2.verify("Claim 2")
        
        assert agent1.agent_id == "agent1"
        assert agent2.agent_id == "agent2"
        assert agent1.last_claim == "Claim 1"
        assert agent2.last_claim == "Claim 2"
        assert agent1.verify_call_count == 1
        assert agent2.verify_call_count == 1
    
    def test_agent_id_immutability(self):
        """Test that agent_id doesn't change after initialization."""
        original_id = "original-id"
        agent = ConcreteTestAgent(agent_id=original_id)
        
        # agent_id should remain the same
        assert agent.agent_id == original_id
        
        # Verify that verify method still works
        result = agent.verify("Test claim")
        assert result.agent_id == original_id


class TestVerificationResultIntegration:
    """Test integration between BaseAgent and VerificationResult."""
    
    def test_verify_returns_proper_verification_result(self):
        """Test that verify method returns properly formatted VerificationResult."""
        agent = ConcreteTestAgent(agent_id="integration-test")
        claim = "Integration test claim"
        
        result = agent.verify(claim)
        
        # Verify all required fields are present
        assert isinstance(result, VerificationResult)
        assert result.claim == claim
        assert result.verdict is not None
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning is not None
        assert isinstance(result.sources, list)
        assert isinstance(result.evidence, list)
        assert isinstance(result.metadata, dict)
        assert isinstance(result.timestamp, datetime)
        assert result.agent_id == agent.agent_id
    
    def test_verification_result_serialization(self):
        """Test that VerificationResult from verify can be serialized."""
        agent = ConcreteTestAgent()
        result = agent.verify("Serialization test")
        
        # Should be able to serialize to dict
        result_dict = result.model_dump()
        assert isinstance(result_dict, dict)
        assert result_dict["claim"] == "Serialization test"
        
        # Should be able to serialize to JSON
        result_json = result.model_dump_json()
        assert isinstance(result_json, str)
        assert "Serialization test" in result_json


class TestVerificationResult:
    """Test cases for VerificationResult model."""
    
    def test_verification_result_str_representation(self):
        """Test string representation of VerificationResult."""
        result = VerificationResult(
            claim="Test claim",
            verdict="TRUE",
            confidence=0.85,
            reasoning="Test reasoning"
        )
        
        str_repr = str(result)
        assert "VerificationResult" in str_repr
        assert "verdict=TRUE" in str_repr
        assert "confidence=0.85" in str_repr
    
    def test_verification_result_repr_representation(self):
        """Test repr representation of VerificationResult."""
        long_claim = "This is a very long claim that should be truncated when displayed in repr"
        result = VerificationResult(
            claim=long_claim,
            verdict="FALSE",
            confidence=0.25,
            reasoning="Test reasoning"
        )
        
        repr_str = repr(result)
        assert "VerificationResult" in repr_str
        assert "verdict='FALSE'" in repr_str
        assert "confidence=0.25" in repr_str
        assert "..." in repr_str  # Should truncate long claim


if __name__ == "__main__":
    pytest.main([__file__, "-v"])