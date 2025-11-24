#!/bin/bash
# Mininet Setup Script for Ubuntu
# Supports Ubuntu 20.04 LTS and 22.04 LTS

set -e

echo "=========================================="
echo "Mininet Setup for Ubuntu"
echo "SOC Dashboard Project"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Detect Ubuntu version
UBUNTU_VERSION=$(lsb_release -rs)
echo "Detected Ubuntu version: $UBUNTU_VERSION"

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install basic dependencies
echo "Installing basic dependencies..."
apt install -y \
    git \
    curl \
    wget \
    vim \
    net-tools \
    iproute2 \
    build-essential

# Install Python 3 and pip
echo "Installing Python 3..."
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev

# Install Mininet
echo "Installing Mininet..."
apt install -y mininet

# Verify Mininet installation
if ! command -v mn &> /dev/null; then
    echo "Mininet installation failed, trying from source..."
    cd /tmp
    git clone https://github.com/mininet/mininet
    cd mininet
    git checkout 2.3.0
    PYTHON=python3 ./util/install.sh -a
fi

# Install Open vSwitch
echo "Installing Open vSwitch..."
apt install -y openvswitch-switch openvswitch-common

# Start and enable OVS
systemctl start openvswitch-switch
systemctl enable openvswitch-switch

# Install network tools
echo "Installing network tools..."
apt install -y \
    tcpdump \
    wireshark \
    tshark \
    hping3 \
    iperf3 \
    nmap \
    netcat

# Install Python packages
echo "Installing Python packages..."
pip3 install --upgrade pip
pip3 install \
    flask \
    flask-cors \
    scapy \
    requests \
    python-dotenv

# Create directories
echo "Creating directories..."
mkdir -p /opt/mininet_api
mkdir -p /var/log/mininet
mkdir -p ~/mininet_data_generation/data_capture/mininet
mkdir -p ~/mininet_data_generation/data_capture/pcaps

# Set permissions
chmod -R 755 ~/mininet_data_generation

# Configure firewall
echo "Configuring firewall..."
ufw allow 22/tcp    # SSH
ufw allow 5001/tcp  # Mininet API
ufw --force enable

# Clean up Mininet
echo "Cleaning up Mininet..."
mn -c 2>/dev/null || true

# Test Mininet
echo "Testing Mininet installation..."
if mn --version; then
    echo "✅ Mininet installed successfully!"
else
    echo "❌ Mininet installation verification failed"
    exit 1
fi

# Test OVS
echo "Testing Open vSwitch..."
if ovs-vsctl show; then
    echo "✅ Open vSwitch is running!"
else
    echo "❌ Open vSwitch is not running"
    exit 1
fi

# Display network information
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo "Network Information:"
ip -4 addr show | grep inet
echo ""
echo "Next Steps:"
echo "1. Note your VM IP address above"
echo "2. Copy vm_mininet_api.py to /opt/mininet_api/"
echo "3. Start the API server: python3 /opt/mininet_api/vm_mininet_api.py"
echo "4. Update MININET_VM_HOST in your dashboard .env file"
echo ""
echo "Test Mininet: sudo mn --test pingall"
echo "=========================================="
