# Mininet VM Setup

This directory contains everything needed to set up Mininet on a CentOS VM for network simulation.

## Architecture

The SOC Assistant uses a **distributed architecture**:

- **CentOS VM** (this setup): Mininet network simulation + PCAP generation
- **Local System**: Model training + Dashboard + Inference

## Files

### Setup Scripts

- `setup_vm_mininet_only.sh` - Main setup script for CentOS VM
- `vm_mininet_api.py` - REST API server for Mininet control

### Helper Scripts (created by setup)

- `start_mininet_api.sh` - Start API server manually
- `stop_mininet_api.sh` - Stop API server and cleanup
- `check_status.sh` - Check system status
- `cleanup_mininet.sh` - Clean up Mininet processes

### Traffic Generation (in topology/)

- `generate_normal_traffic.py` - Generate benign network traffic
- `generate_attack_traffic.py` - Generate attack traffic
- `topology_exporter.py` - Export network topology

## Quick Setup

### 1. Run Setup Script

```bash
chmod +x setup_vm_mininet_only.sh
sudo ./setup_vm_mininet_only.sh
```

### 2. Start Mininet API

```bash
# Using systemd (recommended)
sudo systemctl start mininet-api
sudo systemctl enable mininet-api

# Or manually
./start_mininet_api.sh
```

### 3. Check Status

```bash
./check_status.sh
```

### 4. Configure Local System

```bash
# On local system
export MININET_VM_HOST=<VM_IP>
export MININET_VM_PORT=5001
```

## API Endpoints

The Mininet API server exposes the following endpoints:

### Health & Status

- `GET /health` - Health check
- `GET /api/mininet/status` - Get simulation status

### Simulation Control

- `POST /api/mininet/start` - Start simulation
- `POST /api/mininet/stop` - Stop simulation
- `GET /api/mininet/attacks` - List available attacks

### PCAP Management

- `GET /api/mininet/pcaps` - List PCAP files
- `GET /api/mininet/pcap/<filename>` - Download PCAP
- `DELETE /api/mininet/pcap/<filename>` - Delete PCAP

### Maintenance

- `POST /api/mininet/cleanup` - Clean up Mininet

## Start Simulation Example

```bash
curl -X POST http://localhost:5001/api/mininet/start \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "attack",
    "attack_type": "syn_flood",
    "duration": 60,
    "samples": 10000
  }'
```

## Available Attack Types

- `syn_flood` - SYN flood DDoS attack
- `port_scan` - Port scanning attack
- `udp_flood` - UDP flood attack
- `icmp_flood` - ICMP flood (ping flood)
- `http_flood` - HTTP application layer attack
- `dns_amplification` - DNS amplification attack
- `brute_force` - SSH brute force attack
- `slowloris` - Slowloris attack

## Directory Structure

```
mininet_data_generation/
├── setup_vm_mininet_only.sh    # Main setup script
├── vm_mininet_api.py            # API server
├── topology/                    # Traffic generation scripts
│   ├── generate_normal_traffic.py
│   ├── generate_attack_traffic.py
│   └── topology_exporter.py
├── data_capture/                # PCAP storage
│   └── pcaps/                   # Generated PCAP files
└── logs/                        # Log files
```

## Systemd Service

The setup script creates a systemd service: `mininet-api.service`

### Service Commands

```bash
# Start
sudo systemctl start mininet-api

# Stop
sudo systemctl stop mininet-api

# Status
sudo systemctl status mininet-api

# Enable on boot
sudo systemctl enable mininet-api

# View logs
sudo journalctl -u mininet-api -f
```

## Firewall Configuration

The setup script configures firewall to allow:

- Port 5001 (Mininet API)
- Port 22 (SSH)
- Ports 80, 443, 8080 (for traffic generation)

### Manual Firewall Configuration

```bash
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

## Troubleshooting

### Check API Status

```bash
./check_status.sh
```

### View Logs

```bash
sudo journalctl -u mininet-api -f
```

### Clean Up Mininet

```bash
./cleanup_mininet.sh
# Or
sudo mn -c
```

### Restart Service

```bash
sudo systemctl restart mininet-api
```

### Test API Locally

```bash
curl http://localhost:5001/health
```

### Check Mininet Installation

```bash
sudo mn --version
```

### Check Open vSwitch

```bash
sudo systemctl status openvswitch
# Or
sudo ovs-vsctl show
```

## Resource Requirements

### Minimum

- 2 CPU cores
- 4 GB RAM
- 20 GB disk space

### Recommended

- 4 CPU cores
- 8 GB RAM
- 50 GB disk space

## Network Requirements

- Static IP address (recommended)
- Accessible from local system
- Firewall allows port 5001

## Security Considerations

### Network Security

- API has **no authentication** - use on internal network only
- Configure firewall to restrict access
- Consider VPN for remote access

### VM Isolation

- VM should be on isolated network segment
- Mininet creates virtual networks (no external access)
- PCAP files may contain sensitive data

## Maintenance

### Regular Tasks

```bash
# Clean old PCAP files (older than 7 days)
find data_capture/pcaps -name "*.pcap" -mtime +7 -delete

# Check disk space
df -h

# Review logs
sudo journalctl -u mininet-api --since "1 day ago"
```

### Backup

```bash
# Backup PCAP files
tar -czf pcaps_backup_$(date +%Y%m%d).tar.gz data_capture/pcaps/

# Backup configuration
cp vm_mininet_api.py vm_mininet_api.py.backup
```

## Integration with Local System

### Python Client

```python
from mininet_client import MininetClient

client = MininetClient(vm_host='192.168.1.100', vm_port=5001)

# Check health
health = client.health_check()
print(health)

# Start simulation
result = client.start_simulation(
    mode='attack',
    attack_type='syn_flood',
    duration=60
)
print(result)
```

### Environment Variables

```bash
# On local system
export MININET_VM_HOST=192.168.1.100
export MININET_VM_PORT=5001
```

## Workflow

1. **Local system** sends simulation request to VM
2. **VM** starts Mininet and generates traffic
3. **VM** captures packets to PCAP file
4. **Local system** polls for completion
5. **Local system** downloads PCAP file
6. **Local system** processes PCAP with ML models
7. **Local system** generates alerts

## Performance Tips

### Optimize Simulation

- Reduce sample count for faster simulations
- Use shorter duration for testing
- Clean up old PCAP files regularly

### Monitor Resources

```bash
# CPU and memory
htop

# Disk space
df -h

# Network
ifconfig
```

## Documentation

- Full architecture: `../docs/VM_MININET_ARCHITECTURE.md`
- Quick start: `../docs/QUICK_START_VM_MININET.md`
- API reference: See `vm_mininet_api.py` docstrings

## Support

For issues:

1. Check `./check_status.sh`
2. Review logs: `sudo journalctl -u mininet-api -f`
3. Clean up: `./cleanup_mininet.sh`
4. Restart: `sudo systemctl restart mininet-api`

## Version

- Mininet API: 1.0
- Compatible with: CentOS 7, 8, 9
- Python: 3.6+
- Mininet: 2.3.0+
