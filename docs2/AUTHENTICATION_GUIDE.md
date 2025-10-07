# SOC Dashboard Authentication System

## Overview

The SOC Dashboard now includes a comprehensive authentication system with role-based access control, multi-factor authentication, and audit logging capabilities.

## 🔐 Authentication Features

### Core Security Features
- **JWT-based Authentication** - Secure token-based sessions
- **Google Authenticator MFA** - Time-based one-time passwords (TOTP)
- **Role-Based Access Control** - Admin and Analyst roles with different permissions
- **Password Security** - Bcrypt hashing with strength requirements
- **Account Protection** - Lockout after failed attempts, session management
- **Audit Logging** - Comprehensive tracking of all user actions

### User Roles

#### Administrator
- Full system access
- User management (create, update, delete users)
- Audit log access and security monitoring
- System configuration
- All SOC analyst capabilities

#### SOC Analyst
- Alert management (flag, dismiss alerts)
- Threshold adjustment
- Real-time monitoring controls
- Dashboard access
- Personal settings and MFA setup

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed Initial Data
```bash
python scripts/seed_data.py
```

### 3. Start Authenticated Dashboard
```bash
python scripts/start_auth_dashboard.py
```

### 4. Access Dashboard
- **URL**: http://localhost:5000
- **Default Admin**: `admin` / `SecureAdmin123!`

## 👥 Seeded User Accounts

| Username | Role | Password | MFA Status | Status |
|----------|------|----------|------------|--------|
| admin | Admin | SecureAdmin123! | Disabled | Active |
| john_analyst | Analyst | AnalystPass123! | Disabled | Active |
| sarah_analyst | Analyst | SecurePass123! | Enabled | Active |
| mike_admin | Admin | AdminSecure123! | Enabled | Active |
| inactive_user | Analyst | InactivePass123! | Disabled | Inactive |

## 🔒 Security Policies

### Password Requirements
- Minimum 8 characters
- Must contain uppercase letter
- Must contain lowercase letter
- Must contain digit
- Must contain special character

### Account Security
- Maximum 5 failed login attempts
- 30-minute lockout after failed attempts
- 8-hour session timeout
- 7-day refresh token validity

### MFA Configuration
- Google Authenticator TOTP
- 30-second time window
- QR code setup process
- Manual secret entry option

## 📊 API Endpoints

### Authentication Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/profile` - Get user profile
- `POST /api/auth/change-password` - Change password

### MFA Endpoints
- `POST /api/auth/mfa/setup` - Setup MFA
- `POST /api/auth/mfa/enable` - Enable MFA
- `POST /api/auth/mfa/disable` - Disable MFA

### Admin Endpoints (Admin Only)
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/<username>` - Update user
- `DELETE /api/admin/users/<username>` - Delete user
- `GET /api/admin/audit` - Get audit logs
- `GET /api/admin/audit/summary` - Get audit summary
- `GET /api/admin/security-alerts` - Get security alerts

### SOC Dashboard Endpoints (Authenticated)
- `GET /api/alerts` - Get alerts
- `GET /api/stats` - Get system statistics
- `GET/POST /api/threshold` - Manage detection threshold
- `POST /api/alerts/<id>/flag` - Flag alert
- `POST /api/alerts/<id>/dismiss` - Dismiss alert
- `POST /api/monitoring/start` - Start monitoring
- `POST /api/monitoring/stop` - Stop monitoring

## 🔍 Audit Logging

### Event Types Tracked
- Authentication events (login, logout, failures)
- User management (create, update, delete)
- MFA operations (setup, enable, disable)
- SOC operations (alert actions, threshold changes)
- Security events (unauthorized access, lockouts)

### Audit Data Storage
- **JSON Format**: `data/audit.json` - Structured data for API access
- **Text Format**: `data/audit.log` - Human-readable log file
- **Retention**: 10,000 events max, 90-day retention policy

### Security Monitoring
- Failed login attempt tracking
- Suspicious activity detection
- Account lockout notifications
- Multi-IP login detection

## 🎨 Frontend Features

### Login Interface
- Clean, professional login form
- MFA token input when required
- Error handling and validation
- Password visibility toggle

### User Management (Admin)
- User creation with validation
- Role assignment and modification
- Account activation/deactivation
- Bulk operations support
- Search and filtering

### MFA Setup
- Step-by-step setup wizard
- QR code generation
- Manual secret entry option
- Token verification process

### Audit Dashboard (Admin)
- Real-time audit log viewing
- Advanced filtering options
- Security alert notifications
- Event type categorization
- Export capabilities

## 🧪 Testing

### Run Authentication Tests
```bash
python -m pytest tests/test_authentication.py -v
```

### Test Coverage
- User management operations
- Authentication flows
- MFA setup and verification
- JWT token handling
- Role-based access control
- Audit logging functionality
- API endpoint security

## 📁 File Structure

```
SOC-assistant/
├── src/
│   ├── auth/
│   │   ├── auth_utils.py      # Core authentication logic
│   │   ├── audit_logger.py    # Audit logging system
│   │   └── __init__.py
│   └── dashboard/
│       ├── auth_server.py     # Authenticated dashboard server
│       └── server.py          # Original server (legacy)
├── frontend/
│   └── src/
│       └── components/
│           ├── Login.jsx      # Login interface
│           ├── UserManagement.jsx  # User CRUD interface
│           ├── MFASetup.jsx   # MFA configuration
│           └── AuditLogs.jsx  # Audit log viewer
├── data/
│   ├── users.json            # User accounts (gitignored)
│   ├── audit.json            # Audit events (gitignored)
│   ├── audit.log             # Text audit log (gitignored)
│   └── system_config.json    # System configuration (gitignored)
├── scripts/
│   ├── seed_data.py          # Data seeding script
│   └── start_auth_dashboard.py  # Authenticated server startup
└── tests/
    └── test_authentication.py   # Comprehensive auth tests
```

## 🔧 Configuration

### Environment Variables
- `FLASK_SECRET_KEY` - Flask session secret
- `JWT_SECRET_KEY` - JWT signing secret
- `SOC_ENV` - Environment (development/production)

### System Configuration
Located in `data/system_config.json`:
- Session timeouts
- Password policies
- Rate limiting settings
- Audit retention policies

## 🚨 Security Considerations

### Production Deployment
1. Change default passwords immediately
2. Set strong JWT secrets via environment variables
3. Enable HTTPS/TLS encryption
4. Configure proper CORS policies
5. Set up log monitoring and alerting
6. Regular security audits and updates

### Backup and Recovery
- Regular backup of user data and audit logs
- Secure storage of MFA backup codes
- Disaster recovery procedures
- Data retention compliance

## 📞 Support

For issues or questions regarding the authentication system:
1. Check the audit logs for security events
2. Review the test suite for expected behavior
3. Consult the API documentation for endpoint usage
4. Monitor system logs for error messages

## 🎯 Next Steps

The authentication system is now fully implemented and ready for use. Consider these enhancements:

1. **LDAP/Active Directory Integration** - Enterprise user management
2. **SSO Support** - SAML/OAuth integration
3. **Advanced MFA** - Hardware tokens, biometrics
4. **Risk-Based Authentication** - Behavioral analysis
5. **Compliance Reporting** - SOX, GDPR, HIPAA compliance
6. **Mobile App Support** - Native mobile authentication
