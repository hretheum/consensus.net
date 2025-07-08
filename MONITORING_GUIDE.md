# 📊 ConsensusNet Monitoring Guide

## Overview

ConsensusNet includes a comprehensive monitoring stack based on Prometheus and Grafana, providing real-time insights into system performance, health, and behavior.

## 🚀 Quick Start

### Local Development

```bash
# Start all services with monitoring
docker-compose -f docker-compose.monitoring.yml up -d

# Access services:
# - API: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000 (admin/admin)
```

### Production Deployment

Monitoring is automatically deployed with the main application using the deployment script:

```bash
./deploy_to_digitalocean.sh
```

## 📈 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  ConsensusNet   │────▶│   Prometheus    │────▶│    Grafana      │
│      API        │     │                 │     │                 │
│   /metrics      │     │  Time Series    │     │  Dashboards     │
└─────────────────┘     │    Database     │     │    Alerts       │
                        └─────────────────┘     └─────────────────┘
                                ▲
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐     ┌───────▼────────┐     ┌───────▼────────┐
│ Node Exporter  │     │ Redis Exporter │     │  PG Exporter   │
│ System Metrics │     │ Cache Metrics  │     │  DB Metrics    │
└────────────────┘     └────────────────┘     └────────────────┘
```

## 📊 Metrics Collected

### API Metrics
- **Request Rate**: `consensusnet_api_requests_total`
- **Response Time**: `consensusnet_api_request_duration_seconds`
- **Error Rate**: `consensusnet_api_errors_total`
- **Average Response Time**: `consensusnet_api_response_time_seconds`

### System Metrics
- **CPU Usage**: `consensusnet_cpu_usage_percent`
- **Memory Usage**: `consensusnet_memory_usage_percent`
- **Disk Usage**: `consensusnet_disk_usage_percent`
- **Network I/O**: Via node_exporter

### Application Metrics
- **Queue Size**: `consensusnet_queue_size`
- **Jobs Processed**: `consensusnet_jobs_processed_total`
- **Cache Hit Rate**: `consensusnet_cache_hit_rate`
- **Active DB Connections**: `consensusnet_db_connections_active`

### Agent Metrics
- **Available Agents**: `consensusnet_agents_available`
- **Agent Tasks**: `consensusnet_agent_tasks_total`
- **Processing Time**: `consensusnet_agent_processing_time_seconds`

### Consensus Metrics
- **Consensus Rounds**: `consensusnet_consensus_rounds_total`
- **Confidence Scores**: `consensusnet_consensus_confidence`
- **Debate Rounds**: `consensusnet_debate_rounds_total`

## 🎯 Grafana Dashboards

### ConsensusNet Overview Dashboard
Main dashboard showing:
- System resource utilization
- API performance metrics
- Health status indicators
- Cache and queue statistics
- Agent availability
- Circuit breaker states

### Accessing Dashboards
1. Navigate to Grafana: http://your-server:3000
2. Login with credentials (default: admin/admin)
3. Go to Dashboards → ConsensusNet Overview

### Creating Custom Dashboards
1. Click "+" → "Create Dashboard"
2. Add panels using PromQL queries
3. Save dashboard with appropriate tags

## 🚨 Alerts

### Pre-configured Alerts

#### Critical Alerts
- **API Down**: API unavailable for >2 minutes
- **Database Down**: PostgreSQL unavailable
- **Redis Down**: Cache server unavailable
- **Disk Space Low**: <5GB remaining
- **No Agents Available**: Agent pool empty

#### Warning Alerts
- **High CPU Usage**: >80% for 5 minutes
- **High Memory Usage**: >85% for 5 minutes
- **High API Response Time**: >5s for 5 minutes
- **High Error Rate**: >10% for 5 minutes
- **Low Cache Hit Rate**: <50% for 15 minutes

### Alert Configuration
Alerts are defined in `monitoring/alerts/consensusnet.yml`

To add new alerts:
```yaml
- alert: YourAlertName
  expr: your_prometheus_query > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Alert summary"
    description: "Detailed description"
```

## 📡 Prometheus Queries

### Useful PromQL Examples

**API Request Rate (per second)**
```promql
rate(consensusnet_api_requests_total[5m])
```

**P95 Response Time**
```promql
histogram_quantile(0.95, sum(rate(consensusnet_api_request_duration_seconds_bucket[5m])) by (le))
```

**Error Rate Percentage**
```promql
rate(consensusnet_api_errors_total[5m]) / rate(consensusnet_api_requests_total[5m]) * 100
```

**Available Memory**
```promql
consensusnet_memory_available_bytes / 1024 / 1024 / 1024
```

**Cache Hit Rate Trend**
```promql
avg_over_time(consensusnet_cache_hit_rate[1h])
```

## 🔧 Configuration

### Prometheus Configuration
Located at `monitoring/prometheus.yml`

Key settings:
- Scrape interval: 15s
- Evaluation interval: 15s
- Retention: 15 days (default)

### Grafana Configuration
- Data source: Auto-provisioned
- Dashboards: Auto-imported from `monitoring/grafana/dashboards/`
- Plugins: redis-datasource (auto-installed)

### Exporters Configuration
Each exporter has specific environment variables:
- Redis Exporter: `REDIS_ADDR`
- PostgreSQL Exporter: `DATA_SOURCE_NAME`
- Node Exporter: Various mount points

## 🛠️ Troubleshooting

### Metrics Not Appearing
1. Check if API is exposing metrics:
   ```bash
   curl http://localhost:8000/metrics
   ```

2. Verify Prometheus targets:
   - Go to Prometheus UI → Status → Targets
   - All targets should be "UP"

3. Check container logs:
   ```bash
   docker-compose logs prometheus
   docker-compose logs grafana
   ```

### High Resource Usage
1. Check Prometheus retention:
   ```bash
   du -sh prometheus_data/
   ```

2. Reduce retention if needed:
   ```yaml
   command:
     - '--storage.tsdb.retention.time=7d'
   ```

3. Optimize queries in dashboards

### Connection Issues
1. Verify network connectivity:
   ```bash
   docker network ls
   docker network inspect consensusnet
   ```

2. Check firewall rules:
   ```bash
   ufw status
   ```

## 📈 Best Practices

### Metric Naming
- Use consistent prefixes: `consensusnet_`
- Follow Prometheus conventions
- Include units in metric names

### Dashboard Design
- Group related metrics
- Use appropriate visualizations
- Set meaningful thresholds
- Include documentation

### Alert Management
- Start with few critical alerts
- Tune thresholds based on baseline
- Include runbooks in descriptions
- Test alerts regularly

### Performance
- Limit cardinality of labels
- Use recording rules for complex queries
- Archive old data to object storage
- Monitor Prometheus resource usage

## 🔐 Security

### Production Recommendations
1. **Restrict Access**:
   ```nginx
   location /metrics {
       allow 10.0.0.0/8;  # Internal only
       deny all;
   }
   ```

2. **Enable Authentication**:
   - Grafana: Change default password
   - Prometheus: Use reverse proxy with auth

3. **Use HTTPS**:
   - Configure SSL certificates
   - Update scrape configs to use HTTPS

4. **Firewall Rules**:
   - Limit Prometheus/Grafana to specific IPs
   - Use VPN for remote access

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Tutorial](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/)