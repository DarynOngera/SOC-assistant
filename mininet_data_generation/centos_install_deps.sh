#!/bin/bash
#
# CentOS Dependency Installation Script
# Installs all required tools for PCAP generation
#

set -e

echo "================================================================================"
echo "CENTOS DEPENDENCY INSTALLATION"
echo "================================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Detect OS
if [ -f /etc/redhat-release ]; then
    OS_VERSION=$(cat /etc/redhat-release)
    echo "✓ Detected: $OS_VERSION"
else
    echo "⚠ Warning: Not a Red Hat-based system"
    echo "This script is designed for CentOS/RHEL"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Update system
echo "→ Updating system packages..."
yum update -y > /dev/null 2>&1
echo "✓ System updated"
echo ""

# Install EPEL
echo "→ Installing EPEL repository..."
yum install -y epel-release > /dev/null 2>&1
echo "✓ EPEL installed"
echo ""

# Install Python 3
echo "→ Installing Python 3..."
yum install -y python3 python3-pip python3-devel > /dev/null 2>&1
echo "✓ Python 3 installed"
python3 --version
echo ""

# Install development tools
echo "→ Installing development tools..."
yum groupinstall -y "Development Tools" > /dev/null 2>&1
echo "✓ Development tools installed"
echo ""

# Install network tools
echo "→ Installing network tools..."
yum install -y net-tools tcpdump nmap nc wget curl > /dev/null 2>&1
echo "✓ Network tools installed"
echo ""

# Install Open vSwitch
echo "→ Installing Open vSwitch..."
yum install -y openvswitch > /dev/null 2>&1
systemctl start openvswitch
systemctl enable openvswitch
echo "✓ Open vSwitch installed and started"
echo ""

# Install Apache Bench (optional)
echo "→ Installing Apache Bench..."
yum install -y httpd-tools > /dev/null 2>&1 && echo "✓ Apache Bench installed" || echo "⚠ Apache Bench not available"
echo ""

# Try to install hping3
echo "→ Installing hping3..."
if yum install -y hping3 > /dev/null 2>&1; then
    echo "✓ hping3 installed from repository"
else
    echo "⚠ hping3 not in repository"
    read -p "Compile hping3 from source? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Downloading hping3 source..."
        cd /tmp
        wget -q http://www.hping.org/hping3-20051105.tar.gz
        tar -xzf hping3-20051105.tar.gz
        cd hping3-20051105
        
        echo "  Compiling hping3..."
        yum install -y libpcap-devel > /dev/null 2>&1
        ./configure > /dev/null 2>&1
        make > /dev/null 2>&1
        make install > /dev/null 2>&1
        
        echo "✓ hping3 compiled and installed"
        cd -
    else
        echo "⚠ Skipping hping3 (will use fallback methods)"
    fi
fi
echo ""

# Install Mininet
echo "→ Installing Mininet..."
if command -v mn >/dev/null 2>&1; then
    echo "✓ Mininet already installed"
else
    echo "  Cloning Mininet repository..."
    cd /tmp
    if [ ! -d "mininet" ]; then
        git clone https://github.com/mininet/mininet.git > /dev/null 2>&1
    fi
    cd mininet
    
    echo "  Installing Mininet (this may take a few minutes)..."
    PYTHON=python3 util/install.sh -n > /dev/null 2>&1
    
    echo "✓ Mininet installed"
    cd -
fi
echo ""

# Install Python packages
echo "→ Installing Python packages..."
pip3 install --upgrade pip > /dev/null 2>&1
pip3 install mininet scapy > /dev/null 2>&1
echo "✓ Python packages installed"
echo ""

# Configure firewall (if running)
echo "→ Configuring firewall..."
if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-service=http > /dev/null 2>&1
    firewall-cmd --permanent --add-service=https > /dev/null 2>&1
    firewall-cmd --reload > /dev/null 2>&1
    echo "✓ Firewall configured"
else
    echo "✓ Firewall not running"
fi
echo ""

# Check SELinux
echo "→ Checking SELinux..."
if command -v getenforce >/dev/null 2>&1; then
    SELINUX_STATUS=$(getenforce)
    echo "  SELinux status: $SELINUX_STATUS"
    if [ "$SELINUX_STATUS" = "Enforcing" ]; then
        echo "  ⚠ SELinux is enforcing - may cause issues"
        echo "  To disable temporarily: sudo setenforce 0"
        echo "  To disable permanently: edit /etc/selinux/config"
    fi
fi
echo ""

# Verification
echo "================================================================================"
echo "VERIFICATION"
echo "================================================================================"
echo ""

MISSING=()

command -v python3 >/dev/null 2>&1 && echo "✓ python3" || MISSING+=("python3")
command -v tcpdump >/dev/null 2>&1 && echo "✓ tcpdump" || MISSING+=("tcpdump")
command -v nmap >/dev/null 2>&1 && echo "✓ nmap" || MISSING+=("nmap")
command -v nc >/dev/null 2>&1 && echo "✓ nc (netcat)" || MISSING+=("nc")
command -v ovs-vsctl >/dev/null 2>&1 && echo "✓ Open vSwitch" || MISSING+=("openvswitch")
command -v mn >/dev/null 2>&1 && echo "✓ Mininet" || MISSING+=("mininet")

# Optional tools
command -v hping3 >/dev/null 2>&1 && echo "✓ hping3 (optional)" || echo "⚠ hping3 (will use fallback)"
command -v ab >/dev/null 2>&1 && echo "✓ Apache Bench (optional)" || echo "⚠ Apache Bench (will use fallback)"

echo ""

if [ ${#MISSING[@]} -ne 0 ]; then
    echo "✗ Missing required tools: ${MISSING[*]}"
    echo "Installation incomplete!"
    exit 1
else
    echo "✓ All required dependencies installed!"
fi

echo ""
echo "================================================================================"
echo "INSTALLATION COMPLETE"
echo "================================================================================"
echo ""
echo "Next steps:"
echo "1. Generate PCAPs: sudo bash generate_pcaps_centos.sh"
echo "2. Verify PCAPs: ls -lh data_capture/mininet/"
echo ""
echo "================================================================================"
