# MongoDB Setup Guide for SOC Assistant

This guide provides comprehensive instructions for setting up MongoDB as the database backend for the SOC Assistant project.

## Prerequisites

### MongoDB Installation

#### Ubuntu/Debian
```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Update package database and install MongoDB
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB service
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### macOS (using Homebrew)
```bash
# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB service
brew services start mongodb/brew/mongodb-community
```

#### Windows
1. Download MongoDB Community Server from [MongoDB Download Center](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the setup wizard
3. MongoDB will start automatically as a Windows service

### Python Dependencies
```bash
# Install MongoDB Python drivers
pip install pymongo>=4.3.0 motor>=3.1.0
```

## Quick Setup

### Automated Setup
```bash
# Run the automated MongoDB setup script
python scripts/setup_mongodb.py

# For health check only
python scripts/setup_mongodb.py --health-check-only

# Skip data migration
python scripts/setup_mongodb.py --skip-migration
```

### Manual Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start MongoDB (if not already running)
sudo systemctl start mongod  # Linux
brew services start mongodb/brew/mongodb-community  # macOS

# 3. Initialize MongoDB for SOC Assistant
python -c "from src.database.mongodb_config import initialize_mongodb; initialize_mongodb()"

# 4. Run data migration
python -c "from src.database.migration_utils import migrate_existing_data; migrate_existing_data()"
```

## Configuration

### Environment Variables
Create a `.env` file in the project root with MongoDB configuration:

```bash
# MongoDB Connection Settings
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_DATABASE=soc_assistant
MONGODB_USERNAME=
MONGODB_PASSWORD=
MONGODB_AUTH_SOURCE=admin

# Connection Pool Settings
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=10
MONGODB_MAX_IDLE_TIME_MS=30000
MONGODB_SERVER_SELECTION_TIMEOUT_MS=5000

# Flask Settings
FLASK_SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

### MongoDB Authentication (Optional)
If you want to enable MongoDB authentication:

```bash
# Connect to MongoDB
mongo

# Switch to admin database
use admin

# Create admin user
db.createUser({
  user: "admin",
  pwd: "your-secure-password",
  roles: ["userAdminAnyDatabase", "dbAdminAnyDatabase", "readWriteAnyDatabase"]
})

# Create SOC Assistant database user
use soc_assistant
db.createUser({
  user: "soc_user",
  pwd: "soc-secure-password",
  roles: ["readWrite"]
})

# Exit MongoDB shell
exit
```

Update your `.env` file:
```bash
MONGODB_USERNAME=soc_user
MONGODB_PASSWORD=soc-secure-password
```

## Database Schema

The SOC Assistant uses the following MongoDB collections:

### Collections Overview
- **users**: User accounts, authentication, and profile information
- **alerts**: Security alerts with anomaly detection results
- **audit_logs**: System audit trail and security events
- **system_stats**: System performance and detection statistics
- **csv_uploads**: CSV file upload tracking and processing results
- **model_metadata**: ML model information and performance metrics
- **sessions**: User session management

### Key Indexes
The system automatically creates the following indexes for optimal performance:

```javascript
// Users collection
db.users.createIndex({ "username": 1 }, { unique: true })
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "role": 1 })
db.users.createIndex({ "active": 1 })

// Alerts collection
db.alerts.createIndex({ "timestamp": -1 })
db.alerts.createIndex({ "severity": 1 })
db.alerts.createIndex({ "status": 1 })
db.alerts.createIndex({ "source_ip": 1 })
db.alerts.createIndex({ "anomaly_score": -1 })
db.alerts.createIndex({ "timestamp": -1, "severity": 1 })

// Audit logs collection
db.audit_logs.createIndex({ "timestamp": -1 })
db.audit_logs.createIndex({ "event_type": 1 })
db.audit_logs.createIndex({ "username": 1 })
db.audit_logs.createIndex({ "timestamp": -1, "event_type": 1 })
```

## Data Migration

### Migrating from JSON Files
The system can automatically migrate existing data from JSON files:

```bash
# Migrate users from data/users.json
# Migrate audit logs from data/audit.json
python scripts/setup_mongodb.py
```

### Sample Data Creation
The setup script creates sample data for testing:
- Default admin user (admin/SecureAdmin123!)
- Sample analyst users
- Test alerts and system statistics

## Health Monitoring

### Health Check Endpoints
```bash
# MongoDB health status (admin only)
GET /api/health/mongodb

# Database statistics (admin only)
GET /api/health/database-stats
```

### Manual Health Check
```bash
# Check MongoDB connection and performance
python scripts/setup_mongodb.py --health-check-only
```

### Monitoring Commands
```bash
# Check MongoDB status
sudo systemctl status mongod

# View MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Connect to MongoDB shell
mongo soc_assistant

# Show database statistics
db.stats()

# Show collection statistics
db.alerts.stats()
```

## Performance Optimization

### Index Optimization
```javascript
// Check index usage
db.alerts.explain("executionStats").find({"severity": "high"})

// Create compound indexes for common queries
db.alerts.createIndex({"timestamp": -1, "severity": 1, "status": 1})
db.audit_logs.createIndex({"timestamp": -1, "username": 1})
```

### Connection Pool Tuning
Adjust connection pool settings in `.env`:
```bash
# For high-traffic environments
MONGODB_MAX_POOL_SIZE=200
MONGODB_MIN_POOL_SIZE=20

# For low-resource environments
MONGODB_MAX_POOL_SIZE=50
MONGODB_MIN_POOL_SIZE=5
```

## Backup and Maintenance

### Database Backup
```bash
# Create backup
mongodump --db soc_assistant --out /path/to/backup/

# Restore from backup
mongorestore --db soc_assistant /path/to/backup/soc_assistant/
```

### Data Cleanup
```bash
# Clean up old data (90+ days)
python -c "
from src.database.mongodb_dal import get_dal
dal = get_dal()
results = dal.cleanup_old_data(days=90)
print(f'Cleanup results: {results}')
"
```

### Index Maintenance
```bash
# Rebuild indexes
mongo soc_assistant --eval "db.runCommand({reIndex: 'alerts'})"

# Compact database
mongo soc_assistant --eval "db.runCommand({compact: 'alerts'})"
```

## Troubleshooting

### Common Issues

#### Connection Refused
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB if stopped
sudo systemctl start mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

#### Authentication Failed
```bash
# Verify credentials in .env file
# Check user permissions in MongoDB
mongo -u admin -p --authenticationDatabase admin
```

#### Slow Queries
```bash
# Enable profiling
mongo soc_assistant --eval "db.setProfilingLevel(2)"

# Check slow queries
mongo soc_assistant --eval "db.system.profile.find().limit(5).sort({ts:-1}).pretty()"
```

#### Memory Issues
```bash
# Check MongoDB memory usage
mongo --eval "db.serverStatus().mem"

# Adjust WiredTiger cache size in mongod.conf
storage:
  wiredTiger:
    engineConfig:
      cacheSizeGB: 2
```

### Error Messages

| Error | Solution |
|-------|----------|
| `ServerSelectionTimeoutError` | Check MongoDB is running and connection settings |
| `DuplicateKeyError` | User/email already exists, use different values |
| `ValidationError` | Check data format matches schema requirements |
| `WriteError` | Check user permissions and disk space |

## Testing

### Run MongoDB Integration Tests
```bash
# Run comprehensive MongoDB tests
python tests/test_mongodb_integration.py

# Run specific test class
python -m unittest tests.test_mongodb_integration.TestMongoDBDAL

# Run with verbose output
python tests/test_mongodb_integration.py -v
```

### Manual Testing
```bash
# Test database connection
python -c "
from src.database.mongodb_config import mongodb_health_check
print(mongodb_health_check())
"

# Test user creation
python -c "
from src.database.mongodb_dal import get_dal
dal = get_dal()
success, msg, user_id = dal.create_user('testuser', 'hashedpass', 'test@example.com', 'analyst')
print(f'User creation: {success}, {msg}')
"
```

## Production Deployment

### MongoDB Configuration
For production environments, configure MongoDB with:
- Authentication enabled
- SSL/TLS encryption
- Replica set for high availability
- Regular backups
- Monitoring and alerting

### Security Checklist
- [ ] Enable MongoDB authentication
- [ ] Configure SSL/TLS encryption
- [ ] Set up firewall rules
- [ ] Use strong passwords
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Monitor access logs

### Performance Checklist
- [ ] Optimize indexes for query patterns
- [ ] Configure appropriate connection pool sizes
- [ ] Set up monitoring and alerting
- [ ] Regular database maintenance
- [ ] Implement data retention policies
- [ ] Monitor disk space and memory usage

## Support

For additional help:
1. Check MongoDB documentation: https://docs.mongodb.com/
2. Review SOC Assistant logs in `src/dashboard/data/`
3. Run health checks and diagnostics
4. Check GitHub issues for known problems

## Migration from JSON Storage

If you're migrating from the previous JSON-based storage system:

1. **Backup existing data**: Copy your `data/` directory
2. **Run migration script**: `python scripts/setup_mongodb.py`
3. **Verify migration**: Check collection counts and sample data
4. **Update configuration**: Ensure MongoDB is configured in `.env`
5. **Test functionality**: Run integration tests and manual verification

The migration process preserves all existing users, audit logs, and system data while providing the scalability and features of MongoDB.
