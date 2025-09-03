# SOC Dashboard API Documentation

## Overview

The SOC Dashboard API provides real-time anomaly detection capabilities with WebSocket support for live updates. The backend is built with Flask and Flask-SocketIO.

**Base URL:** `http://localhost:5000`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## REST API Endpoints

### 1. Get Alerts

**Endpoint:** `GET /api/alerts`

**Description:** Retrieve alerts with filtering and pagination support.

**Query Parameters:**
- `page` (integer, optional): Page number (default: 1)
- `per_page` (integer, optional): Items per page (default: 20)
- `severity` (string, optional): Filter by severity (`critical`, `high`, `medium`, `low`)
- `status` (string, optional): Filter by status (`new`, `flagged`, `dismissed`)

**Response:**
```json
{
  "alerts": [
    {
      "id": 1,
      "timestamp": "2025-09-01T12:45:30.123456",
      "severity": "high",
      "source_ip": "192.168.1.100",
      "destination_ip": "10.0.1.50",
      "attack_type": "DDoS",
      "anomaly_score": 0.85,
      "confidence": 0.92,
      "status": "new",
      "flagged": false,
      "dismissed": false,
      "protocol": "TCP",
      "src_port": 45123,
      "dst_port": 80
    }
  ],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "total_pages": 8
}
```

**Example:**
```bash
curl "http://localhost:5000/api/alerts?severity=high&page=1&per_page=10"
```

### 2. Get System Statistics

**Endpoint:** `GET /api/stats`

**Description:** Retrieve current system statistics and metrics.

**Response:**
```json
{
  "total_processed": 15420,
  "anomalies_detected": 23,
  "total_alerts": 156,
  "active_alerts": 12,
  "system_health": "healthy",
  "threshold": 0.5,
  "severity_distribution": {
    "critical": 2,
    "high": 5,
    "medium": 8,
    "low": 8
  },
  "detection_rate": 1.49
}
```

**Example:**
```bash
curl "http://localhost:5000/api/stats"
```

### 3. Get/Update Detection Threshold

**Endpoint:** `GET /api/threshold`

**Description:** Get current detection threshold.

**Response:**
```json
{
  "threshold": 0.5
}
```

**Endpoint:** `POST /api/threshold`

**Description:** Update detection threshold.

**Request Body:**
```json
{
  "threshold": 0.7
}
```

**Response:**
```json
{
  "success": true,
  "threshold": 0.7
}
```

**Error Response:**
```json
{
  "error": "Threshold must be between 0.0 and 1.0"
}
```

**Example:**
```bash
# Get threshold
curl "http://localhost:5000/api/threshold"

# Update threshold
curl -X POST "http://localhost:5000/api/threshold" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 0.7}'
```

### 4. Flag Alert

**Endpoint:** `POST /api/alerts/{alert_id}/flag`

**Description:** Flag a specific alert for investigation.

**Path Parameters:**
- `alert_id` (integer): The ID of the alert to flag

**Response:**
```json
{
  "success": true
}
```

**Error Response:**
```json
{
  "error": "Alert not found"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/alerts/123/flag"
```

### 5. Dismiss Alert

**Endpoint:** `POST /api/alerts/{alert_id}/dismiss`

**Description:** Dismiss a specific alert.

**Path Parameters:**
- `alert_id` (integer): The ID of the alert to dismiss

**Response:**
```json
{
  "success": true
}
```

**Error Response:**
```json
{
  "error": "Alert not found"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/alerts/123/dismiss"
```

### 6. Start Monitoring

**Endpoint:** `POST /api/monitoring/start`

**Description:** Start real-time anomaly detection monitoring.

**Response:**
```json
{
  "success": true,
  "status": "monitoring_started"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/monitoring/start"
```

### 7. Stop Monitoring

**Endpoint:** `POST /api/monitoring/stop`

**Description:** Stop real-time anomaly detection monitoring.

**Response:**
```json
{
  "success": true,
  "status": "monitoring_stopped"
}
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/monitoring/stop"
```

### 8. Get Score Distribution

**Endpoint:** `GET /api/score-distribution`

**Description:** Get anomaly score distribution data for visualization.

**Response:**
```json
{
  "bins": [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95],
  "counts": [45, 32, 28, 15, 12, 8, 5, 3, 2, 1],
  "total_samples": 151
}
```

**Example:**
```bash
curl "http://localhost:5000/api/score-distribution"
```

## WebSocket Events

The API supports real-time communication via WebSocket connections.

**Connection URL:** `ws://localhost:5000`

### Client Events (Sent to Server)

#### 1. Connect
**Event:** `connect`
**Description:** Establish WebSocket connection.

#### 2. Request Alerts
**Event:** `request_alerts`
**Description:** Request current alerts data.

**Example:**
```javascript
socket.emit('request_alerts');
```

#### 3. Disconnect
**Event:** `disconnect`
**Description:** Close WebSocket connection.

### Server Events (Received from Server)

#### 1. Connection Established
**Event:** `connection_established`
**Data:**
```json
{
  "status": "connected"
}
```

#### 2. New Alerts
**Event:** `new_alerts`
**Description:** Sent when new alerts are detected.
**Data:**
```json
{
  "alerts": [
    {
      "id": 157,
      "timestamp": "2025-09-01T12:45:30.123456",
      "severity": "high",
      "source_ip": "192.168.1.100",
      "destination_ip": "10.0.1.50",
      "attack_type": "Port Scan",
      "anomaly_score": 0.78,
      "confidence": 0.89,
      "status": "new",
      "flagged": false,
      "dismissed": false,
      "protocol": "TCP",
      "src_port": 45123,
      "dst_port": 22
    }
  ],
  "stats": {
    "total_processed": 15421,
    "anomalies_detected": 24,
    "active_alerts": 13
  }
}
```

#### 3. Statistics Update
**Event:** `stats_update`
**Description:** Periodic system statistics updates.
**Data:**
```json
{
  "total_processed": 15421,
  "anomalies_detected": 24,
  "total_alerts": 157,
  "active_alerts": 13,
  "system_health": "healthy",
  "threshold": 0.5,
  "severity_distribution": {
    "critical": 2,
    "high": 6,
    "medium": 8,
    "low": 8
  },
  "detection_rate": 1.51
}
```

#### 4. Alerts Update
**Event:** `alerts_update`
**Description:** Full alerts list update.
**Data:**
```json
{
  "alerts": [...],
  "stats": {...}
}
```

## Data Models

### Alert Object
```json
{
  "id": "integer - Unique alert identifier",
  "timestamp": "string - ISO format timestamp",
  "severity": "string - critical|high|medium|low",
  "source_ip": "string - Source IP address",
  "destination_ip": "string - Destination IP address", 
  "attack_type": "string - Type of detected attack",
  "anomaly_score": "float - Anomaly score (0.0-1.0)",
  "confidence": "float - Model confidence (0.0-1.0)",
  "status": "string - new|flagged|dismissed",
  "flagged": "boolean - Whether alert is flagged",
  "dismissed": "boolean - Whether alert is dismissed",
  "protocol": "string - Network protocol (TCP|UDP|ICMP)",
  "src_port": "integer - Source port number",
  "dst_port": "integer - Destination port number"
}
```

### Statistics Object
```json
{
  "total_processed": "integer - Total packets processed",
  "anomalies_detected": "integer - Recent anomalies detected",
  "total_alerts": "integer - Total alerts in history",
  "active_alerts": "integer - Current active alerts",
  "system_health": "string - healthy|warning|error",
  "threshold": "float - Current detection threshold",
  "severity_distribution": {
    "critical": "integer",
    "high": "integer", 
    "medium": "integer",
    "low": "integer"
  },
  "detection_rate": "float - Percentage of anomalies detected"
}
```

## Error Handling

### HTTP Status Codes
- `200 OK` - Successful request
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format
```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "details": "Additional error details (optional)"
}
```

## Rate Limiting

Currently, no rate limiting is implemented. In production, consider implementing rate limiting for:
- Alert flagging/dismissing: 100 requests/minute
- Threshold updates: 10 requests/minute
- General API calls: 1000 requests/minute

## WebSocket Client Example

### JavaScript/React Example
```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000');

// Connection events
socket.on('connect', () => {
  console.log('Connected to SOC Dashboard');
});

socket.on('connection_established', (data) => {
  console.log('Connection established:', data);
});

// Data events
socket.on('new_alerts', (data) => {
  console.log('New alerts received:', data.alerts);
  updateAlertsUI(data.alerts);
  updateStatsUI(data.stats);
});

socket.on('stats_update', (data) => {
  console.log('Stats updated:', data);
  updateStatsUI(data);
});

// Request initial data
socket.emit('request_alerts');
```

### Python Client Example
```python
import socketio

sio = socketio.Client()

@sio.event
def connect():
    print('Connected to SOC Dashboard')
    sio.emit('request_alerts')

@sio.event
def new_alerts(data):
    print(f"New alerts: {len(data['alerts'])}")
    for alert in data['alerts']:
        print(f"Alert {alert['id']}: {alert['attack_type']} from {alert['source_ip']}")

@sio.event
def stats_update(data):
    print(f"Stats - Processed: {data['total_processed']}, Active Alerts: {data['active_alerts']}")

sio.connect('http://localhost:5000')
sio.wait()
```

## Integration Examples

### Fetch Alerts with Filtering
```javascript
async function fetchHighSeverityAlerts() {
  const response = await fetch('http://localhost:5000/api/alerts?severity=high&status=new');
  const data = await response.json();
  return data.alerts;
}
```

### Update Threshold
```javascript
async function updateDetectionThreshold(newThreshold) {
  const response = await fetch('http://localhost:5000/api/threshold', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ threshold: newThreshold }),
  });
  return response.json();
}
```

### Flag Multiple Alerts
```javascript
async function flagAlerts(alertIds) {
  const promises = alertIds.map(id => 
    fetch(`http://localhost:5000/api/alerts/${id}/flag`, { method: 'POST' })
  );
  return Promise.all(promises);
}
```

## Deployment Considerations

### Environment Variables
```bash
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=https://yourdomain.com
```

### Security Headers
In production, implement:
- CORS restrictions
- Rate limiting
- Authentication/Authorization
- HTTPS only
- Input validation and sanitization

### Monitoring
Monitor these metrics:
- API response times
- WebSocket connection count
- Alert processing rate
- Memory and CPU usage
- Error rates

## Changelog

### Version 1.0.0
- Initial API implementation
- Real-time WebSocket support
- Alert management endpoints
- System statistics
- Score distribution visualization
- Threshold adjustment capabilities
