#!/usr/bin/env python3
"""
SOC Dashboard Backend Server
Real-time anomaly detection API with WebSocket support and Authentication
"""

import os
import sys
import json
import tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
import time
import threading
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

# MongoDB imports
from src.database.mongodb_config import initialize_mongodb, mongodb_health_check
from src.database.mongodb_dal import get_dal
from src.database.schemas import AlertSeverity, AlertStatus, AuditEventType
from src.database.migration_utils import migrate_existing_data
from src.auth.mongodb_auth_utils import MongoDBAuthManager, token_required, admin_required, analyst_or_admin_required
from src.utils.csv_processor import CSVProcessor

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'soc-dashboard-secret-key-change-in-production')
CORS(app, origins=["http://localhost:3000"], supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins=["http://localhost:3000"], logger=False, engineio_logger=False)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["1000 per hour"]
)

# Initialize MongoDB and auth manager
try:
    # Initialize MongoDB connection and indexes
    if initialize_mongodb():
        print("✓ MongoDB initialized successfully")
        
        # Run data migration if needed
        migration_results = migrate_existing_data()
        if migration_results.get('error'):
            print(f"⚠ Migration warning: {migration_results['error']}")
        else:
            print("✓ Data migration completed")
    else:
        print("⚠ MongoDB initialization failed, some features may not work")
except Exception as e:
    print(f"⚠ MongoDB setup error: {e}")

# Initialize auth manager with MongoDB backend
auth_manager = MongoDBAuthManager()

# Initialize MongoDB DAL
mongodb_dal = get_dal()

# Initialize audit logger using MongoDB DAL
class MongoDBCompatibleAuditLogger:
    """Audit logger that works with MongoDB DAL"""
    def __init__(self, dal):
        self.dal = dal
    
    def get_audit_logs(self, page=1, per_page=50, event_type=None, username=None, start_date=None, end_date=None):
        """Get audit logs with filtering"""
        try:
            filters = {}
            if event_type:
                filters['event_type'] = event_type
            if username:
                filters['username'] = username
            if start_date:
                # Parse date string if needed
                if isinstance(start_date, str):
                    from datetime import datetime
                    start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                filters['timestamp'] = {'$gte': start_date}
            if end_date:
                # Parse date string if needed
                if isinstance(end_date, str):
                    from datetime import datetime
                    end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                if 'timestamp' not in filters:
                    filters['timestamp'] = {}
                filters['timestamp']['$lte'] = end_date
            
            result = self.dal.get_audit_logs(filters=filters, page=page, per_page=per_page)
            return result
        except Exception as e:
            print(f"Error getting audit logs: {e}")
            return {'logs': [], 'total': 0, 'page': page, 'per_page': per_page}
    
    def get_audit_summary(self, days=30):
        """Get audit summary"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get recent audit logs
            result = self.dal.get_audit_logs(
                filters={'timestamp': {'$gte': cutoff_date}}, 
                page=1, 
                per_page=1000
            )
            logs = result.get('logs', [])
            
            # Calculate summary statistics
            total_events = len(logs)
            event_types = {}
            users = {}
            
            for log in logs:
                event_type = log.get('event_type', 'unknown')
                username = log.get('username', 'unknown')
                
                event_types[event_type] = event_types.get(event_type, 0) + 1
                users[username] = users.get(username, 0) + 1
            
            return {
                'total_events': total_events,
                'event_types': event_types,
                'active_users': len(users),
                'top_users': dict(sorted(users.items(), key=lambda x: x[1], reverse=True)[:10]),
                'days': days
            }
        except Exception as e:
            print(f"Error getting audit summary: {e}")
            return {'total_events': 0, 'event_types': {}, 'active_users': 0, 'top_users': {}, 'days': days}
    
    def get_security_alerts(self, days=7):
        """Get security-related events"""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get security-related audit logs
            security_event_types = ['login_failed', 'unauthorized_access', 'suspicious_activity', 'account_locked']
            
            security_events = []
            for event_type in security_event_types:
                result = self.dal.get_audit_logs(
                    filters={
                        'event_type': event_type,
                        'timestamp': {'$gte': cutoff_date}
                    }, 
                    page=1, 
                    per_page=100
                )
                security_events.extend(result.get('logs', []))
            
            return security_events
        except Exception as e:
            print(f"Error getting security alerts: {e}")
            return []
    
    def log_event(self, event_type, username, details, ip_address=None, user_agent=None):
        """Log an audit event"""
        try:
            self.dal.create_audit_log(
                event_type=event_type.value if hasattr(event_type, 'value') else str(event_type),
                username=username,
                ip_address=ip_address or 'unknown',
                action=details.get('action', 'unknown'),
                success=details.get('success', True),
                details=details
            )
        except Exception as e:
            print(f"Error logging audit event: {e}")

audit_logger = MongoDBCompatibleAuditLogger(mongodb_dal)

# Attach auth manager to Flask app for decorator access
app.auth_manager = auth_manager

def get_client_info():
    """Extract client IP and user agent from request"""
    ip_address = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
    user_agent = request.headers.get('User-Agent', '')
    return ip_address, user_agent

# Audit logging helper functions
def log_login_success(username, ip_address, user_agent):
    """Log successful login"""
    audit_logger.log_event(
        event_type='login_success',
        username=username,
        details={'action': 'login_success'},
        ip_address=ip_address,
        user_agent=user_agent
    )

def log_logout(username, ip_address):
    """Log user logout"""
    audit_logger.log_event(
        event_type='logout',
        username=username,
        details={'action': 'logout'},
        ip_address=ip_address
    )

def log_user_created(admin_username, new_username, ip_address, user_agent):
    """Log user creation"""
    audit_logger.log_event(
        event_type='user_created',
        username=admin_username,
        details={'action': 'create_user', 'target_user': new_username},
        ip_address=ip_address,
        user_agent=user_agent
    )

def log_user_updated(admin_username, target_username, ip_address, user_agent, updated_fields):
    """Log user update"""
    audit_logger.log_event(
        event_type='user_updated',
        username=admin_username,
        details={'action': 'update_user', 'target_user': target_username, 'updated_fields': updated_fields},
        ip_address=ip_address,
        user_agent=user_agent
    )

def log_user_deleted(admin_username, deleted_username, ip_address, user_agent):
    """Log user deletion"""
    audit_logger.log_event(
        event_type='user_deleted',
        username=admin_username,
        details={'action': 'delete_user', 'target_user': deleted_username},
        ip_address=ip_address,
        user_agent=user_agent
    )

class SOCDashboardAPI:
    def __init__(self):
        self.detector = None
        self.dal = get_dal()
        self.threshold = 0.5
        self.is_monitoring = False
        self.load_models()
        
        # Initialize system stats in MongoDB if not exists
        self._initialize_system_stats()
        
    def load_models(self):
        """Load the latest trained models"""
        try:
            # Try to import and initialize the detector
            from src.models.supervised_trainer import SupervisedSOCDetector
            self.detector = SupervisedSOCDetector()
            
            model_dir = 'models'
            if os.path.exists(model_dir):
                self.detector.load_models(model_dir)
                print("✓ Models loaded successfully")
            else:
                print("⚠ No trained models found. Using mock data mode.")
                self.detector = None
        except Exception as e:
            print(f"✗ Error loading models: {e}")
            self.detector = None
    
    def _initialize_system_stats(self):
        """Initialize system statistics in MongoDB if they don't exist"""
        try:
            # Check if system stats exist
            existing_stats = self.dal.get_latest_system_stats("realtime")
            
            if not existing_stats:
                # Create initial system stats
                initial_stats = {
                    'total_processed': 0,
                    'anomalies_detected': 0,
                    'total_alerts': 0,
                    'active_alerts': 0,
                    'system_health': 'healthy',
                    'detection_threshold': self.threshold,
                    'severity_distribution': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'detection_rate': 0.0,
                    'uptime_hours': 0.0,
                    'last_alert_time': None
                }
                
                # Save initial stats to MongoDB
                self.dal.save_system_stats("realtime", initial_stats)
                print("✓ System statistics initialized in MongoDB")
            else:
                print("✓ System statistics found in MongoDB")
                
        except Exception as e:
            print(f"⚠ Error initializing system stats: {e}")
            # Continue without failing - stats will be created on first update
    
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
                pass  # Silently fallback to default features
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
        
        # Processing network records through detection pipeline
        
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
                    pass  # Fallback to conservative prediction
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
        """Process new data and generate alerts using MongoDB storage"""
        new_alerts = []
        
        for record in data_batch:
            # Generate alert if anomaly score exceeds threshold
            if record['anomaly_score'] > self.threshold:
                alert_data = {
                    'timestamp': record['timestamp'],
                    'severity': self.get_severity(record['anomaly_score']),
                    'source_ip': str(record['src_ip']),
                    'destination_ip': str(record['dst_ip']),
                    'attack_type': str(record['attack_type']),
                    'anomaly_score': float(round(record['anomaly_score'], 3)),
                    'confidence': float(round(record['confidence'], 3)),
                    'protocol': str(record['proto']),
                    'source_port': int(record['src_port']),
                    'destination_port': int(record['dst_port']),
                    'status': AlertStatus.NEW.value,
                    'flagged': False,
                    'dismissed': False
                }
                
                # Save alert to MongoDB
                try:
                    success, message, alert_id = self.dal.create_alert(alert_data)
                    if success:
                        # Get the latest alert ID to retrieve the created alert
                        latest_alert = self.dal.db.alerts.find_one({}, sort=[("alert_id", -1)])
                        if latest_alert:
                            new_alerts.append(latest_alert)
                except Exception as e:
                    print(f"Error saving alert to MongoDB: {e}")
        
        # Update system stats in MongoDB
        try:
            current_stats = self.dal.get_latest_system_stats("realtime")
            if current_stats:
                updated_stats = {
                    'total_processed': current_stats.get('total_processed', 0) + len(data_batch),
                    'anomalies_detected': current_stats.get('anomalies_detected', 0) + len(new_alerts),
                    'total_alerts': current_stats.get('total_alerts', 0) + len(new_alerts),
                    'active_alerts': self.get_active_alerts_count(),
                    'system_health': 'healthy',
                    'detection_threshold': self.threshold,
                    'severity_distribution': self.get_severity_distribution(),
                    'detection_rate': self.calculate_detection_rate()
                }
                self.dal.save_system_stats("realtime", updated_stats)
        except Exception as e:
            print(f"Error updating system stats: {e}")
        
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
                    pass  # Continue monitoring despite errors
                    time.sleep(5)
        
        if not self.is_monitoring:
            self.is_monitoring = True
            monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitoring_thread.start()
            pass  # Monitoring started
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        pass  # Monitoring stopped
    
    def get_active_alerts_count(self):
        """Get count of active alerts from MongoDB"""
        try:
            result = self.dal.get_alerts(filters={'status': {'$ne': 'resolved'}}, per_page=1)
            return result.get('total', 0)
        except:
            return 0
    
    def get_severity_distribution(self):
        """Get severity distribution from recent alerts"""
        try:
            stats = self.dal.get_alert_statistics(hours=1)
            return stats.get('severity_distribution', {'critical': 0, 'high': 0, 'medium': 0, 'low': 0})
        except:
            return {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
    
    def calculate_detection_rate(self):
        """Calculate current detection rate"""
        try:
            current_stats = self.dal.get_latest_system_stats("realtime")
            if current_stats:
                total_processed = current_stats.get('total_processed', 0)
                anomalies_detected = current_stats.get('anomalies_detected', 0)
                return round((anomalies_detected / max(1, total_processed)) * 100, 2)
            return 0.0
        except:
            return 0.0
    
    def get_system_stats(self):
        """Get current system statistics from MongoDB"""
        try:
            # Get latest stats from MongoDB
            current_stats = self.dal.get_latest_system_stats("realtime")
            if current_stats:
                return {
                    'total_processed': current_stats.get('total_processed', 0),
                    'anomalies_detected': current_stats.get('anomalies_detected', 0),
                    'total_alerts': current_stats.get('total_alerts', 0),
                    'active_alerts': self.get_active_alerts_count(),
                    'system_health': current_stats.get('system_health', 'healthy'),
                    'threshold': self.threshold,
                    'severity_distribution': self.get_severity_distribution(),
                    'detection_rate': self.calculate_detection_rate()
                }
            else:
                # Fallback stats
                return {
                    'total_processed': 0,
                    'anomalies_detected': 0,
                    'total_alerts': 0,
                    'active_alerts': 0,
                    'system_health': 'healthy',
                    'threshold': self.threshold,
                    'severity_distribution': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'detection_rate': 0.0
                }
        except Exception as e:
            print(f"Error getting system stats: {e}")
            return {
                'total_processed': 0,
                'anomalies_detected': 0,
                'total_alerts': 0,
                'active_alerts': 0,
                'system_health': 'unhealthy',
                'threshold': self.threshold,
                'severity_distribution': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                'detection_rate': 0.0
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
        pass  # Login error handled
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
        
        # Convert MongoDB objects to JSON-serializable format
        if 'logs' in logs:
            for log in logs['logs']:
                # Convert ObjectId to string
                if '_id' in log:
                    log['_id'] = str(log['_id'])
                
                # Convert datetime to ISO string
                if 'timestamp' in log and hasattr(log['timestamp'], 'isoformat'):
                    log['timestamp'] = log['timestamp'].isoformat()
        
        return jsonify(logs)
        
    except Exception as e:
        print(f"Error in audit logs endpoint: {e}")
        import traceback
        traceback.print_exc()
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
        pass  # Error handled
        return jsonify({'error': 'Failed to get security alerts'}), 500

# MongoDB Health Check Endpoint
@app.route('/api/health/mongodb')
@token_required
@admin_required
def mongodb_health():
    """Get MongoDB health status"""
    try:
        health_status = mongodb_health_check()
        return jsonify(health_status)
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/health/database-stats')
@token_required
@admin_required
def database_stats():
    """Get database collection statistics"""
    try:
        stats = dashboard_api.dal.get_collection_stats()
        return jsonify({
            'status': 'success',
            'collections': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

# SOC Dashboard Routes (with authentication)
@app.route('/api/alerts')
@token_required
@analyst_or_admin_required
def get_alerts():
    """Get alerts with filtering and pagination from MongoDB"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        severity = request.args.get('severity')
        status = request.args.get('status')
        
        # Build MongoDB filters
        filters = {}
        if severity:
            filters['severity'] = severity
        if status:
            filters['status'] = status
        
        # Get alerts from MongoDB
        result = dashboard_api.dal.get_alerts(
            filters=filters,
            page=page,
            per_page=per_page,
            sort_by="timestamp",
            sort_order=-1  # Newest first
        )
        
        # Convert ObjectId to string for JSON serialization
        for alert in result['alerts']:
            if '_id' in alert:
                alert['_id'] = str(alert['_id'])
            # Convert datetime to ISO string if needed
            if 'timestamp' in alert and hasattr(alert['timestamp'], 'isoformat'):
                alert['timestamp'] = alert['timestamp'].isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting alerts: {e}")
        return jsonify({'error': 'Failed to get alerts'}), 500

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
    """Flag an alert in MongoDB"""
    try:
        username = request.current_user['username']
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id,
            updates={
                'flagged': True,
                'status': 'flagged'
            },
            updated_by=username
        )
        
        if success:
            # Log the action
            dashboard_api.dal.create_audit_log(
                event_type='alert_updated',
                username=username,
                ip_address=get_client_info()[0],
                action="flag_alert",
                success=True,
                details={'alert_id': alert_id, 'action': 'flagged'}
            )
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error flagging alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to flag alert'}), 500

@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
@token_required
@analyst_or_admin_required
def dismiss_alert(alert_id):
    """Dismiss an alert in MongoDB"""
    try:
        username = request.current_user['username']
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id,
            updates={
                'dismissed': True,
                'status': 'dismissed'
            },
            updated_by=username
        )
        
        if success:
            # Log the action
            dashboard_api.dal.create_audit_log(
                event_type='alert_updated',
                username=username,
                ip_address=get_client_info()[0],
                action="dismiss_alert",
                success=True,
                details={'alert_id': alert_id, 'action': 'dismissed'}
            )
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error dismissing alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to dismiss alert'}), 500

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
    """Get anomaly score distribution for visualization from MongoDB"""
    try:
        # Get recent alerts from MongoDB
        result = dashboard_api.dal.get_alerts(filters={}, page=1, per_page=1000)
        alerts = result.get('alerts', [])
        
        scores = [alert['anomaly_score'] for alert in alerts if 'anomaly_score' in alert]
        
        if not scores:
            return jsonify({'bins': [], 'counts': [], 'total_samples': 0})
        
        # Create histogram data
        hist, bin_edges = np.histogram(scores, bins=20, range=(0, 1))
        bins = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(hist))]
        
        return jsonify({
            'bins': bins,
            'counts': hist.tolist(),
            'total_samples': len(scores)
        })
        
    except Exception as e:
        print(f"Error getting score distribution: {e}")
        return jsonify({'error': 'Failed to get score distribution'}), 500

@app.route('/api/attack-distribution')
@token_required
@analyst_or_admin_required
def get_attack_distribution():
    """Get attack type distribution for threat analysis"""
    try:
        # Get recent alerts from MongoDB (last 24 hours)
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Get alerts from MongoDB
        result = dashboard_api.dal.get_alerts(
            filters={'timestamp': {'$gte': cutoff_time}}, 
            page=1, 
            per_page=1000
        )
        recent_alerts = result.get('alerts', [])
        
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
        pass  # Error handled
        return jsonify({'error': 'Failed to get attack distribution'}), 500

@app.route('/api/attack-trends')
@token_required
@analyst_or_admin_required
def get_attack_trends():
    """Get attack trends over time for threat analysis"""
    try:
        hours = int(request.args.get('hours', 24))
        granularity = request.args.get('granularity', 'hour')  # hour, day
        
        # Get alerts within time range from MongoDB
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get alerts from MongoDB
        result = dashboard_api.dal.get_alerts(
            filters={'timestamp': {'$gte': cutoff_time}}, 
            page=1, 
            per_page=1000
        )
        recent_alerts = result.get('alerts', [])
        
        if not recent_alerts:
            return jsonify({'trends': [], 'summary': {}, 'time_range': f'{hours}h'})
        
        # Group alerts by time buckets
        time_buckets = {}
        attack_type_trends = {}
        
        for alert in recent_alerts:
            # Handle both string and datetime timestamp formats
            timestamp = alert['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
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
        pass  # Error handled
        return jsonify({'error': 'Failed to get attack trends'}), 500

@app.route('/api/threat-triage')
@token_required
@analyst_or_admin_required
def get_threat_triage():
    """Get prioritized threat analysis for efficient triage"""
    try:
        from datetime import datetime
        # Get active alerts (not dismissed) from MongoDB
        result = dashboard_api.dal.get_alerts(
            filters={'status': {'$ne': 'dismissed'}}, 
            page=1, 
            per_page=500
        )
        active_alerts = result.get('alerts', [])
        
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
            alert_time = alert['timestamp']
            if isinstance(alert_time, str):
                alert_time = datetime.fromisoformat(alert_time)
            hours_old = (datetime.now() - alert_time).total_seconds() / 3600
            if hours_old < 1:
                score += 10
            elif hours_old < 6:
                score += 5
            elif hours_old < 24:
                score += 2
            
            return min(score, 100)  # Cap at 100
        
        # Convert MongoDB objects to JSON-serializable format
        for alert in active_alerts:
            # Convert ObjectId to string
            if '_id' in alert:
                alert['_id'] = str(alert['_id'])
            
            # Convert datetime to ISO string
            if 'timestamp' in alert and hasattr(alert['timestamp'], 'isoformat'):
                alert['timestamp'] = alert['timestamp'].isoformat()
            
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
        print(f"Error in threat triage endpoint: {e}")
        import traceback
        traceback.print_exc()
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
            event_type='csv_upload',
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
        pass  # Error handled
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
            event_type='csv_analysis',
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
        pass  # Error handled
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
        pass  # Error handled
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
        pass  # Error handled
        return jsonify({'error': 'Failed to get report'}), 500

@app.route('/api/csv/reports/<report_id>/download', methods=['GET'])
@token_required
@analyst_or_admin_required
def download_csv_report(report_id):
    """Download CSV analysis report as CSV file"""
    try:
        report = csv_processor.get_report(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Create CSV content
        csv_content = []
        
        # Add report metadata
        csv_content.append("# SOC Anomaly Detection Report")
        csv_content.append(f"# Report ID: {report.get('report_id', 'N/A')}")
        csv_content.append(f"# Generated: {report.get('timestamp', 'N/A')}")
        csv_content.append(f"# File: {report.get('filename', 'N/A')}")
        csv_content.append(f"# Total Records: {report.get('total_records', 'N/A')}")
        csv_content.append(f"# Anomalies Detected: {report.get('anomaly_count', 'N/A')}")
        csv_content.append(f"# Anomaly Rate: {report.get('anomaly_rate', 'N/A'):.2%}" if isinstance(report.get('anomaly_rate'), (int, float)) else f"# Anomaly Rate: {report.get('anomaly_rate', 'N/A')}")
        csv_content.append("")
        
        # Add summary statistics
        if 'summary' in report:
            summary = report['summary']
            csv_content.append("# Summary Statistics")
            for key, value in summary.items():
                if isinstance(value, (int, float)):
                    csv_content.append(f"# {key}: {value:.4f}" if isinstance(value, float) else f"# {key}: {value}")
                else:
                    csv_content.append(f"# {key}: {value}")
            csv_content.append("")
        
        # Add anomaly details header
        csv_content.append("# Anomaly Details")
        csv_content.append("Row_Index,Anomaly_Score,Severity,Attack_Type,Confidence")
        
        # Add anomaly data
        if 'anomalies' in report:
            for anomaly in report['anomalies']:
                row_idx = anomaly.get('row_index', 'N/A')
                score = anomaly.get('anomaly_score', 'N/A')
                severity = anomaly.get('severity', 'N/A')
                attack_type = anomaly.get('attack_type', 'N/A')
                confidence = anomaly.get('confidence', 'N/A')
                
                # Format score and confidence as numbers
                if isinstance(score, (int, float)):
                    score = f"{score:.6f}"
                if isinstance(confidence, (int, float)):
                    confidence = f"{confidence:.4f}"
                
                csv_content.append(f"{row_idx},{score},{severity},{attack_type},{confidence}")
        
        # If no anomalies section, add feature statistics
        elif 'feature_stats' in report:
            csv_content.append("# Feature Statistics")
            csv_content.append("Feature,Mean,Std,Min,Max,Anomaly_Threshold")
            
            for feature, stats in report['feature_stats'].items():
                mean = stats.get('mean', 'N/A')
                std = stats.get('std', 'N/A')
                min_val = stats.get('min', 'N/A')
                max_val = stats.get('max', 'N/A')
                threshold = stats.get('threshold', 'N/A')
                
                # Format numbers
                if isinstance(mean, (int, float)):
                    mean = f"{mean:.6f}"
                if isinstance(std, (int, float)):
                    std = f"{std:.6f}"
                if isinstance(min_val, (int, float)):
                    min_val = f"{min_val:.6f}"
                if isinstance(max_val, (int, float)):
                    max_val = f"{max_val:.6f}"
                if isinstance(threshold, (int, float)):
                    threshold = f"{threshold:.6f}"
                
                csv_content.append(f"{feature},{mean},{std},{min_val},{max_val},{threshold}")
        
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as temp_file:
            temp_file.write('\n'.join(csv_content))
            temp_path = temp_file.name
        
        # Log the download
        username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        audit_logger.log_event(
            event_type='csv_report_generated',
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
            download_name=f"anomaly_report_{report_id}.csv",
            mimetype='text/csv'
        )
        
    except Exception as e:
        pass  # Error handled
        return jsonify({'error': 'Failed to download report'}), 500

def create_anomaly_charts(report):
    """Create comprehensive visualization charts for the PDF report"""
    charts = []
    
    try:
        # Set style for better looking plots
        plt.style.use('default')
        sns.set_palette("husl")
    except Exception as e:
        pass  # Continue without custom styling
        # Continue without custom styling
    
    # Get detection results
    detection_results = report.get('detection_results', {})
    anomaly_scores = detection_results.get('anomaly_scores', [])
    predictions = detection_results.get('predictions', [])
    feature_importance = detection_results.get('feature_importance', {})
    
    # Chart 1: Main Analysis Dashboard (4 subplots)
    try:
        if anomaly_scores and predictions:
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('Comprehensive Anomaly Detection Analysis', fontsize=16, fontweight='bold')
            
            # Anomaly Score Distribution
            try:
                axes[0, 0].hist(anomaly_scores, bins=30, alpha=0.7, color='skyblue', edgecolor='black')
                axes[0, 0].axvline(x=0.5, color='red', linestyle='--', label='Threshold (0.5)')
                axes[0, 0].set_xlabel('Anomaly Score')
                axes[0, 0].set_ylabel('Frequency')
                axes[0, 0].set_title('Distribution of Anomaly Scores')
                axes[0, 0].legend()
                axes[0, 0].grid(True, alpha=0.3)
            except Exception as e:
                pass  # Error creating histogram
                axes[0, 0].text(0.5, 0.5, 'Error creating\nhistogram', ha='center', va='center', transform=axes[0, 0].transAxes)
            
            # Normal vs Anomaly Pie Chart
            try:
                normal_count = len(anomaly_scores) - sum(predictions)
                anomaly_count = sum(predictions)
                labels = ['Normal', 'Anomaly']
                counts = [normal_count, anomaly_count]
                colors = ['lightgreen', 'lightcoral']
                axes[0, 1].pie(counts, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
                axes[0, 1].set_title('Normal vs Anomaly Distribution')
            except Exception as e:
                pass  # Error creating pie chart
                axes[0, 1].text(0.5, 0.5, 'Error creating\npie chart', ha='center', va='center', transform=axes[0, 1].transAxes)
            
            # Feature Importance (Top 10)
            try:
                if feature_importance:
                    top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:10]
                    if top_features:
                        features, importance = zip(*top_features)
                        y_pos = np.arange(len(features))
                        axes[1, 0].barh(y_pos, importance, color='lightblue')
                        axes[1, 0].set_yticks(y_pos)
                        axes[1, 0].set_yticklabels([f[:15] + '...' if len(f) > 15 else f for f in features])
                        axes[1, 0].set_xlabel('Importance Score')
                        axes[1, 0].set_title('Top 10 Feature Importance')
                        axes[1, 0].grid(True, alpha=0.3)
                else:
                    axes[1, 0].text(0.5, 0.5, 'Feature importance\nnot available', 
                                   ha='center', va='center', transform=axes[1, 0].transAxes)
                    axes[1, 0].set_title('Feature Importance')
            except Exception as e:
                pass  # Error creating feature chart
                axes[1, 0].text(0.5, 0.5, 'Error creating\nfeature chart', ha='center', va='center', transform=axes[1, 0].transAxes)
            
            # Anomaly Scores Over Samples
            try:
                if len(anomaly_scores) > 10:
                    sample_indices = np.linspace(0, len(anomaly_scores)-1, min(100, len(anomaly_scores)), dtype=int)
                    sampled_scores = [anomaly_scores[i] for i in sample_indices]
                    axes[1, 1].plot(sample_indices, sampled_scores, marker='o', markersize=3, alpha=0.7, color='blue')
                    axes[1, 1].axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Threshold')
                    axes[1, 1].set_xlabel('Sample Index')
                    axes[1, 1].set_ylabel('Anomaly Score')
                    axes[1, 1].set_title('Anomaly Scores Over Samples')
                    axes[1, 1].legend()
                    axes[1, 1].grid(True, alpha=0.3)
                else:
                    axes[1, 1].text(0.5, 0.5, 'Insufficient data\nfor time series', 
                                   ha='center', va='center', transform=axes[1, 1].transAxes)
                    axes[1, 1].set_title('Anomaly Scores Over Time')
            except Exception as e:
                pass  # Error creating time series
                axes[1, 1].text(0.5, 0.5, 'Error creating\ntime series', ha='center', va='center', transform=axes[1, 1].transAxes)
            
            plt.tight_layout()
            
            # Save main analysis chart
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            charts.append(('main_analysis', img_buffer))
            plt.close()
    except Exception as e:
        pass  # Error creating main analysis chart
    
    # Chart 2: Severity Distribution (if available)
    try:
        severity_dist = detection_results.get('severity_distribution', {})
        if severity_dist and any(severity_dist.values()):
            fig, ax = plt.subplots(figsize=(8, 6))
            colors_map = {'high': 'red', 'medium': 'orange', 'low': 'yellow'}
            colors_list = [colors_map.get(sev.lower(), 'blue') for sev in severity_dist.keys()]
            
            wedges, texts, autotexts = ax.pie(severity_dist.values(), labels=severity_dist.keys(), 
                                            autopct='%1.1f%%', colors=colors_list, startangle=90)
            ax.set_title('Anomaly Severity Distribution', fontsize=14, fontweight='bold')
            
            img_buffer = io.BytesIO()
            plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
            img_buffer.seek(0)
            charts.append(('severity_distribution', img_buffer))
            plt.close()
    except Exception as e:
        print(f"Error creating severity distribution chart: {e}")
    
    # Chart 3: Score Statistics Box Plot
    try:
        if anomaly_scores:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # Separate scores by prediction
            normal_scores = [score for i, score in enumerate(anomaly_scores) if i < len(predictions) and predictions[i] == 0]
            anomaly_scores_only = [score for i, score in enumerate(anomaly_scores) if i < len(predictions) and predictions[i] == 1]
            
            data_to_plot = []
            labels = []
            if normal_scores:
                data_to_plot.append(normal_scores)
                labels.append('Normal')
            if anomaly_scores_only:
                data_to_plot.append(anomaly_scores_only)
                labels.append('Anomaly')
            
            if data_to_plot:
                bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
                colors = ['lightgreen', 'lightcoral']
                for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
                    patch.set_facecolor(color)
                
                ax.set_ylabel('Anomaly Score')
                ax.set_title('Score Distribution by Classification', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                
                img_buffer = io.BytesIO()
                plt.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
                img_buffer.seek(0)
                charts.append(('score_statistics', img_buffer))
                plt.close()
    except Exception as e:
        print(f"Error creating box plot chart: {e}")
    
    return charts

@app.route('/api/csv/reports/<report_id>/download-pdf', methods=['GET'])
@token_required
@analyst_or_admin_required
def download_pdf_report(report_id):
    """Download CSV analysis report as PDF file with charts"""
    try:
        report = csv_processor.get_report(report_id)
        
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Create PDF document
        doc = SimpleDocTemplate(temp_path, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        # Title
        story.append(Paragraph("SOC Anomaly Detection Report", title_style))
        story.append(Spacer(1, 20))
        
        # Report metadata table - use comprehensive data
        detection_results = report.get('detection_results', {})
        file_info = report.get('file_info', {})
        
        metadata = [
            ['Report ID:', report.get('report_id', 'N/A')],
            ['Generated:', report.get('timestamp', 'N/A')],
            ['File:', file_info.get('filename', 'N/A')],
            ['Total Records:', str(detection_results.get('total_records', 'N/A'))],
            ['Anomalies Detected:', str(detection_results.get('anomalies_detected', 'N/A'))],
            ['Anomaly Rate:', f"{detection_results.get('anomaly_percentage', 0):.2f}%" if isinstance(detection_results.get('anomaly_percentage'), (int, float)) else str(detection_results.get('anomaly_percentage', 'N/A'))],
            ['Model Used:', detection_results.get('model_used', 'N/A')],
            ['Detection Method:', detection_results.get('method', 'N/A')]
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (1, 0), (1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        # Summary statistics from comprehensive report
        summary_stats = report.get('summary_statistics', {})
        if summary_stats:
            story.append(Paragraph("Summary Statistics", heading_style))
            summary_data = []
            
            # Basic statistics
            summary_data.append(['Total Records Analyzed', str(summary_stats.get('total_records_analyzed', 'N/A'))])
            summary_data.append(['Anomalies Detected', str(summary_stats.get('anomalies_detected', 'N/A'))])
            summary_data.append(['Anomaly Rate', f"{summary_stats.get('anomaly_rate_percentage', 0):.2f}%"])
            summary_data.append(['Normal Records', str(summary_stats.get('normal_records', 'N/A'))])
            
            # Score statistics
            score_stats = summary_stats.get('score_statistics', {})
            if score_stats:
                summary_data.append(['Mean Anomaly Score', f"{score_stats.get('mean_score', 0):.4f}"])
                summary_data.append(['Median Anomaly Score', f"{score_stats.get('median_score', 0):.4f}"])
                summary_data.append(['Max Anomaly Score', f"{score_stats.get('max_score', 0):.4f}"])
                summary_data.append(['95th Percentile Score', f"{score_stats.get('percentile_95', 0):.4f}"])
            
            # Model performance
            model_perf = summary_stats.get('model_performance', {})
            if model_perf:
                summary_data.append(['High Confidence Anomalies', str(model_perf.get('high_confidence_anomalies', 'N/A'))])
                summary_data.append(['Medium Confidence Anomalies', str(model_perf.get('medium_confidence_anomalies', 'N/A'))])
                summary_data.append(['Detection Threshold', str(model_perf.get('detection_threshold', 'N/A'))])
            
            if summary_data:
                summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 20))
        
        # Generate and add charts
        try:
            charts = create_anomaly_charts(report)
            
            if charts:
                story.append(Paragraph("Anomaly Analysis Charts", heading_style))
                story.append(Spacer(1, 10))
                
                for chart_name, chart_buffer in charts:
                    try:
                        # Create image directly from BytesIO buffer
                        chart_buffer.seek(0)  # Reset buffer position
                        img = Image(chart_buffer, width=6*inch, height=3.6*inch)
                        story.append(img)
                        story.append(Spacer(1, 15))
                    except Exception as e:
                        print(f"Error adding chart {chart_name} to PDF: {e}")
                        story.append(Paragraph(f"Chart '{chart_name}' could not be generated", styles['Normal']))
                        story.append(Spacer(1, 10))
            else:
                story.append(Paragraph("Charts", heading_style))
                story.append(Paragraph("No charts could be generated for this report.", styles['Normal']))
                story.append(Spacer(1, 15))
        except Exception as e:
            print(f"Error generating charts: {e}")
            story.append(Paragraph("Charts", heading_style))
            story.append(Paragraph("Charts could not be generated due to technical issues.", styles['Normal']))
            story.append(Spacer(1, 15))
        
        # Add detailed analysis section
        detailed_analysis = report.get('detailed_analysis', {})
        if detailed_analysis:
            story.append(Paragraph("Detailed Analysis", heading_style))
            
            # Data Quality Assessment
            data_quality = detailed_analysis.get('data_quality_assessment', {})
            if data_quality:
                story.append(Paragraph("Data Quality Assessment", ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=6)))
                quality_data = [
                    ['Original Records', str(data_quality.get('original_records', 'N/A'))],
                    ['Processed Records', str(data_quality.get('processed_records', 'N/A'))],
                    ['Features Analyzed', str(data_quality.get('features_analyzed', 'N/A'))],
                    ['Data Completeness', str(data_quality.get('data_completeness', 'N/A'))]
                ]
                
                quality_table = Table(quality_data, colWidths=[2*inch, 2*inch])
                quality_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
                ]))
                story.append(quality_table)
                story.append(Spacer(1, 10))
            
            # Anomaly Patterns
            anomaly_patterns = detailed_analysis.get('anomaly_patterns', {})
            if anomaly_patterns:
                story.append(Paragraph("Anomaly Patterns", ParagraphStyle('SubHeading', parent=styles['Heading3'], fontSize=12, spaceAfter=6)))
                pattern_data = [
                    ['Distribution Type', str(anomaly_patterns.get('distribution_type', 'N/A'))],
                    ['Score Concentration', str(anomaly_patterns.get('score_concentration', 'N/A'))],
                    ['Attack Indicators', 'Yes' if anomaly_patterns.get('potential_attack_indicators') else 'No']
                ]
                
                pattern_table = Table(pattern_data, colWidths=[2*inch, 2*inch])
                pattern_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
                ]))
                story.append(pattern_table)
                story.append(Spacer(1, 15))
        
        # Add recommendations section
        recommendations = report.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Security Recommendations", heading_style))
            
            for i, rec in enumerate(recommendations, 1):
                story.append(Paragraph(f"{i}. {rec}", styles['Normal']))
                story.append(Spacer(1, 6))
            
            story.append(Spacer(1, 15))
        
        # Anomaly details table from detection results
        anomaly_records = detection_results.get('anomaly_records', [])
        if anomaly_records:
            story.append(PageBreak())
            story.append(Paragraph("Top Anomalous Records", heading_style))
            story.append(Spacer(1, 10))
            
            # Table headers
            anomaly_data = [['Index', 'Anomaly Score', 'Confidence', 'Key Features']]
            
            # Add anomaly rows (limit to first 20 for PDF readability)
            for i, record in enumerate(anomaly_records[:20]):
                idx = str(i + 1)
                score = f"{record.get('anomaly_score', 0):.4f}" if isinstance(record.get('anomaly_score'), (int, float)) else str(record.get('anomaly_score', 'N/A'))
                confidence = f"{record.get('confidence', 0):.3f}" if isinstance(record.get('confidence'), (int, float)) else str(record.get('confidence', 'N/A'))
                
                # Get key features (first few non-score fields)
                key_features = []
                for key, value in record.items():
                    if key not in ['anomaly_score', 'confidence'] and len(key_features) < 3:
                        key_features.append(f"{key}: {value}")
                features_str = "; ".join(key_features) if key_features else "N/A"
                if len(features_str) > 40:
                    features_str = features_str[:37] + "..."
                
                anomaly_data.append([idx, score, confidence, features_str])
            
            if len(anomaly_records) > 20:
                anomaly_data.append(['...', '...', '...', f"Showing top 20 of {len(anomaly_records)} anomalies"])
            
            anomaly_table = Table(anomaly_data, colWidths=[0.5*inch, 1*inch, 1*inch, 3.5*inch])
            anomaly_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(anomaly_table)
        
        # Build PDF
        doc.build(story)
        
        # Log the download
        username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        audit_logger.log_event(
            event_type='csv_report_generated',
            username=username,
            details={
                'report_id': report_id,
                'action': 'download_pdf'
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=f"anomaly_report_{report_id}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        import traceback
        print(f"Error downloading PDF report {report_id}: {e}")
        print(f"Full traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Failed to download PDF report: {str(e)}'}), 500

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
            event_type='csv_cleanup',
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
    pass  # Client disconnected silently

@socketio.on('request_alerts')
def handle_request_alerts(data=None):
    """Send current alerts to client (authenticated users only)"""
    from flask import session
    if not session.get('username'):
        emit('error', {'message': 'Authentication required'})
        return
    
    # Get recent alerts from MongoDB
    try:
        result = dashboard_api.dal.get_alerts(filters={}, page=1, per_page=20)
        recent_alerts = result.get('alerts', [])
        
        # Convert ObjectId to string for JSON serialization
        for alert in recent_alerts:
            if '_id' in alert:
                alert['_id'] = str(alert['_id'])
            # Convert datetime to ISO string if needed
            if 'timestamp' in alert and hasattr(alert['timestamp'], 'isoformat'):
                alert['timestamp'] = alert['timestamp'].isoformat()
        
        emit('alerts_update', {
            'alerts': recent_alerts,
            'stats': dashboard_api.get_system_stats()
        })
    except Exception as e:
        print(f"Error getting alerts for WebSocket: {e}")
        emit('error', {'message': 'Failed to get alerts'})

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
