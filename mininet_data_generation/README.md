# VM Training-Only Setup

This directory contains a **clean, minimal setup** for VM-based Mininet training and model export.

## 🎯 Purpose

**VM Side**: Generate network data + Train models  
**Host Side**: Load exported models + Run inference

## 🚀 Quick Start

### 1. VM Setup (CentOS)
```bash
# Run VM training setup
sudo ./setup_vm_training_only.sh

# Execute training pipeline  
./run_vm_training.sh

# Export models for host
# Creates: exported_models.zip
```

### 2. Host Integration
```bash
# Copy exported_models.zip to host system
# Extract and integrate with host dashboard
# Use host_integration.py for inference
```

## Data Generation Process

1. **Topology Setup**: Creates a network with multiple hosts, switches, and a controller
2. **Traffic Generation**: Simulates realistic network behavior
3. **Packet Capture**: Uses tcpdump to capture all traffic
4. **Feature Extraction**: Converts packets to ML-ready features
5. **Labeling**: Automatically labels normal vs attack traffic
6. **Model Training**: Trains Random Forest, XGBoost, and ensemble models
7. **Evaluation**: Tests model performance on simulated attacks

## Features Extracted

- Flow-based: duration, packet count, byte count, packets/sec, bytes/sec
- Protocol: TCP/UDP/ICMP flags, port numbers
- Statistical: mean/std packet size, inter-arrival times
- Network: source/dest IPs, ports, protocol types
- Behavioral: connection patterns, rate anomalies

## Attack Types Simulated

1. **DDoS (SYN Flood)**: High-rate SYN packet flooding
2. **Port Scanning**: Sequential/random port probing
3. **Brute Force**: Repeated SSH/FTP login attempts
4. **DNS Amplification**: DNS query flooding
5. **HTTP Flood**: Application-layer DDoS

## Model Performance

Expected metrics on Mininet-generated data:
- Accuracy: >95%
- Precision: >93%
- Recall: >94%
- F1-Score: >93%
- False Positive Rate: <5%

## Safety Notes

⚠️ **IMPORTANT**: All simulations run in isolated Mininet environment
- No real network traffic is generated
- All attacks are contained within Mininet
- Safe for development and testing

## Troubleshooting

### Mininet not found
```bash
sudo apt-get update
sudo apt-get install mininet
```

### Permission denied
Run Mininet scripts with sudo:
```bash
sudo python topology/generate_normal_traffic.py
```

### tcpdump not capturing
Check interface and permissions:
```bash
sudo tcpdump -i any -w test.pcap
```

## Integration with Existing System

The generated models are compatible with the existing SOC dashboard:
- Drop-in replacement for `models/*.pkl` files
- Same prediction API interface
- Enhanced feature extraction for real-time data
- Backward compatible with existing endpoints
