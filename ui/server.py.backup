from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt
import json
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)

# Secret key to encode and decode JWT tokens
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Load user credentials from users.json
def load_users():
    try:
        with open('../auth/users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {"admin": "password123", "user1": "password456"}

users = load_users()

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user']
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid!'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username in users and users[username] == password:
        # Create a JWT token
        token = jwt.encode({
            'user': username,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'user': username})

    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/alerts', methods=['GET'])
@token_required
def get_alerts(current_user):
    # Sample alerts with anomaly scores and enhanced data
    sample_alerts = [
        {
            'id': 1,
            'timestamp': '2025-08-19 23:30:00',
            'alert': 'Suspicious login attempt from 192.168.1.100',
            'severity': 'High',
            'anomaly_score': 0.85,
            'source_ip': '192.168.1.100',
            'user': 'admin',
            'status': 'active'
        },
        {
            'id': 2,
            'timestamp': '2025-08-19 23:25:00',
            'alert': 'Malware detected on host server-01',
            'severity': 'Critical',
            'anomaly_score': 0.95,
            'source_ip': '10.0.1.50',
            'user': 'system',
            'status': 'active'
        },
        {
            'id': 3,
            'timestamp': '2025-08-19 23:20:00',
            'alert': 'Data exfiltration attempt from internal network',
            'severity': 'High',
            'anomaly_score': 0.78,
            'source_ip': '192.168.2.45',
            'user': 'john.doe',
            'status': 'active'
        },
        {
            'id': 4,
            'timestamp': '2025-08-19 23:15:00',
            'alert': 'Multiple failed login attempts for user "admin"',
            'severity': 'Medium',
            'anomaly_score': 0.65,
            'source_ip': '203.0.113.10',
            'user': 'admin',
            'status': 'active'
        },
        {
            'id': 5,
            'timestamp': '2025-08-19 23:10:00',
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

@app.route('/api/alerts/<int:alert_id>/action', methods=['POST'])
@token_required
def alert_action(current_user, alert_id):
    data = request.get_json()
    action = data.get('action')  # 'flag' or 'dismiss'
    
    # Log the action for future retraining
    log_entry = {
        'user': current_user,
        'alert_id': alert_id,
        'action': action,
        'timestamp': datetime.utcnow().isoformat()
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

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats(current_user):
    stats = {
        'total_alerts': 5,
        'high_severity': 3,
        'medium_severity': 1,
        'critical_severity': 1,
        'avg_anomaly_score': 0.81
    }
    return jsonify(stats)

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
