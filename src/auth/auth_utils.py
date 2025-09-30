#!/usr/bin/env python3
"""
Authentication utilities for SOC Dashboard
Provides secure user management, password hashing, JWT tokens, and MFA support
"""

import os
import json
import bcrypt
try:
    from jwt import encode as jwt_encode, decode as jwt_decode, ExpiredSignatureError, InvalidTokenError
except ImportError:
    # Fallback for systems without PyJWT
    def jwt_encode(payload, key, algorithm='HS256'):
        import base64, json, hmac, hashlib
        header = base64.urlsafe_b64encode(json.dumps({"typ": "JWT", "alg": algorithm}).encode()).decode().rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip('=')
        signature = base64.urlsafe_b64encode(hmac.new(key.encode(), f"{header}.{payload_b64}".encode(), hashlib.sha256).digest()).decode().rstrip('=')
        return f"{header}.{payload_b64}.{signature}"
    
    def jwt_decode(token, key, algorithms=['HS256']):
        import base64, json, hmac, hashlib
        parts = token.split('.')
        if len(parts) != 3:
            raise InvalidTokenError("Invalid token format")
        header, payload, signature = parts
        # Add padding if needed
        payload += '=' * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload.encode()))
    
    class ExpiredSignatureError(Exception):
        pass
    
    class InvalidTokenError(Exception):
        pass
import pyotp
import qrcode
import io
import base64
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, List, Optional, Tuple
from fido2.server import Fido2Server
from fido2.webauthn import PublicKeyCredentialRpEntity, UserVerificationRequirement
from fido2 import cbor
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class AuthManager:
    def __init__(self, users_file: str = "data/users.json", secret_key: str = None):
        self.users_file = users_file
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'soc-dashboard-secret-key-change-in-production')
        self.token_expiry = timedelta(hours=8)  # 8 hour sessions
        self.refresh_expiry = timedelta(days=7)  # 7 day refresh tokens
        self.otp_expiry = timedelta(minutes=10)  # 10 minute OTP validity
        
        # Email OTP storage (in-memory, use Redis in production)
        self.email_otps = {}  # {email: {'otp': code, 'expires': datetime, 'attempts': int}}
        
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_from = os.getenv('SMTP_FROM', 'noreply@soc.local')
        
        # WebAuthn/Passkey configuration
        self.rp_entity = PublicKeyCredentialRpEntity(
            id=os.getenv('RP_ID', 'localhost'),
            name="SOC Dashboard"
        )
        self.fido2_server = Fido2Server(self.rp_entity)
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        
        # Initialize with default admin if no users exist
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Initialize with default admin user if no users exist"""
        if not os.path.exists(self.users_file):
            default_admin = {
                'admin': {
                    'password_hash': self.hash_password('SecureAdmin123!'),
                    'role': 'admin',
                    'email': 'admin@soc.local',
                    'mfa_enabled': False,
                    'mfa_secret': None,
                    'passkeys': [],  # List of registered passkeys
                    'email_verified': False,
                    'created_at': datetime.now().isoformat(),
                    'last_login': None,
                    'active': True,
                    'failed_attempts': 0,
                    'locked_until': None
                }
            }
            self._save_users(default_admin)
    
    def _load_users(self) -> Dict:
        """Load users from JSON file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_users(self, users: Dict):
        """Save users to JSON file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def generate_mfa_secret(self) -> str:
        """Generate new MFA secret for TOTP"""
        return pyotp.random_base32()
    
    def generate_qr_code(self, username: str, secret: str) -> str:
        """Generate QR code for MFA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name="SOC Dashboard"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return base64.b64encode(img_buffer.getvalue()).decode()
    
    def verify_mfa_token(self, secret: str, token: str) -> bool:
        """Verify MFA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # Allow 30 second window
    
    def create_user(self, username: str, password: str, role: str, email: str) -> Tuple[bool, str]:
        """Create new user"""
        users = self._load_users()
        
        if username in users:
            return False, "Username already exists"
        
        if role not in ['admin', 'analyst']:
            return False, "Invalid role. Must be 'admin' or 'analyst'"
        
        # Validate password strength
        if not self._validate_password_strength(password):
            return False, "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        
        users[username] = {
            'password_hash': self.hash_password(password),
            'role': role,
            'email': email,
            'mfa_enabled': False,
            'mfa_secret': None,
            'passkeys': [],
            'email_verified': False,
            'created_at': datetime.now().isoformat(),
            'last_login': None,
            'active': True,
            'failed_attempts': 0,
            'locked_until': None
        }
        
        self._save_users(users)
        return True, "User created successfully"
    
    def _validate_password_strength(self, password: str) -> bool:
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def authenticate_user(self, username: str, password: str, mfa_token: str = None) -> Tuple[bool, str, Dict]:
        """Authenticate user with password and optional MFA"""
        users = self._load_users()
        
        if username not in users:
            return False, "Invalid credentials", {}
        
        user = users[username]
        
        # Check if account is locked
        if user.get('locked_until'):
            locked_until = datetime.fromisoformat(user['locked_until'])
            if datetime.now() < locked_until:
                return False, "Account temporarily locked due to failed attempts", {}
            else:
                # Unlock account
                user['locked_until'] = None
                user['failed_attempts'] = 0
        
        # Check if account is active
        if not user.get('active', True):
            return False, "Account is disabled", {}
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            # Increment failed attempts
            user['failed_attempts'] = user.get('failed_attempts', 0) + 1
            
            # Lock account after 5 failed attempts
            if user['failed_attempts'] >= 5:
                user['locked_until'] = (datetime.now() + timedelta(minutes=30)).isoformat()
            
            self._save_users(users)
            return False, "Invalid credentials", {}
        
        # Check MFA if enabled
        if user.get('mfa_enabled') and user.get('mfa_secret'):
            if not mfa_token:
                return False, "MFA token required", {'mfa_required': True}
            
            if not self.verify_mfa_token(user['mfa_secret'], mfa_token):
                return False, "Invalid MFA token", {}
        
        # Reset failed attempts on successful login
        user['failed_attempts'] = 0
        user['locked_until'] = None
        user['last_login'] = datetime.now().isoformat()
        self._save_users(users)
        
        # Return user info without sensitive data
        user_info = {
            'username': username,
            'role': user['role'],
            'email': user['email'],
            'mfa_enabled': user.get('mfa_enabled', False),
            'last_login': user['last_login']
        }
        
        return True, "Authentication successful", user_info
    
    def generate_tokens(self, username: str, role: str) -> Tuple[str, str]:
        """Generate access and refresh JWT tokens"""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'username': username,
            'role': role,
            'type': 'access',
            'iat': now,
            'exp': now + self.token_expiry
        }
        
        # Refresh token payload
        refresh_payload = {
            'username': username,
            'type': 'refresh',
            'iat': now,
            'exp': now + self.refresh_expiry
        }
        
        access_token = jwt_encode(access_payload, self.secret_key, algorithm='HS256')
        refresh_token = jwt_encode(refresh_payload, self.secret_key, algorithm='HS256')
        
        return access_token, refresh_token
    
    def verify_token(self, token: str) -> Tuple[bool, Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt_decode(token, self.secret_key, algorithms=['HS256'])
            return True, payload
        except ExpiredSignatureError:
            return False, {'error': 'Token expired'}
        except InvalidTokenError:
            return False, {'error': 'Invalid token'}
    
    def refresh_access_token(self, refresh_token: str) -> Tuple[bool, str, str]:
        """Generate new access token from refresh token"""
        valid, payload = self.verify_token(refresh_token)
        
        if not valid or payload.get('type') != 'refresh':
            return False, "Invalid refresh token", ""
        
        username = payload.get('username')
        users = self._load_users()
        
        if username not in users or not users[username].get('active', True):
            return False, "User not found or inactive", ""
        
        user = users[username]
        access_token, new_refresh_token = self.generate_tokens(username, user['role'])
        
        return True, access_token, new_refresh_token
    
    def setup_mfa(self, username: str) -> Tuple[bool, str, str]:
        """Setup MFA for user and return secret and QR code"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found", ""
        
        secret = self.generate_mfa_secret()
        qr_code = self.generate_qr_code(username, secret)
        
        # Save secret but don't enable MFA yet (user needs to verify)
        users[username]['mfa_secret'] = secret
        self._save_users(users)
        
        return True, secret, qr_code
    
    def enable_mfa(self, username: str, token: str) -> Tuple[bool, str]:
        """Enable MFA after user verifies token"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        secret = user.get('mfa_secret')
        
        if not secret:
            return False, "MFA not set up. Please set up MFA first"
        
        if not self.verify_mfa_token(secret, token):
            return False, "Invalid MFA token"
        
        users[username]['mfa_enabled'] = True
        self._save_users(users)
        
        return True, "MFA enabled successfully"
    
    def disable_mfa(self, username: str) -> Tuple[bool, str]:
        """Disable MFA for user"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        users[username]['mfa_enabled'] = False
        users[username]['mfa_secret'] = None
        self._save_users(users)
        
        return True, "MFA disabled successfully"
    
    def get_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        users = self._load_users()
        user_list = []
        
        for username, user_data in users.items():
            user_list.append({
                'username': username,
                'role': user_data['role'],
                'email': user_data['email'],
                'active': user_data.get('active', True),
                'mfa_enabled': user_data.get('mfa_enabled', False),
                'created_at': user_data['created_at'],
                'last_login': user_data.get('last_login'),
                'failed_attempts': user_data.get('failed_attempts', 0)
            })
        
        return user_list
    
    def update_user(self, username: str, updates: Dict) -> Tuple[bool, str]:
        """Update user information (admin only)"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        allowed_updates = ['role', 'email', 'active']
        
        for key, value in updates.items():
            if key in allowed_updates:
                if key == 'role' and value not in ['admin', 'analyst']:
                    return False, "Invalid role"
                users[username][key] = value
        
        self._save_users(users)
        return True, "User updated successfully"
    
    def delete_user(self, username: str, requesting_user: str) -> Tuple[bool, str]:
        """Delete user (admin only, cannot delete self)"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        if username == requesting_user:
            return False, "Cannot delete your own account"
        
        # Prevent deletion of last admin
        admin_count = sum(1 for user in users.values() if user.get('role') == 'admin' and user.get('active', True))
        if users[username].get('role') == 'admin' and admin_count <= 1:
            return False, "Cannot delete the last admin user"
        
        del users[username]
        self._save_users(users)
        
        return True, "User deleted successfully"
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        user = users[username]
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            return False, "Current password is incorrect"
        
        # Validate new password
        if not self._validate_password_strength(new_password):
            return False, "New password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        
        # Update password
        users[username]['password_hash'] = self.hash_password(new_password)
        self._save_users(users)
        
        return True, "Password changed successfully"
    
    # ============ Email OTP Methods ============
    
    def generate_email_otp(self, email: str) -> str:
        """Generate 6-digit OTP for email"""
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Store OTP with expiry
        self.email_otps[email] = {
            'otp': otp,
            'expires': datetime.now() + self.otp_expiry,
            'attempts': 0
        }
        
        return otp
    
    def send_email_otp(self, email: str, otp: str) -> Tuple[bool, str]:
        """Send OTP via email"""
        if not self.smtp_username or not self.smtp_password:
            # Development mode - just log the OTP
            print(f"[DEV MODE] Email OTP for {email}: {otp}")
            return True, f"OTP generated (dev mode): {otp}"
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = 'SOC Dashboard - Login Code'
            msg['From'] = self.smtp_from
            msg['To'] = email
            
            html = f"""
            <!DOCTYPE html>
            <html>
              <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
              </head>
              <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #0f172a;">
                <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #0f172a; padding: 40px 20px;">
                  <tr>
                    <td align="center">
                      <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 12px; overflow: hidden; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);">
                        
                        <!-- Header with Shield Icon -->
                        <tr>
                          <td style="background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%); padding: 30px; text-align: center;">
                            <div style="width: 60px; height: 60px; background: rgba(255, 255, 255, 0.2); border-radius: 50%; margin: 0 auto 15px; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(10px);">
                              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                              </svg>
                            </div>
                            <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 700; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                              SOC Dashboard
                            </h1>
                            <p style="color: rgba(255, 255, 255, 0.9); margin: 8px 0 0; font-size: 14px; letter-spacing: 1px;">
                              SECURE AUTHENTICATION PORTAL
                            </p>
                          </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                          <td style="padding: 40px 30px;">
                            <h2 style="color: #f1f5f9; margin: 0 0 20px; font-size: 20px; font-weight: 600;">
                              🔐 Authentication Code
                            </h2>
                            <p style="color: #cbd5e1; margin: 0 0 30px; font-size: 15px; line-height: 1.6;">
                              A login attempt has been initiated for your account. Use the verification code below to complete authentication:
                            </p>
                            
                            <!-- OTP Code Box -->
                            <div style="background: linear-gradient(135deg, #1e40af 0%, #0891b2 100%); border-radius: 12px; padding: 30px; text-align: center; margin: 30px 0; box-shadow: 0 8px 32px rgba(59, 130, 246, 0.3); border: 2px solid rgba(59, 130, 246, 0.3);">
                              <div style="color: rgba(255, 255, 255, 0.7); font-size: 12px; letter-spacing: 2px; margin-bottom: 10px; font-weight: 600;">
                                VERIFICATION CODE
                              </div>
                              <div style="color: white; font-size: 42px; font-weight: 700; letter-spacing: 12px; font-family: 'Courier New', monospace; text-shadow: 0 2px 8px rgba(0,0,0,0.3);">
                                {otp}
                              </div>
                            </div>
                            
                            <!-- Security Info -->
                            <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 15px; margin: 30px 0; border-radius: 4px;">
                              <p style="color: #fca5a5; margin: 0; font-size: 13px; line-height: 1.6;">
                                <strong>⚠️ Security Notice:</strong> This code expires in <strong>10 minutes</strong>. Never share this code with anyone. SOC Dashboard staff will never ask for your verification code.
                              </p>
                            </div>
                            
                            <!-- Additional Info -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 30px;">
                              <tr>
                                <td style="padding: 15px; background: rgba(59, 130, 246, 0.1); border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2);">
                                  <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                      <td width="30" valign="top">
                                        <div style="width: 24px; height: 24px; background: rgba(59, 130, 246, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                          <span style="color: #60a5fa; font-size: 14px;">🕐</span>
                                        </div>
                                      </td>
                                      <td style="padding-left: 12px;">
                                        <p style="color: #94a3b8; margin: 0; font-size: 13px; line-height: 1.5;">
                                          <strong style="color: #e2e8f0;">Valid for:</strong> 10 minutes from receipt
                                        </p>
                                      </td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>
                              <tr><td style="height: 10px;"></td></tr>
                              <tr>
                                <td style="padding: 15px; background: rgba(59, 130, 246, 0.1); border-radius: 8px; border: 1px solid rgba(59, 130, 246, 0.2);">
                                  <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                      <td width="30" valign="top">
                                        <div style="width: 24px; height: 24px; background: rgba(59, 130, 246, 0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                          <span style="color: #60a5fa; font-size: 14px;">🔒</span>
                                        </div>
                                      </td>
                                      <td style="padding-left: 12px;">
                                        <p style="color: #94a3b8; margin: 0; font-size: 13px; line-height: 1.5;">
                                          <strong style="color: #e2e8f0;">Security:</strong> One-time use only, encrypted transmission
                                        </p>
                                      </td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>
                            </table>
                          </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                          <td style="background: #0f172a; padding: 30px; text-align: center; border-top: 1px solid rgba(59, 130, 246, 0.2);">
                            <p style="color: #64748b; margin: 0 0 10px; font-size: 12px;">
                              If you didn't request this code, please ignore this email or contact your security administrator.
                            </p>
                            <p style="color: #475569; margin: 0; font-size: 11px;">
                              © 2025 SOC Dashboard | Enterprise Security Operations Center
                            </p>
                            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(71, 85, 105, 0.3);">
                              <p style="color: #475569; margin: 0; font-size: 10px; letter-spacing: 0.5px;">
                                CONFIDENTIAL - This email contains sensitive security information
                              </p>
                            </div>
                          </td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True, "OTP sent successfully"
        except Exception as e:
            return False, f"Failed to send email: {str(e)}"
    
    def verify_email_otp(self, email: str, otp: str) -> Tuple[bool, str]:
        """Verify email OTP"""
        if email not in self.email_otps:
            return False, "No OTP found for this email"
        
        otp_data = self.email_otps[email]
        
        # Check expiry
        if datetime.now() > otp_data['expires']:
            del self.email_otps[email]
            return False, "OTP expired"
        
        # Check attempts (max 3)
        if otp_data['attempts'] >= 3:
            del self.email_otps[email]
            return False, "Too many failed attempts"
        
        # Verify OTP
        if otp != otp_data['otp']:
            otp_data['attempts'] += 1
            return False, "Invalid OTP"
        
        # Success - remove OTP
        del self.email_otps[email]
        return True, "OTP verified successfully"
    
    def request_passwordless_login(self, email: str) -> Tuple[bool, str]:
        """Request passwordless login via email OTP"""
        users = self._load_users()
        
        # Find user by email
        user_found = None
        username = None
        for uname, user_data in users.items():
            if user_data.get('email') == email:
                user_found = user_data
                username = uname
                break
        
        if not user_found:
            # Don't reveal if email exists (security)
            return True, "If this email is registered, you will receive a login code"
        
        if not user_found.get('active', True):
            return False, "Account is disabled"
        
        # Generate and send OTP
        otp = self.generate_email_otp(email)
        success, message = self.send_email_otp(email, otp)
        
        if success:
            return True, "Login code sent to your email"
        else:
            return False, message
    
    def authenticate_with_email_otp(self, email: str, otp: str) -> Tuple[bool, str, Dict]:
        """Authenticate user with email OTP"""
        # Verify OTP first
        valid, message = self.verify_email_otp(email, otp)
        if not valid:
            return False, message, {}
        
        users = self._load_users()
        
        # Find user by email
        for username, user_data in users.items():
            if user_data.get('email') == email:
                # Mark email as verified
                user_data['email_verified'] = True
                user_data['last_login'] = datetime.now().isoformat()
                self._save_users(users)
                
                user_info = {
                    'username': username,
                    'role': user_data['role'],
                    'email': user_data['email'],
                    'mfa_enabled': user_data.get('mfa_enabled', False),
                    'last_login': user_data['last_login']
                }
                
                return True, "Authentication successful", user_info
        
        return False, "User not found", {}
    
    # ============ Passkey/WebAuthn Methods ============
    
    def _encode_bytes(self, data):
        """Helper to encode bytes or return as-is if already string"""
        if isinstance(data, bytes):
            return base64.b64encode(data).decode()
        elif isinstance(data, str):
            return data
        return str(data)
    
    def begin_passkey_registration(self, username: str) -> Tuple[bool, Dict, str]:
        """Begin passkey registration process"""
        users = self._load_users()
        
        if username not in users:
            return False, {}, "User not found"
        
        user = users[username]
        
        # Create user handle (unique identifier)
        user_handle = username.encode('utf-8')
        
        # Get existing credentials
        existing_credentials = [
            cbor.decode(base64.b64decode(pk['credential_data']))
            for pk in user.get('passkeys', [])
        ]
        
        # Generate registration options
        registration_data, state = self.fido2_server.register_begin(
            {
                'id': user_handle,
                'name': username,
                'displayName': user.get('email', username)
            },
            existing_credentials,
            user_verification=UserVerificationRequirement.PREFERRED
        )
        
        # Convert to JSON-serializable format
        options = {
            'publicKey': {
                'challenge': self._encode_bytes(registration_data['publicKey']['challenge']),
                'rp': registration_data['publicKey']['rp'],
                'user': {
                    'id': self._encode_bytes(registration_data['publicKey']['user']['id']),
                    'name': registration_data['publicKey']['user']['name'],
                    'displayName': registration_data['publicKey']['user']['displayName']
                },
                'pubKeyCredParams': registration_data['publicKey']['pubKeyCredParams'],
                'timeout': registration_data['publicKey'].get('timeout', 60000),
                'attestation': registration_data['publicKey'].get('attestation', 'none'),
                'authenticatorSelection': registration_data['publicKey'].get('authenticatorSelection', {})
            }
        }
        
        # Store state temporarily (use Redis in production)
        state_id = secrets.token_urlsafe(32)
        if not hasattr(self, '_passkey_states'):
            self._passkey_states = {}
        self._passkey_states[state_id] = {
            'state': state,
            'username': username,
            'expires': datetime.now() + timedelta(minutes=5)
        }
        
        return True, options, state_id
    
    def complete_passkey_registration(self, state_id: str, credential_data: Dict) -> Tuple[bool, str]:
        """Complete passkey registration"""
        if not hasattr(self, '_passkey_states') or state_id not in self._passkey_states:
            return False, "Invalid or expired registration session"
        
        state_info = self._passkey_states[state_id]
        
        # Check expiry
        if datetime.now() > state_info['expires']:
            del self._passkey_states[state_id]
            return False, "Registration session expired"
        
        username = state_info['username']
        state = state_info['state']
        
        try:
            # Decode challenge
            credential_data['response']['clientDataJSON'] = base64.b64decode(
                credential_data['response']['clientDataJSON']
            )
            credential_data['response']['attestationObject'] = base64.b64decode(
                credential_data['response']['attestationObject']
            )
            credential_data['rawId'] = base64.b64decode(credential_data['rawId'])
            
            # Complete registration
            auth_data = self.fido2_server.register_complete(state, credential_data)
            
            # Store credential
            users = self._load_users()
            if username not in users:
                return False, "User not found"
            
            if 'passkeys' not in users[username]:
                users[username]['passkeys'] = []
            
            passkey_entry = {
                'credential_id': base64.b64encode(auth_data.credential_data.credential_id).decode(),
                'credential_data': base64.b64encode(cbor.encode(auth_data.credential_data)).decode(),
                'name': f"Passkey {len(users[username]['passkeys']) + 1}",
                'created_at': datetime.now().isoformat()
            }
            
            users[username]['passkeys'].append(passkey_entry)
            self._save_users(users)
            
            # Clean up state
            del self._passkey_states[state_id]
            
            return True, "Passkey registered successfully"
        
        except Exception as e:
            return False, f"Registration failed: {str(e)}"
    
    def begin_passkey_authentication(self, username: str) -> Tuple[bool, Dict, str]:
        """Begin passkey authentication"""
        users = self._load_users()
        
        if username not in users:
            return False, {}, "User not found"
        
        user = users[username]
        passkeys = user.get('passkeys', [])
        
        if not passkeys:
            return False, {}, "No passkeys registered"
        
        # Get credentials
        credentials = [
            cbor.decode(base64.b64decode(pk['credential_data']))
            for pk in passkeys
        ]
        
        # Generate authentication options
        auth_data, state = self.fido2_server.authenticate_begin(
            credentials,
            user_verification=UserVerificationRequirement.PREFERRED
        )
        
        # Convert to JSON-serializable format
        options = {
            'publicKey': {
                'challenge': self._encode_bytes(auth_data['publicKey']['challenge']),
                'timeout': auth_data['publicKey'].get('timeout', 60000),
                'rpId': auth_data['publicKey']['rpId'],
                'allowCredentials': [
                    {
                        'type': cred['type'],
                        'id': self._encode_bytes(cred['id'])
                    }
                    for cred in auth_data['publicKey']['allowCredentials']
                ],
                'userVerification': auth_data['publicKey'].get('userVerification', 'preferred')
            }
        }
        
        # Store state
        state_id = secrets.token_urlsafe(32)
        if not hasattr(self, '_passkey_auth_states'):
            self._passkey_auth_states = {}
        self._passkey_auth_states[state_id] = {
            'state': state,
            'username': username,
            'expires': datetime.now() + timedelta(minutes=5)
        }
        
        return True, options, state_id
    
    def complete_passkey_authentication(self, state_id: str, credential_data: Dict) -> Tuple[bool, str, Dict]:
        """Complete passkey authentication"""
        if not hasattr(self, '_passkey_auth_states') or state_id not in self._passkey_auth_states:
            return False, "Invalid or expired authentication session", {}
        
        state_info = self._passkey_auth_states[state_id]
        
        # Check expiry
        if datetime.now() > state_info['expires']:
            del self._passkey_auth_states[state_id]
            return False, "Authentication session expired", {}
        
        username = state_info['username']
        state = state_info['state']
        
        try:
            # Decode response data
            credential_data['response']['clientDataJSON'] = base64.b64decode(
                credential_data['response']['clientDataJSON']
            )
            credential_data['response']['authenticatorData'] = base64.b64decode(
                credential_data['response']['authenticatorData']
            )
            credential_data['response']['signature'] = base64.b64decode(
                credential_data['response']['signature']
            )
            credential_data['rawId'] = base64.b64decode(credential_data['rawId'])
            
            # Get user credentials
            users = self._load_users()
            user = users[username]
            credentials = [
                cbor.decode(base64.b64decode(pk['credential_data']))
                for pk in user.get('passkeys', [])
            ]
            
            # Complete authentication
            self.fido2_server.authenticate_complete(
                state,
                credentials,
                credential_data
            )
            
            # Update last login
            user['last_login'] = datetime.now().isoformat()
            self._save_users(users)
            
            # Clean up state
            del self._passkey_auth_states[state_id]
            
            user_info = {
                'username': username,
                'role': user['role'],
                'email': user['email'],
                'mfa_enabled': user.get('mfa_enabled', False),
                'last_login': user['last_login']
            }
            
            return True, "Authentication successful", user_info
        
        except Exception as e:
            return False, f"Authentication failed: {str(e)}", {}
    
    def list_passkeys(self, username: str) -> List[Dict]:
        """List user's registered passkeys"""
        users = self._load_users()
        
        if username not in users:
            return []
        
        passkeys = users[username].get('passkeys', [])
        
        return [
            {
                'id': pk['credential_id'],
                'name': pk['name'],
                'created_at': pk['created_at']
            }
            for pk in passkeys
        ]
    
    def delete_passkey(self, username: str, credential_id: str) -> Tuple[bool, str]:
        """Delete a passkey"""
        users = self._load_users()
        
        if username not in users:
            return False, "User not found"
        
        passkeys = users[username].get('passkeys', [])
        
        # Find and remove passkey
        updated_passkeys = [pk for pk in passkeys if pk['credential_id'] != credential_id]
        
        if len(updated_passkeys) == len(passkeys):
            return False, "Passkey not found"
        
        users[username]['passkeys'] = updated_passkeys
        self._save_users(users)
        
        return True, "Passkey deleted successfully"

# Authentication decorators
def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        auth_manager = current_app.auth_manager
        valid, payload = auth_manager.verify_token(token)
        
        if not valid:
            return jsonify({'error': payload.get('error', 'Invalid token')}), 401
        
        # Add user info to request context
        request.current_user = {
            'username': payload.get('username'),
            'role': payload.get('role')
        }
        
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated

def analyst_or_admin_required(f):
    """Decorator to require analyst or admin role"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(request, 'current_user') or request.current_user.get('role') not in ['admin', 'analyst']:
            return jsonify({'error': 'Analyst or admin access required'}), 403
        return f(*args, **kwargs)
    
    return decorated
