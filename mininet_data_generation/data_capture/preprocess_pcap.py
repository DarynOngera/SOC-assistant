#!/usr/bin/env python3
"""
PCAP Preprocessing for ML Training
Extracts features from packet captures and creates labeled dataset
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict
from scapy.all import rdpcap, IP, TCP, UDP, ICMP
from scapy.layers.inet import TCP, UDP
import warnings
warnings.filterwarnings('ignore')

class PCAPPreprocessor:
    """Extract ML features from PCAP files"""
    
    def __init__(self, pcap_dir='pcaps', output_dir='processed'):
        self.pcap_dir = pcap_dir
        self.output_dir = output_dir
        try:
            os.makedirs(output_dir, exist_ok=True)
        except PermissionError:
            # Try current directory if permission denied
            self.output_dir = 'processed'
            os.makedirs(self.output_dir, exist_ok=True)
        
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
            'src_ip': None,
            'dst_ip': None,
            'src_port': None,
            'dst_port': None,
            'protocol': None
        })
    
    def get_flow_key(self, packet):
        """Generate unique flow key from packet"""
        if IP in packet:
            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            protocol = ip_layer.proto
            
            src_port = 0
            dst_port = 0
            
            if TCP in packet:
                src_port = packet[TCP].sport
                dst_port = packet[TCP].dport
            elif UDP in packet:
                src_port = packet[UDP].sport
                dst_port = packet[UDP].dport
            
            # Bidirectional flow key (normalize direction)
            flow_key = tuple(sorted([
                (src_ip, src_port),
                (dst_ip, dst_port)
            ]))
            
            return (flow_key, protocol)
        
        return None
    
    def extract_packet_features(self, packet):
        """Extract features from individual packet"""
        features = {}
        
        if IP in packet:
            ip_layer = packet[IP]
            features['ip_len'] = ip_layer.len
            features['ip_ttl'] = ip_layer.ttl
            features['ip_proto'] = ip_layer.proto
            
            # TCP features
            if TCP in packet:
                tcp_layer = packet[TCP]
                features['tcp_sport'] = tcp_layer.sport
                features['tcp_dport'] = tcp_layer.dport
                features['tcp_flags'] = int(tcp_layer.flags)
                features['tcp_window'] = tcp_layer.window
                
                # Flag breakdown
                features['tcp_flag_syn'] = 1 if tcp_layer.flags & 0x02 else 0
                features['tcp_flag_ack'] = 1 if tcp_layer.flags & 0x10 else 0
                features['tcp_flag_fin'] = 1 if tcp_layer.flags & 0x01 else 0
                features['tcp_flag_rst'] = 1 if tcp_layer.flags & 0x04 else 0
                features['tcp_flag_psh'] = 1 if tcp_layer.flags & 0x08 else 0
                features['tcp_flag_urg'] = 1 if tcp_layer.flags & 0x20 else 0
            
            # UDP features
            elif UDP in packet:
                udp_layer = packet[UDP]
                features['udp_sport'] = udp_layer.sport
                features['udp_dport'] = udp_layer.dport
                features['udp_len'] = udp_layer.len
            
            # ICMP features
            elif ICMP in packet:
                icmp_layer = packet[ICMP]
                features['icmp_type'] = icmp_layer.type
                features['icmp_code'] = icmp_layer.code
        
        return features
    
    def process_pcap_file(self, pcap_file):
        """Process single PCAP file and extract flows"""
        print(f"Processing: {pcap_file}")
        
        try:
            packets = rdpcap(pcap_file)
            print(f"  Loaded {len(packets)} packets")
        except Exception as e:
            print(f"  Error reading PCAP: {e}")
            return []
        
        # Reset flows for this file
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
            'src_ip': None,
            'dst_ip': None,
            'src_port': None,
            'dst_port': None,
            'protocol': None
        })
        
        # Process each packet
        for i, packet in enumerate(packets):
            if IP not in packet:
                continue
            
            flow_key = self.get_flow_key(packet)
            if flow_key is None:
                continue
            
            flow = self.flows[flow_key]
            
            # Update flow metadata
            if flow['start_time'] is None:
                flow['start_time'] = float(packet.time)
                flow['src_ip'] = packet[IP].src
                flow['dst_ip'] = packet[IP].dst
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
            
            # Inter-arrival time
            if len(flow['packets']) > 1:
                iat = float(packet.time) - float(flow['packets'][-2].time)
                flow['inter_arrival_times'].append(iat)
            
            # TCP flags
            if TCP in packet:
                tcp_flags = packet[TCP].flags
                if tcp_flags & 0x02:  # SYN
                    flow['syn_count'] += 1
                if tcp_flags & 0x01:  # FIN
                    flow['fin_count'] += 1
                if tcp_flags & 0x04:  # RST
                    flow['rst_count'] += 1
                if tcp_flags & 0x08:  # PSH
                    flow['psh_count'] += 1
                if tcp_flags & 0x10:  # ACK
                    flow['ack_count'] += 1
                if tcp_flags & 0x20:  # URG
                    flow['urg_count'] += 1
        
        print(f"  Extracted {len(self.flows)} flows")
        
        # Convert flows to feature vectors
        features_list = []
        for flow_key, flow in self.flows.items():
            features = self.extract_flow_features(flow)
            features_list.append(features)
        
        return features_list
    
    def extract_flow_features(self, flow):
        """Extract ML features from flow"""
        features = {}
        
        # Basic flow features
        duration = flow['end_time'] - flow['start_time'] if flow['end_time'] else 0
        features['duration'] = duration
        features['packet_count'] = len(flow['packets'])
        features['byte_count'] = flow['bytes']
        
        # Rate features
        if duration > 0:
            features['packets_per_sec'] = len(flow['packets']) / duration
            features['bytes_per_sec'] = flow['bytes'] / duration
        else:
            features['packets_per_sec'] = 0
            features['bytes_per_sec'] = 0
        
        # Packet size statistics
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
        
        # Inter-arrival time statistics
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
        
        # TCP flag counts
        features['syn_count'] = flow['syn_count']
        features['fin_count'] = flow['fin_count']
        features['rst_count'] = flow['rst_count']
        features['psh_count'] = flow['psh_count']
        features['ack_count'] = flow['ack_count']
        features['urg_count'] = flow['urg_count']
        
        # TCP flag ratios
        if features['packet_count'] > 0:
            features['syn_ratio'] = flow['syn_count'] / features['packet_count']
            features['fin_ratio'] = flow['fin_count'] / features['packet_count']
            features['rst_ratio'] = flow['rst_count'] / features['packet_count']
        else:
            features['syn_ratio'] = 0
            features['fin_ratio'] = 0
            features['rst_ratio'] = 0
        
        # Protocol
        features['protocol'] = flow['protocol'] if flow['protocol'] else 0
        
        # Port features (for well-known ports)
        features['src_port'] = flow['src_port'] if flow['src_port'] else 0
        features['dst_port'] = flow['dst_port'] if flow['dst_port'] else 0
        
        # Well-known port indicators
        well_known_ports = [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 8080]
        features['is_well_known_port'] = 1 if (
            flow['src_port'] in well_known_ports or 
            flow['dst_port'] in well_known_ports
        ) else 0
        
        return features
    
    def label_data(self, pcap_file, features_list):
        """Label data based on filename"""
        # Determine label from filename
        filename = os.path.basename(pcap_file)
        
        if 'normal' in filename.lower():
            label = 0  # Normal traffic
            attack_type = 'normal'
        elif 'attack' in filename.lower():
            label = 1  # Attack traffic
            
            # Determine specific attack type
            if 'syn_flood' in filename.lower():
                attack_type = 'syn_flood'
            elif 'port_scan' in filename.lower():
                attack_type = 'port_scan'
            elif 'udp_flood' in filename.lower():
                attack_type = 'udp_flood'
            elif 'icmp_flood' in filename.lower():
                attack_type = 'icmp_flood'
            elif 'http_flood' in filename.lower():
                attack_type = 'http_flood'
            elif 'dns_amplification' in filename.lower():
                attack_type = 'dns_amplification'
            elif 'brute_force' in filename.lower():
                attack_type = 'brute_force'
            elif 'slowloris' in filename.lower():
                attack_type = 'slowloris'
            else:
                attack_type = 'unknown_attack'
        else:
            label = 0
            attack_type = 'unknown'
        
        # Add labels to features
        for features in features_list:
            features['label'] = label
            features['attack_type'] = attack_type
        
        return features_list
    
    def process_all_pcaps(self):
        """Process all PCAP files in directory"""
        print("="*60)
        print("PCAP PREPROCESSING")
        print("="*60)
        
        # Find all PCAP files
        pcap_files = glob.glob(os.path.join(self.pcap_dir, '*.pcap'))
        
        if not pcap_files:
            print(f"No PCAP files found in {self.pcap_dir}")
            return None
        
        print(f"Found {len(pcap_files)} PCAP files")
        print("="*60)
        
        all_features = []
        
        # Process each PCAP file
        for pcap_file in pcap_files:
            features_list = self.process_pcap_file(pcap_file)
            labeled_features = self.label_data(pcap_file, features_list)
            all_features.extend(labeled_features)
        
        print("="*60)
        print(f"Total flows extracted: {len(all_features)}")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_features)
        
        # Display statistics
        print("\nDataset Statistics:")
        print(f"  Total samples: {len(df)}")
        print(f"  Features: {len(df.columns) - 2}")  # Exclude label and attack_type
        print(f"\nLabel distribution:")
        print(df['label'].value_counts())
        print(f"\nAttack type distribution:")
        print(df['attack_type'].value_counts())
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f'mininet_dataset_{timestamp}.csv')
        df.to_csv(output_file, index=False)
        
        print(f"\nDataset saved to: {output_file}")
        print("="*60)
        
        return output_file

def main():
    """Main function"""
    print("PCAP to ML Dataset Converter")
    
    # Check if Scapy is available
    try:
        from scapy.all import rdpcap
    except ImportError:
        print("ERROR: Scapy not installed")
        print("Install with: pip install scapy")
        sys.exit(1)
    
    # Create preprocessor
    preprocessor = PCAPPreprocessor()
    
    # Process all PCAPs
    output_file = preprocessor.process_all_pcaps()
    
    if output_file:
        print("\nNext steps:")
        print(f"1. Train models: python ../models/train_mininet_models.py")
        print(f"2. Test models: python ../simulation/realtime_attack_sim.py")

if __name__ == '__main__':
    main()
