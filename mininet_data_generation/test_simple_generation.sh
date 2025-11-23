#!/bin/bash
#
# Quick test - Generate small PCAPs to verify they work
#

set -e

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Must run as root (use sudo)"
    exit 1
fi

echo "================================================================================"
echo "QUICK TEST - GENERATING SMALL PCAPS"
echo "================================================================================"
echo ""

cd topology

echo "→ Testing SYN flood (1000 samples, ~30 seconds)..."
python3 generate_syn_flood_simple.py --samples 1000
echo ""

cd ..

# Verify
echo "================================================================================"
echo "VERIFICATION"
echo "================================================================================"
echo ""

PCAP="data_capture/mininet/syn_flood.pcap"

if [ -f "$PCAP" ]; then
    size=$(du -h "$PCAP" | cut -f1)
    ipv4=$(tcpdump -r "$PCAP" -c 100 2>&1 | grep -c "IP " || true)
    
    echo "File: $PCAP"
    echo "Size: $size"
    echo "IPv4 packets: $ipv4"
    echo ""
    
    if [ "$ipv4" -gt 0 ] && [ "$size" != "24" ]; then
        echo "✓ SUCCESS - PCAP is valid!"
        echo ""
        echo "Sample packets:"
        tcpdump -r "$PCAP" -c 5 2>&1 | grep "IP "
    else
        echo "✗ FAILED - PCAP is empty or invalid"
    fi
else
    echo "✗ FAILED - PCAP not created"
fi

echo ""
echo "================================================================================"
