# Threat Analysis 30-Minute Interval Update

## Overview
Updated the threat analysis graphs to use 30-minute intervals by default, providing more granular and informative visualizations of attack trends.

## Changes Made

### Backend (`src/dashboard/server.py`)

**Endpoint:** `/api/attack-trends`

1. **Default Granularity Changed:**
   - Previous: `granularity = 'hour'`
   - New: `granularity = '30min'`

2. **Added 30-Minute Bucketing Logic:**
   ```python
   if granularity == '30min':
       # Round down to nearest 30-minute interval
       minute = (timestamp.minute // 30) * 30
       bucket_key = timestamp.replace(minute=minute, second=0, microsecond=0).strftime('%Y-%m-%d %H:%M')
   ```

3. **Supported Granularities:**
   - `30min` - 30-minute intervals (NEW DEFAULT)
   - `hour` - Hourly intervals
   - `day` - Daily intervals

### Frontend (`frontend/src/components/AttackTrends.jsx`)

1. **Default Granularity Updated:**
   ```javascript
   const [granularity, setGranularity] = useState('30min');
   ```

2. **Granularity Selector Enhanced:**
   - Added "30 Minutes" option as the first choice
   - Maintains "Hourly" and "Daily" options for flexibility

3. **Timestamp Formatting Updated:**
   - Both 30-minute and hourly views now show time with minutes
   - Format: `MMM DD, HH:MM` (e.g., "Nov 22, 14:30")

## Benefits

### 1. **More Granular Data**
- 48 data points in 24 hours (vs 24 with hourly)
- Better visibility into attack patterns and spikes
- Easier to identify short-duration attack campaigns

### 2. **Improved Trend Detection**
- More accurate trend percentage calculations
- Better peak activity identification
- Clearer visualization of attack progression

### 3. **Enhanced Analysis**
- Detect burst attacks that might be missed in hourly aggregation
- Better correlation with specific events or time windows
- More actionable insights for incident response

### 4. **User Flexibility**
Users can still switch between granularities:
- **30 Minutes** - Detailed view for recent activity (default)
- **Hourly** - Balanced view for daily analysis
- **Daily** - High-level view for long-term trends

## Example Use Cases

### 1. **Burst Attack Detection**
A DDoS attack lasting 15 minutes will now be clearly visible as a spike in a 30-minute bucket, rather than being averaged out in an hourly bucket.

### 2. **Time-Based Pattern Analysis**
Identify if attacks occur at specific times (e.g., 14:00-14:30 vs 14:30-15:00) for better scheduling of security measures.

### 3. **Incident Response**
During active incidents, 30-minute intervals provide near real-time visibility while maintaining manageable data volumes.

## API Usage

### Request
```bash
GET /api/attack-trends?hours=24&granularity=30min
```

### Response Structure
```json
{
  "trends": [
    {
      "timestamp": "2025-11-22 14:00",
      "total_attacks": 15,
      "attack_types": {
        "DDoS": 8,
        "Port Scan": 5,
        "Brute Force": 2
      },
      "severity_distribution": {
        "critical": 3,
        "high": 7,
        "medium": 4,
        "low": 1
      }
    }
  ],
  "summary": {
    "trend_direction": "increasing",
    "trend_percentage": 25.5,
    "total_attacks": 342,
    "unique_attack_types": 8,
    "peak_hour": "2025-11-22 14:30"
  },
  "time_range": "24h",
  "granularity": "30min"
}
```

## Performance Considerations

- **Data Volume:** 30-minute intervals double the data points compared to hourly
- **Query Limit:** Set to 1000 alerts per query (sufficient for most use cases)
- **Refresh Rate:** Frontend refreshes every 60 seconds
- **Chart Performance:** Recharts handles 48+ data points efficiently

## Backward Compatibility

✅ Fully backward compatible:
- API accepts `granularity` parameter (defaults to `30min`)
- Frontend allows switching between all granularities
- Existing hourly/daily views still work perfectly

## Testing

To verify the changes:

1. **Start the backend:**
   ```bash
   python src/dashboard/server.py
   ```

2. **Start the frontend:**
   ```bash
   cd frontend
   npm start
   ```

3. **Navigate to Threat Analysis:**
   - View should default to 30-minute intervals
   - Charts should show more data points
   - Switch between granularities to compare views

4. **Test API directly:**
   ```bash
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     "http://localhost:5000/api/attack-trends?hours=24&granularity=30min"
   ```

## Files Modified

1. `src/dashboard/server.py` - Backend API endpoint
2. `frontend/src/components/AttackTrends.jsx` - Frontend component
3. `THREAT_ANALYSIS_30MIN_UPDATE.md` - This documentation

## Future Enhancements

Potential improvements for even better analysis:

- **5-minute intervals** for real-time monitoring mode
- **Auto-adjust granularity** based on time range (30min for <48h, hourly for <7d, daily for >7d)
- **Zoom functionality** to drill down into specific time periods
- **Comparison mode** to overlay different time periods
