# CentOS VM Deployment Guide for Mininet Pipeline

## 🐧 CentOS-Specific Setup

### Supported CentOS Versions
- **CentOS 7** ✅ (with EPEL)
- **CentOS 8** ✅ (with PowerTools)
- **CentOS 9** ✅ (with CRB)
- **RHEL 7/8/9** ✅ (Red Hat Enterprise Linux)
- **Rocky Linux 8/9** ✅
- **AlmaLinux 8/9** ✅

---

## 🚀 Quick CentOS Setup

### Automated Installation
```bash
# Download and run CentOS setup script
wget https://raw.githubusercontent.com/your-repo/SOC-assistant/main/mininet_data_generation/setup_centos_mininet.sh
chmod +x setup_centos_mininet.sh
sudo ./setup_centos_mininet.sh
```

### Manual CentOS Setup
```bash
# Clone repository
git clone https://github.com/your-repo/SOC-assistant.git
cd SOC-assistant/mininet_data_generation

# Run CentOS-specific setup
sudo ./setup_centos_mininet.sh
```

---

## 🔧 CentOS-Specific Configuration

### 1. Repository Setup

#### CentOS 7
```bash
# Enable EPEL repository
sudo yum install -y epel-release

# Enable Software Collections
sudo yum install -y centos-release-scl

# Update system
sudo yum update -y
```

#### CentOS 8
```bash
# Enable EPEL and PowerTools
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled powertools

# Update system
sudo dnf update -y
```

#### CentOS 9
```bash
# Enable EPEL and CRB (CodeReady Builder)
sudo dnf install -y epel-release
sudo dnf config-manager --set-enabled crb

# Update system
sudo dnf update -y
```

### 2. Firewall Configuration (firewalld)
```bash
# Start and enable firewalld
sudo systemctl enable firewalld
sudo systemctl start firewalld

# Allow SSH
sudo firewall-cmd --permanent --add-service=ssh

# Allow dashboard access
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp

# Allow VM network ranges
sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='192.168.0.0/16' accept"
sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='10.0.0.0/8' accept"

# Reload firewall
sudo firewall-cmd --reload

# Check status
sudo firewall-cmd --list-all
```

### 3. SELinux Configuration
```bash
# Check SELinux status
sestatus

# Set to permissive mode (if needed for Mininet)
sudo setenforce 0

# Make permanent (optional, less secure)
sudo sed -i 's/SELINUX=enforcing/SELINUX=permissive/' /etc/selinux/config

# Or create custom SELinux policy (recommended for production)
sudo setsebool -P httpd_can_network_connect 1
```

---

## 📦 Package Installation

### Development Tools
```bash
# CentOS 7
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3 python3-pip python3-devel

# CentOS 8/9
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y python3 python3-pip python3-devel
```

### Mininet Installation (From Source)
```bash
# Install dependencies
sudo dnf install -y git python3-devel openvswitch openvswitch-devel kernel-devel

# Clone and install Mininet
cd /tmp
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -n

# Verify installation
sudo mn --version
```

### Network Tools
```bash
# CentOS 7
sudo yum install -y tcpdump wireshark-cli hping3 nmap nmap-ncat iperf3

# CentOS 8/9
sudo dnf install -y tcpdump wireshark-cli hping3 nmap nmap-ncat iperf3
```

---

## 🔧 CentOS-Specific Optimizations

### System Service Management
```bash
# Enable and start required services
sudo systemctl enable openvswitch
sudo systemctl start openvswitch

# Check service status
sudo systemctl status openvswitch
sudo systemctl status firewalld
```

### Network Namespace Setup
```bash
# Create isolated namespace
sudo ip netns add mininet_isolated
sudo ip netns exec mininet_isolated ip link set lo up

# List namespaces
sudo ip netns list

# Test namespace
sudo ip netns exec mininet_isolated ping -c 3 127.0.0.1
```

### Performance Tuning
```bash
# Optimize kernel parameters
echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
echo 'vm.swappiness = 10' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

---

## 🏃 Running the Pipeline

### CentOS Pipeline Execution
```bash
# Test installation
./test_centos_installation.sh

# Run optimized pipeline
./run_centos_pipeline.sh

# Monitor execution
watch -n 5 'ps aux | grep -E "(mininet|python3)" | grep -v grep'
```

### Expected Output
```
============================================================
MININET PIPELINE - CENTOS EXECUTION
============================================================
OS: CentOS Linux release 8.4.2105
VM Resources:
  RAM: 16Gi
  CPU: 8 cores
  Disk: 75G available

✓ Open vSwitch is running
Step 1: Generating normal traffic (optimized for CentOS VM)...
Step 2: Generating attack traffic...
Step 3: Processing captured data...
Step 4: Training models...
Step 5: Integrating with dashboard...

============================================================
CENTOS PIPELINE COMPLETED!
============================================================
Generated samples: 35,000 (optimized for CentOS VM)
```

---

## 🔍 CentOS Troubleshooting

### Common CentOS Issues

#### 1. Package Installation Failures
```bash
# Problem: Package not found
# Solution: Enable additional repositories
sudo dnf install epel-release
sudo dnf config-manager --set-enabled powertools  # CentOS 8
sudo dnf config-manager --set-enabled crb         # CentOS 9
```

#### 2. Firewall Blocking Connections
```bash
# Problem: Cannot access dashboard
# Solution: Configure firewall
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# Check if port is open
sudo firewall-cmd --list-ports
```

#### 3. SELinux Preventing Execution
```bash
# Problem: Permission denied with SELinux
# Solution: Check SELinux context
ls -Z /path/to/file

# Temporary fix
sudo setenforce 0

# Permanent fix (create policy)
sudo setsebool -P httpd_can_network_connect 1
```

#### 4. Python Path Issues
```bash
# Problem: Python modules not found
# Solution: Check Python path
python3 -c "import sys; print(sys.path)"

# Add to PATH if needed
export PYTHONPATH=/home/$USER/.local/lib/python3.*/site-packages:$PYTHONPATH
```

#### 5. Open vSwitch Issues
```bash
# Problem: OVS not starting
# Solution: Check and restart service
sudo systemctl status openvswitch
sudo systemctl restart openvswitch

# Check OVS database
sudo ovs-vsctl show
```

### Diagnostic Commands
```bash
# System information
cat /etc/centos-release
uname -a
free -h
df -h

# Network configuration
ip addr show
sudo firewall-cmd --list-all
sestatus

# Service status
sudo systemctl status openvswitch
sudo systemctl status firewalld

# Mininet testing
sudo mn --test pingall
sudo ovs-vsctl show
```

---

## 📊 Performance Expectations

### CentOS Performance Comparison

| CentOS Version | Package Manager | Performance | Notes |
|----------------|-----------------|-------------|-------|
| CentOS 7 | yum | Good | Older packages, stable |
| CentOS 8 | dnf | Better | Modern packages, faster |
| CentOS 9 | dnf | Best | Latest features, optimal |

### Resource Usage
```bash
# Monitor during pipeline execution
htop
iotop
iftop

# Check memory usage
free -h
cat /proc/meminfo

# Check disk usage
df -h
du -sh data_capture/
```

---

## 🔧 Advanced CentOS Configuration

### Custom Kernel Parameters
```bash
# Create custom sysctl configuration
sudo tee /etc/sysctl.d/99-mininet.conf << EOF
# Mininet optimizations
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

# Apply configuration
sudo sysctl -p /etc/sysctl.d/99-mininet.conf
```

### Systemd Service for Pipeline
```bash
# Create systemd service
sudo tee /etc/systemd/system/mininet-pipeline.service << EOF
[Unit]
Description=Mininet SOC Pipeline
After=network.target openvswitch.service

[Service]
Type=oneshot
User=root
WorkingDirectory=/path/to/SOC-assistant/mininet_data_generation
ExecStart=/path/to/SOC-assistant/mininet_data_generation/run_centos_pipeline.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mininet-pipeline.service
```

### Log Rotation Configuration
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/mininet-pipeline << EOF
/tmp/centos_mininet_setup.log
/path/to/SOC-assistant/mininet_data_generation/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF
```

---

## 🎯 CentOS Deployment Checklist

### Pre-Installation
- [ ] CentOS 7/8/9 VM with 8GB+ RAM, 4+ CPU cores
- [ ] Internet connectivity for package downloads
- [ ] Sufficient disk space (50GB+ available)
- [ ] VM tools installed (VMware Tools, VirtualBox Guest Additions)

### Installation
- [ ] EPEL repository enabled
- [ ] PowerTools/CRB repository enabled (CentOS 8/9)
- [ ] Development tools installed
- [ ] Python 3 and pip installed
- [ ] Mininet installed from source
- [ ] Open vSwitch installed and running

### Configuration
- [ ] Firewalld configured for dashboard access
- [ ] SELinux configured (permissive or custom policy)
- [ ] Network namespace created
- [ ] System limits configured
- [ ] Performance optimizations applied

### Testing
- [ ] Python imports working
- [ ] Mininet ping test passes
- [ ] Open vSwitch running
- [ ] Network tools available
- [ ] Firewall ports open

### Execution
- [ ] Pipeline runs without errors
- [ ] Data files generated successfully
- [ ] Models trained successfully
- [ ] Dashboard integration working
- [ ] Real-time detection functional

---

## 📞 CentOS Support Resources

### Official Documentation
- [CentOS Documentation](https://docs.centos.org/)
- [RHEL Documentation](https://access.redhat.com/documentation/)
- [Mininet Documentation](http://mininet.org/)

### Community Support
- [CentOS Forums](https://forums.centos.org/)
- [Stack Overflow CentOS Tag](https://stackoverflow.com/questions/tagged/centos)
- [Reddit r/CentOS](https://www.reddit.com/r/CentOS/)

### Troubleshooting Resources
- [CentOS Wiki](https://wiki.centos.org/)
- [RHEL Troubleshooting Guide](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/)

**CentOS VM Deployment Ready!** 🐧🚀
