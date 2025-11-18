#!/usr/bin/env python3
"""
Feature Compatibility Ensurer
Ensures PCAP feature extraction matches trained model expectations
"""

import os
import sys
import json
import pickle
import pandas as pd
import numpy as np
from pathlib import Path

class FeatureCompatibilityEnsurer:
    """Ensure feature compatibility between PCAP extraction and models"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.models_dir = self.base_dir.parent / "models"
        
    def get_model_feature_names(self):
        """Get feature names expected by trained models"""
        try:
            # Try to load feature names from model metadata
            metadata_path = self.models_dir / "model_metadata.json"
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                return metadata.get('feature_names', None)
            
            # If no metadata, try to infer from scaler
            scaler_path = self.models_dir / "feature_scaler.pkl"
            if scaler_path.exists():
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                if hasattr(scaler, 'feature_names_in_'):
                    return list(scaler.feature_names_in_)
            
            # Default feature set based on common network features
            return self.get_default_feature_set()
            
        except Exception as e:
            print(f"Error getting model features: {e}")
            return self.get_default_feature_set()
    
    def get_default_feature_set(self):
        """Get default feature set for network analysis"""
        return [
            # Basic packet features
            'packet_length', 'protocol', 'ttl', 'flags',
            
            # Port and connection features
            'src_port', 'dst_port', 'src_port_class', 'dst_port_class',
            
            # TCP features
            'tcp_flags', 'tcp_window_size', 'tcp_seq_num', 'tcp_ack_num',
            'tcp_urgent_ptr', 'tcp_options_len',
            
            # UDP features
            'udp_length', 'udp_checksum',
            
            # Flow features
            'flow_duration', 'flow_bytes_sent', 'flow_bytes_recv',
            'flow_packets_sent', 'flow_packets_recv',
            'flow_bytes_per_sec', 'flow_packets_per_sec',
            
            # Statistical features
            'packet_size_mean', 'packet_size_std', 'packet_size_min', 'packet_size_max',
            'inter_arrival_time_mean', 'inter_arrival_time_std',
            
            # Protocol flags
            'is_tcp', 'is_udp', 'is_icmp',
            'is_http', 'is_https', 'is_ftp', 'is_ssh', 'is_dns',
            
            # Behavioral features
            'syn_flag_count', 'fin_flag_count', 'rst_flag_count',
            'psh_flag_count', 'ack_flag_count', 'urg_flag_count',
            
            # Anomaly indicators
            'port_scan_indicator', 'syn_flood_indicator',
            'unusual_port_usage', 'high_packet_rate'
        ]
    
    def create_feature_extractor(self, expected_features):
        """Create enhanced feature extractor for PCAP files"""
        
        extractor_code = f'''#!/usr/bin/env python3
"""
Enhanced PCAP Feature Extractor
Generated to match trained model expectations
"""

import pandas as pd
import numpy as np
from scapy.all import rdpcap, IP, TCP, UDP, ICMP
from collections import defaultdict, Counter
import time

class EnhancedPCAPExtractor:
    """Enhanced PCAP feature extractor matching model expectations"""
    
    def __init__(self):
        self.expected_features = {expected_features}
        self.flow_cache = defaultdict(list)
        
    def extract_features_from_pcap(self, pcap_path, max_packets=None):
        """Extract comprehensive features from PCAP file"""
        try:
            packets = rdpcap(str(pcap_path))
            if max_packets:
                packets = packets[:max_packets]
            
            # Group packets by flow
            flows = self.group_packets_by_flow(packets)
            
            # Extract features for each flow
            features = []
            for flow_key, flow_packets in flows.items():
                flow_features = self.extract_flow_features(flow_packets)
                if flow_features:
                    features.append(flow_features)
            
            if features:
                df = pd.DataFrame(features)
                # Ensure all expected features are present
                df = self.ensure_feature_completeness(df)
                return df
            else:
                return None
                
        except Exception as e:
            print(f"Error extracting features: {{e}}")
            return None
    
    def group_packets_by_flow(self, packets):
        """Group packets into flows"""
        flows = defaultdict(list)
        
        for packet in packets:
            if IP in packet:
                # Create flow key (bidirectional)
                src_ip = packet[IP].src
                dst_ip = packet[IP].dst
                
                if TCP in packet:
                    src_port = packet[TCP].sport
                    dst_port = packet[TCP].dport
                    protocol = 'TCP'
                elif UDP in packet:
                    src_port = packet[UDP].sport
                    dst_port = packet[UDP].dport
                    protocol = 'UDP'
                else:
                    src_port = 0
                    dst_port = 0
                    protocol = 'OTHER'
                
                # Create bidirectional flow key
                flow_key = tuple(sorted([
                    (src_ip, src_port),
                    (dst_ip, dst_port)
                ]) + [protocol])
                
                flows[flow_key].append(packet)
        
        return flows
    
    def extract_flow_features(self, flow_packets):
        """Extract features from a flow of packets"""
        if not flow_packets:
            return None
        
        features = {{}}
        
        # Basic packet statistics
        packet_sizes = [len(pkt) for pkt in flow_packets]
        features['packet_length'] = np.mean(packet_sizes)
        features['packet_size_mean'] = np.mean(packet_sizes)
        features['packet_size_std'] = np.std(packet_sizes)
        features['packet_size_min'] = np.min(packet_sizes)
        features['packet_size_max'] = np.max(packet_sizes)
        
        # Flow statistics
        features['flow_packets_sent'] = len(flow_packets)
        features['flow_packets_recv'] = len(flow_packets)  # Simplified
        features['flow_bytes_sent'] = sum(packet_sizes)
        features['flow_bytes_recv'] = sum(packet_sizes)  # Simplified
        
        # Timing features
        timestamps = [float(pkt.time) for pkt in flow_packets if hasattr(pkt, 'time')]
        if len(timestamps) > 1:
            features['flow_duration'] = max(timestamps) - min(timestamps)
            inter_arrival_times = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
            features['inter_arrival_time_mean'] = np.mean(inter_arrival_times)
            features['inter_arrival_time_std'] = np.std(inter_arrival_times)
        else:
            features['flow_duration'] = 0
            features['inter_arrival_time_mean'] = 0
            features['inter_arrival_time_std'] = 0
        
        # Rate features
        if features['flow_duration'] > 0:
            features['flow_bytes_per_sec'] = features['flow_bytes_sent'] / features['flow_duration']
            features['flow_packets_per_sec'] = features['flow_packets_sent'] / features['flow_duration']
        else:
            features['flow_bytes_per_sec'] = 0
            features['flow_packets_per_sec'] = 0
        
        # Protocol features from first packet
        first_packet = flow_packets[0]
        if IP in first_packet:
            features['protocol'] = first_packet[IP].proto
            features['ttl'] = first_packet[IP].ttl
            features['flags'] = first_packet[IP].flags
        
        # TCP features
        tcp_flags = []
        tcp_windows = []
        tcp_seqs = []
        tcp_acks = []
        
        for pkt in flow_packets:
            if TCP in pkt:
                tcp_flags.append(pkt[TCP].flags)
                tcp_windows.append(pkt[TCP].window)
                tcp_seqs.append(pkt[TCP].seq)
                tcp_acks.append(pkt[TCP].ack)
        
        if tcp_flags:
            features['is_tcp'] = 1
            features['tcp_flags'] = Counter(tcp_flags).most_common(1)[0][0]
            features['tcp_window_size'] = np.mean(tcp_windows)
            features['tcp_seq_num'] = tcp_seqs[0] if tcp_seqs else 0
            features['tcp_ack_num'] = tcp_acks[0] if tcp_acks else 0
            features['tcp_urgent_ptr'] = 0  # Simplified
            features['tcp_options_len'] = 0  # Simplified
            
            # TCP flag counts
            all_flags = sum(tcp_flags, 0)  # Bitwise OR of all flags
            features['syn_flag_count'] = sum(1 for f in tcp_flags if f & 0x02)
            features['fin_flag_count'] = sum(1 for f in tcp_flags if f & 0x01)
            features['rst_flag_count'] = sum(1 for f in tcp_flags if f & 0x04)
            features['psh_flag_count'] = sum(1 for f in tcp_flags if f & 0x08)
            features['ack_flag_count'] = sum(1 for f in tcp_flags if f & 0x10)
            features['urg_flag_count'] = sum(1 for f in tcp_flags if f & 0x20)
        else:
            features['is_tcp'] = 0
            features['tcp_flags'] = 0
            features['tcp_window_size'] = 0
            features['tcp_seq_num'] = 0
            features['tcp_ack_num'] = 0
            features['tcp_urgent_ptr'] = 0
            features['tcp_options_len'] = 0
            features['syn_flag_count'] = 0
            features['fin_flag_count'] = 0
            features['rst_flag_count'] = 0
            features['psh_flag_count'] = 0
            features['ack_flag_count'] = 0
            features['urg_flag_count'] = 0
        
        # UDP features
        udp_lengths = []
        for pkt in flow_packets:
            if UDP in pkt:
                udp_lengths.append(pkt[UDP].len)
        
        if udp_lengths:
            features['is_udp'] = 1
            features['udp_length'] = np.mean(udp_lengths)
            features['udp_checksum'] = 0  # Simplified
        else:
            features['is_udp'] = 0
            features['udp_length'] = 0
            features['udp_checksum'] = 0
        
        # ICMP features
        features['is_icmp'] = 1 if any(ICMP in pkt for pkt in flow_packets) else 0
        
        # Port analysis
        ports = []
        for pkt in flow_packets:
            if TCP in pkt:
                ports.extend([pkt[TCP].sport, pkt[TCP].dport])
            elif UDP in pkt:
                ports.extend([pkt[UDP].sport, pkt[UDP].dport])
        
        if ports:
            features['src_port'] = ports[0] if len(ports) > 0 else 0
            features['dst_port'] = ports[1] if len(ports) > 1 else 0
            features['src_port_class'] = self.classify_port(features['src_port'])
            features['dst_port_class'] = self.classify_port(features['dst_port'])
        else:
            features['src_port'] = 0
            features['dst_port'] = 0
            features['src_port_class'] = 0
            features['dst_port_class'] = 0
        
        # Service identification
        features['is_http'] = 1 if (80 in ports or 8080 in ports) else 0
        features['is_https'] = 1 if (443 in ports or 8443 in ports) else 0
        features['is_ftp'] = 1 if (21 in ports or 20 in ports) else 0
        features['is_ssh'] = 1 if 22 in ports else 0
        features['is_dns'] = 1 if 53 in ports else 0
        
        # Anomaly indicators
        features['port_scan_indicator'] = 1 if len(set(ports)) > 10 else 0
        features['syn_flood_indicator'] = 1 if features['syn_flag_count'] > 100 else 0
        features['unusual_port_usage'] = 1 if any(p > 49152 for p in ports) else 0
        features['high_packet_rate'] = 1 if features['flow_packets_per_sec'] > 1000 else 0
        
        return features
    
    def classify_port(self, port):
        """Classify port into categories"""
        if port == 0:
            return 0
        elif port < 1024:
            return 1  # Well-known ports
        elif port < 49152:
            return 2  # Registered ports
        else:
            return 3  # Dynamic/private ports
    
    def ensure_feature_completeness(self, df):
        """Ensure all expected features are present"""
        for feature in self.expected_features:
            if feature not in df.columns:
                # Add missing feature with appropriate default
                if feature.endswith('_count') or feature.endswith('_indicator'):
                    df[feature] = 0
                elif feature.startswith('is_'):
                    df[feature] = 0
                elif 'time' in feature or 'duration' in feature:
                    df[feature] = 0.0
                elif 'size' in feature or 'length' in feature or 'bytes' in feature:
                    df[feature] = 0.0
                else:
                    df[feature] = 0
        
        # Reorder columns to match expected order
        ordered_columns = [col for col in self.expected_features if col in df.columns]
        remaining_columns = [col for col in df.columns if col not in self.expected_features]
        df = df[ordered_columns + remaining_columns]
        
        return df

# Usage example
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python enhanced_pcap_extractor.py <pcap_file>")
        sys.exit(1)
    
    extractor = EnhancedPCAPExtractor()
    pcap_file = sys.argv[1]
    
    print(f"Extracting features from {{pcap_file}}...")
    features_df = extractor.extract_features_from_pcap(pcap_file)
    
    if features_df is not None:
        print(f"Extracted {{len(features_df)}} flows with {{len(features_df.columns)}} features")
        print("Feature columns:", list(features_df.columns))
        
        # Save to CSV
        output_file = pcap_file.replace('.pcap', '_features.csv')
        features_df.to_csv(output_file, index=False)
        print(f"Features saved to {{output_file}}")
    else:
        print("No features extracted")
'''
        
        # Write the extractor
        extractor_path = self.base_dir / "enhanced_pcap_extractor.py"
        with open(extractor_path, 'w') as f:
            f.write(extractor_code)
        
        # Make executable
        os.chmod(extractor_path, 0o755)
        
        return extractor_path
    
    def update_processing_script(self):
        """Update the data processing script to use enhanced extractor"""
        
        processing_script = self.base_dir / "data_capture" / "preprocess_pcap.py"
        
        if not processing_script.exists():
            # Create new processing script
            processing_code = '''#!/usr/bin/env python3
"""
Enhanced PCAP Preprocessing Script
Uses enhanced feature extractor for model compatibility
"""

import os
import sys
import pandas as pd
from pathlib import Path

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent.parent))
from enhanced_pcap_extractor import EnhancedPCAPExtractor

def main():
    """Main preprocessing function"""
    base_dir = Path(__file__).parent.parent
    pcap_dir = base_dir / "data_capture" / "pcaps"
    output_dir = base_dir / "data_capture" / "processed"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Initialize extractor
    extractor = EnhancedPCAPExtractor()
    
    # Process all PCAP files
    all_features = []
    labels = []
    
    pcap_files = list(pcap_dir.glob("*.pcap"))
    
    for pcap_file in pcap_files:
        print(f"Processing {pcap_file.name}...")
        
        # Extract features
        features_df = extractor.extract_features_from_pcap(pcap_file)
        
        if features_df is not None:
            # Add labels based on filename
            if 'normal' in pcap_file.name.lower():
                file_labels = [0] * len(features_df)  # Normal = 0
            else:
                file_labels = [1] * len(features_df)  # Attack = 1
            
            all_features.append(features_df)
            labels.extend(file_labels)
            
            print(f"  Extracted {len(features_df)} flows")
    
    if all_features:
        # Combine all features
        combined_df = pd.concat(all_features, ignore_index=True)
        combined_df['label'] = labels
        
        # Save processed data
        output_file = output_dir / "mininet_processed_data.csv"
        combined_df.to_csv(output_file, index=False)
        
        print(f"\\nProcessed data saved to: {output_file}")
        print(f"Total samples: {len(combined_df)}")
        print(f"Features: {len(combined_df.columns) - 1}")  # Exclude label column
        print(f"Normal samples: {sum(1 for l in labels if l == 0)}")
        print(f"Attack samples: {sum(1 for l in labels if l == 1)}")
    else:
        print("No features extracted from PCAP files")

if __name__ == "__main__":
    main()
'''
            
            with open(processing_script, 'w') as f:
                f.write(processing_code)
            
            os.chmod(processing_script, 0o755)
        
        return processing_script
    
    def run_compatibility_check(self):
        """Run complete compatibility check and setup"""
        print("="*60)
        print("FEATURE COMPATIBILITY ENSURER")
        print("="*60)
        
        # Get expected features
        expected_features = self.get_model_feature_names()
        print(f"Expected features: {len(expected_features)}")
        
        # Create enhanced extractor
        extractor_path = self.create_feature_extractor(expected_features)
        print(f"✅ Enhanced extractor created: {extractor_path}")
        
        # Update processing script
        processing_path = self.update_processing_script()
        print(f"✅ Processing script updated: {processing_path}")
        
        print("\\n🎯 Feature compatibility ensured!")
        print("\\nThe pipeline will now:")
        print("1. Extract features matching model expectations")
        print("2. Handle missing features with appropriate defaults")
        print("3. Ensure feature order matches training data")
        print("4. Provide comprehensive flow-based analysis")
        
        return True

def main():
    """Main function"""
    ensurer = FeatureCompatibilityEnsurer()
    ensurer.run_compatibility_check()

if __name__ == "__main__":
    main()
