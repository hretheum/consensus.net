"""
Tests for the enhanced InputProcessor module.

These tests verify the input processing capabilities including:
- Multiple input format support
- Input validation and sanitization
- Context extraction
- Domain detection and complexity assessment
"""

import json
import pytest
from unittest.mock import patch

from src.agents.input_processor import InputProcessor
from src.agents.agent_models import ProcessedClaim, ClaimComplexity, InputError


class TestInputProcessor:
    """Test the core InputProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_initialization(self):
        """Test InputProcessor initialization."""
        # Default initialization
        processor = InputProcessor()
        assert processor.max_length == InputProcessor.MAX_CLAIM_LENGTH
        assert processor.min_length == InputProcessor.MIN_CLAIM_LENGTH
        
        # Custom configuration
        config = {"max_claim_length": 5000, "min_claim_length": 5}
        processor = InputProcessor(config)
        assert processor.max_length == 5000
        assert processor.min_length == 5


class TestTextInputParsing:
    """Test parsing of text input formats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_simple_text_input(self):
        """Test parsing simple text input."""
        claim = "The sky is blue."
        result = self.processor.parse_claim(claim)
        
        assert isinstance(result, ProcessedClaim)
        assert result.original_text == claim
        assert result.normalized_text == "the sky is blue."
        assert result.preprocessing_metadata["input_format"] == "text"
        assert result.preprocessing_metadata["processor_version"] == "2.0"
    
    def test_complex_text_input(self):
        """Test parsing complex text with various elements."""
        claim = "According to a 2023 study, 85% of scientists agree that climate change is real!"
        result = self.processor.parse_claim(claim)
        
        assert isinstance(result, ProcessedClaim)
        assert result.domain == "science"
        assert result.complexity in [ClaimComplexity.MODERATE, ClaimComplexity.COMPLEX]
        assert result.context["has_numbers"] is True
        assert result.context["has_dates"] is True
        assert result.context["has_percentages"] is True
    
    def test_text_with_special_characters(self):
        """Test text with special characters and Unicode."""
        claim = 'The café\'s "special" menu costs €50–60.'
        result = self.processor.parse_claim(claim)
        
        assert isinstance(result, ProcessedClaim)
        assert result.context["has_monetary"] is True
        # Check that special characters are normalized
        assert '"' in result.normalized_text or "'" in result.normalized_text


class TestJSONInputParsing:
    """Test parsing of JSON input formats."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_simple_json_input(self):
        """Test parsing simple JSON input."""
        json_input = {
            "claim": "Water boils at 100°C at sea level.",
            "metadata": {
                "source": "physics textbook",
                "confidence": 0.95
            }
        }
        
        result = self.processor.parse_claim(json_input)
        
        assert isinstance(result, ProcessedClaim)
        assert result.original_text == json_input["claim"]
        assert result.preprocessing_metadata["input_format"] == "json"
        assert result.preprocessing_metadata["source_metadata"]["source"] == "physics textbook"
        assert result.preprocessing_metadata["json_structure"]["has_metadata"] is True
    
    def test_json_without_metadata(self):
        """Test JSON input without metadata field."""
        json_input = {"claim": "Simple claim without metadata."}
        
        result = self.processor.parse_claim(json_input)
        
        assert isinstance(result, ProcessedClaim)
        assert result.original_text == json_input["claim"]
        assert result.preprocessing_metadata["input_format"] == "json"
        assert result.preprocessing_metadata["json_structure"]["has_metadata"] is False
    
    def test_json_with_additional_fields(self):
        """Test JSON input with additional fields."""
        json_input = {
            "claim": "Test claim with extra fields.",
            "metadata": {"source": "test"},
            "priority": "high",
            "category": "urgent"
        }
        
        result = self.processor.parse_claim(json_input)
        
        assert isinstance(result, ProcessedClaim)
        additional_fields = result.preprocessing_metadata["json_structure"]["additional_fields"]
        assert "priority" in additional_fields
        assert "category" in additional_fields
    
    def test_invalid_json_structure(self):
        """Test invalid JSON input structures."""
        # Missing claim field
        with pytest.raises(InputError, match="must contain 'claim' field"):
            self.processor.parse_claim({"metadata": {"source": "test"}})
        
        # Non-string claim
        with pytest.raises(InputError, match="Claim field must be a string"):
            self.processor.parse_claim({"claim": 123})
        
        # Non-dict metadata
        with pytest.raises(InputError, match="Metadata field must be a dictionary"):
            self.processor.parse_claim({"claim": "test", "metadata": "invalid"})
    
    def test_json_string_as_text(self):
        """Test JSON string provided as text input."""
        json_string = '{"claim": "This looks like JSON", "metadata": {"source": "test"}}'
        
        result = self.processor.parse_claim(json_string)
        
        assert isinstance(result, ProcessedClaim)
        assert result.original_text == "This looks like JSON"
        # Should detect and parse as JSON since it's a valid JSON with claim field
        assert result.preprocessing_metadata["input_format"] == "json"


class TestInputValidation:
    """Test input validation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_valid_inputs(self):
        """Test validation of valid inputs."""
        valid_claims = [
            "Simple valid claim.",
            "A longer claim with more details and specifics.",
            "Claim with numbers like 123 and symbols like $50.",
            "Multi-sentence claim. It has multiple parts. All should be valid."
        ]
        
        for claim in valid_claims:
            assert self.processor.validate_input(claim) is True
    
    def test_invalid_length_inputs(self):
        """Test validation of inputs with invalid lengths."""
        # Too short
        assert self.processor.validate_input("Hi") is False
        assert self.processor.validate_input("") is False
        
        # Too long
        long_claim = "x" * (InputProcessor.MAX_CLAIM_LENGTH + 1)
        assert self.processor.validate_input(long_claim) is False
    
    def test_whitespace_only_inputs(self):
        """Test validation of whitespace-only inputs."""
        assert self.processor.validate_input("   ") is False
        assert self.processor.validate_input("\n\t\r") is False
        assert self.processor.validate_input("") is False
    
    def test_excessive_repetition(self):
        """Test validation against excessive repetition."""
        # Excessive character repetition
        spam_claim = "This is spam" + "a" * 15 + " text"
        assert self.processor.validate_input(spam_claim) is False
        
        # Excessive word repetition
        word_spam = " ".join(["spam"] * 20 + ["other", "words"])
        assert self.processor.validate_input(word_spam) is False
    
    def test_malicious_patterns(self):
        """Test validation against malicious patterns."""
        malicious_inputs = [
            "Check this <script>alert('xss')</script> claim",
            "Visit javascript:alert('bad') for more info",
            "Data: data:text/html;base64,PHNjcmlwdD4=",
            "Click here onload=badFunction() for details"
        ]
        
        for malicious in malicious_inputs:
            assert self.processor.validate_input(malicious) is False
    
    def test_non_string_input(self):
        """Test validation of non-string inputs."""
        assert self.processor.validate_input(None) is False
        assert self.processor.validate_input(123) is False
        assert self.processor.validate_input([]) is False
        assert self.processor.validate_input({}) is False


class TestTextNormalization:
    """Test text normalization functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_basic_normalization(self):
        """Test basic text normalization."""
        text = "  This   Has   Extra   Spaces  "
        normalized = self.processor.normalize_text(text)
        assert normalized == "this has extra spaces"
    
    def test_case_normalization(self):
        """Test case normalization."""
        text = "ThIs Is MiXeD cAsE"
        normalized = self.processor.normalize_text(text)
        assert normalized == "this is mixed case"
    
    def test_special_character_normalization(self):
        """Test special character normalization."""
        text = 'Smart "quotes" and \'apostrophes\' with em—dash'
        normalized = self.processor.normalize_text(text)
        
        # Should convert smart quotes to regular quotes
        assert '"' in normalized
        assert "'" in normalized
        assert "-" in normalized
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        text = "Café naïve résumé"  # Text with accented characters
        normalized = self.processor.normalize_text(text)
        
        # Should still be readable but normalized
        assert "caf" in normalized.lower()
        assert len(normalized) > 0
    
    def test_empty_text_normalization(self):
        """Test normalization of empty text."""
        assert self.processor.normalize_text("") == ""
        assert self.processor.normalize_text(None) == ""


class TestContextExtraction:
    """Test context extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_basic_context_extraction(self):
        """Test extraction of basic context information."""
        claim = "This is a simple test claim with five words."
        context = self.processor.extract_context(claim)
        
        assert "word_count" in context
        assert "character_count" in context
        assert "sentence_count" in context
        assert context["word_count"] > 0
        assert context["character_count"] > 0
    
    def test_numerical_context_extraction(self):
        """Test extraction of numerical context."""
        claim = "Studies show 85% improvement with $100 investment in 2023."
        context = self.processor.extract_context(claim)
        
        assert context["has_numbers"] is True
        assert context["has_dates"] is True
        assert context["has_percentages"] is True
        assert context["has_monetary"] is True
    
    def test_web_content_context(self):
        """Test extraction of web content context."""
        claim = "Check https://example.com @username #hashtag for more info!"
        context = self.processor.extract_context(claim)
        
        assert context["has_urls"] is True
        assert context["has_mentions"] is True
        assert context["has_hashtags"] is True
        assert context["has_exclamations"] is True
    
    def test_language_context_extraction(self):
        """Test extraction of language characteristics."""
        claim = 'He said "Are you sure?" with concern!'
        context = self.processor.extract_context(claim)
        
        assert context["has_questions"] is True
        assert context["has_exclamations"] is True
        assert context["has_quotations"] is True
    
    def test_domain_indicators(self):
        """Test extraction of domain-specific indicators."""
        science_claim = "The peer-reviewed study analyzed experimental data using statistical methods."
        context = self.processor.extract_context(science_claim)
        assert context["science_indicators"] > 0
        
        health_claim = "The clinical trial showed treatment effectiveness in patients."
        context = self.processor.extract_context(health_claim)
        assert context["health_indicators"] > 0
        
        political_claim = "The government announced new legislation after the election."
        context = self.processor.extract_context(political_claim)
        assert context["political_indicators"] > 0


class TestDomainDetection:
    """Test domain detection functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_science_domain_detection(self):
        """Test detection of science domain."""
        science_claims = [
            "The peer-reviewed study published in Nature shows quantum effects.",
            "Research data indicates hypothesis confirmation through experimentation.",
            "Scientific analysis of laboratory results supports the methodology."
        ]
        
        for claim in science_claims:
            normalized = self.processor.normalize_text(claim)
            domain = self.processor._detect_domain(normalized)
            assert domain == "science"
    
    def test_health_domain_detection(self):
        """Test detection of health domain."""
        health_claims = [
            "Clinical trials show treatment effectiveness in patients.",
            "Medical diagnosis confirmed disease symptoms in healthcare study.",
            "Pharmaceutical therapy shows vaccine effectiveness against virus."
        ]
        
        for claim in health_claims:
            normalized = self.processor.normalize_text(claim)
            domain = self.processor._detect_domain(normalized)
            assert domain == "health"
    
    def test_politics_domain_detection(self):
        """Test detection of politics domain."""
        political_claims = [
            "Government policy announcement affects election candidate votes.",
            "Congressional legislation passed with democratic and republican support.",
            "Presidential administration implements conservative and liberal policies."
        ]
        
        for claim in political_claims:
            normalized = self.processor.normalize_text(claim)
            domain = self.processor._detect_domain(normalized)
            assert domain == "politics"
    
    def test_technology_domain_detection(self):
        """Test detection of technology domain."""
        tech_claims = [
            "Artificial intelligence algorithm improves machine learning software.",
            "Blockchain cryptocurrency technology enables digital programming.",
            "Computer hardware optimization enhances internet applications."
        ]
        
        for claim in tech_claims:
            normalized = self.processor.normalize_text(claim)
            domain = self.processor._detect_domain(normalized)
            assert domain == "technology"
    
    def test_general_domain_fallback(self):
        """Test fallback to general domain."""
        general_claim = "This is a simple statement without specific domain keywords."
        normalized = self.processor.normalize_text(general_claim)
        domain = self.processor._detect_domain(normalized)
        assert domain == "general"


class TestComplexityAssessment:
    """Test complexity assessment functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_simple_complexity(self):
        """Test simple complexity assessment."""
        simple_claims = [
            "The sky is blue.",
            "Water is wet.",
            "Today is Monday."
        ]
        
        for claim in simple_claims:
            normalized = self.processor.normalize_text(claim)
            complexity = self.processor._assess_complexity(normalized)
            assert complexity == ClaimComplexity.SIMPLE
    
    def test_moderate_complexity(self):
        """Test moderate complexity assessment."""
        moderate_claims = [
            "Studies suggest that regular exercise significantly improves overall health outcomes.",
            "The research indicates a strong correlation between improved diet and energy levels.",
            "According to medical experts, climate change directly affects weather patterns."
        ]
        
        for claim in moderate_claims:
            normalized = self.processor.normalize_text(claim)
            complexity = self.processor._assess_complexity(normalized)
            # Should be at least moderate complexity, but could be higher
            assert complexity in [ClaimComplexity.MODERATE, ClaimComplexity.COMPLEX, ClaimComplexity.RESEARCH]
    
    def test_complex_complexity(self):
        """Test complex complexity assessment."""
        complex_claims = [
            "Longitudinal analysis of randomized controlled trials demonstrates statistical significance with p < 0.05 compared to control groups.",
            "Comparative studies show 85% improvement when controlling for confounding variables across multiple populations.",
            "Meta-analysis reveals heterogeneity in effect sizes across different populations and methodologies with significant variance."
        ]
        
        for claim in complex_claims:
            normalized = self.processor.normalize_text(claim)
            complexity = self.processor._assess_complexity(normalized)
            # Should be at least moderate, but could be complex or research
            assert complexity in [ClaimComplexity.MODERATE, ClaimComplexity.COMPLEX, ClaimComplexity.RESEARCH]
    
    def test_research_complexity(self):
        """Test research-level complexity assessment."""
        research_claims = [
            "Systematic review and meta-analysis of peer-reviewed randomized controlled trials demonstrates statistical significance with p < 0.001, however confounding variables and methodological heterogeneity warrant further investigation compared to control groups.",
            "Multivariate regression analysis controlling for demographic factors reveals significant correlation between intervention and outcome measures, although causal inference requires additional longitudinal studies with larger sample sizes and more robust experimental design."
        ]
        
        for claim in research_claims:
            normalized = self.processor.normalize_text(claim)
            complexity = self.processor._assess_complexity(normalized)
            # Should be complex or research level
            assert complexity in [ClaimComplexity.COMPLEX, ClaimComplexity.RESEARCH]


class TestErrorHandling:
    """Test error handling in input processing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_unsupported_input_types(self):
        """Test handling of unsupported input types."""
        unsupported_inputs = [123, [], set(), None]
        
        for invalid_input in unsupported_inputs:
            with pytest.raises(InputError):
                self.processor.parse_claim(invalid_input)
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON structures."""
        # Non-dict JSON input (should be handled as text)
        result = self.processor.parse_claim("not a dict")
        assert result.preprocessing_metadata["input_format"] == "text"
        
        # Dict without claim field
        with pytest.raises(InputError, match="must contain 'claim' field"):
            self.processor.parse_claim({"no_claim": "test"})
    
    def test_validation_failure_handling(self):
        """Test handling of validation failures."""
        # Input that fails validation
        invalid_claim = "x" * (InputProcessor.MAX_CLAIM_LENGTH + 1)
        
        with pytest.raises(InputError, match="Input validation failed"):
            self.processor.parse_claim(invalid_claim)
    
    def test_processing_exception_handling(self):
        """Test handling of unexpected processing exceptions."""
        # Mock a scenario where an unexpected error occurs
        with patch.object(self.processor, '_detect_domain', side_effect=Exception("Unexpected error")):
            with pytest.raises(InputError, match="Failed to parse input"):
                self.processor.parse_claim("Valid claim text")


class TestConfigurationAndCustomization:
    """Test configuration and customization options."""
    
    def test_custom_length_limits(self):
        """Test custom length limit configuration."""
        config = {
            "max_claim_length": 100,
            "min_claim_length": 10
        }
        processor = InputProcessor(config)
        
        # Should accept input within custom limits
        valid_claim = "This claim is within the custom length limits for testing."
        assert processor.validate_input(valid_claim) is True
        
        # Should reject input outside custom limits
        too_short = "Short"
        too_long = "x" * 101
        assert processor.validate_input(too_short) is False
        assert processor.validate_input(too_long) is False
    
    def test_default_configuration(self):
        """Test default configuration values."""
        processor = InputProcessor()
        
        assert processor.max_length == InputProcessor.MAX_CLAIM_LENGTH
        assert processor.min_length == InputProcessor.MIN_CLAIM_LENGTH
        assert processor.config == {}


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InputProcessor()
    
    def test_complete_text_processing_pipeline(self):
        """Test complete processing pipeline for text input."""
        claim = "According to a 2023 peer-reviewed study, 75% of participants showed improvement!"
        
        result = self.processor.parse_claim(claim)
        
        # Verify all components are processed correctly
        assert isinstance(result, ProcessedClaim)
        assert result.original_text == claim
        assert result.normalized_text != claim  # Should be normalized
        assert result.domain == "science"
        assert result.complexity in [ClaimComplexity.MODERATE, ClaimComplexity.COMPLEX]
        assert result.context["has_numbers"] is True
        assert result.context["has_dates"] is True
        assert result.context["has_percentages"] is True
        assert result.context["science_indicators"] > 0
        assert "processor_version" in result.preprocessing_metadata
        assert result.preprocessing_metadata["input_format"] == "text"
    
    def test_complete_json_processing_pipeline(self):
        """Test complete processing pipeline for JSON input."""
        json_input = {
            "claim": "Clinical trials demonstrate vaccine effectiveness in preventing disease transmission.",
            "metadata": {
                "source": "WHO report",
                "date": "2023-12-01",
                "confidence": 0.92
            }
        }
        
        result = self.processor.parse_claim(json_input)
        
        # Verify all components are processed correctly
        assert isinstance(result, ProcessedClaim)
        assert result.original_text == json_input["claim"]
        assert result.domain == "health"
        assert result.complexity in [ClaimComplexity.SIMPLE, ClaimComplexity.MODERATE, ClaimComplexity.COMPLEX]
        assert result.context["health_indicators"] > 0
        assert result.preprocessing_metadata["input_format"] == "json"
        assert result.preprocessing_metadata["source_metadata"]["source"] == "WHO report"
        assert result.preprocessing_metadata["json_structure"]["has_metadata"] is True
    
    def test_multilingual_and_special_content(self):
        """Test processing of multilingual and special content."""
        claim = 'The café\'s naïve résumé costs €50–60 per "special" item! 🎉'
        
        result = self.processor.parse_claim(claim)
        
        # Should handle special characters without errors
        assert isinstance(result, ProcessedClaim)
        assert result.context["has_monetary"] is True
        assert result.context["has_exclamations"] is True
        assert result.context["has_quotations"] is True
        # Should normalize Unicode but preserve meaning
        assert len(result.normalized_text) > 0