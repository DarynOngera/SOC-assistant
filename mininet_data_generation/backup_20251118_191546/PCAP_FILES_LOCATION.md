# PCAP Files Location Guide

## 📁 Your PCAP Files

### Normal Traffic PCAP Files

Located in: `../data_capture/pcaps/`

```
normal_traffic_20251008_003311.pcap  (7.8 MB)  ← LATEST & BEST
normal_traffic_20251008_002608.pcap  (7.5 MB)
normal_traffic_20251007_160040.pcap  (1.2 MB)  [attack_all]
normal_traffic_20251007_155714.pcap  (1.4 MB)
normal_traffic_20251007_154934.pcap  (2.1 MB)
normal_traffic_20251007_152226.pcap  (748 KB)
normal_traffic_20251007_151142.pcap  (17 MB)   ← LARGEST
normal_traffic_20251007_151008.pcap  (1.3 MB)
```

**Recommended for training:**
- `normal_traffic_20251008_003311.pcap` (7.8 MB) - Latest, good size

### Attack Traffic PCAP Files

Located in: `data_capture/mininet/`

```
syn_flood.pcap   (1.6 KB)  ← SYN flood attacks
port_scan.pcap   (1.4 KB)  ← Port scanning
udp_flood.pcap   (1.2 KB)  ← UDP floods
http_flood.pcap  (196 B)   ← HTTP floods (small)
```

---

## 🎯 For Colab Training

### Upload These Files

**Normal Traffic (choose one):**
```bash
# Copy to easily accessible location
cp ../data_capture/pcaps/normal_traffic_20251008_003311.pcap ~/normal_traffic.pcap
```

**Attack Traffic (all):**
```bash
# Copy all attack files
cp data_capture/mininet/*.pcap ~/
```

### Files to Upload to Colab

```
1. normal_traffic.pcap (7.8 MB)
2. syn_flood.pcap (1.6 KB)
3. port_scan.pcap (1.4 KB)
4. udp_flood.pcap (1.2 KB)
5. http_flood.pcap (196 B)
```

**Total size:** ~7.8 MB (easy to upload)

---

## 📊 File Statistics

### Normal Traffic Files

| File | Size | Packets | Best For |
|------|------|---------|----------|
| normal_traffic_20251008_003311.pcap | 7.8 MB | ~50k | **Training** ✅ |
| normal_traffic_20251007_151142.pcap | 17 MB | ~100k | Large dataset |
| normal_traffic_20251007_154934.pcap | 2.1 MB | ~15k | Quick testing |

### Attack Files

| File | Size | Type | Packets |
|------|------|------|---------|
| syn_flood.pcap | 1.6 KB | SYN Flood | ~20 |
| port_scan.pcap | 1.4 KB | Port Scan | ~15 |
| udp_flood.pcap | 1.2 KB | UDP Flood | ~12 |
| http_flood.pcap | 196 B | HTTP Flood | ~2 |

---

## 🚀 Quick Access Commands

### View PCAP Info

```bash
# Check packet count
tcpdump -r ../data_capture/pcaps/normal_traffic_20251008_003311.pcap | wc -l

# View first 10 packets
tcpdump -r ../data_capture/pcaps/normal_traffic_20251008_003311.pcap -c 10

# Check file size
ls -lh ../data_capture/pcaps/*.pcap
```

### Copy for Colab

```bash
# Create upload directory
mkdir -p ~/colab_upload

# Copy recommended files
cp ../data_capture/pcaps/normal_traffic_20251008_003311.pcap ~/colab_upload/normal_traffic.pcap
cp data_capture/mininet/*.pcap ~/colab_upload/

# Check what you have
ls -lh ~/colab_upload/
```

### Merge Multiple Normal Traffic Files (Optional)

```bash
# If you want more training data
mergecap -w ~/combined_normal.pcap \
  ../data_capture/pcaps/normal_traffic_20251008_003311.pcap \
  ../data_capture/pcaps/normal_traffic_20251007_151142.pcap
```

---

## 📈 Recommended Setup

### For Best Training Results

**Option 1: Quick Training (Recommended)**
```
Normal: normal_traffic_20251008_003311.pcap (7.8 MB)
Attacks: All 4 attack files (~5 KB total)
Total: ~7.8 MB
Training time: ~5 minutes
```

**Option 2: Large Dataset**
```
Normal: normal_traffic_20251007_151142.pcap (17 MB)
Attacks: All 4 attack files
Total: ~17 MB
Training time: ~10 minutes
```

**Option 3: Multiple Normal Files**
```
Normal: Combine 2-3 normal traffic files
Attacks: All 4 attack files
Total: ~15-25 MB
Training time: ~8-12 minutes
```

---

## ⚠️ Important Notes

### File Sizes
- **Attack files are small** because they were terminated early
- **Normal traffic files are good** - contain real traffic
- **Recommended:** Use `normal_traffic_20251008_003311.pcap` (latest)

### Upload Limits
- **Colab:** Can handle up to 100 MB easily
- **Your files:** Total ~25 MB (no problem!)

### Quality Check

```bash
# Verify PCAP files are valid
capinfos ../data_capture/pcaps/normal_traffic_20251008_003311.pcap
capinfos data_capture/mininet/syn_flood.pcap
```

---

## 🎯 For Notebook Training

### Update File Paths in Notebook

**Step 4 in the notebook, change:**

```python
pcap_files = [
    # Normal traffic - use your latest file
    ('../data_capture/pcaps/normal_traffic_20251008_003311.pcap', 0, 'normal'),
    
    # Attack traffic
    ('data_capture/mininet/syn_flood.pcap', 1, 'syn_flood'),
    ('data_capture/mininet/port_scan.pcap', 1, 'port_scan'),
    ('data_capture/mininet/udp_flood.pcap', 1, 'udp_flood'),
    ('data_capture/mininet/http_flood.pcap', 1, 'http_flood'),
]
```

---

## ✅ Quick Checklist

Before uploading to Colab:

- [ ] Located PCAP files
- [ ] Verified files exist
- [ ] Checked file sizes
- [ ] Copied to accessible location
- [ ] Ready to upload

---

## 📞 Quick Reference

**Normal traffic location:**
```
/home/ongera/projects/SOC-assistant/data_capture/pcaps/
```

**Attack traffic location:**
```
/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/
```

**Recommended file:**
```
normal_traffic_20251008_003311.pcap (7.8 MB)
```

**All attack files:**
```
syn_flood.pcap, port_scan.pcap, udp_flood.pcap, http_flood.pcap
```

---

**Your PCAP files are ready for Colab training!** 🎊
