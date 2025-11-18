#!/bin/bash
# Combine all PCAP files into one for easy Colab upload

echo "=========================================="
echo "COMBINING PCAP FILES"
echo "=========================================="

UPLOAD_DIR="colab_upload"
OUTPUT_FILE="$UPLOAD_DIR/combined_training_data.pcap"

# Check if mergecap is installed
if ! command -v mergecap &> /dev/null; then
    echo "❌ mergecap not found. Installing..."
    sudo apt-get install -y wireshark-common
fi

echo ""
echo "Combining all PCAP files into one..."
echo ""

# Merge all files
mergecap -w "$OUTPUT_FILE" \
    /home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap \
    /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap \
    /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/port_scan.pcap \
    /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/udp_flood.pcap \
    /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/http_flood.pcap

if [ $? -eq 0 ]; then
    echo "✓ Combined PCAP created!"
    echo ""
    echo "File: $OUTPUT_FILE"
    ls -lh "$OUTPUT_FILE"
    echo ""
    echo "Total packets:"
    tcpdump -r "$OUTPUT_FILE" 2>/dev/null | wc -l
else
    echo "❌ Failed to combine files"
    exit 1
fi

echo ""
echo "=========================================="
echo "✓ READY FOR COLAB"
echo "=========================================="
echo "Upload this ONE file to Colab:"
echo "  $OUTPUT_FILE"
echo "=========================================="
