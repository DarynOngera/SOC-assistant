# VM Mininet Architecture

## Overview

The SOC Assistant now uses a **distributed architecture** that separates network simulation from model training:

- **CentOS VM**: Runs Mininet for network simulation and PCAP generation
- **Local System**: Handles model training, dashboard, and inference

This architecture provides better resource isolation, security, and scalability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      LOCAL SYSTEM                            │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           SOC Dashboard (React + Flask)              │  │
│  │  • User Interface                                    │  │
│  │  • Authentication & RBAC                             │  │
│  │  • Alert Management                                  │  │
│  │  • Statistics & Visualization                        │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │         Mininet Client (mininet_client.py)           │  │
│  │  • REST API client                                   │  │
│  │  • VM communication                                  │  │
│  │  • PCAP download                                     │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │       ML Model Training & Inference                  │  │
│  │  • Random Forest                                     │  │
│  │  • XGBoost                                           │  │
│  │  • Feature extraction                                │  │
│  │  • Anomaly detection                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ HTTP/REST API
                       │ (Port 5001)
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                     CENTOS VM                                 │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      Mininet API Server (vm_mininet_api.py)          │  │
│  │  • REST API endpoints                                │  │
│  │  • Simulation control                                │  │
│  │  • PCAP file management                              │  │
│  └──────────────────┬───────────────────────────────────┘  │
│                     │                                        │
│  ┌──────────────────▼───────────────────────────────────┐  │
│  │              Mininet Network                         │  │
│  │  • Virtual network topology                          │  │
│  │  • Traffic generation (normal & attack)              │  │
│  │  • PCAP capture                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## Components

### 1. CentOS VM (Mininet Server)

**Purpose**: Network simulation and PCAP generation

**Components**:
- `vm_mininet_api.py`: REST API server exposing Mininet functionality
- Mininet: Virtual network simulation
- Traffic generators: Normal and attack traffic scripts
- PCAP capture: tcpdump for packet capture

**Key Features**:
- Isolated network simulation environment
- No model training (resource efficient)
- Exposes REST API on port 5001
- Automatic PCAP file management
- Systemd service for automatic startup

**Setup**:
```bash
cd mininet_data_generation
chmod +x setup_vm_mininet_only.sh
sudo ./setup_vm_mininet_only.sh
```

### 2. Local System (Dashboard & Training)

**Purpose**: Model training, inference, and user interface

**Components**:
- `server.py`: Main dashboard backend
- `mininet_client.py`: Client for VM communication
- ML models: Random Forest and XGBoost
- React UI: User interface

**Key Features**:
- Model training on local hardware
- Real-time inference
- PCAP processing from VM
- User authentication and RBAC
- WebSocket for real-time updates

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
| `/api/mininet/pcap/<filename>` | GET | Download PCAP file |
| `/api/mininet/pcap/<filename>` | DELETE | Delete PCAP file |
| `/api/mininet/cleanup` | POST | Clean up Mininet |

### Start Simulation Request

```json
{
  "mode": "attack",
  "attack_type": "syn_flood",
  "duration": 60,
  "samples": 10000
}
```

**Available Attack Types**:
- `syn_flood`: SYN flood DDoS attack
- `port_scan`: Port scanning attack
- `udp_flood`: UDP flood attack
- `icmp_flood`: ICMP flood (ping flood)
- `http_flood`: HTTP application layer attack
- `dns_amplification`: DNS amplification attack
- `brute_force`: SSH brute force attack
- `slowloris`: Slowloris attack

## Setup Instructions

### 1. VM Setup (CentOS)

```bash
# On CentOS VM
cd /path/to/SOC-assistant/mininet_data_generation
chmod +x setup_vm_mininet_only.sh
sudo ./setup_vm_mininet_only.sh

# Start Mininet API service
sudo systemctl start mininet-api
sudo systemctl enable mininet-api

# Check status
./check_status.sh
```

### 2. Local System Setup

```bash
# Set environment variables
export MININET_VM_HOST=192.168.1.100  # Replace with your VM IP
export MININET_VM_PORT=5001

# Or add to .env file
echo "MININET_VM_HOST=192.168.1.100" >> .env
echo "MININET_VM_PORT=5001" >> .env

# Start dashboard
cd src/dashboard
python3 server.py
```

### 3. Verify Connection

```bash
# Test VM API from local system
curl http://192.168.1.100:5001/health

# Expected response:
# {
#   "status": "healthy",
#   "service": "VM Mininet API",
#   "mininet_available": true
# }
```

## Workflow

### Simulation Workflow

1. **User initiates simulation** via dashboard UI
2. **Local system** sends request to VM via `mininet_client.py`
3. **VM** starts Mininet simulation and generates traffic
4. **VM** captures packets to PCAP file
5. **Local system** polls VM for completion
6. **Local system** downloads PCAP file from VM
7. **Local system** processes PCAP through ML models
8. **Local system** generates alerts and updates dashboard

### Data Flow

```
User Action → Dashboard UI → server.py → mininet_client.py
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
                                    HTTP Response (status)
                                              ↓
                                    Local System Downloads PCAP
                                              ↓
                                    ML Model Processing
                                              ↓
                                    Alert Generation
                                              ↓
                                    Dashboard Update (WebSocket)
```

## Configuration

### Environment Variables

**Local System** (`.env` or shell):
```bash
# Required
MININET_VM_HOST=192.168.1.100
MININET_VM_PORT=5001

# Optional
MININET_TIMEOUT=30
```

**VM System**:
No configuration needed - API runs on 0.0.0.0:5001

### Firewall Configuration

**VM Firewall** (CentOS):
```bash
# Allow API port
sudo firewall-cmd --permanent --add-port=5001/tcp
sudo firewall-cmd --reload
```

**Local Firewall**:
No changes needed (outbound connections only)

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

# Clean up Mininet
sudo mn -c

# Check logs
sudo journalctl -u mininet-api -f

# Restart service
sudo systemctl restart mininet-api
```

### PCAP Download Fails

```bash
# Check PCAP directory
ls -la data_capture/pcaps/

# Check permissions
chmod 755 data_capture/pcaps/

# Check disk space
df -h
```

### Connection Timeout

```bash
# Increase timeout in mininet_client.py
# Default is 30 seconds

# Or set environment variable
export MININET_TIMEOUT=60
```

## Performance Considerations

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
- Download time: 1-10 seconds (depending on network)
- Simulation duration: 30-120 seconds

### Concurrent Simulations

- VM supports **one simulation at a time**
- Queue additional requests on local system
- Use simulation status endpoint to check availability

## Security Considerations

### Network Security

- VM API has **no authentication** (internal network only)
- Use **firewall rules** to restrict access
- Consider **VPN** for remote access
- Use **HTTPS** for production (add reverse proxy)

### VM Isolation

- VM should be on **isolated network segment**
- Mininet creates **virtual networks** (no external access)
- PCAP files contain **network traffic** (sensitive data)

### Access Control

- Dashboard has **RBAC** (Role-Based Access Control)
- Only **admins** can trigger simulations
- Audit logs track all simulation activities

## Maintenance

### Regular Tasks

```bash
# Clean up old PCAP files (on VM)
find data_capture/pcaps -name "*.pcap" -mtime +7 -delete

# Check disk space
df -h

# Review logs
sudo journalctl -u mininet-api --since "1 day ago"

# Update system
sudo yum update -y  # or dnf update -y
```

### Backup

```bash
# Backup PCAP files
tar -czf pcaps_backup_$(date +%Y%m%d).tar.gz data_capture/pcaps/

# Backup configuration
cp vm_mininet_api.py vm_mininet_api.py.backup
```

## Migration from Local Mininet

If you were using local Mininet (PCAP replay mode):

1. **Keep existing PCAP files** - they still work
2. **Set up VM** using setup script
3. **Configure environment variables** on local system
4. **Test connection** with health check
5. **Start using remote simulations**

The system automatically falls back to local PCAPs if VM is unavailable.

## Benefits of This Architecture

### Separation of Concerns
- **VM**: Network simulation only
- **Local**: Model training and inference

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

## Future Enhancements

- [ ] Multiple VM support (load balancing)
- [ ] HTTPS/TLS for API communication
- [ ] Authentication for VM API
- [ ] Distributed PCAP storage
- [ ] Real-time streaming (instead of download)
- [ ] VM health monitoring dashboard
- [ ] Automatic VM provisioning
- [ ] Container-based deployment (Docker/Kubernetes)
