# MongoDB Alignment Guide

## 🎯 Problem

The system needs MongoDB to be aligned with the new trained model:
- Old alerts from previous simulations
- Old system stats
- Need fresh start for accurate testing

## ✅ Solution

### Quick Reset (Recommended)

```bash
# Run the automated reset script
python3 reset_mongodb.py

# Follow prompts to clear old data
```

### Manual Reset

```bash
# Connect to MongoDB
mongo

# Switch to database
use soc_dashboard

# Clear alerts
db.alerts.deleteMany({})

# Clear system stats
db.system_stats.deleteMany({})

# Initialize fresh stats
db.system_stats.insertOne({
    timestamp: new Date(),
    total_processed: 0,
    anomalies_detected: 0,
    total_alerts: 0,
    active_alerts: 0,
    system_health: 'healthy',
    threshold: 0.7,
    severity_distribution: {
        critical: 0,
        high: 0,
        medium: 0,
        low: 0
    },
    detection_rate: 0.0,
    stats_type: 'realtime'
})

# Exit
exit
```

## 🚀 Complete System Startup

### Option 1: Automated (Easiest)

```bash
# Run the startup script
./start_system.sh

# It will:
# 1. Check MongoDB is running
# 2. Verify model files exist
# 3. Check PCAP files
# 4. Optionally reset MongoDB
# 5. Check backend status
# 6. Show next steps
```

### Option 2: Manual Steps

```bash
# 1. Start MongoDB
sudo systemctl start mongodb

# 2. Reset MongoDB
python3 reset_mongodb.py

# 3. Start Backend (Terminal 1)
cd src/dashboard
python3 server.py

# Look for: "✅ Mininet trained model loaded successfully (95.25% accuracy)"

# 4. Start Frontend (Terminal 2)
cd frontend
npm start

# 5. Test in Browser
# → http://localhost:3000
# → Login as admin
# → Dashboard → Simulation Control
```

## 🧪 Verification Steps

### 1. Check MongoDB is Clean

```bash
mongo
use soc_dashboard
db.alerts.count()  # Should be 0
db.system_stats.count()  # Should be 1
exit
```

### 2. Check Model Loaded

```bash
# Backend logs should show:
Loading Mininet trained models from: models
✅ Mininet trained model loaded successfully (95.25% accuracy)
Models loaded successfully
```

### 3. Test Normal Traffic

```bash
# In Dashboard:
# 1. Simulation Control → Mode: Normal
# 2. Click Start
# 3. Watch logs:
#    - "Extracted X flow records"
#    - "Generated 0-10 alerts" (few alerts)
#    - "No anomalies detected - normal traffic pattern"
# 4. Score Distribution: Green bars (left side)
```

### 4. Test Attack Traffic

```bash
# In Dashboard:
# 1. Simulation Control → Mode: Attack, Type: SYN Flood
# 2. Click Start
# 3. Watch logs:
#    - "Extracted X flow records"
#    - "Generated 50-200 alerts" (many alerts)
#    - "Attack Types Detected: {'syn_flood': X}"
# 4. Score Distribution: Red bars (right side)
```

## 📊 MongoDB Collections

### alerts
```javascript
{
    _id: ObjectId,
    alert_id: String,
    timestamp: Date,
    source_ip: String,
    destination_ip: String,
    source_port: Number,
    destination_port: Number,
    protocol: String,
    attack_type: String,
    severity: String,  // 'critical', 'high', 'medium', 'low'
    anomaly_score: Number,  // 0.0 - 1.0
    status: String,  // 'new', 'investigating', 'resolved'
    created_by: String,
    tags: Array,
    confidence: Number,
    simulation_source: Boolean,
    description: String
}
```

### system_stats
```javascript
{
    _id: ObjectId,
    timestamp: Date,
    total_processed: Number,
    anomalies_detected: Number,
    total_alerts: Number,
    active_alerts: Number,
    system_health: String,  // 'healthy', 'warning', 'critical'
    threshold: Number,
    severity_distribution: {
        critical: Number,
        high: Number,
        medium: Number,
        low: Number
    },
    detection_rate: Number,
    stats_type: String  // 'realtime'
}
```

## 🔍 Troubleshooting

### MongoDB Not Starting

```bash
# Check status
sudo systemctl status mongodb

# Check logs
sudo journalctl -u mongodb -n 50

# Restart
sudo systemctl restart mongodb
```

### Can't Connect to MongoDB

```bash
# Check if running
ps aux | grep mongo

# Check port
netstat -an | grep 27017

# Try connecting
mongo --host localhost --port 27017
```

### Old Data Still Showing

```bash
# Force clear everything
mongo
use soc_dashboard
db.alerts.drop()
db.system_stats.drop()
db.createCollection("alerts")
db.createCollection("system_stats")
exit

# Restart backend
```

### Score Distribution Not Updating

```bash
# 1. Clear browser cache
# 2. Hard refresh (Ctrl+Shift+R)
# 3. Check browser console for errors
# 4. Verify WebSocket connection (green dot in sidebar)
# 5. Check backend logs for "Broadcasted X alerts"
```

## 📝 What Gets Reset

### ✅ Cleared (Reset)
- All alerts (old simulation data)
- System statistics
- Score distribution data

### ❌ Preserved (Kept)
- User accounts
- Audit logs
- User preferences
- Authentication settings

## 🎯 Expected Results After Reset

### Dashboard (Before Simulation)
- Total Processed: 0
- Anomalies Detected: 0
- Total Alerts: 0
- System Health: Healthy
- Score Distribution: Empty

### After Normal Traffic Simulation
- Total Alerts: 0-10
- System Health: Healthy
- Score Distribution: Green bars (0.0-0.3)
- Summary: High "Normal Traffic" count

### After Attack Simulation
- Total Alerts: 50-200
- System Health: Critical
- Score Distribution: Red bars (0.8-1.0)
- Summary: High "Confirmed Attack" count

## 🔄 Regular Maintenance

### Daily
- No action needed (system auto-manages)

### Weekly
- Review audit logs
- Check disk space for MongoDB

### Monthly
- Backup MongoDB data
- Archive old alerts
- Review system performance

### Before Demos
```bash
# Clean slate for demonstrations
python3 reset_mongodb.py
# Restart backend
# Test one simulation to verify
```

## 📞 Quick Commands

```bash
# Check MongoDB status
sudo systemctl status mongodb

# Reset database
python3 reset_mongodb.py

# Start system
./start_system.sh

# Check model files
ls -lh models/mininet_*.pkl

# Check PCAP files
ls mininet_data_generation/data_capture/pcaps/*.pcap | wc -l

# View backend logs
cd src/dashboard && python3 server.py

# Kill backend
pkill -f "python3 server.py"
```

---

**MongoDB is now aligned with the new trained model system! 🎉**
