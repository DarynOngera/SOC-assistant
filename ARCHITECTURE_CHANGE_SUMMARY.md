# Architecture Change Summary

## Overview

Successfully restructured the SOC Assistant to use a **distributed architecture** where:
- **CentOS VM**: Handles Mininet network simulation and PCAP generation
- **Local System**: Handles model training, dashboard, and inference

## What Changed

### Previous Architecture (Local PCAP Replay)
```
Local System
├── Dashboard (React + Flask)
├── ML Models (Training + Inference)
└── Mininet (PCAP Replay Mode)
    └── Pre-generated PCAP files
```

**Limitations**:
- Required pre-generated PCAP files
- No live network simulation
- Limited attack variety
- No root privileges needed (but also no real simulation)

### New Architecture (Distributed VM-based)
```
┌─────────────────────────────────┐
│       Local System              │
│  ├── Dashboard (React + Flask)  │
│  ├── ML Models (Training)       │
│  ├── Mininet Client             │
│  └── PCAP Processing            │
└──────────────┬──────────────────┘
               │ HTTP/REST (5001)
┌──────────────▼──────────────────┐
│       CentOS VM                 │
│  ├── Mininet API Server         │
│  ├── Mininet Network Sim        │
│  ├── Traffic Generation         │
│  └── PCAP Capture               │
└─────────────────────────────────┘
```

**Benefits**:
- ✅ Live network simulation
- ✅ Real-time traffic generation
- ✅ Multiple attack types
- ✅ Isolated simulation environment
- ✅ Better resource utilization
- ✅ Scalable architecture

## New Files Created

### VM-Side (CentOS)
1. **`mininet_data_generation/vm_mininet_api.py`**
   - REST API server for Mininet control
   - Exposes simulation endpoints
   - Manages PCAP files
   - Runs as systemd service

2. **`mininet_data_generation/setup_vm_mininet_only.sh`**
   - Automated setup script for CentOS
   - Installs Mininet and dependencies
   - Configures firewall
   - Creates systemd service

3. **`mininet_data_generation/README_VM_SETUP.md`**
   - VM setup documentation
   - API reference
   - Troubleshooting guide

### Local-Side
1. **`src/dashboard/mininet_client.py`**
   - Python client for VM API
   - Handles HTTP communication
   - Downloads PCAP files
   - Manages simulation lifecycle

2. **`src/dashboard/server.py`** (modified)
   - Added `_initialize_mininet_client()` method
   - Updated `start_mininet_simulation()` to use remote VM
   - Updated `stop_mininet_simulation()` to use remote VM
   - Added `_monitor_vm_simulation()` for progress tracking

### Documentation
1. **`docs/VM_MININET_ARCHITECTURE.md`**
   - Complete architecture documentation
   - API reference
   - Configuration guide
   - Troubleshooting

2. **`docs/QUICK_START_VM_MININET.md`**
   - 30-minute quick start guide
   - Step-by-step instructions
   - Common issues and solutions

## API Endpoints

### VM Mininet API (Port 5001)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/mininet/status` | GET | Get simulation status |
| `/api/mininet/attacks` | GET | List available attacks |
| `/api/mininet/start` | POST | Start simulation |
| `/api/mininet/stop` | POST | Stop simulation |
| `/api/mininet/pcaps` | GET | List PCAP files |
| `/api/mininet/pcap/<filename>` | GET | Download PCAP |
| `/api/mininet/pcap/<filename>` | DELETE | Delete PCAP |
| `/api/mininet/cleanup` | POST | Clean up Mininet |

## Configuration

### Environment Variables (Local System)

```bash
# Required
export MININET_VM_HOST=192.168.1.100  # Your VM IP
export MININET_VM_PORT=5001

# Optional
export MININET_TIMEOUT=30
```

### VM Setup

```bash
# On CentOS VM
cd mininet_data_generation
chmod +x setup_vm_mininet_only.sh
sudo ./setup_vm_mininet_only.sh

# Start service
sudo systemctl start mininet-api
sudo systemctl enable mininet-api
```

## Migration Guide

### For Existing Users

1. **Keep existing setup** - local PCAP replay still works
2. **Set up VM** using `setup_vm_mininet_only.sh`
3. **Configure environment variables** on local system
4. **Test connection** with health check
5. **Start using remote simulations**

### Backward Compatibility

The system automatically falls back to local PCAP replay if:
- VM is not configured (`MININET_VM_HOST` not set)
- VM is not reachable
- VM simulation fails

## Workflow

### Simulation Workflow

1. User initiates simulation via dashboard
2. Local system sends request to VM via REST API
3. VM starts Mininet and generates traffic
4. VM captures packets to PCAP file
5. Local system polls VM for completion status
6. Local system downloads PCAP file from VM
7. Local system processes PCAP through ML models
8. Local system generates alerts and updates dashboard

### Data Flow

```
User → Dashboard → server.py → mininet_client.py
                                       ↓
                                  HTTP Request
                                       ↓
                              VM Mininet API (5001)
                                       ↓
                              Mininet Simulation
                                       ↓
                                 PCAP Capture
                                       ↓
                              PCAP File Storage
                                       ↓
                         Local System Downloads PCAP
                                       ↓
                           ML Model Processing
                                       ↓
                            Alert Generation
                                       ↓
                         Dashboard Update (WebSocket)
```

## Testing

### Test VM Connection

```bash
# From local system
curl http://192.168.1.100:5001/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "VM Mininet API",
#   "mininet_available": true
# }
```

### Test Simulation

```bash
# Start simulation
curl -X POST http://192.168.1.100:5001/api/mininet/start \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "attack",
    "attack_type": "syn_flood",
    "duration": 60,
    "samples": 10000
  }'

# Check status
curl http://192.168.1.100:5001/api/mininet/status
```

## Security Considerations

### Network Security
- VM API has **no authentication** - use on internal network only
- Configure firewall to restrict access to trusted IPs
- Consider VPN for remote access
- Use HTTPS/TLS for production (add reverse proxy)

### VM Isolation
- VM should be on isolated network segment
- Mininet creates virtual networks (no external access)
- PCAP files may contain sensitive data

### Access Control
- Dashboard has RBAC (Role-Based Access Control)
- Only admins can trigger simulations
- Audit logs track all simulation activities

## Performance

### VM Resources

**Minimum**:
- 2 CPU cores
- 4 GB RAM
- 20 GB disk space

**Recommended**:
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space

### Network Bandwidth
- Typical PCAP file: 10-100 MB
- Download time: 1-10 seconds
- Simulation duration: 30-120 seconds

## Troubleshooting

### VM Not Reachable

```bash
# Check VM IP
hostname -I

# Check API service
sudo systemctl status mininet-api

# Check firewall
sudo firewall-cmd --list-ports

# Test locally on VM
curl http://localhost:5001/health
```

### Simulation Fails

```bash
# Check Mininet
sudo mn --version

# Clean up
sudo mn -c

# Check logs
sudo journalctl -u mininet-api -f

# Restart service
sudo systemctl restart mininet-api
```

## Benefits Summary

### Separation of Concerns
- VM: Network simulation only
- Local: Model training and inference

### Resource Efficiency
- VM doesn't need ML libraries or GPU
- Local system doesn't need root privileges
- Better resource utilization

### Scalability
- Multiple local systems can use same VM
- Easy to add more VMs for load balancing
- Horizontal scaling possible

### Security
- Mininet runs in isolated VM
- No root access needed on local system
- Better audit trail

### Flexibility
- Train models locally with full hardware access
- Generate data on dedicated VM
- Easy to update either component independently

## Next Steps

### Immediate
- [ ] Set up CentOS VM
- [ ] Configure environment variables
- [ ] Test connection
- [ ] Run first simulation

### Future Enhancements
- [ ] Multiple VM support (load balancing)
- [ ] HTTPS/TLS for API communication
- [ ] Authentication for VM API
- [ ] Distributed PCAP storage
- [ ] Real-time streaming (instead of download)
- [ ] VM health monitoring dashboard
- [ ] Automatic VM provisioning
- [ ] Container-based deployment (Docker/Kubernetes)

## Documentation

- **Architecture**: `docs/VM_MININET_ARCHITECTURE.md`
- **Quick Start**: `docs/QUICK_START_VM_MININET.md`
- **VM Setup**: `mininet_data_generation/README_VM_SETUP.md`
- **API Reference**: `mininet_data_generation/vm_mininet_api.py`
- **Client Library**: `src/dashboard/mininet_client.py`

## Support

For issues or questions:
1. Check documentation in `docs/`
2. Review logs: `sudo journalctl -u mininet-api -f`
3. Test connection: `curl http://VM_IP:5001/health`
4. Clean up: `sudo mn -c`
5. Restart: `sudo systemctl restart mininet-api`

---

**Architecture Change Date**: 2024
**Status**: ✅ Complete and Ready for Use
**Backward Compatible**: Yes (falls back to local PCAP replay)
