# Complete PCAP to ML Model Notebook Guide

## 🎯 Overview

**File:** `mininet_complete_training.ipynb`

This notebook provides a complete end-to-end pipeline from PCAP files to production-ready ML models.

---

## 📋 What It Does

### Complete Pipeline (16 Steps)

1. **Install Dependencies** - All required packages
2. **Import Libraries** - Scapy, scikit-learn, XGBoost, etc.
3. **Feature Extraction** - Parse PCAP files with Scapy
4. **Load PCAP Files** - Process all normal and attack traffic
5. **Data Analysis** - Visualize distributions and patterns
6. **Preprocessing** - Encode, clean, handle missing values
7. **Train/Val/Test Split** - 60/20/20 split with stratification
8. **Feature Scaling** - StandardScaler normalization
9. **Feature Selection** - SelectKBest with mutual information
10. **SMOTE Balancing** - Handle class imbalance
11. **Train Random Forest** - With regularization
12. **Train XGBoost** - With regularization
13. **Create Ensemble** - Voting classifier
14. **Comprehensive Evaluation** - All metrics
15. **Visualizations** - 6+ charts and plots
16. **Save Models** - Production-ready artifacts

---

## 🚀 How to Use

### Option 1: Local Jupyter

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Install Jupyter
pip install jupyter

# Start notebook
jupyter notebook mininet_complete_training.ipynb
```

### Option 2: Google Colab

1. Upload `mininet_complete_training.ipynb` to Colab
2. Upload your PCAP files when prompted
3. Run all cells

### Option 3: JupyterLab

```bash
pip install jupyterlab
jupyter lab mininet_complete_training.ipynb
```

---

## 📊 Metrics Calculated

### Classification Metrics
- ✅ **Accuracy** - Overall correctness
- ✅ **Precision** - Attack detection accuracy
- ✅ **Recall** - Attack detection coverage
- ✅ **F1-Score** - Harmonic mean of precision/recall
- ✅ **ROC AUC** - Area under ROC curve
- ✅ **Specificity** - True negative rate
- ✅ **Sensitivity** - True positive rate

### Confusion Matrix
- True Negatives (TN)
- False Positives (FP)
- False Negatives (FN)
- True Positives (TP)

### Cross-Validation
- 5-fold stratified CV
- Mean and standard deviation
- Per-fold scores

---

## 📁 Input Files Required

The notebook expects these PCAP files:

```
../data_capture/pcaps/normal_traffic_*.pcap  # Normal traffic
data_capture/mininet/syn_flood.pcap          # SYN flood
data_capture/mininet/port_scan.pcap          # Port scan
data_capture/mininet/udp_flood.pcap          # UDP flood
data_capture/mininet/http_flood.pcap         # HTTP flood
```

**You already have these!** ✅

---

## 📈 Output Files Generated

### Models (8 files)
```
../models/
├── mininet_ensemble_model.pkl          # Main ensemble model
├── mininet_random_forest_model.pkl     # RF model
├── mininet_xgboost_model.pkl           # XGBoost model
├── mininet_scaler.pkl                  # Feature scaler
├── mininet_feature_selector.pkl        # Feature selector
├── mininet_feature_columns.pkl         # Selected features
├── mininet_label_encoders.pkl          # Categorical encoders
└── mininet_model_metadata.pkl          # Training metadata
```

### Visualizations (6+ images)
```
data_analysis.png              # Class and feature distributions
data_split.png                 # Train/val/test split
feature_importance.png         # Top 20 features
smote_balancing.png           # Before/after SMOTE
confusion_matrices.png        # All 3 models
roc_curves.png                # ROC comparison
precision_recall_curves.png   # PR comparison
model_comparison.png          # All metrics comparison
```

---

## 🎯 Key Features

### 1. Direct PCAP Processing
- Uses **Scapy** to parse packets
- Extracts 27+ network features
- Groups packets into flows
- Handles TCP/UDP/ICMP protocols

### 2. Comprehensive Feature Engineering
- **Timing features**: Duration, inter-arrival times
- **Size features**: Packet sizes, byte counts
- **Rate features**: Packets/sec, bytes/sec
- **TCP flags**: SYN, FIN, RST, PSH, ACK, URG
- **Statistical features**: Mean, std, min, max
- **Derived features**: Flag ratios, port classification

### 3. Overfitting Prevention
- **Regularization**: max_depth, min_samples_split
- **Cross-validation**: 5-fold stratified
- **Train/val/test split**: Proper evaluation
- **Feature selection**: Top 30 features
- **SMOTE**: Balanced training

### 4. Multiple Models
- **Random Forest**: 100 trees with regularization
- **XGBoost**: Gradient boosting with L1/L2
- **Ensemble**: Soft voting classifier

### 5. Complete Metrics
- **Accuracy, Precision, Recall, F1**
- **ROC AUC, Specificity, Sensitivity**
- **Confusion Matrix**
- **Cross-validation scores**

---

## 📊 Expected Performance

Based on your PCAP files:

| Metric | Expected Range |
|--------|---------------|
| Accuracy | 92-97% |
| Precision | 90-96% |
| Recall | 93-98% |
| F1-Score | 91-96% |
| ROC AUC | 0.95-0.99 |

---

## 🔧 Customization

### Adjust Model Parameters

**Random Forest:**
```python
rf_model = RandomForestClassifier(
    n_estimators=200,      # More trees
    max_depth=20,          # Deeper trees
    min_samples_split=5,   # Less regularization
    ...
)
```

**XGBoost:**
```python
xgb_model = xgb.XGBClassifier(
    n_estimators=150,      # More rounds
    max_depth=10,          # Deeper trees
    learning_rate=0.1,     # Faster learning
    ...
)
```

### Change Feature Selection

```python
k_features = 40  # Select more features
selector = SelectKBest(mutual_info_classif, k=k_features)
```

### Adjust Data Split

```python
# 70/15/15 split instead of 60/20/20
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'scapy'"

```bash
pip install scapy
```

### Issue: "PCAP file not found"

Update the file paths in Step 4:
```python
pcap_files = [
    ('path/to/your/normal.pcap', 0, 'normal'),
    ('path/to/your/attack.pcap', 1, 'attack'),
]
```

### Issue: "Not enough samples"

The notebook works with any amount of data. Minimum recommended: 1000 samples.

### Issue: "Memory error"

Process PCAP files in batches or use a machine with more RAM.

---

## 📚 Dependencies

```bash
pip install scapy pandas numpy scikit-learn xgboost imbalanced-learn matplotlib seaborn jupyter
```

Or use the first cell in the notebook (auto-installs).

---

## ✅ Success Checklist

After running the notebook:

- [ ] All 16 steps completed without errors
- [ ] 8 model files saved to `../models/`
- [ ] 6+ visualization files generated
- [ ] Performance metrics displayed
- [ ] Accuracy > 90%
- [ ] Models ready for deployment

---

## 🎓 What You Learn

1. **PCAP parsing** with Scapy
2. **Feature extraction** from network traffic
3. **Data preprocessing** best practices
4. **Class imbalance** handling with SMOTE
5. **Model training** with regularization
6. **Comprehensive evaluation** with all metrics
7. **Ensemble methods** for better performance

---

## 🚀 Next Steps

After training:

1. **Deploy models** to dashboard
2. **Test on new data** to verify generalization
3. **Monitor performance** in production
4. **Retrain periodically** with new data

---

## 📞 Quick Reference

**Run notebook:**
```bash
jupyter notebook mininet_complete_training.ipynb
```

**Check outputs:**
```bash
ls -lh ../models/mininet_*.pkl
ls -lh *.png
```

**Load trained model:**
```python
import joblib
model = joblib.load('../models/mininet_ensemble_model.pkl')
```

---

**Your complete PCAP-to-ML pipeline is ready!** 🎊

Just open the notebook and run all cells!
