# Minimal Setup Guide - 4GB RAM / 25GB Storage

## 🎯 **Minimal vs Standard Comparison**

| Aspect | **Minimal Setup** | **Standard Setup** |
|--------|-------------------|-------------------|
| **RAM** | 4GB | 8GB |
| **Storage** | 25GB | 50GB |
| **CPU** | 2 cores | 4+ cores |
| **Samples** | 7K total | 35K total |
| **Runtime** | ~5 minutes | ~15 minutes |
| **Memory Usage** | <3GB peak | <6GB peak |

---

## 🚀 **Quick Minimal Setup**

### **1. Run Minimal Setup**
```bash
cd SOC-assistant/mininet_data_generation
sudo ./setup_minimal_centos.sh
```

### **2. Test Installation**
```bash
./test_minimal_setup.sh
```

### **3. Run Minimal Pipeline**
```bash
./run_minimal_pipeline.sh
```

---

## ⚡ **Minimal Configuration Details**

### **Sample Sizes (Optimized for 4GB RAM):**
- **Normal Traffic**: 5,000 samples
- **SYN Flood**: 500 samples
- **Port Scan**: 500 samples  
- **UDP Flood**: 500 samples
- **HTTP Flood**: 500 samples
- **Total**: 7,000 samples

### **Memory Optimizations:**
- **Chunk Processing**: Process 500 packets at a time
- **Single Threading**: Avoid parallel processing overhead
- **Lightweight Models**: Random Forest with 50 trees (vs 100)
- **Basic Features**: 8 core features (vs 40+ advanced)
- **Garbage Collection**: Aggressive memory cleanup

### **Storage Optimizations:**
- **No Intermediate Files**: Process and delete immediately
- **Compressed Logs**: Minimal logging
- **Essential Packages Only**: Skip optional dependencies

---

## 📊 **Expected Performance**

### **Minimal Setup Results:**
```
Dataset: 7,000 samples, 8 features
Normal: 5,000, Attacks: 2,000

Model Performance:
Accuracy: 0.89-0.93 (vs 0.94-0.96 standard)
Training Time: 30 seconds (vs 3-5 minutes)
Memory Usage: 2.1GB peak (vs 5.2GB)
```

### **What You Get:**
✅ **Basic anomaly detection** (89-93% accuracy)  
✅ **Real-time predictions** (functional)  
✅ **Dashboard integration** (working)  
✅ **Attack type classification** (basic)  
✅ **Network visualization** (simplified)  

### **What's Reduced:**
⚠️ **Feature richness** (8 vs 40+ features)  
⚠️ **Model complexity** (lighter algorithms)  
⚠️ **Sample diversity** (fewer attack variants)  
⚠️ **Statistical depth** (basic flow analysis)  

---

## 🔧 **Minimal Pipeline Steps**

### **1. Traffic Generation (2 minutes)**
```bash
# Normal traffic: 5K samples, ~3 minutes simulation
# Attack traffic: 2K samples, ~1 minute simulation
# Total PCAP size: ~5-8MB (vs 50-100MB)
```

### **2. Feature Extraction (1 minute)**
```bash
# Basic features only:
# - packet_size, protocol, ttl
# - src_port, dst_port, tcp_flags
# - is_tcp, is_udp
# Memory usage: <1GB
```

### **3. Model Training (1 minute)**
```bash
# Lightweight Random Forest:
# - 50 trees (vs 100)
# - Max depth: 10 (vs unlimited)
# - Single thread processing
# Memory usage: <2GB
```

### **4. Integration (1 minute)**
```bash
# Basic dashboard integration
# Essential endpoints only
# Simplified real-time detection
```

---

## 🎯 **Use Cases for Minimal Setup**

### **Perfect For:**
- **Learning/Education**: Understanding SOC concepts
- **Development/Testing**: Code development and testing
- **Proof of Concept**: Demonstrating basic functionality
- **Resource-Constrained Environments**: VPS, older hardware
- **Quick Demos**: Fast setup for presentations

### **Not Ideal For:**
- **Production Deployment**: Use standard setup
- **Research/Analysis**: Need more comprehensive features
- **High Accuracy Requirements**: Use full feature set
- **Large-Scale Testing**: Need more sample diversity

---

## 🔍 **Troubleshooting Minimal Setup**

### **Memory Issues:**
```bash
# If still running out of memory:
# 1. Reduce samples further
--samples 3000  # Normal traffic
--samples 1000  # Attack traffic

# 2. Process one attack type at a time
# Edit run_minimal_pipeline.sh to process sequentially
```

### **Storage Issues:**
```bash
# Clean up aggressively:
rm -f data_capture/pcaps/*.pcap  # After processing
rm -f /tmp/*.log                 # Temp files
sudo yum clean all               # Package cache
```

### **Performance Issues:**
```bash
# Single-core processing:
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# Reduce model complexity:
# Edit train_minimal_models.py:
n_estimators=25  # Even fewer trees
max_depth=5      # Shallower trees
```

---

## 📈 **Upgrade Path**

### **From Minimal → Standard:**
```bash
# When you get more resources:
1. Increase VM RAM to 8GB
2. Increase storage to 50GB  
3. Run: ./setup_centos_mininet.sh (full version)
4. Use: ./run_centos_pipeline.sh (35K samples)
```

### **Gradual Scaling:**
```bash
# Intermediate setup (6GB RAM):
--samples 15000  # Normal traffic
--samples 5000   # Attack traffic
# Total: 20K samples, ~8 minutes
```

---

## ✅ **Minimal Setup Checklist**

### **Pre-Installation:**
- [ ] VM has 4GB+ RAM
- [ ] VM has 25GB+ storage
- [ ] CentOS 7/8/9 installed
- [ ] Internet connectivity available

### **Post-Installation:**
- [ ] Python packages working
- [ ] Mininet functional
- [ ] PCAP generation working
- [ ] Model training successful
- [ ] Dashboard accessible

### **Validation:**
- [ ] 7K samples generated
- [ ] Model accuracy >85%
- [ ] Real-time prediction working
- [ ] Memory usage <3GB
- [ ] Total runtime <10 minutes

---

## 🎉 **Ready to Go!**

Your minimal setup provides:
- **Functional SOC analysis** with basic anomaly detection
- **Real-time threat detection** capabilities  
- **Network visualization** and alerting
- **Educational value** for learning SOC concepts
- **Development platform** for further enhancements

**Perfect for getting started with SOC analysis on limited resources!** 🚀
