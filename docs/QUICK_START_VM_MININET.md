# Quick Start: VM Mininet Setup

This guide will get you up and running with the distributed Mininet architecture in under 30 minutes.

## Prerequisites

- **CentOS VM**: CentOS 7, 8, or 9
- **Local System**: Linux, macOS, or WSL2
- **Network**: VM and local system on same network
- **Privileges**: Root access on VM

## Step 1: Setup CentOS VM (10 minutes)

### 1.1 Copy Files to VM

```bash
# On local system
scp -r mininet_data_generation user@vm-ip:/tmp/

# SSH to VM
ssh user@vm-ip
cd /tmp/mininet_data_generation
```

### 1.2 Run Setup Script

```bash
chmod +x setup_vm_mininet_only.sh
sudo ./setup_vm_mininet_only.sh
```

**What it does**:
- Installs Mininet and dependencies
- Installs Open vSwitch
- Sets up Mininet API server
- Configures firewall
- Creates systemd service

### 1.3 Start Mininet API

```bash
# Start service
sudo systemctl start mininet-api

# Enable on boot
sudo systemctl enable mininet-api

# Check status
./check_status.sh
```

### 1.4 Note VM IP Address

```bash
hostname -I
# Example output: 192.168.1.100
```

## Step 2: Configure Local System (5 minutes)

### 2.1 Set Environment Variables

```bash
# Add to ~/.bashrc or ~/.zshrc
export MININET_VM_HOST=192.168.1.100  # Replace with your VM IP
export MININET_VM_PORT=5001

# Or create .env file in project root
cat > .env << EOF
MININET_VM_HOST=192.168.1.100
MININET_VM_PORT=5001
EOF
```

### 2.2 Install Dependencies (if not already done)

```bash
pip install flask flask-cors requests
```

## Step 3: Test Connection (2 minutes)

### 3.1 Test from Command Line

```bash
# Health check
curl http://192.168.1.100:5001/health

# Expected output:
# {
#   "status": "healthy",
#   "service": "VM Mininet API",
#   "mininet_available": true
# }
```

### 3.2 Test with Python Client

```bash
cd src/dashboard
python3 -c "
from mininet_client import MininetClient
client = MininetClient(vm_host='192.168.1.100', vm_port=5001)
print('VM Available:', client.is_available())
"
```

## Step 4: Start Dashboard (2 minutes)

```bash
cd src/dashboard
python3 server.py
```

**Expected output**:
```
✅ Mininet VM is available and ready
🚀 SOC Dashboard running on http://localhost:5000
```

## Step 5: Run First Simulation (5 minutes)

### 5.1 Via Dashboard UI

1. Open browser: `http://localhost:3000`
2. Login as admin
3. Navigate to "Mininet Simulation"
4. Select attack type (e.g., "SYN Flood")
5. Set duration (e.g., 60 seconds)
6. Click "Start Simulation"

### 5.2 Via API

```bash
# Start normal traffic simulation
curl -X POST http://localhost:5000/api/mininet/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "mode": "normal",
    "duration": 60,
    "samples": 10000
  }'

# Start attack simulation
curl -X POST http://localhost:5000/api/mininet/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "mode": "attack",
    "attack_type": "syn_flood",
    "duration": 60,
    "samples": 10000
  }'
```

### 5.3 Via Python Client

```python
from mininet_client import MininetClient

# Initialize client
client = MininetClient(vm_host='192.168.1.100', vm_port=5001)

# Start simulation
result = client.start_simulation(
    mode='attack',
    attack_type='syn_flood',
    duration=60,
    samples=10000
)

print(result)
```

## Verification Checklist

- [ ] VM setup completed without errors
- [ ] Mininet API service is running
- [ ] Health check returns success
- [ ] Local system can connect to VM
- [ ] Dashboard starts without errors
- [ ] First simulation completes successfully
- [ ] Alerts appear in dashboard
- [ ] PCAP files are downloaded

## Common Issues

### Issue: VM Not Reachable

**Solution**:
```bash
# On VM - check firewall
sudo firewall-cmd --list-ports
# Should show: 5001/tcp

# If not, add it
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

### Issue: Mininet Service Not Starting

**Solution**:
```bash
# Check logs
sudo journalctl -u mininet-api -n 50

# Clean up Mininet
sudo mn -c

# Restart service
sudo systemctl restart mininet-api
```

### Issue: Connection Timeout

**Solution**:
```bash
# Check VM IP is correct
ping 192.168.1.100

# Check API is listening
# On VM:
sudo netstat -tulpn | grep 5001

# Should show Python listening on 0.0.0.0:5001
```

### Issue: Permission Denied

**Solution**:
```bash
# On VM - check directory permissions
chmod 755 data_capture/pcaps/

# Restart service as root
sudo systemctl restart mininet-api
```

## Next Steps

### Train Models Locally

```bash
# Process downloaded PCAPs
cd mininet_data_generation
python3 process_training_data.py

# Train models
python3 train_exportable_models.py
```

### Monitor VM

```bash
# On VM - check status
./check_status.sh

# View logs
sudo journalctl -u mininet-api -f

# Check resource usage
htop
```

### Scale Up

- Add more VMs for load balancing
- Increase simulation duration
- Generate more training samples
- Configure multiple attack types

## Architecture Overview

```
Local System                    CentOS VM
┌─────────────┐                ┌─────────────┐
│  Dashboard  │───HTTP/REST───▶│ Mininet API │
│             │◀───PCAP────────│             │
│ ML Training │                │  Simulation │
└─────────────┘                └─────────────┘
```

## Resources

- Full documentation: `docs/VM_MININET_ARCHITECTURE.md`
- API reference: `mininet_data_generation/vm_mininet_api.py`
- Client library: `src/dashboard/mininet_client.py`
- Setup script: `mininet_data_generation/setup_vm_mininet_only.sh`

## Support

If you encounter issues:

1. Check logs: `sudo journalctl -u mininet-api -f`
2. Verify network: `ping VM_IP`
3. Test API: `curl http://VM_IP:5001/health`
4. Clean up: `sudo mn -c`
5. Restart: `sudo systemctl restart mininet-api`

## Summary

You now have:
- ✅ Mininet running on isolated VM
- ✅ REST API for remote control
- ✅ Local system for model training
- ✅ Distributed architecture
- ✅ PCAP generation and processing
- ✅ Real-time simulation capabilities

**Total setup time**: ~25 minutes
**Ready for production**: Yes (with proper security hardening)
