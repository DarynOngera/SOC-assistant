#!/bin/bash
# SAFE Pipeline - No Mininet, No Network Interference
# Uses synthetic data generation instead

set -e

echo "============================================================"
echo "SAFE SOC PIPELINE - NO NETWORK INTERFERENCE"
echo "============================================================"
echo ""
echo "This pipeline:"
echo "  ✓ Does NOT use Mininet"
echo "  ✓ Does NOT require root access"
echo "  ✓ Does NOT touch your network"
echo "  ✓ Runs entirely in Python"
echo "  ✓ Generates synthetic network data"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Activate venv if available
if [ -f "../venv/bin/activate" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source ../venv/bin/activate
fi

# Step 1: Generate Synthetic Data
echo ""
echo "============================================================"
echo "STEP 1: Generate Synthetic Network Data"
echo "============================================================"
echo "Using: Pure Python (no Mininet)"
echo ""

if python3 generate_synthetic_data.py; then
    echo -e "${GREEN}✓ Synthetic data generated${NC}"
else
    echo "✗ Failed to generate data"
    exit 1
fi

# Step 2: Train Models
echo ""
echo "============================================================"
echo "STEP 2: Train ML Models"
echo "============================================================"
echo ""

if python3 models/train_mininet_models.py; then
    echo -e "${GREEN}✓ Models trained${NC}"
else
    echo "✗ Failed to train models"
    exit 1
fi

# Step 3: Integrate with Dashboard
echo ""
echo "============================================================"
echo "STEP 3: Integrate with Dashboard"
echo "============================================================"
echo ""

if python3 integration/integrate_dashboard.py; then
    echo -e "${GREEN}✓ Dashboard integrated${NC}"
else
    echo "✗ Failed to integrate"
    exit 1
fi

# Success
echo ""
echo "============================================================"
echo -e "${GREEN}✓ SAFE PIPELINE COMPLETED SUCCESSFULLY!${NC}"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Review models: ls -lh ../models/mininet_*.pkl"
echo "  2. Start dashboard: cd .. && python scripts/start_dashboard.py"
echo ""
echo "Your network was NOT touched - completely safe!"
echo "============================================================"
