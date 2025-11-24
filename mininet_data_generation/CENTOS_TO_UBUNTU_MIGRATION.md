# CentOS to Ubuntu Migration Guide

## Overview
This guide helps you migrate your Mininet VM from CentOS to Ubuntu.

## Why Ubuntu?
- ✅ **Better Package Management**: APT is more reliable than YUM
- ✅ **Easier Mininet Installation**: Available in default repositories
- ✅ **Up-to-date Packages**: More recent versions of dependencies
- ✅ **Better Documentation**: Larger community and more resources
- ✅ **Native Python 3**: Better Python 3 support out of the box
- ✅ **Simpler Setup**: Fewer compatibility issues

## Migration Steps

### 1. Backup Your CentOS VM (Optional)
```bash
# On CentOS VM, backup any custom configurations
tar -czf ~/centos_backup.tar.gz \
    ~/mininet_data_generation \
    /opt/mininet_api \
    ~/.bashrc \
    /etc/systemd/system/mininet-api.service
```

### 2. Create New Ubuntu VM
**Recommended**: Ubuntu 22.04 LTS Server

**VM Settings**:
- RAM: 4GB (minimum 2GB)
- CPU: 2 cores
- Disk: 20GB
- Network: Bridge or NAT with port forwarding

### 3. Install Ubuntu
1. Download Ubuntu Server ISO from https://ubuntu.com/download/server
2. Create new VM in VirtualBox/VMware
3. Install Ubuntu with default settings
4. Update system: `sudo apt update && sudo apt upgrade -y`

### 4. Run Setup Script
```bash
# Download the setup script
wget https://raw.githubusercontent.com/your-repo/setup_ubuntu_mininet.sh

# Or copy from your project
scp user@host:/path/to/setup_ubuntu_mininet.sh ~/

# Make executable and run
chmod +x setup_ubuntu_mininet.sh
sudo ./setup_ubuntu_mininet.sh
```

### 5. Transfer PCAP Files (If Any)
```bash
# From CentOS VM, copy PCAP files
scp -r ~/mininet_data_generation/data_capture/pcaps/* \
    user@ubuntu-vm:~/mininet_data_generation/data_capture/pcaps/
```

### 6. Setup API Server
```bash
# Copy API server file
scp user@centos-vm:/opt/mininet_api/vm_mininet_api.py \
    ~/mininet_api/

# Or use the new Ubuntu version
# See UBUNTU_SETUP_GUIDE.md for details
```

### 7. Update Dashboard Configuration
On your main machine, update the VM IP:

```bash
# Update .env file or environment variables
export MININET_VM_HOST="<NEW_UBUNTU_VM_IP>"
export MININET_VM_PORT="5001"
```

### 8. Test Connection
```bash
# From main machine
curl http://<UBUNTU_VM_IP>:5001/health

# Should return:
# {"status": "healthy", "os": "ubuntu", "mininet_available": true}
```

## Key Differences

### Package Management
| CentOS | Ubuntu |
|--------|--------|
| `yum install` | `apt install` |
| `yum update` | `apt update` |
| `systemctl` | `systemctl` (same) |

### Mininet Installation
| CentOS | Ubuntu |
|--------|--------|
| Manual compilation required | `apt install mininet` |
| Complex dependencies | Simple one-command install |
| May need EPEL repo | In default repos |

### Python
| CentOS | Ubuntu |
|--------|--------|
| Python 2 default (CentOS 7) | Python 3 default |
| `python3` may need install | `python3` pre-installed |
| `pip3` separate install | `pip3` available |

### Firewall
| CentOS | Ubuntu |
|--------|--------|
| `firewalld` | `ufw` |
| `firewall-cmd --add-port=5001/tcp` | `ufw allow 5001/tcp` |

## Troubleshooting

### Issue: Mininet Not Found
```bash
# Ubuntu solution
sudo apt install mininet

# Verify
mn --version
```

### Issue: OVS Not Starting
```bash
# Ubuntu solution
sudo systemctl start openvswitch-switch
sudo systemctl enable openvswitch-switch
```

### Issue: Permission Denied
```bash
# Add user to sudoers for Mininet
echo "$USER ALL=(ALL) NOPASSWD: /usr/bin/mn" | sudo tee /etc/sudoers.d/mininet
```

### Issue: Can't Connect from Dashboard
```bash
# Check firewall
sudo ufw status

# Allow port
sudo ufw allow 5001/tcp

# Check if API is running
sudo netstat -tlnp | grep 5001
```

## Performance Comparison

### CentOS
- Slower package updates
- More manual configuration
- Older kernel versions
- Limited Python 3 support

### Ubuntu
- Faster package updates
- Automated setup scripts
- Modern kernel versions
- Full Python 3 support

## Cleanup Old CentOS VM

After successful migration:

1. **Verify Ubuntu VM works completely**
2. **Test all simulation workflows**
3. **Backup any remaining CentOS data**
4. **Delete or archive CentOS VM**

```bash
# On host machine
# Shutdown CentOS VM
VBoxManage controlvm "CentOS-Mininet" poweroff

# Export for backup (optional)
VBoxManage export "CentOS-Mininet" -o centos-mininet-backup.ova

# Delete VM (after verification)
VBoxManage unregistervm "CentOS-Mininet" --delete
```

## Rollback Plan

If you need to rollback to CentOS:

1. Keep CentOS VM snapshot
2. Don't delete CentOS VM until Ubuntu is fully tested
3. Keep backup of CentOS configurations
4. Document any custom CentOS settings

## Post-Migration Checklist

- [ ] Ubuntu VM installed and updated
- [ ] Mininet installed and tested
- [ ] Open vSwitch running
- [ ] API server accessible from main machine
- [ ] PCAP files transferred (if needed)
- [ ] Dashboard can connect to new VM
- [ ] Simulation workflows tested
- [ ] Firewall configured
- [ ] Systemd service created (optional)
- [ ] VM snapshot taken
- [ ] Old CentOS VM backed up

## Support

For migration issues:
1. Check `UBUNTU_SETUP_GUIDE.md` for detailed setup
2. Review Ubuntu-specific troubleshooting
3. Compare with CentOS setup to identify differences

## Benefits Realized

After migration, you should experience:
- ✅ Faster setup time (minutes vs hours)
- ✅ Fewer dependency issues
- ✅ Better package availability
- ✅ Easier maintenance
- ✅ More reliable updates
- ✅ Better community support

## Conclusion

The migration from CentOS to Ubuntu simplifies the Mininet VM setup significantly. Ubuntu's superior package management and native Mininet support make it the recommended platform for this project.
