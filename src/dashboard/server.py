#!/usr/bin/env python3
"""
SOC Dashboard Backend Server
Real-time anomaly detection API with WebSocket support
"""

import os
import json
import time
import threading
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import joblib
import glob
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.models.supervised_trainer import SupervisedSOCDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'soc-dashboard-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class SOCDashboardAPI:
    def __init__(self):
        self.detector = SupervisedSOCDetector()
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
        self.load_models()
        
    def load_models(self):
        """Load the latest trained models"""
        try:
            model_dir = 'models'
            if os.path.exists(model_dir):
                self.detector.load_models(model_dir)
                print("Models loaded successfully")
            else:
                print("No trained models found. Please train models first.")
        except Exception as e:
            print(f"Error loading models: {e}")
    
    def generate_mock_data(self, batch_size=10):
        """Generate mock network traffic data for demonstration (backward compatibility)"""
        np.random.seed(int(time.time()) % 1000)
        
        # Generate realistic network features
        data = []
        for i in range(batch_size):
            # Create mix of normal and anomalous traffic
            is_anomaly = np.random.random() < 0.15  # 15% anomaly rate
            
            if is_anomaly:
                # Anomalous traffic patterns
                record = {
                    'timestamp': datetime.now() - timedelta(seconds=i),
                    'src_ip': f"192.168.{int(np.random.randint(1,255))}.{int(np.random.randint(1,255))}",
                    'dst_ip': f"10.0.{int(np.random.randint(1,255))}.{int(np.random.randint(1,255))}",
                    'src_port': int(np.random.randint(1024, 65535)),
                    'dst_port': int(np.random.choice([22, 23, 80, 443, 3389, 1433])),
                    'proto': str(np.random.choice(['tcp', 'udp', 'icmp'])),
                    'flow_duration': float(np.random.exponential(1000)),
                    'total_fwd_packets': int(np.random.poisson(100)),
                    'total_backward_packets': int(np.random.poisson(50)),
                    'flow_bytes_s': float(np.random.exponential(10000)),
                    'flow_packets_s': float(np.random.exponential(100)),
                    'anomaly_score': float(np.random.uniform(0.7, 0.95)),
                    'prediction': int(1),
                    'confidence': float(np.random.uniform(0.8, 0.95)),
                    'attack_type': str(np.random.choice(['DDoS', 'Port Scan', 'Brute Force', 'SQL Injection', 'Malware']))
                }
            else:
                # Normal traffic patterns
                record = {
                    'timestamp': datetime.now() - timedelta(seconds=i),
                    'src_ip': f"192.168.{int(np.random.randint(1,255))}.{int(np.random.randint(1,255))}",
                    'dst_ip': f"10.0.{int(np.random.randint(1,255))}.{int(np.random.randint(1,255))}",
                    'src_port': int(np.random.randint(1024, 65535)),
                    'dst_port': int(np.random.choice([80, 443, 53, 25])),
                    'proto': str(np.random.choice(['tcp', 'udp'])),
                    'flow_duration': float(np.random.normal(500, 100)),
                    'total_fwd_packets': int(np.random.poisson(20)),
                    'total_backward_packets': int(np.random.poisson(15)),
                    'flow_bytes_s': float(np.random.normal(5000, 1000)),
                    'flow_packets_s': float(np.random.normal(50, 10)),
                    'anomaly_score': float(np.random.uniform(0.1, 0.4)),
                    'prediction': int(0),
                    'confidence': float(np.random.uniform(0.7, 0.9)),
                    'attack_type': 'Normal'
                }
            
            data.append(record)
        
        return data
    
    def process_alerts(self, data_batch):
        """Process new data and generate alerts"""
        new_alerts = []
        
        for record in data_batch:
            if record['anomaly_score'] > self.threshold and record['prediction'] == 1:
                alert = {
                    'id': int(len(self.alert_history) + len(new_alerts) + 1),
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

# REST API Endpoints
@app.route('/api/alerts')
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
def get_stats():
    """Get system statistics"""
    return jsonify(dashboard_api.get_system_stats())

@app.route('/api/threshold', methods=['GET', 'POST'])
def threshold_endpoint():
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
def flag_alert(alert_id):
    """Flag an alert"""
    for alert in dashboard_api.current_alerts:
        if alert['id'] == alert_id:
            alert['flagged'] = True
            alert['status'] = 'flagged'
            return jsonify({'success': True})
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/alerts/<int:alert_id>/dismiss', methods=['POST'])
def dismiss_alert(alert_id):
    """Dismiss an alert"""
    for alert in dashboard_api.current_alerts:
        if alert['id'] == alert_id:
            alert['dismissed'] = True
            alert['status'] = 'dismissed'
            return jsonify({'success': True})
    return jsonify({'error': 'Alert not found'}), 404

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start real-time monitoring"""
    dashboard_api.start_monitoring()
    return jsonify({'success': True, 'status': 'monitoring_started'})

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop real-time monitoring"""
    dashboard_api.stop_monitoring()
    return jsonify({'success': True, 'status': 'monitoring_stopped'})

@app.route('/api/score-distribution')
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

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connection_established', {'status': 'connected'})
    emit('stats_update', dashboard_api.get_system_stats())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('request_alerts')
def handle_request_alerts():
    """Send current alerts to client"""
    emit('alerts_update', {
        'alerts': dashboard_api.current_alerts[-20:],  # Last 20 alerts
        'stats': dashboard_api.get_system_stats()
    })

if __name__ == '__main__':
    print("Starting SOC Dashboard Server...")
    print("Dashboard will be available at http://localhost:5000")
    
    # Start monitoring by default
    dashboard_api.start_monitoring()
    
    # Run the server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
