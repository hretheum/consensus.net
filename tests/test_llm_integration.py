"""
Tests for real LLM integration.

Tests the RealLLMInteraction class and agent integration with real LLM APIs.
Uses mocking to avoid actual API calls during testing.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import os

from src.llm.llm_client import RealLLMInteraction
from src.llm.error_handling import (
    APIError, RateLimitError, TimeoutError, ConfigurationError, ModelNotAvailableError
)
from src.agents.agent_models import LLMRequest, LLMResponse, ProcessedClaim, ClaimComplexity, AgentConfig
from src.agents.simple_agent import SimpleAgent
from src.config.llm_config import LLMModel, LLMProvider


class TestRealLLMInteraction:
    """Test the real LLM client implementation."""
    
    @pytest.fixture
    def llm_client(self):
        """Create RealLLMInteraction instance for testing."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key'
        }):
            return RealLLMInteraction()
    
    @pytest.fixture
    def sample_claim(self):
        """Create sample processed claim for testing."""
        return ProcessedClaim(
            original_text="The sky is blue.",
            normalized_text="the sky is blue.",
            domain="science",
            complexity=ClaimComplexity.SIMPLE,
            context={"word_count": 4},
            preprocessing_metadata={"test": True}
        )
    
    @pytest.fixture
    def sample_request(self):
        """Create sample LLM request for testing."""
        return LLMRequest(
            prompt="Verify this claim: The sky is blue.",
            model="gpt-4o-mini",
            parameters={}
        )
    
    def test_initialization_with_api_keys(self):
        """Test RealLLMInteraction initializes with API keys."""
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-openai-key',
            'ANTHROPIC_API_KEY': 'test-anthropic-key'
        }):
            client = RealLLMInteraction()
            assert client.is_available(LLMProvider.OPENAI)
            assert client.is_available(LLMProvider.ANTHROPIC)
            assert client.is_available(LLMProvider.OLLAMA)
    
    def test_initialization_without_api_keys(self):
        """Test RealLLMInteraction handles missing API keys."""
        with patch.dict(os.environ, {}, clear=True):
            client = RealLLMInteraction()
            # Should still initialize but providers may not be available
            assert len(client.get_available_providers()) >= 1  # Ollama should still be available
    
    def test_generate_verification_prompt(self, llm_client, sample_claim):
        """Test prompt generation for verification."""
        prompt = llm_client.generate_verification_prompt(sample_claim)
        
        assert sample_claim.original_text in prompt
        assert sample_claim.domain in prompt
        assert sample_claim.complexity.value in prompt
        assert "Verdict:" in prompt
        assert "Confidence:" in prompt
        assert "Reasoning:" in prompt
    
    @pytest.mark.asyncio
    async def test_openai_api_call_success(self, llm_client, sample_request):
        """Test successful OpenAI API call."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Verdict: TRUE\nConfidence: 0.95\nReasoning: The sky appears blue due to Rayleigh scattering."
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 100
        mock_response.created = 1234567890
        
        with patch.object(llm_client._clients[LLMProvider.OPENAI].chat.completions, 'create', return_value=mock_response):
            response = await llm_client.call_llm_async(sample_request)
            
            assert isinstance(response, LLMResponse)
            assert "Verdict: TRUE" in response.content
            assert response.model_used == sample_request.model
            assert response.tokens_used == 100
            assert response.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_anthropic_api_call_success(self, llm_client):
        """Test successful Anthropic API call."""
        request = LLMRequest(
            prompt="Test prompt",
            model="claude-3-haiku-20240307",
            parameters={}
        )
        
        # Mock Anthropic response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Verdict: FALSE\nConfidence: 0.88\nReasoning: This claim is incorrect."
        mock_response.stop_reason = "end_turn"
        mock_response.id = "test-message-id"
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 30
        
        with patch.object(llm_client._clients[LLMProvider.ANTHROPIC].messages, 'create', return_value=mock_response):
            response = await llm_client.call_llm_async(request)
            
            assert isinstance(response, LLMResponse)
            assert "Verdict: FALSE" in response.content
            assert response.model_used == request.model
            assert response.tokens_used == 80  # 50 + 30
            assert response.confidence == 0.88
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self, llm_client, sample_request):
        """Test rate limit error handling."""
        import openai
        from httpx import Request, Response
        
        # Create a mock response for OpenAI exceptions
        mock_request = Request("POST", "https://api.openai.com/v1/chat/completions")
        mock_response = Response(429, content=b"Rate limit exceeded")
        
        with patch.object(llm_client._clients[LLMProvider.OPENAI].chat.completions, 'create', 
                         side_effect=openai.RateLimitError("Rate limit exceeded", response=mock_response, body=None)):
            with pytest.raises(RateLimitError):
                await llm_client.call_llm_async(sample_request)
    
    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, llm_client, sample_request):
        """Test timeout error handling."""
        import openai
        
        with patch.object(llm_client._clients[LLMProvider.OPENAI].chat.completions, 'create',
                         side_effect=openai.APITimeoutError("Request timeout")):
            with pytest.raises(TimeoutError):
                await llm_client.call_llm_async(sample_request)
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, llm_client, sample_request):
        """Test general API error handling."""
        import openai
        
        with patch.object(llm_client._clients[LLMProvider.OPENAI].chat.completions, 'create',
                         side_effect=openai.APIError("API error")):
            with pytest.raises(APIError):
                await llm_client.call_llm_async(sample_request)
    
    @pytest.mark.asyncio
    async def test_invalid_model_error(self, llm_client):
        """Test error handling for invalid model."""
        request = LLMRequest(
            prompt="Test prompt",
            model="invalid-model",
            parameters={}
        )
        
        # Should raise ValueError when trying to create LLMModel enum
        with pytest.raises((ModelNotAvailableError, ValueError)):
            await llm_client.call_llm_async(request)
    
    def test_synchronous_call_wrapper(self, llm_client, sample_request):
        """Test synchronous wrapper for async LLM call."""
        # Mock async call
        mock_response = LLMResponse(
            content="Test response",
            metadata={"test": True},
            model_used=sample_request.model,
            tokens_used=50,
            confidence=0.8
        )
        
        with patch.object(llm_client, 'call_llm_async', return_value=mock_response):
            response = llm_client.call_llm(sample_request)
            
            assert response == mock_response
    
    @pytest.mark.asyncio
    async def test_retry_logic_success_after_failure(self, llm_client, sample_request):
        """Test retry logic succeeds after initial failure."""
        import openai
        
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Success after retry"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.total_tokens = 50
        mock_response.created = 1234567890
        
        with patch.object(llm_client._clients[LLMProvider.OPENAI].chat.completions, 'create',
                         side_effect=[openai.APIError("Temporary error"), mock_response]):
            response = await llm_client.call_llm_async(sample_request)
            assert "Success after retry" in response.content
    
    def test_extract_confidence_from_response(self, llm_client):
        """Test confidence extraction from LLM response."""
        # Test various confidence formats
        test_cases = [
            ("Confidence: 0.85", 0.85),
            ("confidence: 0.92", 0.92),
            ("Confidence level: 0.77", 0.77),
            ("No confidence mentioned", None),
            ("Confidence: 1.5", 1.0),  # Should cap at 1.0
            ("Confidence: -0.1", 0.0),  # Should floor at 0.0
        ]
        
        for content, expected in test_cases:
            result = llm_client._extract_confidence(content)
            if expected is None:
                assert result is None
            else:
                assert result is not None, f"Expected {expected} but got None for content: {content}"
                assert abs(result - expected) < 0.001  # Use small tolerance for float comparison


class TestAgentLLMIntegration:
    """Test agent integration with real LLM."""
    
    def test_agent_uses_simulation_by_default(self):
        """Test agent uses simulation mode by default."""
        agent = SimpleAgent("test-agent")
        
        # Should use SimpleLLMInteraction by default
        from src.agents.simple_agent import SimpleLLMInteraction
        assert isinstance(agent.llm_interaction, SimpleLLMInteraction)
    
    def test_agent_with_real_llm_config(self):
        """Test agent initialization with real LLM configuration."""
        config = AgentConfig(
            agent_id="test-agent",
            use_real_llm=True,
            primary_model="gpt-4o-mini"
        )
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            with patch('src.agents.simple_agent.REAL_LLM_AVAILABLE', True):
                agent = SimpleAgent("test-agent", config)
                
                # Should attempt to use real LLM (will fall back to simulation if initialization fails)
                assert agent.config.use_real_llm is True
    
    def test_agent_verification_with_real_llm_simulation(self):
        """Test agent verification pipeline with mocked real LLM."""
        config = AgentConfig(
            agent_id="test-agent",
            use_real_llm=True
        )
        
        # Mock the real LLM response
        mock_llm_response = LLMResponse(
            content="Verdict: TRUE\nConfidence: 0.95\nReasoning: This is a well-established scientific fact.",
            metadata={"provider": "openai", "model": "gpt-4o-mini"},
            model_used="gpt-4o-mini",
            tokens_used=100,
            confidence=0.95
        )
        
        with patch('src.agents.simple_agent.REAL_LLM_AVAILABLE', True):
            with patch('src.llm.llm_client.RealLLMInteraction') as mock_real_llm:
                mock_instance = Mock()
                mock_instance.call_llm.return_value = mock_llm_response
                mock_instance.generate_verification_prompt.return_value = "Test prompt"
                mock_real_llm.return_value = mock_instance
                
                agent = SimpleAgent("test-agent", config)
                result = agent.verify("The sky is blue")
                
                assert result.verdict == "TRUE"
                assert result.confidence == 0.95
                assert "well-established scientific fact" in result.reasoning
    
    def test_agent_fallback_to_simulation_on_llm_failure(self):
        """Test agent falls back to simulation when real LLM fails."""
        config = AgentConfig(
            agent_id="test-agent",
            use_real_llm=True
        )
        
        with patch('src.agents.simple_agent.REAL_LLM_AVAILABLE', True):
            with patch('src.llm.llm_client.RealLLMInteraction', side_effect=Exception("LLM init failed")):
                agent = SimpleAgent("test-agent", config)
                
                # Should fall back to simulation
                from src.agents.simple_agent import SimpleLLMInteraction
                assert isinstance(agent.llm_interaction, SimpleLLMInteraction)
                
                # Should still be able to verify claims
                result = agent.verify("The sky is blue")
                assert result.verdict in ["TRUE", "FALSE", "UNCERTAIN"]


class TestLLMIntegrationEndToEnd:
    """End-to-end tests for LLM integration."""
    
    @pytest.mark.integration
    def test_real_llm_available_check(self):
        """Test if real LLM integration is properly available."""
        try:
            from src.llm.llm_client import RealLLMInteraction
            # This should not raise an import error
            assert True
        except ImportError:
            pytest.skip("Real LLM integration not available")
    
    @pytest.mark.integration  
    def test_agent_configuration_validation(self):
        """Test agent configuration with different LLM settings."""
        configs = [
            AgentConfig(agent_id="test1", use_real_llm=False),
            AgentConfig(agent_id="test2", use_real_llm=True, primary_model="gpt-4o-mini"),
            AgentConfig(agent_id="test3", use_real_llm=True, primary_model="claude-3-haiku-20240307"),
        ]
        
        for config in configs:
            try:
                agent = SimpleAgent(config.agent_id, config)
                assert agent.agent_id == config.agent_id
                assert agent.config.use_real_llm == config.use_real_llm
            except Exception as e:
                # Should not fail during initialization
                pytest.fail(f"Agent initialization failed for config {config.agent_id}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])