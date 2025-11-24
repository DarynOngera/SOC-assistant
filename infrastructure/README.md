# SOC Assistant Infrastructure

**Production Monitoring & Logging Stack**

This directory contains the infrastructure configuration for monitoring, logging, and observability.

---

## 📁 Directory Structure

```
infrastructure/
├── prometheus/
│   ├── prometheus.yml          # Prometheus configuration
│   └── alerts.yml              # Alert rules
├── grafana/
│   └── dashboards/
│       └── soc-assistant-dashboard.json  # Grafana dashboard
├── docker-compose.yml          # Docker Compose for monitoring stack
├── setup.sh                    # Automated setup script
└── README.md                   # This file
```

---

## 🚀 Quick Start

### Automated Setup (Recommended)

```bash
cd infrastructure
./setup.sh
```

This will:
1. Create logs directory
2. Install Python dependencies
3. Optionally start Docker monitoring stack
4. Configure Prometheus and Grafana

### Manual Setup

```bash
# 1. Install dependencies
pip install prometheus-client prometheus-flask-exporter python-json-logger psutil

# 2. Start monitoring stack (optional)
docker-compose up -d

# 3. Verify services
docker-compose ps
```

---

## 📊 Services

| Service | Port | Purpose | URL |
|---------|------|---------|-----|
| **Prometheus** | 9090 | Metrics collection | http://localhost:9090 |
| **Grafana** | 3001 | Dashboards | http://localhost:3001 |
| **Node Exporter** | 9100 | System metrics | http://localhost:9100 |
| **Application** | 5000 | Metrics endpoint | http://localhost:5000/metrics |

---

## 🎯 Features

### Monitoring
- ✅ HTTP request metrics
- ✅ Alert generation tracking
- ✅ ML model performance
- ✅ NLP analysis metrics
- ✅ Database operations
- ✅ WebSocket connections
- ✅ System resources (CPU, memory, disk)
- ✅ Authentication attempts

### Logging
- ✅ Structured JSON logs
- ✅ Log rotation (50MB files, 10 backups)
- ✅ Separate error logs
- ✅ Security audit logs
- ✅ Machine-parseable format

### Health Checks
- ✅ `/health` - Overall health
- ✅ `/health/ready` - Readiness probe
- ✅ `/health/live` - Liveness probe

### Alerting
- ✅ High error rate
- ✅ Slow response times
- ✅ Alert volume spikes
- ✅ Database issues
- ✅ High resource usage
- ✅ Failed authentication attempts

---

## 📈 Grafana Dashboard

Access: http://localhost:3001 (admin/admin)

**17 Panels:**
1. HTTP Request Rate
2. HTTP Response Time (95th percentile)
3. Alert Generation Rate
4. Active Alerts by Severity
5. ML Prediction Latency
6. ML Predictions per Second
7. NLP Analysis Rate
8. NLP Confidence Distribution
9. Database Operation Latency
10. Active Database Connections
11. WebSocket Connections
12. WebSocket Message Rate
13. System CPU Usage
14. System Memory Usage
15. System Disk Usage
16. Authentication Attempts
17. Active User Sessions

---

## 🔧 Configuration

### Prometheus

Edit `prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'soc_assistant_backend'
    static_configs:
      - targets: ['localhost:5000']
    scrape_interval: 10s
```

### Alerts

Edit `prometheus/alerts.yml` to customize alert thresholds.

### Grafana

1. Login: http://localhost:3001 (admin/admin)
2. Add Prometheus data source: http://prometheus:9090
3. Import dashboard from `grafana/dashboards/soc-assistant-dashboard.json`

---

## 🐳 Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Remove all data
docker-compose down -v
```

---

## 📊 Metrics Examples

### Query Prometheus

```promql
# Alert rate
rate(alerts_generated_total[5m])

# Response time (95th percentile)
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# CPU usage
system_cpu_usage_percent
```

### View Metrics Endpoint

```bash
curl http://localhost:5000/metrics
```

---

## 🏥 Health Checks

```bash
# Overall health
curl http://localhost:5000/health

# Readiness
curl http://localhost:5000/health/ready

# Liveness
curl http://localhost:5000/health/live
```

---

## 📝 Logs

Located in `../logs/`:

```bash
# View JSON logs
tail -f ../logs/soc_assistant.json.log | jq

# View text logs
tail -f ../logs/soc_assistant.log

# View error logs
tail -f ../logs/soc_assistant.error.log

# View security audit
tail -f ../logs/security_audit.log
```

---

## 🔍 Troubleshooting

### Prometheus Not Scraping

```bash
# Check targets
open http://localhost:9090/targets

# Verify metrics endpoint
curl http://localhost:5000/metrics

# Check Prometheus logs
docker logs soc-prometheus
```

### Grafana Dashboard Empty

```bash
# Check data source
curl http://localhost:3001/api/datasources

# Verify Prometheus connection
docker exec soc-grafana curl http://prometheus:9090/-/healthy

# Restart Grafana
docker-compose restart grafana
```

### High Disk Usage

```bash
# Check Prometheus data size
docker exec soc-prometheus du -sh /prometheus

# Reduce retention (edit prometheus.yml)
--storage.tsdb.retention.time=7d

# Restart Prometheus
docker-compose restart prometheus
```

---

## 🎯 Performance Impact

**Resource Usage:**
- Prometheus: ~200MB RAM, <5% CPU
- Grafana: ~100MB RAM, <2% CPU
- Node Exporter: ~20MB RAM, <1% CPU
- **Total**: ~320MB RAM, <8% CPU

**Application Overhead:**
- Metrics collection: <1ms per request
- Logging: <0.5ms per log
- **Total**: <2% performance impact

---

## 🚀 Production Deployment

### 1. Configure Environment

```bash
export ENVIRONMENT=production
export LOG_LEVEL=INFO
export METRICS_ENABLED=true
```

### 2. Start Monitoring Stack

```bash
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check all services
docker-compose ps

# Test metrics
curl http://localhost:5000/metrics

# Test health
curl http://localhost:5000/health
```

---

## 📚 Documentation

- [Full Infrastructure Guide](../INFRASTRUCTURE.md)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)

---

**Infrastructure is optional and does not affect existing functionality!**
