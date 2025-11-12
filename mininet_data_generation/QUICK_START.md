# Mininet Pipeline - Quick Start Guide

## 🚀 One-Command Setup

```bash
cd mininet_data_generation
./setup_mininet_pipeline.sh && python3 run_complete_pipeline.py
```

**Time:** 15-20 minutes | **Result:** Trained models ready for dashboard

---

## 📋 Prerequisites

```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install mininet tcpdump hping3 nmap netcat-openbsd

# Install Python dependencies
pip install scapy pandas numpy scikit-learn xgboost imbalanced-learn
```

---

## 🔄 Manual Workflow

### Step 1: Generate Normal Traffic (5 min)
```bash
sudo python3 topology/generate_normal_traffic.py
```
**Output:** `data_capture/pcaps/normal_traffic_*.pcap`

### Step 2: Generate Attack Traffic (2 min)
```bash
sudo python3 topology/generate_attack_traffic.py
```
**Output:** `data_capture/pcaps/attack_*_*.pcap`

### Step 3: Preprocess Data (1-2 min)
```bash
python3 data_capture/preprocess_pcap.py
```
**Output:** `data_capture/processed/mininet_dataset_*.csv`

### Step 4: Train Models (3-5 min)
```bash
python3 models/train_mininet_models.py
```
**Output:** `../models/mininet_*.pkl` (7 files)

### Step 5: Integrate with Dashboard (<1 min)
```bash
python3 integration/integrate_dashboard.py
```
**Output:** Model adapter and integration guide

### Step 6: Start Dashboard
```bash
cd .. && python scripts/start_dashboard.py
```
**Access:** http://localhost:3000

---

## 🧪 Testing

### Test Real-Time Detection
```bash
# Monitor mode (passive)
sudo python3 simulation/realtime_attack_sim.py --mode monitor --duration 60

# Simulate mode (active attacks)
sudo python3 simulation/realtime_attack_sim.py --mode simulate
```

### Verify Model Loading
```bash
python3 -c "from src.models.mininet_adapter import MininetModelAdapter; m = MininetModelAdapter(); print('✓ Models loaded successfully')"
```

### Test Prediction
```bash
python3 -c "
from src.models.mininet_adapter import MininetModelAdapter
m = MininetModelAdapter()
template = m.get_feature_template()
result = m.predict_single(template)
print(f'Prediction: {result}')
"
```

---

## 🎯 Attack Types Available

| Attack | Command | Duration |
|--------|---------|----------|
| SYN Flood | `sudo python3 topology/generate_attack_traffic.py syn_flood` | 2 min |
| Port Scan | `sudo python3 topology/generate_attack_traffic.py port_scan` | 2 min |
| UDP Flood | `sudo python3 topology/generate_attack_traffic.py udp_flood` | 2 min |
| ICMP Flood | `sudo python3 topology/generate_attack_traffic.py icmp_flood` | 2 min |
| HTTP Flood | `sudo python3 topology/generate_attack_traffic.py http_flood` | 2 min |
| DNS Amplification | `sudo python3 topology/generate_attack_traffic.py dns_amplification` | 2 min |
| Brute Force | `sudo python3 topology/generate_attack_traffic.py brute_force` | 2 min |
| Slowloris | `sudo python3 topology/generate_attack_traffic.py slowloris` | 2 min |
| All Attacks | `sudo python3 topology/generate_attack_traffic.py all` | 2 min |

---

## 📊 Expected Performance

```
Accuracy:    >95%
Precision:   >93%
Recall:      >94%
F1-Score:    >93%
ROC AUC:     >0.95
FPR:         <5%
```

---

## 🛠️ Troubleshooting

### Mininet Not Found
```bash
sudo apt-get install mininet
```

### Permission Denied
```bash
# Always use sudo for Mininet scripts
sudo python3 topology/generate_normal_traffic.py
```

### No PCAP Files
```bash
# Check directory
ls -la data_capture/pcaps/
# Regenerate if empty
sudo python3 topology/generate_normal_traffic.py
```

### Model Loading Failed
```bash
# Check models exist
ls -la ../models/mininet_*.pkl
# Retrain if missing
python3 models/train_mininet_models.py
```

---

## 🧹 Cleanup

```bash
# Remove all generated data and models
./cleanup.sh

# Clean Mininet
sudo mn -c
```

---

## 📚 Documentation

- **Overview:** `README.md`
- **Detailed Usage:** `USAGE_GUIDE.md`
- **Migration Guide:** `../MININET_MIGRATION_GUIDE.md`
- **Integration:** `../models/INTEGRATION_GUIDE.md`
- **Summary:** `../MININET_IMPLEMENTATION_SUMMARY.md`

---

## 🔗 Quick Links

### Essential Scripts
```bash
# Setup environment
./setup_mininet_pipeline.sh

# Run complete pipeline
python3 run_complete_pipeline.py

# Test installation
./test_installation.sh

# Cleanup
./cleanup.sh
```

### Key Directories
```
topology/          # Traffic generation
data_capture/      # PCAP processing
models/            # ML training
simulation/        # Real-time testing
integration/       # Dashboard integration
```

---

## ✅ Verification Checklist

- [ ] Mininet installed (`mn --version`)
- [ ] Network tools installed (`which tcpdump hping3 nmap`)
- [ ] Python dependencies installed (`pip list | grep scapy`)
- [ ] Normal traffic generated (check `data_capture/pcaps/`)
- [ ] Attack traffic generated (check `data_capture/pcaps/`)
- [ ] Data preprocessed (check `data_capture/processed/`)
- [ ] Models trained (check `../models/mininet_*.pkl`)
- [ ] Integration complete (check `../models/INTEGRATION_GUIDE.md`)
- [ ] Dashboard running (`curl http://localhost:5000/api/health`)
- [ ] Real-time detection working

---

## 🎓 Learning Path

1. **Understand the Pipeline**
   - Read `README.md`
   - Review architecture diagram

2. **Run Basic Example**
   - Execute `run_complete_pipeline.py`
   - Observe output

3. **Explore Components**
   - Generate custom traffic
   - Modify attack parameters
   - Experiment with features

4. **Advanced Usage**
   - Create custom attacks
   - Add new features
   - Optimize models

5. **Production Deployment**
   - Integrate with dashboard
   - Set up monitoring
   - Configure alerts

---

## 💡 Tips

- **Always backup** before running integration
- **Use specific attacks** for faster testing
- **Monitor resources** during traffic generation
- **Check logs** in `reports/` for debugging
- **Test incrementally** before full pipeline
- **Document changes** to topology/features

---

## 🆘 Support

**Common Commands:**
```bash
# Check Mininet status
sudo mn -c

# View PCAP files
ls -lh data_capture/pcaps/

# Check model files
ls -lh ../models/mininet_*.pkl

# View training reports
ls -lh reports/

# Test model adapter
python3 -c "from src.models.mininet_adapter import MininetModelAdapter; MininetModelAdapter()"
```

**Log Locations:**
- Traffic generation: Console output
- Preprocessing: `data_capture/processed/`
- Training: `reports/`
- Integration: Console output

---

**Last Updated:** 2025-10-07  
**Version:** 1.0  
**Status:** Production Ready
