#!/usr/bin/env python3
"""
MongoDB-based Authentication utilities for SOC Dashboard
Provides secure user management, password hashing, JWT tokens, and MFA support using MongoDB
"""

import os
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
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, List, Optional, Tuple
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.database.mongodb_dal import get_dal
from src.database.schemas import UserRole

class MongoDBAuthManager:
    def __init__(self, secret_key: str = None):
        self.dal = get_dal()
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'soc-dashboard-secret-key-change-in-production')
        self.token_expiry = timedelta(hours=8)  # 8 hour sessions
        self.refresh_expiry = timedelta(days=7)  # 7 day refresh tokens
        
        # Initialize with default admin if no users exist
        self._initialize_default_users()
    
    def _initialize_default_users(self):
        """Initialize with default admin user if no users exist"""
        try:
            users = self.dal.get_all_users()
            if not users:
                # Create default admin user
                success, message, user_id = self.dal.create_user(
                    username="admin",
                    password_hash=self.hash_password('SecureAdmin123!'),
                    email="admin@soc.local",
                    role=UserRole.ADMIN.value,
                    active=True,
                    mfa_enabled=False
                )
                if success:
                    print("✓ Default admin user created (admin/SecureAdmin123!)")
                else:
                    print(f"✗ Failed to create default admin: {message}")
        except Exception as e:
            print(f"✗ Error initializing default users: {e}")
    
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
        if role not in [r.value for r in UserRole]:
            return False, "Invalid role. Must be 'admin' or 'analyst'"
        
        # Validate password strength
        if not self._validate_password_strength(password):
            return False, "Password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        
        success, message, user_id = self.dal.create_user(
            username=username,
            password_hash=self.hash_password(password),
            email=email,
            role=role,
            active=True,
            mfa_enabled=False
        )
        
        return success, message
    
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
        user = self.dal.get_user_by_username(username)
        
        if not user:
            return False, "Invalid credentials", {}
        
        # Check if account is locked
        if user.get('locked_until'):
            locked_until = user['locked_until']
            if isinstance(locked_until, str):
                locked_until = datetime.fromisoformat(locked_until)
            if datetime.utcnow() < locked_until:
                return False, "Account temporarily locked due to failed attempts", {}
            else:
                # Unlock account
                self.dal.update_user(username, {
                    'locked_until': None,
                    'failed_attempts': 0
                })
        
        # Check if account is active
        if not user.get('active', True):
            return False, "Account is disabled", {}
        
        # Verify password
        if not self.verify_password(password, user['password_hash']):
            # Increment failed attempts
            failed_attempts = user.get('failed_attempts', 0) + 1
            updates = {'failed_attempts': failed_attempts}
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                updates['locked_until'] = datetime.utcnow() + timedelta(minutes=30)
            
            self.dal.update_user(username, updates)
            return False, "Invalid credentials", {}
        
        # Check MFA if enabled
        if user.get('mfa_enabled') and user.get('mfa_secret'):
            if not mfa_token:
                return False, "MFA token required", {'mfa_required': True}
            
            if not self.verify_mfa_token(user['mfa_secret'], mfa_token):
                return False, "Invalid MFA token", {}
        
        # Reset failed attempts on successful login
        self.dal.update_user(username, {
            'failed_attempts': 0,
            'locked_until': None,
            'last_login': datetime.utcnow()
        })
        
        # Return user info without sensitive data
        user_info = {
            'username': username,
            'role': user['role'],
            'email': user['email'],
            'mfa_enabled': user.get('mfa_enabled', False),
            'last_login': user.get('last_login')
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
        user = self.dal.get_user_by_username(username)
        
        if not user or not user.get('active', True):
            return False, "User not found or inactive", ""
        
        access_token, new_refresh_token = self.generate_tokens(username, user['role'])
        
        return True, access_token, new_refresh_token
    
    def setup_mfa(self, username: str) -> Tuple[bool, str, str]:
        """Setup MFA for user and return secret and QR code"""
        user = self.dal.get_user_by_username(username)
        
        if not user:
            return False, "User not found", ""
        
        secret = self.generate_mfa_secret()
        qr_code = self.generate_qr_code(username, secret)
        
        # Save secret but don't enable MFA yet (user needs to verify)
        success, message = self.dal.update_user(username, {'mfa_secret': secret})
        
        if not success:
            return False, message, ""
        
        return True, secret, qr_code
    
    def enable_mfa(self, username: str, token: str) -> Tuple[bool, str]:
        """Enable MFA after user verifies token"""
        user = self.dal.get_user_by_username(username)
        
        if not user:
            return False, "User not found"
        
        secret = user.get('mfa_secret')
        
        if not secret:
            return False, "MFA not set up. Please set up MFA first"
        
        if not self.verify_mfa_token(secret, token):
            return False, "Invalid MFA token"
        
        success, message = self.dal.update_user(username, {'mfa_enabled': True})
        
        return success, message if success else "MFA enabled successfully"
    
    def disable_mfa(self, username: str) -> Tuple[bool, str]:
        """Disable MFA for user"""
        success, message = self.dal.update_user(username, {
            'mfa_enabled': False,
            'mfa_secret': None
        })
        
        return success, "MFA disabled successfully" if success else message
    
    def get_users(self) -> List[Dict]:
        """Get all users (admin only)"""
        users = self.dal.get_all_users()
        user_list = []
        
        for user in users:
            user_list.append({
                'username': user['username'],
                'role': user['role'],
                'email': user['email'],
                'active': user.get('active', True),
                'mfa_enabled': user.get('mfa_enabled', False),
                'created_at': user['created_at'],
                'last_login': user.get('last_login'),
                'failed_attempts': user.get('failed_attempts', 0)
            })
        
        return user_list
    
    def update_user(self, username: str, updates: Dict) -> Tuple[bool, str]:
        """Update user information (admin only)"""
        allowed_updates = ['role', 'email', 'active']
        
        filtered_updates = {}
        for key, value in updates.items():
            if key in allowed_updates:
                if key == 'role' and value not in [r.value for r in UserRole]:
                    return False, "Invalid role"
                filtered_updates[key] = value
        
        return self.dal.update_user(username, filtered_updates)
    
    def delete_user(self, username: str, requesting_user: str) -> Tuple[bool, str]:
        """Delete user (admin only, cannot delete self)"""
        if username == requesting_user:
            return False, "Cannot delete your own account"
        
        # Prevent deletion of last admin
        users = self.dal.get_all_users(active_only=True)
        admin_count = sum(1 for user in users if user.get('role') == UserRole.ADMIN.value)
        
        user = self.dal.get_user_by_username(username)
        if user and user.get('role') == UserRole.ADMIN.value and admin_count <= 1:
            return False, "Cannot delete the last admin user"
        
        return self.dal.delete_user(username)
    
    def change_password(self, username: str, old_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        user = self.dal.get_user_by_username(username)
        
        if not user:
            return False, "User not found"
        
        # Verify old password
        if not self.verify_password(old_password, user['password_hash']):
            return False, "Current password is incorrect"
        
        # Validate new password
        if not self._validate_password_strength(new_password):
            return False, "New password must be at least 8 characters with uppercase, lowercase, digit, and special character"
        
        # Update password
        success, message = self.dal.update_user(username, {
            'password_hash': self.hash_password(new_password)
        })
        
        return success, "Password changed successfully" if success else message

# Authentication decorators
def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        print(f"DEBUG: token_required decorator called for {f.__name__}")
        token = None
        auth_header = request.headers.get('Authorization')
        print(f"DEBUG: Authorization header: {auth_header}")
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
                print(f"DEBUG: Extracted token: {token[:20]}...")
            except IndexError:
                print("DEBUG: Invalid token format")
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            print("DEBUG: Token is missing")
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            auth_manager = current_app.auth_manager
            print(f"DEBUG: Got auth_manager: {auth_manager}")
            valid, payload = auth_manager.verify_token(token)
            print(f"DEBUG: Token validation result: valid={valid}, payload={payload}")
            
            if not valid:
                print(f"DEBUG: Token validation failed: {payload}")
                return jsonify({'error': payload.get('error', 'Invalid token')}), 401
            
            # Add user info to request context
            request.current_user = {
                'username': payload.get('username'),
                'role': payload.get('role')
            }
            print(f"DEBUG: Set current_user: {request.current_user}")
            
            return f(*args, **kwargs)
        except Exception as e:
            print(f"DEBUG: Exception in token_required: {e}")
            return jsonify({'error': 'Authentication failed'}), 401
    
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
