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
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, List, Optional, Tuple

class AuthManager:
    def __init__(self, users_file: str = "data/users.json", secret_key: str = None):
        self.users_file = users_file
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'soc-dashboard-secret-key-change-in-production')
        self.token_expiry = timedelta(hours=8)  # 8 hour sessions
        self.refresh_expiry = timedelta(days=7)  # 7 day refresh tokens
        
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
