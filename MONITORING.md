# 📊 SOC Assistant Monitoring Infrastructure

Complete guide to the production-grade monitoring and observability stack for SOC Assistant.

---

## 🎯 Overview

The SOC Assistant includes a comprehensive monitoring infrastructure built on **Prometheus** and **Grafana**, providing real-time visibility into application performance, security events, ML model behavior, and system health.

### **Components**
- **Prometheus**: Time-series metrics collection and storage
- **Grafana**: Visualization and dashboards
- **Flask Metrics Exporter**: Application-level metrics
- **Health Check System**: Readiness and liveness probes

---

## 📈 Metrics Collected

### **1. HTTP Request Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `http_requests_total` | Counter | Total HTTP requests received | `method`, `endpoint`, `status` |
| `http_request_duration_seconds` | Histogram | Request processing latency | `method`, `endpoint` |

**Use Cases:**
- Monitor API endpoint performance
- Identify slow endpoints
- Track error rates by endpoint
- Analyze traffic patterns

---

### **2. Security Alert Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `alerts_generated_total` | Counter | Total security alerts generated | `severity`, `attack_type` |
| `alerts_active` | Gauge | Currently active alerts | `severity` |

**Use Cases:**
- Track alert generation rate
- Monitor alert severity distribution
- Identify attack type trends
- Alert on alert spikes (meta-alerting)

**Attack Types Tracked:**
- DDoS
- Port Scan
- Web Attack
- Privilege Escalation
- Advanced Persistent Threat (APT)
- Malware
- Data Exfiltration

**Severity Levels:**
- `critical`
- `high`
- `medium`
- `low`

---

### **3. Machine Learning Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `ml_predictions_total` | Counter | Total ML predictions made | `model_type`, `prediction` |
| `ml_prediction_latency_seconds` | Histogram | ML inference latency | `model_type` |
| `ml_model_accuracy` | Gauge | Current model accuracy | `model_type` |

**Use Cases:**
- Monitor model performance in production
- Track prediction latency
- Detect model degradation
- Compare model versions

**Model Types:**
- `mininet_classifier`: Network traffic classification
- `anomaly_detector`: Anomaly detection
- `threat_classifier`: Threat type classification

---

### **4. NLP Analysis Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `nlp_analyses_total` | Counter | Total NLP analyses performed | None |
| `nlp_confidence_score` | Histogram | NLP confidence score distribution | None |

**Use Cases:**
- Monitor NLP processing volume
- Track confidence score distribution
- Identify low-confidence predictions

---

### **5. Database Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `db_operations_total` | Counter | Total database operations | `operation`, `collection`, `status` |
| `db_operation_duration_seconds` | Histogram | Database operation latency | `operation`, `collection` |
| `db_connections_active` | Gauge | Active database connections | None |

**Use Cases:**
- Monitor database performance
- Identify slow queries
- Track connection pool usage
- Detect database bottlenecks

**Operations Tracked:**
- `insert`
- `update`
- `delete`
- `find`
- `aggregate`

**Collections:**
- `alerts`
- `users`
- `audit_logs`
- `system_stats`

---

### **6. WebSocket Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `websocket_connections_active` | Gauge | Active WebSocket connections | None |
| `websocket_messages_total` | Counter | Total WebSocket messages | `event_type`, `direction` |

**Use Cases:**
- Monitor real-time connection health
- Track message throughput
- Identify connection issues

**Event Types:**
- `alert`
- `stats_update`
- `notification`
- `heartbeat`

---

### **7. System Resource Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `system_cpu_usage_percent` | Gauge | CPU usage percentage | None |
| `system_memory_usage_percent` | Gauge | Memory usage percentage | None |
| `system_disk_usage_percent` | Gauge | Disk usage percentage | None |

**Use Cases:**
- Monitor system resource utilization
- Capacity planning
- Detect resource exhaustion
- Performance optimization

---

### **8. Authentication Metrics**

| Metric | Type | Description | Labels |
|--------|------|-------------|--------|
| `auth_attempts_total` | Counter | Authentication attempts | `status`, `method` |
| `active_sessions` | Gauge | Currently active user sessions | None |

**Use Cases:**
- Monitor authentication success/failure rates
- Detect brute force attacks
- Track active user sessions
- Security auditing

**Status:**
- `success`
- `failure`
- `expired`

**Methods:**
- `jwt`
- `session`
- `api_key`

---

### **9. Python Runtime Metrics**

Automatically collected by `prometheus_flask_exporter`:

| Metric | Description |
|--------|-------------|
| `python_gc_objects_collected_total` | Objects collected during garbage collection |
| `python_gc_collections_total` | Number of GC collections |
| `python_info` | Python version and implementation |
| `process_virtual_memory_bytes` | Virtual memory usage |
| `process_resident_memory_bytes` | Resident memory usage |
| `process_cpu_seconds_total` | CPU time consumed |
| `process_open_fds` | Number of open file descriptors |

---

## 🏥 Health Check Endpoints

### **1. Overall Health Check**
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-24T01:30:00.000000",
  "uptime_seconds": 3600,
  "checks": {
    "database": "healthy",
    "ml_model": "healthy",
    "disk_space": "healthy"
  }
}
```

### **2. Readiness Probe**
```bash
GET /health/ready
```

Checks if the application is ready to serve traffic:
- Database connectivity
- ML models loaded
- Required services available

### **3. Liveness Probe**
```bash
GET /health/live
```

Checks if the application is alive and responsive.

---

## 📊 Grafana Dashboards

### **SOC Assistant Dashboard**

The main dashboard (`soc-assistant-dashboard.json`) includes 17 panels:

#### **Performance Panels**
1. **HTTP Request Rate** - Requests per second
2. **HTTP Request Latency** - P50, P95, P99 percentiles
3. **HTTP Error Rate** - 4xx and 5xx errors

#### **Security Panels**
4. **Alert Generation Rate** - Alerts per minute
5. **Active Alerts by Severity** - Critical, High, Medium, Low
6. **Attack Type Distribution** - Pie chart of attack types
7. **Alert Timeline** - Time series of alerts

#### **ML Model Panels**
8. **ML Predictions Rate** - Predictions per second
9. **ML Prediction Latency** - Inference time
10. **Model Accuracy** - Current accuracy gauge

#### **NLP Panels**
11. **NLP Analysis Rate** - Analyses per minute
12. **NLP Confidence Distribution** - Histogram

#### **Database Panels**
13. **Database Operations Rate** - Operations per second
14. **Database Latency** - Query execution time
15. **Active DB Connections** - Connection pool usage

#### **System Panels**
16. **System Resources** - CPU, Memory, Disk usage
17. **WebSocket Connections** - Active connections

---

## 🚀 Quick Start

### **1. Start Monitoring Stack**

```bash
cd infrastructure
docker-compose up -d
```

**Services Started:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- Node Exporter: http://localhost:9100

### **2. Start SOC Assistant**

```bash
python src/dashboard/server.py
```

**Metrics Endpoint:** http://localhost:5000/metrics

### **3. Access Grafana**

1. Open http://localhost:3001
2. Login: `admin` / `admin`
3. Go to **Dashboards** → **SOC Assistant**

---

## 🔧 Configuration

### **Prometheus Configuration**

Location: `infrastructure/prometheus/prometheus.yml`

```yaml
scrape_configs:
  - job_name: 'soc_assistant_backend'
    static_configs:
      - targets: ['192.168.100.9:5000']  # Your host IP
    metrics_path: '/metrics'
    scrape_interval: 10s
```

**Key Settings:**
- `scrape_interval`: How often to collect metrics (default: 10s)
- `scrape_timeout`: Maximum time for scrape (default: 5s)
- `evaluation_interval`: How often to evaluate rules (default: 15s)

### **Alert Rules**

Location: `infrastructure/prometheus/alerts.yml`

**Configured Alerts:**
1. High Error Rate (>5% for 5 minutes)
2. High Response Time (>2s P95 for 5 minutes)
3. Alert Volume Spike (>100 alerts/min)
4. Database Slow Queries (>1s P95)
5. High CPU Usage (>80% for 5 minutes)
6. High Memory Usage (>85% for 5 minutes)
7. Low Disk Space (<10%)
8. ML Model Degradation (<80% accuracy)
9. Authentication Failures (>10/min)
10. WebSocket Connection Issues

---

## 📝 Usage Examples

### **Query Prometheus Metrics**

```bash
# Get current alert count
curl http://localhost:5000/metrics | grep alerts_generated_total

# Get HTTP request rate
curl http://localhost:5000/metrics | grep http_requests_total

# Get ML prediction latency
curl http://localhost:5000/metrics | grep ml_prediction_latency
```

### **PromQL Queries**

```promql
# Request rate per endpoint
rate(http_requests_total[5m])

# Error rate percentage
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Alerts by severity
sum by (severity) (alerts_active)

# ML prediction throughput
rate(ml_predictions_total[1m])

# Database operation latency P99
histogram_quantile(0.99, rate(db_operation_duration_seconds_bucket[5m]))
```

---

## 🔍 Troubleshooting

### **Prometheus Can't Scrape Metrics**

**Problem:** `connection refused` error

**Solution:**
1. Check if server is running: `curl http://localhost:5000/health`
2. Verify metrics endpoint: `curl http://localhost:5000/metrics`
3. Update Prometheus config with correct IP (not `localhost` from Docker)
4. Restart Prometheus: `docker-compose restart prometheus`

### **No Data in Grafana**

**Problem:** Panels show "No Data"

**Solution:**
1. Check Prometheus targets: http://localhost:9090/targets
2. Verify data source in Grafana: Configuration → Data Sources
3. Test Prometheus connection in Grafana
4. Generate some traffic to create metrics

### **Metrics Endpoint Returns 404**

**Problem:** `/metrics` not found

**Solution:**
1. Verify monitoring is enabled in server logs
2. Check if `prometheus_flask_exporter` is installed
3. Restart the server
4. Check for import errors in logs

---

## 🎯 Best Practices

### **1. Metric Naming**
- Use descriptive names: `http_requests_total` not `requests`
- Include units: `_seconds`, `_bytes`, `_percent`
- Follow Prometheus conventions

### **2. Label Usage**
- Keep cardinality low (avoid unique IDs as labels)
- Use consistent label names across metrics
- Don't use labels for high-cardinality data

### **3. Dashboard Design**
- Group related metrics together
- Use appropriate visualization types
- Set meaningful time ranges
- Add descriptions to panels

### **4. Alerting**
- Alert on symptoms, not causes
- Set appropriate thresholds
- Avoid alert fatigue
- Include actionable information

### **5. Performance**
- Monitor metric collection overhead
- Use appropriate scrape intervals
- Implement metric sampling for high-volume data
- Archive old metrics

---

## 📚 Additional Resources

### **Documentation**
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)

### **Project Files**
- `src/infrastructure/monitoring.py` - Metrics implementation
- `infrastructure/prometheus/prometheus.yml` - Prometheus config
- `infrastructure/prometheus/alerts.yml` - Alert rules
- `infrastructure/grafana/dashboards/` - Dashboard definitions

---

## 🔐 Security Considerations

1. **Metrics Endpoint**: Currently unauthenticated (standard for Prometheus)
2. **Grafana Access**: Change default admin password
3. **Network Security**: Restrict Prometheus/Grafana ports in production
4. **Sensitive Data**: Don't include PII or secrets in metric labels
5. **RBAC**: Configure Grafana user roles appropriately

---

## 📊 Performance Impact

**Metrics Collection Overhead:**
- CPU: <1% additional usage
- Memory: ~50MB for metrics storage
- Network: ~10KB/s for scraping
- Disk: Minimal (metrics stored in memory)

**Recommended Resources:**
- Prometheus: 2GB RAM, 20GB disk
- Grafana: 512MB RAM, 10GB disk
- SOC Assistant: +100MB RAM for metrics

---

## 🎓 Academic Value

This monitoring infrastructure demonstrates:

1. **Production-Ready Observability**: Industry-standard tools and practices
2. **Security Metrics**: Specialized metrics for SOC operations
3. **ML Monitoring**: Model performance tracking in production
4. **Real-Time Analytics**: Sub-second metric collection and visualization
5. **Scalability**: Designed for high-volume environments

**Research Applications:**
- Performance analysis of ML models in production
- Security event correlation and analysis
- System behavior under attack scenarios
- Resource utilization optimization

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs prometheus grafana`
2. Review Prometheus targets: http://localhost:9090/targets
3. Test metrics endpoint: `curl http://localhost:5000/metrics`
4. Verify health checks: `curl http://localhost:5000/health`

---

**Last Updated:** November 24, 2025  
**Version:** 1.0.0  
**Maintainer:** SOC Assistant Team
