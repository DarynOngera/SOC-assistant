# Mininet-Based Network Data Generation for SOC Assistant

This module replaces the existing dataset with Mininet-generated network traffic data for training intrusion detection models.

## Overview

The system generates realistic network traffic using Mininet simulation, including:
- **Normal Traffic**: HTTP, FTP, SSH, DNS, ping traffic
- **Attack Traffic**: DDoS, port scanning, SYN flood, brute force

## Architecture

```
mininet_data_generation/
├── topology/              # Network topology definitions
├── traffic_generators/    # Normal and attack traffic scripts
├── data_capture/         # Packet capture and preprocessing
├── models/               # ML model training scripts
├── simulation/           # Real-time attack simulation
└── integration/          # Dashboard integration
```

## Requirements

### System Requirements
- Ubuntu/Linux system with root access
- Mininet installed: `sudo apt-get install mininet`
- Python 3.8+
- Network tools: tcpdump, hping3, nmap

### Python Dependencies
```bash
pip install scapy pandas numpy scikit-learn tensorflow xgboost imbalanced-learn
```

## Quick Start

### 1. Generate Normal Traffic Data
```bash
sudo python topology/generate_normal_traffic.py
```

### 2. Generate Attack Traffic Data
```bash
sudo python topology/generate_attack_traffic.py
```

### 3. Preprocess Captured Data
```bash
python data_capture/preprocess_pcap.py
```

### 4. Train Models
```bash
python models/train_mininet_models.py
```

### 5. Run Real-Time Simulation
```bash
sudo python simulation/realtime_attack_sim.py
```

### 6. Integrate with Dashboard
```bash
python integration/integrate_dashboard.py
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
