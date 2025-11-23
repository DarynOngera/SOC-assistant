# PCAP Replay Testing Guide
## Testing Trained ML Model with Normal and Attack Traffic

This guide explains how to test the SOC Dashboard's PCAP replay feature with the trained ML model to see the difference between normal and attack traffic detection.

---

## 🎯 Overview

The system now uses **PCAP Replay Mode** with a **trained Random Forest model** to:
- Replay real network traffic from PCAP files
- Process flows through the ML model (95.25% accuracy)
- Generate realistic alerts based on model predictions
- Show the difference between normal and attack traffic

---

## 📊 Trained Model Performance

| Metric | Score |
|--------|-------|
| **Accuracy** | 95.25% |
| **Precision** | 98.84% |
| **Recall** | 95.53% |
| **F1 Score** | 97.16% |
| **ROC AUC** | 99.18% |

**Training Data:**
- 3,156 total network flows
- 472 normal traffic flows (15%)
- 2,684 attack flows (85%)
- 5 attack types: SYN flood, port scan, UDP flood, HTTP flood, ICMP flood
- 5 normal traffic patterns: web browsing, file transfer, DNS+ping, SSH, mixed services

---

## 🚀 Quick Start

### 1. Start the Dashboard

```bash
cd /home/ongera/projects/SOC-assistant/src/dashboard
python3 server.py
```

### 2. Start the Frontend

```bash
cd /home/ongera/projects/SOC-assistant/frontend
npm start
```

### 3. Login
- Navigate to `http://localhost:3000`
- Login with admin credentials
- Go to **Mininet Simulation** page

---

## 🧪 Testing Scenarios

### Scenario 1: Normal Traffic Replay

**Purpose:** Verify that normal traffic generates few or no alerts

**Steps:**
1. In Mininet Simulation page, click **Settings**
2. Select **Simulation Mode**: `Normal Traffic`
3. Set **Duration**: `5 seconds` (visual only, actual processing is instant)
4. Click **Start Simulation**

**Expected Results:**
- Progress bar shows 5 steps (20%, 40%, 60%, 80%, 100%)
- Message: "Processing PCAP data..."
- Completion alert: "Simulation completed! Check Dashboard for alerts."
- **Dashboard should show:**
  - Few or no new alerts (normal traffic accuracy: 93.68%)
  - System health: "Healthy" or "Warning"
  - Low anomaly scores (< 0.5)

**What's Happening:**
- System loads `normal_traffic_v*.pcap` file
- Extracts 24 features per flow (ACK count, ports, packet sizes, etc.)
- ML model predicts: `0` (normal) for most flows
- Only flows with prediction `1` and anomaly_score >= threshold generate alerts

---

### Scenario 2: SYN Flood Attack Replay

**Purpose:** Verify that SYN flood attacks are detected

**Steps:**
1. Click **Settings**
2. Select **Simulation Mode**: `Attack Simulation`
3. Select **Attack Type**: `SYN Flood`
4. Set **Duration**: `5 seconds`
5. Click **Start Simulation**

**Expected Results:**
- Progress bar shows processing
- Completion alert appears
- **Dashboard should show:**
  - Multiple new alerts (attack detection rate: 95.53%)
  - Alert type: "SYN Flood" or "anomaly_detected"
  - System health: "Critical" or "Warning"
  - High anomaly scores (> 0.7)
  - Source IPs: Random spoofed IPs
  - Destination port: 80 (HTTP)

**Attack Characteristics:**
- High packet rate
- Many SYN packets without ACK
- Random source IPs
- Single destination

---

### Scenario 3: Port Scan Attack Replay

**Purpose:** Verify port scan detection

**Steps:**
1. Select **Attack Type**: `Port Scan`
2. Click **Start Simulation**

**Expected Results:**
- **Dashboard alerts show:**
  - Multiple alerts for different ports
  - Sequential or random port access patterns
  - Source IP: Single scanner IP
  - Destination ports: 1-1024 (well-known ports)
  - Attack type: "Port Scan"

**Attack Characteristics:**
- Many connections to different ports
- Short connection duration
- RST packets (connection refused)

---

### Scenario 4: UDP Flood Attack Replay

**Purpose:** Verify UDP flood detection

**Steps:**
1. Select **Attack Type**: `UDP Flood`
2. Click **Start Simulation**

**Expected Results:**
- **Dashboard alerts show:**
  - High volume UDP traffic
  - Random source IPs
  - Destination port: 53 (DNS)
  - Large or small packet sizes
  - Attack type: "UDP Flood"

---

### Scenario 5: Compare Normal vs Attack

**Purpose:** See the clear difference in detection

**Steps:**
1. **First:** Run normal traffic simulation
2. Note the number of alerts (should be 0-5)
3. **Then:** Run SYN flood simulation
4. Note the number of alerts (should be 50-200)

**Comparison:**
| Traffic Type | Alerts Generated | System Health | Anomaly Scores |
|--------------|------------------|---------------|----------------|
| Normal | 0-5 | Healthy | < 0.5 |
| SYN Flood | 50-200 | Critical | > 0.7 |
| Port Scan | 30-100 | Warning | 0.5-0.8 |
| UDP Flood | 50-150 | Critical | > 0.7 |

---

## 🔍 What to Look For

### In the Dashboard

1. **Alert Count**
   - Normal: Low (0-5 alerts)
   - Attack: High (50-200 alerts)

2. **System Health**
   - Normal: Green (Healthy)
   - Attack: Red (Critical) or Yellow (Warning)

3. **Alert Severity Distribution**
   - Normal: Mostly "Low" or "Medium"
   - Attack: Mostly "High" or "Critical"

4. **Network Statistics**
   - Normal: Steady packet rates
   - Attack: Spike in packet rates

### In Threat Triage

1. **Alert Details**
   - Source/Destination IPs
   - Ports
   - Protocol (TCP/UDP/ICMP)
   - Anomaly score
   - Attack type classification

2. **Tags**
   - All alerts tagged with: `mininet`, `ml_detected`
   - Attack-specific tags: `syn_flood`, `port_scan`, etc.

### In Network Map

1. **Topology Updates**
   - Nodes appear for active IPs
   - Connections show traffic flow
   - Red connections for attack traffic

---

## 📁 PCAP File Locations

### Normal Traffic PCAPs
```
/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/pcaps/
├── normal_traffic_v1_*.pcap  (Web browsing)
├── normal_traffic_v2_*.pcap  (File transfer)
├── normal_traffic_v3_*.pcap  (DNS + Ping)
├── normal_traffic_v4_*.pcap  (SSH session)
└── normal_traffic_v5_*.pcap  (Mixed services)
```

### Attack PCAPs
```
/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/pcaps/
├── attack_syn_flood_low_*.pcap
├── attack_syn_flood_medium_*.pcap
├── attack_syn_flood_high_*.pcap
├── attack_port_scan_sequential_*.pcap
├── attack_port_scan_random_*.pcap
├── attack_port_scan_targeted_*.pcap
├── attack_udp_flood_small_*.pcap
└── attack_udp_flood_mixed_*.pcap
```

---

## 🧠 How the ML Model Works

### Feature Extraction (24 Features)

The model analyzes these features from each network flow:

**Top 10 Most Important Features:**
1. **ack_count** (21.05%) - Number of ACK packets
2. **src_port** (19.57%) - Source port number
3. **dst_port** (11.35%) - Destination port number
4. **psh_count** (7.49%) - Number of PSH packets
5. **byte_count** (6.93%) - Total bytes transferred
6. **mean_packet_size** (6.81%) - Average packet size
7. **min_packet_size** (6.44%) - Minimum packet size
8. **max_packet_size** (5.52%) - Maximum packet size
9. **syn_count** (2.54%) - Number of SYN packets
10. **syn_ratio** (2.51%) - Ratio of SYN to total packets

### Prediction Process

1. **PCAP Loading**: Read packets from PCAP file
2. **Flow Extraction**: Group packets into network flows
3. **Feature Calculation**: Compute 24 features per flow
4. **Scaling**: Normalize features using StandardScaler
5. **Prediction**: Random Forest classifies as Normal (0) or Attack (1)
6. **Threshold**: Only flows with anomaly_score >= threshold generate alerts
7. **Alert Creation**: Store alerts in MongoDB with full details

---

## 🐛 Troubleshooting

### No Alerts Generated

**Problem:** Simulation completes but no alerts appear

**Solutions:**
1. Check if model files exist:
   ```bash
   ls -lh models/mininet_*.pkl
   ```
2. Check dashboard logs for errors
3. Verify PCAP files exist in correct directory
4. Ensure MongoDB is running

### Wrong Alert Types

**Problem:** Normal traffic generates many alerts

**Possible Causes:**
1. Model threshold too low (adjust in server.py)
2. PCAP file mislabeled
3. Feature extraction issues

**Solution:**
```python
# In server.py, adjust threshold
self.threshold = 0.7  # Increase to reduce false positives
```

### WebSocket Not Connecting

**Problem:** No progress updates during simulation

**Solutions:**
1. Check if SocketIO is running: `http://localhost:5000/socket.io/`
2. Check browser console for WebSocket errors
3. Ensure CORS is configured correctly

---

## 📈 Performance Metrics to Monitor

### Model Metrics
- **False Positive Rate**: 6.32% (6 normal flows misclassified as attacks out of 95)
- **Attack Detection Rate**: 95.53% (513 attacks detected out of 537)
- **Normal Traffic Accuracy**: 93.68% (89 normal flows correctly classified out of 95)

### Expected Alert Rates
- **Normal Traffic**: 0-10% of flows generate alerts
- **SYN Flood**: 80-95% of flows generate alerts
- **Port Scan**: 70-90% of flows generate alerts
- **UDP Flood**: 80-95% of flows generate alerts

---

## 🎓 Understanding the Results

### Why Normal Traffic Has Some Alerts

The model has a **6.32% false positive rate**, meaning:
- Out of 100 normal flows, ~6 will be flagged as attacks
- This is acceptable for security (better safe than sorry)
- Real SOC analysts would triage these as false positives

### Why Not All Attacks Are Detected

The model has a **95.53% recall**, meaning:
- Out of 100 attack flows, ~95 will be detected
- ~5 attacks might slip through (false negatives)
- This is realistic for production ML models
- Can be improved with more training data

---

## 🔄 Regenerating PCAPs (Optional)

If you want to create new PCAP files:

```bash
cd /home/ongera/projects/SOC-assistant
python3 generate_varied_pcaps.py
```

This generates:
- 5 normal traffic variants
- 3 SYN flood variants (low, medium, high intensity)
- 3 port scan variants (sequential, random, targeted)
- 2 UDP flood variants (small, mixed packet sizes)

---

## 📝 Next Steps

1. **Test all attack types** to see different detection patterns
2. **Compare alert counts** between normal and attack traffic
3. **Review training reports** in `training_reports/` directory
4. **View visualizations** of model performance
5. **Monitor dashboard** for real-time alert generation

---

## 🎯 Success Criteria

Your system is working correctly if:

✅ Normal traffic generates 0-10 alerts  
✅ Attack traffic generates 50-200 alerts  
✅ System health changes from Healthy to Critical during attacks  
✅ Progress bar shows 5 steps during processing  
✅ Alerts appear in Dashboard within 10 seconds  
✅ Model performance metrics match training report (95%+ accuracy)  

---

## 📞 Support

If you encounter issues:
1. Check dashboard logs: `src/dashboard/server.py` output
2. Check browser console for frontend errors
3. Verify model files exist in `models/` directory
4. Review training reports in `training_reports/` directory
5. Ensure all PCAP files are in correct location

---

**Happy Testing! 🚀**
