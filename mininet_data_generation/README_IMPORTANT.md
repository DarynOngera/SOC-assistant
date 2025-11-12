# ⚠️ IMPORTANT: Mininet Setup Instructions

## TL;DR - Quick Solution

```bash
# Option 1: Use the smart runner script (RECOMMENDED)
chmod +x run_with_system_python.sh
./run_with_system_python.sh

# Option 2: Run Mininet scripts manually with system Python
deactivate  # Exit venv first
sudo python3 topology/generate_normal_traffic.py
sudo python3 topology/generate_attack_traffic.py

# Then use venv for other scripts
source ../venv/bin/activate
python3 data_capture/preprocess_pcap.py
python3 models/train_mininet_models.py
```

## The Problem

You encountered: `ModuleNotFoundError: No module named 'mininet'`

**Why this happens:**
- Mininet is installed system-wide (`/usr/lib/python3/dist-packages/`)
- Your virtual environment (`venv`) doesn't have access to system packages
- Mininet scripts need system Python, but you're running them in venv

## The Solution

### ✅ Recommended: Use Smart Runner Script

The `run_with_system_python.sh` script automatically handles this:

```bash
./run_with_system_python.sh
```

**What it does:**
1. Uses system Python + sudo for Mininet traffic generation
2. Switches to venv for data processing and ML training
3. Handles everything automatically

### ✅ Alternative: Manual Execution

**For Mininet scripts (Steps 1-2):**
```bash
# Exit venv
deactivate

# Run with system Python and sudo
sudo python3 topology/generate_normal_traffic.py
sudo python3 topology/generate_attack_traffic.py
```

**For other scripts (Steps 3-5):**
```bash
# Activate venv
source ../venv/bin/activate

# Run normally
python3 data_capture/preprocess_pcap.py
python3 models/train_mininet_models.py
python3 integration/integrate_dashboard.py
```

## Complete Workflow

### Step 1: Verify Mininet Installation
```bash
# Check if Mininet is installed
dpkg -l | grep mininet

# Test with system Python (outside venv)
deactivate
sudo python3 -c "from mininet.net import Mininet; print('✓ Mininet OK')"
```

### Step 2: Generate Traffic Data
```bash
# Use system Python with sudo
sudo python3 topology/generate_normal_traffic.py  # 5 min
sudo python3 topology/generate_attack_traffic.py  # 2 min
```

### Step 3: Process and Train
```bash
# Switch to venv
source ../venv/bin/activate

# Process data
python3 data_capture/preprocess_pcap.py

# Train models
python3 models/train_mininet_models.py

# Integrate
python3 integration/integrate_dashboard.py
```

### Step 4: Start Dashboard
```bash
cd ..
python scripts/start_dashboard.py
```

## Troubleshooting

### Issue: "Cannot find required executable controller"

**Solution:** The Mininet scripts have been updated to work without a controller. Make sure you're using the latest versions.

### Issue: "Permission denied" when creating directories

**Solution:** The scripts now handle permission errors gracefully. If you still have issues:
```bash
# Create directories manually
mkdir -p data_capture/pcaps data_capture/processed reports
chmod 755 data_capture/pcaps data_capture/processed reports
```

### Issue: "HTB quantum warnings"

**Solution:** These are just warnings, not errors. The scripts will work fine. To suppress:
```bash
# Add to your script
export MININET_VERBOSITY=warning
```

### Issue: Virtual environment conflicts

**Solution:** Recreate venv with system packages access:
```bash
deactivate
rm -rf ../venv
python3 -m venv ../venv --system-site-packages
source ../venv/bin/activate
pip install -r ../requirements.txt
```

## Alternative: Skip Mininet Entirely

If Mininet is too complex, you have options:

### Option A: Use Existing Models
```bash
cd ..
python scripts/start_dashboard.py
# Dashboard works with existing models
```

### Option B: Use Synthetic Data Generator
```bash
cd ..
python scripts/generate_sample_network_data.py
```

### Option C: Use Sample PCAP Files
```bash
# Download sample captures
wget https://www.netresec.com/files/Sample-Captures/sample.pcap \
  -O data_capture/pcaps/sample.pcap

# Process them
source ../venv/bin/activate
python3 data_capture/preprocess_pcap.py
```

## Files Overview

| File | Purpose | Python Environment |
|------|---------|-------------------|
| `topology/generate_normal_traffic.py` | Generate normal traffic | System Python + sudo |
| `topology/generate_attack_traffic.py` | Generate attack traffic | System Python + sudo |
| `data_capture/preprocess_pcap.py` | Process PCAPs | Venv or system |
| `models/train_mininet_models.py` | Train ML models | Venv or system |
| `simulation/realtime_attack_sim.py` | Real-time detection | System Python + sudo |
| `integration/integrate_dashboard.py` | Dashboard integration | Venv or system |
| `run_with_system_python.sh` | **Smart runner (use this!)** | Handles both |

## Quick Reference

### ✅ DO:
- Use `run_with_system_python.sh` for automated execution
- Use system Python + sudo for Mininet scripts
- Use venv for data processing and ML scripts
- Check `INSTALLATION_FIX.md` for detailed troubleshooting

### ❌ DON'T:
- Run Mininet scripts inside venv (will fail)
- Run Mininet scripts without sudo (will fail)
- Mix Python environments in same command

## Success Indicators

After successful execution, you should have:

```bash
# Check generated files
ls -lh data_capture/pcaps/          # PCAP files
ls -lh data_capture/processed/      # CSV datasets
ls -lh ../models/mininet_*.pkl      # Trained models
ls -lh reports/                     # Training reports
```

## Getting Help

1. **Read:** `INSTALLATION_FIX.md` for detailed solutions
2. **Read:** `USAGE_GUIDE.md` for comprehensive usage
3. **Check:** `QUICK_START.md` for quick commands
4. **Review:** `MININET_IMPLEMENTATION_SUMMARY.md` for overview

## Final Notes

- **Mininet requires root:** Always use `sudo` for Mininet scripts
- **Virtual environments:** Use for non-Mininet Python scripts
- **Smart runner:** `run_with_system_python.sh` handles everything
- **Alternative paths:** You don't NEED Mininet to use the SOC dashboard

---

**Last Updated:** 2025-10-07  
**Status:** Working solution provided  
**Recommended:** Use `run_with_system_python.sh`
