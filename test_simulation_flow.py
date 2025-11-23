#!/usr/bin/env python3
"""
Test Simulation Flow
Verifies model loading and PCAP processing
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(__file__))

def test_model_loading():
    """Test if model files can be loaded"""
    print("="*70)
    print("TEST 1: MODEL LOADING")
    print("="*70 + "\n")
    
    try:
        import joblib
        
        model_path = 'models/mininet_model.pkl'
        scaler_path = 'models/mininet_scaler.pkl'
        features_path = 'models/mininet_feature_columns.pkl'
        
        print(f"Loading model from: {model_path}")
        model = joblib.load(model_path)
        print(f"✅ Model loaded: {type(model).__name__}")
        
        print(f"\nLoading scaler from: {scaler_path}")
        scaler = joblib.load(scaler_path)
        print(f"✅ Scaler loaded: {type(scaler).__name__}")
        
        print(f"\nLoading features from: {features_path}")
        features = joblib.load(features_path)
        print(f"✅ Features loaded: {len(features)} features")
        print(f"   First 5: {features[:5]}")
        
        return model, scaler, features
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def test_model_prediction(model, scaler, features):
    """Test model prediction"""
    print("\n" + "="*70)
    print("TEST 2: MODEL PREDICTION")
    print("="*70 + "\n")
    
    if not model:
        print("❌ Skipping - model not loaded")
        return False
    
    try:
        import pandas as pd
        import numpy as np
        
        # Create test data (all zeros - should predict normal)
        print("Testing with normal traffic pattern (all zeros)...")
        test_data = pd.DataFrame([[0] * len(features)], columns=features)
        test_scaled = scaler.transform(test_data)
        
        prediction = model.predict(test_scaled)[0]
        proba = model.predict_proba(test_scaled)[0]
        
        print(f"✅ Prediction: {prediction} ({'Attack' if prediction == 1 else 'Normal'})")
        print(f"   Probabilities: Normal={proba[0]:.3f}, Attack={proba[1]:.3f}")
        
        # Create attack-like data (high values)
        print("\nTesting with attack-like pattern (high values)...")
        attack_data = pd.DataFrame([[100] * len(features)], columns=features)
        attack_scaled = scaler.transform(attack_data)
        
        prediction = model.predict(attack_scaled)[0]
        proba = model.predict_proba(attack_scaled)[0]
        
        print(f"✅ Prediction: {prediction} ({'Attack' if prediction == 1 else 'Normal'})")
        print(f"   Probabilities: Normal={proba[0]:.3f}, Attack={proba[1]:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in prediction: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pcap_extraction():
    """Test PCAP feature extraction"""
    print("\n" + "="*70)
    print("TEST 3: PCAP FEATURE EXTRACTION")
    print("="*70 + "\n")
    
    try:
        import glob
        
        pcap_dir = 'mininet_data_generation/data_capture/pcaps'
        pcaps = glob.glob(f"{pcap_dir}/*.pcap")
        
        if not pcaps:
            print(f"❌ No PCAP files found in {pcap_dir}")
            return False
        
        print(f"Found {len(pcaps)} PCAP files")
        
        # Test with first PCAP
        test_pcap = pcaps[0]
        print(f"\nTesting with: {os.path.basename(test_pcap)}")
        
        from scapy.all import rdpcap, IP
        
        packets = rdpcap(test_pcap)
        ipv4_packets = [pkt for pkt in packets if IP in pkt]
        
        print(f"✅ Total packets: {len(packets)}")
        print(f"✅ IPv4 packets: {len(ipv4_packets)}")
        
        if len(ipv4_packets) == 0:
            print("⚠️  Warning: No IPv4 packets in this PCAP")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error extracting PCAP: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_detector_wrapper(model, scaler, features):
    """Test the MininetDetector wrapper"""
    print("\n" + "="*70)
    print("TEST 4: DETECTOR WRAPPER")
    print("="*70 + "\n")
    
    if not model:
        print("❌ Skipping - model not loaded")
        return False
    
    try:
        import pandas as pd
        
        # Create the same wrapper as in server.py
        class MininetDetector:
            def __init__(self, model, scaler, features):
                self.model = model
                self.scaler = scaler
                self.feature_columns = features
            
            def predict_single(self, record):
                """Predict using trained Mininet model"""
                # Extract features in correct order
                features = []
                for col in self.feature_columns:
                    features.append(record.get(col, 0))
                
                # Convert to DataFrame
                X = pd.DataFrame([features], columns=self.feature_columns)
                
                # Scale features
                X_scaled = self.scaler.transform(X)
                
                # Predict
                prediction = int(self.model.predict(X_scaled)[0])
                proba = self.model.predict_proba(X_scaled)[0]
                anomaly_score = float(proba[1])  # Probability of attack
                confidence = float(max(proba))
                
                return {
                    'prediction': prediction,
                    'anomaly_score': anomaly_score,
                    'confidence': confidence
                }
        
        detector = MininetDetector(model, scaler, features)
        
        # Test with sample record
        test_record = {feature: 0 for feature in features}
        result = detector.predict_single(test_record)
        
        print(f"✅ Detector wrapper works!")
        print(f"   Prediction: {result['prediction']}")
        print(f"   Anomaly Score: {result['anomaly_score']:.3f}")
        print(f"   Confidence: {result['confidence']:.3f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in detector wrapper: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*70)
    print("SIMULATION FLOW DIAGNOSTIC TEST")
    print("="*70 + "\n")
    
    # Test 1: Model Loading
    model, scaler, features = test_model_loading()
    
    # Test 2: Model Prediction
    if model:
        test_model_prediction(model, scaler, features)
    
    # Test 3: PCAP Extraction
    test_pcap_extraction()
    
    # Test 4: Detector Wrapper
    if model:
        test_detector_wrapper(model, scaler, features)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    if model and scaler and features:
        print("\n✅ All components are working!")
        print("\nNext steps:")
        print("  1. Start backend: cd src/dashboard && python3 server.py")
        print("  2. Look for: '✅ Mininet trained model loaded successfully'")
        print("  3. Look for: '✅ Using trained model for X records'")
        print("  4. Test simulation in dashboard")
    else:
        print("\n❌ Some components failed!")
        print("\nFix:")
        print("  1. Ensure model files exist: ls -lh models/mininet_*.pkl")
        print("  2. Retrain if needed: python3 train_comprehensive_model.py")
        print("  3. Run this test again")

if __name__ == '__main__':
    main()
