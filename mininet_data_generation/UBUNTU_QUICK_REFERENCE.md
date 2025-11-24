# Ubuntu Mininet VM - Quick Reference

## 🚀 Quick Setup Commands

### One-Line Setup
```bash
sudo ./setup_ubuntu_mininet.sh
```

### Manual Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Mininet
sudo apt install -y mininet

# Install Python packages
pip3 install flask flask-cors scapy

# Install network tools
sudo apt install -y tcpdump hping3 iperf3 openvswitch-switch

# Start OVS
sudo systemctl start openvswitch-switch
sudo systemctl enable openvswitch-switch

# Configure firewall
sudo ufw allow 5001/tcp
sudo ufw enable
```

## 📋 Common Commands

### Mininet
```bash
# Test Mininet
sudo mn --test pingall

# Clean up Mininet
sudo mn -c

# Check version
mn --version

# Start simple topology
sudo mn --topo single,3
```

### Open vSwitch
```bash
# Check OVS status
sudo systemctl status openvswitch-switch

# Restart OVS
sudo systemctl restart openvswitch-switch

# Show OVS configuration
sudo ovs-vsctl show

# List bridges
sudo ovs-vsctl list-br
```

### API Server
```bash
# Start API server
python3 /opt/mininet_api/vm_mininet_api.py

# Start as background service
sudo systemctl start mininet-api

# Check service status
sudo systemctl status mininet-api

# View logs
sudo journalctl -u mininet-api -f
```

### Network
```bash
# Get IP address
ip addr show

# Check listening ports
sudo netstat -tlnp

# Test API from VM
curl http://localhost:5001/health

# Test connectivity
ping <dashboard-host-ip>
```

### Firewall
```bash
# Check firewall status
sudo ufw status

# Allow port
sudo ufw allow 5001/tcp

# Disable firewall (testing only)
sudo ufw disable
```

## 🔧 Troubleshooting

### Mininet Won't Start
```bash
sudo mn -c
sudo systemctl restart openvswitch-switch
sudo mn --test pingall
```

### API Not Accessible
```bash
# Check if running
ps aux | grep vm_mininet_api

# Check port
sudo netstat -tlnp | grep 5001

# Check firewall
sudo ufw status

# Test locally
curl http://localhost:5001/health
```

### OVS Issues
```bash
# Restart OVS
sudo systemctl restart openvswitch-switch

# Check logs
sudo journalctl -u openvswitch-switch -n 50

# Rebuild database
sudo ovs-vsctl emer-reset
```

### Permission Errors
```bash
# Run Mininet with sudo
sudo mn --test pingall

# Check user groups
groups $USER

# Add to sudoers (if needed)
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/mn" | sudo tee /etc/sudoers.d/mininet
```

## 📊 System Information

### Check Versions
```bash
# Ubuntu version
lsb_release -a

# Mininet version
mn --version

# Python version
python3 --version

# OVS version
ovs-vsctl --version
```

### Resource Usage
```bash
# Memory usage
free -h

# Disk usage
df -h

# CPU usage
top

# Network interfaces
ip link show
```

## 🔌 Integration with Dashboard

### Environment Variables
```bash
# On main machine
export MININET_VM_HOST="<UBUNTU_VM_IP>"
export MININET_VM_PORT="5001"
```

### Test Connection
```bash
# From main machine
curl http://<UBUNTU_VM_IP>:5001/health

# Expected response:
# {"status": "healthy", "os": "ubuntu", "mininet_available": true}
```

## 📁 Important Directories

```
/opt/mininet_api/          # API server files
~/mininet_data_generation/ # Data generation scripts
~/mininet_data_generation/data_capture/pcaps/  # PCAP files
/var/log/mininet/          # Log files
/etc/systemd/system/       # Systemd service files
```

## 🔑 Default Ports

- **5001**: Mininet API Server
- **22**: SSH
- **6653**: OpenFlow Controller (if used)

## 💾 Backup Commands

```bash
# Backup PCAP files
tar -czf pcaps_backup.tar.gz ~/mininet_data_generation/data_capture/pcaps/

# Backup API configuration
tar -czf api_backup.tar.gz /opt/mininet_api/

# Full system backup (VM snapshot recommended instead)
```

## 🎯 Performance Tips

```bash
# Increase OVS performance
sudo ovs-vsctl set Open_vSwitch . other_config:max-idle=10000

# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable cups

# Increase file descriptors
ulimit -n 65536
```

## 📝 Useful Aliases

Add to `~/.bashrc`:
```bash
alias mnc='sudo mn -c'
alias mnt='sudo mn --test pingall'
alias ovsr='sudo systemctl restart openvswitch-switch'
alias api='python3 /opt/mininet_api/vm_mininet_api.py'
```

## 🆘 Emergency Recovery

```bash
# Complete cleanup
sudo mn -c
sudo systemctl restart openvswitch-switch
sudo ovs-vsctl emer-reset
sudo reboot

# Reinstall Mininet
sudo apt remove --purge mininet
sudo apt autoremove
sudo apt install mininet
```

## 📚 Documentation Links

- Ubuntu: https://ubuntu.com/server/docs
- Mininet: http://mininet.org/
- Open vSwitch: http://www.openvswitch.org/
- Flask: https://flask.palletsprojects.com/

## ✅ Health Check Checklist

- [ ] Ubuntu system updated
- [ ] Mininet installed and tested
- [ ] OVS running
- [ ] Python 3 and pip3 available
- [ ] Network tools installed
- [ ] API server accessible
- [ ] Firewall configured
- [ ] Can connect from main machine
- [ ] PCAP directories created
- [ ] VM snapshot taken
