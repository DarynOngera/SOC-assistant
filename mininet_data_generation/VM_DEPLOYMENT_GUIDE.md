# Mininet Pipeline VM Deployment Guide

## 🖥️ VM Requirements

### Minimum System Requirements
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS (recommended)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB minimum, 100GB recommended
- **CPU**: 4 cores minimum, 8 cores recommended
- **Network**: NAT or Bridged networking

### VM Platform Support
- **VMware Workstation/Player** ✅ (recommended)
- **VirtualBox** ✅ (good performance)
- **KVM/QEMU** ✅ (Linux hosts)
- **Hyper-V** ✅ (Windows hosts)
- **Cloud VMs** ✅ (AWS, GCP, Azure)

---

## 🚀 Quick VM Setup

### Option 1: Automated Setup Script
```bash
# Download and run the automated setup
wget https://raw.githubusercontent.com/your-repo/SOC-assistant/main/mininet_data_generation/setup_vm_mininet.sh
chmod +x setup_vm_mininet.sh
sudo ./setup_vm_mininet.sh
```

### Option 2: Manual Setup
```bash
# Clone the repository
git clone https://github.com/your-repo/SOC-assistant.git
cd SOC-assistant/mininet_data_generation

# Run the VM setup script
sudo ./setup_vm_mininet.sh
```

---

## 🔧 VM Configuration

### 1. Network Configuration
```bash
# Recommended VM network settings:
# - NAT network for internet access
# - Host-only adapter for dashboard access
# - Disable WiFi inside VM (use Ethernet only)

# Check network interfaces
ip addr show

# Verify internet connectivity
ping -c 3 8.8.8.8
```

### 2. VM Resource Allocation
```bash
# Check allocated resources
echo "CPU cores: $(nproc)"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "Disk space: $(df -h / | tail -1 | awk '{print $4}')"
```

### 3. Enable Nested Virtualization (if needed)
```bash
# For VMware: Enable "Virtualize Intel VT-x/EPT or AMD-V/RVI"
# For VirtualBox: Enable "Enable Nested VT-x/AMD-V"
# For KVM: Already supported

# Verify virtualization support
egrep -c '(vmx|svm)' /proc/cpuinfo
```

---

## 📦 Installation Steps

### Step 1: System Updates
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git build-essential
```

### Step 2: Install Mininet
```bash
# Option A: Package manager (faster)
sudo apt install -y mininet

# Option B: From source (latest features)
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a
cd ..
```

### Step 3: Install Python Dependencies
```bash
# Install Python 3.8+
sudo apt install -y python3 python3-pip python3-venv

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### Step 4: Install Network Tools
```bash
sudo apt install -y tcpdump hping3 nmap netcat-openbsd iperf3
```

### Step 5: Configure Permissions
```bash
# Add user to required groups
sudo usermod -a -G sudo $USER
sudo usermod -a -G wireshark $USER

# Set capabilities for network tools
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/tcpdump
```

---

## 🛡️ VM Security & Isolation

### Network Isolation
```bash
# Create isolated network namespace for Mininet
sudo ip netns add mininet_isolated
sudo ip netns exec mininet_isolated ip link set lo up

# Run Mininet in isolated namespace
sudo ip netns exec mininet_isolated mn --topo single,3
```

### Firewall Configuration
```bash
# Enable UFW firewall
sudo ufw enable

# Allow SSH (if needed)
sudo ufw allow ssh

# Allow dashboard access from host
sudo ufw allow from 192.168.0.0/16 to any port 5000
sudo ufw allow from 10.0.0.0/8 to any port 5000
```

### Resource Limits
```bash
# Set memory limits for Mininet processes
echo "mininet soft memlock 4194304" | sudo tee -a /etc/security/limits.conf
echo "mininet hard memlock 4194304" | sudo tee -a /etc/security/limits.conf
```

---

## 🏃 Running the Pipeline

### Quick Start
```bash
cd /path/to/SOC-assistant/mininet_data_generation

# Test installation
./test_vm_installation.sh

# Run complete pipeline
sudo ./run_vm_pipeline.sh
```

### Step-by-Step Execution
```bash
# 1. Generate normal traffic (5-10 minutes)
sudo python3 topology/generate_normal_traffic.py --samples 50000

# 2. Generate attack traffic (2-5 minutes)
sudo python3 topology/generate_attack_traffic.py --samples 15000

# 3. Process captured data
python3 data_capture/preprocess_pcap.py

# 4. Train models
python3 models/train_mininet_models.py

# 5. Integrate with dashboard
python3 integration/integrate_dashboard.py
```

---

## 📊 Performance Optimization

### VM Performance Tuning
```bash
# Increase VM RAM allocation (in VM settings)
# - Minimum: 8GB
# - Recommended: 16GB
# - Optimal: 32GB

# Enable hardware acceleration
# - VMware: Enable "Accelerate 3D graphics"
# - VirtualBox: Enable "Enable 3D Acceleration"

# Allocate more CPU cores
# - Minimum: 4 cores
# - Recommended: 8 cores
```

### Mininet Optimization
```bash
# Use faster controller
sudo mn --controller=remote,ip=127.0.0.1,port=6653

# Optimize Open vSwitch
sudo ovs-vsctl set Open_vSwitch . other_config:max-idle=10000
sudo ovs-vsctl set Open_vSwitch . other_config:flow-eviction-threshold=1000
```

### Storage Optimization
```bash
# Use SSD storage if available
# Enable write caching in VM settings
# Allocate sufficient disk space (100GB+)

# Check disk performance
sudo hdparm -Tt /dev/sda
```

---

## 🔍 Monitoring & Debugging

### System Monitoring
```bash
# Monitor resource usage during pipeline execution
htop

# Monitor network interfaces
sudo iftop

# Monitor disk I/O
sudo iotop
```

### Mininet Debugging
```bash
# Check Mininet status
sudo mn --version
sudo mn --test pingall

# View Open vSwitch status
sudo ovs-vsctl show
sudo ovs-ofctl dump-flows s1

# Check for orphaned processes
ps aux | grep -E "(mininet|ovs|controller)"
```

### Log Analysis
```bash
# View system logs
sudo journalctl -f

# View Mininet logs
tail -f /var/log/mininet.log

# View pipeline logs
tail -f data_capture/pipeline.log
```

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Permission Denied Errors
```bash
# Solution: Run with sudo or fix permissions
sudo chown -R $USER:$USER /path/to/SOC-assistant
sudo chmod +x mininet_data_generation/*.py
```

#### 2. Network Interface Issues
```bash
# Solution: Clean up and restart
sudo mn -c
sudo systemctl restart openvswitch-switch
sudo systemctl restart networking
```

#### 3. Memory Issues
```bash
# Solution: Increase VM RAM or reduce sample size
# Edit pipeline scripts to use fewer samples
python3 run_mininet_pipeline.py --samples 10000
```

#### 4. Disk Space Issues
```bash
# Solution: Clean up old files
sudo rm -rf data_capture/pcaps/*.pcap.old
sudo apt autoremove && sudo apt autoclean
```

### Recovery Commands
```bash
# Emergency cleanup
sudo mn -c
sudo killall -9 controller ovs-vswitchd ovsdb-server
sudo systemctl restart openvswitch-switch

# Network reset
sudo systemctl restart NetworkManager
sudo dhclient -r && sudo dhclient
```

---

## 📈 Expected Results

### Data Generation
- **Normal Traffic**: 70,000 samples (70%)
- **Attack Traffic**: 30,000 samples (30%)
- **Total Runtime**: 15-25 minutes
- **Output Size**: ~2-5GB

### Model Training
- **Training Time**: 5-15 minutes
- **Model Accuracy**: 85-95%
- **False Positive Rate**: <5%

### Dashboard Integration
- **Real-time Detection**: <1 second response
- **Alert Generation**: Immediate
- **Network Visualization**: Live topology

---

## 🎯 Next Steps

After successful pipeline execution:

1. **Start Dashboard**:
   ```bash
   cd .. && python scripts/start_dashboard.py
   ```

2. **Access Dashboard**:
   - URL: `http://VM_IP:5000`
   - Default credentials in `users.json`

3. **Test Real-time Detection**:
   ```bash
   sudo python3 simulation/realtime_attack_sim.py
   ```

4. **Review Results**:
   - Model reports: `reports/`
   - Processed data: `data_capture/processed/`
   - Integration logs: `integration/logs/`

---

## 🔗 Additional Resources

- [Mininet Documentation](http://mininet.org/walkthrough/)
- [Open vSwitch Manual](http://www.openvswitch.org/support/dist-docs/)
- [VM Performance Tuning Guide](./VM_PERFORMANCE_GUIDE.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review system logs: `sudo journalctl -f`
3. Run diagnostics: `./test_vm_installation.sh`
4. Create an issue with full error logs

**VM Deployment Complete!** 🎉
