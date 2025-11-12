#!/usr/bin/env python3
"""
Real-Time Attack Simulation and Model Testing
Tests trained models against live Mininet attacks
"""

import os
import sys
import time
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict
from scapy.all import sniff, IP, TCP, UDP, ICMP
from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.log import setLogLevel, info
import threading
import queue

class RealTimeDetector:
    """Real-time intrusion detection using trained models"""
    
    def __init__(self, model_dir='../../models'):
        self.model_dir = model_dir
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.feature_columns = None
        self.metadata = None
        
        # Flow tracking
        self.flows = defaultdict(lambda: {
            'packets': [],
            'bytes': 0,
            'start_time': None,
            'end_time': None,
            'syn_count': 0,
            'fin_count': 0,
            'rst_count': 0,
            'psh_count': 0,
            'ack_count': 0,
            'urg_count': 0,
            'packet_sizes': [],
            'inter_arrival_times': [],
            'protocol': None,
            'src_port': None,
            'dst_port': None
        })
        
        # Detection results
        self.detections = []
        self.packet_queue = queue.Queue()
        
        self.load_models()
    
    def load_models(self):
        """Load trained models and preprocessors"""
        print("Loading trained models...")
        
        try:
            # Load ensemble model
            model_path = os.path.join(self.model_dir, 'mininet_ensemble_model.pkl')
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                print(f"✓ Loaded ensemble model")
            else:
                # Fallback to random forest
                model_path = os.path.join(self.model_dir, 'mininet_random_forest_model.pkl')
                if os.path.exists(model_path):
                    self.model = joblib.load(model_path)
                    print(f"✓ Loaded random forest model")
                else:
                    raise FileNotFoundError("No trained models found")
            
            # Load scaler
            scaler_path = os.path.join(self.model_dir, 'mininet_scaler.pkl')
            self.scaler = joblib.load(scaler_path)
            print(f"✓ Loaded scaler")
            
            # Load feature selector
            selector_path = os.path.join(self.model_dir, 'mininet_feature_selector.pkl')
            if os.path.exists(selector_path):
                self.feature_selector = joblib.load(selector_path)
                print(f"✓ Loaded feature selector")
            
            # Load feature columns
            features_path = os.path.join(self.model_dir, 'mininet_feature_columns.pkl')
            self.feature_columns = joblib.load(features_path)
            print(f"✓ Loaded feature columns ({len(self.feature_columns)} features)")
            
            # Load metadata
            metadata_path = os.path.join(self.model_dir, 'mininet_model_metadata.pkl')
            if os.path.exists(metadata_path):
                self.metadata = joblib.load(metadata_path)
                print(f"✓ Loaded metadata")
            
            print("Models loaded successfully!")
            
        except Exception as e:
            print(f"✗ Error loading models: {e}")
            sys.exit(1)
    
    def get_flow_key(self, packet):
        """Generate flow key from packet"""
        if IP in packet:
            src_ip = packet[IP].src
            dst_ip = packet[IP].dst
            protocol = packet[IP].proto
            
            src_port = 0
            dst_port = 0
            
            if TCP in packet:
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
            elif UDP in packet:
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
            
            flow_key = tuple(sorted([
                (src_ip, src_port),
                (dst_ip, dst_port)
            ]))
            
            return (flow_key, protocol)
        
        return None
    
    def extract_flow_features(self, flow):
        """Extract features from flow (same as training)"""
        features = {}
        
        duration = flow['end_time'] - flow['start_time'] if flow['end_time'] else 0
        features['duration'] = duration
        features['packet_count'] = len(flow['packets'])
        features['byte_count'] = flow['bytes']
        
        if duration > 0:
            features['packets_per_sec'] = len(flow['packets']) / duration
            features['bytes_per_sec'] = flow['bytes'] / duration
        else:
            features['packets_per_sec'] = 0
            features['bytes_per_sec'] = 0
        
        if flow['packet_sizes']:
            features['mean_packet_size'] = np.mean(flow['packet_sizes'])
            features['std_packet_size'] = np.std(flow['packet_sizes'])
            features['min_packet_size'] = np.min(flow['packet_sizes'])
            features['max_packet_size'] = np.max(flow['packet_sizes'])
        else:
            features['mean_packet_size'] = 0
            features['std_packet_size'] = 0
            features['min_packet_size'] = 0
            features['max_packet_size'] = 0
        
        if flow['inter_arrival_times']:
            features['mean_iat'] = np.mean(flow['inter_arrival_times'])
            features['std_iat'] = np.std(flow['inter_arrival_times'])
            features['min_iat'] = np.min(flow['inter_arrival_times'])
            features['max_iat'] = np.max(flow['inter_arrival_times'])
        else:
            features['mean_iat'] = 0
            features['std_iat'] = 0
            features['min_iat'] = 0
            features['max_iat'] = 0
        
        features['syn_count'] = flow['syn_count']
        features['fin_count'] = flow['fin_count']
        features['rst_count'] = flow['rst_count']
        features['psh_count'] = flow['psh_count']
        features['ack_count'] = flow['ack_count']
        features['urg_count'] = flow['urg_count']
        
        if features['packet_count'] > 0:
            features['syn_ratio'] = flow['syn_count'] / features['packet_count']
            features['fin_ratio'] = flow['fin_count'] / features['packet_count']
            features['rst_ratio'] = flow['rst_count'] / features['packet_count']
        else:
            features['syn_ratio'] = 0
            features['fin_ratio'] = 0
            features['rst_ratio'] = 0
        
        features['protocol'] = flow['protocol'] if flow['protocol'] else 0
        features['src_port'] = flow['src_port'] if flow['src_port'] else 0
        features['dst_port'] = flow['dst_port'] if flow['dst_port'] else 0
        
        well_known_ports = [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 8080]
        features['is_well_known_port'] = 1 if (
            flow['src_port'] in well_known_ports or 
            flow['dst_port'] in well_known_ports
        ) else 0
        
        return features
    
    def predict_flow(self, flow_features):
        """Predict if flow is malicious"""
        try:
            # Create DataFrame with all required features
            df = pd.DataFrame([flow_features])
            
            # Ensure all feature columns exist
            for col in self.feature_columns:
                if col not in df.columns:
                    df[col] = 0
            
            # Select only training features
            df = df[self.feature_columns]
            
            # Handle missing/infinite values
            df = df.fillna(0)
            df = df.replace([np.inf, -np.inf], 0)
            
            # Scale features
            X_scaled = self.scaler.transform(df)
            
            # Feature selection
            if self.feature_selector:
                X_selected = self.feature_selector.transform(X_scaled)
            else:
                X_selected = X_scaled
            
            # Predict
            prediction = self.model.predict(X_selected)[0]
            probability = self.model.predict_proba(X_selected)[0]
            
            return {
                'prediction': int(prediction),
                'probability': float(probability[1]),  # Probability of attack
                'label': 'Attack' if prediction == 1 else 'Normal'
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {
                'prediction': 0,
                'probability': 0.0,
                'label': 'Error'
            }
    
    def packet_callback(self, packet):
        """Callback for packet capture"""
        if IP not in packet:
            return
        
        flow_key = self.get_flow_key(packet)
        if flow_key is None:
            return
        
        flow = self.flows[flow_key]
        
        # Update flow
        if flow['start_time'] is None:
            flow['start_time'] = float(packet.time)
            flow['protocol'] = packet[IP].proto
            
            if TCP in packet:
                flow['src_port'] = packet[TCP].sport
                flow['dst_port'] = packet[TCP].dport
            elif UDP in packet:
                flow['src_port'] = packet[UDP].sport
                flow['dst_port'] = packet[UDP].dport
        
        flow['end_time'] = float(packet.time)
        flow['packets'].append(packet)
        flow['bytes'] += len(packet)
        flow['packet_sizes'].append(len(packet))
        
        if len(flow['packets']) > 1:
            iat = float(packet.time) - float(flow['packets'][-2].time)
            flow['inter_arrival_times'].append(iat)
        
        if TCP in packet:
            tcp_flags = packet[TCP].flags
            if tcp_flags & 0x02:
                flow['syn_count'] += 1
            if tcp_flags & 0x01:
                flow['fin_count'] += 1
            if tcp_flags & 0x04:
                flow['rst_count'] += 1
            if tcp_flags & 0x08:
                flow['psh_count'] += 1
            if tcp_flags & 0x10:
                flow['ack_count'] += 1
            if tcp_flags & 0x20:
                flow['urg_count'] += 1
        
        # Analyze flow every 10 packets
        if len(flow['packets']) % 10 == 0:
            self.analyze_flow(flow_key, flow)
    
    def analyze_flow(self, flow_key, flow):
        """Analyze flow and detect attacks"""
        features = self.extract_flow_features(flow)
        result = self.predict_flow(features)
        
        if result['prediction'] == 1:  # Attack detected
            detection = {
                'timestamp': datetime.now().isoformat(),
                'flow_key': str(flow_key),
                'prediction': result['label'],
                'probability': result['probability'],
                'packet_count': len(flow['packets']),
                'byte_count': flow['bytes'],
                'duration': flow['end_time'] - flow['start_time'] if flow['end_time'] else 0
            }
            
            self.detections.append(detection)
            
            print(f"\n🚨 ATTACK DETECTED!")
            print(f"   Probability: {result['probability']:.2%}")
            print(f"   Packets: {detection['packet_count']}")
            print(f"   Bytes: {detection['byte_count']}")
            print(f"   Duration: {detection['duration']:.2f}s")
    
    def start_monitoring(self, interface='any', duration=60):
        """Start real-time monitoring"""
        print(f"\n{'='*60}")
        print("REAL-TIME ATTACK DETECTION")
        print(f"{'='*60}")
        print(f"Interface: {interface}")
        print(f"Duration: {duration}s")
        print(f"Monitoring started at {datetime.now()}")
        print(f"{'='*60}\n")
        
        # Start packet capture
        try:
            sniff(
                iface=interface,
                prn=self.packet_callback,
                timeout=duration,
                store=False,
                filter='ip'
            )
        except Exception as e:
            print(f"Capture error: {e}")
        
        print(f"\n{'='*60}")
        print("MONITORING COMPLETED")
        print(f"{'='*60}")
        print(f"Total flows analyzed: {len(self.flows)}")
        print(f"Attacks detected: {len(self.detections)}")
        
        if self.detections:
            print("\nDetection Summary:")
            for i, det in enumerate(self.detections, 1):
                print(f"{i}. {det['timestamp']} - Probability: {det['probability']:.2%}")
        
        print(f"{'='*60}\n")
        
        return self.detections

def run_simulation_with_detection():
    """Run Mininet simulation with real-time detection"""
    print("="*60)
    print("MININET ATTACK SIMULATION WITH REAL-TIME DETECTION")
    print("="*60)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        sys.exit(1)
    
    # Create detector
    detector = RealTimeDetector()
    
    # Start monitoring in background thread
    monitor_thread = threading.Thread(
        target=detector.start_monitoring,
        args=('any', 120)
    )
    monitor_thread.start()
    
    # Wait a bit for monitoring to start
    time.sleep(2)
    
    # Import and run attack simulation
    sys.path.append('../topology')
    from generate_attack_traffic import AttackTrafficGenerator
    
    print("\nStarting attack simulation...")
    generator = AttackTrafficGenerator()
    
    try:
        generator.create_topology()
        generator.run_attack_simulation(attack_type='syn_flood', duration=60)
    except Exception as e:
        print(f"Simulation error: {e}")
    finally:
        generator.cleanup()
    
    # Wait for monitoring to complete
    monitor_thread.join()
    
    print("\nSimulation and detection completed!")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-time attack detection')
    parser.add_argument('--mode', choices=['monitor', 'simulate'], default='monitor',
                       help='Mode: monitor only or simulate attacks')
    parser.add_argument('--interface', default='any', help='Network interface to monitor')
    parser.add_argument('--duration', type=int, default=60, help='Monitoring duration (seconds)')
    
    args = parser.parse_args()
    
    if args.mode == 'simulate':
        run_simulation_with_detection()
    else:
        detector = RealTimeDetector()
        detector.start_monitoring(interface=args.interface, duration=args.duration)

if __name__ == '__main__':
    main()
