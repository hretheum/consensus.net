# ConsensusNet API Specification

## Overview

The ConsensusNet API provides a comprehensive interface for AI-powered fact-checking and claim verification. The API is built using FastAPI with automatic OpenAPI documentation generation.

**Base URL**: `http://localhost:8000` (development)  
**API Version**: 1.0.0  
**Documentation**: `/api/docs` (Swagger UI), `/api/redoc` (ReDoc)  

## Authentication

### API Key Authentication

The API supports optional API key-based authentication using Bearer tokens:

```http
Authorization: Bearer <your-api-key>
```

### Service Tiers

| Tier | Rate Limit | Demo Key |
|------|------------|----------|
| **Anonymous** | 5 requests/minute | N/A |
| **Free** | 10 req/min, 100/hour, 1000/day | `demo_key_12345` |
| **Premium** | 100 req/min, 5000/hour, 50000/day | `test_premium_67890` |

### Permissions

API keys have different permission levels:
- `verify`: Access to claim verification endpoints
- `status`: Access to agent status information
- `admin`: Administrative access (future)

## Endpoints

### 1. Verify Claim

**POST** `/api/v1/verify`

Submit a claim for AI-powered fact-checking verification.

#### Request

```json
{
  "claim": "The Earth is round",
  "context": "Basic astronomy fact",
  "priority": "normal",
  "require_sources": true
}
```

#### Request Schema

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `claim` | string | Yes | The claim to verify (1-5000 characters) |
| `context` | string | No | Additional context (max 2000 characters) |
| `priority` | enum | No | Priority level: "low", "normal", "high" |
| `require_sources` | boolean | No | Whether to require source citations (default: true) |

#### Response

```json
{
  "success": true,
  "verification": {
    "claim": "The Earth is round",
    "verdict": "UNCERTAIN",
    "confidence": 0.48,
    "reasoning": "1. Gathered 2 pieces of evidence (confidence: 0.75) | 2. LLM provided verification analysis (confidence: 0.30) | 3. Combined evidence and LLM analysis for final verdict (confidence: 0.48)",
    "sources": ["wikipedia.org", "britannica.com"],
    "evidence": [
      "evidence_gathering: Gathered 2 pieces of evidence",
      "llm_analysis: LLM provided verification analysis",
      "verdict_calculation: Combined evidence and LLM analysis for final verdict"
    ],
    "metadata": {
      "processing_time": 0.00004673004150390625,
      "steps_count": 3,
      "domain": "general",
      "complexity": "simple",
      "uncertainty_factors": [],
      "request_context": "Basic astronomy fact",
      "priority": "normal",
      "require_sources": true
    },
    "timestamp": "2025-07-03T14:05:41.719841",
    "agent_id": "SimpleAgent"
  },
  "request_id": "64c42e5e-3f41-4ee1-ab36-e7a876faaeee",
  "processing_time_ms": 0,
  "api_version": "1.0"
}
```

#### Status Codes

- `200 OK`: Verification completed successfully
- `400 Bad Request`: Invalid request format
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### 2. Agent Status

**GET** `/api/v1/agent/status`

Retrieve current status and capabilities of the AI agent.

#### Response

```json
{
  "agent_id": "SimpleAgent",
  "status": "healthy",
  "capabilities": [
    {
      "capability": "claim_verification",
      "enabled": true,
      "description": "Verify factual claims using AI reasoning and evidence gathering",
      "performance_metrics": {
        "average_accuracy": 0.75,
        "average_confidence": 0.68,
        "processing_time_ms": 0
      }
    }
  ],
  "uptime_seconds": 30.843297958374023,
  "total_verifications": 0,
  "average_response_time_ms": 0.0,
  "success_rate": 0.95,
  "last_verification": null,
  "version": "1.0.0"
}
```

### 3. Health Check

**GET** `/api/v1/health`

Comprehensive health check for the API and its components.

#### Response

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2025-07-03T14:05:25.888426",
  "uptime_seconds": 22.97970151901245,
  "checks": {
    "api": {
      "status": "operational",
      "response_time_ms": 5,
      "version": "1.0.0"
    },
    "agents": {
      "status": "operational",
      "available_agents": 1,
      "response_time_ms": 0,
      "total_verifications": 0
    },
    "database": {
      "status": "pending",
      "message": "Database not yet implemented"
    },
    "redis": {
      "status": "pending",
      "message": "Redis caching not yet implemented"
    }
  }
}
```

### 4. Root Information

**GET** `/`

Basic API information and available endpoints.

## Error Handling

All errors follow a consistent format:

```json
{
  "error": true,
  "error_type": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {
      "code": "string_too_short",
      "message": "String should have at least 1 character",
      "field": "body.claim"
    }
  ],
  "timestamp": "2025-07-03T14:07:49.624606",
  "request_id": "8d8672a7-b190-4683-8024-31d70a6cdc15"
}
```

### Error Types

- `VALIDATION_ERROR`: Request validation failed
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `RATE_LIMIT_EXCEEDED`: Rate limit exceeded
- `VERIFICATION_ERROR`: Error during claim verification
- `INTERNAL_SERVER_ERROR`: Unexpected server error

## Rate Limiting

Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 9
X-RateLimit-Reset: 2025-07-03T14:08:49.624606
Retry-After: 60
```

When rate limits are exceeded, a `429 Too Many Requests` response is returned with retry information.

## Data Models

### VerificationResult

The core model representing a fact-checking verification result:

| Field | Type | Description |
|-------|------|-------------|
| `claim` | string | The original claim that was verified |
| `verdict` | string | The verification verdict (TRUE, FALSE, UNCERTAIN, ERROR) |
| `confidence` | float | Confidence score between 0 and 1 |
| `reasoning` | string | Explanation of the verification reasoning |
| `sources` | array[string] | List of source URLs used for verification |
| `evidence` | array[string] | Key pieces of evidence found |
| `metadata` | object | Additional metadata about the verification |
| `timestamp` | string | When the verification was performed (ISO 8601) |
| `agent_id` | string | Identifier of the agent that performed verification |

### AgentCapability

Information about an agent's capabilities:

| Field | Type | Description |
|-------|------|-------------|
| `capability` | string | Name of the capability |
| `enabled` | boolean | Whether this capability is currently enabled |
| `description` | string | Description of what this capability does |
| `performance_metrics` | object | Performance metrics for this capability |

## OpenAPI Specification

The complete OpenAPI 3.0 specification is available at:
- **JSON Format**: `/openapi.json`
- **Interactive Documentation**: `/api/docs` (Swagger UI)
- **Alternative Documentation**: `/api/redoc` (ReDoc)

## Usage Examples

### cURL Examples

#### Basic Verification (No Authentication)

```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -d '{"claim": "The Earth is round"}'
```

#### Authenticated Verification

```bash
curl -X POST http://localhost:8000/api/v1/verify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer demo_key_12345" \
  -d '{
    "claim": "Water boils at 100°C at sea level",
    "context": "Basic chemistry fact",
    "priority": "high"
  }'
```

#### Check Agent Status

```bash
curl -X GET http://localhost:8000/api/v1/agent/status \
  -H "Authorization: Bearer demo_key_12345"
```

### Python Example

```python
import requests

# Configuration
API_BASE = "http://localhost:8000"
API_KEY = "demo_key_12345"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

# Verify a claim
response = requests.post(
    f"{API_BASE}/api/v1/verify",
    json={
        "claim": "The Great Wall of China is visible from space",
        "priority": "high",
        "require_sources": True
    },
    headers=headers
)

if response.status_code == 200:
    result = response.json()
    print(f"Verdict: {result['verification']['verdict']}")
    print(f"Confidence: {result['verification']['confidence']}")
    print(f"Reasoning: {result['verification']['reasoning']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### JavaScript Example

```javascript
const API_BASE = "http://localhost:8000";
const API_KEY = "demo_key_12345";

async function verifyFact(claim) {
    try {
        const response = await fetch(`${API_BASE}/api/v1/verify`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${API_KEY}`
            },
            body: JSON.stringify({
                claim: claim,
                priority: 'normal',
                require_sources: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        return result;
    } catch (error) {
        console.error('Error verifying fact:', error);
        throw error;
    }
}

// Usage
verifyFact("Humans have landed on the Moon")
    .then(result => {
        console.log('Verification Result:', result.verification);
    })
    .catch(error => {
        console.error('Verification failed:', error);
    });
```

## Security Considerations

1. **API Key Management**: Store API keys securely and never expose them in client-side code
2. **Rate Limiting**: Respect rate limits to avoid service interruption
3. **HTTPS**: Use HTTPS in production environments
4. **Input Validation**: The API validates all inputs, but clients should also validate data
5. **Error Handling**: Don't expose sensitive information in error messages

## Future Enhancements

- OAuth 2.0 authentication
- Webhook support for async processing
- Batch verification endpoints
- Advanced filtering and search capabilities
- Real-time verification status updates via WebSockets
- Multi-language support
- Custom agent configurations per API key

## Support

For API support, please:
1. Check the interactive documentation at `/api/docs`
2. Review this specification
3. Contact the development team via GitHub issues
4. Check the project repository: https://github.com/hretheum/consensus.net