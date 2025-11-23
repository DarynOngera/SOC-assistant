#!/bin/bash
# Complete System Startup Script
# Ensures MongoDB, model, and services are aligned

set -e

echo "======================================================================"
echo "SOC DASHBOARD SYSTEM STARTUP"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to project directory
cd /home/ongera/projects/SOC-assistant

echo "📍 Working directory: $(pwd)"
echo ""

# 1. Check MongoDB
echo "🔍 [1/6] Checking MongoDB..."
if systemctl is-active --quiet mongodb 2>/dev/null || systemctl is-active --quiet mongod 2>/dev/null; then
    echo -e "${GREEN}✅ MongoDB is running${NC}"
else
    echo -e "${RED}❌ MongoDB is not running${NC}"
    echo "   Starting MongoDB..."
    sudo systemctl start mongodb 2>/dev/null || sudo systemctl start mongod 2>/dev/null || {
        echo -e "${RED}   Failed to start MongoDB${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ MongoDB started${NC}"
fi
echo ""

# 2. Check Model Files
echo "🔍 [2/6] Checking trained model files..."
if [ -f "models/mininet_model.pkl" ] && [ -f "models/mininet_scaler.pkl" ] && [ -f "models/mininet_feature_columns.pkl" ]; then
    echo -e "${GREEN}✅ Model files found${NC}"
    ls -lh models/mininet_*.pkl | head -3
else
    echo -e "${RED}❌ Model files missing${NC}"
    echo "   Run: python3 train_comprehensive_model.py"
    exit 1
fi
echo ""

# 3. Check PCAP Files
echo "🔍 [3/6] Checking PCAP files..."
PCAP_COUNT=$(find mininet_data_generation/data_capture/pcaps -name "*.pcap" 2>/dev/null | wc -l)
if [ "$PCAP_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ Found $PCAP_COUNT PCAP files${NC}"
else
    echo -e "${YELLOW}⚠️  No PCAP files found${NC}"
    echo "   Run: python3 generate_varied_pcaps.py"
fi
echo ""

# 4. Reset MongoDB (optional)
echo "🔍 [4/6] MongoDB alignment..."
read -p "   Reset MongoDB to clear old data? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 reset_mongodb.py
else
    echo "   Skipping MongoDB reset"
fi
echo ""

# 5. Check if backend is already running
echo "🔍 [5/6] Checking backend status..."
if pgrep -f "python3 server.py" > /dev/null; then
    echo -e "${YELLOW}⚠️  Backend is already running${NC}"
    read -p "   Kill and restart? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "python3 server.py"
        sleep 2
        echo "   Killed existing backend"
    fi
fi
echo ""

# 6. Instructions
echo "======================================================================"
echo "SYSTEM READY"
echo "======================================================================"
echo ""
echo "📝 Next steps:"
echo ""
echo "   Terminal 1 (Backend):"
echo "   $ cd src/dashboard"
echo "   $ python3 server.py"
echo ""
echo "   Terminal 2 (Frontend):"
echo "   $ cd frontend"
echo "   $ npm start"
echo ""
echo "   Browser:"
echo "   → http://localhost:3000"
echo "   → Login as admin"
echo "   → Test simulation in dashboard"
echo ""
echo "======================================================================"
echo ""
echo -e "${GREEN}✅ All checks passed! Ready to start services.${NC}"
echo ""
