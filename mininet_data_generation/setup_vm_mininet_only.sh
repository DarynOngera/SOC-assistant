#!/bin/bash
# CentOS VM Setup - Mininet-Only Deployment
# This script sets up ONLY Mininet for network simulation
# Model training happens on the local system

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running on CentOS
check_centos() {
    if [ ! -f /etc/centos-release ]; then
        print_error "This script is designed for CentOS"
        exit 1
    fi
    
    print_status "Running on CentOS $(cat /etc/centos-release)"
}

# Install system packages
install_system_packages() {
    print_header "INSTALLING SYSTEM PACKAGES"
    
    # Detect CentOS version
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        PACKAGE_MANAGER="yum"
        sudo yum install -y epel-release
    else
        PACKAGE_MANAGER="dnf"
        sudo dnf install -y epel-release
        sudo dnf config-manager --set-enabled powertools 2>/dev/null || \
        sudo dnf config-manager --set-enabled crb 2>/dev/null || true
    fi
    
    print_info "Installing essential packages..."
    sudo $PACKAGE_MANAGER install -y \
        python3 python3-pip python3-devel \
        git wget curl \
        tcpdump wireshark \
        net-tools iproute \
        gcc make \
        nmap netcat \
        zip unzip
    
    # Try to install hping3 (optional - used for some attack simulations)
    print_info "Installing optional packages..."
    sudo $PACKAGE_MANAGER install -y hping3 2>/dev/null || {
        print_warning "hping3 not available in repositories (optional - some attacks may not work)"
        print_info "You can install it manually later if needed"
    }
    
    print_status "System packages installed"
}

# Install Open vSwitch
install_openvswitch() {
    print_header "INSTALLING OPEN VSWITCH"
    
    print_info "Installing Open vSwitch..."
    
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        sudo $PACKAGE_MANAGER install -y openvswitch
    else
        # Try different package names for CentOS 8/9
        sudo $PACKAGE_MANAGER install -y openvswitch2.17 || \
        sudo $PACKAGE_MANAGER install -y openvswitch || \
        sudo $PACKAGE_MANAGER install -y network-scripts-openvswitch || {
            print_warning "OpenVSwitch package not found in repos"
            return 1
        }
    fi
    
    # Start and enable OVS service
    print_info "Starting Open vSwitch service..."
    sudo systemctl enable openvswitch 2>/dev/null || \
    sudo systemctl enable openvswitch2.17 2>/dev/null || true
    
    sudo systemctl start openvswitch 2>/dev/null || \
    sudo systemctl start openvswitch2.17 2>/dev/null || {
        print_warning "Could not start OVS service, Mininet will manage it"
    }
    
    print_status "Open vSwitch installed"
}

# Install Mininet
install_mininet() {
    print_header "INSTALLING MININET"
    
    if command -v mn &> /dev/null; then
        print_status "Mininet already installed"
        mn --version
        return 0
    fi
    
    print_info "Cloning Mininet repository..."
    cd /tmp
    
    if [ -d "mininet" ]; then
        rm -rf mininet
    fi
    
    git clone --depth 1 https://github.com/mininet/mininet
    cd mininet
    
    print_info "Installing Mininet (this may take several minutes)..."
    sudo ./util/install.sh -n
    
    # Verify installation
    if command -v mn &> /dev/null; then
        print_status "Mininet installed successfully"
        mn --version
    else
        print_error "Mininet installation failed"
        exit 1
    fi
}

# Install Python packages for Mininet API
install_python_packages() {
    print_header "INSTALLING PYTHON PACKAGES"
    
    print_info "Installing Flask and dependencies..."
    python3 -m pip install --user --upgrade pip
    python3 -m pip install --user \
        flask==2.3.0 \
        flask-cors==4.0.0 \
        scapy==2.5.0 \
        requests==2.31.0
    
    print_status "Python packages installed"
}

# Configure firewall
configure_firewall() {
    print_header "CONFIGURING FIREWALL"
    
    print_info "Configuring firewall rules..."
    
    # Enable firewall
    sudo systemctl enable firewalld
    sudo systemctl start firewalld
    
    # Allow SSH
    sudo firewall-cmd --permanent --add-service=ssh
    
    # Allow Mininet API port (5001)
    sudo firewall-cmd --permanent --add-port=5001/tcp
    
    # Allow common network testing ports
    sudo firewall-cmd --permanent --add-port=80/tcp
    sudo firewall-cmd --permanent --add-port=443/tcp
    sudo firewall-cmd --permanent --add-port=8080/tcp
    
    # Reload firewall
    sudo firewall-cmd --reload
    
    print_status "Firewall configured"
}

# Setup directories
setup_directories() {
    print_header "SETTING UP DIRECTORIES"
    
    # Create directory structure
    mkdir -p data_capture/pcaps
    mkdir -p logs
    
    # Set permissions
    chmod 755 data_capture logs
    
    print_status "Directories created"
}

# Create systemd service for Mininet API
create_systemd_service() {
    print_header "CREATING SYSTEMD SERVICE"
    
    # Get current directory
    CURRENT_DIR=$(pwd)
    SCRIPT_PATH="$CURRENT_DIR/vm_mininet_api.py"
    
    print_info "Creating systemd service file..."
    
    sudo tee /etc/systemd/system/mininet-api.service > /dev/null <<EOF
[Unit]
Description=Mininet API Server
After=network.target openvswitch.service

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
    
    print_status "Systemd service created"
    print_info "Service will be started after setup completes"
}

# Create helper scripts
create_helper_scripts() {
    print_header "CREATING HELPER SCRIPTS"
    
    # Start Mininet API script
    cat > start_mininet_api.sh << 'EOF'
#!/bin/bash
# Start Mininet API Server

echo "Starting Mininet API Server..."
sudo python3 vm_mininet_api.py
EOF
    
    chmod +x start_mininet_api.sh
    
    # Stop Mininet API script
    cat > stop_mininet_api.sh << 'EOF'
#!/bin/bash
# Stop Mininet API Server

echo "Stopping Mininet API Server..."
sudo systemctl stop mininet-api
sudo mn -c
echo "Mininet API stopped and cleaned up"
EOF
    
    chmod +x stop_mininet_api.sh
    
    # Status check script
    cat > check_status.sh << 'EOF'
#!/bin/bash
# Check Mininet API Status

echo "==================================="
echo "Mininet API Server Status"
echo "==================================="
echo ""

# Check service status
echo "Service Status:"
sudo systemctl status mininet-api --no-pager | head -n 10
echo ""

# Check if API is responding
echo "API Health Check:"
curl -s http://localhost:5001/health | python3 -m json.tool 2>/dev/null || echo "API not responding"
echo ""

# Check Mininet
echo "Mininet Status:"
if command -v mn &> /dev/null; then
    echo "✓ Mininet installed: $(mn --version 2>&1 | head -n 1)"
else
    echo "✗ Mininet not found"
fi
echo ""

# Check Open vSwitch
echo "Open vSwitch Status:"
sudo systemctl status openvswitch --no-pager | grep "Active:" || \
sudo systemctl status openvswitch2.17 --no-pager | grep "Active:" || \
echo "OVS service not found"
echo ""

# Check firewall
echo "Firewall Status:"
sudo firewall-cmd --list-ports 2>/dev/null || echo "Firewall not configured"
EOF
    
    chmod +x check_status.sh
    
    # Cleanup script
    cat > cleanup_mininet.sh << 'EOF'
#!/bin/bash
# Clean up Mininet processes and state

echo "Cleaning up Mininet..."
sudo mn -c
echo "Mininet cleaned up"
EOF
    
    chmod +x cleanup_mininet.sh
    
    print_status "Helper scripts created"
}

# Display completion message
display_completion() {
    print_header "SETUP COMPLETED!"
    
    echo -e "${GREEN}✅ CentOS VM configured for Mininet-only operation${NC}"
    echo ""
    echo "VM Configuration:"
    echo "  • Mininet for network simulation"
    echo "  • Mininet API server on port 5001"
    echo "  • PCAP capture capabilities"
    echo "  • No model training (done on local system)"
    echo ""
    echo "Quick Start:"
    echo "  1. Start API: sudo systemctl start mininet-api"
    echo "  2. Check status: ./check_status.sh"
    echo "  3. Configure local system with VM IP"
    echo ""
    echo "Systemd Service Commands:"
    echo "  • Start:   sudo systemctl start mininet-api"
    echo "  • Stop:    sudo systemctl stop mininet-api"
    echo "  • Status:  sudo systemctl status mininet-api"
    echo "  • Enable:  sudo systemctl enable mininet-api"
    echo "  • Logs:    sudo journalctl -u mininet-api -f"
    echo ""
    echo "Helper Scripts:"
    echo "  • ./start_mininet_api.sh  - Start API manually"
    echo "  • ./stop_mininet_api.sh   - Stop API and cleanup"
    echo "  • ./check_status.sh       - Check system status"
    echo "  • ./cleanup_mininet.sh    - Clean up Mininet"
    echo ""
    echo "Network Configuration:"
    echo "  • VM IP: $(hostname -I | awk '{print $1}')"
    echo "  • API Port: 5001"
    echo "  • API URL: http://$(hostname -I | awk '{print $1}'):5001"
    echo ""
    echo "Local System Setup:"
    echo "  1. Set environment variables:"
    echo "     export MININET_VM_HOST=$(hostname -I | awk '{print $1}')"
    echo "     export MININET_VM_PORT=5001"
    echo "  2. Start local dashboard"
    echo "  3. Use Mininet simulation features"
    echo ""
    print_info "VM ready for Mininet-only operations!"
}

# Main execution
main() {
    print_header "CENTOS VM MININET-ONLY SETUP"
    
    echo "This setup configures:"
    echo "  • Mininet for network simulation"
    echo "  • Mininet API server (REST API)"
    echo "  • PCAP generation capabilities"
    echo "  • No model training (local system only)"
    echo ""
    
    read -p "Continue with Mininet-only setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    check_centos
    install_system_packages
    install_openvswitch
    install_mininet
    install_python_packages
    configure_firewall
    setup_directories
    create_systemd_service
    create_helper_scripts
    
    display_completion
}

main "$@"
