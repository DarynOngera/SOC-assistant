#!/bin/bash
# Cleanup Script for Mininet Pipeline
# Removes generated data and models for fresh start
#
# Usage:
#   ./cleanup.sh           # Interactive mode (asks for confirmation)
#   ./cleanup.sh --force   # Force mode (no confirmation)
#   ./cleanup.sh -f        # Force mode (short flag)

echo "============================================================"
echo "MININET PIPELINE CLEANUP"
echo "============================================================"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

echo ""
print_warning "This will remove:"
echo "  - All PCAP files (data_capture/pcaps/)"
echo "  - Processed datasets (data_capture/processed/)"
echo "  - Training reports (reports/)"
echo "  - Mininet models (../models/mininet_*)"
echo ""

# Check for --force flag
if [ "$1" != "--force" ] && [ "$1" != "-f" ]; then
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Cleanup cancelled"
        exit 0
    fi
else
    echo "Running in force mode (--force flag detected)"
fi

echo ""
echo "Starting cleanup..."

# Remove PCAP files
if [ -d "data_capture/pcaps" ]; then
    count=$(find data_capture/pcaps -name "*.pcap" 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        rm -f data_capture/pcaps/*.pcap 2>/dev/null
        print_status "Removed $count PCAP file(s)"
    else
        echo "  No PCAP files to remove"
    fi
else
    echo "  Directory data_capture/pcaps not found"
fi

# Remove processed datasets
if [ -d "data_capture/processed" ]; then
    count=$(find data_capture/processed -name "*.csv" 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        rm -f data_capture/processed/*.csv 2>/dev/null
        print_status "Removed $count processed dataset(s)"
    else
        echo "  No processed datasets to remove"
    fi
else
    echo "  Directory data_capture/processed not found"
fi

# Remove reports
if [ -d "reports" ]; then
    count=$(find reports \( -name "*.png" -o -name "*.json" -o -name "*.html" \) 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        rm -f reports/*.png reports/*.json reports/*.html 2>/dev/null
        print_status "Removed $count report file(s)"
    else
        echo "  No report files to remove"
    fi
else
    echo "  Directory reports not found"
fi

# Remove Mininet models from main models directory
if [ -d "../models" ]; then
    count=$(find ../models -name "mininet_*" \( -name "*.pkl" -o -name "*.h5" \) 2>/dev/null | wc -l)
    if [ "$count" -gt 0 ]; then
        rm -f ../models/mininet_*.pkl ../models/mininet_*.h5 2>/dev/null
        print_status "Removed $count Mininet model(s)"
    else
        echo "  No Mininet models to remove"
    fi
else
    echo "  Directory ../models not found"
fi

# Remove adapter
if [ -f "../src/models/mininet_adapter.py" ]; then
    rm -f ../src/models/mininet_adapter.py
    print_status "Removed model adapter"
else
    echo "  Model adapter not found"
fi

# Remove integration guide
if [ -f "../models/INTEGRATION_GUIDE.md" ]; then
    rm -f ../models/INTEGRATION_GUIDE.md
    print_status "Removed integration guide"
else
    echo "  Integration guide not found"
fi

# Clean Mininet
print_warning "Cleaning Mininet..."
if command -v mn &> /dev/null; then
    sudo mn -c > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_status "Mininet cleaned"
    else
        echo "  Mininet clean failed (may require manual cleanup)"
    fi
else
    echo "  Mininet not installed, skipping"
fi

# Remove Python cache
cache_count=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l)
pyc_count=$(find . -type f -name "*.pyc" 2>/dev/null | wc -l)
if [ "$cache_count" -gt 0 ] || [ "$pyc_count" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -type f -name "*.pyc" -delete 2>/dev/null
    print_status "Removed Python cache ($cache_count dirs, $pyc_count files)"
else
    echo "  No Python cache to remove"
fi

echo ""
echo "============================================================"
echo "CLEANUP COMPLETED"
echo "============================================================"
echo ""
echo "To regenerate data and models:"
echo "  python3 run_complete_pipeline.py"
echo ""
echo "Or run steps individually:"
echo "  1. sudo python3 topology/generate_normal_traffic.py"
echo "  2. sudo python3 topology/generate_attack_traffic.py"
echo "  3. python3 data_capture/preprocess_pcap.py"
echo "  4. python3 models/train_mininet_models.py"
echo "  5. python3 integration/integrate_dashboard.py"
echo "============================================================"
