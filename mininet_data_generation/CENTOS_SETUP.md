# CentOS Mininet Setup for PCAP Generation

## System Requirements
- CentOS 7 or 8
- Root access (sudo)
- Python 3.6+
- Network connectivity

## Installation Steps

### 1. Install System Dependencies

```bash
# Update system
sudo yum update -y

# Install EPEL repository (required for many packages)
sudo yum install -y epel-release

# Install Python 3 and pip
sudo yum install -y python3 python3-pip python3-devel

# Install development tools
sudo yum groupinstall -y "Development Tools"

# Install network tools
sudo yum install -y net-tools tcpdump nmap nc wget curl

# Install Open vSwitch
sudo yum install -y openvswitch
sudo systemctl start openvswitch
sudo systemctl enable openvswitch

# Install hping3 (may need to compile from source on CentOS)
# Option 1: Try from EPEL
sudo yum install -y hping3

# Option 2: If not available, compile from source
# cd /tmp
# wget http://www.hping.org/hping3-20051105.tar.gz
# tar -xzf hping3-20051105.tar.gz
# cd hping3-20051105
# ./configure
# make
# sudo make install
```

### 2. Install Mininet

```bash
# Clone Mininet repository
cd /tmp
git clone https://github.com/mininet/mininet.git
cd mininet

# Install Mininet (core only, no GUI)
sudo PYTHON=python3 util/install.sh -n

# Verify installation
sudo mn --version
```

### 3. Install Python Dependencies

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Install required Python packages
sudo pip3 install mininet scapy
```

### 4. Configure Firewall (if enabled)

```bash
# Check if firewalld is running
sudo systemctl status firewalld

# If running, allow necessary traffic
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload

# Or disable firewall for testing (not recommended for production)
# sudo systemctl stop firewalld
# sudo systemctl disable firewalld
```

### 5. Disable SELinux (if causing issues)

```bash
# Check SELinux status
getenforce

# Temporarily disable (until reboot)
sudo setenforce 0

# Permanently disable (edit /etc/selinux/config)
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config
```

## Troubleshooting

### Issue: "hping3 not found"
```bash
# Install from source
cd /tmp
wget http://www.hping.org/hping3-20051105.tar.gz
tar -xzf hping3-20051105.tar.gz
cd hping3-20051105
./configure
make
sudo make install
```

### Issue: "Open vSwitch not starting"
```bash
# Check status
sudo systemctl status openvswitch

# Restart service
sudo systemctl restart openvswitch

# Check logs
sudo journalctl -u openvswitch -n 50
```

### Issue: "Mininet installation fails"
```bash
# Try minimal installation
cd /tmp/mininet
sudo PYTHON=python3 util/install.sh -n -s /tmp/mininet

# Or install manually
sudo pip3 install mininet
```

### Issue: "Permission denied" errors
```bash
# Ensure you're running with sudo
sudo python3 generate_pcaps_centos.py

# Check file permissions
ls -la topology/
```

## Verification

```bash
# Test Mininet
sudo mn --test pingall

# Test tcpdump
sudo tcpdump --version

# Test hping3
hping3 --version

# Test nmap
nmap --version

# Test Open vSwitch
sudo ovs-vsctl show
```

## Next Steps

After successful installation, use the CentOS-compatible generation scripts:
```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation
sudo bash generate_pcaps_centos.sh
```
