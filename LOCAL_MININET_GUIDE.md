# Local Mininet Setup Guide (Parrot OS)

## Overview

This guide helps you set up Mininet **locally on Parrot OS** to generate normal and attack PCAPs, then verify the frontend simulates correctly.

## 🚀 Quick Start

### Step 1: Install Mininet

```bash
# Install Mininet and dependencies
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch

# Install Python dependencies
pip3 install scapy psutil

# Verify installation
sudo mn --version
```

### Step 2: Generate PCAPs

```bash
# Make script executable
chmod +x mininet_data_generation/generate_local_pcaps.py

# Generate all PCAPs (takes 5-10 minutes)
sudo python3 mininet_data_generation/generate_local_pcaps.py
```

This will generate:
- ✅ `normal_traffic_*.pcap` - Normal network traffic
- ✅ `attack_syn_flood_*.pcap` - SYN flood attack
- ✅ `attack_port_scan_*.pcap` - Port scan attack
- ✅ `attack_udp_flood_*.pcap` - UDP flood attack
- ✅ `attack_http_flood_*.pcap` - HTTP flood attack
- ✅ `attack_icmp_flood_*.pcap` - ICMP flood attack

### Step 3: Test PCAP Processing

```bash
# Test that PCAPs are processed correctly
python3 test_local_simulation.py
```

### Step 4: Start Dashboard

```bash
# Start the dashboard
cd src/dashboard
python3 server.py

# Open browser
# http://localhost:5000
```

### Step 5: Test Frontend Simulation

1. **Login** to the dashboard
2. Navigate to **"Mininet Simulation"** (admin only)
3. **Test Normal Traffic:**
   - Click "Start Normal Traffic"
   - Expected: Few/no alerts, healthy system state
4. **Test Attack Simulations:**
   - Select attack type (e.g., "SYN Flood")
   - Click "Start Simulation"
   - Expected: Multiple alerts, attack identified

## 📋 Generated PCAPs

### Normal Traffic PCAP

**File:** `normal_traffic_YYYYMMDD_HHMMSS.pcap`

**Contains:**
- HTTP requests (port 80)
- Ping/ICMP traffic
- SSH-like traffic (port 22)
- DNS queries
- Normal TCP handshakes

**Expected Model Behavior:**
- Predicts mostly `0` (normal)
- Low anomaly scores (< 0.7)
- Few/no alerts generated

### Attack PCAPs

#### 1. SYN Flood
**File:** `attack_syn_flood_*.pcap`

**Characteristics:**
- High SYN packet rate
- No ACK/FIN packets
- SYN ratio > 0.8
- Incomplete TCP handshakes

**Expected Model Behavior:**
- Predicts `1` (anomaly)
- High anomaly scores (> 0.7)
- Alert type: "SYN Flood Attack"

#### 2. Port Scan
**File:** `attack_port_scan_*.pcap`

**Characteristics:**
- Connections to multiple ports
- Short connection durations
- Many RST packets
- Sequential port access

**Expected Model Behavior:**
- Predicts `1` (anomaly)
- Alert type: "Port Scan"

#### 3. UDP Flood
**File:** `attack_udp_flood_*.pcap`

**Characteristics:**
- High UDP packet rate
- Uniform packet sizes
- No TCP handshakes
- High packets per second

**Expected Model Behavior:**
- Predicts `1` (anomaly)
- Alert type: "UDP Flood"

#### 4. HTTP Flood
**File:** `attack_http_flood_*.pcap`

**Characteristics:**
- Excessive HTTP requests
- High connection rate to port 80
- Rapid request/response cycles

**Expected Model Behavior:**
- Predicts `1` (anomaly)
- Alert type: "HTTP Flood"

#### 5. ICMP Flood
**File:** `attack_icmp_flood_*.pcap`

**Characteristics:**
- High ICMP packet rate
- Ping flood patterns
- High packets per second

**Expected Model Behavior:**
- Predicts `1` (anomaly)
- Alert type: "ICMP Flood"

## 🔍 How Frontend Simulation Works

### Normal Traffic Flow

```
User clicks "Normal Traffic"
    ↓
server.py: current_simulation = 'normal_traffic'
    ↓
Uses: normal_traffic_*.pcap
    ↓
_extract_features_from_pcap()
    ↓
process_with_models()
    ↓
Model predicts: 0 (normal) for most flows
    ↓
Dashboard shows: Healthy state, few alerts
```

### Attack Traffic Flow

```
User selects "SYN Flood"
    ↓
server.py: current_simulation = 'syn_flood'
    ↓
Uses: attack_syn_flood_*.pcap
    ↓
_extract_features_from_pcap()
    ↓
process_with_models()
    ↓
Model predicts: 1 (anomaly) for suspicious flows
    ↓
Dashboard shows: Multiple alerts, attack type, severity
```

## 🧪 Verification Checklist

### PCAP Generation
- [ ] Mininet installed (`sudo mn --version`)
- [ ] PCAPs generated (check `data_capture/pcaps/`)
- [ ] Normal traffic PCAP exists
- [ ] All 5 attack PCAPs exist
- [ ] PCAP files are not empty (> 1KB)

### Feature Extraction
- [ ] Test script runs without errors
- [ ] Normal traffic: Features extracted successfully
- [ ] Attack traffic: Features extracted successfully
- [ ] Feature count matches model (24 features)

### Model Processing
- [ ] Normal traffic: Mostly classified as normal (0)
- [ ] SYN Flood: Detected as anomaly (1)
- [ ] Port Scan: Detected as anomaly (1)
- [ ] UDP Flood: Detected as anomaly (1)
- [ ] HTTP Flood: Detected as anomaly (1)
- [ ] ICMP Flood: Detected as anomaly (1)

### Frontend Simulation
- [ ] Dashboard starts successfully
- [ ] Mininet Simulation page accessible
- [ ] Normal traffic simulation works
- [ ] Attack simulations work
- [ ] Alerts generated correctly
- [ ] Attack types identified correctly

## 🔧 Troubleshooting

### Mininet Not Found

```bash
# Install Mininet
sudo apt-get install -y mininet openvswitch-switch

# Verify
sudo mn --version
```

### Permission Denied

```bash
# Must run as root
sudo python3 mininet_data_generation/generate_local_pcaps.py
```

### No PCAPs Generated

```bash
# Check if tcpdump is installed
which tcpdump

# Install if missing
sudo apt-get install -y tcpdump

# Clean up and retry
sudo mn -c
sudo python3 mininet_data_generation/generate_local_pcaps.py
```

### Empty PCAP Files

```bash
# Check Open vSwitch
sudo systemctl status openvswitch-switch

# Restart if needed
sudo systemctl restart openvswitch-switch

# Clean and retry
sudo mn -c
sudo python3 mininet_data_generation/generate_local_pcaps.py
```

### Model Not Detecting Attacks

```bash
# Verify model is loaded
cd src/dashboard
python3 -c "
from server import SOCDashboardAPI
api = SOCDashboardAPI()
print('Model loaded:', api.detector is not None)
"

# Check feature alignment
python3 verify_feature_alignment.py
```

## 📊 Expected Results

### Normal Traffic
- **Flows:** 50-200 flows
- **Anomalies:** 0-10% (< 5 alerts)
- **Anomaly Score:** < 0.5 average
- **Dashboard:** Green/healthy state

### SYN Flood
- **Flows:** 100-1000 flows
- **Anomalies:** 50-90% (many alerts)
- **Anomaly Score:** > 0.8 average
- **Dashboard:** Red/critical state
- **Attack Type:** SYN Flood identified

### Port Scan
- **Flows:** 20-50 flows
- **Anomalies:** 30-70%
- **Dashboard:** Yellow/warning state
- **Attack Type:** Port Scan identified

### Other Attacks
Similar patterns with high anomaly detection rates and correct attack type identification.

## 🎯 Next Steps

1. ✅ Generate PCAPs locally
2. ✅ Test PCAP processing
3. ✅ Verify model predictions
4. ✅ Test frontend simulations
5. ⏭️ Optional: Set up VM for remote Mininet
6. ⏭️ Deploy to production

## 📝 Notes

- **Local Mode:** PCAPs are pre-generated and replayed
- **VM Mode:** PCAPs are generated on-demand on remote VM
- **Both modes** use the same processing pipeline
- **Feature alignment** is critical for correct predictions
- **Model retraining** not needed if features are aligned

## 🔗 Related Files

- `mininet_data_generation/generate_local_pcaps.py` - PCAP generator
- `test_local_simulation.py` - Test script
- `src/dashboard/server.py` - Dashboard backend
- `verify_feature_alignment.py` - Feature verification
- `FEATURE_ALIGNMENT_REPORT.md` - Alignment documentation

## ✅ Success Criteria

Your setup is working correctly if:

1. ✅ All 6 PCAPs generated successfully
2. ✅ Test script shows PASS for all attacks
3. ✅ Normal traffic shows healthy state in UI
4. ✅ Attack simulations show alerts in UI
5. ✅ Attack types are correctly identified
6. ✅ No feature alignment errors in logs

---

**Ready to test!** Generate your PCAPs and verify the frontend works correctly. 🚀
