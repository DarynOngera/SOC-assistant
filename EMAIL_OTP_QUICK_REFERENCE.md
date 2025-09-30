# Email OTP Verification - Quick Reference

## 🚀 Quick Start

### Development Mode (No SMTP)
```bash
# OTP prints to console - no email configuration needed
python src/dashboard/server.py

# Check console output for OTP:
# [DEV MODE] Email Verification OTP for user@example.com: 123456
```

### Production Mode
```bash
# Set environment variables
export SMTP_SERVER=smtp.gmail.com
export SMTP_PORT=587
export SMTP_USERNAME=your-email@gmail.com
export SMTP_PASSWORD=your-app-password
export SMTP_FROM=noreply@soc.local
```

## 📡 API Endpoints

### Verify Email
```bash
POST /api/auth/email/verify
Content-Type: application/json

{
  "email": "user@example.com",
  "otp": "123456"
}

# Success: 200 OK
# Error: 400 Bad Request
```

### Resend OTP
```bash
POST /api/auth/email/resend
Content-Type: application/json

{
  "email": "user@example.com"
}

# Always returns 200 OK (security)
```

### Check Status
```bash
GET /api/auth/email/status/user@example.com

# Response:
{
  "verified": true,
  "exists": true
}
```

## 💻 Code Examples

### Backend - Send Verification
```python
from src.auth.mongodb_auth_utils import MongoDBAuthManager

auth_manager = MongoDBAuthManager()

# Send verification OTP
success, message = auth_manager.send_verification_otp(
    email="user@example.com",
    username="johndoe"
)

# Verify OTP
success, message = auth_manager.verify_email_with_otp(
    email="user@example.com",
    otp="123456"
)
```

### Frontend - EmailVerification Component
```jsx
import EmailVerification from './components/EmailVerification';

function App() {
  return (
    <EmailVerification
      email="user@example.com"
      onVerified={() => {
        console.log('Email verified!');
        // Redirect or update UI
      }}
      onBack={() => {
        // Handle back navigation
      }}
    />
  );
}
```

### Frontend - Verify API Call
```javascript
const verifyEmail = async (email, otp) => {
  const response = await fetch('http://localhost:5000/api/auth/email/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp })
  });
  
  return response.ok;
};
```

## 🧪 Testing

### Run Test Suite
```bash
python tests/test_email_verification.py
```

### Manual Test Flow
```bash
# 1. Create user (admin)
curl -X POST http://localhost:5000/api/admin/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"Test123!","email":"test@example.com","role":"analyst"}'

# 2. Check console for OTP (dev mode)
# [DEV MODE] Email Verification OTP for test@example.com: 123456

# 3. Verify email
curl -X POST http://localhost:5000/api/auth/email/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp":"123456"}'

# 4. Check status
curl http://localhost:5000/api/auth/email/status/test@example.com
```

## 🔐 Security Settings

| Setting | Value | Location |
|---------|-------|----------|
| OTP Length | 6 digits | `generate_email_otp()` |
| OTP Expiry | 10 minutes | `self.otp_expiry` |
| Max Attempts | 3 | `verify_email_otp()` |
| Resend Cooldown | 60 seconds | Frontend |
| Rate Limit (Verify) | 5/min | `@limiter.limit()` |
| Rate Limit (Resend) | 3/min | `@limiter.limit()` |

## 📧 Email Template

**Subject:** SOC Dashboard - Verify Your Email

**Key Elements:**
- Green gradient header
- 6-digit OTP in large font
- 10-minute expiration warning
- Security tips
- Next steps guide

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Email not received | Check console (dev mode) or spam folder |
| OTP expired | Click resend (10 min expiry) |
| Invalid OTP | Check all 6 digits, max 3 attempts |
| Resend disabled | Wait 60 seconds for cooldown |
| SMTP error | Check credentials and network |

## 📊 Status Indicators

### UserManagement Component
- ✅ **Verified** - Green badge with checkmark
- ⚠️ **Pending** - Amber badge with mail icon
- 📧 **Send button** - Resend verification

### EmailVerification Component
- 🔵 **Input** - Blue focus ring
- ✅ **Success** - Green checkmark animation
- ❌ **Error** - Red error message
- ⏱️ **Cooldown** - Timer countdown

## 🔄 User Flow Diagram

```
Admin Creates User
       ↓
User Created in DB (email_verified: false)
       ↓
OTP Generated (6 digits, 10 min expiry)
       ↓
Email Sent (or console in dev mode)
       ↓
User Receives Email
       ↓
User Enters OTP
       ↓
OTP Validated (max 3 attempts)
       ↓
Email Marked Verified (email_verified: true)
       ↓
User Can Access Full Features
```

## 📁 Key Files

| File | Purpose |
|------|---------|
| `src/auth/mongodb_auth_utils.py` | OTP generation & verification |
| `src/dashboard/server.py` | API endpoints |
| `frontend/src/components/EmailVerification.jsx` | Verification UI |
| `frontend/src/components/UserManagement.jsx` | Admin interface |
| `tests/test_email_verification.py` | Test suite |
| `docs/EMAIL_VERIFICATION_GUIDE.md` | Full documentation |

## 🎯 Common Tasks

### Add User and Send Verification
```python
# In admin code
success, msg = auth_manager.create_user(
    username="newuser",
    password="SecurePass123!",
    role="analyst",
    email="newuser@example.com"
)

if success:
    auth_manager.send_verification_otp(
        email="newuser@example.com",
        username="newuser"
    )
```

### Check if Email Verified
```python
user = dal.get_user_by_email("user@example.com")
is_verified = user.get('email_verified', False)
```

### Resend Verification
```python
success, msg = auth_manager.resend_verification_otp(
    email="user@example.com"
)
```

## 🚦 Rate Limits

```python
# Verify endpoint
@limiter.limit("5 per minute")

# Resend endpoint  
@limiter.limit("3 per minute")

# Status endpoint
@limiter.limit("10 per minute")
```

## 🎨 UI Components

### EmailVerification Props
```typescript
interface EmailVerificationProps {
  email: string;              // Email to verify
  onVerified?: () => void;    // Success callback
  onBack?: () => void;        // Back button callback
}
```

### Features
- Auto-focus first input
- Auto-advance on digit entry
- Paste support (Ctrl+V)
- Resend with cooldown
- Real-time validation
- Success animation

## 📞 Quick Help

**Dev Mode OTP not showing?**
- Check console output
- Verify server is running
- Check SMTP env vars (should be empty for dev mode)

**Production emails not sending?**
- Verify SMTP credentials
- Check firewall/network
- Test SMTP connection manually
- Review server logs

**OTP always invalid?**
- Check system time (expiry calculation)
- Verify OTP hasn't expired (10 min)
- Check for typos in OTP entry
- Max 3 attempts per OTP

---

**Quick Links:**
- Full Guide: `docs/EMAIL_VERIFICATION_GUIDE.md`
- Test Suite: `tests/test_email_verification.py`
- Summary: `EMAIL_VERIFICATION_SUMMARY.md`
