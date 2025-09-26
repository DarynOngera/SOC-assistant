# SOC Assistant - Intelligent Security Operations Center (AEGIS PRIME)

A comprehensive machine learning-powered Security Operations Center (SOC) assistant for real-time network anomaly detection and threat analysis.

## 🚀 Features

- **Real-time Anomaly Detection**: ML-powered network traffic analysis using Random Forest, XGBoost, and ensemble methods
- **Interactive Dashboard**: React-based web interface with live monitoring and real-time alerts
- **Alert Management**: Prioritization, flagging, dismissal, and severity classification
- **WebSocket Integration**: Live updates and notifications for real-time monitoring
- **RESTful API**: Complete API for integration with external systems and SIEM platforms
- **Scalable Architecture**: Modular design supporting both demo and production environments

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Running the Project](#running-the-project)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Contributing](#contributing)

## 📁 Project Structure

```
SOC-assistant/
├── src/                          # Core application code
│   ├── models/                   # ML model classes and training
│   │   ├── __init__.py
│   │   └── supervised_trainer.py # Main ML pipeline with prediction methods
│   ├── dashboard/                # Dashboard backend
│   │   ├── __init__.py
│   │   └── server.py            # Flask server with API endpoints & WebSocket
│   └── utils/                   # Shared utilities
│       ├── __init__.py
│       └── data_utils.py        # Data processing and validation utilities
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_dashboard.py       # Dashboard API tests
│   └── test_integration.py     # End-to-end integration tests
├── scripts/                     # Utility scripts
│   ├── start_dashboard.py      # Dashboard startup script (auto-setup)
│   └── train_models.py         # Model training script
├── frontend/                    # React dashboard UI
│   ├── src/                    # React components and logic
│   ├── public/                 # Static assets
│   └── package.json            # Node.js dependencies
├── data/                       # Training datasets (CSV files)
├── models/                     # Trained model artifacts (.pkl, .h5 files)
├── docs/                       # Documentation
│   └── API_DOCUMENTATION.md   # Complete API reference
├── requirements.txt            # Python dependencies
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🔧 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 14.0 or higher
- **npm**: 6.0 or higher (comes with Node.js)
- **MongoDB**: 4.4 or higher (for persistent data storage)
- **Memory**: At least 4GB RAM (8GB recommended for training)
- **Storage**: 2GB free space for dependencies and models

### Operating System Support
- ✅ Linux (Ubuntu 18.04+, CentOS 7+)
- ✅ macOS (10.14+)
- ✅ Windows 10/11 (with WSL recommended)

### Database Requirements
The SOC Assistant uses **MongoDB** for persistent data storage including:
- User accounts and authentication
- Security alerts and audit logs
- System statistics and performance metrics
- CSV upload tracking and model metadata

**Quick MongoDB Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install -y mongodb-org

# macOS (Homebrew)
brew install mongodb-community

# Start MongoDB service
sudo systemctl start mongod  # Linux
brew services start mongodb/brew/mongodb-community  # macOS
```

For detailed MongoDB setup instructions, see [MONGODB_SETUP.md](MONGODB_SETUP.md).

## 🛠️ Installation

### Step 1: Clone the Repository
```bash
git clone <repository-url>
cd SOC-assistant
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Note**: If you encounter numpy/pandas compatibility issues, run:
```bash
pip install --upgrade numpy pandas scikit-learn
```

### Step 4: Install Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 5: Verify Installation
```bash
# Test Python imports
python -c "from src.models.supervised_trainer import SupervisedSOCDetector; print('✓ Python setup complete')"

# Test Node.js setup
cd frontend && npm list react && cd ..
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Setup MongoDB and initialize the database
python scripts/setup_mongodb.py

# Start the complete SOC Assistant system
python scripts/start_dashboard.py
```

The setup process will:
1. Initialize MongoDB connection and create indexes
2. Migrate existing data from JSON files (if any)
3. Create default admin user and sample data
4. Install missing dependencies
5. Set up the React frontend
6. Start the Flask backend server
7. Launch the React development server
8. Open the dashboard in your browser

### Option 2: Manual Setup

#### 1. Setup MongoDB (First Time Only)
```bash
# Initialize MongoDB and run data migration
python scripts/setup_mongodb.py

# Or just check MongoDB health
python scripts/setup_mongodb.py --health-check-only
```

#### 2. Train Models (First Time Only)
```bash
python scripts/train_models.py
```

#### 3. Start Backend Server
```bash
python src/dashboard/server.py
```

#### 4. Start Frontend (New Terminal)
```bash
cd frontend
npm start
```

### 🌐 Access the Application
- **Dashboard UI**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **MongoDB Health**: http://localhost:5000/api/health/mongodb (admin only)
- **API Documentation**: See [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)

### 🔐 Default Login Credentials
- **Username**: `admin`
- **Password**: `SecureAdmin123!`
- **Role**: Super Admin (full system access)

## 🗄️ Database Navigation

The SOC Assistant uses MongoDB for persistent data storage. This section provides comprehensive guidance for navigating and managing the database.

### Database Structure

The system uses the `soc_assistant` database with the following collections:

#### Core Collections
- **`users`** - User accounts, authentication, and role management
- **`alerts`** - Security alerts and anomaly detections
- **`audit_logs`** - System audit trail and security events
- **`system_stats`** - Performance metrics and system statistics
- **`csv_uploads`** - CSV file upload tracking and metadata

### MongoDB Connection

#### Using MongoDB Shell
```bash
# Connect to local MongoDB instance
mongo soc_assistant

# Or with authentication
mongo mongodb://username:password@localhost:27017/soc_assistant
```

#### Using MongoDB Compass (GUI)
- **Connection String**: `mongodb://localhost:27017/soc_assistant`
- **Database**: `soc_assistant`

### Collection Schemas and Navigation

#### 1. Users Collection (`users`)
```javascript
// View all users
db.users.find().pretty()

// Find specific user
db.users.findOne({username: "admin"})

// Count users by role
db.users.aggregate([
  {$group: {_id: "$role", count: {$sum: 1}}}
])

// Find active users
db.users.find({active: true})

// Sample document structure:
{
  "_id": ObjectId("..."),
  "username": "admin",
  "email": "admin@soc.local",
  "password_hash": "$2b$12$...",
  "role": "super_admin",
  "active": true,
  "mfa_enabled": true,
  "mfa_secret": "...",
  "created_at": ISODate("2024-01-01T00:00:00Z"),
  "last_login": ISODate("2024-01-01T12:00:00Z"),
  "failed_login_attempts": 0,
  "account_locked_until": null
}
```

#### 2. Alerts Collection (`alerts`)
```javascript
// View recent alerts (last 24 hours)
db.alerts.find({
  timestamp: {$gte: new Date(Date.now() - 24*60*60*1000)}
}).sort({timestamp: -1})

// Find high severity alerts
db.alerts.find({severity: "high"}).sort({timestamp: -1})

// Count alerts by attack type
db.alerts.aggregate([
  {$group: {_id: "$attack_type", count: {$sum: 1}}}
])

// Find alerts by IP address
db.alerts.find({$or: [
  {source_ip: "192.168.1.100"},
  {destination_ip: "192.168.1.100"}
]})

// Sample document structure:
{
  "_id": ObjectId("..."),
  "alert_id": "alert_20240101_001",
  "timestamp": ISODate("2024-01-01T12:00:00Z"),
  "severity": "high",
  "status": "active",
  "source_ip": "192.168.1.100",
  "destination_ip": "10.0.0.50",
  "source_port": 443,
  "destination_port": 80,
  "protocol": "tcp",
  "attack_type": "SQL Injection",
  "anomaly_score": 0.95,
  "confidence": 0.87,
  "flagged": false,
  "dismissed": false,
  "description": "Suspicious SQL injection attempt detected"
}
```

#### 3. Audit Logs Collection (`audit_logs`)
```javascript
// View recent audit events
db.audit_logs.find().sort({timestamp: -1}).limit(50)

// Find login events
db.audit_logs.find({event_type: "login"})

// Find failed authentication attempts
db.audit_logs.find({
  event_type: "login",
  success: false
})

// Count events by user
db.audit_logs.aggregate([
  {$group: {_id: "$username", count: {$sum: 1}}}
])

// Sample document structure:
{
  "_id": ObjectId("..."),
  "timestamp": ISODate("2024-01-01T12:00:00Z"),
  "event_type": "login",
  "username": "admin",
  "ip_address": "192.168.1.10",
  "user_agent": "Mozilla/5.0...",
  "success": true,
  "details": {
    "mfa_used": true,
    "session_duration": 28800
  }
}
```

#### 4. System Stats Collection (`system_stats`)
```javascript
// View recent system metrics
db.system_stats.find().sort({timestamp: -1}).limit(10)

// Find CPU usage over time
db.system_stats.find({metric_type: "cpu_usage"})

// Average response times
db.system_stats.aggregate([
  {$match: {metric_type: "response_time"}},
  {$group: {_id: null, avg_response: {$avg: "$value"}}}
])

// Sample document structure:
{
  "_id": ObjectId("..."),
  "timestamp": ISODate("2024-01-01T12:00:00Z"),
  "metric_type": "system_performance",
  "value": 85.2,
  "unit": "percent",
  "details": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

#### 5. CSV Uploads Collection (`csv_uploads`)
```javascript
// View all CSV uploads
db.csv_uploads.find().sort({upload_timestamp: -1})

// Find uploads by user
db.csv_uploads.find({uploaded_by: "admin"})

// Find successful uploads
db.csv_uploads.find({status: "completed"})

// Sample document structure:
{
  "_id": ObjectId("..."),
  "upload_id": "upload_20240101_001",
  "filename": "network_data.csv",
  "uploaded_by": "admin",
  "upload_timestamp": ISODate("2024-01-01T12:00:00Z"),
  "file_size": 1048576,
  "row_count": 10000,
  "status": "completed",
  "processing_time": 45.2,
  "metadata": {
    "columns": ["timestamp", "source_ip", "dest_ip", "protocol"],
    "anomalies_detected": 150
  }
}
```

### Database Management Commands

#### Health Monitoring
```javascript
// Check database status
db.runCommand({dbStats: 1})

// Check collection sizes
db.stats()

// View indexes for a collection
db.alerts.getIndexes()

// Check index usage
db.alerts.aggregate([{$indexStats: {}}])
```

#### Data Maintenance
```javascript
// Clean up old alerts (older than 30 days)
db.alerts.deleteMany({
  timestamp: {$lt: new Date(Date.now() - 30*24*60*60*1000)}
})

// Archive old audit logs
db.audit_logs.aggregate([
  {$match: {timestamp: {$lt: new Date(Date.now() - 90*24*60*60*1000)}}},
  {$out: "audit_logs_archive"}
])

// Compact collections
db.runCommand({compact: "alerts"})
```

#### Performance Optimization
```javascript
// Analyze query performance
db.alerts.find({severity: "high"}).explain("executionStats")

// Create custom indexes
db.alerts.createIndex({
  "timestamp": -1,
  "severity": 1,
  "status": 1
})

// View slow operations
db.currentOp({"secs_running": {$gte: 5}})
```

### Python Database Access

#### Using the MongoDB DAL
```python
from src.database.mongodb_dal import MongoDBDAL

# Initialize DAL
dal = MongoDBDAL()

# Query users
users = dal.get_users(role="admin")

# Get recent alerts
alerts = dal.get_alerts(
    severity="high",
    limit=50,
    sort_by="timestamp"
)

# Create new alert
alert_data = {
    "severity": "medium",
    "source_ip": "192.168.1.100",
    "attack_type": "Port Scan",
    "anomaly_score": 0.75
}
dal.create_alert(alert_data)
```

#### Direct MongoDB Access
```python
from src.database.mongodb_config import get_mongodb_database

# Get database instance
db = get_mongodb_database()

# Query collections directly
alerts = db.alerts.find({"severity": "high"}).limit(10)
users = db.users.find({"active": True})

# Aggregation pipelines
pipeline = [
    {"$match": {"timestamp": {"$gte": datetime.now() - timedelta(days=1)}}},
    {"$group": {"_id": "$attack_type", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}}
]
result = db.alerts.aggregate(pipeline)
```

### Database Administration

#### Backup and Restore
```bash
# Create backup
mongodump --db soc_assistant --out /backup/mongodb/

# Restore from backup
mongorestore --db soc_assistant /backup/mongodb/soc_assistant/

# Export specific collection
mongoexport --db soc_assistant --collection alerts --out alerts.json

# Import collection
mongoimport --db soc_assistant --collection alerts --file alerts.json
```

#### User Management
```javascript
// Create database user
db.createUser({
  user: "soc_admin",
  pwd: "secure_password",
  roles: [
    {role: "readWrite", db: "soc_assistant"},
    {role: "dbAdmin", db: "soc_assistant"}
  ]
})

// Grant additional privileges
db.grantRolesToUser("soc_admin", [
  {role: "backup", db: "admin"}
])
```

#### Monitoring and Alerts
```javascript
// Set up profiling for slow queries
db.setProfilingLevel(2, {slowms: 100})

// View profiling data
db.system.profile.find().sort({ts: -1}).limit(5)

// Monitor real-time operations
db.currentOp()
```

### Troubleshooting Database Issues

#### Connection Problems
```bash
# Check MongoDB service status
sudo systemctl status mongod

# View MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Test connection
python -c "from src.database.mongodb_config import mongodb_health_check; print(mongodb_health_check())"
```

#### Performance Issues
```javascript
// Find slow queries
db.system.profile.find({millis: {$gt: 100}}).sort({ts: -1})

// Check index usage
db.alerts.find({severity: "high"}).hint({$natural: 1}).explain()

// Analyze collection statistics
db.alerts.stats()
```

#### Data Integrity
```javascript
// Validate collections
db.alerts.validate()
db.users.validate()

// Check for orphaned documents
db.alerts.find({user_id: {$exists: true}}).forEach(function(alert) {
  if (!db.users.findOne({_id: alert.user_id})) {
    print("Orphaned alert: " + alert._id);
  }
})
```

### API Integration for Database Operations

The SOC Assistant provides API endpoints for database operations:

```bash
# Health check
curl http://localhost:5000/api/health/mongodb

# Query alerts with filters
curl "http://localhost:5000/api/alerts?severity=high&limit=10"

# Get database statistics
curl http://localhost:5000/api/admin/database/stats
```

## 🔧 Detailed Setup

### Training Your Own Models

1. **Prepare Training Data**
   ```bash
   # Place your CSV files in the data/ directory
   # Supported formats:
   # - Network flow data with features like duration, packets, bytes
   # - Labels: 0 (normal) or 1 (anomaly)
   ```

2. **Configure Training Parameters**
   ```python
   # Edit src/models/supervised_trainer.py
   detector = SupervisedSOCDetector(random_state=42)
   
   # Adjust parameters:
   # - sample_size: Limit training data size
   # - model parameters: Random Forest, XGBoost settings
   # - feature selection: Number of top features to use
   ```

3. **Run Training**
   ```bash
   python scripts/train_models.py
   ```

4. **Monitor Training Progress**
   - Training logs will show progress
   - Model artifacts saved to `models/` directory
   - Evaluation plots generated automatically

### Dashboard Configuration

1. **Backend Settings** (`src/dashboard/server.py`)
   ```python
   # Adjust detection threshold
   self.threshold = 0.5  # Change anomaly detection threshold
   
   # Modify monitoring frequency
   time.sleep(2)  # Process every 2 seconds
   
   # Update batch size
   data_batch = self.generate_realistic_network_data(batch_size=5)
   ```

2. **Frontend Settings** (`frontend/src/`)
   - Modify dashboard layout and components
   - Adjust refresh rates and visualization settings
   - Customize alert display and filtering

## 🏃‍♂️ Running the Project

### Development Mode
```bash
# Terminal 1: Backend with auto-reload
cd SOC-assistant
source venv/bin/activate
python src/dashboard/server.py

# Terminal 2: Frontend with hot-reload
cd frontend
npm start
```

### Production Mode
```bash
# Build frontend for production
cd frontend
npm run build

# Start backend in production mode
cd ..
python src/dashboard/server.py --production
```

### Docker Setup (Optional)
```bash
# Build Docker image
docker build -t soc-assistant .

# Run container
docker run -p 3000:3000 -p 5000:5000 soc-assistant
```

## 📊 Usage Examples

### 1. Real-time Monitoring
```python
from src.models.supervised_trainer import SupervisedSOCDetector

# Load trained models
detector = SupervisedSOCDetector()
detector.load_models('models/')

# Process network traffic record
network_record = {
    'dur': 1.5,
    'proto': 'tcp',
    'spkts': 10,
    'dpkts': 8,
    'sbytes': 500,
    'dbytes': 300,
    # ... other features
}

result = detector.predict_single(network_record)
print(f"Anomaly Score: {result['anomaly_score']:.3f}")
print(f"Is Anomaly: {result['is_anomaly']}")
```

### 2. Batch Processing
```python
# Process multiple records
batch_records = [record1, record2, record3]
results = detector.predict_batch(batch_records)

for i, result in enumerate(results):
    print(f"Record {i+1}: Score={result['anomaly_score']:.3f}")
```

### 3. API Integration
```python
import requests

# Get current alerts
response = requests.get('http://localhost:5000/api/alerts?severity=high')
alerts = response.json()

# Update detection threshold
requests.post('http://localhost:5000/api/threshold', 
              json={'threshold': 0.7})

# Flag an alert
requests.post('http://localhost:5000/api/alerts/123/flag')
```

### 4. WebSocket Integration
```javascript
// Frontend WebSocket connection
const socket = io('http://localhost:5000');

socket.on('new_alerts', (data) => {
    console.log('New alerts:', data.alerts);
    updateDashboard(data.alerts);
});

socket.on('stats_update', (stats) => {
    console.log('System stats:', stats);
    updateMetrics(stats);
});
```

## 🧪 Testing

### Run All Tests
```bash
# Integration tests
python tests/test_integration.py

# Dashboard API tests
python tests/test_dashboard.py
```

### Individual Test Components
```bash
# Test model loading
python -c "from tests.test_integration import test_model_loading; test_model_loading()"

# Test prediction pipeline
python -c "from tests.test_integration import test_single_prediction; test_single_prediction()"

# Test dashboard integration
python -c "from tests.test_integration import test_dashboard_integration; test_dashboard_integration()"
```

### Performance Testing
```bash
# Load test the API
pip install locust
locust -f tests/load_test.py --host=http://localhost:5000
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Import Errors
```bash
# Error: ModuleNotFoundError: No module named 'src'
# Solution: Run from project root directory
cd /path/to/SOC-assistant
python scripts/start_dashboard.py
```

#### 2. Port Already in Use
```bash
# Error: Port 5000 already in use
# Solution: Kill existing process or use different port
lsof -ti:5000 | xargs kill -9
# Or modify port in src/dashboard/server.py
```

#### 3. Node.js/npm Issues
```bash
# Clear npm cache
npm cache clean --force
cd frontend
rm -rf node_modules package-lock.json
npm install
```

#### 4. Model Loading Errors
```bash
# Error: No model files found
# Solution: Train models first
python scripts/train_models.py

# Or check models directory
ls -la models/
```

#### 5. Memory Issues During Training
```bash
# Reduce sample size in training
# Edit scripts/train_models.py or src/models/supervised_trainer.py
sample_size = 10000  # Reduce from default 50000
```

### Debug Mode
```bash
# Enable debug logging
export FLASK_DEBUG=1
python src/dashboard/server.py

# Enable verbose model training
python scripts/train_models.py --verbose
```

### Log Files
```bash
# Check application logs
tail -f logs/dashboard.log
tail -f logs/training.log
```

## 📖 API Documentation

Complete API reference available at `docs/API_DOCUMENTATION.md`

### Key Endpoints
- `GET /api/alerts` - Retrieve alerts with filtering
- `GET /api/stats` - System statistics and metrics
- `POST /api/threshold` - Update detection threshold
- `POST /api/monitoring/start` - Start real-time monitoring
- `GET /api/score-distribution` - Anomaly score distribution

### WebSocket Events
- `new_alerts` - Real-time alert notifications
- `stats_update` - Live system statistics
- `connection_established` - Connection confirmation

## 👨‍💻 Development

### Setting Up Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/ tests/
flake8 src/ tests/
```

### Adding New Features
1. Create feature branch: `git checkout -b feature/new-feature`
2. Add tests in `tests/`
3. Update documentation
4. Run test suite: `python tests/test_integration.py`
5. Submit pull request

### Project Architecture
- **Backend**: Flask + SocketIO for real-time communication
- **Frontend**: React with modern hooks and state management
- **ML Pipeline**: Scikit-learn with custom preprocessing
- **Data Flow**: CSV → Preprocessing → Model Training → Real-time Prediction → Dashboard

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Ensure all tests pass: `python tests/test_integration.py`
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style
- Follow PEP 8 for Python code
- Use ESLint configuration for JavaScript/React
- Add docstrings for all functions and classes
- Include type hints where appropriate

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
1. **Documentation**: Check `docs/` directory
2. **Issues**: Search existing GitHub issues
3. **Tests**: Run test suite to verify setup
4. **Logs**: Check application logs for errors

### Reporting Issues
When reporting issues, please include:
- Operating system and version
- Python and Node.js versions
- Complete error messages and stack traces
- Steps to reproduce the issue
- Expected vs actual behavior

### Community
- GitHub Discussions for questions and ideas
- Issue tracker for bugs and feature requests
- Wiki for additional documentation and tutorials

## 🔮 Roadmap

### Current Version (v1.0)
- [x] Core ML pipeline with supervised learning
- [x] Real-time dashboard with WebSocket integration
- [x] REST API with comprehensive endpoints
- [x] Alert management and classification

### Upcoming Features (v1.1)
- [ ] Advanced NLP integration for threat intelligence
- [ ] Multi-tenant support with role-based access control
- [ ] Real-time data streaming integration (Kafka, Redis)
- [ ] Advanced visualization and reporting capabilities
- [ ] Mobile-responsive dashboard design

### Future Enhancements (v2.0)
- [ ] Integration with popular SIEM platforms
- [ ] Machine learning model versioning and A/B testing
- [ ] Automated model retraining and drift detection
- [ ] Advanced threat hunting capabilities
- [ ] Cloud deployment templates (AWS, Azure, GCP)

---

**Quick Commands Reference:**
```bash
# Setup and run (first time)
python scripts/setup_mongodb.py     # Initialize MongoDB
python scripts/train_models.py      # Train ML models
python scripts/start_dashboard.py   # Start complete system

# Development
source venv/bin/activate
python src/dashboard/server.py      # Backend
cd frontend && npm start            # Frontend

# MongoDB Management
python scripts/setup_mongodb.py --health-check-only  # Check MongoDB
python scripts/setup_mongodb.py --skip-migration     # Skip data migration

# Testing
python tests/test_integration.py           # Integration tests
python tests/test_mongodb_integration.py   # MongoDB tests
```
