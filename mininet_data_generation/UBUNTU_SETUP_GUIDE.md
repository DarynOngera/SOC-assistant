# Ubuntu Mininet VM Setup Guide

## Overview
This guide covers setting up Mininet on Ubuntu for the SOC Dashboard project. Ubuntu provides better package management and easier setup compared to CentOS.

## System Requirements
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS (recommended)
- **RAM**: Minimum 2GB, recommended 4GB
- **CPU**: 2 cores minimum
- **Disk**: 20GB minimum
- **Network**: Bridge or NAT networking with port forwarding

## Quick Setup

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Mininet
```bash
# Install from Ubuntu repositories (easiest method)
sudo apt install -y mininet

# OR install from source for latest version
cd ~
git clone https://github.com/mininet/mininet
cd mininet
git checkout 2.3.0
sudo PYTHON=python3 ./util/install.sh -a

# Verify installation
sudo mn --version
```

### 3. Install Python Dependencies
```bash
# Install Python 3 and pip
sudo apt install -y python3 python3-pip python3-venv

# Install required packages
pip3 install flask flask-cors scapy
```

### 4. Install Network Tools
```bash
sudo apt install -y \
    tcpdump \
    wireshark \
    tshark \
    hping3 \
    iperf3 \
    net-tools \
    iproute2 \
    openvswitch-switch
```

### 5. Configure Open vSwitch
```bash
# Start and enable OVS
sudo systemctl start openvswitch-switch
sudo systemctl enable openvswitch-switch

# Verify OVS is running
sudo ovs-vsctl show
```

### 6. Setup Mininet API Server
```bash
# Create directory for the API
mkdir -p ~/mininet_api
cd ~/mininet_api

# Copy the API server file (from your main machine)
# scp user@mainmachine:/path/to/vm_mininet_api.py ~/mininet_api/

# Or create it directly
cat > ~/mininet_api/vm_mininet_api.py << 'EOF'
#!/usr/bin/env python3
"""
Mininet VM API Server for SOC Dashboard
Runs on Ubuntu VM to handle Mininet operations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import signal
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store running processes
running_processes = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'os': 'ubuntu',
        'mininet_available': check_mininet_available()
    })

def check_mininet_available():
    """Check if Mininet is available"""
    try:
        result = subprocess.run(['which', 'mn'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

@app.route('/start', methods=['POST'])
def start_simulation():
    """Start Mininet simulation"""
    try:
        data = request.json
        topology = data.get('topology', 'single')
        attack_type = data.get('attack_type', 'normal')
        
        logger.info(f"Starting simulation: topology={topology}, attack={attack_type}")
        
        # Start simulation script
        # Implementation depends on your specific scripts
        
        return jsonify({
            'success': True,
            'message': 'Simulation started',
            'topology': topology,
            'attack_type': attack_type
        })
    except Exception as e:
        logger.error(f"Error starting simulation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_simulation():
    """Stop running simulation"""
    try:
        # Clean up Mininet
        subprocess.run(['sudo', 'mn', '-c'], check=True)
        
        return jsonify({
            'success': True,
            'message': 'Simulation stopped'
        })
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
EOF

chmod +x ~/mininet_api/vm_mininet_api.py
```

### 7. Create Systemd Service (Optional)
```bash
sudo tee /etc/systemd/system/mininet-api.service << EOF
[Unit]
Description=Mininet API Server
After=network.target openvswitch-switch.service

[Service]
Type=simple
User=root
WorkingDirectory=/home/$(whoami)/mininet_api
ExecStart=/usr/bin/python3 /home/$(whoami)/mininet_api/vm_mininet_api.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable mininet-api
sudo systemctl start mininet-api

# Check status
sudo systemctl status mininet-api
```

### 8. Configure Firewall
```bash
# Allow API port
sudo ufw allow 5001/tcp

# Allow SSH
sudo ufw allow 22/tcp

# Enable firewall
sudo ufw enable
```

### 9. Test Installation
```bash
# Test Mininet
sudo mn --test pingall

# Test API server
curl http://localhost:5001/health
```

## Network Configuration

### Bridge Networking (Recommended)
```bash
# VM should have bridge adapter configured in VirtualBox/VMware
# Get IP address
ip addr show

# Note the IP address for configuration in main dashboard
```

### Port Forwarding (Alternative)
If using NAT networking, forward port 5001:
- Host: localhost:5001
- Guest: <VM_IP>:5001

## PCAP Directory Setup
```bash
# Create directories for PCAP files
mkdir -p ~/mininet_data_generation/data_capture/mininet
mkdir -p ~/mininet_data_generation/data_capture/pcaps

# Set permissions
chmod -R 755 ~/mininet_data_generation
```

## Troubleshooting

### Mininet Won't Start
```bash
# Clean up any existing Mininet processes
sudo mn -c

# Check OVS status
sudo systemctl status openvswitch-switch

# Restart OVS if needed
sudo systemctl restart openvswitch-switch
```

### Permission Errors
```bash
# Mininet requires root privileges
# Run with sudo or add user to sudoers for specific commands
```

### API Server Not Accessible
```bash
# Check if service is running
sudo systemctl status mininet-api

# Check firewall
sudo ufw status

# Check if port is listening
sudo netstat -tlnp | grep 5001
```

## Integration with SOC Dashboard

### Update Dashboard Configuration
On your main machine, update the environment variables:

```bash
# In your .env file or export directly
export MININET_VM_HOST="<UBUNTU_VM_IP>"
export MININET_VM_PORT="5001"
```

### Test Connection
```bash
# From main machine
curl http://<UBUNTU_VM_IP>:5001/health
```

## Performance Optimization

### Increase OVS Performance
```bash
# Increase OVS limits
sudo ovs-vsctl set Open_vSwitch . other_config:max-idle=10000
```

### Disable Unnecessary Services
```bash
# Disable services you don't need
sudo systemctl disable bluetooth
sudo systemctl disable cups
```

## Backup and Snapshot
After successful setup:
1. Take a VM snapshot
2. Export VM for backup
3. Document your VM IP address

## Advantages of Ubuntu over CentOS
- ✅ Better package availability
- ✅ Easier Mininet installation
- ✅ More up-to-date packages
- ✅ Better community support
- ✅ Simpler dependency management
- ✅ Native Python 3 support

## Next Steps
1. Generate PCAP files using Mininet
2. Configure dashboard to connect to Ubuntu VM
3. Test simulation workflows
4. Set up automated PCAP generation

## Support
For issues specific to Ubuntu setup, check:
- Ubuntu documentation: https://ubuntu.com/server/docs
- Mininet on Ubuntu: http://mininet.org/download/
- Open vSwitch: http://www.openvswitch.org/
