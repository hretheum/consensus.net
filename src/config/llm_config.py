"""
LLM Configuration for ConsensusNet Agent System

Based on research documented in docs/research/llm-selection-analysis.md
Implements the hybrid three-tier LLM strategy.
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
    """Available LLM models with their provider mappings."""
    GPT_4O_MINI = "gpt-4o-mini"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    LLAMA_3_2 = "llama3.2"


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


# Model configurations based on research findings
LLM_CONFIGS = {
    LLMModel.GPT_4O_MINI: LLMConfig(
        model=LLMModel.GPT_4O_MINI,
        provider=LLMProvider.OPENAI,
        max_tokens=2000,
        temperature=0.1,
        max_requests_per_minute=10000,
        cost_per_input_token=0.15,  # $0.15 per 1M tokens
        cost_per_output_token=0.60,  # $0.60 per 1M tokens
        average_latency_ms=847,
        context_window=128000,
        accuracy_score=0.91,
        reasoning_quality=4.2,
        confidence_calibration=0.85
    ),
    
    LLMModel.CLAUDE_3_HAIKU: LLMConfig(
        model=LLMModel.CLAUDE_3_HAIKU,
        provider=LLMProvider.ANTHROPIC,
        max_tokens=2000,
        temperature=0.1,
        max_requests_per_minute=5000,
        cost_per_input_token=0.25,  # $0.25 per 1M tokens
        cost_per_output_token=1.25,  # $1.25 per 1M tokens
        average_latency_ms=623,
        context_window=200000,
        accuracy_score=0.88,
        reasoning_quality=4.4,
        confidence_calibration=0.88
    ),
    
    LLMModel.LLAMA_3_2: LLMConfig(
        model=LLMModel.LLAMA_3_2,
        provider=LLMProvider.OLLAMA,
        max_tokens=2000,
        temperature=0.1,
        max_requests_per_minute=1000,  # Hardware dependent
        cost_per_input_token=0.0,  # Fixed hosting cost
        cost_per_output_token=0.0,  # Fixed hosting cost
        average_latency_ms=1342,
        context_window=8192,
        accuracy_score=0.82,
        reasoning_quality=3.7,
        confidence_calibration=0.72
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
        return LLMModel.LLAMA_3_2
    
    # Complex reasoning: use Claude 3 Haiku for better analysis
    if complexity == ClaimComplexity.COMPLEX and urgency != UrgencyLevel.HIGH:
        return LLMModel.CLAUDE_3_HAIKU
    
    # High urgency: use fastest model (Claude 3 Haiku)
    if urgency == UrgencyLevel.HIGH:
        return LLMModel.CLAUDE_3_HAIKU
    
    # Default case: use GPT-4o-mini for best cost/performance balance
    return LLMModel.GPT_4O_MINI


def get_fallback_model(primary_model: LLMModel) -> LLMModel:
    """
    Get the appropriate fallback model if the primary model fails.
    
    Args:
        primary_model: The model that failed
        
    Returns:
        The fallback model to try next
    """
    fallback_chain = {
        LLMModel.GPT_4O_MINI: LLMModel.CLAUDE_3_HAIKU,
        LLMModel.CLAUDE_3_HAIKU: LLMModel.LLAMA_3_2,
        LLMModel.LLAMA_3_2: None  # No fallback for local model
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


# Export key configurations for use in the agent system
DEFAULT_PRIMARY_MODEL = LLMModel.GPT_4O_MINI
DEFAULT_SECONDARY_MODEL = LLMModel.CLAUDE_3_HAIKU
DEFAULT_FALLBACK_MODEL = LLMModel.LLAMA_3_2

# Usage tracking for cost monitoring
USAGE_TRACKING_ENABLED = True
DAILY_COST_LIMIT = 100.0  # USD per day
MONTHLY_COST_LIMIT = 2000.0  # USD per month