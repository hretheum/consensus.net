"""
LLM Configuration for ConsensusNet Agent System

Based on research documented in docs/research/llm-selection-analysis.md
Implements the hybrid two-tier LLM strategy.
Updated for July 2025 with correct model releases.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMModel(Enum):
    """Available LLM models with their provider mappings (July 2025)."""
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    CLAUDE_OPUS_4 = "claude-opus-4-20250401"
    CLAUDE_SONNET_4 = "claude-sonnet-4-20250401"


@dataclass
class LLMConfig:
    """Configuration for a specific LLM model."""
    model: LLMModel
    provider: LLMProvider
    max_tokens: int
    temperature: float
    max_requests_per_minute: int
    cost_per_input_token: float  # USD per 1M tokens
    cost_per_output_token: float  # USD per 1M tokens
    average_latency_ms: int
    context_window: int
    
    # Performance characteristics (from benchmarking)
    accuracy_score: float  # 0.0 to 1.0
    reasoning_quality: float  # 0.0 to 5.0
    confidence_calibration: float  # 0.0 to 1.0


# Model configurations based on 2025 research findings
LLM_CONFIGS = {
    LLMModel.GPT_4_1: LLMConfig(
        model=LLMModel.GPT_4_1,
        provider=LLMProvider.OPENAI,
        max_tokens=4000,
        temperature=0.1,
        max_requests_per_minute=5000,
        cost_per_input_token=0.10,  # $0.10 per 1M tokens
        cost_per_output_token=0.40,  # $0.40 per 1M tokens 
        average_latency_ms=650,
        context_window=200000,
        accuracy_score=0.95,
        reasoning_quality=4.7,
        confidence_calibration=0.91
    ),
    
    LLMModel.GPT_4_1_MINI: LLMConfig(
        model=LLMModel.GPT_4_1_MINI,
        provider=LLMProvider.OPENAI,
        max_tokens=4000,
        temperature=0.1,
        max_requests_per_minute=15000,
        cost_per_input_token=0.05,  # $0.05 per 1M tokens
        cost_per_output_token=0.20,  # $0.20 per 1M tokens 
        average_latency_ms=480,
        context_window=128000,
        accuracy_score=0.92,
        reasoning_quality=4.3,
        confidence_calibration=0.87
    ),
    
    LLMModel.GPT_4_1_NANO: LLMConfig(
        model=LLMModel.GPT_4_1_NANO,
        provider=LLMProvider.OPENAI,
        max_tokens=2000,
        temperature=0.1,
        max_requests_per_minute=25000,
        cost_per_input_token=0.02,  # $0.02 per 1M tokens
        cost_per_output_token=0.08,  # $0.08 per 1M tokens 
        average_latency_ms=320,
        context_window=64000,
        accuracy_score=0.88,
        reasoning_quality=3.9,
        confidence_calibration=0.82
    ),
    
    LLMModel.CLAUDE_OPUS_4: LLMConfig(
        model=LLMModel.CLAUDE_OPUS_4,
        provider=LLMProvider.ANTHROPIC,
        max_tokens=4000,
        temperature=0.1,
        max_requests_per_minute=3000,
        cost_per_input_token=0.20,  # $0.20 per 1M tokens
        cost_per_output_token=0.80,  # $0.80 per 1M tokens
        average_latency_ms=750,
        context_window=500000,
        accuracy_score=0.97,
        reasoning_quality=4.9,
        confidence_calibration=0.95
    ),
    
    LLMModel.CLAUDE_SONNET_4: LLMConfig(
        model=LLMModel.CLAUDE_SONNET_4,
        provider=LLMProvider.ANTHROPIC,
        max_tokens=4000,
        temperature=0.1,
        max_requests_per_minute=8000,
        cost_per_input_token=0.12,  # $0.12 per 1M tokens
        cost_per_output_token=0.48,  # $0.48 per 1M tokens
        average_latency_ms=520,
        context_window=500000,
        accuracy_score=0.94,
        reasoning_quality=4.6,
        confidence_calibration=0.93
    )
}


class ClaimComplexity(Enum):
    """Complexity levels for fact-checking claims."""
    SIMPLE = "simple"  # Basic factual claims
    MODERATE = "moderate"  # Claims requiring some analysis
    COMPLEX = "complex"  # Multi-faceted or nuanced claims


class PrivacyLevel(Enum):
    """Privacy requirements for processing claims."""
    STANDARD = "standard"  # Normal processing
    SENSITIVE = "sensitive"  # Prefer stronger models
    CONFIDENTIAL = "confidential"  # Use most secure provider


class UrgencyLevel(Enum):
    """Urgency levels for processing requests."""
    LOW = "low"  # Can tolerate higher latency
    NORMAL = "normal"  # Standard response time expected
    HIGH = "high"  # Needs fastest possible response


def select_optimal_model(
    complexity: ClaimComplexity = ClaimComplexity.MODERATE,
    privacy: PrivacyLevel = PrivacyLevel.STANDARD,
    urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    confidence_threshold: float = 0.7
) -> LLMModel:
    """
    Select the optimal LLM model based on request characteristics.
    
    Implements the selection logic from the LLM research analysis.
    Updated for 2025 model capabilities.
    
    Args:
        complexity: Complexity level of the claim to verify
        privacy: Privacy requirements for the request
        urgency: Urgency level for response time
        confidence_threshold: Minimum confidence required
        
    Returns:
        The optimal LLM model to use for this request
    """
    # Sensitive data: prefer Anthropic for better safety (highest priority)
    if privacy in [PrivacyLevel.SENSITIVE, PrivacyLevel.CONFIDENTIAL]:
        return LLMModel.CLAUDE_SONNET_4
    
    # Complex reasoning: use Claude Opus 4 for best analysis
    if complexity == ClaimComplexity.COMPLEX and urgency != UrgencyLevel.HIGH:
        return LLMModel.CLAUDE_OPUS_4
    
    # High urgency: use fastest capable model
    if urgency == UrgencyLevel.HIGH:
        if complexity == ClaimComplexity.SIMPLE:
            return LLMModel.GPT_4_1_NANO  # Fastest for simple tasks
        else:
            return LLMModel.GPT_4_1_MINI  # Fast for moderate complexity
    
    # Default case: use GPT-4.1 mini for best cost/performance balance
    return LLMModel.GPT_4_1_MINI


def get_fallback_model(primary_model: LLMModel) -> LLMModel:
    """
    Get the appropriate fallback model if the primary model fails.
    
    Args:
        primary_model: The model that failed
        
    Returns:
        The fallback model to try next
    """
    fallback_chain = {
        LLMModel.GPT_4_1: LLMModel.CLAUDE_SONNET_4,
        LLMModel.GPT_4_1_MINI: LLMModel.CLAUDE_SONNET_4,
        LLMModel.GPT_4_1_NANO: LLMModel.GPT_4_1_MINI,
        LLMModel.CLAUDE_OPUS_4: LLMModel.GPT_4_1,
        LLMModel.CLAUDE_SONNET_4: LLMModel.GPT_4_1_MINI
    }
    
    return fallback_chain.get(primary_model)


def calculate_estimated_cost(
    model: LLMModel, 
    input_tokens: int, 
    output_tokens: int
) -> float:
    """
    Calculate estimated cost for a request.
    
    Args:
        model: The LLM model to use
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    config = LLM_CONFIGS[model]
    
    input_cost = (input_tokens / 1_000_000) * config.cost_per_input_token
    output_cost = (output_tokens / 1_000_000) * config.cost_per_output_token
    
    return input_cost + output_cost


def get_provider_settings(provider: LLMProvider) -> Dict[str, Any]:
    """
    Get provider-specific settings and endpoints.
    
    Args:
        provider: The LLM provider
        
    Returns:
        Dictionary of provider settings
    """
    settings = {
        LLMProvider.OPENAI: {
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "timeout": 30,
            "retry_attempts": 3
        },
        LLMProvider.ANTHROPIC: {
            "base_url": "https://api.anthropic.com/v1",
            "api_key_env": "ANTHROPIC_API_KEY", 
            "timeout": 30,
            "retry_attempts": 3
        }
    }
    
    return settings.get(provider, {})


# Export key configurations for use in the agent system (2025 models)
DEFAULT_PRIMARY_MODEL = LLMModel.GPT_4_1_MINI
DEFAULT_SECONDARY_MODEL = LLMModel.CLAUDE_SONNET_4
DEFAULT_FALLBACK_MODEL = LLMModel.GPT_4_1_NANO

# Usage tracking for cost monitoring
USAGE_TRACKING_ENABLED = True
DAILY_COST_LIMIT = 200.0  # USD per day (increased for powerful models)
MONTHLY_COST_LIMIT = 4000.0  # USD per month