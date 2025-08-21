import bcrypt
import jwt
import json
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from cryptography.fernet import Fernet
import secrets
import re

class AuthManager:
    def __init__(self, app=None):
        self.app = app
        self.failed_attempts = {}
        self.active_sessions = {}
        self.blacklisted_tokens = set()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the auth manager with Flask app"""
        self.app = app
        
        # Ensure JWT secret key is set
        if not app.config.get('JWT_SECRET_KEY'):
            app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 
                                                         secrets.token_urlsafe(32))
        
        # Set default configurations
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', 3600)  # 1 hour
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', 604800)  # 7 days
        app.config.setdefault('BCRYPT_LOG_ROUNDS', 12)
        app.config.setdefault('MAX_LOGIN_ATTEMPTS', 5)
        app.config.setdefault('LOGIN_ATTEMPT_WINDOW', 300)  # 5 minutes
    
    def hash_password(self, password):
        """Hash password using bcrypt"""
        rounds = self.app.config.get('BCRYPT_LOG_ROUNDS', 12)
        salt = bcrypt.gensalt(rounds=rounds)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password, hashed):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def validate_password_strength(self, password):
        """Validate password meets security requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is valid"
    
    def generate_tokens(self, user_id):
        """Generate access and refresh tokens"""
        now = datetime.utcnow()
        
        # Generate session ID first
        session_id = secrets.token_urlsafe(32)
        
        # Access token
        access_payload = {
            'user_id': user_id,
            'type': 'access',
            'session_id': session_id,  # Include session_id in token
            'iat': now,
            'exp': now + timedelta(seconds=self.app.config['JWT_ACCESS_TOKEN_EXPIRES']),
            'jti': secrets.token_urlsafe(16)  # JWT ID for token tracking
        }
        
        # Refresh token
        refresh_payload = {
            'user_id': user_id,
            'type': 'refresh',
            'session_id': session_id,  # Include session_id in token
            'iat': now,
            'exp': now + timedelta(seconds=self.app.config['JWT_REFRESH_TOKEN_EXPIRES']),
            'jti': secrets.token_urlsafe(16)
        }
        
        access_token = jwt.encode(access_payload, self.app.config['JWT_SECRET_KEY'], 
                                algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, self.app.config['JWT_SECRET_KEY'], 
                                 algorithm='HS256')
        
        # Store session
        self.active_sessions[session_id] = {
            'user_id': user_id,
            'access_token_jti': access_payload['jti'],
            'refresh_token_jti': refresh_payload['jti'],
            'created_at': now,
            'last_activity': now
        }
        
        return access_token, refresh_token, session_id
    
    def verify_token(self, token, token_type='access'):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.app.config['JWT_SECRET_KEY'], 
                               algorithms=['HS256'])
            
            # Check token type
            if payload.get('type') != token_type:
                return None, 'Invalid token type'
            
            # Check if token is blacklisted
            if payload.get('jti') in self.blacklisted_tokens:
                return None, 'Token has been revoked'
            
            return payload, None
            
        except jwt.ExpiredSignatureError:
            return None, 'Token has expired'
        except jwt.InvalidTokenError:
            return None, 'Invalid token'
    
    def refresh_access_token(self, refresh_token):
        """Generate new access token using refresh token"""
        payload, error = self.verify_token(refresh_token, 'refresh')
        if error:
            return None, None, error
        
        user_id = payload['user_id']
        access_token, _, _ = self.generate_tokens(user_id)
        
        return access_token, user_id, None
    
    def revoke_token(self, token):
        """Add token to blacklist"""
        try:
            payload = jwt.decode(token, self.app.config['JWT_SECRET_KEY'], 
                               algorithms=['HS256'], options={"verify_exp": False})
            self.blacklisted_tokens.add(payload.get('jti'))
            return True
        except jwt.InvalidTokenError:
            return False
    
    def check_rate_limit(self, identifier):
        """Check if identifier has exceeded login attempts"""
        now = datetime.utcnow()
        window = self.app.config['LOGIN_ATTEMPT_WINDOW']
        max_attempts = self.app.config['MAX_LOGIN_ATTEMPTS']
        
        if identifier not in self.failed_attempts:
            return True
        
        # Clean old attempts
        cutoff = now - timedelta(seconds=window)
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier] 
            if attempt > cutoff
        ]
        
        return len(self.failed_attempts[identifier]) < max_attempts
    
    def record_failed_attempt(self, identifier):
        """Record failed login attempt"""
        now = datetime.utcnow()
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        self.failed_attempts[identifier].append(now)
    
    def clear_failed_attempts(self, identifier):
        """Clear failed attempts for identifier"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    def logout_session(self, session_id, access_token=None, refresh_token=None):
        """Logout session and revoke tokens"""
        # Remove session
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            # Blacklist session tokens
            self.blacklisted_tokens.add(session['access_token_jti'])
            self.blacklisted_tokens.add(session['refresh_token_jti'])
            del self.active_sessions[session_id]
        
        # Revoke provided tokens
        if access_token:
            self.revoke_token(access_token)
        if refresh_token:
            self.revoke_token(refresh_token)
        
        return True
    
    def validate_session(self, user_id, session_id):
        """Validate if session is active and valid"""
        if not session_id:
            return False
            
        # If session not found (server restart), create a new one for valid users
        if session_id not in self.active_sessions:
            # Check if user exists in system
            try:
                with open('users.json', 'r') as f:
                    users = json.load(f)
                    if user_id in users:
                        # Recreate session for existing user
                        self.active_sessions[session_id] = {
                            'user_id': user_id,
                            'access_token_jti': '',
                            'refresh_token_jti': '',
                            'created_at': datetime.utcnow(),
                            'last_activity': datetime.utcnow()
                        }
                        return True
            except Exception:
                pass
            return False
        
        session = self.active_sessions[session_id]
        if session['user_id'] != user_id:
            return False
        
        # Update last activity
        session['last_activity'] = datetime.utcnow()
        return True

def token_required(auth_manager, optional=False):
    """Decorator for routes requiring authentication"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove 'Bearer ' prefix
            
            if not token:
                if optional:
                    return f(None, *args, **kwargs)
                return jsonify({'message': 'Token is missing'}), 401
            
            payload, error = auth_manager.verify_token(token)
            if error:
                if optional:
                    return f(None, *args, **kwargs)
                return jsonify({'message': error}), 401
            
            return f(payload['user_id'], *args, **kwargs)
        
        return decorated
    return decorator

def load_users(filepath='users.json'):
    """Load users from JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_users(users, filepath='users.json'):
    """Save users to JSON file"""
    with open(filepath, 'w') as f:
        json.dump(users, f, indent=2)

def create_user(username, password, auth_manager, filepath='users.json'):
    """Create new user with hashed password"""
    users = load_users(filepath)
    
    if username in users:
        return False, "User already exists"
    
    # Validate password strength
    is_valid, message = auth_manager.validate_password_strength(password)
    if not is_valid:
        return False, message
    
    # Hash password and store
    hashed_password = auth_manager.hash_password(password)
    users[username] = {
        'password': hashed_password,
        'created_at': datetime.utcnow().isoformat(),
        'last_login': None,
        'active': True
    }
    
    save_users(users, filepath)
    return True, "User created successfully"

def authenticate_user(username, password, auth_manager, filepath='users.json'):
    """Authenticate user credentials"""
    users = load_users(filepath)
    
    if username not in users:
        return False, "Invalid credentials"
    
    user = users[username]
    
    # Handle legacy string format (old users.json format)
    if isinstance(user, str):
        # Legacy format: username -> plain password
        if user == password:
            # Convert to new format
            hashed_password = auth_manager.hash_password(password)
            users[username] = {
                'password': hashed_password,
                'created_at': datetime.utcnow().isoformat(),
                'last_login': datetime.utcnow().isoformat(),
                'active': True,
                'role': 'viewer'
            }
            save_users(users, filepath)
            return True, "Authentication successful"
        else:
            return False, "Invalid credentials"
    
    # Handle new dictionary format
    if not isinstance(user, dict):
        return False, "Invalid user data format"
    
    # Check if user is active
    if not user.get('active', True):
        return False, "Account is disabled"
    
    # Verify password
    if not auth_manager.verify_password(password, user['password']):
        return False, "Invalid credentials"
    
    # Update last login
    user['last_login'] = datetime.utcnow().isoformat()
    save_users(users, filepath)
    
    return True, "Authentication successful"
