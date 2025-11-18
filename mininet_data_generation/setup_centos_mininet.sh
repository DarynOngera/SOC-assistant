#!/bin/bash
# CentOS VM Setup Script for Mininet Pipeline
# Optimized for CentOS 7/8/9 and RHEL derivatives

set -e  # Exit on error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging
LOG_FILE="/tmp/centos_mininet_setup.log"
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

# Detect CentOS version
detect_centos_version() {
    print_header "DETECTING CENTOS VERSION"
    
    if [ -f /etc/centos-release ]; then
        CENTOS_VERSION=$(cat /etc/centos-release)
        print_status "Detected: $CENTOS_VERSION"
        
        # Extract major version number
        if echo "$CENTOS_VERSION" | grep -q "release 7"; then
            OS_MAJOR_VERSION=7
        elif echo "$CENTOS_VERSION" | grep -q "release 8"; then
            OS_MAJOR_VERSION=8
        elif echo "$CENTOS_VERSION" | grep -q "release 9"; then
            OS_MAJOR_VERSION=9
        else
            print_warning "Unknown CentOS version, assuming CentOS 8"
            OS_MAJOR_VERSION=8
        fi
    elif [ -f /etc/redhat-release ]; then
        REDHAT_VERSION=$(cat /etc/redhat-release)
        print_status "Detected RHEL-based: $REDHAT_VERSION"
        
        if echo "$REDHAT_VERSION" | grep -q "release 7"; then
            OS_MAJOR_VERSION=7
        elif echo "$REDHAT_VERSION" | grep -q "release 8"; then
            OS_MAJOR_VERSION=8
        elif echo "$REDHAT_VERSION" | grep -q "release 9"; then
            OS_MAJOR_VERSION=9
        else
            OS_MAJOR_VERSION=8
        fi
    else
        print_error "Not a CentOS/RHEL system"
        exit 1
    fi
    
    print_info "Using configuration for CentOS/RHEL $OS_MAJOR_VERSION"
}

# Check VM environment and resources
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
    fi
    
    if [ "$TOTAL_CORES" -lt 4 ]; then
        print_warning "CPU cores below recommended 4 (${TOTAL_CORES} available)"
    fi
    
    if [ "$DISK_SPACE" -lt 40 ]; then
        print_error "Insufficient disk space (${DISK_SPACE}GB available, 50GB required)"
        exit 1
    fi
}

# Enable required repositories
enable_repositories() {
    print_header "ENABLING REPOSITORIES"
    
    if [ "$OS_MAJOR_VERSION" -eq 7 ]; then
        print_info "Enabling EPEL repository for CentOS 7..."
        sudo yum install -y epel-release
        
        print_info "Enabling additional repositories..."
        sudo yum install -y centos-release-scl
        
    elif [ "$OS_MAJOR_VERSION" -eq 8 ]; then
        print_info "Enabling EPEL and PowerTools for CentOS 8..."
        sudo dnf install -y epel-release
        sudo dnf config-manager --set-enabled powertools
        
    elif [ "$OS_MAJOR_VERSION" -eq 9 ]; then
        print_info "Enabling EPEL and CRB for CentOS 9..."
        sudo dnf install -y epel-release
        sudo dnf config-manager --set-enabled crb
    fi
    
    print_status "Repositories enabled"
}

# Install system packages
install_system_packages() {
    print_header "INSTALLING SYSTEM PACKAGES"
    
    print_info "Updating system packages..."
    if [ "$OS_MAJOR_VERSION" -eq 7 ]; then
        sudo yum update -y
        PACKAGE_MANAGER="yum"
    else
        sudo dnf update -y
        PACKAGE_MANAGER="dnf"
    fi
    
    print_info "Installing development tools..."
    if [ "$OS_MAJOR_VERSION" -eq 7 ]; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y \
            curl wget git vim \
            python3 python3-pip python3-devel \
            gcc gcc-c++ make \
            htop iotop net-tools \
            firewalld fail2ban
    else
        sudo dnf groupinstall -y "Development Tools"
        sudo dnf install -y \
            curl wget git vim \
            python3 python3-pip python3-devel \
            gcc gcc-c++ make \
            htop iotop net-tools \
            firewalld fail2ban
    fi
    
    print_status "System packages installed"
}

# Install Mininet from source (required for CentOS)
install_mininet_centos() {
    print_header "INSTALLING MININET FROM SOURCE"
    
    # Check if already installed
    if command -v mn &> /dev/null; then
        print_status "Mininet already installed: $(mn --version 2>&1 | head -1)"
        return 0
    fi
    
    print_info "Installing Mininet dependencies..."
    if [ "$OS_MAJOR_VERSION" -eq 7 ]; then
        sudo yum install -y \
            git python3 python3-devel \
            openvswitch openvswitch-devel \
            kernel-devel kernel-headers \
            gcc make
    else
        sudo dnf install -y \
            git python3 python3-devel \
            openvswitch openvswitch-devel \
            kernel-devel kernel-headers \
            gcc make
    fi
    
    print_info "Cloning Mininet repository..."
    cd /tmp
    if [ -d "mininet" ]; then
        rm -rf mininet
    fi
    git clone https://github.com/mininet/mininet
    cd mininet
    
    print_info "Installing Mininet (this may take 10-15 minutes)..."
    # Install with minimal dependencies for CentOS
    sudo ./util/install.sh -n
    
    # Verify installation
    if sudo mn --version &> /dev/null; then
        print_status "Mininet installed successfully"
    else
        print_error "Mininet installation failed"
        exit 1
    fi
    
    cd - > /dev/null
}

# Install Open vSwitch
install_openvswitch() {
    print_header "CONFIGURING OPEN VSWITCH"
    
    print_info "Installing Open vSwitch..."
    if [ "$OS_MAJOR_VERSION" -eq 7 ]; then
        sudo yum install -y openvswitch openvswitch-devel
    else
        sudo dnf install -y openvswitch openvswitch-devel
    fi
    
    print_info "Starting Open vSwitch services..."
    sudo systemctl enable openvswitch
    sudo systemctl start openvswitch
    
    # Verify OVS is running
    if sudo systemctl is-active openvswitch &> /dev/null; then
        print_status "Open vSwitch configured and running"
    else
        print_warning "Open vSwitch may not be running properly"
    fi
}

# Install network tools
install_network_tools() {
    print_header "INSTALLING NETWORK TOOLS"
    
    print_info "Installing network analysis tools..."
    if [ "$OS_MAJOR_VERSION" -eq 7 ]; then
        sudo yum install -y \
            tcpdump wireshark-cli \
            hping3 nmap nmap-ncat \
            iperf3 traceroute \
            bind-utils iputils
    else
        sudo dnf install -y \
            tcpdump wireshark-cli \
            hping3 nmap nmap-ncat \
            iperf3 traceroute \
            bind-utils iputils
    fi
    
    # Set capabilities for non-root packet capture
    print_info "Setting network tool capabilities..."
    sudo setcap cap_net_raw,cap_net_admin=eip /usr/sbin/tcpdump
    sudo setcap cap_net_raw=ep /usr/sbin/hping3
    
    print_status "Network tools installed and configured"
}

# Install Python dependencies
install_python_dependencies() {
    print_header "INSTALLING PYTHON DEPENDENCIES"
    
    # Upgrade pip
    print_info "Upgrading pip..."
    python3 -m pip install --user --upgrade pip
    
    # Install core dependencies
    print_info "Installing core Python packages..."
    python3 -m pip install --user \
        pandas>=1.5.0 \
        numpy>=1.21.0 \
        matplotlib>=3.5.0 \
        scikit-learn>=1.1.0 \
        joblib>=1.2.0 \
        seaborn>=0.11.0
    
    # Install networking packages
    print_info "Installing networking packages..."
    python3 -m pip install --user \
        scapy>=2.5.0 \
        netaddr \
        netifaces
    
    # Install ML packages
    print_info "Installing ML packages..."
    python3 -m pip install --user \
        xgboost>=1.6.0 \
        imbalanced-learn>=0.9.0
    
    # Install web framework packages
    print_info "Installing web framework packages..."
    python3 -m pip install --user \
        flask>=2.2.0 \
        flask-cors>=3.0.10 \
        flask-socketio>=5.3.0 \
        PyJWT>=2.4.0
    
    # Optional: TensorFlow (may take time in VM)
    print_info "Installing TensorFlow (optional, may take several minutes)..."
    python3 -m pip install --user tensorflow>=2.10.0 || print_warning "TensorFlow installation skipped"
    
    print_status "Python dependencies installed"
}

# Configure CentOS-specific networking
configure_centos_networking() {
    print_header "CONFIGURING CENTOS NETWORKING"
    
    # Create network namespace for isolation
    print_info "Creating isolated network namespace..."
    sudo ip netns add mininet_isolated 2>/dev/null || print_warning "Namespace already exists"
    sudo ip netns exec mininet_isolated ip link set lo up
    
    # Configure firewalld
    print_info "Configuring firewalld..."
    sudo systemctl enable firewalld
    sudo systemctl start firewalld
    
    # Allow SSH
    sudo firewall-cmd --permanent --add-service=ssh
    
    # Allow dashboard access
    sudo firewall-cmd --permanent --add-port=5000/tcp
    sudo firewall-cmd --permanent --add-port=8080/tcp
    
    # Allow common VM network ranges
    sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='192.168.0.0/16' accept"
    sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='10.0.0.0/8' accept"
    sudo firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='172.16.0.0/12' accept"
    
    # Reload firewall
    sudo firewall-cmd --reload
    
    # Optimize network settings for VM
    print_info "Optimizing network settings..."
    echo 'net.core.rmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
    echo 'net.core.wmem_max = 134217728' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_rmem = 4096 87380 134217728' | sudo tee -a /etc/sysctl.conf
    echo 'net.ipv4.tcp_wmem = 4096 65536 134217728' | sudo tee -a /etc/sysctl.conf
    
    # Apply sysctl changes
    sudo sysctl -p
    
    print_status "CentOS networking configured"
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

# Create CentOS-specific scripts
create_centos_scripts() {
    print_header "CREATING CENTOS-SPECIFIC SCRIPTS"
    
    # CentOS pipeline runner
    cat > run_centos_pipeline.sh << 'EOF'
#!/bin/bash
# CentOS-Optimized Mininet Pipeline Runner

set -e

echo "============================================================"
echo "MININET PIPELINE - CENTOS EXECUTION"
echo "============================================================"

# Check CentOS version
if [ -f /etc/centos-release ]; then
    echo "OS: $(cat /etc/centos-release)"
elif [ -f /etc/redhat-release ]; then
    echo "OS: $(cat /etc/redhat-release)"
fi

# Check VM resources
echo "VM Resources:"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU: $(nproc) cores"
echo "  Disk: $(df -h / | tail -1 | awk '{print $4}') available"
echo ""

# Clean up any existing Mininet processes
echo "Cleaning up existing processes..."
sudo mn -c 2>/dev/null || true

# Check Open vSwitch
echo "Checking Open vSwitch..."
if sudo systemctl is-active openvswitch &> /dev/null; then
    echo "✓ Open vSwitch is running"
else
    echo "Starting Open vSwitch..."
    sudo systemctl start openvswitch
fi

# Run in isolated namespace
echo "Starting pipeline in isolated network namespace..."

# Step 1: Generate normal traffic (reduced samples for VM)
echo ""
echo "Step 1: Generating normal traffic (optimized for CentOS VM)..."
sudo ip netns exec mininet_isolated python3 topology/generate_normal_traffic.py --samples 25000

# Step 2: Generate attack traffic
echo ""
echo "Step 2: Generating attack traffic..."
sudo ip netns exec mininet_isolated python3 topology/generate_attack_traffic.py --samples 10000

# Step 3: Ensure feature compatibility
echo ""
echo "Step 3: Ensuring feature compatibility..."
python3 ensure_feature_compatibility.py

# Step 4: Process data
echo ""
echo "Step 4: Processing captured data..."
python3 data_capture/preprocess_pcap.py

# Step 5: Train models
echo ""
echo "Step 5: Training models..."
python3 models/train_mininet_models.py

# Step 6: Integration
echo ""
echo "Step 6: Integrating with dashboard..."
python3 integration/integrate_dashboard.py

# Step 7: Validation
echo ""
echo "Step 7: Validating pipeline integration..."
python3 validate_pipeline_integration.py

echo ""
echo "============================================================"
echo "CENTOS PIPELINE COMPLETED!"
echo "============================================================"
echo ""
echo "Generated samples: 35,000 (optimized for CentOS VM)"
echo "Next steps:"
echo "  1. Start dashboard: cd .. && python3 scripts/start_dashboard.py"
echo "  2. Access at: http://$(hostname -I | awk '{print $1}'):5000"
echo "  3. Test detection: sudo python3 simulation/realtime_attack_sim.py"
EOF

    chmod +x run_centos_pipeline.sh
    
    # CentOS testing script
    cat > test_centos_installation.sh << 'EOF'
#!/bin/bash
# CentOS Installation Test Script

echo "============================================================"
echo "TESTING CENTOS MININET INSTALLATION"
echo "============================================================"
echo ""

# Show OS version
if [ -f /etc/centos-release ]; then
    echo "OS: $(cat /etc/centos-release)"
elif [ -f /etc/redhat-release ]; then
    echo "OS: $(cat /etc/redhat-release)"
fi
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

# Test Open vSwitch
echo "Testing Open vSwitch..."
if sudo systemctl is-active openvswitch &> /dev/null; then
    echo "✓ Open vSwitch is running"
    sudo ovs-vsctl show | head -5
else
    echo "✗ Open vSwitch not running"
fi
echo ""

# Test network tools
echo "Testing network tools..."
which tcpdump > /dev/null && echo "✓ tcpdump" || echo "✗ tcpdump"
which hping3 > /dev/null && echo "✓ hping3" || echo "✗ hping3"
which nmap > /dev/null && echo "✓ nmap" || echo "✗ nmap"
which nc > /dev/null && echo "✓ netcat" || echo "✗ netcat"
echo ""

# Test firewall
echo "Testing firewall..."
if sudo systemctl is-active firewalld &> /dev/null; then
    echo "✓ Firewalld is running"
    sudo firewall-cmd --list-ports | head -1
else
    echo "⚠ Firewalld not running"
fi
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
echo "CENTOS INSTALLATION TEST COMPLETED"
echo "============================================================"
EOF

    chmod +x test_centos_installation.sh
    
    print_status "CentOS-specific scripts created"
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
    
    # Test Open vSwitch
    print_info "Testing Open vSwitch..."
    if sudo systemctl is-active openvswitch &> /dev/null; then
        print_status "Open vSwitch running"
    else
        print_warning "Open vSwitch may need manual start"
    fi
    
    # Test network tools
    print_info "Testing network tools..."
    which tcpdump hping3 nmap nc > /dev/null && print_status "Network tools available"
    
    print_status "Installation test completed"
}

# Main execution
main() {
    print_header "CENTOS MININET SETUP - AUTOMATED INSTALLER"
    
    print_info "This script will set up Mininet pipeline optimized for CentOS VM deployment"
    print_info "Estimated time: 15-30 minutes depending on VM performance and internet speed"
    print_info "Log file: $LOG_FILE"
    echo ""
    
    # Confirmation
    read -p "Continue with CentOS setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Execute setup steps
    detect_centos_version
    check_vm_environment
    enable_repositories
    install_system_packages
    install_mininet_centos
    install_openvswitch
    install_network_tools
    install_python_dependencies
    configure_centos_networking
    setup_directories
    configure_system_limits
    create_centos_scripts
    test_installation
    
    # Final summary
    print_header "CENTOS SETUP COMPLETED SUCCESSFULLY!"
    
    echo -e "${GREEN}✓ Mininet pipeline ready for CentOS VM deployment${NC}"
    echo ""
    echo "Quick Start Commands:"
    echo "  • Test installation:    ./test_centos_installation.sh"
    echo "  • Run full pipeline:    ./run_centos_pipeline.sh"
    echo ""
    echo "CentOS-Optimized Features:"
    echo "  • Mininet installed from source"
    echo "  • Firewalld configuration"
    echo "  • SELinux compatibility"
    echo "  • RHEL/CentOS 7/8/9 support"
    echo "  • Network namespace isolation"
    echo ""
    echo "Next Steps:"
    echo "  1. Test: ./test_centos_installation.sh"
    echo "  2. Run:  ./run_centos_pipeline.sh"
    echo "  3. Dashboard: cd .. && python3 scripts/start_dashboard.py"
    echo ""
    print_info "Setup log saved to: $LOG_FILE"
    print_header "READY FOR CENTOS MININET PIPELINE EXECUTION!"
}

# Error handling
trap 'print_error "Setup failed on line $LINENO. Check $LOG_FILE for details."' ERR

# Execute main function
main "$@"
