# Integrated PCAP Simulation Guide
## Dashboard-Integrated Network Traffic Simulation

## 🎯 Overview

The PCAP replay simulation is now **fully integrated into the main Dashboard** for seamless testing and visualization. No separate page needed!

### Key Features
- ✅ **Integrated Controls**: Simulation controls embedded in dashboard
- ✅ **Real-time Visualization**: See alerts appear in graphs immediately
- ✅ **Admin-Only Access**: Simulation control visible only to admins
- ✅ **Compact Design**: Efficient use of dashboard space
- ✅ **Live Progress**: WebSocket-based progress updates

---

## 📍 Location

The simulation control is located in the **Dashboard view** (main page):

```
Dashboard (Top Row)
├── Threshold Control
├── Score Distribution  
└── PCAP Replay Simulation ← HERE (Admin only)
```

---

## 🚀 Quick Start

### 1. Login as Admin
```
Username: admin
Password: your_admin_password
```

### 2. View Dashboard
- You'll see the simulation control in the top row (3rd card)
- It shows:
  - Current status (Running/Stopped)
  - Mode selector (Normal/Attack)
  - Attack type dropdown (if attack mode)
  - Start/Stop buttons
  - ML model performance metrics
  - Real-time progress bar

### 3. Run Normal Traffic
1. Select **Mode**: `Normal Traffic`
2. Click **Start**
3. Watch:
   - Progress bar: 0% → 20% → 40% → 60% → 80% → 100%
   - Status Cards update (few alerts)
   - Attack Distribution graph updates
   - Alerts Table shows 0-10 new alerts
   - System Health stays "Healthy" (green)

### 4. Run Attack Traffic
1. Select **Mode**: `Attack`
2. Select **Attack Type**: `SYN Flood` (or any other)
3. Click **Start**
4. Watch:
   - Progress bar with ML brain icon
   - Status Cards spike (many alerts)
   - Attack Distribution shows attack type
   - Alerts Table fills with 50-200 alerts
   - System Health turns "Critical" (red)

---

## 🎨 UI Components

### Simulation Control Card

```
┌─────────────────────────────────────────┐
│ 🧠 PCAP Replay Simulation    ● Running │
├─────────────────────────────────────────┤
│ Progress Bar: ████████░░ 80%            │
│ 🧠 Processing PCAP data...              │
├─────────────────────────────────────────┤
│ Mode: [Normal ▼]  Attack: [SYN Flood ▼]│
├─────────────────────────────────────────┤
│ [▶ Start]  or  [■ Stop]                 │
├─────────────────────────────────────────┤
│ ✓ ML Model: Random Forest               │
│ Accuracy  Precision  Recall  F1         │
│  95.25%    98.84%    95.53%  97.16%     │
├─────────────────────────────────────────┤
│ ℹ PCAP Replay: Processes real network   │
│   traffic through trained ML model.     │
└─────────────────────────────────────────┘
```

---

## 📊 Dashboard Integration

### What Updates in Real-Time

1. **Status Cards** (Top of Dashboard)
   - Total Processed: Increases
   - Anomalies Detected: Increases (attacks)
   - Total Alerts: Increases
   - Active Alerts: Increases
   - System Health: Changes color

2. **Attack Distribution** (Middle Section)
   - New attack types appear
   - Bar chart updates
   - Percentages recalculate

3. **Alerts Table** (Bottom Section)
   - New rows appear
   - Severity indicators
   - Timestamps
   - Source/Destination IPs

4. **Score Distribution** (Top Row)
   - Histogram updates
   - Shows anomaly score distribution

---

## 🔄 Workflow Example

### Normal Traffic Test

```
1. Dashboard loads → All metrics at baseline
2. Click "Start" (Normal mode)
3. Progress: 20% → 40% → 60% → 80% → 100%
4. Observe:
   ├── Status Cards: +0-10 alerts
   ├── System Health: Healthy (green)
   ├── Attack Distribution: Minimal change
   └── Alerts Table: 0-10 new rows
5. Simulation completes → "Completed!" message
6. Dashboard shows stable state
```

### Attack Traffic Test

```
1. Dashboard at baseline
2. Select "Attack" mode → "SYN Flood"
3. Click "Start"
4. Progress: 20% → 40% → 60% → 80% → 100%
5. Observe:
   ├── Status Cards: +50-200 alerts
   ├── System Health: Critical (red)
   ├── Attack Distribution: SYN Flood spike
   └── Alerts Table: 50-200 new rows
6. Simulation completes
7. Dashboard shows attack state
```

---

## 🎯 Key Differences: Normal vs Attack

| Aspect | Normal Traffic | Attack Traffic |
|--------|---------------|----------------|
| **Alerts Generated** | 0-10 | 50-200 |
| **Status Cards** | Minimal change | Significant spike |
| **System Health** | 🟢 Healthy | 🔴 Critical |
| **Attack Distribution** | Flat | Spike in attack type |
| **Alerts Table** | Few rows | Many rows |
| **Anomaly Scores** | < 0.5 | > 0.7 |
| **Processing Time** | 5-10 seconds | 5-10 seconds |

---

## 🧠 ML Model Integration

### How It Works

1. **PCAP Selection**
   - Normal mode → `normal_traffic_v*.pcap`
   - Attack mode → `attack_{type}_*.pcap`

2. **Feature Extraction**
   - 24 network features per flow
   - ACK count, ports, packet sizes, etc.

3. **ML Prediction**
   - Random Forest model (95.25% accuracy)
   - Predicts: 0 (normal) or 1 (attack)

4. **Alert Generation**
   - Only flows with prediction = 1 generate alerts
   - Anomaly score threshold applied
   - Stored in MongoDB

5. **Dashboard Update**
   - WebSocket broadcasts new alerts
   - All components update in real-time
   - Graphs and charts refresh

---

## 📈 Monitoring the Simulation

### Progress Indicators

1. **Status Dot**
   - 🟢 Green (pulsing) = Running
   - ⚫ Gray = Stopped

2. **Progress Bar**
   - Gradient blue-to-purple
   - Shows percentage (0-100%)
   - Updates every second

3. **Progress Message**
   - "Starting PCAP replay..."
   - "Processing PCAP data... 40%"
   - "Completed!"

4. **Model Metrics**
   - Always visible at bottom
   - Shows trained model performance
   - Accuracy, Precision, Recall, F1

---

## 🎓 Testing Scenarios

### Scenario 1: Baseline Verification
**Goal**: Verify normal traffic doesn't trigger false alarms

1. Start with clean dashboard
2. Run normal traffic simulation
3. **Expected**: 0-10 alerts (6.32% false positive rate)
4. **Verify**: System health stays healthy

### Scenario 2: Attack Detection
**Goal**: Verify model detects attacks

1. Run SYN flood simulation
2. **Expected**: 50-200 alerts (95.53% detection rate)
3. **Verify**: System health turns critical
4. **Check**: Attack distribution shows SYN flood

### Scenario 3: Multiple Attack Types
**Goal**: Test different attack patterns

1. Run SYN flood → Observe results
2. Run port scan → Observe results
3. Run UDP flood → Observe results
4. **Compare**: Different alert patterns

### Scenario 4: Back-to-Back Tests
**Goal**: Verify system handles consecutive simulations

1. Run normal traffic
2. Wait for completion
3. Run attack traffic
4. **Verify**: Clear difference in results

---

## 🔧 Troubleshooting

### Simulation Doesn't Start

**Symptoms**: Click "Start" but nothing happens

**Solutions**:
1. Check browser console for errors
2. Verify WebSocket connection (green dot)
3. Ensure you're logged in as admin
4. Check backend logs for errors

### No Alerts Generated

**Symptoms**: Simulation completes but no alerts

**Solutions**:
1. Verify PCAP files exist in correct directory
2. Check model files are loaded (`models/mininet_*.pkl`)
3. Review backend logs for feature extraction errors
4. Ensure MongoDB is running

### Progress Bar Stuck

**Symptoms**: Progress bar doesn't move

**Solutions**:
1. Check WebSocket connection
2. Refresh browser page
3. Restart backend server
4. Check for JavaScript errors in console

---

## 💡 Tips & Best Practices

### For Testing

1. **Start Simple**: Test normal traffic first
2. **One at a Time**: Don't run multiple simulations simultaneously
3. **Wait for Completion**: Let each simulation finish
4. **Clear View**: Keep dashboard visible during simulation
5. **Check All Components**: Verify all dashboard sections update

### For Demonstrations

1. **Show Baseline**: Start with normal traffic
2. **Highlight Difference**: Then show attack traffic
3. **Point Out Metrics**: Reference the ML model performance
4. **Explain Real-time**: Show how graphs update live
5. **Compare Results**: Side-by-side normal vs attack

### For Development

1. **Monitor Logs**: Keep backend terminal visible
2. **Check WebSocket**: Verify events are firing
3. **Test Edge Cases**: Try stopping mid-simulation
4. **Verify Data**: Check MongoDB for stored alerts
5. **Review Reports**: Check `training_reports/` for model details

---

## 📝 Component Files

### Frontend
```
frontend/src/components/
├── SimulationControl.jsx  ← New integrated component
└── App.js                 ← Updated to include SimulationControl
```

### Backend
```
src/dashboard/
└── server.py              ← PCAP replay methods
```

### Models
```
models/
├── mininet_model.pkl
├── mininet_scaler.pkl
└── mininet_feature_columns.pkl
```

---

## 🎉 Advantages of Integration

### Before (Separate Page)
- ❌ Had to navigate away from dashboard
- ❌ Couldn't see real-time impact
- ❌ Needed to switch back to view results
- ❌ Disconnected experience

### After (Integrated)
- ✅ Everything in one view
- ✅ See real-time updates immediately
- ✅ No page switching needed
- ✅ Seamless workflow
- ✅ Better UX for testing and demos

---

## 🚀 Next Steps

1. **Test the Integration**
   ```bash
   cd frontend && npm start
   cd src/dashboard && python3 server.py
   ```

2. **Login as Admin**
   - Navigate to `http://localhost:3000`

3. **Run Simulations**
   - Try normal traffic
   - Try different attacks
   - Compare results

4. **Review Documentation**
   - `PCAP_REPLAY_TESTING_GUIDE.md` - Detailed testing
   - `IMPLEMENTATION_SUMMARY.md` - Technical details
   - `QUICK_REFERENCE.md` - Quick commands

---

**The simulation is now seamlessly integrated into your dashboard! 🎯**
