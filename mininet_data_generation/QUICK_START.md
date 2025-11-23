# Quick Start - Generate Attack PCAPs

## The script was interrupted. Here's how to complete it:

### Option 1: Generate One at a Time (Recommended)

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Generate each attack (takes 30-60 seconds each)
sudo bash generate_one_attack.sh syn_flood
sudo bash generate_one_attack.sh port_scan
sudo bash generate_one_attack.sh udp_flood
sudo bash generate_one_attack.sh http_flood
```

**Why one at a time?**
- Easier to debug if something fails
- Can interrupt and resume
- See progress for each attack
- Less likely to timeout

### Option 2: Run Full Script (if you have time)

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation
sudo bash regenerate_all_pcaps.sh
```

**Note**: Takes 5-10 minutes total, don't interrupt!

## Verify Generated PCAPs

```bash
# Check what was generated
ls -lh data_capture/mininet/

# Verify IPv4 content
tcpdump -r data_capture/mininet/syn_flood.pcap -c 10
```

**Expected**: Should see "IP" packets (not "IP6")

## If You Get Interrupted Again

Just run the individual attack script again:
```bash
sudo bash generate_one_attack.sh syn_flood
```

It will overwrite the incomplete PCAP.

## Current Status

Based on your terminal output:
- ✓ Backup created
- ✓ SYN flood started but interrupted
- ⏳ Need to complete: syn_flood, port_scan, udp_flood, http_flood

## Next Steps

1. **Generate remaining PCAPs** (one at a time):
   ```bash
   cd /home/ongera/projects/SOC-assistant/mininet_data_generation
   sudo bash generate_one_attack.sh syn_flood
   sudo bash generate_one_attack.sh port_scan
   sudo bash generate_one_attack.sh udp_flood
   sudo bash generate_one_attack.sh http_flood
   ```

2. **Verify all have IPv4**:
   ```bash
   for f in data_capture/mininet/*.pcap; do
       echo "=== $(basename $f) ==="
       tcpdump -r "$f" -c 5 2>&1 | grep "IP " | head -2
   done
   ```

3. **Test in dashboard**:
   - Restart dashboard server
   - Run attack simulation
   - Should work without "No IPv4 data" warning

## Troubleshooting

### "Terminated" or interrupted
- Just run the command again
- Or use `generate_one_attack.sh` for individual attacks

### "No IPv4 packets"
- Check if IPv6 was properly disabled
- Verify hping3 has `-4` flag
- Check script output for errors

### "Permission denied"
- Must use `sudo`
- Scripts need root for Mininet

## Time Estimate

- SYN flood: ~60 seconds
- Port scan: ~30 seconds  
- UDP flood: ~60 seconds
- HTTP flood: ~45 seconds

**Total**: ~4 minutes (if run one at a time)
