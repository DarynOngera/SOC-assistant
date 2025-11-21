# Manual Mininet VM Installation Guide

## Quick Install (If Script Fails)

### Step 1: Install System Packages

```bash
# Install EPEL repository
sudo yum install -y epel-release

# Install essential packages (without hping3)
sudo yum install -y \
    python3 python3-pip python3-devel \
    git wget curl \
    tcpdump \
    net-tools iproute \
    gcc make \
    nmap netcat \
    zip unzip

# Optional: Try to install hping3 (may not be available)
sudo yum install -y hping3 || echo "hping3 not available - skipping"
```

### Step 2: Install Mininet

```bash
# Clone Mininet repository
cd /tmp
git clone --depth 1 https://github.com/mininet/mininet
cd mininet

# Install Mininet (this takes a few minutes)
sudo ./util/install.sh -n

# Verify installation
sudo mn --version
```

### Step 3: Install Python Packages

```bash
# Upgrade pip
python3 -m pip install --user --upgrade pip

# Install required packages
python3 -m pip install --user \
    flask==2.3.0 \
    flask-cors==4.0.0 \
    scapy==2.5.0 \
    requests==2.31.0
```

### Step 4: Setup Directories

```bash
# Go to your project directory
cd ~/SOC/SOC-assistant/mininet_data_generation

# Create required directories
mkdir -p data_capture/pcaps
mkdir -p logs

# Set permissions
chmod 755 data_capture logs
```

### Step 5: Configure Firewall

```bash
# Enable firewall
sudo systemctl enable firewalld
sudo systemctl start firewalld

# Allow SSH
sudo firewall-cmd --permanent --add-service=ssh

# Allow Mininet API port
sudo firewall-cmd --permanent --add-port=5001/tcp

# Allow common ports for traffic generation
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --permanent --add-port=8080/tcp

# Reload firewall
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-ports
```

### Step 6: Create Systemd Service

```bash
# Get current directory
CURRENT_DIR=$(pwd)
SCRIPT_PATH="$CURRENT_DIR/vm_mininet_api.py"

# Create systemd service file
sudo tee /etc/systemd/system/mininet-api.service > /dev/null <<EOF
[Unit]
Description=Mininet API Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$CURRENT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_PATH
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable mininet-api

# Start service
sudo systemctl start mininet-api

# Check status
sudo systemctl status mininet-api
```

### Step 7: Verify Installation

```bash
# Check Mininet
sudo mn --version

# Check Python packages
python3 -c "import flask; print('Flask OK')"
python3 -c "from scapy.all import *; print('Scapy OK')"

# Check API service
sudo systemctl status mininet-api

# Test API locally
curl http://localhost:5001/health

# Get VM IP address
hostname -I
```

## Troubleshooting

### Mininet Not Found

```bash
# Check if Mininet is installed
which mn

# If not found, reinstall
cd /tmp/mininet
sudo ./util/install.sh -n
```

### Service Won't Start

```bash
# Check logs
sudo journalctl -u mininet-api -n 50

# Try running manually to see errors
cd ~/SOC/SOC-assistant/mininet_data_generation
sudo python3 vm_mininet_api.py
```

### Port 5001 Not Accessible

```bash
# Check firewall
sudo firewall-cmd --list-ports

# Add port if missing
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload

# Check if service is listening
sudo netstat -tulpn | grep 5001
```

### Python Package Errors

```bash
# Reinstall packages
python3 -m pip install --user --force-reinstall \
    flask==2.3.0 \
    flask-cors==4.0.0 \
    scapy==2.5.0 \
    requests==2.31.0
```

## Quick Test

Once everything is installed:

```bash
# Start API (if not running)
sudo systemctl start mininet-api

# Test from VM
curl http://localhost:5001/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "VM Mininet API",
#   "mininet_available": true
# }
```

## Connect from Local System

On your local machine:

```bash
# Set VM IP (replace with your VM's IP)
export MININET_VM_HOST=192.168.1.100
export MININET_VM_PORT=5001

# Test connection
curl http://192.168.1.100:5001/health

# Start dashboard
cd src/dashboard
python3 server.py
```

## Notes

- **hping3 is optional** - System works without it for most attacks
- **Root required** - Mininet needs root privileges
- **Firewall** - Make sure port 5001 is open
- **Network** - VM must be accessible from local system

## Alternative: Run Without Systemd

If you prefer to run manually:

```bash
cd ~/SOC/SOC-assistant/mininet_data_generation
sudo python3 vm_mininet_api.py
```

This runs in foreground - useful for debugging.
