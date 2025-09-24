#!/usr/bin/env python3
"""
Comprehensive MongoDB Integration Tests
Tests all MongoDB components: configuration, DAL, schemas, migration, and authentication
"""

import unittest
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Test imports
from src.database.mongodb_config import MongoDBConfig, initialize_mongodb
from src.database.mongodb_dal import MongoDBDAL
from src.database.schemas import (
    DocumentBuilder, UserRole, AlertSeverity, AlertStatus, AuditEventType,
    validate_user_role, validate_alert_severity, validate_alert_status
)
from src.database.migration_utils import DataMigrator
from src.auth.mongodb_auth_utils import MongoDBAuthManager

class TestMongoDBConfig(unittest.TestCase):
    """Test MongoDB configuration and connection management"""
    
    def setUp(self):
        self.config = MongoDBConfig()
    
    def test_connection_string_without_auth(self):
        """Test connection string generation without authentication"""
        self.config.username = ""
        self.config.password = ""
        expected = f"mongodb://{self.config.host}:{self.config.port}/{self.config.database_name}"
        self.assertEqual(self.config.get_connection_string(), expected)
    
    def test_connection_string_with_auth(self):
        """Test connection string generation with authentication"""
        self.config.username = "testuser"
        self.config.password = "testpass"
        expected = f"mongodb://testuser:testpass@{self.config.host}:{self.config.port}/{self.config.database_name}?authSource={self.config.auth_source}"
        self.assertEqual(self.config.get_connection_string(), expected)
    
    def test_client_options(self):
        """Test MongoDB client options"""
        options = self.config.get_client_options()
        self.assertIn('maxPoolSize', options)
        self.assertIn('serverSelectionTimeoutMS', options)
        self.assertEqual(options['retryWrites'], True)
    
    @patch('src.database.mongodb_config.MongoClient')
    def test_health_check_success(self, mock_client):
        """Test successful health check"""
        # Mock successful connection
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.admin.command.return_value = {'ok': 1}
        
        # Mock server status
        mock_instance.admin.command.side_effect = [
            {'ok': 1},  # ping
            {'version': '5.0.0', 'uptime': 3600, 'connections': {'current': 10}}  # serverStatus
        ]
        
        # Mock database stats
        self.config._database = MagicMock()
        self.config._database.command.return_value = {
            'dataSize': 1024 * 1024,  # 1MB
            'collections': 5,
            'indexes': 10
        }
        
        health = self.config.health_check()
        self.assertEqual(health['status'], 'healthy')
        self.assertIn('ping_time_ms', health)
        self.assertIn('server_version', health)

class TestMongoDBSchemas(unittest.TestCase):
    """Test MongoDB schemas and document builders"""
    
    def test_user_role_validation(self):
        """Test user role validation"""
        self.assertTrue(validate_user_role(UserRole.ADMIN.value))
        self.assertTrue(validate_user_role(UserRole.ANALYST.value))
        self.assertFalse(validate_user_role('invalid_role'))
    
    def test_alert_severity_validation(self):
        """Test alert severity validation"""
        self.assertTrue(validate_alert_severity(AlertSeverity.CRITICAL.value))
        self.assertTrue(validate_alert_severity(AlertSeverity.HIGH.value))
        self.assertFalse(validate_alert_severity('invalid_severity'))
    
    def test_alert_status_validation(self):
        """Test alert status validation"""
        self.assertTrue(validate_alert_status(AlertStatus.NEW.value))
        self.assertTrue(validate_alert_status(AlertStatus.RESOLVED.value))
        self.assertFalse(validate_alert_status('invalid_status'))
    
    def test_build_user_document(self):
        """Test user document builder"""
        doc = DocumentBuilder.build_user_document(
            username="testuser",
            password_hash="hashed_password",
            email="test@example.com",
            role=UserRole.ANALYST.value,
            first_name="John",
            last_name="Doe"
        )
        
        self.assertEqual(doc['username'], "testuser")
        self.assertEqual(doc['email'], "test@example.com")
        self.assertEqual(doc['role'], UserRole.ANALYST.value)
        self.assertEqual(doc['profile']['first_name'], "John")
        self.assertIn('created_at', doc)
        self.assertIn('preferences', doc)
    
    def test_build_alert_document(self):
        """Test alert document builder"""
        timestamp = datetime.utcnow()
        doc = DocumentBuilder.build_alert_document(
            alert_id=1,
            timestamp=timestamp,
            severity=AlertSeverity.HIGH.value,
            source_ip="192.168.1.100",
            destination_ip="10.0.0.50",
            attack_type="Brute Force",
            anomaly_score=0.85,
            confidence=0.9
        )
        
        self.assertEqual(doc['alert_id'], 1)
        self.assertEqual(doc['severity'], AlertSeverity.HIGH.value)
        self.assertEqual(doc['source_ip'], "192.168.1.100")
        self.assertEqual(doc['anomaly_score'], 0.85)
        self.assertEqual(doc['status'], AlertStatus.NEW.value)
        self.assertIn('ml_metadata', doc)
        self.assertIn('investigation', doc)

class TestMongoDBDAL(unittest.TestCase):
    """Test MongoDB Data Access Layer"""
    
    def setUp(self):
        # Mock the database connection
        self.mock_db = MagicMock()
        with patch('src.database.mongodb_dal.get_mongodb_database', return_value=self.mock_db):
            self.dal = MongoDBDAL()
    
    def test_create_user_success(self):
        """Test successful user creation"""
        # Mock successful insert
        self.mock_db.__getitem__.return_value.insert_one.return_value.inserted_id = "mock_id"
        
        success, message, user_id = self.dal.create_user(
            username="testuser",
            password_hash="hashed_password",
            email="test@example.com",
            role=UserRole.ANALYST.value
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "User created successfully")
        self.assertEqual(user_id, "mock_id")
    
    def test_create_user_invalid_role(self):
        """Test user creation with invalid role"""
        success, message, user_id = self.dal.create_user(
            username="testuser",
            password_hash="hashed_password",
            email="test@example.com",
            role="invalid_role"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Invalid user role")
        self.assertIsNone(user_id)
    
    def test_get_user_by_username(self):
        """Test getting user by username"""
        mock_user = {'username': 'testuser', 'email': 'test@example.com'}
        self.mock_db.__getitem__.return_value.find_one.return_value = mock_user
        
        user = self.dal.get_user_by_username("testuser")
        self.assertEqual(user, mock_user)
    
    def test_create_alert_success(self):
        """Test successful alert creation"""
        # Mock last alert query
        self.mock_db.__getitem__.return_value.find_one.return_value = {'alert_id': 5}
        # Mock successful insert
        self.mock_db.__getitem__.return_value.insert_one.return_value.inserted_id = "mock_alert_id"
        
        alert_data = {
            'timestamp': datetime.utcnow(),
            'severity': AlertSeverity.HIGH.value,
            'source_ip': '192.168.1.100',
            'destination_ip': '10.0.0.50',
            'attack_type': 'Brute Force',
            'anomaly_score': 0.85
        }
        
        success, message, alert_id = self.dal.create_alert(alert_data)
        
        self.assertTrue(success)
        self.assertEqual(message, "Alert created successfully")
        self.assertEqual(alert_id, "mock_alert_id")
    
    def test_get_alerts_with_filters(self):
        """Test getting alerts with filters"""
        mock_alerts = [
            {'alert_id': 1, 'severity': 'high'},
            {'alert_id': 2, 'severity': 'medium'}
        ]
        
        # Mock count and find operations
        self.mock_db.__getitem__.return_value.count_documents.return_value = 2
        mock_cursor = MagicMock()
        mock_cursor.sort.return_value.skip.return_value.limit.return_value = mock_alerts
        self.mock_db.__getitem__.return_value.find.return_value = mock_cursor
        
        result = self.dal.get_alerts(
            filters={'severity': 'high'},
            page=1,
            per_page=10
        )
        
        self.assertEqual(result['total'], 2)
        self.assertEqual(len(result['alerts']), 2)
        self.assertEqual(result['page'], 1)
    
    def test_create_audit_log(self):
        """Test audit log creation"""
        self.mock_db.__getitem__.return_value.insert_one.return_value = MagicMock()
        
        success, message = self.dal.create_audit_log(
            event_type=AuditEventType.LOGIN_SUCCESS.value,
            username="testuser",
            ip_address="192.168.1.100",
            action="login",
            success=True
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Audit log created successfully")

class TestDataMigrator(unittest.TestCase):
    """Test data migration utilities"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.migrator = DataMigrator()
        # Mock the DAL
        self.migrator.dal = MagicMock()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_migrate_users_from_json(self):
        """Test user migration from JSON file"""
        # Create test JSON file
        users_data = {
            'testuser': {
                'password_hash': 'hashed_password',
                'email': 'test@example.com',
                'role': 'analyst',
                'created_at': '2023-01-01T00:00:00',
                'active': True,
                'mfa_enabled': False
            }
        }
        
        json_file = os.path.join(self.temp_dir, 'users.json')
        with open(json_file, 'w') as f:
            json.dump(users_data, f)
        
        # Mock DAL methods
        self.migrator.dal.get_user_by_username.return_value = None  # User doesn't exist
        self.migrator.dal.create_user.return_value = (True, "User created successfully", "mock_id")
        
        success, result = self.migrator.migrate_users_from_json(json_file)
        
        self.assertTrue(success)
        self.assertEqual(result['migrated'], 1)
        self.assertEqual(result['errors'], 0)
    
    def test_create_default_admin_user(self):
        """Test default admin user creation"""
        # Mock no existing users
        self.migrator.dal.get_all_users.return_value = []
        self.migrator.dal.create_user.return_value = (True, "User created successfully", "admin_id")
        
        success, message = self.migrator.create_default_admin_user()
        
        self.assertTrue(success)
        self.assertIn("Default admin user created", message)
    
    def test_migrate_sample_data(self):
        """Test sample data creation"""
        # Mock DAL methods
        self.migrator.dal.get_user_by_username.return_value = None
        self.migrator.dal.create_user.return_value = (True, "User created", "user_id")
        self.migrator.dal.create_alert.return_value = (True, "Alert created", "alert_id")
        self.migrator.dal.save_system_stats.return_value = (True, "Stats saved")
        
        success, results = self.migrator.migrate_sample_data()
        
        self.assertTrue(success)
        self.assertIn('sample_users', results)
        self.assertIn('sample_alerts', results)
        self.assertIn('system_stats', results)

class TestMongoDBAuthManager(unittest.TestCase):
    """Test MongoDB-based authentication manager"""
    
    def setUp(self):
        # Mock the DAL
        with patch('src.auth.mongodb_auth_utils.get_dal') as mock_get_dal:
            self.mock_dal = MagicMock()
            mock_get_dal.return_value = self.mock_dal
            self.auth_manager = MongoDBAuthManager()
    
    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = self.auth_manager.hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(self.auth_manager.verify_password(password, hashed))
    
    def test_validate_password_strength(self):
        """Test password strength validation"""
        # Valid password
        self.assertTrue(self.auth_manager._validate_password_strength("StrongPass123!"))
        
        # Invalid passwords
        self.assertFalse(self.auth_manager._validate_password_strength("weak"))  # Too short
        self.assertFalse(self.auth_manager._validate_password_strength("nouppercase123!"))  # No uppercase
        self.assertFalse(self.auth_manager._validate_password_strength("NOLOWERCASE123!"))  # No lowercase
        self.assertFalse(self.auth_manager._validate_password_strength("NoDigits!"))  # No digits
        self.assertFalse(self.auth_manager._validate_password_strength("NoSpecial123"))  # No special chars
    
    def test_create_user_success(self):
        """Test successful user creation"""
        self.mock_dal.create_user.return_value = (True, "User created successfully", "user_id")
        
        success, message = self.auth_manager.create_user(
            username="testuser",
            password="StrongPass123!",
            role=UserRole.ANALYST.value,
            email="test@example.com"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "User created successfully")
    
    def test_create_user_weak_password(self):
        """Test user creation with weak password"""
        success, message = self.auth_manager.create_user(
            username="testuser",
            password="weak",
            role=UserRole.ANALYST.value,
            email="test@example.com"
        )
        
        self.assertFalse(success)
        self.assertIn("Password must be at least 8 characters", message)
    
    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        mock_user = {
            'username': 'testuser',
            'password_hash': self.auth_manager.hash_password('testpass'),
            'role': UserRole.ANALYST.value,
            'email': 'test@example.com',
            'active': True,
            'mfa_enabled': False,
            'failed_attempts': 0,
            'locked_until': None
        }
        
        self.mock_dal.get_user_by_username.return_value = mock_user
        self.mock_dal.update_user.return_value = (True, "Updated")
        
        success, message, user_info = self.auth_manager.authenticate_user(
            username="testuser",
            password="testpass"
        )
        
        self.assertTrue(success)
        self.assertEqual(message, "Authentication successful")
        self.assertEqual(user_info['username'], 'testuser')
        self.assertEqual(user_info['role'], UserRole.ANALYST.value)
    
    def test_authenticate_user_invalid_password(self):
        """Test authentication with invalid password"""
        mock_user = {
            'username': 'testuser',
            'password_hash': self.auth_manager.hash_password('correctpass'),
            'role': UserRole.ANALYST.value,
            'active': True,
            'failed_attempts': 0,
            'locked_until': None
        }
        
        self.mock_dal.get_user_by_username.return_value = mock_user
        self.mock_dal.update_user.return_value = (True, "Updated")
        
        success, message, user_info = self.auth_manager.authenticate_user(
            username="testuser",
            password="wrongpass"
        )
        
        self.assertFalse(success)
        self.assertEqual(message, "Invalid credentials")
    
    def test_generate_and_verify_tokens(self):
        """Test JWT token generation and verification"""
        username = "testuser"
        role = UserRole.ANALYST.value
        
        access_token, refresh_token = self.auth_manager.generate_tokens(username, role)
        
        # Verify access token
        valid, payload = self.auth_manager.verify_token(access_token)
        self.assertTrue(valid)
        self.assertEqual(payload['username'], username)
        self.assertEqual(payload['role'], role)
        self.assertEqual(payload['type'], 'access')
        
        # Verify refresh token
        valid, payload = self.auth_manager.verify_token(refresh_token)
        self.assertTrue(valid)
        self.assertEqual(payload['username'], username)
        self.assertEqual(payload['type'], 'refresh')

class TestMongoDBIntegration(unittest.TestCase):
    """Integration tests for MongoDB components"""
    
    @patch('src.database.mongodb_config.MongoClient')
    def test_initialization_flow(self, mock_client):
        """Test complete MongoDB initialization flow"""
        # Mock successful connection
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        mock_instance.admin.command.return_value = {'ok': 1}
        
        # Test initialization
        with patch('src.database.mongodb_config.mongodb_config') as mock_config:
            mock_config.connect.return_value = mock_instance
            mock_config.create_indexes.return_value = None
            
            result = initialize_mongodb()
            self.assertTrue(result)
    
    def test_end_to_end_alert_workflow(self):
        """Test complete alert workflow from creation to retrieval"""
        with patch('src.database.mongodb_dal.get_mongodb_database') as mock_get_db:
            mock_db = MagicMock()
            mock_get_db.return_value = mock_db
            
            dal = MongoDBDAL()
            
            # Mock alert creation
            mock_db.__getitem__.return_value.find_one.return_value = {'alert_id': 0}
            mock_db.__getitem__.return_value.insert_one.return_value.inserted_id = "alert_id"
            
            # Create alert
            alert_data = {
                'timestamp': datetime.utcnow(),
                'severity': AlertSeverity.HIGH.value,
                'source_ip': '192.168.1.100',
                'destination_ip': '10.0.0.50',
                'attack_type': 'Brute Force',
                'anomaly_score': 0.85
            }
            
            success, message, alert_id = dal.create_alert(alert_data)
            self.assertTrue(success)
            
            # Mock alert retrieval
            mock_alert = {
                'alert_id': 1,
                'severity': AlertSeverity.HIGH.value,
                'source_ip': '192.168.1.100'
            }
            mock_db.__getitem__.return_value.find_one.return_value = mock_alert
            
            # Retrieve alert
            retrieved_alert = dal.get_alert_by_id(1)
            self.assertEqual(retrieved_alert['alert_id'], 1)
            self.assertEqual(retrieved_alert['severity'], AlertSeverity.HIGH.value)

def run_mongodb_tests():
    """Run all MongoDB integration tests"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestMongoDBConfig,
        TestMongoDBSchemas,
        TestMongoDBDAL,
        TestDataMigrator,
        TestMongoDBAuthManager,
        TestMongoDBIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running MongoDB Integration Tests...")
    success = run_mongodb_tests()
    
    if success:
        print("\n✓ All MongoDB integration tests passed!")
        exit(0)
    else:
        print("\n✗ Some MongoDB integration tests failed!")
        exit(1)
