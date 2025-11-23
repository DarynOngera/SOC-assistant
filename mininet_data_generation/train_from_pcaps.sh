#!/bin/bash
#
# Complete Pipeline: PCAP → CSV → Trained Models
# Based on colab_training_v2.ipynb structure
#

set -e

PROJECT_ROOT="/home/ongera/projects/SOC-assistant"
MININET_DIR="$PROJECT_ROOT/mininet_data_generation"
PCAP_DIR="$MININET_DIR/data_capture/mininet"
PROCESSED_DIR="$MININET_DIR/data_capture/processed"
OUTPUT_DIR="$PROJECT_ROOT/training_output"

echo "================================================================================"
echo "MININET PCAP → TRAINED MODELS PIPELINE"
echo "================================================================================"
echo ""

# Step 1: Check for PCAPs
echo "→ Step 1: Checking for PCAP files..."
if [ ! -d "$PCAP_DIR" ] || [ -z "$(ls -A $PCAP_DIR/*.pcap 2>/dev/null)" ]; then
    echo "⚠ No PCAP files found in $PCAP_DIR"
    echo ""
    read -p "Generate PCAPs now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "  Generating PCAPs..."
        cd "$MININET_DIR"
        sudo bash generate_pcaps_centos.sh
    else
        echo "ERROR: Cannot proceed without PCAP files"
        exit 1
    fi
else
    echo "✓ Found PCAP files:"
    ls -lh "$PCAP_DIR"/*.pcap
fi
echo ""

# Step 2: Process PCAPs to CSV
echo "→ Step 2: Processing PCAPs to CSV..."
mkdir -p "$PROCESSED_DIR"

# Check if processing script exists
PROCESS_SCRIPT="$PROJECT_ROOT/scripts2/process_mininet_pcaps.py"
if [ ! -f "$PROCESS_SCRIPT" ]; then
    echo "⚠ Processing script not found: $PROCESS_SCRIPT"
    echo "  Creating basic processing script..."
    
    cat > "$PROCESS_SCRIPT" << 'EOF'
#!/usr/bin/env python3
"""Process Mininet PCAPs to CSV for training"""
import os
import sys
import glob
from datetime import datetime

# This is a placeholder - you'll need to implement PCAP processing
# For now, check if CSV already exists

processed_dir = "mininet_data_generation/data_capture/processed"
csv_files = glob.glob(f"{processed_dir}/mininet_dataset_*.csv")

if csv_files:
    print(f"✓ Found existing CSV: {csv_files[-1]}")
    print(csv_files[-1])
else:
    print("ERROR: No CSV files found. Please process PCAPs first.")
    print("Expected location: mininet_data_generation/data_capture/processed/")
    sys.exit(1)
EOF
    chmod +x "$PROCESS_SCRIPT"
fi

CSV_FILE=$(python3 "$PROCESS_SCRIPT" 2>&1 | tail -1)

if [ ! -f "$CSV_FILE" ]; then
    echo "ERROR: CSV file not found: $CSV_FILE"
    echo ""
    echo "Please create a CSV file with the following structure:"
    echo "  - Columns: network features + 'label' (0=normal, 1=attack) + 'attack_type'"
    echo "  - Location: $PROCESSED_DIR/mininet_dataset_YYYYMMDD_HHMMSS.csv"
    exit 1
fi

echo "✓ Using CSV: $CSV_FILE"
CSV_SIZE=$(du -h "$CSV_FILE" | cut -f1)
CSV_LINES=$(wc -l < "$CSV_FILE")
echo "  Size: $CSV_SIZE"
echo "  Rows: $CSV_LINES"
echo ""

# Step 3: Train models
echo "→ Step 3: Training ML models..."
echo "  This may take several minutes..."
echo ""

cd "$PROJECT_ROOT"
python3 scripts2/train_mininet_pcaps.py "$CSV_FILE" --output "$OUTPUT_DIR"

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Training failed!"
    exit 1
fi

echo ""
echo "================================================================================"
echo "✓ PIPELINE COMPLETE"
echo "================================================================================"
echo ""
echo "Output directory: $OUTPUT_DIR"
echo ""
echo "Generated files:"
echo "  Models:"
ls -lh "$OUTPUT_DIR/models/" 2>/dev/null | grep -v "^total" | awk '{print "    - " $9 " (" $5 ")"}'
echo ""
echo "  Visualizations:"
ls -1 "$OUTPUT_DIR/visualizations/" 2>/dev/null | awk '{print "    - " $1}'
echo ""
echo "  Reports:"
ls -1 "$OUTPUT_DIR/reports/" 2>/dev/null | awk '{print "    - " $1}'
echo ""
echo "================================================================================"
echo "NEXT STEPS"
echo "================================================================================"
echo ""
echo "1. Review training results:"
echo "   - Check visualizations: $OUTPUT_DIR/visualizations/"
echo "   - Read report: $OUTPUT_DIR/reports/training_report.json"
echo ""
echo "2. Deploy models to dashboard:"
echo "   cp $OUTPUT_DIR/models/* $PROJECT_ROOT/models/"
echo ""
echo "3. Restart dashboard:"
echo "   cd $PROJECT_ROOT"
echo "   python3 src/dashboard/server.py"
echo ""
echo "4. Access dashboard:"
echo "   http://localhost:5000"
echo ""
echo "================================================================================"
