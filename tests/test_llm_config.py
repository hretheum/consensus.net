"""
Test suite for LLM configuration and model selection logic.

Tests the LLM configuration system that implements the research findings
documented in docs/research/llm-selection-analysis.md
"""

import pytest
from src.config.llm_config import (
    LLMModel, LLM_CONFIGS, ClaimComplexity, PrivacyLevel, UrgencyLevel,
    select_optimal_model, get_fallback_model, calculate_estimated_cost
)


class TestLLMConfiguration:
    """Test LLM configuration settings and data integrity."""
    
    def test_all_models_have_configs(self):
        """Test that all defined models have complete configurations."""
        for model in LLMModel:
            assert model in LLM_CONFIGS, f"Model {model} missing configuration"
            
            config = LLM_CONFIGS[model]
            assert config.model == model
            assert config.max_tokens > 0
            assert 0.0 <= config.temperature <= 2.0
            assert config.max_requests_per_minute > 0
            assert config.cost_per_input_token >= 0.0
            assert config.cost_per_output_token >= 0.0
            assert config.average_latency_ms > 0
            assert config.context_window > 0
    
    def test_config_completeness(self):
        """Test that configurations have all required performance metrics."""
        for model, config in LLM_CONFIGS.items():
            assert 0.0 <= config.accuracy_score <= 1.0
            assert 0.0 <= config.reasoning_quality <= 5.0
            assert 0.0 <= config.confidence_calibration <= 1.0
    
    def test_performance_characteristics(self):
        """Test that performance characteristics match research findings."""
        gpt_config = LLM_CONFIGS[LLMModel.GPT_4_1]
        claude_config = LLM_CONFIGS[LLMModel.CLAUDE_OPUS_4]
        nano_config = LLM_CONFIGS[LLMModel.GPT_4_1_NANO]
        
        # Claude Opus 4 should have highest accuracy and reasoning
        assert claude_config.accuracy_score >= gpt_config.accuracy_score
        assert claude_config.reasoning_quality >= gpt_config.reasoning_quality
        
        # Nano should be fastest
        assert nano_config.average_latency_ms <= gpt_config.average_latency_ms


class TestModelSelection:
    """Test model selection logic for different scenarios."""
    
    def test_default_selection(self):
        """Test default model selection returns GPT-4.1 mini."""
        model = select_optimal_model()
        assert model == LLMModel.GPT_4_1_MINI
    
    def test_privacy_override(self):
        """Test that privacy requirements override other selections."""
        # Sensitive data should use Claude Sonnet 4
        model = select_optimal_model(privacy=PrivacyLevel.SENSITIVE)
        assert model == LLMModel.CLAUDE_SONNET_4
        
        # Confidential data should use Claude Sonnet 4
        model = select_optimal_model(privacy=PrivacyLevel.CONFIDENTIAL)
        assert model == LLMModel.CLAUDE_SONNET_4
    
    def test_complex_reasoning_selection(self):
        """Test that complex reasoning selects Claude Opus 4."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX,
            urgency=UrgencyLevel.LOW
        )
        assert model == LLMModel.CLAUDE_OPUS_4
    
    def test_urgency_override(self):
        """Test that high urgency selects fastest appropriate model."""
        # Simple + urgent = nano
        model = select_optimal_model(
            complexity=ClaimComplexity.SIMPLE,
            urgency=UrgencyLevel.HIGH
        )
        assert model == LLMModel.GPT_4_1_NANO
        
        # Moderate + urgent = mini
        model = select_optimal_model(
            complexity=ClaimComplexity.MODERATE,
            urgency=UrgencyLevel.HIGH
        )
        assert model == LLMModel.GPT_4_1_MINI
    
    def test_urgency_overrides_complexity(self):
        """Test that high urgency overrides complex reasoning preference."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX,
            urgency=UrgencyLevel.HIGH
        )
        # Should prefer speed over reasoning quality for urgent requests
        assert model == LLMModel.GPT_4_1_MINI


class TestFallbackLogic:
    """Test fallback model selection."""
    
    def test_gpt_fallback(self):
        """Test GPT-4.1 fallback is Claude Sonnet 4."""
        fallback = get_fallback_model(LLMModel.GPT_4_1)
        assert fallback == LLMModel.CLAUDE_SONNET_4
    
    def test_claude_opus_fallback(self):
        """Test Claude Opus 4 fallback is GPT-4.1."""
        fallback = get_fallback_model(LLMModel.CLAUDE_OPUS_4)
        assert fallback == LLMModel.GPT_4_1
    
    def test_nano_fallback(self):
        """Test Nano fallback is Mini."""
        fallback = get_fallback_model(LLMModel.GPT_4_1_NANO)
        assert fallback == LLMModel.GPT_4_1_MINI


class TestCostCalculation:
    """Test cost calculation functionality."""
    
    def test_gpt_cost_calculation(self):
        """Test GPT-4.1 mini cost calculation."""
        # Example: 100 input tokens, 50 output tokens
        cost = calculate_estimated_cost(LLMModel.GPT_4_1_MINI, 100, 50)
        expected = (100 / 1_000_000) * 0.05 + (50 / 1_000_000) * 0.20
        assert abs(cost - expected) < 0.000001
    
    def test_claude_cost_calculation(self):
        """Test Claude Opus 4 cost calculation."""
        cost = calculate_estimated_cost(LLMModel.CLAUDE_OPUS_4, 100, 50)
        expected = (100 / 1_000_000) * 0.20 + (50 / 1_000_000) * 0.80
        assert abs(cost - expected) < 0.000001
    
    def test_cost_scaling(self):
        """Test cost scales linearly with token usage."""
        base_cost = calculate_estimated_cost(LLMModel.GPT_4_1_MINI, 100, 50)
        double_cost = calculate_estimated_cost(LLMModel.GPT_4_1_MINI, 200, 100)
        assert abs(double_cost - (2 * base_cost)) < 0.000001


class TestModelSelectionScenarios:
    """Test realistic model selection scenarios."""
    
    def test_simple_fact_verification(self):
        """Test simple fact verification uses cost-effective model."""
        model = select_optimal_model(
            complexity=ClaimComplexity.SIMPLE,
            privacy=PrivacyLevel.STANDARD,
            urgency=UrgencyLevel.NORMAL
        )
        assert model == LLMModel.GPT_4_1_MINI
    
    def test_complex_scientific_claim(self):
        """Test complex scientific claim uses best reasoning model."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX,
            privacy=PrivacyLevel.STANDARD,
            urgency=UrgencyLevel.LOW
        )
        assert model == LLMModel.CLAUDE_OPUS_4
    
    def test_urgent_breaking_news(self):
        """Test urgent breaking news uses fast model."""
        model = select_optimal_model(
            complexity=ClaimComplexity.MODERATE,
            privacy=PrivacyLevel.STANDARD,
            urgency=UrgencyLevel.HIGH
        )
        assert model == LLMModel.GPT_4_1_MINI
    
    def test_sensitive_political_claim(self):
        """Test sensitive political claim uses secure provider."""
        model = select_optimal_model(
            complexity=ClaimComplexity.MODERATE,
            privacy=PrivacyLevel.SENSITIVE,
            urgency=UrgencyLevel.NORMAL
        )
        assert model == LLMModel.CLAUDE_SONNET_4
    
    def test_confidential_internal_claim(self):
        """Test confidential internal claim prioritizes security."""
        model = select_optimal_model(
            complexity=ClaimComplexity.COMPLEX,
            privacy=PrivacyLevel.CONFIDENTIAL,
            urgency=UrgencyLevel.HIGH
        )
        # Privacy should override even urgent requests
        assert model == LLMModel.CLAUDE_SONNET_4


if __name__ == "__main__":
    pytest.main([__file__])