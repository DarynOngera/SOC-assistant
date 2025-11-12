#!/usr/bin/env python3
"""
Mininet Network Traffic Generation Pipeline
Generates 100k+ real network samples with attacks
"""

import os
import sys
import time
import argparse
import subprocess
from datetime import datetime

class MininetPipeline:
    """Complete Mininet data generation pipeline"""
    
    def __init__(self, n_samples=100000):
        self.n_samples = n_samples
        self.output_dir = 'data_capture/mininet'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Calculate distribution
        self.n_normal = int(n_samples * 0.70)
        self.n_attacks = n_samples - self.n_normal
        
    def check_root(self):
        """Check if running as root"""
        if os.geteuid() != 0:
            print("❌ Error: Mininet requires root privileges")
            print("Run with: sudo python3 run_mininet_pipeline.py")
            sys.exit(1)
        print("✓ Running as root")
    
    def check_mininet(self):
        """Check if Mininet is installed"""
        try:
            result = subprocess.run(['mn', '--version'], 
                                  capture_output=True, text=True)
            print(f"✓ Mininet installed: {result.stdout.strip()}")
            return True
        except FileNotFoundError:
            print("❌ Mininet not installed!")
            print("\nInstall with:")
            print("  sudo apt-get install mininet")
            print("  OR")
            print("  git clone https://github.com/mininet/mininet")
            print("  cd mininet && sudo ./util/install.sh -a")
            sys.exit(1)
    
    def cleanup_mininet(self):
        """Clean up any existing Mininet processes"""
        print("\nCleaning up existing Mininet processes...")
        subprocess.run(['mn', '-c'], capture_output=True)
        print("✓ Cleanup complete")
    
    def run(self):
        """Run complete pipeline"""
        print("="*60)
        print("MININET NETWORK TRAFFIC GENERATION PIPELINE")
        print("="*60)
        print(f"Target samples: {self.n_samples:,}")
        print(f"  Normal traffic: {self.n_normal:,} (70%)")
        print(f"  Attack traffic: {self.n_attacks:,} (30%)")
        print()
        
        # Safety checks
        self.check_root()
        self.check_mininet()
        self.cleanup_mininet()
        
        # Run generation steps
        print("\n" + "="*60)
        print("STEP 1: Generate Normal Traffic")
        print("="*60)
        self.generate_normal_traffic()
        
        print("\n" + "="*60)
        print("STEP 2: Generate Attack Traffic")
        print("="*60)
        self.generate_attack_traffic()
        
        print("\n" + "="*60)
        print("STEP 3: Process and Combine Data")
        print("="*60)
        self.process_data()
        
        # Final cleanup
        self.cleanup_mininet()
        
        print("\n" + "="*60)
        print("✓ PIPELINE COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"\nGenerated {self.n_samples:,} samples")
        print(f"Output directory: {self.output_dir}")
        print("\nNext steps:")
        print("  1. Train models: python3 models/train_mininet_models.py")
        print("  2. Integrate: python3 integration/integrate_dashboard.py")
        print("="*60)
    
    def generate_normal_traffic(self):
        """Generate normal network traffic"""
        print(f"\nGenerating {self.n_normal:,} normal traffic samples...")
        print("This will take approximately 15-20 minutes...")
        
        # Run normal traffic generation
        cmd = [
            'python3',
            'topology/generate_normal_traffic.py',
            '--samples', str(self.n_normal),
            '--output', os.path.join(self.output_dir, 'normal_traffic.pcap')
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✓ Normal traffic generated")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating normal traffic: {e}")
            sys.exit(1)
    
    def generate_attack_traffic(self):
        """Generate attack traffic"""
        print(f"\nGenerating {self.n_attacks:,} attack samples...")
        print("Attack types: SYN flood, Port scan, UDP flood, HTTP flood")
        
        # Calculate per-attack counts
        attacks = {
            'syn_flood': int(self.n_attacks * 0.33),
            'port_scan': int(self.n_attacks * 0.33),
            'udp_flood': int(self.n_attacks * 0.17),
            'http_flood': self.n_attacks - int(self.n_attacks * 0.83)
        }
        
        for attack_type, count in attacks.items():
            print(f"\n  Generating {count:,} {attack_type} samples...")
            
            cmd = [
                'python3',
                f'topology/generate_{attack_type}.py',
                '--samples', str(count),
                '--output', os.path.join(self.output_dir, f'{attack_type}.pcap')
            ]
            
            try:
                subprocess.run(cmd, check=True)
                print(f"  ✓ {attack_type} generated")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ Error generating {attack_type}: {e}")
                # Continue with other attacks
        
        print("\n✓ All attack traffic generated")
    
    def process_data(self):
        """Process captured packets into ML features"""
        print("\nProcessing captured packets...")
        print("Extracting features from PCAP files...")
        
        cmd = [
            'python3',
            'processing/extract_features.py',
            '--input-dir', self.output_dir,
            '--output', os.path.join(self.output_dir, 'processed', 
                                    f'mininet_dataset_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        ]
        
        try:
            subprocess.run(cmd, check=True)
            print("✓ Data processed and saved")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error processing data: {e}")
            sys.exit(1)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Mininet Traffic Generation Pipeline')
    parser.add_argument('--samples', type=int, default=100000,
                       help='Number of samples to generate (default: 100000)')
    parser.add_argument('--skip-checks', action='store_true',
                       help='Skip safety checks (not recommended)')
    
    args = parser.parse_args()
    
    # Safety warning
    if not args.skip_checks:
        print("\n" + "⚠️ "*30)
        print("WARNING: Mininet will modify your network configuration!")
        print("⚠️ "*30)
        print("\nRecommended precautions:")
        print("  1. Disconnect from WiFi (use Ethernet)")
        print("  2. Backup network settings")
        print("  3. Run in a VM if possible")
        print("\nYour network will be restored after completion.")
        print()
        
        response = input("Continue? (yes/no): ").strip().lower()
        if response != 'yes':
            print("Aborted.")
            sys.exit(0)
    
    # Run pipeline
    pipeline = MininetPipeline(n_samples=args.samples)
    pipeline.run()

if __name__ == '__main__':
    main()
