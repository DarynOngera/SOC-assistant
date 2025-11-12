#!/bin/bash
# Wrapper script to run Mininet pipeline with correct Python environments
# Uses system Python for Mininet, venv for everything else

set -e

echo "============================================================"
echo "MININET PIPELINE - SMART RUNNER"
echo "============================================================"
echo ""
echo "This script automatically uses:"
echo "  - System Python (with sudo) for Mininet scripts"
echo "  - Virtual environment for data processing and ML"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running in venv
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠ Virtual environment detected. Deactivating for Mininet...${NC}"
    deactivate 2>/dev/null || true
fi

# Step 1: Generate Normal Traffic (requires system Python + sudo)
echo ""
echo "============================================================"
echo "STEP 1: Generate Normal Traffic (5 min)"
echo "============================================================"
echo "Using: System Python with sudo"
echo ""

if sudo python3 topology/generate_normal_traffic.py; then
    echo -e "${GREEN}✓ Normal traffic generated${NC}"
else
    echo -e "${RED}✗ Failed to generate normal traffic${NC}"
    echo "See INSTALLATION_FIX.md for troubleshooting"
    exit 1
fi

# Step 2: Generate Attack Traffic (requires system Python + sudo)
echo ""
echo "============================================================"
echo "STEP 2: Generate Attack Traffic (2 min)"
echo "============================================================"
echo "Using: System Python with sudo"
echo ""

if sudo python3 topology/generate_attack_traffic.py; then
    echo -e "${GREEN}✓ Attack traffic generated${NC}"
else
    echo -e "${RED}✗ Failed to generate attack traffic${NC}"
    exit 1
fi

# Activate venv for remaining steps
if [ -f "../venv/bin/activate" ]; then
    echo ""
    echo -e "${YELLOW}Activating virtual environment for data processing...${NC}"
    source ../venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠ No virtual environment found, using system Python${NC}"
fi

# Step 3: Preprocess Data (can use venv)
echo ""
echo "============================================================"
echo "STEP 3: Preprocess Packet Captures"
echo "============================================================"
echo "Using: $(which python3)"
echo ""

if python3 data_capture/preprocess_pcap.py; then
    echo -e "${GREEN}✓ Data preprocessed${NC}"
else
    echo -e "${RED}✗ Failed to preprocess data${NC}"
    exit 1
fi

# Step 4: Train Models (can use venv)
echo ""
echo "============================================================"
echo "STEP 4: Train ML Models"
echo "============================================================"
echo "Using: $(which python3)"
echo ""

if python3 models/train_mininet_models.py; then
    echo -e "${GREEN}✓ Models trained${NC}"
else
    echo -e "${RED}✗ Failed to train models${NC}"
    exit 1
fi

# Step 5: Integrate with Dashboard (can use venv)
echo ""
echo "============================================================"
echo "STEP 5: Integrate with Dashboard"
echo "============================================================"
echo "Using: $(which python3)"
echo ""

if python3 integration/integrate_dashboard.py; then
    echo -e "${GREEN}✓ Dashboard integrated${NC}"
else
    echo -e "${RED}✗ Failed to integrate dashboard${NC}"
    exit 1
fi

# Success
echo ""
echo "============================================================"
echo -e "${GREEN}✓ PIPELINE COMPLETED SUCCESSFULLY!${NC}"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Review models: ls -lh ../models/mininet_*.pkl"
echo "  2. Start dashboard: cd .. && python scripts/start_dashboard.py"
echo "  3. Test detection: sudo python3 simulation/realtime_attack_sim.py"
echo ""
echo "============================================================"
