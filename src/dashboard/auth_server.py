#!/usr/bin/env python3
"""
SOC Dashboard Backend Server with Authentication
Enhanced with JWT authentication, MFA, RBAC, and audit logging
"""

import os
import sys
import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.dashboard.server import SOCDashboardAPI
from src.utils.csv_processor import CSVProcessor
from src.auth.auth_utils import (
    AuthManager, token_required, admin_required, analyst_or_admin_required,
    log_login_attempt, log_user_action, log_mfa_setup, log_password_change,
    log_monitoring_control, log_unauthorized_access, audit_logger
)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'soc-dashboard-secret-key-change-in-production')
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"], logger=True, engineio_logger=True)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per hour"]
)
limiter.init_app(app)

# Initialize authentication manager
auth_manager = AuthManager()
app.auth_manager = auth_manager

# Initialize dashboard API
dashboard_api = SOCDashboardAPI()

# Initialize CSV processor with shared detector for consistent predictions
csv_processor = CSVProcessor(
    detector=dashboard_api.detector,
    upload_dir="src/dashboard/data/uploads",
    reports_dir="src/dashboard/data/reports"
)

def get_client_info():
    """Extract client IP and user agent from request"""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.headers.get('User-Agent', '')
    return ip_address, user_agent

# Authentication endpoints
@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    """User login with optional MFA"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        mfa_token = data.get('mfa_token')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        ip_address, user_agent = get_client_info()
        
        # Authenticate user
        success, message, user_info = auth_manager.authenticate_user(username, password, mfa_token)
        
        if not success:
            log_login_failed(username, ip_address, user_agent, message)
            return jsonify({'error': message, 'mfa_required': user_info.get('mfa_required', False)}), 401
        
        # Generate tokens
        access_token, refresh_token = auth_manager.generate_tokens(username, user_info['role'])
        
        log_login_success(username, ip_address, user_agent)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_info,
            'expires_in': 28800  # 8 hours in seconds
        })
        
    except Exception as e:
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400
        
        success, access_token, new_refresh_token = auth_manager.refresh_access_token(refresh_token)
        
        if not success:
            return jsonify({'error': access_token}), 401
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': new_refresh_token,
            'expires_in': 28800
        })
        
    except Exception as e:
        return jsonify({'error': 'Token refresh failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout():
    """User logout"""
    try:
        username = request.current_user['username']
        ip_address, _ = get_client_info()
        
        log_logout(username, ip_address)
        
        return jsonify({'message': 'Logged out successfully'})
        
    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile"""
    try:
        username = request.current_user['username']
        users = auth_manager._load_users()
        
        if username not in users:
            return jsonify({'error': 'User not found'}), 404
        
        user = users[username]
        profile = {
            'username': username,
            'role': user['role'],
            'email': user['email'],
            'mfa_enabled': user.get('mfa_enabled', False),
            'created_at': user['created_at'],
            'last_login': user.get('last_login')
        }
        
        return jsonify(profile)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get profile'}), 500

@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Old and new passwords required'}), 400
        
        username = request.current_user['username']
        success, message = auth_manager.change_password(username, old_password, new_password)
        
        if not success:
            return jsonify({'error': message}), 400
        
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'error': 'Password change failed'}), 500

# MFA endpoints
@app.route('/api/auth/mfa/setup', methods=['POST'])
@token_required
def setup_mfa():
    """Setup MFA for current user"""
    try:
        username = request.current_user['username']
        success, secret, qr_code = auth_manager.setup_mfa(username)
        
        if not success:
            return jsonify({'error': secret}), 400
        
        return jsonify({
            'secret': secret,
            'qr_code': qr_code,
            'message': 'MFA setup initiated. Please verify with your authenticator app.'
        })
        
    except Exception as e:
        return jsonify({'error': 'MFA setup failed'}), 500

@app.route('/api/auth/mfa/enable', methods=['POST'])
@token_required
def enable_mfa():
    """Enable MFA after verification"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'MFA token required'}), 400
        
        username = request.current_user['username']
        success, message = auth_manager.enable_mfa(username, token)
        
        if not success:
            return jsonify({'error': message}), 400
        
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'error': 'MFA enable failed'}), 500

@app.route('/api/auth/mfa/disable', methods=['POST'])
@token_required
def disable_mfa():
    """Disable MFA for current user"""
    try:
        username = request.current_user['username']
        success, message = auth_manager.disable_mfa(username)
        
        if not success:
            return jsonify({'error': message}), 400
        
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'error': 'MFA disable failed'}), 500

# Admin user management endpoints
@app.route('/api/admin/users', methods=['GET'])
@token_required
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        users = auth_manager.get_users()
        return jsonify({'users': users})
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users'}), 500

@app.route('/api/admin/users', methods=['POST'])
@token_required
@admin_required
def create_user():
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        email = data.get('email')
        
        if not all([username, password, role, email]):
            return jsonify({'error': 'Username, password, role, and email required'}), 400
        
        success, message = auth_manager.create_user(username, password, role, email)
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Log user creation
        admin_username = request.current_user['username']
        ip_address, _ = get_client_info()
        log_user_created(admin_username, username, role, ip_address)
        
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'error': 'User creation failed'}), 500

@app.route('/api/admin/users/<username>', methods=['PUT'])
@token_required
@admin_required
def update_user(username):
    """Update user (admin only)"""
    try:
        data = request.get_json()
        
        success, message = auth_manager.update_user(username, data)
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Log user update
        admin_username = request.current_user['username']
        ip_address, _ = get_client_info()
        log_user_updated(admin_username, username, data, ip_address)
        
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'error': 'User update failed'}), 500

@app.route('/api/admin/users/<username>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(username):
    """Delete user (admin only)"""
    try:
        admin_username = request.current_user['username']
        success, message = auth_manager.delete_user(username, admin_username)
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Log user deletion
        ip_address, _ = get_client_info()
        log_user_deleted(admin_username, username, ip_address)
        
        return jsonify({'message': message})
        
    except Exception as e:
        return jsonify({'error': 'User deletion failed'}), 500

# Audit endpoints
@app.route('/api/admin/audit', methods=['GET'])
@token_required
@admin_required
def get_audit_logs():
    """Get audit logs (admin only)"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        username = request.args.get('username')
        event_type = request.args.get('event_type')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        logs = audit_logger.get_audit_logs(start_date, end_date, username, event_type, limit, offset)
        
        return jsonify({'logs': logs, 'total': len(logs)})
        
    except Exception as e:
        return jsonify({'error': 'Failed to get audit logs'}), 500

@app.route('/api/admin/audit/summary', methods=['GET'])
@token_required
@admin_required
def get_audit_summary():
    """Get audit summary (admin only)"""
    try:
        days = int(request.args.get('days', 30))
        summary = audit_logger.get_audit_summary(days)
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get audit summary'}), 500

@app.route('/api/admin/security-alerts', methods=['GET'])
@token_required
@admin_required
def get_security_alerts():
    """Get security alerts (admin only)"""
    try:
        days = int(request.args.get('days', 7))
        alerts = audit_logger.get_security_alerts(days)
        
        return jsonify({'alerts': alerts})
        
    except Exception as e:
        return jsonify({'error': 'Failed to get security alerts'}), 500

# Protected SOC Dashboard endpoints
@app.route('/api/alerts')
@token_required
@analyst_or_admin_required
def get_alerts():
    """Get alerts with filtering and pagination"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        severity = request.args.get('severity')
        status = request.args.get('status')
        
        alerts = dashboard_api.current_alerts.copy()
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        if status:
            alerts = [a for a in alerts if a['status'] == status]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        paginated_alerts = alerts[start:end]
        
        return jsonify({
            'alerts': paginated_alerts,
            'total': len(alerts),
            'page': page,
            'per_page': per_page,
            'total_pages': (len(alerts) + per_page - 1) // per_page
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to get alerts'}), 500

@app.route('/api/stats')
@token_required
@analyst_or_admin_required
def get_stats():
    """Get system statistics"""
    try:
        return jsonify(dashboard_api.get_system_stats())
    except Exception as e:
        return jsonify({'error': 'Failed to get stats'}), 500

@app.route('/api/threshold', methods=['GET', 'POST'])
@token_required
@analyst_or_admin_required
def threshold_endpoint():
    """Get or update detection threshold"""
    try:
        if request.method == 'POST':
            data = request.get_json()
            old_threshold = dashboard_api.threshold
            new_threshold = float(data.get('threshold', dashboard_api.threshold))
            
            if 0.0 <= new_threshold <= 1.0:
                dashboard_api.threshold = new_threshold
                
                # Log threshold change
                username = request.current_user['username']
                ip_address, _ = get_client_info()
                log_threshold_change(username, old_threshold, new_threshold, ip_address)
                
                return jsonify({'success': True, 'threshold': dashboard_api.threshold})
            else:
                return jsonify({'error': 'Threshold must be between 0.0 and 1.0'}), 400
        
        return jsonify({'threshold': dashboard_api.threshold})
        
    except Exception as e:
        return jsonify({'error': 'Threshold operation failed'}), 500

@app.route('/api/alerts/<int:alert_id>/flag', methods=['POST'])
@token_required
@analyst_or_admin_required
def flag_alert(alert_id):
    """Flag an alert"""
    try:
        for alert in dashboard_api.current_alerts:
            if alert['id'] == alert_id:
                alert['flagged'] = True
                alert['status'] = 'flagged'
                
                # Log alert action
                username = request.current_user['username']
                ip_address, _ = get_client_info()
                log_alert_action(username, alert_id, 'flag', ip_address)
                
                return jsonify({'success': True})
        
        return jsonify({'error': 'Alert not found'}), 404
        
    except Exception as e:
        return jsonify({'error': 'Failed to flag alert'}), 500

@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
@token_required
@analyst_or_admin_required
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    try:
        for alert in dashboard_api.current_alerts:
            if alert['id'] == alert_id:
                alert['dismissed'] = True
                alert['status'] = 'dismissed'
                
                # Log alert action
                username = request.current_user['username']
                ip_address, _ = get_client_info()
                log_alert_action(username, alert_id, 'dismiss', ip_address)
                
                return jsonify({'success': True})
        
        return jsonify({'error': 'Alert not found'}), 404
        
    except Exception as e:
        return jsonify({'error': 'Failed to dismiss alert'}), 500

@app.route('/api/monitoring/start', methods=['POST'])
@token_required
@analyst_or_admin_required
def start_monitoring():
    """Start real-time monitoring"""
    try:
        dashboard_api.start_monitoring()
        
        # Log monitoring action
        username = request.current_user['username']
        ip_address, _ = get_client_info()
        log_monitoring_control(username, 'start', ip_address)
        
        return jsonify({'success': True, 'status': 'monitoring_started'})
        
    except Exception as e:
        return jsonify({'error': 'Failed to start monitoring'}), 500

@app.route('/api/monitoring/stop', methods=['POST'])
@token_required
@analyst_or_admin_required
def stop_monitoring():
    """Stop real-time monitoring"""
    try:
        dashboard_api.stop_monitoring()
        
        # Log monitoring action
        username = request.current_user['username']
        ip_address, _ = get_client_info()
        log_monitoring_control(username, 'stop', ip_address)
        
        return jsonify({'success': True, 'status': 'monitoring_stopped'})
        
    except Exception as e:
        return jsonify({'error': 'Failed to stop monitoring'}), 500

@app.route('/api/score-distribution')
@token_required
@analyst_or_admin_required
def get_score_distribution():
    """Get anomaly score distribution for visualization"""
    try:
        scores = [alert['anomaly_score'] for alert in dashboard_api.current_alerts]
        
        if not scores:
            return jsonify({'bins': [], 'counts': []})
        
        # Create histogram data
        import numpy as np
        hist, bin_edges = np.histogram(scores, bins=20, range=(0, 1))
        bins = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(hist))]
        
        return jsonify({
            'bins': bins,
            'counts': hist.tolist(),
            'total_samples': len(scores)
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to get score distribution'}), 500

# WebSocket authentication
def authenticate_socket(auth_data):
    """Authenticate WebSocket connection"""
    try:
        token = auth_data.get('token')
        if not token:
            return False, None
        
        valid, payload = auth_manager.verify_token(token)
        if not valid:
            return False, None
        
        return True, payload
    except:
        return False, None

# WebSocket Events with authentication
@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection with authentication"""
    try:
        # Authenticate the connection
        authenticated, user_payload = authenticate_socket(auth or {})
        
        if not authenticated:
            print('Unauthenticated WebSocket connection attempt')
            disconnect()
            return False
        
        print(f'Authenticated client connected: {user_payload.get("username")}')
        emit('connection_established', {
            'status': 'connected',
            'user': user_payload.get('username')
        })
        emit('stats_update', dashboard_api.get_system_stats())
        
    except Exception as e:
        print(f'Connection error: {e}')
        disconnect()

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_alerts')
def handle_request_alerts(auth):
    """Send current alerts to authenticated client"""
    try:
        authenticated, user_payload = authenticate_socket(auth or {})
        
        if not authenticated:
            disconnect()
            return
        
        emit('alerts_update', {
            'alerts': dashboard_api.current_alerts[-20:],  # Last 20 alerts
            'stats': dashboard_api.get_system_stats()
        })
        
    except Exception as e:
        print(f'Request alerts error: {e}')

# CSV Upload and Analysis Endpoints
@app.route('/api/csv/upload', methods=['POST'])
@token_required
@analyst_or_admin_required
def upload_csv():
    """Upload CSV file for anomaly detection analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400
        
        # Process the file using csv_processor
        result = csv_processor.upload_file(file)
        
        # Log the upload
        client_ip, user_agent = get_client_info()
        log_user_action(
            user_id=request.current_user.get('user_id'),
            action='csv_upload',
            details=f'Uploaded CSV file: {file.filename}',
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"CSV upload error: {e}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/api/csv/analyze', methods=['POST'])
@token_required
@analyst_or_admin_required
def analyze_csv():
    """Analyze uploaded CSV file for anomalies"""
    try:
        data = request.get_json()
        if not data or 'file_id' not in data:
            return jsonify({'error': 'File ID required'}), 400
        
        file_id = data['file_id']
        sample_size = data.get('sample_size')
        
        # Process the analysis using csv_processor
        result = csv_processor.analyze_file(file_id, sample_size=sample_size)
        
        # Log the analysis
        client_ip, user_agent = get_client_info()
        log_user_action(
            user_id=request.current_user.get('user_id'),
            action='csv_analysis',
            details=f'Analyzed CSV file: {file_id}, Sample size: {sample_size}',
            client_ip=client_ip,
            user_agent=user_agent
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"CSV analysis error: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/csv/reports', methods=['GET'])
@token_required
@analyst_or_admin_required
def get_csv_reports():
    """Get list of CSV analysis reports"""
    try:
        reports = csv_processor.get_reports()
        return jsonify({'reports': reports}), 200
    except Exception as e:
        print(f"Error getting reports: {e}")
        return jsonify({'error': 'Failed to get reports'}), 500

@app.route('/api/csv/reports/<report_id>', methods=['GET'])
@token_required
@analyst_or_admin_required
def get_csv_report(report_id):
    """Get specific CSV analysis report"""
    try:
        report = csv_processor.get_report(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        return jsonify(report), 200
    except Exception as e:
        print(f"Error getting report {report_id}: {e}")
        return jsonify({'error': 'Failed to get report'}), 500

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized access'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Insufficient permissions'}), 403

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded'}), 429

if __name__ == '__main__':
    print("Starting SOC Dashboard Server with Authentication...")
    print("Dashboard will be available at http://localhost:5000")
    print("Default admin credentials: admin / SecureAdmin123!")
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Start monitoring by default
    dashboard_api.start_monitoring()
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
