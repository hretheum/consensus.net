"""
LLM Error handling for ConsensusNet.

Defines custom exceptions for LLM API integration issues.
"""

class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class APIError(LLMError):
    """Exception for API-specific errors (4xx, 5xx responses)."""
    
    def __init__(self, message: str, status_code: int = None, response_text: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_text = response_text


class RateLimitError(LLMError):
    """Exception for rate limit errors (429 status code)."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class TimeoutError(LLMError):
    """Exception for request timeout errors."""
    pass


class ConfigurationError(LLMError):
    """Exception for LLM configuration issues."""
    pass


class ModelNotAvailableError(LLMError):
    """Exception when requested model is not available."""
    pass