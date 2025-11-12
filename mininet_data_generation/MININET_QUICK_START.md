# Mininet Quick Start - Generate 100k Real Samples

## 🚀 Quick Commands

### 1. Check Mininet Installation

```bash
sudo mn --version
```

If not installed:
```bash
sudo apt-get update && sudo apt-get install mininet
```

### 2. Backup Network (Safety First!)

```bash
# Backup network config
sudo cp /etc/network/interfaces /etc/network/interfaces.backup 2>/dev/null
ip addr show > ~/network_backup_$(date +%Y%m%d).txt

# Note your current WiFi/network
nmcli device status
```

### 3. Generate 100k Samples

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Make scripts executable
chmod +x run_mininet_pipeline.py
chmod +x topology/*.py

# Run pipeline (will prompt for confirmation)
sudo python3 run_mininet_pipeline.py --samples 100000
```

**Time estimate:** 20-30 minutes for 100k samples

---

## 📊 What Gets Generated

### Traffic Distribution
- **70,000 normal** traffic samples
  - HTTP/HTTPS requests
  - SSH sessions
  - DNS queries
  - FTP transfers
  - Database connections

- **30,000 attack** samples
  - 10,000 SYN flood
  - 10,000 Port scans
  - 5,000 UDP flood
  - 5,000 HTTP flood

### Output Files
```
data_capture/mininet/
├── normal_traffic.pcap          # Normal traffic capture
├── syn_flood.pcap                # SYN flood attacks
├── port_scan.pcap                # Port scan attacks
├── udp_flood.pcap                # UDP flood attacks
├── http_flood.pcap               # HTTP flood attacks
└── processed/
    └── mininet_dataset_*.csv     # Final ML-ready dataset
```

---

## 🛡️ Safety Features Built-In

1. **Root check** - Ensures proper privileges
2. **Mininet check** - Verifies installation
3. **Cleanup before/after** - Removes orphaned processes
4. **Confirmation prompt** - Asks before starting
5. **Network restore** - Cleans up after completion

---

## 🔧 Advanced Options

### Custom Sample Count

```bash
# Generate 50k samples
sudo python3 run_mininet_pipeline.py --samples 50000

# Generate 200k samples (will take longer)
sudo python3 run_mininet_pipeline.py --samples 200000
```

### Skip Safety Prompts (Not Recommended)

```bash
sudo python3 run_mininet_pipeline.py --samples 100000 --skip-checks
```

### Generate Only Normal Traffic

```bash
cd topology
sudo python3 generate_normal_traffic.py --samples 70000 --output ../data_capture/mininet/normal.pcap
```

### Generate Only Attacks

```bash
cd topology
sudo python3 generate_syn_flood.py --samples 10000 --output ../data_capture/mininet/syn.pcap
```

---

## 🐛 Troubleshooting

### Issue: "Mininet not found"

```bash
# Install Mininet
sudo apt-get update
sudo apt-get install mininet

# Or from source
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a
```

### Issue: "Permission denied"

```bash
# Must run as root
sudo python3 run_mininet_pipeline.py
```

### Issue: "Network not working after Mininet"

```bash
# Clean up Mininet
sudo mn -c

# Restart NetworkManager
sudo systemctl restart NetworkManager

# Or restore backup
sudo cp /etc/network/interfaces.backup /etc/network/interfaces
sudo systemctl restart networking

# Reconnect to WiFi
nmcli device wifi connect "YourSSID" password "YourPassword"
```

### Issue: "OVS switch errors"

```bash
# Restart Open vSwitch
sudo systemctl restart openvswitch-switch

# Or reinstall
sudo apt-get install --reinstall openvswitch-switch
```

### Issue: "Port already in use"

```bash
# Kill existing processes
sudo killall -9 controller
sudo killall -9 ovs-vswitchd
sudo killall -9 ovsdb-server

# Clean Mininet
sudo mn -c
```

---

## 📈 Monitoring Progress

### Watch Generation Progress

```bash
# In another terminal
watch -n 5 'ls -lh data_capture/mininet/*.pcap'
```

### Check Packet Counts

```bash
# Count packets in PCAP files
for f in data_capture/mininet/*.pcap; do
    echo "$f: $(tcpdump -r $f 2>/dev/null | wc -l) packets"
done
```

### Monitor System Resources

```bash
# Watch CPU/Memory
htop

# Or
watch -n 2 'ps aux | grep python'
```

---

## ✅ Verification

### After Generation Completes

```bash
# Check output file
ls -lh data_capture/mininet/processed/*.csv

# Count records
wc -l data_capture/mininet/processed/*.csv

# Preview data
head -20 data_capture/mininet/processed/*.csv
```

### Expected Output

```
mininet_dataset_20251008_002200.csv: 100001 lines (100k + header)
File size: ~15-25 MB
Columns: 24-30 features
```

---

## 🎯 Next Steps After Generation

### 1. Train Models

```bash
cd models
python3 train_mininet_models.py
```

### 2. Integrate with Dashboard

```bash
cd integration
python3 integrate_dashboard.py
```

### 3. Test Models

```bash
# Generate new test data
sudo python3 run_mininet_pipeline.py --samples 10000

# Test models on new data
python3 test_models.py
```

---

## 💡 Tips for Best Results

1. **Close other applications** - Mininet needs resources
2. **Use wired connection** - More stable than WiFi
3. **Run during off-hours** - Less network interference
4. **Monitor disk space** - PCAP files can be large
5. **Keep terminal open** - Don't close during generation

---

## 🆘 Emergency Stop

If something goes wrong:

```bash
# Press Ctrl+C in the terminal

# Then clean up
sudo mn -c
sudo killall -9 python3
sudo systemctl restart NetworkManager

# Verify network restored
ping -c 3 8.8.8.8
```

---

## 📞 Need Help?

Check these files:
- `MININET_SETUP_GUIDE.md` - Detailed setup
- `NETWORK_SAFE_README.md` - Safety information
- `OVERFITTING_PREVENTION.md` - Model training tips

---

**Ready to generate real network data with Mininet!** 🚀

Just run:
```bash
sudo python3 run_mininet_pipeline.py --samples 100000
```
