#!/usr/bin/env python3
"""
Comprehensive tests for SOC Dashboard authentication system
Tests user management, MFA, JWT tokens, RBAC, and audit logging
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.auth.auth_utils import AuthManager
from src.auth.audit_logger import AuditLogger, AuditEventType
from src.dashboard.server import app

class TestAuthManager(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.users_file = os.path.join(self.temp_dir, 'test_users.json')
        self.auth_manager = AuthManager(users_file=self.users_file)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        password = "TestPassword123!"
        hashed = self.auth_manager.hash_password(password)
        
        # Hash should be different from original
        self.assertNotEqual(password, hashed)
        
        # Should verify correctly
        self.assertTrue(self.auth_manager.verify_password(password, hashed))
        
        # Should fail with wrong password
        self.assertFalse(self.auth_manager.verify_password("WrongPassword", hashed))
    
    def test_password_strength_validation(self):
        """Test password strength requirements"""
        # Valid passwords
        valid_passwords = [
            "StrongPass123!",
            "MySecure@Pass1",
            "Complex#Password9"
        ]
        
        for password in valid_passwords:
            self.assertTrue(self.auth_manager._validate_password_strength(password))
        
        # Invalid passwords
        invalid_passwords = [
            "weak",  # Too short
            "nouppercase123!",  # No uppercase
            "NOLOWERCASE123!",  # No lowercase
            "NoDigits!@#",  # No digits
            "NoSpecialChars123"  # No special characters
        ]
        
        for password in invalid_passwords:
            self.assertFalse(self.auth_manager._validate_password_strength(password))
    
    def test_user_creation(self):
        """Test user creation with validation"""
        # Valid user creation
        success, message = self.auth_manager.create_user(
            "testuser", "ValidPass123!", "test@example.com", "analyst"
        )
        self.assertTrue(success)
        self.assertEqual(message, "User created successfully")
        
        # Duplicate username
        success, message = self.auth_manager.create_user(
            "testuser", "ValidPass123!", "test2@example.com", "analyst"
        )
        self.assertFalse(success)
        self.assertEqual(message, "Username already exists")
        
        # Invalid role
        success, message = self.auth_manager.create_user(
            "testuser2", "ValidPass123!", "test@example.com", "invalid_role"
        )
        self.assertFalse(success)
        self.assertIn("Invalid role", message)
        
        # Weak password
        success, message = self.auth_manager.create_user(
            "testuser3", "weak", "test@example.com", "analyst"
        )
        self.assertFalse(success)
        self.assertIn("Password must be at least", message)
    
    def test_user_authentication(self):
        """Test user authentication with various scenarios"""
        # Create test user
        self.auth_manager.create_user("testuser", "ValidPass123!", "test@example.com", "analyst")
        
        # Valid authentication
        success, message, user_info = self.auth_manager.authenticate_user("testuser", "ValidPass123!")
        self.assertTrue(success)
        self.assertEqual(message, "Authentication successful")
        self.assertEqual(user_info['username'], "testuser")
        self.assertEqual(user_info['role'], "analyst")
        
        # Invalid password
        success, message, user_info = self.auth_manager.authenticate_user("testuser", "WrongPassword")
        self.assertFalse(success)
        self.assertEqual(message, "Invalid credentials")
        
        # Non-existent user
        success, message, user_info = self.auth_manager.authenticate_user("nonexistent", "ValidPass123!")
        self.assertFalse(success)
        self.assertEqual(message, "Invalid credentials")
    
    def test_account_lockout(self):
        """Test account lockout after failed attempts"""
        # Create test user
        self.auth_manager.create_user("testuser", "ValidPass123!", "test@example.com", "analyst")
        
        # Make 5 failed attempts
        for i in range(5):
            success, message, user_info = self.auth_manager.authenticate_user("testuser", "WrongPassword")
            self.assertFalse(success)
        
        # Account should be locked
        success, message, user_info = self.auth_manager.authenticate_user("testuser", "ValidPass123!")
        self.assertFalse(success)
        self.assertIn("Account temporarily locked", message)
    
    def test_mfa_setup_and_verification(self):
        """Test MFA setup and token verification"""
        # Create test user
        self.auth_manager.create_user("testuser", "ValidPass123!", "test@example.com", "analyst")
        
        # Setup MFA
        success, secret, qr_code = self.auth_manager.setup_mfa("testuser")
        self.assertTrue(success)
        self.assertIsNotNone(secret)
        self.assertIsNotNone(qr_code)
        
        # Generate valid TOTP token
        import pyotp
        totp = pyotp.TOTP(secret)
        valid_token = totp.now()
        
        # Enable MFA with valid token
        success, message = self.auth_manager.enable_mfa("testuser", valid_token)
        self.assertTrue(success)
        
        # Test authentication with MFA
        success, message, user_info = self.auth_manager.authenticate_user("testuser", "ValidPass123!")
        self.assertFalse(success)  # Should require MFA token
        self.assertTrue(user_info.get('mfa_required', False))
        
        # Authenticate with MFA token
        new_token = totp.now()
        success, message, user_info = self.auth_manager.authenticate_user("testuser", "ValidPass123!", new_token)
        self.assertTrue(success)
    
    def test_jwt_token_generation_and_verification(self):
        """Test JWT token generation and verification"""
        # Generate tokens
        access_token, refresh_token = self.auth_manager.generate_tokens("testuser", "analyst")
        
        # Verify access token
        valid, payload = self.auth_manager.verify_token(access_token)
        self.assertTrue(valid)
        self.assertEqual(payload['username'], "testuser")
        self.assertEqual(payload['role'], "analyst")
        self.assertEqual(payload['type'], "access")
        
        # Verify refresh token
        valid, payload = self.auth_manager.verify_token(refresh_token)
        self.assertTrue(valid)
        self.assertEqual(payload['username'], "testuser")
        self.assertEqual(payload['type'], "refresh")
    
    def test_token_refresh(self):
        """Test token refresh functionality"""
        # Create user and generate tokens
        self.auth_manager.create_user("testuser", "ValidPass123!", "test@example.com", "analyst")
        access_token, refresh_token = self.auth_manager.generate_tokens("testuser", "analyst")
        
        # Refresh tokens
        success, new_access_token, new_refresh_token = self.auth_manager.refresh_access_token(refresh_token)
        self.assertTrue(success)
        self.assertIsNotNone(new_access_token)
        self.assertIsNotNone(new_refresh_token)
        
        # Verify new access token
        valid, payload = self.auth_manager.verify_token(new_access_token)
        self.assertTrue(valid)
        self.assertEqual(payload['username'], "testuser")
    
    def test_user_management_operations(self):
        """Test CRUD operations for user management"""
        # Create test users
        self.auth_manager.create_user("admin1", "AdminPass123!", "admin@example.com", "admin")
        self.auth_manager.create_user("analyst1", "AnalystPass123!", "analyst@example.com", "analyst")
        
        # Get all users
        users = self.auth_manager.get_users()
        self.assertEqual(len(users), 3)  # Including default admin
        
        # Update user
        success, message = self.auth_manager.update_user("analyst1", {"role": "admin", "email": "new@example.com"})
        self.assertTrue(success)
        
        # Verify update
        users = self.auth_manager.get_users()
        analyst_user = next(u for u in users if u['username'] == 'analyst1')
        self.assertEqual(analyst_user['role'], "admin")
        self.assertEqual(analyst_user['email'], "new@example.com")
        
        # Delete user
        success, message = self.auth_manager.delete_user("analyst1", "admin1")
        self.assertTrue(success)
        
        # Verify deletion
        users = self.auth_manager.get_users()
        usernames = [u['username'] for u in users]
        self.assertNotIn("analyst1", usernames)
    
    def test_password_change(self):
        """Test password change functionality"""
        # Create test user
        self.auth_manager.create_user("testuser", "OldPass123!", "test@example.com", "analyst")
        
        # Change password
        success, message = self.auth_manager.change_password("testuser", "OldPass123!", "NewPass123!")
        self.assertTrue(success)
        
        # Verify old password no longer works
        success, message, user_info = self.auth_manager.authenticate_user("testuser", "OldPass123!")
        self.assertFalse(success)
        
        # Verify new password works
        success, message, user_info = self.auth_manager.authenticate_user("testuser", "NewPass123!")
        self.assertTrue(success)

class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.temp_dir, 'test_audit.log')
        self.json_file = os.path.join(self.temp_dir, 'test_audit.json')
        self.audit_logger = AuditLogger(log_file=self.log_file, json_file=self.json_file)
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_audit_event_logging(self):
        """Test logging of audit events"""
        # Log a successful login event
        self.audit_logger.log_event(
            AuditEventType.LOGIN_SUCCESS,
            username="testuser",
            ip_address="192.168.1.100",
            user_agent="Mozilla/5.0",
            details={"method": "password"}
        )
        
        # Verify log file exists and contains event
        self.assertTrue(os.path.exists(self.log_file))
        self.assertTrue(os.path.exists(self.json_file))
        
        # Read JSON log
        with open(self.json_file, 'r') as f:
            logs = json.load(f)
        
        self.assertEqual(len(logs), 1)
        log_entry = logs[0]
        self.assertEqual(log_entry['event_type'], 'login_success')
        self.assertEqual(log_entry['username'], 'testuser')
        self.assertEqual(log_entry['ip_address'], '192.168.1.100')
        self.assertTrue(log_entry['success'])
    
    def test_audit_log_retrieval(self):
        """Test retrieval of audit logs with filtering"""
        # Log multiple events
        events = [
            (AuditEventType.LOGIN_SUCCESS, "user1", True),
            (AuditEventType.LOGIN_FAILED, "user2", False),
            (AuditEventType.USER_CREATED, "admin", True),
            (AuditEventType.ALERT_FLAGGED, "user1", True)
        ]
        
        for event_type, username, success in events:
            self.audit_logger.log_event(event_type, username=username, success=success)
        
        # Get all logs
        all_logs = self.audit_logger.get_audit_logs()
        self.assertEqual(len(all_logs), 4)
        
        # Filter by username
        user1_logs = self.audit_logger.get_audit_logs(username="user1")
        self.assertEqual(len(user1_logs), 2)
        
        # Filter by event type
        login_logs = self.audit_logger.get_audit_logs(event_type="login_success")
        self.assertEqual(len(login_logs), 1)
    
    def test_security_alerts_generation(self):
        """Test generation of security alerts"""
        # Log multiple failed login attempts
        for i in range(4):
            self.audit_logger.log_event(
                AuditEventType.LOGIN_FAILED,
                username="testuser",
                ip_address=f"192.168.1.{100 + i}",
                success=False
            )
        
        # Get security alerts
        alerts = self.audit_logger.get_security_alerts(days=1)
        
        # Should have alert for multiple failed logins
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert['type'], 'multiple_failed_logins')
        self.assertEqual(alert['username'], 'testuser')
        self.assertEqual(alert['details']['failed_attempts'], 4)

class TestAuthenticationAPI(unittest.TestCase):
    def setUp(self):
        """Set up test Flask app"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create temporary files for testing
        self.temp_dir = tempfile.mkdtemp()
        self.app.auth_manager.users_file = os.path.join(self.temp_dir, 'test_users.json')
        self.app.auth_manager._initialize_default_users()
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_login_endpoint(self):
        """Test login API endpoint"""
        # Valid login
        response = self.client.post('/api/auth/login', 
            json={'username': 'admin', 'password': 'SecureAdmin123!'})
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('access_token', data)
        self.assertIn('refresh_token', data)
        self.assertIn('user', data)
        
        # Invalid credentials
        response = self.client.post('/api/auth/login',
            json={'username': 'admin', 'password': 'wrongpassword'})
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_protected_endpoint_access(self):
        """Test access to protected endpoints"""
        # Login to get token
        response = self.client.post('/api/auth/login',
            json={'username': 'admin', 'password': 'SecureAdmin123!'})
        
        data = json.loads(response.data)
        token = data['access_token']
        
        # Access protected endpoint with token
        headers = {'Authorization': f'Bearer {token}'}
        response = self.client.get('/api/alerts', headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Access without token
        response = self.client.get('/api/alerts')
        self.assertEqual(response.status_code, 401)
        
        # Access with invalid token
        headers = {'Authorization': 'Bearer invalid_token'}
        response = self.client.get('/api/alerts', headers=headers)
        self.assertEqual(response.status_code, 401)
    
    def test_role_based_access_control(self):
        """Test RBAC for admin-only endpoints"""
        # Create analyst user
        self.app.auth_manager.create_user("analyst", "AnalystPass123!", "analyst@example.com", "analyst")
        
        # Login as analyst
        response = self.client.post('/api/auth/login',
            json={'username': 'analyst', 'password': 'AnalystPass123!'})
        
        data = json.loads(response.data)
        analyst_token = data['access_token']
        
        # Try to access admin-only endpoint
        headers = {'Authorization': f'Bearer {analyst_token}'}
        response = self.client.get('/api/admin/users', headers=headers)
        self.assertEqual(response.status_code, 403)
        
        # Login as admin
        response = self.client.post('/api/auth/login',
            json={'username': 'admin', 'password': 'SecureAdmin123!'})
        
        data = json.loads(response.data)
        admin_token = data['access_token']
        
        # Access admin endpoint as admin
        headers = {'Authorization': f'Bearer {admin_token}'}
        response = self.client.get('/api/admin/users', headers=headers)
        self.assertEqual(response.status_code, 200)
    
    def test_user_management_endpoints(self):
        """Test user management API endpoints"""
        # Login as admin
        response = self.client.post('/api/auth/login',
            json={'username': 'admin', 'password': 'SecureAdmin123!'})
        
        data = json.loads(response.data)
        token = data['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Create user
        response = self.client.post('/api/admin/users',
            json={
                'username': 'newuser',
                'password': 'NewUserPass123!',
                'role': 'analyst',
                'email': 'newuser@example.com'
            },
            headers=headers)
        
        self.assertEqual(response.status_code, 200)
        
        # Get users
        response = self.client.get('/api/admin/users', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('users', data)
        
        # Update user
        response = self.client.put('/api/admin/users/newuser',
            json={'role': 'admin'},
            headers=headers)
        
        self.assertEqual(response.status_code, 200)
        
        # Delete user
        response = self.client.delete('/api/admin/users/newuser', headers=headers)
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)
