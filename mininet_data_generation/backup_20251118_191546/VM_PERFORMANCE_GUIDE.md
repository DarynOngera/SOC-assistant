# VM Performance Optimization Guide

## 🚀 VM Performance Tuning

### VMware Workstation/Player Settings
```
VM Settings → Hardware:
✓ Memory: 16GB (minimum 8GB)
✓ Processors: 8 cores (minimum 4 cores)
✓ Hard Disk: 100GB+ with pre-allocated space
✓ Network Adapter: NAT + Host-only

VM Settings → Options:
✓ VMware Tools: Install latest version
✓ Shared folders: Disabled (for security)
✓ Unity: Disabled
✓ 3D graphics: Disabled (not needed)
✓ Hardware acceleration: Enabled
```

### VirtualBox Settings
```
VM Settings → System:
✓ Base Memory: 16384 MB (minimum 8192 MB)
✓ Processors: 8 CPUs (minimum 4 CPUs)
✓ Enable PAE/NX: Checked
✓ Hardware Virtualization: Enable VT-x/AMD-V
✓ Enable Nested Paging: Checked

VM Settings → Storage:
✓ Hard Disk: 100GB+ VDI (dynamically allocated)
✓ Enable Host I/O Cache: Checked
✓ Use solid-state drive: Checked (if host has SSD)

VM Settings → Network:
✓ Adapter 1: NAT
✓ Adapter 2: Host-only Adapter
```

### KVM/QEMU Settings
```bash
# Optimal KVM VM creation
virt-install \
  --name soc-mininet \
  --ram 16384 \
  --vcpus 8 \
  --disk path=/var/lib/libvirt/images/soc-mininet.qcow2,size=100 \
  --network network=default \
  --network network=host-only \
  --graphics spice \
  --cpu host-passthrough \
  --features kvm_hidden=on
```

---

## 📊 Performance Monitoring

### Resource Monitoring Script
```bash
#!/bin/bash
# VM Performance Monitor

while true; do
    clear
    echo "=== VM Performance Monitor ==="
    echo "Time: $(date)"
    echo ""
    
    # CPU Usage
    echo "CPU Usage:"
    top -bn1 | grep "Cpu(s)" | awk '{print "  User: " $2 ", System: " $4 ", Idle: " $8}'
    
    # Memory Usage
    echo ""
    echo "Memory Usage:"
    free -h | grep Mem | awk '{print "  Used: " $3 "/" $2 " (" int($3/$2*100) "%)"}'
    
    # Disk I/O
    echo ""
    echo "Disk Usage:"
    df -h / | tail -1 | awk '{print "  Root: " $3 "/" $2 " (" $5 ")"}'
    
    # Network
    echo ""
    echo "Network Interfaces:"
    ip -s link show | grep -A1 "state UP" | grep -E "(UP|RX:|TX:)" | head -6
    
    # Mininet Processes
    echo ""
    echo "Mininet Processes:"
    ps aux | grep -E "(mininet|ovs|mn)" | grep -v grep | wc -l | awk '{print "  Active: " $1}'
    
    sleep 5
done
```

### Performance Benchmarking
```bash
# CPU benchmark
sysbench cpu --cpu-max-prime=20000 run

# Memory benchmark
sysbench memory --memory-total-size=10G run

# Disk benchmark
sudo hdparm -Tt /dev/sda

# Network benchmark (between VM and host)
iperf3 -s  # On host
iperf3 -c HOST_IP  # In VM
```

---

## ⚡ Optimization Techniques

### 1. VM Host Optimizations
```bash
# Host system optimizations (run on host)

# Increase VM priority
sudo renice -10 $(pgrep vmware)  # VMware
sudo renice -10 $(pgrep VBox)    # VirtualBox

# Disable host swap for better VM performance
sudo swapoff -a  # Temporary
# Edit /etc/fstab to disable permanently

# CPU governor (Linux hosts)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### 2. VM Guest Optimizations
```bash
# Inside VM optimizations

# Install VM tools
sudo apt install open-vm-tools  # VMware
sudo apt install virtualbox-guest-additions-iso  # VirtualBox

# Optimize kernel parameters
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=15' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' | sudo tee -a /etc/sysctl.conf
echo 'net.core.rmem_max=134217728' | sudo tee -a /etc/sysctl.conf
echo 'net.core.wmem_max=134217728' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

### 3. Mininet-Specific Optimizations
```bash
# Optimize Open vSwitch
sudo ovs-vsctl set Open_vSwitch . other_config:max-idle=10000
sudo ovs-vsctl set Open_vSwitch . other_config:flow-eviction-threshold=1000

# Use performance controller
sudo mn --controller=remote,ip=127.0.0.1,port=6653

# Optimize link parameters
sudo mn --link=tc,bw=1000,delay=1ms
```

---

## 🔧 Pipeline Optimizations

### Sample Size Optimization
```python
# VM-optimized sample sizes (edit in scripts)
VM_OPTIMIZED_SAMPLES = {
    'small': {
        'normal': 10000,
        'attacks': 5000,
        'time_minutes': 8
    },
    'medium': {
        'normal': 25000,
        'attacks': 10000,
        'time_minutes': 15
    },
    'large': {
        'normal': 50000,
        'attacks': 20000,
        'time_minutes': 30
    }
}
```

### Parallel Processing
```python
# Enable parallel processing in scripts
import multiprocessing
from joblib import Parallel, delayed

# Use all available cores
n_jobs = multiprocessing.cpu_count()

# Parallel feature extraction
Parallel(n_jobs=n_jobs)(
    delayed(process_pcap)(file) for file in pcap_files
)
```

### Memory Management
```python
# Optimize pandas memory usage
import pandas as pd

# Read in chunks for large datasets
chunk_size = 10000
for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
    process_chunk(chunk)

# Use efficient data types
df = df.astype({
    'int_column': 'int32',
    'float_column': 'float32',
    'string_column': 'category'
})
```

---

## 📈 Performance Expectations

### VM Performance Targets

| VM Specs | Sample Size | Execution Time | Expected Performance |
|----------|-------------|----------------|---------------------|
| 8GB/4CPU | 35K samples | 15-20 minutes | Adequate |
| 16GB/8CPU | 100K samples | 20-25 minutes | Good |
| 32GB/16CPU | 250K samples | 30-40 minutes | Excellent |

### Bottleneck Identification

#### CPU Bottleneck
```bash
# Symptoms: High CPU usage (>90%), slow processing
# Solutions:
- Increase VM CPU cores
- Enable hardware acceleration
- Use parallel processing
- Reduce sample sizes
```

#### Memory Bottleneck
```bash
# Symptoms: High memory usage, swap usage, slow I/O
# Solutions:
- Increase VM RAM
- Process data in chunks
- Use memory-efficient data types
- Clear unused variables
```

#### Disk I/O Bottleneck
```bash
# Symptoms: High disk wait time, slow file operations
# Solutions:
- Use SSD storage
- Pre-allocate VM disk space
- Enable write caching
- Use faster disk interface (SATA 3.0, NVMe)
```

#### Network Bottleneck
```bash
# Symptoms: Slow packet capture, network timeouts
# Solutions:
- Use bridged networking
- Increase network buffer sizes
- Use multiple network adapters
- Optimize network parameters
```

---

## 🔍 Troubleshooting Performance Issues

### Diagnostic Commands
```bash
# System performance
htop
iotop
iftop
vmstat 1
iostat -x 1

# VM-specific
# VMware
vmware-toolbox-cmd stat speed
vmware-toolbox-cmd stat memory

# VirtualBox
VBoxManage showvminfo "VM_NAME" --machinereadable
```

### Common Performance Issues

#### Issue: Slow Pipeline Execution
```bash
# Diagnosis
top -p $(pgrep python3)
free -h
df -h

# Solutions
1. Increase VM resources
2. Reduce sample sizes
3. Enable parallel processing
4. Use SSD storage
```

#### Issue: High Memory Usage
```bash
# Diagnosis
ps aux --sort=-%mem | head
cat /proc/meminfo

# Solutions
1. Increase VM RAM
2. Process data in smaller chunks
3. Clear Python variables: del variable
4. Use garbage collection: import gc; gc.collect()
```

#### Issue: Network Performance
```bash
# Diagnosis
iperf3 -c HOST_IP
ping -c 10 HOST_IP
netstat -i

# Solutions
1. Use bridged networking
2. Increase network buffers
3. Disable network offloading
4. Use multiple network interfaces
```

---

## 📋 Performance Checklist

### Pre-Execution Checklist
- [ ] VM has adequate resources (8GB+ RAM, 4+ CPU cores)
- [ ] VM tools installed and updated
- [ ] Host system has sufficient free resources
- [ ] SSD storage preferred over HDD
- [ ] Network connectivity tested
- [ ] Swap usage minimized
- [ ] Unnecessary services disabled

### During Execution Monitoring
- [ ] CPU usage < 90%
- [ ] Memory usage < 85%
- [ ] Disk space > 20% free
- [ ] No swap usage
- [ ] Network connectivity stable
- [ ] No error messages in logs

### Post-Execution Verification
- [ ] All data files generated successfully
- [ ] Model training completed without errors
- [ ] Dashboard integration working
- [ ] Performance logs reviewed
- [ ] Resource cleanup completed

---

## 🎯 Performance Optimization Summary

### Quick Wins
1. **Increase VM RAM** to 16GB minimum
2. **Use SSD storage** for VM files
3. **Enable hardware acceleration** in VM settings
4. **Install VM tools** for better integration
5. **Reduce sample sizes** for faster testing

### Advanced Optimizations
1. **Parallel processing** for data operations
2. **Memory-efficient** data structures
3. **Network namespace isolation** for security
4. **Kernel parameter tuning** for performance
5. **Custom pipeline configurations** for VM

### Monitoring Tools
- `htop` - CPU and memory monitoring
- `iotop` - Disk I/O monitoring
- `iftop` - Network monitoring
- `vmstat` - System statistics
- Custom monitoring scripts

**VM Performance Optimization Complete!** 🚀
