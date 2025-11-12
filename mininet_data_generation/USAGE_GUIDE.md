# Mininet Data Generation - Complete Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Detailed Workflow](#detailed-workflow)
3. [Component Reference](#component-reference)
4. [Troubleshooting](#troubleshooting)
5. [Advanced Usage](#advanced-usage)

## Quick Start

### Prerequisites
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install mininet tcpdump hping3 nmap netcat-openbsd

# Install Python dependencies
pip install -r ../requirements.txt
```

### One-Command Setup
```bash
# Run complete pipeline (15-20 minutes)
chmod +x setup_mininet_pipeline.sh
./setup_mininet_pipeline.sh
python3 run_complete_pipeline.py
```

### Manual Step-by-Step
```bash
# 1. Generate normal traffic (5 minutes)
sudo python3 topology/generate_normal_traffic.py

# 2. Generate attack traffic (2 minutes)
sudo python3 topology/generate_attack_traffic.py

# 3. Preprocess data
python3 data_capture/preprocess_pcap.py

# 4. Train models
python3 models/train_mininet_models.py

# 5. Integrate with dashboard
python3 integration/integrate_dashboard.py

# 6. Start dashboard
cd .. && python scripts/start_dashboard.py
```

## Detailed Workflow

### Phase 1: Data Generation

#### Normal Traffic Generation
Creates realistic benign network traffic patterns:

```bash
sudo python3 topology/generate_normal_traffic.py
```

**What it does:**
- Creates 10-host network topology
- Simulates HTTP, FTP, DNS, SSH, ping traffic
- Captures packets to PCAP file
- Duration: 5 minutes (configurable)
- Output: `data_capture/pcaps/normal_traffic_TIMESTAMP.pcap`

**Network Topology:**
```
Servers (10.0.1.x):
  - h1: Web server (HTTP)
  - h2: FTP server
  - h3: DNS server

Clients (10.0.2.x):
  - h4-h7: Client machines

Internal (10.0.3.x):
  - h8: Database server
  - h9: File server
  - h10: Mail server
```

#### Attack Traffic Generation
Simulates various network attacks:

```bash
# Generate all attack types
sudo python3 topology/generate_attack_traffic.py

# Generate specific attack
sudo python3 topology/generate_attack_traffic.py syn_flood
```

**Available Attack Types:**
1. **syn_flood** - SYN flood DDoS attack
2. **port_scan** - Port scanning (SYN, connect, UDP)
3. **udp_flood** - UDP flooding attack
4. **icmp_flood** - ICMP/ping flood
5. **http_flood** - Application-layer DDoS
6. **dns_amplification** - DNS amplification attack
7. **brute_force** - SSH brute force attempts
8. **slowloris** - Slow HTTP attack
9. **all** - All attack types (default)

**Output:** `data_capture/pcaps/attack_TYPE_TIMESTAMP.pcap`

### Phase 2: Data Preprocessing

Convert PCAP files to ML-ready dataset:

```bash
python3 data_capture/preprocess_pcap.py
```

**Feature Extraction:**
- **Flow-based:** duration, packet count, byte count, rates
- **Statistical:** mean/std packet size, inter-arrival times
- **Protocol:** TCP flags, port numbers, protocol types
- **Behavioral:** connection patterns, rate anomalies

**Output:** `data_capture/processed/mininet_dataset_TIMESTAMP.csv`

**Dataset Format:**
```csv
duration,packet_count,byte_count,packets_per_sec,bytes_per_sec,...,label,attack_type
0.5,10,1500,20.0,3000.0,...,0,normal
2.1,1000,50000,476.2,23809.5,...,1,syn_flood
```

### Phase 3: Model Training

Train intrusion detection models:

```bash
python3 models/train_mininet_models.py
```

**Training Pipeline:**
1. Load and preprocess data
2. Split into train/val/test (60/20/20)
3. Feature scaling with StandardScaler
4. Feature selection (top 30 features)
5. SMOTE for class balancing
6. Train Random Forest + XGBoost
7. Create ensemble model
8. Evaluate and generate reports

**Models Created:**
- `mininet_ensemble_model.pkl` - Main model
- `mininet_random_forest_model.pkl` - RF model
- `mininet_xgboost_model.pkl` - XGBoost model
- `mininet_scaler.pkl` - Feature scaler
- `mininet_feature_selector.pkl` - Feature selector
- `mininet_feature_columns.pkl` - Feature definitions
- `mininet_model_metadata.pkl` - Metadata

**Performance Metrics:**
- Accuracy: >95%
- Precision: >93%
- Recall: >94%
- F1-Score: >93%
- ROC AUC: >0.95

### Phase 4: Real-Time Testing

Test models with live attack simulation:

```bash
# Monitor only (passive)
sudo python3 simulation/realtime_attack_sim.py --mode monitor --duration 60

# Simulate attacks with detection (active)
sudo python3 simulation/realtime_attack_sim.py --mode simulate
```

**Features:**
- Real-time packet capture
- Flow-based analysis
- Live attack detection
- Detection statistics

### Phase 5: Dashboard Integration

Integrate models into SOC dashboard:

```bash
python3 integration/integrate_dashboard.py
```

**Integration Steps:**
1. Backup existing models
2. Copy Mininet models to `models/` directory
3. Create adapter layer for compatibility
4. Update server imports
5. Generate integration guide
6. Verify integration

**Verification:**
```python
from src.models.mininet_adapter import MininetModelAdapter

adapter = MininetModelAdapter()
template = adapter.get_feature_template()
result = adapter.predict_single(template)
print(result)
```

## Component Reference

### Directory Structure
```
mininet_data_generation/
├── README.md                          # Overview
├── USAGE_GUIDE.md                     # This file
├── setup_mininet_pipeline.sh          # Setup script
├── run_complete_pipeline.py           # Orchestrator
├── topology/
│   ├── generate_normal_traffic.py     # Normal traffic generator
│   └── generate_attack_traffic.py     # Attack traffic generator
├── data_capture/
│   ├── preprocess_pcap.py             # PCAP preprocessor
│   ├── pcaps/                         # Raw packet captures
│   └── processed/                     # Processed datasets
├── models/
│   └── train_mininet_models.py        # Model training
├── simulation/
│   └── realtime_attack_sim.py         # Real-time testing
├── integration/
│   └── integrate_dashboard.py         # Dashboard integration
└── reports/                           # Training reports
```

### Configuration Options

#### Traffic Generation
Edit scripts to customize:
```python
# In generate_normal_traffic.py
duration = 300  # Traffic duration in seconds

# In generate_attack_traffic.py
attack_type = 'syn_flood'  # Specific attack type
rate = 1000  # Packets per second for flood attacks
```

#### Model Training
Edit `train_mininet_models.py`:
```python
# Feature selection
k = 30  # Number of features to select

# Random Forest parameters
n_estimators = 100
max_depth = 20

# XGBoost parameters
learning_rate = 0.1
max_depth = 10
```

## Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Error: Permission denied when running Mininet
# Solution: Use sudo
sudo python3 topology/generate_normal_traffic.py
```

#### 2. Mininet Not Found
```bash
# Error: mn: command not found
# Solution: Install Mininet
sudo apt-get install mininet
```

#### 3. Missing Network Tools
```bash
# Error: hping3/nmap not found
# Solution: Install tools
sudo apt-get install hping3 nmap netcat-openbsd tcpdump
```

#### 4. Scapy Import Error
```bash
# Error: No module named 'scapy'
# Solution: Install Scapy
pip install scapy
```

#### 5. No PCAP Files Found
```bash
# Error: No PCAP files found in data_capture/pcaps
# Solution: Generate traffic first
sudo python3 topology/generate_normal_traffic.py
```

#### 6. Model Loading Failed
```bash
# Error: No trained models found
# Solution: Train models first
python3 models/train_mininet_models.py
```

### Debug Mode

Enable verbose logging:
```python
# In any script, add at the top:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Verify Installation
```bash
# Run test script
./test_installation.sh

# Manual verification
python3 -c "import scapy.all; import pandas; import sklearn; print('OK')"
sudo mn --version
```

## Advanced Usage

### Custom Network Topology

Create custom topology:
```python
from mininet.net import Mininet
from mininet.node import Controller

net = Mininet(controller=Controller)

# Add custom hosts and switches
h1 = net.addHost('h1', ip='192.168.1.1/24')
h2 = net.addHost('h2', ip='192.168.1.2/24')
s1 = net.addSwitch('s1')

# Create links
net.addLink(h1, s1)
net.addLink(h2, s1)

net.start()
# Run traffic generation
net.stop()
```

### Custom Attack Patterns

Add new attack in `generate_attack_traffic.py`:
```python
def attack_custom(self, attacker, victim, duration=60):
    """Custom attack implementation"""
    info(f'*** Custom Attack: {attacker.name} -> {victim.name}\n')
    
    # Your attack logic here
    for i in range(duration):
        attacker.cmd(f'custom_command {victim.IP()}')
        time.sleep(1)
```

### Feature Engineering

Add custom features in `preprocess_pcap.py`:
```python
def extract_flow_features(self, flow):
    features = {}
    
    # Add your custom features
    features['custom_metric'] = calculate_custom_metric(flow)
    
    return features
```

### Model Customization

Use different ML algorithms:
```python
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier

# In train_mininet_models.py
def train_svm(self, X_train, y_train):
    svm_model = SVC(kernel='rbf', probability=True)
    svm_model.fit(X_train, y_train)
    return svm_model
```

### Batch Processing

Process multiple datasets:
```bash
# Generate multiple traffic captures
for i in {1..5}; do
    sudo python3 topology/generate_normal_traffic.py
    sudo python3 topology/generate_attack_traffic.py
done

# Process all at once
python3 data_capture/preprocess_pcap.py
```

### Continuous Monitoring

Set up continuous detection:
```python
# In simulation/realtime_attack_sim.py
while True:
    detector.start_monitoring(duration=60)
    time.sleep(5)  # Brief pause between monitoring sessions
```

## Performance Tuning

### Optimize Traffic Generation
- Reduce duration for faster testing
- Adjust packet rates for different scenarios
- Use specific attack types instead of 'all'

### Optimize Model Training
- Reduce feature count for faster training
- Use smaller dataset samples during development
- Adjust cross-validation folds

### Optimize Real-Time Detection
- Increase flow analysis threshold (packets per flow)
- Batch predictions for better performance
- Use ensemble model only in production

## Integration with Existing Systems

### API Integration
```python
from src.models.mininet_adapter import MininetModelAdapter

adapter = MininetModelAdapter()

# REST API endpoint
@app.route('/api/detect', methods=['POST'])
def detect():
    features = request.json
    result = adapter.predict_single(features)
    return jsonify(result)
```

### Batch Processing
```python
# Process CSV file
import pandas as pd

df = pd.read_csv('network_data.csv')
features_list = df.to_dict('records')
results = adapter.predict_batch(features_list)
```

### Real-Time Stream Processing
```python
# Process network stream
from scapy.all import sniff

def packet_handler(packet):
    features = extract_features(packet)
    result = adapter.predict_single(features)
    if result['is_anomaly']:
        alert(result)

sniff(prn=packet_handler, filter='ip')
```

## Best Practices

1. **Always backup** existing models before integration
2. **Test thoroughly** with simulation before production
3. **Monitor performance** and retrain periodically
4. **Use version control** for model artifacts
5. **Document changes** to topology and features
6. **Validate data quality** before training
7. **Set up alerts** for model degradation
8. **Keep logs** of all training sessions

## Support and Resources

- **Documentation:** See README.md and INTEGRATION_GUIDE.md
- **Examples:** Check test scripts in each directory
- **Logs:** Review output in reports/ directory
- **Issues:** Check error messages and troubleshooting section

## Next Steps

After completing the pipeline:

1. **Review Performance**
   - Check confusion matrix in reports/
   - Analyze false positives/negatives
   - Validate with known attack patterns

2. **Fine-Tune Models**
   - Adjust hyperparameters
   - Add/remove features
   - Try different algorithms

3. **Deploy to Production**
   - Integrate with dashboard
   - Set up monitoring
   - Configure alerts

4. **Maintain and Update**
   - Retrain with new data
   - Update attack patterns
   - Monitor model drift

---

**Last Updated:** 2025-10-07
**Version:** 1.0
**Author:** SOC Assistant Team
