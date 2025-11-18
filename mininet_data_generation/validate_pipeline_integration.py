#!/usr/bin/env python3
"""
Pipeline Integration Validator
Ensures newly generated PCAP files work with freshly trained models
"""

import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from scapy.all import rdpcap, IP, TCP, UDP
except ImportError:
    print("❌ Scapy not installed. Run: pip install scapy")
    sys.exit(1)

class PipelineValidator:
    """Validate complete pipeline integration"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.data_dir = self.base_dir / "data_capture"
        self.models_dir = self.base_dir.parent / "models"
        self.pcap_dir = self.data_dir / "pcaps"
        self.processed_dir = self.data_dir / "processed"
        
        # Results tracking
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'tests_passed': 0,
            'tests_failed': 0,
            'details': []
        }
    
    def log_test(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        
        self.validation_results['details'].append({
            'test': test_name,
            'passed': passed,
            'details': details
        })
        
        if passed:
            self.validation_results['tests_passed'] += 1
        else:
            self.validation_results['tests_failed'] += 1
    
    def check_pcap_files(self):
        """Check if PCAP files were generated"""
        print("\n🔍 Checking PCAP file generation...")
        
        expected_files = [
            'normal_traffic.pcap',
            'syn_flood.pcap',
            'port_scan.pcap',
            'udp_flood.pcap',
            'http_flood.pcap'
        ]
        
        found_files = []
        missing_files = []
        
        for pcap_file in expected_files:
            pcap_path = self.pcap_dir / pcap_file
            if pcap_path.exists() and pcap_path.stat().st_size > 0:
                found_files.append(pcap_file)
                file_size = pcap_path.stat().st_size / (1024 * 1024)  # MB
                self.log_test(f"PCAP file {pcap_file}", True, f"Size: {file_size:.2f} MB")
            else:
                missing_files.append(pcap_file)
                self.log_test(f"PCAP file {pcap_file}", False, "File missing or empty")
        
        return len(found_files) > 0, found_files
    
    def extract_features_from_pcap(self, pcap_path, max_packets=1000):
        """Extract features from PCAP file for model prediction"""
        try:
            packets = rdpcap(str(pcap_path))
            features = []
            
            for i, packet in enumerate(packets[:max_packets]):
                if IP in packet:
                    feature_row = self.extract_packet_features(packet)
                    if feature_row:
                        features.append(feature_row)
            
            if features:
                df = pd.DataFrame(features)
                return df
            else:
                return None
                
        except Exception as e:
            print(f"    Error extracting features: {e}")
            return None
    
    def extract_packet_features(self, packet):
        """Extract features from a single packet"""
        try:
            features = {}
            
            # Basic IP features
            if IP in packet:
                features['src_ip'] = packet[IP].src
                features['dst_ip'] = packet[IP].dst
                features['protocol'] = packet[IP].proto
                features['packet_length'] = len(packet)
                features['ttl'] = packet[IP].ttl
                features['flags'] = packet[IP].flags
            
            # TCP features
            if TCP in packet:
                features['src_port'] = packet[TCP].sport
                features['dst_port'] = packet[TCP].dport
                features['tcp_flags'] = packet[TCP].flags
                features['window_size'] = packet[TCP].window
                features['tcp_seq'] = packet[TCP].seq
                features['tcp_ack'] = packet[TCP].ack
            else:
                features['src_port'] = 0
                features['dst_port'] = 0
                features['tcp_flags'] = 0
                features['window_size'] = 0
                features['tcp_seq'] = 0
                features['tcp_ack'] = 0
            
            # UDP features
            if UDP in packet:
                features['src_port'] = packet[UDP].sport
                features['dst_port'] = packet[UDP].dport
                features['udp_length'] = packet[UDP].len
            else:
                features['udp_length'] = 0
            
            # Additional computed features
            features['is_tcp'] = 1 if TCP in packet else 0
            features['is_udp'] = 1 if UDP in packet else 0
            features['is_http'] = 1 if (TCP in packet and (packet[TCP].dport == 80 or packet[TCP].sport == 80)) else 0
            features['is_https'] = 1 if (TCP in packet and (packet[TCP].dport == 443 or packet[TCP].sport == 443)) else 0
            features['is_dns'] = 1 if (UDP in packet and (packet[UDP].dport == 53 or packet[UDP].sport == 53)) else 0
            
            return features
            
        except Exception as e:
            return None
    
    def check_processed_data(self):
        """Check if processed CSV data exists"""
        print("\n🔍 Checking processed data files...")
        
        csv_files = list(self.processed_dir.glob("*.csv"))
        if csv_files:
            for csv_file in csv_files:
                try:
                    df = pd.read_csv(csv_file)
                    self.log_test(f"Processed CSV {csv_file.name}", True, 
                                f"Shape: {df.shape}, Columns: {len(df.columns)}")
                    return True, csv_files[0]
                except Exception as e:
                    self.log_test(f"Processed CSV {csv_file.name}", False, f"Error: {e}")
        else:
            self.log_test("Processed CSV files", False, "No CSV files found")
            return False, None
    
    def check_trained_models(self):
        """Check if models were trained and saved"""
        print("\n🔍 Checking trained models...")
        
        expected_models = [
            'random_forest_model.pkl',
            'xgboost_model.pkl',
            'feature_scaler.pkl',
            'label_encoder.pkl'
        ]
        
        found_models = {}
        
        for model_file in expected_models:
            model_path = self.models_dir / model_file
            if model_path.exists():
                try:
                    with open(model_path, 'rb') as f:
                        model = pickle.load(f)
                    found_models[model_file] = model
                    self.log_test(f"Model {model_file}", True, f"Type: {type(model).__name__}")
                except Exception as e:
                    self.log_test(f"Model {model_file}", False, f"Load error: {e}")
            else:
                self.log_test(f"Model {model_file}", False, "File not found")
        
        return len(found_models) >= 2, found_models  # At least 2 models needed
    
    def test_model_prediction(self, models, pcap_files):
        """Test model prediction on newly generated PCAP data"""
        print("\n🔍 Testing model predictions on new PCAP data...")
        
        if 'random_forest_model.pkl' not in models:
            self.log_test("Model prediction test", False, "No Random Forest model found")
            return False
        
        rf_model = models['random_forest_model.pkl']
        scaler = models.get('feature_scaler.pkl', None)
        
        # Test prediction on each PCAP file
        prediction_results = {}
        
        for pcap_file in pcap_files:
            pcap_path = self.pcap_dir / pcap_file
            
            # Extract features
            df = self.extract_features_from_pcap(pcap_path, max_packets=100)
            
            if df is not None and len(df) > 0:
                try:
                    # Prepare features for prediction
                    feature_columns = self.get_expected_feature_columns()
                    
                    # Align features with model expectations
                    aligned_features = self.align_features(df, feature_columns)
                    
                    if aligned_features is not None:
                        # Scale features if scaler available
                        if scaler:
                            scaled_features = scaler.transform(aligned_features)
                        else:
                            scaled_features = aligned_features
                        
                        # Make predictions
                        predictions = rf_model.predict(scaled_features)
                        probabilities = rf_model.predict_proba(scaled_features)
                        
                        # Calculate statistics
                        anomaly_rate = np.mean(predictions)
                        avg_confidence = np.mean(np.max(probabilities, axis=1))
                        
                        prediction_results[pcap_file] = {
                            'samples': len(predictions),
                            'anomaly_rate': anomaly_rate,
                            'avg_confidence': avg_confidence
                        }
                        
                        expected_anomaly = 'normal' not in pcap_file.lower()
                        test_passed = (anomaly_rate > 0.5) == expected_anomaly
                        
                        self.log_test(f"Prediction on {pcap_file}", test_passed,
                                    f"Anomaly rate: {anomaly_rate:.2f}, Confidence: {avg_confidence:.2f}")
                    else:
                        self.log_test(f"Prediction on {pcap_file}", False, "Feature alignment failed")
                        
                except Exception as e:
                    self.log_test(f"Prediction on {pcap_file}", False, f"Prediction error: {e}")
            else:
                self.log_test(f"Prediction on {pcap_file}", False, "No features extracted")
        
        return len(prediction_results) > 0
    
    def get_expected_feature_columns(self):
        """Get expected feature columns for model"""
        # Standard network features expected by the model
        return [
            'protocol', 'packet_length', 'ttl', 'flags',
            'src_port', 'dst_port', 'tcp_flags', 'window_size',
            'tcp_seq', 'tcp_ack', 'udp_length',
            'is_tcp', 'is_udp', 'is_http', 'is_https', 'is_dns'
        ]
    
    def align_features(self, df, expected_columns):
        """Align extracted features with model expectations"""
        try:
            # Create aligned dataframe
            aligned_df = pd.DataFrame()
            
            for col in expected_columns:
                if col in df.columns:
                    aligned_df[col] = df[col]
                else:
                    # Fill missing columns with appropriate defaults
                    if col in ['protocol', 'packet_length', 'ttl', 'flags', 'src_port', 'dst_port',
                              'tcp_flags', 'window_size', 'tcp_seq', 'tcp_ack', 'udp_length']:
                        aligned_df[col] = 0
                    else:  # Boolean features
                        aligned_df[col] = 0
            
            # Handle any remaining NaN values
            aligned_df = aligned_df.fillna(0)
            
            return aligned_df.values
            
        except Exception as e:
            print(f"    Feature alignment error: {e}")
            return None
    
    def test_dashboard_integration(self):
        """Test dashboard integration readiness"""
        print("\n🔍 Testing dashboard integration readiness...")
        
        # Check if integration script exists
        integration_script = self.base_dir / "integration" / "integrate_dashboard.py"
        if integration_script.exists():
            self.log_test("Integration script exists", True, str(integration_script))
        else:
            self.log_test("Integration script exists", False, "integrate_dashboard.py not found")
        
        # Check if models directory is accessible from parent
        models_accessible = self.models_dir.exists()
        self.log_test("Models directory accessible", models_accessible, str(self.models_dir))
        
        return integration_script.exists() and models_accessible
    
    def run_validation(self):
        """Run complete pipeline validation"""
        print("="*60)
        print("PIPELINE INTEGRATION VALIDATION")
        print("="*60)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. Check PCAP files
        pcap_ok, pcap_files = self.check_pcap_files()
        
        # 2. Check processed data
        processed_ok, csv_file = self.check_processed_data()
        
        # 3. Check trained models
        models_ok, models = self.check_trained_models()
        
        # 4. Test model predictions
        if pcap_ok and models_ok:
            prediction_ok = self.test_model_prediction(models, pcap_files)
        else:
            prediction_ok = False
            self.log_test("Model prediction test", False, "Prerequisites not met")
        
        # 5. Test dashboard integration readiness
        integration_ok = self.test_dashboard_integration()
        
        # Summary
        print("\n" + "="*60)
        print("VALIDATION SUMMARY")
        print("="*60)
        
        total_tests = self.validation_results['tests_passed'] + self.validation_results['tests_failed']
        pass_rate = (self.validation_results['tests_passed'] / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Tests Passed: {self.validation_results['tests_passed']}")
        print(f"Tests Failed: {self.validation_results['tests_failed']}")
        print(f"Pass Rate: {pass_rate:.1f}%")
        
        # Overall status
        pipeline_ready = (pcap_ok and models_ok and prediction_ok and integration_ok)
        
        if pipeline_ready:
            print("\n🎉 PIPELINE INTEGRATION: READY")
            print("✅ PCAP files generated successfully")
            print("✅ Models trained and functional")
            print("✅ Predictions working on new data")
            print("✅ Dashboard integration ready")
        else:
            print("\n⚠️  PIPELINE INTEGRATION: ISSUES FOUND")
            print("Please review failed tests above")
        
        # Save validation report
        report_path = self.base_dir / "validation_report.json"
        with open(report_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2)
        
        print(f"\n📄 Validation report saved: {report_path}")
        
        return pipeline_ready

def main():
    """Main validation function"""
    validator = PipelineValidator()
    success = validator.run_validation()
    
    if success:
        print("\n🚀 Ready to start dashboard and test real-time detection!")
        print("\nNext steps:")
        print("1. cd .. && python3 scripts/start_dashboard.py")
        print("2. Access dashboard at http://VM_IP:5000")
        print("3. Test real-time detection with simulation")
    else:
        print("\n🔧 Please fix the issues above before proceeding")
        sys.exit(1)

if __name__ == "__main__":
    main()
