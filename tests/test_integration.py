#!/usr/bin/env python3
"""
Test Model-Dashboard Integration
Comprehensive test to verify trained models work with dashboard
"""

import os
import sys
import time
import numpy as np
import pandas as pd
from datetime import datetime

# Add current directory to path
sys.path.append('.')

from src.models.supervised_trainer import SupervisedSOCDetector
from src.dashboard.server import SOCDashboardAPI

def test_model_loading():
    """Test if models can be loaded successfully"""
    print("="*60)
    print("TESTING MODEL LOADING")
    print("="*60)
    
    detector = SupervisedSOCDetector()
    
    try:
        detector.load_models('models')
        print("✓ Models loaded successfully")
        
        # Check what was loaded
        print(f"✓ Individual models: {list(detector.models.keys())}")
        print(f"✓ Ensemble model: {'Available' if detector.ensemble_model else 'Not available'}")
        print(f"✓ Feature columns: {len(detector.feature_columns) if detector.feature_columns else 0}")
        
        return True, detector
    except Exception as e:
        print(f"✗ Model loading failed: {e}")
        return False, None

def test_feature_template():
    """Test feature template generation"""
    print("\n" + "="*60)
    print("TESTING FEATURE TEMPLATE")
    print("="*60)
    
    detector = SupervisedSOCDetector()
    
    try:
        detector.load_models('models')
        template = detector.get_feature_template()
        
        print(f"✓ Feature template generated with {len(template)} features")
        print("✓ Sample features:")
        for i, (key, value) in enumerate(list(template.items())[:10]):
            print(f"   {key}: {value}")
        if len(template) > 10:
            print(f"   ... and {len(template) - 10} more features")
        
        return True, template
    except Exception as e:
        print(f"✗ Feature template generation failed: {e}")
        return False, None

def test_single_prediction():
    """Test single record prediction"""
    print("\n" + "="*60)
    print("TESTING SINGLE PREDICTION")
    print("="*60)
    
    detector = SupervisedSOCDetector()
    
    try:
        detector.load_models('models')
        template = detector.get_feature_template()
        
        # Create test record with some variations
        test_record = template.copy()
        test_record.update({
            'dur': 1.5,
            'spkts': 50,
            'dpkts': 30,
            'rate': 75.0,
            'proto': 'tcp',
            'service': 'http'
        })
        
        result = detector.predict_single(test_record)
        
        print("✓ Single prediction successful")
        print(f"   Prediction: {result['prediction']}")
        print(f"   Anomaly Score: {result['anomaly_score']:.4f}")
        print(f"   Confidence: {result['confidence']:.4f}")
        print(f"   Is Anomaly: {result['is_anomaly']}")
        
        return True, result
    except Exception as e:
        print(f"✗ Single prediction failed: {e}")
        return False, None

def test_batch_prediction():
    """Test batch prediction"""
    print("\n" + "="*60)
    print("TESTING BATCH PREDICTION")
    print("="*60)
    
    detector = SupervisedSOCDetector()
    
    try:
        detector.load_models('models')
        template = detector.get_feature_template()
        
        # Create batch of test records
        batch_size = 5
        test_batch = []
        for i in range(batch_size):
            record = template.copy()
            record.update({
                'dur': np.random.exponential(1.0),
                'spkts': int(np.random.poisson(20)),
                'dpkts': int(np.random.poisson(15)),
                'rate': float(np.random.exponential(50)),
                'proto': np.random.choice(['tcp', 'udp']),
                'service': np.random.choice(['http', 'https', 'ftp', '-'])
            })
            test_batch.append(record)
        
        results = detector.predict_batch(test_batch)
        
        print(f"✓ Batch prediction successful for {len(results)} records")
        
        anomalies = sum(1 for r in results if r['is_anomaly'])
        avg_score = np.mean([r['anomaly_score'] for r in results])
        
        print(f"   Anomalies detected: {anomalies}/{len(results)}")
        print(f"   Average anomaly score: {avg_score:.4f}")
        
        return True, results
    except Exception as e:
        print(f"✗ Batch prediction failed: {e}")
        return False, None

def test_dashboard_integration():
    """Test dashboard integration with models"""
    print("\n" + "="*60)
    print("TESTING DASHBOARD INTEGRATION")
    print("="*60)
    
    try:
        dashboard = SOCDashboardAPI()
        
        print(f"✓ Dashboard initialized")
        print(f"   Models loaded: {dashboard.models_loaded}")
        print(f"   Feature template available: {dashboard.feature_template is not None}")
        
        # Test data generation
        data_batch = dashboard.generate_realistic_network_data(batch_size=3)
        print(f"✓ Generated {len(data_batch)} realistic network records")
        
        # Test processing with models
        processed_data = dashboard.process_with_models(data_batch)
        print(f"✓ Processed {len(processed_data)} records through models")
        
        # Test alert generation
        alerts = dashboard.process_alerts(data_batch)
        print(f"✓ Generated {len(alerts)} alerts")
        
        # Show sample results
        if processed_data:
            sample = processed_data[0]
            print("✓ Sample processed record:")
            print(f"   Anomaly Score: {sample.get('anomaly_score', 'N/A')}")
            print(f"   Prediction: {sample.get('prediction', 'N/A')}")
            print(f"   Attack Type: {sample.get('attack_type', 'N/A')}")
        
        return True, dashboard
    except Exception as e:
        print(f"✗ Dashboard integration failed: {e}")
        return False, None

def test_real_data_compatibility():
    """Test compatibility with real training data format"""
    print("\n" + "="*60)
    print("TESTING REAL DATA COMPATIBILITY")
    print("="*60)
    
    try:
        # Load a small sample from training data
        train_file = 'data/train.csv'
        if not os.path.exists(train_file):
            print("⚠ Training data not found, skipping real data test")
            return True, None
        
        # Read first few rows
        df_sample = pd.read_csv(train_file, nrows=3)
        print(f"✓ Loaded {len(df_sample)} sample records from training data")
        
        detector = SupervisedSOCDetector()
        detector.load_models('models')
        
        # Convert to dictionary format
        test_records = []
        for _, row in df_sample.iterrows():
            record = row.to_dict()
            # Remove label columns for prediction
            record.pop('label', None)
            record.pop('attack_cat', None)
            record.pop('id', None)
            test_records.append(record)
        
        # Test prediction
        results = detector.predict_batch(test_records)
        print(f"✓ Successfully predicted on {len(results)} real data samples")
        
        for i, result in enumerate(results):
            print(f"   Sample {i+1}: Score={result['anomaly_score']:.4f}, Anomaly={result['is_anomaly']}")
        
        return True, results
    except Exception as e:
        print(f"✗ Real data compatibility test failed: {e}")
        return False, None

def main():
    """Run all integration tests"""
    print("MODEL-DASHBOARD INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Model Loading", test_model_loading),
        ("Feature Template", test_feature_template),
        ("Single Prediction", test_single_prediction),
        ("Batch Prediction", test_batch_prediction),
        ("Dashboard Integration", test_dashboard_integration),
        ("Real Data Compatibility", test_real_data_compatibility)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success, data = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Model-Dashboard integration is working!")
    else:
        print("⚠ Some tests failed - Check the output above for details")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
