# Total Processed Stats Update - Fix Summary

## Problem
The "Total Processed" statistic remained static at 1000 (or whatever initial value) and didn't increment when simulations ran and processed network records.

## Root Cause
The simulation's `_process_pcap_for_alerts()` method was:
1. ✅ Processing network records from PCAP files
2. ✅ Generating alerts and storing them in MongoDB
3. ✅ Broadcasting alerts via WebSocket
4. ❌ **NOT updating system statistics in MongoDB**

The monitoring system (`process_network_data()`) correctly updates stats, but the simulation didn't have this logic.

## Solution
Added system statistics update logic to the simulation's `_process_pcap_for_alerts()` method, mirroring the monitoring system's approach.

## Changes Made

### File: `src/dashboard/server.py`

**Location:** Inside `_process_pcap_for_alerts()` method, after alert generation but before broadcasting

**Added Code:**
```python
# Update system stats in MongoDB (same as monitoring system)
try:
    current_stats = self.dal.get_latest_system_stats("realtime")
    if current_stats:
        updated_stats = {
            'total_processed': current_stats.get('total_processed', 0) + len(processed_data),
            'anomalies_detected': current_stats.get('anomalies_detected', 0) + len(new_alerts),
            'total_alerts': current_stats.get('total_alerts', 0) + len(new_alerts),
            'active_alerts': self.get_active_alerts_count(),
            'system_health': 'healthy',
            'detection_threshold': self.threshold,
            'severity_distribution': self.get_severity_distribution(),
            'detection_rate': self.calculate_detection_rate()
        }
        self.dal.save_system_stats("realtime", updated_stats)
        logger.info(f"📊 Updated system stats: processed={updated_stats['total_processed']}, alerts={updated_stats['total_alerts']}")
except Exception as e:
    logger.error(f"Error updating system stats: {e}")
```

**Also Added:**
```python
# Emit stats update to ensure StatusCards refresh
socketio.emit('stats_update', updated_stats)
```

## How It Works Now

### Before Fix:
```
Simulation runs
  ↓
Processes 500 network records
  ↓
Generates 15 alerts
  ↓
Stores alerts in MongoDB
  ↓
Broadcasts alerts via WebSocket
  ↓
❌ total_processed stays at 1000 (never updated)
```

### After Fix:
```
Simulation runs
  ↓
Processes 500 network records
  ↓
Generates 15 alerts
  ↓
Stores alerts in MongoDB
  ↓
✅ Updates system stats in MongoDB:
   - total_processed: 1000 → 1500 (+500)
   - anomalies_detected: 50 → 65 (+15)
   - total_alerts: 50 → 65 (+15)
  ↓
Broadcasts alerts + stats via WebSocket
  ↓
✅ Frontend StatusCards update immediately
```

## Statistics Updated

The simulation now updates these MongoDB statistics:

1. **total_processed** - Incremented by number of network records processed
2. **anomalies_detected** - Incremented by number of alerts generated
3. **total_alerts** - Incremented by number of alerts generated
4. **active_alerts** - Recalculated from current database state
5. **system_health** - Set to 'healthy' during simulation
6. **detection_threshold** - Current threshold value
7. **severity_distribution** - Recalculated (critical/high/medium/low counts)
8. **detection_rate** - Recalculated percentage

## WebSocket Events Emitted

After updating stats, the simulation emits:

1. **new_alerts** - Contains alerts array + updated stats
2. **alerts_update** - Contains alerts array + updated stats (compatibility)
3. **alert_batch_generated** - Notification with count and attack types
4. **stats_update** - Dedicated stats update event for StatusCards

## Frontend Impact

### StatusCards Component
The "Total Processed" card now:
- ✅ Updates immediately when simulation runs
- ✅ Shows accurate count of all processed records
- ✅ Increments by the number of records in each simulation

### Other Stats
All statistics update in real-time:
- **Active Alerts** - Shows current alert count
- **Detection Rate** - Recalculates based on new totals
- **System Health** - Reflects current state

## Testing the Fix

### Test 1: Run Single Simulation
1. Note current "Total Processed" value (e.g., 1000)
2. Run a simulation (e.g., SYN_FLOOD)
3. Check backend logs for: `📊 Updated system stats: processed=X, alerts=Y`
4. **Expected:** Total Processed increases by ~100-500 (depending on PCAP size)
5. **Expected:** StatusCards update within 1-2 seconds

### Test 2: Run Multiple Simulations
1. Note starting "Total Processed" (e.g., 1500)
2. Run simulation #1 → Total Processed increases to ~2000
3. Run simulation #2 → Total Processed increases to ~2500
4. Run simulation #3 → Total Processed increases to ~3000
5. **Expected:** Each simulation adds to the cumulative total

### Test 3: Check MongoDB
```javascript
// In MongoDB shell
db.system_stats.find({stat_type: "realtime"}).sort({timestamp: -1}).limit(1)

// Should show:
{
  total_processed: 2500,  // Increases with each simulation
  anomalies_detected: 75,
  total_alerts: 75,
  ...
}
```

## Backend Logs

You should now see these log messages during simulation:

```
🎯 ML Model Results: Generated 15 alerts from 500 network records
📊 Alert Detection Rate: 15/500 (3.0%)
🔍 Attack Types Detected: {'SYN_FLOOD': 15}
📊 Updated system stats: processed=1500, alerts=65
✅ Broadcasted 15 new alerts to dashboard via WebSocket
```

## Consistency with Monitoring System

The simulation now uses **identical logic** to the monitoring system for updating stats:

**Monitoring System** (`process_network_data`):
```python
updated_stats = {
    'total_processed': current_stats.get('total_processed', 0) + len(data_batch),
    'anomalies_detected': current_stats.get('anomalies_detected', 0) + len(new_alerts),
    ...
}
self.dal.save_system_stats("realtime", updated_stats)
```

**Simulation System** (`_process_pcap_for_alerts`):
```python
updated_stats = {
    'total_processed': current_stats.get('total_processed', 0) + len(processed_data),
    'anomalies_detected': current_stats.get('anomalies_detected', 0) + len(new_alerts),
    ...
}
self.dal.save_system_stats("realtime", updated_stats)
```

## Benefits

1. ✅ **Accurate Statistics** - Total processed reflects all activity (monitoring + simulation)
2. ✅ **Real-time Updates** - StatusCards update immediately
3. ✅ **Consistent Behavior** - Simulation and monitoring use same logic
4. ✅ **Better Visibility** - Users can see simulation impact on overall stats
5. ✅ **Proper Tracking** - Detection rate accurately reflects all processed data

## Result

The "Total Processed" statistic now:
- ✅ Increments with each simulation run
- ✅ Shows accurate cumulative count
- ✅ Updates in real-time on the dashboard
- ✅ Matches the actual number of network records processed

**No more static 1000 value!** 🎉
