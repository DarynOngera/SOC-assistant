# Advanced Colab Training Guide - Using Mininet Data

## 🎯 Overview

This notebook trains ML models using your **actual Mininet-generated data** and produces comprehensive reports and visualizations.

---

## 📋 Prerequisites

### 1. Generate Mininet Data First

```bash
cd /home/ongera/projects/SOC-assistant/mininet_data_generation

# Generate 10,000 mixed records
python3 generate_synthetic_data.py
```

This creates: `data_capture/processed/synthetic_dataset_*.csv`

### 2. Locate Your Dataset

```bash
ls -lh data_capture/processed/synthetic_dataset_*.csv
```

---

## 🚀 Using the Notebook

### Step 1: Upload to Colab

1. Go to https://colab.research.google.com/
2. Upload `colab_training_v2.ipynb`
3. Click **Runtime → Change runtime type → GPU**

### Step 2: Upload Your Dataset

When prompted in Step 2, upload your CSV file:
- `synthetic_dataset_YYYYMMDD_HHMMSS.csv`

### Step 3: Run All Cells

Click **Runtime → Run all** and wait ~10 minutes

---

## 📊 What You Get

### Models (7 files)
- `mininet_ensemble_model.pkl` - Main model
- `mininet_random_forest_model.pkl`
- `mininet_xgboost_model.pkl`
- `mininet_scaler.pkl`
- `mininet_feature_selector.pkl`
- `mininet_feature_columns.pkl`
- `mininet_model_metadata.pkl`

### Reports (2 files)
- `training_report.json` - Machine-readable
- `training_report.html` - Human-readable

### Visualizations (9+ images)
1. **class_distribution.png** - Normal vs Attack distribution
2. **data_split.png** - Train/Val/Test split visualization
3. **feature_importance.png** - Top 20 important features
4. **smote_balancing.png** - Before/After SMOTE
5. **confusion_matrices.png** - All 3 models
6. **roc_curves.png** - ROC comparison
7. **precision_recall_curves.png** - PR comparison
8. **model_comparison.png** - All metrics comparison
9. **attack_type_performance.png** - Per-attack performance

---

## 📈 Comprehensive Analysis Includes

### Data Analysis
- Class distribution (Normal vs Attack)
- Attack type breakdown
- Missing value analysis
- Feature statistics

### Feature Engineering
- Top 30 feature selection
- Feature importance ranking
- Correlation analysis
- SMOTE balancing

### Model Training
- Random Forest (100 trees)
- XGBoost (gradient boosting)
- Ensemble (voting classifier)
- 5-fold cross-validation

### Evaluation Metrics
- **Accuracy** - Overall correctness
- **Precision** - Attack detection accuracy
- **Recall** - Attack detection coverage
- **F1-Score** - Balanced metric
- **ROC AUC** - Classification quality
- **Confusion Matrix** - Detailed breakdown
- **Per-Attack Performance** - Individual attack metrics

### Visualizations
- Confusion matrices for all models
- ROC curves comparison
- Precision-Recall curves
- Feature importance charts
- Class distribution plots
- Performance comparison charts

---

## 🎓 Understanding the Reports

### JSON Report Structure

```json
{
  "training_date": "2025-10-08T00:00:00",
  "dataset": {
    "total_samples": 10000,
    "normal_samples": 7000,
    "attack_samples": 3000,
    "features": 24,
    "selected_features": 30
  },
  "models": {
    "Ensemble": {
      "accuracy": 1.0,
      "precision": 1.0,
      "recall": 1.0,
      "f1_score": 1.0,
      "roc_auc": 1.0
    }
  },
  "attack_types": {
    "syn_flood": {...},
    "port_scan": {...}
  }
}
```

### HTML Report Features

- **Visual metrics dashboard**
- **Interactive tables**
- **Color-coded confusion matrix**
- **Complete feature list**
- **Professional formatting**

---

## 🔧 Customization Options

### Adjust Dataset Size

Before running, edit the synthetic data generator:

```python
# Generate more data
df = generate_synthetic_data(n_normal=70000, n_attacks=30000)
```

### Change Train/Val/Test Split

In Step 4:

```python
# Current: 60/20/20
# Change to 70/15/15:
X_train, X_temp, y_train, y_temp = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
```

### Adjust Model Parameters

In Steps 7-8:

```python
# More trees
rf_model = RandomForestClassifier(n_estimators=200, ...)

# Deeper trees
xgb_model = xgb.XGBClassifier(max_depth=15, ...)
```

### Select More Features

In Step 5:

```python
# Select more features
k_features = min(50, X_train.shape[1])  # Instead of 30
```

---

## 📥 Deployment Instructions

### After Training Completes

1. **Download all files** (automatic in Step 15)

2. **Copy models to your project:**

```bash
# On your local machine
cd ~/Downloads
mv mininet_*.pkl /home/ongera/projects/SOC-assistant/models/
```

3. **Verify models:**

```bash
cd /home/ongera/projects/SOC-assistant
ls -lh models/mininet_*.pkl
```

4. **Test model loading:**

```bash
python3 -c "
import joblib
model = joblib.load('models/mininet_ensemble_model.pkl')
print('✓ Model loaded successfully!')
"
```

5. **Restart dashboard:**

```bash
cd src/dashboard
python server.py
```

---

## 📊 Expected Performance

With 10,000 mixed records:

| Metric | Expected Range | Target |
|--------|---------------|--------|
| Accuracy | 95-100% | >95% |
| Precision | 93-100% | >90% |
| Recall | 94-100% | >90% |
| F1-Score | 93-100% | >90% |
| ROC AUC | 0.95-1.0 | >0.90 |

---

## 🐛 Troubleshooting

### Issue: Upload Fails

**Solution:** Ensure CSV file is <100MB
```bash
# Check file size
ls -lh synthetic_dataset_*.csv

# If too large, reduce samples
```

### Issue: Out of Memory

**Solution:** Reduce dataset or use GPU
- Enable GPU: Runtime → Change runtime type → GPU
- Or reduce samples to 5,000

### Issue: Training Takes Too Long

**Solution:** Enable GPU acceleration
- Current: ~10 minutes on CPU
- With GPU: ~3-5 minutes

### Issue: Poor Performance

**Solution:** Check data quality
- Ensure balanced classes
- Verify feature quality
- Check for missing values

---

## 📚 Report Interpretation

### Confusion Matrix

```
                Predicted
              Normal  Attack
Actual Normal   TN      FP
       Attack   FN      TP
```

- **TN (True Negative)**: Correctly identified normal traffic
- **FP (False Positive)**: Normal traffic flagged as attack
- **FN (False Negative)**: Missed attacks
- **TP (True Positive)**: Correctly detected attacks

### ROC Curve

- **Closer to top-left** = Better model
- **AUC = 1.0** = Perfect classifier
- **AUC = 0.5** = Random guessing

### Precision-Recall Curve

- **High precision** = Few false alarms
- **High recall** = Catches most attacks
- **Trade-off** = Balance based on use case

---

## 🎯 Best Practices

### Data Quality

1. **Ensure 10,000+ samples** for robust training
2. **Balance classes** (SMOTE handles this)
3. **Remove duplicates** before training
4. **Verify labels** are correct

### Model Selection

1. **Use Ensemble** for production (best performance)
2. **Use Random Forest** for interpretability
3. **Use XGBoost** for speed

### Validation

1. **Check all metrics**, not just accuracy
2. **Review confusion matrix** for false positives/negatives
3. **Test on unseen data** before deployment
4. **Monitor performance** over time

---

## ✅ Success Checklist

Before deploying:

- [ ] Dataset has 10,000+ samples
- [ ] All models achieve >95% accuracy
- [ ] Confusion matrix looks good (low FP/FN)
- [ ] ROC AUC > 0.95
- [ ] Per-attack performance is consistent
- [ ] All 7 model files downloaded
- [ ] Reports reviewed and understood
- [ ] Models tested locally
- [ ] Dashboard integration verified

---

## 🎉 Summary

This advanced notebook provides:

✅ **Complete training pipeline** using your Mininet data  
✅ **Comprehensive evaluation** with 9+ visualizations  
✅ **Detailed reports** in JSON and HTML  
✅ **Production-ready models** with metadata  
✅ **Per-attack analysis** for all attack types  
✅ **Professional documentation** for stakeholders  

**Ready to train? Upload `colab_training_v2.ipynb` and your CSV data!** 🚀
