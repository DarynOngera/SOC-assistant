#!/bin/bash
#
# CentOS-Compatible PCAP Generation Script
# Handles CentOS-specific differences and dependencies
#

set -e

echo "================================================================================"
echo "CENTOS PCAP GENERATION"
echo "================================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Detect OS
if [ -f /etc/redhat-release ]; then
    OS_VERSION=$(cat /etc/redhat-release)
    echo "✓ Detected: $OS_VERSION"
else
    echo "⚠ Warning: Not a Red Hat-based system"
fi
echo ""

# Check dependencies
echo "→ Checking dependencies..."
MISSING_DEPS=()

command -v python3 >/dev/null 2>&1 || MISSING_DEPS+=("python3")
command -v tcpdump >/dev/null 2>&1 || MISSING_DEPS+=("tcpdump")
command -v nmap >/dev/null 2>&1 || MISSING_DEPS+=("nmap")
command -v nc >/dev/null 2>&1 || MISSING_DEPS+=("nc")
command -v ovs-vsctl >/dev/null 2>&1 || MISSING_DEPS+=("openvswitch")

# Check for hping3 (may not be available on CentOS)
if ! command -v hping3 >/dev/null 2>&1; then
    echo "⚠ hping3 not found - will use alternative methods"
    USE_HPING=false
else
    USE_HPING=true
fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo "✗ Missing dependencies: ${MISSING_DEPS[*]}"
    echo ""
    echo "Install with:"
    echo "  sudo yum install -y ${MISSING_DEPS[*]}"
    exit 1
fi

echo "✓ All required dependencies found"
echo ""

# Check Python packages
echo "→ Checking Python packages..."
python3 -c "import mininet" 2>/dev/null || {
    echo "✗ Mininet Python package not found"
    echo "Install with: sudo pip3 install mininet"
    exit 1
}

python3 -c "import scapy" 2>/dev/null || {
    echo "⚠ Scapy not found - installing..."
    pip3 install scapy
}

echo "✓ Python packages OK"
echo ""

# Start Open vSwitch if not running
echo "→ Checking Open vSwitch..."
if ! systemctl is-active --quiet openvswitch; then
    echo "  Starting Open vSwitch..."
    systemctl start openvswitch
    sleep 2
fi
echo "✓ Open vSwitch running"
echo ""

# Create output directory
OUTPUT_DIR="data_capture/mininet"
mkdir -p "$OUTPUT_DIR"
echo "✓ Output directory: $OUTPUT_DIR"
echo ""

# Backup old PCAPs
if ls "$OUTPUT_DIR"/*.pcap 1> /dev/null 2>&1; then
    BACKUP_DIR="data_capture/mininet_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    mv "$OUTPUT_DIR"/*.pcap "$BACKUP_DIR/" 2>/dev/null || true
    echo "✓ Old PCAPs backed up to: $BACKUP_DIR"
else
    echo "✓ No old PCAPs to backup"
fi
echo ""

# Generate PCAPs
echo "================================================================================"
echo "GENERATING ATTACK PCAPS"
echo "================================================================================"
echo ""

cd topology

# SYN Flood
if [ "$USE_HPING" = true ]; then
    echo "→ Generating SYN Flood (with hping3)..."
    python3 generate_syn_flood_centos.py --samples 1000
else
    echo "→ Generating SYN Flood (without hping3)..."
    python3 generate_syn_flood_simple.py --samples 1000
fi
echo ""

# Port Scan
echo "→ Generating Port Scan..."
python3 generate_port_scan_centos.py --samples 500
echo ""

# UDP Flood
if [ "$USE_HPING" = true ]; then
    echo "→ Generating UDP Flood (with hping3)..."
    python3 generate_udp_flood_centos.py --samples 1000
else
    echo "→ Generating UDP Flood (without hping3)..."
    python3 generate_udp_flood_simple.py --samples 1000
fi
echo ""

# HTTP Flood
echo "→ Generating HTTP Flood..."
python3 generate_http_flood_centos.py --samples 500
echo ""

cd ..

# Verify PCAPs
echo "================================================================================"
echo "VERIFICATION"
echo "================================================================================"
echo ""

SUCCESS_COUNT=0
FAIL_COUNT=0

for pcap in "$OUTPUT_DIR"/*.pcap; do
    if [ -f "$pcap" ]; then
        filename=$(basename "$pcap")
        echo "→ Checking $filename..."
        
        # Get file size
        size=$(du -h "$pcap" | cut -f1)
        
        # Count IPv4 packets
        ipv4_count=$(tcpdump -r "$pcap" -c 100 2>&1 | grep -c "IP " || true)
        
        echo "  Size: $size"
        echo "  IPv4 packets: $ipv4_count"
        
        if [ "$ipv4_count" -gt 0 ] && [ "$size" != "24" ]; then
            echo "  ✓ VALID"
            ((SUCCESS_COUNT++))
        else
            echo "  ✗ INVALID (empty or no IPv4)"
            ((FAIL_COUNT++))
        fi
        echo ""
    fi
done

echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo ""
echo "Generated PCAPs:"
ls -lh "$OUTPUT_DIR"/*.pcap 2>/dev/null || echo "No PCAPs found!"
echo ""
echo "Results:"
echo "  ✓ Valid: $SUCCESS_COUNT"
echo "  ✗ Invalid: $FAIL_COUNT"
echo ""

if [ $SUCCESS_COUNT -gt 0 ]; then
    echo "✓ SUCCESS - PCAPs generated and ready to use!"
else
    echo "✗ FAILED - No valid PCAPs generated"
    exit 1
fi

echo "================================================================================"
