# Enhanced Authentication Deployment Checklist

## Pre-Deployment

### 1. Dependencies Installation
```bash
# Install required packages
pip install fido2 webauthn cryptography pyotp qrcode

# Verify installation
python -c "import fido2, pyotp, qrcode; print('✓ All packages installed')"
```
- [ ] All dependencies installed successfully
- [ ] No import errors

### 2. Environment Configuration

Create `.env` file in project root:

```bash
# Security (REQUIRED - Change these!)
JWT_SECRET_KEY=your-secret-key-change-in-production-use-32-chars-min
FLASK_SECRET_KEY=another-secret-key-change-in-production-32-chars

# Email OTP (Optional for development, required for production)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@yourdomain.com

# WebAuthn (Required for production)
RP_ID=yourdomain.com  # Use 'localhost' for development

# MongoDB (if using MongoDB backend)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=soc_dashboard
```

- [ ] `.env` file created
- [ ] JWT_SECRET_KEY set (32+ characters)
- [ ] FLASK_SECRET_KEY set (32+ characters)
- [ ] SMTP credentials configured (or dev mode accepted)
- [ ] RP_ID set to correct domain

### 3. Testing

```bash
# Run comprehensive test suite
python test_enhanced_auth.py
```

Expected output:
- [ ] ✓ TOTP/MFA Test - PASSED
- [ ] ✓ Email OTP Test - PASSED
- [ ] ✓ Passkey Flow Test - PASSED
- [ ] ✓ Standard Auth Test - PASSED
- [ ] ✓ Failed Auth Test - PASSED
- [ ] ✓ Account Lockout Test - PASSED

## Development Deployment

### 1. Local Testing
```bash
# Start server
python src/dashboard/server.py
```

- [ ] Server starts without errors
- [ ] MongoDB connection successful (if using MongoDB)
- [ ] Default admin user created

### 2. Test Email OTP (Dev Mode)
```bash
# Request OTP
curl -X POST http://localhost:5000/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@soc.local"}'

# Check console for OTP code
# Verify OTP
curl -X POST http://localhost:5000/api/auth/passwordless/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@soc.local","otp":"XXXXXX"}'
```

- [ ] OTP request successful
- [ ] OTP printed to console
- [ ] OTP verification successful
- [ ] JWT tokens received

### 3. Test Standard Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecureAdmin123!"}'
```

- [ ] Login successful
- [ ] Tokens received
- [ ] User info returned

### 4. Test MFA Setup
```bash
# Get access token from login
TOKEN="your-access-token"

# Setup MFA
curl -X POST http://localhost:5000/api/auth/mfa/setup \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

- [ ] MFA setup returns QR code
- [ ] Secret key returned
- [ ] Can scan with authenticator app

## Production Deployment

### 1. Security Hardening

- [ ] Changed default admin password
- [ ] Set strong JWT_SECRET_KEY (32+ random characters)
- [ ] Set strong FLASK_SECRET_KEY (32+ random characters)
- [ ] Removed or secured test accounts
- [ ] Configured SMTP with app-specific password
- [ ] Enabled HTTPS/SSL certificate
- [ ] Set RP_ID to production domain
- [ ] Configured firewall rules
- [ ] Set up rate limiting (already in code)

### 2. SMTP Configuration

For Gmail:
1. Enable 2-Factor Authentication
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in SMTP_PASSWORD

- [ ] SMTP server accessible
- [ ] Test email sending works
- [ ] Email delivery confirmed
- [ ] SPF/DKIM records configured (optional but recommended)

### 3. SSL/HTTPS Setup

**Required for WebAuthn/Passkey in production!**

```bash
# Example with Let's Encrypt
sudo certbot --nginx -d yourdomain.com
```

- [ ] SSL certificate installed
- [ ] HTTPS enabled
- [ ] HTTP redirects to HTTPS
- [ ] Certificate auto-renewal configured

### 4. Database Setup

If using MongoDB:
```bash
# Create database and user
mongo
> use soc_dashboard
> db.createUser({
    user: "soc_admin",
    pwd: "strong-password",
    roles: ["readWrite"]
  })
```

- [ ] Database created
- [ ] Database user created with limited permissions
- [ ] Connection string updated in .env
- [ ] Indexes created (handled by DAL)
- [ ] Backup strategy in place

### 5. Application Deployment

```bash
# Using systemd service (example)
sudo systemctl start soc-dashboard
sudo systemctl enable soc-dashboard
sudo systemctl status soc-dashboard
```

- [ ] Application starts automatically
- [ ] Logs are being written
- [ ] No errors in logs
- [ ] Health check endpoint responding

### 6. Verification Tests

```bash
# Test from external network
curl https://yourdomain.com/api/health

# Test email OTP
curl -X POST https://yourdomain.com/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{"email":"test@yourdomain.com"}'
```

- [ ] API accessible from internet
- [ ] HTTPS working correctly
- [ ] Email OTP sends actual emails
- [ ] Rate limiting working
- [ ] Audit logs being created

### 7. WebAuthn/Passkey Testing

**Must be done in browser with HTTPS:**

1. Log in to dashboard
2. Navigate to security settings
3. Click "Add Passkey"
4. Follow browser prompts
5. Test authentication with passkey

- [ ] Passkey registration works
- [ ] Biometric prompt appears
- [ ] Passkey saved successfully
- [ ] Can authenticate with passkey
- [ ] Can manage/delete passkeys

## Post-Deployment

### 1. Monitoring Setup

- [ ] Set up log monitoring
- [ ] Configure alerts for failed logins
- [ ] Monitor rate limit violations
- [ ] Track authentication method usage
- [ ] Set up uptime monitoring

### 2. Documentation

- [ ] Update internal documentation
- [ ] Train users on new auth methods
- [ ] Create user guides for MFA setup
- [ ] Document recovery procedures
- [ ] Share admin credentials securely

### 3. Backup & Recovery

- [ ] Database backup configured
- [ ] Backup recovery tested
- [ ] Document recovery procedures
- [ ] Store backup codes for MFA (future enhancement)
- [ ] Test disaster recovery plan

### 4. Security Audit

- [ ] Review audit logs
- [ ] Check for suspicious activity
- [ ] Verify rate limits working
- [ ] Test account lockout
- [ ] Verify email enumeration protection
- [ ] Check token expiration
- [ ] Test session management

## Rollback Plan

If issues occur:

1. **Immediate Actions:**
   ```bash
   # Revert to previous version
   git checkout previous-stable-tag
   pip install -r requirements.txt
   sudo systemctl restart soc-dashboard
   ```

2. **Verify:**
   - [ ] Old authentication still works
   - [ ] No data loss
   - [ ] Users can log in

3. **Investigate:**
   - [ ] Check error logs
   - [ ] Review recent changes
   - [ ] Test in staging environment

## Troubleshooting

### Email OTP Issues

**Problem:** Emails not sending
- Check SMTP credentials
- Verify SMTP server allows connections
- Check firewall rules
- Review email logs
- Test with dev mode first

**Problem:** OTP expired
- OTPs expire after 10 minutes
- Request new OTP
- Check server time synchronization

### Passkey Issues

**Problem:** Registration fails
- Verify HTTPS is enabled
- Check RP_ID matches domain
- Ensure browser supports WebAuthn
- Check browser console for errors

**Problem:** Authentication fails
- Verify passkey was registered successfully
- Check user has passkeys in database
- Try different authenticator
- Clear browser cache

### General Issues

**Problem:** Rate limit errors
- Wait for rate limit window to reset
- Check if legitimate traffic
- Adjust rate limits if needed

**Problem:** Account locked
- Wait 30 minutes for auto-unlock
- Admin can manually unlock via database
- Review failed login attempts

## Success Criteria

Deployment is successful when:

- [ ] All authentication methods working
- [ ] No errors in production logs
- [ ] Users can log in successfully
- [ ] Email OTP delivers within 1 minute
- [ ] Passkeys work on all supported browsers
- [ ] Rate limiting prevents abuse
- [ ] Audit logs capture all events
- [ ] Performance is acceptable (< 500ms response time)
- [ ] Security scan shows no vulnerabilities
- [ ] Backup and recovery tested

## Contact Information

**Support Channels:**
- Technical Lead: [Your contact]
- Security Team: [Security contact]
- DevOps Team: [DevOps contact]

**Documentation:**
- Implementation Guide: `ENHANCED_AUTH_GUIDE.md`
- Quick Reference: `docs/AUTH_QUICK_REFERENCE.md`
- API Documentation: [Link to API docs]

---

## Sign-Off

- [ ] Development Team Lead: _________________ Date: _______
- [ ] Security Review: _________________ Date: _______
- [ ] QA Testing: _________________ Date: _______
- [ ] DevOps Approval: _________________ Date: _______
- [ ] Production Deployment: _________________ Date: _______

**Deployment Status:** ⬜ Ready | ⬜ In Progress | ⬜ Complete | ⬜ Rollback

**Notes:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________
