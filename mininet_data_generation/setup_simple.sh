#!/bin/bash
# Simplified VM Setup - Step by Step
# Each step can be run independently

set +e  # Don't exit on errors

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "\n${BLUE}==== STEP $1: $2 ====${NC}"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Function to run each step independently
run_step() {
    local step_num=$1
    local step_name=$2
    local step_function=$3
    
    print_step "$step_num" "$step_name"
    
    if $step_function; then
        print_success "Step $step_num completed successfully"
        return 0
    else
        print_error "Step $step_num failed, but continuing..."
        return 1
    fi
}

# Step 1: Basic system packages
step1_basic_packages() {
    echo "Installing basic packages..."
    
    # Detect package manager
    if command -v dnf &> /dev/null; then
        PACKAGE_MANAGER="dnf"
    else
        PACKAGE_MANAGER="yum"
    fi
    
    # Install EPEL
    sudo $PACKAGE_MANAGER install -y epel-release || {
        print_warning "EPEL installation failed, continuing..."
    }
    
    # Enable additional repos for CentOS 8/9
    if command -v dnf &> /dev/null; then
        sudo dnf config-manager --set-enabled powertools 2>/dev/null || \
        sudo dnf config-manager --set-enabled crb 2>/dev/null || true
    fi
    
    # Install basic packages
    sudo $PACKAGE_MANAGER install -y \
        python3 \
        python3-pip \
        git \
        wget \
        tcpdump \
        zip \
        unzip \
        gcc \
        make || {
        print_error "Some basic packages failed to install"
        return 1
    }
    
    return 0
}

# Step 2: Python packages
step2_python_packages() {
    echo "Installing Python packages..."
    
    # Upgrade pip first
    python3 -m pip install --user --upgrade pip || {
        print_warning "Pip upgrade failed, continuing..."
    }
    
    # Install core packages one by one
    packages=(
        "pandas==1.5.3"
        "numpy==1.21.6" 
        "scikit-learn==1.1.3"
        "scapy==2.5.0"
        "xgboost==1.6.2"
        "joblib==1.2.0"
    )
    
    for package in "${packages[@]}"; do
        echo "Installing $package..."
        python3 -m pip install --user --no-cache-dir "$package" || {
            print_warning "Failed to install $package, continuing..."
        }
    done
    
    return 0
}

# Step 3: Mininet (simplified)
step3_mininet() {
    echo "Installing Mininet..."
    
    # Check if already installed
    if command -v mn &> /dev/null; then
        print_success "Mininet already installed"
        return 0
    fi
    
    # Try package installation first
    sudo $PACKAGE_MANAGER install -y mininet && {
        print_success "Mininet installed from package"
        return 0
    }
    
    # Install from source as fallback
    echo "Installing Mininet from source..."
    cd /tmp
    
    # Clean up any previous attempts
    rm -rf mininet
    
    git clone --depth 1 https://github.com/mininet/mininet || {
        print_error "Failed to clone Mininet repository"
        return 1
    }
    
    cd mininet
    
    # Install with minimal options
    sudo ./util/install.sh -n || {
        print_error "Mininet source installation failed"
        return 1
    }
    
    return 0
}

# Step 4: Test installations
step4_test() {
    echo "Testing installations..."
    
    # Test Python packages
    python3 -c "import pandas; print('✓ Pandas OK')" || print_warning "Pandas test failed"
    python3 -c "import numpy; print('✓ NumPy OK')" || print_warning "NumPy test failed"
    python3 -c "import sklearn; print('✓ Scikit-learn OK')" || print_warning "Scikit-learn test failed"
    python3 -c "import scapy.all; print('✓ Scapy OK')" || print_warning "Scapy test failed"
    
    # Test Mininet
    if command -v mn &> /dev/null; then
        print_success "Mininet command available"
        # Quick test (non-interactive)
        timeout 10 sudo mn --version || print_warning "Mininet version check failed"
    else
        print_warning "Mininet command not found"
    fi
    
    return 0
}

# Step 5: Create training scripts
step5_create_scripts() {
    echo "Creating training scripts..."
    
    # Simple training runner
    cat > run_simple_training.sh << 'EOF'
#!/bin/bash
# Simple Training Script

echo "=== Simple VM Training ==="

# Check if we can run basic Python
python3 -c "import pandas, numpy, sklearn; print('Python packages OK')" || {
    echo "❌ Python packages not working"
    exit 1
}

# Check if Mininet is available
if command -v mn &> /dev/null; then
    echo "✓ Mininet available"
else
    echo "❌ Mininet not available"
    exit 1
fi

echo "✅ Basic setup verified"
echo "Ready for manual training steps"
EOF

    chmod +x run_simple_training.sh
    
    # Create test script
    cat > test_setup.sh << 'EOF'
#!/bin/bash
# Test Setup Script

echo "=== Testing VM Setup ==="

echo "System Info:"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)"
echo "  RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "  CPU: $(nproc) cores"

echo ""
echo "Python Packages:"
python3 -c "import pandas; print('  ✓ Pandas:', pandas.__version__)" 2>/dev/null || echo "  ✗ Pandas"
python3 -c "import numpy; print('  ✓ NumPy:', numpy.__version__)" 2>/dev/null || echo "  ✗ NumPy"  
python3 -c "import sklearn; print('  ✓ Scikit-learn:', sklearn.__version__)" 2>/dev/null || echo "  ✗ Scikit-learn"
python3 -c "import scapy; print('  ✓ Scapy:', scapy.__version__)" 2>/dev/null || echo "  ✗ Scapy"

echo ""
echo "System Commands:"
command -v mn >/dev/null && echo "  ✓ Mininet" || echo "  ✗ Mininet"
command -v tcpdump >/dev/null && echo "  ✓ tcpdump" || echo "  ✗ tcpdump"
command -v git >/dev/null && echo "  ✓ git" || echo "  ✗ git"

echo ""
echo "=== Test Complete ==="
EOF

    chmod +x test_setup.sh
    
    return 0
}

# Main execution
main() {
    echo "============================================================"
    echo "SIMPLIFIED VM SETUP - STEP BY STEP"
    echo "============================================================"
    echo ""
    echo "This script runs each step independently."
    echo "If one step fails, the others will still run."
    echo ""
    
    read -p "Continue with simplified setup? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
    
    # Run each step
    run_step "1" "Basic System Packages" step1_basic_packages
    run_step "2" "Python ML Packages" step2_python_packages  
    run_step "3" "Mininet Installation" step3_mininet
    run_step "4" "Test Installations" step4_test
    run_step "5" "Create Training Scripts" step5_create_scripts
    
    echo ""
    echo "============================================================"
    echo "SIMPLIFIED SETUP COMPLETED"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "1. Test your setup: ./test_setup.sh"
    echo "2. Run simple training: ./run_simple_training.sh"
    echo "3. If issues persist, run steps manually"
    echo ""
    echo "Manual step commands:"
    echo "  Step 1: sudo dnf install -y python3 python3-pip git wget tcpdump"
    echo "  Step 2: python3 -m pip install --user pandas numpy scikit-learn scapy"
    echo "  Step 3: git clone https://github.com/mininet/mininet && cd mininet && sudo ./util/install.sh -n"
}

# Allow running individual steps
if [ "$1" = "step1" ]; then
    step1_basic_packages
elif [ "$1" = "step2" ]; then
    step2_python_packages
elif [ "$1" = "step3" ]; then
    step3_mininet
elif [ "$1" = "step4" ]; then
    step4_test
elif [ "$1" = "step5" ]; then
    step5_create_scripts
else
    main "$@"
fi
