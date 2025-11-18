#!/usr/bin/env python3
"""
Synthetic Network Data Generator
Safe alternative to Mininet - no network interference
Generates realistic network traffic data without requiring root access
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import json

class SyntheticNetworkDataGenerator:
    """Generate synthetic network traffic data"""
    
    def __init__(self, output_dir='data_capture/processed'):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Network parameters
        self.normal_ips = [f'10.0.{i}.{j}' for i in range(1, 4) for j in range(1, 20)]
        self.attacker_ips = [f'192.168.100.{i}' for i in range(1, 10)]
        self.ports = {
            'http': 80,
            'https': 443,
            'ssh': 22,
            'ftp': 21,
            'dns': 53,
        }
    
    def generate_normal_traffic(self, n_samples=5000):
        """Generate normal network traffic patterns with realistic variability"""
        print(f"Generating {n_samples:,} normal traffic samples...")
        
        data = []
        
        for i in range(n_samples):
            # Random normal traffic characteristics
            src_ip = random.choice(self.normal_ips)
            dst_ip = random.choice(self.normal_ips)
            
            # Normal traffic patterns with weighted distribution
            protocol = random.choices(['TCP', 'UDP', 'ICMP'], weights=[0.70, 0.25, 0.05])[0]
            
            if protocol == 'TCP':
                dst_port = random.choices([80, 443, 22, 21, 3306, 25, 110], weights=[0.4, 0.3, 0.1, 0.05, 0.05, 0.05, 0.05])[0]
                src_port = random.randint(1024, 65535)
                
                # Normal TCP characteristics with realistic variability
                # Add noise to prevent overfitting
                packet_count = int(np.random.lognormal(3, 0.8))  # Log-normal distribution
                packet_count = max(5, min(packet_count, 100))  # Clamp between 5-100
                
                byte_count = int(np.random.lognormal(8, 1.2))  # Log-normal for bytes
                byte_count = max(500, min(byte_count, 100000))
                
                duration = np.random.exponential(2.0)  # Exponential distribution
                duration = max(0.1, min(duration, 30.0))
                
                syn_count = 1
                fin_count = 1
                rst_count = 0
                psh_count = random.randint(1, 10)
                ack_count = packet_count - 2
                
            elif protocol == 'UDP':
                dst_port = random.choice([53, 123, 161])
                src_port = random.randint(1024, 65535)
                
                # Normal UDP characteristics
                packet_count = random.randint(1, 10)
                byte_count = random.randint(50, 1500)
                duration = random.uniform(0.01, 1.0)
                
                syn_count = 0
                fin_count = 0
                rst_count = 0
                psh_count = 0
                ack_count = 0
                
            else:  # ICMP
                dst_port = 0
                src_port = 0
                
                # Normal ICMP (ping)
                packet_count = random.randint(1, 5)
                byte_count = packet_count * 64
                duration = random.uniform(0.1, 2.0)
                
                syn_count = 0
                fin_count = 0
                rst_count = 0
                psh_count = 0
                ack_count = 0
            
            # Calculate derived features with small noise to prevent perfect patterns
            noise_factor = np.random.normal(1.0, 0.02)  # 2% noise
            packets_per_sec = (packet_count / duration if duration > 0 else 0) * noise_factor
            bytes_per_sec = (byte_count / duration if duration > 0 else 0) * noise_factor
            mean_packet_size = (byte_count / packet_count if packet_count > 0 else 0) * noise_factor
            
            # Create flow record
            flow = {
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
                'std_packet_size': mean_packet_size * random.uniform(0.1, 0.3),
                'min_packet_size': int(mean_packet_size * 0.5),
                'max_packet_size': int(mean_packet_size * 1.5),
                'mean_inter_arrival_time': duration / packet_count if packet_count > 1 else 0,
                'std_inter_arrival_time': random.uniform(0.001, 0.1),
                'syn_count': syn_count,
                'fin_count': fin_count,
                'rst_count': rst_count,
                'psh_count': psh_count,
                'ack_count': ack_count,
                'urg_count': 0,
                'syn_ratio': syn_count / packet_count if packet_count > 0 else 0,
                'fin_ratio': fin_count / packet_count if packet_count > 0 else 0,
                'rst_ratio': rst_count / packet_count if packet_count > 0 else 0,
                'is_well_known_port': 1 if dst_port < 1024 else 0,
                'label': 0,  # Normal traffic
                'attack_type': 'normal'
            }
            
            data.append(flow)
        
        print(f"✓ Generated {len(data)} normal traffic samples")
        return data
    
    def generate_syn_flood(self, n_samples=500):
        """Generate SYN flood attack patterns with variability"""
        print(f"Generating {n_samples:,} SYN flood attack samples...")
        
        data = []
        
        for i in range(n_samples):
            # Vary attackers and victims to prevent overfitting
            attacker = random.choice(self.attacker_ips)
            victim = random.choice(self.normal_ips)
            
            # SYN flood characteristics with realistic variability
            # Not all SYN floods are the same intensity
            intensity = random.choice(['low', 'medium', 'high'])
            if intensity == 'low':
                packet_count = int(np.random.lognormal(4.5, 0.5))  # ~90-200 packets
            elif intensity == 'medium':
                packet_count = int(np.random.lognormal(5.5, 0.5))  # ~200-500 packets
            else:
                packet_count = int(np.random.lognormal(6.5, 0.5))  # ~500-1500 packets
            
            packet_count = max(50, min(packet_count, 2000))
            
            # SYN packets are small but not always exactly 60 bytes
            packet_size = int(np.random.normal(60, 5))
            packet_size = max(54, min(packet_size, 70))
            byte_count = packet_count * packet_size
            
            duration = np.random.exponential(1.0)
            duration = max(0.05, min(duration, 5.0))
            
            flow = {
                'duration': duration,
                'protocol': 'TCP',
                'src_ip': attacker,
                'dst_ip': victim,
                'src_port': random.randint(1024, 65535),
                'dst_port': random.choice([80, 443, 22]),
                'packet_count': packet_count,
                'byte_count': byte_count,
                'packets_per_sec': packet_count / duration,
                'bytes_per_sec': byte_count / duration,
                'mean_packet_size': 60,
                'std_packet_size': 5,
                'min_packet_size': 54,
                'max_packet_size': 66,
                'mean_inter_arrival_time': duration / packet_count,
                'std_inter_arrival_time': 0.001,
                'syn_count': packet_count,  # All SYN
                'fin_count': 0,
                'rst_count': 0,
                'psh_count': 0,
                'ack_count': 0,
                'urg_count': 0,
                'syn_ratio': 1.0,  # 100% SYN
                'fin_ratio': 0.0,
                'rst_ratio': 0.0,
                'is_well_known_port': 1,
                'label': 1,  # Attack
                'attack_type': 'syn_flood'
            }
            
            data.append(flow)
        
        print(f"✓ Generated {len(data)} SYN flood samples")
        return data
    
    def generate_port_scan(self, n_samples=500):
        """Generate port scanning patterns"""
        print(f"Generating {n_samples} port scan samples...")
        
        data = []
        attacker = random.choice(self.attacker_ips)
        victim = random.choice(self.normal_ips)
        
        for i in range(n_samples):
            # Port scan characteristics
            packet_count = random.randint(1, 5)
            byte_count = packet_count * 60
            duration = random.uniform(0.01, 0.5)
            
            flow = {
                'duration': duration,
                'protocol': 'TCP',
                'src_ip': attacker,
                'dst_ip': victim,
                'src_port': random.randint(1024, 65535),
                'dst_port': random.randint(1, 65535),  # Random ports
                'packet_count': packet_count,
                'byte_count': byte_count,
                'packets_per_sec': packet_count / duration,
                'bytes_per_sec': byte_count / duration,
                'mean_packet_size': 60,
                'std_packet_size': 2,
                'min_packet_size': 54,
                'max_packet_size': 66,
                'mean_inter_arrival_time': duration / packet_count,
                'std_inter_arrival_time': 0.001,
                'syn_count': packet_count,
                'fin_count': 0,
                'rst_count': packet_count,  # RST responses
                'psh_count': 0,
                'ack_count': 0,
                'urg_count': 0,
                'syn_ratio': 1.0,
                'fin_ratio': 0.0,
                'rst_ratio': 1.0,
                'is_well_known_port': 1 if random.random() < 0.3 else 0,
                'label': 1,
                'attack_type': 'port_scan'
            }
            
            data.append(flow)
        
        print(f"✓ Generated {len(data)} port scan samples")
        return data
    
    def generate_udp_flood(self, n_samples=500):
        """Generate UDP flood attack patterns"""
        print(f"Generating {n_samples} UDP flood samples...")
        
        data = []
        attacker = random.choice(self.attacker_ips)
        victim = random.choice(self.normal_ips)
        
        for i in range(n_samples):
            # UDP flood characteristics
            packet_count = random.randint(500, 5000)
            byte_count = packet_count * random.randint(100, 1500)
            duration = random.uniform(0.5, 5.0)
            
            flow = {
                'duration': duration,
                'protocol': 'UDP',
                'src_ip': attacker,
                'dst_ip': victim,
                'src_port': random.randint(1024, 65535),
                'dst_port': random.randint(1, 65535),
                'packet_count': packet_count,
                'byte_count': byte_count,
                'packets_per_sec': packet_count / duration,
                'bytes_per_sec': byte_count / duration,
                'mean_packet_size': byte_count / packet_count,
                'std_packet_size': 100,
                'min_packet_size': 100,
                'max_packet_size': 1500,
                'mean_inter_arrival_time': duration / packet_count,
                'std_inter_arrival_time': 0.0001,
                'syn_count': 0,
                'fin_count': 0,
                'rst_count': 0,
                'psh_count': 0,
                'ack_count': 0,
                'urg_count': 0,
                'syn_ratio': 0.0,
                'fin_ratio': 0.0,
                'rst_ratio': 0.0,
                'is_well_known_port': 0,
                'label': 1,
                'attack_type': 'udp_flood'
            }
            
            data.append(flow)
        
        print(f"✓ Generated {len(data)} UDP flood samples")
        return data
    
    def generate_http_flood(self, n_samples=500):
        """Generate HTTP flood (Layer 7 DDoS) patterns"""
        print(f"Generating {n_samples} HTTP flood samples...")
        
        data = []
        attacker = random.choice(self.attacker_ips)
        victim = random.choice(self.normal_ips)
        
        for i in range(n_samples):
            # HTTP flood characteristics
            packet_count = random.randint(50, 200)
            byte_count = packet_count * random.randint(200, 1500)
            duration = random.uniform(0.1, 2.0)
            
            flow = {
                'duration': duration,
                'protocol': 'TCP',
                'src_ip': attacker,
                'dst_ip': victim,
                'src_port': random.randint(1024, 65535),
                'dst_port': 80,  # HTTP
                'packet_count': packet_count,
                'byte_count': byte_count,
                'packets_per_sec': packet_count / duration,
                'bytes_per_sec': byte_count / duration,
                'mean_packet_size': byte_count / packet_count,
                'std_packet_size': 200,
                'min_packet_size': 200,
                'max_packet_size': 1500,
                'mean_inter_arrival_time': duration / packet_count,
                'std_inter_arrival_time': 0.001,
                'syn_count': 1,
                'fin_count': 1,
                'rst_count': 0,
                'psh_count': random.randint(10, 50),
                'ack_count': packet_count - 2,
                'urg_count': 0,
                'syn_ratio': 1.0 / packet_count,
                'fin_ratio': 1.0 / packet_count,
                'rst_ratio': 0.0,
                'is_well_known_port': 1,
                'label': 1,
                'attack_type': 'http_flood'
            }
            
            data.append(flow)
        
        print(f"✓ Generated {len(data)} HTTP flood samples")
        return data
    
    def generate_complete_dataset(self, n_samples=100000):
        """Generate complete dataset with normal and attack traffic"""
        print("="*60)
        print("SYNTHETIC NETWORK DATA GENERATION")
        print("="*60)
        print(f"Target samples: {n_samples:,}")
        print()
        
        all_data = []
        
        # Calculate split (70% normal, 30% attacks)
        n_normal = int(n_samples * 0.70)
        n_attacks = n_samples - n_normal
        
        # Distribute attacks evenly across types
        n_syn_flood = int(n_attacks * 0.33)
        n_port_scan = int(n_attacks * 0.33)
        n_udp_flood = int(n_attacks * 0.17)
        n_http_flood = n_attacks - (n_syn_flood + n_port_scan + n_udp_flood)
        
        # Generate normal traffic (70%)
        all_data.extend(self.generate_normal_traffic(n_samples=n_normal))
        
        # Generate attacks (30%)
        all_data.extend(self.generate_syn_flood(n_samples=n_syn_flood))
        all_data.extend(self.generate_port_scan(n_samples=n_port_scan))
        all_data.extend(self.generate_udp_flood(n_samples=n_udp_flood))
        all_data.extend(self.generate_http_flood(n_samples=n_http_flood))
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        
        # Shuffle
        df = df.sample(frac=1, random_state=42).reset_index(drop=0)
        
        # Save to CSV
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(self.output_dir, f'synthetic_dataset_{timestamp}.csv')
        df.to_csv(output_file, index=False)
        
        print()
        print("="*60)
        print("GENERATION COMPLETED")
        print("="*60)
        print(f"Total samples: {len(df)}")
        print(f"Normal traffic: {len(df[df['label'] == 0])} ({len(df[df['label'] == 0])/len(df)*100:.1f}%)")
        print(f"Attack traffic: {len(df[df['label'] == 1])} ({len(df[df['label'] == 1])/len(df)*100:.1f}%)")
        print()
        print("Attack types:")
        for attack_type in df[df['label'] == 1]['attack_type'].value_counts().items():
            print(f"  - {attack_type[0]}: {attack_type[1]}")
        print()
        print(f"Dataset saved to: {output_file}")
        print()
        print("Next steps:")
        print("  1. Train models: python models/train_mininet_models.py")
        print("  2. Integrate: python integration/integrate_dashboard.py")
        print("="*60)
        
        return output_file

def main():
    """Main function"""
    import sys
    
    # Allow custom sample count from command line
    n_samples = 100000  # Default to 100k for better generalization
    if len(sys.argv) > 1:
        try:
            n_samples = int(sys.argv[1])
        except ValueError:
            print(f"Invalid sample count, using default: {n_samples}")
    
    generator = SyntheticNetworkDataGenerator()
    generator.generate_complete_dataset(n_samples=n_samples)

if __name__ == '__main__':
    main()
