"""
Real LLM client implementation for ConsensusNet.

Provides actual API integration with OpenAI, Anthropic, and Ollama.
"""

import os
import time
import json
import logging
from typing import Dict, Any, Optional
import asyncio
import aiohttp
import openai
from anthropic import Anthropic

from ..agents.agent_models import LLMRequest, LLMResponse, ProcessedClaim
from ..config.llm_config import LLMProvider, LLMModel, get_provider_settings, LLM_CONFIGS
from .error_handling import (
    LLMError, APIError, RateLimitError, TimeoutError, 
    ConfigurationError, ModelNotAvailableError
)

logger = logging.getLogger(__name__)


class RealLLMInteraction:
    """
    Real LLM interaction implementation with actual API calls.
    
    Supports OpenAI, Anthropic, and Ollama providers with comprehensive
    error handling and retry logic.
    """
    
    def __init__(self, default_model: LLMModel = LLMModel.GPT_4O_MINI):
        """
        Initialize the real LLM client.
        
        Args:
            default_model: Default model to use for requests
        """
        self.default_model = default_model
        self._clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize API clients for different providers."""
        try:
            # Initialize OpenAI client
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self._clients[LLMProvider.OPENAI] = openai.OpenAI(api_key=openai_key)
                logger.info("OpenAI client initialized")
            else:
                logger.warning("OPENAI_API_KEY not found, OpenAI unavailable")
            
            # Initialize Anthropic client
            anthropic_key = os.getenv("ANTHROPIC_API_KEY")
            if anthropic_key:
                self._clients[LLMProvider.ANTHROPIC] = Anthropic(api_key=anthropic_key)
                logger.info("Anthropic client initialized")
            else:
                logger.warning("ANTHROPIC_API_KEY not found, Anthropic unavailable")
            
            # Ollama doesn't need API keys, just check if endpoint is available
            self._clients[LLMProvider.OLLAMA] = "available"  # Placeholder
            logger.info("Ollama client configured")
            
        except Exception as e:
            logger.error(f"Error initializing LLM clients: {e}")
            raise ConfigurationError(f"Failed to initialize LLM clients: {e}")
    
    def generate_verification_prompt(self, claim: ProcessedClaim) -> str:
        """Generate verification prompt for the claim."""
        return f"""You are a professional fact-checker. Please verify the following claim:

Claim: "{claim.original_text}"

Context:
- Domain: {claim.domain}
- Complexity: {claim.complexity.value}
- Additional context: {claim.context}

Please provide:
1. Your verdict: TRUE, FALSE, or UNCERTAIN
2. Your confidence level (0.0 to 1.0)
3. Clear reasoning for your assessment
4. Any relevant concerns or limitations

Format your response as:
Verdict: [TRUE/FALSE/UNCERTAIN]
Confidence: [0.0-1.0]
Reasoning: [Your detailed reasoning here]"""
    
    async def call_llm_async(self, request: LLMRequest) -> LLMResponse:
        """
        Make asynchronous LLM API call.
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with content and metadata
        """
        model_config = LLM_CONFIGS.get(LLMModel(request.model))
        if not model_config:
            raise ModelNotAvailableError(f"Model {request.model} not configured")
        
        provider = model_config.provider
        provider_settings = get_provider_settings(provider)
        
        # Check if provider client is available
        if provider not in self._clients:
            raise ConfigurationError(f"Provider {provider.value} not configured")
        
        start_time = time.time()
        
        try:
            if provider == LLMProvider.OPENAI:
                response = await self._call_openai(request, model_config, provider_settings)
            elif provider == LLMProvider.ANTHROPIC:
                response = await self._call_anthropic(request, model_config, provider_settings)
            elif provider == LLMProvider.OLLAMA:
                response = await self._call_ollama(request, model_config, provider_settings)
            else:
                raise ConfigurationError(f"Unsupported provider: {provider}")
            
            processing_time = time.time() - start_time
            response.metadata["processing_time"] = processing_time
            
            return response
            
        except Exception as e:
            if isinstance(e, LLMError):
                raise
            else:
                logger.error(f"Unexpected error in LLM call: {e}")
                raise LLMError(f"Unexpected error: {str(e)}") from e
    
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """
        Synchronous wrapper for LLM API call.
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with content and metadata
        """
        try:
            # Run async call in event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create new event loop for sync call if one is already running
                import nest_asyncio
                nest_asyncio.apply()
                return loop.run_until_complete(self.call_llm_async(request))
            else:
                return loop.run_until_complete(self.call_llm_async(request))
        except Exception:
            # Fallback to new event loop
            return asyncio.run(self.call_llm_async(request))
    
    async def _call_openai(self, request: LLMRequest, config, settings) -> LLMResponse:
        """Call OpenAI API."""
        client = self._clients[LLMProvider.OPENAI]
        
        try:
            # Prepare request parameters
            params = {
                "model": request.model,
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                **request.parameters
            }
            
            # Make API call with retry logic
            response = await self._retry_api_call(
                lambda: client.chat.completions.create(**params),
                settings.get("retry_attempts", 3),
                settings.get("timeout", 30)
            )
            
            # Extract response content
            content = response.choices[0].message.content
            tokens_used = response.usage.total_tokens if response.usage else 0
            
            return LLMResponse(
                content=content,
                metadata={
                    "model": request.model,
                    "provider": "openai",
                    "finish_reason": response.choices[0].finish_reason,
                    "created": response.created
                },
                model_used=request.model,
                tokens_used=tokens_used,
                confidence=self._extract_confidence(content)
            )
            
        except openai.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {e}")
        except openai.APITimeoutError as e:
            raise TimeoutError(f"OpenAI request timeout: {e}")
        except openai.APIError as e:
            raise APIError(f"OpenAI API error: {e}", getattr(e, 'status_code', None))
    
    async def _call_anthropic(self, request: LLMRequest, config, settings) -> LLMResponse:
        """Call Anthropic API."""
        client = self._clients[LLMProvider.ANTHROPIC]
        
        try:
            # Prepare request parameters
            params = {
                "model": request.model,
                "messages": [{"role": "user", "content": request.prompt}],
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                **request.parameters
            }
            
            # Make API call with retry logic
            response = await self._retry_api_call(
                lambda: client.messages.create(**params),
                settings.get("retry_attempts", 3),
                settings.get("timeout", 30)
            )
            
            # Extract response content
            content = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens
            
            return LLMResponse(
                content=content,
                metadata={
                    "model": request.model,
                    "provider": "anthropic",
                    "stop_reason": response.stop_reason,
                    "message_id": response.id
                },
                model_used=request.model,
                tokens_used=tokens_used,
                confidence=self._extract_confidence(content)
            )
            
        except Exception as e:
            # Handle Anthropic-specific errors
            if hasattr(e, 'status_code'):
                if e.status_code == 429:
                    raise RateLimitError(f"Anthropic rate limit exceeded: {e}")
                else:
                    raise APIError(f"Anthropic API error: {e}", e.status_code)
            else:
                raise LLMError(f"Anthropic error: {e}")
    
    async def _call_ollama(self, request: LLMRequest, config, settings) -> LLMResponse:
        """Call Ollama API."""
        base_url = settings.get("base_url", "http://localhost:11434")
        timeout = settings.get("timeout", 60)
        
        try:
            # Prepare request payload
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens,
                    **request.parameters
                },
                "stream": False
            }
            
            # Make HTTP request to Ollama
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(timeout)) as session:
                async with session.post(f"{base_url}/api/generate", json=payload) as response:
                    if response.status != 200:
                        raise APIError(f"Ollama API error: {response.status}", response.status)
                    
                    result = await response.json()
                    
                    content = result.get("response", "")
                    
                    return LLMResponse(
                        content=content,
                        metadata={
                            "model": request.model,
                            "provider": "ollama",
                            "total_duration": result.get("total_duration"),
                            "load_duration": result.get("load_duration"),
                            "prompt_eval_count": result.get("prompt_eval_count"),
                            "eval_count": result.get("eval_count")
                        },
                        model_used=request.model,
                        tokens_used=result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
                        confidence=self._extract_confidence(content)
                    )
        
        except aiohttp.ClientTimeout:
            raise TimeoutError("Ollama request timeout")
        except aiohttp.ClientError as e:
            raise APIError(f"Ollama connection error: {e}")
    
    async def _retry_api_call(self, api_func, max_retries: int, timeout: int):
        """
        Retry API call with exponential backoff.
        
        Args:
            api_func: Function to call the API
            max_retries: Maximum number of retry attempts
            timeout: Request timeout in seconds
        """
        for attempt in range(max_retries + 1):
            try:
                return api_func()
            except Exception as e:
                if attempt == max_retries:
                    raise
                
                # Check if error is retryable
                if not self._is_retryable_error(e):
                    raise
                
                # Exponential backoff
                wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                logger.warning(f"API call failed (attempt {attempt + 1}), retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable."""
        # Rate limits and temporary server errors are retryable
        if isinstance(error, (RateLimitError, TimeoutError)):
            return True
        
        if isinstance(error, APIError):
            # Retry on 5xx server errors, but not 4xx client errors
            return error.status_code >= 500
        
        # Network errors are typically retryable
        if isinstance(error, (aiohttp.ClientError, ConnectionError)):
            return True
        
        return False
    
    def _extract_confidence(self, content: str) -> Optional[float]:
        """Extract confidence score from LLM response content."""
        try:
            # Look for confidence patterns in the response
            import re
            confidence_patterns = [
                r"Confidence:\s*(-?\d*\.?\d+)",
                r"confidence:\s*(-?\d*\.?\d+)",
                r"Confidence level:\s*(-?\d*\.?\d+)"
            ]
            
            for pattern in confidence_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    confidence = float(match.group(1))
                    # Ensure confidence is in valid range
                    return max(0.0, min(1.0, confidence))
            
            return None
        except Exception:
            return None
    
    def is_available(self, provider: LLMProvider) -> bool:
        """Check if a provider is available."""
        return provider in self._clients
    
    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of available providers."""
        return list(self._clients.keys())