#!/bin/bash
# Automated VM Setup Script for Mininet Pipeline
# Optimized for VM deployment with network isolation

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/tmp/vm_mininet_setup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

print_header() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running in VM
check_vm_environment() {
    print_header "CHECKING VM ENVIRONMENT"
    
    # Detect virtualization
    if command -v systemd-detect-virt &> /dev/null; then
        VIRT_TYPE=$(systemd-detect-virt)
        if [ "$VIRT_TYPE" != "none" ]; then
            print_status "Running in VM: $VIRT_TYPE"
        else
            print_warning "Not detected as VM, but continuing..."
        fi
    fi
    
    # Check system resources
    TOTAL_RAM=$(free -m | awk 'NR==2{print $2}')
    TOTAL_CORES=$(nproc)
    DISK_SPACE=$(df -BG / | awk 'NR==2{print $4}' | sed 's/G//')
    
    print_info "System Resources:"
    echo "  - RAM: ${TOTAL_RAM}MB"
    echo "  - CPU Cores: ${TOTAL_CORES}"
    echo "  - Available Disk: ${DISK_SPACE}GB"
    
    # Validate minimum requirements
    if [ "$TOTAL_RAM" -lt 7000 ]; then
        print_warning "RAM below recommended 8GB (${TOTAL_RAM}MB available)"
        echo "Consider increasing VM RAM allocation"
    fi
    
    if [ "$TOTAL_CORES" -lt 4 ]; then
        print_warning "CPU cores below recommended 4 (${TOTAL_CORES} available)"
        echo "Consider increasing VM CPU allocation"
    fi
    
    if [ "$DISK_SPACE" -lt 40 ]; then
        print_error "Insufficient disk space (${DISK_SPACE}GB available, 50GB required)"
        exit 1
    fi
}

# System updates and basic packages
install_system_packages() {
    print_header "INSTALLING SYSTEM PACKAGES"
    
    print_info "Updating package lists..."
    sudo apt update
    
    print_info "Installing essential packages..."
    sudo apt install -y \
        curl wget git vim \
        build-essential software-properties-common \
        apt-transport-https ca-certificates \
        python3 python3-pip python3-venv python3-dev \
        htop iotop iftop net-tools \
        ufw fail2ban
    
    print_status "System packages installed"
}

# Install Mininet with VM optimizations
install_mininet() {
    print_header "INSTALLING MININET"
    
    # Check if already installed
    if command -v mn &> /dev/null; then
        print_status "Mininet already installed: $(mn --version 2>&1 | head -1)"
        return 0
    fi
    
    print_info "Installing Mininet from package manager..."
    sudo apt install -y mininet
    
    # Verify installation
    if sudo mn --version &> /dev/null; then
        print_status "Mininet installed successfully"
    else
        print_error "Mininet installation failed"
        exit 1
    fi
    
    # Install Open vSwitch tools
    print_info "Installing Open vSwitch tools..."
    sudo apt install -y openvswitch-switch openvswitch-common
    
    print_status "Mininet and OVS installed"
}

# Install network tools
install_network_tools() {
    print_header "INSTALLING NETWORK TOOLS"
    
    print_info "Installing network analysis tools..."
    sudo apt install -y \
        tcpdump wireshark-common \
        hping3 nmap netcat-openbsd \
        iperf3 traceroute \
        dnsutils iputils-ping
    
    # Set capabilities for non-root packet capture
    print_info "Setting network tool capabilities..."
    sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/tcpdump
    sudo setcap cap_net_raw=ep /usr/bin/hping3
    
    # Add user to wireshark group
    sudo usermod -a -G wireshark $USER
    
    print_status "Network tools installed and configured"
}

# Install Python dependencies with VM optimizations
install_python_dependencies() {
    print_header "INSTALLING PYTHON DEPENDENCIES"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    python3 -m pip install --upgrade pip
    
    # Install core dependencies
    print_info "Installing core Python packages..."
    pip3 install --user \
        pandas>=1.5.0 \
        numpy>=1.21.0 \
        matplotlib>=3.5.0 \
        scikit-learn>=1.1.0 \
        joblib>=1.2.0 \
        seaborn>=0.11.0
    
    # Install networking packages
    print_info "Installing networking packages..."
    pip3 install --user \
        scapy>=2.5.0 \
        netaddr \
        netifaces
    
    # Install ML packages
    print_info "Installing ML packages..."
    pip3 install --user \
        xgboost>=1.6.0 \
        imbalanced-learn>=0.9.0
    
    # Install web framework packages
    print_info "Installing web framework packages..."
    pip3 install --user \
        flask>=2.2.0 \
        flask-cors>=3.0.10 \
        flask-socketio>=5.3.0 \
        PyJWT>=2.4.0
    
    # Optional: TensorFlow (may take time in VM)
    print_info "Installing TensorFlow (optional, may take several minutes)..."
    pip3 install --user tensorflow>=2.10.0 || print_warning "TensorFlow installation skipped"
    
    print_status "Python dependencies installed"
}

# Configure VM-specific network settings
configure_vm_networking() {
    print_header "CONFIGURING VM NETWORKING"
    
    # Create network namespace for isolation
    print_info "Creating isolated network namespace..."
    sudo ip netns add mininet_isolated 2>/dev/null || print_warning "Namespace already exists"
    sudo ip netns exec mininet_isolated ip link set lo up
    
    # Configure firewall
    print_info "Configuring firewall..."
    sudo ufw --force enable
    
    # Allow SSH
    sudo ufw allow ssh
    
    # Allow dashboard access from common VM network ranges
    sudo ufw allow from 192.168.0.0/16 to any port 5000
    sudo ufw allow from 10.0.0.0/8 to any port 5000
    sudo ufw allow from 172.16.0.0/12 to any port 5000
    
    # Optimize network settings for VM
    print_info "Optimizing network settings..."
    echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
    echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_rmem = 4096 87380 134217728' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf
    
    print_status "VM networking configured"
}

# Set up directory structure
setup_directories() {
    print_header "SETTING UP DIRECTORY STRUCTURE"
    
    # Create required directories
    mkdir -p data_capture/{pcaps,processed,logs}
    mkdir -p reports/{models,visualizations}
    mkdir -p logs
    mkdir -p ../models/mininet
    
    # Set permissions
    chmod 755 data_capture reports logs
    chmod 755 ../models/mininet
    
    print_status "Directory structure created"
}

# Configure system limits and optimizations
configure_system_limits() {
    print_header "CONFIGURING SYSTEM LIMITS"
    
    # Increase file descriptor limits
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # Increase memory limits for Mininet
    echo "* soft memlock unlimited" | sudo tee -a /etc/security/limits.conf
    echo "* hard memlock unlimited" | sudo tee -a /etc/security/limits.conf
    
    # Configure swap usage (important for VMs)
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    
    # Optimize for VM performance
    echo 'vm.dirty_ratio=15' | sudo tee -a /etc/sysctl.conf
    echo 'vm.dirty_background_ratio=5' | sudo tee -a /etc/sysctl.conf
    
    print_status "System limits configured"
}

# Create VM-specific scripts
create_vm_scripts() {
    print_header "CREATING VM-SPECIFIC SCRIPTS"
    
    # VM pipeline runner
    cat > run_vm_pipeline.sh << 'EOF'
#!/bin/bash
# VM-Optimized Mininet Pipeline Runner

set -e

echo "============================================================"
echo "MININET PIPELINE - VM EXECUTION"
echo "============================================================"

# Check VM resources
echo "VM Resources:"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU: $(nproc) cores"
echo "  Disk: $(df -h / | tail -1 | awk '{print $4}') available"
echo ""

# Clean up any existing Mininet processes
echo "Cleaning up existing processes..."
sudo mn -c 2>/dev/null || true

# Run in isolated namespace
echo "Starting pipeline in isolated network namespace..."

# Step 1: Generate normal traffic (reduced samples for VM)
echo ""
echo "Step 1: Generating normal traffic (optimized for VM)..."
sudo ip netns exec mininet_isolated python3 topology/generate_normal_traffic.py --samples 25000

# Step 2: Generate attack traffic
echo ""
echo "Step 2: Generating attack traffic..."
sudo ip netns exec mininet_isolated python3 topology/generate_attack_traffic.py --samples 10000

# Step 3: Process data
echo ""
echo "Step 3: Processing captured data..."
python3 data_capture/preprocess_pcap.py

# Step 4: Train models
echo ""
echo "Step 4: Training models..."
python3 models/train_mininet_models.py

# Step 5: Integration
echo ""
echo "Step 5: Integrating with dashboard..."
python3 integration/integrate_dashboard.py

echo ""
echo "============================================================"
echo "VM PIPELINE COMPLETED!"
echo "============================================================"
echo ""
echo "Generated samples: 35,000 (optimized for VM)"
echo "Next steps:"
echo "  1. Start dashboard: cd .. && python scripts/start_dashboard.py"
echo "  2. Access at: http://$(hostname -I | awk '{print $1}'):5000"
echo "  3. Test detection: sudo python3 simulation/realtime_attack_sim.py"
EOF

    chmod +x run_vm_pipeline.sh
    
    # VM testing script
    cat > test_vm_installation.sh << 'EOF'
#!/bin/bash
# VM Installation Test Script

echo "============================================================"
echo "TESTING VM MININET INSTALLATION"
echo "============================================================"
echo ""

# Test system resources
echo "System Resources:"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU: $(nproc) cores"
echo "  Disk: $(df -h / | tail -1 | awk '{print $4}') available"
echo ""

# Test Python imports
echo "Testing Python imports..."
python3 -c "import pandas; print('✓ Pandas')" || echo "✗ Pandas"
python3 -c "import numpy; print('✓ NumPy')" || echo "✗ NumPy"
python3 -c "import sklearn; print('✓ Scikit-learn')" || echo "✗ Scikit-learn"
python3 -c "import scapy.all; print('✓ Scapy')" || echo "✗ Scapy"
python3 -c "import xgboost; print('✓ XGBoost')" || echo "✗ XGBoost"
echo ""

# Test Mininet
echo "Testing Mininet..."
if sudo mn --version &> /dev/null; then
    echo "✓ Mininet: $(sudo mn --version 2>&1 | head -1)"
else
    echo "✗ Mininet not working"
fi
echo ""

# Test network tools
echo "Testing network tools..."
which tcpdump > /dev/null && echo "✓ tcpdump" || echo "✗ tcpdump"
which hping3 > /dev/null && echo "✓ hping3" || echo "✗ hping3"
which nmap > /dev/null && echo "✓ nmap" || echo "✗ nmap"
which nc > /dev/null && echo "✓ netcat" || echo "✗ netcat"
echo ""

# Test network namespace
echo "Testing network isolation..."
if sudo ip netns list | grep -q mininet_isolated; then
    echo "✓ Isolated namespace available"
else
    echo "✗ Isolated namespace not found"
fi
echo ""

# Test Mininet functionality
echo "Testing Mininet functionality..."
if timeout 30 sudo mn --test pingall &> /dev/null; then
    echo "✓ Mininet ping test passed"
else
    echo "⚠ Mininet ping test failed (may be normal in some VMs)"
fi

echo ""
echo "============================================================"
echo "VM INSTALLATION TEST COMPLETED"
echo "============================================================"
EOF

    chmod +x test_vm_installation.sh
    
    # VM monitoring script
    cat > monitor_vm_pipeline.sh << 'EOF'
#!/bin/bash
# VM Pipeline Monitoring Script

echo "VM Pipeline Resource Monitor"
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    clear
    echo "============================================================"
    echo "VM PIPELINE RESOURCE MONITOR - $(date)"
    echo "============================================================"
    echo ""
    
    # CPU usage
    echo "CPU Usage:"
    top -bn1 | grep "Cpu(s)" | awk '{print "  " $2 " user, " $4 " system, " $8 " idle"}'
    echo ""
    
    # Memory usage
    echo "Memory Usage:"
    free -h | grep -E "(Mem|Swap)" | awk '{print "  " $1 " " $3 "/" $2 " (" $3/$2*100 "% used)"}'
    echo ""
    
    # Disk usage
    echo "Disk Usage:"
    df -h / | tail -1 | awk '{print "  Root: " $3 "/" $2 " (" $5 " used)"}'
    echo ""
    
    # Network interfaces
    echo "Network Interfaces:"
    ip addr show | grep -E "(inet |UP)" | grep -v "127.0.0.1" | head -5
    echo ""
    
    # Active Mininet processes
    echo "Mininet Processes:"
    ps aux | grep -E "(mininet|ovs|mn)" | grep -v grep | wc -l | awk '{print "  Active processes: " $1}'
    echo ""
    
    sleep 5
done
EOF

    chmod +x monitor_vm_pipeline.sh
    
    print_status "VM-specific scripts created"
}

# Test installation
test_installation() {
    print_header "TESTING INSTALLATION"
    
    # Test Python imports
    print_info "Testing Python imports..."
    python3 -c "import pandas, numpy, sklearn, scapy.all" && print_status "Core packages working"
    
    # Test Mininet
    print_info "Testing Mininet..."
    if sudo mn --version &> /dev/null; then
        print_status "Mininet working"
    else
        print_error "Mininet test failed"
        return 1
    fi
    
    # Test network tools
    print_info "Testing network tools..."
    which tcpdump hping3 nmap nc > /dev/null && print_status "Network tools available"
    
    print_status "Installation test completed"
}

# Main execution
main() {
    print_header "MININET VM SETUP - AUTOMATED INSTALLER"
    
    print_info "This script will set up Mininet pipeline optimized for VM deployment"
    print_info "Estimated time: 10-20 minutes depending on VM performance"
    print_info "Log file: $LOG_FILE"
    echo ""
    
    # Confirmation
    read -p "Continue with VM setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Execute setup steps
    check_vm_environment
    install_system_packages
    install_mininet
    install_network_tools
    install_python_dependencies
    configure_vm_networking
    setup_directories
    configure_system_limits
    create_vm_scripts
    test_installation
    
    # Final summary
    print_header "VM SETUP COMPLETED SUCCESSFULLY!"
    
    echo -e "${GREEN}✓ Mininet pipeline ready for VM deployment${NC}"
    echo ""
    echo "Quick Start Commands:"
    echo "  • Test installation:    ./test_vm_installation.sh"
    echo "  • Run full pipeline:    ./run_vm_pipeline.sh"
    echo "  • Monitor resources:    ./monitor_vm_pipeline.sh"
    echo ""
    echo "VM-Optimized Features:"
    echo "  • Reduced sample sizes for faster execution"
    echo "  • Network namespace isolation"
    echo "  • Resource monitoring tools"
    echo "  • Firewall configuration for dashboard access"
    echo ""
    echo "Next Steps:"
    echo "  1. Test: ./test_vm_installation.sh"
    echo "  2. Run:  ./run_vm_pipeline.sh"
    echo "  3. Dashboard: cd .. && python scripts/start_dashboard.py"
    echo ""
    print_info "Setup log saved to: $LOG_FILE"
    print_header "READY FOR MININET PIPELINE EXECUTION!"
}

# Error handling
trap 'print_error "Setup failed on line $LINENO. Check $LOG_FILE for details."' ERR

# Execute main function
main "$@"
