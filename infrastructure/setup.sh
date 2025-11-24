#!/bin/bash

# SOC Assistant Infrastructure Setup Script
# Sets up monitoring and logging infrastructure

set -e

echo "🚀 SOC Assistant Infrastructure Setup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker not found. Installing monitoring stack requires Docker.${NC}"
    echo "   You can still use the application without Docker."
    echo ""
    read -p "Continue without Docker? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    DOCKER_AVAILABLE=false
else
    echo -e "${GREEN}✅ Docker found${NC}"
    DOCKER_AVAILABLE=true
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo -e "${YELLOW}⚠️  docker-compose not found${NC}"
        DOCKER_AVAILABLE=false
    fi
else
    echo -e "${GREEN}✅ docker-compose found${NC}"
fi

echo ""

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p ../logs
echo -e "${GREEN}✅ Logs directory created${NC}"

# Install Python dependencies
echo ""
echo "📦 Installing Python monitoring dependencies..."
pip install prometheus-client prometheus-flask-exporter python-json-logger psutil

echo -e "${GREEN}✅ Python dependencies installed${NC}"

# Setup Docker monitoring stack (optional)
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo ""
    echo "🐳 Docker Monitoring Stack Setup"
    echo "================================"
    echo ""
    echo "This will start:"
    echo "  - Prometheus (metrics collection) on port 9090"
    echo "  - Grafana (dashboards) on port 3001"
    echo "  - Node Exporter (system metrics) on port 9100"
    echo ""
    read -p "Start monitoring stack with Docker? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🚀 Starting monitoring stack..."
        docker-compose up -d
        
        echo ""
        echo -e "${GREEN}✅ Monitoring stack started!${NC}"
        echo ""
        echo "📊 Access Points:"
        echo "  - Prometheus: http://localhost:9090"
        echo "  - Grafana:    http://localhost:3001 (admin/admin)"
        echo "  - Metrics:    http://localhost:5000/metrics"
        echo ""
    fi
else
    echo ""
    echo -e "${YELLOW}⚠️  Docker not available. Skipping monitoring stack setup.${NC}"
    echo "   Application will still work with file-based logging."
fi

echo ""
echo "📝 Configuration"
echo "==============="
echo ""
echo "Logging:"
echo "  - JSON logs: logs/soc_assistant.json.log"
echo "  - Text logs: logs/soc_assistant.log"
echo "  - Error logs: logs/soc_assistant.error.log"
echo "  - Security audit: logs/security_audit.log"
echo ""
echo "Health Checks:"
echo "  - Health: http://localhost:5000/health"
echo "  - Ready: http://localhost:5000/health/ready"
echo "  - Live: http://localhost:5000/health/live"
echo ""
echo "Metrics:"
echo "  - Prometheus: http://localhost:5000/metrics"
echo ""

echo -e "${GREEN}✅ Infrastructure setup complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Start the application: python src/dashboard/server.py"
echo "  2. Check metrics: curl http://localhost:5000/metrics"
echo "  3. View logs: tail -f logs/soc_assistant.log"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "  4. Open Grafana: http://localhost:3001"
fi
echo ""
