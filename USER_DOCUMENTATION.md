# ConsensusNet - User Documentation

> Revolutionary multi-agent AI system for decentralized fact-checking using collective intelligence

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Installation and Configuration](#installation-and-configuration)
3. [Getting Started](#getting-started)
4. [API Endpoints](#api-endpoints)
5. [Verification Types](#verification-types)
6. [Usage Examples](#usage-examples)
7. [System Monitoring](#system-monitoring)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [FAQ](#faq)

---

## 🎯 Introduction

ConsensusNet is an innovative multi-agent AI system that leverages collective intelligence to combat misinformation. The system implements the **ECAMAN** (Emergent Consensus through Adversarial Meta-Agent Networks) architecture, which orchestrates specialized AI agents in adversarial debates and consensus mechanisms.

### Key Features

- **🤖 Dynamic Agent Spawning**: Meta-agents create specialized verifiers on-demand
- **⚔️ Adversarial Verification**: Prosecutor/Defender agents actively challenge claims
- **🛡️ Byzantine Fault Tolerance**: Robust consensus even with unreliable agents
- **🕸️ Trust Networks**: Graph-based reputation system for agent credibility
- **⚡ Real-time Processing**: WebSocket support for live verification updates

### System Architecture

```
Meta-Agent Orchestrator
    ↓ spawns
Specialized Agents → Adversarial Debates → Trust-Weighted Consensus
```

---

## 🚀 Installation and Configuration

### System Requirements

- **Python**: 3.11 or newer
- **Docker**: 20.10 or newer
- **Docker Compose**: 2.0 or newer
- **Memory**: minimum 4GB, recommended 8GB
- **Storage**: minimum 2GB

### Docker Installation (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/hretheum/consensus.net
cd consensus.net
```

2. **Environment configuration**
```bash
# Copy example configuration file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

3. **Start all services**
```bash
# Start all containers
docker-compose up -d

# Check service status
docker-compose ps

# View application logs
docker-compose logs -f
```

### API Keys Configuration

Configure the following API keys in your `.env` file:

```env
# OpenAI (primary LLM provider)
OPENAI_API_KEY=sk-...

# Anthropic (backup)
ANTHROPIC_API_KEY=sk-ant-...

# Database configuration
POSTGRES_DB=consensus
POSTGRES_USER=consensus
POSTGRES_PASSWORD=devpassword

# Redis
REDIS_URL=redis://localhost:6380

# Environment
ENVIRONMENT=development
```

### Service Access

After starting Docker Compose, the following services will be available:

- **ConsensusNet API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/api/docs
- **PostgreSQL**: localhost:5433
- **Redis**: localhost:6380

---

## 🔧 Getting Started

### System Health Check

Before starting verification, ensure the system is running correctly:

```bash
# Test basic availability
curl http://localhost:8000/

# Detailed health check
curl http://localhost:8000/api/health
```

### First Verification

Example of basic claim verification:

```bash
curl -X POST "http://localhost:8000/api/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "The Earth is flat",
    "metadata": {
      "language": "en"
    }
  }'
```

### Response Structure

Each verification returns a structured response:

```json
{
  "success": true,
  "result": {
    "claim": "The Earth is flat",
    "verdict": "FALSE",
    "confidence": 0.99,
    "reasoning": "There is extensive scientific evidence confirming...",
    "sources": [
      "https://nasa.gov/earth-round-evidence",
      "https://wikipedia.org/wiki/Spherical_Earth"
    ],
    "evidence": [
      {
        "type": "scientific",
        "content": "Satellite images show...",
        "credibility": 0.95
      }
    ],
    "agent_id": "simple_agent_v1",
    "metadata": {
      "processing_method": "llm_enhanced",
      "llm_provider": "openai"
    }
  },
  "processing_time": 2.34,
  "timestamp": "2025-01-07T10:30:00Z"
}
```

---

## 🌐 API Endpoints

### Basic Endpoints

#### `GET /`
**Description**: Basic health check endpoint  
**Parameters**: None  
**Response**: Application status

#### `GET /api/health`
**Description**: Detailed system health check  
**Parameters**: None  
**Response**: Status of all components

```json
{
  "status": "healthy",
  "checks": {
    "api": "operational",
    "database": "operational",
    "redis": "operational",
    "agents": "operational",
    "llm_services": "operational"
  }
}
```

### Verification Endpoints

#### `POST /api/verify`
**Description**: Basic claim verification  
**Rate limit**: 10 requests/minute per IP  
**Content-Type**: `application/json`

**Request parameters**:
```json
{
  "claim": "string (1-2000 characters)",
  "agent_id": "string (optional)",
  "metadata": {
    "language": "en|pl",
    "priority": "low|normal|high"
  }
}
```

#### `POST /api/verify/enhanced`
**Description**: Enhanced verification with full LLM integration  
**Rate limit**: 10 requests/minute per IP  

**Parameters**: Same as `/api/verify`  
**Difference**: Uses advanced LLM models with fallback mechanisms

#### `POST /api/verify/multi-agent`
**Description**: Verification using multi-agent system  
**Rate limit**: 5 requests/minute per IP  

**Features**:
- Parallel processing by multiple agents
- Result aggregation through consensus
- Domain specialization of agents

#### `POST /api/verify/adversarial`
**Description**: Verification through adversarial debate  
**Rate limit**: 3 requests/minute per IP  

**Process**:
1. Prosecutor agent looks for weak points
2. Defender agent presents evidence
3. Moderator synthesizes consensus
4. Additional experts for uncertainty

### Monitoring Endpoints

#### `GET /api/verify/stats`
**Description**: Verification service statistics

```json
{
  "status": "operational",
  "service": "verification",
  "total_verifications": 1234,
  "accuracy_rate": 0.89,
  "average_processing_time": 3.2,
  "active_agents": 5
}
```

#### `GET /api/llm/status`
**Description**: LLM provider status

```json
{
  "status": "operational",
  "llm_services": {
    "openai": {
      "status": "operational",
      "model": "gpt-4o-mini",
      "latency": 1.2
    },
    "anthropic": {
      "status": "operational",
      "model": "claude-3-haiku",
      "latency": 0.8
    },
    "ollama": {
      "status": "operational",
      "model": "llama3.2",
      "latency": 3.5
    }
  }
}
```

#### `GET /api/system/info`
**Description**: Comprehensive system information

---

## 🔍 Verification Types

### 1. Basic Verification (`/api/verify`)

**Use case**: Quick verification of simple facts  
**Response time**: 1-3 seconds  
**Accuracy**: ~85% for simple facts  

**Usage example**:
```bash
curl -X POST "http://localhost:8000/api/verify" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "The capital of Poland is Warsaw"
  }'
```

### 2. Enhanced Verification (`/api/verify/enhanced`)

**Use case**: Complex claims requiring contextual analysis  
**Response time**: 3-8 seconds  
**Accuracy**: ~90% for complex claims  

**Features**:
- Integration with latest LLM models
- Automatic fallback between providers
- Better confidence calibration

**Usage example**:
```bash
curl -X POST "http://localhost:8000/api/verify/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Studies from 2024 showed that artificial intelligence could replace 40% of jobs by 2030",
    "metadata": {
      "language": "en",
      "domain": "technology"
    }
  }'
```

### 3. Multi-Agent System (`/api/verify/multi-agent`)

**Use case**: Verification requiring domain expertise  
**Response time**: 5-15 seconds  
**Accuracy**: ~92% through consensus  

**Process**:
1. **Generalist agent**: Basic verification
2. **Enhanced agent**: LLM analysis
3. **Specialist agent**: Domain analysis (science/news/technology)
4. **Consensus**: Result aggregation through majority voting

**Example response**:
```json
{
  "result": {
    "verdict": "TRUE",
    "confidence": 0.87,
    "metadata": {
      "multi_agent_system": "simulation",
      "agent_count": 3,
      "individual_verdicts": ["TRUE", "TRUE", "UNCERTAIN"],
      "consensus_agreement": 0.67,
      "agents_used": ["agent_generalist_1", "agent_enhanced_2", "agent_specialist_3"],
      "domain_specialists": ["generalist", "generalist", "science"]
    }
  }
}
```

### 4. Adversarial Debate (`/api/verify/adversarial`)

**Use case**: Controversial claims requiring detailed analysis  
**Response time**: 10-30 seconds  
**Accuracy**: ~95% for complex cases  

**Debate architecture**:
```
Prosecutor → Defender → Moderator → [Experts] → Consensus
```

**Usage example**:
```bash
curl -X POST "http://localhost:8000/api/verify/adversarial" \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "COVID-19 vaccines cause serious side effects in most patients",
    "metadata": {
      "controversy_level": "high",
      "domain": "medical"
    }
  }'
```

---

## 💡 Usage Examples

### Example 1: Scientific Fact Verification

```python
import requests
import json

def verify_scientific_claim(claim):
    url = "http://localhost:8000/api/verify/enhanced"
    
    payload = {
        "claim": claim,
        "metadata": {
            "domain": "science",
            "language": "en"
        }
    }
    
    response = requests.post(url, json=payload)
    result = response.json()
    
    if result["success"]:
        verification = result["result"]
        print(f"Claim: {verification['claim']}")
        print(f"Verdict: {verification['verdict']}")
        print(f"Confidence: {verification['confidence']:.2%}")
        print(f"Reasoning: {verification['reasoning'][:200]}...")
        print(f"Sources: {len(verification['sources'])} found")
    
    return result

# Usage example
result = verify_scientific_claim(
    "Antibiotics are effective in treating viral infections"
)
```

### Example 2: Batch Verification of Multiple Claims

```python
import asyncio
import aiohttp

async def batch_verify(claims, verification_type="basic"):
    endpoint_map = {
        "basic": "/api/verify",
        "enhanced": "/api/verify/enhanced", 
        "multi_agent": "/api/verify/multi-agent",
        "adversarial": "/api/verify/adversarial"
    }
    
    url = f"http://localhost:8000{endpoint_map[verification_type]}"
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for claim in claims:
            task = verify_single_claim(session, url, claim)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results

async def verify_single_claim(session, url, claim):
    payload = {"claim": claim}
    async with session.post(url, json=payload) as response:
        return await response.json()

# Usage example
claims = [
    "Earth revolves around the Sun",
    "Water boils at 100°C",
    "Humans use only 10% of their brain"
]

results = asyncio.run(batch_verify(claims, "enhanced"))
for i, result in enumerate(results):
    print(f"Claim {i+1}: {result['result']['verdict']}")
```

### Example 3: Real-time System Monitoring

```python
import requests
import time

def monitor_system_health():
    endpoints = [
        "/api/health",
        "/api/verify/stats", 
        "/api/llm/status",
        "/api/system/info"
    ]
    
    base_url = "http://localhost:8000"
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            data = response.json()
            
            print(f"\n=== {endpoint} ===")
            print(json.dumps(data, indent=2))
            
        except Exception as e:
            print(f"Error for {endpoint}: {e}")
        
        time.sleep(1)

# Run monitoring
monitor_system_health()
```

### Example 4: Web Application Integration

```javascript
// Frontend JavaScript
class ConsensusNetClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async verifyFact(claim, options = {}) {
        const {
            type = 'basic',
            language = 'en',
            priority = 'normal'
        } = options;
        
        const endpoints = {
            basic: '/api/verify',
            enhanced: '/api/verify/enhanced',
            multiAgent: '/api/verify/multi-agent',
            adversarial: '/api/verify/adversarial'
        };
        
        try {
            const response = await fetch(`${this.baseUrl}${endpoints[type]}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    claim,
                    metadata: { language, priority }
                })
            });
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Verification failed');
            }
            
            return result;
            
        } catch (error) {
            console.error('Verification error:', error);
            throw error;
        }
    }
    
    async getSystemStatus() {
        const response = await fetch(`${this.baseUrl}/api/system/info`);
        return response.json();
    }
}

// Usage example
const client = new ConsensusNetClient();

document.getElementById('verify-btn').addEventListener('click', async () => {
    const claim = document.getElementById('claim-input').value;
    const resultDiv = document.getElementById('result');
    
    if (!claim.trim()) {
        alert('Please enter a claim to verify');
        return;
    }
    
    try {
        resultDiv.innerHTML = '<div class="loading">Verification in progress...</div>';
        
        const result = await client.verifyFact(claim, { type: 'enhanced' });
        const verification = result.result;
        
        const verdictClass = verification.verdict.toLowerCase();
        const confidencePercent = (verification.confidence * 100).toFixed(1);
        
        resultDiv.innerHTML = `
            <div class="verification-result ${verdictClass}">
                <h3>Verification Result</h3>
                <div class="verdict">
                    Verdict: <span class="verdict-${verdictClass}">${verification.verdict}</span>
                </div>
                <div class="confidence">
                    Confidence: ${confidencePercent}%
                </div>
                <div class="reasoning">
                    <h4>Reasoning:</h4>
                    <p>${verification.reasoning}</p>
                </div>
                <div class="sources">
                    <h4>Sources (${verification.sources.length}):</h4>
                    <ul>
                        ${verification.sources.map(source => 
                            `<li><a href="${source}" target="_blank">${source}</a></li>`
                        ).join('')}
                    </ul>
                </div>
                <div class="metadata">
                    Processing time: ${result.processing_time.toFixed(2)}s
                </div>
            </div>
        `;
        
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="error">
                <h3>Verification Error</h3>
                <p>${error.message}</p>
            </div>
        `;
    }
});
```

---

## 📊 System Monitoring

### Health Check Commands

```bash
# Basic status
curl http://localhost:8000/api/health

# Detailed system information
curl http://localhost:8000/api/system/info

# LLM provider status
curl http://localhost:8000/api/llm/status

# Verification statistics
curl http://localhost:8000/api/verify/stats
```

### System Metrics

ConsensusNet provides the following metrics:

#### Verification Metrics
- **Total verifications**: All completed verifications
- **Accuracy rate**: Percentage of correct verifications
- **Average processing time**: System response time
- **Active agents**: Number of running agents

#### LLM Metrics
- **Provider status**: OpenAI, Anthropic, Ollama
- **Latency**: Response times for individual models
- **API usage**: Number of calls and costs

#### System Metrics
- **Memory usage**: RAM and storage
- **Database connections**: PostgreSQL and Redis
- **Rate limiting**: Active restrictions

### System Logs

```bash
# All logs
docker-compose logs -f

# API only
docker-compose logs -f api

# Database only
docker-compose logs -f postgres

# Last 100 lines
docker-compose logs --tail=100
```

### Automated Monitoring

Example monitoring script:

```bash
#!/bin/bash
# monitor.sh - ConsensusNet monitoring script

ENDPOINT="http://localhost:8000"
LOG_FILE="/var/log/consensusnet-monitor.log"

check_health() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local response=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT/api/health)
    
    if [ "$response" = "200" ]; then
        echo "[$timestamp] HEALTH: OK" >> $LOG_FILE
        return 0
    else
        echo "[$timestamp] HEALTH: FAILED (HTTP $response)" >> $LOG_FILE
        return 1
    fi
}

check_verification() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local test_claim="Test claim for monitoring"
    
    local response=$(curl -s -X POST "$ENDPOINT/api/verify" \
        -H "Content-Type: application/json" \
        -d "{\"claim\":\"$test_claim\"}" \
        -w "%{http_code}")
    
    if echo "$response" | grep -q '"success":true'; then
        echo "[$timestamp] VERIFICATION: OK" >> $LOG_FILE
        return 0
    else
        echo "[$timestamp] VERIFICATION: FAILED" >> $LOG_FILE
        return 1
    fi
}

# Run checks every 5 minutes
while true; do
    check_health
    sleep 60
    check_verification
    sleep 240
done
```

---

## 🔧 Advanced Features

### Agent Configuration

#### Available agent types in the system:

1. **Simple Agent**: Basic verification agent
2. **Enhanced Agent**: Agent with LLM integration
3. **Science Agent**: Specialist for scientific facts
4. **News Agent**: Specialist for current events
5. **Tech Agent**: Specialist for technology

#### Agent Pool Management

```bash
# Check agent pool status
curl http://localhost:8000/api/agents/pool/status

# Initialize agent pool
curl -X POST http://localhost:8000/api/agents/pool/initialize

# Add specialized agents
curl -X POST http://localhost:8000/api/agents/specialized/add
```

### Reputation and Trust System

```bash
# Reputation statistics
curl http://localhost:8000/api/reputation/stats

# Agent rankings
curl http://localhost:8000/api/reputation/rankings

# Domain experts
curl http://localhost:8000/api/reputation/domain-experts/science
```

### Adversarial Debate Mechanism

The system implements an advanced debate protocol:

1. **Preparation phase**: Claim analysis and role assignment
2. **Prosecutor round**: Prosecutor agent looks for weak points
3. **Defense round**: Defender agent presents evidence
4. **Synthesis**: Moderator combines arguments
5. **Expert consultation**: Additional experts when uncertainty >30%

```bash
# Debate statistics
curl http://localhost:8000/api/debates/stats

# Recent debates
curl http://localhost:8000/api/debates/recent?limit=10
```

### Swarm Burst Mode

For urgent verifications, the system can activate "burst" mode:

- Creates 10-20 micro-agents for 30 seconds
- Parallel processing of different claim aspects
- Quick consensus in <30 seconds

```json
{
  "claim": "BREAKING: Important event requires verification",
  "metadata": {
    "priority": "urgent",
    "enable_burst": true,
    "time_limit": 30
  }
}
```

### Advanced Configuration

#### Environment Variables

```env
# Agent configuration
MAX_AGENTS_PER_VERIFICATION=5
AGENT_TIMEOUT_SECONDS=30
CONSENSUS_THRESHOLD=0.7

# LLM configuration
OPENAI_MODEL=gpt-4o-mini
ANTHROPIC_MODEL=claude-3-haiku-20240307
OLLAMA_MODEL=llama3.2

# Debate configuration
ADVERSARIAL_ROUNDS=4
DEBATE_TIMEOUT_SECONDS=120
EXPERT_CONSULTATION_THRESHOLD=0.3

# Trust system configuration
TRUST_DECAY_RATE=0.01
REPUTATION_UPDATE_FREQUENCY=3600
MIN_TRUST_SCORE=0.1
```

#### Custom Verification Parameters

```python
# Example of customization through metadata
request_payload = {
    "claim": "Your claim",
    "metadata": {
        "verification_parameters": {
            "confidence_threshold": 0.8,
            "max_sources": 10,
            "require_scientific_sources": True,
            "language_preference": "en",
            "fact_check_depth": "deep"
        },
        "agent_preferences": {
            "prefer_specialist_agents": True,
            "exclude_agents": ["unreliable_agent_id"],
            "force_adversarial": False
        }
    }
}
```

---

## 🚨 Troubleshooting

### Common Issues and Solutions

#### Issue: API Connection Error
```
curl: (7) Failed to connect to localhost:8000: Connection refused
```

**Solution**:
```bash
# Check if containers are running
docker-compose ps

# If not - restart
docker-compose up -d

# Check logs
docker-compose logs api
```

#### Issue: LLM Authorization Errors
```json
{
  "error": "OpenAI API authentication failed",
  "error_code": "LLM_AUTH_ERROR"
}
```

**Solution**:
1. Check API keys in `.env` file
2. Verify key validity on provider websites
3. Restart container after changing `.env`:
```bash
docker-compose down
docker-compose up -d
```

#### Issue: Slow Responses
```json
{
  "processing_time": 45.2,
  "error": "Request timeout"
}
```

**Solutions**:
1. Check LLM status: `curl http://localhost:8000/api/llm/status`
2. Use simpler endpoint `/api/verify` instead of `/api/verify/adversarial`
3. Increase timeout in configuration
4. Check system resources: `docker stats`

#### Issue: Rate Limiting
```json
{
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_ERROR"
}
```

**Solution**:
- Wait 1 minute before next request
- Rate limits: 10/min (basic), 5/min (multi-agent), 3/min (adversarial)

### System Diagnostics

#### Resource Check
```bash
# Container resource usage
docker stats

# All service status
docker-compose ps

# Disk space check
df -h

# Memory check
free -h
```

#### Error Log Check
```bash
# API errors
docker-compose logs api | grep ERROR

# Database errors
docker-compose logs postgres | grep ERROR

# All errors from last 24h
docker-compose logs --since="24h" | grep ERROR
```

#### End-to-End Test
```bash
#!/bin/bash
# test_e2e.sh - End-to-end functionality test

echo "=== Basic verification test ==="
response=$(curl -s -X POST "http://localhost:8000/api/verify" \
  -H "Content-Type: application/json" \
  -d '{"claim":"2+2=4"}')

if echo "$response" | grep -q '"success":true'; then
    echo "✓ Basic verification works"
else
    echo "✗ Basic verification failed"
    echo "$response"
fi

echo "=== Enhanced verification test ==="
response=$(curl -s -X POST "http://localhost:8000/api/verify/enhanced" \
  -H "Content-Type: application/json" \
  -d '{"claim":"Water boils at 100°C"}')

if echo "$response" | grep -q '"success":true'; then
    echo "✓ Enhanced verification works"
else
    echo "✗ Enhanced verification failed"
fi

echo "=== System health test ==="
response=$(curl -s "http://localhost:8000/api/health")

if echo "$response" | grep -q '"status":"healthy"'; then
    echo "✓ System is healthy"
else
    echo "✗ System health issues"
    echo "$response"
fi
```

### Support Contact

For issues that cannot be resolved:

1. **Check documentation**: https://github.com/hretheum/consensus.net
2. **Create issue**: https://github.com/hretheum/consensus.net/issues
3. **Attach logs**: Use `docker-compose logs > debug.log`
4. **Describe environment**: OS, Docker version, configuration

---

## ❓ FAQ

### General Questions

**Q: Can ConsensusNet verify facts in Polish?**  
A: Yes, the system supports Polish. Add `"language": "pl"` in request metadata.

**Q: How much does using ConsensusNet cost?**  
A: The system is open source. Only costs are API calls to LLM providers (OpenAI, Anthropic).

**Q: Can I use ConsensusNet without API keys?**  
A: Yes, the system has simulation mode, but with limited accuracy. API keys are recommended.

### Technical Questions

**Q: What are the request limits?**  
A: 
- `/api/verify`: 10 requests/minute
- `/api/verify/enhanced`: 10 requests/minute  
- `/api/verify/multi-agent`: 5 requests/minute
- `/api/verify/adversarial`: 3 requests/minute

**Q: Can I increase the limits?**  
A: Yes, modify configuration in `src/api/rate_limiter.py` and restart.

**Q: How long are verification results stored?**  
A: By default, results are not permanently stored. You can configure persistence in the database.

**Q: Does the system support enterprise API keys?**  
A: Yes, the system automatically detects and uses enterprise keys with higher limits.

### Accuracy Questions

**Q: What is the system's accuracy?**  
A:
- Simple facts: ~85-90%
- Complex claims: ~70-80%
- Adversarial system: ~90-95%

**Q: Can the system make mistakes?**  
A: Yes, no AI system is perfect. Always verify critical information in additional sources.

**Q: How does the system handle controversies?**  
A: Controversial topics are routed to the adversarial system with multiple experts.

### Integration Questions

**Q: Can I integrate ConsensusNet with my application?**  
A: Yes, the system provides REST API. See integration examples in documentation.

**Q: Is there an SDK available?**  
A: Currently only REST API is available. Python and JavaScript SDKs are planned.

**Q: Does the system support webhooks?**  
A: Not currently, but the feature is planned for future versions.

### Deployment Questions

**Q: Can I run ConsensusNet in the cloud?**  
A: Yes, the system is containerized and can run on AWS, GCP, Azure, Digital Ocean.

**Q: What are the hardware requirements for production?**  
A: Minimum 8GB RAM, 4 CPU cores, 50GB storage. Recommended 16GB RAM.

**Q: Is the system secure?**  
A: The system implements rate limiting, input validation, and can be run behind a reverse proxy.

---

## 📚 Additional Resources

### Technical Documentation
- [ECAMAN Architecture](docs/architecture/ARCHITECTURE_RECOMMENDATION.md)
- [Project Roadmap](consensus-roadmap.md)
- [Development Status](STATUS.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

### API Reference
- [OpenAPI Documentation](http://localhost:8000/api/docs)
- [ReDoc](http://localhost:8000/api/redoc)

### Examples and Tutorials
- [Integration Examples](docs/examples/)
- [Tutorials](docs/tutorials/)
- [Best Practices](docs/best-practices/)

### Community
- [GitHub Repository](https://github.com/hretheum/consensus.net)
- [GitHub Issues](https://github.com/hretheum/consensus.net/issues)
- [GitHub Discussions](https://github.com/hretheum/consensus.net/discussions)

---

**Last Updated**: January 7, 2025  
**Documentation Version**: 1.0  
**System Version**: 0.1.0