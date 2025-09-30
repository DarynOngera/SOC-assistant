# Email Verification Guide

## Overview

The SOC Dashboard implements a secure email verification system using One-Time Passwords (OTP) sent via email. This ensures that users have access to their registered email address and helps prevent unauthorized account creation.

## Features

### 🔐 Security Features
- **6-digit OTP codes** with 10-minute expiration
- **Rate limiting**: Maximum 3 verification attempts per OTP
- **Secure email templates** with professional design
- **Development mode** for testing without SMTP configuration
- **Email enumeration protection** (doesn't reveal if email exists)

### ✨ User Experience
- **Auto-focus** and **auto-advance** between OTP input fields
- **Paste support** for OTP codes
- **Resend functionality** with 60-second cooldown
- **Real-time validation** and error feedback
- **Visual status indicators** in admin dashboard

## Architecture

### Backend Components

#### 1. Authentication Manager (`mongodb_auth_utils.py`)

**Email Verification Methods:**

```python
# Generate and send verification OTP
send_verification_otp(email: str, username: str) -> Tuple[bool, str]

# Verify email with OTP
verify_email_with_otp(email: str, otp: str) -> Tuple[bool, str]

# Resend verification OTP
resend_verification_otp(email: str) -> Tuple[bool, str]

# Generate 6-digit OTP
generate_email_otp(email: str) -> str

# Verify OTP code
verify_email_otp(email: str, otp: str) -> Tuple[bool, str]
```

**OTP Storage:**
```python
self.email_otps = {
    'email@example.com': {
        'otp': '123456',
        'expires': datetime.utcnow() + timedelta(minutes=10),
        'attempts': 0
    }
}
```

#### 2. API Endpoints (`server.py`)

**Email Verification Endpoints:**

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/api/auth/email/verify` | POST | Verify email with OTP | 5/min |
| `/api/auth/email/resend` | POST | Resend verification OTP | 3/min |
| `/api/auth/email/status/<email>` | GET | Check verification status | 10/min |

**Request/Response Examples:**

```bash
# Verify Email
POST /api/auth/email/verify
{
  "email": "user@example.com",
  "otp": "123456"
}

Response (Success):
{
  "message": "Email verified successfully"
}

Response (Error):
{
  "error": "Invalid OTP"
}

# Resend Verification
POST /api/auth/email/resend
{
  "email": "user@example.com"
}

Response:
{
  "message": "If this email is registered and unverified, you will receive a verification code"
}

# Check Status
GET /api/auth/email/status/user@example.com

Response:
{
  "verified": true,
  "exists": true
}
```

### Frontend Components

#### 1. EmailVerification Component

**Location:** `frontend/src/components/EmailVerification.jsx`

**Props:**
- `email` (string): Email address to verify
- `onVerified` (function): Callback when verification succeeds
- `onBack` (function): Callback for back navigation

**Features:**
- 6-digit OTP input with auto-focus and auto-advance
- Paste support for OTP codes
- Resend functionality with cooldown timer
- Real-time validation and error messages
- Success animation and auto-redirect

**Usage:**
```jsx
import EmailVerification from './components/EmailVerification';

<EmailVerification
  email="user@example.com"
  onVerified={() => {
    // Handle successful verification
    console.log('Email verified!');
  }}
  onBack={() => {
    // Handle back navigation
    setShowVerification(false);
  }}
/>
```

#### 2. UserManagement Updates

**New Features:**
- **Email verification status column** with visual indicators
- **Resend button** for unverified emails
- **Success notifications** when verification emails are sent
- **Real-time status updates**

**Visual Indicators:**
- ✅ **Green checkmark** - Email verified
- ⚠️ **Amber warning** - Email pending verification
- 📧 **Send icon** - Resend verification email

## User Flow

### 1. User Creation (Admin)

```
Admin creates user
    ↓
User account created in database
    ↓
Verification OTP generated
    ↓
Email sent to user with OTP
    ↓
Admin sees "Verification email sent" message
```

### 2. Email Verification (User)

```
User receives email with OTP
    ↓
User opens verification page
    ↓
User enters 6-digit OTP
    ↓
System validates OTP
    ↓
Email marked as verified
    ↓
User can access full features
```

### 3. Resend Flow

```
User didn't receive email
    ↓
Admin clicks resend button
    ↓
New OTP generated
    ↓
New email sent to user
    ↓
60-second cooldown starts
```

## Email Templates

### Verification Email

**Subject:** SOC Dashboard - Verify Your Email

**Features:**
- Professional gradient design
- Large, readable OTP code
- Security warnings
- Expiration notice (10 minutes)
- Next steps guide
- Mobile-responsive

**Template Preview:**
```
┌─────────────────────────────────┐
│   Welcome to SOC Dashboard      │
│   VERIFY YOUR EMAIL ADDRESS     │
├─────────────────────────────────┤
│                                 │
│   👋 Hello, username!           │
│                                 │
│   Your verification code:       │
│                                 │
│   ┌─────────────────────────┐  │
│   │      1 2 3 4 5 6        │  │
│   └─────────────────────────┘  │
│                                 │
│   ⚠️ Expires in 10 minutes     │
│                                 │
│   📋 Next Steps:                │
│   1. Enter code                 │
│   2. Complete profile           │
│   3. Start using dashboard      │
│                                 │
└─────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@soc.local

# OTP Settings (in code)
OTP_EXPIRY=10  # minutes
OTP_MAX_ATTEMPTS=3
RESEND_COOLDOWN=60  # seconds
```

### Development Mode

When SMTP credentials are not configured, the system runs in **development mode**:

- OTP codes are printed to console
- No actual emails are sent
- All other functionality works normally

**Console Output:**
```
[DEV MODE] Email Verification OTP for user@example.com: 123456
```

## Security Considerations

### 1. OTP Generation
- Uses `secrets.randbelow(10)` for cryptographically secure random digits
- 6 digits = 1,000,000 possible combinations
- 10-minute expiration reduces attack window

### 2. Rate Limiting
- **API level**: 3-5 requests per minute per endpoint
- **OTP level**: Maximum 3 attempts per OTP code
- **Resend cooldown**: 60 seconds between resend requests

### 3. Email Enumeration Protection
- Resend endpoint always returns success message
- Doesn't reveal if email exists in database
- Status endpoint requires authentication (future enhancement)

### 4. Data Storage
- OTPs stored in memory (use Redis in production)
- Automatic cleanup on expiration
- No OTP codes stored in database

### 5. Email Security
- TLS encryption for SMTP connection
- HTML email with security warnings
- Clear expiration notices
- No sensitive data in email body

## Testing

### Run Test Suite

```bash
# Run email verification tests
python tests/test_email_verification.py
```

**Test Coverage:**
- ✅ User creation with email verification
- ✅ OTP generation and sending
- ✅ Email verification with valid OTP
- ✅ Email verification with invalid OTP
- ✅ OTP expiration handling
- ✅ Resend functionality
- ✅ Rate limiting (max attempts)
- ✅ Already verified rejection
- ✅ OTP format validation

### Manual Testing

1. **Create User:**
   ```bash
   # Login as admin
   # Navigate to User Management
   # Click "Create User"
   # Fill in details and submit
   ```

2. **Check Email:**
   - Check console for dev mode OTP
   - Or check email inbox for verification email

3. **Verify Email:**
   - Navigate to verification page
   - Enter 6-digit OTP
   - Verify success message

4. **Test Resend:**
   - Click resend button in User Management
   - Wait for cooldown to expire
   - Click again to resend

## Troubleshooting

### Issue: Email not received

**Solutions:**
1. Check spam/junk folder
2. Verify SMTP configuration
3. Check server logs for errors
4. Use resend functionality
5. In dev mode, check console output

### Issue: OTP expired

**Solutions:**
1. Click resend to get new OTP
2. OTPs expire after 10 minutes
3. Check system time is correct

### Issue: Invalid OTP error

**Solutions:**
1. Verify all 6 digits are correct
2. Check for typos
3. OTP is case-sensitive (digits only)
4. Request new OTP if attempts exceeded

### Issue: Resend button disabled

**Solutions:**
1. Wait for 60-second cooldown
2. Countdown timer shows remaining time
3. Refresh page if timer stuck

## Production Deployment

### Checklist

- [ ] Configure SMTP credentials in environment variables
- [ ] Use Redis for OTP storage instead of in-memory
- [ ] Enable HTTPS for all API endpoints
- [ ] Configure proper rate limiting
- [ ] Set up email monitoring/logging
- [ ] Test email delivery to common providers (Gmail, Outlook, etc.)
- [ ] Configure SPF, DKIM, DMARC records for email domain
- [ ] Monitor OTP success/failure rates
- [ ] Set up alerts for high failure rates

### Redis Integration (Recommended)

```python
# Replace in-memory storage with Redis
import redis

class MongoDBAuthManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
    
    def generate_email_otp(self, email: str) -> str:
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Store in Redis with expiration
        key = f"email_otp:{email}"
        self.redis_client.setex(
            key,
            timedelta(minutes=10),
            json.dumps({
                'otp': otp,
                'attempts': 0
            })
        )
        
        return otp
```

## API Integration Examples

### Python

```python
import requests

# Verify email
response = requests.post(
    'http://localhost:5000/api/auth/email/verify',
    json={
        'email': 'user@example.com',
        'otp': '123456'
    }
)

if response.status_code == 200:
    print("Email verified successfully!")
else:
    print(f"Error: {response.json()['error']}")
```

### JavaScript/React

```javascript
// Verify email
const verifyEmail = async (email, otp) => {
  try {
    const response = await fetch('http://localhost:5000/api/auth/email/verify', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, otp }),
    });

    const data = await response.json();

    if (response.ok) {
      console.log('Email verified!');
      return true;
    } else {
      console.error('Verification failed:', data.error);
      return false;
    }
  } catch (error) {
    console.error('Network error:', error);
    return false;
  }
};
```

### cURL

```bash
# Verify email
curl -X POST http://localhost:5000/api/auth/email/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","otp":"123456"}'

# Resend verification
curl -X POST http://localhost:5000/api/auth/email/resend \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com"}'

# Check status
curl http://localhost:5000/api/auth/email/status/user@example.com
```

## Future Enhancements

### Planned Features
- [ ] SMS verification as alternative to email
- [ ] Magic link verification (passwordless)
- [ ] Verification reminder emails
- [ ] Admin dashboard for verification analytics
- [ ] Bulk verification status export
- [ ] Custom email templates per organization
- [ ] Multi-language email support
- [ ] Verification badges/achievements

### Performance Optimizations
- [ ] Redis caching for OTP storage
- [ ] Email queue with retry mechanism
- [ ] Batch email sending
- [ ] CDN for email assets
- [ ] Email template caching

## Support

For issues or questions:
- Check troubleshooting section above
- Review test suite for examples
- Contact system administrator
- Submit issue on project repository

---

**Last Updated:** 2025-09-30  
**Version:** 1.0.0  
**Author:** SOC Dashboard Team
