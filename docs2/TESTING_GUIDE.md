# Testing Guide - Enhanced Authentication

## Quick Test Commands

### Backend Testing

```bash
# Run comprehensive test suite
python test_enhanced_auth.py

# Expected output:
# ✅ TOTP/MFA Test - PASSED
# ✅ Email OTP Test - PASSED
# ✅ Passkey Flow Test - PASSED
# ✅ Standard Auth Test - PASSED
# ✅ Failed Auth Test - PASSED
# ✅ Account Lockout Test - PASSED
```

### Frontend Testing

```bash
# Start frontend
cd frontend
npm start

# Open browser to http://localhost:3000
# Test each authentication method manually
```

### Email Service Testing

```bash
# Test email OTP (Development mode - OTP printed to console)
curl -X POST http://localhost:5000/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@soc.local"}'

# Check server console for:
# [DEV MODE] Email OTP for admin@soc.local: 123456

# Verify OTP
curl -X POST http://localhost:5000/api/auth/passwordless/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@soc.local","otp":"123456"}'
```

## Manual Testing Checklist

### 1. Password Login ✓
- [ ] Open http://localhost:3000
- [ ] Select "Password" tab
- [ ] Enter username: `admin`
- [ ] Enter password: `SecureAdmin123!`
- [ ] Click "Sign in with Password"
- [ ] Verify successful login

### 2. Email OTP Login ✓
- [ ] Select "Email OTP" tab
- [ ] Enter email: `admin@soc.local`
- [ ] Click "Send Login Code"
- [ ] Check server console for OTP code
- [ ] Enter the 6-digit OTP
- [ ] Click "Verify Code"
- [ ] Verify successful login

### 3. Passkey Login ✓
- [ ] First, register a passkey (see Passkey Registration below)
- [ ] Logout and return to login page
- [ ] Select "Passkey" tab
- [ ] Enter username: `admin`
- [ ] Click "Sign in with Passkey"
- [ ] Follow browser biometric prompt
- [ ] Verify successful login

### 4. MFA Setup ✓
- [ ] Login with password
- [ ] Navigate to Security Settings
- [ ] Click "Setup MFA"
- [ ] Scan QR code with Google Authenticator
- [ ] Enter 6-digit code from app
- [ ] Click "Enable MFA"
- [ ] Logout and login again
- [ ] Verify MFA code is required

### 5. Passkey Registration ✓
- [ ] Login with any method
- [ ] Navigate to Security Settings
- [ ] Find "Passkey Management" section
- [ ] Click "Register New Passkey"
- [ ] Follow browser biometric prompt
- [ ] Verify passkey appears in list
- [ ] Try deleting passkey

### 6. Error Handling ✓
- [ ] Try login with wrong password
- [ ] Try login with wrong OTP
- [ ] Try OTP after expiry (wait 10 minutes)
- [ ] Try 5 failed password attempts (account lockout)
- [ ] Try passkey on unsupported browser
- [ ] Verify error messages display correctly

## API Testing with cURL

### Standard Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SecureAdmin123!"
  }'
```

### Login with MFA
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "SecureAdmin123!",
    "mfa_token": "123456"
  }'
```

### Request Email OTP
```bash
curl -X POST http://localhost:5000/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@soc.local"
  }'
```

### Verify Email OTP
```bash
curl -X POST http://localhost:5000/api/auth/passwordless/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@soc.local",
    "otp": "123456"
  }'
```

### List Passkeys
```bash
TOKEN="your-access-token"
curl -X GET http://localhost:5000/api/auth/passkey/list \
  -H "Authorization: Bearer $TOKEN"
```

### Setup MFA
```bash
TOKEN="your-access-token"
curl -X POST http://localhost:5000/api/auth/mfa/setup \
  -H "Authorization: Bearer $TOKEN"
```

## Browser Testing

### Chrome/Edge (Recommended)
- ✅ All features supported
- ✅ Passkey with Windows Hello
- ✅ Passkey with security keys
- ✅ Best WebAuthn support

### Firefox
- ✅ All features supported
- ✅ Passkey with security keys
- ⚠️ Limited platform authenticator support

### Safari
- ✅ All features supported
- ✅ Passkey with Touch ID/Face ID
- ✅ Excellent platform authenticator

### Mobile Browsers
- ✅ Chrome Mobile - Full support
- ✅ Safari iOS - Full support with Face ID/Touch ID
- ✅ Samsung Internet - Full support

## Email Template Testing

### Gmail
1. Send test OTP to Gmail account
2. Check inbox (and spam folder)
3. Verify email renders correctly
4. Check mobile Gmail app
5. Verify OTP is clearly visible

### Outlook
1. Send test OTP to Outlook account
2. Check inbox
3. Verify email renders correctly
4. Check Outlook mobile app
5. Verify dark mode compatibility

### Mobile Email Clients
- [ ] Gmail app (iOS/Android)
- [ ] Outlook app (iOS/Android)
- [ ] Apple Mail (iOS)
- [ ] Samsung Email (Android)

## Performance Testing

### Response Times
```bash
# Test login endpoint performance
time curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecureAdmin123!"}'

# Should complete in < 500ms
```

### Rate Limiting
```bash
# Test rate limiting (should block after 5 attempts)
for i in {1..6}; do
  curl -X POST http://localhost:5000/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"wrong"}'
  echo "Attempt $i"
done
```

### OTP Expiry
```bash
# Request OTP
curl -X POST http://localhost:5000/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# Wait 11 minutes
sleep 660

# Try to verify (should fail with "OTP expired")
curl -X POST http://localhost:5000/api/auth/passwordless/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp":"123456"}'
```

## Security Testing

### SQL Injection
```bash
# Test username field
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'\'' OR 1=1--","password":"test"}'

# Should return "Invalid credentials"
```

### XSS
```bash
# Test with script tags
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"<script>alert(1)</script>","password":"test"}'

# Should be sanitized
```

### CSRF
```bash
# Test without proper headers
curl -X POST http://localhost:5000/api/auth/login \
  -d '{"username":"admin","password":"test"}'

# Should fail without Content-Type header
```

## Load Testing (Optional)

### Using Apache Bench
```bash
# Install ab
sudo apt-get install apache2-utils

# Test login endpoint
ab -n 100 -c 10 -p login.json -T application/json \
  http://localhost:5000/api/auth/login

# login.json content:
# {"username":"admin","password":"SecureAdmin123!"}
```

### Using wrk
```bash
# Install wrk
sudo apt-get install wrk

# Test endpoint
wrk -t4 -c100 -d30s --latency \
  -s login.lua http://localhost:5000/api/auth/login

# login.lua content:
# wrk.method = "POST"
# wrk.body = '{"username":"admin","password":"SecureAdmin123!"}'
# wrk.headers["Content-Type"] = "application/json"
```

## Automated Testing

### Python Test Script
```python
#!/usr/bin/env python3
import requests
import time

BASE_URL = "http://localhost:5000"

def test_password_login():
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "SecureAdmin123!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    print("✓ Password login test passed")

def test_email_otp():
    # Request OTP
    response = requests.post(f"{BASE_URL}/api/auth/passwordless/request", json={
        "email": "admin@soc.local"
    })
    assert response.status_code == 200
    print("✓ OTP request test passed")

def test_invalid_login():
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    print("✓ Invalid login test passed")

def test_rate_limiting():
    for i in range(6):
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "username": "admin",
            "password": "wrong"
        })
    # 6th attempt should be rate limited
    assert response.status_code == 429
    print("✓ Rate limiting test passed")

if __name__ == "__main__":
    test_password_login()
    test_email_otp()
    test_invalid_login()
    test_rate_limiting()
    print("\n✅ All tests passed!")
```

## Troubleshooting Tests

### If Tests Fail

**Backend not starting:**
```bash
# Check dependencies
pip list | grep -E "fido2|pyotp|qrcode"

# Check for errors
python src/dashboard/server.py
```

**Frontend not loading:**
```bash
# Check Node version
node --version  # Should be 14+

# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Email OTP not working:**
```bash
# Check environment variables
cat .env | grep SMTP

# Test SMTP connection
python -c "import smtplib; smtplib.SMTP('smtp.gmail.com', 587).starttls()"
```

**Passkey not working:**
```bash
# Check HTTPS
# Passkeys require HTTPS (except localhost)

# Check browser support
# Open browser console and run:
# console.log(!!window.PublicKeyCredential)
```

## Test Data

### Default Admin Account
```
Username: admin
Password: SecureAdmin123!
Email: admin@soc.local
```

### Test Users (Create as needed)
```
Username: analyst1
Password: TestPass123!
Email: analyst1@soc.local
Role: analyst

Username: manager1
Password: TestPass123!
Email: manager1@soc.local
Role: admin
```

## Success Criteria

All tests should pass with:
- ✅ Response time < 500ms
- ✅ No errors in console
- ✅ Proper error messages
- ✅ Rate limiting working
- ✅ OTP expiry working
- ✅ Account lockout working
- ✅ All auth methods functional
- ✅ Email template rendering correctly
- ✅ Passkeys working on supported browsers

## Reporting Issues

When reporting issues, include:
1. Test that failed
2. Error message
3. Browser/OS version
4. Server logs
5. Network tab screenshot
6. Steps to reproduce

---

**Happy Testing!** 🧪
