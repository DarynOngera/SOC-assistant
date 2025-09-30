# Enhanced Authentication Guide

## Overview

The SOC Dashboard now supports three advanced authentication methods:

1. **TOTP/Google Authenticator** - Time-based One-Time Password (already implemented)
2. **Email OTP** - Passwordless login via email verification codes
3. **Passkey/WebAuthn** - Biometric and hardware key authentication

## Features

### 1. TOTP/Google Authenticator MFA

Multi-factor authentication using time-based one-time passwords compatible with Google Authenticator, Authy, and other TOTP apps.

**Setup Flow:**
1. User enables MFA in their profile
2. System generates QR code and secret key
3. User scans QR code with authenticator app
4. User verifies with 6-digit code to activate MFA
5. Future logins require password + TOTP code

**API Endpoints:**
- `POST /api/auth/mfa/setup` - Initialize MFA setup (returns QR code)
- `POST /api/auth/mfa/enable` - Enable MFA after verification
- `POST /api/auth/mfa/disable` - Disable MFA for user

### 2. Email OTP (Passwordless Login)

Secure passwordless authentication using one-time codes sent via email.

**Features:**
- 6-digit numeric OTP
- 10-minute expiry
- Maximum 3 verification attempts
- Email enumeration protection
- Development mode (prints OTP to console)
- Production mode (sends via SMTP)

**Setup Flow:**
1. User enters email address
2. System generates and sends OTP
3. User enters OTP within 10 minutes
4. System authenticates and issues JWT tokens

**API Endpoints:**
- `POST /api/auth/passwordless/request` - Request OTP via email
  ```json
  {
    "email": "user@example.com"
  }
  ```

- `POST /api/auth/passwordless/verify` - Verify OTP and authenticate
  ```json
  {
    "email": "user@example.com",
    "otp": "123456"
  }
  ```

**Environment Variables:**
```bash
# Email Configuration (optional, uses dev mode if not set)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@soc.local
```

### 3. Passkey/WebAuthn Authentication

Modern biometric and hardware key authentication using WebAuthn standard.

**Features:**
- Biometric authentication (Face ID, Touch ID, Windows Hello)
- Hardware security keys (YubiKey, etc.)
- Phishing-resistant authentication
- Multiple passkeys per user
- Platform and cross-platform authenticators

**Registration Flow:**
1. User logs in with password
2. User initiates passkey registration
3. Browser prompts for biometric/security key
4. System stores public key credential
5. User can name and manage passkeys

**Authentication Flow:**
1. User enters username
2. System checks for registered passkeys
3. Browser prompts for biometric/security key
4. System verifies signature and issues tokens

**API Endpoints:**

**Registration:**
- `POST /api/auth/passkey/register/begin` - Start passkey registration (requires auth)
  ```json
  Response: {
    "options": { /* WebAuthn credential creation options */ },
    "state_id": "unique-session-id"
  }
  ```

- `POST /api/auth/passkey/register/complete` - Complete passkey registration
  ```json
  {
    "state_id": "unique-session-id",
    "credential": { /* WebAuthn credential response */ }
  }
  ```

**Authentication:**
- `POST /api/auth/passkey/authenticate/begin` - Start passkey authentication
  ```json
  {
    "username": "user123"
  }
  Response: {
    "options": { /* WebAuthn credential request options */ },
    "state_id": "unique-session-id"
  }
  ```

- `POST /api/auth/passkey/authenticate/complete` - Complete passkey authentication
  ```json
  {
    "state_id": "unique-session-id",
    "credential": { /* WebAuthn assertion response */ }
  }
  ```

**Management:**
- `GET /api/auth/passkey/list` - List user's registered passkeys
- `DELETE /api/auth/passkey/<credential_id>` - Delete a passkey

**Environment Variables:**
```bash
# WebAuthn Configuration
RP_ID=localhost  # Your domain (e.g., soc.example.com)
```

## Security Features

### Rate Limiting
- Login attempts: 5 per minute
- Passwordless requests: 3 per minute
- Passkey operations: 10 per minute

### Account Protection
- Account lockout after 5 failed password attempts (30 minutes)
- OTP expiry after 10 minutes
- Maximum 3 OTP verification attempts
- Session state expiry (5 minutes for passkey flows)

### Privacy Protection
- Email enumeration protection (always returns success message)
- Secure credential storage (hashed passwords, encrypted keys)
- No sensitive data in JWT tokens

## Implementation Details

### Backend Files Modified

1. **`src/auth/auth_utils.py`** - File-based auth manager
   - Added email OTP methods
   - Added passkey/WebAuthn methods
   - Enhanced user schema with passkey storage

2. **`src/auth/mongodb_auth_utils.py`** - MongoDB auth manager
   - Same enhancements as auth_utils.py
   - Uses MongoDB for user storage
   - Supports `get_user_by_email()` method

3. **`src/dashboard/server.py`** - API endpoints
   - Added 8 new authentication endpoints
   - Integrated with existing auth flow
   - Proper error handling and logging

### User Schema Updates

```python
{
  "username": "user123",
  "password_hash": "bcrypt_hash",
  "email": "user@example.com",
  "role": "analyst",
  "mfa_enabled": False,
  "mfa_secret": None,
  "passkeys": [
    {
      "credential_id": "base64_encoded_id",
      "credential_data": "base64_encoded_credential",
      "name": "Passkey 1",
      "created_at": "2025-09-30T02:00:00"
    }
  ],
  "email_verified": False,
  "active": True,
  "failed_attempts": 0,
  "locked_until": None,
  "created_at": "2025-09-30T01:00:00",
  "last_login": "2025-09-30T02:00:00"
}
```

## Frontend Integration

### Email OTP Example

```javascript
// Request OTP
const requestOTP = async (email) => {
  const response = await fetch('/api/auth/passwordless/request', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  const data = await response.json();
  console.log(data.message); // "If this email is registered..."
};

// Verify OTP
const verifyOTP = async (email, otp) => {
  const response = await fetch('/api/auth/passwordless/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, otp })
  });
  const data = await response.json();
  if (response.ok) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  }
};
```

### Passkey Registration Example

```javascript
// Begin registration
const registerPasskey = async () => {
  const token = localStorage.getItem('access_token');
  
  // Step 1: Get registration options
  const beginResponse = await fetch('/api/auth/passkey/register/begin', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  const { options, state_id } = await beginResponse.json();
  
  // Step 2: Create credential with WebAuthn API
  const publicKey = {
    ...options.publicKey,
    challenge: Uint8Array.from(atob(options.publicKey.challenge), c => c.charCodeAt(0)),
    user: {
      ...options.publicKey.user,
      id: Uint8Array.from(atob(options.publicKey.user.id), c => c.charCodeAt(0))
    }
  };
  
  const credential = await navigator.credentials.create({ publicKey });
  
  // Step 3: Complete registration
  const completeResponse = await fetch('/api/auth/passkey/register/complete', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      state_id,
      credential: {
        id: credential.id,
        rawId: btoa(String.fromCharCode(...new Uint8Array(credential.rawId))),
        type: credential.type,
        response: {
          clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(credential.response.clientDataJSON))),
          attestationObject: btoa(String.fromCharCode(...new Uint8Array(credential.response.attestationObject)))
        }
      }
    })
  });
  
  const result = await completeResponse.json();
  console.log(result.message); // "Passkey registered successfully"
};
```

### Passkey Authentication Example

```javascript
// Authenticate with passkey
const authenticateWithPasskey = async (username) => {
  // Step 1: Begin authentication
  const beginResponse = await fetch('/api/auth/passkey/authenticate/begin', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username })
  });
  const { options, state_id } = await beginResponse.json();
  
  // Step 2: Get assertion with WebAuthn API
  const publicKey = {
    ...options.publicKey,
    challenge: Uint8Array.from(atob(options.publicKey.challenge), c => c.charCodeAt(0)),
    allowCredentials: options.publicKey.allowCredentials.map(cred => ({
      ...cred,
      id: Uint8Array.from(atob(cred.id), c => c.charCodeAt(0))
    }))
  };
  
  const assertion = await navigator.credentials.get({ publicKey });
  
  // Step 3: Complete authentication
  const completeResponse = await fetch('/api/auth/passkey/authenticate/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      state_id,
      credential: {
        id: assertion.id,
        rawId: btoa(String.fromCharCode(...new Uint8Array(assertion.rawId))),
        type: assertion.type,
        response: {
          clientDataJSON: btoa(String.fromCharCode(...new Uint8Array(assertion.response.clientDataJSON))),
          authenticatorData: btoa(String.fromCharCode(...new Uint8Array(assertion.response.authenticatorData))),
          signature: btoa(String.fromCharCode(...new Uint8Array(assertion.response.signature))),
          userHandle: assertion.response.userHandle ? btoa(String.fromCharCode(...new Uint8Array(assertion.response.userHandle))) : null
        }
      }
    })
  });
  
  const data = await completeResponse.json();
  if (completeResponse.ok) {
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
  }
};
```

## Testing

### Manual Testing

1. **Email OTP (Development Mode):**
   ```bash
   # Start server
   python src/dashboard/server.py
   
   # Request OTP (check console for OTP code)
   curl -X POST http://localhost:5000/api/auth/passwordless/request \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@soc.local"}'
   
   # Verify OTP
   curl -X POST http://localhost:5000/api/auth/passwordless/verify \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@soc.local","otp":"123456"}'
   ```

2. **Passkey Authentication:**
   - Requires HTTPS and browser support
   - Test in Chrome/Edge/Safari with WebAuthn support
   - Use localhost or proper domain with SSL certificate

### Automated Testing

```bash
# Run test suite
python test_enhanced_auth.py
```

## Production Deployment

### Prerequisites

1. **SSL Certificate** - Required for WebAuthn
2. **SMTP Server** - For email OTP (or use dev mode)
3. **Domain Name** - Set RP_ID to your domain

### Environment Setup

```bash
# .env file
JWT_SECRET_KEY=your-secret-key-change-in-production
FLASK_SECRET_KEY=another-secret-key

# Email OTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com

# WebAuthn
RP_ID=yourdomain.com

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=soc_dashboard
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fido2, pyotp, qrcode; print('✓ All packages installed')"
```

## Troubleshooting

### Email OTP Issues

**Problem:** OTP not received
- Check SMTP credentials
- Verify email server allows app passwords
- Check spam folder
- Use dev mode for testing (OTP printed to console)

**Problem:** OTP expired
- OTPs expire after 10 minutes
- Request new OTP

### Passkey Issues

**Problem:** WebAuthn not available
- Requires HTTPS (except localhost)
- Browser must support WebAuthn API
- Check browser compatibility

**Problem:** Registration fails
- Ensure user is authenticated
- Check browser console for errors
- Verify RP_ID matches domain

**Problem:** Authentication fails
- Ensure passkey was registered successfully
- Try different authenticator
- Check credential hasn't been deleted

## Browser Compatibility

### WebAuthn Support

| Browser | Version | Platform Auth | USB Keys |
|---------|---------|---------------|----------|
| Chrome  | 67+     | ✓             | ✓        |
| Edge    | 18+     | ✓             | ✓        |
| Firefox | 60+     | ✓             | ✓        |
| Safari  | 13+     | ✓             | ✓        |

### Recommended Setup

- **Desktop:** Windows Hello, Touch ID, YubiKey
- **Mobile:** Face ID, Touch ID, Fingerprint
- **Cross-platform:** YubiKey, Google Titan

## Security Best Practices

1. **Always use HTTPS in production**
2. **Set strong JWT_SECRET_KEY**
3. **Enable rate limiting**
4. **Monitor failed authentication attempts**
5. **Regularly audit passkey usage**
6. **Use Redis for OTP storage in production** (current: in-memory)
7. **Implement proper session management**
8. **Log all authentication events**

## Future Enhancements

- [ ] Redis integration for OTP storage
- [ ] SMS OTP support
- [ ] Backup codes for MFA
- [ ] Passkey sync across devices
- [ ] Authentication analytics dashboard
- [ ] Risk-based authentication
- [ ] Device fingerprinting
- [ ] Biometric consent management

## Support

For issues or questions:
- Check logs: `src/dashboard/server.py` logging output
- Review audit logs: `/api/admin/audit`
- Test with: `python test_enhanced_auth.py`

## References

- [WebAuthn Specification](https://www.w3.org/TR/webauthn/)
- [FIDO2 Python Library](https://github.com/Yubico/python-fido2)
- [TOTP RFC 6238](https://tools.ietf.org/html/rfc6238)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
