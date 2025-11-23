#!/bin/bash
#
# Regenerate All Attack PCAPs with IPv4
# Run with: sudo bash regenerate_all_pcaps.sh
#

set -e  # Exit on error

echo "================================================================================"
echo "REGENERATING ALL ATTACK PCAPS WITH IPv4"
echo "================================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Backup old PCAPs
echo "Step 1: Backing up old PCAPs..."
BACKUP_DIR="data_capture/mininet_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
if ls data_capture/mininet/*.pcap 1> /dev/null 2>&1; then
    mv data_capture/mininet/*.pcap "$BACKUP_DIR/" 2>/dev/null || true
    echo "✓ Old PCAPs backed up to: $BACKUP_DIR"
else
    echo "✓ No old PCAPs to backup"
fi
echo ""

# Ensure output directory exists
mkdir -p data_capture/mininet
echo "✓ Output directory ready: data_capture/mininet"
echo ""

# Change to topology directory
cd topology

# Generate each attack type
echo "================================================================================"
echo "Step 2: Generating Attack PCAPs (IPv4)"
echo "================================================================================"
echo ""

echo "→ Generating SYN Flood..."
python3 generate_syn_flood_ipv4.py --samples 10000
echo ""

echo "→ Generating Port Scan..."
python3 generate_port_scan_ipv4.py --samples 5000
echo ""

echo "→ Generating UDP Flood..."
python3 generate_udp_flood_ipv4.py --samples 10000
echo ""

echo "→ Generating HTTP Flood..."
python3 generate_http_flood_ipv4.py --samples 5000
echo ""

# Return to parent directory
cd ..

# Verify all PCAPs
echo "================================================================================"
echo "Step 3: Verifying Generated PCAPs"
echo "================================================================================"
echo ""

for pcap in data_capture/mininet/*.pcap; do
    if [ -f "$pcap" ]; then
        filename=$(basename "$pcap")
        echo "→ Checking $filename..."
        
        # Count IPv4 packets
        ipv4_count=$(tcpdump -r "$pcap" -c 100 2>&1 | grep -c "IP " || true)
        
        # Count IPv6 packets
        ipv6_count=$(tcpdump -r "$pcap" -c 100 2>&1 | grep -c "IP6 " || true)
        
        # Get file size
        size=$(du -h "$pcap" | cut -f1)
        
        if [ "$ipv4_count" -gt 0 ]; then
            echo "  ✓ IPv4 packets: $ipv4_count"
            echo "  ✓ IPv6 packets: $ipv6_count"
            echo "  ✓ File size: $size"
            echo "  ✓ STATUS: GOOD"
        else
            echo "  ✗ IPv4 packets: $ipv4_count"
            echo "  ✗ IPv6 packets: $ipv6_count"
            echo "  ✗ STATUS: FAILED (No IPv4 traffic!)"
        fi
        echo ""
    fi
done

echo "================================================================================"
echo "PCAP REGENERATION COMPLETE"
echo "================================================================================"
echo ""
echo "Generated PCAPs:"
ls -lh data_capture/mininet/*.pcap 2>/dev/null || echo "No PCAPs found!"
echo ""
echo "Next steps:"
echo "1. Verify PCAPs have IPv4: tcpdump -r data_capture/mininet/syn_flood.pcap -c 10"
echo "2. Test simulation in dashboard"
echo "3. Verify score distribution shows clear attack vs normal difference"
echo ""
echo "================================================================================"
