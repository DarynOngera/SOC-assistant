#!/bin/bash
#
# Generate a single attack PCAP with IPv4
# Usage: sudo bash generate_one_attack.sh <attack_type>
# Example: sudo bash generate_one_attack.sh syn_flood
#

set -e

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

ATTACK_TYPE=$1

if [ -z "$ATTACK_TYPE" ]; then
    echo "Usage: sudo bash generate_one_attack.sh <attack_type>"
    echo ""
    echo "Available attack types:"
    echo "  syn_flood"
    echo "  port_scan"
    echo "  udp_flood"
    echo "  http_flood"
    exit 1
fi

echo "================================================================================"
echo "GENERATING ${ATTACK_TYPE} PCAP (IPv4)"
echo "================================================================================"
echo ""

cd topology

case $ATTACK_TYPE in
    syn_flood)
        python3 generate_syn_flood_ipv4.py --samples 10000
        ;;
    port_scan)
        python3 generate_port_scan_ipv4.py --samples 5000
        ;;
    udp_flood)
        python3 generate_udp_flood_ipv4.py --samples 10000
        ;;
    http_flood)
        python3 generate_http_flood_ipv4.py --samples 5000
        ;;
    *)
        echo "ERROR: Unknown attack type: $ATTACK_TYPE"
        echo "Valid types: syn_flood, port_scan, udp_flood, http_flood"
        exit 1
        ;;
esac

cd ..

# Verify
PCAP_FILE="data_capture/mininet/${ATTACK_TYPE}.pcap"
if [ -f "$PCAP_FILE" ]; then
    echo ""
    echo "→ Verifying $PCAP_FILE..."
    ipv4_count=$(tcpdump -r "$PCAP_FILE" -c 100 2>&1 | grep -c "IP " || true)
    size=$(du -h "$PCAP_FILE" | cut -f1)
    
    echo "  IPv4 packets: $ipv4_count"
    echo "  File size: $size"
    
    if [ "$ipv4_count" -gt 0 ]; then
        echo "  ✓ SUCCESS"
    else
        echo "  ✗ FAILED (No IPv4 traffic)"
    fi
fi

echo ""
echo "================================================================================"
