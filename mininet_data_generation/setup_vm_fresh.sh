#!/bin/bash
# Fresh Mininet VM Setup Script - Fixed Version
# Handles missing packages gracefully

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

# Check if running as root or with sudo
check_root() {
    if [ "$EUID" -eq 0 ]; then 
        print_status "Running with root privileges"
        SUDO=""
    else
        print_info "Will use sudo for privileged commands"
        SUDO="sudo"
    fi
}

# Install system packages
install_system_packages() {
    print_header "INSTALLING SYSTEM PACKAGES"
    
    # Detect CentOS version and package manager
    if grep -q "release 7" /etc/centos-release 2>/dev/null; then
        PACKAGE_MANAGER="yum"
        print_info "Detected CentOS 7 - using yum"
    else
        PACKAGE_MANAGER="dnf"
        print_info "Detected CentOS 8/9 - using dnf"
    fi
    
    # Install EPEL repository
    print_info "Installing EPEL repository..."
    $SUDO $PACKAGE_MANAGER install -y epel-release
    
    # Enable PowerTools/CRB for CentOS 8/9
    if [ "$PACKAGE_MANAGER" = "dnf" ]; then
        $SUDO dnf config-manager --set-enabled powertools 2>/dev/null || \
        $SUDO dnf config-manager --set-enabled crb 2>/dev/null || \
        print_warning "Could not enable PowerTools/CRB repository"
    fi
    
    # Install essential packages
    print_info "Installing essential packages..."
    $SUDO $PACKAGE_MANAGER install -y \
        python3 \
        python3-pip \
        python3-devel \
        git \
        wget \
        curl \
        tcpdump \
        net-tools \
        iproute \
        gcc \
        make \
        nmap \
        nc \
        zip \
        unzip || {
        print_error "Failed to install essential packages"
        exit 1
    }
    
    # Try to install optional packages
    print_info "Installing optional packages..."
    
    # Try hping3 (optional)
    if $SUDO $PACKAGE_MANAGER install -y hping3 2>/dev/null; then
        print_status "hping3 installed"
    else
        print_warning "hping3 not available (optional - some attacks may not work)"
    fi
    
    # Try wireshark (optional)
    if $SUDO $PACKAGE_MANAGER install -y wireshark 2>/dev/null; then
        print_status "wireshark installed"
    else
        print_warning "wireshark not available (optional)"
    fi
    
    print_status "System packages installed"
}

# Install Mininet
install_mininet() {
    print_header "INSTALLING MININET"
    
    # Check if Mininet is already installed
    if command -v mn &> /dev/null; then
        print_status "Mininet already installed"
        mn --version
        return 0
    fi
    
    print_info "Cloning Mininet repository..."
    cd /tmp
    
    # Remove old clone if exists
    if [ -d "mininet" ]; then
        rm -rf mininet
    fi
    
    git clone --depth 1 https://github.com/mininet/mininet || {
        print_error "Failed to clone Mininet repository"
        exit 1
    }
    
    cd mininet
    
    print_info "Installing Mininet (this may take 5-10 minutes)..."
    $SUDO ./util/install.sh -n || {
        print_error "Mininet installation failed"
        exit 1
    }
    
    # Verify installation
    if command -v mn &> /dev/null; then
        print_status "Mininet installed successfully"
        mn --version
    else
        print_error "Mininet installation verification failed"
        exit 1
    fi
}

# Install Python packages
install_python_packages() {
    print_header "INSTALLING PYTHON PACKAGES"
    
    print_info "Upgrading pip..."
    python3 -m pip install --upgrade pip --user
    
    print_info "Installing Flask and dependencies..."
    python3 -m pip install --user \
        flask==2.3.0 \
        flask-cors==4.0.0 \
        scapy==2.5.0 \
        requests==2.31.0 || {
        print_error "Failed to install Python packages"
        exit 1
    }
    
    # Verify installations
    print_info "Verifying Python packages..."
    python3 -c "import flask; print('Flask OK')" || {
        print_error "Flask verification failed"
        exit 1
    }
    
    python3 -c "from scapy.all import *; print('Scapy OK')" || {
        print_error "Scapy verification failed"
        exit 1
    }
    
    print_status "Python packages installed"
}

# Configure firewall
configure_firewall() {
    print_header "CONFIGURING FIREWALL"
    
    # Check if firewalld is available
    if ! command -v firewall-cmd &> /dev/null; then
        print_warning "firewalld not installed, skipping firewall configuration"
        return 0
    fi
    
    print_info "Configuring firewall rules..."
    
    # Enable and start firewall
    $SUDO systemctl enable firewalld 2>/dev/null || true
    $SUDO systemctl start firewalld 2>/dev/null || true
    
    # Allow SSH
    $SUDO firewall-cmd --permanent --add-service=ssh 2>/dev/null || true
    
    # Allow Mininet API port (5001)
    $SUDO firewall-cmd --permanent --add-port=5001/tcp || {
        print_warning "Could not configure firewall port 5001"
    }
    
    # Allow common network testing ports
    $SUDO firewall-cmd --permanent --add-port=80/tcp 2>/dev/null || true
    $SUDO firewall-cmd --permanent --add-port=443/tcp 2>/dev/null || true
    $SUDO firewall-cmd --permanent --add-port=8080/tcp 2>/dev/null || true
    
    # Reload firewall
    $SUDO firewall-cmd --reload 2>/dev/null || true
    
    print_status "Firewall configured"
}

# Setup directories
setup_directories() {
    print_header "SETTING UP DIRECTORIES"
    
    # Create directory structure
    mkdir -p data_capture/pcaps
    mkdir -p logs
    
    # Set permissions
    chmod 755 data_capture
    chmod 755 data_capture/pcaps
    chmod 755 logs
    
    print_status "Directories created"
}

# Create systemd service
create_systemd_service() {
    print_header "CREATING SYSTEMD SERVICE"
    
    # Get current directory
    CURRENT_DIR=$(pwd)
    SCRIPT_PATH="$CURRENT_DIR/vm_mininet_api.py"
    
    # Check if script exists
    if [ ! -f "$SCRIPT_PATH" ]; then
        print_error "vm_mininet_api.py not found at $SCRIPT_PATH"
        exit 1
    fi
    
    print_info "Creating systemd service file..."
    
    $SUDO tee /etc/systemd/system/mininet-api.service > /dev/null <<EOF
[Unit]
Description=Mininet API Server for SOC Assistant
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
    $SUDO systemctl daemon-reload
    
    print_status "Systemd service created"
}

# Create helper scripts
create_helper_scripts() {
    print_header "CREATING HELPER SCRIPTS"
    
    # Start script
    cat > start_mininet_api.sh << 'EOF'
#!/bin/bash
echo "Starting Mininet API Server..."
sudo systemctl start mininet-api
sudo systemctl status mininet-api
EOF
    chmod +x start_mininet_api.sh
    
    # Stop script
    cat > stop_mininet_api.sh << 'EOF'
#!/bin/bash
echo "Stopping Mininet API Server..."
sudo systemctl stop mininet-api
sudo mn -c 2>/dev/null || true
echo "Mininet API stopped"
EOF
    chmod +x stop_mininet_api.sh
    
    # Status script
    cat > check_status.sh << 'EOF'
#!/bin/bash
echo "==================================="
echo "Mininet API Server Status"
echo "==================================="
echo ""

# Service status
echo "Service Status:"
sudo systemctl status mininet-api --no-pager | head -n 10
echo ""

# API health check
echo "API Health Check:"
curl -s http://localhost:5001/health 2>/dev/null | python3 -m json.tool 2>/dev/null || echo "API not responding"
echo ""

# Mininet check
echo "Mininet:"
if command -v mn &> /dev/null; then
    echo "✓ Installed: $(mn --version 2>&1 | head -n 1)"
else
    echo "✗ Not found"
fi
echo ""

# Firewall
echo "Firewall Ports:"
sudo firewall-cmd --list-ports 2>/dev/null || echo "Firewall not configured"
echo ""

# IP Address
echo "VM IP Address:"
hostname -I
EOF
    chmod +x check_status.sh
    
    # Cleanup script
    cat > cleanup_mininet.sh << 'EOF'
#!/bin/bash
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
    
    echo -e "${GREEN}✅ Mininet VM configured successfully${NC}"
    echo ""
    echo "Configuration:"
    echo "  • Mininet installed and ready"
    echo "  • Python packages installed"
    echo "  • Mininet API service configured"
    echo "  • Firewall configured (port 5001)"
    echo "  • Helper scripts created"
    echo ""
    echo "Quick Start:"
    echo "  1. Start API:   sudo systemctl start mininet-api"
    echo "  2. Check:       ./check_status.sh"
    echo "  3. Enable boot: sudo systemctl enable mininet-api"
    echo ""
    echo "Service Commands:"
    echo "  • Start:   sudo systemctl start mininet-api"
    echo "  • Stop:    sudo systemctl stop mininet-api"
    echo "  • Status:  sudo systemctl status mininet-api"
    echo "  • Logs:    sudo journalctl -u mininet-api -f"
    echo ""
    echo "Helper Scripts:"
    echo "  • ./start_mininet_api.sh  - Start API"
    echo "  • ./stop_mininet_api.sh   - Stop API"
    echo "  • ./check_status.sh       - Check status"
    echo "  • ./cleanup_mininet.sh    - Clean up"
    echo ""
    echo "VM Network:"
    echo "  • IP: $(hostname -I | awk '{print $1}')"
    echo "  • API Port: 5001"
    echo "  • API URL: http://$(hostname -I | awk '{print $1}'):5001"
    echo ""
    echo "Local System Setup:"
    echo "  export MININET_VM_HOST=$(hostname -I | awk '{print $1}')"
    echo "  export MININET_VM_PORT=5001"
    echo ""
    print_info "Ready for Mininet operations!"
}

# Main execution
main() {
    print_header "MININET VM SETUP - FIXED VERSION"
    
    echo "This script will install:"
    echo "  • System packages (Python, Git, tcpdump, etc.)"
    echo "  • Mininet network simulator"
    echo "  • Python packages (Flask, Scapy)"
    echo "  • Mininet API service"
    echo "  • Firewall configuration"
    echo ""
    
    read -p "Continue with setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    check_root
    install_system_packages
    install_mininet
    install_python_packages
    configure_firewall
    setup_directories
    create_systemd_service
    create_helper_scripts
    
    display_completion
}

main "$@"
