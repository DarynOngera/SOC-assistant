# Complete CentOS PCAP Generation Guide

## Overview
CentOS-compatible PCAP generation scripts that handle:
- Missing tools (hping3, Apache Bench)
- Different package managers (yum vs apt)
- SELinux and firewall configurations
- Open vSwitch setup
- Automatic fallback to alternative tools

## Quick Start

### 1. Install Dependencies
```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Run the setup script
sudo bash centos_install_deps.sh
```

### 2. Generate PCAPs
```bash
# Generate all attack PCAPs
sudo bash generate_pcaps_centos.sh
```

## Detailed Installation

### Step 1: System Preparation
```bash
# Update system
sudo yum update -y

# Install EPEL repository
sudo yum install -y epel-release

# Install Python 3
sudo yum install -y python3 python3-pip python3-devel
```

### Step 2: Install Network Tools
```bash
# Essential tools
sudo yum install -y net-tools tcpdump nmap nc wget curl

# Development tools
sudo yum groupinstall -y "Development Tools"

# Open vSwitch
sudo yum install -y openvswitch
sudo systemctl start openvswitch
sudo systemctl enable openvswitch
```

### Step 3: Install Optional Tools
```bash
# Apache Bench (for HTTP flood)
sudo yum install -y httpd-tools

# hping3 (may need compilation)
# Try from EPEL first
sudo yum install -y hping3

# If not available, compile from source
cd /tmp
wget http://www.hping.org/hping3-20051105.tar.gz
tar -xzf hping3-20051105.tar.gz
cd hping3-20051105
./configure
make
sudo make install
```

### Step 4: Install Mininet
```bash
# Clone Mininet
cd /tmp
git clone https://github.com/mininet/mininet.git
cd mininet

# Install (core only)
sudo PYTHON=python3 util/install.sh -n
```

### Step 5: Install Python Packages
```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Install required packages
sudo pip3 install mininet scapy
```

## CentOS-Specific Features

### 1. Automatic Tool Detection
Scripts automatically detect available tools:
- **hping3**: If available, uses for SYN/UDP floods
- **Fallback**: Uses netcat if hping3 not found
- **Apache Bench**: If available, uses for HTTP flood
- **Fallback**: Uses curl if ab not found

### 2. Firewall Handling
```bash
# Check firewall status
sudo systemctl status firewalld

# Allow necessary traffic
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Or disable for testing
sudo systemctl stop firewalld
```

### 3. SELinux Handling
```bash
# Check SELinux status
getenforce

# Temporarily disable
sudo setenforce 0

# Permanently disable (requires reboot)
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
```

## Generated Scripts

### 1. Main Generation Script
**File**: `generate_pcaps_centos.sh`

**Features**:
- Checks all dependencies
- Detects available tools
- Backs up old PCAPs
- Generates all 4 attack types
- Verifies IPv4 content
- Shows summary

**Usage**:
```bash
sudo bash generate_pcaps_centos.sh
```

### 2. Individual Attack Scripts

#### SYN Flood
**File**: `topology/generate_syn_flood_centos.py`

**Methods**:
- Primary: hping3 (if available)
- Fallback: netcat

**Usage**:
```bash
cd topology
sudo python3 generate_syn_flood_centos.py --samples 1000
```

#### Port Scan
**File**: `topology/generate_port_scan_centos.py`

**Methods**:
- Uses nmap (always available)

**Usage**:
```bash
cd topology
sudo python3 generate_port_scan_centos.py --samples 500
```

#### UDP Flood
**File**: `topology/generate_udp_flood_centos.py`

**Methods**:
- Primary: hping3 (if available)
- Fallback: netcat

**Usage**:
```bash
cd topology
sudo python3 generate_udp_flood_centos.py --samples 1000
```

#### HTTP Flood
**File**: `topology/generate_http_flood_centos.py`

**Methods**:
- Primary: Apache Bench (if available)
- Fallback: curl

**Usage**:
```bash
cd topology
sudo python3 generate_http_flood_centos.py --samples 500
```

## Tool Comparison

### With hping3 (Recommended)
```
SYN Flood: hping3 -4 -S -p 80 --faster
UDP Flood: hping3 -4 --udp -p 53 --faster
```
**Pros**: Faster, more realistic, better control
**Cons**: May need compilation on CentOS

### Without hping3 (Fallback)
```
SYN Flood: nc (netcat) connection attempts
UDP Flood: nc -u (UDP mode)
```
**Pros**: Always available, no compilation
**Cons**: Slower, less realistic

### HTTP Flood
```
With ab: ab -n 500 -c 50 http://target/
Without ab: curl in loop
```

## Verification

### Check Generated PCAPs
```bash
# List PCAPs
ls -lh data_capture/mininet/

# Verify IPv4 content
for f in data_capture/mininet/*.pcap; do
    echo "=== $(basename $f) ==="
    tcpdump -r "$f" -c 5 2>&1 | grep "IP "
done
```

### Expected Output
```
syn_flood.pcap: 100-500 KB, IPv4 packets
port_scan.pcap: 50-200 KB, IPv4 packets
udp_flood.pcap: 100-500 KB, IPv4 packets
http_flood.pcap: 50-200 KB, IPv4 packets
```

## Troubleshooting

### Issue: "Open vSwitch not running"
```bash
# Start service
sudo systemctl start openvswitch

# Check status
sudo systemctl status openvswitch

# Check logs
sudo journalctl -u openvswitch -n 50
```

### Issue: "Mininet not found"
```bash
# Check installation
sudo mn --version

# Reinstall if needed
cd /tmp/mininet
sudo PYTHON=python3 util/install.sh -n
```

### Issue: "Permission denied"
```bash
# Always use sudo
sudo bash generate_pcaps_centos.sh

# Check file permissions
chmod +x generate_pcaps_centos.sh
chmod +x topology/generate_*_centos.py
```

### Issue: "Empty PCAPs"
```bash
# Check tcpdump is capturing
sudo tcpdump -i any -c 10

# Verify network interfaces
ip addr show

# Check Open vSwitch
sudo ovs-vsctl show
```

### Issue: "hping3 compilation fails"
```bash
# Install build dependencies
sudo yum install -y gcc make libpcap-devel

# Try compilation again
cd /tmp/hping3-20051105
make clean
./configure
make
sudo make install
```

## Performance Tuning

### For Faster Generation
```bash
# Reduce samples
sudo python3 generate_syn_flood_centos.py --samples 500

# Or use quick mode
sudo bash generate_pcaps_centos_quick.sh
```

### For Better Quality
```bash
# Increase samples
sudo python3 generate_syn_flood_centos.py --samples 5000

# Use hping3 if available
sudo yum install -y hping3
```

## Infrastructure Deployment

### For Production CentOS Server
```bash
# 1. Install on server
ssh user@centos-server
cd /path/to/SOC-assistant/mininet_data_generation
sudo bash centos_install_deps.sh

# 2. Generate PCAPs
sudo bash generate_pcaps_centos.sh

# 3. Copy to development machine
scp data_capture/mininet/*.pcap user@dev-machine:/path/to/project/
```

### For CI/CD Pipeline
```yaml
# .gitlab-ci.yml or similar
generate_pcaps:
  image: centos:8
  script:
    - cd mininet_data_generation
    - bash centos_install_deps.sh
    - bash generate_pcaps_centos.sh
  artifacts:
    paths:
      - mininet_data_generation/data_capture/mininet/*.pcap
```

## Differences from Ubuntu/Debian

| Feature | Ubuntu/Debian | CentOS |
|---------|--------------|--------|
| Package Manager | apt-get | yum |
| EPEL | Not needed | Required |
| hping3 | In repos | May need compilation |
| Apache Bench | apache2-utils | httpd-tools |
| SELinux | Usually disabled | Usually enabled |
| Firewall | ufw | firewalld |
| Python | python3 | python3 (EPEL) |

## Result

CentOS-compatible PCAP generation with:
- ✅ Automatic tool detection
- ✅ Fallback mechanisms
- ✅ IPv4 traffic generation
- ✅ Production-ready
- ✅ Infrastructure-friendly
- ✅ No manual intervention needed

**Ready for CentOS infrastructure deployment!** 🎯
