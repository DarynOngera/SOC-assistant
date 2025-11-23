# Triage Actions Alert ID Format Fix

## Problem
All triage action endpoints were returning "Error: Invalid alert ID format" when attempting to perform actions on alerts.

## Root Cause
The triage action endpoints in `server.py` were forcing conversion of alert IDs to integers and throwing an error if the conversion failed:

```python
try:
    alert_id_int = int(alert_id)
except ValueError:
    return jsonify({'error': 'Invalid alert ID format'}), 400
```

However, MongoDB alerts can use either:
- **Integer IDs** (for backward compatibility): `alert_id: 1, 2, 3, etc.`
- **ObjectId strings** (MongoDB native): `alert_id: "507f1f77bcf86cd799439011"`

The MongoDB DAL (`mongodb_dal.py`) was already designed to handle both formats gracefully, but the server endpoints were blocking non-integer IDs before they reached the DAL.

## Solution
Updated all triage action endpoints to accept both integer and ObjectId formats without throwing errors:

```python
# Handle both integer and ObjectId formats
# Try to convert to int for backward compatibility, but accept strings (ObjectId)
try:
    alert_id_int = int(alert_id)
except (ValueError, TypeError):
    # Keep as string if not convertible (likely ObjectId)
    alert_id_int = alert_id
```

This allows the DAL to handle the ID format detection and query construction.

## Endpoints Fixed

1. **`/api/alerts/<alert_id>/flag`** - Flag an alert
2. **`/api/alerts/<alert_id>/escalate`** - Escalate an alert
3. **`/api/alerts/<alert_id>/assign`** - Assign an alert to analyst
4. **`/api/alerts/<alert_id>/investigate`** - Start investigation
5. **`/api/alerts/<alert_id>/update-investigation`** - Update investigation
6. **`/api/alerts/<alert_id>/resolve`** - Resolve an alert

Note: `/api/alerts/<alert_id>/dismiss` was already handling both formats correctly.

## MongoDB DAL Handling

The `update_alert` method in `mongodb_dal.py` already handles both formats:

```python
# Handle both integer alert_id and ObjectId formats
if isinstance(alert_id, str) and len(alert_id) == 24:
    # Looks like ObjectId string
    try:
        query = {"_id": ObjectId(alert_id)}
    except Exception:
        # Fallback to string search
        query = {"alert_id": alert_id}
else:
    # Integer alert_id (backward compatibility)
    query = {"alert_id": alert_id}
```

## Testing

Run the test script to verify all triage actions work:

```bash
# Start the server first
python src/dashboard/server.py

# In another terminal, run the test
python test_triage_fix.py
```

The test will:
1. Authenticate and get a token
2. Fetch existing alerts
3. Test all 7 triage actions on real alerts
4. Report success/failure for each action

## Impact

- ✅ All triage actions now work with both integer and ObjectId alert IDs
- ✅ Backward compatible with existing integer-based alerts
- ✅ Forward compatible with MongoDB ObjectId-based alerts
- ✅ No database schema changes required
- ✅ No breaking changes to API

## Files Modified

- `src/dashboard/server.py` - Updated 6 triage action endpoints
- `test_triage_fix.py` - Created test script (new file)
- `TRIAGE_FIX_SUMMARY.md` - This documentation (new file)
