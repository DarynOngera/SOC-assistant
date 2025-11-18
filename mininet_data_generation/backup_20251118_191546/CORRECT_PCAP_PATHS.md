# Correct PCAP File Paths

## ✅ Verified PCAP Locations

### Normal Traffic Files

**Location:** `/home/ongera/projects/SOC-assistant/data_capture/pcaps/`

```bash
/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap  ← BEST
/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_002608.pcap
/home/ongera/projects/SOC-assistant/data_capture/pcaps/attack_all_20251007_160040.pcap
/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251007_155714.pcap
/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251007_154934.pcap
/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251007_152226.pcap
/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251007_151142.pcap
/home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251007_151008.pcap
```

### Attack Traffic Files

**Location:** `/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/`

```bash
/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap
/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/port_scan.pcap
/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/udp_flood.pcap
/home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/http_flood.pcap
```

---

## 🚀 Copy Files for Easy Upload to Colab

### Create Upload Directory

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Create upload directory
mkdir -p colab_upload

# Copy normal traffic (use latest)
cp /home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap \
   colab_upload/normal_traffic.pcap

# Copy all attack files
cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/syn_flood.pcap \
   colab_upload/

cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/port_scan.pcap \
   colab_upload/

cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/udp_flood.pcap \
   colab_upload/

cp /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/http_flood.pcap \
   colab_upload/

# Verify files
ls -lh colab_upload/
```

### Your Upload Directory Will Have

```
colab_upload/
├── normal_traffic.pcap    (7.8 MB)
├── syn_flood.pcap         (1.6 KB)
├── port_scan.pcap         (1.4 KB)
├── udp_flood.pcap         (1.2 KB)
└── http_flood.pcap        (196 B)
```

---

## 📊 Verify Files Exist

```bash
# Check normal traffic
ls -lh /home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap

# Check attack files
ls -lh /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/*.pcap

# Count packets in each file
echo "Normal traffic packets:"
tcpdump -r /home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap 2>/dev/null | wc -l

echo "Attack packets:"
for f in /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/*.pcap; do
    echo "$(basename $f): $(tcpdump -r $f 2>/dev/null | wc -l) packets"
done
```

---

## 🎯 For Colab Upload

**Option 1: Upload from colab_upload directory**
1. Run the copy commands above
2. Navigate to `colab_upload/` directory
3. Upload all 5 files to Colab

**Option 2: Upload directly from original locations**
- Just navigate to the paths above and upload

---

## ✅ Quick Test

```bash
# Test if files are readable
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Test normal traffic
tcpdump -r /home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap -c 5

# Test attack files
tcpdump -r data_capture/mininet/syn_flood.pcap -c 5
```

---

## 📝 Summary

**All files exist and are accessible!**

- ✅ Normal traffic: 8 files available
- ✅ Attack traffic: 4 files available
- ✅ Total size: ~25 MB (easy to upload)

**Recommended for training:**
```
Normal: /home/ongera/projects/SOC-assistant/data_capture/pcaps/normal_traffic_20251008_003311.pcap
Attacks: /home/ongera/projects/SOC-assistant/mininet_data_generation/data_capture/mininet/*.pcap
```

**Files are ready for Colab!** 🎊
