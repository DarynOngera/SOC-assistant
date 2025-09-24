# Network Map Documentation

## Overview

The Network Map feature provides interactive network topology visualization for SOC analysts, enabling real-time monitoring of network traffic patterns, threat sources, and security incidents across your infrastructure.

## Features

### 🗺️ Interactive Network Visualization
- **Node-based topology**: Visual representation of IP addresses as nodes
- **Connection mapping**: Edges showing traffic flows between IPs
- **Real-time updates**: Live data refresh every 30 seconds
- **Interactive exploration**: Click nodes for detailed information

### 🎯 Network Classification
- **IP Type Detection**:
  - Internal (192.168.x.x, 10.x.x.x, 172.16-31.x.x)
  - External (Public IP addresses)
  - Localhost (127.x.x.x)
- **Subnet Grouping**: Automatic subnet detection and visualization
- **Visual Coding**: Color-coded nodes by network type

### 📊 Security Analytics
- **Threat Correlation**: Links network activity with security alerts
- **Attack Pattern Analysis**: Visualizes attack sources and targets
- **Severity Mapping**: Node sizing based on alert frequency
- **Port Analysis**: Tracks active ports per IP address

### 🔍 Advanced Filtering
- **Node Type Filters**: View all, internal, external, or high-risk nodes
- **Time-based Analysis**: 1 hour, 24 hours, or 7-day timeframes
- **Subnet Toggle**: Show/hide subnet boundaries
- **Connection Analysis**: Filter by connection frequency and severity

## API Endpoints

### GET /api/network/topology
Returns comprehensive network topology data.

**Response Structure:**
```json
{
  "nodes": [
    {
      "id": "192.168.1.100",
      "ip": "192.168.1.100",
      "subnet": "192.168.1.0/24",
      "type": "internal",
      "alert_count": 5,
      "severity_counts": {
        "critical": 1,
        "high": 2,
        "medium": 2,
        "low": 0
      },
      "attack_types": ["Brute Force", "Port Scan"],
      "ports": [22, 80, 443]
    }
  ],
  "edges": [
    {
      "id": "192.168.1.100->10.0.0.50",
      "source": "192.168.1.100",
      "target": "10.0.0.50",
      "weight": 3,
      "alerts": [
        {
          "timestamp": "2025-01-07T13:30:00Z",
          "severity": "high",
          "attack_type": "Brute Force",
          "score": 0.85
        }
      ]
    }
  ],
  "subnets": [
    {
      "subnet": "192.168.1.0/24",
      "ip_count": 15,
      "alert_count": 25,
      "ips": ["192.168.1.100", "192.168.1.101"]
    }
  ],
  "stats": {
    "total_nodes": 50,
    "total_edges": 75,
    "total_subnets": 5
  }
}
```

### GET /api/network/connections?timeframe={1h|24h|7d}
Returns active network connections analysis.

**Parameters:**
- `timeframe`: Time window for analysis (1h, 24h, 7d)

**Response Structure:**
```json
{
  "connections": [
    {
      "source_ip": "192.168.1.100",
      "destination_ip": "10.0.0.50",
      "source_port": 54321,
      "destination_port": 22,
      "connection_count": 15,
      "total_score": 12.5,
      "max_score": 0.95,
      "avg_score": 0.83,
      "attack_types": ["Brute Force"],
      "severities": ["high", "medium"],
      "first_seen": "2025-01-07T12:00:00Z",
      "last_seen": "2025-01-07T13:30:00Z"
    }
  ],
  "timeframe": "1h",
  "total_connections": 150
}
```

## User Interface Components

### Main Visualization
- **SVG-based Network Graph**: Scalable vector graphics for crisp visualization
- **Force-directed Layout**: Automatic node positioning with physics simulation
- **Zoom and Pan**: Interactive navigation of large networks
- **Node Interactions**: Click for details, hover for quick info

### Control Panel
- **Filter Controls**: Dropdown menus for node type and timeframe selection
- **Subnet Toggle**: Checkbox to show/hide subnet boundaries
- **Refresh Button**: Manual data refresh trigger
- **Legend**: Visual guide for node colors and indicators

### Information Panels
- **Network Statistics**: Overview cards showing key metrics
- **Node Details**: Comprehensive information for selected nodes
- **Top Connections**: List of most active network connections
- **Threat Indicators**: Real-time security alerts and warnings

## Network Analysis Capabilities

### Threat Detection
- **Anomaly Visualization**: Highlights suspicious network patterns
- **Attack Source Identification**: Pinpoints external threat actors
- **Lateral Movement Tracking**: Visualizes internal network propagation
- **Command & Control Detection**: Identifies C2 communications

### Network Intelligence
- **Traffic Flow Analysis**: Understands normal vs. abnormal patterns
- **Port Usage Mapping**: Tracks service utilization across the network
- **Subnet Security Assessment**: Evaluates security posture by network segment
- **Connection Frequency Analysis**: Identifies high-volume communications

### Incident Response Support
- **Visual Threat Correlation**: Links related security events
- **Network Forensics**: Historical analysis of network activities
- **Impact Assessment**: Visualizes affected network segments
- **Containment Planning**: Identifies isolation points and critical paths

## Configuration and Customization

### Display Settings
```javascript
// Customize node appearance
const nodeConfig = {
  minSize: 8,        // Minimum node radius
  maxSize: 20,       // Maximum node radius
  colors: {
    internal: '#3b82f6',  // Blue for internal IPs
    external: '#ef4444',  // Red for external IPs
    localhost: '#10b981'  // Green for localhost
  }
};

// Customize edge appearance
const edgeConfig = {
  minWidth: 1,       // Minimum edge width
  maxWidth: 4,       // Maximum edge width
  opacity: 0.6,      // Edge transparency
  alertThreshold: 5  // Threshold for red edges
};
```

### Performance Tuning
- **Node Limit**: Maximum 500 nodes for optimal performance
- **Edge Limit**: Maximum 1000 edges for smooth rendering
- **Refresh Rate**: Configurable update interval (default: 30 seconds)
- **Data Retention**: Configurable time window for historical analysis

## Security Considerations

### Access Control
- **Role-based Access**: Requires analyst or admin privileges
- **JWT Authentication**: Secure API access with token validation
- **Audit Logging**: All network map access is logged for security

### Data Privacy
- **IP Anonymization**: Option to mask sensitive IP addresses
- **Subnet Filtering**: Ability to exclude sensitive network segments
- **Export Controls**: Restricted data export capabilities

## Troubleshooting

### Common Issues

**No Network Data Displayed**
- Verify alerts are being generated in the system
- Check MongoDB connection and alert collection
- Ensure proper authentication and permissions

**Performance Issues**
- Reduce timeframe scope (use 1h instead of 7d)
- Apply node type filters to limit data volume
- Check server resources and MongoDB performance

**Visualization Problems**
- Clear browser cache and reload
- Check browser console for JavaScript errors
- Verify SVG rendering support in browser

### Debug Commands
```bash
# Test network topology endpoint
curl -H "Authorization: Bearer $TOKEN" \
     http://localhost:5000/api/network/topology

# Test network connections endpoint
curl -H "Authorization: Bearer $TOKEN" \
     "http://localhost:5000/api/network/connections?timeframe=1h"

# Check MongoDB alerts collection
python -c "
from src.database.mongodb_dal import get_dal
dal = get_dal()
alerts = list(dal.get_alerts(limit=10))
print(f'Found {len(alerts)} alerts')
"
```

## Integration Examples

### Custom Dashboard Integration
```javascript
// Fetch network data
const fetchNetworkData = async () => {
  const response = await fetch('/api/network/topology', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};

// Process for custom visualization
const processNetworkData = (data) => {
  const highRiskNodes = data.nodes.filter(n => n.alert_count > 10);
  const externalThreats = data.nodes.filter(n => n.type === 'external');
  return { highRiskNodes, externalThreats };
};
```

### Automated Alerting
```python
# Monitor for high-risk network patterns
def check_network_threats():
    response = requests.get(
        'http://localhost:5000/api/network/topology',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code == 200:
        data = response.json()
        
        # Alert on external IPs with high activity
        for node in data['nodes']:
            if node['type'] == 'external' and node['alert_count'] > 5:
                send_alert(f"High activity from external IP: {node['ip']}")
```

## Best Practices

### Network Monitoring
1. **Regular Review**: Check network map daily for new patterns
2. **Baseline Establishment**: Understand normal network topology
3. **Anomaly Investigation**: Investigate unexpected connections
4. **Trend Analysis**: Monitor changes in network patterns over time

### Security Operations
1. **Threat Hunting**: Use network map for proactive threat detection
2. **Incident Response**: Leverage visualization during security incidents
3. **Forensic Analysis**: Analyze historical network patterns
4. **Risk Assessment**: Evaluate network security posture regularly

### Performance Optimization
1. **Filter Usage**: Apply appropriate filters to manage data volume
2. **Timeframe Selection**: Use shorter timeframes for real-time analysis
3. **Regular Cleanup**: Archive old network data to maintain performance
4. **Resource Monitoring**: Monitor server resources during peak usage

## Future Enhancements

### Planned Features
- **3D Network Visualization**: Enhanced spatial representation
- **Machine Learning Integration**: Automated pattern recognition
- **Threat Intelligence Feeds**: External threat data correlation
- **Custom Alerting Rules**: User-defined network monitoring rules
- **Export Capabilities**: Network diagram export in various formats
- **Historical Playback**: Time-based network activity replay

### API Expansions
- **Real-time Streaming**: WebSocket-based live updates
- **Bulk Data Export**: Large dataset export capabilities
- **Custom Queries**: Advanced filtering and search options
- **Integration APIs**: Third-party security tool integration
