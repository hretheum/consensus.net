"""
Tests for the FastAPI Gateway /verify endpoint and rate limiting.
"""
import pytest
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # Reset rate limiter for each test
    from api.rate_limiter import rate_limiter
    rate_limiter.request_history.clear()
    
    return TestClient(app)


class TestVerifyEndpoint:
    """Test cases for the /verify endpoint."""
    
    def test_verify_simple_claim_success(self, client):
        """Test successful verification of a simple claim."""
        response = client.post("/api/verify", json={"claim": "The sky is blue"})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "result" in data
        assert "processing_time" in data
        assert data["processing_time"] >= 0
        
        result = data["result"]
        assert result["claim"] == "The sky is blue"
        assert result["verdict"] in ["TRUE", "FALSE", "UNCERTAIN", "ERROR"]
        assert 0.0 <= result["confidence"] <= 1.0
        assert len(result["reasoning"]) > 0
        assert isinstance(result["sources"], list)
        assert isinstance(result["evidence"], list)
        assert isinstance(result["metadata"], dict)
        assert "timestamp" in result
    
    def test_verify_with_metadata(self, client):
        """Test verification with additional metadata."""
        request_data = {
            "claim": "2+2=4",
            "metadata": {"source": "test", "priority": "high"}
        }
        
        response = client.post("/api/verify", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        result = data["result"]
        
        assert "request_metadata" in result["metadata"]
        assert result["metadata"]["request_metadata"] == request_data["metadata"]
    
    def test_verify_with_custom_agent_id(self, client):
        """Test verification with custom agent ID."""
        request_data = {
            "claim": "The Earth is round",
            "agent_id": "custom_agent"
        }
        
        response = client.post("/api/verify", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        result = data["result"]
        
        assert result["agent_id"] == "custom_agent"
    
    def test_verify_different_claim_types(self, client):
        """Test verification of different types of claims."""
        test_claims = [
            "The sky is blue",
            "2+2=4", 
            "The Earth is flat",
            "COVID-19 vaccines are effective",
            "Climate change is real"
        ]
        
        for claim in test_claims:
            response = client.post("/api/verify", json={"claim": claim})
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["result"]["claim"] == claim


class TestVerifyValidation:
    """Test cases for request validation."""
    
    def test_empty_claim_validation(self, client):
        """Test validation fails for empty claim."""
        response = client.post("/api/verify", json={"claim": ""})
        
        assert response.status_code == 422
    
    def test_missing_claim_validation(self, client):
        """Test validation fails for missing claim."""
        response = client.post("/api/verify", json={})
        
        assert response.status_code == 422
    
    def test_claim_too_long_validation(self, client):
        """Test validation fails for claim that's too long."""
        long_claim = "A" * 2001  # Max is 2000
        response = client.post("/api/verify", json={"claim": long_claim})
        
        assert response.status_code == 422
    
    def test_invalid_agent_id_validation(self, client):
        """Test validation fails for agent ID that's too long."""
        long_agent_id = "A" * 101  # Max is 100
        response = client.post("/api/verify", json={
            "claim": "Test claim",
            "agent_id": long_agent_id
        })
        
        assert response.status_code == 422
    
    def test_invalid_json_validation(self, client):
        """Test validation fails for invalid JSON."""
        response = client.post(
            "/api/verify", 
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422


class TestRateLimiting:
    """Test cases for rate limiting functionality."""
    
    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are present in successful responses."""
        response = client.post("/api/verify", json={"claim": "Test claim"})
        
        assert response.status_code == 200
        assert "x-ratelimit-limit" in response.headers
        assert "x-ratelimit-remaining" in response.headers
        assert "x-ratelimit-reset" in response.headers
        
        limit = int(response.headers["x-ratelimit-limit"])
        remaining = int(response.headers["x-ratelimit-remaining"])
        
        assert limit == 10  # Default rate limit
        assert 0 <= remaining <= limit
    
    def test_rate_limit_enforcement(self, client):
        """Test that rate limiting is enforced after limit is exceeded."""
        # Make requests up to the limit
        for i in range(10):
            response = client.post("/api/verify", json={"claim": f"Test claim {i}"})
            assert response.status_code == 200
        
        # The 11th request should be rate limited
        response = client.post("/api/verify", json={"claim": "Rate limited claim"})
        
        assert response.status_code == 429
        data = response.json()
        
        assert data["success"] is False
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "rate_limit" in data
        assert data["rate_limit"]["remaining"] == 0
    
    def test_rate_limit_skips_health_endpoints(self, client):
        """Test that rate limiting doesn't apply to health check endpoints."""
        # Exhaust the rate limit first
        for i in range(10):
            response = client.post("/api/verify", json={"claim": f"Test claim {i}"})
            assert response.status_code == 200
        
        # Verify next request is rate limited
        response = client.post("/api/verify", json={"claim": "Should be rate limited"})
        assert response.status_code == 429
        
        # But health endpoints should still work
        response = client.get("/")
        assert response.status_code == 200
        
        response = client.get("/api/health")
        assert response.status_code == 200
        
        response = client.get("/api/docs")
        assert response.status_code == 200


class TestHealthEndpoints:
    """Test cases for health check endpoints."""
    
    def test_root_health_check(self, client):
        """Test the root health check endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "ConsensusNet API"
        assert data["version"] == "0.1.0"
        assert "environment" in data
    
    def test_detailed_health_check(self, client):
        """Test the detailed health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert "checks" in data
        assert data["checks"]["api"] == "operational"


class TestVerificationStats:
    """Test cases for verification statistics endpoint."""
    
    def test_verification_stats(self, client):
        """Test the verification stats endpoint."""
        response = client.get("/api/verify/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "operational"
        assert data["service"] == "verification"
        assert "active_agents" in data
        assert "agent_ids" in data
        assert "agents" in data
        
        assert isinstance(data["active_agents"], int)
        assert isinstance(data["agent_ids"], list)
        assert isinstance(data["agents"], dict)


class TestOpenAPIDocumentation:
    """Test cases for OpenAPI documentation."""
    
    def test_openapi_docs_accessible(self, client):
        """Test that OpenAPI documentation is accessible."""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "swagger-ui" in response.text.lower()
    
    def test_openapi_schema_accessible(self, client):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        assert "openapi" in schema
        assert "paths" in schema
        assert "/api/verify" in schema["paths"]
        assert "post" in schema["paths"]["/api/verify"]