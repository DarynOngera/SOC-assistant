# Authentication Setup Guide

This guide covers setting up all authentication methods for the SOC Dashboard: password-based login, Multi-Factor Authentication (MFA), Email OTP, and Passkey authentication.

## Table of Contents
1. [Environment Configuration](#environment-configuration)
2. [Email Server Setup](#email-server-setup)
3. [Passkey/WebAuthn Setup](#passkeywebauthn-setup)
4. [MFA Setup](#mfa-setup)
5. [Testing Authentication](#testing-authentication)
6. [Troubleshooting](#troubleshooting)

---

## Environment Configuration

### 1. Create Environment File

Copy the example environment file:
```bash
cp .env.example .env
```

### 2. Configure Required Variables

Edit `.env` and set the following:

```bash
# Flask & JWT - Generate strong random keys
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# MongoDB
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=soc_dashboard

# Email (see Email Server Setup section)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@soc-dashboard.local

# WebAuthn/Passkey
RP_ID=localhost  # Change to your domain in production
RP_NAME=SOC Dashboard
```

---

## Email Server Setup

Email OTP authentication requires an SMTP server. Here are setup instructions for common providers:

### Option 1: Gmail (Recommended for Development)

#### Prerequisites
- Gmail account with 2-Factor Authentication enabled

#### Steps

1. **Enable 2-Factor Authentication**
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Name it "SOC Dashboard"
   - Copy the 16-character password

3. **Configure .env**
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # The 16-char app password
   SMTP_FROM=your-email@gmail.com
   ```

### Option 2: Microsoft Outlook/Office 365

```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your-email@outlook.com
SMTP_PASSWORD=your-password
SMTP_FROM=your-email@outlook.com
```

### Option 3: Custom SMTP Server

```bash
SMTP_SERVER=mail.your-domain.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USERNAME=noreply@your-domain.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@your-domain.com
```

### Option 4: Development/Testing (Mailtrap)

For testing without sending real emails:

1. Sign up at https://mailtrap.io
2. Get your SMTP credentials
3. Configure:
   ```bash
   SMTP_SERVER=smtp.mailtrap.io
   SMTP_PORT=2525
   SMTP_USERNAME=your-mailtrap-username
   SMTP_PASSWORD=your-mailtrap-password
   SMTP_FROM=test@soc-dashboard.local
   ```

### Testing Email Configuration

Run this Python script to test your email setup:

```python
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

def test_email():
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_from = os.getenv('SMTP_FROM')
    
    msg = MIMEText('This is a test email from SOC Dashboard')
    msg['Subject'] = 'SOC Dashboard - Email Test'
    msg['From'] = smtp_from
    msg['To'] = smtp_username  # Send to yourself
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        print("✓ Email sent successfully!")
        return True
    except Exception as e:
        print(f"✗ Email failed: {e}")
        return False

if __name__ == '__main__':
    test_email()
```

Save as `test_email.py` and run:
```bash
python test_email.py
```

---

## Passkey/WebAuthn Setup

Passkeys use the WebAuthn standard for passwordless authentication using biometrics or security keys.

### Requirements

#### Browser Support
- **Chrome/Edge**: Version 109+ (recommended)
- **Safari**: Version 16+
- **Firefox**: Version 119+

#### Device Support
- **Windows**: Windows Hello (fingerprint, face, PIN)
- **macOS**: Touch ID or password
- **iOS/iPadOS**: Face ID or Touch ID
- **Android**: Fingerprint, face unlock, or PIN
- **Hardware Keys**: YubiKey, Titan Security Key, etc.

### Configuration

1. **Development (localhost)**
   ```bash
   RP_ID=localhost
   RP_NAME=SOC Dashboard
   ```

2. **Production**
   ```bash
   RP_ID=your-domain.com  # WITHOUT https://
   RP_NAME=SOC Dashboard
   ```

   **Important**: The RP_ID must match your domain. For example:
   - ✓ Correct: `soc.company.com`
   - ✗ Wrong: `https://soc.company.com`
   - ✗ Wrong: `soc.company.com:5000`

### HTTPS Requirement

**Passkeys require HTTPS in production!**

- Development: Works on `localhost` without HTTPS
- Production: Must use HTTPS with valid SSL certificate

### Setting Up HTTPS for Production

#### Option 1: Let's Encrypt (Free)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo certbot renew --dry-run
```

#### Option 2: Reverse Proxy with Nginx

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Registering a Passkey

1. **Log in** with username/password
2. Go to **Settings** → **Security Settings**
3. Click **"Add Passkey"** in the Passkey Authentication section
4. Follow your device's prompts:
   - **Windows**: Use Windows Hello (fingerprint, face, or PIN)
   - **macOS**: Use Touch ID or password
   - **Mobile**: Use Face ID, Touch ID, or fingerprint
   - **Security Key**: Insert and touch your hardware key

5. Your passkey is now registered!

### Using a Passkey to Log In

1. On the login page, click the **"Passkey"** tab
2. Enter your **username**
3. Click **"Sign in with Passkey"**
4. Authenticate with your device (fingerprint, face, etc.)
5. You're logged in!

---

## MFA Setup

Multi-Factor Authentication adds an extra layer of security using time-based one-time passwords (TOTP).

### Requirements

- **Mobile Device** with one of:
  - Google Authenticator (iOS/Android)
  - Microsoft Authenticator (iOS/Android)
  - Authy (iOS/Android)
  - Any TOTP-compatible app

### Setting Up MFA

1. **Log in** to your account
2. Go to **Settings** → **Security Settings**
3. In the **Multi-Factor Authentication Setup** section:
   - Click **"Start MFA Setup"**
   - Scan the QR code with your authenticator app
   - Or manually enter the secret key
4. Enter the 6-digit code from your app
5. Click **"Verify & Enable"**
6. MFA is now active!

### Logging In with MFA

1. Enter your **username** and **password**
2. Enter the **6-digit code** from your authenticator app
3. Click **"Sign in"**

### Backup Codes

**Important**: If you lose access to your authenticator app, contact your administrator to disable MFA.

---

## Testing Authentication

### 1. Test Password Login

```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "SecureAdmin123!"}'
```

Expected response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "username": "admin",
    "role": "admin",
    "email": "admin@soc.local"
  }
}
```

### 2. Test Email OTP

```bash
# Request OTP
curl -X POST http://localhost:5000/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@soc.local"}'

# Check your email for the 6-digit code, then verify:
curl -X POST http://localhost:5000/api/auth/passwordless/verify \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@soc.local", "otp": "123456"}'
```

### 3. Test Passkey (Browser Only)

Passkeys require browser interaction and cannot be tested with curl. Use the web interface:

1. Open http://localhost:3000
2. Click "Passkey" tab
3. Enter username
4. Click "Sign in with Passkey"

---

## Troubleshooting

### Email Issues

#### "Authentication failed" or "Username and Password not accepted"

**Gmail Users:**
- Ensure 2-Factor Authentication is enabled
- Use an App Password, not your regular password
- Remove spaces from the app password in .env

**Outlook Users:**
- Enable "Less secure app access" if using basic auth
- Or use OAuth2 (requires additional setup)

#### "Connection refused" or "Connection timed out"

- Check SMTP_SERVER and SMTP_PORT are correct
- Verify firewall isn't blocking outbound SMTP
- Try port 465 (SSL) instead of 587 (TLS)

#### Emails not arriving

- Check spam/junk folder
- Verify SMTP_FROM is a valid email address
- Test with Mailtrap.io first

### Passkey Issues

#### "Passkeys are not supported in this browser"

- Update your browser to the latest version
- Use Chrome 109+, Edge 109+, Safari 16+, or Firefox 119+

#### "No passkey found for this account"

- Register a passkey first in Settings
- Ensure you're using the same device/browser where you registered

#### "Authentication cancelled or timed out"

- Try again and complete the biometric prompt quickly
- Check if your device's biometric sensor is working

#### "Invalid or expired authentication session"

- The authentication request expired (30 seconds)
- Start over and complete the process faster

### MFA Issues

#### "Invalid verification code"

- Ensure your device's time is synchronized
- The code changes every 30 seconds - use the current one
- Check you're using the correct account in your authenticator app

#### Lost access to authenticator app

- Contact your administrator to disable MFA
- They can run: `python -c "from src.auth.mongodb_auth_utils import MongoDBAuthManager; auth = MongoDBAuthManager(); auth.dal.update_user('username', {'mfa_enabled': False, 'mfa_secret': None})"`

### General Issues

#### "Token expired" errors

- Access tokens expire after 8 hours
- Refresh tokens expire after 7 days
- Log out and log back in

#### "CORS" errors in browser console

- Ensure backend is running on http://localhost:5000
- Ensure frontend is running on http://localhost:3000
- Check CORS_ORIGINS in .env

---

## Security Best Practices

### For Administrators

1. **Use strong secret keys** - Generate with `secrets.token_hex(32)`
2. **Enable HTTPS in production** - Required for passkeys
3. **Secure your .env file** - Never commit to git
4. **Regular security audits** - Check audit logs regularly
5. **Backup MFA secrets** - Store securely for account recovery

### For Users

1. **Enable MFA** - Adds extra security layer
2. **Use passkeys** - Most secure and convenient
3. **Don't share credentials** - Each user should have their own account
4. **Log out on shared devices** - Especially important for passkeys
5. **Report suspicious activity** - Contact your administrator immediately

---

## Additional Resources

- [WebAuthn Guide](https://webauthn.guide/)
- [FIDO Alliance](https://fidoalliance.org/)
- [Google Authenticator](https://support.google.com/accounts/answer/1066447)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

---

## Support

For issues or questions:
1. Check this documentation
2. Review server logs: `logs/soc_dashboard.log`
3. Check browser console for errors (F12)
4. Contact your system administrator
