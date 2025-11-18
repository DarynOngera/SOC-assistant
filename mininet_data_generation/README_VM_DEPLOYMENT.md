# VM Deployment Summary - Mininet Pipeline

## 🎯 Quick Start for CentOS VM

### 1. Download and Setup
```bash
# Clone repository
git clone https://github.com/your-repo/SOC-assistant.git
cd SOC-assistant/mininet_data_generation

# Run CentOS setup (automated)
sudo ./setup_centos_mininet.sh
```

### 2. Test Installation
```bash
# Verify everything works
./test_centos_installation.sh
```

### 3. Run Pipeline
```bash
# Execute optimized pipeline
./run_centos_pipeline.sh
```

### 4. Access Dashboard
```bash
# Start dashboard
cd .. && python3 scripts/start_dashboard.py

# Access at: http://YOUR_VM_IP:5000
```

---

## 📁 File Overview

### Setup Scripts
- **`setup_centos_mininet.sh`** - Automated CentOS setup script
- **`setup_vm_mininet.sh`** - Generic VM setup script (Ubuntu-focused)
- **`run_centos_pipeline.sh`** - CentOS-optimized pipeline runner
- **`test_centos_installation.sh`** - CentOS installation verification

### Documentation
- **`CENTOS_DEPLOYMENT_GUIDE.md`** - Complete CentOS deployment guide
- **`VM_DEPLOYMENT_GUIDE.md`** - General VM deployment guide
- **`VM_PERFORMANCE_GUIDE.md`** - Performance optimization guide

### Configuration
- **`vm_config.json`** - VM configuration parameters
- **`requirements.txt`** - Python dependencies

---

## 🐧 CentOS-Specific Features

### Automated Setup Includes:
- ✅ CentOS 7/8/9 version detection
- ✅ EPEL/PowerTools/CRB repository setup
- ✅ Mininet installation from source
- ✅ Firewalld configuration
- ✅ SELinux compatibility
- ✅ Network namespace isolation
- ✅ Performance optimizations

### Key Differences from Ubuntu:
- Uses `dnf`/`yum` instead of `apt`
- Requires EPEL repository for additional packages
- Uses `firewalld` instead of `ufw`
- SELinux considerations
- Mininet installed from source (not package)

---

## 🚀 Performance Optimizations

### VM-Optimized Sample Sizes:
- **Normal Traffic**: 25,000 samples
- **Attack Traffic**: 10,000 samples
- **Total Execution**: ~15 minutes
- **Resource Usage**: Optimized for 8GB RAM

### CentOS-Specific Optimizations:
- Network namespace isolation
- Firewall rules for dashboard access
- Kernel parameter tuning
- Service management with systemd

---

## 🔧 Troubleshooting Quick Reference

### Common CentOS Issues:
```bash
# Package not found
sudo dnf install epel-release
sudo dnf config-manager --set-enabled powertools

# Firewall blocking
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# SELinux issues
sudo setenforce 0  # Temporary
```

### Diagnostic Commands:
```bash
# System info
cat /etc/centos-release
free -h
df -h

# Services
sudo systemctl status openvswitch
sudo systemctl status firewalld

# Mininet
sudo mn --test pingall
sudo ovs-vsctl show
```

---

## 📊 Expected Results

### Pipeline Output:
- **Data Generated**: 35,000 network samples
- **Models Trained**: Random Forest + XGBoost
- **Accuracy**: 85-95%
- **Integration**: Real-time dashboard alerts

### File Structure After Completion:
```
mininet_data_generation/
├── data_capture/
│   ├── pcaps/           # Raw packet captures
│   └── processed/       # Processed CSV data
├── reports/
│   ├── models/          # Model performance reports
│   └── visualizations/  # Charts and graphs
└── logs/                # Execution logs
```

---

## 🎯 Next Steps After Setup

1. **Verify Installation**: Run test script
2. **Execute Pipeline**: Generate training data
3. **Start Dashboard**: Access web interface
4. **Test Detection**: Run real-time simulation
5. **Review Results**: Check model performance

---

## 📞 Support

### If Issues Occur:
1. Check logs: `/tmp/centos_mininet_setup.log`
2. Run diagnostics: `./test_centos_installation.sh`
3. Review troubleshooting guides
4. Check firewall and SELinux settings

### Documentation Files:
- `CENTOS_DEPLOYMENT_GUIDE.md` - Detailed CentOS setup
- `VM_PERFORMANCE_GUIDE.md` - Performance tuning
- `TROUBLESHOOTING.md` - Common issues and solutions

**Your CentOS VM is ready for Mininet pipeline deployment!** 🎉
