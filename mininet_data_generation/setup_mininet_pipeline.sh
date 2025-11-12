#!/bin/bash
# Mininet Data Generation Pipeline Setup Script

set -e  # Exit on error

echo "============================================================"
echo "MININET DATA GENERATION PIPELINE SETUP"
echo "============================================================"

# Check if running as root for Mininet operations
if [ "$EUID" -eq 0 ]; then 
    echo "⚠ Warning: Running as root. Some operations will be performed with elevated privileges."
fi

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check system requirements
echo ""
echo "Checking system requirements..."

# Check for Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check for Mininet
if command -v mn &> /dev/null; then
    print_status "Mininet found"
else
    print_warning "Mininet not found"
    echo "Installing Mininet..."
    sudo apt-get update
    sudo apt-get install -y mininet
    print_status "Mininet installed"
fi

# Check for required network tools
echo ""
echo "Checking network tools..."

TOOLS=("tcpdump" "hping3" "nmap" "nc")
MISSING_TOOLS=()

for tool in "${TOOLS[@]}"; do
    if command -v $tool &> /dev/null; then
        print_status "$tool found"
    else
        MISSING_TOOLS+=($tool)
        print_warning "$tool not found"
    fi
done

if [ ${#MISSING_TOOLS[@]} -gt 0 ]; then
    echo ""
    echo "Installing missing tools: ${MISSING_TOOLS[*]}"
    sudo apt-get install -y tcpdump hping3 nmap netcat-openbsd
    print_status "Network tools installed"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."

pip3 install --upgrade pip

# Core dependencies
pip3 install scapy pandas numpy scikit-learn matplotlib seaborn joblib

# ML dependencies
pip3 install xgboost imbalanced-learn

# Optional dependencies
pip3 install tensorflow keras torch || print_warning "Deep learning libraries skipped (optional)"

print_status "Python dependencies installed"

# Create directory structure
echo ""
echo "Creating directory structure..."

mkdir -p data_capture/pcaps
mkdir -p data_capture/processed
mkdir -p reports
mkdir -p ../models

print_status "Directory structure created"

# Set permissions
echo ""
echo "Setting permissions..."

chmod +x topology/generate_normal_traffic.py
chmod +x topology/generate_attack_traffic.py
chmod +x data_capture/preprocess_pcap.py
chmod +x models/train_mininet_models.py
chmod +x simulation/realtime_attack_sim.py
chmod +x integration/integrate_dashboard.py

print_status "Permissions set"

# Test Mininet installation
echo ""
echo "Testing Mininet installation..."

if sudo mn --version &> /dev/null; then
    print_status "Mininet test passed"
else
    print_error "Mininet test failed"
    exit 1
fi

# Create quick start script
echo ""
echo "Creating quick start script..."

cat > run_pipeline.sh << 'EOF'
#!/bin/bash
# Quick Start Script for Mininet Pipeline

echo "============================================================"
echo "MININET PIPELINE - QUICK START"
echo "============================================================"

echo ""
echo "Step 1: Generating normal traffic (5 minutes)..."
sudo python3 topology/generate_normal_traffic.py

echo ""
echo "Step 2: Generating attack traffic (2 minutes)..."
sudo python3 topology/generate_attack_traffic.py

echo ""
echo "Step 3: Preprocessing captured data..."
python3 data_capture/preprocess_pcap.py

echo ""
echo "Step 4: Training models..."
python3 models/train_mininet_models.py

echo ""
echo "Step 5: Integrating with dashboard..."
python3 integration/integrate_dashboard.py

echo ""
echo "============================================================"
echo "PIPELINE COMPLETED!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "1. Review integration guide: ../models/INTEGRATION_GUIDE.md"
echo "2. Start dashboard: cd .. && python scripts/start_dashboard.py"
echo "3. Test real-time detection: sudo python3 simulation/realtime_attack_sim.py"
EOF

chmod +x run_pipeline.sh
print_status "Quick start script created: run_pipeline.sh"

# Create test script
cat > test_installation.sh << 'EOF'
#!/bin/bash
# Test Mininet Pipeline Installation

echo "Testing Mininet Pipeline Installation..."
echo ""

# Test Python imports
echo "Testing Python imports..."
python3 -c "import scapy.all; print('✓ Scapy')"
python3 -c "import pandas; print('✓ Pandas')"
python3 -c "import numpy; print('✓ NumPy')"
python3 -c "import sklearn; print('✓ Scikit-learn')"
python3 -c "import xgboost; print('✓ XGBoost')"
python3 -c "import imblearn; print('✓ Imbalanced-learn')"

echo ""
echo "Testing Mininet..."
sudo mn --version

echo ""
echo "Testing network tools..."
which tcpdump
which hping3
which nmap
which nc

echo ""
echo "✓ All tests passed!"
EOF

chmod +x test_installation.sh
print_status "Test script created: test_installation.sh"

# Summary
echo ""
echo "============================================================"
echo "SETUP COMPLETED SUCCESSFULLY!"
echo "============================================================"
echo ""
echo "Directory structure:"
echo "  mininet_data_generation/"
echo "  ├── topology/              # Network topology and traffic generation"
echo "  ├── data_capture/          # Packet capture and preprocessing"
echo "  ├── models/                # Model training scripts"
echo "  ├── simulation/            # Real-time attack simulation"
echo "  └── integration/           # Dashboard integration"
echo ""
echo "Quick commands:"
echo "  1. Test installation:      ./test_installation.sh"
echo "  2. Run full pipeline:      ./run_pipeline.sh"
echo "  3. Generate normal traffic: sudo python3 topology/generate_normal_traffic.py"
echo "  4. Generate attacks:       sudo python3 topology/generate_attack_traffic.py"
echo "  5. Train models:           python3 models/train_mininet_models.py"
echo "  6. Real-time detection:    sudo python3 simulation/realtime_attack_sim.py"
echo ""
echo "Documentation:"
echo "  - README.md                # Complete documentation"
echo "  - ../models/INTEGRATION_GUIDE.md  # Dashboard integration guide"
echo ""
echo "⚠ Note: Mininet scripts require root privileges (use sudo)"
echo "============================================================"
