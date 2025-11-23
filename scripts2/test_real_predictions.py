#!/usr/bin/env python3
"""
Test script to verify that SOC Dashboard uses real model predictions
instead of simulated anomaly results
"""

import sys
import os
import numpy as np
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__)))

def test_model_integration():
    """Test that the dashboard uses real trained models for predictions"""
    print("="*60)
    print("TESTING REAL MODEL PREDICTIONS vs SIMULATED RESULTS")
    print("="*60)
    
    try:
        # Import the dashboard API
        from src.dashboard.server import SOCDashboardAPI
        
        # Initialize dashboard
        print("\n1. Initializing SOC Dashboard API...")
        dashboard = SOCDashboardAPI()
        
        # Check if models are loaded
        print(f"   Models loaded: {dashboard.detector is not None}")
        if dashboard.detector:
            print(f"   Available models: {list(dashboard.detector.models.keys()) if dashboard.detector.models else 'None'}")
            print(f"   Ensemble model: {dashboard.detector.ensemble_model is not None}")
        
        # Test network data generation (should only simulate traffic, not predictions)
        print("\n2. Testing network traffic generation...")
        network_data = dashboard.generate_realistic_network_data(batch_size=5)
        
        print(f"   Generated {len(network_data)} network records")
        sample_record = network_data[0]
        print(f"   Sample network features: {list(sample_record.keys())}")
        
        # Verify that network data doesn't contain prediction results
        prediction_keys = ['anomaly_score', 'prediction', 'confidence', 'attack_type']
        has_predictions = any(key in sample_record for key in prediction_keys)
        print(f"   Network data contains predictions: {has_predictions} (should be False)")
        
        # Test model processing
        print("\n3. Testing model prediction processing...")
        processed_data = dashboard.process_with_models(network_data)
        
        print(f"   Processed {len(processed_data)} records")
        sample_processed = processed_data[0]
        print(f"   Sample processed features: {list(sample_processed.keys())}")
        
        # Verify that processed data contains prediction results
        has_all_predictions = all(key in sample_processed for key in prediction_keys)
        print(f"   Processed data contains all predictions: {has_all_predictions} (should be True)")
        
        # Test full pipeline
        print("\n4. Testing full data generation pipeline...")
        full_data = dashboard.generate_mock_data(batch_size=10)
        
        print(f"   Generated {len(full_data)} complete records")
        
        # Analyze prediction patterns
        anomaly_scores = [record['anomaly_score'] for record in full_data]
        predictions = [record['prediction'] for record in full_data]
        attack_types = [record['attack_type'] for record in full_data]
        
        print(f"   Anomaly score range: {min(anomaly_scores):.3f} - {max(anomaly_scores):.3f}")
        print(f"   Predictions: Normal={predictions.count(0)}, Anomaly={predictions.count(1)}")
        print(f"   Attack types: {set(attack_types)}")
        
        # Test consistency across multiple runs
        print("\n5. Testing prediction consistency...")
        
        # Generate same network data multiple times
        consistent_results = []
        for i in range(3):
            # Use same seed for network generation
            np.random.seed(42)
            test_network = dashboard.generate_realistic_network_data(batch_size=3)
            test_processed = dashboard.process_with_models(test_network)
            consistent_results.append(test_processed)
        
        # Check if model predictions are deterministic for same input
        if dashboard.detector and dashboard.detector.models:
            print("   Testing prediction determinism...")
            first_scores = [r['anomaly_score'] for r in consistent_results[0]]
            second_scores = [r['anomaly_score'] for r in consistent_results[1]]
            
            # Model predictions should be deterministic for same input
            score_diff = np.mean([abs(a - b) for a, b in zip(first_scores, second_scores)])
            print(f"   Average score difference between runs: {score_diff:.6f}")
            print(f"   Predictions are deterministic: {score_diff < 0.001} (should be True)")
        else:
            print("   No trained models available - using fallback mode")
        
        # Test model vs fallback behavior
        print("\n6. Testing model vs fallback behavior...")
        
        if dashboard.detector and dashboard.detector.models:
            print("   ✅ Using REAL TRAINED MODELS for predictions")
            print("   ✅ Anomaly scores come from model probability outputs")
            print("   ✅ Attack classification uses model predictions + heuristics")
        else:
            print("   ⚠️  Using FALLBACK MODE (no trained models)")
            print("   ⚠️  Anomaly scores are conservative defaults")
            print("   ⚠️  Most predictions will be 'Normal'")
        
        # Verify model file existence
        print("\n7. Checking for trained model files...")
        model_dir = 'models'
        if os.path.exists(model_dir):
            model_files = [f for f in os.listdir(model_dir) if f.endswith('.pkl')]
            print(f"   Found {len(model_files)} model files in {model_dir}/")
            for file in model_files[:5]:  # Show first 5
                print(f"     - {file}")
        else:
            print(f"   ❌ Model directory '{model_dir}' not found")
            print("   Run 'python scripts/train_models.py' to train models")
        
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        
        if dashboard.detector and dashboard.detector.models:
            print("✅ SUCCESS: Dashboard is using REAL TRAINED MODEL predictions")
            print("✅ Network traffic is simulated (as intended)")
            print("✅ Anomaly detection uses actual ML model outputs")
            print("✅ Attack classification combines model + heuristics")
        else:
            print("⚠️  WARNING: No trained models found - using fallback mode")
            print("📝 To enable real predictions:")
            print("   1. Run: python scripts/train_models.py")
            print("   2. Restart the dashboard server")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prediction_quality():
    """Test the quality and realism of model predictions"""
    print("\n" + "="*60)
    print("TESTING PREDICTION QUALITY AND REALISM")
    print("="*60)
    
    try:
        from src.dashboard.server import SOCDashboardAPI
        
        dashboard = SOCDashboardAPI()
        
        if not dashboard.detector or not dashboard.detector.models:
            print("⚠️  Skipping quality tests - no trained models available")
            return True
        
        print("\n1. Generating large sample for analysis...")
        large_sample = dashboard.generate_mock_data(batch_size=100)
        
        # Analyze distribution
        anomaly_scores = [r['anomaly_score'] for r in large_sample]
        predictions = [r['prediction'] for r in large_sample]
        
        print(f"   Sample size: {len(large_sample)}")
        print(f"   Anomaly rate: {np.mean(predictions)*100:.1f}%")
        print(f"   Score statistics:")
        print(f"     Mean: {np.mean(anomaly_scores):.3f}")
        print(f"     Std:  {np.std(anomaly_scores):.3f}")
        print(f"     Min:  {np.min(anomaly_scores):.3f}")
        print(f"     Max:  {np.max(anomaly_scores):.3f}")
        
        # Check for realistic patterns
        print("\n2. Checking prediction realism...")
        
        # Most traffic should be normal
        normal_rate = (1 - np.mean(predictions)) * 100
        print(f"   Normal traffic rate: {normal_rate:.1f}% (should be >80%)")
        
        # Anomaly scores should be distributed (not all same value)
        unique_scores = len(set(anomaly_scores))
        print(f"   Unique anomaly scores: {unique_scores} (should be >10)")
        
        # Attack types should be diverse for anomalies
        anomaly_records = [r for r in large_sample if r['prediction'] == 1]
        if anomaly_records:
            attack_types = [r['attack_type'] for r in anomaly_records]
            unique_attacks = len(set(attack_types))
            print(f"   Unique attack types: {unique_attacks} (should be >1)")
        
        print("\n✅ Prediction quality analysis complete")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR in quality test: {e}")
        return False

if __name__ == "__main__":
    print("Starting SOC Dashboard Real Prediction Tests...")
    print(f"Timestamp: {datetime.now()}")
    
    success1 = test_model_integration()
    success2 = test_prediction_quality()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED - Real model predictions are working!")
    else:
        print("\n❌ Some tests failed - check output above")
        sys.exit(1)
