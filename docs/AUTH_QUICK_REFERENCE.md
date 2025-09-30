# Authentication Quick Reference

## Installation

```bash
pip install fido2 webauthn cryptography pyotp qrcode
```

## Environment Variables

```bash
# Required
JWT_SECRET_KEY=your-secret-key-here
FLASK_SECRET_KEY=another-secret-key

# Email OTP (optional - uses dev mode if not set)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@soc.local

# WebAuthn (required for production)
RP_ID=localhost  # Change to your domain in production
```

## API Endpoints Summary

### Standard Authentication
```bash
POST /api/auth/login
POST /api/auth/refresh
POST /api/auth/logout
POST /api/auth/change-password
```

### TOTP/MFA
```bash
POST /api/auth/mfa/setup      # Get QR code
POST /api/auth/mfa/enable     # Activate MFA
POST /api/auth/mfa/disable    # Deactivate MFA
```

### Email OTP (Passwordless)
```bash
POST /api/auth/passwordless/request   # Request OTP
POST /api/auth/passwordless/verify    # Verify OTP & login
```

### Passkey/WebAuthn
```bash
# Registration (requires auth)
POST /api/auth/passkey/register/begin
POST /api/auth/passkey/register/complete

# Authentication
POST /api/auth/passkey/authenticate/begin
POST /api/auth/passkey/authenticate/complete

# Management
GET  /api/auth/passkey/list
DELETE /api/auth/passkey/<credential_id>
```

## Quick Examples

### Email OTP Login

```javascript
// 1. Request OTP
await fetch('/api/auth/passwordless/request', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' })
});

// 2. Verify OTP (check console in dev mode)
const response = await fetch('/api/auth/passwordless/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    email: 'user@example.com',
    otp: '123456'
  })
});
const { access_token, refresh_token } = await response.json();
```

### Passkey Registration

```javascript
// Helper function to convert base64 to Uint8Array
const base64ToUint8Array = (base64) => 
  Uint8Array.from(atob(base64), c => c.charCodeAt(0));

// Helper function to convert Uint8Array to base64
const uint8ArrayToBase64 = (buffer) => 
  btoa(String.fromCharCode(...new Uint8Array(buffer)));

// 1. Begin registration
const beginRes = await fetch('/api/auth/passkey/register/begin', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
const { options, state_id } = await beginRes.json();

// 2. Convert options for WebAuthn API
const publicKey = {
  ...options.publicKey,
  challenge: base64ToUint8Array(options.publicKey.challenge),
  user: {
    ...options.publicKey.user,
    id: base64ToUint8Array(options.publicKey.user.id)
  }
};

// 3. Create credential
const credential = await navigator.credentials.create({ publicKey });

// 4. Complete registration
await fetch('/api/auth/passkey/register/complete', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    state_id,
    credential: {
      id: credential.id,
      rawId: uint8ArrayToBase64(credential.rawId),
      type: credential.type,
      response: {
        clientDataJSON: uint8ArrayToBase64(credential.response.clientDataJSON),
        attestationObject: uint8ArrayToBase64(credential.response.attestationObject)
      }
    }
  })
});
```

### Passkey Authentication

```javascript
// 1. Begin authentication
const beginRes = await fetch('/api/auth/passkey/authenticate/begin', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user123' })
});
const { options, state_id } = await beginRes.json();

// 2. Convert options
const publicKey = {
  ...options.publicKey,
  challenge: base64ToUint8Array(options.publicKey.challenge),
  allowCredentials: options.publicKey.allowCredentials.map(cred => ({
    ...cred,
    id: base64ToUint8Array(cred.id)
  }))
};

// 3. Get assertion
const assertion = await navigator.credentials.get({ publicKey });

// 4. Complete authentication
const completeRes = await fetch('/api/auth/passkey/authenticate/complete', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    state_id,
    credential: {
      id: assertion.id,
      rawId: uint8ArrayToBase64(assertion.rawId),
      type: assertion.type,
      response: {
        clientDataJSON: uint8ArrayToBase64(assertion.response.clientDataJSON),
        authenticatorData: uint8ArrayToBase64(assertion.response.authenticatorData),
        signature: uint8ArrayToBase64(assertion.response.signature),
        userHandle: assertion.response.userHandle ? 
          uint8ArrayToBase64(assertion.response.userHandle) : null
      }
    }
  })
});
const { access_token, refresh_token } = await completeRes.json();
```

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/api/auth/login` | 5/min |
| `/api/auth/passwordless/request` | 3/min |
| `/api/auth/passwordless/verify` | 5/min |
| `/api/auth/passkey/*` | 10/min |

## Security Features

- ✓ Bcrypt password hashing
- ✓ JWT token authentication (8-hour expiry)
- ✓ Refresh tokens (7-day expiry)
- ✓ Account lockout (5 failed attempts, 30-min lock)
- ✓ OTP expiry (10 minutes)
- ✓ Rate limiting on all endpoints
- ✓ Email enumeration protection
- ✓ Audit logging

## Testing

```bash
# Run test suite
python test_enhanced_auth.py

# Test email OTP (dev mode)
curl -X POST http://localhost:5000/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@soc.local"}'

# Check console for OTP, then verify
curl -X POST http://localhost:5000/api/auth/passwordless/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@soc.local","otp":"123456"}'
```

## Troubleshooting

### Email OTP not working
- Check SMTP credentials in environment variables
- In dev mode, OTP is printed to console
- Verify email exists in database

### Passkey not working
- Requires HTTPS (except localhost)
- Check browser supports WebAuthn
- Verify RP_ID matches domain
- Check browser console for errors

### Token expired
- Use refresh token to get new access token
- POST to `/api/auth/refresh` with `refresh_token`

## Browser Support

| Feature | Chrome | Firefox | Safari | Edge |
|---------|--------|---------|--------|------|
| Email OTP | ✓ | ✓ | ✓ | ✓ |
| TOTP | ✓ | ✓ | ✓ | ✓ |
| Passkey | 67+ | 60+ | 13+ | 18+ |

## Production Checklist

- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure SMTP for email OTP
- [ ] Set RP_ID to your domain
- [ ] Enable HTTPS/SSL
- [ ] Configure rate limiting
- [ ] Set up Redis for OTP storage (recommended)
- [ ] Enable audit logging
- [ ] Test all authentication flows
- [ ] Document recovery procedures

## Files Modified

- `src/auth/auth_utils.py` - File-based auth manager
- `src/auth/mongodb_auth_utils.py` - MongoDB auth manager
- `src/dashboard/server.py` - API endpoints
- `requirements.txt` - Dependencies

## Default Admin Account

```
Username: admin
Password: SecureAdmin123!
Email: admin@soc.local
```

**⚠️ Change default password immediately in production!**
