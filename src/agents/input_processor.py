"""
Enhanced Input Processing Module for Consensus.Net

This module provides comprehensive input processing capabilities including:
- Multiple input format support (text, JSON)
- Input validation and sanitization
- Standardized output format conversion
- Context extraction and analysis

Implements the Input Processor component as specified in 
docs/architecture/core-agent-architecture.md
"""

import json
import re
import time
from typing import Dict, Any, Union, Optional, List
from dataclasses import asdict

from .agent_models import ProcessedClaim, ClaimComplexity, InputError


class InputProcessor:
    """
    Enhanced input processor that handles multiple formats and provides
    comprehensive validation and normalization capabilities.
    """
    
    # Input validation limits
    MAX_CLAIM_LENGTH = 10000  # Maximum characters in a claim
    MIN_CLAIM_LENGTH = 3      # Minimum characters in a claim
    MAX_JSON_DEPTH = 10       # Maximum nesting depth for JSON
    
    # Supported input formats
    SUPPORTED_FORMATS = ["text", "json"]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the input processor with optional configuration.
        
        Args:
            config: Optional configuration dictionary with validation settings
        """
        self.config = config or {}
        self.max_length = self.config.get("max_claim_length", self.MAX_CLAIM_LENGTH)
        self.min_length = self.config.get("min_claim_length", self.MIN_CLAIM_LENGTH)
        
    def parse_claim(self, raw_input: Union[str, Dict[str, Any]]) -> ProcessedClaim:
        """
        Parse and normalize incoming input into a ProcessedClaim.
        
        Supports multiple input formats:
        - Plain text string
        - JSON object with claim and metadata
        
        Args:
            raw_input: Input in text or JSON format
            
        Returns:
            ProcessedClaim: Standardized claim representation
            
        Raises:
            InputError: If input is invalid or cannot be processed
        """
        try:
            # Determine input format and extract claim text
            if isinstance(raw_input, str):
                claim_text, input_metadata = self._parse_text_input(raw_input)
                # Check if text was actually parsed as JSON
                input_format = input_metadata.get("detected_format", "text")
            elif isinstance(raw_input, dict):
                claim_text, input_metadata = self._parse_json_input(raw_input)
                input_format = "json"
            else:
                raise InputError(f"Unsupported input type: {type(raw_input)}")
            
            # Validate the extracted claim text
            if not self.validate_input(claim_text):
                raise InputError("Input validation failed")
            
            # Normalize the text
            normalized_text = self.normalize_text(claim_text)
            
            # Extract context and metadata
            context = self.extract_context(normalized_text)
            
            # Detect domain and assess complexity
            domain = self._detect_domain(normalized_text)
            complexity = self._assess_complexity(normalized_text)
            
            # Combine input metadata with processing metadata
            preprocessing_metadata = {
                "processor_version": "2.0",
                "processing_time": time.time(),
                "input_format": input_format,
                **input_metadata
            }
            
            return ProcessedClaim(
                original_text=claim_text,
                normalized_text=normalized_text,
                domain=domain,
                complexity=complexity,
                context=context,
                preprocessing_metadata=preprocessing_metadata
            )
            
        except Exception as e:
            if isinstance(e, InputError):
                raise
            raise InputError(f"Failed to parse input: {str(e)}")
    
    def validate_input(self, claim: str) -> bool:
        """
        Validate input claim for safety and processability.
        
        Checks for:
        - Length limits
        - Content safety
        - Character encoding
        - Basic structure
        
        Args:
            claim: The claim text to validate
            
        Returns:
            bool: True if input is valid, False otherwise
        """
        if not claim or not isinstance(claim, str):
            return False
        
        # Check length limits
        if len(claim) < self.min_length or len(claim) > self.max_length:
            return False
        
        # Check for only whitespace
        if not claim.strip():
            return False
        
        # Check for excessive repeated characters (potential spam)
        if self._has_excessive_repetition(claim):
            return False
        
        # Check for malicious patterns
        if self._contains_malicious_patterns(claim):
            return False
        
        # Check character encoding (should be valid UTF-8)
        try:
            claim.encode('utf-8')
        except UnicodeEncodeError:
            return False
        
        return True
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text for consistent processing.
        
        Performs:
        - Whitespace normalization
        - Case normalization
        - Special character handling
        - Unicode normalization
        
        Args:
            text: Raw text to normalize
            
        Returns:
            str: Normalized text
        """
        if not text:
            return ""
        
        # Basic whitespace cleanup
        normalized = re.sub(r'\s+', ' ', text.strip())
        
        # Convert to lowercase for consistent processing
        normalized = normalized.lower()
        
        # Remove or normalize special characters
        normalized = self._normalize_special_characters(normalized)
        
        # Normalize Unicode characters
        normalized = self._normalize_unicode(normalized)
        
        return normalized
    
    def extract_context(self, claim: str) -> Dict[str, Any]:
        """
        Extract contextual information from the claim.
        
        Analyzes the claim to identify:
        - Statistical properties
        - Temporal references
        - Numerical data
        - Entity mentions
        - Language characteristics
        
        Args:
            claim: The claim text to analyze
            
        Returns:
            Dict[str, Any]: Context information dictionary
        """
        context = {}
        
        # Basic statistical properties
        words = claim.split()
        context["word_count"] = len(words)
        context["character_count"] = len(claim)
        context["sentence_count"] = len(re.findall(r'[.!?]+', claim))
        
        # Numerical and temporal analysis
        context["has_numbers"] = bool(re.search(r'\d', claim))
        context["has_dates"] = self._contains_dates(claim)
        context["has_percentages"] = bool(re.search(r'\d+%', claim))
        context["has_monetary"] = bool(re.search(r'[$€£¥]\d+|\d+\s*(dollars?|euros?|pounds?|yen)', claim))
        
        # Entity and reference analysis
        context["has_urls"] = bool(re.search(r'https?://|www\.', claim))
        context["has_mentions"] = bool(re.search(r'@\w+', claim))
        context["has_hashtags"] = bool(re.search(r'#\w+', claim))
        
        # Language characteristics
        context["has_questions"] = bool(re.search(r'\?', claim))
        context["has_exclamations"] = bool(re.search(r'!', claim))
        context["has_quotations"] = bool(re.search(r'["""\'\u2018\u2019]', claim))
        
        # Domain-specific indicators
        context["science_indicators"] = self._count_science_indicators(claim)
        context["health_indicators"] = self._count_health_indicators(claim)
        context["political_indicators"] = self._count_political_indicators(claim)
        
        return context
    
    def _parse_text_input(self, text_input: str) -> tuple[str, Dict[str, Any]]:
        """Parse plain text input."""
        # Try to detect if it's actually JSON disguised as text
        if text_input.strip().startswith('{') and text_input.strip().endswith('}'):
            try:
                json_data = json.loads(text_input)
                if isinstance(json_data, dict) and "claim" in json_data:
                    claim_text, metadata = self._parse_json_input(json_data)
                    # Mark that this was detected as JSON from text
                    metadata["detected_format"] = "json"
                    return claim_text, metadata
            except json.JSONDecodeError:
                pass  # Not valid JSON, treat as text
        
        return text_input, {"original_format": "text", "detected_format": "text"}
    
    def _parse_json_input(self, json_input: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Parse JSON input format.
        
        Expected JSON structure:
        {
            "claim": "The actual claim text",
            "metadata": {
                "source": "optional source info",
                "timestamp": "optional timestamp",
                "context": "optional additional context"
            }
        }
        """
        if not isinstance(json_input, dict):
            raise InputError("JSON input must be a dictionary")
        
        # Extract the claim text
        if "claim" not in json_input:
            raise InputError("JSON input must contain 'claim' field")
        
        claim_text = json_input["claim"]
        if not isinstance(claim_text, str):
            raise InputError("Claim field must be a string")
        
        # Extract metadata
        metadata = json_input.get("metadata", {})
        if not isinstance(metadata, dict):
            raise InputError("Metadata field must be a dictionary")
        
        # Add JSON-specific metadata
        input_metadata = {
            "original_format": "json",
            "source_metadata": metadata,
            "json_structure": self._analyze_json_structure(json_input)
        }
        
        return claim_text, input_metadata
    
    def _analyze_json_structure(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the structure of JSON input for metadata."""
        return {
            "field_count": len(json_data),
            "has_metadata": "metadata" in json_data,
            "additional_fields": [k for k in json_data.keys() if k not in ["claim", "metadata"]]
        }
    
    def _detect_domain(self, text: str) -> str:
        """Enhanced domain detection with more categories and better accuracy."""
        domain_scores = {}
        
        # Science and research keywords
        science_keywords = [
            "study", "research", "scientist", "data", "experiment", "scattering", 
            "quantum", "physics", "chemistry", "biology", "methodology", "hypothesis",
            "peer-reviewed", "journal", "academic", "laboratory", "analysis"
        ]
        domain_scores["science"] = sum(1 for keyword in science_keywords if keyword in text)
        
        # Health and medical keywords
        health_keywords = [
            "health", "medical", "doctor", "treatment", "disease", "exercise",
            "medicine", "patient", "diagnosis", "symptom", "healthcare", "clinical",
            "therapy", "pharmaceutical", "vaccine", "virus", "bacteria"
        ]
        domain_scores["health"] = sum(1 for keyword in health_keywords if keyword in text)
        
        # News and current events
        news_keywords = [
            "breaking", "report", "announced", "today", "yesterday", "news",
            "journalist", "media", "press", "coverage", "update", "developing",
            "sources", "confirmed", "investigation"
        ]
        domain_scores["news"] = sum(1 for keyword in news_keywords if keyword in text)
        
        # Politics and government
        politics_keywords = [
            "government", "political", "policy", "election", "candidate", "vote",
            "congress", "senate", "president", "minister", "parliament", "legislation",
            "democracy", "republican", "democrat", "conservative", "liberal"
        ]
        domain_scores["politics"] = sum(1 for keyword in politics_keywords if keyword in text)
        
        # Technology
        tech_keywords = [
            "technology", "software", "hardware", "computer", "internet", "digital",
            "algorithm", "artificial intelligence", "machine learning", "blockchain",
            "cryptocurrency", "app", "website", "programming", "coding"
        ]
        domain_scores["technology"] = sum(1 for keyword in tech_keywords if keyword in text)
        
        # Business and economics
        business_keywords = [
            "business", "economy", "financial", "market", "stock", "investment",
            "company", "corporation", "profit", "revenue", "economics", "trade",
            "gdp", "inflation", "recession", "growth"
        ]
        domain_scores["business"] = sum(1 for keyword in business_keywords if keyword in text)
        
        # Find the domain with the highest score
        if any(score > 0 for score in domain_scores.values()):
            return max(domain_scores, key=domain_scores.get)
        else:
            return "general"
    
    def _assess_complexity(self, text: str) -> ClaimComplexity:
        """Enhanced complexity assessment considering multiple factors."""
        complexity_score = 0
        
        # Word count factor (more generous scoring)
        word_count = len(text.split())
        if word_count > 15:
            complexity_score += 2
        elif word_count > 8:
            complexity_score += 1
        
        # Sentence structure complexity
        sentence_count = len(re.findall(r'[.!?]+', text))
        if sentence_count > 1:
            complexity_score += 1
        
        # Technical/scientific indicators
        technical_patterns = [
            r'\b\d+\.?\d*%\b',  # Percentages
            r'\b\d{4}\b',       # Years
            r'\bp\s*<\s*0\.\d+\b',  # P-values
            r'\b(correlation|causation|statistical|significance)\b',
            r'\b(according to|research shows|study found|trials|demonstrate|effectiveness)\b',
            r'\b(clinical|vaccine|treatment|analysis|methodology)\b',
            r'\b(longitudinal|meta-analysis|randomized|controlled)\b'
        ]
        for pattern in technical_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                complexity_score += 1
        
        # Conditional and comparative language
        complex_language = [
            r'\b(if|when|unless|although|however|whereas|nevertheless)\b',
            r'\b(more|less|better|worse|higher|lower)\s+than\b',
            r'\b(compared to|in contrast|on the other hand)\b',
            r'\b(demonstrate|effectiveness|preventing|significantly)\b',
            r'\b(heterogeneity|confounding|variance|regression)\b'
        ]
        for pattern in complex_language:
            if re.search(pattern, text, re.IGNORECASE):
                complexity_score += 1
        
        # Map score to complexity level (adjusted thresholds)
        if complexity_score >= 7:
            return ClaimComplexity.RESEARCH
        elif complexity_score >= 4:
            return ClaimComplexity.COMPLEX
        elif complexity_score >= 2:
            return ClaimComplexity.MODERATE
        else:
            return ClaimComplexity.SIMPLE
    
    def _contains_dates(self, text: str) -> bool:
        """Enhanced date detection with more patterns."""
        date_patterns = [
            r'\b\d{4}\b',  # Years
            r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
            r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
            r'\b\d{1,2}/\d{1,2}/\d{2,4}\b',  # MM/DD/YYYY
            r'\b\d{1,2}-\d{1,2}-\d{2,4}\b',  # MM-DD-YYYY
            r'\b(today|yesterday|tomorrow|last week|next week|last month|next month)\b'
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in date_patterns)
    
    def _has_excessive_repetition(self, text: str) -> bool:
        """Check for excessive character or word repetition (spam detection)."""
        # Check for excessive character repetition
        if re.search(r'(.)\1{10,}', text):  # Same character repeated 10+ times
            return True
        
        # Check for excessive word repetition
        words = text.lower().split()
        if len(words) > 10:
            word_counts = {}
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
                if word_counts[word] > len(words) * 0.3:  # Word appears in >30% of text
                    return True
        
        return False
    
    def _contains_malicious_patterns(self, text: str) -> bool:
        """Check for potentially malicious patterns."""
        malicious_patterns = [
            r'<script\b',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:.*base64',  # Base64 data URLs
            r'vbscript:',  # VBScript URLs
            r'onload\s*=',  # Event handlers
            r'onerror\s*=',
            r'onclick\s*=',
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in malicious_patterns)
    
    def _normalize_special_characters(self, text: str) -> str:
        """Normalize special characters for consistent processing."""
        # Replace smart quotes with regular quotes
        text = re.sub(r'["""]', '"', text)
        text = re.sub(r'[\u2018\u2019]', "'", text)
        
        # Normalize dashes
        text = re.sub(r'[–—]', '-', text)
        
        # Normalize ellipsis
        text = re.sub(r'…', '...', text)
        
        return text
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters."""
        import unicodedata
        # Normalize to NFKD form (canonical decomposition, then canonical combining)
        return unicodedata.normalize('NFKD', text)
    
    def _count_science_indicators(self, text: str) -> int:
        """Count scientific terminology indicators."""
        indicators = [
            "study", "research", "data", "analysis", "methodology", "hypothesis",
            "experiment", "control", "sample", "statistical", "correlation",
            "peer-reviewed", "published", "journal", "evidence"
        ]
        return sum(1 for indicator in indicators if indicator in text)
    
    def _count_health_indicators(self, text: str) -> int:
        """Count health and medical terminology indicators."""
        indicators = [
            "health", "medical", "clinical", "patient", "treatment", "therapy",
            "diagnosis", "symptom", "disease", "virus", "bacteria", "vaccine",
            "medicine", "pharmaceutical", "healthcare", "doctor"
        ]
        return sum(1 for indicator in indicators if indicator in text)
    
    def _count_political_indicators(self, text: str) -> int:
        """Count political terminology indicators."""
        indicators = [
            "political", "government", "policy", "election", "vote", "candidate",
            "congress", "senate", "president", "minister", "legislation",
            "democracy", "republican", "democrat", "conservative", "liberal"
        ]
        return sum(1 for indicator in indicators if indicator in text)