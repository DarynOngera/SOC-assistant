#!/usr/bin/env python3
"""
Comprehensive test suite for CSV upload and anomaly detection functionality
Tests the complete workflow from file upload to report generation
"""

import os
import sys
import json
import tempfile
import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.csv_processor import CSVProcessor
from src.models.supervised_trainer import SupervisedSOCDetector

class TestCSVProcessor(unittest.TestCase):
    """Test CSV processing functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.upload_dir = os.path.join(self.test_dir, 'uploads')
        self.reports_dir = os.path.join(self.test_dir, 'reports')
        
        # Create test CSV processor
        self.processor = CSVProcessor(
            detector=None,  # Will test with mock detector
            upload_dir=self.upload_dir,
            reports_dir=self.reports_dir
        )
        
        # Create sample CSV data
        self.sample_data = self._create_sample_csv_data()
        
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_sample_csv_data(self):
        """Create sample CSV data for testing"""
        np.random.seed(42)
        n_samples = 1000
        
        # Create realistic network traffic features
        data = {
            'duration': np.random.exponential(1.0, n_samples),
            'protocol_type': np.random.choice(['tcp', 'udp', 'icmp'], n_samples),
            'service': np.random.choice(['http', 'ftp', 'smtp', 'ssh'], n_samples),
            'flag': np.random.choice(['SF', 'S0', 'REJ'], n_samples),
            'src_bytes': np.random.exponential(1000, n_samples),
            'dst_bytes': np.random.exponential(500, n_samples),
            'land': np.random.choice([0, 1], n_samples, p=[0.99, 0.01]),
            'wrong_fragment': np.random.poisson(0.1, n_samples),
            'urgent': np.random.poisson(0.05, n_samples),
            'hot': np.random.poisson(0.2, n_samples),
            'num_failed_logins': np.random.poisson(0.1, n_samples),
            'logged_in': np.random.choice([0, 1], n_samples, p=[0.3, 0.7]),
            'num_compromised': np.random.poisson(0.05, n_samples),
            'root_shell': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
            'su_attempted': np.random.choice([0, 1], n_samples, p=[0.98, 0.02]),
            'num_root': np.random.poisson(0.1, n_samples),
            'num_file_creations': np.random.poisson(0.2, n_samples),
            'num_shells': np.random.poisson(0.05, n_samples),
            'num_access_files': np.random.poisson(0.1, n_samples),
            'num_outbound_cmds': np.random.poisson(0.05, n_samples),
            'is_host_login': np.random.choice([0, 1], n_samples, p=[0.9, 0.1]),
            'is_guest_login': np.random.choice([0, 1], n_samples, p=[0.95, 0.05]),
            'count': np.random.poisson(10, n_samples),
            'srv_count': np.random.poisson(5, n_samples),
            'serror_rate': np.random.uniform(0, 1, n_samples),
            'srv_serror_rate': np.random.uniform(0, 1, n_samples),
            'rerror_rate': np.random.uniform(0, 1, n_samples),
            'srv_rerror_rate': np.random.uniform(0, 1, n_samples),
            'same_srv_rate': np.random.uniform(0, 1, n_samples),
            'diff_srv_rate': np.random.uniform(0, 1, n_samples),
            'srv_diff_host_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_count': np.random.poisson(50, n_samples),
            'dst_host_srv_count': np.random.poisson(20, n_samples),
            'dst_host_same_srv_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_diff_srv_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_same_src_port_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_srv_diff_host_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_serror_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_srv_serror_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_rerror_rate': np.random.uniform(0, 1, n_samples),
            'dst_host_srv_rerror_rate': np.random.uniform(0, 1, n_samples),
            'label': np.random.choice(['normal', 'attack'], n_samples, p=[0.8, 0.2])
        }
        
        return pd.DataFrame(data)
    
    def _create_test_csv_file(self, filename='test_data.csv', data=None):
        """Create a test CSV file"""
        if data is None:
            data = self.sample_data
            
        file_path = os.path.join(self.test_dir, filename)
        data.to_csv(file_path, index=False)
        return file_path
    
    def test_csv_file_validation_valid_file(self):
        """Test CSV file validation with valid file"""
        csv_path = self._create_test_csv_file()
        
        is_valid, message = self.processor.validate_csv_file(csv_path)
        
        self.assertTrue(is_valid)
        self.assertEqual(message, "File is valid")
    
    def test_csv_file_validation_nonexistent_file(self):
        """Test CSV file validation with nonexistent file"""
        is_valid, message = self.processor.validate_csv_file('/nonexistent/file.csv')
        
        self.assertFalse(is_valid)
        self.assertEqual(message, "File does not exist")
    
    def test_csv_file_validation_wrong_extension(self):
        """Test CSV file validation with wrong file extension"""
        txt_path = os.path.join(self.test_dir, 'test.txt')
        with open(txt_path, 'w') as f:
            f.write("test content")
        
        is_valid, message = self.processor.validate_csv_file(txt_path)
        
        self.assertFalse(is_valid)
        self.assertEqual(message, "File must be a CSV file")
    
    def test_csv_file_validation_empty_file(self):
        """Test CSV file validation with empty CSV file"""
        empty_csv = os.path.join(self.test_dir, 'empty.csv')
        pd.DataFrame().to_csv(empty_csv, index=False)
        
        is_valid, message = self.processor.validate_csv_file(empty_csv)
        
        self.assertFalse(is_valid)
        self.assertEqual(message, "CSV file is empty or corrupted")
    
    def test_csv_file_validation_too_few_columns(self):
        """Test CSV file validation with too few columns"""
        small_data = pd.DataFrame({'col1': [1, 2, 3], 'col2': [4, 5, 6]})
        small_csv = self._create_test_csv_file('small.csv', small_data)
        
        is_valid, message = self.processor.validate_csv_file(small_csv)
        
        self.assertFalse(is_valid)
        self.assertEqual(message, "CSV file must have at least 5 columns for meaningful analysis")
    
    def test_preprocess_csv_data(self):
        """Test CSV data preprocessing"""
        csv_path = self._create_test_csv_file()
        
        df, metadata = self.processor.preprocess_csv_data(csv_path)
        
        # Check that data was loaded and processed
        self.assertIsInstance(df, pd.DataFrame)
        self.assertGreater(len(df), 0)
        self.assertIsInstance(metadata, dict)
        
        # Check metadata structure
        required_keys = ['original_shape', 'processed_shape', 'numeric_columns', 
                        'categorical_columns', 'file_size_mb', 'preprocessing_timestamp']
        for key in required_keys:
            self.assertIn(key, metadata)
    
    def test_preprocess_csv_data_with_sample_size(self):
        """Test CSV data preprocessing with sample size limit"""
        csv_path = self._create_test_csv_file()
        sample_size = 100
        
        df, metadata = self.processor.preprocess_csv_data(csv_path, sample_size=sample_size)
        
        # Check that sampling was applied
        self.assertLessEqual(len(df), sample_size)
        self.assertEqual(metadata['processed_shape'][0], len(df))
    
    def test_detect_anomalies_mock_model(self):
        """Test anomaly detection with mock model (no trained detector)"""
        csv_path = self._create_test_csv_file()
        df, metadata = self.processor.preprocess_csv_data(csv_path)
        
        results = self.processor.detect_anomalies(df, metadata)
        
        # Check results structure
        required_keys = ['total_records', 'anomalies_detected', 'anomaly_percentage',
                        'predictions', 'anomaly_scores', 'feature_importance',
                        'detection_timestamp', 'model_used']
        for key in required_keys:
            self.assertIn(key, results)
        
        # Check data types and ranges
        self.assertEqual(results['total_records'], len(df))
        self.assertIsInstance(results['anomalies_detected'], int)
        self.assertIsInstance(results['anomaly_percentage'], float)
        self.assertIsInstance(results['predictions'], list)
        self.assertIsInstance(results['anomaly_scores'], list)
        self.assertEqual(len(results['predictions']), len(df))
        self.assertEqual(len(results['anomaly_scores']), len(df))
        self.assertEqual(results['model_used'], 'mock_detector')
    
    def test_generate_report(self):
        """Test comprehensive report generation"""
        csv_path = self._create_test_csv_file()
        df, metadata = self.processor.preprocess_csv_data(csv_path)
        detection_results = self.processor.detect_anomalies(df, metadata)
        
        file_info = {
            'file_id': 'test-123',
            'filename': 'test_data.csv',
            'file_size': os.path.getsize(csv_path),
            'analysis_timestamp': '2024-01-01T00:00:00',
            'analyzed_by': 'test_user'
        }
        
        report = self.processor.generate_report(file_info, metadata, detection_results)
        
        # Check report structure
        required_keys = ['report_id', 'timestamp', 'file_info', 'preprocessing_metadata',
                        'detection_results', 'summary_statistics', 'detailed_analysis',
                        'visualizations', 'recommendations', 'report_version']
        for key in required_keys:
            self.assertIn(key, report)
        
        # Check that report was saved
        report_files = list(Path(self.reports_dir).glob("anomaly_report_*.json"))
        self.assertEqual(len(report_files), 1)
        
        # Verify saved report content
        with open(report_files[0], 'r') as f:
            saved_report = json.load(f)
        self.assertEqual(saved_report['report_id'], report['report_id'])
    
    def test_get_report(self):
        """Test retrieving saved report"""
        # First generate a report
        csv_path = self._create_test_csv_file()
        df, metadata = self.processor.preprocess_csv_data(csv_path)
        detection_results = self.processor.detect_anomalies(df, metadata)
        
        file_info = {
            'file_id': 'test-123',
            'filename': 'test_data.csv',
            'file_size': os.path.getsize(csv_path),
            'analysis_timestamp': '2024-01-01T00:00:00',
            'analyzed_by': 'test_user'
        }
        
        original_report = self.processor.generate_report(file_info, metadata, detection_results)
        report_id = original_report['report_id']
        
        # Retrieve the report
        retrieved_report = self.processor.get_report(report_id)
        
        self.assertIsNotNone(retrieved_report)
        self.assertEqual(retrieved_report['report_id'], report_id)
    
    def test_get_nonexistent_report(self):
        """Test retrieving nonexistent report"""
        result = self.processor.get_report('nonexistent-id')
        self.assertIsNone(result)
    
    def test_list_reports(self):
        """Test listing all reports"""
        # Generate multiple reports
        for i in range(3):
            csv_path = self._create_test_csv_file(f'test_data_{i}.csv')
            df, metadata = self.processor.preprocess_csv_data(csv_path)
            detection_results = self.processor.detect_anomalies(df, metadata)
            
            file_info = {
                'file_id': f'test-{i}',
                'filename': f'test_data_{i}.csv',
                'file_size': os.path.getsize(csv_path),
                'analysis_timestamp': f'2024-01-0{i+1}T00:00:00',
                'analyzed_by': 'test_user'
            }
            
            self.processor.generate_report(file_info, metadata, detection_results)
        
        # List reports
        reports = self.processor.list_reports()
        
        self.assertEqual(len(reports), 3)
        
        # Check report summary structure
        for report in reports:
            required_keys = ['report_id', 'timestamp', 'file_name', 'total_records',
                           'anomalies_detected', 'anomaly_percentage']
            for key in required_keys:
                self.assertIn(key, report)
        
        # Check that reports are sorted by timestamp (newest first)
        timestamps = [report['timestamp'] for report in reports]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))


class TestCSVProcessorWithTrainedModel(unittest.TestCase):
    """Test CSV processor with mocked trained model"""
    
    def setUp(self):
        """Set up test environment with mock detector"""
        self.test_dir = tempfile.mkdtemp()
        
        # Create mock detector
        self.mock_detector = MagicMock(spec=SupervisedSOCDetector)
        self.mock_detector.models = {'random_forest': MagicMock()}
        self.mock_detector.scaler = MagicMock()
        self.mock_detector.feature_selector = MagicMock()
        self.mock_detector.feature_columns = [f'feature_{i}' for i in range(10)]
        
        # Configure mock model behavior
        mock_model = self.mock_detector.models['random_forest']
        mock_model.predict.return_value = np.array([0, 1, 0, 1, 0])
        mock_model.predict_proba.return_value = np.array([[0.8, 0.2], [0.3, 0.7], [0.9, 0.1], [0.4, 0.6], [0.7, 0.3]])
        mock_model.feature_importances_ = np.array([0.1, 0.2, 0.15, 0.05, 0.3, 0.05, 0.1, 0.03, 0.01, 0.01])
        
        # Configure scaler and feature selector
        self.mock_detector.scaler.transform.return_value = np.random.randn(5, 10)
        self.mock_detector.feature_selector.transform.return_value = np.random.randn(5, 8)
        
        # Create processor with mock detector
        self.processor = CSVProcessor(
            detector=self.mock_detector,
            upload_dir=os.path.join(self.test_dir, 'uploads'),
            reports_dir=os.path.join(self.test_dir, 'reports')
        )
        
        # Create sample data
        self.sample_data = pd.DataFrame({
            f'feature_{i}': np.random.randn(5) for i in range(15)
        })
    
    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_detect_anomalies_with_trained_model(self):
        """Test anomaly detection with trained model"""
        csv_path = os.path.join(self.test_dir, 'test.csv')
        self.sample_data.to_csv(csv_path, index=False)
        
        df, metadata = self.processor.preprocess_csv_data(csv_path)
        results = self.processor.detect_anomalies(df, metadata)
        
        # Verify trained model was used
        self.assertEqual(results['model_used'], 'random_forest')
        self.assertIn('feature_importance', results)
        self.assertIsInstance(results['feature_importance'], dict)
        
        # Verify model methods were called
        self.mock_detector.scaler.transform.assert_called_once()
        self.mock_detector.feature_selector.transform.assert_called_once()
        mock_model = self.mock_detector.models['random_forest']
        mock_model.predict.assert_called_once()
        mock_model.predict_proba.assert_called_once()


class TestCSVAPIIntegration(unittest.TestCase):
    """Integration tests for CSV API endpoints"""
    
    def setUp(self):
        """Set up test Flask app"""
        # This would require setting up a test Flask app
        # For now, we'll test the core functionality
        pass
    
    def test_file_upload_validation(self):
        """Test file upload validation logic"""
        # Test valid CSV file
        valid_extensions = ['.csv', '.CSV']
        for ext in valid_extensions:
            filename = f'test{ext}'
            self.assertTrue(filename.lower().endswith('.csv'))
        
        # Test invalid extensions
        invalid_extensions = ['.txt', '.xlsx', '.json', '.xml']
        for ext in invalid_extensions:
            filename = f'test{ext}'
            self.assertFalse(filename.lower().endswith('.csv'))
    
    def test_secure_filename_generation(self):
        """Test secure filename generation"""
        from werkzeug.utils import secure_filename
        import uuid
        
        # Test various filenames
        test_filenames = [
            'normal_file.csv',
            'file with spaces.csv',
            'file-with-dashes.csv',
            '../../../etc/passwd.csv',
            'file_with_unicode_éñ.csv'
        ]
        
        for filename in test_filenames:
            secure_name = secure_filename(filename)
            file_id = str(uuid.uuid4())
            safe_filename = f"{file_id}_{secure_name}"
            
            # Verify safe filename doesn't contain dangerous characters
            self.assertNotIn('..', safe_filename)
            self.assertNotIn('/', safe_filename)
            self.assertTrue(safe_filename.endswith('.csv'))


def run_csv_functionality_tests():
    """Run all CSV functionality tests"""
    print("="*60)
    print("RUNNING CSV FUNCTIONALITY TESTS")
    print("="*60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestCSVProcessor,
        TestCSVProcessorWithTrainedModel,
        TestCSVAPIIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "="*60)
    print("CSV FUNCTIONALITY TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASS' if success else 'FAIL'}")
    
    return success


if __name__ == "__main__":
    success = run_csv_functionality_tests()
    sys.exit(0 if success else 1)
