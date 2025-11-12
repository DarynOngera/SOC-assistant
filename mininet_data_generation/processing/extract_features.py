#!/usr/bin/env python3
"""
Extract ML features from PCAP files
"""

import os
import sys
import argparse
import pandas as pd
import numpy as np
from scapy.all import rdpcap, IP, TCP, UDP, ICMP
from datetime import datetime
from collections import defaultdict

class FeatureExtractor:
    """Extract features from PCAP files"""
    
    def __init__(self, input_dir, output_file):
        self.input_dir = input_dir
        self.output_file = output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
    def extract_from_pcap(self, pcap_file, label, attack_type):
        """Extract features from a single PCAP file"""
        print(f"Processing {pcap_file}...")
        
        try:
            packets = rdpcap(pcap_file)
        except Exception as e:
            print(f"Error reading {pcap_file}: {e}")
            return []
        
        # Group packets by flow (src_ip, dst_ip, src_port, dst_port, protocol)
        flows = defaultdict(list)
        
        for pkt in packets:
            if IP in pkt:
                key = self._get_flow_key(pkt)
                if key:
                    flows[key].append(pkt)
        
        # Extract features for each flow
        features = []
        for flow_key, flow_packets in flows.items():
            feature = self._extract_flow_features(flow_key, flow_packets, label, attack_type)
            if feature:
                features.append(feature)
        
        print(f"  Extracted {len(features)} flows")
        return features
    
    def _get_flow_key(self, pkt):
        """Get flow identifier from packet"""
        if IP not in pkt:
            return None
        
        src_ip = pkt[IP].src
        dst_ip = pkt[IP].dst
        
        if TCP in pkt:
            protocol = 'TCP'
            src_port = pkt[TCP].sport
            dst_port = pkt[TCP].dport
        elif UDP in pkt:
            protocol = 'UDP'
            src_port = pkt[UDP].sport
            dst_port = pkt[UDP].dport
        elif ICMP in pkt:
            protocol = 'ICMP'
            src_port = 0
            dst_port = 0
        else:
            return None
        
        return (src_ip, dst_ip, src_port, dst_port, protocol)
    
    def _extract_flow_features(self, flow_key, packets, label, attack_type):
        """Extract features from flow packets"""
        src_ip, dst_ip, src_port, dst_port, protocol = flow_key
        
        # Basic statistics
        packet_count = len(packets)
        if packet_count == 0:
            return None
        
        # Timing
        timestamps = [float(pkt.time) for pkt in packets]
        duration = max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0.1
        
        # Packet sizes
        packet_sizes = [len(pkt) for pkt in packets]
        byte_count = sum(packet_sizes)
        
        # TCP flags
        syn_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x02)
        fin_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x01)
        rst_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x04)
        psh_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x08)
        ack_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x10)
        urg_count = sum(1 for pkt in packets if TCP in pkt and pkt[TCP].flags & 0x20)
        
        # Derived features
        packets_per_sec = packet_count / duration if duration > 0 else 0
        bytes_per_sec = byte_count / duration if duration > 0 else 0
        mean_packet_size = np.mean(packet_sizes) if packet_sizes else 0
        std_packet_size = np.std(packet_sizes) if len(packet_sizes) > 1 else 0
        min_packet_size = min(packet_sizes) if packet_sizes else 0
        max_packet_size = max(packet_sizes) if packet_sizes else 0
        
        # Inter-arrival times
        if len(timestamps) > 1:
            inter_arrival_times = np.diff(timestamps)
            mean_iat = np.mean(inter_arrival_times)
            std_iat = np.std(inter_arrival_times)
        else:
            mean_iat = 0
            std_iat = 0
        
        # Flag ratios
        syn_ratio = syn_count / packet_count if packet_count > 0 else 0
        fin_ratio = fin_count / packet_count if packet_count > 0 else 0
        rst_ratio = rst_count / packet_count if packet_count > 0 else 0
        
        # Port classification
        is_well_known_port = 1 if dst_port < 1024 else 0
        
        return {
            'duration': duration,
            'protocol': protocol,
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'packet_count': packet_count,
            'byte_count': byte_count,
            'packets_per_sec': packets_per_sec,
            'bytes_per_sec': bytes_per_sec,
            'mean_packet_size': mean_packet_size,
            'std_packet_size': std_packet_size,
            'min_packet_size': min_packet_size,
            'max_packet_size': max_packet_size,
            'mean_inter_arrival_time': mean_iat,
            'std_inter_arrival_time': std_iat,
            'syn_count': syn_count,
            'fin_count': fin_count,
            'rst_count': rst_count,
            'psh_count': psh_count,
            'ack_count': ack_count,
            'urg_count': urg_count,
            'syn_ratio': syn_ratio,
            'fin_ratio': fin_ratio,
            'rst_ratio': rst_ratio,
            'is_well_known_port': is_well_known_port,
            'label': label,
            'attack_type': attack_type
        }
    
    def process_all(self):
        """Process all PCAP files"""
        print("="*60)
        print("FEATURE EXTRACTION FROM PCAP FILES")
        print("="*60)
        
        all_features = []
        
        # Process normal traffic
        normal_pcap = os.path.join(self.input_dir, 'normal_traffic.pcap')
        if os.path.exists(normal_pcap):
            features = self.extract_from_pcap(normal_pcap, label=0, attack_type='normal')
            all_features.extend(features)
        
        # Process attacks
        attacks = [
            ('syn_flood.pcap', 1, 'syn_flood'),
            ('port_scan.pcap', 1, 'port_scan'),
            ('udp_flood.pcap', 1, 'udp_flood'),
            ('http_flood.pcap', 1, 'http_flood')
        ]
        
        for pcap_name, label, attack_type in attacks:
            pcap_file = os.path.join(self.input_dir, pcap_name)
            if os.path.exists(pcap_file):
                features = self.extract_from_pcap(pcap_file, label, attack_type)
                all_features.extend(features)
        
        # Convert to DataFrame
        df = pd.DataFrame(all_features)
        
        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Save
        df.to_csv(self.output_file, index=False)
        
        print(f"\n✓ Extracted {len(df)} total samples")
        print(f"  Normal: {len(df[df['label'] == 0])}")
        print(f"  Attack: {len(df[df['label'] == 1])}")
        print(f"\n✓ Saved to: {self.output_file}")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Extract features from PCAP files')
    parser.add_argument('--input-dir', type=str, required=True, help='Directory with PCAP files')
    parser.add_argument('--output', type=str, required=True, help='Output CSV file')
    
    args = parser.parse_args()
    
    extractor = FeatureExtractor(args.input_dir, args.output)
    extractor.process_all()

if __name__ == '__main__':
    main()
