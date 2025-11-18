# Google Colab - Training & Prediction Guide

## 🎯 Complete Pipeline

**File:** `mininet_colab_training.ipynb`

This notebook trains models from your PCAP files and makes predictions on NEW PCAP files.

---

## 📋 What It Does

### Part 1: Training (Steps 1-11)
1. Upload training PCAP files
2. Extract features
3. Train models (RF, XGBoost, Ensemble)
4. Evaluate with all metrics
5. Download trained models

### Part 2: Prediction (Steps 12-16)
6. Upload NEW PCAP files
7. Extract features from new data
8. Make predictions using trained models
9. Analyze predictions
10. Download prediction results

---

## 🚀 How to Use

### Step 1: Upload to Colab

1. Go to https://colab.research.google.com/
2. Click **File → Upload notebook**
3. Upload `mininet_colab_training.ipynb`

### Step 2: Run Training

1. Click **Runtime → Run all** (or run cells one by one)
2. When prompted, upload your training PCAP files:
   - `normal_traffic_20251008_003311.pcap`
   - `syn_flood.pcap`
   - `port_scan.pcap`
   - `udp_flood.pcap`
   - `http_flood.pcap`

3. Wait for training to complete (~5-10 minutes)
4. Download trained models (8 files)

### Step 3: Make Predictions

1. Continue in the same notebook
2. Upload NEW PCAP files when prompted
3. Get predictions automatically
4. Download prediction results

---

## 📊 Outputs

### Training Outputs (Downloaded)
```
mininet_ensemble_model.pkl          # Main model
mininet_random_forest_model.pkl     # RF model
mininet_xgboost_model.pkl           # XGBoost model
mininet_scaler.pkl                  # Feature scaler
mininet_feature_selector.pkl        # Feature selector
mininet_feature_columns.pkl         # Selected features
mininet_label_encoders.pkl          # Encoders
mininet_model_metadata.pkl          # Metadata
```

### Prediction Outputs (Downloaded)
```
predictions_YYYYMMDD_HHMMSS.csv     # Prediction results
prediction_analysis.png             # Visualizations
confusion_matrix.png                # Training metrics
```

---

## 📈 Prediction Results Format

The CSV file contains:

| Column | Description |
|--------|-------------|
| protocol | TCP/UDP/ICMP |
| src_port | Source port |
| dst_port | Destination port |
| packet_count | Number of packets |
| packets_per_sec | Packet rate |
| bytes_per_sec | Byte rate |
| syn_ratio | SYN flag ratio |
| **prediction** | 0=Normal, 1=Attack |
| **prediction_label** | "Normal" or "Attack" |
| **confidence** | 0.0-1.0 (model confidence) |

---

## 🎯 Example Workflow

### Scenario: Train and Test

```
1. Upload Training Data (Step 3)
   ├── normal_traffic.pcap (7.8 MB)
   ├── syn_flood.pcap (1.6 KB)
   ├── port_scan.pcap (1.4 KB)
   ├── udp_flood.pcap (1.2 KB)
   └── http_flood.pcap (196 B)

2. Training Completes
   ├── Accuracy: 94.5%
   ├── Precision: 93.2%
   ├── Recall: 96.1%
   └── F1-Score: 94.6%

3. Download Models (Step 11)
   └── 8 .pkl files downloaded

4. Upload New PCAP (Step 12)
   └── new_traffic_capture.pcap

5. Get Predictions (Step 14)
   ├── Total flows: 1,234
   ├── Normal: 1,150 (93.2%)
   ├── Attack: 84 (6.8%)
   └── High-confidence attacks: 72

6. Download Results (Step 16)
   └── predictions_20251008_010000.csv
```

---

## 📊 Understanding Predictions

### Prediction Labels
- **0 / "Normal"** - Benign traffic
- **1 / "Attack"** - Malicious traffic

### Confidence Scores
- **> 0.9** - High confidence (very reliable)
- **0.7-0.9** - Medium confidence (reliable)
- **< 0.7** - Low confidence (uncertain)

### Example Predictions

```
Flow 1:
  Protocol: TCP
  Packets/sec: 1,234
  SYN ratio: 0.95
  → Prediction: Attack (SYN Flood)
  → Confidence: 0.98 (98%)

Flow 2:
  Protocol: TCP
  Packets/sec: 45
  SYN ratio: 0.02
  → Prediction: Normal
  → Confidence: 0.92 (92%)
```

---

## 🔧 Customization

### Adjust Confidence Threshold

In Step 15, change:
```python
high_conf_attacks = new_df[(new_df['prediction'] == 1) & (new_df['confidence'] > 0.95)]
```

### Filter by Protocol

```python
tcp_attacks = new_df[(new_df['prediction'] == 1) & (new_df['protocol'] == 'TCP')]
```

### Export Only Attacks

```python
attacks_only = new_df[new_df['prediction'] == 1]
attacks_only.to_csv('attacks_only.csv', index=False)
```

---

## 🐛 Troubleshooting

### Issue: "File upload failed"

**Solution:** Files must be < 100MB. Split large PCAP files.

### Issue: "Feature mismatch"

**Solution:** The notebook handles this automatically by aligning features.

### Issue: "Low confidence predictions"

**Solution:** 
- Train with more data
- Check if new PCAP is similar to training data
- Adjust model parameters

### Issue: "All predictions are attacks"

**Solution:**
- Check if new PCAP actually contains attacks
- Verify training data quality
- Review confidence scores

---

## 📈 Expected Performance

### Training Metrics
- Accuracy: 92-97%
- Precision: 90-96%
- Recall: 93-98%
- F1-Score: 91-96%

### Prediction Confidence
- High (>0.9): 70-80% of predictions
- Medium (0.7-0.9): 15-25% of predictions
- Low (<0.7): 5-10% of predictions

---

## 💡 Tips for Best Results

### Training Phase
1. **Use diverse data** - Mix of normal and attack traffic
2. **Balance classes** - Similar amounts of normal/attack (SMOTE handles this)
3. **Quality over quantity** - Clean data is better than lots of noisy data

### Prediction Phase
1. **Check confidence** - Focus on high-confidence predictions
2. **Analyze patterns** - Look for common attack characteristics
3. **Validate results** - Cross-check suspicious flows

---

## 🎓 What You Learn

1. **PCAP processing** with Scapy
2. **Feature extraction** from network traffic
3. **ML model training** with scikit-learn
4. **Real-time prediction** on new data
5. **Result analysis** and interpretation

---

## 📞 Quick Reference

**Upload notebook:**
```
https://colab.research.google.com/ → Upload mininet_colab_training.ipynb
```

**Run training:**
```
Runtime → Run all → Upload PCAP files
```

**Make predictions:**
```
Continue to Step 12 → Upload new PCAP → Get predictions
```

**Download results:**
```
Automatic download in Steps 11 and 16
```

---

## ✅ Success Checklist

Training Phase:
- [ ] Notebook uploaded to Colab
- [ ] Training PCAP files uploaded
- [ ] Models trained successfully
- [ ] Accuracy > 90%
- [ ] 8 model files downloaded

Prediction Phase:
- [ ] New PCAP files uploaded
- [ ] Features extracted
- [ ] Predictions generated
- [ ] Results analyzed
- [ ] Predictions CSV downloaded

---

## 🎉 Summary

This notebook provides:
- ✅ **Complete training** from PCAP files
- ✅ **All metrics** (accuracy, precision, recall, F1, ROC AUC)
- ✅ **Model download** for deployment
- ✅ **Prediction on new data** using trained models
- ✅ **Result analysis** with visualizations
- ✅ **CSV export** of predictions

**Your complete PCAP training and prediction pipeline!** 🚀
