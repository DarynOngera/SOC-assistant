# Mininet Topology - Network Map Integration Guide

## ✅ Integration Complete

Your Mininet topology is now fully integrated with the SOC Dashboard Network Map!

## 🎯 What Was Implemented

### 1. **Topology Exporter** (`topology/topology_exporter.py`)
- Exports Mininet network structure to JSON
- Includes 10 hosts, 3 switches, network segments
- Provides service and port information
- **File Generated**: `data_capture/mininet_topology.json` (5.9KB)

### 2. **Backend API** (`src/dashboard/server.py`)
- **New Endpoint**: `GET /api/network/mininet-topology`
- Loads topology from JSON file
- Enriches with real-time MongoDB alert data
- Maps alerts to hosts by IP address
- Returns comprehensive topology with security metrics

### 3. **Frontend Network Map** (`frontend/src/components/NetworkMap.jsx`)
- **Toggle Views**: Switch between "Mininet" and "Alerts" modes
- **Mininet Visualization**:
  - All 10 hosts with proper positioning
  - 3 switches (yellow squares)
  - Network segments with color-coded boundaries
  - Trunk and access links
  - Real-time alert indicators (pulsing red dots)
  - Interactive node selection
  - Detailed host information panel

## 🗺️ Your Network Topology

### Server Segment (10.0.1.0/24) - Green
- **h1**: Web Server (10.0.1.1) - HTTP/HTTPS ports 80, 443
- **h2**: FTP Server (10.0.1.2) - FTP port 21
- **h3**: DNS Server (10.0.1.3) - DNS port 53

### Client Segment (10.0.2.0/24) - Blue
- **h4**: Client 1 (10.0.2.1)
- **h5**: Client 2 (10.0.2.2)
- **h6**: Client 3 (10.0.2.3)
- **h7**: Client 4 (10.0.2.4)

### Internal Segment (10.0.3.0/24) - Purple
- **h8**: Database Server (10.0.3.1) - MySQL port 3306
- **h9**: File Server (10.0.3.2) - SMB/NFS ports 445, 2049
- **h10**: Mail Server (10.0.3.3) - SMTP/IMAP ports 25, 143

### Network Infrastructure
- **s1**: Server Switch (connects server segment)
- **s2**: Client Switch (connects client segment)
- **s3**: Internal Switch (connects internal segment)
- **Inter-switch links**: 1Gbps trunk connections

## 🚀 How to Use

### Step 1: Generate Topology (Already Done ✅)
```bash
cd mininet_data_generation/topology
python3 topology_exporter.py
```

### Step 2: Start Backend Server
```bash
cd /home/ongera/projects/SOC-assistant
python src/dashboard/server.py
```

### Step 3: Start Frontend (Already Running)
```bash
cd frontend
npm start
```

### Step 4: View Network Map
1. Open browser: `http://localhost:3000`
2. Login to dashboard
3. Navigate to **Network Map** section
4. Use toggle buttons:
   - **Mininet**: Your actual Mininet topology
   - **Alerts**: Alert-based topology view

## 🎨 Visualization Features

### Interactive Elements
- **Click hosts/switches**: View detailed information
- **Hover**: Highlight effect
- **Color coding**:
  - Green = Servers (segment color)
  - Blue = Clients (segment color)
  - Purple = Internal servers (segment color)
  - Orange = Hosts with alerts
  - Red = Hosts with critical alerts
  - Yellow = Switches
- **Alert indicators**: Pulsing red dots on affected hosts
- **Auto-refresh**: Updates every 30 seconds

### Node Details Panel
When you click a host, you'll see:
- Hostname and IP address
- Host type (server/client)
- Network segment
- Services running
- Open ports
- Alert count
- Severity distribution
- Attack types detected

## 📊 Real-Time Integration

The topology is enriched with live security data:

```
Mininet Topology (Static)
         +
MongoDB Alerts (Dynamic)
         ↓
Enriched Visualization
```

- Alert counts mapped to each host by IP
- Severity distribution calculated
- Attack types identified
- Visual indicators updated in real-time

## 🔧 API Endpoint Details

### GET /api/network/mininet-topology

**Authentication**: Required (JWT Bearer token)

**Authorization**: Analyst or Admin role

**Response** (when available):
```json
{
  "available": true,
  "metadata": {
    "name": "SOC Training Network",
    "description": "Mininet-based network topology",
    "created_at": "2025-10-12T00:11:00",
    "version": "1.0"
  },
  "hosts": [
    {
      "id": "h1",
      "name": "Web Server",
      "ip": "10.0.1.1",
      "subnet": "10.0.1.0/24",
      "type": "server",
      "services": ["HTTP", "HTTPS"],
      "ports": [80, 443],
      "segment": "servers",
      "position": {"x": 400, "y": 100},
      "alert_count": 5,
      "severity_counts": {"critical": 1, "high": 2, "medium": 2, "low": 0},
      "attack_types": ["Port Scan", "SQL Injection"]
    }
  ],
  "switches": [...],
  "links": [...],
  "segments": [...]
}
```

**Response** (when not available):
```json
{
  "available": false,
  "message": "Mininet topology not yet generated. Run topology_exporter.py first."
}
```

## 📝 Files Modified/Created

### Created
- ✅ `mininet_data_generation/topology/topology_exporter.py`
- ✅ `mininet_data_generation/data_capture/mininet_topology.json`
- ✅ `mininet_data_generation/NETWORK_MAP_INTEGRATION.md` (this file)

### Modified
- ✅ `src/dashboard/server.py` - Added `/api/network/mininet-topology` endpoint
- ✅ `frontend/src/components/NetworkMap.jsx` - Added Mininet visualization

## 🎯 Next Steps

### 1. View Your Topology
- Navigate to Network Map in the dashboard
- Click "Mininet" button to see your topology
- Click on hosts to see details

### 2. Generate Traffic & Alerts
```bash
cd mininet_data_generation
sudo python3 topology/generate_normal_traffic.py
sudo python3 topology/generate_attack_traffic.py
```

### 3. Watch Real-Time Updates
- Alerts will automatically appear on the topology
- Hosts with alerts show pulsing red indicators
- Alert counts update every 30 seconds

### 4. Customize Topology (Optional)
Edit `topology/topology_exporter.py` to:
- Add more hosts
- Change network segments
- Modify positioning
- Add custom metadata

Then re-run: `python3 topology_exporter.py`

## 🔍 Troubleshooting

### Topology Not Showing?
1. Check if file exists:
   ```bash
   ls -lh mininet_data_generation/data_capture/mininet_topology.json
   ```
2. Verify backend server is running
3. Check browser console for errors
4. Ensure you're logged in with analyst/admin role

### No Alerts on Topology?
- Alerts are mapped by IP address
- Generate traffic to create alerts
- Check MongoDB has alerts: `db.alerts.count()`
- Verify IP addresses match (10.0.x.x range)

### Frontend Not Updating?
- Check browser console for API errors
- Verify JWT token is valid
- Refresh the page
- Clear browser cache

## 📚 Additional Resources

- **Mininet Documentation**: See `FINAL_STATUS.md`
- **Network Map API**: See `docs2/NETWORK_MAP_DOCUMENTATION.md`
- **Dashboard Setup**: See main `README.md`

## ✨ Features Summary

✅ **Static topology visualization** - Your Mininet network structure  
✅ **Dynamic alert overlay** - Real-time security events  
✅ **Interactive exploration** - Click to view details  
✅ **Dual view modes** - Switch between Mininet and Alerts  
✅ **Auto-refresh** - Updates every 30 seconds  
✅ **Color-coded segments** - Easy network identification  
✅ **Service information** - Know what's running where  
✅ **Alert correlation** - See which hosts are under attack  

---

**Status**: ✅ Fully Integrated and Operational  
**Last Updated**: 2025-10-12  
**Version**: 1.0
