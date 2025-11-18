# Mininet Installation & Fix Guide

## Issue: Mininet Python Module Not Found

The error `ModuleNotFoundError: No module named 'mininet'` occurs because Mininet is installed system-wide but not accessible in your virtual environment.

## Solutions

### Option 1: Use System Python (Recommended for Mininet)

Mininet scripts must run with system Python that has access to system packages:

```bash
# Deactivate virtual environment
deactivate

# Run Mininet scripts with system Python and sudo
sudo python3 topology/generate_normal_traffic.py
sudo python3 topology/generate_attack_traffic.py

# For other scripts (preprocessing, training), use venv
source ../venv/bin/activate
python3 data_capture/preprocess_pcap.py
python3 models/train_mininet_models.py
```

### Option 2: Allow Venv to Access System Packages

```bash
# Recreate venv with system packages access
deactivate
rm -rf ../venv
python3 -m venv ../venv --system-site-packages
source ../venv/bin/activate
pip install -r ../requirements.txt
```

### Option 3: Install Mininet Python Package (May Not Work)

```bash
# Try installing mininet in venv (often fails)
pip install mininet
```

### Option 4: Use Alternative Approach (No Mininet Required)

Since Mininet setup is complex, you can use the existing trained models or generate synthetic data:

```bash
# Skip Mininet data generation
# Use existing models or synthetic data generator
python3 ../scripts/generate_sample_network_data.py
```

## Recommended Workflow

### Step 1: Install Mininet System-Wide
```bash
sudo apt-get update
sudo apt-get install mininet
```

### Step 2: Verify Mininet Installation
```bash
# Test with system Python (outside venv)
deactivate
sudo python3 -c "from mininet.net import Mininet; print('Mininet OK')"
```

### Step 3: Run Mininet Scripts with System Python
```bash
# Always use sudo and system python3 for Mininet
sudo python3 topology/generate_normal_traffic.py
sudo python3 topology/generate_attack_traffic.py
```

### Step 4: Run Other Scripts in Venv
```bash
# Activate venv for non-Mininet scripts
source ../venv/bin/activate
python3 data_capture/preprocess_pcap.py
python3 models/train_mininet_models.py
python3 integration/integrate_dashboard.py
```

## Alternative: Skip Mininet Entirely

If Mininet is too complex to set up, you can:

### 1. Use Existing Models
The SOC dashboard already has trained models. Just integrate them:

```bash
cd ..
python scripts/start_dashboard.py
```

### 2. Generate Synthetic Data
Use the built-in data generator:

```bash
cd ..
python scripts/generate_sample_network_data.py
```

### 3. Use Pre-recorded PCAP Files
Download sample PCAP files and process them:

```bash
# Download sample PCAPs
wget https://www.netresec.com/files/Sample-Captures/sample.pcap -O data_capture/pcaps/sample.pcap

# Process with venv
source ../venv/bin/activate
python3 data_capture/preprocess_pcap.py
```

## Quick Fix for Current Error

```bash
# Exit venv
deactivate

# Test Mininet with system Python
sudo python3 -c "from mininet.net import Mininet; print('✓ Mininet accessible')"

# If that works, run Mininet scripts with system Python
sudo python3 topology/generate_normal_traffic.py

# For other scripts, use venv
source ../venv/bin/activate
python3 data_capture/preprocess_pcap.py
```

## Understanding the Issue

- **Mininet** is a system package installed in `/usr/lib/python3/dist-packages/`
- **Virtual environments** by default don't access system packages
- **Solution**: Either use system Python for Mininet OR recreate venv with `--system-site-packages`

## Verification Commands

```bash
# Check if Mininet is installed system-wide
dpkg -l | grep mininet

# Check Python path
python3 -c "import sys; print(sys.path)"

# Check if mininet module exists
python3 -c "import mininet; print(mininet.__file__)" 2>/dev/null || echo "Not found"
```

## Final Recommendation

**For simplest setup:**

1. **Use system Python for Mininet scripts** (with sudo)
2. **Use venv for everything else**
3. **Or skip Mininet** and use existing models/synthetic data

The SOC dashboard works perfectly without Mininet-generated data!
