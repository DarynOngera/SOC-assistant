#!/usr/bin/env python3
"""
SOC Dashboard Backend Server
Real-time anomaly detection API with WebSocket support and Authentication
"""

import os
import sys
import json
import tempfile
import logging
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
from flask import Flask, request, jsonify, send_file
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename
import joblib
import glob
import uuid
from bson import ObjectId

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# MongoDB imports
from src.database.mongodb_config import initialize_mongodb, mongodb_health_check
from src.database.mongodb_dal import get_dal
from src.database.schemas import AlertSeverity, AlertStatus, AuditEventType
from src.database.migration_utils import migrate_existing_data
from src.auth.mongodb_auth_utils import MongoDBAuthManager, token_required, admin_required, analyst_or_admin_required
from src.utils.csv_processor import CSVProcessor
from src.utils.audit_exporter import AuditExporter

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create logger for this module
logger = logging.getLogger(__name__)

# Reduce noise from external libraries
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('socketio').setLevel(logging.WARNING)
logging.getLogger('engineio').setLevel(logging.WARNING)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

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
            
            # Get all recent audit logs
            result = self.dal.get_audit_logs(
                filters={'timestamp': {'$gte': cutoff_date}}, 
                page=1, 
                per_page=10000
            )
            records = result.get('logs', [])
            
            security_events = []
            
            # Track failed login attempts by user
            failed_attempts = {}
            
            for record in records:
                event_type = record.get('event_type')
                username = record.get('username', 'unknown')
                
                # Multiple failed login attempts
                if event_type == 'login_failed':
                    if username not in failed_attempts:
                        failed_attempts[username] = []
                    failed_attempts[username].append(record)
                
                # Direct security events
                elif event_type in ['unauthorized_access', 'account_locked', 'suspicious_activity']:
                    security_events.append({
                        'type': 'security_event',
                        'severity': 'high' if event_type == 'unauthorized_access' else 'medium',
                        'event_type': event_type,
                        'username': username,
                        'timestamp': record.get('timestamp'),
                        'details': record.get('details', {}),
                        'description': f"{event_type.replace('_', ' ').title()} for user {username}"
                    })
            
            # Process failed login attempts
            for username, attempts in failed_attempts.items():
                if len(attempts) >= 3:  # Multiple failed attempts
                    security_events.append({
                        'type': 'failed_login_pattern',
                        'severity': 'high' if len(attempts) >= 5 else 'medium',
                        'event_type': 'multiple_failed_logins',
                        'username': username,
                        'timestamp': attempts[-1].get('timestamp'),
                        'count': len(attempts),
                        'details': {'attempts': len(attempts), 'timespan': f'{days} days'},
                        'description': f"Multiple failed login attempts ({len(attempts)}) for user {username}"
                    })
            
            # Sort by timestamp (most recent first)
            security_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            return security_events
        except Exception as e:
            print(f"Error getting security alerts: {e}")
            import traceback
            traceback.print_exc()
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
        details={'action': 'login', 'status': 'success'},
        ip_address=ip_address,
        user_agent=user_agent
    )

def log_login_failed(username, ip_address, user_agent, reason):
    """Log failed login attempt"""
    audit_logger.log_event(
        event_type='login_failed',
        username=username,
        details={'action': 'login', 'status': 'failed', 'reason': reason},
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
        self.threshold = 0.7  # Increased from 0.5 to reduce false positives
        self.presentation_mode = False  # Toggle for demo presentations
        self.is_monitoring = False
        self.load_models()
        
        # Initialize system stats in MongoDB if not exists
        self._initialize_system_stats()
        
        # Attack simulation state
        self.simulation_active = False
        self.current_simulation = None
        self.simulation_duration = 0
        self.simulation_start_time = None
        
        # Mininet integration state
        self.mininet_active = False
        self.mininet_process = None
        self.mininet_mode = 'normal'  # 'normal' or 'attack'
        self.available_attacks = [
            'syn_flood', 'port_scan', 'udp_flood', 'icmp_flood',
            'http_flood', 'dns_amplification', 'brute_force', 'slowloris'
        ]
        
    def load_models(self):
        """Load ML models for anomaly detection"""
        try:
            from src.models.supervised_trainer import SupervisedSOCDetector
            import os
            
            # Find the correct models directory regardless of current working directory
            possible_model_paths = [
                'models',  # If running from project root
                '../models',  # If running from src/dashboard
                '../../models',  # If running from deeper subdirectory
                '/home/ongera/projects/SOC-assistant/models'  # Absolute path as fallback
            ]
            
            models_dir = None
            for path in possible_model_paths:
                if os.path.exists(path) and os.path.isdir(path):
                    # Check if it actually contains model files
                    model_files = [f for f in os.listdir(path) if f.endswith('.pkl')]
                    if model_files:
                        models_dir = path
                        break
            
            if not models_dir:
                raise FileNotFoundError("Models directory not found in any expected location")
            
            logger.info(f"Loading models from: {models_dir}")
            self.detector = SupervisedSOCDetector()
            self.detector.load_models(models_dir)
            
            logger.info("Models loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading models: {e}")
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
        
        # Get feature template from trained model if available
        logger.debug(f"🔍 Detector status: detector={self.detector is not None}, has_method={hasattr(self.detector, 'get_feature_template') if self.detector else False}")
        
        if self.detector and hasattr(self.detector, 'get_feature_template'):
            try:
                template = self.detector.get_feature_template()
                feature_columns = template.get('feature_columns', [])
                logger.info(f"🎯 Using model feature template with {len(feature_columns)} features")
                logger.debug(f"📋 Model features: {feature_columns[:10]}...")
            except Exception as e:
                logger.error(f"❌ Error getting feature template: {e}")
                import traceback
                logger.error(traceback.format_exc())
                feature_columns = []
        else:
            logger.warning(f"⚠️ Detector not available or missing method")
            feature_columns = []
            
        # If no feature template available, use fallback
        if not feature_columns:
            logger.info("📋 Using fallback feature template")
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
                # Adjust anomaly rate based on presentation mode
                anomaly_rate = 0.15 if self.presentation_mode else 0.05  # Reduced from 20% to 5% (15% in presentation mode)
                
                if np.random.random() < anomaly_rate:
                    # Generate anomalies with scores above threshold for clear detection
                    anomaly_score = float(np.random.uniform(0.75, 0.95))  # Higher scores for clear anomalies
                    prediction = 1
                    confidence = float(np.random.uniform(0.8, 0.95))
                    # Generate realistic attack types based on anomaly score
                    attack_types = ['Brute Force', 'DDoS', 'Port Scan', 'SQL Injection', 'Web Attack', 'Network Scan', 'Data Exfiltration']
                    attack_type = np.random.choice(attack_types)
                else:
                    # Normal traffic with scores well below threshold
                    anomaly_score = float(np.random.uniform(0.05, 0.3))  # Reduced max from 0.4 to 0.3
                    prediction = 0
                    confidence = float(np.random.uniform(0.7, 0.9))
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
        # Step 1: Generate realistic network traffic data using model features
        network_data = self._generate_model_compatible_data(batch_size)
        
        # Step 2: Process through trained models for real anomaly predictions
        processed_data = self.process_with_models(network_data)
        
        return processed_data
    
    def _generate_model_compatible_data(self, batch_size=10):
        """Generate network data using the exact features the model expects"""
        import random
        import numpy as np
        
        # Get the model's expected features
        logger.debug(f"🔍 Model check: detector={self.detector is not None}, has_method={hasattr(self.detector, 'get_feature_template') if self.detector else False}")
        
        if self.detector and hasattr(self.detector, 'get_feature_template'):
            try:
                template = self.detector.get_feature_template()
                feature_columns = template.get('feature_columns', [])
                logger.info(f"🎯 Generating data with model features: {len(feature_columns)} features")
            except Exception as e:
                logger.error(f"Error getting model features: {e}")
                return self._generate_fallback_data(batch_size)
        else:
            logger.warning(f"⚠️ Model not available in data generation: detector={self.detector is not None}")
            return self._generate_fallback_data(batch_size)
        
        if not feature_columns:
            return self._generate_fallback_data(batch_size)
        
        # Generate data with the exact features the model expects
        network_data = []
        for i in range(batch_size):
            record = {}
            
            # Generate each feature the model expects
            for feature in feature_columns:
                if feature == 'index':
                    record[feature] = i
                elif feature == 'duration':
                    record[feature] = random.uniform(0.1, 10.0)
                elif feature == 'protocol':
                    record[feature] = random.choice(['TCP', 'UDP'])  # Use uppercase as expected by model
                elif feature in ['src_ip', 'dst_ip']:
                    record[feature] = f"10.0.{random.randint(1,3)}.{random.randint(1,10)}"
                elif feature in ['src_port', 'dst_port']:
                    record[feature] = random.randint(1024, 65535) if 'src' in feature else random.choice([80, 443, 22, 21, 53])
                elif feature == 'packet_count':
                    record[feature] = random.randint(1, 100)
                elif feature == 'byte_count':
                    record[feature] = random.randint(60, 10000)
                elif feature in ['packets_per_sec', 'bytes_per_sec']:
                    record[feature] = random.uniform(1, 1000)
                elif 'packet_size' in feature:
                    record[feature] = random.uniform(60, 1500)
                elif 'inter_arrival_time' in feature:
                    record[feature] = random.uniform(0.001, 1.0)
                elif feature in ['syn_count', 'fin_count', 'rst_count', 'psh_count', 'ack_count', 'urg_count']:
                    record[feature] = random.randint(0, 10)
                elif 'ratio' in feature:
                    record[feature] = random.uniform(0.0, 1.0)
                elif feature == 'is_well_known_port':
                    record[feature] = random.choice([0, 1])
                else:
                    # Default for unknown features
                    record[feature] = random.uniform(0, 1)
            
            network_data.append(record)
        
        logger.info(f"✅ Generated {len(network_data)} records with model-compatible features")
        return network_data
    
    def _generate_fallback_data(self, batch_size=10):
        """Fallback data generation when model features aren't available"""
        logger.info("📋 Using fallback data generation")
        return self.generate_realistic_network_data(batch_size)
    
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
        # Ensure model is loaded before starting monitoring
        if not self.detector:
            logger.info("🔄 Loading models before starting monitoring...")
            try:
                self.load_models()
                if not self.detector:
                    logger.error("❌ Cannot start monitoring: Model loading failed")
                    return False
            except Exception as e:
                logger.error(f"Failed to load models for monitoring: {e}")
                return False
        
        def monitor_loop():
            logger.info("🔄 Monitoring thread started")
            
            while self.is_monitoring:
                try:
                    # Skip model checking - if we got here, model should be loaded
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
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(5)
            
            logger.info("🛑 Monitoring thread stopped")
        
        if not self.is_monitoring:
            self.is_monitoring = True
            monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitoring_thread.start()
            logger.info("✅ Monitoring started successfully")
            return True
        
        return True
    
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
    
    # Mininet Integration Methods
    def start_mininet_simulation(self, mode='normal', attack_type=None, duration=5):
        """Start Mininet simulation by replaying existing PCAP files"""
        if self.mininet_active:
            return {'success': False, 'message': 'Mininet simulation already running'}
        
        try:
            import os
            import glob
            
            # Ensure topology is exported first
            self._ensure_topology_exported()
            
            # Find existing PCAP files
            pcap_dir = os.path.join(
                os.path.dirname(__file__), 
                '..', '..', 
                'mininet_data_generation', 
                'data_capture', 
                'mininet'
            )
            
            if mode == 'normal':
                # Look for normal traffic PCAP in parent directory
                normal_pcap_dir = os.path.join(
                    os.path.dirname(__file__), 
                    '..', '..', 
                    'data_capture', 
                    'pcaps'
                )
                pcap_files = glob.glob(os.path.join(normal_pcap_dir, 'normal_traffic_*.pcap'))
                if not pcap_files:
                    return {'success': False, 'message': 'No normal traffic PCAP files found. Run the Mininet pipeline first.'}
                pcap_file = max(pcap_files, key=os.path.getctime)  # Get latest file
                simulation_name = 'normal_traffic'
                
            elif mode == 'attack' and attack_type:
                pcap_file = os.path.join(pcap_dir, f'{attack_type}.pcap')
                if not os.path.exists(pcap_file):
                    return {'success': False, 'message': f'PCAP file for {attack_type} not found. Run the Mininet pipeline first.'}
                simulation_name = attack_type
                
            else:
                return {'success': False, 'message': 'Invalid mode or missing attack type'}
            
            # Start simulation replay
            logger.info(f"Starting Mininet simulation replay: {mode} ({attack_type if attack_type else 'N/A'})")
            logger.info(f"Using PCAP file: {pcap_file}")
            
            self.mininet_active = True
            self.mininet_mode = mode
            self.current_simulation = simulation_name
            self.simulation_start_time = datetime.now()
            self.simulation_duration = duration
            self.simulation_pcap_file = pcap_file
            self.mininet_process = None  # No actual process for replay
            
            # Ensure monitoring is active for real-time updates
            if not self.is_monitoring:
                logger.info("🔄 Starting monitoring system for Mininet simulation")
                success = self.start_monitoring()
                if not success:
                    logger.error("❌ Failed to start monitoring for Mininet simulation")
                    # Continue anyway - Mininet simulation can still work
            
            # Start replay processing thread
            replay_thread = threading.Thread(
                target=self._replay_pcap_simulation,
                args=(pcap_file, duration),
                daemon=True
            )
            replay_thread.start()
            
            return {
                'success': True,
                'message': f'Mininet {mode} simulation started (replaying PCAP)',
                'mode': mode,
                'attack_type': attack_type,
                'duration': duration,
                'pcap_file': pcap_file,
                'replay_mode': True
            }
            
        except Exception as e:
            logger.error(f"Error starting Mininet simulation: {e}")
            return {'success': False, 'message': f'Failed to start simulation: {str(e)}'}
    
    def stop_mininet_simulation(self):
        """Stop current Mininet simulation"""
        if not self.mininet_active:
            return {'success': False, 'message': 'No active Mininet simulation'}
        
        try:
            logger.info("Stopping Mininet simulation")
            
            # For PCAP replay mode, just update the state
            self.mininet_active = False
            self.mininet_process = None
            self.current_simulation = None
            
            return {'success': True, 'message': 'Mininet simulation stopped'}
            
        except Exception as e:
            logger.error(f"Error stopping Mininet simulation: {e}")
            return {'success': False, 'message': f'Failed to stop simulation: {str(e)}'}
    
    def _ensure_topology_exported(self):
        """Ensure Mininet topology is exported"""
        try:
            import os
            import sys
            
            # Check if topology file exists
            topology_file = os.path.join(
                os.path.dirname(__file__),
                '../../mininet_data_generation/data_capture/mininet_topology.json'
            )
            
            if not os.path.exists(topology_file):
                logger.info("Exporting Mininet topology...")
                
                # Add topology directory to path
                topology_dir = os.path.join(
                    os.path.dirname(__file__),
                    '../../mininet_data_generation/topology'
                )
                sys.path.append(topology_dir)
                
                from topology_exporter import TopologyExporter
                
                exporter = TopologyExporter()
                exporter.export_topology()
                logger.info("Topology exported successfully")
            
        except Exception as e:
            logger.warning(f"Could not export topology: {e}")
    
    def _replay_pcap_simulation(self, pcap_file, duration):
        """Replay PCAP file simulation with immediate alert generation"""
        try:
            import time
            
            logger.info(f"Starting PCAP replay simulation for {duration} seconds")
            
            # Process PCAP file and generate alerts immediately
            self._process_pcap_for_alerts(pcap_file)
            
            # For PCAP replay, we don't need to wait - alerts are generated instantly
            # Just wait a short time to let the frontend show progress, then complete
            time.sleep(2)  # Just 2 seconds for visual feedback
            
            # Simulation completed
            if self.mininet_active:  # Only if not stopped manually
                self.mininet_active = False
                self.mininet_process = None
                
                logger.info("PCAP replay simulation completed")
                
                # Emit completion event and trigger dashboard refresh
                socketio.emit('mininet_simulation_completed', {
                    'mode': self.mininet_mode,
                    'simulation': self.current_simulation,
                    'duration': duration,
                    'pcap_file': pcap_file
                })
                
                # Also emit a stats update to refresh dashboard
                updated_stats = self.get_system_stats()
                socketio.emit('stats_update', updated_stats)
            
        except Exception as e:
            logger.error(f"Error in PCAP replay simulation: {e}")
            self.mininet_active = False
            self.mininet_process = None
    
    def _process_pcap_for_alerts(self, pcap_file):
        """Process actual PCAP file using ML model to generate realistic alerts"""
        try:
            import os
            import random
            from datetime import datetime, timedelta
            
            logger.info(f"🔬 Processing actual PCAP file: {pcap_file}")
            
            # Check if PCAP file exists
            if not os.path.exists(pcap_file):
                logger.warning(f"PCAP file not found: {pcap_file}, trying normal traffic PCAP")
                pcap_file = self._get_fallback_pcap_file()
            
            # Extract features from actual PCAP file
            network_data = self._extract_features_from_pcap(pcap_file)
            
            if not network_data:
                logger.warning(f"No IPv4 data in PCAP: {pcap_file}, trying normal traffic PCAP")
                pcap_file = self._get_fallback_pcap_file()
                network_data = self._extract_features_from_pcap(pcap_file)
                
            if not network_data:
                logger.error("No usable PCAP files found, using synthetic data as last resort")
                return self._generate_synthetic_attack_data()
            
            logger.info(f"📊 Extracted {len(network_data)} records from PCAP file: {os.path.basename(pcap_file)}")
            
            # If this is an attack simulation but we're using normal traffic PCAP,
            # apply attack patterns to make it realistic
            if 'attack' in self.current_simulation or self.current_simulation != 'normal_traffic':
                if 'normal_traffic' in pcap_file:
                    logger.info(f"🎯 Applying {self.current_simulation} patterns to normal traffic data")
                    network_data = self._inject_attack_patterns(network_data, self.current_simulation)
            
            # Process through ML model pipeline
            processed_data = self.process_with_models(network_data)
            
            # Convert model predictions to alerts
            new_alerts = []
            for record in processed_data:
                # Only create alerts for anomalies detected by the model
                if record.get('prediction', 0) == 1 and record.get('anomaly_score', 0) >= self.threshold:
                    
                    # Create alert data from model prediction
                    alert_data = {
                        'timestamp': datetime.now() - timedelta(seconds=random.randint(0, 60)),
                        'source_ip': record.get('source_ip', f"10.0.{random.randint(1,3)}.{random.randint(1,10)}"),
                        'destination_ip': record.get('destination_ip', f"10.0.{random.randint(1,3)}.{random.randint(1,10)}"),
                        'source_port': int(record.get('source_port', random.randint(1024, 65535))),
                        'destination_port': int(record.get('destination_port', random.choice([80, 443, 22, 21, 53, 3306]))),
                        'protocol': record.get('protocol', 'tcp').lower(),
                        'attack_type': record.get('attack_type', 'anomaly_detected'),
                        'severity': self._calculate_severity_from_score(record.get('anomaly_score', 0.5)),
                        'anomaly_score': float(record.get('anomaly_score', 0.5)),
                        'status': 'new',
                        'created_by': 'mininet_ml_model',
                        'tags': ['mininet', 'ml_detected', self.current_simulation],
                        'confidence': float(record.get('confidence', 0.5)),
                        'simulation_source': True,
                        'description': f"ML model detected anomaly in Mininet simulation: {self.current_simulation}"
                    }
                
                # Store alert in database using create_alert method
                try:
                    success, message, db_alert_id = self.dal.create_alert(alert_data)
                    if success:
                        # Add the generated alert_id to our data for broadcasting
                        alert_data['alert_id'] = db_alert_id
                        new_alerts.append(alert_data)
                        logger.info(f"✅ Stored Mininet alert: {db_alert_id} - {alert_data['attack_type']} ({alert_data['severity']})")
                    else:
                        logger.error(f"❌ Failed to create alert: {message}")
                except Exception as e:
                    logger.error(f"❌ Exception storing alert: {e}")
            
            logger.info(f"🎯 ML Model Results: Generated {len(new_alerts)} alerts from {len(processed_data)} network records")
            logger.info(f"📊 Alert Detection Rate: {len(new_alerts)}/{len(processed_data)} ({len(new_alerts)/len(processed_data)*100:.1f}%)")
            
            # Log attack type distribution
            if new_alerts:
                attack_types = {}
                for alert in new_alerts:
                    attack_type = alert.get('attack_type', 'unknown')
                    attack_types[attack_type] = attack_types.get(attack_type, 0) + 1
                logger.info(f"🔍 Attack Types Detected: {dict(attack_types)}")
            else:
                logger.info("✅ No anomalies detected by ML model - normal traffic pattern")
            
            # Broadcast new alerts to all connected clients via WebSocket
            if new_alerts:
                try:
                    # Convert datetime objects to strings for JSON serialization
                    alerts_for_broadcast = []
                    for alert in new_alerts:
                        alert_copy = alert.copy()
                        if isinstance(alert_copy['timestamp'], datetime):
                            alert_copy['timestamp'] = alert_copy['timestamp'].isoformat()
                        alerts_for_broadcast.append(alert_copy)
                    
                    # Get updated stats
                    updated_stats = self.get_system_stats()
                    
                    # Emit to all connected clients using the same event as the monitoring system
                    socketio.emit('new_alerts', {
                        'alerts': alerts_for_broadcast,
                        'stats': updated_stats,
                        'source': 'mininet_simulation'
                    })
                    
                    # Also emit alerts_update for compatibility
                    socketio.emit('alerts_update', {
                        'alerts': alerts_for_broadcast,
                        'stats': updated_stats
                    })
                    
                    logger.info(f"✅ Broadcasted {len(new_alerts)} new alerts to dashboard via WebSocket")
                    
                except Exception as e:
                    logger.error(f"❌ Error broadcasting alerts: {e}")
            else:
                logger.warning("⚠️ No new alerts to broadcast - check alert generation")
            
        except Exception as e:
            logger.error(f"Error processing PCAP for alerts: {e}")
    
    def _get_fallback_pcap_file(self):
        """Get a working normal traffic PCAP file as fallback"""
        import os
        import glob
        
        # Look for normal traffic PCAP files
        normal_pcap_dirs = [
            '/home/ongera/projects/SOC-assistant/data_capture/pcaps/',
            '/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/'
        ]
        
        for pcap_dir in normal_pcap_dirs:
            if os.path.exists(pcap_dir):
                # Look for normal traffic files
                patterns = ['normal_traffic_*.pcap', '*.pcap']
                for pattern in patterns:
                    pcap_files = glob.glob(os.path.join(pcap_dir, pattern))
                    if pcap_files:
                        # Use the largest file (likely has more data)
                        largest_file = max(pcap_files, key=os.path.getsize)
                        logger.info(f"🔄 Using fallback PCAP: {largest_file}")
                        return largest_file
        
        logger.error("No fallback PCAP files found")
        return None
    
    def _extract_features_from_pcap(self, pcap_file):
        """Extract network features from PCAP file using the SAME method used for training"""
        try:
            from scapy.all import rdpcap, IP, TCP, UDP, ICMP
            from collections import defaultdict
            import numpy as np
            
            logger.info(f"🔍 Extracting features from PCAP using training method: {pcap_file}")
            
            # Read PCAP file using scapy (same as training)
            try:
                packets = rdpcap(pcap_file)
            except Exception as e:
                logger.error(f"Error reading PCAP file: {e}")
                return None
            
            # Group packets by flow (same as training pipeline)
            flows = defaultdict(list)
            ipv4_count = 0
            ipv6_count = 0
            other_count = 0
            
            for pkt in packets:
                if IP in pkt:
                    ipv4_count += 1
                    key = self._get_flow_key(pkt)
                    if key:
                        flows[key].append(pkt)
                elif 'IPv6' in str(pkt):
                    ipv6_count += 1
                else:
                    other_count += 1
            
            logger.info(f"📊 Packet analysis: IPv4={ipv4_count}, IPv6={ipv6_count}, Other={other_count}")
            
            # Extract features for each flow (same as training)
            network_data = []
            for flow_key, flow_packets in flows.items():
                feature = self._extract_flow_features(flow_key, flow_packets)
                if feature:
                    network_data.append(feature)
            
            logger.info(f"✅ Extracted {len(network_data)} flow records from PCAP")
            return network_data
                
        except ImportError:
            logger.error("scapy not installed - install with: pip install scapy")
            return None
        except Exception as e:
            logger.error(f"Error extracting features from PCAP: {e}")
            return None
    
    def _get_flow_key(self, pkt):
        """Get flow identifier from packet (same as training)"""
        from scapy.all import IP, TCP, UDP, ICMP
        
        if IP not in pkt:
            return None
        
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        
        if TCP in pkt:
            protocol = 'TCP'
            src_port = pkt[TCP].sport
            dst_port = pkt[TCP].dport
        elif UDP in pkt:
            protocol = 'UDP'
            src_port = pkt[UDP].sport
            dst_port = pkt[UDP].dport
        elif ICMP in pkt:
            protocol = 'ICMP'
            src_port = 0
            dst_port = 0
        else:
            return None
        
        return (src_ip, dst_ip, src_port, dst_port, protocol)
    
    def _extract_flow_features(self, flow_key, packets):
        """Extract features from flow packets (EXACT same as training)"""
        from scapy.all import TCP
        import numpy as np
        
        src_ip, dst_ip, src_port, dst_port, protocol = flow_key
        
        # Basic statistics
        packet_count = len(packets)
        if packet_count == 0:
            return None
        
        # Timing
        timestamps = [float(pkt.time) for pkt in packets]
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0.1
        
        # Packet sizes
        packet_sizes = [len(pkt) for pkt in packets]
        byte_count = sum(packet_sizes)
        
        # TCP flags
        syn_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x02)
        fin_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x01)
        rst_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x04)
        psh_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x08)
        ack_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x10)
        urg_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x20)
        
        # Derived features
        packets_per_sec = packet_count / duration if duration > 0 else 0
        bytes_per_sec = byte_count / duration if duration > 0 else 0
        mean_packet_size = np.mean(packet_sizes) if packet_sizes else 0
        std_packet_size = np.std(packet_sizes) if len(packet_sizes) > 1 else 0
        min_packet_size = min(packet_sizes) if packet_sizes else 0
        max_packet_size = max(packet_sizes) if packet_sizes else 0
        
        # Inter-arrival times
        if len(timestamps) > 1:
            inter_arrival_times = np.diff(timestamps)
            mean_iat = np.mean(inter_arrival_times)
            std_iat = np.std(inter_arrival_times)
        else:
            mean_iat = 0
            std_iat = 0
        
        # Flag ratios
        syn_ratio = syn_count / packet_count if packet_count > 0 else 0
        fin_ratio = fin_count / packet_count if packet_count > 0 else 0
        rst_ratio = rst_count / packet_count if packet_count > 0 else 0
        
        # Port classification
        is_well_known_port = 1 if dst_port < 1024 else 0
        
        # Return the EXACT same features as training (including index)
        return {
            'index': 0,  # Add missing index feature
            'duration': duration,
            'protocol': protocol,
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'packet_count': packet_count,
            'byte_count': byte_count,
            'packets_per_sec': packets_per_sec,
            'bytes_per_sec': bytes_per_sec,
            'mean_packet_size': mean_packet_size,
            'std_packet_size': std_packet_size,
            'min_packet_size': min_packet_size,
            'max_packet_size': max_packet_size,
            'mean_inter_arrival_time': mean_iat,
            'std_inter_arrival_time': std_iat,
            'syn_count': syn_count,
            'fin_count': fin_count,
            'rst_count': rst_count,
            'psh_count': psh_count,
            'ack_count': ack_count,
            'urg_count': urg_count,
            'syn_ratio': syn_ratio,
            'fin_ratio': fin_ratio,
            'rst_ratio': rst_ratio,
            'is_well_known_port': is_well_known_port
        }
    
    def _convert_to_model_features(self, raw_record):
        """Convert raw PCAP fields to model-expected features"""
        try:
            import random
            
            # Get the model's expected features
            if self.detector and hasattr(self.detector, 'get_feature_template'):
                template = self.detector.get_feature_template()
                expected_features = template.get('feature_columns', [])
            else:
                return None
            
            # Create record with model-expected features
            record = {}
            
            # Map raw PCAP fields to model features
            for feature in expected_features:
                if feature == 'duration':
                    record[feature] = float(raw_record.get('frame.time_relative', 0))
                elif feature == 'protocol_type':
                    proto = raw_record.get('ip.proto', '6')
                    record[feature] = 'tcp' if proto == '6' else 'udp' if proto == '17' else 'icmp'
                elif feature == 'service':
                    port = raw_record.get('tcp.dstport', '80')
                    # Map common ports to services
                    port_map = {'80': 'http', '443': 'https', '22': 'ssh', '21': 'ftp', '53': 'dns', '25': 'smtp'}
                    record[feature] = port_map.get(port, 'other')
                elif feature == 'flag':
                    flags = raw_record.get('tcp.flags', '0x18')
                    # Map TCP flags to connection states
                    record[feature] = 'SF' if '0x18' in flags else 'S0' if '0x02' in flags else 'REJ'
                elif feature == 'src_bytes':
                    record[feature] = int(raw_record.get('frame.len', 60))
                elif feature == 'dst_bytes':
                    record[feature] = int(raw_record.get('tcp.len', 0))
                elif feature in ['land', 'wrong_fragment', 'urgent', 'logged_in', 'root_shell', 'su_attempted', 'is_host_login', 'is_guest_login']:
                    # Binary features - mostly 0 for normal traffic
                    record[feature] = 0
                elif 'count' in feature:
                    # Connection counts - use reasonable defaults
                    record[feature] = random.randint(1, 10)
                elif 'rate' in feature or 'error' in feature:
                    # Rate features - mostly low for normal traffic
                    record[feature] = random.uniform(0.0, 0.1)
                else:
                    # Default numeric features
                    record[feature] = random.uniform(0, 1)
            
            return record
            
        except Exception as e:
            logger.error(f"Error converting PCAP record to model features: {e}")
            return None
    
    def _generate_synthetic_attack_data(self):
        """Generate synthetic attack data with realistic attack patterns"""
        import random
        import numpy as np
        from datetime import datetime, timedelta
        
        logger.info(f"🎯 Generating synthetic attack data for: {self.current_simulation}")
        
        # Generate realistic attack flows based on attack type
        if 'normal' in self.current_simulation:
            num_flows = random.randint(10, 20)
            attack_ratio = 0.05  # 5% anomalies for normal traffic
        else:
            num_flows = random.randint(30, 60)
            attack_ratio = 0.7   # 70% anomalies for attack traffic
        
        # Generate network flows with attack characteristics
        network_data = []
        for i in range(num_flows):
            # Create base flow
            flow = self._create_synthetic_flow(i, is_attack=random.random() < attack_ratio)
            network_data.append(flow)
        
        logger.info(f"📊 Generated {len(network_data)} synthetic flows ({attack_ratio*100:.0f}% attack patterns)")
        
        # Process through ML model pipeline
        processed_data = self.process_with_models(network_data)
        
        # Convert model predictions to alerts
        new_alerts = []
        for record in processed_data:
            # Only create alerts for anomalies detected by the model
            if record.get('prediction', 0) == 1 and record.get('anomaly_score', 0) >= self.threshold:
                
                # Create alert data from model prediction
                alert_data = {
                    'timestamp': datetime.now() - timedelta(seconds=random.randint(0, 60)),
                    'source_ip': record.get('src_ip', f"10.0.{random.randint(1,3)}.{random.randint(1,10)}"),
                    'destination_ip': record.get('dst_ip', f"10.0.{random.randint(1,3)}.{random.randint(1,10)}"),
                    'source_port': int(record.get('src_port', random.randint(1024, 65535))),
                    'destination_port': int(record.get('dst_port', random.choice([80, 443, 22, 21, 53, 3306]))),
                    'protocol': record.get('protocol', 'tcp').lower(),
                    'attack_type': record.get('attack_type', 'anomaly_detected'),
                    'severity': self._calculate_severity_from_score(record.get('anomaly_score', 0.5)),
                    'anomaly_score': float(record.get('anomaly_score', 0.5)),
                    'status': 'new',
                    'created_by': 'mininet_ml_model',
                    'tags': ['mininet', 'ml_detected', self.current_simulation],
                    'confidence': float(record.get('confidence', 0.5)),
                    'simulation_source': True,
                    'description': f"ML model detected anomaly in synthetic {self.current_simulation} data"
                }
                
                # Store alert in database using create_alert method
                try:
                    success, message, db_alert_id = self.dal.create_alert(alert_data)
                    if success:
                        # Add the generated alert_id to our data for broadcasting
                        alert_data['alert_id'] = db_alert_id
                        new_alerts.append(alert_data)
                        logger.info(f"✅ Stored synthetic alert: {db_alert_id} - {alert_data['attack_type']} ({alert_data['severity']})")
                    else:
                        logger.error(f"❌ Failed to create alert: {message}")
                except Exception as e:
                    logger.error(f"❌ Exception storing alert: {e}")
        
        logger.info(f"🎯 ML Model Results: Generated {len(new_alerts)} alerts from {len(processed_data)} synthetic records")
        logger.info(f"📊 Alert Detection Rate: {len(new_alerts)}/{len(processed_data)} ({len(new_alerts)/len(processed_data)*100:.1f}%)")
        
        # Broadcast new alerts to all connected clients via WebSocket
        if new_alerts:
            try:
                # Convert datetime objects to strings for JSON serialization
                alerts_for_broadcast = []
                for alert in new_alerts:
                    alert_copy = alert.copy()
                    if isinstance(alert_copy['timestamp'], datetime):
                        alert_copy['timestamp'] = alert_copy['timestamp'].isoformat()
                    alerts_for_broadcast.append(alert_copy)
                
                # Get updated stats
                updated_stats = self.get_system_stats()
                
                # Emit to all connected clients using the same event as the monitoring system
                socketio.emit('new_alerts', {
                    'alerts': alerts_for_broadcast,
                    'stats': updated_stats,
                    'source': 'mininet_simulation'
                })
                
                # Also emit alerts_update for compatibility
                socketio.emit('alerts_update', {
                    'alerts': alerts_for_broadcast,
                    'stats': updated_stats
                })
                
                logger.info(f"✅ Broadcasted {len(new_alerts)} synthetic alerts to dashboard via WebSocket")
                
            except Exception as e:
                logger.error(f"❌ Error broadcasting alerts: {e}")
        else:
            logger.info("✅ No anomalies detected by ML model - normal traffic pattern")
    
    def _create_synthetic_flow(self, index, is_attack=False):
        """Create a synthetic network flow with realistic characteristics"""
        import random
        import numpy as np
        
        base_flow = {
            'index': index,
            'duration': random.uniform(0.1, 10.0),
            'protocol': random.choice(['TCP', 'UDP']),  # Use uppercase to match model training
            'src_ip': f"10.0.{random.randint(1,3)}.{random.randint(1,10)}",
            'dst_ip': f"10.0.{random.randint(1,3)}.{random.randint(1,10)}",
            'src_port': random.randint(1024, 65535),
            'dst_port': random.choice([80, 443, 22, 21, 53, 3306, 8080]),
            'packet_count': random.randint(1, 100),
            'byte_count': random.randint(60, 10000),
            'is_well_known_port': 1 if random.randint(1, 65535) < 1024 else 0
        }
        
        # Calculate derived features
        base_flow['packets_per_sec'] = base_flow['packet_count'] / base_flow['duration']
        base_flow['bytes_per_sec'] = base_flow['byte_count'] / base_flow['duration']
        base_flow['mean_packet_size'] = base_flow['byte_count'] / base_flow['packet_count']
        base_flow['std_packet_size'] = random.uniform(0, base_flow['mean_packet_size'] * 0.3)
        base_flow['min_packet_size'] = max(60, base_flow['mean_packet_size'] - base_flow['std_packet_size'])
        base_flow['max_packet_size'] = base_flow['mean_packet_size'] + base_flow['std_packet_size']
        base_flow['mean_inter_arrival_time'] = base_flow['duration'] / base_flow['packet_count']
        base_flow['std_inter_arrival_time'] = random.uniform(0, base_flow['mean_inter_arrival_time'])
        
        # TCP flags
        base_flow['syn_count'] = random.randint(0, 5)
        base_flow['fin_count'] = random.randint(0, 3)
        base_flow['rst_count'] = random.randint(0, 2)
        base_flow['psh_count'] = random.randint(0, base_flow['packet_count'])
        base_flow['ack_count'] = random.randint(0, base_flow['packet_count'])
        base_flow['urg_count'] = random.randint(0, 1)
        
        # Flag ratios
        base_flow['syn_ratio'] = base_flow['syn_count'] / base_flow['packet_count']
        base_flow['fin_ratio'] = base_flow['fin_count'] / base_flow['packet_count']
        base_flow['rst_ratio'] = base_flow['rst_count'] / base_flow['packet_count']
        
        # If this should be an attack, modify characteristics
        if is_attack:
            if 'syn_flood' in self.current_simulation:
                base_flow['syn_count'] = random.randint(50, 200)
                base_flow['syn_ratio'] = 0.8 + random.uniform(0, 0.2)
                base_flow['packet_count'] = random.randint(100, 1000)
                base_flow['byte_count'] = random.randint(6000, 60000)
                base_flow['duration'] = random.uniform(0.01, 0.5)
            elif 'port_scan' in self.current_simulation:
                base_flow['packet_count'] = random.randint(20, 100)
                base_flow['byte_count'] = random.randint(1200, 6000)
                base_flow['duration'] = random.uniform(0.01, 0.1)
                base_flow['dst_port'] = random.randint(1, 65535)
            elif 'udp_flood' in self.current_simulation:
                base_flow['protocol'] = 'UDP'  # Use uppercase to match model
                base_flow['packet_count'] = random.randint(200, 2000)
                base_flow['byte_count'] = random.randint(20000, 200000)
                base_flow['duration'] = random.uniform(0.1, 2.0)
            elif 'http_flood' in self.current_simulation:
                base_flow['protocol'] = 'TCP'  # Use uppercase to match model
                base_flow['dst_port'] = random.choice([80, 443, 8080])
                base_flow['packet_count'] = random.randint(50, 500)
                base_flow['byte_count'] = random.randint(5000, 50000)
                base_flow['duration'] = random.uniform(0.1, 5.0)
            
            # Recalculate derived features for attacks
            base_flow['packets_per_sec'] = base_flow['packet_count'] / base_flow['duration']
            base_flow['bytes_per_sec'] = base_flow['byte_count'] / base_flow['duration']
            base_flow['mean_packet_size'] = base_flow['byte_count'] / base_flow['packet_count']
        
        return base_flow
    
    def _inject_attack_patterns(self, network_data, attack_type):
        """Inject attack-specific patterns into network data for realistic model detection"""
        try:
            import random
            import numpy as np
            
            logger.info(f"🎯 Injecting {attack_type} patterns into network data")
            
            # Modify a portion of the data to exhibit attack characteristics
            attack_ratio = 0.3  # 30% of data will have attack patterns
            num_attack_records = int(len(network_data) * attack_ratio)
            
            # Randomly select records to modify
            attack_indices = random.sample(range(len(network_data)), num_attack_records)
            
            for idx in attack_indices:
                record = network_data[idx]
                
                if attack_type == 'syn_flood':
                    # SYN flood characteristics using model features
                    if 'src_bytes' in record:
                        record['src_bytes'] = random.randint(50000, 200000)  # High bytes sent
                    if 'dst_bytes' in record:
                        record['dst_bytes'] = random.randint(0, 1000)  # Low bytes received
                    if 'duration' in record:
                        record['duration'] = random.uniform(0.001, 0.1)  # Very short duration
                    if 'count' in record:
                        record['count'] = random.randint(100, 1000)  # High connection count
                    if 'flag' in record:
                        record['flag'] = 'S0'  # SYN flood flag
                    if 'protocol_type' in record:
                        record['protocol_type'] = 'tcp'
                    if 'service' in record:
                        record['service'] = 'http'
                    
                elif attack_type == 'port_scan':
                    # Port scan characteristics using model features
                    if 'src_bytes' in record:
                        record['src_bytes'] = random.randint(100, 1000)  # Low bytes per connection
                    if 'dst_bytes' in record:
                        record['dst_bytes'] = random.randint(0, 100)  # Very low response
                    if 'duration' in record:
                        record['duration'] = random.uniform(0.001, 0.05)  # Very short connections
                    if 'count' in record:
                        record['count'] = random.randint(50, 500)  # Many connections
                    if 'srv_count' in record:
                        record['srv_count'] = random.randint(1, 10)  # Few services per connection
                    if 'flag' in record:
                        record['flag'] = random.choice(['REJ', 'S0', 'RSTR'])  # Rejected connections
                    if 'protocol_type' in record:
                        record['protocol_type'] = 'tcp'
                    
                elif attack_type == 'udp_flood':
                    # UDP flood characteristics using model features
                    if 'src_bytes' in record:
                        record['src_bytes'] = random.randint(100000, 500000)  # Very high bytes
                    if 'dst_bytes' in record:
                        record['dst_bytes'] = random.randint(0, 1000)  # Low response
                    if 'duration' in record:
                        record['duration'] = random.uniform(0.1, 1.0)  # Short bursts
                    if 'count' in record:
                        record['count'] = random.randint(200, 2000)  # High packet count
                    if 'protocol_type' in record:
                        record['protocol_type'] = 'udp'
                    if 'service' in record:
                        record['service'] = 'dns'
                    
                elif attack_type == 'http_flood':
                    # HTTP flood characteristics using model features
                    if 'src_bytes' in record:
                        record['src_bytes'] = random.randint(20000, 100000)  # HTTP request size
                    if 'dst_bytes' in record:
                        record['dst_bytes'] = random.randint(5000, 50000)  # HTTP response size
                    if 'duration' in record:
                        record['duration'] = random.uniform(0.1, 2.0)  # HTTP session duration
                    if 'count' in record:
                        record['count'] = random.randint(100, 1000)  # High request rate
                    if 'protocol_type' in record:
                        record['protocol_type'] = 'tcp'
                    if 'service' in record:
                        record['service'] = 'http'
                    if 'flag' in record:
                        record['flag'] = 'SF'  # Successful connections
                
                # Add some noise to make it more realistic
                for key in ['src_bytes', 'dst_bytes', 'count', 'srv_count']:
                    if key in record:
                        record[key] = int(record[key] * random.uniform(0.8, 1.2))
            
            logger.info(f"✅ Injected attack patterns into {num_attack_records}/{len(network_data)} records")
            return network_data
            
        except Exception as e:
            logger.error(f"Error injecting attack patterns: {e}")
            return network_data
    
    def _monitor_mininet_process(self, duration):
        """Monitor Mininet process and handle completion"""
        try:
            # Wait for process to complete or timeout
            self.mininet_process.wait(timeout=duration + 30)
            
            # Process completed naturally
            self.mininet_active = False
            self.mininet_process = None
            
            logger.info("Mininet simulation completed")
            
            # Emit completion event via WebSocket
            socketio.emit('mininet_simulation_completed', {
                'mode': self.mininet_mode,
                'simulation': self.current_simulation,
                'duration': duration
            })
            
        except subprocess.TimeoutExpired:
            # Timeout reached, force stop
            logger.warning("Mininet simulation timed out, forcing stop")
            self.stop_mininet_simulation()
        except Exception as e:
            logger.error(f"Error monitoring Mininet process: {e}")
            self.mininet_active = False
            self.mininet_process = None
    
    def get_mininet_status(self):
        """Get current Mininet simulation status"""
        if not self.mininet_active:
            return {
                'active': False,
                'mode': None,
                'simulation': None,
                'duration': 0,
                'elapsed': 0
            }
        
        elapsed = 0
        if self.simulation_start_time:
            elapsed = (datetime.now() - self.simulation_start_time).total_seconds()
        
        return {
            'active': True,
            'mode': self.mininet_mode,
            'simulation': self.current_simulation,
            'duration': self.simulation_duration,
            'elapsed': int(elapsed),
            'remaining': max(0, self.simulation_duration - int(elapsed)),
            'pid': self.mininet_process.pid if self.mininet_process else None
        }
    
    def switch_network_mode(self, target_mode, attack_type=None):
        """Switch between normal and attack network modes"""
        try:
            # Stop current simulation if running
            if self.mininet_active:
                stop_result = self.stop_mininet_simulation()
                if not stop_result['success']:
                    return stop_result
                
                # Wait a moment for cleanup
                time.sleep(2)
            
            # Start new simulation
            if target_mode == 'normal':
                return self.start_mininet_simulation(mode='normal', duration=300)  # 5 minutes
            elif target_mode == 'attack':
                if not attack_type:
                    attack_type = 'syn_flood'  # Default attack
                return self.start_mininet_simulation(mode='attack', attack_type=attack_type, duration=120)  # 2 minutes
            else:
                return {'success': False, 'message': 'Invalid network mode'}
                
        except Exception as e:
            logger.error(f"Error switching network mode: {e}")
            return {'success': False, 'message': f'Failed to switch mode: {str(e)}'}

# Initialize dashboard API (model loading will happen in main())
dashboard_api = None

# CSV processor will be initialized in main() after dashboard_api is created
csv_processor = None

# Authentication endpoints
@app.route('/api/auth/check-mfa', methods=['POST'])
@limiter.limit("10 per minute")
def check_mfa_requirement():
    """Check if user requires MFA without authenticating"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        # Get user info without authentication
        user = mongodb_dal.get_user_by_username(username)
        if not user:
            # Don't reveal if user exists or not for security
            return jsonify({'mfa_required': False}), 200
        
        # Check if MFA is enabled for this user
        mfa_required = user.get('mfa_enabled', False) and user.get('mfa_secret')
        
        return jsonify({'mfa_required': bool(mfa_required)}), 200
        
    except Exception as e:
        print(f"Error checking MFA requirement: {e}")
        return jsonify({'error': 'Internal server error'}), 500

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
        print(f"Error disabling MFA: {e}")
        return jsonify({'error': 'MFA disable failed'}), 500

# Email OTP / Passwordless Login endpoints
@app.route('/api/auth/passwordless/request', methods=['POST'])
@limiter.limit("3 per minute")
def request_passwordless_login():
    """Request passwordless login via email OTP"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        success, message = auth_manager.request_passwordless_login(email)
        
        # Always return success to prevent email enumeration
        return jsonify({'message': 'If this email is registered, you will receive a login code'})
        
    except Exception as e:
        logger.error(f"Passwordless login request error: {e}")
        return jsonify({'error': 'Failed to process request'}), 500

@app.route('/api/auth/passwordless/verify', methods=['POST'])
@limiter.limit("5 per minute")
def verify_passwordless_login():
    """Verify email OTP and authenticate"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            return jsonify({'error': 'Email and OTP required'}), 400
        
        ip_address, user_agent = get_client_info()
        
        success, message, user_info = auth_manager.authenticate_with_email_otp(email, otp)
        
        if not success:
            log_login_failed(email, ip_address, user_agent, message)
            return jsonify({'error': message}), 401
        
        # Generate tokens
        access_token, refresh_token = auth_manager.generate_tokens(
            user_info['username'], 
            user_info['role']
        )
        
        log_login_success(user_info['username'], ip_address, user_agent)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_info,
            'expires_in': 28800
        })
        
    except Exception as e:
        logger.error(f"Passwordless verification error: {e}")
        return jsonify({'error': 'Verification failed'}), 500

# Email Verification endpoints
@app.route('/api/auth/email/verify', methods=['POST'])
@limiter.limit("5 per minute")
def verify_email():
    """Verify email address with OTP"""
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        
        if not email or not otp:
            return jsonify({'error': 'Email and OTP required'}), 400
        
        success, message = auth_manager.verify_email_with_otp(email, otp)
        
        if not success:
            return jsonify({'error': message}), 400
        
        return jsonify({'message': message})
        
    except Exception as e:
        logger.error(f"Email verification error: {e}")
        return jsonify({'error': 'Verification failed'}), 500

@app.route('/api/auth/email/resend', methods=['POST'])
@limiter.limit("3 per minute")
def resend_verification():
    """Resend email verification OTP"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email required'}), 400
        
        success, message = auth_manager.resend_verification_otp(email)
        
        # Always return success to prevent email enumeration
        return jsonify({'message': 'If this email is registered and unverified, you will receive a verification code'})
        
    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        return jsonify({'error': 'Failed to resend verification'}), 500

@app.route('/api/auth/email/status/<email>', methods=['GET'])
@limiter.limit("10 per minute")
def check_email_verification_status(email):
    """Check if email is verified (public endpoint for user convenience)"""
    try:
        user = auth_manager.dal.get_user_by_email(email)
        
        if not user:
            # Don't reveal if email exists
            return jsonify({'verified': False, 'exists': False})
        
        return jsonify({
            'verified': user.get('email_verified', False),
            'exists': True
        })
        
    except Exception as e:
        logger.error(f"Email status check error: {e}")
        return jsonify({'error': 'Failed to check status'}), 500

# Passkey / WebAuthn endpoints
@app.route('/api/auth/passkey/register/begin', methods=['POST'])
@token_required
def begin_passkey_registration():
    """Begin passkey registration"""
    try:
        username = request.current_user['username']
        success, options, state_id = auth_manager.begin_passkey_registration(username)
        
        if not success:
            return jsonify({'error': options}), 400
        
        return jsonify({
            'options': options,
            'state_id': state_id
        })
        
    except Exception as e:
        logger.error(f"Passkey registration begin error: {e}")
        return jsonify({'error': 'Failed to begin passkey registration'}), 500

@app.route('/api/auth/passkey/register/complete', methods=['POST'])
@token_required
def complete_passkey_registration():
    """Complete passkey registration"""
    try:
        data = request.get_json()
        state_id = data.get('state_id')
        credential = data.get('credential')
        
        if not state_id or not credential:
            return jsonify({'error': 'State ID and credential required'}), 400
        
        success, message = auth_manager.complete_passkey_registration(state_id, credential)
        
        if not success:
            return jsonify({'error': message}), 400
        
        username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        logger.info(f"Passkey registered for user {username} from {ip_address}")
        
        return jsonify({'message': message})
        
    except Exception as e:
        logger.error(f"Passkey registration complete error: {e}")
        return jsonify({'error': 'Failed to complete passkey registration'}), 500

@app.route('/api/auth/passkey/authenticate/begin', methods=['POST'])
@limiter.limit("10 per minute")
def begin_passkey_authentication():
    """Begin passkey authentication"""
    try:
        data = request.get_json()
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username required'}), 400
        
        success, result, state_id = auth_manager.begin_passkey_authentication(username)
        
        if not success:
            # result contains error message when success is False
            logger.warning(f"Passkey auth begin failed for {username}: {result}")
            return jsonify({'error': result}), 400
        
        # result contains options when success is True
        return jsonify({
            'options': result,
            'state_id': state_id
        })
        
    except Exception as e:
        logger.error(f"Passkey authentication begin error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to begin passkey authentication'}), 500

@app.route('/api/auth/passkey/authenticate/complete', methods=['POST'])
@limiter.limit("10 per minute")
def complete_passkey_authentication():
    """Complete passkey authentication"""
    try:
        data = request.get_json()
        state_id = data.get('state_id')
        credential = data.get('credential')
        
        if not state_id or not credential:
            return jsonify({'error': 'State ID and credential required'}), 400
        
        ip_address, user_agent = get_client_info()
        
        success, message, user_info = auth_manager.complete_passkey_authentication(state_id, credential)
        
        if not success:
            log_login_failed('passkey_auth', ip_address, user_agent, message)
            return jsonify({'error': message}), 401
        
        # Generate tokens
        access_token, refresh_token = auth_manager.generate_tokens(
            user_info['username'],
            user_info['role']
        )
        
        log_login_success(user_info['username'], ip_address, user_agent)
        
        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_info,
            'expires_in': 28800
        })
        
    except Exception as e:
        logger.error(f"Passkey authentication complete error: {e}")
        return jsonify({'error': 'Authentication failed'}), 500

@app.route('/api/auth/passkey/list', methods=['GET'])
@token_required
def list_passkeys():
    """List user's registered passkeys"""
    try:
        username = request.current_user['username']
        passkeys = auth_manager.list_passkeys(username)
        
        return jsonify({'passkeys': passkeys})
        
    except Exception as e:
        logger.error(f"List passkeys error: {e}")
        return jsonify({'error': 'Failed to list passkeys'}), 500

@app.route('/api/auth/passkey/<credential_id>', methods=['DELETE'])
@token_required
def delete_passkey(credential_id):
    """Delete a passkey"""
    try:
        username = request.current_user['username']
        success, message = auth_manager.delete_passkey(username, credential_id)
        
        if not success:
            return jsonify({'error': message}), 400
        
        ip_address, user_agent = get_client_info()
        logger.info(f"Passkey deleted for user {username} from {ip_address}")
        
        return jsonify({'message': message})
        
    except Exception as e:
        logger.error(f"Delete passkey error: {e}")
        return jsonify({'error': 'Failed to delete passkey'}), 500

# Authentication preferences endpoints
@app.route('/api/auth/preferences', methods=['GET'])
@token_required
def get_auth_preferences():
    """Get user's authentication preferences"""
    try:
        username = request.current_user['username']
        user = auth_manager.dal.get_user_by_username(username)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has passkeys
        passkeys = auth_manager.list_passkeys(username)
        has_passkeys = len(passkeys) > 0
        
        preferences = {
            'default_method': user.get('default_auth_method', 'password'),
            'email_otp_enabled': user.get('email_otp_enabled', False),
            'passkey_enabled': user.get('passkey_enabled', has_passkeys),
            'mfa_enabled': user.get('mfa_enabled', False),
            'email_verified': user.get('email_verified', False)
        }
        
        return jsonify(preferences)
        
    except Exception as e:
        logger.error(f"Get auth preferences error: {e}")
        return jsonify({'error': 'Failed to get preferences'}), 500

@app.route('/api/auth/preferences', methods=['PUT'])
@token_required
def update_auth_preferences():
    """Update user's authentication preferences"""
    try:
        username = request.current_user['username']
        data = request.get_json()
        
        # Allowed preference keys
        allowed_keys = ['default_method', 'email_otp_enabled', 'passkey_enabled']
        
        # Filter and validate updates
        updates = {}
        for key in allowed_keys:
            if key in data:
                value = data[key]
                
                # Validate default_method
                if key == 'default_method':
                    if value not in ['password', 'email_otp', 'passkey']:
                        return jsonify({'error': 'Invalid authentication method'}), 400
                
                updates[key] = value
        
        if not updates:
            return jsonify({'error': 'No valid preferences to update'}), 400
        
        # Update user preferences
        success = auth_manager.dal.update_user(username, updates)
        
        if not success:
            return jsonify({'error': 'Failed to update preferences'}), 500
        
        # Log the change
        ip_address, user_agent = get_client_info()
        logger.info(f"User {username} updated auth preferences from {ip_address}")
        
        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': updates
        })
        
    except Exception as e:
        logger.error(f"Update auth preferences error: {e}")
        return jsonify({'error': 'Failed to update preferences'}), 500

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
        
        # Send email verification OTP
        otp_success, otp_message = auth_manager.send_verification_otp(email, username)
        
        # Log user creation
        admin_username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        log_user_created(admin_username, username, ip_address, user_agent)
        
        return jsonify({
            'message': message,
            'verification_sent': otp_success,
            'verification_message': otp_message
        }), 201
        
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
        print(f"Error getting audit summary: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to get audit summary'}), 500

@app.route('/api/admin/audit/export', methods=['GET'])
@token_required
@admin_required
def export_audit_data():
    """Export audit data in various formats (admin only)"""
    try:
        # Initialize audit exporter
        exporter = AuditExporter(audit_logger)
        
        # Get export parameters
        format_type = request.args.get('format', 'json').lower()
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        event_type = request.args.get('event_type')
        username = request.args.get('username')
        severity = request.args.get('severity')
        include_summary = request.args.get('include_summary', 'true').lower() == 'true'
        
        # Validate format
        if format_type not in ['json', 'csv', 'pdf', 'excel']:
            return jsonify({'error': 'Invalid format. Supported formats: json, csv, pdf, excel'}), 400
        
        # Export data
        exported_data = exporter.export_audit_data(
            format_type=format_type,
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            username=username,
            severity=severity,
            include_summary=include_summary
        )
        
        # Generate filename
        filename = exporter.get_export_filename(format_type, start_date, end_date)
        
        # Log the export
        current_username = request.current_user['username']
        ip_address, user_agent = get_client_info()
        audit_logger.log_event(
            event_type='audit_export',
            username=current_username,
            details={
                'format': format_type,
                'start_date': start_date,
                'end_date': end_date,
                'event_type': event_type,
                'username_filter': username,
                'severity': severity,
                'filename': filename
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Return appropriate response based on format
        if format_type == 'json':
            return jsonify({
                'success': True,
                'data': json.loads(exported_data),
                'filename': filename
            })
        elif format_type == 'csv':
            return send_file(
                io.BytesIO(exported_data.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        elif format_type in ['pdf', 'excel']:
            mimetype = 'application/pdf' if format_type == 'pdf' else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            return send_file(
                io.BytesIO(exported_data),
                mimetype=mimetype,
                as_attachment=True,
                download_name=filename
            )
        
    except Exception as e:
        print(f"Error exporting audit data: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to export audit data'}), 500

@app.route('/api/admin/audit/export/formats', methods=['GET'])
@token_required
@admin_required
def get_export_formats():
    """Get available export formats (admin only)"""
    return jsonify({
        'formats': [
            {
                'value': 'json',
                'label': 'JSON',
                'description': 'Structured data format, includes full details',
                'mime_type': 'application/json'
            },
            {
                'value': 'csv',
                'label': 'CSV',
                'description': 'Comma-separated values, good for spreadsheets',
                'mime_type': 'text/csv'
            },
            {
                'value': 'excel',
                'label': 'Excel',
                'description': 'Microsoft Excel format with multiple sheets',
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            },
            {
                'value': 'pdf',
                'label': 'PDF',
                'description': 'Portable document format, good for reports',
                'mime_type': 'application/pdf'
            }
        ],
        'severity_levels': ['high', 'medium', 'low'],
        'event_types': [
            'login_success', 'login_failed', 'logout', 'token_refresh',
            'mfa_setup', 'mfa_enabled', 'mfa_disabled', 'mfa_failed',
            'user_created', 'user_updated', 'user_deleted', 'password_changed',
            'account_locked', 'account_unlocked', 'alert_flagged', 'alert_dismissed',
            'threshold_changed', 'monitoring_started', 'monitoring_stopped',
            'csv_upload', 'csv_analysis', 'csv_report_generated', 'csv_cleanup',
            'unauthorized_access', 'permission_denied', 'system_error'
        ]
    })

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
        print(f"Error getting security alerts: {e}")
        traceback.print_exc()
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

# Network topology endpoints
@app.route('/api/network/topology')
@token_required
@analyst_or_admin_required
def get_network_topology():
    """Get network topology data for visualization"""
    try:
        # Get recent alerts for network analysis
        alerts_data = mongodb_dal.get_alerts(per_page=500)
        alerts = alerts_data.get('alerts', [])
        
        # Build network topology from alerts
        nodes = {}
        edges = []
        subnets = {}
        
        for alert in alerts:
            src_ip = alert.get('source_ip')
            dst_ip = alert.get('destination_ip')
            
            if not src_ip or not dst_ip:
                continue
                
            # Classify IP addresses by subnet
            src_subnet = get_subnet(src_ip)
            dst_subnet = get_subnet(dst_ip)
            
            # Add nodes
            if src_ip not in nodes:
                nodes[src_ip] = {
                    'id': src_ip,
                    'ip': src_ip,
                    'subnet': src_subnet,
                    'type': classify_ip_type(src_ip),
                    'alert_count': 0,
                    'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'attack_types': set(),
                    'ports': set()
                }
            
            if dst_ip not in nodes:
                nodes[dst_ip] = {
                    'id': dst_ip,
                    'ip': dst_ip,
                    'subnet': dst_subnet,
                    'type': classify_ip_type(dst_ip),
                    'alert_count': 0,
                    'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                    'attack_types': set(),
                    'ports': set()
                }
            
            # Update node statistics
            severity = alert.get('severity', 'low').lower()
            attack_type = alert.get('attack_type', 'Unknown')
            
            nodes[src_ip]['alert_count'] += 1
            nodes[src_ip]['severity_counts'][severity] += 1
            nodes[src_ip]['attack_types'].add(attack_type)
            
            nodes[dst_ip]['alert_count'] += 1
            nodes[dst_ip]['severity_counts'][severity] += 1
            nodes[dst_ip]['attack_types'].add(attack_type)
            
            # Add ports if available
            if alert.get('source_port'):
                nodes[src_ip]['ports'].add(alert['source_port'])
            if alert.get('destination_port'):
                nodes[dst_ip]['ports'].add(alert['destination_port'])
            
            # Add edge
            edge_id = f"{src_ip}->{dst_ip}"
            edge_exists = False
            for edge in edges:
                if edge['id'] == edge_id:
                    edge['weight'] += 1
                    edge['alerts'].append({
                        'timestamp': alert.get('timestamp'),
                        'severity': severity,
                        'attack_type': attack_type,
                        'score': alert.get('anomaly_score', 0)
                    })
                    edge_exists = True
                    break
            
            if not edge_exists:
                edges.append({
                    'id': edge_id,
                    'source': src_ip,
                    'target': dst_ip,
                    'weight': 1,
                    'alerts': [{
                        'timestamp': alert.get('timestamp'),
                        'severity': severity,
                        'attack_type': attack_type,
                        'score': alert.get('anomaly_score', 0)
                    }]
                })
            
            # Track subnets
            if src_subnet not in subnets:
                subnets[src_subnet] = {'ips': set(), 'alert_count': 0}
            if dst_subnet not in subnets:
                subnets[dst_subnet] = {'ips': set(), 'alert_count': 0}
            
            subnets[src_subnet]['ips'].add(src_ip)
            subnets[dst_subnet]['ips'].add(dst_ip)
            subnets[src_subnet]['alert_count'] += 1
            subnets[dst_subnet]['alert_count'] += 1
        
        # Convert sets to lists for JSON serialization
        for node in nodes.values():
            node['attack_types'] = list(node['attack_types'])
            node['ports'] = list(node['ports'])
        
        # Convert subnet data
        subnet_data = []
        for subnet, data in subnets.items():
            subnet_data.append({
                'subnet': subnet,
                'ip_count': len(data['ips']),
                'alert_count': data['alert_count'],
                'ips': list(data['ips'])
            })
        
        return jsonify({
            'nodes': list(nodes.values()),
            'edges': edges,
            'subnets': subnet_data,
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'total_subnets': len(subnets)
            }
        })
        
    except Exception as e:
        print(f"Error getting network topology: {e}")
        return jsonify({'error': 'Failed to get network topology'}), 500

@app.route('/api/network/mininet-topology')
@token_required
@analyst_or_admin_required
def get_mininet_topology():
    """Get Mininet network topology structure"""
    try:
        import json
        import os
        
        # Path to the topology file
        topology_file = os.path.join(
            os.path.dirname(__file__),
            '../../mininet_data_generation/data_capture/mininet_topology.json'
        )
        
        # Check if topology file exists
        if not os.path.exists(topology_file):
            # Return empty topology if file doesn't exist
            return jsonify({
                'available': False,
                'message': 'Mininet topology not yet generated. Run topology_exporter.py first.'
            })
        
        # Load topology from file
        with open(topology_file, 'r') as f:
            topology = json.load(f)
        
        # Enrich topology with alert data
        alerts_data = mongodb_dal.get_alerts(per_page=500)
        alerts = alerts_data.get('alerts', [])
        
        # Create IP to alert mapping
        ip_alerts = {}
        for alert in alerts:
            for ip_field in ['source_ip', 'destination_ip']:
                ip = alert.get(ip_field)
                if ip:
                    if ip not in ip_alerts:
                        ip_alerts[ip] = {
                            'count': 0,
                            'severity_counts': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0},
                            'attack_types': set()
                        }
                    ip_alerts[ip]['count'] += 1
                    severity = alert.get('severity', 'low').lower()
                    ip_alerts[ip]['severity_counts'][severity] += 1
                    ip_alerts[ip]['attack_types'].add(alert.get('attack_type', 'Unknown'))
        
        # Enrich hosts with alert data
        for host in topology.get('hosts', []):
            ip = host.get('ip')
            if ip in ip_alerts:
                host['alert_count'] = ip_alerts[ip]['count']
                host['severity_counts'] = ip_alerts[ip]['severity_counts']
                host['attack_types'] = list(ip_alerts[ip]['attack_types'])
            else:
                host['alert_count'] = 0
                host['severity_counts'] = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
                host['attack_types'] = []
        
        topology['available'] = True
        return jsonify(topology)
        
    except Exception as e:
        print(f"Error getting Mininet topology: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to get Mininet topology', 'available': False}), 500

def get_subnet(ip):
    """Get subnet classification for IP address"""
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return 'unknown'
        
        first_octet = int(parts[0])
        second_octet = int(parts[1])
        
        if first_octet == 192 and second_octet == 168:
            return f"192.168.{parts[2]}.0/24"
        elif first_octet == 10:
            return f"10.{parts[1]}.0.0/16"
        elif first_octet == 172 and 16 <= second_octet <= 31:
            return f"172.{parts[1]}.0.0/16"
        elif first_octet in [127]:
            return "localhost"
        else:
            return f"{parts[0]}.{parts[1]}.0.0/16"
    except:
        return 'unknown'

def classify_ip_type(ip):
    """Classify IP address type"""
    try:
        parts = ip.split('.')
        if len(parts) != 4:
            return 'unknown'
        
        first_octet = int(parts[0])
        second_octet = int(parts[1])
        
        if first_octet == 192 and second_octet == 168:
            return 'internal'
        elif first_octet == 10:
            return 'internal'
        elif first_octet == 172 and 16 <= second_octet <= 31:
            return 'internal'
        elif first_octet == 127:
            return 'localhost'
        else:
            return 'external'
    except:
        return 'unknown'

@app.route('/api/network/connections')
@token_required
@analyst_or_admin_required
def get_network_connections():
    """Get active network connections"""
    try:
        time_filter = request.args.get('timeframe', '1h')
        
        # Calculate time threshold
        now = datetime.utcnow()
        if time_filter == '1h':
            threshold = now - timedelta(hours=1)
        elif time_filter == '24h':
            threshold = now - timedelta(hours=24)
        elif time_filter == '7d':
            threshold = now - timedelta(days=7)
        else:
            threshold = now - timedelta(hours=1)
        
        # Get recent alerts
        alerts_data = mongodb_dal.get_alerts(per_page=1000)
        alerts = alerts_data.get('alerts', [])
        recent_alerts = [a for a in alerts if a.get('timestamp', now) >= threshold]
        
        # Analyze connections
        connections = {}
        for alert in recent_alerts:
            src_ip = alert.get('source_ip')
            dst_ip = alert.get('destination_ip')
            src_port = alert.get('source_port', 0)
            dst_port = alert.get('destination_port', 0)
            
            if not src_ip or not dst_ip:
                continue
            
            conn_key = f"{src_ip}:{src_port}->{dst_ip}:{dst_port}"
            
            if conn_key not in connections:
                connections[conn_key] = {
                    'source_ip': src_ip,
                    'destination_ip': dst_ip,
                    'source_port': src_port,
                    'destination_port': dst_port,
                    'connection_count': 0,
                    'total_score': 0,
                    'max_score': 0,
                    'attack_types': set(),
                    'severities': set(),
                    'first_seen': alert.get('timestamp'),
                    'last_seen': alert.get('timestamp')
                }
            
            conn = connections[conn_key]
            conn['connection_count'] += 1
            conn['total_score'] += alert.get('anomaly_score', 0)
            conn['max_score'] = max(conn['max_score'], alert.get('anomaly_score', 0))
            conn['attack_types'].add(alert.get('attack_type', 'Unknown'))
            conn['severities'].add(alert.get('severity', 'low'))
            
            # Update timestamps
            alert_time = alert.get('timestamp')
            if alert_time:
                if conn['first_seen'] is None or alert_time < conn['first_seen']:
                    conn['first_seen'] = alert_time
                if conn['last_seen'] is None or alert_time > conn['last_seen']:
                    conn['last_seen'] = alert_time
        
        # Convert to list and calculate averages
        connection_list = []
        for conn in connections.values():
            conn['avg_score'] = conn['total_score'] / conn['connection_count'] if conn['connection_count'] > 0 else 0
            conn['attack_types'] = list(conn['attack_types'])
            conn['severities'] = list(conn['severities'])
            connection_list.append(conn)
        
        # Sort by connection count and score
        connection_list.sort(key=lambda x: (x['connection_count'], x['max_score']), reverse=True)
        
        return jsonify({
            'connections': connection_list[:100],  # Limit to top 100
            'timeframe': time_filter,
            'total_connections': len(connection_list)
        })
        
    except Exception as e:
        print(f"Error getting network connections: {e}")
        return jsonify({'error': 'Failed to get network connections'}), 500

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

@app.route('/api/alerts/<alert_id>/flag', methods=['POST'])
@token_required
@analyst_or_admin_required
def flag_alert(alert_id):
    """Flag an alert in MongoDB"""
    try:
        username = request.current_user['username']
        
        # Convert alert_id to integer if it's a string
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return jsonify({'error': 'Invalid alert ID format'}), 400
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id_int,
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
                details={'alert_id': alert_id_int, 'action': 'flagged'}
            )
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error flagging alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to flag alert'}), 500

@app.route('/api/alerts/<alert_id>/dismiss', methods=['POST'])
@token_required
@analyst_or_admin_required
def dismiss_alert(alert_id):
    """Dismiss an alert in MongoDB"""
    try:
        print(f"DEBUG: dismiss_alert called with alert_id: {alert_id}")
        print(f"DEBUG: request.headers: {dict(request.headers)}")
        print(f"DEBUG: request.current_user: {getattr(request, 'current_user', 'NOT SET')}")
        username = request.current_user['username']
        
        # Handle both integer and ObjectId formats
        try:
            # Try integer first (for backward compatibility)
            alert_id_int = int(alert_id)
            print(f"DEBUG: Using integer alert_id: {alert_id_int}")
        except ValueError:
            # If not integer, use as string (ObjectId)
            alert_id_int = alert_id
            print(f"DEBUG: Using ObjectId alert_id: {alert_id_int}")
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id_int,
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
                details={'alert_id': alert_id_int, 'action': 'dismissed'}
            )
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error dismissing alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to dismiss alert'}), 500

# Enhanced Triage Actions
@app.route('/api/alerts/<alert_id>/escalate', methods=['POST'])
@token_required
@analyst_or_admin_required
def escalate_alert(alert_id):
    """Escalate an alert to higher-level analysts"""
    try:
        username = request.current_user['username']
        data = request.get_json() or {}
        
        # Convert alert_id to integer if it's a string
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return jsonify({'error': 'Invalid alert ID format'}), 400
        
        escalation_reason = data.get('reason', 'No reason provided')
        escalated_to = data.get('escalated_to', 'Senior Analyst')
        priority_increase = data.get('priority_increase', True)
        
        # Get current alert to determine new severity
        if isinstance(alert_id_int, str) and len(alert_id_int) == 24:
            try:
                current_alert = dashboard_api.dal.db.alerts.find_one({'_id': ObjectId(alert_id_int)})
            except:
                current_alert = dashboard_api.dal.db.alerts.find_one({'alert_id': alert_id_int})
        else:
            current_alert = dashboard_api.dal.db.alerts.find_one({'alert_id': alert_id_int})
        if not current_alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        # Increase severity if requested
        new_severity = current_alert.get('severity', 'medium')
        if priority_increase:
            severity_map = {'low': 'medium', 'medium': 'high', 'high': 'critical'}
            new_severity = severity_map.get(new_severity, new_severity)
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id_int,
            updates={
                'status': 'escalated',
                'escalated': True,
                'escalated_by': username,
                'escalated_to': escalated_to,
                'escalation_reason': escalation_reason,
                'escalation_timestamp': datetime.now(),
                'severity': new_severity
            },
            updated_by=username
        )
        
        if success:
            # Log the action
            dashboard_api.dal.create_audit_log(
                event_type='alert_escalated',
                username=username,
                ip_address=get_client_info()[0],
                action="escalate_alert",
                success=True,
                details={
                    'alert_id': alert_id_int, 
                    'escalated_to': escalated_to,
                    'reason': escalation_reason,
                    'new_severity': new_severity
                }
            )
            
            # Send real-time notification
            socketio.emit('triage_update', {
                'type': 'escalation',
                'alert_id': alert_id_int,
                'action': 'escalated',
                'performed_by': username,
                'escalated_to': escalated_to,
                'new_severity': new_severity,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'success': True, 'new_severity': new_severity})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error escalating alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to escalate alert'}), 500

@app.route('/api/alerts/<alert_id>/assign', methods=['POST'])
@token_required
@analyst_or_admin_required
def assign_alert(alert_id):
    """Assign an alert to a specific analyst"""
    try:
        username = request.current_user['username']
        data = request.get_json() or {}
        
        # Convert alert_id to integer if it's a string
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return jsonify({'error': 'Invalid alert ID format'}), 400
        
        assigned_to = data.get('assigned_to')
        assignment_notes = data.get('notes', '')
        
        if not assigned_to:
            return jsonify({'error': 'assigned_to is required'}), 400
        
        # Verify the assigned user exists
        assigned_user = dashboard_api.dal.get_user_by_username(assigned_to)
        if not assigned_user:
            return jsonify({'error': 'Assigned user not found'}), 404
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id_int,
            updates={
                'status': 'assigned',
                'assigned_to': assigned_to,
                'assigned_by': username,
                'assignment_timestamp': datetime.now(),
                'assignment_notes': assignment_notes
            },
            updated_by=username
        )
        
        if success:
            # Log the action
            dashboard_api.dal.create_audit_log(
                event_type='alert_assigned',
                username=username,
                ip_address=get_client_info()[0],
                action="assign_alert",
                success=True,
                details={
                    'alert_id': alert_id_int,
                    'assigned_to': assigned_to,
                    'notes': assignment_notes
                }
            )
            
            # Send real-time notification
            socketio.emit('triage_update', {
                'type': 'assignment',
                'alert_id': alert_id_int,
                'action': 'assigned',
                'performed_by': username,
                'assigned_to': assigned_to,
                'notes': assignment_notes,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error assigning alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to assign alert'}), 500

@app.route('/api/alerts/<alert_id>/investigate', methods=['POST'])
@token_required
@analyst_or_admin_required
def start_investigation(alert_id):
    """Start investigation on an alert"""
    try:
        username = request.current_user['username']
        data = request.get_json() or {}
        
        # Convert alert_id to integer if it's a string
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return jsonify({'error': 'Invalid alert ID format'}), 400
        
        investigation_notes = data.get('notes', '')
        investigation_priority = data.get('priority', 'medium')
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id_int,
            updates={
                'status': 'investigating',
                'investigation_started': True,
                'investigator': username,
                'investigation_start_time': datetime.now(),
                'investigation_notes': investigation_notes,
                'investigation_priority': investigation_priority
            },
            updated_by=username
        )
        
        if success:
            # Log the action
            dashboard_api.dal.create_audit_log(
                event_type='investigation_started',
                username=username,
                ip_address=get_client_info()[0],
                action="start_investigation",
                success=True,
                details={
                    'alert_id': alert_id_int,
                    'priority': investigation_priority,
                    'notes': investigation_notes
                }
            )
            
            # Send real-time notification
            socketio.emit('triage_update', {
                'type': 'investigation',
                'alert_id': alert_id_int,
                'action': 'investigation_started',
                'performed_by': username,
                'investigator': username,
                'priority': investigation_priority,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error starting investigation for alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to start investigation'}), 500

@app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
@token_required
@analyst_or_admin_required
def resolve_alert(alert_id):
    """Resolve/close an alert with resolution details"""
    try:
        username = request.current_user['username']
        data = request.get_json() or {}
        
        # Convert alert_id to integer if it's a string
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return jsonify({'error': 'Invalid alert ID format'}), 400
        
        resolution_type = data.get('resolution_type', 'resolved')  # resolved, false_positive, duplicate
        resolution_notes = data.get('notes', '')
        resolution_action_taken = data.get('action_taken', '')
        
        if not resolution_notes:
            return jsonify({'error': 'Resolution notes are required'}), 400
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id_int,
            updates={
                'status': 'resolved',
                'resolved': True,
                'resolved_by': username,
                'resolution_timestamp': datetime.now(),
                'resolution_type': resolution_type,
                'resolution_notes': resolution_notes,
                'action_taken': resolution_action_taken
            },
            updated_by=username
        )
        
        if success:
            # Log the action
            dashboard_api.dal.create_audit_log(
                event_type='alert_resolved',
                username=username,
                ip_address=get_client_info()[0],
                action="resolve_alert",
                success=True,
                details={
                    'alert_id': alert_id_int,
                    'resolution_type': resolution_type,
                    'notes': resolution_notes,
                    'action_taken': resolution_action_taken
                }
            )
            
            # Send real-time notification
            socketio.emit('triage_update', {
                'type': 'resolution',
                'alert_id': alert_id_int,
                'action': 'resolved',
                'performed_by': username,
                'resolution_type': resolution_type,
                'action_taken': resolution_action_taken,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error resolving alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to resolve alert'}), 500

@app.route('/api/alerts/<alert_id>/update-investigation', methods=['POST'])
@token_required
@analyst_or_admin_required
def update_investigation(alert_id):
    """Update investigation progress and notes"""
    try:
        username = request.current_user['username']
        data = request.get_json() or {}
        
        # Convert alert_id to integer if it's a string
        try:
            alert_id_int = int(alert_id)
        except ValueError:
            return jsonify({'error': 'Invalid alert ID format'}), 400
        
        investigation_update = data.get('update', '')
        investigation_status = data.get('status', 'in_progress')  # in_progress, completed, blocked
        
        if not investigation_update:
            return jsonify({'error': 'Investigation update is required'}), 400
        
        # Get current investigation notes
        current_alert = dashboard_api.dal.db.alerts.find_one({'alert_id': alert_id_int})
        if not current_alert:
            return jsonify({'error': 'Alert not found'}), 404
        
        # Append to existing investigation notes
        existing_notes = current_alert.get('investigation_notes', '')
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        updated_notes = f"{existing_notes}\n\n[{timestamp_str}] {username}: {investigation_update}".strip()
        
        success, message = dashboard_api.dal.update_alert(
            alert_id=alert_id_int,
            updates={
                'investigation_notes': updated_notes,
                'investigation_status': investigation_status,
                'last_investigation_update': datetime.now()
            },
            updated_by=username
        )
        
        if success:
            # Log the action
            dashboard_api.dal.create_audit_log(
                event_type='investigation_updated',
                username=username,
                ip_address=get_client_info()[0],
                action="update_investigation",
                success=True,
                details={
                    'alert_id': alert_id_int,
                    'status': investigation_status,
                    'update': investigation_update
                }
            )
            
            # Send real-time notification
            socketio.emit('triage_update', {
                'type': 'investigation_update',
                'alert_id': alert_id_int,
                'action': 'investigation_updated',
                'performed_by': username,
                'status': investigation_status,
                'update': investigation_update,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({'success': True})
        else:
            return jsonify({'error': message}), 404
            
    except Exception as e:
        print(f"Error updating investigation for alert {alert_id}: {e}")
        return jsonify({'error': 'Failed to update investigation'}), 500

# Bulk triage operations
@app.route('/api/alerts/bulk-triage', methods=['POST'])
@token_required
@analyst_or_admin_required
def bulk_triage_alerts():
    """Perform bulk triage operations on multiple alerts"""
    try:
        print(f"DEBUG: bulk_triage_alerts called")
        print(f"DEBUG: request.headers: {dict(request.headers)}")
        print(f"DEBUG: request.current_user: {getattr(request, 'current_user', 'NOT SET')}")
        username = request.current_user['username']
        data = request.get_json() or {}
        print(f"DEBUG: request data: {data}")
        
        alert_ids = data.get('alert_ids', [])
        action = data.get('action')  # flag, dismiss, escalate, assign, resolve
        action_data = data.get('action_data', {})
        
        if not alert_ids or not action:
            return jsonify({'error': 'alert_ids and action are required'}), 400
        
        # Handle both integer and ObjectId formats for alert_ids
        processed_alert_ids = []
        for aid in alert_ids:
            try:
                # Try integer first (for backward compatibility)
                processed_alert_ids.append(int(aid))
            except ValueError:
                # If not integer, use as string (ObjectId)
                processed_alert_ids.append(aid)
        alert_ids = processed_alert_ids
        print(f"DEBUG: Processed alert_ids: {alert_ids}")
        
        results = {'success': [], 'failed': []}
        
        for alert_id in alert_ids:
            try:
                if action == 'flag':
                    success, message = dashboard_api.dal.update_alert(
                        alert_id=alert_id,
                        updates={'flagged': True, 'status': 'flagged'},
                        updated_by=username
                    )
                elif action == 'dismiss':
                    success, message = dashboard_api.dal.update_alert(
                        alert_id=alert_id,
                        updates={'dismissed': True, 'status': 'dismissed'},
                        updated_by=username
                    )
                elif action == 'assign':
                    assigned_to = action_data.get('assigned_to')
                    if not assigned_to:
                        results['failed'].append({'alert_id': alert_id, 'error': 'assigned_to required'})
                        continue
                    success, message = dashboard_api.dal.update_alert(
                        alert_id=alert_id,
                        updates={
                            'status': 'assigned',
                            'assigned_to': assigned_to,
                            'assigned_by': username,
                            'assignment_timestamp': datetime.now()
                        },
                        updated_by=username
                    )
                else:
                    results['failed'].append({'alert_id': alert_id, 'error': f'Unsupported action: {action}'})
                    continue
                
                if success:
                    results['success'].append(alert_id)
                    # Log the action
                    dashboard_api.dal.create_audit_log(
                        event_type=f'bulk_{action}',
                        username=username,
                        ip_address=get_client_info()[0],
                        action=f"bulk_{action}",
                        success=True,
                        details={'alert_id': alert_id, 'action': action}
                    )
                else:
                    results['failed'].append({'alert_id': alert_id, 'error': message})
                    
            except Exception as e:
                results['failed'].append({'alert_id': alert_id, 'error': str(e)})
        
        return jsonify({
            'success': True,
            'results': results,
            'total_processed': len(alert_ids),
            'successful': len(results['success']),
            'failed': len(results['failed'])
        })
        
    except Exception as e:
        print(f"Error in bulk triage operation: {e}")
        return jsonify({'error': 'Failed to perform bulk triage'}), 500

# Get available analysts for assignment
@app.route('/api/analysts', methods=['GET'])
@token_required
@analyst_or_admin_required
def get_analysts():
    """Get list of analysts available for alert assignment"""
    try:
        # Get all users with analyst or admin roles
        users = dashboard_api.dal.get_all_users()
        analysts = []
        
        for user in users:
            if user.get('role') in ['analyst', 'senior_analyst', 'soc_manager', 'super_admin']:
                analysts.append({
                    'username': user['username'],
                    'role': user['role'],
                    'full_name': user.get('full_name', user['username']),
                    'active': user.get('active', True)
                })
        
        return jsonify({'analysts': analysts})
        
    except Exception as e:
        print(f"Error getting analysts: {e}")
        return jsonify({'error': 'Failed to get analysts'}), 500

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
            # Convert ObjectId to string and set as id for frontend compatibility
            if '_id' in alert:
                alert['id'] = str(alert['_id'])
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
    from flask_socketio import disconnect
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

# Mininet Simulation API Endpoints
@app.route('/api/mininet/start', methods=['POST'])
@token_required
@admin_required
def start_mininet_simulation():
    """Start Mininet network simulation"""
    try:
        data = request.get_json()
        mode = data.get('mode', 'normal')  # 'normal' or 'attack'
        attack_type = data.get('attack_type')
        duration = data.get('duration', 120)
        
        result = dashboard_api.start_mininet_simulation(
            mode=mode,
            attack_type=attack_type,
            duration=duration
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error starting Mininet simulation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/mininet/stop', methods=['POST'])
@token_required
@admin_required
def stop_mininet_simulation():
    """Stop current Mininet simulation"""
    try:
        result = dashboard_api.stop_mininet_simulation()
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error stopping Mininet simulation: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/mininet/status')
@token_required
@analyst_or_admin_required
def get_mininet_status():
    """Get current Mininet simulation status"""
    try:
        status = dashboard_api.get_mininet_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting Mininet status: {e}")
        return jsonify({'error': 'Failed to get Mininet status'}), 500

@app.route('/api/mininet/switch-mode', methods=['POST'])
@token_required
@admin_required
def switch_network_mode():
    """Switch between normal and attack network modes"""
    try:
        data = request.get_json()
        target_mode = data.get('mode')  # 'normal' or 'attack'
        attack_type = data.get('attack_type')
        
        if not target_mode:
            return jsonify({'success': False, 'message': 'Mode is required'}), 400
        
        result = dashboard_api.switch_network_mode(
            target_mode=target_mode,
            attack_type=attack_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error switching network mode: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/mininet/attacks')
@token_required
@analyst_or_admin_required
def get_available_attacks():
    """Get list of available attack types"""
    try:
        attacks = dashboard_api.available_attacks
        return jsonify({
            'attacks': attacks,
            'descriptions': {
                'syn_flood': 'SYN Flood DDoS Attack - Overwhelms target with SYN packets',
                'port_scan': 'Port Scanning - Scans target for open ports',
                'udp_flood': 'UDP Flood Attack - Floods target with UDP packets',
                'icmp_flood': 'ICMP Flood Attack - Floods target with ICMP packets',
                'http_flood': 'HTTP Flood Attack - Overwhelms web server with HTTP requests',
                'dns_amplification': 'DNS Amplification Attack - Uses DNS servers to amplify attack traffic',
                'brute_force': 'Brute Force Attack - Attempts to crack passwords through repeated attempts',
                'slowloris': 'Slowloris Attack - Keeps connections open to exhaust server resources'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting available attacks: {e}")
        return jsonify({'error': 'Failed to get available attacks'}), 500

@app.route('/api/mininet/export-topology', methods=['POST'])
@token_required
@admin_required
def export_mininet_topology():
    """Export current Mininet topology to file"""
    try:
        import os
        import sys
        
        # Add topology directory to path
        topology_dir = os.path.join(
            os.path.dirname(__file__),
            '../../mininet_data_generation/topology'
        )
        sys.path.append(topology_dir)
        
        from topology_exporter import TopologyExporter
        
        exporter = TopologyExporter()
        output_file = exporter.export_topology()
        
        return jsonify({
            'success': True,
            'message': 'Topology exported successfully',
            'file': output_file
        })
        
    except Exception as e:
        logger.error(f"Error exporting topology: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/test/generate-alerts', methods=['POST'])
@token_required
@admin_required
def test_generate_alerts():
    """Test endpoint to manually generate alerts"""
    try:
        # Set simulation context
        dashboard_api.current_simulation = 'syn_flood'
        
        # Ensure monitoring is running
        if not dashboard_api.is_monitoring:
            dashboard_api.start_monitoring()
        
        # Generate test alerts
        dashboard_api._process_pcap_for_alerts('/fake/path/syn_flood.pcap')
        
        return jsonify({
            'success': True,
            'message': 'Test alerts generated successfully',
            'monitoring_active': dashboard_api.is_monitoring
        })
        
    except Exception as e:
        logger.error(f"Error generating test alerts: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/debug/status', methods=['GET'])
@token_required
@admin_required
def debug_status():
    """Debug endpoint to check system status"""
    try:
        return jsonify({
            'monitoring_active': dashboard_api.is_monitoring,
            'mininet_active': dashboard_api.mininet_active,
            'mininet_mode': dashboard_api.mininet_mode,
            'current_simulation': dashboard_api.current_simulation,
            'detector_loaded': dashboard_api.detector is not None,
            'dal_type': type(dashboard_api.dal).__name__
        })
        
    except Exception as e:
        logger.error(f"Error getting debug status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/debug/flush-db', methods=['POST'])
@token_required
@admin_required
def flush_database():
    """Flush all alerts from the database for clean testing"""
    try:
        from src.database.schemas import COLLECTIONS
        
        # Get current alert count
        current_stats = dashboard_api.get_system_stats()
        initial_count = current_stats.get('total_alerts', 0)
        
        # Delete all alerts from the alerts collection
        alerts_collection = COLLECTIONS["alerts"]
        result = dashboard_api.dal.db[alerts_collection].delete_many({})
        deleted_count = result.deleted_count
        
        logger.info(f"🗑️ Flushed database: Deleted {deleted_count} alerts from {alerts_collection}")
        
        # Emit stats update to refresh dashboard
        updated_stats = dashboard_api.get_system_stats()
        socketio.emit('stats_update', updated_stats)
        socketio.emit('alerts_cleared', {'count': deleted_count})
        
        return jsonify({
            'success': True,
            'message': f'Successfully deleted {deleted_count} alerts',
            'initial_count': initial_count,
            'deleted_count': deleted_count,
            'collection': alerts_collection
        })
        
    except Exception as e:
        logger.error(f"Error flushing database: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting SOC Dashboard Server")
    print("=" * 50)
    print("📍 Server will be available at: http://localhost:5000")
    print("👤 Default admin credentials:")
    print("   Username: admin")
    print("   Password: SecureAdmin123!")
    print("")
    print("🔧 Environment Variables (optional):")
    print("   FLASK_SECRET_KEY - Flask session secret")
    print("   JWT_SECRET_KEY - JWT token signing key")
    print("")
    
    logger.info("🚀 Initializing SOC Dashboard...")
    
    # Create dashboard API instance
    dashboard_api = SOCDashboardAPI()
    logger.info(f"✅ Dashboard API created, detector loaded: {dashboard_api.detector is not None}")
    
    # Create CSV processor with shared detector
    csv_processor = CSVProcessor(
        detector=dashboard_api.detector,  # Share the same detector instance
        upload_dir="src/dashboard/data/uploads",
        reports_dir="src/dashboard/data/reports"
    )
    logger.info("✅ CSV processor initialized")
    
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
    
    # Debug server startup environment
    import os
    logger.info(f"🔍 Server startup debug:")
    logger.info(f"   - Current working directory: {os.getcwd()}")
    logger.info(f"   - Models directory exists: {os.path.exists('models')}")
    logger.info(f"   - Model status: detector={dashboard_api.detector is not None}")
    
    if os.path.exists('models'):
        model_files = os.listdir('models')
        logger.info(f"   - Model files: {[f for f in model_files if f.endswith('.pkl')]}")
    
    # Start monitoring by default (only if model is available)
    if dashboard_api.detector:
        logger.info("🔄 Starting monitoring system...")
        dashboard_api.start_monitoring()
    else:
        logger.warning("⚠️ Model not available at startup, attempting to load...")
        try:
            dashboard_api.load_models()
            if dashboard_api.detector:
                logger.info("✅ Model loaded successfully, starting monitoring...")
                dashboard_api.start_monitoring()
            else:
                logger.error("❌ Model loading failed at startup")
        except Exception as e:
            logger.error(f"❌ Model loading error at startup: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    # Run the server
    logger.info("🌐 Starting Flask server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
