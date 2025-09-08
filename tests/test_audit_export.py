#!/usr/bin/env python3
"""
Test suite for audit export functionality
"""

import os
import sys
import json
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.audit_exporter import AuditExporter
from src.auth.audit_logger import AuditLogger, AuditEventType

class TestAuditExporter(unittest.TestCase):
    """Test cases for audit export functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.audit_log_file = os.path.join(self.temp_dir, 'test_audit.log')
        self.audit_json_file = os.path.join(self.temp_dir, 'test_audit.json')
        
        # Create mock audit logger
        self.mock_audit_logger = Mock()
        self.exporter = AuditExporter(self.mock_audit_logger)
        
        # Sample audit data
        self.sample_logs = [
            {
                'id': '1',
                'timestamp': '2024-01-01T10:00:00Z',
                'event_type': 'login_success',
                'username': 'admin',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0',
                'success': True,
                'details': {'action': 'login'},
                'error_message': None
            },
            {
                'id': '2',
                'timestamp': '2024-01-01T10:05:00Z',
                'event_type': 'login_failed',
                'username': 'user1',
                'ip_address': '192.168.1.101',
                'user_agent': 'Mozilla/5.0',
                'success': False,
                'details': {'reason': 'invalid_password'},
                'error_message': 'Invalid credentials'
            },
            {
                'id': '3',
                'timestamp': '2024-01-01T10:10:00Z',
                'event_type': 'alert_flagged',
                'username': 'analyst1',
                'ip_address': '192.168.1.102',
                'user_agent': 'Mozilla/5.0',
                'success': True,
                'details': {'alert_id': 123},
                'error_message': None
            }
        ]
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_json_export(self):
        """Test JSON export functionality"""
        self.mock_audit_logger.get_audit_logs.return_value = self.sample_logs
        
        result = self.exporter.export_audit_data(format_type='json')
        
        # Parse the result
        data = json.loads(result)
        
        # Verify structure
        self.assertIn('metadata', data)
        self.assertIn('audit_logs', data)
        self.assertIn('summary', data)
        
        # Verify metadata
        self.assertEqual(data['metadata']['export_format'], 'json')
        self.assertEqual(data['metadata']['total_records'], 3)
        
        # Verify audit logs
        self.assertEqual(len(data['audit_logs']), 3)
        self.assertEqual(data['audit_logs'][0]['event_type'], 'login_success')
        
        # Verify summary
        self.assertEqual(data['summary']['total_events'], 3)
        self.assertIn('event_types', data['summary'])
    
    def test_csv_export(self):
        """Test CSV export functionality"""
        self.mock_audit_logger.get_audit_logs.return_value = self.sample_logs
        
        result = self.exporter.export_audit_data(format_type='csv')
        
        # Verify CSV structure
        lines = result.strip().split('\n')
        
        # Should have summary comments, header, and data rows
        self.assertGreater(len(lines), 5)
        
        # Find the header line
        header_line = None
        for i, line in enumerate(lines):
            if line.startswith('id,timestamp'):
                header_line = i
                break
        
        self.assertIsNotNone(header_line, "CSV header not found")
        
        # Verify header
        headers = [h.strip() for h in lines[header_line].split(',')]
        expected_headers = ['id', 'timestamp', 'event_type', 'username', 'ip_address', 
                          'user_agent', 'success', 'error_message', 'details']
        self.assertEqual(headers, expected_headers)
        
        # Verify data rows
        data_rows = lines[header_line + 1:]
        self.assertEqual(len(data_rows), 3)
    
    def test_pdf_export(self):
        """Test PDF export functionality"""
        self.mock_audit_logger.get_audit_logs.return_value = self.sample_logs
        
        result = self.exporter.export_audit_data(format_type='pdf')
        
        # Verify it's binary data (PDF)
        self.assertIsInstance(result, bytes)
        self.assertTrue(result.startswith(b'%PDF'))
    
    def test_excel_export(self):
        """Test Excel export functionality"""
        self.mock_audit_logger.get_audit_logs.return_value = self.sample_logs
        
        result = self.exporter.export_audit_data(format_type='excel')
        
        # Verify it's binary data (Excel)
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)
    
    def test_filtering_by_event_type(self):
        """Test filtering by event type"""
        self.mock_audit_logger.get_audit_logs.return_value = [
            log for log in self.sample_logs if log['event_type'] == 'login_success'
        ]
        
        result = self.exporter.export_audit_data(
            format_type='json',
            event_type='login_success'
        )
        
        data = json.loads(result)
        self.assertEqual(len(data['audit_logs']), 1)
        self.assertEqual(data['audit_logs'][0]['event_type'], 'login_success')
    
    def test_filtering_by_username(self):
        """Test filtering by username"""
        self.mock_audit_logger.get_audit_logs.return_value = [
            log for log in self.sample_logs if log['username'] == 'admin'
        ]
        
        result = self.exporter.export_audit_data(
            format_type='json',
            username='admin'
        )
        
        data = json.loads(result)
        self.assertEqual(len(data['audit_logs']), 1)
        self.assertEqual(data['audit_logs'][0]['username'], 'admin')
    
    def test_date_range_filtering(self):
        """Test date range filtering"""
        start_date = '2024-01-01T10:00:00Z'
        end_date = '2024-01-01T10:05:00Z'
        
        # Mock filtered results
        filtered_logs = [
            log for log in self.sample_logs 
            if start_date <= log['timestamp'] <= end_date
        ]
        self.mock_audit_logger.get_audit_logs.return_value = filtered_logs
        
        result = self.exporter.export_audit_data(
            format_type='json',
            start_date=start_date,
            end_date=end_date
        )
        
        data = json.loads(result)
        self.assertEqual(len(data['audit_logs']), 2)
    
    def test_severity_filtering(self):
        """Test severity filtering"""
        # Mock high severity events
        high_severity_logs = [
            log for log in self.sample_logs 
            if log['event_type'] in ['account_locked', 'unauthorized_access']
        ]
        
        result = self.exporter._filter_by_severity(self.sample_logs, 'high')
        
        # Should return empty since our sample logs don't have high severity events
        self.assertEqual(len(result), 0)
        
        # Test with actual high severity event
        high_severity_log = {
            'id': '4',
            'timestamp': '2024-01-01T10:15:00Z',
            'event_type': 'account_locked',
            'username': 'user2',
            'success': False
        }
        
        logs_with_high_severity = self.sample_logs + [high_severity_log]
        result = self.exporter._filter_by_severity(logs_with_high_severity, 'high')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['event_type'], 'account_locked')
    
    def test_summary_generation(self):
        """Test summary statistics generation"""
        summary = self.exporter._generate_export_summary(self.sample_logs)
        
        self.assertEqual(summary['total_events'], 3)
        self.assertIn('event_types', summary)
        self.assertIn('users', summary)
        self.assertIn('success_rate', summary)
        
        # Verify event type counts
        self.assertEqual(summary['event_types']['login_success'], 1)
        self.assertEqual(summary['event_types']['login_failed'], 1)
        self.assertEqual(summary['event_types']['alert_flagged'], 1)
        
        # Verify user counts
        self.assertEqual(summary['users']['admin'], 1)
        self.assertEqual(summary['users']['user1'], 1)
        self.assertEqual(summary['users']['analyst1'], 1)
        
        # Verify success rate (2 successful out of 3 total)
        self.assertEqual(summary['success_rate'], 66.67)
    
    def test_filename_generation(self):
        """Test export filename generation"""
        # Test with date range
        filename = self.exporter.get_export_filename(
            'json', 
            '2024-01-01T00:00:00Z', 
            '2024-01-31T23:59:59Z'
        )
        self.assertTrue(filename.startswith('soc_audit_export_2024-01-01_to_2024-01-31'))
        self.assertTrue(filename.endswith('.json'))
        
        # Test without date range
        filename = self.exporter.get_export_filename('csv')
        self.assertTrue(filename.startswith('soc_audit_export_'))
        self.assertTrue(filename.endswith('.csv'))
    
    def test_empty_logs_handling(self):
        """Test handling of empty audit logs"""
        self.mock_audit_logger.get_audit_logs.return_value = []
        
        # JSON export
        result = self.exporter.export_audit_data(format_type='json')
        data = json.loads(result)
        self.assertEqual(len(data['audit_logs']), 0)
        self.assertEqual(data['summary']['total_events'], 0)
        
        # CSV export
        result = self.exporter.export_audit_data(format_type='csv')
        self.assertIn('No audit data to export', result)
    
    def test_invalid_format_handling(self):
        """Test handling of invalid export format"""
        # Mock the audit logger to return empty list for invalid format test
        self.mock_audit_logger.get_audit_logs.return_value = []
        
        with self.assertRaises(ValueError) as context:
            self.exporter.export_audit_data(format_type='invalid_format')
        
        self.assertIn('Unsupported export format', str(context.exception))


class TestAuditExportAPI(unittest.TestCase):
    """Test cases for audit export API endpoints"""
    
    def setUp(self):
        """Set up test Flask app"""
        # This would require setting up a test Flask app
        # For now, we'll focus on unit tests for the exporter class
        pass
    
    def test_export_endpoint_parameters(self):
        """Test export endpoint parameter handling"""
        # This would test the actual Flask endpoint
        # Implementation would depend on Flask test client setup
        pass


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
