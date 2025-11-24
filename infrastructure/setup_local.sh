#!/bin/bash

# SOC Assistant Local Infrastructure Setup (No Docker Required)
# Sets up monitoring and logging without Docker

set -e

echo "🚀 SOC Assistant Local Infrastructure Setup"
echo "==========================================="
echo ""
echo "This setup does NOT require Docker!"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p ../logs
echo -e "${GREEN}✅ Logs directory created: ../logs/${NC}"
echo ""

# Install Python dependencies
echo "📦 Installing Python monitoring dependencies..."
echo ""

# Check if virtual environment is active
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo -e "${YELLOW}⚠️  Virtual environment not detected${NC}"
    echo "   Recommended: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

pip install prometheus-client prometheus-flask-exporter python-json-logger psutil

echo ""
echo -e "${GREEN}✅ Python dependencies installed${NC}"
echo ""

# Test imports
echo "🧪 Testing Python imports..."
python3 << EOF
try:
    from prometheus_client import Counter, Gauge, Histogram
    from pythonjsonlogger import jsonlogger
    import psutil
    print("✅ All imports successful!")
except ImportError as e:
    print(f"❌ Import failed: {e}")
    exit(1)
EOF

echo ""
echo -e "${GREEN}✅ Infrastructure modules ready!${NC}"
echo ""

echo "📝 Configuration"
echo "==============="
echo ""
echo "Logging (File-based):"
echo "  - JSON logs: logs/soc_assistant.json.log"
echo "  - Text logs: logs/soc_assistant.log"
echo "  - Error logs: logs/soc_assistant.error.log"
echo "  - Security audit: logs/security_audit.log"
echo ""
echo "Metrics (In-Memory):"
echo "  - Endpoint: http://localhost:5000/metrics"
echo "  - Format: Prometheus text format"
echo "  - Collection: Automatic on each request"
echo ""
echo "Health Checks:"
echo "  - Health: http://localhost:5000/health"
echo "  - Ready: http://localhost:5000/health/ready"
echo "  - Live: http://localhost:5000/health/live"
echo ""

echo -e "${BLUE}📊 Viewing Metrics (No Grafana Required)${NC}"
echo "========================================"
echo ""
echo "Option 1: View raw metrics"
echo "  curl http://localhost:5000/metrics"
echo ""
echo "Option 2: View specific metric"
echo "  curl http://localhost:5000/metrics | grep alerts_generated"
echo ""
echo "Option 3: Monitor in real-time"
echo "  watch -n 2 'curl -s http://localhost:5000/metrics | grep -E \"(alerts|http_requests)\"'"
echo ""

echo -e "${BLUE}📝 Viewing Logs${NC}"
echo "=============="
echo ""
echo "Option 1: Tail all logs"
echo "  tail -f logs/soc_assistant.log"
echo ""
echo "Option 2: View JSON logs (formatted)"
echo "  tail -f logs/soc_assistant.json.log | jq"
echo ""
echo "Option 3: View errors only"
echo "  tail -f logs/soc_assistant.error.log"
echo ""
echo "Option 4: Search logs"
echo "  grep 'alert_generated' logs/soc_assistant.log"
echo ""

echo -e "${GREEN}✅ Local infrastructure setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Start the application: python src/dashboard/server.py"
echo "  2. Check metrics: curl http://localhost:5000/metrics"
echo "  3. View logs: tail -f logs/soc_assistant.log"
echo "  4. Check health: curl http://localhost:5000/health | jq"
echo ""
echo -e "${BLUE}💡 Tip: Install 'jq' for better JSON viewing${NC}"
echo "   Ubuntu/Debian: sudo apt-get install jq"
echo "   macOS: brew install jq"
echo ""
