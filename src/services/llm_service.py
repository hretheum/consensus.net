"""
Real LLM Service for ConsensusNet

Implements actual API connections to OpenAI, Anthropic, and Together AI
based on the 3-tier LLM strategy defined in config/llm_config.py
"""

import os
import asyncio
import aiohttp
import time
import json
from typing import Dict, Any, Optional, List
from dataclasses import asdict

from src.config.llm_config import (
    LLMModel, LLMProvider, LLMConfig, LLM_CONFIGS,
    select_optimal_model, get_fallback_model, get_provider_settings,
    ClaimComplexity, PrivacyLevel, UrgencyLevel
)
from src.agents.agent_models import LLMRequest, LLMResponse


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class LLMAPIError(LLMServiceError):
    """Error during API communication."""
    pass


class LLMRateLimitError(LLMServiceError):
    """Rate limit exceeded."""
    pass


class LLMService:
    """
    Production LLM service with real API connections.
    
    Implements the 3-tier LLM strategy:
    - Tier 1: GPT-4o-mini (primary, cost-effective)
    - Tier 2: Claude 3 Haiku (fallback, better reasoning)
    - Tier 3: Llama 3.2 (local fallback, privacy)
    """
    
    def __init__(self):
        """Initialize the LLM service with API configurations."""
        self.session = None
        self.usage_tracking = {
            "requests_today": 0,
            "cost_today": 0.0,
            "tokens_used": {
                "input": 0,
                "output": 0
            }
        }
        
        # Check API key availability
        self.available_providers = self._check_api_availability()
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _check_api_availability(self) -> Dict[LLMProvider, bool]:
        """Check which API providers are available based on environment variables."""
        availability = {}
        
        # Check OpenAI
        availability[LLMProvider.OPENAI] = bool(os.getenv("OPENAI_API_KEY"))
        
        # Check Anthropic
        availability[LLMProvider.ANTHROPIC] = bool(os.getenv("ANTHROPIC_API_KEY"))
        
        # Check Ollama (local)
        availability[LLMProvider.OLLAMA] = True  # Assume local is available
        
        return availability
    
    def generate_verification_prompt(self, claim: str, complexity: ClaimComplexity = ClaimComplexity.MODERATE) -> str:
        """
        Generate a comprehensive verification prompt for LLM analysis.
        
        Args:
            claim: The claim to verify
            complexity: Complexity level of the claim
            
        Returns:
            Formatted prompt for LLM analysis
        """
        base_prompt = f"""You are a fact-checking expert tasked with verifying the following claim:

CLAIM: "{claim}"

Please provide a comprehensive verification analysis with the following structure:

1. VERDICT: State whether the claim is TRUE, FALSE, or UNCERTAIN
2. CONFIDENCE: Rate your confidence from 0.0 (no confidence) to 1.0 (completely certain)
3. REASONING: Provide detailed reasoning for your verdict, including:
   - Key evidence that supports or contradicts the claim
   - Any important context or nuances
   - Limitations of available information
4. CONCERNS: Note any potential biases, missing information, or areas of uncertainty

Requirements:
- Be precise and factual
- Acknowledge uncertainty when evidence is insufficient
- Consider multiple perspectives when relevant
- Base conclusions on verifiable information

Format your response as JSON with the following structure:
{{
    "verdict": "TRUE|FALSE|UNCERTAIN",
    "confidence": 0.XX,
    "reasoning": "Your detailed reasoning here",
    "concerns": ["List of concerns or limitations"],
    "key_evidence": ["List of key evidence points"]
}}"""

        # Add complexity-specific instructions
        if complexity == ClaimComplexity.COMPLEX:
            base_prompt += "\n\nNote: This is a complex claim requiring nuanced analysis. Consider multiple angles and potential edge cases."
        elif complexity == ClaimComplexity.SIMPLE:
            base_prompt += "\n\nNote: This is a straightforward factual claim. Focus on clear, direct evidence."
        
        return base_prompt
    
    async def call_openai(self, request: LLMRequest) -> LLMResponse:
        """Call OpenAI GPT-4o-mini API."""
        config = LLM_CONFIGS[LLMModel.GPT_4O_MINI]
        settings = get_provider_settings(LLMProvider.OPENAI)
        
        headers = {
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.model.value,
            "messages": [
                {"role": "user", "content": request.prompt}
            ],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature
        }
        
        try:
            async with self.session.post(
                f"{settings['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=settings['timeout']
            ) as response:
                
                if response.status == 429:
                    raise LLMRateLimitError("OpenAI rate limit exceeded")
                elif response.status != 200:
                    raise LLMAPIError(f"OpenAI API error: {response.status}")
                
                data = await response.json()
                
                return LLMResponse(
                    content=data['choices'][0]['message']['content'],
                    metadata={
                        "provider": "openai",
                        "model": config.model.value,
                        "finish_reason": data['choices'][0]['finish_reason']
                    },
                    model_used=config.model.value,
                    tokens_used=data['usage']['total_tokens'],
                    confidence=None  # Will be extracted from content
                )
                
        except asyncio.TimeoutError:
            raise LLMAPIError("OpenAI API timeout")
        except Exception as e:
            raise LLMAPIError(f"OpenAI API error: {str(e)}")
    
    async def call_anthropic(self, request: LLMRequest) -> LLMResponse:
        """Call Anthropic Claude 3 Haiku API."""
        config = LLM_CONFIGS[LLMModel.CLAUDE_3_HAIKU]
        settings = get_provider_settings(LLMProvider.ANTHROPIC)
        
        headers = {
            "x-api-key": os.getenv('ANTHROPIC_API_KEY'),
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": config.model.value,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "messages": [
                {"role": "user", "content": request.prompt}
            ]
        }
        
        try:
            async with self.session.post(
                f"{settings['base_url']}/messages",
                headers=headers,
                json=payload,
                timeout=settings['timeout']
            ) as response:
                
                if response.status == 429:
                    raise LLMRateLimitError("Anthropic rate limit exceeded")
                elif response.status != 200:
                    raise LLMAPIError(f"Anthropic API error: {response.status}")
                
                data = await response.json()
                
                return LLMResponse(
                    content=data['content'][0]['text'],
                    metadata={
                        "provider": "anthropic",
                        "model": config.model.value,
                        "stop_reason": data.get('stop_reason')
                    },
                    model_used=config.model.value,
                    tokens_used=data['usage']['input_tokens'] + data['usage']['output_tokens'],
                    confidence=None  # Will be extracted from content
                )
                
        except asyncio.TimeoutError:
            raise LLMAPIError("Anthropic API timeout")
        except Exception as e:
            raise LLMAPIError(f"Anthropic API error: {str(e)}")
    
    async def call_ollama(self, request: LLMRequest) -> LLMResponse:
        """Call local Ollama Llama 3.2 API."""
        config = LLM_CONFIGS[LLMModel.LLAMA_3_2]
        settings = get_provider_settings(LLMProvider.OLLAMA)
        
        payload = {
            "model": config.model.value,
            "prompt": request.prompt,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "num_predict": config.max_tokens
            }
        }
        
        try:
            async with self.session.post(
                f"{settings['base_url']}/api/generate",
                json=payload,
                timeout=settings['timeout']
            ) as response:
                
                if response.status != 200:
                    raise LLMAPIError(f"Ollama API error: {response.status}")
                
                data = await response.json()
                
                # Estimate tokens (Ollama doesn't always provide token counts)
                estimated_tokens = len(request.prompt.split()) + len(data['response'].split())
                
                return LLMResponse(
                    content=data['response'],
                    metadata={
                        "provider": "ollama",
                        "model": config.model.value,
                        "eval_count": data.get('eval_count', 0)
                    },
                    model_used=config.model.value,
                    tokens_used=estimated_tokens,
                    confidence=None  # Will be extracted from content
                )
                
        except asyncio.TimeoutError:
            raise LLMAPIError("Ollama API timeout")
        except Exception as e:
            raise LLMAPIError(f"Ollama API error: {str(e)}")
    
    def extract_structured_response(self, content: str) -> Dict[str, Any]:
        """
        Extract structured data from LLM response.
        
        Args:
            content: Raw LLM response content
            
        Returns:
            Parsed structured response or fallback data
        """
        try:
            # Try to find JSON in the response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Fallback: parse manually
        verdict = "UNCERTAIN"
        confidence = 0.3
        reasoning = content
        
        content_lower = content.lower()
        
        # Extract verdict
        if "verdict" in content_lower:
            if "true" in content_lower:
                verdict = "TRUE"
            elif "false" in content_lower:
                verdict = "FALSE"
        
        # Extract confidence
        import re
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', content_lower)
        if confidence_match:
            try:
                confidence = float(confidence_match.group(1))
                if confidence > 1.0:
                    confidence = confidence / 100.0  # Convert percentage
            except ValueError:
                pass
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "reasoning": reasoning,
            "concerns": [],
            "key_evidence": []
        }
    
    async def call_llm_with_fallback(
        self, 
        request: LLMRequest,
        complexity: ClaimComplexity = ClaimComplexity.MODERATE,
        privacy: PrivacyLevel = PrivacyLevel.STANDARD,
        urgency: UrgencyLevel = UrgencyLevel.NORMAL
    ) -> LLMResponse:
        """
        Call LLM with automatic fallback based on the 3-tier strategy.
        
        Args:
            request: LLM request
            complexity: Claim complexity level
            privacy: Privacy requirements
            urgency: Urgency level
            
        Returns:
            LLM response from the successful provider
        """
        # Select optimal model
        primary_model = select_optimal_model(complexity, privacy, urgency)
        
        # Try primary model
        if not self.session:
            raise LLMServiceError("LLM service not initialized. Use async context manager.")
        
        errors = []
        
        for model in [primary_model, get_fallback_model(primary_model)]:
            if model is None:
                continue
                
            config = LLM_CONFIGS[model]
            
            # Skip if provider not available
            if not self.available_providers.get(config.provider, False):
                errors.append(f"{config.provider.value} not available (missing API key)")
                continue
            
            try:
                start_time = time.time()
                
                # Call appropriate provider
                if config.provider == LLMProvider.OPENAI:
                    response = await self.call_openai(request)
                elif config.provider == LLMProvider.ANTHROPIC:
                    response = await self.call_anthropic(request)
                elif config.provider == LLMProvider.OLLAMA:
                    response = await self.call_ollama(request)
                else:
                    raise LLMServiceError(f"Unsupported provider: {config.provider}")
                
                # Extract structured data from response
                structured_data = self.extract_structured_response(response.content)
                response.confidence = structured_data.get("confidence", 0.5)
                
                # Update usage tracking
                self.usage_tracking["requests_today"] += 1
                self.usage_tracking["tokens_used"]["input"] += len(request.prompt.split())
                self.usage_tracking["tokens_used"]["output"] += len(response.content.split())
                
                # Add timing and structured data to metadata
                response.metadata.update({
                    "response_time_ms": int((time.time() - start_time) * 1000),
                    "structured_data": structured_data,
                    "fallback_used": model != primary_model
                })
                
                return response
                
            except (LLMAPIError, LLMRateLimitError) as e:
                errors.append(f"{model.value}: {str(e)}")
                continue
        
        # All models failed
        raise LLMServiceError(f"All LLM providers failed: {'; '.join(errors)}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return {
            "usage_tracking": self.usage_tracking,
            "available_providers": {
                provider.value: available 
                for provider, available in self.available_providers.items()
            },
            "provider_configs": {
                model.value: {
                    "provider": config.provider.value,
                    "max_tokens": config.max_tokens,
                    "cost_per_request_estimate": config.cost_per_input_token + config.cost_per_output_token
                }
                for model, config in LLM_CONFIGS.items()
            }
        }


# Global LLM service instance
llm_service = LLMService()