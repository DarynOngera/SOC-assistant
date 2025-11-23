# Live Score Distribution - Implementation Summary

## Overview
Implemented a real-time, live score distribution graph that shows anomaly scores **as they are generated** during simulation, instead of pulling historical data from MongoDB. This provides immediate visual feedback of the ML model's scoring behavior.

## Problem Solved
- **Before**: Score distribution graph showed historical data from MongoDB (all past alerts)
- **Issue**: Graph didn't update dynamically during simulation, making it hard to see live effects
- **After**: Graph switches to LIVE mode during simulation, showing real-time score distribution

## Architecture

### Backend Components

#### 1. Live Scores Buffer
```python
# In SOCDashboardAPI.__init__()
self.live_scores = []  # Stores scores from current simulation
self.max_live_scores = 1000  # Keep last 1000 scores for performance
```

#### 2. Score Collection
```python
# In _process_pcap_for_alerts()
# Collect ALL anomaly scores (not just alerts)
for record in processed_data:
    score = record.get('anomaly_score', 0.0)
    self.live_scores.append(float(score))

# Keep buffer manageable
if len(self.live_scores) > self.max_live_scores:
    self.live_scores = self.live_scores[-self.max_live_scores:]
```

#### 3. Buffer Management
- **On Simulation Start**: Buffer is cleared (`self.live_scores = []`)
- **During Processing**: Scores are collected from all processed records
- **On Completion**: Buffer retains data for viewing results

#### 4. WebSocket Emission
```python
# Real-time distribution broadcast
if self.live_scores:
    hist, bin_edges = np.histogram(self.live_scores, bins=20, range=(0, 1))
    bins = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(hist))]
    socketio.emit('live_score_distribution', {
        'bins': bins,
        'counts': hist.tolist(),
        'total_samples': len(self.live_scores),
        'simulation_active': self.mininet_active
    })
```

#### 5. New API Endpoint
```python
@app.route('/api/score-distribution/live')
@token_required
@analyst_or_admin_required
def get_live_score_distribution():
    """Get live anomaly score distribution from current simulation"""
    # Returns histogram from live_scores buffer
    # Includes simulation_active flag and simulation_type
```

### Frontend Components

#### 1. State Management
```javascript
const [isLiveMode, setIsLiveMode] = useState(false);
const [simulationActive, setSimulationActive] = useState(false);
```

#### 2. Mode Switching Logic
```javascript
// On simulation start → Switch to LIVE mode
socket.on('simulation_started', (data) => {
  setIsLiveMode(true);
  setSimulationActive(true);
});

// On simulation complete → Show results for 10s, then switch back
socket.on('mininet_complete', (data) => {
  setSimulationActive(false);
  setTimeout(() => {
    setIsLiveMode(false);
    fetchDistributionData(); // Back to historical
  }, 10000);
});
```

#### 3. Live Data Updates
```javascript
// Receive live distribution via WebSocket
socket.on('live_score_distribution', (data) => {
  if (isLiveMode) {
    updateChartData(data);
  }
  setSimulationActive(data.simulation_active);
});
```

#### 4. Visual Indicators
```jsx
{isLiveMode && (
  <span className="animate-pulse">
    {simulationActive ? '🔴 LIVE' : '📊 LIVE RESULTS'}
  </span>
)}
```

## Data Flow

### Normal Mode (Historical Data)
```
MongoDB Alerts
    ↓
GET /api/score-distribution
    ↓
Extract anomaly_score from alerts
    ↓
Create histogram (20 bins, 0-1 range)
    ↓
Display on graph
```

### Live Mode (Real-time Data)
```
Simulation Processing
    ↓
ML Model generates scores for each record
    ↓
Scores collected in live_scores buffer
    ↓
WebSocket emit 'live_score_distribution'
    ↓
Frontend receives and displays immediately
    ↓
Graph updates in real-time
```

## Key Features

### 1. Automatic Mode Switching
- **Starts**: When simulation begins → switches to LIVE
- **Ends**: 10 seconds after simulation completes → switches back to historical
- **Seamless**: No user interaction required

### 2. Real-time Updates
- Scores collected as they're generated
- WebSocket broadcasts after each batch
- Graph updates within 1-2 seconds

### 3. Performance Optimization
- Buffer limited to 1000 scores (configurable)
- Histogram calculation on-demand
- Efficient numpy operations

### 4. Visual Feedback
- **🔴 LIVE**: Simulation actively running
- **📊 LIVE RESULTS**: Simulation complete, showing final results
- **Pulse animation**: Draws attention to live mode

### 5. Data Accuracy
- Collects scores from **all processed records**, not just alerts
- Shows true distribution of ML model predictions
- Includes both normal and anomalous scores

## Benefits

### For Users
1. ✅ **Immediate Feedback**: See scores as simulation runs
2. ✅ **Model Behavior**: Understand how ML model scores traffic
3. ✅ **Attack Patterns**: Visualize difference between normal and attack traffic
4. ✅ **Threshold Validation**: See how many scores exceed threshold

### For System
1. ✅ **Memory Efficient**: Fixed buffer size (1000 scores)
2. ✅ **No Database Load**: Doesn't query MongoDB during live mode
3. ✅ **Real-time Performance**: WebSocket-based, sub-second updates
4. ✅ **Automatic Cleanup**: Buffer cleared on each simulation

## Testing the Live Feature

### Test 1: Normal Traffic Simulation
1. Start normal traffic simulation
2. **Expected**: Graph switches to LIVE mode
3. **Expected**: Most bars appear in 0.0-0.3 range (low scores)
4. **Expected**: "🔴 LIVE" indicator shows
5. **Expected**: Graph updates as processing continues

### Test 2: Attack Simulation (SYN_FLOOD)
1. Start SYN_FLOOD simulation
2. **Expected**: Graph switches to LIVE mode
3. **Expected**: Bars appear in 0.7-1.0 range (high scores)
4. **Expected**: Clear visual difference from normal traffic
5. **Expected**: Real-time updates show score accumulation

### Test 3: Mode Transition
1. Run simulation to completion
2. **Expected**: "🔴 LIVE" changes to "📊 LIVE RESULTS"
3. **Expected**: Graph shows final distribution
4. **Expected**: After 10 seconds, switches back to historical
5. **Expected**: No "LIVE" indicator, shows all-time data

### Test 4: Multiple Simulations
1. Run simulation #1 (normal) → See low scores
2. Run simulation #2 (attack) → See high scores
3. **Expected**: Buffer clears between simulations
4. **Expected**: Each simulation shows its own distribution
5. **Expected**: Historical mode shows cumulative data

## Backend Logs

During live mode, you'll see:
```
🔄 Cleared live scores buffer for new simulation
🔬 Processing PCAP with trained ML model...
📊 Live scores buffer: 500 scores collected
📊 Emitted live score distribution: 500 samples
📊 Live scores buffer: 1000 scores collected
📊 Emitted live score distribution: 1000 samples
```

## API Endpoints

### Historical Distribution
```
GET /api/score-distribution
Returns: Histogram from MongoDB alerts (last 1000)
```

### Live Distribution
```
GET /api/score-distribution/live
Returns: Histogram from current simulation buffer
Includes: simulation_active, simulation_type
```

## WebSocket Events

### Emitted by Backend
- `live_score_distribution` - Real-time histogram data
- `simulation_started` - Triggers live mode
- `mininet_complete` - Triggers results display

### Listened by Frontend
- Switches modes automatically
- Updates graph in real-time
- Manages visual indicators

## Configuration

### Buffer Size
```python
self.max_live_scores = 1000  # Adjust for performance vs. accuracy
```

### Results Display Duration
```javascript
setTimeout(() => {
  setIsLiveMode(false);
}, 10000);  // 10 seconds, adjust as needed
```

### Histogram Bins
```python
hist, bin_edges = np.histogram(scores, bins=20, range=(0, 1))
# 20 bins from 0.0 to 1.0, each 0.05 wide
```

## Comparison: Historical vs. Live

| Aspect | Historical Mode | Live Mode |
|--------|----------------|-----------|
| **Data Source** | MongoDB alerts | In-memory buffer |
| **Update Frequency** | 10 seconds (polling) | Real-time (WebSocket) |
| **Data Scope** | All past alerts | Current simulation only |
| **Performance** | Database query | Memory access |
| **Use Case** | Overall trends | Simulation feedback |
| **Indicator** | None | 🔴 LIVE badge |

## Result

The score distribution graph now provides **immediate, live visual feedback** during simulations:

- ✅ Switches automatically to live mode
- ✅ Shows scores as they're generated
- ✅ Updates in real-time (1-2 seconds)
- ✅ Clear visual indicators (LIVE badge)
- ✅ Displays final results for 10 seconds
- ✅ Returns to historical mode automatically
- ✅ Memory efficient (fixed buffer)
- ✅ No database load during live mode

**Users can now watch the ML model's scoring behavior in real-time!** 🎉
