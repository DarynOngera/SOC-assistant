#!/usr/bin/env python3
"""
SOC Dashboard Backend Server
Real-time anomaly detection API with WebSocket support and Authentication
"""

import os
import sys
import json
import time
import threading
import numpy as np
import tempfile
# import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, disconnect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import joblib
import glob
import uuid

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
\
from src.auth.auth_utils import AuthManager, token_required, admin_required, analyst_or_admin_required
from src.auth.audit_logger import (
    AuditLogger, AuditEventType, log_login_success, log_login_failed, log_logout, log_user_created,
    log_user_updated, log_user_deleted, log_alert_action, log_threshold_change,
    log_monitoring_control, log_unauthorized_access, audit_logger
)
from src.utils.csv_processor import CSVProcessor

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'soc-dashboard-secret-key-change-in-production')
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"], logger=True, engineio_logger=True)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["1000 per hour"]
)

# Initialize auth manager and audit logger
auth_manager = AuthManager()
audit_logger = AuditLogger(log_file="src/dashboard/data/audit.log", json_file="src/dashboard/data/audit.json")

# Attach auth manager to Flask app for decorator access
app.auth_manager = auth_manager

def get_client_info():
    """Extract client IP and user agent from request"""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.headers.get('User-Agent', '')
    return ip_address, user_agent

class SOCDashboardAPI:
    def __init__(self):
        self.detector = None
        self.current_alerts = []
        self.alert_history = []
        self.system_stats = {
            'total_processed': 0,
            'anomalies_detected': 0,
            'false_positives': 0,
            'system_health': 'healthy'
        }
        self.threshold = 0.5
        self.is_monitoring = False
        self.next_alert_id = int(time.time() * 1000)  # Start with timestamp-based ID for uniqueness
        self.load_models()
        
    def load_models(self):
        """Load the latest trained models"""
        try:
            # Try to import and initialize the detector
            from src.models.supervised_trainer import SupervisedSOCDetector
            self.detector = SupervisedSOCDetector()
            
            model_dir = 'models'
            if os.path.exists(model_dir):
                self.detector.load_models(model_dir)
                print("Models loaded successfully")
            else:
                print("No trained models found. Using mock data mode.")
        except Exception as e:
            print(f"Error loading models: {e}. Using mock data mode.")
            self.detector = None
    
    def generate_realistic_network_data(self, batch_size=10):
        """Generate realistic network traffic data using model's feature template (network traffic only)"""
        np.random.seed(int(time.time()) % 1000)
        
        # Initialize feature_columns with default value
        feature_columns = []
        
        # Get feature template from the trained model
        if self.detector:
            try:
                template = self.detector.get_feature_template()
                feature_columns = template.get('feature_columns', [])
            except Exception as e:
                print(f"Warning: Could not get feature template: {e}")
                feature_columns = []
        
        if not feature_columns:
            # Fallback to standard network features
            feature_columns = [
                'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
                'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
                'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
                'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
                'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
                'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
                'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
                'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
                'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
                'dst_host_rerror_rate', 'dst_host_srv_rerror_rate'
            ]
        
        data = []
        for i in range(batch_size):
            # Generate realistic network traffic features
            record = {
                'timestamp': datetime.now() - timedelta(seconds=i),
                'src_ip': f"192.168.{int(np.random.randint(1,255))}.{int(np.random.randint(1,255))}",
                'dst_ip': f"10.0.{int(np.random.randint(1,255))}.{int(np.random.randint(1,255))}",
                'src_port': int(np.random.randint(1024, 65535)),
                'dst_port': int(np.random.choice([22, 23, 80, 443, 3389, 1433, 53, 25])),
                'proto': str(np.random.choice(['tcp', 'udp', 'icmp'])),
            }
            
            # Generate features that match the model's expected input
            for feature in feature_columns:
                if 'rate' in feature or 'error' in feature:
                    # Rate features (0-1)
                    record[feature] = float(np.random.beta(2, 8))  # Skewed towards lower values
                elif 'count' in feature:
                    # Count features
                    record[feature] = int(np.random.poisson(10))
                elif 'bytes' in feature:
                    # Byte counts
                    record[feature] = int(np.random.exponential(1000))
                elif feature in ['land', 'wrong_fragment', 'urgent', 'logged_in', 'root_shell', 'su_attempted', 'is_host_login', 'is_guest_login']:
                    # Binary features
                    record[feature] = int(np.random.choice([0, 1], p=[0.9, 0.1]))
                elif feature == 'duration':
                    record[feature] = float(np.random.exponential(100))
                elif feature in ['protocol_type', 'service', 'flag']:
                    # Categorical features (will be encoded by model)
                    if feature == 'protocol_type':
                        record[feature] = str(np.random.choice(['tcp', 'udp', 'icmp']))
                    elif feature == 'service':
                        record[feature] = str(np.random.choice(['http', 'ftp', 'smtp', 'ssh', 'telnet', 'dns']))
                    elif feature == 'flag':
                        record[feature] = str(np.random.choice(['SF', 'S0', 'REJ', 'RSTR', 'SH']))
                else:
                    # Default numeric features
                    record[feature] = float(np.random.exponential(1))
            
            data.append(record)
        
        return data
    
    def process_with_models(self, network_data):
        """Process network data through trained models to get real anomaly predictions"""
        processed_data = []
        
        print(f"Processing {len(network_data)} network records through detection pipeline...")
        
        for record in network_data:
            if self.detector and hasattr(self.detector, 'predict_single'):
                try:
                    # Use trained model for real prediction
                    prediction_result = self.detector.predict_single(record)
                    
                    # Extract prediction results
                    anomaly_score = prediction_result.get('anomaly_score', 0.1)
                    prediction = prediction_result.get('prediction', 0)
                    confidence = prediction_result.get('confidence', 0.5)
                    
                    # Classify attack type based on network features and anomaly score
                    attack_type = self.classify_attack_type(record, anomaly_score, prediction)
                    
                except Exception as e:
                    print(f"Error in model prediction: {e}")
                    # Fallback to conservative prediction
                    anomaly_score = 0.1
                    prediction = 0
                    confidence = 0.5
                    attack_type = 'Normal'
            else:
                # Fallback when no model is available - generate realistic anomaly scores
                # Create some anomalies for demonstration (20% chance of anomaly)
                if np.random.random() < 0.2:
                    anomaly_score = float(np.random.uniform(0.6, 0.95))  # High anomaly score
                    prediction = 1
                    confidence = float(np.random.uniform(0.7, 0.9))
                    # Generate realistic attack types based on anomaly score
                    attack_types = ['Brute Force', 'DDoS', 'Port Scan', 'SQL Injection', 'Web Attack', 'Network Scan', 'Data Exfiltration']
                    attack_type = np.random.choice(attack_types)
                else:
                    anomaly_score = float(np.random.uniform(0.05, 0.4))  # Low anomaly score
                    prediction = 0
                    confidence = float(np.random.uniform(0.6, 0.8))
                    attack_type = 'Normal'
            
            # Add prediction results to the record
            record.update({
                'anomaly_score': float(anomaly_score),
                'prediction': int(prediction),
                'confidence': float(confidence),
                'attack_type': str(attack_type)
            })
            
            processed_data.append(record)
        
        return processed_data
    
    def classify_attack_type(self, record, anomaly_score, prediction):
        """Classify attack type based on network features and model prediction"""
        if prediction == 0 or anomaly_score < self.threshold:
            return 'Normal'
        
        # Heuristic attack classification based on network patterns
        dst_port = record.get('dst_port', 80)
        src_port = record.get('src_port', 1024)
        proto = record.get('proto', 'tcp')
        
        # High anomaly score patterns
        if anomaly_score > 0.9:
            if dst_port in [22, 23, 3389]:  # SSH, Telnet, RDP
                return 'Brute Force'
            elif dst_port in [80, 443]:  # HTTP/HTTPS
                return 'Web Attack'
            else:
                return 'Advanced Persistent Threat'
        
        # Medium-high anomaly score patterns
        elif anomaly_score > 0.7:
            if proto == 'icmp':
                return 'Network Scan'
            elif dst_port in [1433, 3306, 5432]:  # Database ports
                return 'SQL Injection'
            elif src_port < 1024:  # Privileged ports
                return 'Privilege Escalation'
            else:
                return 'DDoS'
        
        # Medium anomaly score patterns
        elif anomaly_score > 0.5:
            if dst_port == 53:  # DNS
                return 'DNS Tunneling'
            elif dst_port in [21, 25]:  # FTP, SMTP
                return 'Data Exfiltration'
            else:
                return 'Port Scan'
        
        # Low-medium anomaly score
        else:
            return 'Suspicious Activity'
    
    def generate_mock_data(self, batch_size=10):
        """Generate network traffic and process through trained models for real anomaly detection"""
        # Step 1: Generate realistic network traffic data (simulation)
        network_data = self.generate_realistic_network_data(batch_size)
        
        # Step 2: Process through trained models for real anomaly predictions
        processed_data = self.process_with_models(network_data)
        
        return processed_data
    
    def process_alerts(self, data_batch):
        """Process new data and generate alerts"""
        new_alerts = []
        
        for record in data_batch:
            # Generate alert if anomaly score exceeds threshold (regardless of prediction value)
            if record['anomaly_score'] > self.threshold:
                alert = {
                    'id': self.next_alert_id,
                    'timestamp': record['timestamp'].isoformat(),
                    'severity': self.get_severity(record['anomaly_score']),
                    'source_ip': str(record['src_ip']),
                    'destination_ip': str(record['dst_ip']),
                    'attack_type': str(record['attack_type']),
                    'anomaly_score': float(round(record['anomaly_score'], 3)),
                    'confidence': float(round(record['confidence'], 3)),
                    'status': 'new',
                    'flagged': False,
                    'dismissed': False,
                    'protocol': str(record['proto']),
                    'src_port': int(record['src_port']),
                    'dst_port': int(record['dst_port'])
                }
                new_alerts.append(alert)
                self.next_alert_id += 1  # Increment ID counter
                print(f"Alert generated: ID {alert['id']}, Score: {alert['anomaly_score']}, Type: {alert['attack_type']}")
        
        # Add to current alerts and history
        self.current_alerts.extend(new_alerts)
        self.alert_history.extend(new_alerts)
        
        # Keep only recent alerts in current (last 100)
        if len(self.current_alerts) > 100:
            self.current_alerts = self.current_alerts[-100:]
        
        # Update system stats
        self.system_stats['total_processed'] += len(data_batch)
        self.system_stats['anomalies_detected'] += len(new_alerts)
        
        return new_alerts
    
    def get_severity(self, score):
        """Determine alert severity based on anomaly score"""
        if score >= 0.9:
            return 'critical'
        elif score >= 0.7:
            return 'high'
        elif score >= 0.5:
            return 'medium'
        else:
            return 'low'
    
    def start_monitoring(self):
        """Start real-time monitoring simulation"""
        def monitor_loop():
            while self.is_monitoring:
                try:
                    # Generate and process new data
                    data_batch = self.generate_mock_data(batch_size=5)
                    new_alerts = self.process_alerts(data_batch)
                    
                    if new_alerts:
                        # Emit new alerts via WebSocket
                        socketio.emit('new_alerts', {
                            'alerts': new_alerts,
                            'stats': self.get_system_stats()
                        })
                    
                    # Emit updated stats every cycle
                    socketio.emit('stats_update', self.get_system_stats())
                    
                    time.sleep(2)  # Process every 2 seconds
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(5)
        
        if not self.is_monitoring:
            self.is_monitoring = True
            monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitoring_thread.start()
            print("Real-time monitoring started")
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        print("Real-time monitoring stopped")
    
    def get_system_stats(self):
        """Get current system statistics"""
        recent_alerts = [a for a in self.current_alerts if 
                        datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=1)]
        
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for alert in recent_alerts:
            severity_counts[alert['severity']] += 1
        
        return {
            'total_processed': self.system_stats['total_processed'],
            'anomalies_detected': len(recent_alerts),
            'total_alerts': len(self.alert_history),
            'active_alerts': len([a for a in self.current_alerts if a['status'] == 'new']),
            'system_health': self.system_stats['system_health'],
            'threshold': self.threshold,
            'severity_distribution': severity_counts,
            'detection_rate': round((len(recent_alerts) / max(1, self.system_stats['total_processed'])) * 100, 2)
        }

# Initialize dashboard API
dashboard_api = SOCDashboardAPI()

# Initialize CSV processor with shared detector for consistent predictions
csv_processor = CSVProcessor(
    detector=dashboard_api.detector,  # Share the same detector instance
    upload_dir="src/dashboard/data/uploads",
    reports_dir="src/dashboard/data/reports"
)

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
        print(f"Login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

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
        email = data.get('email')
        role = data.get('role', 'analyst')
        
        if not all([username, password, email]):
            return jsonify({'error': 'Username, password, and email required'}), 400
        
        success, message = auth_manager.create_user(username, password, role, email)
        
        if not success:
            return jsonify({'error': message}), 400
        
        # Log user creation
        admin_username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        log_user_created(admin_username, username, ip_address, user_agent)
        
        return jsonify({'message': message}), 201
        
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
        ip_address, user_agent = get_client_info()
        log_user_updated(admin_username, username, ip_address, user_agent, list(data.keys()))
        
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
        ip_address, user_agent = get_client_info()
        log_user_deleted(admin_username, username, ip_address, user_agent)
        
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
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        event_type = request.args.get('event_type')
        username = request.args.get('username')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        logs = audit_logger.get_audit_logs(
            page=page,
            per_page=per_page,
            event_type=event_type,
            username=username,
            start_date=start_date,
            end_date=end_date
        )
        
        return jsonify(logs)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get audit logs'}), 500

@app.route('/api/admin/audit/summary', methods=['GET'])
@token_required
@admin_required
def get_audit_summary():
    """Get audit summary (admin only)"""
    try:
        summary = audit_logger.get_audit_summary()
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': 'Failed to get audit summary'}), 500

@app.route('/api/admin/security-alerts', methods=['GET'])
@token_required
@admin_required
def get_security_alerts():
    """Get security alerts from audit logs (admin only)"""
    try:
        days = int(request.args.get('days', 7))
        
        # Get recent security events
        security_events = audit_logger.get_security_alerts(days=days)
        
        return jsonify({
            'alerts': security_events,
            'total': len(security_events),
            'days': days
        })
        
    except Exception as e:
        print(f"Security alerts error: {e}")
        return jsonify({'error': 'Failed to get security alerts'}), 500

# SOC Dashboard Routes (with authentication)
@app.route('/api/alerts')
@token_required
@analyst_or_admin_required
def get_alerts():
    """Get alerts with filtering and pagination"""
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

@app.route('/api/stats')
@token_required
@analyst_or_admin_required
def get_stats():
    """Get system statistics"""
    return jsonify(dashboard_api.get_system_stats())

@app.route('/api/threshold', methods=['GET', 'POST'])
@token_required
@analyst_or_admin_required
def threshold():
    """Get or update detection threshold"""
    if request.method == 'POST':
        data = request.get_json()
        new_threshold = float(data.get('threshold', dashboard_api.threshold))
        if 0.0 <= new_threshold <= 1.0:
            dashboard_api.threshold = new_threshold
            return jsonify({'success': True, 'threshold': dashboard_api.threshold})
        else:
            return jsonify({'error': 'Threshold must be between 0.0 and 1.0'}), 400
    
    return jsonify({'threshold': dashboard_api.threshold})

@app.route('/api/alerts/<int:alert_id>/flag', methods=['POST'])
@token_required
@analyst_or_admin_required
def flag_alert(alert_id):
    """Flag an alert"""
    for alert in dashboard_api.current_alerts:
        if alert['id'] == alert_id:
            alert['flagged'] = True
            alert['status'] = 'flagged'
            return jsonify({'success': True})
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
@token_required
@analyst_or_admin_required
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    for alert in dashboard_api.current_alerts:
        if alert['id'] == alert_id:
            alert['dismissed'] = True
            alert['status'] = 'dismissed'
            return jsonify({'success': True})
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/monitoring/start', methods=['POST'])
@token_required
@analyst_or_admin_required
def start_monitoring():
    """Start real-time monitoring"""
    dashboard_api.start_monitoring()
    return jsonify({'success': True, 'status': 'monitoring_started'})

@app.route('/api/monitoring/stop', methods=['POST'])
@token_required
@analyst_or_admin_required
def stop_monitoring():
    """Stop real-time monitoring"""
    dashboard_api.stop_monitoring()
    return jsonify({'success': True, 'status': 'monitoring_stopped'})

@app.route('/api/score-distribution')
@token_required
@analyst_or_admin_required
def get_score_distribution():
    """Get anomaly score distribution for visualization"""
    scores = [alert['anomaly_score'] for alert in dashboard_api.current_alerts]
    
    if not scores:
        return jsonify({'bins': [], 'counts': []})
    
    # Create histogram data
    hist, bin_edges = np.histogram(scores, bins=20, range=(0, 1))
    bins = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(hist))]
    
    return jsonify({
        'bins': bins,
        'counts': hist.tolist(),
        'total_samples': len(scores)
    })

@app.route('/api/attack-distribution')
@token_required
@analyst_or_admin_required
def get_attack_distribution():
    """Get attack type distribution for threat analysis"""
    try:
        # Get attack types from recent alerts (last 24 hours)
        recent_alerts = [a for a in dashboard_api.alert_history if 
                        datetime.fromisoformat(a['timestamp']) > datetime.now() - timedelta(hours=24)]
        
        if not recent_alerts:
            return jsonify({'distribution': {}, 'total_attacks': 0, 'time_range': '24h'})
        
        # Count attack types
        attack_counts = {}
        severity_by_attack = {}
        
        for alert in recent_alerts:
            attack_type = alert['attack_type']
            severity = alert['severity']
            
            if attack_type not in attack_counts:
                attack_counts[attack_type] = 0
                severity_by_attack[attack_type] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            
            attack_counts[attack_type] += 1
            severity_by_attack[attack_type][severity] += 1
        
        # Calculate percentages and threat scores
        total_attacks = sum(attack_counts.values())
        distribution = {}
        
        for attack_type, count in attack_counts.items():
            percentage = round((count / total_attacks) * 100, 1)
            
            # Calculate threat score based on severity distribution
            severities = severity_by_attack[attack_type]
            threat_score = (
                severities['critical'] * 4 + 
                severities['high'] * 3 + 
                severities['medium'] * 2 + 
                severities['low'] * 1
            ) / count if count > 0 else 0
            
            distribution[attack_type] = {
                'count': count,
                'percentage': percentage,
                'threat_score': round(threat_score, 2),
                'severity_breakdown': severities
            }
        
        # Sort by threat score descending
        sorted_distribution = dict(sorted(distribution.items(), 
                                        key=lambda x: x[1]['threat_score'], reverse=True))
        
        return jsonify({
            'distribution': sorted_distribution,
            'total_attacks': total_attacks,
            'time_range': '24h',
            'top_threats': list(sorted_distribution.keys())[:5]
        })
        
    except Exception as e:
        print(f"Attack distribution error: {e}")
        return jsonify({'error': 'Failed to get attack distribution'}), 500

@app.route('/api/attack-trends')
@token_required
@analyst_or_admin_required
def get_attack_trends():
    """Get attack trends over time for threat analysis"""
    try:
        hours = int(request.args.get('hours', 24))
        granularity = request.args.get('granularity', 'hour')  # hour, day
        
        # Get alerts within time range
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_alerts = [a for a in dashboard_api.alert_history if 
                        datetime.fromisoformat(a['timestamp']) > cutoff_time]
        
        if not recent_alerts:
            return jsonify({'trends': [], 'summary': {}, 'time_range': f'{hours}h'})
        
        # Group alerts by time buckets
        time_buckets = {}
        attack_type_trends = {}
        
        for alert in recent_alerts:
            timestamp = datetime.fromisoformat(alert['timestamp'])
            attack_type = alert['attack_type']
            
            # Create time bucket key
            if granularity == 'hour':
                bucket_key = timestamp.strftime('%Y-%m-%d %H:00')
            else:  # day
                bucket_key = timestamp.strftime('%Y-%m-%d')
            
            # Initialize buckets
            if bucket_key not in time_buckets:
                time_buckets[bucket_key] = {'total': 0, 'by_type': {}, 'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}}
            
            if attack_type not in attack_type_trends:
                attack_type_trends[attack_type] = {}
            
            if bucket_key not in attack_type_trends[attack_type]:
                attack_type_trends[attack_type][bucket_key] = 0
            
            # Count attacks
            time_buckets[bucket_key]['total'] += 1
            time_buckets[bucket_key]['by_severity'][alert['severity']] += 1
            
            if attack_type not in time_buckets[bucket_key]['by_type']:
                time_buckets[bucket_key]['by_type'][attack_type] = 0
            time_buckets[bucket_key]['by_type'][attack_type] += 1
            
            attack_type_trends[attack_type][bucket_key] += 1
        
        # Convert to timeline format
        timeline = []
        for bucket_key in sorted(time_buckets.keys()):
            bucket_data = time_buckets[bucket_key]
            timeline.append({
                'timestamp': bucket_key,
                'total_attacks': bucket_data['total'],
                'attack_types': bucket_data['by_type'],
                'severity_distribution': bucket_data['by_severity']
            })
        
        # Calculate trends summary
        if len(timeline) >= 2:
            recent_total = sum(t['total_attacks'] for t in timeline[-2:])
            previous_total = sum(t['total_attacks'] for t in timeline[-4:-2]) if len(timeline) >= 4 else 0
            trend_direction = 'increasing' if recent_total > previous_total else 'decreasing' if recent_total < previous_total else 'stable'
            trend_percentage = round(((recent_total - previous_total) / max(previous_total, 1)) * 100, 1) if previous_total > 0 else 0
        else:
            trend_direction = 'insufficient_data'
            trend_percentage = 0
        
        # Get top attack types by recent activity
        recent_attack_counts = {}
        for alert in recent_alerts[-50:]:  # Last 50 alerts
            attack_type = alert['attack_type']
            recent_attack_counts[attack_type] = recent_attack_counts.get(attack_type, 0) + 1
        
        top_recent_attacks = sorted(recent_attack_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        summary = {
            'trend_direction': trend_direction,
            'trend_percentage': trend_percentage,
            'total_attacks': len(recent_alerts),
            'unique_attack_types': len(attack_type_trends),
            'top_recent_attacks': [{'type': attack, 'count': count} for attack, count in top_recent_attacks],
            'peak_hour': max(timeline, key=lambda x: x['total_attacks'])['timestamp'] if timeline else None
        }
        
        return jsonify({
            'trends': timeline,
            'attack_type_trends': attack_type_trends,
            'summary': summary,
            'time_range': f'{hours}h',
            'granularity': granularity
        })
        
    except Exception as e:
        print(f"Attack trends error: {e}")
        return jsonify({'error': 'Failed to get attack trends'}), 500

@app.route('/api/threat-triage')
@token_required
@analyst_or_admin_required
def get_threat_triage():
    """Get prioritized threat analysis for efficient triage"""
    try:
        # Get active alerts (not dismissed)
        active_alerts = [a for a in dashboard_api.current_alerts if a['status'] != 'dismissed']
        
        if not active_alerts:
            return jsonify({'high_priority': [], 'medium_priority': [], 'low_priority': [], 'summary': {}})
        
        # Enhanced threat scoring
        def calculate_threat_priority(alert):
            score = 0
            
            # Base score from anomaly score (0-40 points)
            score += alert['anomaly_score'] * 40
            
            # Severity multiplier (0-30 points)
            severity_scores = {'critical': 30, 'high': 20, 'medium': 10, 'low': 5}
            score += severity_scores.get(alert['severity'], 0)
            
            # Attack type risk factor (0-20 points)
            high_risk_attacks = ['Advanced Persistent Threat', 'Data Exfiltration', 'Privilege Escalation', 'SQL Injection']
            medium_risk_attacks = ['Brute Force', 'Web Attack', 'DDoS']
            
            if alert['attack_type'] in high_risk_attacks:
                score += 20
            elif alert['attack_type'] in medium_risk_attacks:
                score += 10
            else:
                score += 5
            
            # Recency factor (0-10 points) - more recent = higher priority
            alert_time = datetime.fromisoformat(alert['timestamp'])
            hours_old = (datetime.now() - alert_time).total_seconds() / 3600
            if hours_old < 1:
                score += 10
            elif hours_old < 6:
                score += 5
            elif hours_old < 24:
                score += 2
            
            return min(score, 100)  # Cap at 100
        
        # Calculate priority scores
        for alert in active_alerts:
            alert['priority_score'] = calculate_threat_priority(alert)
            
            # Determine priority level
            if alert['priority_score'] >= 70:
                alert['priority_level'] = 'high'
            elif alert['priority_score'] >= 40:
                alert['priority_level'] = 'medium'
            else:
                alert['priority_level'] = 'low'
        
        # Sort by priority score
        active_alerts.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Group by priority
        high_priority = [a for a in active_alerts if a['priority_level'] == 'high']
        medium_priority = [a for a in active_alerts if a['priority_level'] == 'medium']
        low_priority = [a for a in active_alerts if a['priority_level'] == 'low']
        
        # Generate triage recommendations
        recommendations = []
        
        if high_priority:
            recommendations.append({
                'type': 'immediate_action',
                'message': f'{len(high_priority)} high-priority threats require immediate attention',
                'action': 'investigate_high_priority'
            })
        
        # Check for attack patterns
        attack_counts = {}
        for alert in active_alerts[:20]:  # Recent alerts
            attack_type = alert['attack_type']
            attack_counts[attack_type] = attack_counts.get(attack_type, 0) + 1
        
        for attack_type, count in attack_counts.items():
            if count >= 3:
                recommendations.append({
                    'type': 'pattern_detected',
                    'message': f'Multiple {attack_type} attacks detected ({count} instances)',
                    'action': 'investigate_pattern'
                })
        
        # Check for source IP patterns
        source_ips = {}
        for alert in active_alerts[:20]:
            ip = alert['source_ip']
            source_ips[ip] = source_ips.get(ip, 0) + 1
        
        for ip, count in source_ips.items():
            if count >= 3:
                recommendations.append({
                    'type': 'suspicious_source',
                    'message': f'Multiple attacks from source IP {ip} ({count} instances)',
                    'action': 'block_investigate_ip'
                })
        
        summary = {
            'total_active_alerts': len(active_alerts),
            'high_priority_count': len(high_priority),
            'medium_priority_count': len(medium_priority),
            'low_priority_count': len(low_priority),
            'average_priority_score': round(sum(a['priority_score'] for a in active_alerts) / len(active_alerts), 1),
            'recommendations': recommendations[:5],  # Top 5 recommendations
            'most_common_attack': max(attack_counts.items(), key=lambda x: x[1])[0] if attack_counts else None
        }
        
        return jsonify({
            'high_priority': high_priority[:10],  # Top 10 high priority
            'medium_priority': medium_priority[:10],  # Top 10 medium priority
            'low_priority': low_priority[:5],  # Top 5 low priority
            'summary': summary
        })
        
    except Exception as e:
        print(f"Threat triage error: {e}")
        return jsonify({'error': 'Failed to get threat triage data'}), 500

# CSV Upload and Analysis Endpoints
@app.route('/api/csv/upload', methods=['POST'])
@token_required
@analyst_or_admin_required
def upload_csv():
    """Upload CSV file for anomaly detection"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        if not filename.lower().endswith('.csv'):
            return jsonify({'error': 'File must be a CSV file'}), 400
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{filename}"
        file_path = str(csv_processor.upload_dir / safe_filename)
        
        # Ensure upload directory exists
        csv_processor.upload_dir.mkdir(parents=True, exist_ok=True)
        
        file.save(file_path)
        
        # Validate file
        is_valid, error_message = csv_processor.validate_csv_file(file_path)
        if not is_valid:
            os.remove(file_path)  # Clean up invalid file
            return jsonify({'error': error_message}), 400
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_info = {
            'file_id': file_id,
            'filename': filename,
            'safe_filename': safe_filename,
            'file_size': file_size,
            'upload_timestamp': datetime.now().isoformat(),
            'uploaded_by': request.current_user['username']
        }
        
        # Log the upload
        username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        audit_logger.log_event(
            event_type=AuditEventType.CSV_UPLOAD,
            username=username,
            details={
                'filename': filename,
                'file_size': file_size,
                'file_id': file_id
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify({
            'message': 'File uploaded successfully',
            'file_info': file_info
        }), 201
        
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
        file_id = data.get('file_id')
        sample_size = data.get('sample_size')  # Optional limit on rows to process
        
        if not file_id:
            return jsonify({'error': 'File ID required'}), 400
        
        # Find the uploaded file
        file_pattern = str(csv_processor.upload_dir / f"{file_id}_*")
        matching_files = glob.glob(file_pattern)
        
        if not matching_files:
            return jsonify({'error': 'File not found'}), 404
        
        file_path = matching_files[0]
        filename = os.path.basename(file_path).split('_', 1)[1]  # Remove file_id prefix
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_info = {
            'file_id': file_id,
            'filename': filename,
            'file_size': file_size,
            'analysis_timestamp': datetime.now().isoformat(),
            'analyzed_by': request.current_user['username']
        }
        
        # Preprocess data
        df, preprocessing_metadata = csv_processor.preprocess_csv_data(file_path, sample_size)
        
        # Perform anomaly detection
        detection_results = csv_processor.detect_anomalies(df, preprocessing_metadata)
        
        # Generate comprehensive report
        report = csv_processor.generate_report(file_info, preprocessing_metadata, detection_results)
        
        # Log the analysis
        username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        audit_logger.log_event(
            event_type=AuditEventType.CSV_ANALYSIS,
            username=username,
            details={
                'filename': filename,
                'file_id': file_id,
                'anomalies_detected': detection_results['anomalies_detected'],
                'total_records': detection_results['total_records']
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Convert numpy types to JSON-serializable types
        def convert_numpy_types(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        # Clean the report for JSON serialization
        clean_report = convert_numpy_types(report)
        
        return jsonify({
            'message': 'Analysis completed successfully',
            'report': clean_report
        })
        
    except Exception as e:
        print(f"CSV analysis error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/csv/reports', methods=['GET'])
@token_required
@analyst_or_admin_required
def get_csv_reports():
    """Get list of all CSV analysis reports"""
    try:
        reports = csv_processor.list_reports()
        return jsonify({
            'reports': reports,
            'total': len(reports)
        })
        
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
        
        return jsonify(report)
        
    except Exception as e:
        print(f"Error getting report {report_id}: {e}")
        return jsonify({'error': 'Failed to get report'}), 500

@app.route('/api/csv/reports/<report_id>/download', methods=['GET'])
@token_required
@analyst_or_admin_required
def download_csv_report(report_id):
    """Download CSV analysis report as JSON file"""
    try:
        report = csv_processor.get_report(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Create temporary file for download
        def json_serializer(obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return str(obj)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(report, temp_file, indent=2, default=json_serializer)
            temp_path = temp_file.name
        
        # Log the download
        username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        audit_logger.log_event(
            event_type=AuditEventType.CSV_REPORT_GENERATED,
            username=username,
            details={
                'report_id': report_id,
                'action': 'download'
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f"anomaly_report_{report_id}.json",
            mimetype='application/json'
        )
        
    except Exception as e:
        print(f"Error downloading report {report_id}: {e}")
        return jsonify({'error': 'Failed to download report'}), 500

@app.route('/api/csv/cleanup', methods=['POST'])
@token_required
@admin_required
def cleanup_csv_files():
    """Clean up old CSV files and reports (admin only)"""
    try:
        data = request.get_json()
        days_old = data.get('days_old', 30)
        
        csv_processor.cleanup_old_files(days_old)
        
        # Log the cleanup
        username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        audit_logger.log_event(
            event_type=AuditEventType.CSV_CLEANUP,
            username=username,
            details={
                'days_old': days_old,
                'action': 'cleanup_old_files'
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return jsonify({'message': f'Cleaned up files older than {days_old} days'})
        
    except Exception as e:
        print(f"Cleanup error: {e}")
        return jsonify({'error': 'Cleanup failed'}), 500

# WebSocket Events with Authentication
@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection with authentication"""
    try:
        # Check for authentication token
        token = auth.get('token') if auth else None
        if not token:
            print('Client connection rejected: No token provided')
            disconnect()
            return False
        
        # Verify token
        valid, payload = auth_manager.verify_token(token)
        if not valid:
            print('Client connection rejected: Invalid token')
            disconnect()
            return False
        
        # Store user info in session
        from flask import session
        session['username'] = payload.get('username')
        session['role'] = payload.get('role')
        
        print(f'Client connected: {payload.get("username")} ({payload.get("role")})')
        emit('connection_established', {'status': 'connected', 'user': payload.get('username')})
        emit('stats_update', dashboard_api.get_system_stats())
        
    except Exception as e:
        print(f'Connection error: {e}')
        disconnect()
        return False

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import session
    username = session.get('username', 'Unknown')
    print(f'Client disconnected: {username}')

@socketio.on('request_alerts')
def handle_request_alerts(data=None):
    """Send current alerts to client (authenticated users only)"""
    from flask import session
    if not session.get('username'):
        emit('error', {'message': 'Authentication required'})
        return
    
    emit('alerts_update', {
        'alerts': dashboard_api.current_alerts[-20:],  # Last 20 alerts
        'stats': dashboard_api.get_system_stats()
    })

if __name__ == '__main__':
    print("🔐 Starting SOC Dashboard with Authentication...")
    print("📍 Server will be available at: http://localhost:5000")
    print("👤 Default admin credentials:")
    print("   Username: admin")
    print("   Password: SecureAdmin123!")
    print("")
    print("🔧 Environment Variables (optional):")
    print("   FLASK_SECRET_KEY - Flask session secret")
    print("   JWT_SECRET_KEY - JWT token signing key")
    print("")
    
    # Ensure data directory and seed data exist
    if not os.path.exists('data'):
        print("⚠️  Data directory not found. Running seed script...")
        try:
            import subprocess
            subprocess.run(['python', 'scripts/seed_data.py'], check=True)
            print("✅ Data seeded successfully")
        except Exception as e:
            print(f"❌ Failed to seed data: {e}")
            print("Please run: python scripts/seed_data.py")
    
    # Start monitoring by default
    dashboard_api.start_monitoring()
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
