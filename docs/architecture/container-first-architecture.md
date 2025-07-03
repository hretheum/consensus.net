# Container-First Architecture for ConsensusNet

## Overview

ConsensusNet follows a strict container-first approach where:
- **All services run in containers** (both local and production)
- **No source code on production** servers
- **Images built in CI/CD** pipeline only
- **GitHub Container Registry** (ghcr.io) for image storage
- **Production only pulls** pre-built images

## Architecture Principles

### 1. Development = Production
```yaml
# Same docker-compose.yml structure for both environments
# Only env vars and volumes differ
```

### 2. Immutable Infrastructure
- Containers are never modified after build
- Updates = new image version
- Easy rollback to previous versions

### 3. Security First
- No source code on production servers
- No build tools on production
- Minimal attack surface

## Service Containerization Strategy

### Core Services (Containerized)

#### 1. API Service (FastAPI)
```dockerfile
# Dockerfile.api
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Agent Workers
```dockerfile
# Dockerfile.agent
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/agents/ ./src/agents/
CMD ["python", "-m", "src.agents.worker"]
```

#### 3. Frontend (Next.js)
```dockerfile
# Dockerfile.frontend
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package*.json ./
RUN npm ci --production
CMD ["npm", "start"]
```

#### 4. Nginx Reverse Proxy
```dockerfile
# Dockerfile.nginx
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY ssl/ /etc/nginx/ssl/
```

### Managed Services (Not Containerized)

1. **PostgreSQL** - Use DO Managed Database
   - Automated backups
   - High availability
   - Security patches

2. **Redis** (Optional) - DO Managed Redis or container
   - For caching: container is fine
   - For persistent data: use managed

## CI/CD Pipeline Configuration

### GitHub Actions Workflow

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Build and push API image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile.api
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/api:${{ github.sha }}
      
      - name: Build and push Agent image
        uses: docker/build-push-action@v4
        with:
          context: .
          file: ./Dockerfile.agent
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/agent:latest
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/agent:${{ github.sha }}
      
      # Repeat for other services...
      
  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    
    steps:
      - name: Deploy to Digital Ocean
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.DO_HOST }}
          username: ${{ secrets.DO_USER }}
          key: ${{ secrets.DO_SSH_KEY }}
          script: |
            # Pull latest images
            docker compose -f /app/docker-compose.prod.yml pull
            
            # Restart services with new images
            docker compose -f /app/docker-compose.prod.yml up -d
            
            # Clean up old images
            docker image prune -f
```

## Local Development Setup

### docker-compose.yml (Development)
```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    volumes:
      - ./src:/app/src  # Hot reload for development
    environment:
      - ENV=development
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis

  agent:
    build:
      context: .
      dockerfile: Dockerfile.agent
    volumes:
      - ./src:/app/src
    environment:
      - ENV=development
    depends_on:
      - db
      - redis

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.frontend.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    ports:
      - "3000:3000"

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: consensusnet
      POSTGRES_USER: consensus
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.dev.conf:/etc/nginx/nginx.conf
    ports:
      - "80:80"
    depends_on:
      - api
      - frontend

volumes:
  postgres_data:
```

## Production Deployment

### docker-compose.prod.yml (Production)
```yaml
version: '3.8'

services:
  api:
    image: ghcr.io/hretheum/consensus.net/api:latest
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}  # DO Managed DB
      - REDIS_URL=${REDIS_URL}
    restart: unless-stopped
    networks:
      - consensusnet

  agent:
    image: ghcr.io/hretheum/consensus.net/agent:latest
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    restart: unless-stopped
    deploy:
      replicas: 3  # Multiple agent instances
    networks:
      - consensusnet

  frontend:
    image: ghcr.io/hretheum/consensus.net/frontend:latest
    environment:
      - NODE_ENV=production
    restart: unless-stopped
    networks:
      - consensusnet

  nginx:
    image: ghcr.io/hretheum/consensus.net/nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./letsencrypt:/etc/letsencrypt
    restart: unless-stopped
    networks:
      - consensusnet

  # Optional: Redis if not using managed
  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - consensusnet

networks:
  consensusnet:
    driver: bridge

volumes:
  redis_data:
```

### Production Server Setup

```bash
#!/bin/bash
# setup-production.sh - Run once on new DO droplet

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt update
apt install -y docker-compose-plugin

# Create app directory
mkdir -p /app
cd /app

# Copy only docker-compose.prod.yml and .env
# NO source code!

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin

# Pull and start services
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

## Environment Configuration

### Development (.env.development)
```bash
ENV=development
DATABASE_URL=postgresql://consensus:password@db:5432/consensusnet
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=sk-...
```

### Production (.env.production)
```bash
ENV=production
DATABASE_URL=postgresql://doadmin:xxx@db-consensusnet.b.db.ondigitalocean.com:25060/defaultdb?sslmode=require
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=sk-...
```

## Benefits of This Approach

1. **Security**
   - No source code on production
   - No build tools on production
   - Minimal attack surface

2. **Consistency**
   - Same container runs everywhere
   - No environment-specific bugs

3. **Scalability**
   - Easy horizontal scaling
   - Load balancing ready

4. **Maintenance**
   - Easy rollbacks
   - Blue-green deployments possible
   - Clear separation of concerns

5. **Cost Efficiency**
   - Smaller droplet needed (no build tools)
   - Better resource utilization

## Migration Path

Week 1-2: Local containers only
Week 3: Deploy containers to DO
Week 4+: Iterate with confidence

## Monitoring Considerations

Add monitoring containers to production:
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
grafana:
  image: grafana/grafana:latest
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
```

---

This container-first approach ensures professional, scalable deployment from day one.