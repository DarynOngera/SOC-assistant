#!/bin/bash
# Prepare PCAP files for Colab upload

echo "=========================================="
echo "PREPARING PCAP FILES FOR COLAB UPLOAD"
echo "=========================================="

# Create upload directory
UPLOAD_DIR="colab_upload"
mkdir -p "$UPLOAD_DIR"

echo ""
echo "Copying files to $UPLOAD_DIR/..."
echo ""

# Copy normal traffic (latest file)
echo "1. Copying normal traffic..."
cp /home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap \
   "$UPLOAD_DIR/normal_traffic.pcap"

if [ $? -eq 0 ]; then
    echo "   ✓ normal_traffic.pcap"
else
    echo "   ❌ Failed to copy normal_traffic.pcap"
fi

# Copy attack files
echo ""
echo "2. Copying attack files..."

cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap \
   "$UPLOAD_DIR/"
echo "   ✓ syn_flood.pcap"

cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/port_scan.pcap \
   "$UPLOAD_DIR/"
echo "   ✓ port_scan.pcap"

cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/udp_flood.pcap \
   "$UPLOAD_DIR/"
echo "   ✓ udp_flood.pcap"

cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/http_flood.pcap \
   "$UPLOAD_DIR/"
echo "   ✓ http_flood.pcap"

echo ""
echo "=========================================="
echo "✓ FILES READY FOR UPLOAD"
echo "=========================================="
echo ""
echo "Files in $UPLOAD_DIR/:"
ls -lh "$UPLOAD_DIR/"

echo ""
echo "Total size:"
du -sh "$UPLOAD_DIR/"

echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo "1. Navigate to: $(pwd)/$UPLOAD_DIR/"
echo "2. Upload all 5 files to Google Colab"
echo "3. Run the notebook: mininet_colab_training.ipynb"
echo "=========================================="
