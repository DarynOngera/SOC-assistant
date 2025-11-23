# Quick Start - Local Mininet (Parrot OS)

## 🚀 3-Step Setup

### Step 1: Install Mininet (2 minutes)

```bash
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch tcpdump
pip3 install scapy psutil
```

### Step 2: Generate PCAPs (5-10 minutes)

```bash
sudo python3 mininet_data_generation/generate_local_pcaps.py
```

This creates:
- ✅ 1 normal traffic PCAP
- ✅ 5 attack PCAPs (SYN flood, port scan, UDP flood, HTTP flood, ICMP flood)

### Step 3: Test & Run (1 minute)

```bash
# Test PCAP processing
python3 test_local_simulation.py

# Start dashboard
cd src/dashboard
python3 server.py

# Open browser: http://localhost:5000
```

## ✅ Verify It Works

1. **Login** to dashboard
2. Go to **"Mininet Simulation"**
3. Click **"Start Normal Traffic"** → Should show healthy state
4. Click **"Start SYN Flood"** → Should show alerts

## 📁 Generated Files

All PCAPs saved to:
```
mininet_data_generation/data_capture/pcaps/
├── normal_traffic_20241121_141530.pcap
├── attack_syn_flood_20241121_141545.pcap
├── attack_port_scan_20241121_141600.pcap
├── attack_udp_flood_20241121_141615.pcap
├── attack_http_flood_20241121_141630.pcap
└── attack_icmp_flood_20241121_141645.pcap
```

## 🎯 What to Expect

### Normal Traffic Simulation
- **Dashboard:** Green/healthy state
- **Alerts:** 0-2 alerts (very few)
- **Model:** Predicts mostly normal (0)

### Attack Simulations
- **Dashboard:** Red/warning state
- **Alerts:** 5-20 alerts
- **Model:** Predicts anomalies (1)
- **Attack Type:** Correctly identified

## 🔧 Troubleshooting

**"Permission denied"**
```bash
sudo python3 mininet_data_generation/generate_local_pcaps.py
```

**"Mininet not found"**
```bash
sudo apt-get install -y mininet openvswitch-switch
```

**"No PCAPs generated"**
```bash
sudo mn -c  # Clean up
sudo systemctl restart openvswitch-switch
sudo python3 mininet_data_generation/generate_local_pcaps.py
```

## 📚 Full Documentation

- **Complete Guide:** `LOCAL_MININET_GUIDE.md`
- **Feature Alignment:** `FEATURE_ALIGNMENT_REPORT.md`
- **VM Setup:** `docs/VM_MININET_ARCHITECTURE.md`

---

**That's it!** You now have a working local Mininet setup. 🎉
