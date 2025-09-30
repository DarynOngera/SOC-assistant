#!/usr/bin/env python3
"""
Comprehensive tests for triage action functionality
Tests all triage operations: escalate, assign, investigate, resolve, bulk operations
"""

import unittest
import json
import tempfile
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.dashboard.server import app, dashboard_api, socketio
from src.database.mongodb_dal import get_dal
from src.auth.mongodb_auth_utils import MongoDBAuthManager

class TestTriageActions(unittest.TestCase):
    """Test suite for comprehensive triage actions"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock MongoDB DAL
        self.mock_dal = Mock()
        dashboard_api.dal = self.mock_dal
        
        # Mock auth manager
        self.mock_auth = Mock()
        self.app.auth_manager = self.mock_auth
        
        # Mock user context
        self.test_user = {
            'username': 'test_analyst',
            'role': 'analyst',
            'user_id': 'test_user_123'
        }
        
        # Sample alert data
        self.sample_alert = {
            'alert_id': 123,
            'severity': 'high',
            'attack_type': 'Brute Force',
            'source_ip': '192.168.1.100',
            'destination_ip': '10.0.0.50',
            'status': 'new',
            'timestamp': datetime.now(),
            'anomaly_score': 0.85
        }
        
        # Create a test request context with authenticated user
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Mock the decorators at the module level
        import src.dashboard.server as server_module
        
        def mock_token_required(f):
            def decorated(*args, **kwargs):
                # Add user to Flask's g object
                from flask import g
                g.current_user = self.test_user
                # Also add to request for compatibility
                try:
                    from flask import request
                    request.current_user = self.test_user
                except RuntimeError:
                    pass  # Outside request context
                return f(*args, **kwargs)
            return decorated
        
        def mock_analyst_required(f):
            return f
        
        # Patch the decorators in the server module
        server_module.token_required = mock_token_required
        server_module.analyst_or_admin_required = mock_analyst_required
        
    def tearDown(self):
        """Clean up after tests"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()
        
    def test_escalate_alert_success(self):
        """Test successful alert escalation"""
        # Mock successful update
        self.mock_dal.db.alerts.find_one.return_value = self.sample_alert
        self.mock_dal.update_alert.return_value = (True, "Alert updated successfully")
        self.mock_dal.create_audit_log.return_value = True
        
        # Mock socketio emit
        with patch('src.dashboard.server.socketio.emit') as mock_emit:
            response = self.client.post(
                '/api/alerts/123/escalate',
                json={
                    'reason': 'High severity attack detected',
                    'escalated_to': 'Senior Analyst',
                    'priority_increase': True
                },
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual(data['new_severity'], 'critical')
            
            # Verify audit log was created
            self.mock_dal.create_audit_log.assert_called_once()
            
            # Verify WebSocket notification was sent
            mock_emit.assert_called_once()
            emit_args = mock_emit.call_args[0]
            self.assertEqual(emit_args[0], 'triage_update')
            self.assertEqual(emit_args[1]['type'], 'escalation')
            self.assertEqual(emit_args[1]['alert_id'], 123)
    
    def test_assign_alert_success(self):
        """Test successful alert assignment"""
        # Mock user exists
        self.mock_dal.get_user_by_username.return_value = {'username': 'senior_analyst', 'role': 'senior_analyst'}
        self.mock_dal.update_alert.return_value = (True, "Alert assigned successfully")
        self.mock_dal.create_audit_log.return_value = True
        
        with patch('src.dashboard.server.socketio.emit') as mock_emit:
            response = self.client.post(
                '/api/alerts/123/assign',
                json={
                    'assigned_to': 'senior_analyst',
                    'notes': 'Requires immediate attention'
                },
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verify assignment was logged
            self.mock_dal.create_audit_log.assert_called_once()
            
            # Verify notification was sent
            mock_emit.assert_called_once()
            emit_data = mock_emit.call_args[0][1]
            self.assertEqual(emit_data['type'], 'assignment')
            self.assertEqual(emit_data['assigned_to'], 'senior_analyst')
    
    def test_assign_alert_user_not_found(self):
        """Test assignment failure when user doesn't exist"""
        self.mock_dal.get_user_by_username.return_value = None
        
        response = self.client.post(
            '/api/alerts/123/assign',
            json={'assigned_to': 'nonexistent_user'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Assigned user not found')
    
    def test_start_investigation_success(self):
        """Test successful investigation start"""
        self.mock_dal.update_alert.return_value = (True, "Investigation started")
        self.mock_dal.create_audit_log.return_value = True
        
        with patch('src.dashboard.server.socketio.emit') as mock_emit:
            response = self.client.post(
                '/api/alerts/123/investigate',
                json={
                    'notes': 'Starting detailed analysis of attack pattern',
                    'priority': 'high'
                },
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verify investigation was logged
            self.mock_dal.create_audit_log.assert_called_once()
            
            # Verify notification
            mock_emit.assert_called_once()
            emit_data = mock_emit.call_args[0][1]
            self.assertEqual(emit_data['type'], 'investigation')
            self.assertEqual(emit_data['investigator'], 'test_analyst')
    
    def test_resolve_alert_success(self):
        """Test successful alert resolution"""
        self.mock_dal.update_alert.return_value = (True, "Alert resolved")
        self.mock_dal.create_audit_log.return_value = True
        
        with patch('src.dashboard.server.socketio.emit') as mock_emit:
            response = self.client.post(
                '/api/alerts/123/resolve',
                json={
                    'resolution_type': 'resolved',
                    'notes': 'Attack blocked by firewall rules',
                    'action_taken': 'Updated firewall configuration'
                },
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verify resolution was logged
            self.mock_dal.create_audit_log.assert_called_once()
            
            # Verify notification
            mock_emit.assert_called_once()
            emit_data = mock_emit.call_args[0][1]
            self.assertEqual(emit_data['type'], 'resolution')
            self.assertEqual(emit_data['resolution_type'], 'resolved')
    
    def test_resolve_alert_missing_notes(self):
        """Test resolution failure when notes are missing"""
        response = self.client.post(
            '/api/alerts/123/resolve',
            json={'resolution_type': 'resolved'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Resolution notes are required')
    
    def test_update_investigation_success(self):
        """Test successful investigation update"""
        # Mock existing alert with investigation notes
        existing_alert = {
            **self.sample_alert,
            'investigation_notes': 'Initial analysis completed'
        }
        self.mock_dal.db.alerts.find_one.return_value = existing_alert
        self.mock_dal.update_alert.return_value = (True, "Investigation updated")
        self.mock_dal.create_audit_log.return_value = True
        
        with patch('src.dashboard.server.socketio.emit') as mock_emit:
            response = self.client.post(
                '/api/alerts/123/update-investigation',
                json={
                    'update': 'Found additional indicators of compromise',
                    'status': 'in_progress'
                },
                headers={'Content-Type': 'application/json'}
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            
            # Verify update was logged
            self.mock_dal.create_audit_log.assert_called_once()
            
            # Verify notification
            mock_emit.assert_called_once()
            emit_data = mock_emit.call_args[0][1]
            self.assertEqual(emit_data['type'], 'investigation_update')
    
    def test_bulk_triage_flag_success(self):
        """Test successful bulk flag operation"""
        self.mock_dal.update_alert.return_value = (True, "Alert flagged")
        self.mock_dal.create_audit_log.return_value = True
        
        response = self.client.post(
            '/api/alerts/bulk-triage',
            json={
                'alert_ids': [123, 124, 125],
                'action': 'flag',
                'action_data': {}
            },
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['total_processed'], 3)
        self.assertEqual(data['successful'], 3)
        self.assertEqual(data['failed'], 0)
        
        # Verify all alerts were processed
        self.assertEqual(self.mock_dal.update_alert.call_count, 3)
        self.assertEqual(self.mock_dal.create_audit_log.call_count, 3)
    
    def test_bulk_triage_assign_success(self):
        """Test successful bulk assignment"""
        self.mock_dal.update_alert.return_value = (True, "Alert assigned")
        self.mock_dal.create_audit_log.return_value = True
        
        response = self.client.post(
            '/api/alerts/bulk-triage',
            json={
                'alert_ids': [123, 124],
                'action': 'assign',
                'action_data': {'assigned_to': 'senior_analyst'}
            },
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['successful'], 2)
    
    def test_bulk_triage_mixed_results(self):
        """Test bulk operation with mixed success/failure results"""
        # Mock one success, one failure
        self.mock_dal.update_alert.side_effect = [
            (True, "Success"),
            (False, "Alert not found")
        ]
        self.mock_dal.create_audit_log.return_value = True
        
        response = self.client.post(
            '/api/alerts/bulk-triage',
            json={
                'alert_ids': [123, 999],
                'action': 'flag'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['successful'], 1)
        self.assertEqual(data['failed'], 1)
        self.assertEqual(len(data['results']['success']), 1)
        self.assertEqual(len(data['results']['failed']), 1)
    
    def test_get_analysts_success(self):
        """Test successful retrieval of analysts"""
        mock_users = [
            {'username': 'analyst1', 'role': 'analyst', 'full_name': 'John Analyst', 'active': True},
            {'username': 'senior1', 'role': 'senior_analyst', 'full_name': 'Jane Senior', 'active': True},
            {'username': 'manager1', 'role': 'soc_manager', 'full_name': 'Bob Manager', 'active': True},
            {'username': 'viewer1', 'role': 'viewer', 'full_name': 'Alice Viewer', 'active': True}  # Should be excluded
        ]
        self.mock_dal.get_all_users.return_value = mock_users
        
        response = self.client.get('/api/analysts')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        
        # Should only return analysts, senior_analysts, soc_managers, super_admins
        self.assertEqual(len(data['analysts']), 3)
        usernames = [analyst['username'] for analyst in data['analysts']]
        self.assertIn('analyst1', usernames)
        self.assertIn('senior1', usernames)
        self.assertIn('manager1', usernames)
        self.assertNotIn('viewer1', usernames)
    
    def test_invalid_alert_id_format(self):
        """Test handling of invalid alert ID format"""
        response = self.client.post(
            '/api/alerts/invalid_id/escalate',
            json={'reason': 'test'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Invalid alert ID format')
    
    def test_alert_not_found(self):
        """Test handling when alert is not found"""
        self.mock_dal.db.alerts.find_one.return_value = None
        
        response = self.client.post(
            '/api/alerts/999/escalate',
            json={'reason': 'test'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Alert not found')
    
    def test_database_error_handling(self):
        """Test handling of database errors"""
        self.mock_dal.db.alerts.find_one.return_value = self.sample_alert
        self.mock_dal.update_alert.side_effect = Exception("Database connection error")
        
        response = self.client.post(
            '/api/alerts/123/escalate',
            json={'reason': 'test'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Failed to escalate alert')
    
    def test_bulk_operation_validation(self):
        """Test validation for bulk operations"""
        # Test missing alert_ids
        response = self.client.post(
            '/api/alerts/bulk-triage',
            json={'action': 'flag'},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'alert_ids and action are required')
        
        # Test missing action
        response = self.client.post(
            '/api/alerts/bulk-triage',
            json={'alert_ids': [123]},
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'alert_ids and action are required')
    
    def test_unsupported_bulk_action(self):
        """Test handling of unsupported bulk actions"""
        response = self.client.post(
            '/api/alerts/bulk-triage',
            json={
                'alert_ids': [123],
                'action': 'unsupported_action'
            },
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['successful'], 0)
        self.assertEqual(data['failed'], 1)
        self.assertIn('Unsupported action', data['results']['failed'][0]['error'])

class TestTriageIntegration(unittest.TestCase):
    """Integration tests for triage workflow"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Mock components for integration testing
        self.mock_dal = Mock()
        dashboard_api.dal = self.mock_dal
        
        # Mock user context
        self.test_user = {
            'username': 'integration_test_user',
            'role': 'senior_analyst'
        }
        
        # Create app context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Mock the decorators at the module level
        import src.dashboard.server as server_module
        
        def mock_token_required(f):
            def decorated(*args, **kwargs):
                from flask import g
                g.current_user = self.test_user
                try:
                    from flask import request
                    request.current_user = self.test_user
                except RuntimeError:
                    pass
                return f(*args, **kwargs)
            return decorated
        
        def mock_analyst_required(f):
            return f
        
        server_module.token_required = mock_token_required
        server_module.analyst_or_admin_required = mock_analyst_required
    
    def tearDown(self):
        """Clean up integration tests"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()
    
    def test_complete_triage_workflow(self):
        """Test complete triage workflow from escalation to resolution"""
        alert_id = 123
        
        # Mock alert exists
        sample_alert = {
            'alert_id': alert_id,
            'severity': 'medium',
            'status': 'new',
            'investigation_notes': ''
        }
        
        self.mock_dal.db.alerts.find_one.return_value = sample_alert
        self.mock_dal.update_alert.return_value = (True, "Success")
        self.mock_dal.create_audit_log.return_value = True
        self.mock_dal.get_user_by_username.return_value = {'username': 'analyst2', 'role': 'analyst'}
        
        with patch('src.dashboard.server.socketio.emit') as mock_emit:
            # Step 1: Escalate alert
            response = self.client.post(
                f'/api/alerts/{alert_id}/escalate',
                json={'reason': 'Suspicious activity pattern detected'},
                headers={'Content-Type': 'application/json'}
            )
            self.assertEqual(response.status_code, 200)
            
            # Step 2: Assign to analyst
            response = self.client.post(
                f'/api/alerts/{alert_id}/assign',
                json={'assigned_to': 'analyst2', 'notes': 'Please investigate immediately'},
                headers={'Content-Type': 'application/json'}
            )
            self.assertEqual(response.status_code, 200)
            
            # Step 3: Start investigation
            response = self.client.post(
                f'/api/alerts/{alert_id}/investigate',
                json={'notes': 'Beginning forensic analysis', 'priority': 'high'},
                headers={'Content-Type': 'application/json'}
            )
            self.assertEqual(response.status_code, 200)
            
            # Step 4: Update investigation
            response = self.client.post(
                f'/api/alerts/{alert_id}/update-investigation',
                json={'update': 'Found malicious payload', 'status': 'in_progress'},
                headers={'Content-Type': 'application/json'}
            )
            self.assertEqual(response.status_code, 200)
            
            # Step 5: Resolve alert
            response = self.client.post(
                f'/api/alerts/{alert_id}/resolve',
                json={
                    'resolution_type': 'resolved',
                    'notes': 'Threat neutralized and systems secured',
                    'action_taken': 'Blocked malicious IPs and updated signatures'
                },
                headers={'Content-Type': 'application/json'}
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify all steps generated notifications
            self.assertEqual(mock_emit.call_count, 5)
            
            # Verify all actions were logged
            self.assertEqual(self.mock_dal.create_audit_log.call_count, 5)

if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
