#!/usr/bin/env python3
"""
Complete Mininet Pipeline Orchestrator
Automates the entire process from data generation to dashboard integration
"""

import os
import sys
import subprocess
import time
from datetime import datetime
from pathlib import Path

class PipelineOrchestrator:
    """Orchestrate complete Mininet pipeline"""
    
    def __init__(self):
        self.start_time = datetime.now()
        self.steps_completed = []
        self.steps_failed = []
        
    def print_header(self, text):
        """Print formatted header"""
        print("\n" + "="*60)
        print(text.center(60))
        print("="*60 + "\n")
    
    def print_step(self, step_num, total_steps, description):
        """Print step information"""
        print(f"\n[Step {step_num}/{total_steps}] {description}")
        print("-" * 60)
    
    def run_command(self, cmd, description, requires_root=False):
        """Run command and handle errors"""
        print(f"Running: {description}")
        
        if requires_root and os.geteuid() != 0:
            print("⚠ This step requires root privileges")
            cmd = ['sudo'] + cmd if isinstance(cmd, list) else f"sudo {cmd}"
        
        try:
            if isinstance(cmd, str):
                result = subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True
                )
            
            print(f"✓ {description} completed successfully")
            self.steps_completed.append(description)
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"✗ {description} failed")
            print(f"Error: {e.stderr}")
            self.steps_failed.append(description)
            return False
        except Exception as e:
            print(f"✗ {description} failed: {e}")
            self.steps_failed.append(description)
            return False
    
    def check_prerequisites(self):
        """Check system prerequisites"""
        self.print_step(0, 6, "Checking Prerequisites")
        
        # Check Python dependencies using pip
        required_packages = ['pandas', 'numpy', 'scikit-learn', 'scapy']
        try:
            import pkg_resources
            missing_packages = []
            for package in required_packages:
                try:
                    pkg_resources.get_distribution(package)
                except pkg_resources.DistributionNotFound:
                    missing_packages.append(package)
            
            if missing_packages:
                print(f"✗ Missing Python packages: {', '.join(missing_packages)}")
                print("Run: pip install -r ../requirements.txt")
                return False
            else:
                print("✓ Python dependencies available")
        except Exception as e:
            print(f"⚠ Could not verify Python dependencies: {e}")
            print("  Continuing anyway...")
        
        # Check Mininet
        result = subprocess.run(['which', 'mn'], capture_output=True)
        if result.returncode == 0:
            print("✓ Mininet available")
        else:
            print("✗ Mininet not found")
            print("Install with: sudo apt-get install mininet")
            return False
        
        # Check network tools (check both PATH and common locations)
        tools = ['tcpdump', 'hping3', 'nmap']
        missing = []
        for tool in tools:
            # Try which first, then command -v, then check common locations
            result = subprocess.run(['which', tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 0:
                result = subprocess.run(['command', '-v', tool], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    # Check common locations for system tools
                    common_paths = [f'/usr/sbin/{tool}', f'/sbin/{tool}', f'/usr/bin/{tool}', f'/bin/{tool}']
                    found = any(os.path.exists(path) for path in common_paths)
                    if not found:
                        missing.append(tool)
        
        if missing:
            print(f"✗ Missing tools: {', '.join(missing)}")
            print(f"Install with: sudo apt-get install {' '.join(missing)}")
            return False
        else:
            print("✓ Network tools available")
        
        # Check root access for Mininet
        if os.geteuid() != 0:
            print("⚠ Not running as root - will use sudo for Mininet operations")
        
        return True
    
    def generate_normal_traffic(self):
        """Step 1: Generate normal network traffic"""
        self.print_step(1, 6, "Generating Normal Network Traffic")
        
        print("This will take approximately 5 minutes...")
        print("Simulating: HTTP, FTP, DNS, SSH, ping traffic")
        
        return self.run_command(
            ['python3', 'topology/generate_normal_traffic.py'],
            "Normal traffic generation",
            requires_root=True
        )
    
    def generate_attack_traffic(self):
        """Step 2: Generate attack traffic"""
        self.print_step(2, 6, "Generating Attack Traffic")
        
        print("This will take approximately 2 minutes...")
        print("Simulating: SYN flood, port scan, UDP flood, HTTP flood, etc.")
        
        return self.run_command(
            ['python3', 'topology/generate_attack_traffic.py'],
            "Attack traffic generation",
            requires_root=True
        )
    
    def preprocess_data(self):
        """Step 3: Preprocess captured packets"""
        self.print_step(3, 6, "Preprocessing Packet Captures")
        
        print("Extracting features from PCAP files...")
        print("Features: flow statistics, packet sizes, TCP flags, etc.")
        
        return self.run_command(
            ['python3', 'data_capture/preprocess_pcap.py'],
            "Data preprocessing",
            requires_root=False
        )
    
    def train_models(self):
        """Step 4: Train ML models"""
        self.print_step(4, 6, "Training Machine Learning Models")
        
        print("Training Random Forest and XGBoost models...")
        print("This may take several minutes depending on dataset size...")
        
        return self.run_command(
            ['python3', 'models/train_mininet_models.py'],
            "Model training",
            requires_root=False
        )
    
    def test_models(self):
        """Step 5: Test models with simulation (optional)"""
        self.print_step(5, 6, "Testing Models (Optional)")
        
        print("Skipping real-time simulation test (can be run separately)")
        print("To test: sudo python3 simulation/realtime_attack_sim.py")
        
        self.steps_completed.append("Model testing (skipped)")
        return True
    
    def integrate_dashboard(self):
        """Step 6: Integrate with dashboard"""
        self.print_step(6, 6, "Integrating with SOC Dashboard")
        
        print("Backing up existing models...")
        print("Installing Mininet models...")
        print("Creating adapter layer...")
        
        return self.run_command(
            ['python3', 'integration/integrate_dashboard.py'],
            "Dashboard integration",
            requires_root=False
        )
    
    def print_summary(self):
        """Print execution summary"""
        duration = datetime.now() - self.start_time
        
        self.print_header("PIPELINE EXECUTION SUMMARY")
        
        print(f"Start time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        print(f"\nSteps completed: {len(self.steps_completed)}")
        print(f"Steps failed: {len(self.steps_failed)}")
        
        if self.steps_completed:
            print("\n✓ Completed steps:")
            for step in self.steps_completed:
                print(f"  - {step}")
        
        if self.steps_failed:
            print("\n✗ Failed steps:")
            for step in self.steps_failed:
                print(f"  - {step}")
        
        print("\n" + "="*60)
        
        if not self.steps_failed:
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("\nNext steps:")
            print("1. Review integration guide:")
            print("   cat ../models/INTEGRATION_GUIDE.md")
            print("\n2. Start the SOC dashboard:")
            print("   cd .. && python scripts/start_dashboard.py")
            print("\n3. Test real-time detection:")
            print("   sudo python3 simulation/realtime_attack_sim.py")
            print("\n4. Review model performance:")
            print("   cat reports/confusion_matrix.png")
        else:
            print("⚠ PIPELINE COMPLETED WITH ERRORS")
            print("="*60)
            print("\nPlease review the errors above and:")
            print("1. Check system requirements")
            print("2. Verify file permissions")
            print("3. Ensure sufficient disk space")
            print("4. Run failed steps individually for debugging")
        
        print("="*60 + "\n")
    
    def run(self):
        """Run complete pipeline"""
        self.print_header("MININET PIPELINE ORCHESTRATOR")
        
        print("This script will:")
        print("1. Generate normal network traffic (5 min)")
        print("2. Generate attack traffic (2 min)")
        print("3. Preprocess packet captures")
        print("4. Train ML models")
        print("5. Test models (optional)")
        print("6. Integrate with dashboard")
        print("\nTotal estimated time: 15-20 minutes")
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n✗ Prerequisites check failed. Please install missing components.")
            return False
        
        # Run pipeline steps
        steps = [
            self.generate_normal_traffic,
            self.generate_attack_traffic,
            self.preprocess_data,
            self.train_models,
            self.test_models,
            self.integrate_dashboard
        ]
        
        for step in steps:
            if not step():
                print(f"\n⚠ Step failed: {step.__name__}")
                response = input("Continue with remaining steps? (y/n): ")
                if response.lower() != 'y':
                    print("Pipeline aborted by user")
                    break
        
        # Print summary
        self.print_summary()
        
        return len(self.steps_failed) == 0

def main():
    """Main function"""
    # Check if running from correct directory
    if not os.path.exists('topology/generate_normal_traffic.py'):
        print("Error: Please run this script from the mininet_data_generation directory")
        sys.exit(1)
    
    # Create orchestrator
    orchestrator = PipelineOrchestrator()
    
    # Run pipeline
    success = orchestrator.run()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
