# Mininet Setup Guide - Safe Usage

## ⚠️ Important Safety Notes

**Before running Mininet:**
1. **Disconnect from WiFi** or use Ethernet only
2. **Run on isolated network** if possible
3. **Use virtual machine** (recommended)
4. **Backup your network settings**

---

## 🔧 Installation

### Check if Mininet is installed

```bash
sudo mn --version
```

### Install Mininet (if not installed)

```bash
# Option 1: From package manager (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install mininet

# Option 2: From source (latest version)
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a

# Verify installation
sudo mn --version
sudo mn --test pingall
```

---

## 🛡️ Safety Precautions

### 1. Create Network Backup

```bash
# Backup current network configuration
sudo cp /etc/network/interfaces /etc/network/interfaces.backup
sudo cp /etc/resolv.conf /etc/resolv.conf.backup
ip addr show > ~/network_config_backup.txt
```

### 2. Clean Up Before Starting

```bash
# Clean any existing Mininet processes
sudo mn -c

# Check for orphaned processes
ps aux | grep mininet
ps aux | grep ovs
```

### 3. Use Isolated Mode

```bash
# Run Mininet in a separate network namespace
sudo ip netns add mininet_ns
sudo ip netns exec mininet_ns mn
```

---

## 🚀 Quick Start

### Test Mininet Works

```bash
# Simple test
sudo mn --test pingall

# If successful, you'll see:
# *** Ping: testing ping reachability
# h1 -> h2
# h2 -> h1
# *** Results: 0% dropped
```

### Generate 100k Records

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Run the complete pipeline
sudo python3 run_mininet_pipeline.py --samples 100000
```

---

## 📊 Data Generation Pipeline

I'll create scripts for:
1. **Mininet topology** - Network setup
2. **Traffic generation** - Normal + attack traffic
3. **Packet capture** - tcpdump/tshark
4. **Feature extraction** - Convert to ML features
5. **Data processing** - Clean and format

---

## 🔄 After Mininet Usage

### Clean Up

```bash
# Stop Mininet
sudo mn -c

# Kill any remaining processes
sudo killall -9 controller
sudo killall -9 ovs-vswitchd
sudo killall -9 ovsdb-server

# Restore network (if needed)
sudo systemctl restart NetworkManager
```

### Verify Network Restored

```bash
# Check network connectivity
ping -c 3 8.8.8.8

# Check WiFi
nmcli device status

# If issues, restore backup
sudo cp /etc/network/interfaces.backup /etc/network/interfaces
sudo systemctl restart networking
```

---

## 🎯 Next Steps

1. **Confirm Mininet is installed**
2. **Backup network settings**
3. **I'll create the Mininet scripts**
4. **Generate 100k real network samples**

Ready to proceed?
