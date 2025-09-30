# Frontend Integration Guide - Enhanced Authentication

## Overview

This guide explains how to integrate the enhanced authentication features (Email OTP, Passkey, TOTP) into your React frontend.

## Components Created

### 1. EnhancedLogin.jsx
**Location:** `frontend/src/components/EnhancedLogin.jsx`

**Features:**
- Tab-based interface for 3 auth methods
- Password login with MFA support
- Email OTP passwordless login
- Passkey/WebAuthn authentication
- Cybersecurity-themed dark UI
- Responsive design

**Usage:**
```jsx
import EnhancedLogin from './components/EnhancedLogin';

function App() {
  const handleLogin = (user) => {
    console.log('User logged in:', user);
    // Navigate to dashboard
  };

  return <EnhancedLogin onLogin={handleLogin} />;
}
```

### 2. PasskeyManagement.jsx
**Location:** `frontend/src/components/PasskeyManagement.jsx`

**Features:**
- List registered passkeys
- Register new passkeys
- Delete passkeys
- Browser compatibility info
- User-friendly interface

**Usage:**
```jsx
import PasskeyManagement from './components/PasskeyManagement';

function SecuritySettings() {
  return (
    <div>
      <h1>Security Settings</h1>
      <PasskeyManagement />
    </div>
  );
}
```

## Integration Steps

### Step 1: Install Dependencies

Ensure you have the required packages:

```bash
cd frontend
npm install lucide-react
```

### Step 2: Update App.jsx

Replace the existing Login component with EnhancedLogin:

```jsx
// Before
import Login from './components/Login';

// After
import EnhancedLogin from './components/EnhancedLogin';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleLogin = (userData) => {
    setUser(userData);
    // Navigate to dashboard or update state
  };

  if (!user) {
    return <EnhancedLogin onLogin={handleLogin} loading={loading} />;
  }

  return <Dashboard user={user} />;
}
```

### Step 3: Add Passkey Management to Settings

Add PasskeyManagement to your user settings or security page:

```jsx
import PasskeyManagement from './components/PasskeyManagement';
import MFASetup from './components/MFASetup';

function SecuritySettings() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Security Settings</h1>
      
      {/* MFA Setup (existing) */}
      <MFASetup />
      
      {/* Passkey Management (new) */}
      <PasskeyManagement />
    </div>
  );
}
```

### Step 4: Update API Base URL

For production, update the API base URL in both components:

```jsx
// Development
const API_BASE = 'http://localhost:5000';

// Production
const API_BASE = process.env.REACT_APP_API_URL || 'https://yourdomain.com';

// Usage
fetch(`${API_BASE}/api/auth/login`, {...})
```

## API Integration

### Authentication Flow

#### 1. Password Login
```javascript
const response = await fetch('http://localhost:5000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'user123',
    password: 'password',
    mfa_token: '123456' // Optional, if MFA enabled
  })
});

const data = await response.json();
// Store tokens
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

#### 2. Email OTP Login
```javascript
// Step 1: Request OTP
await fetch('http://localhost:5000/api/auth/passwordless/request', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com' })
});

// Step 2: Verify OTP
const response = await fetch('http://localhost:5000/api/auth/passwordless/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    otp: '123456'
  })
});

const data = await response.json();
localStorage.setItem('access_token', data.access_token);
```

#### 3. Passkey Login
```javascript
// Helper functions
const base64ToUint8Array = (base64) => 
  Uint8Array.from(atob(base64), c => c.charCodeAt(0));

const uint8ArrayToBase64 = (buffer) => 
  btoa(String.fromCharCode(...new Uint8Array(buffer)));

// Step 1: Begin authentication
const beginRes = await fetch('http://localhost:5000/api/auth/passkey/authenticate/begin', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: 'user123' })
});

const { options, state_id } = await beginRes.json();

// Step 2: Convert options
const publicKey = {
  ...options.publicKey,
  challenge: base64ToUint8Array(options.publicKey.challenge),
  allowCredentials: options.publicKey.allowCredentials.map(cred => ({
    ...cred,
    id: base64ToUint8Array(cred.id)
  }))
};

// Step 3: Get assertion
const assertion = await navigator.credentials.get({ publicKey });

// Step 4: Complete authentication
const completeRes = await fetch('http://localhost:5000/api/auth/passkey/authenticate/complete', {
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

const data = await completeRes.json();
localStorage.setItem('access_token', data.access_token);
```

## Styling

### Cybersecurity Theme

The components use a dark, cybersecurity-themed design:

**Colors:**
- Background: `bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900`
- Primary: Blue (`bg-blue-600`)
- Accent: Cyan (`bg-cyan-500`)
- Text: White/Gray shades

**Customization:**
```jsx
// Change primary color
className="bg-blue-600" // Change to bg-purple-600, bg-green-600, etc.

// Change gradient
className="from-slate-900 via-blue-900 to-slate-900" 
// Change to from-gray-900 via-purple-900 to-gray-900
```

### Responsive Design

All components are mobile-responsive:
- Flexbox layouts
- Responsive text sizes (`text-sm`, `text-base`, `text-lg`)
- Mobile-friendly buttons and inputs
- Touch-friendly tap targets

## Error Handling

### Common Errors

1. **Network Errors**
```jsx
try {
  const response = await fetch(...);
  if (!response.ok) {
    const data = await response.json();
    setError(data.error || 'Request failed');
  }
} catch (err) {
  setError('Network error. Please check your connection.');
}
```

2. **WebAuthn Errors**
```jsx
try {
  const credential = await navigator.credentials.create({...});
} catch (err) {
  if (err.name === 'NotAllowedError') {
    setError('Authentication cancelled');
  } else if (err.name === 'InvalidStateError') {
    setError('Authenticator already registered');
  } else {
    setError('Authentication failed');
  }
}
```

3. **Token Expiry**
```jsx
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
  }
});

if (response.status === 401) {
  // Token expired, refresh or redirect to login
  const refreshToken = localStorage.getItem('refresh_token');
  // Implement token refresh logic
}
```

## Testing

### Manual Testing Checklist

**Password Login:**
- [ ] Login with valid credentials
- [ ] Login with invalid credentials
- [ ] Login with MFA enabled
- [ ] Password visibility toggle works
- [ ] Error messages display correctly

**Email OTP:**
- [ ] Request OTP with valid email
- [ ] Request OTP with invalid email
- [ ] Verify OTP with correct code
- [ ] Verify OTP with incorrect code
- [ ] OTP expiry handling
- [ ] "Use different email" button works

**Passkey:**
- [ ] Register new passkey
- [ ] Authenticate with passkey
- [ ] List passkeys
- [ ] Delete passkey
- [ ] Browser compatibility check
- [ ] Error handling for unsupported browsers

### Automated Testing

```javascript
// Example Jest test
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import EnhancedLogin from './EnhancedLogin';

test('switches between auth modes', () => {
  render(<EnhancedLogin onLogin={jest.fn()} />);
  
  // Check password tab is active
  expect(screen.getByText('Password')).toHaveClass('bg-blue-600');
  
  // Click Email OTP tab
  fireEvent.click(screen.getByText('Email OTP'));
  
  // Check Email OTP tab is active
  expect(screen.getByText('Email OTP')).toHaveClass('bg-blue-600');
});

test('handles email OTP flow', async () => {
  const mockFetch = jest.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ message: 'OTP sent' })
    })
  );
  global.fetch = mockFetch;

  render(<EnhancedLogin onLogin={jest.fn()} />);
  
  // Switch to Email OTP
  fireEvent.click(screen.getByText('Email OTP'));
  
  // Enter email
  const emailInput = screen.getByPlaceholderText('Email address');
  fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
  
  // Submit
  fireEvent.click(screen.getByText('Send Login Code'));
  
  // Wait for success message
  await waitFor(() => {
    expect(screen.getByText(/Login code sent/)).toBeInTheDocument();
  });
});
```

## Production Deployment

### Environment Variables

Create `.env` file in frontend directory:

```bash
REACT_APP_API_URL=https://api.yourdomain.com
REACT_APP_RP_ID=yourdomain.com
```

### Build for Production

```bash
cd frontend
npm run build
```

### HTTPS Requirement

**Important:** Passkeys require HTTPS in production!

- Development: Works on `localhost` without HTTPS
- Production: Must use HTTPS

### CORS Configuration

Ensure backend allows frontend origin:

```python
# src/dashboard/server.py
CORS(app, origins=[
    "http://localhost:3000",  # Development
    "https://yourdomain.com"   # Production
], supports_credentials=True)
```

## Browser Compatibility

### WebAuthn Support

| Browser | Version | Support |
|---------|---------|---------|
| Chrome | 67+ | ✓ Full |
| Edge | 18+ | ✓ Full |
| Firefox | 60+ | ✓ Full |
| Safari | 13+ | ✓ Full |
| Opera | 54+ | ✓ Full |

### Feature Detection

```javascript
// Check WebAuthn support
if (window.PublicKeyCredential) {
  // Passkeys supported
} else {
  // Show alternative auth method
}

// Check platform authenticator
PublicKeyCredential.isUserVerifyingPlatformAuthenticatorAvailable()
  .then(available => {
    if (available) {
      // Device has biometric auth
    }
  });
```

## Troubleshooting

### Issue: CORS Errors

**Solution:**
```python
# Backend: src/dashboard/server.py
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
```

### Issue: Passkey Registration Fails

**Solutions:**
- Ensure HTTPS (or localhost)
- Check browser console for errors
- Verify RP_ID matches domain
- Try different authenticator

### Issue: Email OTP Not Received

**Solutions:**
- Check spam folder
- Verify SMTP configuration
- Check server console (dev mode)
- Test with different email provider

### Issue: Token Expired

**Solution:**
```javascript
// Implement token refresh
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token');
  const response = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken })
  });
  const data = await response.json();
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
};
```

## Next Steps

1. **Customize Styling** - Match your brand colors
2. **Add Analytics** - Track auth method usage
3. **Implement Remember Me** - Extended session option
4. **Add Social Login** - OAuth integration
5. **Enhanced Security** - Device fingerprinting, risk-based auth

## Support

For issues:
- Check browser console for errors
- Review network tab for API calls
- Test with different browsers
- Consult `ENHANCED_AUTH_GUIDE.md`

---

**Frontend integration complete!** 🎉

Your SOC Dashboard now supports:
- ✅ Password + MFA authentication
- ✅ Email OTP passwordless login
- ✅ Passkey/WebAuthn biometric auth
- ✅ Modern, cybersecurity-themed UI
- ✅ Mobile-responsive design
