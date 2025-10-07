# Email Service Setup Guide for OTP Authentication

## Overview

This guide will help you configure email service for sending OTP (One-Time Password) codes to users for passwordless authentication.

## Supported Email Providers

### 1. Gmail (Recommended for Development)

**Step-by-Step Setup:**

1. **Enable 2-Factor Authentication**
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification

2. **Generate App Password**
   - Visit https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Enter "SOC Dashboard" as the name
   - Click "Generate"
   - Copy the 16-character password (remove spaces)

3. **Configure Environment Variables**
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM=your-email@gmail.com
   ```

**Gmail Limits:**
- Free: 500 emails/day
- Google Workspace: 2,000 emails/day

---

### 2. Microsoft Outlook/Office 365

**Setup:**

1. **Enable SMTP Authentication**
   - Go to Outlook settings
   - Enable "Let devices and apps use POP"

2. **Configure Environment Variables**
   ```bash
   SMTP_SERVER=smtp.office365.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@outlook.com
   SMTP_PASSWORD=your-password
   SMTP_FROM=your-email@outlook.com
   ```

**Outlook Limits:**
- Free: 300 emails/day
- Office 365: 10,000 emails/day

---

### 3. SendGrid (Recommended for Production)

**Setup:**

1. **Create SendGrid Account**
   - Sign up at https://sendgrid.com
   - Verify your email

2. **Create API Key**
   - Go to Settings → API Keys
   - Create API Key with "Mail Send" permission
   - Copy the API key

3. **Configure Environment Variables**
   ```bash
   SMTP_SERVER=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USERNAME=apikey
   SMTP_PASSWORD=your-sendgrid-api-key
   SMTP_FROM=noreply@yourdomain.com
   ```

4. **Verify Sender Identity**
   - Go to Settings → Sender Authentication
   - Verify your domain or single sender email

**SendGrid Limits:**
- Free: 100 emails/day
- Essentials ($19.95/mo): 50,000 emails/month
- Pro ($89.95/mo): 1.5M emails/month

---

### 4. AWS SES (Amazon Simple Email Service)

**Setup:**

1. **Create AWS Account**
   - Sign up at https://aws.amazon.com

2. **Verify Email/Domain**
   - Go to SES Console
   - Verify email addresses or domain

3. **Create SMTP Credentials**
   - Go to SMTP Settings
   - Create SMTP credentials
   - Download credentials

4. **Configure Environment Variables**
   ```bash
   SMTP_SERVER=email-smtp.us-east-1.amazonaws.com
   SMTP_PORT=587
   SMTP_USERNAME=your-smtp-username
   SMTP_PASSWORD=your-smtp-password
   SMTP_FROM=verified@yourdomain.com
   ```

**AWS SES Limits:**
- Sandbox: 200 emails/day (to verified addresses only)
- Production: 50,000 emails/day (request limit increase)

---

### 5. Mailgun

**Setup:**

1. **Create Mailgun Account**
   - Sign up at https://www.mailgun.com

2. **Get SMTP Credentials**
   - Go to Sending → Domain Settings
   - Find SMTP credentials

3. **Configure Environment Variables**
   ```bash
   SMTP_SERVER=smtp.mailgun.org
   SMTP_PORT=587
   SMTP_USERNAME=postmaster@your-domain.mailgun.org
   SMTP_PASSWORD=your-mailgun-password
   SMTP_FROM=noreply@yourdomain.com
   ```

**Mailgun Limits:**
- Free Trial: 5,000 emails/month (3 months)
- Foundation ($35/mo): 50,000 emails/month

---

## Configuration Steps

### 1. Create .env File

Create a `.env` file in your project root:

```bash
# Security Keys
JWT_SECRET_KEY=your-secret-key-32-chars-minimum
FLASK_SECRET_KEY=another-secret-key-32-chars

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@soc.local

# WebAuthn
RP_ID=localhost  # Change to your domain in production

# MongoDB (if using)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=soc_dashboard
```

### 2. Load Environment Variables

The application automatically loads `.env` file. Ensure `python-dotenv` is installed:

```bash
pip install python-dotenv
```

### 3. Test Email Configuration

Run the test script:

```bash
python test_email_otp.py
```

Or test manually:

```python
from src.auth.auth_utils import AuthManager

auth = AuthManager()

# Test email sending
success, message = auth.send_email_otp('test@example.com', '123456')
print(f"Success: {success}, Message: {message}")
```

---

## Email Template Customization

The email template is located in:
- `src/auth/auth_utils.py` (line ~470)
- `src/auth/mongodb_auth_utils.py` (line ~438)

### Current Template Features:
- ✅ Cybersecurity-themed dark design
- ✅ Gradient blue/cyan header
- ✅ Large, prominent OTP code display
- ✅ Security warnings and notices
- ✅ Mobile-responsive design
- ✅ Professional footer with branding

### Customization Options:

1. **Change Colors**
   ```html
   <!-- Header gradient -->
   background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%);
   
   <!-- OTP box gradient -->
   background: linear-gradient(135deg, #1e40af 0%, #0891b2 100%);
   ```

2. **Change Company Name**
   ```html
   <h1>Your Company Name</h1>
   <p>© 2025 Your Company | Security Operations Center</p>
   ```

3. **Add Logo**
   ```html
   <img src="https://yourdomain.com/logo.png" alt="Logo" style="height: 40px;">
   ```

---

## Development Mode

For development/testing without email service:

1. **Leave SMTP credentials empty** in `.env`:
   ```bash
   SMTP_USERNAME=
   SMTP_PASSWORD=
   ```

2. **OTP will be printed to console**:
   ```
   [DEV MODE] Email OTP for user@example.com: 123456
   ```

3. **Check server console** for OTP codes during testing

---

## Production Deployment

### Security Checklist:

- [ ] Use environment variables (never hardcode credentials)
- [ ] Use app-specific passwords (not account passwords)
- [ ] Enable SSL/TLS (port 587 with STARTTLS)
- [ ] Verify sender domain (SPF, DKIM, DMARC records)
- [ ] Monitor email delivery rates
- [ ] Set up bounce/complaint handling
- [ ] Use dedicated email service (SendGrid, AWS SES, etc.)
- [ ] Implement rate limiting (already in code)
- [ ] Log email sending attempts
- [ ] Set up alerts for delivery failures

### DNS Records (for custom domain):

**SPF Record:**
```
v=spf1 include:_spf.google.com ~all
```

**DKIM Record:**
```
(Provided by your email service)
```

**DMARC Record:**
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

---

## Troubleshooting

### Issue: "Authentication failed"

**Solutions:**
- Verify SMTP credentials are correct
- For Gmail: Use app password, not account password
- Check if 2FA is enabled (required for app passwords)
- Verify SMTP server and port are correct

### Issue: "Connection refused"

**Solutions:**
- Check firewall allows outbound connections on port 587
- Verify SMTP server address is correct
- Try alternative ports (465 for SSL, 587 for TLS)

### Issue: "Emails going to spam"

**Solutions:**
- Verify sender domain with SPF/DKIM/DMARC
- Use professional "From" address
- Avoid spam trigger words in subject/body
- Warm up new sending domain gradually
- Use reputable email service provider

### Issue: "Rate limit exceeded"

**Solutions:**
- Upgrade email service plan
- Implement request queuing
- Use Redis for OTP storage (instead of in-memory)
- Monitor and optimize email sending patterns

### Issue: "Emails not arriving"

**Solutions:**
- Check spam/junk folders
- Verify recipient email address
- Check email service logs/dashboard
- Verify sender domain is not blacklisted
- Test with different email providers

---

## Testing

### Manual Testing:

```bash
# 1. Start server
python src/dashboard/server.py

# 2. Request OTP
curl -X POST http://localhost:5000/api/auth/passwordless/request \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com"}'

# 3. Check email or console for OTP

# 4. Verify OTP
curl -X POST http://localhost:5000/api/auth/passwordless/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","otp":"123456"}'
```

### Automated Testing:

```python
# test_email_otp.py
from src.auth.auth_utils import AuthManager

def test_email_otp():
    auth = AuthManager()
    
    # Request OTP
    success, message = auth.request_passwordless_login('test@example.com')
    assert success, f"Failed to request OTP: {message}"
    
    # Get OTP from in-memory storage (dev mode)
    if 'test@example.com' in auth.email_otps:
        otp = auth.email_otps['test@example.com']['otp']
        print(f"OTP: {otp}")
        
        # Verify OTP
        success, message, user_info = auth.authenticate_with_email_otp(
            'test@example.com', 
            otp
        )
        assert success, f"Failed to verify OTP: {message}"
        print("✓ Email OTP test passed")

if __name__ == '__main__':
    test_email_otp()
```

---

## Monitoring

### Metrics to Track:

1. **Email Delivery Rate**
   - Sent vs Delivered
   - Bounce rate
   - Spam complaint rate

2. **OTP Usage**
   - OTP requests per day
   - Verification success rate
   - Expiry rate

3. **Performance**
   - Email sending time
   - OTP verification time
   - Error rates

### Logging:

The application logs email events:
```python
logger.info(f"OTP sent to {email}")
logger.warning(f"Failed OTP attempt for {email}")
logger.error(f"Email sending failed: {error}")
```

---

## Cost Comparison

| Provider | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| Gmail | 500/day | N/A | Development |
| SendGrid | 100/day | $19.95/mo (50K) | Production |
| AWS SES | 62K/mo* | $0.10/1K | High volume |
| Mailgun | 5K/mo (3mo) | $35/mo (50K) | Mid-size |
| Outlook | 300/day | N/A | Small teams |

*First 62,000 emails free when sent from EC2

---

## Support

For issues:
- Check server logs: `src/dashboard/server.py`
- Review email service dashboard
- Test with `test_email_otp.py`
- Consult provider documentation

---

## Quick Start (Gmail)

1. Enable 2FA on Gmail account
2. Generate app password
3. Create `.env` file:
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   SMTP_FROM=your-email@gmail.com
   ```
4. Start server: `python src/dashboard/server.py`
5. Test login with email OTP

Done! 🎉
