#!/bin/bash
# VM Training-Only Setup - Mininet + Model Training
# Models exported for inference on host system

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

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Install minimal packages for training only
install_training_packages() {
    print_header "INSTALLING TRAINING-ONLY PACKAGES"
    
    # Detect CentOS version
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        PACKAGE_MANAGER="yum"
        sudo yum install -y epel-release
    else
        PACKAGE_MANAGER="dnf"
        sudo dnf install -y epel-release
        sudo dnf config-manager --set-enabled powertools 2>/dev/null || sudo dnf config-manager --set-enabled crb 2>/dev/null || true
    fi
    
    print_info "Installing VM training essentials..."
    sudo $PACKAGE_MANAGER install -y \
        python3 python3-pip \
        git wget \
        tcpdump \
        zip unzip
    
    # Install Open vSwitch separately (different package names on different CentOS versions)
    print_info "Installing Open vSwitch..."
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        sudo $PACKAGE_MANAGER install -y openvswitch
    else
        # CentOS 8/9 - try different package names
        sudo $PACKAGE_MANAGER install -y openvswitch2.17 || \
        sudo $PACKAGE_MANAGER install -y openvswitch || \
        sudo $PACKAGE_MANAGER install -y network-scripts-openvswitch || {
            print_warning "OpenVSwitch package not found, will install from source later"
        }
    fi
    
    print_status "Training packages installed"
}

# Install Python packages for training only
install_training_python() {
    print_header "INSTALLING TRAINING PYTHON PACKAGES"
    
    print_info "Installing ML training packages..."
    python3 -m pip install --user --no-cache-dir \
        pandas==1.5.3 \
        numpy==1.21.6 \
        scikit-learn==1.1.3 \
        scapy==2.5.0 \
        xgboost==1.6.2 \
        joblib==1.2.0
    
    print_status "Training Python packages installed"
}

# Install Mininet for data generation
install_mininet_training() {
    print_header "INSTALLING MININET FOR TRAINING"
    
    if command -v mn &> /dev/null; then
        print_status "Mininet already installed"
        return 0
    fi
    
    print_info "Installing Mininet..."
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        cd /tmp
        git clone --depth 1 https://github.com/mininet/mininet
        cd mininet
        sudo ./util/install.sh -n
    else
        sudo $PACKAGE_MANAGER install -y mininet || {
            cd /tmp
            git clone --depth 1 https://github.com/mininet/mininet
            cd mininet
            sudo ./util/install.sh -n
        }
    fi
    
    # Start OpenVSwitch service (try different service names)
    print_info "Starting OpenVSwitch service..."
    sudo systemctl enable openvswitch 2>/dev/null || sudo systemctl enable openvswitch2.17 2>/dev/null || true
    sudo systemctl start openvswitch 2>/dev/null || sudo systemctl start openvswitch2.17 2>/dev/null || {
        print_warning "OpenVSwitch service not found, Mininet will handle OVS internally"
    }
    
    print_status "Mininet installed for training"
}

# Create training-only pipeline
create_training_pipeline() {
    print_header "CREATING TRAINING-ONLY PIPELINE"
    
    # VM training pipeline
    cat > run_vm_training.sh << 'EOF'
#!/bin/bash
# VM Training Pipeline - Generate Data & Train Models

set -e

echo "============================================================"
echo "VM TRAINING PIPELINE - MININET + MODEL TRAINING"
echo "============================================================"

# Check VM resources
echo "VM Resources:"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU: $(nproc) cores"
echo "  Disk: $(df -h / | tail -1 | awk '{print $4}') available"
echo ""

# Clean up
sudo mn -c 2>/dev/null || true

# Step 1: Generate training data
echo "Step 1: Generating network traffic for training..."
echo "  Normal traffic: 10K samples"
sudo python3 topology/generate_normal_traffic.py --samples 10000

echo "  Attack traffic: 5K samples"  
sudo python3 topology/generate_attack_traffic.py --samples 5000

# Step 2: Process training data
echo ""
echo "Step 2: Processing training data..."
python3 process_training_data.py

# Step 3: Train exportable models
echo ""
echo "Step 3: Training exportable models..."
python3 train_exportable_models.py

# Step 4: Export models for host system
echo ""
echo "Step 4: Exporting models for host system..."
python3 export_models.py

echo ""
echo "============================================================"
echo "VM TRAINING COMPLETED!"
echo "============================================================"
echo ""
echo "Generated: 15K training samples"
echo "Trained: Random Forest + XGBoost models"
echo "Exported: Models ready for host system inference"
echo ""
echo "Next steps:"
echo "1. Copy exported_models.zip to host system"
echo "2. Extract and integrate with host dashboard"
echo "3. Run inference on host system"
EOF

    chmod +x run_vm_training.sh
    
    # Training data processor
    cat > process_training_data.py << 'EOF'
#!/usr/bin/env python3
"""
Training Data Processor - VM Only
Processes PCAP files for model training
"""

import pandas as pd
import numpy as np
from pathlib import Path
from scapy.all import rdpcap, IP, TCP, UDP
import gc

def extract_training_features(pcap_file, max_samples=2000):
    """Extract comprehensive features for training"""
    try:
        packets = rdpcap(str(pcap_file))[:max_samples]
        features = []
        
        # Group packets by flow for better features
        flows = {}
        
        for packet in packets:
            if IP in packet:
                # Create flow key
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
                    continue
                
                flow_key = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}-{protocol}"
                
                if flow_key not in flows:
                    flows[flow_key] = []
                flows[flow_key].append(packet)
        
        # Extract features per flow
        for flow_key, flow_packets in flows.items():
            if len(flow_packets) > 0:
                feature = extract_flow_features(flow_packets)
                if feature:
                    features.append(feature)
        
        return features
        
    except Exception as e:
        print(f"Error processing {pcap_file}: {e}")
        return []

def extract_flow_features(flow_packets):
    """Extract features from packet flow"""
    try:
        # Basic statistics
        packet_sizes = [len(pkt) for pkt in flow_packets]
        
        feature = {
            # Size features
            'flow_packets': len(flow_packets),
            'total_bytes': sum(packet_sizes),
            'avg_packet_size': np.mean(packet_sizes),
            'std_packet_size': np.std(packet_sizes),
            'min_packet_size': np.min(packet_sizes),
            'max_packet_size': np.max(packet_sizes),
            
            # Timing features (simplified)
            'flow_duration': 1.0,  # Placeholder
            'packets_per_sec': len(flow_packets),
            'bytes_per_sec': sum(packet_sizes),
        }
        
        # Protocol analysis
        first_packet = flow_packets[0]
        if IP in first_packet:
            feature['protocol'] = first_packet[IP].proto
            feature['ttl'] = first_packet[IP].ttl
        
        # TCP features
        tcp_flags = []
        tcp_windows = []
        
        for pkt in flow_packets:
            if TCP in pkt:
                tcp_flags.append(pkt[TCP].flags)
                tcp_windows.append(pkt[TCP].window)
        
        if tcp_flags:
            feature['is_tcp'] = 1
            feature['tcp_flags'] = tcp_flags[0]
            feature['avg_window_size'] = np.mean(tcp_windows)
            feature['syn_count'] = sum(1 for f in tcp_flags if f & 0x02)
            feature['fin_count'] = sum(1 for f in tcp_flags if f & 0x01)
            feature['rst_count'] = sum(1 for f in tcp_flags if f & 0x04)
        else:
            feature['is_tcp'] = 0
            feature['tcp_flags'] = 0
            feature['avg_window_size'] = 0
            feature['syn_count'] = 0
            feature['fin_count'] = 0
            feature['rst_count'] = 0
        
        # UDP features
        feature['is_udp'] = 1 if any(UDP in pkt for pkt in flow_packets) else 0
        
        # Port analysis
        ports = []
        for pkt in flow_packets:
            if TCP in pkt:
                ports.extend([pkt[TCP].sport, pkt[TCP].dport])
            elif UDP in pkt:
                ports.extend([pkt[UDP].sport, pkt[UDP].dport])
        
        if ports:
            feature['unique_ports'] = len(set(ports))
            feature['has_well_known_port'] = 1 if any(p < 1024 for p in ports) else 0
            feature['has_high_port'] = 1 if any(p > 49152 for p in ports) else 0
        else:
            feature['unique_ports'] = 0
            feature['has_well_known_port'] = 0
            feature['has_high_port'] = 0
        
        # Service detection
        feature['is_http'] = 1 if (80 in ports or 8080 in ports) else 0
        feature['is_https'] = 1 if 443 in ports else 0
        feature['is_dns'] = 1 if 53 in ports else 0
        feature['is_ssh'] = 1 if 22 in ports else 0
        
        return feature
        
    except Exception as e:
        return None

def main():
    """Process all PCAP files for training"""
    pcap_dir = Path("data_capture/pcaps")
    output_dir = Path("data_capture/processed")
    output_dir.mkdir(exist_ok=True)
    
    all_features = []
    labels = []
    
    pcap_files = list(pcap_dir.glob("*.pcap"))
    
    for pcap_file in pcap_files:
        print(f"Processing {pcap_file.name}...")
        
        features = extract_training_features(pcap_file)
        
        if features:
            # Label based on filename
            if 'normal' in pcap_file.name.lower():
                file_labels = [0] * len(features)
            else:
                file_labels = [1] * len(features)
            
            all_features.extend(features)
            labels.extend(file_labels)
            
            print(f"  Extracted {len(features)} flows")
            gc.collect()
    
    if all_features:
        # Create training dataset
        df = pd.DataFrame(all_features)
        df['label'] = labels
        
        # Save training data
        output_file = output_dir / "training_data.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\nTraining data saved: {output_file}")
        print(f"Total flows: {len(df)}")
        print(f"Features: {len(df.columns) - 1}")
        print(f"Normal flows: {sum(df['label'] == 0)}")
        print(f"Attack flows: {sum(df['label'] == 1)}")
        
        return output_file
    
    return None

if __name__ == "__main__":
    main()
EOF

    chmod +x process_training_data.py
    
    # Exportable model trainer
    cat > train_exportable_models.py << 'EOF'
#!/usr/bin/env python3
"""
Exportable Model Trainer - VM Only
Trains models for export to host system
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import xgboost as xgb
import pickle
import json
from pathlib import Path
import joblib

def train_exportable_models():
    """Train models optimized for export"""
    
    # Load training data
    data_file = Path("data_capture/processed/training_data.csv")
    
    if not data_file.exists():
        print("❌ No training data found. Run data processing first.")
        return False
    
    print("Loading training dataset...")
    df = pd.read_csv(data_file)
    
    # Prepare features and labels
    X = df.drop('label', axis=1)
    y = df['label']
    
    print(f"Training dataset: {len(df)} samples, {len(X.columns)} features")
    print(f"Normal flows: {sum(y == 0)}, Attack flows: {sum(y == 1)}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Feature scaling
    print("Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train Random Forest
    print("Training Random Forest...")
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train_scaled, y_train)
    rf_pred = rf_model.predict(X_test_scaled)
    rf_accuracy = accuracy_score(y_test, rf_pred)
    
    print(f"Random Forest Accuracy: {rf_accuracy:.3f}")
    
    # Train XGBoost
    print("Training XGBoost...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42
    )
    
    xgb_model.fit(X_train_scaled, y_train)
    xgb_pred = xgb_model.predict(X_test_scaled)
    xgb_accuracy = accuracy_score(y_test, xgb_pred)
    
    print(f"XGBoost Accuracy: {xgb_accuracy:.3f}")
    
    # Cross-validation
    print("Performing cross-validation...")
    rf_cv_scores = cross_val_score(rf_model, X_train_scaled, y_train, cv=5)
    xgb_cv_scores = cross_val_score(xgb_model, X_train_scaled, y_train, cv=5)
    
    print(f"RF CV Score: {rf_cv_scores.mean():.3f} (+/- {rf_cv_scores.std() * 2:.3f})")
    print(f"XGB CV Score: {xgb_cv_scores.mean():.3f} (+/- {xgb_cv_scores.std() * 2:.3f})")
    
    # Save models for export
    models_dir = Path("trained_models")
    models_dir.mkdir(exist_ok=True)
    
    # Save models
    joblib.dump(rf_model, models_dir / "random_forest_model.pkl")
    joblib.dump(xgb_model, models_dir / "xgboost_model.pkl")
    joblib.dump(scaler, models_dir / "feature_scaler.pkl")
    
    # Save feature names
    feature_names = list(X.columns)
    with open(models_dir / "feature_names.json", 'w') as f:
        json.dump(feature_names, f)
    
    # Save model metadata
    metadata = {
        'training_date': pd.Timestamp.now().isoformat(),
        'training_samples': len(df),
        'features': len(X.columns),
        'feature_names': feature_names,
        'models': {
            'random_forest': {
                'accuracy': float(rf_accuracy),
                'cv_score': float(rf_cv_scores.mean()),
                'cv_std': float(rf_cv_scores.std())
            },
            'xgboost': {
                'accuracy': float(xgb_accuracy),
                'cv_score': float(xgb_cv_scores.mean()),
                'cv_std': float(xgb_cv_scores.std())
            }
        },
        'class_distribution': {
            'normal': int(sum(y == 0)),
            'attack': int(sum(y == 1))
        }
    }
    
    with open(models_dir / "model_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Generate detailed reports
    print("\nGenerating detailed reports...")
    
    # Classification reports
    rf_report = classification_report(y_test, rf_pred, output_dict=True)
    xgb_report = classification_report(y_test, xgb_pred, output_dict=True)
    
    with open(models_dir / "rf_classification_report.json", 'w') as f:
        json.dump(rf_report, f, indent=2)
    
    with open(models_dir / "xgb_classification_report.json", 'w') as f:
        json.dump(xgb_report, f, indent=2)
    
    # Confusion matrices
    rf_cm = confusion_matrix(y_test, rf_pred).tolist()
    xgb_cm = confusion_matrix(y_test, xgb_pred).tolist()
    
    with open(models_dir / "confusion_matrices.json", 'w') as f:
        json.dump({
            'random_forest': rf_cm,
            'xgboost': xgb_cm
        }, f, indent=2)
    
    print(f"\n✅ Models trained and saved to: {models_dir}")
    print("Ready for export to host system!")
    
    return True

if __name__ == "__main__":
    train_exportable_models()
EOF

    chmod +x train_exportable_models.py
    
    # Model export script
    cat > export_models.py << 'EOF'
#!/usr/bin/env python3
"""
Model Export Script - VM to Host System
Creates portable model package for host inference
"""

import zipfile
import json
import shutil
from pathlib import Path
from datetime import datetime

def export_models_for_host():
    """Export trained models for host system inference"""
    
    models_dir = Path("trained_models")
    export_dir = Path("exported_models")
    
    if not models_dir.exists():
        print("❌ No trained models found. Run training first.")
        return False
    
    # Create export directory
    export_dir.mkdir(exist_ok=True)
    
    print("Exporting models for host system...")
    
    # Copy model files
    model_files = [
        "random_forest_model.pkl",
        "xgboost_model.pkl", 
        "feature_scaler.pkl",
        "feature_names.json",
        "model_metadata.json",
        "rf_classification_report.json",
        "xgb_classification_report.json",
        "confusion_matrices.json"
    ]
    
    for file_name in model_files:
        src_file = models_dir / file_name
        if src_file.exists():
            shutil.copy2(src_file, export_dir / file_name)
            print(f"  ✓ Exported {file_name}")
    
    # Create host integration script
    integration_script = '''#!/usr/bin/env python3
"""
Host System Model Integration
Integrates VM-trained models with host dashboard
"""

import pickle
import json
import numpy as np
from pathlib import Path

class VMTrainedModelLoader:
    """Load and use VM-trained models on host system"""
    
    def __init__(self, models_dir="exported_models"):
        self.models_dir = Path(models_dir)
        self.rf_model = None
        self.xgb_model = None
        self.scaler = None
        self.feature_names = None
        self.metadata = None
        
    def load_models(self):
        """Load all exported models"""
        try:
            # Load models
            with open(self.models_dir / "random_forest_model.pkl", 'rb') as f:
                self.rf_model = pickle.load(f)
            
            with open(self.models_dir / "xgboost_model.pkl", 'rb') as f:
                self.xgb_model = pickle.load(f)
            
            with open(self.models_dir / "feature_scaler.pkl", 'rb') as f:
                self.scaler = pickle.load(f)
            
            # Load metadata
            with open(self.models_dir / "feature_names.json", 'r') as f:
                self.feature_names = json.load(f)
            
            with open(self.models_dir / "model_metadata.json", 'r') as f:
                self.metadata = json.load(f)
            
            print("✅ VM-trained models loaded successfully")
            print(f"Training date: {self.metadata['training_date']}")
            print(f"Training samples: {self.metadata['training_samples']}")
            print(f"RF Accuracy: {self.metadata['models']['random_forest']['accuracy']:.3f}")
            print(f"XGB Accuracy: {self.metadata['models']['xgboost']['accuracy']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            return False
    
    def predict_single(self, features_dict, model_type='random_forest'):
        """Predict single sample"""
        if not self.rf_model:
            raise ValueError("Models not loaded. Call load_models() first.")
        
        # Convert features to array
        feature_array = self.dict_to_array(features_dict)
        
        # Scale features
        scaled_features = self.scaler.transform([feature_array])
        
        # Predict
        if model_type == 'random_forest':
            prediction = self.rf_model.predict(scaled_features)[0]
            probability = self.rf_model.predict_proba(scaled_features)[0]
        else:
            prediction = self.xgb_model.predict(scaled_features)[0]
            probability = self.xgb_model.predict_proba(scaled_features)[0]
        
        return {
            'prediction': int(prediction),
            'probability': float(probability[1]),  # Probability of attack
            'confidence': float(max(probability))
        }
    
    def predict_batch(self, features_list, model_type='random_forest'):
        """Predict batch of samples"""
        if not self.rf_model:
            raise ValueError("Models not loaded. Call load_models() first.")
        
        # Convert to array
        feature_arrays = [self.dict_to_array(f) for f in features_list]
        
        # Scale features
        scaled_features = self.scaler.transform(feature_arrays)
        
        # Predict
        if model_type == 'random_forest':
            predictions = self.rf_model.predict(scaled_features)
            probabilities = self.rf_model.predict_proba(scaled_features)
        else:
            predictions = self.xgb_model.predict(scaled_features)
            probabilities = self.xgb_model.predict_proba(scaled_features)
        
        results = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            results.append({
                'prediction': int(pred),
                'probability': float(prob[1]),
                'confidence': float(max(prob))
            })
        
        return results
    
    def dict_to_array(self, features_dict):
        """Convert feature dictionary to array matching training order"""
        feature_array = []
        
        for feature_name in self.feature_names:
            if feature_name in features_dict:
                feature_array.append(features_dict[feature_name])
            else:
                # Use default value for missing features
                feature_array.append(0.0)
        
        return np.array(feature_array)
    
    def get_model_info(self):
        """Get model information"""
        return self.metadata

# Usage example
if __name__ == "__main__":
    # Load VM-trained models
    loader = VMTrainedModelLoader()
    
    if loader.load_models():
        # Example prediction
        sample_features = {
            'flow_packets': 10,
            'total_bytes': 5000,
            'avg_packet_size': 500,
            'is_tcp': 1,
            'syn_count': 1,
            # ... other features
        }
        
        result = loader.predict_single(sample_features)
        print(f"Prediction: {result}")
'''
    
    with open(export_dir / "host_integration.py", 'w') as f:
        f.write(integration_script)
    
    # Create README for host system
    readme_content = f'''# VM-Trained Models Export

## Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Files Included:
- random_forest_model.pkl: Trained Random Forest model
- xgboost_model.pkl: Trained XGBoost model  
- feature_scaler.pkl: Feature preprocessing scaler
- feature_names.json: Expected feature names and order
- model_metadata.json: Training metadata and performance
- host_integration.py: Integration script for host system

## Host System Integration:

1. Copy this entire folder to your host system
2. Install required packages: pip install scikit-learn xgboost pandas numpy
3. Use host_integration.py to load and use models

## Example Usage:

```python
from host_integration import VMTrainedModelLoader

# Load models
loader = VMTrainedModelLoader("path/to/exported_models")
loader.load_models()

# Make predictions
result = loader.predict_single(features_dict)
print(f"Attack probability: {{result['probability']:.3f}}")
```

## Model Performance:
- Training samples: {Path("data_capture/processed/training_data.csv").stat().st_size if Path("data_capture/processed/training_data.csv").exists() else "N/A"}
- Features: {len(json.load(open(models_dir / "feature_names.json")) if (models_dir / "feature_names.json").exists() else [])}
- See model_metadata.json for detailed performance metrics
'''
    
    with open(export_dir / "README.md", 'w') as f:
        f.write(readme_content)
    
    # Create ZIP package
    zip_file = "exported_models.zip"
    
    with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in export_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(export_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n✅ Models exported successfully!")
    print(f"📦 Export package: {zip_file}")
    print(f"📁 Export directory: {export_dir}")
    print("\nNext steps:")
    print("1. Copy exported_models.zip to your host system")
    print("2. Extract the ZIP file")
    print("3. Install required packages on host")
    print("4. Use host_integration.py to integrate with dashboard")
    
    return True

if __name__ == "__main__":
    export_models_for_host()
EOF

    chmod +x export_models.py
    
    print_status "Training-only pipeline created"
}

# Main execution
main() {
    print_header "VM TRAINING-ONLY SETUP"
    
    print_info "This setup focuses on:"
    print_info "• Mininet data generation on VM"
    print_info "• Model training on VM"
    print_info "• Model export for host system inference"
    echo ""
    
    read -p "Continue with training-only setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    install_training_packages
    install_training_python
    install_mininet_training
    create_training_pipeline
    
    print_header "VM TRAINING-ONLY SETUP COMPLETED!"
    
    echo -e "${GREEN}✅ VM configured for training only${NC}"
    echo ""
    echo "VM Training Configuration:"
    echo "  • Mininet for data generation"
    echo "  • ML libraries for model training"
    echo "  • Model export capabilities"
    echo "  • No dashboard/inference components"
    echo ""
    echo "Quick Start:"
    echo "  1. Run training: ./run_vm_training.sh"
    echo "  2. Copy exported_models.zip to host system"
    echo "  3. Integrate models with host dashboard"
    echo ""
    print_info "VM ready for training-only operations!"
}

main "$@"
