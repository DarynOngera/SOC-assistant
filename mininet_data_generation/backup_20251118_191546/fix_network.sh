#!/bin/bash
# Network Recovery Script - Fix issues caused by Mininet

echo "============================================================"
echo "NETWORK RECOVERY - FIXING MININET INTERFERENCE"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "Step 1: Cleaning up Mininet..."
sudo mn -c 2>/dev/null
echo -e "${GREEN}✓${NC} Mininet cleaned"

echo ""
echo "Step 2: Removing virtual interfaces..."
# Remove any lingering virtual interfaces
for iface in $(ip link show | grep -E 's[0-9]+-eth|h[0-9]+-eth' | awk '{print $2}' | tr -d ':'); do
    echo "  Removing $iface"
    sudo ip link delete $iface 2>/dev/null
done
echo -e "${GREEN}✓${NC} Virtual interfaces removed"

echo ""
echo "Step 3: Restarting NetworkManager..."
sudo systemctl restart NetworkManager
sleep 2
echo -e "${GREEN}✓${NC} NetworkManager restarted"

echo ""
echo "Step 4: Checking WiFi status..."
# Check WiFi interface
WIFI_IFACE=$(ip link show | grep -E 'wlan|wlp' | awk '{print $2}' | tr -d ':' | head -1)

if [ -n "$WIFI_IFACE" ]; then
    echo "  WiFi interface found: $WIFI_IFACE"
    
    # Bring interface down and up
    sudo ip link set $WIFI_IFACE down
    sleep 1
    sudo ip link set $WIFI_IFACE up
    sleep 2
    
    # Check if it's up
    if ip link show $WIFI_IFACE | grep -q "state UP"; then
        echo -e "${GREEN}✓${NC} WiFi interface is UP"
    else
        echo -e "${YELLOW}⚠${NC} WiFi interface is DOWN - trying to bring it up"
        sudo ifconfig $WIFI_IFACE up 2>/dev/null
    fi
    
    # Restart wpa_supplicant if needed
    if systemctl is-active --quiet wpa_supplicant; then
        sudo systemctl restart wpa_supplicant
        echo -e "${GREEN}✓${NC} wpa_supplicant restarted"
    fi
else
    echo -e "${RED}✗${NC} No WiFi interface found"
fi

echo ""
echo "Step 5: Flushing routing tables..."
sudo ip route flush table main
sudo ip route flush cache
echo -e "${GREEN}✓${NC} Routing tables flushed"

echo ""
echo "Step 6: Restarting network services..."
sudo systemctl restart networking 2>/dev/null || echo "  networking service not available"
sudo systemctl restart network-manager 2>/dev/null || echo "  network-manager already restarted"
echo -e "${GREEN}✓${NC} Network services restarted"

echo ""
echo "Step 7: Checking current network status..."
echo ""
echo "Network Interfaces:"
ip -brief link show
echo ""
echo "Active Connections:"
nmcli connection show --active 2>/dev/null || echo "  NetworkManager not available"
echo ""
echo "WiFi Networks:"
nmcli device wifi list 2>/dev/null | head -5 || echo "  Cannot scan WiFi"

echo ""
echo "============================================================"
echo "RECOVERY COMPLETED"
echo "============================================================"
echo ""
echo "If WiFi is still not working:"
echo "  1. Try: sudo systemctl restart NetworkManager"
echo "  2. Reconnect to your WiFi network manually"
echo "  3. Reboot if necessary: sudo reboot"
echo ""
echo "To check WiFi status:"
echo "  nmcli device status"
echo "  iwconfig"
echo ""
echo "============================================================"
