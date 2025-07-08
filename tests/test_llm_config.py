"""
Tests for LLM configuration and selection logic.
"""

import pytest
from src.config.llm_config import (
    LLMModel, LLMProvider, ClaimComplexity, PrivacyLevel, UrgencyLevel,
    select_optimal_model, get_fallback_model, calculate_estimated_cost,
    LLM_CONFIGS
)


class TestLLMConfiguration:
    """Test LLM configuration data and constants."""
    
    def test_all_models_have_configs(self):
        """Test that all defined models have configuration entries."""
        for model in LLMModel:
            assert model in LLM_CONFIGS, f"Missing config for {model}"
    
    def test_config_completeness(self):
        """Test that all LLM configs have required fields."""
        for model, config in LLM_CONFIGS.items():
            assert config.model == model
            assert isinstance(config.provider, LLMProvider)
            assert config.max_tokens > 0
            assert 0.0 <= config.temperature <= 1.0
            assert config.max_requests_per_minute > 0
            assert config.cost_per_input_token >= 0.0
            assert config.cost_per_output_token >= 0.0
            assert config.average_latency_ms > 0
            assert config.context_window > 0
            assert 0.0 <= config.accuracy_score <= 1.0
            assert 0.0 <= config.reasoning_quality <= 5.0
            assert 0.0 <= config.confidence_calibration <= 1.0

    def test_performance_characteristics(self):
        """Test that performance characteristics match research findings."""
        gpt_config = LLM_CONFIGS[LLMModel.GPT_4O_MINI]
        claude_config = LLM_CONFIGS[LLMModel.CLAUDE_3_HAIKU]
        llama_config = LLM_CONFIGS[LLMModel.LLAMA_3_2]
        
        # GPT-4o-mini should have highest accuracy
        assert gpt_config.accuracy_score > claude_config.accuracy_score
        assert gpt_config.accuracy_score > llama_config.accuracy_score
        
        # Claude should have best reasoning quality
        assert claude_config.reasoning_quality >= gpt_config.reasoning_quality
        assert claude_config.reasoning_quality > llama_config.reasoning_quality
        
        # Claude should be fastest
        assert claude_config.average_latency_ms < gpt_config.average_latency_ms
        assert claude_config.average_latency_ms < llama_config.average_latency_ms


class TestModelSelection:
    """Test the model selection logic."""
    
    def test_default_selection(self):
        """Test default model selection returns GPT-4o-mini."""
        model = select_optimal_model()
        assert model == LLMModel.GPT_4O_MINI
    
    def test_privacy_override(self):
        """Test that privacy requirements override other selections."""
        # Sensitive data should use local model
        model = select_optimal_model(privacy=PrivacyLevel.SENSITIVE)
        assert model == LLMModel.LLAMA_3_2
        
        # Confidential data should use local model
        model = select_optimal_model(privacy=PrivacyLevel.CONFIDENTIAL)
        assert model == LLMModel.LLAMA_3_2
    
    def test_complex_reasoning_selection(self):
        """Test complex claims select Claude for better reasoning."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX, 
            urgency=UrgencyLevel.LOW
        )
        assert model == LLMModel.CLAUDE_3_HAIKU
    
    def test_urgency_override(self):
        """Test that high urgency selects fastest model."""
        model = select_optimal_model(urgency=UrgencyLevel.HIGH)
        assert model == LLMModel.CLAUDE_3_HAIKU
    
    def test_urgency_overrides_complexity(self):
        """Test that urgency overrides complexity preferences."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX,
            urgency=UrgencyLevel.HIGH
        )
        # Should prefer speed over reasoning quality for urgent requests
        assert model == LLMModel.CLAUDE_3_HAIKU


class TestFallbackLogic:
    """Test the fallback model selection."""
    
    def test_gpt_fallback(self):
        """Test GPT-4o-mini fallback is Claude."""
        fallback = get_fallback_model(LLMModel.GPT_4O_MINI)
        assert fallback == LLMModel.CLAUDE_3_HAIKU
    
    def test_claude_fallback(self):
        """Test Claude fallback is Llama."""
        fallback = get_fallback_model(LLMModel.CLAUDE_3_HAIKU)
        assert fallback == LLMModel.LLAMA_3_2
    
    def test_llama_no_fallback(self):
        """Test Llama has no fallback (local model)."""
        fallback = get_fallback_model(LLMModel.LLAMA_3_2)
        assert fallback is None


class TestCostCalculation:
    """Test cost calculation logic."""
    
    def test_gpt_cost_calculation(self):
        """Test GPT-4o-mini cost calculation."""
        # Example: 100 input tokens, 50 output tokens
        cost = calculate_estimated_cost(LLMModel.GPT_4O_MINI, 100, 50)
        expected = (100 / 1_000_000) * 0.15 + (50 / 1_000_000) * 0.60
        assert abs(cost - expected) < 0.000001
    
    def test_claude_cost_calculation(self):
        """Test Claude cost calculation."""
        cost = calculate_estimated_cost(LLMModel.CLAUDE_3_HAIKU, 100, 50)
        expected = (100 / 1_000_000) * 0.25 + (50 / 1_000_000) * 1.25
        assert abs(cost - expected) < 0.000001
    
    def test_ollama_zero_cost(self):
        """Test that local models have zero marginal cost."""
        cost = calculate_estimated_cost(LLMModel.LLAMA_3_2, 1000, 500)
        assert cost == 0.0
    
    def test_cost_scaling(self):
        """Test cost scales linearly with token usage."""
        base_cost = calculate_estimated_cost(LLMModel.GPT_4O_MINI, 100, 50)
        double_cost = calculate_estimated_cost(LLMModel.GPT_4O_MINI, 200, 100)
        assert abs(double_cost - (2 * base_cost)) < 0.000001


class TestModelSelectionScenarios:
    """Test realistic model selection scenarios."""
    
    def test_simple_fact_verification(self):
        """Test model selection for simple facts."""
        model = select_optimal_model(
            complexity=ClaimComplexity.SIMPLE,
            privacy=PrivacyLevel.STANDARD,
            urgency=UrgencyLevel.NORMAL
        )
        assert model == LLMModel.GPT_4O_MINI
    
    def test_complex_scientific_claim(self):
        """Test model selection for complex scientific claims."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX,
            privacy=PrivacyLevel.STANDARD,
            urgency=UrgencyLevel.LOW
        )
        assert model == LLMModel.CLAUDE_3_HAIKU
    
    def test_urgent_breaking_news(self):
        """Test model selection for urgent breaking news verification."""
        model = select_optimal_model(
            complexity=ClaimComplexity.MODERATE,
            privacy=PrivacyLevel.STANDARD,
            urgency=UrgencyLevel.HIGH
        )
        assert model == LLMModel.CLAUDE_3_HAIKU
    
    def test_sensitive_political_claim(self):
        """Test model selection for sensitive political claims."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX,
            privacy=PrivacyLevel.SENSITIVE,
            urgency=UrgencyLevel.NORMAL
        )
        assert model == LLMModel.LLAMA_3_2
    
    def test_confidential_internal_claim(self):
        """Test model selection for confidential internal claims."""
        model = select_optimal_model(
            complexity=ClaimComplexity.SIMPLE,
            privacy=PrivacyLevel.CONFIDENTIAL,
            urgency=UrgencyLevel.HIGH
        )
        # Privacy should override even urgent requests
        assert model == LLMModel.LLAMA_3_2


if __name__ == "__main__":
    pytest.main([__file__])