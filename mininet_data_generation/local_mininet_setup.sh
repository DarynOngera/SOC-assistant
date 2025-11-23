#!/bin/bash
# Local Mininet Setup for Parrot OS
# Generates normal and attack PCAPs locally

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Local Mininet Setup for Parrot OS${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Please run as root (sudo)${NC}"
    exit 1
fi

# Install Mininet if not present
if ! command -v mn &> /dev/null; then
    echo -e "${BLUE}Installing Mininet...${NC}"
    apt-get update
    apt-get install -y mininet openvswitch-switch
else
    echo -e "${GREEN}✓ Mininet already installed${NC}"
fi

# Install Python dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
pip3 install scapy psutil

# Create directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p data_capture/pcaps
mkdir -p logs

echo -e "${GREEN}✓ Local Mininet setup complete!${NC}"
echo -e "\nYou can now generate PCAPs using:"
echo -e "  sudo python3 generate_local_pcaps.py"
