#!/bin/bash
# ========================================
# ConsensusNet - Digital Ocean Deployment Script
# ========================================
# This script automates the creation and configuration of a Digital Ocean Droplet
# for running ConsensusNet in production.
#
# Prerequisites:
# 1. Install doctl: https://docs.digitalocean.com/reference/doctl/how-to/install/
# 2. Authenticate: doctl auth init
# 3. Have your SSH key added to DO: doctl compute ssh-key list
#
# Usage: ./deploy_to_digitalocean.sh
# ========================================

set -e  # Exit on error

# ========================================
# CONFIGURATION
# ========================================
DROPLET_NAME="consensus-api-prod"
REGION="nyc3"  # New York 3 (change as needed: nyc1, sfo3, ams3, etc.)
SIZE="s-4vcpu-8gb-amd"  # Premium AMD 8GB/4vCPU ($48/mo)
IMAGE="ubuntu-22-04-x64"  # Ubuntu 22.04 LTS
SSH_KEY_NAME="your-ssh-key"  # Replace with your SSH key name from DO
DOMAIN="api.consensus.ai"  # Your domain (optional)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========================================
# FUNCTIONS
# ========================================
print_status() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# ========================================
# PRE-FLIGHT CHECKS
# ========================================
print_status "Starting ConsensusNet deployment to Digital Ocean..."

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    print_error "doctl CLI not found. Please install it first: https://docs.digitalocean.com/reference/doctl/how-to/install/"
fi

# Check if authenticated
if ! doctl auth list &> /dev/null; then
    print_error "Not authenticated with Digital Ocean. Run: doctl auth init"
fi

# Get SSH key fingerprint
print_status "Getting SSH key fingerprint..."
SSH_KEY_ID=$(doctl compute ssh-key list --format ID,Name --no-header | grep "$SSH_KEY_NAME" | awk '{print $1}')

if [ -z "$SSH_KEY_ID" ]; then
    print_error "SSH key '$SSH_KEY_NAME' not found. Available keys:"
    doctl compute ssh-key list
    exit 1
fi

# ========================================
# CREATE DROPLET
# ========================================
print_status "Creating Droplet '$DROPLET_NAME'..."

# Check if droplet already exists
if doctl compute droplet list --format Name --no-header | grep -q "^$DROPLET_NAME$"; then
    print_warning "Droplet '$DROPLET_NAME' already exists. Skipping creation."
    DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep "^$DROPLET_NAME" | awk '{print $2}')
else
    # Create the droplet
    doctl compute droplet create "$DROPLET_NAME" \
        --region "$REGION" \
        --size "$SIZE" \
        --image "$IMAGE" \
        --ssh-keys "$SSH_KEY_ID" \
        --enable-monitoring \
        --enable-backups \
        --wait

    print_status "Droplet created successfully!"
    
    # Get droplet IP
    DROPLET_IP=$(doctl compute droplet list --format Name,PublicIPv4 --no-header | grep "^$DROPLET_NAME" | awk '{print $2}')
fi

print_status "Droplet IP: $DROPLET_IP"

# ========================================
# CREATE VOLUME FOR DATABASE
# ========================================
print_status "Creating volume for database..."

VOLUME_NAME="${DROPLET_NAME}-data"
if doctl compute volume list --format Name --no-header | grep -q "^$VOLUME_NAME$"; then
    print_warning "Volume '$VOLUME_NAME' already exists. Skipping creation."
else
    doctl compute volume create "$VOLUME_NAME" \
        --region "$REGION" \
        --size 50GiB \
        --desc "PostgreSQL data for ConsensusNet"
    
    # Attach volume to droplet
    DROPLET_ID=$(doctl compute droplet list --format Name,ID --no-header | grep "^$DROPLET_NAME" | awk '{print $2}')
    VOLUME_ID=$(doctl compute volume list --format Name,ID --no-header | grep "^$VOLUME_NAME" | awk '{print $2}')
    
    doctl compute volume-action attach "$VOLUME_ID" "$DROPLET_ID" --wait
fi

# ========================================
# WAIT FOR SSH
# ========================================
print_status "Waiting for SSH to be ready..."
sleep 30  # Initial wait

while ! ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 root@"$DROPLET_IP" "echo 'SSH ready'" &> /dev/null; do
    echo -n "."
    sleep 5
done
echo ""

# ========================================
# CONFIGURE DROPLET
# ========================================
print_status "Configuring Droplet..."

# Create setup script
cat > /tmp/consensus_setup.sh << 'EOF'
#!/bin/bash
set -e

echo "Starting ConsensusNet server setup..."

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    docker.io \
    docker-compose \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    htop \
    ufw \
    fail2ban

# Enable Docker
systemctl enable docker
systemctl start docker

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow http
ufw allow https
# Allow Grafana (restrict to specific IPs in production)
ufw allow 3000/tcp comment 'Grafana'
# Allow Prometheus (restrict to specific IPs in production)
ufw allow 9090/tcp comment 'Prometheus'
ufw --force enable

# Setup swap (4GB)
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Mount volume for PostgreSQL data
if [ -b /dev/sda ]; then
    mkdir -p /mnt/consensus-data
    if ! grep -q "/dev/sda" /etc/fstab; then
        mkfs.ext4 /dev/sda
        echo '/dev/sda /mnt/consensus-data ext4 defaults,nofail,discard 0 2' >> /etc/fstab
        mount -a
    fi
fi

# Create application user
if ! id -u consensus >/dev/null 2>&1; then
    useradd -m -s /bin/bash consensus
    usermod -aG docker consensus
fi

# Clone repository (replace with your repo URL)
if [ ! -d /home/consensus/app ]; then
    git clone https://github.com/your-org/ConsensusNet.git /home/consensus/app
    chown -R consensus:consensus /home/consensus/app
fi

# Create directories
mkdir -p /home/consensus/app/logs
mkdir -p /home/consensus/app/data
chown -R consensus:consensus /home/consensus/app

echo "Server setup completed!"
EOF

# Copy and run setup script
scp -o StrictHostKeyChecking=no /tmp/consensus_setup.sh root@"$DROPLET_IP":/tmp/
ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" "bash /tmp/consensus_setup.sh"

# ========================================
# DEPLOY APPLICATION
# ========================================
print_status "Deploying ConsensusNet application..."

# Create production docker-compose file
cat > /tmp/docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  api:
    image: ghcr.io/your-org/consensusnet/api:latest
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://consensus_user:${DB_PASSWORD}@postgres:5432/consensus_prod
      - REDIS_URL=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8000"
      - "prometheus.io/path=/metrics"

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=consensus_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=consensus_prod
    volumes:
      - /mnt/consensus-data/postgres:/var/lib/postgresql/data
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # Monitoring Stack
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./monitoring/alerts:/etc/prometheus/alerts:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    ports:
      - "127.0.0.1:9090:9090"
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=redis-datasource
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards:ro
    ports:
      - "127.0.0.1:3000:3000"
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  node-exporter:
    image: prom/node-exporter:latest
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "127.0.0.1:9100:9100"
    restart: unless-stopped

  redis-exporter:
    image: oliver006/redis_exporter:latest
    environment:
      - REDIS_ADDR=redis://redis:6379
    ports:
      - "127.0.0.1:9121:9121"
    restart: unless-stopped

  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    environment:
      - DATA_SOURCE_NAME=postgresql://consensus_user:${DB_PASSWORD}@postgres:5432/consensus_prod?sslmode=disable
    ports:
      - "127.0.0.1:9187:9187"
    restart: unless-stopped

volumes:
  redis_data:
  prometheus_data:
  grafana_data:
EOF

# Create .env file
cat > /tmp/.env.prod << EOF
# Generated on $(date)
ENVIRONMENT=production
DB_PASSWORD=$(openssl rand -base64 32)
SECRET_KEY=$(openssl rand -hex 32)
GRAFANA_PASSWORD=$(openssl rand -base64 16)
EOF

# Copy files to server
scp -o StrictHostKeyChecking=no /tmp/docker-compose.prod.yml root@"$DROPLET_IP":/home/consensus/app/docker-compose.prod.yml
scp -o StrictHostKeyChecking=no /tmp/.env.prod root@"$DROPLET_IP":/home/consensus/app/.env

# ========================================
# CONFIGURE NGINX
# ========================================
print_status "Configuring Nginx..."

cat > /tmp/nginx_consensus.conf << EOF
server {
    listen 80;
    server_name $DROPLET_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

# Deploy Nginx config
scp -o StrictHostKeyChecking=no /tmp/nginx_consensus.conf root@"$DROPLET_IP":/etc/nginx/sites-available/consensus
ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" << 'ENDSSH'
ln -sf /etc/nginx/sites-available/consensus /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx
ENDSSH

# ========================================
# START APPLICATION
# ========================================
print_status "Starting ConsensusNet application..."

ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" << 'ENDSSH'
cd /home/consensus/app
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
ENDSSH

# ========================================
# SETUP SYSTEMD SERVICE
# ========================================
print_status "Creating systemd service..."

cat > /tmp/consensus-api.service << EOF
[Unit]
Description=ConsensusNet API
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/consensus/app
ExecStart=/usr/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
ExecReload=/usr/bin/docker-compose -f docker-compose.prod.yml pull && /usr/bin/docker-compose -f docker-compose.prod.yml up -d

[Install]
WantedBy=multi-user.target
EOF

scp -o StrictHostKeyChecking=no /tmp/consensus-api.service root@"$DROPLET_IP":/etc/systemd/system/
ssh -o StrictHostKeyChecking=no root@"$DROPLET_IP" << 'ENDSSH'
systemctl daemon-reload
systemctl enable consensus-api
ENDSSH

# ========================================
# FINAL CHECKS
# ========================================
print_status "Running final checks..."

# Wait for services to start
sleep 10

# Check if API is responding
if curl -s -o /dev/null -w "%{http_code}" "http://$DROPLET_IP/api/health" | grep -q "200"; then
    print_status "✅ API is responding!"
else
    print_warning "API is not responding yet. Check logs with: ssh root@$DROPLET_IP 'docker-compose -f /home/consensus/app/docker-compose.prod.yml logs'"
fi

# ========================================
# SUMMARY
# ========================================
echo ""
echo "========================================="
echo -e "${GREEN}DEPLOYMENT COMPLETED!${NC}"
echo "========================================="
echo "Droplet Name: $DROPLET_NAME"
echo "IP Address: $DROPLET_IP"
echo "API URL: http://$DROPLET_IP"
echo "API Health: http://$DROPLET_IP/api/health"
echo "API Docs: http://$DROPLET_IP/api/docs"
echo "Prometheus: http://$DROPLET_IP:9090"
echo "Grafana: http://$DROPLET_IP:3000 (admin/check .env file)"
echo ""
echo "SSH Access: ssh root@$DROPLET_IP"
echo ""
echo "Next steps:"
echo "1. Update your DNS to point to $DROPLET_IP"
echo "2. Run certbot for SSL: ssh root@$DROPLET_IP 'certbot --nginx -d $DOMAIN'"
echo "3. Update GitHub secrets for CI/CD:"
echo "   - DO_HOST=$DROPLET_IP"
echo "   - DO_USER=root"
echo "   - DO_SSH_KEY=<your-private-key>"
echo ""
echo "Monitoring:"
echo "- Check logs: ssh root@$DROPLET_IP 'docker-compose -f /home/consensus/app/docker-compose.prod.yml logs -f'"
echo "- System stats: ssh root@$DROPLET_IP 'htop'"
echo "- API metrics: curl http://$DROPLET_IP/api/v1/production/metrics"
echo "========================================="

# Cleanup temp files
rm -f /tmp/consensus_setup.sh /tmp/docker-compose.prod.yml /tmp/.env.prod /tmp/nginx_consensus.conf /tmp/consensus-api.service