# Dashboard Simulation - Quick Start

## 🚀 Start System

```bash
# Terminal 1: Backend
cd src/dashboard && python3 server.py

# Terminal 2: Frontend  
cd frontend && npm start

# Browser: http://localhost:3000
```

## 📍 Location

**Dashboard → Top Row → 3rd Card (Admin Only)**

```
[Threshold Control] [Score Distribution] [🧠 Simulation Control]
```

## ⚡ Quick Test

### Normal Traffic (30 seconds)
1. Login as admin
2. Dashboard → See simulation control
3. Mode: **Normal Traffic**
4. Click **Start**
5. Watch: 0-10 alerts, Health stays green

### Attack Traffic (30 seconds)
1. Mode: **Attack**
2. Attack Type: **SYN Flood**
3. Click **Start**
4. Watch: 50-200 alerts, Health turns red

## 📊 What Updates

- ✅ Status Cards (top)
- ✅ Attack Distribution (middle)
- ✅ Alerts Table (bottom)
- ✅ System Health color

## 🎯 Expected Results

| Mode | Alerts | Health | Time |
|------|--------|--------|------|
| Normal | 0-10 | 🟢 Healthy | 5-10s |
| Attack | 50-200 | 🔴 Critical | 5-10s |

## 📖 Full Guides

- **Integration**: `INTEGRATED_SIMULATION_GUIDE.md`
- **Complete**: `INTEGRATION_COMPLETE.md`
- **Testing**: `PCAP_REPLAY_TESTING_GUIDE.md`

---

**Everything in one view! 🎉**
