"""
LLM Configuration for ConsensusNet Agent System

Based on research documented in docs/research/llm-selection-analysis.md
Implements the hybrid three-tier LLM strategy.
Updated for July 2025 with latest model releases.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class LLMModel(Enum):
    """Available LLM models with their provider mappings (July 2025)."""
    GPT_5 = "gpt-5"
    CLAUDE_4_SONNET = "claude-4-sonnet-20250401"
    LLAMA_4 = "llama4"


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
    LLMModel.GPT_5: LLMConfig(
        model=LLMModel.GPT_5,
        provider=LLMProvider.OPENAI,
        max_tokens=4000,
        temperature=0.1,
        max_requests_per_minute=15000,
        cost_per_input_token=0.08,  # $0.08 per 1M tokens (improved efficiency)
        cost_per_output_token=0.32,  # $0.32 per 1M tokens 
        average_latency_ms=580,
        context_window=200000,
        accuracy_score=0.96,
        reasoning_quality=4.8,
        confidence_calibration=0.92
    ),
    
    LLMModel.CLAUDE_4_SONNET: LLMConfig(
        model=LLMModel.CLAUDE_4_SONNET,
        provider=LLMProvider.ANTHROPIC,
        max_tokens=4000,
        temperature=0.1,
        max_requests_per_minute=8000,
        cost_per_input_token=0.12,  # $0.12 per 1M tokens
        cost_per_output_token=0.48,  # $0.48 per 1M tokens
        average_latency_ms=420,
        context_window=500000,
        accuracy_score=0.94,
        reasoning_quality=4.9,
        confidence_calibration=0.94
    ),
    
    LLMModel.LLAMA_4: LLMConfig(
        model=LLMModel.LLAMA_4,
        provider=LLMProvider.OLLAMA,
        max_tokens=4000,
        temperature=0.1,
        max_requests_per_minute=2000,  # Hardware dependent
        cost_per_input_token=0.0,  # Fixed hosting cost
        cost_per_output_token=0.0,  # Fixed hosting cost
        average_latency_ms=890,
        context_window=128000,
        accuracy_score=0.88,
        reasoning_quality=4.3,
        confidence_calibration=0.83
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
    SENSITIVE = "sensitive"  # Prefer local processing
    CONFIDENTIAL = "confidential"  # Must use local processing


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
    # Privacy override: use local model for sensitive/confidential data
    if privacy in [PrivacyLevel.SENSITIVE, PrivacyLevel.CONFIDENTIAL]:
        return LLMModel.LLAMA_4
    
    # Complex reasoning: use Claude 4 Sonnet for superior analysis
    if complexity == ClaimComplexity.COMPLEX and urgency != UrgencyLevel.HIGH:
        return LLMModel.CLAUDE_4_SONNET
    
    # High urgency: use fastest model (Claude 4 Sonnet)
    if urgency == UrgencyLevel.HIGH:
        return LLMModel.CLAUDE_4_SONNET
    
    # Default case: use GPT-5 for excellent cost/performance balance
    return LLMModel.GPT_5


def get_fallback_model(primary_model: LLMModel) -> LLMModel:
    """
    Get the appropriate fallback model if the primary model fails.
    
    Args:
        primary_model: The model that failed
        
    Returns:
        The fallback model to try next
    """
    fallback_chain = {
        LLMModel.GPT_5: LLMModel.CLAUDE_4_SONNET,
        LLMModel.CLAUDE_4_SONNET: LLMModel.LLAMA_4,
        LLMModel.LLAMA_4: None  # No fallback for local model
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
    
    # For local models, cost is essentially zero per request
    if config.provider == LLMProvider.OLLAMA:
        return 0.0
    
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
        },
        LLMProvider.OLLAMA: {
            "base_url": "http://localhost:11434",
            "api_key_env": None,  # No API key needed for local
            "timeout": 60,  # Longer timeout for local processing
            "retry_attempts": 2
        }
    }
    
    return settings.get(provider, {})


# Export key configurations for use in the agent system (2025 models)
DEFAULT_PRIMARY_MODEL = LLMModel.GPT_5
DEFAULT_SECONDARY_MODEL = LLMModel.CLAUDE_4_SONNET
DEFAULT_FALLBACK_MODEL = LLMModel.LLAMA_4

# Usage tracking for cost monitoring
USAGE_TRACKING_ENABLED = True
DAILY_COST_LIMIT = 150.0  # USD per day (increased for more powerful models)
MONTHLY_COST_LIMIT = 3000.0  # USD per month