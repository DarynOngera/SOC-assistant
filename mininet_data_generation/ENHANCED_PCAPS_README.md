# Enhanced Attack PCAP Generation

## Problem
The current attack PCAP files contain very few packets (2-16 packets each), resulting in minimal alerts during replay simulations in the dashboard.

## Solution
Created `generate_enhanced_attack_pcaps.py` which generates attack PCAPs with significantly more packets for better visibility:

### Packet Counts by Attack Type

| Attack Type  | Packet Count | Description |
|-------------|--------------|-------------|
| **SYN Flood** | ~500 packets | 3-phase attack with increasing intensity |
| **Port Scan** | ~300 packets | Comprehensive scan of 17 common ports, multiple passes |
| **UDP Flood** | ~400 packets | Multi-port UDP flood targeting DNS and other services |
| **HTTP Flood** | ~300 packets | Intensive GET request flood from multiple sources |

### Features

1. **Multi-phase attacks**: Each attack has multiple phases with varying intensity
2. **Multiple sources**: Uses multiple hosts to simulate distributed attacks
3. **Realistic patterns**: Mimics real-world attack behavior
4. **Better visibility**: Generates enough packets to create visible alerts in dashboard

## Usage

### Generate Enhanced PCAPs

```bash
# Navigate to mininet directory
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Run with sudo (Mininet requires root)
sudo python3 generate_enhanced_attack_pcaps.py
```

### Output

The script will:
1. Generate 4 attack PCAP files in `data_capture/mininet/`
2. Replace existing small PCAP files
3. Show packet counts and file sizes for verification
4. Display total statistics

### Expected Output

```
[1/4] Generating SYN_FLOOD (500+ SYN packets)...
    Phase 1: Low intensity (100 packets)...
    Phase 2: Medium intensity (200 packets)...
    Phase 3: High intensity (200 packets)...
    ✓ Generated ~500 SYN flood packets
✓ syn_flood.pcap (45,234 bytes, ~523 packets)

[2/4] Generating PORT_SCAN (300+ scan packets)...
    Phase 1: Sequential scan...
    Phase 2: Parallel scan from multiple sources...
    ✓ Generated ~300 port scan packets
✓ port_scan.pcap (32,156 bytes, ~312 packets)

[3/4] Generating UDP_FLOOD (400+ UDP packets)...
    Phase 1: DNS flood (150 packets)...
    Phase 2: Multi-port UDP flood (250 packets)...
    ✓ Generated ~400 UDP flood packets
✓ udp_flood.pcap (38,421 bytes, ~418 packets)

[4/4] Generating HTTP_FLOOD (300+ HTTP requests)...
    Phase 1: GET flood (150 requests)...
    Phase 2: Parallel GET flood (150 requests)...
    ✓ Generated ~300 HTTP flood packets
✓ http_flood.pcap (41,789 bytes, ~327 packets)
```

## Impact on Dashboard

### Before (Current PCAPs)
- **syn_flood.pcap**: 16 packets → ~1-2 alerts
- **port_scan.pcap**: 14 packets → ~1-2 alerts
- **udp_flood.pcap**: 10 packets → ~1 alert
- **http_flood.pcap**: 2 packets → ~0 alerts

### After (Enhanced PCAPs)
- **syn_flood.pcap**: ~500 packets → ~50-100 alerts
- **port_scan.pcap**: ~300 packets → ~30-60 alerts
- **udp_flood.pcap**: ~400 packets → ~40-80 alerts
- **http_flood.pcap**: ~300 packets → ~30-60 alerts

## Alert Generation Logic

The dashboard processes PCAPs through the ML model pipeline:
1. Extracts network features from each packet flow
2. Runs features through trained ML model
3. Creates alerts for anomalies with score >= threshold
4. Broadcasts alerts to dashboard via WebSocket

With more packets, you'll see:
- More alerts in the Threat Triage view
- Better populated Network Map
- More data points in Threat Analysis charts
- Higher security event counts in Dashboard statistics

## Testing

After generating enhanced PCAPs:

1. **Start the dashboard server**:
   ```bash
   cd /home/ongera/projects/SOC-assistant/src/dashboard
   python3 server.py
   ```

2. **Start the frontend**:
   ```bash
   cd /home/ongera/projects/SOC-assistant/frontend
   npm start
   ```

3. **Run a simulation**:
   - Navigate to Admin → Mininet Simulation
   - Select an attack type (e.g., SYN Flood)
   - Click "Start Simulation"
   - Watch alerts appear in real-time

4. **Verify results**:
   - Check Threat Triage for new alerts
   - View Network Map for affected nodes
   - Check Dashboard statistics for event counts

## Troubleshooting

### No packets in PCAP
- Ensure Mininet is properly installed
- Check that scapy is installed: `pip3 install scapy`
- Verify network interfaces are up

### Permission denied
- Run with sudo: `sudo python3 generate_enhanced_attack_pcaps.py`
- Mininet requires root privileges

### Low packet counts
- Increase sleep times between packet generation
- Check system resources (CPU, memory)
- Verify tcpdump is capturing correctly

## Technical Details

### Attack Generation Methods

**SYN Flood**: Uses scapy to send TCP SYN packets with no ACK response
```python
send(IP(dst='10.0.0.2')/TCP(dport=80,flags='S'), verbose=0)
```

**Port Scan**: Uses netcat to probe multiple ports
```python
nc -zv -w 1 10.0.0.2 {port}
```

**UDP Flood**: Sends UDP packets to multiple ports
```python
echo "FLOOD_DATA" | nc -u 10.0.0.2 {port}
```

**HTTP Flood**: Uses curl to generate HTTP GET requests
```python
curl -s http://10.0.0.2
```

### Network Topology

```
    h1 (10.0.0.1) ─┐
                   ├─ s1 (switch)
    h2 (10.0.0.2) ─┤
                   │
    h3 (10.0.0.3) ─┘
```

- h1, h3: Attackers
- h2: Victim
- s1: Switch with packet capture

## Future Enhancements

1. **Variable intensity**: Add command-line options for packet counts
2. **Mixed traffic**: Combine normal and attack traffic
3. **Distributed attacks**: Simulate DDoS from many sources
4. **Protocol variety**: Add more attack types (ICMP, DNS amplification, etc.)
5. **Realistic timing**: Add jitter and realistic inter-packet delays

## References

- Original script: `generate_simple_pcaps.py`
- Dashboard integration: `src/dashboard/server.py` (lines 1265-1413)
- PCAP processing: `_process_pcap_for_alerts()` method
- Feature extraction: `_extract_features_from_pcap()` method
