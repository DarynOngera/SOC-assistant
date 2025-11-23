# Quick Commands Reference

## 🚀 Start System

```bash
# Automated startup (checks everything)
./start_system.sh

# Manual startup
python3 reset_mongodb.py  # Optional: reset database
cd src/dashboard && python3 server.py  # Terminal 1
cd frontend && npm start  # Terminal 2
```

## 🔄 Reset & Clean

```bash
# Reset MongoDB only
python3 reset_mongodb.py

# Kill backend
pkill -f "python3 server.py"

# Kill frontend
pkill -f "npm start"
```

## 🧪 Verify System

```bash
# Check MongoDB
sudo systemctl status mongodb
mongo --eval "db.version()"

# Check model files
ls -lh models/mininet_*.pkl | head -3

# Check PCAP files
ls mininet_data_generation/data_capture/pcaps/*.pcap | wc -l

# Test model loading
python3 -c "import joblib; print('✅ Model OK' if joblib.load('models/mininet_model.pkl') else '❌ Error')"
```

## 📊 MongoDB Commands

```bash
# Connect
mongo

# Use database
use soc_dashboard

# Count alerts
db.alerts.count()

# Clear alerts
db.alerts.deleteMany({})

# View recent alerts
db.alerts.find().sort({timestamp:-1}).limit(5).pretty()

# Exit
exit
```

## 🎯 Test Simulations

```bash
# Browser: http://localhost:3000
# 1. Login as admin
# 2. Dashboard → Simulation Control

# Test normal traffic
# Mode: Normal → Start
# Expected: 0-10 alerts, green bars

# Test attack traffic
# Mode: Attack, Type: SYN Flood → Start
# Expected: 50-200 alerts, red bars
```

## 🔍 Debug

```bash
# Backend logs
cd src/dashboard && python3 server.py

# Check for:
# "✅ Mininet trained model loaded successfully (95.25% accuracy)"

# MongoDB logs
sudo journalctl -u mongodb -n 50

# Check ports
netstat -an | grep 5000  # Backend
netstat -an | grep 3000  # Frontend
netstat -an | grep 27017 # MongoDB
```

## 📁 Important Paths

```bash
# Models
models/mininet_model.pkl
models/mininet_scaler.pkl
models/mininet_feature_columns.pkl

# PCAPs
mininet_data_generation/data_capture/pcaps/

# Backend
src/dashboard/server.py

# Frontend
frontend/src/components/SimulationControl.jsx
frontend/src/components/ScoreDistribution.js
```

## 🛠️ Regenerate Data

```bash
# Generate new PCAPs
python3 generate_varied_pcaps.py

# Retrain model
python3 train_comprehensive_model.py

# Reset database
python3 reset_mongodb.py
```

---

**Quick Reference - Keep this handy! 📌**
