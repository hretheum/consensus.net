# 🚀 ConsensusNet Deployment Guide

**Version**: 1.0  
**Last Updated**: January 2025  
**Status**: Production Ready

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Installation Methods](#installation-methods)
4. [Configuration](#configuration)
5. [Running the Application](#running-the-application)
6. [Verification & Testing](#verification--testing)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)
9. [Monitoring & Maintenance](#monitoring--maintenance)
10. [API Documentation](#api-documentation)

---

## 🏃 Quick Start

The fastest way to get ConsensusNet running:

```bash
# 1. Clone the repository
git clone <repository-url>
cd ConsensusNet

# 2. Copy environment configuration
cp .env.example .env

# 3. Start all services with Docker Compose
docker-compose up -d

# 4. Verify installation
curl http://localhost:8000/api/health

# 5. Access API documentation
open http://localhost:8000/api/docs
```

**That's it!** The API is now running at `http://localhost:8000`

---

## 💻 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Linux (Ubuntu 20.04+), macOS, Windows with WSL2 |
| **Python** | 3.11 or higher |
| **RAM** | 4GB minimum |
| **CPU** | 2 cores minimum |
| **Storage** | 10GB free space |
| **Docker** | 24.0+ (if using containers) |
| **Docker Compose** | 2.20+ (if using containers) |

### Recommended Production Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Ubuntu 22.04 LTS |
| **Python** | 3.11+ |
| **RAM** | 8GB or more |
| **CPU** | 4+ cores |
| **Storage** | 50GB+ SSD |
| **Network** | 100Mbps+ |

### External Services

| Service | Version | Purpose |
|---------|---------|---------|
| **PostgreSQL** | 15+ | Primary database |
| **Redis** | 7+ | Caching & job queue |
| **Nginx** | 1.24+ | Reverse proxy (production) |

---

## 📦 Installation Methods

### Method 1: Docker Compose (Recommended)

This is the easiest and most reliable method.

```bash
# 1. Install Docker and Docker Compose
# Ubuntu/Debian:
sudo apt update
sudo apt install docker.io docker-compose-v2

# macOS:
brew install docker docker-compose

# 2. Clone repository
git clone <repository-url>
cd ConsensusNet

# 3. Create environment file
cp .env.example .env

# 4. Build and start services
docker-compose build
docker-compose up -d

# 5. Check service status
docker-compose ps
```

### Method 2: Local Python Installation

For development or when Docker is not available.

```bash
# 1. Install Python 3.11+
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip

# macOS:
brew install python@3.11

# 2. Clone repository
git clone <repository-url>
cd ConsensusNet

# 3. Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# 4. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Install and run PostgreSQL
docker run -d \
  --name consensus-postgres \
  -e POSTGRES_USER=consensus_user \
  -e POSTGRES_PASSWORD=consensus_pass \
  -e POSTGRES_DB=consensus \
  -p 5432:5432 \
  postgres:15-alpine

# 6. Install and run Redis
docker run -d \
  --name consensus-redis \
  -p 6379:6379 \
  redis:7-alpine

# 7. Run database migrations (if needed)
cd src
python -m alembic upgrade head  # If using Alembic

# 8. Start the application
python main.py
```

### Method 3: Production Kubernetes Deployment

For scalable production deployments.

```yaml
# Save as consensus-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: consensus-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: consensus-api
  template:
    metadata:
      labels:
        app: consensus-api
    spec:
      containers:
      - name: api
        image: consensus/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: consensus-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: consensus-secrets
              key: redis-url
```

```bash
# Deploy to Kubernetes
kubectl apply -f consensus-deployment.yaml
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# === API Configuration ===
PORT=8000
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO
API_KEY_HEADER=X-API-Key  # Optional API key header

# === Database Configuration ===
DATABASE_URL=postgresql://consensus_user:consensus_pass@localhost:5432/consensus
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# === Redis Configuration ===
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50

# === LLM API Keys (Optional) ===
# For enhanced verification capabilities
OPENAI_API_KEY=sk-...          # GPT-4o-mini
ANTHROPIC_API_KEY=sk-ant-...   # Claude 3 Haiku
OLLAMA_BASE_URL=http://localhost:11434  # Local Ollama

# === Production Settings ===
# Caching
CACHE_TTL=3600  # 1 hour default
CACHE_MAX_SIZE=10000

# Job Queue
JOB_QUEUE_WORKERS=4
JOB_QUEUE_MAX_RETRIES=3
JOB_TIMEOUT=300  # 5 minutes

# Auto-scaling
ENABLE_AUTO_SCALING=true
MIN_INSTANCES=1
MAX_INSTANCES=10
SCALE_UP_THRESHOLD=70  # CPU %
SCALE_DOWN_THRESHOLD=30  # CPU %

# Monitoring
ENABLE_MONITORING=true
METRICS_RETENTION_HOURS=24
HEALTH_CHECK_INTERVAL=30  # seconds

# Circuit Breakers
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_TIMEOUT=60  # seconds
CIRCUIT_BREAKER_RECOVERY_TIME=120  # seconds

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Security
CORS_ORIGINS=["http://localhost:3000", "https://app.consensus.ai"]
ALLOWED_HOSTS=["localhost", "api.consensus.ai"]
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
```

### Configuration Files

#### `docker-compose.yml`
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://consensus_user:consensus_pass@postgres:5432/consensus
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./src:/app/src
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: consensus_user
      POSTGRES_PASSWORD: consensus_pass
      POSTGRES_DB: consensus
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

#### `requirements.txt`
```txt
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3

# Database
asyncpg==0.29.0
sqlalchemy==2.0.25
alembic==1.13.1

# Redis
redis==5.0.1
aioredis==2.0.1

# LLM Integrations
openai==1.8.0
anthropic==0.8.1
ollama==0.1.7

# Production Dependencies
gunicorn==21.2.0
prometheus-client==0.19.0
psutil==5.9.7

# Utilities
python-dotenv==1.0.0
httpx==0.26.0
tenacity==8.2.3
```

---

## 🚀 Running the Application

### Development Mode

```bash
# Using Docker Compose
docker-compose up

# Using Python directly
cd src
python main.py

# With auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```bash
# Using Docker Compose with production config
docker-compose -f docker-compose.prod.yml up -d

# Using Gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  --log-level info

# Using systemd service
sudo systemctl start consensus-api
sudo systemctl enable consensus-api
```

### Initializing Services

After starting the application, initialize the multi-agent system:

```bash
# 1. Initialize agent pool
curl -X POST http://localhost:8000/api/agents/pool/initialize

# 2. Add specialized agents
curl -X POST http://localhost:8000/api/agents/specialized/add

# 3. Start job queue workers
curl -X POST http://localhost:8000/api/v1/production/jobs/start

# 4. Enable monitoring
curl -X POST http://localhost:8000/api/v1/production/monitoring/enable
```

---

## ✅ Verification & Testing

### Basic Health Checks

```bash
# 1. API Health
curl http://localhost:8000/api/health

# Expected response:
{
  "status": "healthy",
  "checks": {
    "api": "operational",
    "database": "operational",
    "redis": "operational",
    "agents": "operational"
  }
}

# 2. System Status
curl http://localhost:8000/api/system/phase4

# 3. Production Health
curl http://localhost:8000/api/v1/production/health
```

### Test Verification Endpoints

```bash
# 1. Basic verification
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "The Earth orbits around the Sun",
    "context": "astronomy"
  }'

# 2. Multi-agent verification
curl -X POST http://localhost:8000/api/verify/multi-agent \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "COVID-19 vaccines are safe and effective",
    "context": "health"
  }'

# 3. Adversarial verification
curl -X POST http://localhost:8000/api/verify/adversarial \
  -H "Content-Type: application/json" \
  -d '{
    "claim": "Artificial Intelligence will replace all human jobs by 2030",
    "context": "technology"
  }'
```

### Load Testing

```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 100 concurrent requests
ab -n 1000 -c 100 -p test_claim.json -T application/json \
  http://localhost:8000/api/verify

# Using Python script
python tests/load_test.py --users 100 --duration 60
```

---

## 🏭 Production Deployment

### Pre-deployment Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up monitoring and alerting
- [ ] Create database backups
- [ ] Test auto-scaling policies
- [ ] Configure log aggregation

### Deployment Steps

#### 1. Server Setup (Ubuntu 22.04)

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.11 python3-pip nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash consensus
sudo usermod -aG docker consensus

# Clone repository
sudo -u consensus git clone <repository-url> /home/consensus/app
cd /home/consensus/app

# Set up environment
sudo -u consensus cp .env.example .env
# Edit .env with production values
sudo -u consensus nano .env
```

#### 2. Nginx Configuration

```nginx
# /etc/nginx/sites-available/consensus
server {
    listen 80;
    server_name api.consensus.ai;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/consensus /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Set up SSL
sudo certbot --nginx -d api.consensus.ai
```

#### 3. Systemd Service

```ini
# /etc/systemd/system/consensus-api.service
[Unit]
Description=ConsensusNet API
After=network.target

[Service]
Type=exec
User=consensus
WorkingDirectory=/home/consensus/app
Environment="PATH=/home/consensus/app/venv/bin"
ExecStart=/home/consensus/app/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable consensus-api
sudo systemctl start consensus-api
sudo systemctl status consensus-api
```

#### 4. Database Setup

```bash
# Create production database
sudo -u postgres psql

CREATE DATABASE consensus_prod;
CREATE USER consensus_prod WITH ENCRYPTED PASSWORD 'strong-password';
GRANT ALL PRIVILEGES ON DATABASE consensus_prod TO consensus_prod;
\q

# Run migrations
cd /home/consensus/app/src
python -m alembic upgrade head
```

#### 5. Monitoring Setup

```bash
# Install Prometheus Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter

# Create systemd service for node_exporter
sudo nano /etc/systemd/system/node_exporter.service
```

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue: "Connection to Redis failed"

**Symptoms**: Cache errors, job queue not working

**Solution**:
```bash
# Check Redis status
docker ps | grep redis
systemctl status redis

# Restart Redis
docker restart consensus-redis
# or
sudo systemctl restart redis

# Test connection
redis-cli ping
```

#### Issue: "Database connection pool exhausted"

**Symptoms**: Timeout errors, slow responses

**Solution**:
```bash
# Increase pool size in .env
DATABASE_POOL_SIZE=40
DATABASE_MAX_OVERFLOW=60

# Restart application
docker-compose restart api
```

#### Issue: "Port 8000 already in use"

**Solution**:
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>

# Or change port in .env
PORT=8001
```

#### Issue: "Import error: No module named 'consensus'"

**Solution**:
```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/ConsensusNet/src"

# Or run from src directory
cd src
python main.py
```

#### Issue: "LLM API rate limit exceeded"

**Solution**:
```bash
# Enable request batching
ENABLE_BATCH_PROCESSING=true
BATCH_MAX_WAIT_TIME=2.0
BATCH_MAX_SIZE=10

# Add fallback LLM providers
FALLBACK_TO_OLLAMA=true
```

### Debug Mode

Enable detailed logging:

```bash
# In .env
LOG_LEVEL=DEBUG
ENABLE_REQUEST_LOGGING=true

# View logs
docker-compose logs -f api
# or
tail -f logs/consensus.log
```

---

## 📊 Monitoring & Maintenance

### Metrics Endpoints

| Endpoint | Description |
|----------|-------------|
| `/api/v1/production/metrics` | System performance metrics |
| `/api/v1/production/health` | Comprehensive health status |
| `/api/v1/production/cache/stats` | Cache performance stats |
| `/api/v1/production/jobs/stats` | Job queue statistics |
| `/api/v1/production/scaling/status` | Auto-scaling status |

### Monitoring Dashboard

```bash
# Access Grafana dashboard (if configured)
open http://localhost:3000

# Default credentials
Username: admin
Password: admin
```

### Maintenance Tasks

#### Daily
- Check system health: `curl http://localhost:8000/api/v1/production/health`
- Review error logs: `docker-compose logs --tail=100 api | grep ERROR`
- Monitor cache hit rate

#### Weekly
- Clear old cache entries: `curl -X POST http://localhost:8000/api/v1/production/cache/cleanup`
- Review job queue performance
- Check disk usage: `df -h`

#### Monthly
- Update dependencies: `pip install -r requirements.txt --upgrade`
- Database maintenance: `VACUUM ANALYZE;`
- Review and rotate logs

### Backup Procedures

```bash
# Database backup
pg_dump -U consensus_user -h localhost consensus > backup_$(date +%Y%m%d).sql

# Redis backup
docker exec consensus-redis redis-cli BGSAVE

# Application backup
tar -czf consensus_backup_$(date +%Y%m%d).tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  /home/consensus/app
```

---

## 📚 API Documentation

### Interactive Documentation

Once the application is running, access:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

### Key API Endpoints

#### Core Verification
- `POST /api/verify` - Basic fact verification
- `POST /api/verify/multi-agent` - Multi-agent consensus verification
- `POST /api/verify/adversarial` - Adversarial debate verification

#### System Status
- `GET /api/health` - Basic health check
- `GET /api/system/info` - Comprehensive system information
- `GET /api/system/phase4` - Phase 4 production status

#### Production Features
- `GET /api/v1/production/health` - Production health monitoring
- `GET /api/v1/production/metrics` - Performance metrics
- `POST /api/v1/production/jobs/enqueue` - Enqueue background job
- `GET /api/v1/production/circuit-breakers` - Circuit breaker status

### Example API Usage

```python
import httpx
import asyncio

async def verify_claim(claim: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/verify",
            json={"claim": claim, "context": "general"}
        )
        return response.json()

# Run verification
result = asyncio.run(verify_claim("The speed of light is constant"))
print(f"Verdict: {result['result']['verdict']}")
print(f"Confidence: {result['result']['confidence']}")
```

---

## 🆘 Support & Resources

### Getting Help

1. **Documentation**: Check this guide and API docs
2. **Issues**: Report bugs on GitHub Issues
3. **Discussions**: Join our Discord community
4. **Email**: support@consensus.ai

### Useful Commands Cheatsheet

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f api

# Restart service
docker-compose restart api

# Check status
docker-compose ps

# Run tests
pytest tests/

# Update code
git pull origin main
docker-compose build
docker-compose up -d

# Database shell
docker exec -it consensus-postgres psql -U consensus_user -d consensus

# Redis shell
docker exec -it consensus-redis redis-cli
```

### Performance Tuning

For optimal performance:

1. **Enable caching**: Set appropriate `CACHE_TTL`
2. **Use connection pooling**: Configure pool sizes
3. **Enable batch processing**: For LLM requests
4. **Configure auto-scaling**: Based on load patterns
5. **Monitor metrics**: Use Grafana dashboards

---

## 📄 License & Credits

ConsensusNet is released under the MIT License.

**Built with**:
- FastAPI - Modern web framework
- PostgreSQL - Reliable database
- Redis - High-performance caching
- Docker - Container platform

---

**Happy Deploying! 🚀**

For the latest updates and documentation, visit: https://github.com/your-org/ConsensusNet