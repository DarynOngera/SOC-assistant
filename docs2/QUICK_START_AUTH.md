# Quick Start - Authentication Setup

Get your SOC Dashboard authentication up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- MongoDB running
- Node.js 14+ (for frontend)

## Step 1: Install Dependencies

```bash
# Backend dependencies
pip install -r requirements.txt

# Frontend dependencies
cd frontend
npm install
cd ..
```

## Step 2: Run Setup Script

```bash
python scripts/setup_auth.py
```

Choose option 1 (Gmail) for quickest setup, or option 4 (Mailtrap) for testing without real emails.

## Step 3: Start Services

```bash
# Terminal 1: Start MongoDB (if not running)
mongod

# Terminal 2: Start Backend
python src/dashboard/server.py

# Terminal 3: Start Frontend
cd frontend
npm start
```

## Step 4: Access Dashboard

Open http://localhost:3000

**Default Login:**
- Username: `admin`
- Password: `SecureAdmin123!`

## Available Authentication Methods

### 1. Password + MFA (Most Secure)
1. Log in with username/password
2. Go to Settings → Security Settings
3. Set up MFA with Google Authenticator
4. Next login will require 6-digit code

### 2. Email OTP (Passwordless)
1. Click "Email OTP" tab on login
2. Enter your email address
3. Check email for 6-digit code
4. Enter code to log in

### 3. Passkey (Biometric)
1. Log in with password first
2. Go to Settings → Security Settings
3. Click "Add Passkey"
4. Follow device prompts (fingerprint/face)
5. Next time, use "Passkey" tab to log in

## Quick Email Setup

### Gmail (Recommended)

1. **Enable 2FA**: https://myaccount.google.com/security
2. **Get App Password**: https://myaccount.google.com/apppasswords
3. **Run setup script**: `python scripts/setup_auth.py` → Choose option 1
4. **Test**: Send yourself a test email

### Mailtrap (Testing)

1. **Sign up**: https://mailtrap.io (free)
2. **Get credentials**: From inbox settings
3. **Run setup script**: `python scripts/setup_auth.py` → Choose option 4
4. **Test**: Emails appear in Mailtrap inbox (not real email)

## Troubleshooting

### "Email failed to send"
- Gmail: Use App Password, not regular password
- Check spam folder
- Try Mailtrap for testing

### "Passkeys not supported"
- Update browser (Chrome 109+, Safari 16+, Firefox 119+)
- Use HTTPS in production
- localhost works for development

### "MFA code invalid"
- Sync device time
- Code changes every 30 seconds
- Use current code from app

### "Connection refused"
- Check MongoDB is running: `mongod`
- Check backend is running on port 5000
- Check frontend is running on port 3000

## Next Steps

- **Read full docs**: `AUTHENTICATION_SETUP.md`
- **Set up users**: Settings → User Management (admin only)
- **Review audit logs**: Settings → Audit Logs (admin only)
- **Configure alerts**: Dashboard → Threat Analysis

## Security Checklist

- [ ] Changed default admin password
- [ ] Generated new secret keys (`.env`)
- [ ] Enabled MFA for admin account
- [ ] Configured email server
- [ ] Set up HTTPS (production only)
- [ ] Reviewed audit logs regularly

## Support

- **Documentation**: See `AUTHENTICATION_SETUP.md`
- **Logs**: Check `logs/soc_dashboard.log`
- **Browser Console**: Press F12 for errors

---

**Need help?** Check the full documentation or contact your system administrator.
