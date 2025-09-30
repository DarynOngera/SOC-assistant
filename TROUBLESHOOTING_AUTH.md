# Authentication Troubleshooting Guide

## Issue: Cannot Add Passkey or Toggle Auth Settings

### Quick Diagnosis

Open your browser's Developer Tools (F12) and check:

1. **Console Tab** - Look for JavaScript errors
2. **Network Tab** - Check which API calls are failing (400, 401, 500)
3. **Application Tab** → Local Storage - Verify `access_token` exists

### Common Issues & Solutions

## 1. Not Logged In / Token Expired

**Symptoms:**
- 401 Unauthorized errors
- Redirected to login page
- "Token required" or "Invalid token" errors

**Solution:**
```bash
# Log out and log back in
1. Click Logout
2. Login with: admin / SecureAdmin123!
3. Try again
```

## 2. MongoDB Not Initialized

**Symptoms:**
- 500 Internal Server Error
- "Database connection failed"
- Backend logs show MongoDB errors

**Solution:**
```bash
# Ensure MongoDB is running
mongod

# Check if database exists
mongosh
use soc_dashboard
db.users.findOne({username: "admin"})

# If user doesn't have required fields, update:
db.users.updateOne(
  {username: "admin"},
  {$set: {
    email_verified: false,
    default_auth_method: "password",
    email_otp_enabled: false,
    passkey_enabled: false,
    passkeys: []
  }}
)
```

## 3. Missing User Fields

**Symptoms:**
- Preferences don't load
- Toggles don't work
- 400 Bad Request on preferences endpoint

**Solution:**
Run this MongoDB update to add missing fields:

```javascript
// Connect to MongoDB
mongosh
use soc_dashboard

// Update all users with missing fields
db.users.updateMany(
  {},
  {$set: {
    email_verified: {$ifNull: ["$email_verified", false]},
    default_auth_method: {$ifNull: ["$default_auth_method", "password"]},
    email_otp_enabled: {$ifNull: ["$email_otp_enabled", false]},
    passkey_enabled: {$ifNull: ["$passkey_enabled", false]},
    passkeys: {$ifNull: ["$passkeys", []]}
  }}
)
```

## 4. CORS Issues

**Symptoms:**
- "CORS policy" errors in console
- Requests blocked by browser
- "Access-Control-Allow-Origin" errors

**Solution:**
```bash
# Check backend is running on correct port
python src/dashboard/server.py
# Should show: Running on http://localhost:5000

# Check frontend is on correct port
cd frontend && npm start
# Should show: Running on http://localhost:3000
```

## 5. WebAuthn Not Supported

**Symptoms:**
- "Passkeys are not supported in this browser"
- Passkey button disabled

**Solution:**
- Update browser to latest version
- Use Chrome 109+, Edge 109+, Safari 16+, or Firefox 119+
- For production, ensure HTTPS is enabled

## 6. Backend Endpoints Missing

**Symptoms:**
- 404 Not Found errors
- "Endpoint does not exist"

**Solution:**
```bash
# Verify server.py has all endpoints
grep -n "api/auth/passkey" src/dashboard/server.py
grep -n "api/auth/preferences" src/dashboard/server.py

# Should show:
# - /api/auth/passkey/register/begin
# - /api/auth/passkey/register/complete
# - /api/auth/passkey/authenticate/begin
# - /api/auth/passkey/authenticate/complete
# - /api/auth/passkey/list
# - /api/auth/passkey/<credential_id> (DELETE)
# - /api/auth/preferences (GET, PUT)
```

## Step-by-Step Debugging

### Step 1: Check Backend is Running

```bash
# Terminal 1: Start MongoDB
mongod

# Terminal 2: Start Backend
cd /home/ongera/projects/SOC-assistant
python src/dashboard/server.py

# Should see:
# ✓ MongoDB initialized successfully
# ✓ Data migration completed
# * Running on http://localhost:5000
```

### Step 2: Check Frontend is Running

```bash
# Terminal 3: Start Frontend
cd /home/ongera/projects/SOC-assistant/frontend
npm start

# Should open browser at http://localhost:3000
```

### Step 3: Test API Endpoints

```bash
# Get auth token first
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecureAdmin123!"}' \
  | jq -r '.access_token')

# Test preferences endpoint
curl -X GET http://localhost:5000/api/auth/preferences \
  -H "Authorization: Bearer $TOKEN"

# Should return:
# {"default_method":"password","email_otp_enabled":false,...}

# Test passkey registration begin
curl -X POST http://localhost:5000/api/auth/passkey/register/begin \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"

# Should return options and state_id
```

### Step 4: Check Browser Console

```javascript
// Open DevTools (F12) → Console
// Paste this to check localStorage:
console.log('Token:', localStorage.getItem('access_token'));
console.log('User:', JSON.parse(localStorage.getItem('user')));

// Should show valid token and user object
```

### Step 5: Check Network Requests

```
1. Open DevTools (F12) → Network tab
2. Click "Add Passkey" button
3. Look for failed requests (red)
4. Click on failed request
5. Check:
   - Request URL
   - Request Headers (Authorization header present?)
   - Response (error message)
```

## Common Error Messages

### "Token required" or "Authorization header missing"

**Cause:** Not logged in or token expired

**Fix:**
```bash
# Log out and log back in
# Token expires after 8 hours
```

### "User not found"

**Cause:** User doesn't exist in database

**Fix:**
```bash
mongosh
use soc_dashboard
db.users.findOne({username: "admin"})
# If null, user doesn't exist - recreate it
```

### "No passkeys found for user"

**Cause:** Trying to authenticate with passkey before registering one

**Fix:**
```bash
# This is expected! Register a passkey first:
1. Login with password
2. Go to Settings
3. Click "Add Passkey"
4. Then try passkey login
```

### "Invalid or expired registration session"

**Cause:** Registration took too long (>5 minutes) or server restarted

**Fix:**
```bash
# Start over:
1. Refresh the page
2. Click "Add Passkey" again
3. Complete registration within 5 minutes
```

### "This device already has a passkey registered"

**Cause:** Trying to register duplicate passkey on same device

**Fix:**
```bash
# Either:
1. Use a different device/browser
2. Or delete existing passkey first, then re-register
```

## Reset Everything (Nuclear Option)

If nothing works, reset the entire authentication system:

```bash
# 1. Stop all services
# Ctrl+C in all terminals

# 2. Clear MongoDB
mongosh
use soc_dashboard
db.users.deleteMany({})
db.dropDatabase()
exit

# 3. Clear browser data
# DevTools (F12) → Application → Clear storage → Clear site data

# 4. Restart services
mongod
python src/dashboard/server.py
cd frontend && npm start

# 5. Login with default admin
# Username: admin
# Password: SecureAdmin123!
# (Will be created automatically on first start)
```

## Get Help

### Check Logs

```bash
# Backend logs
tail -f logs/soc_dashboard.log

# Or check terminal where server is running
```

### Enable Debug Mode

```python
# In src/dashboard/server.py, add:
app.config['DEBUG'] = True

# Restart server
```

### Contact Support

Provide:
1. Error message from browser console
2. Failed API request from Network tab
3. Backend logs
4. Steps to reproduce

## Prevention

### Best Practices

1. **Keep services running** - Don't stop MongoDB or backend during use
2. **Use latest browser** - Update to latest Chrome/Edge/Safari/Firefox
3. **Check token expiry** - Re-login if session expired (8 hours)
4. **Complete registration quickly** - Passkey registration expires in 5 minutes
5. **One passkey per device** - Don't register multiple passkeys on same device

### Health Check

Run this periodically:

```bash
# Check MongoDB
mongosh --eval "db.adminCommand('ping')"

# Check Backend
curl http://localhost:5000/api/health

# Check Frontend
curl http://localhost:3000
```

All should return success!
