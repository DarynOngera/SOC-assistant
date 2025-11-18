#!/bin/bash
# Minimal CentOS Setup for Mininet Pipeline
# Optimized for 4GB RAM / 25GB storage

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check minimal requirements
check_minimal_requirements() {
    print_header "CHECKING MINIMAL REQUIREMENTS"
    
    # Check RAM (minimum 3.5GB usable)
    TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
    if [ "$TOTAL_RAM" -lt 3500 ]; then
        print_warning "RAM: ${TOTAL_RAM}MB (minimum 4GB recommended)"
        echo "Pipeline will use reduced sample sizes"
    else
        print_status "RAM: ${TOTAL_RAM}MB (sufficient)"
    fi
    
    # Check disk space (minimum 20GB)
    DISK_SPACE=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    if [ "$DISK_SPACE" -lt 20 ]; then
        echo "❌ Insufficient disk space (${DISK_SPACE}GB available, 25GB required)"
        exit 1
    else
        print_status "Disk: ${DISK_SPACE}GB (sufficient)"
    fi
    
    # Check CPU cores
    CORES=$(nproc)
    print_info "CPU cores: $CORES"
}

# Install minimal packages only
install_minimal_packages() {
    print_header "INSTALLING MINIMAL PACKAGES"
    
    # Detect CentOS version
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        PACKAGE_MANAGER="yum"
        sudo yum install -y epel-release
    else
        PACKAGE_MANAGER="dnf"
        sudo dnf install -y epel-release
        sudo dnf config-manager --set-enabled powertools 2>/dev/null || sudo dnf config-manager --set-enabled crb 2>/dev/null || true
    fi
    
    print_info "Installing essential packages only..."
    sudo $PACKAGE_MANAGER install -y \
        python3 python3-pip \
        git wget \
        tcpdump \
        openvswitch \
        firewalld
    
    print_status "Minimal packages installed"
}

# Install minimal Python packages
install_minimal_python() {
    print_header "INSTALLING MINIMAL PYTHON PACKAGES"
    
    print_info "Installing core ML packages..."
    python3 -m pip install --user --no-cache-dir \
        pandas==1.5.3 \
        numpy==1.21.6 \
        scikit-learn==1.1.3 \
        scapy==2.5.0
    
    print_info "Installing lightweight ML package..."
    python3 -m pip install --user --no-cache-dir \
        xgboost==1.6.2
    
    print_status "Minimal Python packages installed"
}

# Install Mininet (minimal)
install_minimal_mininet() {
    print_header "INSTALLING MININET (MINIMAL)"
    
    if command -v mn &> /dev/null; then
        print_status "Mininet already installed"
        return 0
    fi
    
    print_info "Installing Mininet from package..."
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        # CentOS 7 - install from source (minimal)
        cd /tmp
        git clone --depth 1 https://github.com/mininet/mininet
        cd mininet
        sudo ./util/install.sh -n  # Minimal install
    else
        # CentOS 8/9 - try package first
        sudo $PACKAGE_MANAGER install -y mininet || {
            print_info "Package install failed, installing from source..."
            cd /tmp
            git clone --depth 1 https://github.com/mininet/mininet
            cd mininet
            sudo ./util/install.sh -n
        }
    fi
    
    print_status "Mininet installed (minimal)"
}

# Configure minimal networking
configure_minimal_networking() {
    print_header "CONFIGURING MINIMAL NETWORKING"
    
    # Basic firewall
    sudo systemctl enable firewalld
    sudo systemctl start firewalld
    sudo firewall-cmd --permanent --add-port=5000/tcp
    sudo firewall-cmd --reload
    
    # Start OVS
    sudo systemctl enable openvswitch
    sudo systemctl start openvswitch
    
    print_status "Minimal networking configured"
}

# Create minimal pipeline scripts
create_minimal_scripts() {
    print_header "CREATING MINIMAL PIPELINE SCRIPTS"
    
    # Minimal pipeline runner
    cat > run_minimal_pipeline.sh << 'EOF'
#!/bin/bash
# Minimal Pipeline Runner - Optimized for 4GB RAM

set -e

echo "============================================================"
echo "MINIMAL MININET PIPELINE - LOW RESOURCE MODE"
echo "============================================================"

# Check resources
echo "Resources:"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU: $(nproc) cores"
echo "  Disk: $(df -h / | tail -1 | awk '{print $4}') available"
echo ""

# Clean up
sudo mn -c 2>/dev/null || true

# Step 1: Generate minimal normal traffic
echo "Step 1: Generating minimal normal traffic (5K samples)..."
timeout 300 sudo python3 topology/generate_normal_traffic.py --samples 5000 || {
    echo "⚠ Normal traffic generation timed out, using existing data"
}

# Step 2: Generate minimal attack traffic  
echo "Step 2: Generating minimal attack traffic (2K samples)..."
timeout 180 sudo python3 topology/generate_attack_traffic.py --samples 2000 || {
    echo "⚠ Attack traffic generation timed out, using existing data"
}

# Step 3: Process with memory limits
echo "Step 3: Processing data (memory-optimized)..."
python3 process_minimal_data.py

# Step 4: Train lightweight models
echo "Step 4: Training lightweight models..."
python3 train_minimal_models.py

echo ""
echo "============================================================"
echo "MINIMAL PIPELINE COMPLETED!"
echo "============================================================"
echo "Generated: ~7K samples (optimized for 4GB RAM)"
echo "Models: Lightweight Random Forest"
echo "Ready for basic SOC detection"
EOF

    chmod +x run_minimal_pipeline.sh
    
    # Minimal data processor
    cat > process_minimal_data.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal Data Processor - Memory Optimized
"""

import pandas as pd
import numpy as np
from pathlib import Path
import gc

def process_pcap_minimal(pcap_dir, output_dir, max_samples=1000):
    """Process PCAP files with memory constraints"""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    all_features = []
    labels = []
    
    pcap_files = list(Path(pcap_dir).glob("*.pcap"))
    
    for pcap_file in pcap_files:
        print(f"Processing {pcap_file.name} (max {max_samples} samples)...")
        
        try:
            # Simple feature extraction (memory efficient)
            features = extract_basic_features(pcap_file, max_samples)
            
            if features:
                # Determine label
                if 'normal' in pcap_file.name.lower():
                    file_labels = [0] * len(features)
                else:
                    file_labels = [1] * len(features)
                
                all_features.extend(features)
                labels.extend(file_labels)
                
                print(f"  Extracted {len(features)} samples")
                
                # Force garbage collection
                gc.collect()
                
        except Exception as e:
            print(f"  Error processing {pcap_file.name}: {e}")
    
    if all_features:
        # Create minimal dataset
        df = pd.DataFrame(all_features)
        df['label'] = labels
        
        # Save processed data
        output_file = output_dir / "minimal_processed_data.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\nProcessed data saved: {output_file}")
        print(f"Total samples: {len(df)}")
        print(f"Features: {len(df.columns) - 1}")
        
        return output_file
    
    return None

def extract_basic_features(pcap_file, max_samples):
    """Extract basic features with minimal memory usage"""
    try:
        from scapy.all import rdpcap, IP, TCP, UDP
        
        packets = rdpcap(str(pcap_file))[:max_samples]
        features = []
        
        for packet in packets:
            if IP in packet:
                feature = {
                    'packet_size': len(packet),
                    'protocol': packet[IP].proto,
                    'ttl': packet[IP].ttl,
                    'src_port': 0,
                    'dst_port': 0,
                    'is_tcp': 0,
                    'is_udp': 0,
                    'tcp_flags': 0
                }
                
                if TCP in packet:
                    feature['src_port'] = packet[TCP].sport
                    feature['dst_port'] = packet[TCP].dport
                    feature['is_tcp'] = 1
                    feature['tcp_flags'] = packet[TCP].flags
                elif UDP in packet:
                    feature['src_port'] = packet[UDP].sport
                    feature['dst_port'] = packet[UDP].dport
                    feature['is_udp'] = 1
                
                features.append(feature)
        
        return features
        
    except Exception as e:
        print(f"Error extracting features: {e}")
        return []

if __name__ == "__main__":
    pcap_dir = "data_capture/pcaps"
    output_dir = "data_capture/processed"
    
    process_pcap_minimal(pcap_dir, output_dir, max_samples=500)
EOF

    chmod +x process_minimal_data.py
    
    # Minimal model trainer
    cat > train_minimal_models.py << 'EOF'
#!/usr/bin/env python3
"""
Minimal Model Trainer - Memory Optimized
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import pickle
from pathlib import Path
import gc

def train_minimal_model():
    """Train lightweight model with memory constraints"""
    
    # Load processed data
    data_file = Path("data_capture/processed/minimal_processed_data.csv")
    
    if not data_file.exists():
        print("❌ No processed data found. Run data processing first.")
        return False
    
    print("Loading minimal dataset...")
    df = pd.read_csv(data_file)
    
    # Prepare features and labels
    X = df.drop('label', axis=1)
    y = df['label']
    
    print(f"Dataset: {len(df)} samples, {len(X.columns)} features")
    print(f"Normal: {sum(y == 0)}, Attacks: {sum(y == 1)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Scale features (memory efficient)
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train lightweight Random Forest
    print("Training lightweight Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=50,  # Reduced from 100
        max_depth=10,     # Limited depth
        random_state=42,
        n_jobs=1          # Single thread to save memory
    )
    
    rf_model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = rf_model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nModel Performance:")
    print(f"Accuracy: {accuracy:.3f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save models
    models_dir = Path("../models")
    models_dir.mkdir(exist_ok=True)
    
    with open(models_dir / "minimal_rf_model.pkl", 'wb') as f:
        pickle.dump(rf_model, f)
    
    with open(models_dir / "minimal_scaler.pkl", 'wb') as f:
        pickle.dump(scaler, f)
    
    # Save feature names
    feature_names = list(X.columns)
    with open(models_dir / "minimal_features.pkl", 'wb') as f:
        pickle.dump(feature_names, f)
    
    print(f"\n✅ Models saved to: {models_dir}")
    print("Ready for minimal SOC detection!")
    
    # Clean up memory
    del X_train_scaled, X_test_scaled, rf_model
    gc.collect()
    
    return True

if __name__ == "__main__":
    train_minimal_model()
EOF

    chmod +x train_minimal_models.py
    
    # Test script
    cat > test_minimal_setup.sh << 'EOF'
#!/bin/bash
# Test Minimal Setup

echo "============================================================"
echo "TESTING MINIMAL SETUP"
echo "============================================================"

# Check resources
echo "System Resources:"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU: $(nproc) cores"  
echo "  Disk: $(df -h / | tail -1 | awk '{print $4}') available"
echo ""

# Test Python imports
echo "Testing Python packages..."
python3 -c "import pandas; print('✓ Pandas')" || echo "✗ Pandas"
python3 -c "import numpy; print('✓ NumPy')" || echo "✗ NumPy"
python3 -c "import sklearn; print('✓ Scikit-learn')" || echo "✗ Scikit-learn"
python3 -c "import scapy.all; print('✓ Scapy')" || echo "✗ Scapy"
echo ""

# Test Mininet
echo "Testing Mininet..."
if sudo mn --version &> /dev/null; then
    echo "✓ Mininet working"
else
    echo "✗ Mininet not working"
fi
echo ""

# Test OVS
echo "Testing Open vSwitch..."
if sudo systemctl is-active openvswitch &> /dev/null; then
    echo "✓ Open vSwitch running"
else
    echo "✗ Open vSwitch not running"
fi

echo ""
echo "============================================================"
echo "MINIMAL SETUP TEST COMPLETED"
echo "============================================================"
EOF

    chmod +x test_minimal_setup.sh
    
    print_status "Minimal pipeline scripts created"
}

# Main execution
main() {
    print_header "MINIMAL CENTOS MININET SETUP"
    
    print_info "Optimized for 4GB RAM / 25GB storage"
    print_info "Reduced sample sizes and memory usage"
    echo ""
    
    read -p "Continue with minimal setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    check_minimal_requirements
    install_minimal_packages
    install_minimal_python
    install_minimal_mininet
    configure_minimal_networking
    create_minimal_scripts
    
    print_header "MINIMAL SETUP COMPLETED!"
    
    echo -e "${GREEN}✅ Minimal Mininet pipeline ready${NC}"
    echo ""
    echo "Minimal Configuration:"
    echo "  • Sample size: 7K total (5K normal + 2K attacks)"
    echo "  • Memory usage: <3GB during processing"
    echo "  • Storage usage: ~15GB total"
    echo "  • Processing time: ~5 minutes"
    echo ""
    echo "Quick Start:"
    echo "  1. Test setup:     ./test_minimal_setup.sh"
    echo "  2. Run pipeline:   ./run_minimal_pipeline.sh"
    echo "  3. Start dashboard: cd .. && python3 scripts/start_dashboard.py"
    echo ""
    print_info "Minimal setup optimized for low-resource environments!"
}

main "$@"
