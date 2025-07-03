"""
Tests for the ConsensusNet API endpoints.

This module tests the API functionality including authentication, 
rate limiting, validation, and error handling.
"""
import pytest
from fastapi.testclient import TestClient
import json
import time

# Import the app from main
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app

# Create test client
client = TestClient(app)


class TestAPIEndpoints:
    """Test the main API endpoints."""
    
    def test_root_endpoint(self):
        """Test the root endpoint returns correct information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["service"] == "ConsensusNet API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "operational"
        assert "endpoints" in data
        assert "verify" in data["endpoints"]
    
    def test_health_check_v1(self):
        """Test the v1 health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded", "unhealthy"]
        assert data["version"] == "1.0.0"
        assert "checks" in data
        assert "api" in data["checks"]
        assert "agents" in data["checks"]
    
    def test_legacy_health_check(self):
        """Test the legacy health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "checks" in data
    
    def test_agent_status(self):
        """Test the agent status endpoint."""
        response = client.get("/api/v1/agent/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "agent_id" in data
        assert "status" in data
        assert "capabilities" in data
        assert "uptime_seconds" in data
        assert data["status"] in ["healthy", "degraded", "unavailable"]
        
        # Check capabilities structure
        assert len(data["capabilities"]) > 0
        cap = data["capabilities"][0]
        assert "capability" in cap
        assert "enabled" in cap
        assert "description" in cap


class TestVerificationEndpoint:
    """Test the verification endpoint."""
    
    def test_basic_verification_no_auth(self):
        """Test basic verification without authentication."""
        response = client.post(
            "/api/v1/verify",
            json={
                "claim": "The Earth is round",
                "priority": "normal"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "verification" in data
        assert "request_id" in data
        assert "processing_time_ms" in data
        
        # Check verification structure
        verification = data["verification"]
        assert verification["claim"] == "The Earth is round"
        assert "verdict" in verification
        assert "confidence" in verification
        assert "reasoning" in verification
        assert "sources" in verification
        assert "evidence" in verification
        assert "metadata" in verification
        assert "timestamp" in verification
        assert "agent_id" in verification
    
    def test_verification_with_auth(self):
        """Test verification with API key authentication."""
        response = client.post(
            "/api/v1/verify",
            headers={"Authorization": "Bearer demo_key_12345"},
            json={
                "claim": "Water boils at 100°C at sea level",
                "context": "Basic chemistry fact",
                "priority": "high",
                "require_sources": True
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Check that context is preserved in metadata
        metadata = data["verification"]["metadata"]
        assert metadata["request_context"] == "Basic chemistry fact"
        assert metadata["priority"] == "high"
        assert metadata["require_sources"] is True
    
    def test_verification_validation_error(self):
        """Test verification with invalid input."""
        response = client.post(
            "/api/v1/verify",
            json={
                "claim": "",  # Empty claim should fail validation
            }
        )
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == "VALIDATION_ERROR"
        assert data["message"] == "Request validation failed"
        assert len(data["details"]) > 0
        
        detail = data["details"][0]
        assert detail["field"] == "body.claim"
        assert "too_short" in detail["code"]
    
    def test_verification_long_claim(self):
        """Test verification with very long claim."""
        long_claim = "A" * 6000  # Exceeds 5000 character limit
        response = client.post(
            "/api/v1/verify",
            json={
                "claim": long_claim
            }
        )
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == "VALIDATION_ERROR"
    
    def test_verification_invalid_priority(self):
        """Test verification with invalid priority value."""
        response = client.post(
            "/api/v1/verify",
            json={
                "claim": "Test claim",
                "priority": "invalid_priority"
            }
        )
        assert response.status_code == 422
        
        data = response.json()
        assert data["error"] is True
        assert data["error_type"] == "VALIDATION_ERROR"


class TestAuthentication:
    """Test authentication and authorization."""
    
    def test_invalid_api_key(self):
        """Test with invalid API key."""
        response = client.post(
            "/api/v1/verify",
            headers={"Authorization": "Bearer invalid_key"},
            json={"claim": "Test claim"}
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
    
    def test_malformed_auth_header(self):
        """Test with malformed authorization header."""
        response = client.post(
            "/api/v1/verify",
            headers={"Authorization": "Basic invalid_format"},
            json={"claim": "Test claim"}
        )
        # Since auth is optional, malformed headers are ignored and request succeeds
        # But if we had a required auth endpoint, this would be tested there
        assert response.status_code == 200
    
    def test_valid_free_tier_key(self):
        """Test with valid free tier API key."""
        response = client.post(
            "/api/v1/verify",
            headers={"Authorization": "Bearer demo_key_12345"},
            json={"claim": "Test claim"}
        )
        assert response.status_code == 200
    
    def test_valid_premium_key(self):
        """Test with valid premium API key."""
        response = client.post(
            "/api/v1/verify",
            headers={"Authorization": "Bearer test_premium_67890"},
            json={"claim": "Test claim"}
        )
        assert response.status_code == 200


class TestOpenAPISpec:
    """Test OpenAPI specification generation."""
    
    def test_openapi_json(self):
        """Test that OpenAPI JSON is generated correctly."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert data["info"]["title"] == "ConsensusNet API"
        assert data["info"]["version"] == "1.0.0"
        assert "paths" in data
        
        # Check that our endpoints are documented
        paths = data["paths"]
        assert "/api/v1/verify" in paths
        assert "/api/v1/health" in paths
        assert "/api/v1/agent/status" in paths
        
        # Check verify endpoint documentation
        verify_path = paths["/api/v1/verify"]["post"]
        assert "summary" in verify_path
        assert "description" in verify_path
        assert "requestBody" in verify_path
        assert "responses" in verify_path
    
    def test_docs_endpoint(self):
        """Test that Swagger UI docs are accessible."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower()
    
    def test_redoc_endpoint(self):
        """Test that ReDoc docs are accessible."""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "redoc" in response.text.lower()


class TestErrorHandling:
    """Test error handling across the API."""
    
    def test_404_error(self):
        """Test 404 error for non-existent endpoint."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_405_error(self):
        """Test 405 error for wrong HTTP method."""
        response = client.put("/api/v1/verify")
        assert response.status_code == 405
    
    def test_malformed_json(self):
        """Test error handling for malformed JSON."""
        response = client.post(
            "/api/v1/verify",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422


class TestResponseFormats:
    """Test response formats and data structures."""
    
    def test_verification_response_structure(self):
        """Test that verification response has correct structure."""
        response = client.post(
            "/api/v1/verify",
            json={"claim": "Test claim"}
        )
        assert response.status_code == 200
        
        data = response.json()
        
        # Top-level response structure
        required_fields = ["success", "verification", "request_id", "processing_time_ms", "api_version"]
        for field in required_fields:
            assert field in data
        
        # Verification object structure
        verification = data["verification"]
        verification_fields = [
            "claim", "verdict", "confidence", "reasoning", 
            "sources", "evidence", "metadata", "timestamp", "agent_id"
        ]
        for field in verification_fields:
            assert field in verification
        
        # Data types
        assert isinstance(data["success"], bool)
        assert isinstance(data["processing_time_ms"], int)
        assert isinstance(verification["confidence"], float)
        assert isinstance(verification["sources"], list)
        assert isinstance(verification["evidence"], list)
        assert isinstance(verification["metadata"], dict)
        
        # Value ranges
        assert 0.0 <= verification["confidence"] <= 1.0
    
    def test_error_response_structure(self):
        """Test that error response has correct structure."""
        response = client.post(
            "/api/v1/verify",
            json={"claim": ""}
        )
        assert response.status_code == 422
        
        data = response.json()
        
        # Error response structure
        required_fields = ["error", "error_type", "message", "details", "timestamp", "request_id"]
        for field in required_fields:
            assert field in data
        
        assert data["error"] is True
        assert isinstance(data["details"], list)
        assert len(data["details"]) > 0
        
        # Detail structure
        detail = data["details"][0]
        detail_fields = ["code", "message", "field"]
        for field in detail_fields:
            assert field in detail