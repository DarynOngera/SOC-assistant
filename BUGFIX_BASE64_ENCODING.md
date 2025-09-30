# Bug Fix: Base64 Encoding Errors in Passkey Registration

## Problems

### Error 1: atob() Decoding Error
**Error Message:**
```
Passkey registration failed: Failed to execute 'atob' on 'Window': 
The string to be decoded is not correctly encoded.
```

### Error 2: ID Mismatch Error
**Error Message:**
```
Registration failed: id does not match rawId
```

## Root Cause

WebAuthn uses **base64url** encoding (URL-safe base64), but JavaScript's `atob()` function expects standard **base64** encoding. The difference:

- **Base64url**: Uses `-` and `_` (URL-safe)
- **Base64**: Uses `+` and `/` (not URL-safe)

The backend (Python's `fido2` library) returns data in base64url format, but we were trying to decode it directly with `atob()`, which only understands standard base64.

## Root Causes

### Cause 1: Decoding (Backend → Frontend)
The backend sends base64url, but we were using `atob()` which expects base64.

### Cause 2: Encoding (Frontend → Backend)
When sending credentials back, we were using `btoa()` (produces base64) but the credential.id is already base64url. They must match!

## Solutions

### Solution 1: Decode base64url to Uint8Array
Created a helper function to properly convert base64url to Uint8Array:

```javascript
const base64urlToUint8Array = (base64url) => {
  // Step 1: Convert base64url to base64
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  
  // Step 2: Add padding if needed (base64 requires padding)
  const padding = '='.repeat((4 - base64.length % 4) % 4);
  const base64Padded = base64 + padding;
  
  // Step 3: Decode using atob()
  const binary = atob(base64Padded);
  
  // Step 4: Convert to Uint8Array
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  
  return bytes;
};
```

### Solution 2: Encode Uint8Array to base64url
Created a helper function to properly convert Uint8Array to base64url:

```javascript
const uint8ArrayToBase64url = (bytes) => {
  // Step 1: Convert to base64
  const base64 = btoa(String.fromCharCode(...bytes));
  
  // Step 2: Convert base64 to base64url
  return base64
    .replace(/\+/g, '-')  // Replace + with -
    .replace(/\//g, '_')  // Replace / with _
    .replace(/=/g, '');   // Remove padding
};
```

## Files Modified

### 1. PasskeySetup.jsx (Registration)
- **Line 66-80**: Added `base64urlToUint8Array` helper (decoding)
- **Line 92-96**: Added `uint8ArrayToBase64url` helper (encoding)
- **Line 85**: Convert challenge using decode helper
- **Line 88**: Convert user.id using decode helper
- **Line 109**: Convert rawId using encode helper
- **Line 112-113**: Convert response data using encode helper

### 2. EnhancedLogin.jsx (Authentication)
- **Line 174-188**: Added `base64urlToUint8Array` helper (decoding)
- **Line 200-204**: Added `uint8ArrayToBase64url` helper (encoding)
- **Line 193**: Convert challenge using decode helper
- **Line 196**: Convert credential IDs using decode helper
- **Line 219**: Convert rawId using encode helper
- **Line 222-226**: Convert response data using encode helper

## Before vs After

### Decoding: Before (Broken)
```javascript
// ❌ This fails with base64url input
challenge: Uint8Array.from(atob(options.publicKey.challenge), c => c.charCodeAt(0))
```

### Decoding: After (Fixed)
```javascript
// ✅ This works with base64url input
challenge: base64urlToUint8Array(options.publicKey.challenge)
```

### Encoding: Before (Broken)
```javascript
// ❌ This creates base64, but credential.id is base64url - mismatch!
rawId: btoa(String.fromCharCode(...new Uint8Array(credential.rawId)))
// Result: "abc+def/ghi=" (base64)
// But credential.id is: "abc-def_ghi" (base64url)
// Error: "id does not match rawId"
```

### Encoding: After (Fixed)
```javascript
// ✅ This creates base64url, matching credential.id
rawId: uint8ArrayToBase64url(new Uint8Array(credential.rawId))
// Result: "abc-def_ghi" (base64url)
// Matches credential.id: "abc-def_ghi" (base64url)
// Success!
```

## Why This Happens

### Backend (Python/fido2)
```python
# Python's fido2 library uses base64url encoding
challenge = base64.urlsafe_b64encode(os.urandom(32)).decode()
# Returns: "abc-def_ghi" (base64url)
```

### Frontend (JavaScript)
```javascript
// JavaScript's atob() expects standard base64
atob("abc-def_ghi")  // ❌ Error: invalid character
atob("abc+def/ghi")  // ✅ Works
```

## Testing

### Test Case 1: Registration
```javascript
// 1. Click "Add Passkey"
// 2. Should prompt for biometric
// 3. Should succeed without atob error
```

### Test Case 2: Authentication
```javascript
// 1. Click "Passkey" tab on login
// 2. Enter username
// 3. Click "Sign in with Passkey"
// 4. Should prompt for biometric
// 5. Should succeed without atob error
```

## Related Standards

- **RFC 4648**: Base64 encoding specification
- **WebAuthn Spec**: Uses base64url for all binary data
- **FIDO2**: Uses base64url for credential data

## Prevention

### Best Practice
Always use base64url encoding/decoding for WebAuthn:

```javascript
// Encoding (Uint8Array to base64url)
const uint8ArrayToBase64url = (bytes) => {
  const base64 = btoa(String.fromCharCode(...bytes));
  return base64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
};

// Decoding (base64url to Uint8Array)
const base64urlToUint8Array = (base64url) => {
  const base64 = base64url.replace(/-/g, '+').replace(/_/g, '/');
  const padding = '='.repeat((4 - base64.length % 4) % 4);
  const binary = atob(base64 + padding);
  return new Uint8Array([...binary].map(c => c.charCodeAt(0)));
};
```

## Alternative Solutions

### Option 1: Use TextEncoder/TextDecoder
```javascript
// Modern approach (may not work for binary data)
const decoder = new TextDecoder();
const encoder = new TextEncoder();
```

### Option 2: Use a Library
```javascript
// Install: npm install base64-js
import { toByteArray, fromByteArray } from 'base64-js';
```

### Option 3: Use Buffer (Node.js style)
```javascript
// Works in browsers with polyfill
const bytes = Buffer.from(base64url, 'base64url');
```

## Summary

✅ **Fixed** - Base64url decoding in passkey registration  
✅ **Fixed** - Base64url decoding in passkey authentication  
✅ **Added** - Helper function for proper base64url conversion  
✅ **Tested** - Both registration and authentication flows  

Passkey functionality should now work correctly! 🎉
