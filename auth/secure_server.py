from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from auth_utils import AuthManager, token_required, authenticate_user, create_user, load_users, save_users
from rbac_utils import (RBACManager, Role, Permission, require_permission, require_role, 
                       get_role_description, create_default_super_admin)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize CORS with specific origins
cors_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
CORS(app, origins=cors_origins, supports_credentials=True)

# Initialize rate limiter
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=[os.environ.get('DEFAULT_RATE_LIMIT', '100 per hour')],
    storage_uri=os.environ.get('RATE_LIMIT_STORAGE_URL', 'memory://')
)

# Configure Flask app
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES', 604800))
app.config['BCRYPT_LOG_ROUNDS'] = int(os.environ.get('BCRYPT_LOG_ROUNDS', 12))
app.config['MAX_LOGIN_ATTEMPTS'] = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
app.config['LOGIN_ATTEMPT_WINDOW'] = int(os.environ.get('LOGIN_ATTEMPT_WINDOW', 300))

# Initialize auth and RBAC managers
auth_manager = AuthManager(app)
rbac_manager = RBACManager()

@app.before_request
def add_security_headers():
    """Add security headers to all responses"""
    pass

@app.after_request
def after_request(response):
    """Add security headers after each request"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https:; font-src 'self' https://fonts.gstatic.com"
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """Enhanced login endpoint with rate limiting and security"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request format'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Input validation
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        if len(username) > 50 or len(password) > 128:
            return jsonify({'message': 'Invalid input length'}), 400
        
        # Get client IP for rate limiting
        client_ip = auth_manager.get_client_ip(request)
        identifier = f"{username}:{client_ip}"
        
        # Check rate limiting
        if not auth_manager.check_rate_limit(identifier):
            return jsonify({
                'message': 'Too many failed attempts. Please try again later.'
            }), 429
        
        # Authenticate user
        success, message = authenticate_user(username, password, auth_manager, 'users.json')
        
        if not success:
            auth_manager.record_failed_attempt(identifier)
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Clear failed attempts on successful login
        auth_manager.clear_failed_attempts(identifier)
        
        # Generate tokens
        access_token, refresh_token, session_id = auth_manager.generate_tokens(username)
        
        # Get user role and permissions
        user_role = rbac_manager.get_user_role(username)
        
        # Log successful login
        log_security_event('login_success', {
            'username': username,
            'role': user_role.value if user_role else 'unknown',
            'ip': client_ip,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'session_id': session_id,
            'user': username,
            'role': user_role.value if user_role else 'viewer',
            'expires_in': app.config['JWT_ACCESS_TOKEN_EXPIRES']
        })
        
    except Exception as e:
        log_security_event('login_error', {
            'error': str(e),
            'ip': auth_manager.get_client_ip(request),
            'timestamp': datetime.utcnow().isoformat()
        })
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/refresh', methods=['POST'])
@limiter.limit("10 per minute")
def refresh_token():
    """Refresh access token using refresh token"""
    try:
        data = request.get_json()
        if not data or 'refresh_token' not in data:
            return jsonify({'message': 'Refresh token is required'}), 400
        
        refresh_token = data['refresh_token']
        
        # Generate new access token
        new_access_token, user_id, error = auth_manager.refresh_access_token(refresh_token)
        
        if error:
            return jsonify({'message': error}), 401
        
        return jsonify({
            'access_token': new_access_token,
            'expires_in': app.config['JWT_ACCESS_TOKEN_EXPIRES']
        })
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/logout', methods=['POST'])
@token_required(auth_manager)
def logout(current_user):
    """Logout and revoke tokens"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        refresh_token = data.get('refresh_token')
        
        # Get access token from header
        auth_header = request.headers.get('Authorization')
        access_token = auth_header[7:] if auth_header and auth_header.startswith('Bearer ') else None
        
        # Logout session
        auth_manager.logout_session(session_id, access_token, refresh_token)
        
        # Log logout
        log_security_event('logout', {
            'username': current_user,
            'ip': auth_manager.get_client_ip(request),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({'message': 'Logged out successfully'})
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

# ADMIN USER MANAGEMENT ENDPOINTS

@app.route('/api/admin/users', methods=['GET'])
@token_required(auth_manager)
@require_permission(Permission.VIEW_USERS)
def list_users(current_user):
    """List all users (admin only)"""
    try:
        users = load_users('users.json')
        current_user_role = rbac_manager.get_user_role(current_user)
        
        user_list = []
        for username, user_data in users.items():
            if isinstance(user_data, str):
                # Legacy user format
                user_info = {
                    'username': username,
                    'role': 'viewer',
                    'active': True,
                    'created_at': None,
                    'last_login': None,
                    'legacy': True
                }
            else:
                user_role = Role(user_data.get('role', 'viewer'))
                
                # Check if current user can view this user
                if not rbac_manager.can_manage_user(current_user_role, user_role):
                    continue
                
                user_info = {
                    'username': username,
                    'role': user_data.get('role', 'viewer'),
                    'role_description': get_role_description(user_role),
                    'active': user_data.get('active', True),
                    'created_at': user_data.get('created_at'),
                    'created_by': user_data.get('created_by'),
                    'last_login': user_data.get('last_login'),
                    'is_super_admin': user_data.get('is_super_admin', False)
                }
            
            user_list.append(user_info)
        
        return jsonify({
            'users': user_list,
            'total': len(user_list),
            'manageable_roles': [role.value for role in rbac_manager.get_manageable_roles(current_user_role)]
        })
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/admin/users', methods=['POST'])
@token_required(auth_manager)
@require_permission(Permission.CREATE_USER)
def create_new_user(current_user):
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request format'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'viewer')
        
        # Input validation
        if not username or not password:
            return jsonify({'message': 'Username and password are required'}), 400
        
        if len(username) < 3 or len(username) > 50:
            return jsonify({'message': 'Username must be between 3 and 50 characters'}), 400
        
        # Validate role
        try:
            target_role = Role(role)
        except ValueError:
            return jsonify({'message': 'Invalid role specified'}), 400
        
        # Check if current user can assign this role
        current_user_role = rbac_manager.get_user_role(current_user)
        manageable_roles = rbac_manager.get_manageable_roles(current_user_role)
        
        if target_role not in manageable_roles:
            return jsonify({'message': 'Insufficient permissions to assign this role'}), 403
        
        # Create user
        users = load_users('users.json')
        
        if username in users:
            return jsonify({'message': 'User already exists'}), 400
        
        # Validate password strength
        is_valid, message = auth_manager.validate_password_strength(password)
        if not is_valid:
            return jsonify({'message': message}), 400
        
        # Hash password and store
        hashed_password = auth_manager.hash_password(password)
        users[username] = {
            'password': hashed_password,
            'role': target_role.value,
            'created_at': datetime.utcnow().isoformat(),
            'created_by': current_user,
            'last_login': None,
            'active': True
        }
        
        save_users(users, 'users.json')
        
        # Log user creation
        log_security_event('user_created', {
            'username': username,
            'role': target_role.value,
            'created_by': current_user,
            'ip': auth_manager.get_client_ip(request),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({'message': 'User created successfully'}), 201
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/admin/users/<username>', methods=['PUT'])
@token_required(auth_manager)
@require_permission(Permission.MODIFY_USER)
def modify_user(current_user, username):
    """Modify user (admin only)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid request format'}), 400
        
        users = load_users('users.json')
        
        if username not in users:
            return jsonify({'message': 'User not found'}), 404
        
        current_user_role = rbac_manager.get_user_role(current_user)
        target_user_role = rbac_manager.get_user_role(username)
        
        # Check if current user can manage target user
        if not rbac_manager.can_manage_user(current_user_role, target_user_role):
            return jsonify({'message': 'Insufficient permissions to modify this user'}), 403
        
        user_data = users[username]
        if isinstance(user_data, str):
            # Convert legacy user to new format
            user_data = {
                'password': auth_manager.hash_password(user_data),
                'role': 'viewer',
                'created_at': datetime.utcnow().isoformat(),
                'created_by': current_user,
                'last_login': None,
                'active': True
            }
        
        # Update fields
        if 'role' in data:
            new_role = Role(data['role'])
            manageable_roles = rbac_manager.get_manageable_roles(current_user_role)
            
            if new_role not in manageable_roles:
                return jsonify({'message': 'Insufficient permissions to assign this role'}), 403
            
            user_data['role'] = new_role.value
        
        if 'active' in data:
            user_data['active'] = bool(data['active'])
        
        if 'password' in data and data['password']:
            # Validate password strength
            is_valid, message = auth_manager.validate_password_strength(data['password'])
            if not is_valid:
                return jsonify({'message': message}), 400
            
            user_data['password'] = auth_manager.hash_password(data['password'])
        
        user_data['modified_at'] = datetime.utcnow().isoformat()
        user_data['modified_by'] = current_user
        
        users[username] = user_data
        save_users(users, 'users.json')
        
        # Log user modification
        log_security_event('user_modified', {
            'username': username,
            'modified_by': current_user,
            'changes': list(data.keys()),
            'ip': auth_manager.get_client_ip(request),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({'message': 'User updated successfully'})
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/admin/users/<username>', methods=['DELETE'])
@token_required(auth_manager)
@require_permission(Permission.DELETE_USER)
def delete_user(current_user, username):
    """Delete user (super admin only)"""
    try:
        if username == current_user:
            return jsonify({'message': 'Cannot delete your own account'}), 400
        
        users = load_users('users.json')
        
        if username not in users:
            return jsonify({'message': 'User not found'}), 404
        
        current_user_role = rbac_manager.get_user_role(current_user)
        target_user_role = rbac_manager.get_user_role(username)
        
        # Check if current user can manage target user
        if not rbac_manager.can_manage_user(current_user_role, target_user_role):
            return jsonify({'message': 'Insufficient permissions to delete this user'}), 403
        
        # Prevent deletion of last super admin
        if target_user_role == Role.SUPER_ADMIN:
            super_admin_count = sum(1 for user_data in users.values() 
                                  if isinstance(user_data, dict) and 
                                  user_data.get('role') == Role.SUPER_ADMIN.value and 
                                  user_data.get('active', True))
            
            if super_admin_count <= 1:
                return jsonify({'message': 'Cannot delete the last super admin'}), 400
        
        del users[username]
        save_users(users, 'users.json')
        
        # Log user deletion
        log_security_event('user_deleted', {
            'username': username,
            'deleted_by': current_user,
            'ip': auth_manager.get_client_ip(request),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        return jsonify({'message': 'User deleted successfully'})
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/admin/roles', methods=['GET'])
@token_required(auth_manager)
@require_permission(Permission.VIEW_USERS)
def get_roles(current_user):
    """Get available roles and their descriptions"""
    try:
        current_user_role = rbac_manager.get_user_role(current_user)
        manageable_roles = rbac_manager.get_manageable_roles(current_user_role)
        
        roles_info = []
        for role in manageable_roles:
            roles_info.append({
                'value': role.value,
                'name': role.value.replace('_', ' ').title(),
                'description': get_role_description(role),
                'level': rbac_manager.role_hierarchy[role]
            })
        
        return jsonify({'roles': roles_info})
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/user/profile', methods=['GET'])
@token_required(auth_manager)
def get_user_profile(current_user):
    """Get current user profile"""
    try:
        users = load_users('users.json')
        user_data = users.get(current_user, {})
        user_role = rbac_manager.get_user_role(current_user)
        
        if isinstance(user_data, str):
            # Legacy user
            profile = {
                'username': current_user,
                'role': 'viewer',
                'role_description': get_role_description(Role.VIEWER),
                'created_at': None,
                'last_login': None,
                'active': True,
                'legacy': True
            }
        else:
            profile = {
                'username': current_user,
                'role': user_data.get('role', 'viewer'),
                'role_description': get_role_description(user_role),
                'created_at': user_data.get('created_at'),
                'last_login': user_data.get('last_login'),
                'active': user_data.get('active', True),
                'is_super_admin': user_data.get('is_super_admin', False)
            }
        
        return jsonify(profile)
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/alerts', methods=['GET'])
@token_required(auth_manager)
@require_permission(Permission.VIEW_ALERTS)
def get_alerts(current_user):
    """Get security alerts for authenticated user"""
    try:
        # Sample alerts with anomaly scores and enhanced data
        sample_alerts = [
            {
                'id': 1,
                'timestamp': '2025-08-20 12:30:00',
                'alert': 'Suspicious login attempt from 192.168.1.100',
                'severity': 'High',
                'anomaly_score': 0.85,
                'source_ip': '192.168.1.100',
                'user': 'admin',
                'status': 'active'
            },
            {
                'id': 2,
                'timestamp': '2025-08-20 12:25:00',
                'alert': 'Malware detected on host server-01',
                'severity': 'Critical',
                'anomaly_score': 0.95,
                'source_ip': '10.0.1.50',
                'user': 'system',
                'status': 'active'
            },
            {
                'id': 3,
                'timestamp': '2025-08-20 12:20:00',
                'alert': 'Data exfiltration attempt from internal network',
                'severity': 'High',
                'anomaly_score': 0.78,
                'source_ip': '192.168.2.45',
                'user': 'john.doe',
                'status': 'active'
            },
            {
                'id': 4,
                'timestamp': '2025-08-20 12:15:00',
                'alert': 'Multiple failed login attempts for user "admin"',
                'severity': 'Medium',
                'anomaly_score': 0.65,
                'source_ip': '203.0.113.10',
                'user': 'admin',
                'status': 'active'
            },
            {
                'id': 5,
                'timestamp': '2025-08-20 12:10:00',
                'alert': 'Denial of service attack detected on web server',
                'severity': 'High',
                'anomaly_score': 0.82,
                'source_ip': '198.51.100.25',
                'user': 'unknown',
                'status': 'active'
            }
        ]
        
        # Sort by anomaly score (highest first)
        sorted_alerts = sorted(sample_alerts, key=lambda x: x['anomaly_score'], reverse=True)
        return jsonify(sorted_alerts)
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/alerts/<int:alert_id>/action', methods=['POST'])
@token_required(auth_manager)
@require_permission(Permission.FLAG_ALERTS)
def alert_action(current_user, alert_id):
    """Handle alert actions (flag/dismiss)"""
    try:
        data = request.get_json()
        if not data or 'action' not in data:
            return jsonify({'message': 'Action is required'}), 400
        
        action = data.get('action')
        if action not in ['flag', 'dismiss']:
            return jsonify({'message': 'Invalid action'}), 400
        
        # Check if user has permission for dismiss action
        if action == 'dismiss':
            user_role = rbac_manager.get_user_role(current_user)
            if not rbac_manager.has_permission(user_role, Permission.DISMISS_ALERTS):
                return jsonify({'message': 'Insufficient permissions to dismiss alerts'}), 403
        
        # Log the action for future retraining
        log_entry = {
            'user': current_user,
            'alert_id': alert_id,
            'action': action,
            'timestamp': datetime.utcnow().isoformat(),
            'ip': auth_manager.get_client_ip(request)
        }
        
        # Ensure logs directory exists
        os.makedirs('../logs', exist_ok=True)
        
        # Append to feedback log
        try:
            with open('../logs/feedback.json', 'r') as f:
                feedback_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            feedback_logs = []
        
        feedback_logs.append(log_entry)
        
        with open('../logs/feedback.json', 'w') as f:
            json.dump(feedback_logs, f, indent=2)
        
        return jsonify({'message': f'Alert {alert_id} {action}ed successfully'})
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
@token_required(auth_manager)
@require_permission(Permission.VIEW_STATISTICS)
def get_stats(current_user):
    """Get security statistics"""
    try:
        stats = {
            'total_alerts': 5,
            'high_severity': 3,
            'medium_severity': 1,
            'critical_severity': 1,
            'avg_anomaly_score': 0.81,
            'active_sessions': len(auth_manager.active_sessions),
            'failed_attempts_today': len([
                attempt for attempts in auth_manager.failed_attempts.values()
                for attempt in attempts
                if attempt > datetime.utcnow() - timedelta(days=1)
            ])
        }
        
        # Add admin-only stats
        user_role = rbac_manager.get_user_role(current_user)
        if rbac_manager.has_permission(user_role, Permission.VIEW_USERS):
            users = load_users('users.json')
            stats['total_users'] = len(users)
            stats['active_users'] = sum(1 for user in users.values() 
                                      if isinstance(user, dict) and user.get('active', True))
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'message': 'Internal server error'}), 500

def log_security_event(event_type, data):
    """Log security events for monitoring"""
    try:
        os.makedirs('../logs', exist_ok=True)
        
        log_entry = {
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            **data
        }
        
        # Append to security log
        try:
            with open('../logs/security.json', 'r') as f:
                security_logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            security_logs = []
        
        security_logs.append(log_entry)
        
        # Keep only last 1000 entries
        if len(security_logs) > 1000:
            security_logs = security_logs[-1000:]
        
        with open('../logs/security.json', 'w') as f:
            json.dump(security_logs, f, indent=2)
            
    except Exception as e:
        print(f"Failed to log security event: {e}")

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('../ui', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../ui', path)

# Error handlers
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'message': 'Rate limit exceeded. Please try again later.'}), 429

@app.errorhandler(404)
def not_found(e):
    return jsonify({'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure users file exists with default super admin user
    if not os.path.exists('users.json'):
        print("Creating default super admin user...")
        success, message = create_default_super_admin('admin', 'SecurePass123!', auth_manager, 'users.json')
        if success:
            print("Default super admin user created:")
            print("Username: admin")
            print("Password: SecurePass123!")
            print("Role: super_admin")
        else:
            print(f"Failed to create super admin user: {message}")
    
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true', 
            host='0.0.0.0', port=5000)
