# SOC Assistant - Intelligent Security Operations Center

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
- **Memory**: At least 4GB RAM (8GB recommended for training)
- **Storage**: 2GB free space for dependencies and models

### Operating System Support
- ✅ Linux (Ubuntu 18.04+, CentOS 7+)
- ✅ macOS (10.14+)
- ✅ Windows 10/11 (with WSL recommended)

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
# This script handles everything automatically
python scripts/start_dashboard.py
```

The script will:
1. Install missing dependencies
2. Set up the React frontend
3. Start the Flask backend server
4. Launch the React development server
5. Open the dashboard in your browser

### Option 2: Manual Setup

#### 1. Train Models (First Time Only)
```bash
python scripts/train_models.py
```

#### 2. Start Backend Server
```bash
python src/dashboard/server.py
```

#### 3. Start Frontend (New Terminal)
```bash
cd frontend
npm start
```

### 🌐 Access the Application
- **Dashboard UI**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api/docs (if available)

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
python scripts/train_models.py
python scripts/start_dashboard.py

# Development
source venv/bin/activate
python src/dashboard/server.py  # Backend
cd frontend && npm start        # Frontend

# Testing
python tests/test_integration.py
```
