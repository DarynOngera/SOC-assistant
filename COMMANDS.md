# 🚀 Quick Command Reference

Essential commands for running SOC Assistant with monitoring infrastructure.

---

## 📦 Initial Setup

```bash
# Clone and navigate
git clone <repository-url>
cd SOC-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend && npm install && cd ..
```

---

## 🐳 Docker Monitoring Stack

### Start Monitoring Infrastructure
```bash
# Start Prometheus, Grafana, Node Exporter
cd infrastructure
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Stop Monitoring Infrastructure
```bash
cd infrastructure
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Restart Services
```bash
cd infrastructure

# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart prometheus
docker-compose restart grafana
```

### Update Configuration
```bash
# After editing prometheus.yml or alerts.yml
cd infrastructure
docker-compose restart prometheus

# Reload Prometheus config without restart
curl -X POST http://localhost:9090/-/reload
```

---

## 🖥️ Application Commands

### Start Backend Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start Flask server with monitoring
python src/dashboard/server.py

# Server runs on: http://localhost:5000
```

### Start Frontend Dashboard
```bash
# In new terminal
cd frontend
npm start

# Dashboard opens at: http://localhost:3000
```

### Start Both (Production)
```bash
# Terminal 1: Backend
source venv/bin/activate && python src/dashboard/server.py

# Terminal 2: Frontend
cd frontend && npm start

# Terminal 3: Monitoring (optional)
cd infrastructure && docker-compose up -d
```

---

## 📊 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Dashboard** | http://localhost:3000 | admin / SecureAdmin123! |
| **Backend API** | http://localhost:5000 | - |
| **Grafana** | http://localhost:3001 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Metrics** | http://localhost:5000/metrics | - |
| **Health Check** | http://localhost:5000/health | - |
| **API Documentation** | http://localhost:5000/api/docs | Swagger UI |

---

## 🔍 Monitoring Commands

### Check Metrics
```bash
# View Prometheus metrics
curl http://localhost:5000/metrics | head -20

# Check health endpoints
curl http://localhost:5000/health
curl http://localhost:5000/health/ready
curl http://localhost:5000/health/live

# Get system stats
curl http://localhost:5000/api/stats
```

### Prometheus Queries
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq

# Query metrics
curl 'http://localhost:9090/api/v1/query?query=http_requests_total'

# Query with time range
curl 'http://localhost:9090/api/v1/query_range?query=http_requests_total&start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&step=15s'
```

### Grafana Management
```bash
# Access Grafana
open http://localhost:3001

# Import dashboard
# 1. Login (admin/admin)
# 2. Go to Dashboards → Import
# 3. Upload: infrastructure/grafana/dashboards/soc-assistant-dashboard.json
# 4. Select Prometheus data source
# 5. Click Import
```

---

## 🗄️ MongoDB Commands

### Start MongoDB
```bash
# Ubuntu/Debian
sudo systemctl start mongod
sudo systemctl status mongod

# macOS
brew services start mongodb-community

# Check connection
mongo --eval "db.runCommand({ connectionStatus: 1 })"
```

### MongoDB Shell
```bash
# Connect to database
mongo soc_assistant

# Common queries
show collections
db.alerts.find().limit(5)
db.users.find()
db.alerts.countDocuments()
```

### Backup & Restore
```bash
# Backup database
mongodump --db soc_assistant --out /backup/$(date +%Y%m%d)

# Restore database
mongorestore --db soc_assistant /backup/20240101/soc_assistant

# Export collection
mongoexport --db soc_assistant --collection alerts --out alerts.json

# Import collection
mongoimport --db soc_assistant --collection alerts --file alerts.json
```

---

## 🧪 Testing Commands

### Run Tests
```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_dashboard.py
python tests/test_mongodb_integration.py

# Run with verbose output
python -m pytest tests/ -v
```

### Test API Endpoints
```bash
# Login and get token
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecureAdmin123!"}' \
  | jq -r '.access_token')

# Get alerts
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/api/alerts?limit=10"

# Get stats
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:5000/api/stats"
```

---

## 🔧 Troubleshooting Commands

### Check Running Processes
```bash
# Check if server is running
ps aux | grep "python.*server.py"
lsof -i :5000

# Check Docker containers
docker ps
docker-compose ps

# Check MongoDB
sudo systemctl status mongod
```

### Kill Processes
```bash
# Kill Flask server
pkill -f "python.*server.py"

# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Stop all Docker containers
docker stop $(docker ps -q)
```

### View Logs
```bash
# Application logs
tail -f logs/soc_assistant.log
tail -f logs/soc_assistant.error.log

# Docker logs
docker-compose logs -f prometheus
docker-compose logs -f grafana

# MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### Clean Up
```bash
# Remove Python cache
find . -type d -name "__pycache__" -exec rm -r {} +
find . -type f -name "*.pyc" -delete

# Clean npm cache
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install

# Clean Docker
docker system prune -a
docker volume prune
```

---

## 🎓 Training Commands

### Train ML Models
```bash
# Activate virtual environment
source venv/bin/activate

# Train network anomaly detection models
cd scripts2
python train_mininet_pcaps.py

# Train NLP classifier
cd ml_training/nlp
python train_from_real_alerts.py

# View training report
cat ML_TRAINING_REPORT.md
```

---

## 📈 Performance Monitoring

### System Resources
```bash
# CPU and memory usage
htop
top

# Disk usage
df -h
du -sh *

# Network connections
netstat -tuln | grep LISTEN
ss -tuln | grep LISTEN
```

### Application Metrics
```bash
# Request rate
curl -s http://localhost:5000/metrics | grep http_requests_total

# Alert generation rate
curl -s http://localhost:5000/metrics | grep alerts_generated_total

# System resource usage
curl -s http://localhost:5000/metrics | grep system_
```

---

## 🔄 Update & Maintenance

### Update Dependencies
```bash
# Python dependencies
pip install --upgrade -r requirements.txt

# Frontend dependencies
cd frontend
npm update
npm audit fix
```

### Git Operations
```bash
# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feature/new-feature

# Commit changes
git add .
git commit -m "Description of changes"
git push origin feature/new-feature
```

### Database Maintenance
```bash
# Compact MongoDB collections
mongo soc_assistant --eval "db.alerts.compact()"

# Rebuild indexes
mongo soc_assistant --eval "db.alerts.reIndex()"

# Clean old data (older than 30 days)
mongo soc_assistant --eval 'db.alerts.deleteMany({timestamp: {$lt: new Date(Date.now() - 30*24*60*60*1000)}})'
```

---

## 🚨 Emergency Commands

### Quick Restart Everything
```bash
# Stop everything
pkill -f "python.*server.py"
cd infrastructure && docker-compose down
sudo systemctl stop mongod

# Start everything
sudo systemctl start mongod
cd infrastructure && docker-compose up -d
source venv/bin/activate && python src/dashboard/server.py &
cd frontend && npm start
```

### Reset to Clean State
```bash
# WARNING: This deletes all data!

# Stop services
pkill -f "python.*server.py"
cd infrastructure && docker-compose down -v

# Clear MongoDB
mongo soc_assistant --eval "db.dropDatabase()"

# Clear logs
rm -rf logs/*

# Restart
sudo systemctl start mongod
cd infrastructure && docker-compose up -d
python src/dashboard/server.py
```

---

## 📚 Documentation

- **Full Monitoring Guide**: [MONITORING.md](MONITORING.md)
- **API Documentation**: [docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)
- **ML Training Report**: [ML_TRAINING_REPORT.md](ML_TRAINING_REPORT.md)
- **MongoDB Setup**: [docs/MONGODB_SETUP.md](docs/MONGODB_SETUP.md)
- **Main README**: [README.md](README.md)

---

## 💡 Pro Tips

```bash
# Create aliases for common commands
alias soc-start="source venv/bin/activate && python src/dashboard/server.py"
alias soc-monitor="cd infrastructure && docker-compose up -d && cd .."
alias soc-logs="tail -f logs/soc_assistant.log"
alias soc-metrics="curl http://localhost:5000/metrics | head -20"

# Add to ~/.bashrc or ~/.zshrc
echo 'alias soc-start="cd ~/projects/SOC-assistant && source venv/bin/activate && python src/dashboard/server.py"' >> ~/.bashrc
```

---

**Last Updated:** November 24, 2025  
**Version:** 1.0.0
