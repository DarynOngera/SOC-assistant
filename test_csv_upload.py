#!/usr/bin/env python3
"""
Test CSV upload functionality to verify the fix
"""

import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from src.utils.csv_processor import CSVProcessor

def create_test_csv():
    """Create a test CSV file for upload testing"""
    # Generate sample network traffic data
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'src_ip': [f"192.168.1.{np.random.randint(1, 255)}" for _ in range(n_samples)],
        'dst_ip': [f"10.0.0.{np.random.randint(1, 255)}" for _ in range(n_samples)],
        'src_port': np.random.randint(1024, 65535, n_samples),
        'dst_port': np.random.choice([80, 443, 22, 21, 25, 53], n_samples),
        'protocol': np.random.choice(['TCP', 'UDP', 'ICMP'], n_samples),
        'packet_size': np.random.normal(1500, 500, n_samples),
        'duration': np.random.exponential(2, n_samples),
        'bytes_sent': np.random.lognormal(8, 2, n_samples),
        'bytes_received': np.random.lognormal(7, 2, n_samples),
        'flags': np.random.choice(['SYN', 'ACK', 'FIN', 'RST'], n_samples)
    }
    
    df = pd.DataFrame(data)
    test_file = "test_sample.csv"
    df.to_csv(test_file, index=False)
    print(f"Created test CSV file: {test_file}")
    return test_file

def test_csv_processor():
    """Test the CSV processor functionality"""
    print("Testing CSV Processor...")
    
    # Create test CSV
    test_file = create_test_csv()
    
    try:
        # Initialize CSV processor
        processor = CSVProcessor(
            detector=None,  # No detector for this test
            upload_dir="test_uploads",
            reports_dir="test_reports"
        )
        
        # Test file validation
        print("\n1. Testing file validation...")
        is_valid, message = processor.validate_csv_file(test_file)
        print(f"Validation result: {is_valid}, Message: {message}")
        
        if not is_valid:
            print("❌ File validation failed")
            return False
        
        # Test preprocessing
        print("\n2. Testing data preprocessing...")
        df, metadata = processor.preprocess_csv_data(test_file, sample_size=500)
        print(f"Preprocessed shape: {df.shape}")
        print(f"Metadata keys: {list(metadata.keys())}")
        
        # Test anomaly detection (should use mock model)
        print("\n3. Testing anomaly detection...")
        detection_results = processor.detect_anomalies(df, metadata)
        print(f"Detection method: {detection_results.get('method', 'unknown')}")
        print(f"Total records: {detection_results.get('total_records', 0)}")
        print(f"Anomalies detected: {detection_results.get('anomalies_detected', 0)}")
        print(f"Anomaly percentage: {detection_results.get('anomaly_percentage', 0)}%")
        
        # Test report generation
        print("\n4. Testing report generation...")
        file_info = {
            'file_id': 'test-123',
            'filename': 'test_sample.csv',
            'file_size': os.path.getsize(test_file),
            'upload_timestamp': '2024-01-01T00:00:00',
            'uploaded_by': 'test_user'
        }
        
        report = processor.generate_report(file_info, metadata, detection_results)
        print(f"Report ID: {report.get('report_id', 'unknown')}")
        print(f"Report sections: {list(report.keys())}")
        
        print("\n✅ All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
        
        # Clean up test directories
        import shutil
        for dir_name in ["test_uploads", "test_reports"]:
            if os.path.exists(dir_name):
                shutil.rmtree(dir_name)

if __name__ == "__main__":
    success = test_csv_processor()
    sys.exit(0 if success else 1)
